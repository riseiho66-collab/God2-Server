"""Bounded OFFLINE native trade world-hit investigation.

Reads current EXE, qualified original image and frozen run06 receipts only.
Writes NEW evidence. No process open, UI input, native call, memory write,
network connection, emulator or authority claim about unobserved live guards.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import private_peer_pose_20261002 as source

OUT = ROOT / 'artifacts/research/native-trade-world-hit-20261003'
RUN = ROOT / 'artifacts/playtests/private-native-blackbox-trade-armor-projection-20261002-06'
SPANS = (
    ('mouse_message_dispatch', 0x418950, 0x208),
    ('mouse_registry', 0x418b80, 0x190),
    ('actor_hit_cache_producer', 0x50aa20, 0x398),
    ('actor_hit_cache_getters', 0x50b220, 0x190),
    ('remote_actor_events', 0x4fb290, 0x1be),
    ('world_frame_actor_dispatch', 0x466b00, 0x480),
    ('world_action_trade_branch', 0x465fa0, 0x108),
    ('ui_event_translation', 0x481f70, 0x128),
    ('cursor_reset', 0x4834e0, 0x48),
    ('cursor4_mouse_translation', 0x4835a0, 0xb0),
    ('native29_producer', 0x49de30, 0x11),
    ('native29_argument_packer', 0x497250, 0x36),
    ('queue_and_flush', 0x4132e0, 0xf7),
    ('global_lock_early_guard', 0x4b2ae0, 0x24),
    ('generic_ui_lock_early_guard', 0x4aacd0, 0x22),
    ('window_mouse_forwarder', 0x40e6f7, 0x24),
    ('actor_rectangle_move', 0x50a890, 0x79),
    ('actor_rectangle_move_full', 0x50a610, 0x278),
    ('actor_visibility_registry', 0x50b0b0, 0xf5),
    ('DATA_mouse_message_jump_table', 0x418b58, 28),
    ('DATA_ui_event_jump_table', 0x48205c, 60),
    ('DATA_world_action_jump_table', 0x46643c, 80),
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    # This helper qualifies only source identity and a small existing span set.
    # Every additional relevant span is explicitly qualified below.
    original = source.qualify_source()
    current = pefile.PE(str(source.base.LIVE)).get_memory_mapped_image()
    code = []
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    disassembly = []
    for name, va, size in SPANS:
        rva = va - 0x400000
        raw = original[rva:rva + size]
        assert raw == current[rva:rva + size], f'CURRENT_SPAN_CHANGED:{name}'
        code.append({'name': name, 'va': hex(va), 'size': size,
                     'original_sha256': hashlib.sha256(raw).hexdigest(),
                     'current_equal_original': True, 'raw_hex': raw.hex()})
        disassembly.append(f'\n{name} {va:08X} size={size}\n')
        # Jump table bytes in a containing span are data, not instructions.
        if name.startswith('DATA_'):
            disassembly += [f'{va+i*4:08X} DWORD {value:08X}\n'
                            for i, value in enumerate(struct.unpack('<'+'I'*(size//4), raw))]
        else:
            disassembly += [f'{i.address:08X} {i.bytes.hex():24s} {i.mnemonic} {i.op_str}\n'
                            for i in decoder.disasm(raw, va)]

    receipt_paths = [RUN/'ui-result.json', RUN/'run-result.json']
    receipt_before = {str(p.relative_to(ROOT)): sha(p) for p in receipt_paths}
    ui = json.loads(receipt_paths[0].read_text('utf-8'))
    checkpoints = []
    for index in range(214, 222):
        e = ui['events'][index]
        assert e['source'] == 5 and e['intended_target'] == 4
        own = next(x for x in e['trade_native'] if x['identity'] == 5)
        remote = e['actual_remote_peer']
        assert remote['identity'] == 4
        mouse = bytes.fromhex(e['input_mouse_12000_12034'])
        checkpoints.append({
            'event_index': index, 'phase': e['phase'],
            'source_world': e['source_world'], 'target_world': e['target_world'],
            'click': e['click'], 'queue_length': e['queue_length'],
            'queue_prefix10_stale_when_length0': e['queue_prefix'][:20],
            'actual_visible_widget_hits': e['actual_visible_widget_hits'],
            'remote': {k: remote[k] for k in ('identity','slot','world','entry','renderer','x','y','movement','status','live_components')},
            'cursor4': own['cursor_mode_232f36'],
            'global_input_lock': own['global_input_lock_232f68'],
            'generic_input_mode': own['generic_input_mode_5bfa4'],
            'selected_bag_slot': own['selected_bag_slot_855f0'],
            'trade_active': own['active'],
            'mouse_current_xy': list(struct.unpack_from('<hh', mouse)),
            'mouse_event_flags_sampled_after_gesture': {
                hex(0x12000 + off): struct.unpack_from('<I', mouse, off)[0]
                for off in (0x10,0x14,0x18,0x1c,0x20,0x24,0x28,0x2c)},
        })
    world = checkpoints[0]['source_world']['world']
    renderer = checkpoints[0]['remote']['renderer']
    display = world + 0xaba32e0
    node = display + 0x1c + renderer*0xa7e0
    wm_targets = [hex(struct.unpack_from('<I', original, 0x418b58-0x400000 + i*4)[0]) for i in range(7)]
    assert wm_targets == ['0x41896c','0x4189ec','0x418a8c','0x418ac8','0x418a72','0x418aaa','0x418b48']
    assert struct.unpack_from('<I', original, 0x46643c-0x400000 + 18*4)[0] == 0x466068
    assert struct.unpack_from('<I', original, 0x48205c-0x400000 + 2*4)[0] == 0x481fdd
    result = {
        'scope': 'OFFLINE_READ_ONLY_PRODUCER_BRANCH_MAP_NOT_LIVE_ACCEPTANCE',
        'emulator_used': False, 'emulator_is_authority': False,
        'current_client': str(source.base.LIVE), 'current_client_sha256': sha(source.base.LIVE),
        'original_mapped_sha256': hashlib.sha256(original).hexdigest(),
        'tool_sha256': sha(__file__), 'code_spans': code,
        'code_span_count': len(code), 'code_bytes': sum(x[2] for x in SPANS),
        'run06_receipts_sha256': receipt_before,
        'run06_checkpoint_subset': checkpoints,
        'mouse_wm200_through206_table': wm_targets,
        'event_minus6_table_branch': '0x466068',
        'ui_event3_table_branch': '0x481fdd',
        'wm_flag_semantics_verified_from_table_not_variable_names': {
            'WM201_primary_down': '4189EC->418A60 sets mouse+1202C=1 after inclusive rectangle scan',
            'WM202_primary_up': '418A8C->418A90/96 clears mouse+1202C and +12014, sets +12020=1',
            'WM203_primary_double': '418AC8->418B3C sets +12014=1 after rectangle scan',
            'WM204_secondary_down': '418A72 sets +12018=1 and +12024=0',
            'WM205_secondary_up': '418AAA clears +12018/+1201C and sets +12024=1',
            'WM206_secondary_double': '418B48 sets +1201C=1',
            'important': 'Do not label +12018 as left-up or +12020 as right-down. Actual WM dispatch table disproves those earlier labels.',
        },
        'source_tool_callcontext': {
            'frozen_trade_tool': 'tools/strike_lab/private_trade_armor_projection_20261002_v06.py',
            'frozen_trade_tool_sha256': sha(ROOT/'tools/strike_lab/private_trade_armor_projection_20261002_v06.py'),
            'world_click_line243': 'click(source HWND, px, py-26, interval=.03)',
            'frozen_click_helper': 'tools/strike_lab/private_potion_ui.py',
            'frozen_click_helper_sha256': sha(ROOT/'tools/strike_lab/private_potion_ui.py'),
            'helper_lines48_54': 'WM200 -> interval -> WM201 -> interval -> WM202 -> interval; scales 800x600 to ClientRect',
            'necessity_not_confirmed_root_cause': 'WM201 press flag must survive until world frame/cache producer. WM202 clears that flag. run06 30ms down interval has no during-press frame/cache snapshot; cannot prove it missed the frame.',
        },
        'next_read_contract': {
            'source_world_from_run06_only': hex(world),
            'remote_manager': hex(world+0x15383410),
            'remote_display': hex(display), 'remote_renderer_index': renderer,
            'node_base': hex(node), 'node_active_dword': hex(node),
            'node_hit_id_dword': hex(node+0x10), 'node_category_dword': hex(node+0xa7d0),
            'display_node_count_dword': hex(display+0xa7e001c),
            'mouse_pointer_dword': hex(display+8),
            'cache_base_category0': hex(display+0xa7e005a),
            'cache_7categories_6words_each': 'category*12; WM201+0 WM204+2 WM203+4 WM202+6 WM205+8 hover+10',
            'registry': 'mouse + signed_hit_id*24; active DWORD+0; left/top/right/bottom signed DWORD+4/+8/+C/+10; inside DWORD+14',
            'guard': '0<=hit_id<0xC00; active==1; inside!=0; node.active==2; category<4 for 4FB290',
            'warning': 'These are run06 address derivations, not captured values. Re-resolve world/display/mouse/node in any later authorized live handle.',
        },
        'unknown_live_guard': 'Run06 did not capture actor-node hit ID, registered rectangle/inside, real display hit caches, 4820A0 routing output, or 481F70/4FB290 return values. No unique failing branch proven.',
        'retracted_claims': [
            'W+1539689C/AC/BC are hit arrays: false; they are target detail output buffers in 465FFD->4FAC70.',
            'No visible UI widget hit proves actor body hit: false; separate mouse registry and display cache.',
            'Global input lock or selected drag caused run06: unsupported; recorded lock0/selected-1.',
            'Sprite alpha/animation caused run06: unsupported; 418CD0 checks rectangle registry, no pixel alpha test.',
            'The chosen feet-minus26 point is native body hit geometry: unsupported.',
            'Stale buffer prefix with queue_length0 is a fresh request: false; 4133B9 clears only length.',
            'WM202 sets +12018, WM204 clears +1202C: false; the exact table gives the opposite mapping.',
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'oracle.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    (OUT/'qualified-native-disassembly.txt').write_text(''.join(disassembly),'utf-8')
    assert receipt_before == {str(p.relative_to(ROOT)): sha(p) for p in receipt_paths}
    print(json.dumps({'output': str(OUT/'oracle.json'), 'code_spans': len(code),
                      'code_bytes': result['code_bytes'], 'all_spans_equal': True,
                      'receipt_unchanged': True, 'no_ui_started': True}))


if __name__ == '__main__':
    main()
