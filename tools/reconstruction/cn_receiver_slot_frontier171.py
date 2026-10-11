"""Round171 bounded file-only CN scene-slot and worker-context frontier.

The retained original instructions establish mechanical owner transfers only.
They do not assign unknown receive helpers to a phase, producer or gameplay.
"""
from pathlib import Path
import csv
import io
import json
import struct

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from .cn_receiver_owner_frontier169 import sha, mapped
from .cn_pe_import_directory import FileView


SERVER = Path(__file__).resolve().parents[2]
ROOT = SERVER / 'artifacts/integration/packet-connections-20261006'
OUT = ROOT / 'tw-native-movement-scene-source-01/agents/cn-slot-frontier'
EXE = SERVER.parent.parent / 'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY = EXE.parent.parent / 'God2_opt_source_recovery_20260926_055734/decompiled'
PIN = '582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
OWN = 'tools/reconstruction/cn_receiver_slot_frontier171.py'
SOURCE = ['AGENTS.md', 'docs/IMPLEMENTATION_PROVENANCE.md', 'docs/GOAL_ACCEPTANCE.md',
          'tools/reconstruction/cn_receiver_owner_frontier169.py',
          'tools/reconstruction/cn_receiver_slot_selection170.py',
          'tools/reconstruction/cn_pe_import_directory.py', OWN]
FUNCTIONS = {'0043eaf0': 'part_0004', '00443e80': 'part_0004',
             '00449060': 'part_0004', '0047f430': 'part_0007',
             '00481440': 'part_0007', '0047b6e0': 'part_0007',
             '0047b920': 'part_0007', '0047c680': 'part_0007',
             '0047c970': 'part_0007'}


def dump(rel, value):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write((json.dumps(value, indent=2, ensure_ascii=True) + '\n').encode())


def retain(rel, path, repository=False):
    raw = path.read_bytes()
    dest = OUT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open('xb') as stream:
        stream.write(raw)
    return {'path': path.relative_to(SERVER).as_posix() if repository else str(path),
            'copy': rel, 'bytes': len(raw), 'sha256': sha(raw)}


