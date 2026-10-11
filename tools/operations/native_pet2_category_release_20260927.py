"""Promote native NCP/category catalogs, preserving saves and client binaries."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
from tools.operations import native_quest_catalog_release as base
from tools.strike_lab import import_native_pet2_categories as categories
from tools.strike_lab import import_companion_metadata as metadata

CANDIDATE=base.ROOT/'build-town-visibility/Release/god2-server-native-results.exe'
RECEIPT=base.ROOT/'artifacts/playtests/private-pet-categories-20260927-01/run-result.json'
CACHE=base.ROOT/'artifacts/research/native-pet2-categories-20260927/records.json'
NEW={'native_pet2_category_source','native_pet2_category_rows'}

def require(v,m):
    if not v:raise ValueError(m)
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def read(path):return json.loads(path.read_text('utf-8'))

def unchanged(before,after):
    a,b=base.snapshot(before),base.snapshot(after)
    require(set(b)-set(a)==NEW-set(a),'Unexpected schema additions')
    require(a['schema_migrations'][0]==b['schema_migrations'][0] and
            all(r in b['schema_migrations'][1] for r in a['schema_migrations'][1]),'Old migration history rewritten')
    for name in a:
        if name not in {'schema_migrations','native_companion_metadata'}:
            require(a[name]==b.get(name),'Existing state changed: '+name)
    require(all(r in b['native_companion_metadata'][1] for r in a['native_companion_metadata'][1]),
            'Existing companion metadata rewritten')

def ncp_rows(release):
    m=read(release/'manifest.json')
    path=release/'ncp-records.json'
    require(base.sha(path)==m['ncp_cache_sha256'],'Staged NCP cache changed')
    rows=[tuple(bytes.fromhex(x) if i in (4,6) else x for i,x in enumerate(row)) for row in read(path)]
    require(len(rows)==1165 and len({r[1] for r in rows})==1165 and
            all(r[0]=='NCP' and r[2]==metadata.SOURCE and len(r[6])==396 for r in rows),'NCP cache bounds')
    return rows

def verify_sources(database,expected):
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        actual=db.execute("SELECT * FROM native_companion_metadata WHERE family='NCP' ORDER BY metadata_key").fetchall()
        require(actual==sorted(expected,key=lambda r:r[1]),'Formal NCP catalog differs')
        actual_categories=db.execute('SELECT * FROM native_pet2_category_rows ORDER BY group_id,category_index').fetchall()
        require(actual_categories==categories.cached(CACHE),'Formal native categories differ')
        require(db.execute('SELECT max(version) FROM schema_migrations').fetchone()==(36,),'Expected schema36')
        require(db.execute('PRAGMA quick_check').fetchone()==('ok',),'Database integrity failed')
        require(db.execute('PRAGMA foreign_key_check').fetchone() is None,'Foreign key failure')
    subprocess.run([str(base.ROOT/'build-town-visibility/tests/Release/native-pet2-categories.exe'),
                    '--read-only',str(database)],check=True,capture_output=True,creationflags=base.FLAGS,timeout=30)

def stage(release):
    receipt=read(RECEIPT)
    require(receipt['accepted'] and receipt['server_sha256']==base.sha(CANDIDATE),'Same-candidate client acceptance missing')
    require(all(receipt[k] for k in ('source_db_unchanged','live_client_unchanged','private_client_unchanged')),'Fixture preservation failed')
    require(receipt['category_import']['rows']==464 and receipt['category_import']['dataset_sha256']==categories.DATASET,
            'Native category hidden import missing')
    require(receipt['ui']['desktop_before']==receipt['ui']['desktop_after']==receipt['ui']['desktop_final'],'Desktop changed')
    require(len(receipt['ui']['stages'])==3,'Missing owned transfer stages')
    require(base.sha(base.CLIENT)==categories.CLIENT_SHA,'Current client identity changed')
    release.mkdir(parents=True,exist_ok=False)
    cfg=read(base.CONFIG);database=Path(cfg['database']['path'])
    base.backup(database,release/'accounts.before.db');base.backup(database,release/'town-diagnostic-accounts.db')
    shutil.copy2(base.ACTIVE,release/'god2-server.before.exe')
    shutil.copy2(CANDIDATE,release/'god2-server.candidate.exe')
    shutil.copy2(base.CONFIG,release/'server-config.before.json')
    cfg['database']['path']=str(release/'town-diagnostic-accounts.db');cfg['logging']['file']=str(release/'migration.log')
    save(release/'stage-config.json',cfg)
    subprocess.run([str(CANDIDATE),'--config',str(release/'stage-config.json'),'--migrate-only'],
                   cwd=base.ROOT,check=True,capture_output=True,creationflags=base.FLAGS,timeout=30)
    rows=metadata.extract()
    save(release/'ncp-records.json',[[x.hex() if isinstance(x,bytes) else x for x in row] for row in rows])
    imported=metadata.install(release/'town-diagnostic-accounts.db',rows)
    with closing(sqlite3.connect(release/'town-diagnostic-accounts.db')) as db:
        catalog=categories.install(db,categories.cached(CACHE))
    unchanged(release/'accounts.before.db',release/'town-diagnostic-accounts.db');verify_sources(release/'town-diagnostic-accounts.db',rows)
    info=dict(state='STAGED',live_database=str(database),old_server_sha256=base.sha(base.ACTIVE),
              candidate_sha256=base.sha(CANDIDATE),config_sha256=base.sha(base.CONFIG),client_sha256=base.sha(base.CLIENT),
              ncp_cache_sha256=base.sha(release/'ncp-records.json'),category_dataset_sha256=categories.DATASET,
              ncp_import=imported,category_import=catalog,client_receipt=str(RECEIPT),
              scope='Native static definitions and owned display-category resolution; no pet grants or growth formulas')
    save(release/'manifest.json',info);return {k:v for k,v in info.items() if k!='ncp_import'}

def verify(release):
    info=read(release/'manifest.json');database=Path(info['live_database'])
    require(base.sha(base.ACTIVE)==info['candidate_sha256'] and base.sha(base.CONFIG)==info['config_sha256'] and
            base.sha(base.CLIENT)==info['client_sha256'],'Managed identity changed')
    verify_sources(database,ncp_rows(release))
    result=dict(service_pid=base.listener(allow_players=True),schema=36,native_ncp_rows=1165,
                native_category_rows=464,player_state_verified_before_start=True,
                client_unchanged=True,config_unchanged=True,pet_instances_granted=0,
                original_growth_formula_verified=False)
    require(read(release/'player-state-verification.json')==dict(all_existing_player_tables_unchanged=True,
            schema_history_preserved=True,phase='STOPPED_BEFORE_START',pet_instances_granted=0),
            'Stopped-phase player preservation receipt differs')
    save(release/'verification.json',result);return result

def apply(release):
    info=read(release/'manifest.json');database=Path(info['live_database'])
    require(info['state']=='STAGED','Stage before apply')
    require(base.sha(base.ACTIVE)==info['old_server_sha256'] and base.sha(base.CONFIG)==info['config_sha256'] and
            base.sha(base.CLIENT)==info['client_sha256'],'Managed identities changed since staging')
    require(base.snapshot(database)==base.snapshot(release/'accounts.before.db'),'Saves changed; restage')
    candidate=release/'god2-server.candidate.exe'
    require(base.sha(candidate)==info['candidate_sha256'],'Staged candidate changed')
    rows=ncp_rows(release);pid=base.listener();base.stop(pid)
    started=False;startup_snapshot=None
    try:
        require(base.snapshot(database)==base.snapshot(release/'accounts.before.db'),'Saves changed while stopping')
        subprocess.run([str(candidate),'--config',str(base.CONFIG),'--migrate-only'],cwd=base.ROOT,
                       check=True,capture_output=True,creationflags=base.FLAGS,timeout=30)
        metadata.install(database,rows)
        with closing(sqlite3.connect(database)) as db:categories.install(db,categories.cached(CACHE))
        # Check every prior player table while the service is stopped. Once it
        # listens, new legitimate player writes must never trigger an old-save rollback.
        unchanged(release/'accounts.before.db',database);verify_sources(database,rows)
        save(release/'player-state-verification.json',dict(all_existing_player_tables_unchanged=True,
             schema_history_preserved=True,phase='STOPPED_BEFORE_START',pet_instances_granted=0))
        startup_snapshot=base.snapshot(database)
        shutil.copy2(candidate,base.ACTIVE);base.start()
        base.powershell("$deadline=(Get-Date).AddSeconds(15); do {Start-Sleep -Milliseconds 300; $r=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $r.Count -and (Get-Date) -lt $deadline); if($r.Count -ne 1){throw 'Managed service did not listen'}")
        started=True
        result=verify(release);info['state']='INSTALLED';save(release/'manifest.json',info);return result
    except BaseException:
        if started or (startup_snapshot is not None and base.snapshot(database)!=startup_snapshot):
            info['state']='VERIFY_FAILED_RUNNING_SAVES_PRESERVED';save(release/'manifest.json',info)
            raise
        try:base.stop(base.listener(allow_players=True))
        except Exception:pass
        base.backup(release/'accounts.before.db',database)
        shutil.copy2(release/'god2-server.before.exe',base.ACTIVE);base.start();raise

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=('stage','apply','verify'))
    ap.add_argument('--name',required=True);a=ap.parse_args()
    require(a.name.startswith('native-pet2-category-') and '/' not in a.name and '\\' not in a.name,'Invalid release directory')
    release=base.ROOT/'artifacts/releases'/a.name
    print(json.dumps({'stage':stage,'apply':apply,'verify':verify}[a.mode](release)))
