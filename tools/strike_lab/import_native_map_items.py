"""Pinned SPI5569/5576 display sources only; never inventory ownership or use rules."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
from .omega_assets import decode_csvz
from .recover_items import lines_of, section, LABELS

ROOT=Path(__file__).resolve().parents[2]
SOURCE='Data2/Patch/Comm/gamedata.csvZ'
SOURCE_SHA='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
DECODED_SHA='75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
AUTHORITY='SOURCE_DISPLAY_ONLY'
ROW_PINS={5569:(8236,'6aad4d59bbbd41192acfc375d538ca93f1c2e454975e44f57114e7aedbae172e'),
          5576:(8243,'6877e19719a222a3ad7bf45d1f61526d7364eb3b822890f15845d6a8ca216404')}
SCHEMA=(
'''CREATE TABLE native_map_item_sources (
 source_file TEXT PRIMARY KEY,
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64),
 decoded_sha256 TEXT NOT NULL CHECK(length(decoded_sha256)=64),
 source_section TEXT NOT NULL CHECK(source_section='SPI'),
 section_row_count INTEGER NOT NULL CHECK(section_row_count=737),
 row_desc_line INTEGER NOT NULL CHECK(row_desc_line=3),
 row_desc_sha256 TEXT NOT NULL CHECK(length(row_desc_sha256)=64),
 row_desc_raw BLOB NOT NULL CHECK(typeof(row_desc_raw)='blob'),
 encoding TEXT NOT NULL CHECK(encoding='CP950'),
 authority TEXT NOT NULL CHECK(authority='SOURCE_DISPLAY_ONLY')
)''',
'''CREATE TABLE native_map_item_rows (
 item_id INTEGER PRIMARY KEY CHECK(item_id IN (5569,5576)),
 source_file TEXT NOT NULL REFERENCES native_map_item_sources(source_file),
 source_line INTEGER NOT NULL CHECK(source_line>0),
 decoded_offset INTEGER NOT NULL CHECK(decoded_offset>=0),
 record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record)>0),
 category_code INTEGER NOT NULL,
 resource_name BLOB NOT NULL CHECK(typeof(resource_name)='blob'),
 icon_id INTEGER NOT NULL CHECK(icon_id BETWEEN 0 AND 65535),
 name_bytes BLOB NOT NULL CHECK(typeof(name_bytes)='blob'),
 description_bytes BLOB NOT NULL CHECK(typeof(description_bytes)='blob'),
 effect_code INTEGER NOT NULL CHECK(effect_code BETWEEN 0 AND 65535),
 source_flags BLOB NOT NULL CHECK(typeof(source_flags)='blob' AND length(source_flags)=12),
 authority TEXT NOT NULL CHECK(authority='SOURCE_DISPLAY_ONLY')
)''')
TABLES=('native_map_item_sources','native_map_item_rows')
ORDERS=('source_file','item_id')

def require(condition,message):
    if not condition:raise ValueError(message)

def sha(value):return hashlib.sha256(value).hexdigest()

def pinned_records(client):
    raw=(Path(client)/SOURCE).read_bytes()
    require(sha(raw)==SOURCE_SHA,'Map item source pin mismatch')
    decoded=decode_csvz(raw)
    require(sha(decoded)==DECODED_SHA,'Map item decoded pin mismatch')
    lines=lines_of(decoded)
    desc=section(lines,b'RowDesc')
    require(len(desc)==1 and desc[0][0]==3 and desc[0][1].split(b',')==[s.encode('cp950') for s in LABELS],
            'Map item RowDesc mismatch')
    desc_line,desc_raw=desc[0]
    require(sha(desc_raw)=='ab84cb5beb35b1a0f753f657993d881673b3b59351049cdedf91c2f7fab79e34','RowDesc pin mismatch')
    definitions=section(lines,b'SPI')
    require(len(definitions)==737,'SPI source count changed')
    offsets=[];position=0
    for line in decoded.split(b'\n'):
        offsets.append(position);position+=len(line)+1
    rows=[]
    for line,record in definitions:
        fields=record.split(b',')
        if fields[0] not in (b'5569',b'5576'):continue
        key=int(fields[0])
        require((line,sha(record))==ROW_PINS[key] and len(fields)==26,'Map item record pin/shape mismatch')
        record.decode('cp950',errors='strict')
        require(all(v in (b'0',b'1') for v in fields[14:26]),'Map item flag column mismatch')
        # Columns14..24 have RowDesc labels. Column25 is retained verbatim as
        # the twelfth raw flag; it has no supplied RowDesc label. These are not
        # packed inventory metadata, stack limits, consumption or grants.
        flags=bytes(int(v) for v in fields[14:26])
        rows.append((key,SOURCE,line,offsets[line-1],sha(record),record,int(fields[1]),fields[2],
                     int(fields[3]),fields[4],fields[8],int(fields[13]),flags,AUTHORITY))
    require([row[0] for row in rows]==[5569,5576],'Map item source subset incomplete')
    sources=((SOURCE,SOURCE_SHA,DECODED_SHA,'SPI',737,desc_line,sha(desc_raw),desc_raw,'CP950',AUTHORITY),)
    return sources,tuple(rows)

def _install(db):
    for table,ddl in zip(TABLES,SCHEMA):
        existing=db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone()
        if existing:
            require(' '.join(existing[0].split())==' '.join(ddl.split()),'Conflicting map item schema')
        else:db.execute(ddl)

def install(db):
    require(not db.in_transaction,'Map item install requires its own transaction')
    db.execute('PRAGMA foreign_keys=ON');db.execute('BEGIN IMMEDIATE')
    try:_install(db);db.commit()
    except BaseException:db.rollback();raise

def import_catalog(db,client):
    require(not db.in_transaction,'Map item import requires its own transaction')
    expected=pinned_records(client)
    db.execute('PRAGMA foreign_keys=ON');db.execute('BEGIN IMMEDIATE')
    try:
        _install(db)
        read=lambda:tuple(tuple(db.execute('SELECT * FROM '+table+' ORDER BY '+order)) for table,order in zip(TABLES,ORDERS))
        stored=read();present=any(stored)
        require(not present or stored==expected,'Conflicting/partial map item source; refusing overwrite')
        if not present:
            for table,rows in zip(TABLES,expected):
                db.executemany('INSERT INTO '+table+' VALUES('+','.join('?' for _ in rows[0])+')',rows)
        require(read()==expected,'Map item source readback mismatch')
        require(db.execute('PRAGMA foreign_key_check').fetchone() is None and
                db.execute('PRAGMA quick_check').fetchone()==('ok',),'Map item database integrity failed')
        db.commit()
        return dict(items=2,inserted=0 if present else 2,authority=AUTHORITY,inventory_grants=0,gameplay_rules=0)
    except BaseException:db.rollback();raise

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--client',type=Path,default=ROOT.parent/'God2')
    args=parser.parse_args();db=args.database.resolve();client=args.client.resolve()
    require(not db.is_relative_to(client),'Refusing database inside client tree')
    with closing(sqlite3.connect(db)) as connection:print(json.dumps(import_catalog(connection,client)))

if __name__=='__main__':main()
