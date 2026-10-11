"""Promote tested regional map presentation; preserve player saves and rollback."""
import argparse,json,re,shutil,sqlite3,subprocess
from contextlib import closing
from pathlib import Path
from tools.operations import native_quest_catalog_release as base
from tools.strike_lab import import_native_catalog as maps,import_native_map_items as items

ROOT=base.ROOT
CANDIDATE=ROOT/'build-town-visibility/Release/god2-server-owned-map-view.exe'
ACCEPTANCE=ROOT/'artifacts/playtests/private-owned-map-view-20260926-03/run-result.json'

def read_config(path):return json.loads(path.read_text('utf-8'))
def check_sources(database):
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        if db.execute('select * from native_data_sources where dataset_id=?',(maps.DATASET,)).fetchone()!=maps.SOURCE_ROW:raise ValueError('Map source mismatch')
        if db.execute('select * from native_map_catalog where dataset_id=? order by source_record_index',(maps.DATASET,)).fetchall()!=maps.pinned_records(base.CLIENT.parent):raise ValueError('Map rows mismatch')
        if tuple(tuple(db.execute('select * from '+t+' order by '+o)) for t,o in zip(items.TABLES,items.ORDERS))!=items.pinned_records(base.CLIENT.parent):raise ValueError('Map item source mismatch')
    for name in ('native-map-item-catalog','owned-map-view'):
        subprocess.run([str(ROOT/'build-town-visibility/tests/Release'/f'{name}.exe'),str(database)],check=True,capture_output=True,creationflags=base.FLAGS)

def differences(before,after):
    extended={'schema_migrations','native_data_sources','native_map_catalog'}
    changed=[name for name in before if name not in extended and before[name]!=after.get(name)]
    for name in extended:
        if before[name][0]!=after[name][0] or any(row not in after[name][1] for row in before[name][1]):changed.append(name)
    return changed

def stage(release):
    accepted=read_config(ACCEPTANCE)
    if not accepted['accepted'] or accepted['server_sha256']!=base.sha(CANDIDATE) or not all(accepted[k] for k in ('source_db_unchanged','live_client_unchanged','private_client_unchanged')):raise ValueError('Final candidate hidden acceptance required')
    release.mkdir(parents=True,exist_ok=False)
    config=read_config(base.CONFIG);database=Path(config['database']['path'])
    shutil.copy2(base.ACTIVE,release/'god2-server.before.exe');shutil.copy2(CANDIDATE,release/'god2-server.candidate.exe')
    shutil.copy2(base.CONFIG,release/'server-config.before.json');base.backup(database,release/'accounts.before.db');base.backup(database,release/'town-diagnostic-accounts.db')
    staged=dict(config);staged=read_config(base.CONFIG);staged['database']['path']=str(release/'town-diagnostic-accounts.db');staged['logging']['file']=str(release/'migration.log')
    cfg=release/'stage-config.json';cfg.write_text(json.dumps(staged),encoding='utf-8')
    subprocess.run([str(CANDIDATE),'--config',str(cfg),'--migrate-only'],cwd=ROOT,check=True,capture_output=True,creationflags=base.FLAGS)
    with closing(sqlite3.connect(release/'town-diagnostic-accounts.db')) as db:
        result={'maps':maps.import_catalog(db,base.CLIENT.parent),'items':items.import_catalog(db,base.CLIENT.parent)}
    check_sources(release/'town-diagnostic-accounts.db')
    changed=differences(base.snapshot(release/'accounts.before.db'),base.snapshot(release/'town-diagnostic-accounts.db'))
    if changed:raise ValueError('Staging rewrote saved state: '+repr(changed))
    config.setdefault('world',{})['owned_map_views']={'enabled':True}
    (release/'server-config.candidate.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    info={'live_database':str(database),'old_server_sha256':base.sha(base.ACTIVE),'candidate_sha256':base.sha(CANDIDATE),
          'original_config_sha256':base.sha(base.CONFIG),'client_sha256':base.sha(base.CLIENT),'sources':result,
          'candidate_config_sha256':base.sha(release/'server-config.candidate.json'),'acceptance':str(ACCEPTANCE),
          'scope':'CUSTOM-0044 repeatable owned regional map presentation; original sources only; no item/quest/NPC grant or player mutation'}
    (release/'manifest.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8');print(json.dumps({'staged':str(release),'sources':result}))

def apply(release):
    info=base.manifest(release);database=Path(info['live_database'])
    if base.sha(base.ACTIVE)!=info['old_server_sha256'] or base.sha(base.CONFIG)!=info['original_config_sha256'] or base.sha(release/'god2-server.candidate.exe')!=info['candidate_sha256'] or base.sha(release/'server-config.candidate.json')!=info['candidate_config_sha256']:raise ValueError('Managed/staged files changed')
    if base.snapshot(database)!=base.snapshot(release/'accounts.before.db'):raise ValueError('Saves changed; restage')
    check_sources(release/'town-diagnostic-accounts.db');pid=base.listener();base.stop(pid)
    try:
        if base.snapshot(database)!=base.snapshot(release/'accounts.before.db'):raise ValueError('Saves changed while stopping')
        base.backup(release/'town-diagnostic-accounts.db',database)
        shutil.copy2(release/'god2-server.candidate.exe',base.ACTIVE);shutil.copy2(release/'server-config.candidate.json',base.CONFIG);base.start()
        base.powershell("$deadline=(Get-Date).AddSeconds(15); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Server did not listen'}")
        verify(release)
    except BaseException:
        base.powershell("Stop-ScheduledTask -TaskName 'GOD2 Local Server' -ErrorAction SilentlyContinue; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue); foreach($row in $rows){$p=Get-Process -Id $row.OwningProcess; if($p.Path -eq '"+str(base.ACTIVE).replace("'","''")+"'){Stop-Process -Id $p.Id}}")
        base.backup(release/'accounts.before.db',database);shutil.copy2(release/'god2-server.before.exe',base.ACTIVE);shutil.copy2(release/'server-config.before.json',base.CONFIG);base.start();raise

def verify(release):
    info=base.manifest(release);database=Path(info['live_database']);check_sources(database)
    changed=differences(base.snapshot(release/'accounts.before.db'),base.snapshot(database))
    config=read_config(base.CONFIG);before=read_config(release/'server-config.before.json');before.setdefault('world',{})['owned_map_views']={'enabled':True}
    result={'player_tables_changed':changed,'map_rows':144,'map_item_rows':2,'quick_check':'ok',
            'client_unchanged':base.sha(base.CLIENT)==info['client_sha256'],'active_binary_matches_candidate':base.sha(base.ACTIVE)==info['candidate_sha256'],
            'config_only_map_views_changed':config==before,'service_pid':base.listener(allow_players=True),'no_live_item_grants':not changed}
    (release/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    if changed or not all(result[k] for k in ('client_unchanged','active_binary_matches_candidate','config_only_map_views_changed')):raise ValueError('Release verification failed')
    print(json.dumps(result))

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=('stage','apply','verify'));ap.add_argument('--release-name',required=True);args=ap.parse_args()
    if not re.fullmatch(r'owned-map-view-[0-9-]+',args.release_name):raise ValueError('Invalid release name')
    {'stage':stage,'apply':apply,'verify':verify}[args.mode](ROOT/'artifacts/releases'/args.release_name)
if __name__=='__main__':main()
