"""Import34 current GOD definitions, never grant owned instances or formulas."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
from .current_deity_metadata import NativeDeityMetadata
from .import_companion_metadata import SOURCE

def extract():
    native=NativeDeityMetadata();source=native.sections['GOD']['records']
    if len(source)!=34:raise ValueError('Current GOD definition count changed')
    rows=[]
    for ordinal,row in enumerate(source):
        parsed=native.item_row('GOD',ordinal);raw=bytes.fromhex(row['raw_record_hex'])
        if parsed['key']!=2801+ordinal or parsed['selector']!=0 or len(parsed['record'])!=396:
            raise ValueError('Original GOD record binding changed')
        rows.append(('GOD',parsed['key'],SOURCE,parsed['source_line'],raw,
                     hashlib.sha256(raw).hexdigest(),parsed['record']))
    return rows,native.category_proof()

def validate(rows):
    ordered=sorted(rows,key=lambda row:row[1])
    if len(ordered)!=34:raise ValueError('Incomplete GOD definitions')
    for ordinal,row in enumerate(ordered):
        if len(row)!=7 or row[:3]!=('GOD',2801+ordinal,SOURCE) or not isinstance(row[3],int) or row[3]<=0:
            raise ValueError('GOD source identity invalid')
        if not 1<=len(row[4])<=4095 or hashlib.sha256(row[4]).hexdigest()!=row[5] or len(row[6])!=396:
            raise ValueError('GOD original bytes invalid')
    return ordered

def install_transaction(db,rows):
    """Caller owns transaction so promotion can check all tables before commit."""
    if not db.in_transaction:raise ValueError('GOD import requires a transaction')
    ordered=validate(rows)
    existing=db.execute("select * from native_companion_metadata where family='GOD' order by metadata_key").fetchall()
    if existing and existing!=ordered:raise ValueError('Existing GOD import differs')
    if not existing:db.executemany('insert into native_companion_metadata values(?,?,?,?,?,?,?)',ordered)
    if db.execute("select * from native_companion_metadata where family='GOD' order by metadata_key").fetchall()!=ordered:
        raise ValueError('GOD import readback mismatch')
    return dict(rows=34,source_sha256=SOURCE,player_instances_created=0,idempotent=bool(existing))

def install(database,rows):
    with closing(sqlite3.connect(Path(database).resolve(strict=True))) as db:
        db.execute('pragma foreign_keys=on');db.execute('begin immediate')
        try:
            result=install_transaction(db,rows)
            db.commit()
        except BaseException:db.rollback();raise
    return result

def save(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps([[*row[:4],row[4].hex(),row[5],row[6].hex()] for row in validate(rows)],indent=2)+'\n',encoding='utf-8')

def cached(path):
    data=Path(path).read_bytes()
    # Pin installed cache only after original extraction; callers must not
    # turn a modified raw/parsed record into original authority.
    if hashlib.sha256(data).hexdigest()!=CACHE_SHA:raise ValueError('Native GOD cache hash mismatch')
    return validate([(*row[:4],bytes.fromhex(row[4]),row[5],bytes.fromhex(row[6])) for row in json.loads(data)])

CACHE_SHA='ed8c71d8bc2d276b4534df1389138f98096fce78f9128c451f9d110faba484df'

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();rows,proof=extract();save(args.output,rows)
    args.output.with_name('category-binding.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(rows=34,catalog_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),player_instances_created=0)))
