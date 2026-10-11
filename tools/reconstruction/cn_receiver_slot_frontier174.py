"""File-only CN exact pointer-candidate table consumers, round174.

Old raw helper-address matches are not new receiver references. Recover bounded
aligned table fields and actual consumers; keep receiver phase/slot unknown.
"""
from pathlib import Path
import csv
import io
import json
import struct

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from .cn_receiver_owner_frontier169 import sha, mapped

SERVER = Path(__file__).resolve().parents[2]
ROOT = SERVER / 'artifacts/integration/packet-connections-20261006'
OUT = ROOT / 'tw-native-rom-geometry-source-01/agents/cn-slot-frontier'
EXE = SERVER.parent.parent / 'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY = EXE.parent.parent / 'God2_opt_source_recovery_20260926_055734/decompiled'
PIN = '582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
OWN = 'tools/reconstruction/cn_receiver_slot_frontier174.py'
SOURCE = ['AGENTS.md', 'docs/IMPLEMENTATION_PROVENANCE.md', 'docs/GOAL_ACCEPTANCE.md',
          'tools/reconstruction/cn_receiver_owner_frontier169.py',
          'tools/reconstruction/cn_computed_receiver_references.py',
          'tools/reconstruction/cn_cfg_receiver_references.py',
          'tools/reconstruction/cn_receiver_slot_frontier173.py', OWN]
NEW = {'005a4284', '005a42ef', '005a4319', '007a19aa', '007a1b12', '007a1bbc'}


def dump(rel, value):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write((json.dumps(value, indent=2, ensure_ascii=True) + '\n').encode())


def retain(rel, path, repository=False):
    raw = path.read_bytes()
    target = OUT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(raw)
    return {'path': path.relative_to(SERVER).as_posix() if repository else str(path),
            'copy': rel, 'bytes': len(raw), 'sha256': sha(raw)}


