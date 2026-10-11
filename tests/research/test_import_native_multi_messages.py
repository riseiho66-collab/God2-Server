"""Pinned original MultiMessage import into isolated SQLite; no gameplay claims."""
from contextlib import closing
import hashlib
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import import_native_multi_messages as source
from tools.strike_lab.omega_assets import decode_csvz

CLIENT = ROOT.parent / 'God2'


class MultiMessageImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected = source.pinned_records(CLIENT)

    def test_full_current_source_provenance_and_cp950_bytes(self):
        sources, definitions, rows = self.expected
        self.assertEqual(len(sources), 3)
        self.assertEqual([row[0] for row in definitions], list(range(1, 2996)))
        self.assertEqual(sum(row[2] for row in definitions), 8799)
        self.assertEqual(len(rows), 11794)
        decoded = {name: decode_csvz((CLIENT / name).read_bytes()) for name, *_ in sources}
        owner = {key: (name, count) for key, name, count, _ in definitions}
        for key, ordinal, line, offset, digest, raw, text in rows:
            name, count = owner[key]
            self.assertLessEqual(ordinal, count)
            self.assertEqual(decoded[name].splitlines()[line-1], raw)
            self.assertEqual(decoded[name][offset:offset+len(raw)], raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            self.assertEqual(raw.split(b',', 2)[2], text)
            self.assertEqual(text.decode('cp950').encode('cp950'), text)
        # Native researched mode4 key1434: exact intro followed by seven options.
        group = [row for row in rows if row[0] == 1434]
        self.assertEqual([row[1] for row in group], list(range(8)))
        self.assertEqual([row[2] for row in group], list(range(1529, 1537)))

    def test_install_import_idempotence_and_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.sqlite'
            with closing(sqlite3.connect(path)) as db:
                source.install(db)
                source.install(db)
                result = source.import_catalog(db, CLIENT)
                self.assertEqual(result['inserted_keys'], 2995)
                self.assertEqual(result['authority'], 'SOURCE_DISPLAY_ONLY')
                self.assertEqual(result['gameplay_rules'], 0)
                before = tuple(db.iterdump())
                self.assertEqual(source.import_catalog(db, CLIENT)['inserted_keys'], 0)
                self.assertEqual(tuple(db.iterdump()), before)
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(source.import_catalog(db, CLIENT)['inserted_keys'], 0)
                self.assertEqual(tuple(db.iterdump()), before)

    def test_bad_last_source_creates_no_schema_or_partial_catalog(self):
        with tempfile.TemporaryDirectory() as directory, closing(sqlite3.connect(':memory:')) as db:
            client = Path(directory)
            target = client / 'Data2/Patch/Comm'
            target.mkdir(parents=True)
            for name in source.PINS:
                data = (CLIENT / 'Data2/Patch/Comm' / name).read_bytes()
                (target / name).write_bytes(data if '03' not in name else data[:-1] + bytes((data[-1] ^ 1,)))
            with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                source.import_catalog(db, client)
            self.assertEqual(db.execute('SELECT name FROM sqlite_master').fetchall(), [])
            self.assertFalse(db.in_transaction)

    def test_conflicting_partial_and_altered_source_refuse_overwrite(self):
        for mutation in (
            "DELETE FROM native_multi_message_rows WHERE message_key=1434 AND ordinal=7",
            "UPDATE native_multi_message_sources SET source_sha256=printf('%064d',0)",
            "UPDATE native_multi_message_rows SET text_bytes=X'41' WHERE message_key=1 AND ordinal=0",
        ):
            with self.subTest(mutation=mutation), closing(sqlite3.connect(':memory:')) as db:
                source.import_catalog(db, CLIENT)
                db.execute(mutation)
                db.commit()
                before = tuple(db.iterdump())
                with self.assertRaisesRegex(ValueError, 'Conflicting/partial'):
                    source.import_catalog(db, CLIENT)
                self.assertEqual(tuple(db.iterdump()), before)
                self.assertFalse(db.in_transaction)

    def test_failure_after_inserts_and_trigger_corruption_roll_back(self):
        for action in (
            "SELECT RAISE(ABORT,'fixture failed')",
            "UPDATE native_multi_message_rows SET text_bytes=X'41' WHERE message_key=NEW.message_key AND ordinal=NEW.ordinal",
        ):
            with self.subTest(action=action), closing(sqlite3.connect(':memory:')) as db:
                source.install(db)
                db.execute('CREATE TRIGGER fail_import AFTER INSERT ON native_multi_message_rows '
                           'WHEN NEW.message_key=1434 BEGIN ' + action + '; END')
                before = tuple(db.iterdump())
                with self.assertRaises((ValueError, sqlite3.DatabaseError)):
                    source.import_catalog(db, CLIENT)
                self.assertEqual(tuple(db.iterdump()), before)
                self.assertFalse(db.in_transaction)

    def test_foreign_transaction_and_schema_are_preserved(self):
        with closing(sqlite3.connect(':memory:')) as db:
            db.execute('CREATE TABLE unrelated(value)')
            db.execute('INSERT INTO unrelated VALUES(9)')
            for action in (lambda: source.install(db), lambda: source.import_catalog(db, CLIENT)):
                with self.assertRaisesRegex(ValueError, 'own transaction'):
                    action()
                self.assertTrue(db.in_transaction)
                self.assertEqual(db.execute('SELECT * FROM unrelated').fetchall(), [(9,)])
            db.rollback()
            db.execute('CREATE TABLE native_multi_message_sources(wrong TEXT)')
            before = tuple(db.iterdump())
            with self.assertRaisesRegex(ValueError, 'Conflicting MultiMessage schema'):
                source.import_catalog(db, CLIENT)
            self.assertEqual(tuple(db.iterdump()), before)

    def test_structural_parser_rejects_malformed_groups_without_pin_bypass(self):
        raw = b'MultiMessage,v2.00,test\r\nMultiMessage,1\r\n1,2,intro\r\n,1,one\r\n,2,two\r\n'
        groups, rows, _ = source._parse_rows('synthetic-parser-only', raw, 1, 1, 2)
        self.assertEqual(groups[0][2], 2)
        self.assertEqual([row[1] for row in rows], [0, 1, 2])
        for bad in (raw.replace(b',2,two', b',3,two'), raw.replace(b'1,2,intro', b'2,2,intro'),
                    raw.replace(b',1,one\r\n', b''), raw.replace(b'intro', b'\0'),
                    raw.replace(b',2,two', b',2,'), raw.replace(b'intro', b'\xff')):
            with self.assertRaises((ValueError, UnicodeError)):
                source._parse_rows('synthetic-parser-only', bad, 1, 1, 2)
        # Even structurally valid decoded data is rejected when decoded pin differs.
        with closing(sqlite3.connect(':memory:')) as db, patch.object(source, 'decode_csvz', return_value=raw):
            with self.assertRaisesRegex(ValueError, 'decoded identity mismatch'):
                source.import_catalog(db, CLIENT)
            self.assertEqual(db.execute('SELECT name FROM sqlite_master').fetchall(), [])


if __name__ == '__main__':
    unittest.main()
