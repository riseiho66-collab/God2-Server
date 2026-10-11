from contextlib import closing
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
from tools.strike_lab import import_native_pet1_metadata as catalog

ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/'artifacts/research/native-pet1-20260927/records.json'

class Pet1MetadataTests(unittest.TestCase):
    def test_cached_definitions_match_current_source_and_original_loader_samples(self):
        rows=catalog.cached(CACHE);native=catalog.Pet1Metadata()
        self.assertEqual(len(rows),2070)
        source=native.sections['COM']['records']
        for index,row in enumerate(rows):
            self.assertEqual(row[4],bytes.fromhex(source[index]['raw_record_hex']))
            self.assertEqual(row[3],source[index]['source_line'])
        for index in (0,1,6,1000,2069):
            parsed=native.item_row('COM',index)
            self.assertEqual(parsed['record'],rows[index][6]);self.assertEqual(parsed['selector'],32)
    def test_transaction_conflicts_and_cache_corruption_rejected(self):
        rows=catalog.cached(CACHE)
        with tempfile.TemporaryDirectory(prefix='god2-com-import-') as tmp:
            path=Path(tmp)/'catalog.db'
            with closing(sqlite3.connect(path)) as db:
                db.execute('create table native_pet1_metadata(family,metadata_key primary key,source_sha256,source_line,raw_record,record_sha256,parsed_record)')
                db.execute('create table saved_player(secret blob)');db.execute("insert into saved_player values(X'1234')");db.commit()
            self.assertFalse(catalog.install(path,rows)['idempotent']);self.assertTrue(catalog.install(path,rows)['idempotent'])
            changed=list(rows);last=changed[-1];changed[-1]=(*last[:6],bytes(396))
            with self.assertRaisesRegex(ValueError,'Existing COM import differs'):catalog.install(path,changed)
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute('select * from native_pet1_metadata order by metadata_key').fetchall(),rows)
                self.assertEqual(db.execute('select * from saved_player').fetchall(),[(b'\x12\x34',)])
            bad=Path(tmp)/'bad.json';data=bytearray(CACHE.read_bytes());data[-2]^=1;bad.write_bytes(data)
            with self.assertRaisesRegex(ValueError,'cache hash mismatch'):catalog.cached(bad)

if __name__=='__main__':unittest.main()
