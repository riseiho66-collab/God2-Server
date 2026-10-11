"""Full current source import/readback, missing fields and transaction failures."""
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest
from tools.strike_lab import import_native_quests as missions
from tools.strike_lab import import_native_quest_requirements as requirements
from tools.strike_lab import import_native_quest_sources as sources
from test_import_native_skills import migrations,migrate_test_database

class QuestSourceTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:');self.addCleanup(self.db.close)
        migrate_test_database(self.db,migrations());self.client=missions.ROOT.parent/'God2'
        self.db.execute("insert into accounts(username,password_hash) values('preserved','hash')");self.db.commit()
        missions.import_catalog(self.db,self.client)

    def test_full_import_cpp_readback_and_missing_columns(self):
        result=sources.import_catalog(self.db,self.client)
        self.assertEqual(result['inserted'],{'native_quest_definitions':418,'native_daily_quest_source':85})
        self.assertEqual(sources.import_catalog(self.db,self.client)['inserted'],{'native_quest_definitions':0,'native_daily_quest_source':0})
        requirements.import_catalog(self.db,self.client)
        executable=Path(os.environ.get('GOD2_NATIVE_QUEST_READER',missions.ROOT/'build-town-visibility/tests/Release/native-quest-catalog-reader.exe'))
        with tempfile.TemporaryDirectory(prefix='god2-quest-sources-') as tmp:
            path=Path(tmp)/'sources.db'
            def read():
                with closing(sqlite3.connect(path)) as target:self.db.backup(target)
                return subprocess.run([str(executable),str(path),'--source-records'],capture_output=True,text=True,timeout=15)
            run=read();self.assertEqual(run.returncode,0,run.stderr);output=json.loads(run.stdout)
            self.assertEqual(output['counts'],[418,2014,169,85]);catalog=missions.build_catalog(self.client)
            for key,kind in (('definitions','missions'),('requirements','requirements'),('daily','daily')):
                expected=catalog['tables'][kind]['records']
                if key=='definitions':expected=[row for row in expected if row['raw_fields_hex'][0]]
                self.assertEqual([row['fields_hex'] for row in output[key]],[row['raw_fields_hex'] for row in expected])
                self.assertEqual([row['record_sha256'] for row in output[key]],[row['source_record_sha256'] for row in expected])
            expected=[row for row in catalog['tables']['missions']['records'] if not row['raw_fields_hex'][0]]
            self.assertEqual([row['fields_hex'] for row in output['descriptions']],[row['raw_fields_hex'] for row in expected])
            self.assertEqual(sum(row['reward_hex'] is None for row in output['daily']),5)
            self.db.execute("update native_quest_definitions set title_bytes=x'61' where mission_index=1");self.db.commit()
            run=read();self.assertNotEqual(run.returncode,0);self.assertEqual(run.stdout,'')
        self.assertEqual(self.db.execute('select username,password_hash from accounts').fetchall(),[('preserved','hash')])

    def test_injected_daily_failure_rolls_back_both_tables(self):
        self.db.execute("create trigger fail_daily before insert on native_daily_quest_source when NEW.record_index=3 begin select raise(ABORT,'injected'); end")
        with self.assertRaises(sqlite3.DatabaseError):sources.import_catalog(self.db,self.client)
        for table in ('native_quest_definitions','native_daily_quest_source'):
            self.assertEqual(self.db.execute('select count(*) from '+table).fetchone(),(0,))
        self.assertFalse(self.db.in_transaction)

    def test_conflicting_daily_source_refuses_overwrite(self):
        sources.import_catalog(self.db,self.client)
        self.db.execute("update native_daily_quest_source set raw_record=x'61' where record_index=0");self.db.commit()
        with self.assertRaises(ValueError):sources.import_catalog(self.db,self.client)
        self.assertEqual(self.db.execute('select raw_record from native_daily_quest_source where record_index=0').fetchone(),(b'a',))

if __name__=='__main__':unittest.main()
