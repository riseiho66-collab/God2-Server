"""CUSTOM-0059: create a separate candidate DB for0/150 牛轉仙界踏.

Reads the source database read-only. Never edits/replaces it, grants character
skills, or changes the native catalog. Reserve122..149 except existing126.
"""
from __future__ import annotations
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
from tools.skills.register_shunying_skill import COLUMNS, SCHEMA, check_database, native_snapshot, snapshot_digest

ROOT=Path(__file__).resolve().parents[2]
CANDIDATES=ROOT/'artifacts/custom-skills/thousand-bulls'
DESIGN='CUSTOM-0059'
ROW=(0,150,'牛轉仙界踏','pending_client_integration',DESIGN,'CUSTOM_DESIGNED',0,73,14)

def build_candidate(source:Path,output:Path,*,candidate_root:Path=CANDIDATES)->dict:
    source=Path(source).resolve(strict=True);output=Path(output).resolve()
    if source==output or output.exists() or not output.is_relative_to(Path(candidate_root).resolve()):
        raise ValueError('Output must be a new file under the isolated candidate directory')
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('xb'):pass
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as origin, closing(sqlite3.connect(output)) as db:
        origin.backup(db);check_database(db);baseline=native_snapshot(db)
        db.execute('PRAGMA foreign_keys=ON');db.execute('BEGIN IMMEDIATE')
        try:
            before=db.execute('SELECT * FROM custom_skill_registry ORDER BY kind,definition_id').fetchall()
            if tuple(row[1] for row in db.execute('PRAGMA table_info(custom_skill_registry)'))!=COLUMNS:
                raise ValueError('Unknown custom registry columns')
            shunying=[r for r in before if r[:2]==(0,126)]
            if len(shunying)!=1 or shunying[0][2]!='瞬影三煞斬' or shunying[0][4]!='CUSTOM-0058':
                raise ValueError('Existing Shunying0/126 identity must be preserved')
            # The previous schema allowed at most3 selected opponents. Rebuild
            # only this simple registry, with every existing row kept verbatim.
            dependent=db.execute("SELECT name FROM sqlite_master WHERE tbl_name='custom_skill_registry' AND type IN ('trigger','index') AND sql IS NOT NULL").fetchall()
            for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
                if any(row[2]=='custom_skill_registry' for row in db.execute('PRAGMA foreign_key_list("'+table.replace('"','""')+'")')):
                    dependent.append((table,))
            if dependent:raise ValueError('Registry migration requires explicit dependency review')
            schema=SCHEMA.replace('custom_skill_registry','custom_skill_registry_candidate').replace('max_targets BETWEEN 1 AND 3','max_targets BETWEEN 1 AND 14')
            # Preserve the already-installed126 active status from its verified release.
            schema=schema.replace("('reserved','pending_client_integration')","('reserved','pending_client_integration','active')")
            schema=schema.replace("status='pending_client_integration' AND","status IN ('pending_client_integration','active') AND")
            db.execute(schema)
            db.executemany('INSERT INTO custom_skill_registry_candidate VALUES(?,?,?,?,?,?,?,?,?)',before)
            db.execute('DROP TABLE custom_skill_registry')
            db.execute('ALTER TABLE custom_skill_registry_candidate RENAME TO custom_skill_registry')
            for number in range(122,150):
                if number==126:continue
                existing=db.execute('SELECT * FROM custom_skill_registry WHERE kind=0 AND definition_id=?',(number,)).fetchone()
                if existing:
                    if existing[2] is not None or existing[3]!='reserved' or any(v is not None for v in existing[6:]):
                        raise ValueError(f'Reserved identity collision0/{number}')
                else:db.execute('INSERT INTO custom_skill_registry VALUES(?,?,?,?,?,?,?,?,?)',(0,number,None,'reserved',DESIGN,'CUSTOM_DESIGNED',None,None,None))
            existing=db.execute('SELECT * FROM custom_skill_registry WHERE kind=0 AND definition_id=150').fetchone()
            if existing and existing!=ROW:raise ValueError('Skill identity collision0/150')
            if not existing:db.execute('INSERT INTO custom_skill_registry VALUES(?,?,?,?,?,?,?,?,?)',ROW)
            for row in before:
                if db.execute('SELECT * FROM custom_skill_registry WHERE kind=? AND definition_id=?',row[:2]).fetchone()!=row:
                    raise ValueError('Existing custom row changed')
            if native_snapshot(db)!=baseline:raise ValueError('Native catalog changed')
            check_database(db);db.commit()
        except BaseException:db.rollback();raise
    return {'source_read_only':str(source),'candidate':str(output),'skill':dict(zip(COLUMNS,ROW)),
        'reserved':list(range(122,126))+list(range(127,150)),
        'preserved_skill':126,'native_snapshot_sha256':snapshot_digest(baseline),
        'activation':'candidate registration only; no grants, installation or live mutation'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(build_candidate(args.source,args.output),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
