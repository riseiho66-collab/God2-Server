import json
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest
from tools.strike_lab import import_native_pet2_categories as native


class NativePet2CategoriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = native.cached(native.ROOT / 'artifacts/research/native-pet2-categories-20260927/records.json')
        cls.executable = Path(os.environ.get('GOD2_NATIVE_PET2_CATEGORY_TEST',
                            native.ROOT / 'build-town-visibility/tests/Release/native-pet2-categories.exe'))

    def setup_db(self, path):
        subprocess.run([str(self.executable), '--initialize', str(path)], check=True, timeout=30)
        db = sqlite3.connect(path)
        return db

    def test_original_fb_selector_and_copied_name_for_all464_rows(self):
        self.assertEqual(native.extract(), self.rows)

    def test_import_idempotence_real_cpp_lookup_and_corruption(self):
        with tempfile.TemporaryDirectory(prefix='god2-pet2-categories-') as directory:
            path = Path(directory) / 'fixture.db'
            db = self.setup_db(path)
            tables_before = db.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name').fetchall()
            self.assertFalse(native.install(db,self.rows)['idempotent'])
            self.assertTrue(native.install(db,self.rows)['idempotent'])
            self.assertEqual(tables_before,db.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name').fetchall())
            self.assertEqual(db.execute('SELECT COUNT(*) FROM accounts').fetchone(),(0,))
            self.assertEqual(db.execute('SELECT COUNT(*) FROM character_pet2_slots').fetchone(),(0,))
            self.assertEqual(db.execute('PRAGMA quick_check').fetchone(),('ok',))
            db.close()
            result = subprocess.run([str(self.executable),'--test',str(path)],
                                    check=True,capture_output=True,text=True,timeout=30)
            self.assertIn('4096 selectors', result.stdout)

    def test_conflicting_existing_import_is_atomic_and_cache_not_self_certifying(self):
        with tempfile.TemporaryDirectory(prefix='god2-pet2-category-conflict-') as directory:
            path = Path(directory) / 'fixture.db'
            with closing(self.setup_db(path)) as db:
                native.install(db,self.rows)
                db.execute('DELETE FROM native_pet2_category_rows WHERE group_id=29 AND category_index=15')
                db.commit()
                before = db.execute('SELECT * FROM native_pet2_category_rows').fetchall()
                with self.assertRaises(ValueError):native.install(db,self.rows)
                self.assertEqual(before, db.execute('SELECT * FROM native_pet2_category_rows').fetchall())
                forged = list(self.rows)
                a,b,c,d,_ = forged[0];forged[0]=(a,b,c,d,b'forged')
                cache = Path(directory)/'forged.json';native.cache(forged,cache)
                with self.assertRaises(ValueError):native.cached(cache)
                with self.assertRaises(ValueError):native.install(db,forged)


if __name__ == '__main__':unittest.main()
