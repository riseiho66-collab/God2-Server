"""Read-only C++ integrity gate against a disposable full original-source DB."""
import argparse
from contextlib import closing
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.strike_lab.import_native_enemy_display import import_catalog
def main():
    p=argparse.ArgumentParser();p.add_argument('--executable',type=Path,required=True);a=p.parse_args()
    migration=(ROOT/'src/db/Migration.cpp').read_text('utf-8')
    ddl=[]
    for name in ('native_data_sources','native_enemy_display_catalog'):
        match=re.search(r'CREATE TABLE '+name+r'\s*\(.*?\n\);',migration,re.S)
        if not match:raise ValueError('Missing source schema')
        ddl.append(match.group(0))
    with tempfile.TemporaryDirectory(prefix='god2-all-enemy-display-') as temporary:
        path=Path(temporary)/'isolated.sqlite'
        with closing(sqlite3.connect(path)) as db:
            db.executescript(''.join(ddl)+"CREATE TABLE schema_migrations(version INTEGER,name TEXT); INSERT INTO schema_migrations VALUES(20,'native_enemy_display_catalog');")
        def check(mode):
            r=subprocess.run([str(a.executable.resolve()),mode,str(path)],capture_output=True,text=True,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),timeout=30)
            print(r.stdout,end='');print(r.stderr,end='',file=sys.stderr)
            if r.returncode:raise RuntimeError('Enemy display C++ gate failed')
        check('empty')
        with closing(sqlite3.connect(path)) as db:import_catalog(db,ROOT.parent/'God2')
        check('full')
        with closing(sqlite3.connect(path)) as db:
            db.execute('DELETE FROM native_enemy_display_catalog WHERE source_record_index=229');db.commit()
        check('reject')
if __name__=='__main__':main()
