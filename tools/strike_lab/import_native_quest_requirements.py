"""Import native ACTMIS display pairs, not authoritative quest conditions."""
import hashlib
import struct
from . import current_quest_requirements as native

DATASET='current-actmis-display-v1'
SOURCE_ROW=(DATASET,native.SOURCE,native.SOURCE_SHA,native.DECODED_SHA,native.IMAGE_SHA,
            'ACTMIS','0x58780','0xb9f8d',169)


def import_catalog(db,client):
    _,table=native.evidence(client=client)
    records=[]
    for row in table['records']:
        fields=[bytes.fromhex(f) for f in row['raw_fields_hex']]
        serial=int(fields[0]);raw=b','.join(fields)
        pairs=[(int(fields[i]),int(fields[i+1])) for i in (2,4,6,8)]
        if not 1<=serial<=169 or any(not 0<=key<=65535 or not 0<=qty<=255 for key,qty in pairs):
            raise ValueError('ACTMIS source bounds changed')
        records.append((DATASET,serial,row['source_line'],hashlib.sha256(raw).hexdigest(),raw,
                        b''.join(struct.pack('<HB',key,qty) for key,qty in pairs)))
    records.sort(key=lambda r:r[1])
    if [r[1] for r in records]!=list(range(1,170)):
        raise ValueError('ACTMIS keys incomplete')
    if db.in_transaction:raise ValueError('ACTMIS import requires its own transaction')
    db.execute('PRAGMA foreign_keys=ON');db.execute('BEGIN IMMEDIATE')
    try:
        if db.execute('SELECT name FROM schema_migrations WHERE version=15').fetchall()!=[('native_quest_requirement_display',)]:
            raise ValueError('Apply ACTMIS display migration first')
        source=db.execute('SELECT * FROM native_data_sources WHERE dataset_id=?',(DATASET,)).fetchall()
        stored=db.execute('SELECT * FROM native_quest_requirement_display WHERE dataset_id=? ORDER BY serial',(DATASET,)).fetchall()
        if source:
            if source!=[SOURCE_ROW] or stored!=records:raise ValueError('Conflicting ACTMIS import')
        else:
            if stored:raise ValueError('Orphaned ACTMIS display records')
            db.execute('INSERT INTO native_data_sources VALUES(?,?,?,?,?,?,?,?,?)',SOURCE_ROW)
            db.executemany('INSERT INTO native_quest_requirement_display VALUES(?,?,?,?,?,?)',records)
        if db.execute('SELECT * FROM native_quest_requirement_display WHERE dataset_id=? ORDER BY serial',(DATASET,)).fetchall()!=records:
            raise ValueError('ACTMIS readback mismatch')
        if db.execute('PRAGMA foreign_key_check').fetchone():raise ValueError('Foreign key violation')
        db.commit()
        return dict(dataset=DATASET,rows=169,inserted=0 if source else 169,authority='DISPLAY_ONLY')
    except BaseException:
        db.rollback();raise
