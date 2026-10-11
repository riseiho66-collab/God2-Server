"""Import pinned current EnyName display identities into server SQLite.

This is a lookup namespace, not a monster stat, spawn, encounter or drop table.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import uuid

from .current_monster_inventory import pinned_catalog, SOURCE, SOURCE_SHA, PLAIN_SHA
from .import_native_catalog import configured_database

ROOT = Path(__file__).resolve().parents[2]
DATASET = 'current-enyname-display-v1'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
SOURCE_ROW = (DATASET, SOURCE, SOURCE_SHA, PLAIN_SHA, IMAGE_SHA,
              'EnyName', '0x5a1a0', '0x5a0a0', 7815)


def pinned_rows(client_root):
    catalog = pinned_catalog(client_root)
    records = catalog['records']
    if len(records) != 7815 or sum(r['lookup_visible'] for r in records) != 7791:
        raise ValueError('Current EnyName source count changed')
    rows = []
    seen_visible = set()
    for row in records:
        raw = bytes.fromhex(row['raw_record_hex'])
        name = bytes.fromhex(row['name_bytes_hex'])
        if (not 1 <= len(raw) <= 2047 or not 1 <= len(name) <= 15 or
                hashlib.sha256(raw).hexdigest() != row['record_sha256'] or
                name != bytes.fromhex(row['fields_hex'][1])):
            raise ValueError('EnyName row or name bytes changed')
        if row['lookup_visible']:
            key = (row['area'], row['scene'], row['ordinal'])
            if key in seen_visible:
                raise ValueError('Ambiguous final native lookup key')
            seen_visible.add(key)
        rows.append((DATASET, row['source_record_index'], row['source_line'],
                     row['source_offset'], row['record_sha256'], raw,
                     row['area_generation'], row['area'], row['scene'], row['ordinal'],
                     int(row['lookup_visible']), row['source_label'], name))
    return rows


def import_catalog(connection, client_root):
    rows = pinned_rows(client_root)  # Verify the original file before writing.
    if connection.in_transaction:
        raise ValueError('EnyName import requires its own transaction')
    connection.execute('PRAGMA foreign_keys=ON')
    connection.execute('BEGIN IMMEDIATE')
    try:
        if connection.execute('SELECT name FROM schema_migrations WHERE version=20').fetchone() != (
                'native_enemy_display_catalog',):
            raise ValueError('Apply native_enemy_display_catalog migration first')
        existing = connection.execute(
            'SELECT dataset_id,source_path,source_sha256,decoded_sha256,native_image_sha256,'
            'source_section,loader_rva,lookup_rva,row_count FROM native_data_sources '
            'WHERE dataset_id=?', (DATASET,)).fetchone()
        if existing is not None and existing != SOURCE_ROW:
            raise ValueError('Conflicting EnyName source; refusing replacement')
        if existing is None:
            connection.execute('INSERT INTO native_data_sources VALUES(?,?,?,?,?,?,?,?,?)', SOURCE_ROW)
            connection.executemany('INSERT INTO native_enemy_display_catalog VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)', rows)
        stored = connection.execute(
            'SELECT dataset_id,source_record_index,source_line,source_offset,record_sha256,'
            'raw_record,area_generation,area,scene,ordinal,lookup_visible,source_label,name_bytes '
            'FROM native_enemy_display_catalog WHERE dataset_id=? ORDER BY source_record_index',
            (DATASET,)).fetchall()
        if stored != rows:
            raise ValueError('EnyName catalog conflict or incomplete import')
        if connection.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise ValueError('EnyName catalog foreign key check failed')
        if connection.execute('PRAGMA quick_check').fetchone() != ('ok',):
            raise ValueError('EnyName catalog integrity check failed')
        connection.commit()
        return {'dataset': DATASET, 'rows': len(rows),
                'lookup_visible': 7791, 'inserted': len(rows) if existing is None else 0}
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
    pinned_rows(client)
    database = configured_database(args.config)
    if database.is_relative_to(client) or not database.is_file():
        raise ValueError('Refusing client-tree or nonexistent target database')
    backup_dir = ROOT / 'artifacts/db-backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / ('native-enyname-' + uuid.uuid4().hex + '.sqlite')
    with closing(sqlite3.connect(database.as_uri() + '?mode=rw', uri=True)) as source:
        with closing(sqlite3.connect(backup)) as target:
            source.backup(target)
    subprocess.run([str(args.server_exe.resolve()), '--config', str(args.config.resolve()),
                    '--migrate-only'], cwd=ROOT, check=True)
    with closing(sqlite3.connect(database.as_uri() + '?mode=rw', uri=True)) as connection:
        result = import_catalog(connection, client)
    print(json.dumps(dict(result, database=str(database), backup=str(backup)), sort_keys=True))


if __name__ == '__main__':
    main()
