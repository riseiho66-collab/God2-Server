"""Pinned original party-chat producers, filters, dispatch and ring consumers.

No live processes, services, windows or database mutations. External CRT string
formatting and UI redraw boundaries are explicitly observed/modeled.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import pefile
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EBP, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP
from tools.strike_lab.current_party_20261002 import Oracle, UI, STACK, BODY, STOP, ACTOR
from tools.strike_lab.current_protocol_coverage import qualified_image, IMAGE_SHA256
from tools.strike_lab.current_battle_entry import NativeRun, SP, WORLD, PACKET_PAGE

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT.parent / 'God2/God2.exe'
CLIENT_SHA256 = 'c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575'
SOURCE = ROOT.parent.parent / 'God2-解殼EXE原始碼重建/decompiled/functions'
VISIBLE = 0x23000000
REGIONS = ((0x496990, 0x497030), (0x46ae9e, 0x46b022),
           (0x475e00, 0x476570), (0x4c7610, 0x4c7621),
           (0x4c7627, 0x4c7680), (0x47de06, 0x47e1d0), (0x45ff00, 0x460220),
           (0x531c10, 0x531c30), (0x4b2ae0, 0x4b2bf4), (0x4b2bf9, 0x4b3290),
           (0x4f7eb0, 0x4f8220), (0x4f89b0, 0x4f8f70),
           (0x4b12b0, 0x4b15d0), (0x47ebf0, 0x47ece0),
           (0x47f270, 0x47f3f0), (0x4c7520, 0x4c7610),
           (0x47dd60, 0x47ddc0), (0x45ac00, 0x45ac50))


def sha(data):
    return hashlib.sha256(data).hexdigest()


class ChatVM(Oracle):
    def __init__(self, raw, *, language=0, residue=0xa5):
        self.residue, self.boundaries, self.visits = residue, [], []
        self.stop_at = None
        super().__init__(raw)
        # Frozen display wrapper adds another native stack frame before the
        # original implementation; bounded scratch pages cover that nesting.
        self.vm.mem_map(STACK - 0x2000, 0x2000)
        self.vm.mem_map(VISIBLE, 0x10000)
        self.put(UI + 0x39de8, '<I', VISIBLE)
        self.put(UI + 0x232e10, '<h', -1)
        self.put(UI + 0x39e04, '<I', 15)
        self.put(ACTOR + 0x449c, '<H', 0x20)
        self.put(ACTOR + 0x3f98, '<I', 1)
        self.put(0x59dfd8, '<HH', 4, 2 if language else 0)
        self.helpers.update({0x47f6d0: 4, 0x47e380: 4, 0x47e1d0: 0})

    def cstr(self, address, limit=512):
        return self.read(address, limit).split(b'\0', 1)[0]

    def hook(self, vm, address, size, context):
        self.visits.append(address)
        if address == self.stop_at:
            vm.emu_stop()
            return
        esp = vm.reg_read(UC_X86_REG_ESP)
        if address in (0x475e00, 0x47de00):
            args = list(struct.unpack('<3I', self.read(esp + 4, 12)))
            self.boundaries.append({'function': f'{address:08X}', 'args': args})
        if address == 0x4fb690:
            raise AssertionError('Party mode unexpectedly reached native bubble consumer')
        if address == 0x547af7:
            ret, dst, fmt = struct.unpack('<3I', self.read(esp, 12))
            pattern = self.cstr(fmt)
            # CRT formatting is a declared boundary, not recovered server text
            # logic. Original x86 executes mode/filter/color and ring storage.
            require_tokens = pattern.count(b'%s')
            assert pattern.replace(b'%s', b'').find(b'%') < 0, pattern
            pointers = struct.unpack('<' + 'I' * require_tokens, self.read(esp + 12, 4 * require_tokens))
            output = pattern
            for pointer in pointers:
                output = output.replace(b'%s', self.cstr(pointer), 1)
            self.vm.mem_write(dst, output + b'\0')
            self.boundaries.append({'function': '00547AF7', 'format_va': f'{fmt:08X}',
                                    'format_hex': pattern.hex(), 'output_hex': output.hex(),
                                    'external_CRT_boundary_model': True})
            vm.reg_write(UC_X86_REG_EAX, len(output))
            vm.reg_write(UC_X86_REG_EIP, ret)
            vm.reg_write(UC_X86_REG_ESP, esp + 4)
            return
        super().hook(vm, address, size, context)

    def call(self, entry, *args, body=None):
        if body is not None:
            self.vm.mem_write(BODY, body)
        self.vm.mem_write(STACK, bytes([self.residue]) * 4096)
        self.put(STACK + 0x800, '<' + 'I' * (1 + len(args)), STOP, *args)
        self.vm.reg_write(UC_X86_REG_ECX, UI)
        self.vm.reg_write(UC_X86_REG_ESP, STACK + 0x800)
        self.vm.emu_start(entry, STOP, count=100000)
        assert self.vm.reg_read(UC_X86_REG_EIP) == STOP, hex(entry)
        assert self.vm.reg_read(UC_X86_REG_ESP) == STACK + 0x804 + 4 * len(args)

    def ring(self, address):
        count, oldest, nxt = struct.unpack('<3I', self.read(address + 0x67e8, 12))
        assert count <= 200 and oldest < 200 and nxt < 200
        return {'count': count, 'oldest': oldest, 'next': nxt,
                'rows': [{'channel': self.read(address + 0x6400 + i, 1)[0],
                          'color': self.u32(address + 0x64c8 + i * 4),
                          'text_hex': self.cstr(address + i * 128, 128).hex()}
                         for i in ((oldest + j) % 200 for j in range(count))]}


def dispatch_case(raw, language):
    n = NativeRun(raw)
    packet = bytearray(24)
    packet[0] = 0x5c
    struct.pack_into('<H', packet, 1, len(packet))
    struct.pack_into('<I', packet, 5, 513)
    packet[9] = 1 | (language << 7)
    packet[13:] = b'PartyProbe\0'
    n.put(PACKET_PAGE, bytes(packet))
    n.put(0x59dfd8, struct.pack('<HH', 4, 2 if language else 0))
    n.registers(esp=SP, ebp=WORLD, ebx=PACKET_PAGE)
    n.run(0x6ae96, ((0x6ae96, 0x6b022), (0x131c10, 0x131c30)), {0x75e00})
    sp = n.vm.reg_read(UC_X86_REG_ESP)
    ret, mode, pointer = struct.unpack('<3I', n.vm.mem_read(sp, 12))
    assert mode == 1 and pointer == PACKET_PAGE + 13
    assert 0xfb690 not in n.visits
    return {'language': language, 'packet_hex': bytes(packet).hex(), 'stop_va': '00475E00',
            'mode': mode, 'text_pointer': hex(pointer), 'text_offset': 13,
            'caller_return_va': f'{ret:08X}', 'bubble_consumer_visited': False,
            'instruction_count': len(n.visits)}


def current_dispatch_case(current, language):
    v = ChatVM(current, language=language)
    packet = bytearray(24)
    packet[0] = 0x5c
    struct.pack_into('<H', packet, 1, len(packet))
    struct.pack_into('<I', packet, 5, 513)
    packet[9] = 1 | (language << 7)
    packet[13:] = b'PartyProbe\0'
    v.vm.mem_write(BODY, bytes(packet))
    v.stop_at = 0x475e00
    v.put(STACK + 0x800, '<I', STOP)
    v.vm.reg_write(UC_X86_REG_ESP, STACK + 0x800)
    v.vm.reg_write(UC_X86_REG_EBP, UI - 0xa7f2f6c)
    v.vm.reg_write(UC_X86_REG_EBX, BODY)
    v.vm.emu_start(0x46ae96, STOP, count=100000)
    assert v.vm.reg_read(UC_X86_REG_EIP) == v.stop_at
    esp = v.vm.reg_read(UC_X86_REG_ESP)
    ret, mode, text = struct.unpack('<3I', v.read(esp, 12))
    assert mode == 1 and text == BODY + 13 and 0x714200 in v.visits and 0x70ff5b in v.visits
    assert 0x4fb690 not in v.visits
    return {'language': language, 'packet_hex': bytes(packet).hex(), 'mode': mode,
            'text_offset': 13, 'current_wrapper_visited': ['00714200', '0070FF5B'],
            'bubble_consumer_visited': False, 'stop_va': '00475E00', 'return_va': f'{ret:08X}'}


def build_report():
    raw = qualified_image()
    exe = EXE.read_bytes()
    assert sha(exe) == CLIENT_SHA256
    current = pefile.PE(data=exe).get_memory_mapped_image()
    intervals = []
    for start, end in REGIONS:
        a, b = start - 0x400000, end - 0x400000
        assert raw[a:b] == current[a:b], f'Current code changed at {start:X}'
        intervals.append({'start_va': f'{start:08X}', 'end_va_exclusive': f'{end:08X}',
                          'sha256': sha(raw[a:b]), 'current_exe_equal': True})
    pins = []
    for entry in ('00496990', '00475e00', '004c7610', '0047de00', '0045ff00',
                  '0047e0f0', '00531c10', '004b2ae0', '004f7eb0', '004f89b0',
                  '004b12b0', '0047ebf0', '0047f270', '004c7520', '0047f120'):
        path = SOURCE / f'{entry}_FUN_{entry}.c'
        pins.append({'path': str(path), 'sha256': sha(path.read_bytes())})
    producer = []
    for language in (0, 1):
        for target in (0, 0xffff, 0xff00):
            for selected, text in ((0, b'!PartyProbe'), (1, b'PartyProbe')):
                for residue in (0, 0xa5):
                    v = ChatVM(raw, language=language, residue=residue)
                    v.put(UI + 0x39e00, '<I', selected)
                    v.call(0x496990, BODY, 0, target, 0, body=text + b'\0')
                    assert len(v.queued) == 1
                    wire = v.queued[0]
                    assert wire[0] == 0x2f and struct.unpack_from('<H', wire, 1)[0] == len(wire)
                    assert wire[3] == 1 | (language << 7)
                    assert wire[4] == residue
                    assert struct.unpack_from('<H', wire, 5)[0] == target
                    assert wire[7:] == b'PartyProbe\0'
                    producer.append({'language': language, 'target_argument': target,
                                     'selected_channel': selected, 'input_hex': text.hex(),
                                     'stack_residue': residue, 'logical_hex': wire.hex(),
                                     'queue_call_visited': 0x4132e0 in v.visits})
    consumer = []
    for enabled in (False, True):
        for visible_mask in (0, 1, 2, 15):
            v = ChatVM(raw)
            v.put(ACTOR + 0x449c, '<H', 0x20 if enabled else 0)
            v.put(UI + 0x39e04, '<I', visible_mask)
            v.call(0x475e00, 1, BODY, body=b'PartyProbe\0')
            archive, visible = v.ring(UI + 0x39e20), v.ring(VISIBLE)
            assert archive['count'] == int(enabled)
            assert visible['count'] == int(enabled and bool(visible_mask & 2))
            for ring in (archive, visible):
                for row in ring['rows']:
                    assert row['channel'] == 1 and row['color'] == 0xff00
                    assert bytes.fromhex(row['text_hex']).endswith(b'PartyProbe')
            consumer.append({'option_bit20_enabled': enabled, 'visible_mask': visible_mask,
                             'archive': archive, 'visible': visible,
                             'filter_visited': 0x4c7610 in v.visits,
                             'channel1_display_visited': 0x47de00 in v.visits,
                             'bubble_consumer_visited': 0x4fb690 in v.visits,
                             'display_boundary': [r for r in v.boundaries if r['function'] == '0047DE00'],
                             'formatting_boundary': [r for r in v.boundaries if r['function'] == '00547AF7']})
    dispatch = [dispatch_case(raw, language) for language in (0, 1)]
    current_dispatch = [current_dispatch_case(current, language) for language in (0, 1)]
    current_consumer = []
    for enabled in (False, True):
        for mask in (0, 1, 2, 15):
            v = ChatVM(current)
            v.put(ACTOR + 0x449c, '<H', 0x20 if enabled else 0)
            v.put(UI + 0x39e04, '<I', mask)
            v.call(0x475e00, 1, BODY, body=b'PartyProbe\0')
            archive, visible = v.ring(UI + 0x39e20), v.ring(VISIBLE)
            assert archive['count'] == int(enabled)
            assert visible['count'] == int(enabled and bool(mask & 2))
            if enabled:
                assert 0x70f9b6 in v.visits and 0x70ff41 in v.visits
            for ring in (archive, visible):
                assert all(row['channel'] == 1 and row['color'] == 0xff00 for row in ring['rows'])
            current_consumer.append({'option_bit20_enabled': enabled, 'visible_mask': mask,
                                     'archive': archive, 'visible': visible,
                                     'frozen_wrapper_executed': enabled,
                                     'bubble_consumer_visited': 0x4fb690 in v.visits})
    frozen = [ROOT / 'src/protocol/RecoveredChat.h', ROOT / 'tools/strike_lab/current_party_20261002.py']
    return {'format': 'native-party-chat-20261003-v1', 'native_image_sha256': IMAGE_SHA256,
            'current_exe_sha256': CLIENT_SHA256, 'code_intervals': intervals, 'source_pins': pins,
            'current_build_detours': [
                {'start_va': f'{start:08X}', 'end_va_exclusive': f'{end:08X}',
                 'original_hex': raw[start-0x400000:end-0x400000].hex(),
                 'current_hex': current[start-0x400000:end-0x400000].hex(),
                 'note': note}
                for start,end,note in (
                    (0x46ae96,0x46ae9e,'Frozen receiver wrapper jumps714200; ordinary non-ST packet returns46AE9E after531C10.'),
                    (0x47de00,0x47de06,'Frozen display wrapper jumps70F9B6; mode1 uses70FB41→70FF41 original-function trampoline.'),
                    (0x4c7621,0x4c7627,'Frozen common-channel filter wrapper70A0DA; partychannel1 branch is unchanged.'),
                    (0x4b2bf4,0x4b2bf9,'Frozen input helper detour70BC59→70B415; ordinary producer caller later suppliesparam3=0.'))],
            'counts': {'producer': len(producer), 'consumer': len(consumer), 'dispatch': len(dispatch),
                       'current_dispatch': len(current_dispatch), 'current_consumer': len(current_consumer)},
            'producer_cases': producer, 'consumer_cases': consumer, 'dispatch_cases': dispatch,
            'current_dispatch_cases': current_dispatch, 'current_consumer_cases': current_consumer,
            'current_wrapper_pins': [{'start_va': f'{a:08X}', 'end_va_exclusive': f'{b:08X}',
                                      'sha256': sha(current[a-0x400000:b-0x400000])}
                                     for a,b in ((0x714200,0x714223),(0x70ff5b,0x71010e),
                                                 (0x70f9b6,0x70fb61),(0x70ff41,0x70ff5b))],
            'c2s': {'opcode': '2F', 'length_word_offsets': [1, 2], 'mode_offset': 3,
                    'mode_low7': 1, 'language_highbit': '531C10:locale WORDs0059DFD8=4 and0059DFDA=2 ->1; otherwise0',
                    'opaque_pad_offset': 4, 'target_word_offsets': [5, 6], 'text_offset': 7,
                    'target_authority': 'param3 overrides earlierFF00; normal typed Enter caller4B2AE0 supplies0; F7EB0/F89B0 item-link callers supplyFFFF. No universalFF00 validation.',
                    'prefix': '! stripsonebyte andrequiresnonempty nativeparty roster; selectedchannelUI+39E00=1 emitsmode1withoutprefix.'},
            's2c': {'opcode': '5C', 'mode_offset': 9, 'language_highbit': True,
                    'sender_dword_offset': 5, 'text_offset': 13,
                    'consumer': '46AE96 ->475E00(mode1) ->4C7610(option20) ->47DE00(channel1,colorFF00)',
                    'bubble': 'Mode1 jumps46B00A directly;4FB690 isonly reached inmode0/6 branch.',
                    'rings': 'Enabledpartychat archived atUI+39E20 withchannel1; visibleUI+39DE8 onlywhenUI+39E04&2 andprivate-view39E18==0. Ringchannel bytes+6400 andcolorDWORDs+64C8+i*4.'},
            'normal_ui': {
                'typed_chat': 'Click native chat edit, typeASCII !token then Enter (normal4B2AE0→496990(text,0,0,0)); acceptedparty roster requiredfor!prefix.',
                'channel_selection': '4B12B0(1,1) requiresrosterCount>0 andsetsUI+39E00=1/colorFF00. Mainmenu4A6760(mode2) control31 choosesparty; commoncontrol30. Chatfilterwidget232E10 control11 withSHIFT (418300(0x10)) choosespartyinput; withoutSHIFT togglesvisiblepartybit2 through47ECE0→47EBF0.',
                'visibility': 'Read actor+449C optionbit20; settingspanel callback4C7520 control6,event20 togglesit andsendsacceptedoptions1D. ReadUI+39E04&2 visiblepartymask; chatfilterwidget232E10 control11 release,event20 togglesbit2; commoncontrol10 bit1.',
                'coordinates': 'Use dynamicnativehitrect: controlentryUI+E2170+widget*2A08+8B8+index*100; signedhitWORD+8; managerDWORD UI+E2174; rectDWORDs manager+hit*24+[4,8,12,16]. Usewindowlocal200/201/202 withframegaps.',
                'item_links': 'F7EB0/F89B0 generateitem-linktext andsupplyFFFF; theyare not ordinaryplaintextinput.'},
            'frozen_source_snapshot': [{'path': str(p), 'sha256': sha(p.read_bytes())} for p in frozen],
            'scope': 'Original x86 mode,language,target,pad,filter,color,ringwrites executed. CRT%s formatting andUIredraw are modeled/observedboundaries. No liveclient,server,pixels,network orDB acceptance.',
            'open_limits': ['Cross-language52F500 conversion not executed bydispatchcases; matchinglocale cases only.',
                            'Frozen currentclient receiver/display wrappers are additionally executed againstexactc5d8mappedEXE forordinarymode1; livecurrentclient acceptance remainsrequired.',
                            'Normal UIactions are source-pinned; hidden realwindow input/liveacceptance remainsrequired.',
                            'Originalserver partybroadcast authorization,offline-members andcross-map scope areunknown; requireseparateCUSTOMpolicy.',
                            'No native bubble should be expectedforparty mode1; visible/archive ringsare theconsumerproof.'],
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
