"""Import current MED02 tooltip recovery declarations into formal SQLite.

These are client text amounts, not verified server potion effects.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import uuid

from .import_native_catalog import configured_database
from .recover_items import build_items
from .recover_supply_tooltips import declared_amounts

ROOT = Path(__file__).resolve().parents[2]
DATASET = 'current-med02-recovery-v1'
SOURCE = 'Data2/Patch/Comm/gamedata.csvZ'
SOURCE_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
PLAIN_SHA = '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
SOURCE_ROW = (DATASET, SOURCE, SOURCE_SHA, PLAIN_SHA, IMAGE_SHA,
              'MED02', '0x59420', '0x59a60', 100)


def pinned_rows(client_root):
    catalog = build_items(client_root)
    source = catalog['source']
    if (source['path'] != SOURCE or source['sha256'] != SOURCE_SHA or
            source['decoded_sha256'] != PLAIN_SHA):
        raise ValueError('Current MED02 source identity changed')
    med02 = [r for r in catalog['records'] if r['section'] == 'MED02']
    if len(med02) != 100 or [r['source_record_index'] for r in med02] != list(range(100)):
        raise ValueError('Current MED02 source record count/order changed')
    rows = []
    for row in med02:
        raw = b','.join(bytes.fromhex(field) for field in row['raw_fields_hex'])
        tooltip = bytes.fromhex(row['raw_fields_hex'][8])
        try:
            amounts = declared_amounts(tooltip)
        except UnicodeDecodeError:
            amounts = None
        if (not 1 <= len(raw) <= 4095 or
                hashlib.sha256(raw).hexdigest() != row['source_record_sha256'] or
                row['definition_key'] != f"MED02:{row['client_item_id']}"):
            raise ValueError('MED02 source record bytes changed')
        if amounts is None:
            continue
        if (not 1 <= len(tooltip) <= 255 or not row['client_flags']['normal_use'] or
                not row['client_flags']['hotkey_allowed']):
            raise ValueError('Qualified MED02 use flags or tooltip changed')
        rows.append((DATASET, row['source_record_index'], row['source_line'],
                     row['client_item_id'], row['source_record_sha256'], raw, tooltip,
                     amounts['hp'], amounts['mp'], 1, 1))
    if len(rows) != 71 or len({r[3] for r in rows}) != 71:
        raise ValueError('Qualified MED02 declaration count changed')
    return rows


def import_catalog(connection, client_root):
    rows = pinned_rows(client_root)
    if connection.in_transaction:
        raise ValueError('MED02 import requires its own transaction')
    connection.execute('PRAGMA foreign_keys=ON')
    connection.execute('BEGIN IMMEDIATE')
    try:
        if connection.execute('SELECT name FROM schema_migrations WHERE version=21').fetchone() != (
                'native_med02_recovery_declarations',):
            raise ValueError('Apply native_med02_recovery_declarations migration first')
        existing = connection.execute(
            'SELECT dataset_id,source_path,source_sha256,decoded_sha256,native_image_sha256,'
            'source_section,loader_rva,lookup_rva,row_count FROM native_data_sources '
            'WHERE dataset_id=?', (DATASET,)).fetchone()
        if existing is not None and existing != SOURCE_ROW:
            raise ValueError('Conflicting MED02 source; refusing replacement')
        if existing is None:
            connection.execute('INSERT INTO native_data_sources VALUES(?,?,?,?,?,?,?,?,?)', SOURCE_ROW)
            connection.executemany('INSERT INTO native_med02_recovery_declarations '
                                   'VALUES(?,?,?,?,?,?,?,?,?,?,?)', rows)
        stored = connection.execute(
            'SELECT dataset_id,source_record_index,source_line,item_id,record_sha256,'
            'raw_record,tooltip_bytes,declared_hp,declared_mp,normal_use,hotkey_allowed '
            'FROM native_med02_recovery_declarations WHERE dataset_id=? '
            'ORDER BY source_record_index', (DATASET,)).fetchall()
        if stored != rows:
            raise ValueError('MED02 declaration conflict or incomplete import')
        if connection.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise ValueError('MED02 catalog foreign key check failed')
        if connection.execute('PRAGMA quick_check').fetchone() != ('ok',):
            raise ValueError('MED02 catalog integrity check failed')
        connection.commit()
        return {'dataset': DATASET, 'rows': len(rows),
                'unmatched': 29, 'inserted': len(rows) if existing is None else 0}
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
    backup = backup_dir / ('native-med02-' + uuid.uuid4().hex + '.sqlite')
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
