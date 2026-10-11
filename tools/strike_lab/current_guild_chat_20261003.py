"""Build-pinned offline guild chat and S2C guild-name x86 qualification.

Executes actual producer, dispatch, filter and ring writes. Win32 rectangle and
widget redraw functions are explicitly modeled boundaries; no live processes,
network, database, client-byte modifications or rendered pixels are involved.
"""
import argparse
import json
import struct
from pathlib import Path

import pefile
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EBP, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP
from tools.strike_lab.current_party_chat_20261003 import ChatVM, ROOT, EXE, SOURCE, CLIENT_SHA256, IMAGE_SHA256, UI, STACK, BODY, STOP, ACTOR, VISIBLE, REGIONS, sha
from tools.strike_lab.current_protocol_coverage import qualified_image, NativeLengths

WORLD = UI - 0xa7f2f6c
WORLD_GUILD = WORLD + 0x153968d2
WORLD_GRAPHIC = WORLD + 0x1539ad80


class GuildVM(ChatVM):
    def __init__(self, raw, **kwargs):
        super().__init__(raw, **kwargs)
        self.vm.mem_map(WORLD_GUILD & ~4095, 0x6000)
        self.put(WORLD_GRAPHIC, '<i', -1)
        # Pure redraw/widget boundaries only; native selection guards/writes,
        # name copies, mode selection, colors, filters and rings still execute.
        self.helpers.update({0x5077c0: 0, 0x5059f0: 36, 0x5068c0: 16,
                             0x5073e0: 8, 0x4b2160: 4, 0x507850: 12,
                             0x4c7680: 0, 0x47f120: 4})
        self.put(0x5706c4, '<I', STOP + 32)
        self.put(0x5706c8, '<I', STOP + 48)

    def hook(self, vm, address, size, context):
        esp = vm.reg_read(UC_X86_REG_ESP)
        if address in (STOP + 32, STOP + 48):
            ret = self.u32(esp)
            if address == STOP + 32:
                dst, src = struct.unpack('<2I', self.read(esp + 4, 8))
                vm.mem_write(dst, self.read(src, 16))
                cleanup = 8
                label = 'Win32 CopyRect'
            else:
                dst, x, y = struct.unpack('<Iii', self.read(esp + 4, 12))
                rect = struct.unpack('<4i', self.read(dst, 16))
                self.put(dst, '<4i', rect[0] + x, rect[1] + y, rect[2] + x, rect[3] + y)
                cleanup = 12
                label = 'Win32 OffsetRect'
            self.boundaries.append({'function': label, 'external_rectangle_boundary_model': True})
            vm.reg_write(UC_X86_REG_EAX, 1)
            vm.reg_write(UC_X86_REG_EIP, ret)
            vm.reg_write(UC_X86_REG_ESP, esp + 4 + cleanup)
            return
        if address in self.helpers:
            self.boundaries.append({'function': f'{address:08X}',
                                    'args': list(struct.unpack('<4I', self.read(esp + 4, 16))),
                                    'external_widget_boundary_model': True})
        super().hook(vm, address, size, context)

    def update_guild(self, name):
        assert len(name) <= 15 and b'\0' not in name
        logical = b'\x2d' + (name + b'\0').ljust(16, b'\0')
        self.vm.mem_write(BODY, logical)
        self.stop_at = 0x46b517
        self.put(STACK + 0x800, '<I', STOP)
        self.vm.reg_write(UC_X86_REG_ESP, STACK + 0x800)
        self.vm.reg_write(UC_X86_REG_EBP, WORLD)
        self.vm.reg_write(UC_X86_REG_EAX, BODY)
        self.vm.emu_start(0x468b4c, STOP, count=100000)
        assert self.vm.reg_read(UC_X86_REG_EIP) == self.stop_at
        self.stop_at = None
        assert self.cstr(ACTOR + 6) == name
        assert self.cstr(WORLD_GUILD) == name
        assert 0x469e49 in self.visits and 0x4e7180 in self.visits
        return {'logical_hex': logical.hex(), 'logical_length': len(logical),
                'entry_va': '00468B4C', 'switch_table_va': '0046B5D4',
                'dispatch_branch_va': '00469E49', 'consumer_va': '004E7180',
                'world_name_hex': self.cstr(WORLD_GUILD).hex(),
                'actor_name_hex': self.cstr(ACTOR + 6).hex(),
                'native_widget_refresh_5077C0_observed': any(x['function'] == '005077C0' for x in self.boundaries)}


