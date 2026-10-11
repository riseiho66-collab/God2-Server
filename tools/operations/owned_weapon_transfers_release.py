"""Install tested owned-instance route/schema with production gameplay still gated."""
import argparse,json,re,shutil,sqlite3,subprocess
from pathlib import Path
from contextlib import closing
from tools.operations import native_quest_catalog_release as base
from tools.strike_lab import import_native_weapons as weapons
ROOT=base.ROOT
CANDIDATE=ROOT/'build-town-visibility/Release/god2-server-weapon-transfers.exe'
ACCEPTANCE=ROOT/'artifacts/playtests/private-weapon-transfers-20260926-03/run-result.json'
CACHE=ROOT/'artifacts/research/native-weapons-20260926/records.json'
CLIENT_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'

def require(value,message):
    if not value:raise ValueError(message)
def read(path):return json.loads(path.read_text('utf-8'))
def triggers(path):
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        return dict(db.execute("SELECT name,sql FROM sqlite_master WHERE type='trigger'"))
def differences(before,after):
    changed=[name for name in before if name!='schema_migrations' and before[name]!=after.get(name)]
    if before['schema_migrations'][0]!=after['schema_migrations'][0] or any(row not in after['schema_migrations'][1] for row in before['schema_migrations'][1]):changed.append('schema_migrations')
    if set(after)-set(before)!={'character_weapon_slot_metadata'}-set(before):changed.append('unexpected tables')
    return changed
def accepted():
    result=read(ACCEPTANCE);ui=result['ui'];transfers=ui['weapon_transfers']
    require(result['accepted'] and result['server_sha256']==base.sha(CANDIDATE),'Final same-candidate hidden acceptance required')
    require(all(result[k] for k in ('source_db_unchanged','live_client_unchanged','private_client_unchanged')),'Hidden isolation/preservation failed')
    require(transfers['authority']=='CUSTOM_TEST_NOT_NATIVE' and len(transfers['stages'])==4,'Four native UI weapon steps missing')
    require([(step['source'],step['destination']) for step in transfers['stages']]==[(0,34),(1,34),(34,0),(0,34)],'Wrong native UI transitions')
    require(all(step['fresh_hover']['fresh_cache_transition'] and step['unrelated_native_state_unchanged'] for step in transfers['stages']),'Tooltip/state acceptance missing')
    require(ui['client_alive'] and ui['desktop_final']['input']=='Default','Hidden client/desktop acceptance missing')
def check_state(database):
    require(base.sha(base.CLIENT)==CLIENT_SHA,'Client identity changed')
    expected=weapons.cached_records(CACHE)
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        require(db.execute('PRAGMA quick_check').fetchone()==('ok',) and db.execute('PRAGMA foreign_key_check').fetchone() is None,'SQLite integrity failed')
        actual=tuple(tuple(db.execute('SELECT * FROM '+t+' ORDER BY '+o)) for t,o in zip(weapons.TABLES,weapons.ORDERS))
        require(actual==expected,'Pinned weapon source changed')
        require(db.execute('SELECT max(version) FROM schema_migrations').fetchone()==(28,),'Expected schema28')
        require(db.execute('SELECT count(*) FROM character_weapon_slot_metadata').fetchone()==(0,),'Production metadata/grant must stay absent')
    require('retire_empty_weapon_overlay' in triggers(database),'Inactive overlay retirement trigger missing')
    subprocess.run([str(ROOT/'build-town-visibility/tests/Release/native-weapon-catalog.exe'),str(database)],check=True,capture_output=True,creationflags=base.FLAGS)
def trigger_change(before,after):
    require(all(after.get(name)==sql for name,sql in before.items()),'Existing trigger changed')
    require(set(after)-set(before)=={'retire_empty_weapon_overlay'}-set(before),'Unexpected trigger changes')
def production_gate(config):
    require(not config.get('world',{}).get('owned_weapon_transfers',{}).get('enabled',False),
        'Complete production equipment gameplay remains gated on original appearance/stat generation')
