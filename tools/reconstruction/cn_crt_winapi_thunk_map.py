"""File-only mapping of pinned CRT dynamic API caches and literal call sources.

Does not invoke native code/APIs, emulate, build/test or access gameplay DBs.
Byte candidates, literal push sequences and metadata-rooted calls stay distinct.
"""
import bisect
import csv
import hashlib
import json
import struct

import capstone
from capstone.x86 import X86_OP_IMM
import pefile

from .cn_wrapper_route_frontier import ROOT, CN, RECOVERY, PIN
from .cn_pe_import_directory import FileView, import_directory
from .cn_delete_caller_seh_frontier import decode_cfg

NAME = 'cn-crt-winapi-thunk-map-01'
ROUND = '20261007-cn-crt-winapi-thunk-map'
LOOKUPS = {0x793212: ('ucrt', 0x9fa8f8, 32, 0x83ed10, 20),
           0x754938: ('vcrt', 0x9f9a78, 5, 0x83c3c4, 3)}
SOURCES = ('tools/reconstruction/cn_crt_winapi_thunk_map.py',
           'docs/research/cn-crt-winapi-thunk-map-20261007.md',
           'src/cn/protocol/CnCharacterDeleteReply.h')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    base = ROOT / 'artifacts/integration/packet-connections-20261006'
    out = base / NAME
    if not (out / 'before-manifest.json').exists() or (out / 'findings.json').exists():
        raise RuntimeError('Fresh before snapshot required; preserve deliveries')
    files = []

    def save(rel, raw, original):
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as stream:
            stream.write(raw)
        files.append({'path': rel, 'original': str(original), 'bytes': len(raw),
                      'sha256': digest(raw)})

    def dump(rel, value):
        save(rel, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode(),
             'primary-file static source recovery')

    prior = base / 'cn-crt-startup-callees-01'
    manifest = json.loads((prior / 'manifest.json').read_text(encoding='utf-8'))
    pins = {r['path']: r['sha256'] for r in manifest['files']}
    for rel in ('findings.json', 'ucrt-paired-initializer-chain.json',
                'encoded-signal-and-nested-init-source.json'):
        code = (prior / rel).read_bytes()
        if not manifest['sealed'] or digest(code) != pins[rel]:
            raise RuntimeError('Prior source provenance changed')
        save('retained-source/' + rel, code, prior / rel)
    exe = CN.parent / 'XJZ-CN/God2_opt.exe'
    raw = exe.read_bytes()
    if digest(raw) != PIN:
        raise RuntimeError('Pinned image changed')
    pe = pefile.PE(data=raw, fast_load=True)
    ib = pe.OPTIONAL_HEADER.ImageBase
    view = FileView(pe, raw)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    metadata = (RECOVERY / 'functions.tsv').read_bytes()
    rows = list(csv.DictReader(metadata.decode('utf-8-sig').splitlines(), delimiter='\t'))
    entries = {int(r['address'], 16): r for r in rows}
    starts = sorted(entries)
    decoded, captured = {}, {}

    def capture(entry):
        if entry in captured:
            return decoded[entry]
        row = entries[entry]
        code = view.read(entry - ib, int(row['bytes']))
        cfg, asm, ins = decode_cfg(md, code, entry, entry + len(code), {})
        name = f'{entry:08x}'
        save('native/functions/' + name + '.bin', code, str(exe) + ':VA' + name)
        save('native/functions/' + name + '.asm', asm, 'metadata-entry rooted bounded CFG')
        dump('native/functions/' + name + '-cfg.json', cfg)
        save('native/functions/' + name + '.c', (RECOVERY / row['file']).read_bytes(), RECOVERY / row['file'])
        decoded[entry] = ins
        captured[entry] = {'metadata': row, 'instructions': len(ins),
                           'open_edges': cfg['open_edges'], 'whole_program_reachability_proven': False}
        return ins

    def owner(site):
        index = bisect.bisect_right(starts, site) - 1
        if index >= 0:
            entry = starts[index]
            if site < entry + int(entries[entry]['bytes']):
                return entry
        return None

    refs = []
    for si, section in enumerate(pe.sections):
        if not section.Characteristics & 0x20000000:
            continue
        data = raw[section.PointerToRawData:section.PointerToRawData + section.SizeOfRawData]
        position = 0
        while True:
            position = data.find(b'\xe8', position)
            if position < 0:
                break
            if position + 5 <= len(data):
                site = ib + section.VirtualAddress + position
                target = (site + 5 + struct.unpack_from('<i', data, position + 1)[0]) & 0xffffffff
                if target in LOOKUPS:
                    entry = owner(site)
                    ins = capture(entry).get(site) if entry is not None else None
                    refs.append({'site': f'{site:08x}', 'target': f'{target:08x}',
                        'section': si, 'bytes': data[position:position + 5].hex(),
                        'metadata_owner': f'{entry:08x}' if entry is not None else None,
                        'entry_rooted_call': bool(ins and ins.mnemonic == 'call' and
                            bytes(ins.bytes) == data[position:position + 5]),
                        'whole_program_reachability_proven': False})
            position += 1

    modules = {}
    for target, (kind, cache, capacity, table, module_count) in LOOKUPS.items():
        capture(target)
        values_raw = view.read(table - ib, module_count * 4)
        save(f'native/modules/{kind}-table.bin', values_raw, str(exe) + ':module table')
        module_rows = []
        for index, ptr in enumerate(struct.unpack('<' + str(module_count) + 'I', values_raw)):
            text_raw = bytearray()
            for offset in range(0, 512, 2):
                word = view.read(ptr - ib + offset, 2)
                text_raw.extend(word)
                if word == b'\0\0':
                    break
            else:
                raise RuntimeError('Bounded DLL literal lacks terminator')
            text_raw = bytes(text_raw)
            save(f'native/modules/{kind}-{index}.bin', text_raw, str(exe) + ':DLL literal')
            module_rows.append({'id': index, 'name_pointer': f'{ptr:08x}',
                                'name': text_raw[:-2].decode('utf-16le'),
                                'loaded_module_observed': False})
        modules[kind] = module_rows

    requests, signatures = [], {}
    for ref in refs:
        site, target = int(ref['site'], 16), int(ref['target'], 16)
        kind, cache, capacity, table, module_count = LOOKUPS[target]
        # Four immediate pushes immediately preceding the actual rel32 CALL.
        # For missing metadata this is only a literal instruction sequence,
        # not proof that its apparent beginning is an authorized function entry.
        sequences = []
        for size in range(8, 21):
            code = view.read(site - size - ib, size)
            ins = list(md.disasm(code, site - size))
            if len(ins) == 4 and sum(i.size for i in ins) == size and all(
                    i.mnemonic == 'push' and len(i.operands) == 1 and
                    i.operands[0].type == X86_OP_IMM for i in ins):
                sequences.append(ins)
        if ref['entry_rooted_call']:
            actual = decoded[int(ref['metadata_owner'], 16)]
            rooted_sequences = [candidate for candidate in sequences if all(
                i.address in actual and bytes(actual[i.address].bytes) == bytes(i.bytes)
                for i in candidate)]
            if len(rooted_sequences) == 1:
                # A decode starting inside an immediate can imitate PUSH.
                # Actual entry-rooted instruction boundaries disambiguate it.
                sequences = rooted_sequences
        if len(sequences) != 1:
            ref['argument_recovery'] = 'open: four-immediate-push sequence not unique'
            continue
        ins = sequences[0]
        end, begin, name, function_id = (i.operands[0].imm & 0xffffffff for i in ins)
        rooted_args = False
        if ref['entry_rooted_call']:
            actual = decoded[int(ref['metadata_owner'], 16)]
            rooted_args = all(i.address in actual and bytes(actual[i.address].bytes) == bytes(i.bytes) for i in ins)
        if function_id >= capacity or begin > end or (end - begin) % 4 or end - begin > 256:
            ref['argument_recovery'] = 'open: out-of-range literal arguments'
            continue
        name_text = view.string(name - ib)
        module_raw = view.read(begin - ib, end - begin)
        ids = list(struct.unpack('<' + str(len(module_raw) // 4) + 'I', module_raw)) if module_raw else []
        if any(i >= module_count for i in ids):
            ref['argument_recovery'] = 'open: DLL id outside primary cache range'
            continue
        signature = (kind, function_id, name, begin, end)
        if signature not in signatures:
            seq = len(signatures)
            save(f'native/requests/{seq}-name.bin', view.read(name - ib, len(name_text) + 1), exe)
            save(f'native/requests/{seq}-modules.bin', module_raw, exe)
            signatures[signature] = {'kind': kind, 'function_id': function_id,
                'name': name_text, 'name_va': f'{name:08x}', 'cache_slot': f'{cache + function_id * 4:08x}',
                'modules_begin': f'{begin:08x}', 'modules_end': f'{end:08x}',
                'candidate_modules_in_native_order': [modules[kind][i] for i in ids],
                'source_call_sites': [], 'metadata_rooted_argument_call_sites': [],
                'loaded_address_or_execution_observed': False}
        record = signatures[signature]
        record['source_call_sites'].append(ref['site'])
        if rooted_args:
            record['metadata_rooted_argument_call_sites'].append(ref['site'])
        prefix_raw = view.read(ins[0].address - ib, site + 5 - ins[0].address)
        save('native/call-arguments/' + ref['site'] + '.bin', prefix_raw, str(exe) + ':actual argument/CALL byte sequence')
        requests.append({'site': ref['site'], 'lookup': ref['target'], 'kind': kind,
            'function_id': function_id, 'name': name_text, 'sequence_begin': f'{ins[0].address:08x}',
            'metadata_rooted_argument_sequence': rooted_args,
            'literal_push_sequence_only': not rooted_args,
            'loaded_execution_observed': False})
        ref['argument_recovery'] = 'primary literal pushes; rooted status separate'

    # Concrete resolver/encode/initializer and uncached resolver source spans.
    for entry in (0x754796, 0x754874, 0x7549a7, 0x754a41,
                  0x754baf, 0x754bd8, 0x752bb9,
                  0x7931ee, 0x7932ae, 0x793329, 0x79335d, 0x793f72):
        if entry in entries:
            capture(entry)
    imports = import_directory(pe, raw)
    selected = [r for r in imports['bindings'] if int(r['iat_va'], 16) in
                (0x7eb58c, 0xaaf41c, 0xaafd78, 0x7eb4e0) or
                r['name'] in ('LoadLibraryExW', 'GetLastError')]
    dump('primary-import-declarations.json', {'bindings': selected,
         'loaded_iat_or_api_behavior_observed': False})
    thunk = view.read(0x74a8e2 - ib, 6)
    save('native/0074a8e2-import-tail.bin', thunk, exe)
    dump('cache-lifetime-and-resolver-source.json', {
        'ucrt': {'initializer': '00793E1F', 'cache_begin': '009FA8F8', 'slots': 32,
                 'module_cache_begin': '009FA8A8', 'module_slots': 20,
                 'lookup': '00793212', 'module_lookup': '007932AE',
                 'decode': 'ROR32(cache XOR cookie, cookie&31)',
                 'missing_function_sentinel': 'Encoded FFFFFFFF returns null without lookup retry.',
                 'module_fallback': 'LoadLibraryExW(name,0,800h); only error57h selects flags0 fallback.',
                 'uninitialize': '00793F72 with argument0 frees nonzero/non-FFFFFFFF cached modules and clears their cells.'},
        'vcrt': {'initializer': '00754BAF', 'initializer_caller': '00752BB9',
                 'cache_begin': '009F9A78', 'slots': 5,
                 'module_cache_begin': '009F9A6C', 'module_slots': 3,
                 'lookup': '00754938', 'module_loop': '00754874',
                 'module_fallback': 'Error57h may use flags0 only after excluding api-ms-/ext-ms- names.',
                 'uninitialize': '00754BD8 argument0 frees cached nonzero/non-FFFFFFFF modules then clears cells.'},
        'encoded_pointer_helper': '00754796',
        'function_cache_publish': 'XCHG with actual cache cell; file value is not loaded function VA.',
        'uncached_resolver': '00793329 also performs module-loop/GetProcAddress without either function-cache index; its actual call sources remain an additional frontier.',
        '0074a8e2': 'Primary JMP [00AAFD78] declares IsProcessorFeaturePresent; no loaded target observed.',
        'dll_loading_or_exception_registration_exhausted': False,
        'native1e_result_proven': False})
    dump('lookup-call-candidates.json', refs)
    dump('literal-lookup-arguments.json', requests)
    dump('dynamic-api-cache-map.json', {'module_tables': modules,
        'function_requests': list(signatures.values()),
        'literal_sequences_do_not_prove_missing_metadata_function_entries': True,
        'whole_program_dynamic_api_coverage_proven': False})
    preserved = []
    for rel in ('src/core/Application.cpp', 'src/net/Session.cpp',
                'src/auth/RecoveredAccountLogin.cpp', 'src/auth/SharedTaiwanCharacterRemoval.cpp',
                'src/cn/auth/SharedCharacterDeleteOperation.cpp'):
        code = (ROOT / rel).read_bytes()
        if code != (out / 'before' / rel).read_bytes():
            raise RuntimeError('Existing/frozen source changed')
        preserved.append({'path': rel, 'byte_identical': True, 'sha256': digest(code)})
    findings = {'round': ROUND, 'native_sha256': PIN,
        'previous_goal_turn_classification': 'progress: sealed99 CRT function envelopes and15 internal paired initializers; source remains incomplete',
        'primary_rel32_lookup_byte_candidates_not_routes': len(refs),
        'metadata_rooted_lookup_calls_not_routes': sum(r['entry_rooted_call'] for r in refs),
        'primary_literal_argument_sequences_not_packets': len(requests),
        'metadata_rooted_literal_argument_sequences': sum(r['metadata_rooted_argument_sequence'] for r in requests),
        'literal_sequences_without_metadata_rooted_entry': sum(r['literal_push_sequence_only'] for r in requests),
        'ucrt_distinct_requested_function_ids_not_packets': len({r['function_id'] for r in requests if r['kind'] == 'ucrt'}),
        'vcrt_distinct_requested_function_ids_not_packets': len({r['function_id'] for r in requests if r['kind'] == 'vcrt'}),
        'distinct_request_signatures_not_packets': len(signatures),
        'primary_dll_pointer_table_cells_not_packets': sum(len(r) for r in modules.values()),
        'exact_metadata_function_spans_retained': len(captured),
        'function_spans_with_open_frontier': sum(bool(r['open_edges']) for r in captured.values()),
        'new_packet_values': 0, 'new_native_phase_source_bindings': 0,
        'new_source_owner_chains': 0, 'new_complete_bidirectional_routes': 0,
        'native1e_outcome_proven': False, 'whole_program_dynamic_exception_closure': False,
        'formal_application_hosted': False, 'preserved_existing_sources': preserved,
        'whole_game_route_total': None, 'whole_game_completion_percent': None,
        'levels_changed': False, 'build_run': False, 'tests_run': False,
        'runtime_run': False, 'database_access': False, 'deployed': False,
        'remaining': [
            'Root missing-metadata literal helpers from actual callers; retain the uncached resolver00793329 and other loader/action sources as separate frontiers.',
            'Live per-thread signal actions, loaded context repair and CN1E post-DeleteFileA FIST[EAX] result remain unresolved.',
            'Actual shared TW/CN auth/mutation policy, guild/replay/full02/03/durable receipt and Application hosting remain incomplete.',
            'Whole-game phase/state/variant/indirect/deferred denominator and native/web gameplay remain open.']}
    doc = ROOT / SOURCES[1]
    if doc.exists():
        raise RuntimeError('Preserve prior research document')
    doc.write_text('# CN primary CRT WinAPI caches and actual lookup sources\n\n'
        'PHASE1 file-only static source recovery. No native/API/DLL/emulation/server execution, build/test, gameplay DB access or deployment. Native levels unchanged. CN SHA256 ' + PIN + '.\n\n'
        f'Two actual cache resolvers00793212 and00754938 have{len(refs)} rel32 byte candidates. {findings["metadata_rooted_lookup_calls_not_routes"]} align with metadata-entry rooted CFGs. Each literal argument sequence is preserved separately; missing metadata helpers are not silently promoted into actual function-entry/global reachability claims.\n\n'
        f'Four immediate pushes recover{len(requests)} lookup argument sequences, mapping{findings["ucrt_distinct_requested_function_ids_not_packets"]} UCRT and{findings["vcrt_distinct_requested_function_ids_not_packets"]} VCRT function IDs to exact ASCII names, encoded function cache slots and DLL candidates in original order. Primary DLL pointer tables have20 and3 entries. These are cache IDs and API names, not packet opcodes or completed routes. Primary bytes, per-call qualification, modules and source spans are retained.\n\n'
        'UCRT startup00793E1F initializes32 encoded-null slots at9FA8F8; resolver00793212 decodes ROR32(cell XOR cookie,cookie&31). DecodedFFFFFFFF suppresses retries; decoded0 attempts module lookup/GetProcAddress and publishes encoded success or missing sentinel with actualXCHG. UCRT module helper007932AE uses LoadLibraryExW flag800h and only error57h permits flags0 fallback. Uninit00793F72 argument0 frees nonzero/non-FFFFFFFF cached module handles at9FA8A8..9FA8F8 and clears cells.\n\n'
        'VCRT00752BB9 directly calls00754BAF to initialize5 slots at9F9A78, separately from UCRT. Module range has3 cells beginning9F9A6C. Its module-loop00754874 additionally excludes api-ms-/ext-ms- names before the error57h/flags0 fallback. Uninit00754BD8 argument0 frees cached handles and clears cells. No original DLL is loaded by this reader; file IAT values are metadata, never loaded addresses.\n\n'
        'Uncached resolver00793329 is a separate GetProcAddress path and is not closed by recovering the32+5 cache IDs. Previous open tail0074A8E2 is retained as primary JMP[AAFD78] declaring IsProcessorFeaturePresent; this still does not observe its loaded target. API names or cache coverage cannot prove absence of runtime VEH/SEH/signal/context modifications elsewhere. CN1E outcome remains unknown.\n\n'
        'New packet values/owner chains/source bindings/full bidirectional routes all0; whole-game denominator and completion percent null. Frozen/common runtime source byte-identical; only native decoder provenance gains this reference. Next connect actual missing helper callers and uncached lookup sources while continuing actual auth/permission/guild/replay/full02/03/common-host sources; no invented permission or success response.\n', encoding='utf-8')
    for rel in SOURCES:
        save('source/' + rel, (ROOT / rel).read_bytes(), ROOT / rel)
    dump('native-function-index.json', {'metadata_sha256': digest(metadata),
        'functions': {f'{k:08x}': v for k, v in captured.items()}})
    dump('findings.json', findings)
    dump('source-manifest.json', {'files': files})
    print(json.dumps({k: findings[k] for k in ('round',
        'primary_rel32_lookup_byte_candidates_not_routes', 'metadata_rooted_lookup_calls_not_routes',
        'primary_literal_argument_sequences_not_packets', 'metadata_rooted_literal_argument_sequences',
        'ucrt_distinct_requested_function_ids_not_packets', 'vcrt_distinct_requested_function_ids_not_packets',
        'exact_metadata_function_spans_retained', 'new_complete_bidirectional_routes')}))


if __name__ == '__main__':
    main()