def main():
    if OUT.exists():
        raise RuntimeError('Preserve earlier round171 evidence')
    raw = EXE.read_bytes()
    if sha(raw) != PIN:
        raise ValueError('Pinned CN native input changed')
    OUT.mkdir(parents=True)
    originals = [retain('native-original-inputs/God2_opt.exe', EXE)]
    for filename in ('functions.tsv', 'calls.tsv'):
        originals.append(retain('native-original-inputs/' + filename, RECOVERY / filename))
    for address, folder in FUNCTIONS.items():
        originals.append(retain('native-original-inputs/' + address + '.c',
                                RECOVERY / folder / (address + '_FUN_' + address + '.c')))
    dump('native-original-inputs.json', originals)
    dump('before-source-origins.json', [retain('before/' + rel, SERVER / rel, True) for rel in SOURCE])
    dump('new-source-absence.json', {'new_absent_from_root_before1225': [OWN], 'existing_cpp_edits': []})
    old = ROOT / 'tw-common-movement-host-source-01/agents/cn-slot-selection'
    old_sources = [old / 'findings.json', old / 'seal.json', old / 'native/sites.json',
        ROOT / 'tw-native-record-grammar-source-01/agents/cn-receiver/findings.json',
        ROOT / 'cn-cfg-receiver-references-01/findings.json',
        ROOT / 'endpoint-catalog170/inputs/cn-receive-stages.json']
    dump('retained-prior/originals.json', [retain('retained-prior/' + str(n) + '-' + p.name, p)
                                       for n, p in enumerate(old_sources)])
    pe = pefile.PE(data=raw, fast_load=True)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    metadata = list(csv.DictReader(io.StringIO((RECOVERY / 'functions.tsv').read_text(
        encoding='utf-8-sig')), delimiter='\t'))
    selected = [r for r in metadata if r['address'].lower() in FUNCTIONS]
    dump('native/selected-original-metadata.json', selected)
    sites = []
    instructions = {}
    for row in selected:
        address = row['address'].lower()
        lo, size = int(address, 16), int(row['bytes'])
        offset, native = mapped(pe, raw, lo, lo + size)
        decoded = [{'va': f'{i.address:08x}', 'bytes': bytes(i.bytes).hex(),
                    'instruction': i.mnemonic + (' ' + i.op_str if i.op_str else '')}
                   for i in md.disasm(native, lo)]
        instructions.update({r['va']: r for r in decoded})
        p = OUT / ('native/' + address + '.bin')
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as stream:
            stream.write(native)
        dump('native/' + address + '.json', decoded)
        sites.append({'owner': address, 'start_va': f'{lo:08x}', 'end_va_exclusive': f'{lo+size:08x}',
            'file_offset': offset, 'raw_bytes': native.hex(), 'sha256': sha(native),
            'decoded_instruction_count': len(decoded),
            'decoded_bytes': sum(len(bytes.fromhex(i['bytes'])) for i in decoded)})
    dump('native/sites.json', sites)
    calls = list(csv.DictReader(io.StringIO((RECOVERY / 'calls.tsv').read_text(
        encoding='utf-8-sig')), delimiter='\t'))
    dump('native/selected-original-calls.json', [r for r in calls
        if any(v.lower() in FUNCTIONS for v in r.values())])
    # Read the two explicit descriptors/ILT/IAT cells associated with the
    # actual retained indirect calls. No global import or CFG rescan here.
    view = FileView(pe, raw)
    imports = []
    for descriptor_rva in (0x6ab5f4, 0x6ab608):
        descriptor = view.read(descriptor_rva, 20)
        oft, stamp, chain, name, ft = struct.unpack('<5I', descriptor)
        lookup = oft or ft
        cell = view.read(lookup, 4)
        hint_name = struct.unpack('<I', cell)[0]
        imports.append({'descriptor_rva': f'{descriptor_rva:08x}',
            'descriptor_raw_bytes': descriptor.hex(), 'lookup_rva': f'{lookup:08x}',
            'lookup_raw_bytes': cell.hex(), 'iat_rva': f'{ft:08x}',
            'iat_va': f'{pe.OPTIONAL_HEADER.ImageBase + ft:08x}',
            'iat_raw_bytes': view.read(ft, 4).hex(), 'dll': view.string(name),
            'dll_name_rva': f'{name:08x}', 'hint_name_rva': f'{hint_name:08x}',
            'hint': struct.unpack('<H', view.read(hint_name, 2))[0],
            'name': view.string(hint_name + 2), 'loaded_binding_observed': False,
            'method': 'two specific FILE_BACKED_PE32_DESCRIPTOR_ILT/IAT declarations'})
    dump('native/selected-declared-import-bindings.json', imports)

    def relation(identifier, scope, vas, **fields):
        return {'id': identifier, 'scope': scope,
                'rawsites': [instructions[va] for va in vas], **fields}

    relations = [
        relation('second-scene-slot-to-global-count-reader',
            'Actual ECX is second owner+104, but this exact callee ignores ECX and reads one global DWORD; no receiver registration.',
            ['0043eaf3', '0043eafd', '0043eb03', '0047c680', '0043eb0a', '0043eb15', '0043eb1d'],
            scene_slot_offset=0x16180, owner_subobject_offset=0x104, actual_target='0047c680',
            global_dword_va='009ee1b8', result_predicate='signed result>0',
            state_gate='scene+1792DC!=0x0B', assigned_scene_state=3),
        relation('second-scene-slot-to-global-indexed-reader',
            'Actual ECX is second owner+104; signed16 scene field is explicit index. Exact callee reads global indexed pointer+40, not ECX.',
            ['00443e83', '00443e8d', '00443e94', '00443e9b', '0047c973', '0047c976', '0047c97d', '00443eb5'],
            scene_slot_offset=0x16180, owner_subobject_offset=0x104, scene_index_offset=0x8f4,
            actual_target='0047c970', global_pointer_table_va='009ee1c0', table_scale=4,
            pointed_field_offset=0x40, result_predicate='signed result>0',
            state_gate='scene+1792DC!=0x0B', assigned_scene_state=0x12),
        relation('numeric-state12-invokes-known-selection',
            'Exact state predicate invokes already-known00449310 with original scene ECX; receiver phase inventory is unchanged.',
            ['00449061', '00449069', '0044906c', '0044906e', '00449075', '0044907d', '0044908d'],
            scene_state_offset=0x1792dc, required_state=0x12, actual_target='00449310',
            nonzero_result_branch='if current state!=0x0B, store prior state at1792E0 and assign4'),
        relation('zero-selection-result-two-exact-owner-transfers',
            'Zero return branches to second-owner disconnect when active, then first-owner0047F310. Neither unknown helper is selected by these exact calls.',
            ['0044909b', '004490a1', '004490a8', '004490b0', '004490b5', '004490c3', '004490ce', '004490de'],
            second_owner_scene_offset=0x16180, active_owner_byte_offset=0x2cb8,
            second_owner_actual_target='00480b10', first_owner_scene_offset=0x1617c,
            first_owner_actual_target='0047f310', state_gate='scene+1792DC!=0x0B',
            assigned_scene_state=1),
        relation('outbound-flush-worker-context-use',
            'Actual owner+40D4 is an object argument to lock helpers around the send-buffer operation; it is not dereferenced as a receiver callback in this span.',
            ['0047f433', '0047f444', '0047f446', '0047f450', '0047f463', '0047f469', '0047f46e', '0047f482'],
            worker_context_owner_offset=0x40d4, pending_byte_count_owner_offset=0x36c4,
            buffer_owner_offset=0x36c8, actual_base_displacement=0x104,
            actual_send_target='0047d350', actual_lock_targets=['0047b6e0', '0047b920']),
        relation('outbound-append-worker-context-use',
            'Actual owner+40D4 is passed in ECX to the same lock helpers during append. These named transfers do not recover receive-helper dispatch.',
            ['0048146f', '00481479', '0048147b', '00481489', '004814a2', '004814ab', '004814ba'],
            worker_context_owner_offset=0x40d4, buffer_owner_offset=0x36c8,
            pending_byte_count_owner_offset=0x36c4,
            actual_lock_targets=['0047b6e0', '0047b920']),
        relation('worker-lock-storage-and-declared-iat',
            'Exact small helpers gate on context+8 and pass context+3C to declared Enter/LeaveCriticalSection IAT slots. Only file declarations are observed.',
            ['0047b6e0', '0047b6e6', '0047b6ea', '0047b920', '0047b926', '0047b92a'],
            active_context_offset=8, critical_section_context_offset=0x3c,
            enter_iat_va='007eb5a0', leave_iat_va='007eb59c', loaded_binding_observed=False),
    ]
    findings = {'round': 171, 'version_scope': 'cn', 'native_sha256': PIN,
        'new_native_relations': relations, 'new_bounded_native_spans': len(sites),
        'new_bounded_native_bytes': sum((int(s['end_va_exclusive'], 16)-int(s['start_va'], 16)) for s in sites),
        'prior169_constructor_spans_recounted': 0, 'prior170_slot_spans_recounted': 0,
        'old_global_cfg_spans_or_sites_recounted': 0, 'receiver_contexts': 14,
        'qualified_receiver_contexts': 12,
        'unresolved_helpers': [{'address': '0047de70', 'phase': None, 'slot': None, 'producer_pair': None},
                               {'address': '004812b0', 'phase': None, 'slot': None, 'producer_pair': None}],
        'new_phase_opcode_bindings': 0, 'new_formal_source_owner_chains': 0,
        'new_complete_bidirectional_routes': 0, 'new_cpp_files': 0,
        'whole_game_route_total': None, 'whole_game_completion_percent': None,
        'unreachable_proven': False, 'build_run': False, 'tests_run': False,
        'native_run': False, 'emulation_run': False, 'database_access': False, 'deployed': False}
    dump('findings.json', findings)
    dump('stage-accounting.json', {'direction': 'S2C-receiver-owner-frontier',
        'known_prior_receiver_contexts': 14, 'known_prior_qualified_contexts': 12,
        'new_confirmed_contexts': 0, 'new_actual_mechanical_relations': len(relations),
        'new_bounded_native_spans': len(sites), 'complete_routes_added': 0})
    dump('gaps.json', [
        'Actual caller or encoded/deferred transfer to0047DE70/004812B0 remains missing; phases, exact calling slots and producer pairing remain null.',
        'Observed owner+40D4 lock-context transfers narrow this frontier; do not continue treating that field as a proven receive-function pointer table.',
        'Next concrete roots: actual remaining scene-slot loaders00448950/004468F0 and outgoing status/error branches using those exact owners; recover their instruction-level target and ECX before assigning a phase.',
        'Actual global009EE1B8/009EE1C0 producers and later memory/encoded registrations remain outside these nine exact spans.',
        'No dead-code/global-absence conclusion follows; source recovery is incomplete and all unknown helper variants stay open.',
        'Old169/170 spans and prior global79/3735 findings remain immutable retained history; no rescan/recount or155titlechain retry.',
    ])
    print(json.dumps({'artifact': str(OUT), 'new_native_relations': len(relations),
        'new_bounded_native_spans': len(sites), 'new_bounded_native_bytes': findings['new_bounded_native_bytes'],
        'new_confirmed_phases': 0, 'new_complete_routes': 0, 'cpp_edits': 0}))


