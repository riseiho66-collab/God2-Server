"""Exact static catalog overlay for NEW disposable schema49 UI fixtures only.

No formal database writes, schema replacement, history copy or gameplay grants.
Use a pinned read-only backup snapshot. Existing target rows must be typed-exact
subsets; only missing PKs are inserted in one transaction. No INSERT OR REPLACE.
"""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import struct

FORMAT = 'guild-formal-catalog-fixture-20261004-v1'
TABLES = (
    'native_armor_rows', 'native_armor_sources', 'native_companion_metadata',
    'native_daily_quest_parsed', 'native_daily_quest_source', 'native_data_sources',
    'native_enemy_display_catalog', 'native_map_catalog', 'native_map_item_rows',
    'native_map_item_sources', 'native_med02_recovery_declarations',
    'native_multi_message_rows', 'native_multi_message_sources', 'native_multi_messages',
    'native_npc_display_rows', 'native_npc_display_sources', 'native_pet1_metadata',
    'native_pet2_category_rows', 'native_pet2_category_source', 'native_quest_definitions',
    'native_quest_descriptions', 'native_quest_requirement_display', 'native_skill_book_bindings',
    'native_skill_books', 'native_skill_catalog', 'native_weapon_rows', 'native_weapon_sources',
)
MIGRATION49 = 'owned_player_guild_membership_candidate'
SCHEMA49_TABLES = {'owned_guild_governance_0078', 'owned_guild_applications_0078'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def quote(name):
    return '"' + name.replace('"', '""') + '"'


def typed(row):
    output = bytearray()
    for value in row:
        if value is None:
            data = b'N'
        elif isinstance(value, bytes):
            data = b'B' + value
        elif isinstance(value, str):
            data = b'T' + value.encode('utf-8')
        elif isinstance(value, int):
            data = b'I' + struct.pack('<q', value)
        elif isinstance(value, float):
            data = b'F' + struct.pack('<d', value)
        else:
            raise ValueError('Unknown SQLite storage type')
        output += struct.pack('<Q', len(data)) + data
    return bytes(output)


def fingerprint(rows):
    encoded = sorted(typed(row) for row in rows)
    digest = hashlib.sha256()
    for row in encoded:
        digest.update(struct.pack('<Q', len(row)))
        digest.update(row)
    return {'rows': len(encoded), 'typed_sha256': digest.hexdigest()}


def integrity(db):
    require(db.execute('PRAGMA quick_check').fetchall() == [('ok',)], 'Fixture SQLite quick_check failed')
    require(not db.execute('PRAGMA foreign_key_check').fetchall(), 'Fixture SQLite foreign key check failed')


def schemas(db):
    return [list(row) for row in db.execute(
        'SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name')]


def catalog(db):
    result = {}
    schema = schemas(db)
    for table in TABLES:
        rows = db.execute('SELECT * FROM ' + quote(table)).fetchall()
        columns = [list(row) for row in db.execute('PRAGMA table_xinfo(' + quote(table) + ')')]
        primary = [row[0] for row in sorted(columns, key=lambda row: row[5]) if row[5]]
        require(primary and all(row[6] == 0 for row in columns), 'Catalog needs exact ordinary PK columns: ' + table)
        result[table] = {
            'schema': [row for row in schema if row[2] == table],
            'columns': columns, 'primary_key_indices': primary,
            'fingerprint': fingerprint(rows),
            'foreign_keys': [list(row) for row in db.execute('PRAGMA foreign_key_list(' + quote(table) + ')')],
        }
    return result


def copy_order(catalogs):
    parents = {table: {row[2] for row in catalogs[table]['foreign_keys']} for table in TABLES}
    parents['native_npc_display_rows'].add('native_npc_display_sources')
    parents['native_pet2_category_rows'].add('native_pet2_category_source')
    require(all(parent <= set(TABLES) for parent in parents.values()), 'Catalog closure has external authority dependency')
    pending, order = set(TABLES), []
    while pending:
        ready = sorted(table for table in pending if not parents[table].intersection(pending))
        require(ready, 'Catalog FK cycle')
        order.extend(ready)
        pending.difference_update(ready)
    return order


def readonly_snapshot(path):
    path = Path(path).resolve()
    require(path.is_file(), 'Snapshot missing')
    # Archived backup is complete, not a live WAL/journal source. Immutable mode
    # is appropriate ONLY after full snapshot file SHA has been verified.
    for suffix in ('-wal', '-journal'):
        require(not Path(str(path) + suffix).exists(), 'Snapshot has unbound WAL/journal sidecar')
    db = sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True)
    db.execute('PRAGMA query_only=ON')
    db.execute('BEGIN')
    return db


def build_manifest(source_snapshot, migration49_sql):
    """Read-only metadata builder used once to seal the NEW fixture snapshot."""
    path = Path(source_snapshot).resolve()
    expected = sha(path)
    with closing(readonly_snapshot(path)) as db:
        integrity(db)
        catalogs = catalog(db)
        result = {'format': FORMAT, 'source_snapshot_sha256': expected,
                  'source_snapshot_path': str(path), 'tables': list(TABLES),
                  'catalogs': catalogs, 'copy_order': copy_order(catalogs),
                  'target_history_versions': list(range(1, 50)),
                  'target_history49_name': MIGRATION49,
                  'target_history49_sql_sha256': hashlib.sha256(migration49_sql.encode('utf-8')).hexdigest(),
                  'authority': 'TEST_ONLY_PRIVATE_CATALOG_OVERLAY_NO_GAMEPLAY_ROWS'}
        with closing(sqlite3.connect(':memory:')) as schema_db:
            schema_db.executescript(migration49_sql)
            result['target_schema49_addition'] = [row for row in schemas(schema_db) if row[2] in SCHEMA49_TABLES]
    require(sha(path) == expected, 'Snapshot changed while sealing')
    return result