def main():
    if OUT.exists():
        raise RuntimeError('Preserve previous round174 evidence')
    raw = EXE.read_bytes()
    if sha(raw) != PIN:
        raise ValueError('Pinned CN original changed')
    metadata = list(csv.DictReader(io.StringIO((RECOVERY / 'functions.tsv').read_text(
        encoding='utf-8-sig')), delimiter='\t'))
    selected = [r for r in metadata if r['address'].lower() in NEW]
    OUT.mkdir(parents=True)
    originals = [retain('native-original-inputs/God2_opt.exe', EXE)]
    for name in ('functions.tsv', 'calls.tsv'):
        originals.append(retain('native-original-inputs/' + name, RECOVERY / name))
    for row in selected:
        originals.append(retain('native-original-inputs/' + row['address'].lower() + '.c',
                                RECOVERY / row['file']))
    dump('native-original-inputs.json', originals)
    dump('before-source-origins.json', [retain('before/' + rel, SERVER / rel, True) for rel in SOURCE])
    dump('new-source-absence.json', {'new_absent_from_root_before1246': [OWN], 'existing_cpp_edits': []})
    prior = [ROOT / 'cn-receiver-reachability-agent-01' / name
             for name in ('findings.json', 'reachability.json')]
    prior += [ROOT / 'cn-cfg-receiver-references-01/findings.json',
              ROOT / 'tw-native-mask-material-source-01/agents/cn-slot-frontier/findings.json',
              ROOT / 'tw-native-mask-material-source-01/agents/cn-slot-frontier/seal.json']
    dump('retained-prior/originals.json', [retain('retained-prior/' + str(i) + '-' + p.name, p)
                                        for i, p in enumerate(prior)])
    pe = pefile.PE(data=raw, fast_load=True)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    dump('native/selected-original-metadata.json', selected)
    instructions, spans = {}, []
    for row in selected:
        a = row['address'].lower()
        lo, size = int(a, 16), int(row['bytes'])
        offset, body = mapped(pe, raw, lo, lo + size)
        decoded = [{'va': f'{i.address:08x}', 'bytes': bytes(i.bytes).hex(),
                    'instruction': i.mnemonic + (' ' + i.op_str if i.op_str else '')}
                   for i in md.disasm(body, lo)]
        instructions.update({r['va']: r for r in decoded})
        path = OUT / ('native/functions/' + a + '.bin')
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(body)
        dump('native/functions/' + a + '.json', decoded)
        spans.append({'owner': a, 'start_va': f'{lo:08x}', 'end_va_exclusive': f'{lo+size:08x}',
                      'file_offset': offset, 'raw_bytes': body.hex(), 'sha256': sha(body),
                      'decoded_instruction_count': len(decoded),
                      'decoded_bytes': sum(len(bytes.fromhex(r['bytes'])) for r in decoded)})
    dump('native/new-sites.json', spans)
    calls = list(csv.DictReader(io.StringIO((RECOVERY / 'calls.tsv').read_text(
        encoding='utf-8-sig')), delimiter='\t'))
    dump('native/selected-original-calls.json', [r for r in calls
        if any(v.lower() in NEW for v in r.values())])
    data = []
    bounds = [('locale-table-a', 0x7f77a8, 0x7f7ec8),
              ('locale-table-b', 0x8418f8, 0x842018),
              ('literal-duplicate-table-b', 0x21afb8fc, 0x21afc01c),
              ('actual-a-string', 0x7f8524, 0x7f8530),
              ('actual-b-string', 0x8425fc, 0x842608),
              ('unknown-islands-numeric-context', 0x200baa90, 0x200bab00)]
    for label, lo, hi in bounds:
        offset, body = mapped(pe, raw, lo, hi)
        path = OUT / ('native/data/' + label + '.bin')
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(body)
        data.append({'label': label, 'start_va': f'{lo:08x}', 'end_va_exclusive': f'{hi:08x}',
                     'file_offset': offset, 'raw_bytes': body.hex(), 'sha256': sha(body)})
        if 'table' in label:
            dump('native/data/' + label + '-rows.json', [
                {'index': i, 'key_va': f'{lo+i*8:08x}', 'key': key, 'pointer_va': f'{pointer:08x}'}
                for i, (key, pointer) in enumerate(struct.iter_unpack('<II', body))])
    dump('native/new-data-sites.json', data)
    targets = [0x7f77a8, 0x7f77ac, 0x8418f8, 0x8418fc, 0x7f8524, 0x8425fc,
               0x7f7c58, 0x841da8, 0x200baaa0]
    references = []
    for value in targets:
        hits = []
        for section in pe.sections:
            if not section.PointerToRawData:
                continue
            body = raw[section.PointerToRawData:section.PointerToRawData+section.SizeOfRawData]
            index = body.find(struct.pack('<I', value))
            while index >= 0:
                va = int(pe.OPTIONAL_HEADER.ImageBase) + int(section.VirtualAddress) + index
                hits.append({'va': f'{va:08x}', 'file_offset': int(section.PointerToRawData)+index,
                             'raw_bytes': body[max(0,index-8):index+12].hex(),
                             'candidate_only_until_instruction_or_table_context': True})
                index = body.find(struct.pack('<I', value), index+1)
        references.append({'exact_value': f'{value:08x}', 'raw_file_candidates': hits,
                           'scan': 'these nine new table/field/string literal values only; no helper/global CFG rescan'})
    dump('native/bounded-table-address-references.json', references)

    def relation(identifier, scope, vas, labels, **fields):
        return {'id': identifier, 'scope': scope,
                'rawsites': [instructions[v] for v in vas],
                'raw_data_sites': [r for r in data if r['label'] in labels], **fields}

    relations = [
        relation('candidate-007f7c57-is-cross-field-locale-key',
            'Old unaligned helper-interior RVA match crosses row boundary. Actual aligned 007F7C58 key is00000813; next field points to UTF16 nl-BE. Exact native consumers binary-search scalar keys and load text pointers at index*8, not receiver dispatch.',
            ['005a431f', '005a432f', '005a4305', '005a430c', '005a42b1', '005a42bb'],
            ['locale-table-a', 'actual-a-string'], table_base='007f77a8', rows=228,
            old_candidate_va='007f7c57', aligned_key_va='007f7c58', aligned_key=0x813,
            actual_text_pointer='007f8524', actual_utf16_text='nl-BE', receiver_registration_proven=False),
        relation('candidate-00841da7-is-cross-field-locale-key',
            'Second old unaligned candidate also crosses aligned scalar fields. Actual00841DA8 key00000813 and008425FC UTF16 nl-BE text are consumed by binary key search and pointer load; declared original metadata names include LocaleNameToLCID.',
            ['007a19b2', '007a19c2', '007a1b48', '007a1b57', '007a1b77', '007a1bd4', '007a1bdb'],
            ['locale-table-b', 'actual-b-string'], table_base='008418f8', rows=228,
            old_candidate_va='00841da7', aligned_key_va='00841da8', aligned_key=0x813,
            actual_text_pointer='008425fc', actual_utf16_text='nl-BE', receiver_registration_proven=False),
        relation('islands-candidate-21afbdab-shares-complete-table-bytes',
            'The complete228-row table at21AFB8FC is byte-identical to008418F8, including actual scalar813 and text pointer. Literal duplication proves data identity only, not execution or helper reachability.',
            [], ['locale-table-b', 'literal-duplicate-table-b'],
            old_candidate_va='21afbdab', rows=228, complete_table_bytes_identical=True,
            duplicate_runtime_use_proven=False),
        relation('islands-candidate-200baa9f-crosses-scalar-boundary',
            'Bounded raw context has aligned0000480B at200BAA9C and00004813 at200BAAA0; old00481300 literal starts at preceding last byte. Table semantics/consumer remain unknown; no callable target is established.',
            [], ['unknown-islands-numeric-context'], old_candidate_va='200baa9f',
            aligned_scalar_va='200baaa0', aligned_scalar=0x4813, table_semantics=None,
            actual_consumer=None, receiver_registration_proven=False),
    ]
    findings = {'round': 174, 'version_scope': 'cn', 'native_sha256': PIN,
        'new_native_relations': relations, 'new_bounded_native_spans': len(spans),
        'new_bounded_native_bytes': sum(int(r['bytes']) for r in selected),
        'new_bounded_data_spans': len(data),
        'new_bounded_data_bytes': sum((hi-lo) for _, lo, hi in bounds),
        'old_raw_pointer_candidates_recounted': 0, 'old_global_cfg_spans_or_sites_recounted': 0,
        'old169_to173_spans_or_relations_recounted': 0,
        'receiver_contexts': 14, 'qualified_receiver_contexts': 12,
        'unresolved_helpers': [{'address': address, 'phase': None, 'slot': None, 'producer_pair': None}
                               for address in ('0047de70', '004812b0')],
        'new_phase_opcode_bindings': 0, 'new_formal_source_owner_chains': 0,
        'new_complete_bidirectional_routes': 0, 'new_cpp_files': 0,
        'whole_game_route_total': None, 'whole_game_completion_percent': None,
        'unreachable_proven': False, 'global_absence_proven': False, 'build_run': False,
        'tests_run': False, 'native_run': False, 'emulation_run': False,
        'database_access': False, 'deployed': False}
    dump('findings.json', findings)
    dump('stage-accounting.json', {'direction': 'unknown-S2C-receiver-table-selection-frontier',
        'new_actual_bounded_relations': len(relations), 'new_native_function_spans': len(spans),
        'new_confirmed_receiver_contexts': 0, 'new_opcode_inventory': 0, 'complete_routes_added': 0})
    dump('gaps.json', [
        'These exact old table candidates now have bounded aligned/native consumer context. They do not establish caller, registration, ECX transfer, phase, slot or producer pair for0047DE70/004812B0.',
        'Nine exact data-address searches are scoped literal candidates only; no-hit is not global absence or unreachable evidence. Old31 raw hits/79 spans/3735 sites remain old history.',
        'Unknown200BAA9F data consumer remains missing. Aligned numeric fields do not justify guessing a dispatch/vtable/encoded target.',
        'Next exact original trace root remains0047FC50 success continuation through actual scene owner slots, plus0047FAA0 actual caller after eligibility activation; recover an actual call/ECX transfer rather than another common gate.',
        'Original table consumers are preserved whole only for provenance. No font/locale conversion edit, runtime call, formatter155/capacity-chain analysis or validation was performed.',
    ])
    print(json.dumps({'artifact': str(OUT), 'new_native_spans': len(spans),
        'new_native_bytes': findings['new_bounded_native_bytes'], 'new_relations': len(relations),
        'new_data_spans': len(data), 'native_original_count': len(originals), 'new_phases': 0}))


