"""Read-only build-matched clone bridge ABI/stolen-instruction evidence.

CUSTOM-0058: these checks establish addresses/signatures, not live acceptance.
"""
from pathlib import Path
import hashlib
import json
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = Path(__file__).resolve().parents[3]
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
HOOKS = {
    0x432a20: ('renderer_present_direct_COM_and_screen_paths', 8, '568bf1e8d80efdff', 0x432a90, 0),
    0x524820: ('bull150_generic_skill_tick', 6, '83ec14535556', 0x525140, 4),
    0x53ca50: ('final_screen_present_bull150_whole_ui_shake', 5, '83ec505356', 0x53cc20, 12),
    0x4327a0: ('battle_background_capture', 5, '568bf16a00', 0x432810, 4),
    0x432810: ('battle_background_restore_before_draw', 5, '53568bf157', 0x432910, 4),
    0x53dd40: ('DD_screen_rebuild_generation', 6, '81ec04010000', 0x53e090, 16),
    0x41c360: ('native_ACT_step_parent_scope', 5, '83ec185355', 0x41cce5, 4),
    0x41b9c0: ('native_ACT_independent_emit', 8, '515355568b742414', 0x41bc90, 40),
    0x41b330: ('native_ACT_release_ownership', 5, '538bd95556', 0x41b4f0, 4),
    0x426ab0: ('before_native_display_traversal', 5, '538b5c2408', 0x426b30, 4),
    0x518e50: ('custom_target_submit_guard', 8, '83ec10538a5c2418', 0x519330, 16),
    0x5154e0: ('custom_target_setup', 6, '515355568bf1', 0x515670, 4),
    0x513080: ('custom_target_input', 7, '83ec2055568bf1', 0x513ce0, 4),
    0x516ae0: ('skill_resource_preload', 6, '81ec34010000', 0x5171b0, 4),
    0x52c520: ('skill_result', 7, '8b44240c83ec08', 0x52ccd0, 20),
    0x529020: ('battle_frame', 7, '83ec0c8b442414', 0x529610, 8),
    0x51fc40: ('battle_reset', 6, '83ec10538bd9', 0x51fde0, 0),
    0x427400: ('display_reset', 8, '51535657894c240c', 0x427450, 0),
}
APIS = {
    0x426b30: ('native_single_display_entry_damage_overlay', 0x426cf0, 16),
    0x5156a0: ('current_skill_definition', 0x5156e0, 4),
    0x518e50: ('native_selection_submit', 0x519330, 16),
    0x512620: ('native_selection_cancel_to_attack', 0x512760, 0),
    0x511e10: ('native_target_highlights', 0x5120b0, 12),
    0x425b60: ('display_allocate', 0x425ba0, 0),
    0x425dc0: ('display_initialize', 0x4260f0, 32),
    0x426a30: ('display_release', 0x426ab0, 4),
    0x426e80: ('display_position', 0x426f40, 12),
    0x426cf0: ('display_depth', 0x426e00, 8),
}

def main():
    image = IMAGE.read_bytes()
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    rows = []
    for address, (name, width, expected, end, pop) in HOOKS.items():
        code = image[address-0x400000:end-0x400000]
        assert code[:width].hex() == expected
        ins = list(decoder.disasm(code[:width], address))
        assert sum(i.size for i in ins) == width
        if address == 0x432a20:
            assert [(i.address, i.mnemonic, i.op_str) for i in ins if i.mnemonic == 'call'] == [(0x432a23, 'call', '0x403900')]
            assert not any(i.mnemonic.startswith(('j', 'loop')) for i in ins)
        else:
            assert not any(i.mnemonic.startswith(('j', 'call', 'loop')) for i in ins)
        returns = [i.op_str for i in decoder.disasm(code, address) if i.mnemonic == 'ret']
        assert (hex(pop) if pop >= 10 else str(pop)) in returns if pop else '' in returns
        rows.append(dict(kind='hook', address=hex(address), name=name,
                         preserved_bytes=expected, width=width, thiscall_stack_pop=pop,
                         instructions=[f'{i.mnemonic} {i.op_str}' for i in ins], passed=True))
    for address, (name, end, pop) in APIS.items():
        code=image[address-0x400000:end-0x400000]
        returns=[i.op_str for i in decoder.disasm(code,address) if i.mnemonic=='ret']
        assert (hex(pop) if pop >= 10 else str(pop)) in returns if pop else '' in returns
        rows.append(dict(kind='api', address=hex(address), name=name,
                         thiscall_stack_pop=pop, passed=True))
    result=dict(design='CUSTOM-0058', image=str(IMAGE), sha256=hashlib.sha256(image).hexdigest(),
                signatures=rows, live_acceptance=False)
    path=Path(__file__).with_name('clone_native_evidence.json')
    path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(output=str(path),checks=len(rows),passed=True)))

if __name__=='__main__': main()
