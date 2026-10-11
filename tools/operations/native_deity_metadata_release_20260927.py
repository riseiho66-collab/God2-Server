"""Promote34 qualified GOD definitions atomically, preserving every saved row."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
from . import native_quest_catalog_release as base
from tools.strike_lab import import_native_deity_metadata as catalog

CACHE=base.ROOT/'artifacts/research/native-deity-metadata-20260927/records.json'
RECEIPT=base.ROOT/'artifacts/playtests/private-deity-templates-20260927-13/run-result.json'
CLIENT_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'

def require(value,message):
    if not value:raise ValueError(message)
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def read(path):return json.loads(path.read_text('utf-8'))

def qualify():
    r=read(RECEIPT);u=r['ui']
    require(r['accepted'] and r['server_sha256']==base.sha(base.ACTIVE),'Same running candidate acceptance required')
    require(all(r[k] for k in ('source_db_unchanged','live_client_unchanged','private_client_unchanged')),'Fixture/client changed')
    require(base.sha(base.CLIENT)==CLIENT_SHA,'Current client changed')
    require(u['desktop_before']==u['desktop_after']==u['desktop_final'],'Input desktop changed')
    require(u['deity_native_metadata']['definition_count']==34,'All native definitions required')
    require(u['deity_native_metadata']['owned']==[{'key':1,'name':'姜子牙'},{'key':2,'name':'鄧嬋玉'}],'Native owned names missing')
    stages=u['deity_native_selection']['stages']
    require([(s['control'],s['selection']) for s in stages]==[(41,[2,2]),(40,[1,3])],'Real C2S67 switching missing')
    require([s['portrait']['original_action_id'] for s in stages]==[1002,1001],'Native selection portraits missing')
    require(len(u['stages'])==5 and len(u['pet_native_icons']['stages'])==5,'Mixed companion regressions missing')
    require('NATIVE_CLIENT_DIAGNOSTIC' not in (RECEIPT.parent/'server.log').read_text('utf-8',errors='replace'),'Native diagnostic remains')

def snapshot(db):
    return {name:(sql,sorted(repr(row) for row in db.execute('select * from "'+name.replace('"','""')+'"')))
        for name,sql in db.execute("select name,sql from sqlite_master where type='table'").fetchall()}

def import_preserving_saves(database):
    rows=catalog.cached(CACHE)
    with closing(sqlite3.connect(database)) as db:
        db.execute('pragma foreign_keys=on');db.execute('begin immediate')
        try:
            before=snapshot(db);result=catalog.install_transaction(db,rows);after=snapshot(db)
            require(before.keys()==after.keys(),'Schema tables changed')
            for table in before:
                require(before[table][0]==after[table][0],'Table schema changed')
                if table!='native_companion_metadata':require(before[table]==after[table],f'Saved table changed: {table}')
            original=before['native_companion_metadata'][1]
            expected=sorted(set(original)|{repr(row) for row in rows})
            require(after['native_companion_metadata'][1]==expected,'Unexpected companion catalog change')
            require(db.execute('pragma quick_check').fetchone()==('ok',),'Database integrity failed')
            require(not db.execute('pragma foreign_key_check').fetchall(),'Foreign keys invalid')
            db.commit()
        except BaseException:db.rollback();raise
    return dict(**result,all_other_tables_and_schemas_unchanged=True,existing_catalog_rows_preserved=True)

def stage(release):
    qualify();release.mkdir(parents=True,exist_ok=False)
    database=Path(read(base.CONFIG)['database']['path'])
    base.backup(database,release/'accounts.before.db')
    base.backup(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    result=import_preserving_saves(release/'town-diagnostic-accounts.db')
    manifest=dict(state='STAGED',live_database=str(database),server_sha256=base.sha(base.ACTIVE),
        config_sha256=base.sha(base.CONFIG),client_sha256=CLIENT_SHA,receipt=str(RECEIPT),
        catalog_sha256=base.sha(CACHE),stage_import=result,
        scope='Native GOD definitions, owned restore/select/display contracts. No grants, growth or battle formulas.')
    save(release/'manifest.json',manifest);return manifest

def verify(release):
    info=read(release/'manifest.json');database=Path(info['live_database'])
    require(base.sha(base.ACTIVE)==info['server_sha256'] and base.sha(base.CONFIG)==info['config_sha256'] and
            base.sha(base.CLIENT)==info['client_sha256'],'Managed identity changed')
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        require(db.execute("select * from native_companion_metadata where family='GOD' order by metadata_key").fetchall()==catalog.cached(CACHE),'Live GOD catalog mismatch')
        counts={table:db.execute('select count(*) from '+table).fetchone()[0] for table in
                ('accounts','recovered_characters','character_deities','native_companion_metadata','native_pet1_metadata')}
        schema=db.execute('select max(version) from schema_migrations').fetchone()[0]
    result=dict(service_pid=base.listener(allow_players=True),schema=schema,counts=counts,god_definitions=34,
        instances_granted=0,client_unchanged=True,server_restart=False,
        transaction_preservation=read(release/'save-preservation.json'))
    save(release/'verification.json',result);return result

def apply(release):
    qualify();info=read(release/'manifest.json');require(info['state']=='STAGED','Stage first')
    require(base.sha(base.ACTIVE)==info['server_sha256'] and base.sha(base.CONFIG)==info['config_sha256'],'Managed identity changed')
    require(base.sha(CACHE)==info['catalog_sha256'],'Catalog changed')
    base.listener(allow_players=True)
    # Only append static catalog data. Validate all rows within the same write
    # transaction, so concurrent legitimate player writes are neither compared
    # with stale snapshots nor overwritten. Never restore an old player DB.
    result=import_preserving_saves(Path(info['live_database']))
    save(release/'save-preservation.json',result)
    info['state']='INSTALLED';save(release/'manifest.json',info)
    return verify(release)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=('stage','apply','verify'));ap.add_argument('--name',required=True)
    args=ap.parse_args();require(args.name.startswith('native-deity-metadata-') and '/' not in args.name and '\\' not in args.name,'Invalid release name')
    print(json.dumps({'stage':stage,'apply':apply,'verify':verify}[args.mode](base.ROOT/'artifacts/releases'/args.name)))
