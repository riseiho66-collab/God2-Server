"""Import current native NCP metadata, never owned pets or combat/growth stats.

Original item parser59420, key index59A20, lookup59A60 and icon consumer9B720
execute unchanged against the pinned current source. GOD's separately
qualified native ItemType selector0 is in import_native_deity_metadata.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
from .current_item_metadata import NativeItemMetadata

SOURCE='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'

class CompanionMetadata(NativeItemMetadata):
    ITEM_SECTIONS=('NCP',)

def extract():
    native=CompanionMetadata()
    source=native.sections['NCP']['records']
    if len(source)!=1165:raise ValueError('Current NCP denominator changed')
    rows=[]
    for index,row in enumerate(source):
        parsed=native.item_row('NCP',index)
        raw=bytes.fromhex(row['raw_record_hex'])
        if not 28001<=parsed['key']<0x7f58 or len(parsed['record'])!=396:
            raise ValueError('Native NCP row outside recovered boundaries')
        rows.append(('NCP',parsed['key'],SOURCE,parsed['source_line'],raw,
                     hashlib.sha256(raw).hexdigest(),parsed['record']))
    if len({row[1] for row in rows})!=len(rows):raise ValueError('Duplicate native NCP key')
    return rows

def install(database,rows):
    database=database.resolve(strict=True)
    with closing(sqlite3.connect(database)) as db:
        db.execute('pragma foreign_keys=on')
        if db.execute('pragma quick_check').fetchone()!=('ok',):raise ValueError('Database integrity failed')
        # Import may only change this current metadata table. Conflicting prior
        # imports are rejected, not replaced; player tables are never touched.
        db.execute('begin immediate')
        try:
            existing=db.execute('select * from native_companion_metadata where family=? order by metadata_key',('NCP',)).fetchall()
            ordered=sorted(rows,key=lambda row:row[1])
            if existing and existing!=ordered:raise ValueError('Existing NCP import differs')
            if not existing:
                db.executemany('insert into native_companion_metadata values(?,?,?,?,?,?,?)',ordered)
            if db.execute('select * from native_companion_metadata where family=? order by metadata_key',('NCP',)).fetchall()!=ordered:
                raise ValueError('Native NCP import readback mismatch')
            db.commit()
        except BaseException:
            db.rollback();raise
    return {'rows':len(rows),'source_sha256':SOURCE,'player_instances_created':0,
            'idempotent':bool(existing),'database':str(database)}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--database',type=Path,required=True)
    ap.add_argument('--report',type=Path)
    args=ap.parse_args();result=install(args.database,extract())
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))

if __name__=='__main__':main()
