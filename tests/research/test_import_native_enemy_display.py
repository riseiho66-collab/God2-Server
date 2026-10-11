"""Current EnyName identity import into an isolated formal server database."""
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest

from tools.strike_lab import import_native_enemy_display as catalog


class NativeEnemyDisplayImportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='god2-enyname-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        database = root / 'test.sqlite'
        config = json.loads((catalog.ROOT / 'config/server.json').read_text(encoding='utf-8'))
        config['database']['path'] = str(database)
        config_path = root / 'server.json'
        config_path.write_text(json.dumps(config), encoding='utf-8')
        result = subprocess.run([str(catalog.ROOT / 'build/Release/god2-server.exe'),
                                 '--config', str(config_path), '--migrate-only'],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.db = sqlite3.connect(database)
        self.addCleanup(self.db.close)
        self.client = catalog.ROOT.parent / 'God2'
        self.db.execute("INSERT INTO accounts(username,password_hash) VALUES('enyname-test','not-a-login')")
        self.db.commit()
        self.account_rows = self.db.execute('SELECT * FROM accounts').fetchall()

    def test_complete_visible_catalog_and_idempotence(self):
        self.assertEqual(catalog.import_catalog(self.db, self.client)['inserted'], 7815)
        self.assertEqual(catalog.import_catalog(self.db, self.client)['inserted'], 0)
        self.assertEqual(self.db.execute('SELECT count(*),sum(lookup_visible) '
                                         'FROM native_enemy_display_catalog').fetchone(), (7815, 7791))
        self.assertEqual(self.db.execute('SELECT count(*),min(ordinal),max(ordinal) '
                                         'FROM native_enemy_display_catalog WHERE area=2 AND scene=0 '
                                         'AND lookup_visible=1').fetchone(), (27, 1, 27))
        self.assertEqual(self.db.execute('SELECT * FROM accounts').fetchall(), self.account_rows)
        self.assertEqual(self.db.execute('PRAGMA quick_check').fetchone(), ('ok',))
        self.assertIsNone(self.db.execute('PRAGMA foreign_key_check').fetchone())

    def test_conflict_refusal_and_transaction_rollback(self):
        self.db.execute('CREATE TRIGGER reject_middle BEFORE INSERT ON native_enemy_display_catalog '
                        "WHEN NEW.source_record_index=100 BEGIN SELECT RAISE(ABORT,'test failure'); END")
        self.db.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            catalog.import_catalog(self.db, self.client)
        self.assertEqual(self.db.execute('SELECT count(*) FROM native_enemy_display_catalog').fetchone(), (0,))
        self.assertIsNone(self.db.execute('SELECT 1 FROM native_data_sources WHERE dataset_id=?',
                                         (catalog.DATASET,)).fetchone())
        self.assertEqual(self.db.execute('SELECT * FROM accounts').fetchall(), self.account_rows)
        self.db.execute('DROP TRIGGER reject_middle')
        self.db.commit()
        catalog.import_catalog(self.db, self.client)
        self.db.execute("UPDATE native_enemy_display_catalog SET name_bytes=x'4142' "
                        'WHERE area=2 AND scene=0 AND ordinal=1 AND lookup_visible=1')
        self.db.commit()
        with self.assertRaisesRegex(ValueError, 'conflict'):
            catalog.import_catalog(self.db, self.client)
        self.assertEqual(self.db.execute('SELECT hex(name_bytes) FROM native_enemy_display_catalog '
                                         'WHERE area=2 AND scene=0 AND ordinal=1 AND lookup_visible=1').fetchone(),
                         ('4142',))
        self.assertFalse(self.db.in_transaction)


if __name__ == '__main__':
    unittest.main()
