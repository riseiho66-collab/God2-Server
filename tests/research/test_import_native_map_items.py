from contextlib import closing
import hashlib
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.strike_lab import import_native_map_items as native
CLIENT=ROOT.parent/'God2'

class MapItemSourceTests(unittest.TestCase):
    def test_real_source_flags_rows_and_idempotence(self):
        sources,rows=native.pinned_records(CLIENT)
        self.assertEqual([r[0] for r in rows],[5569,5576])
        self.assertEqual([r[2] for r in rows],[8236,8243])
        self.assertEqual([r[6] for r in rows],[3,0])
        self.assertEqual([r[8] for r in rows],[55069,55076])
        self.assertEqual(rows[1][9].decode('cp950'),'崑崙仙界地圖')
        for row in rows:
            self.assertEqual(row[12],bytes((1,0,0,0,1,1,1,1,1,0,0,0)))
            self.assertEqual(row[4],hashlib.sha256(row[5]).hexdigest())
            self.assertEqual(row[13],'SOURCE_DISPLAY_ONLY')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.db'
            with closing(sqlite3.connect(path)) as db:
                native.install(db);native.install(db)
                self.assertEqual(native.import_catalog(db,CLIENT)['inserted'],2)
                before=tuple(db.iterdump())
                self.assertEqual(native.import_catalog(db,CLIENT)['inserted'],0)
                self.assertEqual(tuple(db.iterdump()),before)
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(native.import_catalog(db,CLIENT)['inserted'],0)
                self.assertEqual(tuple(db.iterdump()),before)

    def test_bad_source_and_decode_write_nothing(self):
        with closing(sqlite3.connect(':memory:')) as db:
            with patch.object(Path,'read_bytes',return_value=b'bad'):
                with self.assertRaisesRegex(ValueError,'source pin'):native.import_catalog(db,CLIENT)
            with patch.object(native,'decode_csvz',return_value=b'bad'):
                with self.assertRaisesRegex(ValueError,'decoded pin'):native.import_catalog(db,CLIENT)
            self.assertEqual(db.execute('SELECT name FROM sqlite_master').fetchall(),[])

    def test_partial_wrong_flags_or_source_refuse_overwrite(self):
        for mutation in ('DELETE FROM native_map_item_rows WHERE item_id=5576',
            "UPDATE native_map_item_rows SET source_flags=zeroblob(12) WHERE item_id=5576",
            "UPDATE native_map_item_sources SET source_sha256=printf('%064d',0)"):
            with self.subTest(mutation=mutation),closing(sqlite3.connect(':memory:')) as db:
                native.import_catalog(db,CLIENT);db.execute(mutation);db.commit();before=tuple(db.iterdump())
                with self.assertRaisesRegex(ValueError,'Conflicting/partial'):native.import_catalog(db,CLIENT)
                self.assertEqual(tuple(db.iterdump()),before)
                self.assertFalse(db.in_transaction)

    def test_write_failure_and_changed_readback_roll_back(self):
        for action in ("SELECT RAISE(ABORT,'fixture')",
                       "UPDATE native_map_item_rows SET source_flags=zeroblob(12) WHERE item_id=NEW.item_id"):
            with self.subTest(action=action),closing(sqlite3.connect(':memory:')) as db:
                native.install(db)
                db.execute('CREATE TRIGGER fail_second AFTER INSERT ON native_map_item_rows WHEN NEW.item_id=5576 BEGIN '+action+'; END')
                before=tuple(db.iterdump())
                with self.assertRaises((ValueError,sqlite3.DatabaseError)):native.import_catalog(db,CLIENT)
                self.assertEqual(tuple(db.iterdump()),before)
                self.assertFalse(db.in_transaction)

    def test_foreign_transaction_and_schema_untouched(self):
        with closing(sqlite3.connect(':memory:')) as db:
            db.execute('CREATE TABLE unrelated(value)');db.execute('INSERT INTO unrelated VALUES(7)')
            for action in (lambda:native.install(db),lambda:native.import_catalog(db,CLIENT)):
                with self.assertRaisesRegex(ValueError,'own transaction'):action()
                self.assertTrue(db.in_transaction)
            db.rollback();db.execute('CREATE TABLE native_map_item_sources(wrong TEXT)');before=tuple(db.iterdump())
            with self.assertRaisesRegex(ValueError,'schema'):native.import_catalog(db,CLIENT)
            self.assertEqual(tuple(db.iterdump()),before)

if __name__=='__main__':unittest.main()
