"""Current source -> migrated isolated SQLite, with conflict/rollback checks."""
import sqlite3
import struct
from contextlib import closing
import os
import subprocess
import tempfile
from pathlib import Path
import unittest
from tools.strike_lab import import_native_quests as catalog
from test_import_native_skills import migrations, migrate_test_database


class QuestImportTests(unittest.TestCase):
    def test_actmis_display_import_and_rollback(self):
        from tools.strike_lab import import_native_quest_requirements as requirements
        self.db.execute("CREATE TRIGGER fail_actmis BEFORE INSERT ON native_quest_requirement_display WHEN NEW.serial=2 BEGIN SELECT RAISE(ABORT,'injected'); END")
        with self.assertRaises(sqlite3.DatabaseError):requirements.import_catalog(self.db,self.client)
        self.assertEqual(self.db.execute('SELECT count(*) FROM native_quest_requirement_display').fetchone(),(0,))
        self.assertEqual(self.db.execute('SELECT count(*) FROM native_data_sources WHERE dataset_id=?',(requirements.DATASET,)).fetchone(),(0,))
        self.db.execute('DROP TRIGGER fail_actmis')
        self.assertEqual(requirements.import_catalog(self.db,self.client)['inserted'],169)
        self.assertEqual(requirements.import_catalog(self.db,self.client)['inserted'],0)
        rows=self.db.execute('SELECT serial,raw_record,item_quantity_pairs FROM native_quest_requirement_display ORDER BY serial').fetchall()
        self.assertEqual([row[0] for row in rows],list(range(1,170)))
        for serial,raw,pairs in rows:
            fields=raw.split(b',')
            self.assertEqual(int(fields[0]),serial)
            self.assertEqual(list(struct.iter_unpack('<HB',pairs)),[(int(fields[i]),int(fields[i+1])) for i in (2,4,6,8)])
        self.db.execute("UPDATE native_quest_requirement_display SET item_quantity_pairs=zeroblob(12) WHERE serial=1")
        self.db.commit()
        with self.assertRaises(ValueError):requirements.import_catalog(self.db,self.client)

    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        migrate_test_database(self.db,migrations())
        self.client=catalog.ROOT.parent/'God2'
        self.db.execute("INSERT INTO accounts(username,password_hash) VALUES('untouched','test')")
        self.db.commit()

    def test_full_import_and_idempotence(self):
        self.assertEqual(catalog.import_catalog(self.db,self.client)['inserted'],2014)
        self.assertEqual(catalog.import_catalog(self.db,self.client)['inserted'],0)
        self.assertEqual(self.db.execute('SELECT count(DISTINCT mission_index),count(*) FROM native_quest_descriptions').fetchone(),(418,2014))
        self.assertEqual(self.db.execute('SELECT * FROM native_data_sources WHERE dataset_id=?',(catalog.DATASET,)).fetchall(),[catalog.SOURCE_ROW])
        self.assertEqual(self.db.execute('SELECT username,password_hash FROM accounts').fetchall(),[('untouched','test')])

    def test_conflict_refuses_overwrite(self):
        catalog.import_catalog(self.db,self.client)
        self.db.execute("UPDATE native_quest_descriptions SET raw_record=x'61' WHERE mission_index=1 AND description_index=0")
        self.db.commit()
        with self.assertRaises(ValueError):catalog.import_catalog(self.db,self.client)
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(self.db.execute('SELECT raw_record FROM native_quest_descriptions WHERE mission_index=1 AND description_index=0').fetchone(),(b'a',))

    def test_injected_failure_rolls_back_source_and_records(self):
        self.db.execute("CREATE TRIGGER fail_quest BEFORE INSERT ON native_quest_descriptions WHEN NEW.mission_index=2 BEGIN SELECT RAISE(ABORT,'injected'); END")
        with self.assertRaises(sqlite3.DatabaseError):catalog.import_catalog(self.db,self.client)
        self.assertEqual(self.db.execute('SELECT count(*) FROM native_quest_descriptions').fetchone(),(0,))
        self.assertEqual(self.db.execute('SELECT count(*) FROM native_data_sources WHERE dataset_id=?',(catalog.DATASET,)).fetchone(),(0,))
        self.assertFalse(self.db.in_transaction)

    def test_cpp_reader_matches_all_source_counts_and_rejects_damage(self):
        executable=Path(os.environ.get('GOD2_NATIVE_QUEST_READER',
            catalog.ROOT/'build/tests/Release/native-quest-catalog-reader.exe'))
        self.assertTrue(executable.is_file(),'Build native-quest-catalog-reader first')
        catalog.import_catalog(self.db,self.client)
        expected=[q['step_field'] for q in catalog.build_catalog(self.client)['quests']]
        with tempfile.TemporaryDirectory(prefix='god2-quest-reader-') as directory:
            path=Path(directory)/'catalog.sqlite'
            def read():
                with closing(sqlite3.connect(path)) as target:self.db.backup(target)
                return subprocess.run([str(executable),str(path)],capture_output=True,text=True,timeout=10)
            result=read()
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(list(map(int,result.stdout.split())),expected)
            self.db.execute("UPDATE native_data_sources SET source_sha256=? WHERE dataset_id=?",('a'*64,catalog.DATASET))
            self.db.commit()
            result=read();self.assertNotEqual(result.returncode,0);self.assertEqual(result.stdout,'')
            self.db.execute("UPDATE native_data_sources SET source_sha256=? WHERE dataset_id=?",(catalog.SOURCE_SHA,catalog.DATASET))
            self.db.execute('DELETE FROM native_quest_descriptions WHERE mission_index=418')
            self.db.commit()
            result=read();self.assertNotEqual(result.returncode,0);self.assertEqual(result.stdout,'')


if __name__=='__main__':
    unittest.main()