def stage(release):
    accepted();config=read(base.CONFIG);production_gate(config)
    release.mkdir(parents=True,exist_ok=False);database=Path(config['database']['path'])
    shutil.copy2(base.ACTIVE,release/'god2-server.before.exe');shutil.copy2(CANDIDATE,release/'god2-server.candidate.exe')
    shutil.copy2(base.CONFIG,release/'server-config.before.json')
    base.backup(database,release/'accounts.before.db');base.backup(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    config['database']['path']=str(release/'town-diagnostic-accounts.db');config['logging']['file']=str(release/'migration.log')
    cfg=release/'stage-config.json';cfg.write_text(json.dumps(config),encoding='utf-8')
    subprocess.run([str(CANDIDATE),'--config',str(cfg),'--migrate-only'],cwd=ROOT,check=True,capture_output=True,creationflags=base.FLAGS)
    check_state(release/'town-diagnostic-accounts.db')
    changed=differences(base.snapshot(release/'accounts.before.db'),base.snapshot(release/'town-diagnostic-accounts.db'))
    require(not changed,'Staging changed saves: '+repr(changed));trigger_change(triggers(release/'accounts.before.db'),triggers(release/'town-diagnostic-accounts.db'))
    info={'live_database':str(database),'old_server_sha256':base.sha(base.ACTIVE),'candidate_sha256':base.sha(CANDIDATE),
        'original_config_sha256':base.sha(base.CONFIG),'client_sha256':CLIENT_SHA,'acceptance':str(ACCEPTANCE),
        'scope':'CUSTOM-0046 full20byte owned28/weapon24 transaction/native projection connected and accepted in isolated current client; production option remains disabled pending appearance/stat generation; no grants or save rewrites'}
    (release/'manifest.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8');print(json.dumps({'staged':str(release),'schema':28,'player_tables_changed':changed,'production_equipment_enabled':False}))
def apply(release):
    info=base.manifest(release);database=Path(info['live_database'])
    require(base.sha(base.ACTIVE)==info['old_server_sha256'] and base.sha(base.CONFIG)==info['original_config_sha256'],'Managed files changed; restage')
    require(base.sha(release/'god2-server.candidate.exe')==info['candidate_sha256'],'Candidate changed')
    accepted();check_state(release/'town-diagnostic-accounts.db');production_gate(read(base.CONFIG))
    require(base.snapshot(database)==base.snapshot(release/'accounts.before.db'),'Saves changed; restage')
    pid=base.listener();base.stop(pid)
    if base.snapshot(database)!=base.snapshot(release/'accounts.before.db'):
        base.start();raise ValueError('Saves changed during stop; restage')
    try:
        base.backup(release/'town-diagnostic-accounts.db',database);shutil.copy2(release/'god2-server.candidate.exe',base.ACTIVE);base.start()
        base.powershell("$deadline=(Get-Date).AddSeconds(15); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Server did not listen'}")
        verify(release)
    except BaseException:
        base.powershell("Stop-ScheduledTask -TaskName 'GOD2 Local Server' -ErrorAction SilentlyContinue; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue); foreach($row in $rows){$p=Get-Process -Id $row.OwningProcess; if($p.Path -eq '"+str(base.ACTIVE).replace("'","''")+"'){Stop-Process -Id $p.Id}}")
        base.backup(release/'accounts.before.db',database);shutil.copy2(release/'god2-server.before.exe',base.ACTIVE);base.start();raise
def verify(release):
    info=base.manifest(release);database=Path(info['live_database']);check_state(database);production_gate(read(base.CONFIG))
    changed=differences(base.snapshot(release/'accounts.before.db'),base.snapshot(database));trigger_change(triggers(release/'accounts.before.db'),triggers(database))
    result={'schema_version':28,'player_tables_changed':changed,'metadata_rows':0,'production_equipment_enabled':False,
        'client_unchanged':base.sha(base.CLIENT)==info['client_sha256'],'active_config_unchanged':base.sha(base.CONFIG)==info['original_config_sha256'],
        'active_binary_matches_candidate':base.sha(base.ACTIVE)==info['candidate_sha256'],'service_pid':base.listener(allow_players=True)}
    (release/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    require(not changed and all(result[k] for k in ('client_unchanged','active_config_unchanged','active_binary_matches_candidate')),'Release verification failed');print(json.dumps(result))
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('stage','apply','verify'));parser.add_argument('--release-name',required=True);args=parser.parse_args()
    require(re.fullmatch(r'owned-weapon-transfers-[0-9-]+',args.release_name),'Invalid release name')
    {'stage':stage,'apply':apply,'verify':verify}[args.mode](ROOT/'artifacts/releases'/args.release_name)
if __name__=='__main__':main()
