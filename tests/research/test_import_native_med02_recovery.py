"""Pinned MED02 tooltip import into isolated formal SQLite."""
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest

from tools.strike_lab import import_native_med02_recovery as catalog


class NativeMed02RecoveryImportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='god2-med02-')
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
        self.db.execute("INSERT INTO accounts(username,password_hash) VALUES('med02-test','not-a-login')")
        self.db.commit()
        self.account_rows = self.db.execute('SELECT * FROM accounts').fetchall()

    def test_71_exact_declarations_and_idempotence(self):
        rows = catalog.pinned_rows(self.client)
        self.assertEqual(len(rows), 71)
        self.assertEqual(catalog.import_catalog(self.db, self.client)['inserted'], 71)
        self.assertEqual(catalog.import_catalog(self.db, self.client)['inserted'], 0)
        self.assertEqual(self.db.execute('SELECT * FROM native_data_sources WHERE dataset_id=?',
                                         (catalog.DATASET,)).fetchone(), catalog.SOURCE_ROW)
        self.assertEqual(self.db.execute('SELECT * FROM native_med02_recovery_declarations '
                                         'ORDER BY source_record_index').fetchall(), rows)
        amounts = self.db.execute('SELECT declared_hp,declared_mp FROM '
                                  'native_med02_recovery_declarations WHERE item_id=3113').fetchone()
        self.assertEqual(amounts, (500, 150))
        self.assertEqual(self.db.execute('SELECT * FROM accounts').fetchall(), self.account_rows)
        self.assertEqual(self.db.execute('PRAGMA quick_check').fetchone(), ('ok',))
        self.assertIsNone(self.db.execute('PRAGMA foreign_key_check').fetchone())

    def test_mid_import_failure_rolls_back_and_existing_conflict_refuses(self):
        self.db.execute('CREATE TRIGGER reject_middle BEFORE INSERT ON native_med02_recovery_declarations '
                        "WHEN NEW.item_id=3113 BEGIN SELECT RAISE(ABORT,'test failure'); END")
        self.db.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            catalog.import_catalog(self.db, self.client)
        self.assertEqual(self.db.execute('SELECT count(*) FROM native_med02_recovery_declarations').fetchone(), (0,))
        self.assertIsNone(self.db.execute('SELECT 1 FROM native_data_sources WHERE dataset_id=?',
                                         (catalog.DATASET,)).fetchone())
        self.db.execute('DROP TRIGGER reject_middle')
        self.db.commit()
        catalog.import_catalog(self.db, self.client)
        self.db.execute("UPDATE native_med02_recovery_declarations SET declared_hp=499 WHERE item_id=3113")
        self.db.commit()
        with self.assertRaisesRegex(ValueError, 'conflict'):
            catalog.import_catalog(self.db, self.client)
        self.assertEqual(self.db.execute('SELECT declared_hp FROM native_med02_recovery_declarations '
                                         'WHERE item_id=3113').fetchone(), (499,))
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(self.db.execute('SELECT * FROM accounts').fetchall(), self.account_rows)


if __name__ == '__main__':
    unittest.main()
