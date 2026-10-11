"""Promote pinned weapon definitions/owned2C restore, with save-preserving rollback."""
import argparse,json,re,shutil,sqlite3,subprocess
from contextlib import closing
from pathlib import Path
from tools.operations import native_quest_catalog_release as base
from tools.strike_lab import import_native_weapons as weapons

ROOT=base.ROOT
CANDIDATE=ROOT/'build-town-visibility/Release/god2-server-role-auxiliary.exe'
ACCEPTANCE=ROOT/'artifacts/playtests/private-role-auxiliary-20260926-02/run-result.json'
CACHE=ROOT/'artifacts/research/native-weapons-20260926/records.json'
CLIENT_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
NEW_TABLES=set(weapons.TABLES)|{'character_role_auxiliary_snapshots'}

def require(value,message):
    if not value:raise ValueError(message)
def read(path):return json.loads(path.read_text('utf-8'))
def differences(before,after):
    changed=[name for name in before if name!='schema_migrations' and before[name]!=after.get(name)]
    if before['schema_migrations'][0]!=after['schema_migrations'][0] or any(row not in after['schema_migrations'][1] for row in before['schema_migrations'][1]):changed.append('schema_migrations')
    if set(after)-set(before)!=NEW_TABLES-set(before):changed.append('unexpected new tables')
    return changed

def check_sources(database):
    require(base.sha(base.CLIENT)==CLIENT_SHA,'Current client identity changed')
    expected=weapons.cached_records(CACHE)
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        actual=tuple(tuple(db.execute('SELECT * FROM '+table+' ORDER BY '+order)) for table,order in zip(weapons.TABLES,weapons.ORDERS))
        require(actual==expected,'Native weapon formal rows mismatch')
        require(db.execute('PRAGMA quick_check').fetchone()==('ok',),'Integrity failed')
        require(db.execute('PRAGMA foreign_key_check').fetchone() is None,'Foreign key violation')
        require(db.execute('SELECT count(*) FROM character_role_auxiliary_snapshots').fetchone()==(0,),'No production auxiliary grants permitted')
        require(db.execute('SELECT max(version) FROM schema_migrations').fetchone()==(27,),'Expected schema27')
    # This executable opens the supplied DB read-only; negative mutations occur
    # exclusively on its in-memory copy. Lua reads full real native records.
    subprocess.run([str(ROOT/'build-town-visibility/tests/Release/native-weapon-catalog.exe'),str(database)],check=True,capture_output=True,creationflags=base.FLAGS)

def accepted_candidate():
    result=read(ACCEPTANCE)
    require(result.get('accepted') and result['server_sha256']==base.sha(CANDIDATE),'Final same-candidate hidden acceptance required')
    require(all(result.get(key) for key in ('source_db_unchanged','live_client_unchanged','private_client_unchanged')),'Hidden fixture preservation failed')
    auxiliary=result['ui']['role_auxiliary_restore']
    require(auxiliary['persisted_snapshot_unchanged'] and auxiliary['resources_match_owned_fixture'] and
            auxiliary['resources_after_actions']==[52,120,26,80] and auxiliary['authority']=='CUSTOM_TEST_NOT_NATIVE','Owned2C hidden acceptance missing')
    require(result['native_weapon_import']['source_rows']==1259 and result['native_weapon_import']['player_instances_created']==0,'Hidden source catalog missing')
    require(result['ui']['client_alive'] and result['ui']['desktop_final']['input']=='Default','Hidden client/desktop acceptance failed')

