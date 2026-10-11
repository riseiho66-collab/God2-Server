"""Release gates only: private in-memory SQLite, no processes or formal saves."""
from copy import deepcopy
import sqlite3
import unittest
from tools.operations import owned_guild_announcement_release_v01_20261004 as release


class AnnouncementReleaseGates(unittest.TestCase):
    def test_disabled_preserves_every_other_config_field(self):
        cfg = {'world': {'owned_guild_membership': {'enabled': True,
            'entry_resource_bundle': release.base.BUNDLE}, 'future': {'bytes': [0, 1]}},
            'development': {'recovered_account_auth': True}, 'database': {'path': 'untouched'}}
        before = deepcopy(cfg)
        enabled = release.announcement_config(cfg, True)
        disabled = release.announcement_config(enabled, False)
        self.assertEqual(cfg, before)
        self.assertEqual(disabled['database'], cfg['database'])
        self.assertEqual(disabled['development'], cfg['development'])
        self.assertFalse(disabled['world']['owned_guild_announcements']['enabled'])
        disabled['world'].pop('owned_guild_announcements')
        self.assertEqual(disabled, before)
        cfg['world']['owned_guild_membership']['enabled'] = False
        with self.assertRaises(ValueError):
            release.announcement_config(cfg, True)

    def test_real_changed_draft_and_restored_cache_are_mandatory(self):
        text = b'PersistedNotice'
        proof = {'accepted': True, 'sql_exact': True, 'cache_restored': True,
            'native79_via_control28': True, 'no_explicit_help_reopen': True,
            'denied_log': {'fields': {'committed': 'false'}},
            'restored_log': {'fields': {'revision': '1', 'published': 'true'}},
            'cache': {'text_hex': text.hex(), 'logical_size': len(text) + 4,
                      'editing': 0, 'self_role': 3},
            'native_input': {'draft_text_hex': b'NotPersisted'.hex()}}
        self.assertEqual(release.validate_denied_save({'announcement_denied_save_restore': proof}, text), proof)
        for key in ('accepted', 'sql_exact', 'cache_restored', 'native79_via_control28', 'no_explicit_help_reopen'):
            bad = deepcopy(proof); bad[key] = False
            with self.assertRaises(ValueError):
                release.validate_denied_save({'announcement_denied_save_restore': bad}, text)
        for section, key, wrong in (('cache', 'editing', 1), ('cache', 'text_hex', b'NotPersisted'.hex()),
            ('cache', 'logical_size', len(text) + 5), ('cache', 'self_role', 1),
            ('native_input', 'draft_text_hex', text.hex())):
            bad = deepcopy(proof); bad[section][key] = wrong
            with self.assertRaises(ValueError):
                release.validate_denied_save({'announcement_denied_save_restore': bad}, text)
        with self.assertRaises(ValueError):
            release.validate_denied_save({}, text)

    def test_migration_preserves_typed_unknown_saved_rows(self):
        with sqlite3.connect(':memory:') as db:
            db.executescript('CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY,name TEXT,sql_text TEXT,applied_at TEXT);'
                'CREATE TABLE owned_guilds(id INTEGER PRIMARY KEY AUTOINCREMENT);'
                'CREATE TABLE owned_guild_governance_0078(id INTEGER);'
                'CREATE TABLE owned_guild_applications_0078(id INTEGER);'
                'CREATE TABLE unknown_saved(i,v);'
                "INSERT INTO unknown_saved VALUES(NULL,X''),(1.25,X'0000FF'),(1.25,X'0000FF'),('01',NULL);")
            db.executemany('INSERT INTO schema_migrations VALUES(?,?,?,?)',
                ((v, 'TEST_ONLY_' + str(v), 'TEST_ONLY_SQL', 'before') for v in range(1, 50)))
            before = release.capture_connection(db)
            sql = release.migration_sql()
            db.executescript(sql)
            db.execute('INSERT INTO schema_migrations VALUES(?,?,?,?)',
                       (50, release.MIGRATION_NAME, sql, 'after'))
            after = release.capture_connection(db)
            release.require50(before, after, sql)
            db.execute("UPDATE unknown_saved SET v=X'FF' WHERE typeof(i)='real'")
            changed = release.capture_connection(db)
            with self.assertRaises(ValueError):
                release.require50(before, changed, sql)


if __name__ == '__main__':
    unittest.main()
