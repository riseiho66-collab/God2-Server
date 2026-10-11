"""Install the current-client-qualified portrait guard without save migration."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
from . import native_quest_catalog_release as base

RECEIPT=base.ROOT/'artifacts/playtests/private-deity-portrait-20260927-04/run-result.json'
CANDIDATE=base.ROOT/'build-town-visibility/Release/god2-server-native-results.exe'
CLIENT_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'

def require(value,message):
    if not value:raise ValueError(message)
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def read(path):return json.loads(path.read_text('utf-8'))

def qualify():
    r=read(RECEIPT);u=r['ui']
    require(r['accepted'] and r['server_sha256']==base.sha(CANDIDATE),'Same candidate client acceptance required')
    require(all(r[k] for k in ('source_db_unchanged','live_client_unchanged','private_client_unchanged')),'Fixture/client changed')
    require(u['desktop_before']==u['desktop_after']==u['desktop_final'],'Input desktop changed')
    require(all(u['deity_native_portrait'][k]==u['deity_native_portrait_after'][k]
                for k in ('key','bank','action','bank_action_count','original_action_id','image_pointer')) and
            u['deity_native_portrait']['key']==101 and u['deity_native_portrait']['action']==34 and
            u['deity_native_portrait']['original_action_id']==1101,'Native deity portrait missing')
    require(len(u['stages'])==5 and len(u['pet_native_icons']['stages'])==5,'Mixed pet acceptance incomplete')
    require('NATIVE_CLIENT_DIAGNOSTIC' not in (RECEIPT.parent/'server.log').read_text('utf-8',errors='replace'),'Native diagnostic remains')
    require(base.sha(base.CLIENT)==CLIENT_SHA,'Current client changed')

def stage(release):
    qualify();release.mkdir(parents=True,exist_ok=False)
    config=read(base.CONFIG);database=Path(config['database']['path'])
    base.backup(database,release/'accounts.before.db');base.backup(database,release/'town-diagnostic-accounts.db')
    shutil.copy2(base.ACTIVE,release/'god2-server.before.exe');shutil.copy2(CANDIDATE,release/'god2-server.candidate.exe')
    shutil.copy2(base.CONFIG,release/'server-config.before.json')
    with closing(sqlite3.connect((release/'town-diagnostic-accounts.db').resolve().as_uri()+'?mode=ro',uri=True)) as db:
        require(db.execute('select max(version) from schema_migrations').fetchone()==(37,),'Unexpected schema')
        # Audit all stored IDs, never rename/delete player-owned instances.
        keys=db.execute('select character_id,row_key from character_deities').fetchall()
        require(all(1<=key<=34 or 101<=key<=108 for _,key in keys),'Unrenderable persisted deity needs explicit migration')
    config['database']['path']=str(release/'town-diagnostic-accounts.db');config['logging']['file']=str(release/'stage.log')
    save(release/'stage-config.json',config)
    subprocess.run([str(CANDIDATE),'--config',str(release/'stage-config.json'),'--migrate-only'],cwd=base.ROOT,
                   check=True,capture_output=True,creationflags=base.FLAGS,timeout=30)
    require(base.snapshot(release/'accounts.before.db')==base.snapshot(release/'town-diagnostic-accounts.db'),'Candidate changed schema/saves')
    info=dict(state='STAGED',live_database=str(database),old_server_sha256=base.sha(base.ACTIVE),
        candidate_sha256=base.sha(CANDIDATE),config_sha256=base.sha(base.CONFIG),client_sha256=CLIENT_SHA,
        client_receipt=str(RECEIPT),owned_deity_count=len(keys),scope='Native portrait guard; no growth, grants, client edits or save migration')
    save(release/'manifest.json',info);return info

def verify(release):
    info=read(release/'manifest.json');database=Path(info['live_database'])
    require(base.sha(base.ACTIVE)==info['candidate_sha256'] and base.sha(base.CONFIG)==info['config_sha256'] and
            base.sha(base.CLIENT)==info['client_sha256'],'Managed identity changed')
    require(read(release/'save-preservation.json')['all_tables_and_schemas_unchanged'],'Stopped-state preservation missing')
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        require(db.execute('pragma quick_check').fetchone()==('ok',) and not db.execute('pragma foreign_key_check').fetchall(),'Database integrity failed')
        counts={name:db.execute('select count(*) from '+name).fetchone()[0] for name in
                ('accounts','recovered_characters','native_companion_metadata','native_pet1_metadata','character_deities')}
    result=dict(service_pid=base.listener(allow_players=True),schema=37,counts=counts,
                client_unchanged=True,config_unchanged=True,save_migration=False,instances_granted=0)
    save(release/'verification.json',result);return result

def apply(release):
    info=read(release/'manifest.json');database=Path(info['live_database'])
    require(info['state']=='STAGED','Stage before apply')
    require(base.sha(base.ACTIVE)==info['old_server_sha256'] and base.sha(base.CONFIG)==info['config_sha256'],'Managed files changed')
    baseline=base.snapshot(release/'accounts.before.db')
    require(base.snapshot(database)==baseline,'Saved state changed; restage')
    candidate=release/'god2-server.candidate.exe';require(base.sha(candidate)==info['candidate_sha256'],'Candidate changed')
    pid=base.listener();base.stop(pid);started=False
    try:
        require(base.snapshot(database)==baseline,'Saves changed during stop')
        save(release/'save-preservation.json',dict(all_tables_and_schemas_unchanged=True,phase='STOPPED_BEFORE_START'))
        shutil.copy2(candidate,base.ACTIVE);base.start()
        base.powershell("$deadline=(Get-Date).AddSeconds(15); do {Start-Sleep -Milliseconds 300; $r=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $r.Count -and (Get-Date) -lt $deadline); if($r.Count -ne 1){throw 'Managed server did not listen'}")
        started=True;result=verify(release);info['state']='INSTALLED';save(release/'manifest.json',info);return result
    except BaseException:
        # Never restore old DB after any new player write. This release does
        # not mutate the DB at all; rollback only the executable on startup failure.
        if started:
            info['state']='VERIFY_FAILED_RUNNING_SAVES_PRESERVED';save(release/'manifest.json',info);raise
        try:base.stop(base.listener(allow_players=True))
        except Exception:pass
        shutil.copy2(release/'god2-server.before.exe',base.ACTIVE);base.start();raise

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=('stage','apply','verify'));ap.add_argument('--name',required=True)
    args=ap.parse_args();require(args.name.startswith('deity-portrait-') and '/' not in args.name and '\\' not in args.name,'Invalid release name')
    print(json.dumps({'stage':stage,'apply':apply,'verify':verify}[args.mode](base.ROOT/'artifacts/releases'/args.name)))
