"""Import a bounded CN source snapshot. No build, execution or save access."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

SERVER = Path(__file__).resolve().parents[2]
CN = SERVER.parent.parent / 'God2-xjz/God2-Server-CN'
CLIENT = CN.parent / 'XJZ-CN/God2_opt.exe'
CLIENT_SHA = '582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SNAPSHOT = SERVER / 'artifacts/integration/packet-connections-20261006/cn-import-20261006-v1'
SOURCES = (
    'protocol/CnTransport.h', 'protocol/CnTransport.cpp',
    'protocol/CnNativeTables.h', 'protocol/CnAccountWire.h',
    'protocol/CnAccountReplies.h', 'protocol/CnAccountReplies.cpp',
    'net/CnTransportSession.h', 'net/CnTransportSession.cpp',
)
EVIDENCE = (
    'docs/NATIVE_TRANSPORT.md', 'docs/NATIVE_ACCOUNT_PHASE.md',
    'artifacts/native/20261006-cn-baseline/summary.json',
    'artifacts/native/20261006-cn-native-login-02/login-evidence.json',
    'artifacts/native/20261006-cn-account-phase-01/account-phase-evidence.json',
    'artifacts/integration/packet-route-ledger.json',
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    if SNAPSHOT.exists():
        raise FileExistsError('Preserve the existing snapshot; use a new import version')
    client_sha = sha(CLIENT.read_bytes())
    if client_sha != CLIENT_SHA:
        raise ValueError('CN client input does not match the selected native evidence')
    originals = {p: (CN / 'src' / p).read_bytes() for p in SOURCES}
    evidence = {p: (CN / p).read_bytes() for p in EVIDENCE}
    ledger = json.loads(evidence['artifacts/integration/packet-route-ledger.json'])
    if ledger['native_evidence']['client_sha256'] != client_sha:
        raise ValueError('CN source ledger client identity differs')
    destinations = {p: SERVER / 'src/cn' / p for p in SOURCES}
    if any(p.exists() for p in destinations.values()):
        raise FileExistsError('Never overwrite a previously adapted CN source')
    manifest = {
        'format': 'god2-cn-source-import-v1',
        'recorded_utc': datetime.now(timezone.utc).isoformat(),
        'upstream_root': str(CN), 'client': str(CLIENT), 'client_sha256': client_sha,
        'upstream_latest_round': ledger['latest_round'],
        'source_changes': 'Only include prefixes change from protocol/net to cn/protocol/cn/net',
        'upstream_modified': False, 'database_imported': False,
        'build_tests_client_execution_deployment': False,
        'complete_bidirectional_gameplay_routes_added': 0, 'sources': [], 'evidence': [],
    }
    for path, raw in originals.items():
        saved = SNAPSHOT / 'original/src' / path
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes(raw)
        adapted = raw.replace(b'#include "protocol/', b'#include "cn/protocol/').replace(
            b'#include "net/', b'#include "cn/net/')
        target = destinations[path]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(adapted)
        manifest['sources'].append({'upstream': 'src/' + path, 'upstream_sha256': sha(raw),
                                   'adapted': target.relative_to(SERVER).as_posix(),
                                   'imported_sha256': sha(adapted)})
    for path, raw in evidence.items():
        saved = SNAPSHOT / 'evidence' / path
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes(raw)
        manifest['evidence'].append({'upstream': path, 'sha256': sha(raw)})
    (SNAPSHOT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'snapshot': str(SNAPSHOT), 'source_files': len(SOURCES),
                      'evidence_files': len(EVIDENCE), 'client_sha256': client_sha}))


if __name__ == '__main__':
    main()
