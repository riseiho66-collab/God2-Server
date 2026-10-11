"""Current COM definitions via unchanged native loader; no owned grants/growth."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
from .current_item_metadata import NativeItemMetadata
from .import_companion_metadata import SOURCE
CACHE_SHA='48779aff006267371dcbce6c7813c521025496c82ad69e7c083bdcb8b2a204f2'

class Pet1Metadata(NativeItemMetadata):
    ITEM_SECTIONS=('COM',)

def extract():
    native=Pet1Metadata();source=native.sections['COM']['records']
    if len(source)!=2070:raise ValueError('Current COM denominator changed')
    rows=[]
    for index,row in enumerate(source):
        parsed=native.item_row('COM',index);raw=bytes.fromhex(row['raw_record_hex'])
        if parsed['key']!=24001+index or parsed['selector']!=32 or len(parsed['record'])!=396:
            raise ValueError('Native COM key/type/record contract changed')
        rows.append(('COM',parsed['key'],SOURCE,parsed['source_line'],raw,hashlib.sha256(raw).hexdigest(),parsed['record']))
    return rows

def validate(rows):
    ordered=sorted(rows,key=lambda row:row[1])
    if len(ordered)!=2070:raise ValueError('Incomplete COM catalog')
    for index,row in enumerate(ordered):
        if len(row)!=7 or row[:3]!=('COM',24001+index,SOURCE) or not isinstance(row[3],int) or row[3]<=0:
            raise ValueError('COM identity/source invalid')
        if not 1<=len(row[4])<=4095 or hashlib.sha256(row[4]).hexdigest()!=row[5] or len(row[6])!=396:
            raise ValueError('COM bytes invalid')
    return ordered

def install(database,rows):
    ordered=validate(rows)
    with closing(sqlite3.connect(Path(database).resolve(strict=True))) as db:
        db.execute('pragma foreign_keys=on');db.execute('begin immediate')
        try:
            existing=db.execute('select * from native_pet1_metadata order by metadata_key').fetchall()
            if existing and existing!=ordered:raise ValueError('Existing COM import differs')
            if not existing:db.executemany('insert into native_pet1_metadata values(?,?,?,?,?,?,?)',ordered)
            if db.execute('select * from native_pet1_metadata order by metadata_key').fetchall()!=ordered:
                raise ValueError('COM readback mismatch')
            db.commit()
        except BaseException:db.rollback();raise
    return dict(rows=len(ordered),source_sha256=SOURCE,player_instances_created=0,idempotent=bool(existing))

def save(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps([[*row[:4],row[4].hex(),row[5],row[6].hex()] for row in validate(rows)],indent=2)+'\n',encoding='utf-8')

def cached(path):
    data=Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest()!=CACHE_SHA:raise ValueError('Original native COM cache hash mismatch')
    rows=json.loads(data)
    return validate([(*row[:4],bytes.fromhex(row[4]),row[5],bytes.fromhex(row[6])) for row in rows])

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();rows=extract();save(args.output,rows)
    print(json.dumps(dict(rows=len(rows),catalog_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),player_instances_created=0)))
