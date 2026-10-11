"""Pinned native EQU/TEQ definitions, not player instances or final combat rules."""
import argparse,hashlib,json,sqlite3,struct
from contextlib import closing
from pathlib import Path
from .recover_combat_rules import CLIENT,IMAGE,IMAGE_SHA256
from .omega_assets import decode_csvz

ROOT=Path(__file__).resolve().parents[2]
SOURCE='Data2/Patch/Comm/gamedata.csvZ'
SOURCE_SHA='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
CLIENT_EXE_SHA='c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575'
DECODED_SHA='75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
AUTHORITY='NATIVE_PARSED_DEFINITION_ONLY'
COUNTS={'EQU':692,'TEQ':662}
ORIGINAL=ROOT/'artifacts/capture_work/host-20260918-1430/client'/SOURCE
RECORDS=ROOT/'artifacts/research/native-armor-20261002/records.json'
CURRENT_SOURCE_SHA='ef297a84e828537c4a18c5cf0be3d1c15bc26d5d2f25850ce9f2f030bdb58fa2'
CATALOG_SHA='29d1de3729c843571c3a7bc117beb12289bd7110932ec45fc5d846b627282efe'
SCHEMA=(
'''CREATE TABLE native_armor_sources (
 family TEXT PRIMARY KEY CHECK(family IN ('EQU','TEQ')),
 source_file TEXT NOT NULL CHECK(source_file='Data2/Patch/Comm/gamedata.csvZ'),
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64),
 decoded_sha256 TEXT NOT NULL CHECK(length(decoded_sha256)=64),
 native_image_sha256 TEXT NOT NULL CHECK(length(native_image_sha256)=64),
 loader_rva TEXT NOT NULL CHECK(loader_rva='0x59420'),
 lookup_rva TEXT NOT NULL CHECK(lookup_rva='0x59a60'),
 row_count INTEGER NOT NULL CHECK(row_count IN (662,692)),
 encoding TEXT NOT NULL CHECK(encoding='CP950'),
 authority TEXT NOT NULL CHECK(authority='NATIVE_PARSED_DEFINITION_ONLY')
)''',
'''CREATE TABLE native_armor_rows (
 family TEXT NOT NULL REFERENCES native_armor_sources(family),
 item_id INTEGER NOT NULL CHECK(item_id BETWEEN 1 AND 32767),
 source_record_index INTEGER NOT NULL CHECK(source_record_index BETWEEN 0 AND 691),
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
TABLES=('native_armor_sources','native_armor_rows')
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
    """Build pin and unchanged EQU/TEQ rows, independent of custom-skill edits."""
    from . import recover_companion_growth as growth
    require(Path(client).resolve()==CLIENT.resolve(),'Only current pinned client supported')
    require(sha((Path(client)/'God2.exe').read_bytes())==CLIENT_EXE_SHA,'Armor current client identity changed')
    original=ORIGINAL.read_bytes()
    require(sha(original)==SOURCE_SHA,'Armor original source identity changed')
    decoded=decode_csvz(original)
    require(sha(decoded)==DECODED_SHA,'Armor original decoded source changed')
    current=(Path(client)/SOURCE).read_bytes()
    require(sha(current)==CURRENT_SOURCE_SHA,'Armor current source identity changed')
    first=growth.parse_sections(decoded,tuple(COUNTS))
    last=growth.parse_sections(decode_csvz(current),tuple(COUNTS))
    for family,count in COUNTS.items():
        left=first[family]['records'];right=last[family]['records']
        require(len(left)==len(right)==count,'Armor source denominator changed')
        require([r['raw_record_hex'] for r in left]==[r['raw_record_hex'] for r in right],
                'Armor current rows differ from original source')
    require(sha(IMAGE.read_bytes())==IMAGE_SHA256,'Armor native image identity changed')

def validate_records(groups):
    require(isinstance(groups,(tuple,list)) and len(groups)==2,'Expected two armor record groups')
    require(all(isinstance(group,(tuple,list)) for group in groups),'Malformed armor cached groups')
    require(len(groups[0])==2 and len(groups[1])==1354,'Armor cached denominator changed')
    normalized=[]
    for group_index,group in enumerate(groups):
        rows=[]
        for row in group:
            require(isinstance(row,(tuple,list)) and len(row)==10,'Malformed armor cached row')
            types=([str]*7+[int,str,str] if group_index==0 else
                   [str,int,int,int,int,str,bytes,str,bytes,str])
            require(all(type(value) is expected for value,expected in zip(row,types)),
                    'Armor cached field type mismatch')
            rows.append(tuple(row))
        normalized.append(tuple(rows))
    result=tuple(normalized)
    require(fingerprint(result)==CATALOG_SHA,'Supplied native armor catalog pin mismatch')
    return result

def cached_records(path,client=CLIENT):
    validate_source(client)
    groups=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    require(isinstance(groups,list) and len(groups)==2,'Expected two armor record groups')
    require(all(isinstance(group,list) for group in groups),'Malformed armor cached groups')
    for row in groups[1]:
        require(isinstance(row,list) and len(row)==10,'Malformed armor cached row')
        for index in (6,8):
            require(type(row[index]) is str,'Expected hexadecimal armor BLOB')
            row[index]=bytes.fromhex(row[index])
    return validate_records(groups)

def pinned_records(client=CLIENT):
    # The independent new oracle executes every original definition and emits
    # this pinned cache; importer never generates player instance bytes.
    return cached_records(RECORDS,client)

def install(db):
    for name,ddl in zip(TABLES,SCHEMA):
        row=db.execute("select sql from sqlite_master where type='table' and name=?",(name,)).fetchone()
        if row:require(' '.join(row[0].split())==' '.join(ddl.split()),'Conflicting native armor schema')
        else:db.execute(ddl)

def import_catalog(db,client=CLIENT,*,records=None):
    require(not db.in_transaction,'Armor import requires its own transaction')
    validate_source(client)
    groups=validate_records(pinned_records(client) if records is None else records)
    db.execute('PRAGMA foreign_keys=ON');db.execute('BEGIN IMMEDIATE')
    try:
        install(db)
        read=lambda:tuple(tuple(db.execute('SELECT * FROM '+t+' ORDER BY '+o)) for t,o in zip(TABLES,ORDERS))
        before=read();present=any(before)
        require(not present or before==groups,'Conflicting/partial armor source; refusing overwrite')
        if not present:
            for table,rows in zip(TABLES,groups):db.executemany('INSERT INTO '+table+' VALUES('+','.join('?' for _ in rows[0])+')',rows)
        require(read()==groups,'Armor readback mismatch')
        require(db.execute('PRAGMA quick_check').fetchone()==('ok',) and db.execute('PRAGMA foreign_key_check').fetchone() is None,'Armor database integrity failed')
        db.commit();return {'source_rows':1354,'inserted':0 if present else 1354,'authority':AUTHORITY,'player_instances_created':0,'combat_rules_created':0}
    except BaseException:db.rollback();raise

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--database',type=Path,required=True)
    ap.add_argument('--records-cache',type=Path,help='Previously extracted native records; full pins still enforced')
    args=ap.parse_args()
    require(not args.database.resolve().is_relative_to(CLIENT.resolve()),'Refusing client-tree database')
    records=cached_records(args.records_cache) if args.records_cache else None
    with closing(sqlite3.connect(args.database)) as db:print(json.dumps(import_catalog(db,records=records)))
if __name__=='__main__':main()
