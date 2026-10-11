"""CUSTOM-0058 registry tests use disposable synthetic databases only."""
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from tools.skills.register_shunying_skill import ROWS, LEGACY_ROW, SCHEMA, native_snapshot, register


class RegisterShunyingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / "test.sqlite"
        self.backups = self.root / "backups"
        with closing(sqlite3.connect(self.db)) as connection:
            connection.execute("CREATE TABLE native_skill_catalog(kind INTEGER, definition_id INTEGER, raw_record BLOB, PRIMARY KEY(kind,definition_id))")
            connection.executemany("INSERT INTO native_skill_catalog VALUES(?,?,?)", (
                (kind, identity, bytes((kind, identity)))
                for kind, count in enumerate((121, 129, 87, 111))
                for identity in range(1, count + 1)))
            connection.commit()
            self.baseline = native_snapshot(connection)

    def run_registration(self):
        return register(self.db, backup_directory=self.backups)

    def test_registers_reserved_four_pending126_and_is_exactly_idempotent(self):
        first = self.run_registration()
        second = self.run_registration()
        self.assertEqual((first["inserted"], second["inserted"]), (5, 0))
        self.assertNotEqual(first["backup"], second["backup"])
        with closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual(connection.execute("SELECT * FROM custom_skill_registry ORDER BY definition_id").fetchall(), list(ROWS))
            self.assertEqual(native_snapshot(connection), self.baseline)
        with closing(sqlite3.connect(first["backup"])) as saved:
            self.assertEqual(native_snapshot(saved), self.baseline)
            self.assertIsNone(saved.execute("SELECT name FROM sqlite_master WHERE name='custom_skill_registry'").fetchone())

    def test_conflicting126_rolls_back_reservations_without_overwrite(self):
        conflicting = list(ROWS[-1]); conflicting[2] = "Existing different skill"
        with closing(sqlite3.connect(self.db)) as connection:
            connection.execute(SCHEMA)
            connection.execute("INSERT INTO custom_skill_registry VALUES(?,?,?,?,?,?,?,?,?)", conflicting)
            connection.commit()
        with self.assertRaisesRegex(ValueError, "collision"):
            self.run_registration()
        with closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual(connection.execute("SELECT * FROM custom_skill_registry").fetchall(), [tuple(conflicting)])
            self.assertEqual(native_snapshot(connection), self.baseline)
        self.assertEqual(len(list(self.backups.glob("*.sqlite"))), 1)

    def test_migrates_exact_previous_pending_skill(self):
        with closing(sqlite3.connect(self.db)) as connection:
            connection.execute(SCHEMA)
            connection.executemany("INSERT INTO custom_skill_registry VALUES(?,?,?,?,?,?,?,?,?)", [ROWS[0], LEGACY_ROW])
            connection.commit()
        result = self.run_registration()
        self.assertTrue(result["migrated_from_123"])
        with closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual(connection.execute("SELECT * FROM custom_skill_registry ORDER BY definition_id").fetchall(), list(ROWS))

    def test_native_collision_refuses_before_registry_creation(self):
        with closing(sqlite3.connect(self.db)) as connection:
            connection.execute("UPDATE native_skill_catalog SET definition_id=123 WHERE kind=0 AND definition_id=121")
            connection.commit()
        with self.assertRaisesRegex(ValueError, "tail"):
            self.run_registration()
        with closing(sqlite3.connect(self.db)) as connection:
            self.assertIsNone(connection.execute("SELECT name FROM sqlite_master WHERE name='custom_skill_registry'").fetchone())


if __name__ == "__main__":
    unittest.main()
