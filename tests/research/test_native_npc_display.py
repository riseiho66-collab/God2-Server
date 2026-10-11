"""Actual pinned source/memory match and transactional NPC catalog regressions."""
from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path
from tools.strike_lab import import_native_npc_display as m

class NpcCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.client=m.ROOT.parent/'God2';cls.rows=m.pinned_rows(cls.client)
    def test_full_source_memory_and_fields(self):
        self.assertEqual(len(self.rows),4043)
        self.assertEqual(m.sha(m.canonical(self.rows)),m.DATASET_SHA)
        self.assertEqual(max(r[0] for r in self.rows),6224)
        self.assertEqual(len(next(r for r in self.rows if r[0]==1156)[5]),28)
    def test_idempotent_empty_and_exact(self):
        with closing(sqlite3.connect(':memory:')) as db:
            result=m.install(db,self.client,install_schema=True);self.assertEqual(result['inserted'],4043)
            self.assertEqual(m.install(db,self.client)['inserted'],0)
            self.assertEqual(db.execute('SELECT * FROM native_npc_display_rows ORDER BY npc_key').fetchall(),self.rows)
    def test_bad_source_before_schema(self):
        with tempfile.TemporaryDirectory() as directory,closing(sqlite3.connect(':memory:')) as db:
            source=Path(directory)/m.SOURCE;source.parent.mkdir(parents=True);source.write_bytes(b'bad')
            with self.assertRaises(ValueError):m.install(db,Path(directory),install_schema=True)
            self.assertEqual(db.execute('SELECT name FROM sqlite_master').fetchall(),[])
    def test_wrong_receipt_before_schema(self):
        with tempfile.TemporaryDirectory() as directory,closing(sqlite3.connect(':memory:')) as db:
            receipt=Path(directory)/'receipt.json';receipt.write_bytes(b'{"accepted":true}')
            with self.assertRaises(ValueError):m.install(db,self.client,receipt,True)
            self.assertEqual(db.execute('SELECT name FROM sqlite_master').fetchall(),[])
    def test_conflict_preserved(self):
        with closing(sqlite3.connect(':memory:')) as db:
            m.install(db,self.client,install_schema=True)
            db.execute('UPDATE native_npc_display_rows SET source_line=999 WHERE npc_key=1');db.commit();before=db.serialize()
            with self.assertRaises(ValueError):m.install(db,self.client)
            self.assertEqual(db.serialize(),before)
    def test_partial_failure_rolls_back(self):
        with closing(sqlite3.connect(':memory:')) as db:
            for sql in m.SCHEMA:db.execute(sql)
            db.execute("CREATE TRIGGER fail_npc BEFORE INSERT ON native_npc_display_rows WHEN NEW.npc_key=2000 BEGIN SELECT RAISE(ABORT,'fixture'); END");db.commit();before=db.serialize()
            with self.assertRaises(sqlite3.DatabaseError):m.install(db,self.client)
            self.assertEqual(db.serialize(),before)
    def test_existing_transaction_not_taken(self):
        with closing(sqlite3.connect(':memory:')) as db:
            db.execute('BEGIN')
            with self.assertRaises(ValueError):m.install(db,self.client,install_schema=True)
            self.assertTrue(db.in_transaction)

if __name__=='__main__':unittest.main()
