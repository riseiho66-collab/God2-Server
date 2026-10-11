"""Promote E3/COM support after own-client mixed-family acceptance; preserve saves."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
from tools.operations import native_quest_catalog_release as base
from tools.strike_lab import import_native_pet1_metadata as catalog

CANDIDATE=base.ROOT/'build-town-visibility/Release/god2-server-native-results.exe'
RECEIPT=base.ROOT/'artifacts/playtests/private-pet1-mixed-20260927-02/run-result.json'
CACHE=base.ROOT/'artifacts/research/native-pet1-20260927/records.json'
CLIENT_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'

def require(v,m):
    if not v:raise ValueError(m)
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def read(path):return json.loads(path.read_text('utf-8'))

def unchanged(before,after):
    a,b=base.snapshot(before),base.snapshot(after)
    require(set(b)-set(a)=={'native_pet1_metadata'}-set(a),'Unexpected schema additions')
    require(a['schema_migrations'][0]==b['schema_migrations'][0] and
        all(r in b['schema_migrations'][1] for r in a['schema_migrations'][1]),'Old migration history changed')
    for name in a:
        if name=='schema_migrations':continue
        if name=='character_pet2_slots':
            require(a[name][1]==b[name][1],'Owned shared-slot bytes/revisions/provenance changed')
            continue # Schema37 deliberately broadens stats CHECK, same capacity.
        require(a[name]==b.get(name),'Existing state changed: '+name)
    # Rebuilding the shared table must not silently discard local custom indexes/triggers.
    with closing(sqlite3.connect(before.resolve().as_uri()+'?mode=ro',uri=True)) as old:
        objects=old.execute("select type,name,sql from sqlite_master where tbl_name='character_pet2_slots' and sql is not null and type!='table'").fetchall()
        require(not objects,'Unmanaged owned-slot indexes/triggers require migration qualification')

def verify_sources(database):
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        require(db.execute('select * from native_pet1_metadata order by metadata_key').fetchall()==catalog.cached(CACHE),'Formal COM rows differ')
        require(db.execute('select max(version) from schema_migrations').fetchone()==(37,),'Expected schema37')
        require(db.execute('pragma quick_check').fetchone()==('ok',),'Database integrity failed')
        require(db.execute('pragma foreign_key_check').fetchone() is None,'Foreign key failure')

def qualify():
    receipt=read(RECEIPT)
    require(receipt['accepted'] and receipt['server_sha256']==base.sha(CANDIDATE),'Same candidate acceptance missing')
    require(all(receipt[k] for k in ('source_db_unchanged','live_client_unchanged','private_client_unchanged')),'Fixture preservation failed')
    require(receipt['ui']['desktop_before']==receipt['ui']['desktop_after']==receipt['ui']['desktop_final'],'Desktop changed')
    require(receipt['ui']['mixed_pet_generations']==dict(accepted=True,shared_capacity=3,transfers=5,opposite_caches_cleared=True),'Mixed family acceptance incomplete')
    require(receipt['pet1_import']['rows']==2070 and len(receipt['ui']['stages'])==5,'COM import/transfers missing')
    require(base.sha(base.CLIENT)==CLIENT_SHA,'Current client changed')
    return receipt

def stage(release):
    qualify();rows=catalog.cached(CACHE);release.mkdir(parents=True,exist_ok=False)
    cfg=read(base.CONFIG);database=Path(cfg['database']['path'])
    base.backup(database,release/'accounts.before.db');base.backup(database,release/'town-diagnostic-accounts.db')
    shutil.copy2(base.ACTIVE,release/'god2-server.before.exe');shutil.copy2(CANDIDATE,release/'god2-server.candidate.exe')
    shutil.copy2(base.CONFIG,release/'server-config.before.json')
    cfg['database']['path']=str(release/'town-diagnostic-accounts.db');cfg['logging']['file']=str(release/'migration.log')
    save(release/'stage-config.json',cfg)
    subprocess.run([str(CANDIDATE),'--config',str(release/'stage-config.json'),'--migrate-only'],cwd=base.ROOT,
        check=True,capture_output=True,creationflags=base.FLAGS,timeout=30)
    imported=catalog.install(release/'town-diagnostic-accounts.db',rows)
    unchanged(release/'accounts.before.db',release/'town-diagnostic-accounts.db');verify_sources(release/'town-diagnostic-accounts.db')
    info=dict(state='STAGED',live_database=str(database),old_server_sha256=base.sha(base.ACTIVE),candidate_sha256=base.sha(CANDIDATE),
        config_sha256=base.sha(base.CONFIG),client_sha256=CLIENT_SHA,com_cache_sha256=catalog.CACHE_SHA,
        com_import=imported,client_receipt=str(RECEIPT),scope='COM definitions and owned E3/FB shared-cell route; no acquisitions or growth formulas')
    save(release/'manifest.json',info);return info

def verify(release):
    info=read(release/'manifest.json');database=Path(info['live_database'])
    require(base.sha(base.ACTIVE)==info['candidate_sha256'] and base.sha(base.CONFIG)==info['config_sha256'] and
        base.sha(base.CLIENT)==info['client_sha256'],'Managed identity changed')
    verify_sources(database)
    require(read(release/'player-state-verification.json')==dict(all_existing_player_rows_unchanged=True,
        all_other_player_schemas_unchanged=True,schema_history_preserved=True,phase='STOPPED_BEFORE_START',pet_instances_granted=0),
        'Stopped phase preservation missing')
    result=dict(service_pid=base.listener(allow_players=True),schema=37,native_com_rows=2070,
        client_unchanged=True,config_unchanged=True,pet_instances_granted=0,shared_pet_capacity=3,
        original_growth_formula_verified=False)
    save(release/'verification.json',result);return result

def apply(release):
    info=read(release/'manifest.json');database=Path(info['live_database'])
    require(info['state']=='STAGED','Stage before apply')
    require(base.sha(base.ACTIVE)==info['old_server_sha256'] and base.sha(base.CONFIG)==info['config_sha256'] and
        base.sha(base.CLIENT)==info['client_sha256'],'Identities changed since staging')
    require(base.snapshot(database)==base.snapshot(release/'accounts.before.db'),'Saves changed; restage')
    candidate=release/'god2-server.candidate.exe';require(base.sha(candidate)==info['candidate_sha256'],'Candidate changed')
    rows=catalog.cached(CACHE);pid=base.listener();base.stop(pid);started=False;startup_snapshot=None
    try:
        require(base.snapshot(database)==base.snapshot(release/'accounts.before.db'),'Saves changed during stop')
        subprocess.run([str(candidate),'--config',str(base.CONFIG),'--migrate-only'],cwd=base.ROOT,
            check=True,capture_output=True,creationflags=base.FLAGS,timeout=30)
        catalog.install(database,rows);unchanged(release/'accounts.before.db',database);verify_sources(database)
        save(release/'player-state-verification.json',dict(all_existing_player_rows_unchanged=True,
            all_other_player_schemas_unchanged=True,schema_history_preserved=True,phase='STOPPED_BEFORE_START',pet_instances_granted=0))
        startup_snapshot=base.snapshot(database);shutil.copy2(candidate,base.ACTIVE);base.start()
        base.powershell("$deadline=(Get-Date).AddSeconds(15); do {Start-Sleep -Milliseconds 300; $r=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $r.Count -and (Get-Date) -lt $deadline); if($r.Count -ne 1){throw 'Managed server did not listen'}")
        started=True;result=verify(release);info['state']='INSTALLED';save(release/'manifest.json',info);return result
    except BaseException:
        if started or (startup_snapshot is not None and base.snapshot(database)!=startup_snapshot):
            info['state']='VERIFY_FAILED_RUNNING_SAVES_PRESERVED';save(release/'manifest.json',info);raise
        try:base.stop(base.listener(allow_players=True))
        except Exception:pass
        base.backup(release/'accounts.before.db',database);shutil.copy2(release/'god2-server.before.exe',base.ACTIVE);base.start();raise

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=('stage','apply','verify'));ap.add_argument('--name',required=True)
    args=ap.parse_args();require(args.name.startswith('native-pet1-') and '/' not in args.name and '\\' not in args.name,'Invalid release directory')
    release=base.ROOT/'artifacts/releases'/args.name
    print(json.dumps({'stage':stage,'apply':apply,'verify':verify}[args.mode](release)))
