"""Original armor definitions: exact import, no player grant or inferred stats."""
import sqlite3
import unittest
from tools.strike_lab import import_native_armor_20261002 as armor


class NativeArmorImport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = armor.pinned_records()

    def test_exact_idempotent_catalog_preserves_player_rows(self):
        with sqlite3.connect(':memory:') as db:
            db.execute('CREATE TABLE players(id INTEGER PRIMARY KEY, save BLOB)')
            db.execute('INSERT INTO players VALUES(1,?)', (bytes(range(256)),))
            db.commit()
            before = db.execute('SELECT * FROM players').fetchall()
            first = armor.import_catalog(db, records=self.records)
            self.assertEqual(first['inserted'], 1354)
            self.assertEqual(first['player_instances_created'], 0)
            self.assertEqual(first['combat_rules_created'], 0)
            actual = tuple(tuple(db.execute('SELECT * FROM '+t+' ORDER BY '+o))
                           for t, o in zip(armor.TABLES, armor.ORDERS))
            self.assertEqual(actual, self.records)
            self.assertEqual(armor.import_catalog(db, records=self.records)['inserted'], 0)
            self.assertEqual(db.execute('SELECT * FROM players').fetchall(), before)

    def test_corrupt_or_partial_saved_catalog_refuses_overwrite(self):
        for sql in ('DELETE FROM native_armor_rows WHERE item_id=1001',
                    "UPDATE native_armor_sources SET source_sha256=replace(source_sha256,'7','6') WHERE family='EQU'",
                    'UPDATE native_armor_rows SET decoded_offset=decoded_offset+1 WHERE item_id=1001'):
            with self.subTest(sql=sql), sqlite3.connect(':memory:') as db:
                armor.import_catalog(db, records=self.records)
                db.execute(sql)
                db.commit()
                before = tuple(tuple(db.execute('SELECT * FROM '+t+' ORDER BY '+o))
                               for t, o in zip(armor.TABLES, armor.ORDERS))
                with self.assertRaises(ValueError):
                    armor.import_catalog(db, records=self.records)
                self.assertEqual(tuple(tuple(db.execute('SELECT * FROM '+t+' ORDER BY '+o))
                                       for t, o in zip(armor.TABLES, armor.ORDERS)), before)

    def test_changed_native_records_and_types_cannot_bypass_pin(self):
        cases = []
        changed = [list(group) for group in self.records]
        changed[1] = changed[1][:-1]
        cases.append(changed)
        for index, replacement in ((1, True), (5, '0'*64), (8, bytes(396))):
            changed = [list(group) for group in self.records]
            row = list(changed[1][0]); row[index] = replacement
            changed[1][0] = row
            cases.append(changed)
        for case in cases:
            with self.subTest(case=type(case)), self.assertRaises(ValueError):
                armor.validate_records(case)

    def test_insert_failure_rolls_back_all_rows(self):
        with sqlite3.connect(':memory:') as db:
            armor.install(db)
            db.execute("CREATE TRIGGER reject_one_armor BEFORE INSERT ON native_armor_rows WHEN NEW.item_id=20001 BEGIN SELECT RAISE(IGNORE); END")
            db.commit()
            with self.assertRaises(ValueError):
                armor.import_catalog(db, records=self.records)
            self.assertEqual(db.execute('SELECT count(*) FROM native_armor_rows').fetchone(), (0,))
            self.assertEqual(db.execute('SELECT count(*) FROM native_armor_sources').fetchone(), (0,))

    def test_caller_transaction_and_conflicting_schema_reject(self):
        with sqlite3.connect(':memory:') as db:
            db.execute('BEGIN')
            with self.assertRaises(ValueError):
                armor.import_catalog(db, records=self.records)
            self.assertTrue(db.in_transaction)
            db.rollback()
            db.execute('CREATE TABLE native_armor_sources(family TEXT)')
            db.commit()
            with self.assertRaises(ValueError):
                armor.import_catalog(db, records=self.records)
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='native_armor_rows'").fetchone())


if __name__ == '__main__':
    unittest.main()
