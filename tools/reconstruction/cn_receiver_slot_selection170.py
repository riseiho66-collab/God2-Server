"""Round170 file-only native CN allocated receiver-owner slot usage.

No global rescan, client execution, emulation, build, tests or database access.
Already-known receivers get concrete slot witnesses, not additional phases.
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
OUT = ROOT / 'tw-common-movement-host-source-01/agents/cn-slot-selection'
EXE = SERVER.parent.parent / 'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY = EXE.parent.parent / 'God2_opt_source_recovery_20260926_055734/decompiled'
PIN = '582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
OWN = 'tools/reconstruction/cn_receiver_slot_selection170.py'
SOURCE = ['AGENTS.md', 'docs/IMPLEMENTATION_PROVENANCE.md', 'docs/GOAL_ACCEPTANCE.md',
          'tools/reconstruction/cn_computed_receiver_references.py',
          'tools/reconstruction/cn_cfg_receiver_references.py',
          'tools/reconstruction/cn_receiver_owner_frontier169.py', OWN]
FUNCTIONS = {'00445040': 'part_0004', '00444ec0': 'part_0004',
             '00449310': 'part_0004', '0047b610': 'part_0007',
             '0047b810': 'part_0007'}
SPANS = [('actual-scene-slot-copy', 0x445040, 0x4450e9),
         ('actual-second-slot-world-list-caller', 0x444ec0, 0x444f5c),
         ('actual-first-slot-selection-caller', 0x449310, 0x449368),
         ('actual-background-context-start', 0x47b610, 0x47b6ce),
         ('actual-background-owner-callback', 0x47b810, 0x47b917)]


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
        raise RuntimeError('Preserve prior round170 slot evidence')
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
    before = [retain('before/' + rel, SERVER / rel, True) for rel in SOURCE]
    dump('before-source-origins.json', before)
    dump('new-source-absence.json', {'new_absent_from_root_before1220': [OWN],
                                   'existing_cpp_edits': []})
    old = ROOT / 'tw-native-record-grammar-source-01/agents/cn-receiver'
    old_sources = [old / 'findings.json', old / 'seal.json', old / 'native/sites.json',
                   ROOT / 'cn-cfg-receiver-references-01/findings.json',
                   ROOT / 'cn-computed-receiver-references-01/computed-reference-scan.json',
                   ROOT / 'endpoint-catalog169/inputs/cn-receive-stages.json']
    prior = [retain('retained-prior/' + str(n) + '-' + p.name, p)
             for n, p in enumerate(old_sources)]
    dump('retained-prior/originals.json', prior)
    pe = pefile.PE(data=raw, fast_load=True)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    rows = list(csv.DictReader(io.StringIO((RECOVERY / 'functions.tsv').read_text(
        encoding='utf-8-sig')), delimiter='\t'))
    selected = [r for r in rows if r['address'].lower() in FUNCTIONS]
    dump('native/selected-original-metadata.json', selected)
    for row in selected:
        lo = int(row['address'], 16)
        _, full = mapped(pe, raw, lo, lo + int(row['bytes']))
        p = OUT / ('native/full-original-spans/' + row['address'] + '.bin')
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as stream:
            stream.write(full)
    sites = []
    for label, lo, hi in SPANS:
        offset, native = mapped(pe, raw, lo, hi)
        ins = [{'va': f'{i.address:08x}', 'bytes': bytes(i.bytes).hex(),
                'instruction': i.mnemonic + (' ' + i.op_str if i.op_str else '')}
               for i in md.disasm(native, lo)]
        p = OUT / ('native/' + label + '.bin')
        with p.open('xb') as stream:
            stream.write(native)
        dump('native/' + label + '.json', ins)
        sites.append({'label': label, 'start_va': f'{lo:08x}',
            'end_va_exclusive': f'{hi:08x}', 'file_offset': offset,
            'raw_bytes': native.hex(), 'sha256': sha(native),
            'decoded_instruction_count': len(ins),
            'decoded_bytes': sum(len(bytes.fromhex(i['bytes'])) for i in ins)})
    dump('native/sites.json', sites)
    calls = list(csv.DictReader(io.StringIO((RECOVERY / 'calls.tsv').read_text(
        encoding='utf-8-sig')), delimiter='\t'))
    # Keep rows as original metadata, never turn a metadata absence into a proof.
    filtered = [r for r in calls if any(value.lower() in FUNCTIONS for value in r.values())]
    dump('native/selected-original-calls.json', filtered)
    relations = [
        {'id': 'actual-outer-to-scene-slot-copy', 'owner_function': '00445040',
         'source_owner_from_first_argument': '00445075',
         'destination_scene_from_incoming_ecx': '0044506d',
         'copies': [{'load': '004450b3', 'source_offset': 0x458, 'store': '004450b9', 'scene_offset': 0x16180},
                    {'load': '004450bf', 'source_offset': 0x454, 'store': '004450c5', 'scene_offset': 0x1617c}],
         'scope': 'Actual object identity copy; no unresolved helper selected'},
        {'id': 'actual-second-slot-known-world-list-ecx', 'owner_function': '00444ec0',
         'ecx_slot_loads': ['00444f2d', '00444f43'], 'scene_offset': 0x16180,
         'outer_offset_by_prior_copy': 0x458,
         'calls': [{'site': '00444f3e', 'target': '004814d0'},
                   {'site': '00444f57', 'target': '0047e060'}],
         'scope': 'New slot witness for already-known receive context; no new phase or opcode'},
        {'id': 'actual-first-slot-known-selection-ecx', 'owner_function': '00449310',
         'ecx_slot_load': '00449339', 'scene_offset': 0x1617c,
         'outer_offset_by_prior_copy': 0x454, 'call': '00449363', 'target': '00481640',
         'scope': 'New slot witness for already-known receive context; no pairing to004812B0'},
        {'id': 'actual-background-callback-registration', 'owner_function': '0047b610',
         'incoming_context_copy': '0047b614', 'actual_owner_argument_load': '0047b620',
         'owner_store_site': '0047b630', 'context_owner_offset': 0x14,
         'context_argument_push': '0047b6b2', 'callback_argument_push': '0047b6b3',
         'callback_target': '0047b810', 'beginthreadex_call': '0047b6bc',
         'scope': 'Exact asynchronous callback/context registration; callback is not unresolved receive helper'},
        {'id': 'actual-background-owner-use', 'owner_function': '0047b810',
         'context_argument_load': '0047b81b', 'loop_exit_context_offset': 4,
         'work_enable_context_offset': 0x18,
         'owner_slot_loads': ['0047b869', '0047b8c7'], 'owner_slot_offset': 0x14,
         'sender_calls': [{'site': '0047b87e', 'target': '00481440', 'existing_c2s_opcode': 0x30},
                          {'site': '0047b8db', 'target': '00481440', 'existing_c2s_opcode': 0x36}],
         'ecx_owner_assignment_sites': ['0047b87c', '0047b8d6'],
         'scope': 'Mechanical timer/background owner use of already-inventoried producers; no additional packet route'},
    ]
    findings = {'round': 170, 'native_sha256': PIN, 'version_scope': 'cn',
        'new_bounded_native_spans': len(SPANS), 'new_mechanical_slot_relations': relations,
        'prior169_constructor_spans_recounted': 0, 'prior169_relations_recounted': 0,
        'old_global_cfg_spans_or_sites_recounted': 0,
        'unresolved_helpers': [{'address': '0047de70', 'phase': None, 'calling_slot': None, 'producer_pair': None},
                               {'address': '004812b0', 'phase': None, 'calling_slot': None, 'producer_pair': None}],
        'receiver_contexts': 14, 'qualified_receiver_contexts': 12,
        'new_phase_opcode_bindings': 0, 'new_complete_bidirectional_routes': 0,
        'new_formal_source_owner_chains': 0, 'new_cpp_files': 0,
        'whole_game_route_total': None, 'whole_game_completion_percent': None,
        'unreachable_proven': False, 'build_run': False, 'tests_run': False,
        'native_run': False, 'emulation_run': False, 'database_access': False, 'deployed': False}
    dump('findings.json', findings)
    dump('stage-accounting.json', {'direction': 'S2C-receiver-slot-owner-frontier',
        'known_prior_receiver_contexts': 14, 'known_prior_qualified_contexts': 12,
        'new_confirmed_contexts': 0, 'new_actual_slot_relations': len(relations),
        'complete_routes_added': 0})
    dump('gaps.json', [
        'Neither unresolved helper has an exact caller using scene+1617C/+16180 or a registered callback; calling_slot/phase/producer_pair remain null.',
        'Actual copied owner identity is established only for the explicitly retained known callers; do not classify all scene loads as one universal account/world phase.',
        'Actual background registration selects0047B810, not0047DE70/004812B0; its timer sends do not recover a missing receive phase.',
        'Next concrete trace roots: other actual loads of scene+1617C/+16180 and connection owner+40D4 callbacks; actual encoded/memory dispatch remains open.',
        'Prior global CFG3735sites/79spans and round169 constructor evidence are retained history, not new work.',
        'Stopped155 titleformatter/capacity chain is excluded entirely; no native/runtime absence proof follows from bounded static relations.',
    ])
    print(json.dumps({'artifact': str(OUT), 'new_slot_relations': len(relations),
                      'new_confirmed_phases': 0, 'new_complete_routes': 0, 'cpp_edits': 0}))


def capture():
    if not (OUT / 'findings.json').is_file() or (OUT / 'seal.json').exists():
        raise RuntimeError('No unsealed delivery')
    current = [retain('current/' + rel, SERVER / rel, True) for rel in SOURCE]
    dump('current-source-origins.json', current)
    listing = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file())
    with (OUT / 'LIST.txt').open('xb') as stream:
        stream.write(('\n'.join(listing + ['LIST.txt']) + '\n').encode())
    rows = [{'path': p.relative_to(OUT).as_posix(), 'bytes': p.stat().st_size,
             'sha256': sha(p.read_bytes())} for p in sorted(OUT.rglob('*')) if p.is_file()]
    dump('seal.json', {'kind': 'immutable round170 bounded CN owner slot usage',
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
        raise SystemExit('Only static extraction or explicit BATCHFINAL capture is supported')
