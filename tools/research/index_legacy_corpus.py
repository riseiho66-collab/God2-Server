"""Isolated ZIP ingestion; archive contents are data, never executable instructions."""
import argparse
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import stat
import zipfile


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--classification', default='GOD2_LEGACY_SERVER_EVIDENCE_CORPUS')
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    evidence = root / 'files'
    evidence.mkdir()
    records = []
    with zipfile.ZipFile(args.archive) as archive:
        entries = archive.infolist()
        if sum(e.file_size for e in entries) > 2_000_000_000:
            raise ValueError('Archive expansion exceeds 2 GB bound')
        seen = set()
        for entry in entries:
            name = entry.filename.replace('\\', '/')
            relative = PurePosixPath(name)
            if (relative.is_absolute() or '..' in relative.parts or ':' in name
                    or stat.S_ISLNK(entry.external_attr >> 16)):
                raise ValueError('Unsafe archive entry: ' + name)
            path = evidence.joinpath(*relative.parts)
            if not path.resolve().is_relative_to(evidence.resolve()):
                raise ValueError('Path escapes evidence root')
            if entry.is_dir():
                path.mkdir(parents=True, exist_ok=True)
                continue
            if name.casefold() in seen:
                raise ValueError('Duplicate case-insensitive entry')
            seen.add(name.casefold())
            path.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(entry) as source, path.open('xb') as target:
                shutil.copyfileobj(source, target, 1024 * 1024)
            modified = datetime(*entry.date_time).timestamp()
            os.utime(path, (modified, modified))
            records.append(dict(path=name, size=path.stat().st_size,
                                archive_modified_local=datetime(*entry.date_time).isoformat(),
                                extension=path.suffix.lower(), sha256=digest(path)))
    with (root / 'files.jsonl').open('x', encoding='utf-8') as index:
        for record in records:
            index.write(json.dumps(record, ensure_ascii=False) + '\n')
    # SQL dumps remain searchable in place. SQLite files are opened read-only;
    # indexing schema does not evaluate stored views or execute dump statements.
    schemas = []
    for record in records:
        path = evidence / record['path']
        with path.open('rb') as stream:
            header = stream.read(16)
        if header == b'SQLite format 3\0':
            with sqlite3.connect(path.resolve().as_uri() + '?mode=ro&immutable=1', uri=True) as db:
                for kind, name, sql in db.execute(
                        "SELECT type,name,sql FROM sqlite_master WHERE sql IS NOT NULL"):
                    schemas.append(dict(path=record['path'], type=kind, name=name, sql=sql))
    (root / 'sqlite-schema.json').write_text(json.dumps(schemas, ensure_ascii=False, indent=2), encoding='utf-8')
    manifest = dict(classification=args.classification,
                    provenance='Owner attribution; version equivalence requires current-client validation',
                    archive=str(args.archive.resolve()), archive_sha256=digest(args.archive),
                    archive_entries=len(entries), extracted_files=len(records),
                    extracted_bytes=sum(r['size'] for r in records),
                    file_index='files.jsonl', schema_index='sqlite-schema.json',
                    text_search='rg against files/; derived decoding must remain outside files/',
                    executed_archive_content=False)
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest))


if __name__ == '__main__':
    main()