def capture():
    if not (OUT / 'findings.json').is_file() or (OUT / 'seal.json').exists():
        raise RuntimeError('No unsealed delivery')
    dump('current-source-origins.json', [retain('current/' + rel, SERVER / rel, True) for rel in SOURCE])
    listing = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file())
    with (OUT / 'LIST.txt').open('xb') as stream:
        stream.write(('\n'.join(listing + ['LIST.txt']) + '\n').encode())
    rows = [{'path': p.relative_to(OUT).as_posix(), 'bytes': p.stat().st_size,
             'sha256': sha(p.read_bytes())} for p in sorted(OUT.rglob('*')) if p.is_file()]
    dump('seal.json', {'kind': 'immutable round174 CN exact table candidate consumers',
        'files': rows, 'native_input_sha256': PIN, 'source_original_count': len(SOURCE),
        'complete_routes_added': 0, 'build_run': False, 'tests_run': False,
        'native_run': False, 'database_access': False})
    print(json.dumps({'seal_sha256': sha((OUT / 'seal.json').read_bytes()),
        'members': len(rows), 'current_source_originals': len(SOURCE),
        'tool_sha256': sha((SERVER / OWN).read_bytes())}))


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['--capture-after-batchfinal']:
        capture()
    elif not sys.argv[1:]:
        main()
    else:
        raise SystemExit('Only file-only extraction or BATCHFINAL capture is supported')
