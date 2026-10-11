"""New-directory operational snapshot; not a reconstruction certificate."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3

from runtime_evidence import RuntimeStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('artifacts'))
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--artifact', required=True)
    args = parser.parse_args()
    root, destination = args.root.resolve(strict=True), args.destination.absolute()
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copytree(args.evidence, destination/'operational-evidence')
    for name in ('hashes.json', 'metadata.json'):
        shutil.copy2(root/'clients'/args.artifact/name, destination/name)
    if (root/'proofs').exists():
        shutil.copytree(root/'proofs', destination/'proofs')
    records = destination/'verification-records'
    records.mkdir()
    for pattern in ('runtime-*', 'host-cdb-*'):
        for path in (root/'reports').glob(pattern):
            if path.is_file():
                shutil.copy2(path, records/path.name)
    with sqlite3.connect((root/'research.db').as_uri()+'?mode=ro', uri=True) as source:
        with sqlite3.connect(destination/'research.db') as backup:
            source.backup(backup)
    state = RuntimeStore(root).report(args.artifact, destination/'generated-status')
    for capture in state['captures']:
        cid = capture['capture_id']
        shutil.copytree(root/'runtime'/cid, destination/'runtime'/cid)
    tools = destination/'tool-sources'
    tools.mkdir()
    for path in Path(__file__).parent.iterdir():
        if path.suffix in ('.py', '.txt', '.ps1'):
            shutil.copy2(path, tools/path.name)
    files = {}
    for path in sorted(destination.rglob('*')):
        if path.is_file():
            with path.open('rb') as stream:
                files[path.relative_to(destination).as_posix()] = hashlib.file_digest(stream, 'sha256').hexdigest()
    manifest = {'schema_version': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
                'artifact_id': args.artifact, 'kind': 'OPERATIONAL_SNAPSHOT_NOT_CERTIFICATE',
                'files': files, 'capture_ids': [c['capture_id'] for c in RuntimeStore(root).status(args.artifact)['captures']]}
    raw = json.dumps(manifest, indent=2, sort_keys=True).encode()
    (destination/'snapshot.json').write_bytes(raw)
    print(json.dumps({'snapshot': str(destination), 'manifest_sha256': hashlib.sha256(raw).hexdigest()}))


if __name__ == '__main__':
    main()
