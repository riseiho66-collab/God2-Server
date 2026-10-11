"""Primary file-only CRT callee, paired-init and encoded signal-slot recovery.

No image loading, emulation, DLL/API invocation, builds, tests or database use.
Bounded rooted CFGs retain open calls/transfers; they are not gameplay routes.
"""
import bisect
import csv
import hashlib
import json
import struct

import capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM
import pefile

from .cn_wrapper_route_frontier import ROOT, CN, RECOVERY, PIN
from .cn_pe_import_directory import FileView, import_directory
from .cn_delete_caller_seh_frontier import decode_cfg

NAME = 'cn-crt-startup-callees-01'
ROUND = '20261007-cn-crt-startup-callees'
SOURCES = ('tools/reconstruction/cn_crt_startup_callees.py',
           'docs/research/cn-crt-startup-callees-20261007.md',
           'src/cn/protocol/CnCharacterDeleteReply.h')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    base = ROOT / 'artifacts/integration/packet-connections-20261006'
    out = base / NAME
    if not (out / 'before-manifest.json').exists() or (out / 'findings.json').exists():
        raise RuntimeError('Fresh before snapshot required; preserve earlier evidence')
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
             'bounded primary-file recovery; no native execution')

    prior = base / 'cn-delete-caller-seh-frontier-01'
    manifest = json.loads((prior / 'manifest.json').read_text(encoding='utf-8'))
    pins = {r['path']: r['sha256'] for r in manifest['files']}
    retained = {}
    for rel in ('findings.json', 'crt-startup-callback-index.json',
                'crt-main-seh4-source-chain.json'):
        raw = (prior / rel).read_bytes()
        if digest(raw) != pins[rel] or not manifest['sealed']:
            raise RuntimeError('Sealed primary provenance changed')
        save('retained-source/' + rel, raw, prior / rel)
        retained[rel] = json.loads(raw)
    # Derive actual callee roots from the earlier qualified table-rooted CFGs,
    # not from guessed function names or byte-pattern-only call candidates.
    prior_roots = retained['crt-startup-callback-index.json']['roots']
    direct = {int(e['target'], 16) for r in prior_roots for e in r['calls']
              if len(e['target']) == 8 and all(c in '0123456789abcdef' for c in e['target'])}
    tail = {0x5a0a48, 0x745b91}
    exe = CN.parent / 'XJZ-CN/God2_opt.exe'
    raw = exe.read_bytes()
    if digest(raw) != PIN:
        raise RuntimeError('Pinned CN image changed')
    pe = pefile.PE(data=raw, fast_load=True)
    view = FileView(pe, raw)
    ib = pe.OPTIONAL_HEADER.ImageBase
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    metadata = (RECOVERY / 'functions.tsv').read_bytes()
    rows = list(csv.DictReader(metadata.decode('utf-8-sig').splitlines(), delimiter='\t'))
    entries = {int(r['address'], 16): r for r in rows}
    starts = sorted(entries)
    imports = import_directory(pe, raw)
    # Preserve all matching descriptors in case primary import arrays alias.
    bindings = {}
    for binding in imports['bindings']:
        bindings.setdefault(int(binding['iat_va'], 16), []).append(binding)

    table_lo, table_hi = 0x83e390, 0x83e408
    table_raw = view.read(table_lo - ib, table_hi - table_lo)
    save('native/ucrt-paired-initializers.bin', table_raw, str(exe) + ':0083E390..0083E408')
    pairs = []
    paired_targets = set()
    for i, (init, uninit) in enumerate(struct.iter_unpack('<II', table_raw)):
        paired_targets.update(x for x in (init, uninit) if x)
        pairs.append({'index': i, 'cell': f'{table_lo + i * 8:08x}',
                      'initialize': f'{init:08x}', 'uninitialize': f'{uninit:08x}',
                      'loaded_execution_observed': False})
    # These additional roots are actual references in the CRT source chain.
    explicit = {0x748bbd, 0x78bb99, 0x79a119, 0x79a63f, 0x74a4d6,
                0x75aa17, 0x79a289, 0x78c6bb, 0x78a55c,
                0x7496db, 0x7496f8, 0x78e35f, 0x79a59b}
    roots = direct | tail | paired_targets | explicit
    boundaries = sorted(set(starts) | roots)
    captured, decoded = {}, {}

    def capture(target, authority):
        name = f'{target:08x}'
        if name in captured:
            captured[name]['root_sources'].append(authority)
            return
        row = entries.get(target)
        if row:
            hi = target + int(row['bytes'])
            exact = True
        else:
            _, available = view.window(target - ib)
            n = bisect.bisect_right(boundaries, target)
            next_start = boundaries[n] if n < len(boundaries) else target + available
            hi = min(target + available, next_start, target + 4096)
            exact = False
        code = view.read(target - ib, hi - target)
        cfg, asm, instructions = decode_cfg(md, code, target, hi, {})
        decoded[name] = instructions
        save('native/functions/' + name + '.bin', code, str(exe) + ':VA' + name)
        save('native/functions/' + name + '.asm', asm, 'entry-rooted file-only CFG; callees open')
        dump('native/functions/' + name + '-cfg.json', cfg)
        if row:
            save('native/functions/' + name + '.c', (RECOVERY / row['file']).read_bytes(),
                 RECOVERY / row['file'])
        calls = []
        for ins in instructions.values():
            if not ins.group(capstone.CS_GRP_CALL):
                continue
            op = ins.operands[0]
            item = {'site': f'{ins.address:08x}', 'bytes': bytes(ins.bytes).hex(),
                    'operand': ins.op_str, 'called_code_not_followed': True}
            if op.type == X86_OP_IMM:
                item['direct_target'] = f'{op.imm & 0xffffffff:08x}'
            elif op.type == X86_OP_MEM and not op.mem.base and not op.mem.index:
                iat = op.mem.disp & 0xffffffff
                item['absolute_slot'] = f'{iat:08x}'
                item['declared_import_bindings'] = bindings.get(iat, [])
            calls.append(item)
        captured[name] = {'metadata': row, 'exact_metadata_entry': exact,
            'end_exclusive': f'{hi:08x}', 'root_sources': [authority],
            'envelope_is_static_bound_not_exact_function_size': not exact,
            'instructions': len(instructions), 'calls': calls, 'open_edges': cfg['open_edges'],
            'whole_program_reachability_proven': False}

    for target in sorted(direct):
        capture(target, 'actual call from a previous primary initterm callback root')
    for target in sorted(tail):
        capture(target, 'actual previous callback-root external jump; still bounded')
    for target in sorted(paired_targets):
        capture(target, 'primary internal UCRT paired initializer/uninitializer table pointer')
    for target in sorted(explicit):
        capture(target, 'explicit actual CRT helper reference; graph closure not implied')

    # Exact immediate sites: trace DLL/API lookup arguments at their native PCs.
    dynamic = []
    literals = ((0x74974a, 0x832878, 'utf-16le', 'GetModuleHandleW'),
                (0x74975b, 0x8001d0, 'utf-16le', 'GetModuleHandleW'),
                (0x749770, 0x8328bc, 'ascii', 'GetProcAddress'),
                (0x74977c, 0x8328d8, 'ascii', 'GetProcAddress'),
                (0x74978a, 0x8328f4, 'ascii', 'GetProcAddress'))
    for site, address, encoding, api in literals:
        instructions = decoded['00749715']
        ins = instructions.get(site)
        if not ins or ins.mnemonic != 'push' or ins.operands[0].type != X86_OP_IMM or ins.operands[0].imm != address:
            raise RuntimeError(f'Lookup literal source not rooted at {site:08x}')
        if encoding == 'ascii':
            text = view.string(address - ib)
            data = view.read(address - ib, len(text) + 1)
        else:
            data = bytearray()
            for offset in range(0, 512, 2):
                word = view.read(address - ib + offset, 2)
                data.extend(word)
                if word == b'\0\0':
                    break
            else:
                raise RuntimeError('Bounded UTF16 literal lacks terminator')
            data = bytes(data)
            text = data[:-2].decode('utf-16le')
        save(f'native/literals/{address:08x}.bin', data, str(exe) + ':literal')
        dynamic.append({'push_site': f'{site:08x}', 'literal_va': f'{address:08x}',
                        'literal': text, 'encoding': encoding, 'requested_api': api,
                        'loaded_resolution_observed': False})
    dump('thread-static-dynamic-resolution.json', {
        'owner': '00749715', 'literal_arguments': dynamic,
        'get_module_handle_iat': bindings.get(0x7eb3d8, []),
        'get_proc_address_iat': bindings.get(0x7eb58c, []),
        'fallback_event_iat': bindings.get(0x7eb374, []),
        'resolved_functions': ['InitializeConditionVariable', 'SleepConditionVariableCS', 'WakeAllConditionVariable'],
        'success_path': 'All three nonzero: initialize9F9870 through actual guarded EBX; encode EDI/ESI into9F9878/9F987C.',
        'fallback_path': 'CreateEventW(0,1,0,0) ->9F9874; missing handle reaches fastfail helper.',
        'exception_or_delete_eip_repair_source_qualified': False,
        'other_dynamic_api_sources_exhausted': False})
    dump('ucrt-paired-initializer-chain.json', {
        'scrt_entry': '00748BBD', 'ucrt_entry': '0078BB99', 'executor': '0079A119',
        'primary_table_begin': f'{table_lo:08x}', 'primary_table_end': f'{table_hi:08x}',
        'pairs': pairs, 'pair_stride': 8,
        'normal': 'Each nonzero initializer is guard-qualified then indirectly called; AL0 stops iteration.',
        'failure': 'Backtrack prior pairs with nonzero initializer and uninitializer, passing0; uninit-only pairs are skipped by this failure loop.',
        'scrt_failure': 'After successful VCRT initialization, failed UCRT initialization calls VCRT uninitialize(0).',
        'actual_callback_execution_observed': False, 'rollback_is_gameplay_sql_recovery': False})
    dump('encoded-signal-and-nested-init-source.json', {
        'startup_root': '0078BAA8', 'cookie_slot': '008A6194',
        'encoded_null': 'ESI=0; count=32-(cookie&31); ROR ESI,CL remains0; XOR ESI,cookie produces encoded-null argument.',
        'actual_calls': [{'site': s, 'target': t} for s, t in (
            ('0078BAC1', '0075AA17'), ('0078BAC7', '0079A289'),
            ('0078BACD', '0079A63F'), ('0078BAD3', '0078C6BB'), ('0078BAD9', '0078A55C'))],
        'signal_initializer': '0079A63F copies the supplied encoded pointer into9FA9C4/9FA9C8/9FA9CC/9FA9D0 via dual-state initialization helpers.',
        'signal_default_slots_prove_runtime_per_thread_action_table': False,
        'nested_initializer': {'entry': '0074A4D6', 'begin': '00856EE0', 'end': '00856EE0',
                               'file_literal_range_empty': True,
                               'loaded_state_or_all_startup_callbacks_empty': False},
        'native1e_result_proven': False, 'whole_program_exception_or_code_repair_absence_proven': False})

    preserved = []
    for rel in ('src/core/Application.cpp', 'src/net/Session.cpp',
                'src/auth/RecoveredAccountLogin.cpp', 'src/auth/SharedTaiwanCharacterRemoval.cpp',
                'src/cn/auth/SharedCharacterDeleteOperation.cpp'):
        code = (ROOT / rel).read_bytes()
        if code != (out / 'before' / rel).read_bytes():
            raise RuntimeError('Frozen/existing source changed')
        preserved.append({'path': rel, 'byte_identical': True, 'sha256': digest(code)})
    findings = {'round': ROUND, 'native_sha256': PIN,
        'previous_goal_turn_classification': 'no progress: level-preservation acknowledgement only; existing evidence re-read and actual CRT recovery now resumed',
        'prior_startup_direct_callee_roots_not_packets': len(direct),
        'prior_startup_tail_jump_roots_not_packets': len(tail),
        'native_function_envelopes_retained': len(captured),
        'function_envelopes_without_exact_metadata': sum(not r['exact_metadata_entry'] for r in captured.values()),
        'function_envelopes_with_open_frontier': sum(bool(r['open_edges']) for r in captured.values()),
        'internal_ucrt_paired_initializer_entries_not_packets': len(pairs),
        'internal_ucrt_nonzero_initializer_cells': sum(r['initialize'] != '00000000' for r in pairs),
        'internal_ucrt_nonzero_uninitializer_cells': sum(r['uninitialize'] != '00000000' for r in pairs),
        'internal_ucrt_distinct_function_roots_not_packets': len(paired_targets),
        'dynamic_sync_function_name_literals_not_packets': 3,
        'encoded_signal_default_slots_not_runtime_handlers': 4,
        'primary_metadata_sha256': digest(metadata),
        'new_packet_values': 0, 'new_native_phase_source_bindings': 0,
        'new_source_owner_chains': 0, 'new_complete_bidirectional_routes': 0,
        'native1e_outcome_proven': False, 'crt_initializers_exhaustively_followed': False,
        'whole_program_exception_or_loaded_repair_absence_proven': False,
        'formal_application_hosted': False, 'preserved_existing_sources': preserved,
        'whole_game_route_total': None, 'whole_game_completion_percent': None,
        'levels_changed': False, 'build_run': False, 'tests_run': False,
        'runtime_run': False, 'database_access': False, 'deployed': False,
        'remaining': [
            'Follow the newly retained actual callees, open tail transfers and runtime exception/code-patch registration sources; this bounded graph is not whole-program closure.',
            'Actual per-thread exception actions and loaded context repair at CN1E DeleteFileA/FIST[EAX] remain unresolved.',
            'TW/CN native mutation permission/guild/replay/durable receipt/full02/03 issuer and actual common Application host remain missing.',
            'Whole-game phase/state/variant/indirect/deferred denominator and native/web gameplay remain incomplete.']}
    doc = ROOT / SOURCES[1]
    if doc.exists():
        raise RuntimeError('Preserve previous research')
    doc.write_text('# CN CRT actual callees and paired initialization\n\n'
        'PHASE1: file-only primary PE/CFG/source analysis. No builds, tests, emulation, DLL/API/native/server execution, DB access or deployment. Levels unchanged. CN SHA256 ' + PIN + '.\n\n'
        f'From the prior215 primary initterm callback roots, retain{len(direct)} actual direct callee entries and two external tail-jump roots. Together with concrete internal CRT table pointers and selected helper references, retain{len(captured)} distinct function envelopes. Exact functions.tsv spans and bounded metadata-missing envelopes are labeled separately; calls and exception/indirect transfers stay open. No loaded reachability or exact unknown function-end claim.\n\n'
        '00748BBD invokes VCRT then UCRT initialization; failure of the latter invokes VCRT uninitialize(0). UCRT0078BB99 passes0083E390..0083E408 to0079A119. The primary120-byte range contains15 initialize/uninitialize pairs, not15 packets. The executor uses stride8, actual control-flow guard then callback, stops onAL0 and unwinds prior successful pairs with both pointers nonzero. Uninit-only cells do not become invoked rollback actions in that failure loop. This is CRT lifetime behavior, not game save recovery.\n\n'
        'Actual initializer0078BAA8 computes encoded NULL from the cookie008A6194 and passes it to0075AA17,0079A289,0079A63F,0078C6BB,0078A55C. Signal helper0079A63F writes supplied values through dual-state initialization to9FA9C4/9FA9C8/9FA9CC/9FA9D0. Default encoded signal slots do not determine the live per-thread action table used by0078A0E0 or prove deletion exception repair absent. The raw primary nested range in0074A4D6 has both bounds00856EE0; this zero-length literal range does not prove all loaded initialization is empty.\n\n'
        'Thread-static initializer00749715 resolves api-ms-win-core-synch-l1-2-0.dll with kernel32.dll fallback and the literal names InitializeConditionVariable, SleepConditionVariableCS and WakeAllConditionVariable. Primary IAT declarations and exact push sites are retained. Nonzero functions select guarded initialization/encoded callback storage; otherwise the actual code uses CreateEventW(0,1,0,0). These named lookups concern synchronization; they do not supply a VEH/EIP repair for the deletion wrapper. Other dynamic APIs and runtime handler changes remain open. File IAT name RVAs are never treated as loaded targets.\n\n'
        'New packet values, partial-owner chains, source bindings and complete bidirectional routes all0. Whole-game totals and completion percentage null. Existing Application/Session/auth/common deletion behavior unchanged; the native reader only gains a provenance comment. CN1E result and actual native permission/guild/replay/durable receipt/full02/03/common hosting remain open. Next pursue actual referenced thunks/actions and native permission sources rather than treating CRT callbacks as gameplay coverage.\n', encoding='utf-8')
    for rel in SOURCES:
        save('source/' + rel, (ROOT / rel).read_bytes(), ROOT / rel)
    dump('native-function-index.json', {'metadata_original': str(RECOVERY / 'functions.tsv'),
                                      'metadata_sha256': digest(metadata), 'functions': captured})
    dump('findings.json', findings)
    dump('source-manifest.json', {'files': files})
    print(json.dumps({k: findings[k] for k in (
        'round', 'prior_startup_direct_callee_roots_not_packets',
        'native_function_envelopes_retained', 'function_envelopes_without_exact_metadata',
        'internal_ucrt_nonzero_initializer_cells', 'internal_ucrt_nonzero_uninitializer_cells',
        'new_complete_bidirectional_routes')}))


if __name__ == '__main__':
    main()
