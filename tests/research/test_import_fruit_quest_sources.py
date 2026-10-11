"""Immutable fruit source importer gates; never uses a configured player DB."""
import sqlite3
import unittest
from tools.strike_lab import import_fruit_quest_sources as source


class FruitQuestSourceImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload=source.qualified_payload(source.ROOT.parent/'God2')

    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)

    def install(self,**kwargs):
        return source.install(self.db,self.payload,**kwargs)

    def snapshot(self):
        return tuple(self.db.iterdump())

    def test_exact_payload_idempotence_and_no_player_tables(self):
        first=self.install(install_schema=True)
        self.assertTrue(first['inserted']);self.assertEqual(first['payload_bytes'],30421)
        self.assertEqual(first['player_rows_written'],0)
        before=self.snapshot()
        self.assertFalse(self.install()['inserted']);self.assertEqual(self.snapshot(),before)
        self.assertEqual(self.db.execute('SELECT payload FROM qualified_fruit_quest_sources').fetchone()[0],self.payload)
        self.assertEqual(self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(),[('qualified_fruit_quest_sources',)])

    def test_schema_requires_explicit_install(self):
        before=self.snapshot()
        with self.assertRaises(ValueError):self.install()
        self.assertEqual(self.snapshot(),before);self.assertFalse(self.db.in_transaction)

    def test_bad_payload_never_creates_schema(self):
        for raw in (b'',self.payload[:-1],self.payload+b'\n',b'X'+self.payload[1:],self.payload.replace(b'\r\n',b'\n')):
            with self.subTest(size=len(raw)):
                with self.assertRaises(ValueError):source.install(self.db,raw,install_schema=True)
                self.assertEqual(self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(),[])
                self.assertFalse(self.db.in_transaction)

    def test_existing_different_payload_cannot_be_replaced(self):
        self.install(install_schema=True)
        self.db.execute("UPDATE qualified_fruit_quest_sources SET payload=CAST(X'00'||substr(payload,2) AS BLOB)")
        self.db.commit();before=self.snapshot()
        with self.assertRaises(ValueError):self.install()
        self.assertEqual(self.snapshot(),before)

    def test_trigger_failure_rolls_back_insert(self):
        self.db.execute(source.SCHEMA)
        self.db.execute("CREATE TRIGGER reject_fruit BEFORE INSERT ON qualified_fruit_quest_sources BEGIN SELECT RAISE(ABORT,'fixture'); END")
        self.db.commit();before=self.snapshot()
        with self.assertRaises(sqlite3.IntegrityError):self.install()
        self.assertEqual(self.snapshot(),before);self.assertFalse(self.db.in_transaction)

    def test_trigger_corruption_rolls_back_after_insert(self):
        self.db.execute(source.SCHEMA)
        self.db.execute("CREATE TRIGGER alter_fruit AFTER INSERT ON qualified_fruit_quest_sources BEGIN UPDATE qualified_fruit_quest_sources SET payload=CAST(X'00'||substr(payload,2) AS BLOB); END")
        self.db.commit();before=self.snapshot()
        with self.assertRaises(ValueError):self.install()
        self.assertEqual(self.snapshot(),before);self.assertFalse(self.db.in_transaction)

    def test_does_not_take_over_outer_transaction(self):
        self.db.execute('BEGIN')
        with self.assertRaises(ValueError):self.install(install_schema=True)
        self.assertTrue(self.db.in_transaction)
        self.db.rollback()


if __name__=='__main__':unittest.main()
