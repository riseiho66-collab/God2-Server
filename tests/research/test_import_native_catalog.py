"""Formal migrations and original-only catalog import, isolated temporary DBs."""
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.strike_lab import import_native_catalog as catalog


class NativeCatalogImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='god2-native-catalog-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'test.sqlite'
        config = json.loads((catalog.ROOT / 'config/server.json').read_text())
        config['database']['path'] = str(self.path)
        config_path = self.root / 'server.json'
        config_path.write_text(json.dumps(config), encoding='utf-8')
        self.config = config_path
        subprocess.run([str(catalog.ROOT / 'build/Release/god2-server.exe'),
                        '--config', str(config_path), '--migrate-only'],
                       check=True, capture_output=True, text=True)
        self.db = sqlite3.connect(self.path)
        self.addCleanup(self.db.close)
        self.db.execute("INSERT INTO accounts(username,password_hash) VALUES('test-only','not-a-login')")
        self.db.commit()
        self.accounts = self.db.execute('SELECT * FROM accounts').fetchall()
        self.client = catalog.ROOT.parent / 'God2'

    def test_all_native_rows_roundtrip_and_idempotence(self):
        result = catalog.import_catalog(self.db, self.client)
        self.assertEqual(result['inserted'], 144)
        self.assertEqual(catalog.import_catalog(self.db, self.client)['inserted'], 0)
        self.assertEqual(self.db.execute('SELECT * FROM native_data_sources').fetchall(), [catalog.SOURCE_ROW])
        self.assertEqual(self.db.execute('SELECT * FROM native_map_catalog ORDER BY source_record_index').fetchall(),
                         catalog.pinned_records(self.client))
        self.assertEqual(self.db.execute('SELECT * FROM accounts').fetchall(), self.accounts)
        self.assertEqual(self.db.execute('PRAGMA quick_check').fetchall(), [('ok',)])
        self.assertEqual(self.db.execute('PRAGMA foreign_key_check').fetchall(), [])
        self.assertEqual(catalog.configured_database(self.config), self.path)

    def test_changed_record_is_not_overwritten(self):
        catalog.import_catalog(self.db, self.client)
        self.db.execute('UPDATE native_map_catalog SET kind=(kind+1)%4 WHERE source_record_index=0')
        self.db.commit()
        before = self.db.execute('SELECT * FROM native_map_catalog').fetchall()
        with self.assertRaisesRegex(ValueError, 'conflict'):
            catalog.import_catalog(self.db, self.client)
        self.assertEqual(self.db.execute('SELECT * FROM native_map_catalog').fetchall(), before)
        self.assertFalse(self.db.in_transaction)

    def test_changed_source_and_partial_dataset_are_not_accepted(self):
        catalog.import_catalog(self.db, self.client)
        self.db.execute("UPDATE native_data_sources SET source_path='conflicting-source'")
        self.db.commit()
        with self.assertRaisesRegex(ValueError, 'Conflicting native source'):
            catalog.import_catalog(self.db, self.client)
        self.db.execute('UPDATE native_data_sources SET source_path=?', (catalog.SOURCE,))
        self.db.execute('DELETE FROM native_map_catalog WHERE source_record_index=1')
        self.db.commit()
        with self.assertRaisesRegex(ValueError, 'incomplete import'):
            catalog.import_catalog(self.db, self.client)
        self.assertEqual(self.db.execute('SELECT count(*) FROM native_map_catalog').fetchone(), (143,))

    def test_insert_error_rolls_back_source_and_records(self):
        self.db.execute("CREATE TRIGGER reject_catalog BEFORE INSERT ON native_map_catalog "
                        "WHEN NEW.source_record_index=71 BEGIN SELECT RAISE(ABORT,'test failure'); END")
        self.db.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            catalog.import_catalog(self.db, self.client)
        self.assertEqual(self.db.execute('SELECT count(*) FROM native_data_sources').fetchone(), (0,))
        self.assertEqual(self.db.execute('SELECT count(*) FROM native_map_catalog').fetchone(), (0,))
        self.assertEqual(self.db.execute('SELECT * FROM accounts').fetchall(), self.accounts)

    def test_pin_failure_and_outer_transaction_have_no_writes(self):
        with patch.object(catalog, 'SOURCE_SHA', '0' * 64):
            with self.assertRaisesRegex(ValueError, 'identity changed'):
                catalog.import_catalog(self.db, self.client)
        self.assertEqual(self.db.execute('SELECT count(*) FROM native_data_sources').fetchone(), (0,))
        self.db.execute('BEGIN')
        with self.assertRaisesRegex(ValueError, 'own transaction'):
            catalog.import_catalog(self.db, self.client)
        self.assertTrue(self.db.in_transaction)
        self.db.rollback()

    def test_formal_recovered_server_lua_reads_all_original_records(self):
        catalog.import_catalog(self.db, self.client)
        rows = catalog.pinned_records(self.client)
        scripts = self.root / 'scripts'
        scripts.mkdir()
        checks = ['assert(GOD2_FIXTURE_MODE == false)']
        source_fields = ('dataset_id', 'source_path', 'source_sha256', 'decoded_sha256',
                         'native_image_sha256', 'source_section', 'loader_rva',
                         'lookup_rva', 'row_count')
        source_checks = ' '.join(
            'assert(r.source.%s==%s);' % (field, json.dumps(value, ensure_ascii=True))
            for field, value in zip(source_fields, catalog.SOURCE_ROW))
        for _, index, line, digest, raw, area, scene, kind in rows:
            literal = ''.join('\\%03d' % value for value in raw)
            checks.append(
                'do local r=native_map_catalog(%d,%d); assert(r); '
                'assert(r.area==%d and r.scene==%d); '
                'assert(r.source_record_index==%d and r.source_line==%d and r.kind==%d); '
                'assert(r.raw_record=="%s"); assert(r.record_sha256=="%s"); '
                '%s end'
                % (area, scene, area, scene, index, line, kind, literal, digest, source_checks))
        checks.append('log("NATIVE_CATALOG_ALL_144_VERIFIED")')
        bootstrap = scripts / 'bootstrap.lua'
        bootstrap.write_text('\n'.join(checks), encoding='ascii')
        config = json.loads((catalog.ROOT / 'config/recovered-world-entry.json').read_text())
        config['database']['path'] = str(self.path)
        config['server'].update(port=0, character_port=0, worker_threads=1)
        config['lua'].update(bootstrap=str(bootstrap), script_root=str(scripts), hot_reload=False)
        config['logging']['file'] = str(self.root / 'server.log')
        config['protocol']['packet_dump'] = False
        self.config.write_text(json.dumps(config), encoding='utf-8')
        result = subprocess.run([str(catalog.ROOT / 'build/Release/god2-server.exe'),
                                 '--config', str(self.config), '--run-for', '1'],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertIn('NATIVE_CATALOG_ALL_144_VERIFIED', (self.root / 'server.log').read_text())
        self.assertEqual(self.db.execute('SELECT * FROM accounts').fetchall(), self.accounts)
        self.assertEqual(self.db.execute('SELECT * FROM native_map_catalog ORDER BY source_record_index').fetchall(), rows)


if __name__ == '__main__':
    unittest.main()