def guard(db):
    schema = schemas(db)
    return {'schema': schema,
            'noncatalog': {row[1]: fingerprint(db.execute('SELECT * FROM ' + quote(row[1])).fetchall())
                           for row in schema if row[0] == 'table' and row[1] not in TABLES},
            'pragmas': {name: db.execute('PRAGMA ' + name).fetchone()[0]
                        for name in ('application_id', 'user_version', 'encoding')}}


def target_scope(path):
    original = Path(path).absolute()
    require(original.is_file() and original.parent.name.startswith('private-native-blackbox-'),
            'Target must be an existing private-native-blackbox-* database')
    # No shared file/link may masquerade as a disposable target.
    require(original.stat().st_nlink == 1, 'Target database is hardlinked')
    for component in (original, *original.parents):
        require(not component.is_symlink() and not (getattr(component.lstat(), 'st_file_attributes', 0) & 0x400),
                'Target path has a reparse point')
    return original.resolve()


def _insert_missing(db, table, rows):
    if rows:
        sql = 'INSERT INTO ' + quote(table) + ' VALUES(' + ','.join('?' for _ in rows[0]) + ')'
        db.executemany(sql, rows)


def prepare_catalogs(source_snapshot, private_db, expectedpins):
    """Return an exact preservation receipt; raise and rollback on any mismatch.

    expectedpins is the sealed manifest dictionary or its JSON Path. Caller owns
    exclusive disposable DB provisioning, before any server/client is started.
    Source database is opened immutable/read-only and never attached writable.
    """
    pins = json.loads(Path(expectedpins).read_text('utf-8')) if not isinstance(expectedpins, dict) else expectedpins
    require(pins.get('format') == FORMAT and pins.get('tables') == list(TABLES), 'Manifest catalog scope differs')
    source, target = Path(source_snapshot).resolve(), target_scope(private_db)
    require(source != target, 'Source and target must be independent files')
    require(sha(source) == pins['source_snapshot_sha256'], 'Source snapshot file hash differs')
    with closing(readonly_snapshot(source)) as src:
        integrity(src)
        source_catalogs = catalog(src)
        require(source_catalogs == pins['catalogs'], 'Source catalog DDL/column/count/digest differs')
        order = copy_order(source_catalogs)
        require(order == pins['copy_order'], 'Manifest catalog copy order differs')
        source_rows = {table: src.execute('SELECT * FROM ' + quote(table)).fetchall() for table in TABLES}
        with closing(sqlite3.connect(target.as_uri() + '?mode=rw', uri=True, timeout=5)) as db:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('BEGIN IMMEDIATE')
            try:
                integrity(db)
                history = db.execute('SELECT version,name,sql_text FROM schema_migrations ORDER BY version').fetchall()
                require([row[0] for row in history] == pins['target_history_versions'] == list(range(1,50)),
                        'Target needs exact schema49 history')
                require(history[-1][1] == pins['target_history49_name'] == MIGRATION49
                        and hashlib.sha256(history[-1][2].encode('utf-8')).hexdigest() == pins['target_history49_sql_sha256'],
                        'Target migration49 identity/SQL differs')
                require([row for row in schemas(db) if row[2] in SCHEMA49_TABLES] == pins['target_schema49_addition'],
                        'Target migration49 actual table/index DDL differs')
                before = guard(db)
                target_catalogs = catalog(db)
                inserted = {}
                # Validate ALL target schema/subsets before first insertion.
                missing_by_table = {}
                for table in TABLES:
                    for key in ('schema', 'columns', 'primary_key_indices', 'foreign_keys'):
                        require(target_catalogs[table][key] == source_catalogs[table][key],
                                'Target catalog schema differs: ' + table + '/' + key)
                    original = db.execute('SELECT * FROM ' + quote(table)).fetchall()
                    existing = {typed(row) for row in original}
                    full = {typed(row) for row in source_rows[table]}
                    require(existing <= full, 'Target PK/content collision or extra row: ' + table)
                    keys = source_catalogs[table]['primary_key_indices']
                    key_map = {typed(tuple(row[index] for index in keys)): typed(row) for row in original}
                    missing = []
                    for row in source_rows[table]:
                        encoded, pk = typed(row), typed(tuple(row[index] for index in keys))
                        require(pk not in key_map or key_map[pk] == encoded, 'Target typed PK collision: ' + table)
                        if pk not in key_map:
                            missing.append(row)
                    missing_by_table[table] = missing
                for table in order:
                    _insert_missing(db, table, missing_by_table[table])
                    inserted[table] = len(missing_by_table[table])
                integrity(db)
                require(catalog(db) == source_catalogs, 'Final catalog differs from source')
                require(guard(db) == before, 'Catalog copy changed saved rows/schema/history/sequence')
                require(sha(source) == pins['source_snapshot_sha256'], 'Snapshot changed before target commit')
                db.commit()
                return {'accepted': True, 'authority': pins['authority'], 'target': str(target),
                        'source_snapshot_sha256': pins['source_snapshot_sha256'], 'schema': 49,
                        'catalog_tables': list(TABLES), 'inserted_rows': inserted,
                        'all_catalogs_exact': True, 'noncatalog_typed_rows_exact': True,
                        'all_schema_history_sequence_exact': True, 'foreign_key_check': 0,
                        'existing_catalog_rows_preserved': True, 'source_read_only': True,
                        'no_replace_or_delete': True, 'no_gameplay_rows_copied': True}
            except BaseException:
                db.rollback()
                raise
