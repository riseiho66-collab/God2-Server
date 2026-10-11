"""All 4043 current NPC display prefixes; source-bound, never spawn/stat authority."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import struct
from .omega_assets import decode_csvz

ROOT=Path(__file__).resolve().parents[2]
SOURCE='Data2/Patch/Comm/gamedata.csvZ'
SOURCE_SHA='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
DECODED_SHA='75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
CLIENT_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
MEMORY_SHA='1f3de6e0f62c340b20447c3b868907103b01caa64074688ebf47e9b5c725930a'
DATASET_SHA='b770c11e516b488adba54ab7b2bee5d1fee3eaf1c5deb3dafe2e22962ccd343c'
SCHEMA=(
'''CREATE TABLE native_npc_display_sources (
 id INTEGER PRIMARY KEY CHECK(id=1), source_file TEXT NOT NULL,
 source_sha256 TEXT NOT NULL, decoded_sha256 TEXT NOT NULL, client_sha256 TEXT NOT NULL,
 memory_receipt_sha256 TEXT NOT NULL, dataset_sha256 TEXT NOT NULL,
 row_count INTEGER NOT NULL CHECK(row_count=4043), section TEXT NOT NULL,
 loader_rva TEXT NOT NULL, authority TEXT NOT NULL)''',
'''CREATE TABLE native_npc_display_rows (
 npc_key INTEGER PRIMARY KEY CHECK(npc_key BETWEEN 1 AND 6999),
 source_line INTEGER NOT NULL CHECK(source_line>0), decoded_offset INTEGER NOT NULL CHECK(decoded_offset>=0),
 record_sha256 TEXT NOT NULL, raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob'),
 prefix28 BLOB NOT NULL CHECK(typeof(prefix28)='blob' AND length(prefix28)=28))''')

def sha(value):return hashlib.sha256(value).hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)

def project(fields):
    """4570F0 source writes into zero-initialized observed static prefix."""
    require(len(fields)>=5,'Short NPC row')
    name=fields[1];code=int(fields[2]);flags=(int(fields[3])&0x3fff)|((int(fields[4])&1)<<14)
    require(len(name)<64 and 0<=code<=65535,'NPC source bounds')
    out=bytearray(28)
    out[:min(len(name)+1,28)]=(name+b'\0')[:28]
    if len(name)>=16:out[15]=0
    if 5000<code<5004:flags|=0x8000
    struct.pack_into('<HH',out,16,flags,code)
    if 5000<code<5004:
        for field,kind,offset in ((5,b'h',24),(6,b'f',22),(7,b'b',20),(8,b'w',26)):
            value=fields[field] if field<len(fields) else b''
            if not value:continue
            require(re.fullmatch(rb'[0-9]'+kind+rb'[0-9][0-9]+',value) is not None,'NPC component grammar')
            a=((code-5001)&15)|((value[2]<<4)&255)
            b=((value[0]<<5)&255)|(int(value[3:])&31)
            out[offset:offset+2]=bytes((a,b))
    return bytes(out)

def canonical(rows):
    return b''.join(struct.pack('<HIII',r[0],r[1],r[2],len(r[4]))+r[4]+r[5] for r in rows)

def source_row():
    return (1,SOURCE,SOURCE_SHA,DECODED_SHA,CLIENT_SHA,MEMORY_SHA,DATASET_SHA,4043,'NPCAppearData','0x570f0','SOURCE_DISPLAY_ONLY')

def pinned_rows(client,receipt=ROOT/'artifacts/research/live-memory-references-20260927-02/memory-result.json'):
    packed=(Path(client)/SOURCE).read_bytes();require(sha(packed)==SOURCE_SHA,'NPC compressed source pin')
    plain=decode_csvz(packed);require(sha(plain)==DECODED_SHA,'NPC decoded source pin')
    memory_bytes=Path(receipt).read_bytes();require(sha(memory_bytes)==MEMORY_SHA,'NPC memory receipt pin')
    memory=json.loads(memory_bytes);require(memory['accepted'] is True,'NPC memory acceptance')
    observed=memory['loaded_static_catalogs'];require(observed['npc_source_count']==4043,'NPC memory count')
    by_key={r['key']:r for r in observed['npc_records']};require(len(by_key)==len(observed['npc_records'])==4043,'NPC memory duplicate/count')
    lines=plain.splitlines(keepends=True);offset=0;rows=[];remaining=None
    for line,full in enumerate(lines,1):
        raw=full.rstrip(b'\r\n');fields=raw.split(b',')
        if fields[0]==b'NPCAppearData':
            require(remaining is None and fields==[b'NPCAppearData',b'4043'],'NPC section identity');remaining=4043
        elif remaining:
            key=int(fields[0]);require(0<key<7000,'NPC key bounds');prefix=project(fields);match=by_key.get(key)
            require(match is not None and match['source_line']==line and match['source_record_sha256']==sha(raw),'NPC source/memory row mismatch')
            native=bytes.fromhex(match['record94_hex']);require(len(native)==94 and native[:28]==prefix,f'NPC full prefix mismatch {key}: {native[:28].hex()} != {prefix.hex()}')
            rows.append((key,line,offset,sha(raw),raw,prefix));remaining-=1
        offset+=len(full)
    rows.sort();require(remaining==0 and len(rows)==len({r[0] for r in rows})==4043,'NPC source count/keys')
    require(sha(canonical(rows))==DATASET_SHA,'NPC dataset pin')
    return rows

def install(db,client,receipt=ROOT/'artifacts/research/live-memory-references-20260927-02/memory-result.json',install_schema=False):
    rows=pinned_rows(client,receipt)
    require(not db.in_transaction,'NPC import requires own transaction')
    db.execute('BEGIN IMMEDIATE')
    try:
        if install_schema:
            for sql in SCHEMA:db.execute(sql.replace('CREATE TABLE ','CREATE TABLE IF NOT EXISTS ',1))
        sources=db.execute('SELECT * FROM native_npc_display_sources ORDER BY id').fetchall()
        stored=db.execute('SELECT * FROM native_npc_display_rows ORDER BY npc_key').fetchall()
        inserted=not sources and not stored
        if inserted:
            db.execute('INSERT INTO native_npc_display_sources VALUES(?,?,?,?,?,?,?,?,?,?,?)',source_row())
            db.executemany('INSERT INTO native_npc_display_rows VALUES(?,?,?,?,?,?)',rows)
        require(db.execute('SELECT * FROM native_npc_display_sources ORDER BY id').fetchall()==[source_row()],'NPC source conflict')
        require(db.execute('SELECT * FROM native_npc_display_rows ORDER BY npc_key').fetchall()==rows,'NPC rows conflict/readback')
        require(db.execute('PRAGMA quick_check').fetchone()==('ok',),'NPC database integrity')
        db.commit();return {'rows':4043,'inserted':4043 if inserted else 0,'dataset_sha256':DATASET_SHA,'authority':'SOURCE_DISPLAY_ONLY','player_rows_written':0}
    except BaseException:db.rollback();raise

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--database',type=Path,required=True)
    p.add_argument('--client',type=Path,default=ROOT.parent/'God2');p.add_argument('--memory-receipt',type=Path,default=ROOT/'artifacts/research/live-memory-references-20260927-02/memory-result.json');p.add_argument('--install-schema',action='store_true');a=p.parse_args()
    dbpath=a.database.resolve();require(dbpath.is_file() and not dbpath.is_relative_to(a.client.resolve()),'NPC explicit existing non-client database required')
    with closing(sqlite3.connect(dbpath.as_uri()+'?mode=rw',uri=True)) as db:print(json.dumps(install(db,a.client,a.memory_receipt,a.install_schema),sort_keys=True))
