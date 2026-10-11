"""Round172 file-only CN nested receive-object and aggregate byte transfer.

No execution/emulation/global scan. Prior receive-loop/frame-reader witnesses
are retained separately and are never counted as new phase/format inventory.
"""
from pathlib import Path
import csv
import io
import json

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from .cn_receiver_owner_frontier169 import sha, mapped


SERVER = Path(__file__).resolve().parents[2]
ROOT = SERVER / 'artifacts/integration/packet-connections-20261006'
OUT = ROOT / 'tw-native-grid-composition-source-01/agents/cn-slot-frontier'
EXE = SERVER.parent.parent / 'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY = EXE.parent.parent / 'God2_opt_source_recovery_20260926_055734/decompiled'
PIN = '582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
OWN = 'tools/reconstruction/cn_receiver_slot_frontier172.py'
SOURCE = ['AGENTS.md', 'docs/IMPLEMENTATION_PROVENANCE.md', 'docs/GOAL_ACCEPTANCE.md',
          'tools/reconstruction/cn_receiver_owner_frontier169.py',
          'tools/reconstruction/cn_receiver_slot_selection170.py',
          'tools/reconstruction/cn_receiver_slot_frontier171.py', OWN]
NEW = {'0047d2e0', '0047a120', '0047a290', '0047a590'}
RETAINED = {'0047d8d0', '0047a170'}


