"""CTest wrapper: isolated actual source imports plus C++ SQL repository gates."""
import argparse
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools.strike_lab import import_native_quests, import_native_quest_sources
from tools.strike_lab import import_fruit_quest_sources


def run(executable,client):
    executable=Path(executable).resolve();client=Path(client).resolve()
    if not executable.is_file():raise ValueError('Repository test executable missing')
    creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    def child(mode,database):
        result=subprocess.run([str(executable),mode,str(database)],cwd=ROOT,
            check=True,text=True,capture_output=True,creationflags=creationflags,timeout=90)
        if result.stdout:print(result.stdout.strip())
        if result.stderr:print(result.stderr.strip(),file=sys.stderr)
    with tempfile.TemporaryDirectory(prefix='god2-fruit-repository-') as directory:
        work=Path(directory).resolve()
        if work.parent!=Path(tempfile.gettempdir()).resolve():raise ValueError('Test output outside system temporary directory')
        database=work/'fixture.sqlite'
        child('--initialize',database)
        with closing(sqlite3.connect(database)) as db:
            import_native_quests.import_catalog(db,client)
            import_native_quest_sources.import_catalog(db,client)
            import_fruit_quest_sources.install(db,import_fruit_quest_sources.qualified_payload(client))
        child('--test',database)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--executable',type=Path,required=True)
    p.add_argument('--client',type=Path,default=ROOT.parent/'God2')
    args=p.parse_args()
    try:run(args.executable,args.client)
    except subprocess.CalledProcessError as error:
        print(error.stdout or '',file=sys.stderr);print(error.stderr or '',file=sys.stderr)
        raise SystemExit(error.returncode)
