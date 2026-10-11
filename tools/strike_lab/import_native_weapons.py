"""Pinned native WPN/TWP definitions, not player instances or final combat rules."""
import argparse,hashlib,json,sqlite3,struct
from contextlib import closing
from pathlib import Path
from .current_item_metadata import NativeItemMetadata
from .recover_combat_rules import CLIENT,IMAGE,IMAGE_SHA256
from .omega_assets import decode_csvz

ROOT=Path(__file__).resolve().parents[2]
SOURCE='Data2/Patch/Comm/gamedata.csvZ'
SOURCE_SHA='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
CLIENT_EXE_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
DECODED_SHA='75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
AUTHORITY='NATIVE_PARSED_DEFINITION_ONLY'
COUNTS={'WPN':630,'TWP':629}
CATALOG_SHA='1a6e35c37950d5edada081b184c6b7f6d1f101929d4ccf46004747c8740cde26'
SCHEMA=(
'''CREATE TABLE native_weapon_sources (
 family TEXT PRIMARY KEY CHECK(family IN ('WPN','TWP')),
 source_file TEXT NOT NULL CHECK(source_file='Data2/Patch/Comm/gamedata.csvZ'),
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64),
 decoded_sha256 TEXT NOT NULL CHECK(length(decoded_sha256)=64),
 native_image_sha256 TEXT NOT NULL CHECK(length(native_image_sha256)=64),
 loader_rva TEXT NOT NULL CHECK(loader_rva='0x59420'),
 lookup_rva TEXT NOT NULL CHECK(lookup_rva='0x59a60'),
 row_count INTEGER NOT NULL CHECK(row_count IN (629,630)),
 encoding TEXT NOT NULL CHECK(encoding='CP950'),
 authority TEXT NOT NULL CHECK(authority='NATIVE_PARSED_DEFINITION_ONLY')
)''',
'''CREATE TABLE native_weapon_rows (
 family TEXT NOT NULL REFERENCES native_weapon_sources(family),
 item_id INTEGER NOT NULL CHECK(item_id BETWEEN 1 AND 32767),
 source_record_index INTEGER NOT NULL CHECK(source_record_index BETWEEN 0 AND 629),
 source_line INTEGER NOT NULL CHECK(source_line>0),
 decoded_offset INTEGER NOT NULL CHECK(decoded_offset>=0),
 record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64),
 raw_record BLOB NOT NULL CHECK(typeof(raw_record)='blob' AND length(raw_record) BETWEEN 1 AND 4095),
 parsed_sha256 TEXT NOT NULL CHECK(length(parsed_sha256)=64),
 parsed_record BLOB NOT NULL CHECK(typeof(parsed_record)='blob' AND length(parsed_record)=396),
 authority TEXT NOT NULL CHECK(authority='NATIVE_PARSED_DEFINITION_ONLY'),
 PRIMARY KEY(family,item_id),
 UNIQUE(item_id),
 UNIQUE(family,source_record_index)
)''')
TABLES=('native_weapon_sources','native_weapon_rows')
ORDERS=('family','family,item_id')

def require(value,message):
    if not value:raise ValueError(message)
def sha(value):return hashlib.sha256(value).hexdigest()
def fingerprint(groups):
    digest=hashlib.sha256()
    for rows in groups:
        for row in rows:
            for value in row:
                raw=value if isinstance(value,bytes) else str(value).encode('ascii')
                digest.update(struct.pack('<I',len(raw)));digest.update(raw)
    return digest.hexdigest()

def validate_source(client=CLIENT):
    """A cached extraction cannot bypass the current input identity checks."""
    require(Path(client).resolve()==CLIENT.resolve(),'Only current pinned client supported')
    require(sha((Path(client)/'God2.exe').read_bytes())==CLIENT_EXE_SHA,'Weapon current client identity changed')
    raw=(Path(client)/SOURCE).read_bytes()
    require(sha(raw)==SOURCE_SHA,'Weapon source file identity changed')
    require(sha(decode_csvz(raw))==DECODED_SHA,'Weapon decoded source changed')
    require(sha(IMAGE.read_bytes())==IMAGE_SHA256,'Weapon native image identity changed')

