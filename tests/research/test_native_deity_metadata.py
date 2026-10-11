from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from tools.strike_lab import import_native_deity_metadata as catalog
from tools.strike_lab.import_companion_metadata import CompanionMetadata
from tools.strike_lab.import_native_pet1_metadata import Pet1Metadata

ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/'artifacts/research/native-deity-metadata-20260927/records.json'

class NativeDeityMetadataTests(unittest.TestCase):
    def test_all_original_rows_and_category_binding(self):
        rows=catalog.cached(CACHE);native=catalog.NativeDeityMetadata()
        self.assertEqual(native.lookup_section('GOD'),(2,0))
        self.assertEqual(native.category_proof()['category_count'],46)
        for index,row in enumerate(rows):
            source=native.sections['GOD']['records'][index]
            self.assertEqual(row[4],bytes.fromhex(source['raw_record_hex']))
            self.assertEqual(row[3],source['source_line'])
            parsed=native.item_row('GOD',index)
            self.assertEqual(parsed['selector'],0)
            self.assertEqual(parsed['record'],row[6])
        for original,family,selector in ((CompanionMetadata(),'NCP',34),(Pet1Metadata(),'COM',32)):
            self.assertEqual(original.item_row(family,0)['selector'],selector)

    def test_atomic_idempotent_import_preserves_other_data(self):
        rows=catalog.cached(CACHE)
        with tempfile.TemporaryDirectory(prefix='god2-god-import-') as tmp:
            path=Path(tmp)/'catalog.db'
            with closing(sqlite3.connect(path)) as db:
                db.execute('create table native_companion_metadata(family,metadata_key,source_sha256,source_line,raw_record,record_sha256,parsed_record,primary key(family,metadata_key))')
                other=('NCP',28002,'other',1,b'raw','hash',b'parsed')
                db.execute('insert into native_companion_metadata values(?,?,?,?,?,?,?)',other)
                db.execute('create table saved_player(secret blob)')
                db.execute("insert into saved_player values(X'1234')");db.commit()
            self.assertFalse(catalog.install(path,rows)['idempotent'])
            self.assertTrue(catalog.install(path,rows)['idempotent'])
            changed=list(rows);last=changed[-1];changed[-1]=(*last[:6],bytes(396))
            with self.assertRaisesRegex(ValueError,'Existing GOD import differs'):catalog.install(path,changed)
            with self.assertRaisesRegex(ValueError,'Incomplete GOD'):catalog.install(path,rows[:-1])
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute("select * from native_companion_metadata where family='GOD' order by metadata_key").fetchall(),rows)
                self.assertEqual(db.execute("select * from native_companion_metadata where family='NCP'").fetchall(),[other])
                self.assertEqual(db.execute('select * from saved_player').fetchall(),[(b'\x12\x34',)])
            bad=Path(tmp)/'bad.json';data=bytearray(CACHE.read_bytes());data[-2]^=1;bad.write_bytes(data)
            with self.assertRaisesRegex(ValueError,'cache hash mismatch'):catalog.cached(bad)

if __name__=='__main__':unittest.main()
