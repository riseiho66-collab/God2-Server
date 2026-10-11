"""Import only the pinned current cbspec2 identities and 110-byte raw records.

No names, costs, classification, formulas, learned ownership or battle rules
are inferred. The CLI backs up the configured SQLite DB before server migration.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import uuid

from . import current_skill_identity as identity
from .import_native_catalog import configured_database

ROOT = Path(__file__).resolve().parents[2]
DATASET = 'current-skill-catalog-v1'
SOURCE = identity.SOURCE
SOURCE_SHA = identity.SOURCE_SHA256
PLAIN_SHA = SOURCE_SHA  # The original file is uncompressed.
IMAGE_SHA = identity.IMAGE_SHA256
KIND_COUNTS = (121, 129, 87, 111)
SOURCE_ROW = (DATASET, SOURCE, SOURCE_SHA, PLAIN_SHA, IMAGE_SHA,
              '1.03', '0x12d3b0', '0x11c520', 448)
SOURCE_COLUMNS = ('dataset_id,source_path,source_sha256,decoded_sha256,native_image_sha256,'
                  'source_section,loader_rva,lookup_rva,row_count')
RECORD_COLUMNS = ('dataset_id,source_record_index,source_offset,record_sha256,'
                  'raw_record,kind,definition_id')


def pinned_records(client_root):
    root = Path(client_root).resolve()
    source = (root / SOURCE).resolve()
    if not source.is_relative_to(root) or source.stat().st_size != identity.FILE_SIZE:
        raise ValueError('Native skill source path/size bound')
    with source.open('rb') as stream:
        raw = stream.read(identity.FILE_SIZE + 1)
    if len(raw) != identity.FILE_SIZE or hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError('Native skill source identity changed')
    definitions = identity.decode_definitions(raw)
    if (len(definitions) != SOURCE_ROW[-1] or
            tuple(sum(kind == key[0] for key in definitions) for kind in range(4)) != KIND_COUNTS):
        raise ValueError('Native skill definition counts changed')
    rows = []
    for index, ((kind, definition_id), definition) in enumerate(sorted(definitions.items())):
        offset = 8 + kind * identity.GROUP_STRIDE + (definition_id - 1) * identity.RECORD_SIZE
        record = definition.raw
        if (not 0 <= kind <= 3 or not 1 <= definition_id <= 255 or
                definition.kind != kind or definition.id != definition_id or
                definition.source_offset != offset or len(record) != 110 or
                record[:2] != bytes((definition_id, kind)) or raw[offset:offset + 110] != record):
            raise ValueError('Native skill record identity mismatch')
        rows.append((DATASET, index, offset, hashlib.sha256(record).hexdigest(),
                     record, kind, definition_id))
    return rows


def import_catalog(connection, client_root):
    rows = pinned_records(client_root)
    if connection.in_transaction:
        raise ValueError('Skill catalog import requires its own transaction')
    connection.execute('PRAGMA foreign_keys=ON')
    connection.execute('BEGIN IMMEDIATE')
    try:
        migration = connection.execute(
            'SELECT name FROM schema_migrations WHERE version=5').fetchall()
        if migration != [('native_skill_catalog',)]:
            raise ValueError('Apply the server native_skill_catalog migration first')
        existing = connection.execute(
            f'SELECT {SOURCE_COLUMNS} FROM native_data_sources WHERE dataset_id=?', (DATASET,)).fetchall()
        if existing and existing != [SOURCE_ROW]:
            raise ValueError('Conflicting native skill source; refusing replacement')
        stored = connection.execute(
            f'SELECT {RECORD_COLUMNS} FROM native_skill_catalog WHERE dataset_id=? '
            'ORDER BY source_record_index', (DATASET,)).fetchall()
        if not existing:
            if stored:
                raise ValueError('Orphaned native skill records; refusing replacement')
            connection.execute(f'INSERT INTO native_data_sources({SOURCE_COLUMNS}) VALUES(?,?,?,?,?,?,?,?,?)',
                               SOURCE_ROW)
            connection.executemany(
                f'INSERT INTO native_skill_catalog({RECORD_COLUMNS}) VALUES(?,?,?,?,?,?,?)', rows)
        stored = connection.execute(
            f'SELECT {RECORD_COLUMNS} FROM native_skill_catalog WHERE dataset_id=? '
            'ORDER BY source_record_index', (DATASET,)).fetchall()
        source = connection.execute(
            f'SELECT {SOURCE_COLUMNS} FROM native_data_sources WHERE dataset_id=?', (DATASET,)).fetchall()
        if stored != rows or source != [SOURCE_ROW]:
            raise ValueError('Native skill catalog conflict or incomplete import; refusing overwrite')
        if connection.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise ValueError('Database foreign key check failed')
        if connection.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
            raise ValueError('Database integrity check failed')
        connection.commit()
        return {'dataset': DATASET, 'rows': len(rows), 'inserted': 0 if existing else len(rows)}
    except BaseException:
        connection.rollback()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'config/server.json')
    parser.add_argument('--client', type=Path, default=ROOT.parent / 'God2')
    parser.add_argument('--server-exe', type=Path, default=ROOT / 'build/Release/god2-server.exe')
    args = parser.parse_args()
    client = args.client.resolve()
    pinned_records(client)  # Validate the current original before any DB write.
    database = configured_database(args.config)
    if database.is_relative_to(client) or not database.is_file():
        raise ValueError('Refusing client-tree or nonexistent target database')
    backup_dir = ROOT / 'artifacts/db-backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / ('native-skills-' + uuid.uuid4().hex + '.sqlite')
    with closing(sqlite3.connect(database.as_uri() + '?mode=rw', uri=True)) as source:
        with closing(sqlite3.connect(backup)) as destination:
            source.backup(destination)
    subprocess.run([str(args.server_exe.resolve()), '--config', str(args.config.resolve()),
                    '--migrate-only'], cwd=ROOT, check=True)
    with closing(sqlite3.connect(database.as_uri() + '?mode=rw', uri=True)) as connection:
        result = import_catalog(connection, client)
    print(json.dumps(dict(result, database=str(database), backup=str(backup)), sort_keys=True))


if __name__ == '__main__':
    main()
