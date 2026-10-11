"""CUSTOM-0058: reserve 0/122..125 and register 0/126 without enabling gameplay.

This explicit, backup-first operation never grants a skill or modifies the
native catalog. A registry row is not proof of client integration or casting.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid

ROOT = Path(__file__).resolve().parents[2]
BACKUPS = ROOT / "artifacts/custom-skills/shunying/db-backups"
COLUMNS = ("kind", "definition_id", "name", "status", "design_id", "origin",
           "base_kind", "base_definition_id", "max_targets")
LEGACY_ROW = (0, 123, "瞬影三煞斬", "pending_client_integration", "CUSTOM-0058",
              "CUSTOM_DESIGNED", 0, 8, 3)
ROWS = tuple((0, number, None, "reserved", "CUSTOM-0058", "CUSTOM_DESIGNED", None, None, None)
             for number in range(122, 126)) + (
    (0, 126, "瞬影三煞斬", "pending_client_integration", "CUSTOM-0058",
     "CUSTOM_DESIGNED", 0, 8, 3),
)
SCHEMA = """CREATE TABLE IF NOT EXISTS custom_skill_registry (
    kind INTEGER NOT NULL CHECK(kind BETWEEN 0 AND 3),
    definition_id INTEGER NOT NULL CHECK(definition_id BETWEEN 1 AND 255),
    name TEXT,
    status TEXT NOT NULL CHECK(status IN ('reserved','pending_client_integration')),
    design_id TEXT NOT NULL,
    origin TEXT NOT NULL CHECK(origin='CUSTOM_DESIGNED'),
    base_kind INTEGER,
    base_definition_id INTEGER,
    max_targets INTEGER,
    PRIMARY KEY(kind,definition_id),
    CHECK((status='reserved' AND name IS NULL AND base_kind IS NULL
           AND base_definition_id IS NULL AND max_targets IS NULL)
       OR (status='pending_client_integration' AND name IS NOT NULL
           AND base_kind BETWEEN 0 AND 3 AND base_definition_id BETWEEN 1 AND 255
           AND max_targets BETWEEN 1 AND 3))
)"""


def check_database(connection: sqlite3.Connection) -> None:
    if connection.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise ValueError("Database quick_check failed")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise ValueError("Database foreign_key_check failed")


def native_snapshot(connection: sqlite3.Connection) -> tuple:
    columns = tuple(row[1] for row in connection.execute("PRAGMA table_info(native_skill_catalog)"))
    if not {"kind", "definition_id"}.issubset(columns):
        raise ValueError("Native skill catalog is absent or incompatible")
    rows = connection.execute("SELECT * FROM native_skill_catalog ORDER BY kind,definition_id").fetchall()
    if len(rows) != 448:
        raise ValueError("Expected exactly 448 existing native skill records")
    if connection.execute("SELECT max(definition_id) FROM native_skill_catalog WHERE kind=0").fetchone() != (121,):
        raise ValueError("Native kind0 tail must be 121; refusing identity collision")
    if connection.execute("SELECT count(*) FROM native_skill_catalog WHERE kind=0 AND definition_id=8").fetchone() != (1,):
        raise ValueError("Native blade3 base 0/8 must exist exactly once")
    return columns, rows


def snapshot_digest(snapshot: tuple) -> str:
    raw = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"),
                     default=lambda value: {"blob_hex": value.hex()}).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def register(database: Path, *, backup_directory: Path = BACKUPS) -> dict:
    database = Path(database).resolve(strict=True)
    if not database.is_file():
        raise ValueError("An existing SQLite database file is required")
    backup_directory = Path(backup_directory).resolve()
    backup_directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = backup_directory / f"{database.stem}-before-shunying-{stamp}-{uuid.uuid4().hex}.sqlite"
    # Exclusive creation prevents replacing any earlier release evidence.
    with backup.open("xb"):
        pass
    with closing(sqlite3.connect(database.as_uri() + "?mode=rw", uri=True, timeout=30)) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        with closing(sqlite3.connect(backup)) as saved:
            connection.backup(saved)
            check_database(saved)
            baseline = native_snapshot(saved)
        connection.execute("BEGIN IMMEDIATE")
        try:
            check_database(connection)
            if native_snapshot(connection) != baseline:
                raise ValueError("Native catalog changed after backup; refusing registration")
            connection.execute(SCHEMA)
            info = connection.execute("PRAGMA table_info(custom_skill_registry)").fetchall()
            if tuple(row[1] for row in info) != COLUMNS or [(row[1], row[5]) for row in info if row[5]] != [("kind", 1), ("definition_id", 2)]:
                raise ValueError("Existing custom registry schema is incompatible")
            inserted = 0
            migrated = False
            legacy = connection.execute("SELECT * FROM custom_skill_registry WHERE kind=0 AND definition_id=123").fetchone()
            if legacy == LEGACY_ROW:
                # Explicit owner-requested renumbering of this exact pending row only.
                connection.execute("UPDATE custom_skill_registry SET name=NULL,status='reserved',base_kind=NULL,base_definition_id=NULL,max_targets=NULL WHERE kind=0 AND definition_id=123")
                migrated = True
            for expected in ROWS:
                existing = connection.execute(
                    "SELECT * FROM custom_skill_registry WHERE kind=? AND definition_id=?",
                    expected[:2]).fetchall()
                if existing and existing != [expected]:
                    raise ValueError(f"Custom skill identity collision at {expected[0]}/{expected[1]}")
                if not existing:
                    connection.execute("INSERT INTO custom_skill_registry VALUES(?,?,?,?,?,?,?,?,?)", expected)
                    inserted += 1
            actual = connection.execute(
                "SELECT * FROM custom_skill_registry WHERE kind=0 AND definition_id BETWEEN 122 AND 126 ORDER BY definition_id").fetchall()
            if actual != list(ROWS):
                raise ValueError("Custom registry readback mismatch")
            if native_snapshot(connection) != baseline:
                raise ValueError("Native catalog changed during registration")
            check_database(connection)
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
    return {"database": str(database), "backup": str(backup), "inserted": inserted, "migrated_from_123": migrated,
            "native_records_unchanged": 448, "native_snapshot_sha256": snapshot_digest(baseline),
            "entries": [dict(zip(COLUMNS, row)) for row in ROWS],
            "activation": "Registry only: no character grant, client integration or cast acceptance"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True,
                        help="Explicit existing server SQLite database; no implicit production path")
    args = parser.parse_args()
    print(json.dumps(register(args.database), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