def validate_records(groups):
    require(isinstance(groups,(tuple,list)) and len(groups)==2,'Expected two weapon record groups')
    require(all(isinstance(group,(tuple,list)) for group in groups),'Malformed weapon cached groups')
    require(len(groups[0])==2 and len(groups[1])==1259,'Weapon cached denominator changed')
    normalized=[]
    for group_index,group in enumerate(groups):
        rows=[]
        for row in group:
            require(isinstance(row,(tuple,list)) and len(row)==10,'Malformed weapon cached row')
            types=([str]*7+[int,str,str] if group_index==0 else
                   [str,int,int,int,int,str,bytes,str,bytes,str])
            require(all(type(value) is expected for value,expected in zip(row,types)),
                    'Weapon cached field type mismatch')
            rows.append(tuple(row))
        normalized.append(tuple(rows))
    result=tuple(normalized)
    require(fingerprint(result)==CATALOG_SHA,'Supplied native weapon catalog pin mismatch')
    return result

def cached_records(path,client=CLIENT):
    validate_source(client)
    groups=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    require(isinstance(groups,list) and len(groups)==2,'Expected two weapon record groups')
    require(all(isinstance(group,list) for group in groups),'Malformed weapon cached groups')
    for row in groups[1]:
        require(isinstance(row,list) and len(row)==10,'Malformed weapon cached row')
        for index in (6,8):
            require(type(row[index]) is str,'Expected hexadecimal weapon BLOB')
            row[index]=bytes.fromhex(row[index])
    return validate_records(groups)

def pinned_records(client=CLIENT):
    require(Path(client).resolve()==CLIENT.resolve(),'Only current pinned client supported')
    native=NativeItemMetadata()
    require(sha(native.decoded)==DECODED_SHA,'Weapon decoded source changed')
    sources=[];rows=[]
    for family in sorted(COUNTS):
        original=native.sections[family]['records'];count=COUNTS[family]
        require(len(original)==count,'Weapon source denominator changed')
        sources.append((family,SOURCE,SOURCE_SHA,DECODED_SHA,IMAGE_SHA256,'0x59420','0x59a60',count,'CP950',AUTHORITY))
        for ordinal,source in enumerate(original):
            parsed=native.item_row(family,ordinal)
            raw=bytes.fromhex(source['raw_record_hex']).rstrip(b'\r\n');offset=source['decoded_offset']
            require(len(parsed['record'])==396 and native.decoded[offset:offset+len(raw)]==raw and
                    parsed['source_line']==source['source_line'],'Weapon native source/record mismatch')
            raw.decode('cp950',errors='strict')
            rows.append((family,parsed['key'],ordinal,parsed['source_line'],offset,sha(raw),raw,sha(parsed['record']),parsed['record'],AUTHORITY))
    require(len({row[1] for row in rows})==1259,'Weapon key collision')
    groups=(tuple(sources),tuple(sorted(rows,key=lambda r:(r[0],r[1]))))
    require(fingerprint(groups)==CATALOG_SHA,'Weapon complete native catalog pin mismatch')
    return groups

def install(db):
    for name,ddl in zip(TABLES,SCHEMA):
        row=db.execute("select sql from sqlite_master where type='table' and name=?",(name,)).fetchone()
        if row:require(' '.join(row[0].split())==' '.join(ddl.split()),'Conflicting native weapon schema')
        else:db.execute(ddl)

def import_catalog(db,client=CLIENT,*,records=None):
    require(not db.in_transaction,'Weapon import requires its own transaction')
    validate_source(client)
    groups=validate_records(pinned_records(client) if records is None else records)
    db.execute('PRAGMA foreign_keys=ON');db.execute('BEGIN IMMEDIATE')
    try:
        install(db)
        read=lambda:tuple(tuple(db.execute('SELECT * FROM '+t+' ORDER BY '+o)) for t,o in zip(TABLES,ORDERS))
        before=read();present=any(before)
        require(not present or before==groups,'Conflicting/partial weapon source; refusing overwrite')
        if not present:
            for table,rows in zip(TABLES,groups):db.executemany('INSERT INTO '+table+' VALUES('+','.join('?' for _ in rows[0])+')',rows)
        require(read()==groups,'Weapon readback mismatch')
        require(db.execute('PRAGMA quick_check').fetchone()==('ok',) and db.execute('PRAGMA foreign_key_check').fetchone() is None,'Weapon database integrity failed')
        db.commit();return {'source_rows':1259,'inserted':0 if present else 1259,'authority':AUTHORITY,'player_instances_created':0,'combat_rules_created':0}
    except BaseException:db.rollback();raise

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--database',type=Path,required=True)
    ap.add_argument('--records-cache',type=Path,help='Previously extracted native records; full pins still enforced')
    args=ap.parse_args()
    require(not args.database.resolve().is_relative_to(CLIENT.resolve()),'Refusing client-tree database')
    records=cached_records(args.records_cache) if args.records_cache else None
    with closing(sqlite3.connect(args.database)) as db:print(json.dumps(import_catalog(db,records=records)))
if __name__=='__main__':main()
