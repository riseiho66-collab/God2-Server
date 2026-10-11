"""Extract pinned ordinary-create UI name sources and actual resource rows.

File-only PE/resource accounting. Never execute the native loader, emulate
acceptance cases, load its DLLs, authorize a mutation or generate a reply.
"""
import csv
import hashlib
import importlib.util
import json
import struct
from collections import Counter

import capstone
import pefile

from .cn_pe_import_directory import FileView, import_directory
from .cn_wrapper_route_frontier import ROOT, CN, RECOVERY, PIN

NAME = 'cn-create-name-input-01'
ROUND = '20261007-cn-create-name-input'
TARGETS = (0x433b00, 0x43d8b0, 0x43d640, 0x440140, 0x458c70,
           0x4462f0, 0x446550, 0x445040, 0x4496f0, 0x423350,
           0x423390, 0x423480, 0x4234f0, 0x4231b0, 0x4232d0,
           0x422fd0, 0x45b270, 0x45a060, 0x74ff90, 0x749104)
SOURCES = ('tools/reconstruction/cn_create_name_input.py',
           'docs/research/cn-create-name-input-20261007.md',
           'src/cn/protocol/CnCharacterCreate.h')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    out = ROOT/'artifacts/integration/packet-connections-20261006'/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh before snapshot; preserve prior evidence')
    image = CN.parent/'XJZ-CN/God2_opt.exe'
    raw = image.read_bytes()
    if digest(raw) != PIN:
        raise RuntimeError('Pinned CN image changed')
    pe = pefile.PE(data=raw, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    view = FileView(pe, raw)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    files = []

    def save(rel, data, original):
        path = out/rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
        files.append({'path': rel, 'original': str(original), 'bytes': len(data),
                      'sha256': digest(data)})

    def dump(rel, value):
        save(rel, (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'),
             'file-only source interpretation; not execution evidence')

    with (RECOVERY/'functions.tsv').open(encoding='utf-8-sig') as stream:
        funcs = {row['address']: row for row in csv.DictReader(stream, delimiter='\t')}
    selected = []
    for va in TARGETS:
        key = f'{va:08x}'
        row = funcs[key]
        source = RECOVERY/row['file']
        code = view.read(va-base, int(row['bytes']))
        assembly = '\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}'
                             for i in md.disasm(code, va))+'\n'
        save('native/'+key+'.bin', code, image)
        save('native/'+key+'.asm', assembly.encode('utf-8'), image)
        save('decompiled/'+key+'.c', source.read_bytes(), source)
        selected.append({**row, 'native_sha256': digest(code),
                         'decompiled_sha256': digest(source.read_bytes())})
    dump('native-index.json', {'cn_sha256': PIN, 'functions': selected,
         'scope': 'metadata-sized source navigation spans; no whole-function CFG closure claim'})

    table = view.read(0x888210-base, 64)
    save('native/name-reserved-pointer-table.bin', table, image)
    patterns = []
    for index, va in enumerate(struct.unpack('<16I', table)):
        offset, available = view.window(va-base)
        window = raw[offset:offset+min(available, 64)]
        nul = window.find(b'\0')
        if nul < 0:
            raise ValueError('Unterminated fixed native name pattern')
        value = window[:nul]
        save(f'native/reserved-pattern-{index:02}.bin', value+b'\0', image)
        patterns.append({'index': index, 'va': f'{va:08x}', 'bytes_hex': value.hex(),
                         'byte_length': len(value)})
    dump('reserved-patterns.json', {'table_va': '00888210', 'patterns': patterns,
         'consumer': '0043D687 call0074FF90; nonzero ->SystemMessage205'})
    save('native/forbidwords-path.bin', view.read(0x7ef9c0-base, 35), image)
    save('native/dynamic-vector-file-bytes.bin', view.read(0x9edda0-base, 12), image)
    imports = import_directory(pe, raw)
    dump('dynamic-import-declarations.json', {
        'bindings': [row for row in imports['bindings'] if row.get('name') == 'StrStrA'],
        'callsite': '004463E3', 'loaded_binding_observed': False,
        'dll_implementation_executed_or_emulated': False})

    # Reuse the retained read-only decoder, not the native file loader or main().
    decoder = CN/'tools/reverse/recover_cn_login.py'
    save('retained-source/recover_cn_login.py', decoder.read_bytes(), decoder)
    spec = importlib.util.spec_from_file_location('retained_cn_resource_decoder', decoder)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    resource = CN.parent/'XJZ-CN/Data2/Patch/Comm/forbidwords.csvZ'
    packed = resource.read_bytes()
    plain = module.unpack_config(packed)
    if b'\0' in plain or b'\x1a' in plain:
        raise ValueError('Resource requires additional native text-mode analysis')
    save('resource/forbidwords.csvZ', packed, resource)
    save('resource/forbidwords.decoded.csv', plain, resource)
    # Current asset is CRLF text. Native fopen("r")/fgets translate CRLF.
    text_bytes = plain.replace(b'\r\n', b'\n')
    lines = text_bytes.splitlines(keepends=True)
    if not lines or max(map(len, lines)) >= 512:
        raise ValueError('Current header/lines exceed the qualified header read window')
    header_cells = lines[0].removesuffix(b'\n').split(b',')
    header_count = int(header_cells[2])
    if header_count != 2:
        raise ValueError('Recover changed native header skipping before accounting rows')
    # 004232D0(1) clamps the column budget to5. 00423390 skips count-2
    # lines after the header, i.e. zero here. 00423480 returns1 per read
    # line, NOT the parser's column count. The loader then copies column0.
    rows = []
    for line_index, line in enumerate(lines[1:], 1):
        comma = line.find(b',')
        delimiter = comma if comma >= 0 else line.find(b'\n')
        # 004234F0 does not commit an unterminated last field.
        value = line[:delimiter][:379] if delimiter >= 0 else b''
        if not value:
            continue
        if len(value) >= 256:
            raise ValueError('Current value exceeds native loader temporary buffer')
        rows.append({'source_line_index_zero_based': line_index,
                     'bytes_hex': value.hex(), 'byte_length': len(value)})
    declared = int(lines[3].removesuffix(b'\n').split(b',')[1])
    counts = Counter(row['bytes_hex'] for row in rows)
    dump('resource/native-loader-column0.json', {
        'packed_sha256': digest(packed), 'decoded_sha256': digest(plain),
        'header_skip_count': header_count-2, 'configured_column_budget': 5,
        'declared_body_terms': declared, 'column0_appends_on_one_successful_load': len(rows),
        'distinct_column0_bytes': len(counts), 'duplicate_occurrences': sum(c-1 for c in counts.values()),
        'rows': rows, 'native_runtime_vector_observed': False,
        'repeated_loader_calls_not_deduplicated_in_this_source': True})
    dump('name-input-source-contract.json', {
        'pin': PIN, 'scope': 'ordinary17 UI event only; not a server name policy',
        'event': '00440140 case11/bit1 calls0043D8B0 but ignores its result; checks name[0], then0043D640 EAX',
        'copy': '00433B00 copies min(encoded byte length,14) and NUL; no codepoint boundary repair',
        'edit_ready': '0043D8B0 AL from00458C70 is edit commit readiness, not the submission accept gate',
        'fixed14': 'A1 40 scan offsets0..12 over retained14-byte buffer, independent of earlierNUL; message203',
        'reserved': '16 explicit substring patterns at00888210, CRT0074FF90; message205',
        'legacy_window': 'first G/g orA2EF/A2D5 offset0..11; three following positions check4F/6D orA2F5/A2DB; can read through buffer offset16; preserve4F literal and postNUL bytes; message205',
        'dynamic': '004462F0 consumes009EDDA0..009EDDA4 24-byte strings; IAT-declaredStrStrA; AL1->message206, AL0->success',
        'loader': '00445040 callsite00445B12 ->00446550; source success result ignored here; vector not cleared or deduplicated in this loader',
        'resource_path': '.\\Data2\\Patch\\Comm\\forbidwords.csv',
        'columns': '004232D0(1) clamps to5; header2 skips0;00423480 alwaysEAX1 per fetched line, EOF0',
        'file_open': '0045B270 first tries path+Z/signature0516/0045A060 to temporary text file, then plain fallback',
        'runtime': 'vector file DWORDs are zero but loaded vector/times/locale/StrStrA body are unobserved',
        'wire': 'accepted UI state18 feeds retained43D280/47E900 ordinary17; no new opcode or complete mutation route',
        'rules_missing': ['actual server uniqueness/collation/reserved policy',
            'owned create operation, shared transaction/defaults, native02/18/03 issuers',
            'alternate1B upstream gate, all producers and native hosting/acceptance']})
    for rel in SOURCES:
        save('source/'+rel, (ROOT/rel).read_bytes(), ROOT/rel)
    findings = {
        'round': ROUND, 'previous_goal_turn_classification': 'no progress: acknowledgement only; safe static research resumed',
        'current_round_classification': 'progress: primary name-gate return values and actual resource loader rows recovered',
        'native_primary_function_spans_retained_not_routes': len(TARGETS),
        'fixed_native_reserved_patterns_not_packets': len(patterns),
        'resource_declared_body_terms': declared,
        'native_loader_column0_appends_per_successful_load': len(rows),
        'native_loader_metadata_rows_also_appended': [row['bytes_hex'] for row in rows[:3]],
        'native_runtime_vector_observed': False, 'new_native_opcode_values': 0,
        'new_phase_opcode_source_bindings': 0, 'new_source_owner_chains': 0,
        'new_complete_bidirectional_routes': 0, 'server_name_policy_added': False,
        'remaining': ['Native client input filter is not server authority: recover actual uniqueness/collation/name policy and operation owner.',
            'Complete17/19 common transactions, native02/1E/18/03 issuers and configured hosting remain open.',
            'Indirect/deferred/aggregate variants and whole-game route denominator remain open.'],
        'levels_changed': False, 'whole_game_route_total': None, 'whole_game_completion_percent': None,
        'build_run': False, 'tests_run': False, 'runtime_run': False, 'database_access': False, 'deployed': False}
    dump('findings.json', findings)
    dump('source-manifest.json', {'files': files})
    print(json.dumps({key: findings[key] for key in ('round',
        'fixed_native_reserved_patterns_not_packets', 'resource_declared_body_terms',
        'native_loader_column0_appends_per_successful_load', 'new_complete_bidirectional_routes')}))


if __name__ == '__main__':
    main()
