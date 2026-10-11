"""Pinned current skills, formal SQL and isolated DBs; no production binary needed."""
from contextlib import closing, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.strike_lab import import_native_skills as catalog


def migrations():
    # Test-only extraction of the actual migration SQL; production uses the server.
    source = (catalog.ROOT / 'src/db/Migration.cpp').read_text(encoding='utf-8')
    return [(int(version), name, sql) for version, name, sql in re.findall(
        r'\{(\d+), "([^"]+)", R"SQL\((.*?)\)SQL"', source, re.DOTALL)]


def migrate_test_database(db, entries):
    db.execute('CREATE TABLE IF NOT EXISTS schema_migrations ('
               'version INTEGER PRIMARY KEY, name TEXT NOT NULL, sql_text TEXT NOT NULL)')
    for version, name, sql in entries:
        if db.execute('SELECT 1 FROM schema_migrations WHERE version=?', (version,)).fetchone():
            continue
        db.executescript(sql)
        db.execute('INSERT INTO schema_migrations VALUES(?,?,?)', (version, name, sql))
        db.commit()


class NativeSkillImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='god2-native-skills-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'test.sqlite'
        self.db = sqlite3.connect(self.path)
        self.addCleanup(self.db.close)
        self.migrations = migrations()
        migrate_test_database(self.db, self.migrations)
        self.client = catalog.ROOT.parent / 'God2'
        self.db.execute("INSERT INTO accounts(username,password_hash) VALUES('test-only','not-a-login')")
        # Shared provenance and map records must survive skill imports unchanged.
        self.db.execute('INSERT INTO native_data_sources VALUES(?,?,?,?,?,?,?,?,?)',
                        ('test-only-map', 'test-only/map.bin', 'a' * 64, 'b' * 64,
                         'c' * 64, 'test-only', '0x1', '0x2', 1))
        self.db.execute('INSERT INTO native_map_catalog VALUES(?,?,?,?,?,?,?,?)',
                        ('test-only-map', 0, 1, 'd' * 64, b'TEST-ONLY', 1, 0, 0))
        self.db.commit()
        self.accounts = self.db.execute('SELECT * FROM accounts').fetchall()
        self.maps = self.db.execute('SELECT * FROM native_map_catalog').fetchall()

    def stored(self):
        return self.db.execute(f'SELECT {catalog.RECORD_COLUMNS} FROM native_skill_catalog '
                               'WHERE dataset_id=? ORDER BY source_record_index',
                               (catalog.DATASET,)).fetchall()

    def assert_empty(self):
        self.assertEqual(self.stored(), [])
        self.assertEqual(self.db.execute('SELECT * FROM native_data_sources WHERE dataset_id=?',
                                        (catalog.DATASET,)).fetchall(), [])
        self.assertEqual(self.db.execute('SELECT * FROM accounts').fetchall(), self.accounts)
        self.assertEqual(self.db.execute('SELECT * FROM native_map_catalog').fetchall(), self.maps)
        self.assertFalse(self.db.in_transaction)

    def test_old_migrations_immutable(self):
        self.assertEqual([(version, hashlib.sha256(sql.encode()).hexdigest())
                          for version, _, sql in self.migrations[:4]], [
            (1, '2975a7c05e5365c2ced18dbf4c9708c8c9798a51cffe5f9e823c5442554fb0e8'),
            (2, 'ac353779eb19622532ab61238fa535458f9f22ad3d898628287665c2f61a03da'),
            (3, '32237b7705f1a1fc409f996020c444c890e5539dd6f4b98d8c6303032fc05c65'),
            (4, 'abc14f15fab977e3e86c566c365ad94d5be83096cb8546865f7c795f22c6a072')])
        self.assertEqual(self.migrations[4][:2], (5, 'native_skill_catalog'))
        self.assert_empty()

    def test_all_original_rows_roundtrip_and_idempotence(self):
        source = (self.client / catalog.SOURCE).read_bytes()
        self.assertEqual(len(source), 112660)
        self.assertEqual(hashlib.sha256(source).hexdigest(),
                         '7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51')
        result = catalog.import_catalog(self.db, self.client)
        self.assertEqual(result, {'dataset': catalog.DATASET, 'rows': 448, 'inserted': 448})
        before_changes = self.db.total_changes
        self.assertEqual(catalog.import_catalog(self.db, self.client)['inserted'], 0)
        self.assertEqual(self.db.total_changes, before_changes)
        rows = self.stored()
        self.assertEqual(rows, catalog.pinned_records(self.client))
        self.assertEqual([sum(row[5] == kind for row in rows) for kind in range(4)], [121, 129, 87, 111])
        for index, row in enumerate(rows):
            dataset, ordinal, offset, digest, raw, kind, definition_id = row
            self.assertEqual(dataset, catalog.DATASET)
            self.assertEqual(ordinal, index)
            self.assertEqual(offset, 8 + kind * 0x6e04 + (definition_id - 1) * 110)
            self.assertEqual(raw, source[offset:offset + 110])
            self.assertEqual(raw[:2], bytes((definition_id, kind)))
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
        self.assertEqual(self.db.execute('SELECT * FROM native_data_sources WHERE dataset_id=?',
                                        (catalog.DATASET,)).fetchall(), [catalog.SOURCE_ROW])
        self.assertEqual(catalog.SOURCE_ROW[2], catalog.SOURCE_ROW[3])
        self.assertEqual(self.db.execute('SELECT * FROM accounts').fetchall(), self.accounts)
        self.assertEqual(self.db.execute('SELECT * FROM native_map_catalog').fetchall(), self.maps)
        self.assertEqual(self.db.execute('PRAGMA quick_check').fetchall(), [('ok',)])
        self.assertEqual(self.db.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_changed_raw_or_hash_is_not_overwritten(self):
        catalog.import_catalog(self.db, self.client)
        for assignment in ("raw_record=CAST(substr(raw_record,1,109) || X'FF' AS BLOB)",
                           "record_sha256=replace(hex(zeroblob(32)),'0','a')"):
            with self.subTest(assignment=assignment):
                original = self.stored()[0]
                self.db.execute(f'UPDATE native_skill_catalog SET {assignment} WHERE source_record_index=0')
                self.db.commit()
                before = self.stored()
                self.assertNotEqual(before[0], original)
                with self.assertRaisesRegex(ValueError, 'conflict'):
                    catalog.import_catalog(self.db, self.client)
                self.assertEqual(self.stored(), before)
                self.assertFalse(self.db.in_transaction)
                self.db.execute('UPDATE native_skill_catalog SET record_sha256=?,raw_record=? '
                                'WHERE source_record_index=0', original[3:5])
                self.db.commit()

    def test_conflicting_source_and_partial_import(self):
        catalog.import_catalog(self.db, self.client)
        self.db.execute("UPDATE native_data_sources SET source_path='conflict' WHERE dataset_id=?",
                        (catalog.DATASET,))
        self.db.commit()
        with self.assertRaisesRegex(ValueError, 'Conflicting native skill source'):
            catalog.import_catalog(self.db, self.client)
        self.db.execute('UPDATE native_data_sources SET source_path=? WHERE dataset_id=?',
                        (catalog.SOURCE, catalog.DATASET))
        self.db.execute('DELETE FROM native_skill_catalog WHERE source_record_index=7')
        self.db.commit()
        with self.assertRaisesRegex(ValueError, 'incomplete import'):
            catalog.import_catalog(self.db, self.client)
        self.assertEqual(len(self.stored()), 447)

    def test_orphans_are_not_repaired(self):
        catalog.import_catalog(self.db, self.client)
        self.db.execute('PRAGMA foreign_keys=OFF')
        self.db.execute('DELETE FROM native_data_sources WHERE dataset_id=?', (catalog.DATASET,))
        self.db.commit()
        before = self.stored()
        with self.assertRaisesRegex(ValueError, 'Orphaned'):
            catalog.import_catalog(self.db, self.client)
        self.assertEqual(self.stored(), before)
        self.assertIsNone(self.db.execute('SELECT 1 FROM native_data_sources WHERE dataset_id=?',
                                         (catalog.DATASET,)).fetchone())

    def test_insert_failure_rolls_back_entire_import(self):
        self.db.execute('CREATE TRIGGER reject_skill BEFORE INSERT ON native_skill_catalog '
                        "WHEN NEW.source_record_index=224 BEGIN SELECT RAISE(ABORT,'test failure'); END")
        self.db.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            catalog.import_catalog(self.db, self.client)
        self.assert_empty()

    def test_trigger_source_mutation_rolls_back(self):
        self.db.execute('CREATE TRIGGER mutate_source AFTER INSERT ON native_skill_catalog '
                        "WHEN NEW.source_record_index=447 BEGIN UPDATE native_data_sources SET source_path='bad' "
                        'WHERE dataset_id=NEW.dataset_id; END')
        self.db.commit()
        with self.assertRaisesRegex(ValueError, 'conflict'):
            catalog.import_catalog(self.db, self.client)
        self.assert_empty()

    def test_pin_size_count_and_decoded_identity_fail_before_writes(self):
        with patch.object(catalog, 'SOURCE_SHA', '0' * 64):
            with self.assertRaisesRegex(ValueError, 'identity changed'):
                catalog.import_catalog(self.db, self.client)
        client = self.root / 'client'
        source_path = client / catalog.SOURCE
        source_path.parent.mkdir(parents=True)
        source_path.write_bytes(b'1.03')
        with self.assertRaisesRegex(ValueError, 'path/size bound'):
            catalog.import_catalog(self.db, client)
        source = bytearray((self.client / catalog.SOURCE).read_bytes())
        source[-1] ^= 1
        source_path.write_bytes(source)
        with self.assertRaisesRegex(ValueError, 'identity changed'):
            catalog.import_catalog(self.db, client)
        with patch.object(catalog, 'KIND_COUNTS', (120, 130, 87, 111)):
            with self.assertRaisesRegex(ValueError, 'counts changed'):
                catalog.import_catalog(self.db, self.client)
        definitions = catalog.identity.decode_definitions((self.client / catalog.SOURCE).read_bytes())
        item = definitions[0, 1]
        definitions[0, 1] = catalog.identity.Definition(item.id, item.kind, item.source_offset + 1, item.raw)
        with patch.object(catalog.identity, 'decode_definitions', return_value=definitions):
            with self.assertRaisesRegex(ValueError, 'record identity mismatch'):
                catalog.import_catalog(self.db, self.client)
        self.assert_empty()

    def test_outer_transaction_is_preserved(self):
        self.db.execute('BEGIN')
        self.db.execute("INSERT INTO accounts(username,password_hash) VALUES('test-pending','test-only')")
        with self.assertRaisesRegex(ValueError, 'own transaction'):
            catalog.import_catalog(self.db, self.client)
        self.assertTrue(self.db.in_transaction)
        self.assertEqual(self.db.execute('SELECT count(*) FROM accounts').fetchone(), (2,))
        self.db.rollback()
        self.assert_empty()

    def test_missing_migration_and_unrelated_fk_corruption(self):
        self.db.execute('DELETE FROM schema_migrations WHERE version=5')
        self.db.commit()
        with self.assertRaisesRegex(ValueError, 'migration first'):
            catalog.import_catalog(self.db, self.client)
        self.assert_empty()
        self.db.execute('INSERT INTO schema_migrations VALUES(?,?,?)', self.migrations[4])
        self.db.commit()
        self.db.execute('PRAGMA foreign_keys=OFF')
        self.db.execute("INSERT INTO characters(account_id,name) VALUES(999,'test-only-orphan')")
        self.db.commit()
        with self.assertRaisesRegex(ValueError, 'foreign key check failed'):
            catalog.import_catalog(self.db, self.client)
        self.assert_empty()

    def test_sql_constraints(self):
        catalog.import_catalog(self.db, self.client)
        for assignment in ('source_offset=9', 'source_offset=118', 'source_record_index=-1',
                           'source_record_index=1020', 'kind=-1', 'kind=4', 'definition_id=0',
                           'definition_id=256', 'raw_record=zeroblob(110)',
                           'raw_record=zeroblob(109)', "record_sha256='bad'"):
            with self.subTest(assignment=assignment):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.db.execute(f'UPDATE native_skill_catalog SET {assignment} WHERE source_record_index=0')
                self.db.rollback()
        self.assertEqual(self.stored(), catalog.pinned_records(self.client))

    def test_cli_backup_precedes_migration_and_import(self):
        target = self.root / 'cli.sqlite'
        with closing(sqlite3.connect(target)) as db:
            migrate_test_database(db, self.migrations[:4])
        config = self.root / 'server.json'
        config.write_text(json.dumps({'database': {'type': 'sqlite', 'path': str(target)}}))
        executable = self.root / 'test-only-server.exe'

        def migrate(command, **kwargs):
            self.assertEqual(command, [str(executable), '--config', str(config), '--migrate-only'])
            self.assertTrue(kwargs['check'])
            self.assertEqual(kwargs['cwd'], self.root)
            backups = list((self.root / 'artifacts/db-backups').glob('native-skills-*.sqlite'))
            self.assertEqual(len(backups), 1)
            with closing(sqlite3.connect(backups[0])) as backup:
                self.assertEqual(backup.execute('SELECT max(version) FROM schema_migrations').fetchone(), (4,))
                self.assertIsNone(backup.execute("SELECT 1 FROM sqlite_master WHERE name='native_skill_catalog'").fetchone())
            with closing(sqlite3.connect(target)) as db:
                migrate_test_database(db, self.migrations)

        output = io.StringIO()
        with patch.object(catalog, 'ROOT', self.root), patch.object(catalog.subprocess, 'run', side_effect=migrate), \
                patch('sys.argv', ['import_native_skills', '--config', str(config), '--client', str(self.client),
                                   '--server-exe', str(executable)]), redirect_stdout(output):
            catalog.main()
        result = json.loads(output.getvalue())
        self.assertEqual(result['inserted'], 448)
        self.assertEqual(Path(result['database']), target)
        with closing(sqlite3.connect(target)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM native_skill_catalog').fetchone(), (448,))

    def test_cli_rejects_source_before_backup_or_migration(self):
        config = self.root / 'server.json'
        config.write_text(json.dumps({'database': {'type': 'sqlite', 'path': str(self.path)}}))
        with patch.object(catalog, 'ROOT', self.root), patch.object(catalog, 'SOURCE_SHA', '0' * 64), \
                patch.object(catalog.subprocess, 'run') as server, patch('sys.argv', [
                    'import_native_skills', '--config', str(config), '--client', str(self.client)]):
            with self.assertRaisesRegex(ValueError, 'identity changed'):
                catalog.main()
        server.assert_not_called()
        self.assertFalse((self.root / 'artifacts').exists())
        self.assert_empty()

    @unittest.skipUnless(os.environ.get('GOD2_NATIVE_SKILL_READER_TEST'), 'Optional private C++ reader executable')
    def test_original_import_through_cpp_reader(self):
        catalog.import_catalog(self.db, self.client)
        result = subprocess.run([os.environ['GOD2_NATIVE_SKILL_READER_TEST'], '--verify-import', str(self.path),
                                 str(self.client / catalog.SOURCE)], check=True, capture_output=True,
                                text=True, timeout=15)
        self.assertIn('All 448 original skill records verified', result.stdout)


if __name__ == '__main__':
    unittest.main()
