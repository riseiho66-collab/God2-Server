"""Import the pinned native map catalog into the configured server SQLite DB.

Only source records and native selector semantics are promoted. Catalog
coordinates are not spawn locations; no player records or gameplay rules change.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import uuid

from .omega_assets import decode_csvz
from .world_atlas import parse_catalog, SOURCE, SECTION

ROOT = Path(__file__).resolve().parents[2]
DATASET = 'current-map-catalog-v1'
SOURCE_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
PLAIN_SHA = '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
SOURCE_ROW = (DATASET, SOURCE, SOURCE_SHA, PLAIN_SHA, IMAGE_SHA,
              SECTION.decode('ascii'), '0x59a80', '0x59d80', 144)


def pinned_records(client_root):
    root = Path(client_root).resolve()
    source = (root / SOURCE).resolve()
    if not source.is_relative_to(root) or source.stat().st_size > 1024 * 1024:
        raise ValueError('Native catalog source path/size bound')
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError('Native catalog source identity changed')
    plain = decode_csvz(raw, limit=4 * 1024 * 1024)
    if hashlib.sha256(plain).hexdigest() != PLAIN_SHA:
        raise ValueError('Native catalog decoded identity changed')
    parsed = parse_catalog(plain)
    if len(parsed) != SOURCE_ROW[-1]:
        raise ValueError('Native catalog count changed')
    lines = plain.split(b'\n')
    rows = []
    for item in parsed:
        record = lines[item['source_line'] - 1].rstrip(b'\r')
        if (not 1 <= len(record) <= 4095
                or hashlib.sha256(record).hexdigest() != item['source_record_sha256']
                or record != b','.join(bytes.fromhex(f) for f in item['raw_fields_hex'])):
            raise ValueError('Native catalog record identity mismatch')
        rows.append((DATASET, item['source_record_index'], item['source_line'],
                     item['source_record_sha256'], record,
                     item['area'], item['scene'], item['kind']))
    return rows


def import_catalog(connection, client_root):
    rows = pinned_records(client_root)
    if connection.in_transaction:
        raise ValueError('Catalog import requires its own transaction')
    connection.execute('PRAGMA foreign_keys=ON')
    connection.execute('BEGIN IMMEDIATE')
    try:
        migration = connection.execute(
            'SELECT name FROM schema_migrations WHERE version=4').fetchone()
        if migration != ('native_map_catalog',):
            raise ValueError('Apply the server native_map_catalog migration first')
        existing = connection.execute(
            'SELECT dataset_id,source_path,source_sha256,decoded_sha256,native_image_sha256,'
            'source_section,loader_rva,lookup_rva,row_count FROM native_data_sources '
            'WHERE dataset_id=?', (DATASET,)).fetchone()
        if existing is not None and existing != SOURCE_ROW:
            raise ValueError('Conflicting native source; refusing replacement')
        if existing is None:
            connection.execute('INSERT INTO native_data_sources VALUES(?,?,?,?,?,?,?,?,?)', SOURCE_ROW)
            connection.executemany('INSERT INTO native_map_catalog VALUES(?,?,?,?,?,?,?,?)', rows)
        stored = connection.execute(
            'SELECT dataset_id,source_record_index,source_line,record_sha256,raw_record,area,scene,kind '
            'FROM native_map_catalog WHERE dataset_id=? ORDER BY source_record_index', (DATASET,)).fetchall()
        if stored != rows:
            raise ValueError('Native catalog conflict or incomplete import; refusing overwrite')
        if connection.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise ValueError('Database foreign key check failed')
        if connection.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
            raise ValueError('Database integrity check failed')
        connection.commit()
        return {'dataset': DATASET, 'rows': len(rows), 'inserted': len(rows) if existing is None else 0}
    except BaseException:
        connection.rollback()
        raise


def configured_database(config_path):
    config_path = Path(config_path).resolve()
    config = json.loads(config_path.read_text(encoding='utf-8'))
    if config['database']['type'] != 'sqlite':
        raise ValueError('Only configured SQLite storage is supported')
    value = config['database']['path']
    if not isinstance(value, str) or not value or '\0' in value:
        raise ValueError('Invalid configured database path')
    return (config_path.parent.parent / value).resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'config/server.json')
    parser.add_argument('--client', type=Path, default=ROOT.parent / 'God2')
    parser.add_argument('--server-exe', type=Path, default=ROOT / 'build/Release/god2-server.exe')
    args = parser.parse_args()
    client = args.client.resolve()
    pinned_records(client)  # Validate authority before any database write.
    database = configured_database(args.config)
    if database.is_relative_to(client) or not database.is_file():
        raise ValueError('Refusing client-tree or nonexistent target database')
    backup_dir = ROOT / 'artifacts/db-backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / ('native-catalog-' + uuid.uuid4().hex + '.sqlite')
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
