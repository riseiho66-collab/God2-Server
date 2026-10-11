"""Import all mission definitions/daily source rows, never invent quest rules."""
import hashlib
from . import import_native_quests as missions

DAILY_SHA='4a347d56706946d7004b2bd2118500ffc60844628fa461862b2f6d5320a90e54'
DAILY_DECODED_SHA='2848b95b0af99eac10ca4dff61a5533c13917127c4738039e263c60a1be45eaf'

def pinned_records(client):
    catalog=missions.build_catalog(client)
    mission_table=catalog['tables']['missions'];daily_table=catalog['tables']['daily']
    if (mission_table['source_sha256'],mission_table['decoded_sha256'])!=(missions.SOURCE_SHA,missions.DECODED_SHA):
        raise ValueError('Mission source changed')
    if (daily_table['source_sha256'],daily_table['decoded_sha256'])!=(DAILY_SHA,DAILY_DECODED_SHA):
        raise ValueError('Daily source changed')
    if catalog['validation']['structural_issues']:raise ValueError('Malformed quest source')
    definitions=[];daily=[]
    for row in mission_table['records']:
        fields=[bytes.fromhex(f) for f in row['raw_fields_hex']]
        if not fields[0]:continue
        raw=b','.join(fields)
        if hashlib.sha256(raw).hexdigest()!=row['source_record_sha256']:raise ValueError('Mission row hash mismatch')
        definitions.append((missions.DATASET,int(fields[0]),int(fields[2]),row['source_line'],row['source_record_sha256'],raw,fields[1]))
    for index,row in enumerate(daily_table['records']):
        fields=[bytes.fromhex(f) for f in row['raw_fields_hex']];raw=b','.join(fields)
        if hashlib.sha256(raw).hexdigest()!=row['source_record_sha256']:raise ValueError('Daily row hash mismatch')
        daily.append((index,daily_table['source_file'],DAILY_SHA,DAILY_DECODED_SHA,row['source_line'],row['source_record_sha256'],raw,len(fields),'SOURCE_FIELDS_ONLY'))
    if len(definitions)!=418 or len(daily)!=85:raise ValueError('Incomplete native source')
    return definitions,daily

def import_catalog(db,client):
    definitions,daily=pinned_records(client)
    if db.in_transaction:raise ValueError('Source import requires its own transaction')
    db.execute('PRAGMA foreign_keys=ON');db.execute('BEGIN IMMEDIATE')
    try:
        if db.execute('select name from schema_migrations where version=23').fetchone()!=('native_quest_source_catalog',):
            raise ValueError('Apply quest source migration first')
        if db.execute('select * from native_data_sources where dataset_id=?',(missions.DATASET,)).fetchall()!=[missions.SOURCE_ROW]:
            raise ValueError('Qualified mission description catalog required')
        inserted={}
        for table,order,rows in (('native_quest_definitions','mission_index',definitions),('native_daily_quest_source','record_index',daily)):
            stored=db.execute('select * from '+table+' order by '+order).fetchall()
            if stored and stored!=rows:raise ValueError('Conflicting '+table+'; refusing overwrite')
            if not stored:db.executemany('insert into '+table+' values('+','.join('?' for _ in rows[0])+')',rows)
            if db.execute('select * from '+table+' order by '+order).fetchall()!=rows:raise ValueError('Readback mismatch')
            inserted[table]=0 if stored else len(rows)
        if db.execute('pragma foreign_key_check').fetchone() or db.execute('pragma quick_check').fetchone()!=('ok',):
            raise ValueError('Quest source DB integrity failed')
        db.commit()
        return dict(mission_definitions=418,daily_source_records=85,inserted=inserted,gameplay_rules=0,authority='SOURCE_FIELDS_ONLY')
    except BaseException:
        db.rollback();raise