def capture():
    if not (OUT / 'findings.json').is_file() or (OUT / 'seal.json').exists():
        raise RuntimeError('No unsealed delivery')
    dump('current-source-origins.json', [retain('current/' + rel, SERVER / rel, True) for rel in SOURCE])
    listing = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file())
    with (OUT / 'LIST.txt').open('xb') as stream:
        stream.write(('\n'.join(listing + ['LIST.txt']) + '\n').encode())
    rows = [{'path': p.relative_to(OUT).as_posix(), 'bytes': p.stat().st_size,
             'sha256': sha(p.read_bytes())} for p in sorted(OUT.rglob('*')) if p.is_file()]
    dump('seal.json', {'kind': 'immutable round171 CN bounded actual slot/lock frontier',
        'files': rows, 'native_input_sha256': PIN, 'source_original_count': len(SOURCE),
        'complete_routes_added': 0, 'build_run': False, 'tests_run': False,
        'native_run': False, 'database_access': False})
    print(json.dumps({'sealed': str(OUT), 'seal_sha256': sha((OUT / 'seal.json').read_bytes()),
        'members': len(rows), 'current_source_originals': len(SOURCE)}))


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['--capture-after-batchfinal']:
        capture()
    elif not sys.argv[1:]:
        main()
    else:
        raise SystemExit('Only static extraction or explicit BATCHFINAL capture is supported')
