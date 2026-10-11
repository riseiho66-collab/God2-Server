"""Release safety tests: temporary databases/files and mocked service lifecycle.

Never invoke a scheduled task, touch the configured live save, or run apply
against a real release. The tests intentionally exercise the inverse migration.
"""
from contextlib import closing
import copy
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from tools.operations import packet_links_release_20260930 as release


ROLE_SQL = '''CREATE TABLE character_role_text (
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) ON DELETE CASCADE,
 legacy_text BLOB NOT NULL, utf8_text TEXT NOT NULL, codepage INTEGER NOT NULL,
 revision INTEGER NOT NULL, origin TEXT NOT NULL, source_sha256 TEXT NOT NULL, design_id TEXT NOT NULL
)'''


def make38(path):
    with closing(sqlite3.connect(path)) as db:
        db.execute('CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY,name TEXT NOT NULL,sql_text TEXT NOT NULL,applied_at TEXT NOT NULL)')
        db.executemany('INSERT INTO schema_migrations VALUES(?,?,?,?)',
                       [(n, 'migration' + str(n), 'sql' + str(n), 'old-time') for n in range(1, 39)])
        db.execute('CREATE TABLE recovered_characters(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,revision INTEGER NOT NULL)')
        db.execute("INSERT INTO recovered_characters VALUES(1,'saved role',7)")
        for index in range(51):
            db.execute('CREATE TABLE table_' + str(index) + '(id INTEGER PRIMARY KEY,value BLOB)')
            db.execute('INSERT INTO table_' + str(index) + ' VALUES(1,?)', (bytes([index]),))
        db.commit()


def add39(path):
    with closing(sqlite3.connect(path)) as db:
        db.execute(ROLE_SQL)
        db.execute('INSERT INTO schema_migrations VALUES(39,?,?,?)', ('owned_secondary_role_text', ROLE_SQL, 'new-time'))
        db.commit()


class PacketLinksReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='packet-links-release-test-')
        self.addCleanup(self.temporary.cleanup)
        self.here = Path(self.temporary.name)
        self.db = self.here / 'town-diagnostic-accounts.db'
        make38(self.db)
        self.before = release.capture(self.db)
        release.require38(self.before)
        add39(self.db)
        self.after = release.capture(self.db)
        self.artifacts = self.here / 'release'
        self.artifacts.mkdir()

    def execute(self, sql):
        with closing(sqlite3.connect(self.db)) as db:
            db.execute(sql)
            db.commit()

    def test_exact_53_table_migration_and_safe_inverse_preserve_all_rows(self):
        release.require39(self.before, self.after, self.after)
        self.assertEqual(len(self.before['tables']) - 1, 53)
        result = release.undo_empty_migration(self.db, self.before, self.after)
        self.assertEqual(result, {'schema': 38, 'migration39_removed': True})
        self.assertEqual(release.capture(self.db), self.before)
        self.assertEqual(release.undo_empty_migration(self.db, self.before, self.after),
                         {'schema': 38, 'migration39_removed': False})

    def test_refuses_every_old_table_change_and_never_overwrites(self):
        for table in ('recovered_characters', 'table_0', 'table_50', 'sqlite_sequence'):
            with self.subTest(table=table):
                clone = self.here / (table + '.db')
                release.managed.backup(self.db, clone)
                with closing(sqlite3.connect(clone)) as db:
                    column = 'revision' if table == 'recovered_characters' else ('seq' if table == 'sqlite_sequence' else 'id')
                    db.execute('UPDATE ' + release.quoted(table) + ' SET ' + column + '=' + column + '+1')
                    db.commit()
                changed = release.capture(clone)
                with self.assertRaises(release.RollbackUnsafe):
                    release.undo_empty_migration(clone, self.before, self.after)
                self.assertEqual(release.capture(clone), changed)

    def test_nonempty_role_row_including_empty_text_blocks_inverse(self):
        self.execute("INSERT INTO character_role_text VALUES(1,zeroblob(16),'',950,1,'CUSTOM_DESIGNED','sha','CUSTOM-0056')")
        changed = release.capture(self.db)
        with self.assertRaisesRegex(release.RollbackUnsafe, 'not empty'):
            release.undo_empty_migration(self.db, self.before, self.after)
        self.assertEqual(release.capture(self.db), changed)

    def test_schema_old_history_and_new_sql_drift_block_inverse(self):
        for sql in ("CREATE INDEX extra ON recovered_characters(name)",
                    "UPDATE schema_migrations SET applied_at='rewritten' WHERE version=1",
                    "UPDATE schema_migrations SET sql_text='changed' WHERE version=39",
                    "PRAGMA user_version=123", "CREATE TABLE surprise(id INTEGER)"):
            with self.subTest(sql=sql):
                clone = self.here / ('drift' + str(abs(hash(sql))) + '.db')
                release.managed.backup(self.db, clone)
                with closing(sqlite3.connect(clone)) as db:
                    db.execute(sql)
                    db.commit()
                changed = release.capture(clone)
                with self.assertRaises(release.RollbackUnsafe):
                    release.undo_empty_migration(clone, self.before, self.after)
                self.assertEqual(release.capture(clone), changed)

    def test_inverse_drop_and_delete_are_one_transaction(self):
        # Trigger is part of this baseline, so it is not rejected as schema drift.
        release.undo_empty_migration(self.db, self.before, self.after)
        self.execute("CREATE TRIGGER deny_history BEFORE DELETE ON schema_migrations BEGIN SELECT RAISE(ABORT,'blocked'); END")
        baseline = release.capture(self.db)
        add39(self.db)
        migrated = release.capture(self.db)
        with self.assertRaisesRegex(release.RollbackUnsafe, 'blocked'):
            release.undo_empty_migration(self.db, baseline, migrated)
        self.assertEqual(release.capture(self.db), migrated)
        self.assertIn('character_role_text', release.capture(self.db)['tables'])

    def test_changed_save_is_valid_runtime_state_but_not_rollback_eligible(self):
        self.execute('UPDATE recovered_characters SET revision=8 WHERE id=1')
        current = release.capture(self.db)
        release.require39(self.before, current, self.after, unchanged=False, empty=False)
        self.assertEqual(release.changed_old_tables(self.before, current), ['recovered_characters'])
        with self.assertRaises(ValueError):
            release.require39(self.before, current, self.after)

    def test_backup_destination_must_be_new_release_artifact(self):
        with self.assertRaises(ValueError):
            release.backup_new(self.db, self.db, self.artifacts)
        with self.assertRaises(ValueError):
            release.backup_new(self.db, self.here / 'outside.db', self.artifacts)
        clone = self.artifacts / 'snapshot.db'
        release.backup_new(self.db, clone, self.artifacts)
        self.assertEqual(release.capture(clone), self.after)
        with self.assertRaises(ValueError):
            release.backup_new(self.db, clone, self.artifacts)

    def test_file_install_hash_gate_and_atomic_copy(self):
        active, candidate = self.here / 'active.exe', self.here / 'candidate.exe'
        active.write_bytes(b'old')
        candidate.write_bytes(b'new')
        with patch.object(release.managed, 'ACTIVE', active):
            with self.assertRaises(ValueError):
                release.install_binary(candidate, 'wrong hash')
            self.assertEqual(active.read_bytes(), b'old')
            release.install_binary(candidate, release.managed.sha(candidate))
        self.assertEqual(active.read_bytes(), b'new')
        self.assertEqual(list(self.here.glob('packet-links-*.exe')), [])

    def qualify_apply_context(self):
        active = self.here / 'active.exe'
        active.write_bytes(b'old')
        candidate = self.here / 'candidate.exe'
        candidate.write_bytes(b'candidate')
        info = {'candidate_sha256': release.managed.sha(candidate), 'old_server_sha256': release.managed.sha(active), 'freeze': 'ok'}
        for name, value in (('load_manifest', (info, self.db, self.after)), ('freeze_gate', 'ok'),
                            ('qualify_hidden', {}), ('qualify_tcp', {})):
            mock = patch.object(release, name, return_value=value)
            mock.start()
            self.addCleanup(mock.stop)
        for owner, name, value in ((release, 'CANDIDATE', candidate), (release.managed, 'ACTIVE', active)):
            mock = patch.object(owner, name, value)
            mock.start()
            self.addCleanup(mock.stop)
        return info

    def test_apply_active_player_refusal_precedes_stop_backup_and_install(self):
        self.qualify_apply_context()
        with patch.object(release, 'managed_listener', side_effect=ValueError('Player active')), \
             patch.object(release, 'stop_idle') as stop, patch.object(release, 'backup_new') as backup, \
             patch.object(release, 'install_binary') as install:
            with self.assertRaisesRegex(ValueError, 'Player active'):
                release.apply(self.artifacts)
            stop.assert_not_called()
            backup.assert_not_called()
            install.assert_not_called()

    def test_partial_stop_failure_enters_availability_recovery_without_install(self):
        self.qualify_apply_context()
        with patch.object(release, 'managed_listener', return_value=123), \
             patch.object(release, 'stop_idle', side_effect=RuntimeError('stopped then failed')), \
             patch.object(release, 'restore_original_availability') as recover, \
             patch.object(release, 'install_binary') as install:
            with self.assertRaisesRegex(RuntimeError, 'stopped then failed'):
                release.apply(self.artifacts)
            recover.assert_called_once()
            install.assert_not_called()

    def test_commandline_requires_exact_image_and_config_no_extra_args(self):
        image, config = str(release.managed.ACTIVE.resolve()), str(release.managed.CONFIG.resolve())
        valid = '"' + image + '" --config "' + config + '" '
        release.require_commandline(valid)
        for command in (valid + '--migrate-only', valid.replace(config, config + '.other'),
                        valid.replace('--config', '--help'), valid[:-2], 'other.exe --config "' + config + '"'):
            with self.subTest(command=command), self.assertRaises(ValueError):
                release.require_commandline(command)

    def test_partial_stop_restarts_only_when_original_process_is_absent(self):
        active, info = self.recovery_context()
        active.write_bytes(b'old')
        with patch.object(release, 'managed_listener', side_effect=ValueError('No listener')), \
             patch.object(release.managed, 'powershell'), patch.object(release.managed, 'start') as start, \
             patch.object(release, 'wait_listener', return_value=123):
            release.restore_original_availability(self.artifacts, info, RuntimeError('partial stop'))
            start.assert_called_once()
        self.assertTrue(release.read(self.artifacts / 'stop-recovery.json')['original_available'])

    def recovery_context(self):
        active, old, config = self.here / 'active.exe', self.artifacts / 'god2-server.before.exe', self.here / 'config.json'
        active.write_bytes(b'candidate')
        old.write_bytes(b'old')
        config.write_bytes(b'config unchanged')
        info = {'candidate_sha256': release.managed.sha(active), 'old_server_sha256': release.managed.sha(old),
                'config_sha256': release.managed.sha(config)}
        for name, value in (('ACTIVE', active), ('CONFIG', config)):
            mock = patch.object(release.managed, name, value)
            mock.start()
            self.addCleanup(mock.stop)
        return active, info

    def test_failed_start_can_restore_old_code_only_after_safe_inverse(self):
        active, info = self.recovery_context()
        with patch.object(release, 'stop_for_recovery') as stop, \
             patch.object(release.managed, 'start') as start, patch.object(release, 'wait_listener', return_value=123):
            release.recover(self.artifacts, info, self.db, self.before, self.after, RuntimeError('startup failed'))
            stop.assert_called_once()
            start.assert_called_once()
        self.assertEqual(active.read_bytes(), b'old')
        self.assertEqual(release.capture(self.db), self.before)
        self.assertTrue(release.read(self.artifacts / 'rollback.json')['migration39_removed'])

    def test_new_save_keeps_candidate_and_no_old_service_start(self):
        active, info = self.recovery_context()
        self.execute('UPDATE recovered_characters SET revision=8 WHERE id=1')
        current = release.capture(self.db)
        with patch.object(release, 'stop_for_recovery'), patch.object(release.managed, 'start') as start:
            with self.assertRaises(release.RollbackUnsafe):
                release.recover(self.artifacts, info, self.db, self.before, self.after, RuntimeError('post-start error'))
            start.assert_not_called()
        self.assertEqual(active.read_bytes(), b'candidate')
        self.assertEqual(release.capture(self.db), current)
        self.assertTrue(release.read(self.artifacts / 'rollback.json')['manual_repair_required'])

    def test_connected_player_on_recovery_keeps_candidate_and_save(self):
        active, info = self.recovery_context()
        with patch.object(release, 'stop_for_recovery', side_effect=ValueError('Player active')), \
             patch.object(release, 'undo_empty_migration') as inverse, patch.object(release.managed, 'start') as start:
            with self.assertRaisesRegex(release.RollbackUnsafe, 'Player active'):
                release.recover(self.artifacts, info, self.db, self.before, self.after, RuntimeError('verification error'))
            inverse.assert_not_called()
            start.assert_not_called()
        self.assertEqual(active.read_bytes(), b'candidate')
        self.assertEqual(release.capture(self.db), self.after)

    def test_guard_script_checks_connections_and_path_before_stopping(self):
        with patch.object(release.managed, 'powershell') as run:
            release.stop_idle(123)
        script = run.call_args.args[0]
        self.assertLess(script.index('Player active'), script.index('Stop-ScheduledTask'))
        self.assertLess(script.index('Managed PID identity changed'), script.index('Stop-ScheduledTask'))
        self.assertIn('SynReceived', script)
        self.assertIn('Unmanaged listener', script)


