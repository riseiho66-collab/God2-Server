"""Import pinned current CP950 MultiMessage source bytes, never dialogue rules.

No emulator/native-audit module is imported. Importing this module does not read
files or open a database. CLI writes only the explicitly supplied database.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3

from .omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = 'SOURCE_DISPLAY_ONLY'
# filename -> compressed SHA256, decoded SHA256, first key, key count, options
PINS = {
    'MultiMessage01.csvZ': ('0d573b607f477c0da53c2efa7aeb1881bcb1d38941cf36472cd9a506d13f9985',
        'e5234537a68f63df15d6279a232395a130f2c2cfddd3589b2a66372d2da4b4b9', 1, 1000, 2531),
    'MultiMessage02.csvZ': ('441b2828b6edccdb36098c3aba9d6e631ae351d82e685969d34758b67fe6c10f',
        '72c1840846e3925b43a62552c354308ecbc83a5d0e1e4121826bc59303d99003', 1001, 1000, 2780),
    'MultiMessage03.csvZ': ('e0551afec2108f478f27f2364bd15bd8d7ff999c8f12a087b320d06d23659e4d',
        'eb6551f327caba720f71bcee78dda84a796b3c1b615e0287651d5e6cae6af58c', 2001, 995, 3488),
}
SCHEMA = (
    '''CREATE TABLE native_multi_message_sources (
 source_file TEXT PRIMARY KEY,
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64),
 decoded_sha256 TEXT NOT NULL CHECK(length(decoded_sha256)=64),
 encoding TEXT NOT NULL CHECK(encoding='CP950'),
 record_count INTEGER NOT NULL CHECK(record_count>0),
 line_count INTEGER NOT NULL CHECK(line_count>2),
 decoded_size INTEGER NOT NULL CHECK(decoded_size>0),
 authority TEXT NOT NULL CHECK(authority='SOURCE_DISPLAY_ONLY')
)''',
    '''CREATE TABLE native_multi_messages (
 message_key INTEGER PRIMARY KEY CHECK(message_key BETWEEN 1 AND 2995),
 source_file TEXT NOT NULL REFERENCES native_multi_message_sources(source_file),
 option_count INTEGER NOT NULL CHECK(option_count BETWEEN 1 AND 255),
 authority TEXT NOT NULL CHECK(authority='SOURCE_DISPLAY_ONLY')
)''',
    '''CREATE TABLE native_multi_message_rows (
 message_key INTEGER NOT NULL REFERENCES native_multi_messages(message_key),
 ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 255),
 source_line INTEGER NOT NULL CHECK(source_line>=3),
 decoded_offset INTEGER NOT NULL CHECK(decoded_offset>=0),
 record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record)>0),
 text_bytes BLOB NOT NULL CHECK(typeof(text_bytes)='blob' AND length(text_bytes)>0),
 PRIMARY KEY(message_key,ordinal)
)''',
)
TABLES = ('native_multi_message_sources', 'native_multi_messages', 'native_multi_message_rows')
ORDERS = ('source_file', 'message_key', 'message_key,ordinal')


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _number(raw):
    _require(raw and raw.isdigit(), 'Invalid MultiMessage decimal field')
    return int(raw)


def _parse_rows(source_file, decoded, first_key, key_count, option_total):
    """Structural parser; callers must separately verify both source hashes."""
    _require(b'\0' not in decoded, 'NUL in MultiMessage source')
    decoded.decode('cp950', errors='strict')  # Validation only; bytes stay original.
    lines = decoded.splitlines(keepends=True)
    _require(len(lines) >= 3 and lines[0].startswith(b'MultiMessage,v2.00,'), 'Invalid MultiMessage header')
    _require(lines[1].rstrip(b'\r\n') == b'MultiMessage,' + str(key_count).encode(), 'Invalid declared key count')
    definitions, rows = [], []
    offset = sum(len(line) for line in lines[:2])
    key, count, ordinal = None, 0, 0
    for line_number, line in enumerate(lines[2:], 3):
        raw = line.removesuffix(b'\n').removesuffix(b'\r')
        _require(raw and b'\r' not in raw and b'\n' not in raw, 'Invalid source line')
        fields = raw.split(b',', 2)  # Native comma fields, not RFC quoted CSV.
        _require(len(fields) == 3 and fields[2], 'Missing MultiMessage text')
        if fields[0]:
            _require(key is None or ordinal == count, 'Incomplete option group')
            key, count = _number(fields[0]), _number(fields[1])
            _require(key == first_key + len(definitions) and 1 <= count <= 255,
                     'Noncontiguous key or invalid option count')
            ordinal = 0
            definitions.append((key, source_file, count, AUTHORITY))
        else:
            _require(key is not None, 'Option before intro')
            ordinal += 1
            _require(_number(fields[1]) == ordinal and ordinal <= count, 'Invalid option ordinal')
        rows.append((key, ordinal, line_number, offset, _sha(raw), raw, fields[2]))
        offset += len(line)
    _require(len(definitions) == key_count and ordinal == count and
             len(rows) == key_count + option_total and offset == len(decoded), 'Incomplete MultiMessage source')
    return definitions, rows, len(lines)


def pinned_records(client):
    """Return immutable SQL row tuples after all three original files validate."""
    sources, definitions, rows = [], [], []
    for filename, (compressed_sha, decoded_sha, first, count, options) in PINS.items():
        relative = 'Data2/Patch/Comm/' + filename
        compressed = (Path(client) / relative).read_bytes()
        _require(_sha(compressed) == compressed_sha, 'MultiMessage source identity mismatch: ' + filename)
        decoded = decode_csvz(compressed)
        _require(_sha(decoded) == decoded_sha, 'MultiMessage decoded identity mismatch: ' + filename)
        groups, records, line_count = _parse_rows(relative, decoded, first, count, options)
        sources.append((relative, compressed_sha, decoded_sha, 'CP950', count, line_count, len(decoded), AUTHORITY))
        definitions.extend(groups)
        rows.extend(records)
    _require([row[0] for row in definitions] == list(range(1, 2996)) and len(rows) == 11794,
             'Incomplete global MultiMessage catalog')
    return tuple(sources), tuple(definitions), tuple(rows)


def _install(connection):
    for table, ddl in zip(TABLES, SCHEMA):
        existing = connection.execute('SELECT sql FROM sqlite_master WHERE type=\'table\' AND name=?', (table,)).fetchone()
        if existing:
            # This independent source schema is version-pinned. Refuse an old
            # or unrelated table rather than silently weakening constraints.
            _require(' '.join(existing[0].split()) == ' '.join(ddl.split()), 'Conflicting MultiMessage schema: ' + table)
        else:
            connection.execute(ddl)


def install(connection):
    """Atomically install the independent source schema; no gameplay migration."""
    _require(not connection.in_transaction, 'MultiMessage install requires its own transaction')
    connection.execute('PRAGMA foreign_keys=ON')
    connection.execute('BEGIN IMMEDIATE')
    try:
        _install(connection)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise


def import_catalog(connection, client):
    _require(not connection.in_transaction, 'MultiMessage import requires its own transaction')
    expected = pinned_records(client)  # Validate every source before schema/data writes.
    connection.execute('PRAGMA foreign_keys=ON')
    connection.execute('BEGIN IMMEDIATE')
    try:
        _install(connection)
        stored = tuple(tuple(connection.execute('SELECT * FROM ' + table + ' ORDER BY ' + order))
                       for table, order in zip(TABLES, ORDERS))
        present = any(stored)
        _require(not present or stored == expected, 'Conflicting/partial MultiMessage catalog; refusing overwrite')
        if not present:
            for table, records in zip(TABLES, expected):
                placeholders = ','.join('?' for _ in records[0])
                connection.executemany('INSERT INTO ' + table + ' VALUES(' + placeholders + ')', records)
        actual = tuple(tuple(connection.execute('SELECT * FROM ' + table + ' ORDER BY ' + order))
                       for table, order in zip(TABLES, ORDERS))
        _require(actual == expected, 'MultiMessage import readback mismatch')
        _require(connection.execute('PRAGMA foreign_key_check').fetchone() is None and
                 connection.execute('PRAGMA quick_check').fetchone() == ('ok',), 'Database integrity check failed')
        connection.commit()
        return dict(source_files=3, keys=2995, introductions=2995, options=8799,
                    text_rows=11794, inserted_keys=0 if present else 2995,
                    authority=AUTHORITY, gameplay_rules=0)
    except BaseException:
        connection.rollback()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True, type=Path)
    parser.add_argument('--client', type=Path, default=ROOT.parent / 'God2')
    args = parser.parse_args()
    database, client = args.database.resolve(), args.client.resolve()
    _require(not database.is_relative_to(client), 'Refusing database inside the client tree')
    with closing(sqlite3.connect(database)) as connection:
        print(json.dumps(import_catalog(connection, client)))


if __name__ == '__main__':
    main()
