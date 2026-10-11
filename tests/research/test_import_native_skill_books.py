"""Pinned SKB metadata promotion without claiming gameplay authority."""
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest

from tools.strike_lab import import_native_skill_books as books
from tools.strike_lab import import_native_skills as skills
from test_import_native_skills import migrate_test_database, migrations


class NativeSkillBookImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = books.CLIENT
        cls.records = books.pinned_records(cls.client)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='god2-native-books-test-')
        self.addCleanup(self.temp.cleanup)
        self.db = sqlite3.connect(Path(self.temp.name) / 'test.sqlite')
        self.addCleanup(self.db.close)
        migrate_test_database(self.db, migrations())
        skills.import_catalog(self.db, self.client)
        self.db.execute("INSERT INTO accounts(username,password_hash) VALUES('preserved','hash')")
        self.db.commit()

    def stored(self):
        return self.db.execute(f'SELECT {books.BOOK_COLUMNS} FROM native_skill_books '
                               'WHERE dataset_id=? ORDER BY source_record_index',
                               (books.DATASET,)).fetchall()

    def test_source_parsed_rows_and_bindings_roundtrip(self):
        expected_books, expected_bindings = self.records
        self.assertEqual(books.import_catalog(self.db, self.client, records=self.records),
                         {'dataset': books.DATASET, 'books': 381, 'bindings': 381, 'inserted': 381})
        before = self.db.total_changes
        self.assertEqual(books.import_catalog(self.db, self.client, records=self.records)['inserted'], 0)
        self.assertEqual(self.db.total_changes, before)
        self.assertEqual(self.stored(), expected_books)
        self.assertEqual(self.db.execute(f'SELECT {books.BINDING_COLUMNS} FROM native_skill_book_bindings '
                                         'ORDER BY book_dataset_id,skill_dataset_id,kind,definition_id,item_id').fetchall(),
                         expected_bindings)
        self.assertEqual(self.db.execute(f'SELECT {books.SOURCE_COLUMNS} FROM native_data_sources '
                                         'WHERE dataset_id=?', (books.DATASET,)).fetchall(), [books.SOURCE_ROW])
        self.assertEqual(self.db.execute('SELECT username FROM accounts').fetchall(), [('preserved',)])
        self.assertEqual(self.db.execute('SELECT count(*) FROM native_skill_catalog').fetchone(), (448,))
        for row in expected_books:
            _, _, _, offset, _, source_hash, raw, parsed_hash, parsed = row
            self.assertEqual(books.SOURCE_ROW[3], '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815')
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source_hash)
            self.assertEqual(hashlib.sha256(parsed).hexdigest(), parsed_hash)
            self.assertEqual(len(parsed), 396)
            self.assertGreaterEqual(offset, 0)
        self.assertEqual(self.db.execute('PRAGMA foreign_key_check').fetchall(), [])
        self.assertEqual(self.db.execute('PRAGMA quick_check').fetchall(), [('ok',)])

    def test_conflicts_never_overwrite_saved_or_source_rows(self):
        books.import_catalog(self.db, self.client, records=self.records)
        self.db.execute("UPDATE native_skill_books SET record_sha256=? WHERE source_record_index=0",
                        ('a' * 64,))
        self.db.commit()
        corrupted = self.stored()
        with self.assertRaisesRegex(ValueError, 'conflict'):
            books.import_catalog(self.db, self.client, records=self.records)
        self.assertEqual(self.stored(), corrupted)
        self.assertEqual(self.db.execute('SELECT username FROM accounts').fetchall(), [('preserved',)])
        self.assertFalse(self.db.in_transaction)

    def test_failed_insert_rolls_back_source_and_every_row(self):
        self.db.execute('CREATE TRIGGER reject_book BEFORE INSERT ON native_skill_books '
                        "WHEN NEW.source_record_index=190 BEGIN SELECT RAISE(ABORT,'test failure'); END")
        self.db.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            books.import_catalog(self.db, self.client, records=self.records)
        self.assertEqual(self.stored(), [])
        self.assertEqual(self.db.execute('SELECT * FROM native_data_sources WHERE dataset_id=?',
                                         (books.DATASET,)).fetchall(), [])
        self.assertEqual(self.db.execute('SELECT username FROM accounts').fetchall(), [('preserved',)])
        self.assertFalse(self.db.in_transaction)


if __name__ == '__main__':
    unittest.main()
