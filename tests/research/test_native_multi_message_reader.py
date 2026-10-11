"""Pinned original source -> formal C++ source reader, read-only/negative checks."""
from contextlib import closing
import hashlib
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest
from tools.strike_lab.import_native_multi_messages import import_catalog,ROOT

class NativeMultiMessageReaderTests(unittest.TestCase):
    def test_complete_source_and_corruption_rejection_preserve_readonly_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            database=Path(tmp)/'source.db'
            with closing(sqlite3.connect(database)) as db:import_catalog(db,ROOT.parent/'God2')
            original=database.read_bytes()
            binary=os.environ['GOD2_MULTI_MESSAGE_READER_BINARY']
            result=subprocess.run([binary,str(database)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(result.stdout.strip(),'2995')
            self.assertEqual(database.read_bytes(),original)
            for mutation in (
                "UPDATE native_multi_message_rows SET text_bytes=X'61' WHERE message_key=1434 AND ordinal=1",
                "UPDATE native_multi_message_rows SET raw_record=X'61' WHERE message_key=1434 AND ordinal=1",
                "UPDATE native_multi_message_rows SET record_sha256=replace(record_sha256,'a','b') WHERE message_key=1434 AND ordinal=1",
                "UPDATE native_multi_messages SET option_count=8 WHERE message_key=1434",
                "UPDATE native_multi_message_sources SET source_sha256=replace(source_sha256,'a','b')",
                "DELETE FROM native_multi_message_rows WHERE message_key=2995 AND ordinal=1"):
                with self.subTest(mutation=mutation):
                    database.write_bytes(original)
                    with closing(sqlite3.connect(database)) as db:db.execute(mutation);db.commit()
                    before=hashlib.sha256(database.read_bytes()).digest()
                    result=subprocess.run([binary,str(database)],capture_output=True,text=True)
                    self.assertNotEqual(result.returncode,0);self.assertEqual(result.stdout,'')
                    self.assertEqual(hashlib.sha256(database.read_bytes()).digest(),before)
if __name__=='__main__':unittest.main()