def stage(release):
    accepted_candidate();require(base.sha(base.CLIENT)==CLIENT_SHA,'Client identity changed')
    release.mkdir(parents=True,exist_ok=False)
    config=read(base.CONFIG);database=Path(config['database']['path'])
    shutil.copy2(base.ACTIVE,release/'god2-server.before.exe');shutil.copy2(CANDIDATE,release/'god2-server.candidate.exe')
    shutil.copy2(base.CONFIG,release/'server-config.before.json')
    base.backup(database,release/'accounts.before.db');base.backup(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    config['database']['path']=str(release/'town-diagnostic-accounts.db');config['logging']['file']=str(release/'migration.log')
    stage_config=release/'stage-config.json';stage_config.write_text(json.dumps(config),encoding='utf-8')
    subprocess.run([str(CANDIDATE),'--config',str(stage_config),'--migrate-only'],cwd=ROOT,check=True,capture_output=True,creationflags=base.FLAGS)
    with closing(sqlite3.connect(release/'town-diagnostic-accounts.db')) as db:
        imported=weapons.import_catalog(db,records=weapons.cached_records(CACHE))
    check_sources(release/'town-diagnostic-accounts.db')
    changed=differences(base.snapshot(release/'accounts.before.db'),base.snapshot(release/'town-diagnostic-accounts.db'))
    require(not changed,'Stage changed existing state: '+repr(changed))
    info={'live_database':str(database),'old_server_sha256':base.sha(base.ACTIVE),'candidate_sha256':base.sha(CANDIDATE),
          'original_config_sha256':base.sha(base.CONFIG),'client_sha256':CLIENT_SHA,'source_import':imported,
          'catalog_sha256':weapons.CATALOG_SHA,'acceptance':str(ACCEPTANCE),
          'scope':'1259 native WPN/TWP definitions and CUSTOM-0045 owned raw2C persistence/restore; no equipped formula, instance grant, appearance mapping or live auxiliary grant'}
    (release/'manifest.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'staged':str(release),'native_weapon_rows':1259,'player_tables_changed':changed,'auxiliary_rows':0}))

def apply(release):
    info=base.manifest(release);database=Path(info['live_database'])
    require(base.sha(base.ACTIVE)==info['old_server_sha256'] and base.sha(base.CONFIG)==info['original_config_sha256'],'Managed files changed; restage')
    require(base.sha(release/'god2-server.candidate.exe')==info['candidate_sha256'],'Candidate changed')
    accepted_candidate();check_sources(release/'town-diagnostic-accounts.db')
    require(base.snapshot(database)==base.snapshot(release/'accounts.before.db'),'Saves changed; restage')
    pid=base.listener();base.stop(pid)
    # If saves changed during shutdown, simply resume: no writes have occurred.
    if base.snapshot(database)!=base.snapshot(release/'accounts.before.db'):
        base.start();raise ValueError('Saves changed during stop; restage')
    try:
        base.backup(release/'town-diagnostic-accounts.db',database)
        shutil.copy2(release/'god2-server.candidate.exe',base.ACTIVE);base.start()
        base.powershell("$deadline=(Get-Date).AddSeconds(15); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Server did not listen'}")
        verify(release)
    except BaseException:
        base.powershell("Stop-ScheduledTask -TaskName 'GOD2 Local Server' -ErrorAction SilentlyContinue; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue); foreach($row in $rows){$p=Get-Process -Id $row.OwningProcess; if($p.Path -eq '"+str(base.ACTIVE).replace("'","''")+"'){Stop-Process -Id $p.Id}}")
        base.backup(release/'accounts.before.db',database);shutil.copy2(release/'god2-server.before.exe',base.ACTIVE);base.start();raise

def verify(release):
    info=base.manifest(release);database=Path(info['live_database']);check_sources(database)
    changed=differences(base.snapshot(release/'accounts.before.db'),base.snapshot(database))
    result={'schema_version':27,'native_weapon_counts':{'WPN':630,'TWP':629},'player_tables_changed':changed,
            'client_unchanged':base.sha(base.CLIENT)==info['client_sha256'],
            'active_binary_matches_candidate':base.sha(base.ACTIVE)==info['candidate_sha256'],
            'active_config_unchanged':base.sha(base.CONFIG)==info['original_config_sha256'],
            'service_pid':base.listener(allow_players=True),'auxiliary_rows':0,'no_instances_or_stat_grants':not changed}
    (release/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    require(not changed and all(result[key] for key in ('client_unchanged','active_binary_matches_candidate','active_config_unchanged')),'Release verification failed')
    print(json.dumps(result))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('stage','apply','verify'))
    parser.add_argument('--release-name',required=True);args=parser.parse_args()
    require(re.fullmatch(r'native-weapons-auxiliary-[0-9-]+',args.release_name),'Invalid release name')
    {'stage':stage,'apply':apply,'verify':verify}[args.mode](ROOT/'artifacts/releases'/args.release_name)
if __name__=='__main__':main()
