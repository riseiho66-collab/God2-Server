"""Candidate-only custom150 registry migration on disposable databases."""
from contextlib import closing
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
from tools.skills.register_shunying_skill import ROWS,SCHEMA
from tools.skills.register_thousand_bulls_skill import ROW,build_candidate

class ThousandBullsRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.source=self.root/'source.db';self.output=self.root/'candidate/new.db'
        with closing(sqlite3.connect(self.source)) as db:
            db.execute('CREATE TABLE native_skill_catalog(kind INTEGER,definition_id INTEGER,raw_record BLOB,PRIMARY KEY(kind,definition_id))')
            db.executemany('INSERT INTO native_skill_catalog VALUES(?,?,?)',((k,i,bytes((k,i))) for k,n in enumerate((121,129,87,111)) for i in range(1,n+1)))
            db.execute(SCHEMA);db.executemany('INSERT INTO custom_skill_registry VALUES(?,?,?,?,?,?,?,?,?)',ROWS)
            db.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY,password BLOB)');db.execute("INSERT INTO accounts VALUES(1,X'1234')");db.commit()
    def run_candidate(self):return build_candidate(self.source,self.output,candidate_root=self.root/'candidate')
    def test_reserves_and_preserves_source_accounts_catalog_and126(self):
        before=hashlib.sha256(self.source.read_bytes()).hexdigest();result=self.run_candidate()
        self.assertEqual(result['preserved_skill'],126)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),before)
        with closing(sqlite3.connect(self.output)) as db:
            self.assertEqual(db.execute('SELECT * FROM custom_skill_registry WHERE definition_id=150').fetchone(),ROW)
            self.assertEqual(db.execute('SELECT * FROM custom_skill_registry WHERE definition_id<=126 ORDER BY definition_id').fetchall(),list(ROWS))
            self.assertEqual(db.execute("SELECT definition_id FROM custom_skill_registry WHERE status='reserved' ORDER BY definition_id").fetchall(),[(i,) for i in range(122,150) if i!=126])
            self.assertEqual(db.execute('SELECT * FROM accounts').fetchall(),[(1,b'\x12\x34')])
            self.assertEqual(db.execute('SELECT count(*) FROM native_skill_catalog').fetchone(),(448,))
    def test_preserves_installed_active126(self):
        with closing(sqlite3.connect(self.source)) as db:
            db.execute('DROP TABLE custom_skill_registry')
            schema=SCHEMA.replace("('reserved','pending_client_integration')","('reserved','pending_client_integration','active')").replace("status='pending_client_integration' AND","status IN ('pending_client_integration','active') AND")
            db.execute(schema);rows=list(ROWS);last=list(rows[-1]);last[3]='active';rows[-1]=tuple(last)
            db.executemany('INSERT INTO custom_skill_registry VALUES(?,?,?,?,?,?,?,?,?)',rows);db.commit()
        self.run_candidate()
        with closing(sqlite3.connect(self.output)) as db:
            self.assertEqual(db.execute('SELECT * FROM custom_skill_registry WHERE definition_id=126').fetchone(),rows[-1])
    def test_refuses_existing_output_and_non_candidate_or_source(self):
        self.run_candidate()
        with self.assertRaises(ValueError):self.run_candidate()
        with self.assertRaises(ValueError):build_candidate(self.source,self.source,candidate_root=self.root)
        with self.assertRaises(ValueError):build_candidate(self.source,self.root/'unscoped.db',candidate_root=self.root/'candidate')
    def test_collision_rolls_back_candidate_and_leaves_source_unchanged(self):
        with closing(sqlite3.connect(self.source)) as db:
            row=list(ROWS[-1]);row[1]=130;row[2]='Other skill';db.execute('INSERT INTO custom_skill_registry VALUES(?,?,?,?,?,?,?,?,?)',row);db.commit()
        before=self.source.read_bytes()
        with self.assertRaisesRegex(ValueError,'collision'):self.run_candidate()
        self.assertEqual(self.source.read_bytes(),before)
        with closing(sqlite3.connect(self.output)) as db:self.assertEqual(db.execute('SELECT count(*) FROM custom_skill_registry WHERE definition_id=150').fetchone(),(0,))

if __name__=='__main__':unittest.main()
