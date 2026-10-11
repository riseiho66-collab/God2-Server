"""Actual current native weapon cache/import regressions; temporary DBs only."""
import copy
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from tools.strike_lab import import_native_weapons as catalog

CACHE=catalog.ROOT/'artifacts/research/native-weapons-20260926/records.json'

class WeaponImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=catalog.cached_records(CACHE)
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='god2-native-weapon-import-')
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.path=self.root/'native.sqlite';self.db=sqlite3.connect(self.path)
        self.addCleanup(self.db.close)
        self.db.execute('CREATE TABLE unrelated_save(id INTEGER PRIMARY KEY,payload BLOB)')
        self.db.execute("INSERT INTO unrelated_save VALUES(1,X'001180ff')");self.db.commit()
    def snapshot(self):return '\n'.join(self.db.iterdump())
    def imported(self):return catalog.import_catalog(self.db,records=self.records)
    def test_native_cache_fingerprint_types_and_sample_original_parser(self):
        self.assertEqual(catalog.fingerprint(self.records),catalog.CATALOG_SHA)
        self.assertEqual([len(g) for g in self.records],[2,1259])
        self.assertTrue(all(type(r[6]) is bytes and type(r[8]) is bytes for r in self.records[1]))
        native=catalog.NativeItemMetadata()
        for family,ordinal in (('WPN',0),('WPN',1),('TWP',0),('TWP',628)):
            sample=native.item_row(family,ordinal)
            cached=next(r for r in self.records[1] if r[0]==family and r[2]==ordinal)
            self.assertEqual((sample['key'],sample['source_line'],sample['record']),
                             (cached[1],cached[3],cached[8]))
    def test_complete_roundtrip_idempotence_and_unrelated_save(self):
        before=self.db.execute('SELECT * FROM unrelated_save').fetchall()
        self.assertEqual(self.imported()['inserted'],1259)
        snapshot=self.snapshot();self.assertEqual(self.imported()['inserted'],0)
        self.assertEqual(self.snapshot(),snapshot)
        self.assertEqual(self.db.execute('SELECT * FROM unrelated_save').fetchall(),before)
        groups=tuple(tuple(self.db.execute('SELECT * FROM '+t+' ORDER BY '+order))
                     for t,order in zip(catalog.TABLES,catalog.ORDERS))
        self.assertEqual(groups,self.records)
        self.assertEqual(self.db.execute('PRAGMA foreign_key_check').fetchall(),[])
    def test_source_identity_checked_even_for_direct_cached_records(self):
        before=self.snapshot()
        for name in ('CLIENT_EXE_SHA','SOURCE_SHA','DECODED_SHA','IMAGE_SHA256'):
            with self.subTest(pin=name),patch.object(catalog,name,'0'*64):
                with self.assertRaises(ValueError):self.imported()
                with self.assertRaises(ValueError):catalog.cached_records(CACHE)
            self.assertEqual(self.snapshot(),before);self.assertFalse(self.db.in_transaction)
        with self.assertRaisesRegex(ValueError,'Only current pinned client'):
            catalog.import_catalog(self.db,self.root,records=self.records)
        with patch.object(catalog,'NativeItemMetadata',side_effect=RuntimeError('Do not re-extract cached records')):
            records=catalog.cached_records(CACHE)
            self.assertEqual(catalog.import_catalog(self.db,records=records)['inserted'],1259)
    def test_changed_cache_and_fingerprint_type_aliases_refused_before_writes(self):
        original=json.loads(CACHE.read_text())
        edits=(lambda g:g[1][0].__setitem__(8,'00'+g[1][0][8][2:]),
               lambda g:g[0][0].__setitem__(2,'0'*64),
               lambda g:g[1].pop(),lambda g:g[1][0].__setitem__(1,str(g[1][0][1])),
               lambda g:g[1][0].__setitem__(6,'not hexadecimal'))
        before=self.snapshot()
        for ordinal,edit in enumerate(edits):
            value=copy.deepcopy(original);edit(value);path=self.root/f'bad-{ordinal}.json';path.write_text(json.dumps(value))
            with self.subTest(ordinal=ordinal),self.assertRaises(ValueError):catalog.cached_records(path)
            self.assertEqual(self.snapshot(),before)
        mutable=[list(self.records[0]),list(self.records[1])];row=list(mutable[1][0]);row[1]=str(row[1]);mutable[1][0]=row
        self.assertEqual(catalog.fingerprint(mutable),catalog.CATALOG_SHA)
        with self.assertRaisesRegex(ValueError,'field type'):catalog.import_catalog(self.db,records=mutable)
    def test_partial_or_corrupt_existing_catalog_not_overwritten(self):
        self.imported()
        for sql in ("UPDATE native_weapon_rows SET decoded_offset=decoded_offset+1 WHERE item_id=1",
                    "DELETE FROM native_weapon_rows WHERE item_id=1",
                    "UPDATE native_weapon_sources SET source_sha256=replace(source_sha256,'7','6') WHERE family='WPN'"):
            with self.subTest(sql=sql):
                self.db.execute(sql);self.db.commit();before=self.snapshot()
                with self.assertRaisesRegex(ValueError,'Conflicting/partial'):self.imported()
                self.assertEqual(self.snapshot(),before);self.assertFalse(self.db.in_transaction)
    def test_failed_insert_rolls_back_both_groups(self):
        catalog.install(self.db)
        self.db.execute("CREATE TRIGGER fail_weapon BEFORE INSERT ON native_weapon_rows WHEN NEW.source_record_index=17 BEGIN SELECT RAISE(ABORT,'isolated failure'); END")
        self.db.commit();before=self.snapshot()
        with self.assertRaises(sqlite3.IntegrityError):self.imported()
        self.assertEqual(self.snapshot(),before);self.assertFalse(self.db.in_transaction)
    def test_outer_transaction_schema_conflict_and_readonly(self):
        self.db.execute('BEGIN');before=self.snapshot()
        with self.assertRaisesRegex(ValueError,'own transaction'):self.imported()
        self.assertTrue(self.db.in_transaction);self.assertEqual(self.snapshot(),before);self.db.rollback()
        self.db.execute('CREATE TABLE native_weapon_sources(family TEXT)');self.db.commit();before=self.snapshot()
        with self.assertRaisesRegex(ValueError,'Conflicting native weapon schema'):self.imported()
        self.assertEqual(self.snapshot(),before)
        self.db.execute('DROP TABLE native_weapon_sources');self.db.commit()
        ro=sqlite3.connect(self.path.as_uri()+'?mode=ro',uri=True)
        try:
            with self.assertRaises(sqlite3.OperationalError):catalog.import_catalog(ro,records=self.records)
            self.assertFalse(ro.in_transaction)
        finally:ro.close()
    def test_cli_cached_formal_import(self):
        flags=['-O'] if sys.flags.optimize else []
        result=subprocess.run([sys.executable,*flags,'-X','utf8','-B','-m','tools.strike_lab.import_native_weapons',
                               '--database',str(self.path),'--records-cache',str(CACHE)],cwd=catalog.ROOT,
                               capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['inserted'],1259)
    def test_cpp_reader_and_lua_against_actual_imported_database(self):
        configured=os.environ.get('GOD2_NATIVE_WEAPON_TEST_EXE')
        executable=Path(configured) if configured else catalog.ROOT/'build-town-visibility/tests/Release/native-weapon-catalog.exe'
        if not executable.is_file():self.skipTest('Build native-weapon-catalog or set GOD2_NATIVE_WEAPON_TEST_EXE')
        self.imported();self.db.close();before=self.path.read_bytes()
        result=subprocess.run([str(executable),str(self.path)],cwd=catalog.ROOT,capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
        self.assertIn('PASS:',result.stdout);self.assertEqual(self.path.read_bytes(),before)

if __name__=='__main__':unittest.main()
