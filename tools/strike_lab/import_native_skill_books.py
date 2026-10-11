"""Import pinned original SKB rows and native identity bindings as read-only evidence.

The parsed bytes and binding do not establish learning, cost, damage, or ownership.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import uuid

from .current_skill_book_binding import NativeSkillBookBinding
from .import_native_catalog import configured_database
from . import import_native_skills as skills
from .recover_combat_rules import CLIENT, IMAGE_SHA256, SKILLS, SOURCE_HASHES

ROOT = Path(__file__).resolve().parents[2]
DATASET = 'current-skill-books-v1'
SOURCE_ROW = (DATASET, SKILLS, SOURCE_HASHES[SKILLS],
              '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815',
              IMAGE_SHA256, 'SKB', '0x59420', '0xA8E10', 381)
SOURCE_COLUMNS = ('dataset_id,source_path,source_sha256,decoded_sha256,native_image_sha256,'
                  'source_section,loader_rva,lookup_rva,row_count')
BOOK_COLUMNS = ('dataset_id,source_record_index,source_line,decoded_offset,item_id,'
                'record_sha256,raw_record,parsed_sha256,parsed_record')
BINDING_COLUMNS = ('book_dataset_id,skill_dataset_id,kind,definition_id,item_id')


def pinned_records(client_root):
    if Path(client_root).resolve() != CLIENT.resolve():
        raise ValueError('Only the pinned current client root is supported')
    native = NativeSkillBookBinding()
    if hashlib.sha256(native.decoded).hexdigest() != SOURCE_ROW[3]:
        raise ValueError('Decoded native skill book source changed')
    source_rows = native.sections['SKB']['records']
    if len(source_rows) != SOURCE_ROW[-1]:
        raise ValueError('Native SKB row count changed')
    books = []
    seen = set()
    for index, row in enumerate(source_rows):
        item_id = int(bytes.fromhex(row['fields_hex'][0]))
        if item_id in seen or item_id not in native.records or native.sources[item_id] != row:
            raise ValueError('Native SKB item binding changed')
        seen.add(item_id)
        raw = bytes.fromhex(row['raw_record_hex']).rstrip(b'\r\n')
        offset = row['decoded_offset']
        parsed = native.records[item_id][1]
        if (not 6501 <= item_id <= 7199 or not raw or len(parsed) != 396 or
                native.decoded[offset:offset + len(raw)] != raw):
            raise ValueError('Native SKB source/parsed record differs')
        books.append((DATASET, index, row['source_line'], offset, item_id,
                      hashlib.sha256(raw).hexdigest(), raw,
                      hashlib.sha256(parsed).hexdigest(), parsed))
    catalog = native.catalog()
    bindings = sorted((DATASET, skills.DATASET, row['kind'], row['skill_id'], row['item_id'])
                      for row in catalog['entries'])
    if (len(bindings) != 381 or len(catalog['unmatched']) != 67 or
            {row[4] for row in bindings} != seen or
            len({(row[2], row[3]) for row in bindings}) != len(bindings)):
        raise ValueError('Native skill-to-SKB identity set changed')
    return books, bindings


def import_catalog(connection, client_root, *, records=None):
    books, bindings = pinned_records(client_root) if records is None else records
    if connection.in_transaction:
        raise ValueError('Skill book import requires its own transaction')
    connection.execute('PRAGMA foreign_keys=ON')
    connection.execute('BEGIN IMMEDIATE')
    try:
        if connection.execute('SELECT name FROM schema_migrations WHERE version=18').fetchall() != [
                ('native_skill_books',)]:
            raise ValueError('Apply the server native_skill_books migration first')
        if connection.execute(f'SELECT {SOURCE_COLUMNS} FROM native_data_sources WHERE dataset_id=?',
                              (skills.DATASET,)).fetchall() != [skills.SOURCE_ROW]:
            raise ValueError('Pinned native skill catalog source is required')
        if connection.execute(f'SELECT {skills.RECORD_COLUMNS} FROM native_skill_catalog '
                              'WHERE dataset_id=? ORDER BY source_record_index',
                              (skills.DATASET,)).fetchall() != skills.pinned_records(client_root):
            raise ValueError('Pinned native skill catalog rows are required')
        existing = connection.execute(f'SELECT {SOURCE_COLUMNS} FROM native_data_sources '
                                      'WHERE dataset_id=?', (DATASET,)).fetchall()
        if existing and existing != [SOURCE_ROW]:
            raise ValueError('Conflicting native skill book source; refusing replacement')
        stored_books = connection.execute(f'SELECT {BOOK_COLUMNS} FROM native_skill_books '
                                          'WHERE dataset_id=? ORDER BY source_record_index',
                                          (DATASET,)).fetchall()
        stored_bindings = connection.execute(f'SELECT {BINDING_COLUMNS} FROM native_skill_book_bindings '
                                             'WHERE book_dataset_id=? ORDER BY book_dataset_id,skill_dataset_id,kind,definition_id,item_id',
                                             (DATASET,)).fetchall()
        if not existing:
            if stored_books or stored_bindings:
                raise ValueError('Orphaned native skill book rows; refusing replacement')
            connection.execute(f'INSERT INTO native_data_sources({SOURCE_COLUMNS}) VALUES(?,?,?,?,?,?,?,?,?)',
                               SOURCE_ROW)
            connection.executemany(f'INSERT INTO native_skill_books({BOOK_COLUMNS}) VALUES(?,?,?,?,?,?,?,?,?)',
                                   books)
            connection.executemany(f'INSERT INTO native_skill_book_bindings({BINDING_COLUMNS}) VALUES(?,?,?,?,?)',
                                   bindings)
        if (connection.execute(f'SELECT {BOOK_COLUMNS} FROM native_skill_books '
                               'WHERE dataset_id=? ORDER BY source_record_index', (DATASET,)).fetchall() != books or
                connection.execute(f'SELECT {BINDING_COLUMNS} FROM native_skill_book_bindings '
                                   'WHERE book_dataset_id=? ORDER BY book_dataset_id,skill_dataset_id,kind,definition_id,item_id',
                                   (DATASET,)).fetchall() != bindings or
                connection.execute(f'SELECT {SOURCE_COLUMNS} FROM native_data_sources '
                                   'WHERE dataset_id=?', (DATASET,)).fetchall() != [SOURCE_ROW]):
            raise ValueError('Native skill book conflict or incomplete import; refusing overwrite')
        if connection.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise ValueError('Database foreign key check failed')
        if connection.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
            raise ValueError('Database integrity check failed')
        connection.commit()
        return {'dataset': DATASET, 'books': len(books), 'bindings': len(bindings),
                'inserted': 0 if existing else len(books)}
    except BaseException:
        connection.rollback()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'config/server.json')
    parser.add_argument('--client', type=Path, default=CLIENT)
    parser.add_argument('--server-exe', type=Path, default=ROOT / 'build/Release/god2-server.exe')
    args = parser.parse_args()
    client = args.client.resolve()
    records = pinned_records(client)
    database = configured_database(args.config)
    if database.is_relative_to(client) or not database.is_file():
        raise ValueError('Refusing client-tree or nonexistent target database')
    backup_dir = ROOT / 'artifacts/db-backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / ('native-skill-books-' + uuid.uuid4().hex + '.sqlite')
    with closing(sqlite3.connect(database.as_uri() + '?mode=rw', uri=True)) as source:
        with closing(sqlite3.connect(backup)) as destination:
            source.backup(destination)
    subprocess.run([str(args.server_exe.resolve()), '--config', str(args.config.resolve()),
                    '--migrate-only'], cwd=ROOT, check=True)
    with closing(sqlite3.connect(database.as_uri() + '?mode=rw', uri=True)) as connection:
        result = import_catalog(connection, client, records=records)
    print(json.dumps(dict(result, database=str(database), backup=str(backup)), sort_keys=True))


if __name__ == '__main__':
    main()