def dump(rel, value):
    dest = OUT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open('xb') as stream:
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
        raise RuntimeError('Preserve previous round172 evidence')
    raw = EXE.read_bytes()
    if sha(raw) != PIN:
        raise ValueError('Pinned CN native input changed')
    OUT.mkdir(parents=True)
    originals = [retain('native-original-inputs/God2_opt.exe', EXE)]
    for filename in ('functions.tsv', 'calls.tsv'):
        originals.append(retain('native-original-inputs/' + filename, RECOVERY / filename))
    for address in sorted(NEW | RETAINED):
        originals.append(retain('native-original-inputs/' + address + '.c',
            RECOVERY / 'part_0007' / (address + '_FUN_' + address + '.c')))
    dump('native-original-inputs.json', originals)
    dump('before-source-origins.json', [retain('before/' + rel, SERVER / rel, True) for rel in SOURCE])
    dump('new-source-absence.json', {'new_absent_from_root_before1232': [OWN], 'existing_cpp_edits': []})
    old = ROOT / 'tw-native-movement-scene-source-01/agents/cn-slot-frontier'
    original_cn = EXE.parent.parent / 'God2-Server-CN/artifacts/native/20261006-cn-receive-phases-01'
    prior = [old / 'findings.json', old / 'seal.json', old / 'native/sites.json',
             ROOT / 'tw-common-movement-host-source-01/agents/cn-slot-selection/findings.json',
             ROOT / 'tw-native-record-grammar-source-01/agents/cn-receiver/findings.json',
             original_cn / 'summary.json', original_cn / 'source-manifest.json']
    dump('retained-prior/originals.json', [retain('retained-prior/' + str(n) + '-' + p.name, p)
                                       for n, p in enumerate(prior)])
    pe = pefile.PE(data=raw, fast_load=True)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    metadata = list(csv.DictReader(io.StringIO((RECOVERY / 'functions.tsv').read_text(
        encoding='utf-8-sig')), delimiter='\t'))
    selected = [r for r in metadata if r['address'].lower() in NEW | RETAINED]
    dump('native/selected-original-metadata.json', selected)
    new_sites, old_sites, instructions = [], [], {}
    for row in selected:
        address = row['address'].lower()
        lo, size = int(address, 16), int(row['bytes'])
        offset, native = mapped(pe, raw, lo, lo + size)
        decoded = [{'va': f'{i.address:08x}', 'bytes': bytes(i.bytes).hex(),
                    'instruction': i.mnemonic + (' ' + i.op_str if i.op_str else '')}
                   for i in md.disasm(native, lo)]
        instructions.update({r['va']: r for r in decoded})
        section = 'new-nested-object-spans' if address in NEW else 'retained-caller-witnesses'
        dest = OUT / ('native/' + section + '/' + address + '.bin')
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as stream:
            stream.write(native)
        dump('native/' + section + '/' + address + '.json', decoded)
        record = {'owner': address, 'start_va': f'{lo:08x}', 'end_va_exclusive': f'{lo+size:08x}',
            'file_offset': offset, 'raw_bytes': native.hex(), 'sha256': sha(native),
            'decoded_instruction_count': len(decoded),
            'decoded_bytes': sum(len(bytes.fromhex(i['bytes'])) for i in decoded),
            'new_round172_bounded_relation_scope': address in NEW,
            'native_phase_or_frame_format_inventory_increment': False}
        (new_sites if address in NEW else old_sites).append(record)
    dump('native/new-sites.json', new_sites)
    dump('native/retained-caller-sites.json', old_sites)
    calls = list(csv.DictReader(io.StringIO((RECOVERY / 'calls.tsv').read_text(
        encoding='utf-8-sig')), delimiter='\t'))
    dump('native/selected-original-calls.json', [r for r in calls
        if any(v.lower() in NEW | RETAINED for v in r.values())])

    def relation(identifier, scope, new_vas, witness_vas, **fields):
        return {'id': identifier, 'scope': scope,
            'rawsites': [instructions[va] for va in new_vas],
            'retained_caller_rawsites_not_recounted': [instructions[va] for va in witness_vas], **fields}

    relations = [
        relation('actual-two-step-nested-receive-owner',
            '0047D2E0 gets fullowner+104 then adds654 before passing ECX to A290/A120; direct retained receive-loop witnesses independently use fullowner+758.',
            ['0047d2e4', '0047d2ee', '0047d2f0', '0047d2fc', '0047d2fe'],
            ['0047d8e2', '0047d900', '0047d906', '0047d949', '0047d94f'],
            first_subobject_displacement=0x104, second_subobject_displacement=0x654,
            full_owner_nested_receive_displacement=0x758,
            actual_targets=['0047a290', '0047a120'], unknown_helper_selected=False),
        relation('nested-readable-cursor-gate-to-byte-copy',
            'Signed nested produced<=read predicate gates one-byte copy; actual raw transfer target is A120, not a registered receive helper.',
            ['0047a290', '0047a298', '0047a29e', '0047d2f5', '0047d2f7', '0047d2f9', '0047d2fe', '0047d303', '0047d306'], [],
            nested_produced_count_offset=0x1810, nested_read_cursor_offset=0x1814,
            produced_full_owner_offset=0x1f68, read_cursor_full_owner_offset=0x1f6c,
            requested_byte_count=1, byte_read_success_return=0, byte_read_unavailable_return=1),
        relation('actual-nested-bytes-to-distinct-logical-aggregate',
            'A120 copies from nested+C10+readcursor to the actual explicit destination and advances nested cursor; retained caller provides fullowner+2CC4 plus logical fill. These counters are distinct.',
            ['0047a128', '0047a12e', '0047a134', '0047a13a', '0047a142', '0047a145', '0047a14c', '0047a14f', '0047a152', '0047a15a'],
            ['0047d942', '0047d948', '0047d949', '0047d94f', '0047d990', '0047d996', '0047d99c', '0047d9a1', '0047d9a4'],
            nested_readable_buffer_offset=0xc10, readable_buffer_full_owner_offset=0x1368,
            nested_read_cursor_offset=0x1814, nested_read_cursor_full_owner_offset=0x1f6c,
            full_owner_logical_fill_offset=0x2cc0, full_owner_logical_buffer_offset=0x2cc4,
            actual_copy_target='0074f150', helper_phase_determined=False),
        relation('frame-finalizer-publishes-same-nested-readable-domain',
            'Actual A590 retains incoming nested ECX and writes produced count+1810/read cursor+1814 for A120; retained A170 caller passes that same object after exact framed count completion. Existing frame algorithms are not recounted.',
            ['0047a59f', '0047a5a1', '0047a5a8', '0047a699', '0047a69c', '0047a6a4'],
            ['0047a256', '0047a25f', '0047a265', '0047a268', '0047a26f'],
            finalized_readable_buffer_nested_offset=0xc10,
            finalized_produced_count_nested_offset=0x1810,
            finalized_read_cursor_nested_offset=0x1814,
            finalized_read_cursor_value=0, retained_frame_storage_nested_offset=0x1818,
            actual_complete_frame_callback_target='0047a590',
            transfer_kind='direct named function call with real ECX, not an indirect receive selector'),
    ]
    byte_count = sum(int(s['end_va_exclusive'], 16)-int(s['start_va'], 16) for s in new_sites)
    findings = {'round': 172, 'version_scope': 'cn', 'native_sha256': PIN,
        'new_native_relations': relations, 'new_bounded_native_spans': len(new_sites),
        'new_bounded_native_bytes': byte_count, 'retained_old_caller_spans_not_recounted': len(old_sites),
        'old169_170_171_spans_or_relations_recounted': 0, 'old_global_cfg_spans_or_sites_recounted': 0,
        'receiver_contexts': 14, 'qualified_receiver_contexts': 12,
        'unresolved_helpers': [{'address': '0047de70', 'phase': None, 'slot': None, 'producer_pair': None},
                               {'address': '004812b0', 'phase': None, 'slot': None, 'producer_pair': None}],
        'new_phase_opcode_bindings': 0, 'new_formal_source_owner_chains': 0,
        'new_complete_bidirectional_routes': 0, 'new_cpp_files': 0,
        'whole_game_route_total': None, 'whole_game_completion_percent': None,
        'unreachable_proven': False, 'build_run': False, 'tests_run': False,
        'native_run': False, 'emulation_run': False, 'database_access': False, 'deployed': False}
    dump('findings.json', findings)
    dump('stage-accounting.json', {'direction': 'S2C-receive-owner-frontier',
        'known_prior_receiver_contexts': 14, 'known_prior_qualified_contexts': 12,
        'new_confirmed_contexts': 0, 'new_actual_nested_object_relations': len(relations),
        'new_bounded_native_spans': len(new_sites), 'retained_caller_spans_not_recounted': len(old_sites),
        'new_frame_format_or_opcode_inventory': 0, 'complete_routes_added': 0})
    dump('gaps.json', [
        'Exact indirect/encoded/deferred caller assigning0047DE70/004812B0 remains missing; phase/slot/producer pair stay null.',
        'Nested receive fields belong to fullowner+758, not fullowner+104 or logical aggregate owner+2CC0; preserve exact domain when tracing later selectors.',
        'The retained receive loop directly calls its existing length lookup after byte copying; recover actual upstream helper invocation rather than inferring phase from framing or readable counters.',
        'Next bounded original frontier: actual0047D8D0 callers outside the two unknown helper bodies and concrete function-pointer/table registration on their exact ECX owner; ordinary frame-finalizer targetA590 is not that registration.',
        'No global absence, dead-code or completed-route conclusion follows from these four bounded nested-transfer relations.',
        'Oldglobal79/3735 and169/170/171 studies are retained history; no global scan, frame-format recount, source execution or155titlechain retry.',
    ])
    print(json.dumps({'artifact': str(OUT), 'new_native_relations': len(relations),
        'new_bounded_native_spans': len(new_sites), 'new_bounded_native_bytes': byte_count,
        'retained_caller_spans_not_recounted': len(old_sites),
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
    dump('seal.json', {'kind': 'immutable round172 CN nested receive-owner frontier',
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
