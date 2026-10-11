"""Compare only the three warning rows with current assets and recorded runtime."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/strike_lab'))
from omega_assets import decode_csvz


def main():
    corpus = ROOT / 'artifacts/legacy-evidence/xjz-20260820'
    database = corpus / 'files/XJZ-Server-Cpp/server_implementation/xjz_evidence.sqlite'
    with sqlite3.connect(database.as_uri() + '?mode=ro&immutable=1', uri=True) as db:
        legacy = {row[0]: dict(raw=json.loads(row[1]), source=row[2], line=row[3])
                  for row in db.execute("SELECT message_id,raw_json,raw_source,raw_line "
                                        "FROM client_message_template WHERE source_section='SystemMessage' "
                                        "AND message_id IN (285,905,916)")}
    asset = ROOT.parent / 'God2/Data2/Patch/Comm/message.csvZ'
    packed = asset.read_bytes()
    lines = decode_csvz(packed).splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(b'SystemMessage,'))
    count = int(lines[start].split(b',')[1])
    current = {}
    for line in lines[start+1:start+count+1]:
        fields = line.split(b',', 2)
        if fields[0] in (b'285', b'905', b'916'):
            current[int(fields[0])] = fields[2].decode('cp950')
    runtime_path = ROOT / 'artifacts/runs/warning-source-20260919-02/compat-events.jsonl'
    events = [json.loads(line) for line in runtime_path.read_text().splitlines()]
    warning = next(e for e in events if e.get('known_memory_warning'))
    matches = current[905] == warning['message_text']
    if set(legacy) != {285, 905, 916} or not matches:
        raise ValueError('Warning anchor mismatch')
    result = {
        'legacy_warning_anchor': 'VERIFIED',
        'anchor_scope': 'Message identity/localized meaning only, not build or implementation equivalence',
        'legacy_message_id': 905,
        'legacy_message_text': legacy[905]['raw'][2],
        'current_message_text': current[905],
        'current_message_match': matches,
        'legacy_current_byte_identical': False,
        'version_classification': 'VERSION_VARIANT_LOCALIZATION',
        'comparison': [{'id': key, 'legacy': legacy[key], 'current': current[key]} for key in sorted(legacy)],
        'warning_lookup_rva': '0xf25d',
        'lookup_evidence': 'Recorded native code checks table count >=0x389 (905), then reads the message pointer at table+0x3884; no blind immediate-only inference',
        'warning_callsite_rva': '0xf2c8',
        'messagebox_wrapper_return_rva': '0x2e0d',
        'dominating_branch_rva': '0xf246',
        'predicate': 'Unsigned uint32(EAX+ECX)<700 enters message-905 path; >=700 skips to 0xf2d0. Earlier 0xf186/0xf195 branches can instead select the message-916 path. Not a complete all-path no-warning proof.',
        'input_source': {
            'kind': 'PROCESS_STATE',
            'api_or_source': 'PagingFiles-related text parser plus indirect query [0x57040c]',
            'details': 'Format %s %d %d; ECX comes from parsed stack+0x0c. EAX is a 32-bit product/shift of query output slots. Live query target lies inside ddraw.dll, exact semantics unverified. Host reports system-managed ?:\\pagefile.sys and an allocated 17408 MB pagefile; this does not prove what the client query consumed.'
        },
        'natural_no_warning_possible': 'unknown',
        'fresh_client_run': 'NOT_RUN',
        'next_action': 'Keep live substrate blocked; require evidence for actual query semantics or a reproducible compatible environment before changing resource configuration or introducing a shim',
        'warning_solved': False,
        'source_hashes': {
            'archive': json.loads((corpus/'manifest.json').read_text())['archive_sha256'],
            'current_message_csvz': hashlib.sha256(packed).hexdigest(),
            'runtime_events': hashlib.sha256(runtime_path.read_bytes()).hexdigest(),
        },
        'evidence_boundary': 'Archive SQL/SQLite are historical evidence data, not executed instructions. No proof of historical OS query implementation was found in the warning-focused source search.'
    }
    output = ROOT / 'artifacts/spec-queries/god2-warning-source-result.json'
    output.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('legacy_warning_anchor', 'legacy_message_id',
                                           'current_message_match', 'natural_no_warning_possible', 'fresh_client_run')}))


if __name__ == '__main__':
    main()
