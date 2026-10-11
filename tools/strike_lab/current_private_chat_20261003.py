"""Pinned private-chat x86 producer/consumer proof; no live-process mutations."""
import argparse
import json
import struct
from pathlib import Path

import pefile
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EBP, UC_X86_REG_EIP, UC_X86_REG_ESP
from tools.strike_lab.current_party_chat_20261003 import ChatVM, ROOT, EXE, SOURCE, CLIENT_SHA256, IMAGE_SHA256, UI, STACK, BODY, STOP, ACTOR, VISIBLE, REGIONS, sha
from tools.strike_lab.current_protocol_coverage import qualified_image


class PrivateVM(ChatVM):
    def __init__(self, raw, **kwargs):
        super().__init__(raw, **kwargs)
        # Contact-history insertion and UI refresh are observed boundaries.
        self.helpers[0x50f1c0] = 8
        self.helpers[0x47e600] = 0
        self.helpers[0x475d60] = 16
        self.helpers[0x5068c0] = 16
        self.helpers[0x47ece0] = 4

    def hook(self, vm, address, size, context):
        if address == 0x547f90:
            esp = vm.reg_read(UC_X86_REG_ESP)
            ret, string, chars = struct.unpack('<3I', self.read(esp, 12))
            value, delimiters = self.cstr(string), self.cstr(chars)
            self.boundaries.append({'function': '00547F90', 'input_hex': value.hex(),
                                    'substring_hex': delimiters.hex(),
                                    'native_CRT_strstr_executed': True})
            # Execute the actual mapped native strstr, including its strchr
            # single-character branch; never model strpbrk semantics.
        if address == 0x4b29b0:
            esp = vm.reg_read(UC_X86_REG_ESP)
            ret, index = struct.unpack('<2I', self.read(esp, 8))
            self.boundaries.append({'function': '004B29B0', 'index': index,
                                    'UI_reply_template_boundary_model': True})
            vm.reg_write(UC_X86_REG_EAX, BODY + 0x600)
            vm.reg_write(UC_X86_REG_EIP, ret)
            vm.reg_write(UC_X86_REG_ESP, esp + 8)
            return
        super().hook(vm, address, size, context)


def dispatch(raw, language, mode, *, current=False):
    v = PrivateVM(raw, language=language)
    text = b'Leader: PrivateProbe'
    packet = bytearray(14 + len(text))
    packet[0] = 0x5c
    struct.pack_into('<H', packet, 1, len(packet))
    struct.pack_into('<I', packet, 5, 513)
    packet[9] = mode | (language << 7)
    packet[13:] = text + b'\0'
    v.vm.mem_write(BODY, bytes(packet))
    v.stop_at = 0x475e00
    v.put(STACK + 0x800, '<I', STOP)
    v.vm.reg_write(UC_X86_REG_ESP, STACK + 0x800)
    v.vm.reg_write(UC_X86_REG_EBP, UI - 0xa7f2f6c)
    v.vm.reg_write(UC_X86_REG_EBX, BODY)
    v.vm.emu_start(0x46ae96, STOP, count=100000)
    assert v.vm.reg_read(UC_X86_REG_EIP) == v.stop_at
    ret, delivered_mode, pointer = struct.unpack('<3I', v.read(v.vm.reg_read(UC_X86_REG_ESP), 12))
    assert delivered_mode == mode and pointer == BODY + 13
    assert 0x4fb690 not in v.visits
    return {'language': language, 'mode': mode, 'packet_hex': bytes(packet).hex(),
            'consumer_mode': delivered_mode, 'text_offset': 13, 'caller_return_va': f'{ret:08X}',
            'bubble_consumer_visited': False, 'current_detour_executed': current,
            'instruction_count': len(v.visits)}


