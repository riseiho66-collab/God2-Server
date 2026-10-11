"""Bounded tempclone tests; no formal writes/server/UI/port or old-helper edits."""
from contextlib import closing
from copy import deepcopy
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.strike_lab import guild_formal_catalog_fixture_20261004 as helper

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / 'artifacts/research/native-guild-membership-0078/formal-catalog-fixture-v01'
PINS = json.loads((ARTIFACT / 'manifest.json').read_text('utf-8'))
SNAPSHOT = ARTIFACT / 'source-snapshot.db'


def capture(path):
    with closing(sqlite3.connect(Path(path).as_uri() + '?mode=ro', uri=True)) as db:
        db.execute('BEGIN')
        return {'guard': helper.guard(db), 'catalog': helper.catalog(db)}


class CatalogFixtureRiskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='guild-catalog-tests-')
        self.addCleanup(self.temp.cleanup)
        self.private = Path(self.temp.name) / 'private-native-blackbox-catalog-unit'
        self.private.mkdir()
        self.target = self.private / 'fixture.db'
        shutil.copyfile(SNAPSHOT, self.target)
        with closing(sqlite3.connect(self.target)) as db:
            db.executescript(PINS['migration49_sql'])
            db.execute('INSERT INTO schema_migrations(version,name,sql_text,applied_at) VALUES(49,?,?,?)',
                       (helper.MIGRATION49, PINS['migration49_sql'], 'TEST_ONLY_TIME'))
            # Mimic existing weapon + quest-description fixture. No saved row
            # is deleted; original snapshot player/account/unknown cells remain.
            keep = {'native_weapon_sources', 'native_weapon_rows', 'native_quest_descriptions'}
            for table in reversed(PINS['copy_order']):
                if table in keep:
                    continue
                if table == 'native_data_sources':
                    db.execute("DELETE FROM native_data_sources WHERE dataset_id<>'current-quest-descriptions-v1'")
                else:
                    db.execute('DELETE FROM ' + helper.quote(table))
            db.executescript('''
CREATE TABLE unknown_fixture_save(id INTEGER PRIMARY KEY,cell,extra BLOB);
INSERT INTO unknown_fixture_save VALUES(1,17,X'0001');
INSERT INTO unknown_fixture_save VALUES(2,'17',NULL);
INSERT INTO unknown_fixture_save VALUES(3,17.5,X'');
INSERT INTO unknown_fixture_save VALUES(4,NULL,X'FF');
''')
            db.commit()
        self.before = capture(self.target)

    def run_copy(self, pins=PINS):
        return helper.prepare_catalogs(SNAPSHOT, self.target, pins)

    def test_full27_catalog_overlay_preserves_existing_weapon_quest_and_all_other_saved_cells(self):
        result = self.run_copy()
        after = capture(self.target)
        self.assertTrue(result['accepted'])
        self.assertEqual(after['guard'], self.before['guard'])
        self.assertEqual(after['catalog'], PINS['catalogs'])
        self.assertEqual(result['inserted_rows']['native_weapon_rows'], 0)
        self.assertEqual(result['inserted_rows']['native_quest_descriptions'], 0)
        self.assertEqual(result['inserted_rows']['native_data_sources'], 5)
        self.assertEqual(sum(result['inserted_rows'].values()),36445-1259-2-2014-1)

    def test_repeated_overlay_is_exact_idempotent_and_never_replaces_existing_rows(self):
        self.run_copy()
        before = capture(self.target)
        result = self.run_copy()
        self.assertEqual(sum(result['inserted_rows'].values()),0)
        self.assertEqual(capture(self.target),before)

    def test_midtransaction_failure_rolls_back_every_prior_catalog_insert(self):
        original = helper._insert_missing
        visited = []
        def failure(db,table,rows):
            visited.append(table)
            original(db,table,rows)
            if len(visited)==4:
                raise sqlite3.OperationalError('TEST_ONLY failure after real inserts')
        with patch.object(helper, '_insert_missing', side_effect=failure):
            with self.assertRaisesRegex(sqlite3.OperationalError, 'after real inserts'):
                self.run_copy()
        self.assertEqual(len(visited),4)
        self.assertEqual(capture(self.target),self.before)

    def test_existing_primary_key_content_collision_rejected_without_any_data_change(self):
        with closing(sqlite3.connect(self.target)) as db:
            db.execute("UPDATE native_data_sources SET source_path='different-path' WHERE dataset_id='current-quest-descriptions-v1'")
            db.commit()
        changed = capture(self.target)
        with self.assertRaisesRegex(ValueError, 'collision or extra row'):
            self.run_copy()
        self.assertEqual(capture(self.target),changed)

    def test_extra_target_catalog_index_is_rejected_before_insert(self):
        with closing(sqlite3.connect(self.target)) as db:
            db.execute('CREATE INDEX unknown_catalog_index ON native_armor_sources(family)')
            db.commit()
        changed = capture(self.target)
        with self.assertRaisesRegex(ValueError, 'schema differs'):
            self.run_copy()
        self.assertEqual(capture(self.target),changed)

    def test_source_row_digest_mismatch_cannot_be_ignored(self):
        pins = deepcopy(PINS)
        pins['catalogs']['native_skill_catalog']['fingerprint']['typed_sha256']='0'*64
        with self.assertRaisesRegex(ValueError, 'count/digest differs'):
            self.run_copy(pins)
        self.assertEqual(capture(self.target),self.before)

    def test_source_file_sha_mismatch_rejected_before_target_transaction(self):
        pins = deepcopy(PINS)
        pins['source_snapshot_sha256']='0'*64
        with self.assertRaisesRegex(ValueError, 'snapshot file hash differs'):
            self.run_copy(pins)
        self.assertEqual(capture(self.target),self.before)

    def test_manifest_cannot_widen_scope_to_player_accounts(self):
        pins = deepcopy(PINS)
        pins['tables'].append('accounts')
        with self.assertRaisesRegex(ValueError, 'scope differs'):
            self.run_copy(pins)
        self.assertEqual(capture(self.target),self.before)

    def test_schema48_or_unknown49_identity_rejected(self):
        with closing(sqlite3.connect(self.target)) as db:
            db.execute("UPDATE schema_migrations SET name='wrong49' WHERE version=49")
            db.commit()
        changed = capture(self.target)
        with self.assertRaisesRegex(ValueError, 'identity/SQL differs'):
            self.run_copy()
        self.assertEqual(capture(self.target),changed)
        with closing(sqlite3.connect(self.target)) as db:
            db.execute('DELETE FROM schema_migrations WHERE version=49')
            db.commit()
        changed48=capture(self.target)
        with self.assertRaisesRegex(ValueError, 'exact schema49 history'):
            self.run_copy()
        self.assertEqual(capture(self.target),changed48)

    def test_matching_history_cannot_hide_modified_actual_schema49(self):
        with closing(sqlite3.connect(self.target)) as db:
            db.execute('DROP INDEX owned_guild_pending_audience_0078')
            db.commit()
        changed=capture(self.target)
        with self.assertRaisesRegex(ValueError, 'actual table/index DDL differs'):
            self.run_copy()
        self.assertEqual(capture(self.target),changed)

    def test_nonprivate_path_is_rejected_and_source_snapshot_is_unchanged(self):
        outside=Path(self.temp.name)/'looks-formal.db'
        shutil.copyfile(self.target,outside)
        source_before=helper.sha(SNAPSHOT)
        with self.assertRaisesRegex(ValueError, 'private-native-blackbox'):
            helper.prepare_catalogs(SNAPSHOT,outside,PINS)
        self.assertEqual(helper.sha(SNAPSHOT),source_before)
        self.assertEqual(capture(outside),self.before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