class PacketLinksEvidenceTests(unittest.TestCase):
    def test_final_hidden_receipt_accepts_exact_candidate_and_rejects_modified_flags(self):
        path = release.ROOT / 'artifacts/playtests/private-pet-reserve-20260930-03/run-result.json'
        if not path.exists():
            self.skipTest('Final local acceptance artifact not installed')
        actual = release.read(path)
        release.qualify_hidden(path, actual['candidate_sha256'])
        with self.assertRaises(ValueError):
            release.qualify_hidden(path, 'wrong candidate')
        for area, key in ((None, 'accepted'), (None, 'source_files_unchanged'), (None, 'all_owned_processes_closed'),
                          ('ui', 'desktop_unchanged'), ('ui', 'all_clients_closed')):
            bad = copy.deepcopy(actual)
            (bad[area] if area else bad)[key] = False
            with self.subTest(key=key), patch.object(release, 'read', return_value=bad):
                with self.assertRaises(ValueError):
                    release.qualify_hidden(path, actual['candidate_sha256'])

    def test_final_tcp_receipt_requires_module_identities_and_all_eight_cases(self):
        folder = release.ROOT / 'artifacts/research/role-text-20260930'
        path, log = folder / 'tcp-optimized-result.json', folder / 'tcp-optimized-run.log'
        if not path.exists():
            self.skipTest('Final local TCP evidence not installed')
        actual = release.read(path)
        release.qualify_tcp(path, log, actual['candidate_sha256'])
        for key, value in (('passed', False), ('tests_run', 7), ('errors', 1), ('candidate_sha256', 'other')):
            bad = copy.deepcopy(actual)
            bad[key] = value
            with self.subTest(key=key), patch.object(release, 'read', return_value=bad):
                with self.assertRaises(ValueError):
                    release.qualify_tcp(path, log, actual['candidate_sha256'])
        bad = copy.deepcopy(actual)
        bad['modules'][0]['sha256'] = 'wrong hash'
        with patch.object(release, 'read', return_value=bad):
            with self.assertRaisesRegex(ValueError, 'source changed'):
                release.qualify_tcp(path, log, actual['candidate_sha256'])


if __name__ == '__main__':
    unittest.main()