def dispatch(image, language):
    v = GuildVM(image, language=language)
    text = b'Leader: GuildProbe'
    logical = bytearray(14 + len(text))
    logical[0] = 0x5c
    struct.pack_into('<H', logical, 1, len(logical))
    struct.pack_into('<I', logical, 5, 513)
    logical[9] = 3 | language << 7
    logical[13:] = text + b'\0'
    v.vm.mem_write(BODY, bytes(logical))
    v.stop_at = 0x475e00
    v.put(STACK + 0x800, '<I', STOP)
    v.vm.reg_write(UC_X86_REG_ESP, STACK + 0x800)
    v.vm.reg_write(UC_X86_REG_EBP, WORLD)
    v.vm.reg_write(UC_X86_REG_EBX, BODY)
    v.vm.emu_start(0x46ae96, STOP, count=100000)
    assert v.vm.reg_read(UC_X86_REG_EIP) == v.stop_at
    ret, mode, ptr = struct.unpack('<3I', v.read(v.vm.reg_read(UC_X86_REG_ESP), 12))
    assert mode == 3 and ptr == BODY + 13 and 0x4fb690 not in v.visits
    return {'language': language, 'logical_hex': bytes(logical).hex(),
            'consumer_mode': mode, 'text_offset': 13, 'return_va': f'{ret:08X}',
            'bubble_consumer_visited': False,
            'current_receiver_wrappers_visited': [f'{a:08X}' for a in (0x714200, 0x70ff5b) if a in v.visits]}


