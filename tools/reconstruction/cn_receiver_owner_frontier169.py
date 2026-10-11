"""Bounded file-only CN receiver owner-construction relations for round169.

No client loading, emulation, build, tests, database access or global scan.
An allocated owner is not a qualified calling phase for an unresolved helper.
"""
from pathlib import Path
import csv
import hashlib
import io
import json
import shutil

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32


SERVER = Path(__file__).resolve().parents[2]
ROOT = SERVER / 'artifacts/integration/packet-connections-20261006'
OUT = ROOT / 'tw-native-record-grammar-source-01/agents/cn-receiver'
EXE = SERVER.parent.parent / 'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY = EXE.parent.parent / 'God2_opt_source_recovery_20260926_055734/decompiled'
PIN = '582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
OWN = 'tools/reconstruction/cn_receiver_owner_frontier169.py'
SOURCE = [
    'AGENTS.md', 'docs/IMPLEMENTATION_PROVENANCE.md', 'docs/GOAL_ACCEPTANCE.md',
    'tools/reconstruction/cn_computed_receiver_references.py',
    'tools/reconstruction/cn_cfg_receiver_references.py',
    'tools/reconstruction/cn_wrapper_route_frontier.py', OWN,
]
EXTERNAL_FUNCTIONS = {
    '00449f50': 'part_0004', '0047d6c0': 'part_0007',
    '0047c1a0': 'part_0007', '00479630': 'part_0007',
    '0047fa20': 'part_0007', '0047c990': 'part_0007',
    '0047d8d0': 'part_0007', '0047d870': 'part_0007',
    '0047de70': 'part_0007', '004812b0': 'part_0007',
}
SPANS = [
    ('first-owner-allocation', 0x44a195, 0x44a1e1),
    ('second-owner-allocation', 0x44a260, 0x44a2a9),
    ('full-owner-constructor', 0x47d6c0, 0x47d7b7),
    ('embedded-base-constructor', 0x47c1a0, 0x47c1d3),
    ('full-owner-setup', 0x47fa20, 0x47fa9a),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(rel, value):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write((json.dumps(value, indent=2, ensure_ascii=True) + '\n').encode())


def retain(rel, origin):
    raw = origin.read_bytes()
    target = OUT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(raw)
    return {'original': str(origin), 'copy': rel,
            'bytes': len(raw), 'sha256': sha(raw)}


def mapped(pe, raw, lo, hi):
    """Read only a unique complete section-backed native interval."""
    base = pe.OPTIONAL_HEADER.ImageBase
    matches = []
    for section in pe.sections:
        start = base + section.VirtualAddress
        end = start + section.SizeOfRawData
        if start <= lo and hi <= end:
            offset = section.PointerToRawData + lo - start
            if offset + hi - lo <= len(raw):
                matches.append((offset, raw[offset:offset + hi - lo]))
    if len(matches) != 1:
        raise ValueError('Native interval is not uniquely file-backed')
    return matches[0]


def main():
    if OUT.exists():
        raise RuntimeError('Preserve round169 receiver delivery; use capture only')
    raw = EXE.read_bytes()
    if sha(raw) != PIN:
        raise ValueError('Pinned CN input changed')
    OUT.mkdir(parents=True)
    originals = [retain('native-original-inputs/God2_opt.exe', EXE)]
    for filename in ('functions.tsv', 'calls.tsv'):
        originals.append(retain('native-original-inputs/' + filename, RECOVERY / filename))
    for address, folder in EXTERNAL_FUNCTIONS.items():
        originals.append(retain('native-original-inputs/' + address + '.c',
                                RECOVERY / folder / (address + '_FUN_' + address + '.c')))
    prior_files = [
        ROOT / 'cn-computed-receiver-references-01/computed-reference-scan.json',
        ROOT / 'cn-computed-receiver-references-01/integration-manifest.json',
        ROOT / 'cn-cfg-receiver-references-01/findings.json',
        ROOT / 'cn-cfg-receiver-references-01/unresolved-frontiers.json',
        ROOT / 'cn-cfg-receiver-references-01/receiver-candidates.json',
        ROOT / 'cn-receiver-reachability-agent-01/findings.json',
        ROOT / 'endpoint-catalog168/inputs/cn-receive-stages.json',
    ]
    for number, path in enumerate(prior_files):
        originals.append(retain('retained-prior/' + str(number) + '-' + path.name, path))
    source = [retain('before/' + rel, SERVER / rel) for rel in SOURCE]
    dump('before-source-origins.json', {'files': source,
        'owned_new_absent_from_root_round_start': [OWN],
        'existing_sources_modified': []})
    dump('native-original-inputs/manifest.json', {'inputs': originals,
         'complete_original_files_retained': True,
         'native_execution': False, 'metadata_execution': False})
    pe = pefile.PE(data=raw, fast_load=True)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    sites = []
    for label, lo, hi in SPANS:
        offset, native = mapped(pe, raw, lo, hi)
        rows = [{'va': f'{i.address:08x}', 'bytes': bytes(i.bytes).hex(),
                 'instruction': i.mnemonic + (' ' + i.op_str if i.op_str else '')}
                for i in md.disasm(native, lo)]
        retained = OUT / ('native/' + label + '.bin')
        retained.parent.mkdir(parents=True, exist_ok=True)
        with retained.open('xb') as stream:
            stream.write(native)
        dump('native/' + label + '.json', rows)
        sites.append({'label': label, 'start_va': f'{lo:08x}',
            'end_va_exclusive': f'{hi:08x}', 'file_offset': offset,
            'raw_bytes': native.hex(), 'sha256': sha(native),
            'decoded_instruction_count': len(rows),
            'decoded_bytes': sum(len(bytes.fromhex(row['bytes'])) for row in rows)})
    dump('native/sites.json', sites)
    metadata = list(csv.DictReader(io.StringIO((RECOVERY / 'functions.tsv').read_text(
        encoding='utf-8-sig')), delimiter='\t'))
    selected = [row for row in metadata if row['address'].lower() in EXTERNAL_FUNCTIONS]
    dump('native/selected-original-metadata.json', selected)
    findings = {
        'round': 169, 'version_scope': 'cn', 'native_sha256': PIN,
        'analysis': 'Five explicit bounded native owner-construction/setup spans; no full old scan rerun',
        'new_native_relations': [
            {'id': 'two-independent-owner-allocations',
             'first': {'allocation_size': 0x4710, 'size_push': '0044a195',
                       'allocation_call': '0044a19a', 'ecx_from_allocation': '0044a1b3',
                       'constructor_call': '0044a1b5', 'store': '0044a1d6',
                       'outer_owner_offset': 0x454, 'setup_call': '0044a1dc'},
             'second': {'allocation_size': 0x4710, 'size_push': '0044a260',
                        'allocation_call': '0044a265', 'ecx_from_allocation': '0044a27e',
                        'constructor_call': '0044a280', 'store': '0044a29e',
                        'outer_owner_offset': 0x458, 'setup_call': '0044a2a4'},
             'scope': 'Both constructed objects share implementation; neither unresolved receiver is assigned to a slot'},
            {'id': 'embedded-owner-base-displacement',
             'incoming_owner_copy': '0047d6e6', 'base_ecx_lea': '0047d6eb',
             'base_constructor_call': '0047d6f1', 'base_displacement': 0x104,
             'base_field_writes': [
                 {'site': '0047c1b0', 'base_offset': 0x64c, 'full_owner_offset': 0x750, 'value': 0xffffffff, 'width': 4},
                 {'site': '0047c1bf', 'base_offset': 0, 'full_owner_offset': 0x104, 'value': 0, 'width': 4},
                 {'site': '0047c1c7', 'base_offset': 0x650, 'full_owner_offset': 0x754, 'value': 0, 'width': 1}],
             'scope': 'These zero/invalid initial fields are not a recovered receiver pointer or registration'},
            {'id': 'full-owner-packet-state-initialization',
             'fields': [
                 {'site': '0047d732', 'offset': 0x2cc0, 'width': 4, 'value': 0},
                 {'site': '0047d73c', 'offset': 0x36c4, 'width': 4, 'value': 0},
                 {'site': '0047d746', 'offset': 0x2cb8, 'width': 2, 'value': 0},
                 {'site': '0047d74f', 'offset': 0x40d0, 'width': 4, 'value': 0},
                 {'site': '0047d759', 'offset': 0x40f8, 'width': 4, 'value': 0},
                 {'site': '0047d763', 'offset': 0x41fc, 'width': 4, 'value': 0},
                 {'site': '0047d76d', 'offset': 0x40e8, 'width': 4, 'value': 1}],
             'scope': 'Mechanical constructor relation to previously recovered receiver fields; no phase assignment'},
            {'id': 'setup-reuses-embedded-base',
             'incoming_full_owner_copy': '0047fa27', 'base_ecx_lea': '0047fa29',
             'base_setup_call': '0047fa2f', 'base_displacement': 0x104,
             'resource_owner_write': '0047fa83', 'resource_owner_offset': 0x40d0,
             'resource_owner_value': 'actual first explicit setup argument',
             'scope': 'Per-object setup shares base mechanics; no receiver selector installed by these retained instructions'},
        ],
        'retained_prior_only': {'cfg_scanned_spans': 43751,
            'cfg_spans_beyond_linear_prefix': 79, 'cfg_new_instruction_sites': 3735,
            'new_recounted_scanned_spans': 0, 'new_recounted_old_sites': 0},
        'unresolved_helpers': [{'address': '0047de70', 'phase': None,
            'calling_slot': None, 'producer_pair': None},
            {'address': '004812b0', 'phase': None, 'calling_slot': None, 'producer_pair': None}],
        'new_phase_opcode_bindings': 0, 'new_complete_bidirectional_routes': 0,
        'new_cpp_files': 0, 'whole_game_route_total': None, 'whole_game_completion_percent': None,
        'unreachable_proven': False, 'build_run': False, 'tests_run': False,
        'native_run': False, 'emulation_run': False, 'database_access': False,
        'deployed': False,
    }
    dump('findings.json', findings)
    gaps = [
        'Actual caller/selector after construction must bind one exact allocated object to unresolved0047DE70/004812B0; common constructor and buffer offsets do not select phase.',
        'Other constructor callees, later memory/encoded dispatch, transformed islands and loader/runtime mutation remain outside these five spans.',
        'No direct allocation-to-helper invocation was recovered; both helper phases and producer pairs remain null.',
        'No global absence/dead-code proof, new opcode/variant/complete route, official rule or server integration follows from this bounded owner relation.',
        'The unrelated security-stopped title formatter/capacity chain is excluded; original whole function file is retained only for provenance.',
    ]
    dump('gaps.json', gaps)
    dump('stage-accounting.json', {'direction': 'S2C-consumer-owner-frontier',
        'known_prior_receiver_contexts': 14, 'known_prior_qualified_contexts': 12,
        'unresolved_contexts': 2, 'new_bounded_owner_spans': len(SPANS),
        'new_actual_owner_relations': len(findings['new_native_relations']),
        'new_confirmed_contexts': 0, 'complete_routes_added': 0})
    print(json.dumps({'artifact': str(OUT), 'new_owner_relations': 4,
        'new_confirmed_phases': 0, 'new_complete_routes': 0, 'cpp_edits': 0}))


def capture():
    """Final file-only original capture after root's explicit BATCHFINAL."""
    if not (OUT / 'findings.json').is_file() or (OUT / 'seal.json').exists():
        raise RuntimeError('No draft delivery or already sealed')
    current = []
    for rel in SOURCE:
        saved = retain('current/' + rel, SERVER / rel)
        current.append({'path': rel, 'copy': saved['copy'],
                        'bytes': saved['bytes'], 'sha256': saved['sha256']})
    dump('current-source-origins.json', current)
    listing = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file())
    with (OUT / 'LIST.txt').open('xb') as stream:
        stream.write(('\n'.join(listing + ['LIST.txt']) + '\n').encode())
    rows = [{'path': p.relative_to(OUT).as_posix(), 'bytes': p.stat().st_size,
             'sha256': sha(p.read_bytes())} for p in sorted(OUT.rglob('*')) if p.is_file()]
    dump('seal.json', {'kind': 'immutable round169 static CN owner relation delivery',
        'files': rows, 'native_input_sha256': PIN, 'source_original_count': len(current),
        'complete_routes_added': 0, 'build_run': False, 'tests_run': False,
        'native_run': False, 'database_access': False})
    print(json.dumps({'sealed': str(OUT), 'seal_sha256': sha((OUT / 'seal.json').read_bytes()),
                      'members': len(rows), 'current_source_originals': len(current)}))


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['--capture-after-batchfinal']:
        capture()
    elif not sys.argv[1:]:
        main()
    else:
        raise SystemExit('Only initial static extraction or explicit BATCHFINAL capture is supported')
