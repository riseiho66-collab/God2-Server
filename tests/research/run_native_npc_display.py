"""Full actual-memory qualified NPC source fixture for the C++ reader."""
import argparse
from contextlib import closing
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.strike_lab.import_native_npc_display import install
def main():
    p=argparse.ArgumentParser();p.add_argument('--executable',type=Path,required=True);a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='god2-all-npc-display-') as temporary:
        path=Path(temporary)/'isolated.sqlite'
        with closing(sqlite3.connect(path)) as db:
            install(db,ROOT.parent/'God2',install_schema=True)
            db.execute('CREATE TABLE npc_test_fixture_marker(value TEXT)')
            db.execute("INSERT INTO npc_test_fixture_marker VALUES('DISPOSABLE-NPC-CATALOG')")
            db.commit()
        result=subprocess.run([str(a.executable.resolve()),str(path)],capture_output=True,text=True,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),timeout=30)
        print(result.stdout,end='');print(result.stderr,end='',file=sys.stderr)
        if result.returncode:raise RuntimeError('Full NPC C++ fixture rejected')
if __name__=='__main__':main()