def build_report():
    original = qualified_image()
    exe = EXE.read_bytes()
    assert sha(exe) == CLIENT_SHA256
    current = pefile.PE(data=exe).get_memory_mapped_image()
    extra = ((0x468b4c, 0x468b68), (0x46b5d4, 0x46b9cc),
             (0x469e49, 0x469e99), (0x4e7180, 0x4e71d8),
             (0x4b147b, 0x4b15d0), (0x4b2190, 0x4b21ad),
             (0x497d80, 0x497da0))
    intervals = []
    for start, end in REGIONS + extra:
        a, b = start - 0x400000, end - 0x400000
        assert original[a:b] == current[a:b], f'Code changed at {start:X}'
        intervals.append({'start_va': f'{start:08X}', 'end_va_exclusive': f'{end:08X}',
                          'sha256': sha(original[a:b]), 'current_exe_equal': True})
    lengths = {f'{op:02X}': NativeLengths(original).query(op)[0] for op in (0x2d, 0x5c)}
    assert lengths['2D'] == 17
    table_entry = struct.unpack_from('<I', original, 0x46b5d4 - 0x400000 + 4 * 0x2d)[0]
    assert table_entry == 0x469e49
    updates, producers, consumers, dispatches, selections, lifecycle, controls = [], [], [], [], [], [], []
    for build, image in (('original', original), ('current', current)):
        for name in (b'', b'GuildA', b'ABCDEFGHIJKLMNO', '仙界傳'.encode('cp950'), '仙界传'.encode('cp936')):
            v = GuildVM(image)
            # Always exercise actual S2C dispatch, never direct Actor+6 writes.
            update = v.update_guild(name)
            updates.append({'build': build, 'name_hex': name.hex(), **update})
            v.call(0x4b12b0, 1, 2)
            selected = v.u32(UI + 0x39e00)
            result = v.vm.reg_read(UC_X86_REG_EAX)
            assert selected == (2 if name else 0) and result == bool(name)
            selections.append({'build': build, 'guild_name_hex': name.hex(),
                               'selection_return': result, 'selected_channel': selected,
                               'native_actor_name_gate': True, 'widget_boundaries': v.boundaries})
        v = GuildVM(image)
        v.update_guild(b'GuildA')
        v.call(0x4b12b0, 1, 2)
        assert v.u32(UI + 0x39e00) == 2
        clear = v.update_guild(b'')
        assert v.u32(UI + 0x39e00) == 2
        v.call(0x4b12b0, 1, 2)
        assert v.vm.reg_read(UC_X86_REG_EAX) == 0 and v.u32(UI + 0x39e00) == 2
        v.call(0x496990, BODY, 0, 0, 0, body=b'AfterLeaveProbe\0')
        assert v.queued[-1][3] == 3 and v.queued[-1][7:] == b'AfterLeaveProbe\0'
        lifecycle.append({'build': build, 'clear_update': clear,
                          'selected_input_after_native_clear': 2,
                          'reselect_empty_returns': 0, 'after_clear_logical_hex': v.queued[-1].hex(),
                          'server_must_reject_without_membership': True,
                          'no_client_native_automatic_common_input_reset': True})
        v = GuildVM(image)
        v.put(ACTOR + 0x449c, '<H', 0x30)
        v.call(0x4c7520, 7, 0x20)
        assert v.read(ACTOR + 0x449c, 2) == b'\x70\x00' and v.queued == [b'\x1d\x70\x00']
        v.call(0x4c7520, 7, 0x20)
        assert v.read(ACTOR + 0x449c, 2) == b'\x30\x00' and v.queued[-1] == b'\x1d\x30\x00'
        v.put(UI + 0x39e04, '<I', 3)
        v.call(0x47ebf0, 12)
        assert v.u32(UI + 0x39e04) == 7
        v.call(0x47ebf0, 12)
        assert v.u32(UI + 0x39e04) == 3
        controls.append({'build': build, 'settings_event_control': 7,
                         'settings_event_flags': 0x20, 'native_c2s_options_records': [x.hex() for x in v.queued],
                         'visible_filter_control': 12, 'visible_mask_sequence': [3, 7, 3],
                         'native_497D80_and_47EBF0_executed': True})
        for language in (0, 1):
            dispatches.append({'build': build, **dispatch(image, language)})
            for name in (b'', b'GuildA'):
                for word in (0, 0xffff, 0xff00):
                    for residue in (0, 0xa5):
                        for selected, text in ((0, b'#GuildProbe'), (2, b'GuildProbe'), (2, b'#GuildProbe')):
                            v = GuildVM(image, language=language, residue=residue)
                            v.update_guild(name)
                            # Synthetic selected=2 when empty name tests server's
                            # need for membership authority: producer alone trusts
                            # this state although normal UI selector rejects it.
                            v.put(UI + 0x39e00, '<I', selected)
                            v.call(0x496990, BODY, 0, word, 0, body=text + b'\0')
                            assert len(v.queued) == 1
                            logical = v.queued[0]
                            mode = 3 if selected == 2 or name else 0
                            expected = text[1:] if text[:1] == b'#' and name else text
                            assert logical[0] == 0x2f and len(logical) == struct.unpack_from('<H', logical, 1)[0]
                            assert logical[3] == mode | language << 7 and logical[4] == residue
                            assert struct.unpack_from('<H', logical, 5)[0] == word and logical[7:] == expected + b'\0'
                            producers.append({'build': build, 'language': language,
                                              'guild_name_hex': name.hex(), 'selected_channel': selected,
                                              'caller_word': word, 'stack_residue': residue,
                                              'input_hex': text.hex(), 'mode': mode, 'logical_hex': logical.hex(),
                                              'synthetic_selected_empty_membership': not name and selected == 2,
                                              'queue_4132E0_visited': 0x4132e0 in v.visits})
        for options in (0, 0x20, 0x40, 0x70):
            for mask in (0, 1, 2, 4, 15):
                for private_view in (0, 1):
                    v = GuildVM(image)
                    v.put(ACTOR + 0x449c, '<H', options)
                    v.put(UI + 0x39e04, '<I', mask)
                    v.put(UI + 0x39e18, '<B', private_view)
                    v.call(0x475e00, 3, BODY, body=b'Leader: GuildProbe\0')
                    archive, visible = v.ring(UI + 0x39e20), v.ring(VISIBLE)
                    assert archive['count'] == bool(options & 0x40)
                    assert visible['count'] == bool(options & 0x40 and mask & 4 and not private_view)
                    for ring in (archive, visible):
                        assert all(row['channel'] == 3 and row['color'] == 0xffff00 for row in ring['rows'])
                    assert 0x4fb690 not in v.visits
                    consumers.append({'build': build, 'options': options, 'visible_mask': mask,
                                      'private_view_39E18': private_view, 'archive': archive, 'visible': visible,
                                      'native_filter_4C7610_visited': 0x4c7610 in v.visits,
                                      'native_display_47DE00_visited': 0x47de00 in v.visits,
                                      'current_display_wrappers_visited': [f'{a:08X}' for a in (0x70f9b6, 0x70ff41) if a in v.visits],
                                      'bubble_consumer_visited': False})
    pins = []
    for entry in ('00496990', '00475e00', '004c7610', '0047de00', '00468ae0', '004e7180', '004b12b0', '004b2190', '0047f270', '004c7520', '00497d80'):
        path = SOURCE / f'{entry}_FUN_{entry}.c'
        pins.append({'path': str(path), 'sha256': sha(path.read_bytes()), 'analysis_only': True})
    private_report = json.loads((ROOT / 'artifacts/research/native-private-chat-20261003/native.json').read_text(encoding='utf-8'))
    return {'format': 'native-guild-chat-20261003-v1', 'native_image_sha256': IMAGE_SHA256,
            'current_exe_sha256': CLIENT_SHA256, 'native_lengths': lengths,
            'code_intervals': intervals, 'source_pins': pins,
            'current_build_detours': private_report['current_build_detours'],
            'current_wrapper_pins': private_report['current_wrapper_pins'],
            'imported_oracle_pins': [{'path': str(p), 'sha256': sha(p.read_bytes())} for p in
                                    (ROOT / 'tools/strike_lab/current_party_chat_20261003.py',
                                     ROOT / 'tools/strike_lab/current_party_20261002.py',
                                     ROOT / 'tools/strike_lab/current_protocol_coverage.py')],
            'counts': {'guild_name_update': len(updates), 'channel_selection': len(selections),
                       'producer': len(producers), 'consumer': len(consumers), 'dispatch': len(dispatches),
                       'guild_clear_selected_lifecycle': len(lifecycle), 'native_options_and_filter_controls': len(controls)},
            'guild_name_update_cases': updates, 'channel_selection_cases': selections,
            'guild_clear_selected_lifecycle_cases': lifecycle,
            'native_options_and_filter_control_cases': controls,
            'producer_cases': producers, 'consumer_cases': consumers, 'dispatch_cases': dispatches,
            'c2s': {'opcode': '2F', 'mode_low7': 3, 'language_offset': 3, 'opaque_residue_offset': 4,
                    'caller_word_offsets': [5, 6], 'text_offset': 7,
                    'membership_guard': '# prefix requires nonempty Actor+6 guild-name string; selectedUI39E00=2 sendsmode3 without rechecking name. Normal UI4B12B0(1,2) doescheckname.',
                    'caller_word_authority': 'Normal typed caller supplies0; FFFF/FF00 preserved. Not guildID and not authorization.'},
            's2c': {'chat_opcode': '5C', 'sender_dword_offset': 5, 'mode_offset': 9, 'text_offset': 13,
                    'channel': 3, 'native_color': '00FFFF00', 'reception_option': 'Actor+449C WORD bit40',
                    'visible_mask': 'UI+39E04 bit4', 'private_view': 'UI+39E18 must be0 for visible ring',
                    'no_bubble': True, 'guild_name_opcode': '2D', 'guild_name_logical_length': 17,
                    'guild_name_field': 'offset1 fixed16 bytes, NUL terminated (maximum15 encoded bytes)',
                    'guild_name_dispatch': '468B4C→switch46B5D4[2D]=469E49→4E7180',
                    'name_copies': 'World+153968D2 then Actor+6; 5077C0 widget refresh',
                    'guild_name_authority': 'Client display/producer gating only; actual group membership and audience must be independently server-owned.'},
            'normal_ui': {'select_input': 'Shift+chatfilter control12 invokes4B12B0(1,2); noShift togglesguildvisiblebit4 via47ECE0.',
                          'receive_option': 'Settingsgroup22 control7 releaseevent20 togglesActor449C bit40 and emitsacceptedoptions1D.',
                          'guild_name_population': 'Server sends2D opcode+fixed16byte actualownedguildname on entry and membership changes. Empty name clearsnativeguildinputguard.'},
            'scope': 'Offline original/current x86 execution only. Rectangle imports, widget redraw helpers, CRT%s formatting and queue transport are declared boundaries. No live-client/server/database/pixel acceptance.',
            'open_limits': ['Original server group creation/admission/ranks/permissions unknown; guild-name display is not membership authority.',
                            'Initial snapshot guild-name source beyond explicit2D update not traced; 2D authoritativeclientupdate proven.',
                            'Cross-language conversion52F500 not executed; matchinglocale dispatch only.',
                            'UI source-pinned selector call is executed with widget redraw boundaries; real hidden-window input remainsrequired.',
                            'No original guildID encoded in2F mode3; authoritative audience requires fresh server membership rows.'],
            'oracle_source_sha256': sha(Path(__file__).read_bytes()),
            'current_client_accepted': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    report = json.dumps(build_report(), ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding='utf-8')
        print(f'wrote {args.output}')
    else:
        print(report, end='')