def build_report():
    raw = qualified_image()
    exe = EXE.read_bytes()
    assert sha(exe) == CLIENT_SHA256
    current = pefile.PE(data=exe).get_memory_mapped_image()
    intervals = []
    for start, end in REGIONS + ((0x476be0, 0x476c60), (0x47dc90, 0x47dcb0),
                                (0x47ddc0, 0x47de00), (0x547f90, 0x548010),
                                (0x5489a6, 0x548a60), (0x47ee70, 0x47f120),
                                (0x47eba0, 0x47ebf0), (0x4f57e0, 0x4f58c0),
                                (0x4b39a0, 0x4b3a40)):
        a, b = start - 0x400000, end - 0x400000
        assert raw[a:b] == current[a:b], f'Current code changed at {start:X}'
        intervals.append({'start_va': f'{start:08X}', 'end_va_exclusive': f'{end:08X}',
                          'sha256': sha(raw[a:b]), 'current_exe_equal': True})
    producer = []
    inputs = [('$prefix', b'$Target PrivateProbe', 0, 0, 0),
              ('$spaces', b'$Target   PrivateProbe', 0, 0, 0),
              ('$missing_separator', b'$Target', 0, 0, 0),
              ('$empty_message', b'$Target ', 0, 0, 0),
              ('selected_private', b'PrivateProbe', 0, 3, BODY + 0x600),
              ('auto_reply_mode9', b'PrivateProbe', 9, 3, BODY + 0x600)]
    for build, image in (('original', raw), ('current', current)):
        for language in (0, 1):
            for word in (0, 0xffff, 0xff00):
                for case, text, param2, selected, recipient in inputs:
                    v = PrivateVM(image, language=language)
                    v.put(UI + 0x39e00, '<I', selected)
                    v.vm.mem_write(BODY + 0x600, b'Target\0')
                    v.call(0x496990, BODY, param2, word, recipient, body=text + b'\0')
                    assert len(v.queued) <= 1
                    wires = [wire.hex() for wire in v.queued]
                    if case in ('$prefix', '$spaces', 'selected_private', 'auto_reply_mode9'):
                        assert len(v.queued) == 1
                        wire = v.queued[0]
                        assert wire[0] == 0x2f and len(wire) == struct.unpack_from('<H', wire, 1)[0]
                        assert wire[3] == (9 if param2 == 9 else 2) | (language << 7)
                        assert wire[4] == 0xa5 and struct.unpack_from('<H', wire, 5)[0] == word
                        assert wire[7:] == b'$Target PrivateProbe\0', wire
                    producer.append({'build': build, 'case': case, 'language': language,
                                     'caller_word': word, 'selected_channel': selected,
                                     'param2': param2, 'param4_supplied': bool(recipient),
                                     'input_hex': text.hex(), 'queued': wires,
                                     'boundaries': v.boundaries})
    consumers = []
    for build, image in (('original', raw), ('current', current)):
        for mode in (2, 9):
            for flags in (0, 0x20, 0xffff):
                for mask in (0, 1, 8, 15):
                    v = PrivateVM(image)
                    v.put(ACTOR + 0x449c, '<H', flags)
                    v.put(UI + 0x39e04, '<I', mask)
                    v.call(0x475e00, mode, BODY, body=b'Leader: PrivateProbe\0')
                    archive, visible = v.ring(UI + 0x39e20), v.ring(VISIBLE)
                    assert archive['count'] == 1 and visible['count'] == bool(mask & 8)
                    for ring in (archive, visible):
                        assert all(row['channel'] == 2 and row['color'] == 0xffff for row in ring['rows'])
                    consumers.append({'build': build, 'mode': mode, 'option_word': flags,
                                      'visible_mask': mask, 'archive': archive, 'visible': visible,
                                      'bubble_consumer_visited': False,
                                      'display_boundary': [item for item in v.boundaries if item['function'] == '0047DE00']})
    dispatches = [dict(dispatch(image, language, mode, current=build == 'current'), build=build)
                  for build, image in (('original', raw), ('current', current))
                  for language in (0, 1) for mode in (2, 9)]
    dedicated = []
    for build, image in (('original', raw), ('current', current)):
        for self_name, selected_peer, text in (
            (b'Leader', b'Target', b'Leader: [Target] PrivateProbe'),
            (b'Target', b'Leader', b'Leader: [Target] PrivateProbe'),
            (b'Target', b'Leader', b'Leader: PrivateProbe'),
            (b'Leader', b'Target', b'Leader: PrivateProbe'),
            (b'Other', b'Leader', b'Leader: [Target] PrivateProbe'),
        ):
            v = PrivateVM(image)
            v.vm.mem_write(ACTOR + 0x27, self_name + b'\0')
            v.vm.mem_write(UI + 0x39e08, selected_peer + b'\0')
            v.put(UI + 0x39e18, '<B', 1)
            v.call(0x475e00, 2, BODY, body=text + b'\0')
            archive, visible = v.ring(UI + 0x39e20), v.ring(VISIBLE)
            expected = int((self_name == b'Leader' and b'[Target]' in text) or
                           (self_name != b'Leader' and selected_peer == b'Leader'))
            assert archive['count'] == 1 and visible['count'] == expected, (build, self_name, text, archive, visible)
            dedicated.append({'build': build, 'self_hex': self_name.hex(),
                              'selected_peer_hex': selected_peer.hex(), 'input_hex': text.hex(),
                              'archive': archive, 'visible': visible,
                              'native_conversation_filter_executed': 0x47eeb0 in v.visits,
                              'substring_boundaries': [x for x in v.boundaries if x['function'] == '00547F90']})
    automatic = []
    for build, image in (('original', raw), ('current', current)):
        for mode in (2, 9):
            v = PrivateVM(image)
            v.put(UI + 0x23d89c, '<B', 1)
            v.put(UI + 0x39e00, '<I', 3)
            v.vm.mem_write(BODY + 0x600, b'AwayProbe\0')
            v.call(0x475e00, mode, BODY, body=b'Remote: [Leader] PrivateProbe\0')
            assert len(v.queued) == (1 if mode == 2 else 0)
            if mode == 2:
                assert v.queued[0][3] == 9 and v.queued[0][5:7] == b'\xff\xff'
                assert v.queued[0][7:] == b'$Remote AwayProbe\0'
            automatic.append({'build': build, 'incoming_mode': mode,
                              'auto_reply_setting_UI_23D89C': 1,
                              'setting_after': v.read(UI + 0x23d89c, 1)[0],
                              'queued': [wire.hex() for wire in v.queued],
                              'bubble_consumer_visited': False,
                              'boundaries': v.boundaries,
                              'contact_history_boundary': [list(x) for x in v.calls if x[0] == 0x50f1c0]})
    names = []
    for build, image in (('original', raw), ('current', current)):
        for speaker, text in ((b'Leader', b'Leader: [Target] PrivateProbe'),
                              (b'Leader', b'Leader: PrivateProbe'),
                              ('小明'.encode('cp950'), '小明: [小華] 中文測試'.encode('cp950')),
                              ('小明'.encode('cp936'), '小明: [小华] 中文测试'.encode('cp936'))):
            v = PrivateVM(image)
            v.call(0x47dd60, BODY, BODY + 0x600, body=text + b'\0')
            assert v.cstr(BODY + 0x600) == speaker
            assert v.vm.reg_read(UC_X86_REG_EAX) == 1
            names.append({'build': build, 'text_hex': text.hex(), 'speaker_hex': speaker.hex(),
                          'native_speaker_extractor_executed': True})
    ui = []
    for build, image in (('original', raw), ('current', current)):
        v = PrivateVM(image)
        v.call(0x4f57e0, 11, 1)
        assert v.read(UI + 0x23d89c, 1) == b'\x01'
        v.call(0x4f57e0, 11, 1)
        assert v.read(UI + 0x23d89c, 1) == b'\0'
        v.call(0x47eba0, BODY, body=b'Target\0')
        assert v.read(UI + 0x39e18, 1) == b'\x01'
        assert v.cstr(UI + 0x39e08) == b'Target'
        ui.append({'build': build, 'away_callback': '004F57E0(control11,event1)',
                   'away_toggle_observed': [1, 0], 'private_view_callback': '0047EBA0(Target)',
                   'private_view_after': 1, 'selected_peer_after': 'Target',
                   'ring_rebuild_boundary_observed': '0047ECE0(-1)'})
    detours = []
    for start, end in ((0x46ae96, 0x46ae9e), (0x47de00, 0x47de06),
                       (0x4c7621, 0x4c7627), (0x4b2bf4, 0x4b2bf9)):
        a, b = start - 0x400000, end - 0x400000
        detours.append({'start_va': f'{start:08X}', 'end_va_exclusive': f'{end:08X}',
                        'original_hex': raw[a:b].hex(), 'current_hex': current[a:b].hex()})
    source_entries = ('00496990', '00475e00', '0047dd60', '0047ddc0', '0047de00',
                      '0047eeb0', '0047ee70', '004c7610', '004b2ae0', '004b12b0',
                      '004a6760', '0047f270', '0047ebf0', '00547f90',
                      '004f57e0', '004b39a0', '0047eba0', '00473b00', '00473600')
    return {'format': 'native-private-chat-20261003-v1', 'native_image_sha256': IMAGE_SHA256,
            'current_exe_sha256': CLIENT_SHA256, 'code_intervals': intervals,
            'producer_cases': producer, 'consumer_cases': consumers, 'dispatch_cases': dispatches,
            'dedicated_conversation_cases': dedicated, 'automatic_reply_cases': automatic,
            'speaker_extraction_cases': names,
            'native_ui_state_cases': ui,
            'current_build_detours': detours,
            'current_wrapper_pins': [{'start_va': f'{a:08X}', 'end_va_exclusive': f'{b:08X}',
                                      'sha256': sha(current[a-0x400000:b-0x400000])}
                                     for a,b in ((0x714200,0x714223),(0x70ff5b,0x71010e),
                                                 (0x70f9b6,0x70fb61),(0x70ff41,0x70ff5b))],
            'source_pins': [{'path': str(SOURCE / f'{entry}_FUN_{entry}.c'),
                            'sha256': sha((SOURCE / f'{entry}_FUN_{entry}.c').read_bytes()),
                            'authority': 'Pseudocode aid only; mapped x86 is executable authority'}
                           for entry in source_entries],
            'frozen_helper_pins': [{'path': str(ROOT / 'tools/strike_lab/current_party_chat_20261003.py'),
                                   'sha256': sha((ROOT / 'tools/strike_lab/current_party_chat_20261003.py').read_bytes())}],
            'counts': {'producer': len(producer), 'consumer': len(consumers), 'dispatch': len(dispatches),
                       'dedicated_conversation': len(dedicated), 'automatic_reply': len(automatic),
                       'speaker_extraction': len(names), 'ui_state': len(ui)},
            'c2s': {'opcode': '2F', 'length_word_offsets': [1, 2], 'mode_offset': 3,
                    'mode_low7': [2, 9], 'language_highbit': True,
                    'opaque_stack_pad_offset': 4, 'caller_word_offsets': [5, 6], 'text_offset': 7,
                    'grammar': '$recipient message followed by NUL; first ASCII space splits recipient; native prefix parser skips further spaces before message.',
                    'ordinary_caller_word': 0, 'automatic_reply_caller_word': 65535,
                    'target_authority': 'Recipient is text. Caller WORD is not a guessed character ID. Original server name lookup/matching policy unknown.',
                    'malformed_prefix': 'Missing separator and empty message fall back to native common mode0, preserving $recipient text.'},
            's2c': {'opcode': '5C', 'sender_dword_offset': 5, 'mode_offset': 9,
                    'text_offset': 13, 'modes': [2, 9], 'display_channel': 2,
                    'native_color': 'FFFF', 'bubble': False,
                    'filter': '4C7610(2) always returns1; no actor449C option bit gates private display.',
                    'rings': 'Archive UI+39E20 always receives enabled private chat; common visible ring UI+39DE8 requiresUI+39E04&8 with39E18=0.',
                    'native_self_summary': 'Producer stores Sender: [Recipient] message atUI+39D68. Dedicated self-view requires recipient bracket to match selectedpeer; recipient can displaySender:message too.',
                    'server_text_origin': 'Client summary supports Sender: [Recipient] message, but original server self/recipient packet text policy is not recoverable solely from consumer.',
                    'auto_reply': 'UI+23D89C=1 and foreign sender: incoming2 emitsmode9 to extracted sender usingreplytemplate0; incoming9 displaysbutdoesnotreplyandexecutes4B39A0toclearAway, preventingrecursiveautoresponse.'},
            'normal_ui': {
                'direct_typed': 'Click native chat edit and typeASCII $Target message then Enter.4B2AE0 normal branch calls496990(text,0,0,0). No party membership required.',
                'selected_private': 'Mainmenu4A6760(mode2) control33→4B12B0(1,3), or chatfilterwidget232E10 SHIFT+control13; selectedUI+39E00=3. Native39E00=3 Enterreadsrecipient edit up to15bytes andcalls496990(text,0,0,recipient).',
                'recipient_edit': '4B12B0 private selection invokes4B1A80(1), selects native recipient edit state5BFA4=1;4B2AE0(state1) takesrecipient up to15bytes and message up to51bytes, then returns to chat state0.',
                'away': 'Mainmenu4A6760 mode0,item32,param2=5 opens4F56F0→4F5730 replypanel232DBE.4F57E0 control11,event1 toggles23D89C; controls0..7 selectreplytemplates(editstate17..24); closecontrol10 or right event2.4B39A0 clearsAwayonordinarytypedchatandforeignincomingmode9.',
                'dedicated_view': 'Recentprivate-contactlist473B00(row), with42D98=1, invokes47EBA0(contactname) setting39E18=1 and39E08=name, then47DCF0.473600callback uses50D8A0 listrowhit,4092C=0; native50F1C0 addscontactonprivatesend/receive.',
                'visible_filter': 'Chatfilter widget232E10 control13,event20 withoutSHIFT clearsprivate-view39E18 and togglesvisiblebit8 through47ECE0→47EBF0. NormalwindowlocalWM200/201/202 withframegaps.',
                'coordinates': 'Dynamicnativehitrect controlentryUI+E2170+widget*2A08+8B8+index*100; signedhitWORD+8; managerDWORD UI+E2174; rectDWORDs manager+hit*24+[4,8,12,16].',
                'scope': 'UI control identities are source/native-code pinned; actual hidden-window input still requires live acceptance.'},
            'boundaries': ['00547AF7 sprintf external CRT%s formatting modeled by frozenChatVM.',
                           '00547F90 native strstr and native0047DD60 speaker extraction actuallyexecute.',
                           '0050F1C0 contacthistory mutation observed, not executed; UIreplytemplate004B29B0 modeled asAwayProbe.',
                           'UI redraw helpers0047E600/0047ECE0/005068C0 and programmessage00475D60 observed boundaries;4B39A0 Awayclear executesnative; no renderedpixels accepted.'],
            'open_limits': ['Original server recipient lookup, duplicate names, exact versus folded names, offline replies and cross-language naming are unknown; requireexplicitCUSTOMownership policy.',
                            'Current/native matchinglocale5C dispatch executed;cross-language52F500conversion remains live-server acceptance work.',
                            'All probes runoffline mappedx86 only, no client/network/database/service mutations.'],
            'current_client_accepted': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    report = json.dumps(build_report(), indent=2, ensure_ascii=False) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding='utf-8')
        print(f'wrote {args.output}')
    else:
        print(report, end='')
