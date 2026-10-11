"""Install the immutable CUSTOM-0051 fruit quest source/inference bundle.

No players, quests, items or rewards are created. An explicit database is
required; this tool never discovers the configured production database.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
from .current_inferred_quest_sources_20260927 import bundle

ROOT=Path(__file__).resolve().parents[2]
SHA='ab3e063564d0e7b351c3abab9e3475419c3a710ec9371b3de4d9b01f44a76541'
CLIENT_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
AUTHORITY='PINNED_SOURCE_AND_INFERENCE_BUNDLE'
SCHEMA='''CREATE TABLE qualified_fruit_quest_sources (
 id INTEGER PRIMARY KEY CHECK(id=1),
 payload BLOB NOT NULL CHECK(typeof(payload)='blob' AND length(payload)=30421),
 payload_sha256 TEXT NOT NULL CHECK(payload_sha256='ab3e063564d0e7b351c3abab9e3475419c3a710ec9371b3de4d9b01f44a76541'),
 client_sha256 TEXT NOT NULL CHECK(client_sha256='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'),
 authority TEXT NOT NULL CHECK(authority='PINNED_SOURCE_AND_INFERENCE_BUNDLE'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0051')
)'''


def require(value,message):
    if not value:raise ValueError(message)


def qualified_payload(client):
    # Historical Windows receipt has577CRLFs. Preserve its exact30421bytes
    # on every host rather than silently changing the pinned document to LF.
    payload=(json.dumps(bundle(Path(client)),ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf-8')
    validate(payload)
    return payload


def validate(payload):
    require(isinstance(payload,bytes) and len(payload)==30421 and hashlib.sha256(payload).hexdigest()==SHA,
            'Fruit source bundle bytes/hash changed')


def install(db,payload,*,install_schema=False):
    validate(payload)
    require(not db.in_transaction,'Fruit import requires its own transaction')
    expected=(1,payload,SHA,CLIENT_SHA,AUTHORITY,'CUSTOM-0051')
    db.execute('BEGIN IMMEDIATE')
    try:
        exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='qualified_fruit_quest_sources'").fetchone()
        if not exists:
            require(install_schema,'Apply source schema32 before importing')
            db.execute(SCHEMA)
        prior=db.execute('SELECT id,payload,payload_sha256,client_sha256,authority,design_id FROM qualified_fruit_quest_sources ORDER BY id').fetchall()
        require(not prior or prior==[expected],'Conflicting fruit bundle; refusing replacement')
        if not prior:db.execute('INSERT INTO qualified_fruit_quest_sources VALUES(?,?,?,?,?,?)',expected)
        require(db.execute('SELECT id,payload,payload_sha256,client_sha256,authority,design_id FROM qualified_fruit_quest_sources').fetchall()==[expected],
                'Fruit bundle readback mismatch')
        require(db.execute('PRAGMA quick_check').fetchone()==('ok',),'Fruit import DB integrity')
        db.commit()
        return dict(inserted=not bool(prior),payload_bytes=len(payload),payload_sha256=SHA,authority=AUTHORITY,player_rows_written=0)
    except BaseException:
        db.rollback()
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--database',type=Path,required=True)
    p.add_argument('--client',type=Path,default=ROOT.parent/'God2')
    p.add_argument('--install-schema',action='store_true')
    args=p.parse_args();database=args.database.resolve();client=args.client.resolve()
    require(database.is_file() and not database.is_relative_to(client),'Explicit existing non-client database required')
    payload=qualified_payload(client)
    with closing(sqlite3.connect(database.as_uri()+'?mode=rw',uri=True)) as db:
        result=install(db,payload,install_schema=args.install_schema)
    print(json.dumps(result))


if __name__=='__main__':main()
