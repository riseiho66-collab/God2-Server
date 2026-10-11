"""Migrate a read-only backup of the configured save, never the live database.

This review deliberately runs only --migrate-only, with the clone's own config
and logging path. Row fingerprints never print player data or credentials.
"""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'artifacts/releases/town-chat-welcome-20260924/server-config.json'
BINARY = Path(os.environ.get('GOD2_PACKET_LINKS_REVIEW_BINARY',
    ROOT / 'build-town-visibility/Release/god2-server-native-results.exe'))


def quoted(identifier):
    return '"' + identifier.replace('"', '""') + '"'


def fingerprint(db, table):
    digests = []
    for row in db.execute('SELECT * FROM ' + quoted(table)):
        digest = hashlib.sha256()
        for value in row:
            if value is None:
                data = b'N'
            elif isinstance(value, bytes):
                data = b'B' + value
            elif isinstance(value, str):
                data = b'T' + value.encode('utf-8')
            elif isinstance(value, int):
                data = b'I' + str(value).encode('ascii')
            else:
                data = b'F' + repr(value).encode('ascii')
            digest.update(len(data).to_bytes(8, 'little'))
            digest.update(data)
        digests.append(digest.digest())
    return len(digests), hashlib.sha256(b''.join(sorted(digests))).hexdigest()


class PacketLinksMigrationReviewTests(unittest.TestCase):
    def test_configured_save_readonly_backup_migrates_38_to_39_without_old_row_changes(self):
        self.assertTrue(BINARY.is_file(), 'Candidate required')
        config = json.loads(CONFIG.read_text('utf-8'))
        source_path = Path(config['database']['path'])
        if not source_path.is_absolute():
            source_path = ROOT / source_path
        self.assertTrue(source_path.is_file(), 'Configured source save required')
        with tempfile.TemporaryDirectory(prefix='god2-packet-migration-review-') as temporary:
            here = Path(temporary)
            clone = here / 'town-diagnostic-accounts.db'
            self.assertNotEqual(clone.resolve(), source_path.resolve())
            # Opening mode=ro and query_only prevents a misplaced migration or
            # fixture write even if this code changes in a later review.
            with closing(sqlite3.connect(source_path.resolve().as_uri() + '?mode=ro', uri=True)) as source:
                source.execute('PRAGMA query_only=ON')
                self.assertEqual(source.execute('PRAGMA query_only').fetchone(), (1,))
                with closing(sqlite3.connect(clone)) as copied:
                    source.backup(copied)
            with closing(sqlite3.connect(clone)) as before:
                history = before.execute('SELECT * FROM schema_migrations ORDER BY version').fetchall()
                self.assertEqual(history[-1][0], 38, 'This review expects the current pre39 configured save')
                schema = before.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name").fetchall()
                tables = [r[0] for r in before.execute("SELECT name FROM sqlite_master WHERE type='table' AND name!='schema_migrations' ORDER BY name")]
                original = {table: fingerprint(before, table) for table in tables}
            config['database']['path'] = str(clone)
            config['logging']['file'] = str(here / 'migration.log')
            cfg = here / 'config.json'
            cfg.write_text(json.dumps(config), encoding='utf-8')
            for attempt in range(2):
                result = subprocess.run([str(BINARY), '--config', str(cfg), '--migrate-only'],
                    cwd=ROOT, capture_output=True, text=True, timeout=60,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                with closing(sqlite3.connect(clone)) as after:
                    migrated = after.execute('SELECT * FROM schema_migrations ORDER BY version').fetchall()
                    self.assertEqual(migrated[:-1], history)
                    self.assertEqual(migrated[-1][:2], (39, 'owned_secondary_role_text'))
                    self.assertEqual({table: fingerprint(after, table) for table in tables}, original)
                    migrated_schema = after.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name!='character_role_text' ORDER BY type,name").fetchall()
                    self.assertEqual(migrated_schema, schema, 'Existing schema was rewritten')
                    self.assertEqual(after.execute('SELECT count(*) FROM character_role_text').fetchone(), (0,))
                    self.assertEqual(after.execute('PRAGMA quick_check').fetchone(), ('ok',))
                    self.assertEqual(after.execute('PRAGMA foreign_key_check').fetchall(), [])
                    if attempt == 0:
                        after_history = migrated
                    else:
                        self.assertEqual(migrated, after_history, 'Second migration rewrote history')
            # The live source can change through its running server, so do not
            # treat whole-file hashes as a concurrency-safe mutation detector.
            # Its schema version is checked read-only; this test never migrates it.
            with closing(sqlite3.connect(source_path.resolve().as_uri() + '?mode=ro', uri=True)) as source:
                self.assertEqual(source.execute('SELECT max(version) FROM schema_migrations').fetchone(), (38,))
            print('Migration review PASS:', len(tables), 'existing tables unchanged; versions1..38 unchanged;'
                  ' empty39 table; second migration idempotent; candidate SHA256',
                  hashlib.sha256(BINARY.read_bytes()).hexdigest(), flush=True)


if __name__ == '__main__':
    unittest.main()
