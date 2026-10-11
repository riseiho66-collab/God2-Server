"""Install a tested staged schema29 candidate, preserving saves and fixture gates."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
from tools.operations import native_quest_catalog_release as base
from tools.operations.stage_owned_player_appearance import require

def verify(release):
    info=base.manifest(release)
    config=json.loads(base.CONFIG.read_text('utf-8'))
    database=Path(config['database']['path'])
    before=base.snapshot(release/'accounts.before.db');after=base.snapshot(database)
    require(not [name for name in before if name!='schema_migrations' and before[name]!=after.get(name)],'Saved tables changed')
    require(set(after)-set(before)=={'character_player_appearance_snapshots'}-set(before),'Unexpected schema changes')
    require(before['schema_migrations'][0]==after['schema_migrations'][0] and set(before['schema_migrations'][1]).issubset(after['schema_migrations'][1]),'Migration history changed')
    def objects(path):
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
            return dict(db.execute("select name,sql from sqlite_master where type in ('trigger','index')"))
    original=objects(release/'accounts.before.db');current=objects(database)
    require(all(current.get(name)==sql for name,sql in original.items()),'Existing trigger/index changed')
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        require(db.execute('pragma foreign_key_check').fetchone() is None,'Foreign key check failed')
        require(db.execute('select max(version) from schema_migrations').fetchone()==(29,),'Schema29 required')
        require(db.execute('select count(*) from character_player_appearance_snapshots').fetchone()==(0,),'Appearance autogrant rejected')
    require(base.sha(base.ACTIVE)==info['candidate_sha256'],'Active candidate mismatch')
    require(base.sha(base.CONFIG)==base.sha(release/'server-config.active-before.json'),'Config changed')
    require(base.sha(base.CLIENT)==info['client_sha256'],'Client changed')
    require(not config.get('world',{}).get('owned_weapon_transfers',{}).get('enabled',False) and
        not config.get('world',{}).get('owned_player_appearance',{}).get('enabled',False) and
        not config['development'].get('diagnostic_owned_weapon_appearance',False),'Production fixture enabled')
    result={'state':'INSTALLED_GATED','schema_version':29,'pre_existing_tables_changed':[],
        'appearance_rows':0,'client_unchanged':True,'config_unchanged':True,
        'candidate_sha256':info['candidate_sha256'],'service_pid':base.listener(allow_players=True)}
    (release/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result

def apply(release):
    info=base.manifest(release)
    require(info['state']=='STAGED_NOT_INSTALLED' and info.get('actual_peer_refresh_accepted'),'Qualified staged peer release required')
    require(base.sha(base.ACTIVE)==base.sha(release/'god2-server.active-before.exe') and
        base.sha(base.CONFIG)==base.sha(release/'server-config.active-before.json'),'Managed files changed; restage')
    require(base.sha(release/'god2-server.candidate.exe')==info['candidate_sha256'],'Staged candidate changed')
    accepted=json.loads((Path(info['acceptance'])/'run-result.json').read_text('utf-8'))
    require(accepted['accepted'] and accepted['server_sha256']==info['candidate_sha256'],'Acceptance changed')
    config=json.loads(base.CONFIG.read_text('utf-8'));database=Path(config['database']['path'])
    require(base.snapshot(database)==base.snapshot(release/'accounts.before.db'),'Saves changed; restage')
    pid=base.listener();base.stop(pid)
    if base.snapshot(database)!=base.snapshot(release/'accounts.before.db'):
        base.start();raise RuntimeError('Saves changed during stop; restage')
    try:
        base.backup(release/'town-diagnostic-accounts.db',database)
        shutil.copy2(release/'god2-server.candidate.exe',base.ACTIVE);base.start()
        base.powershell("$deadline=(Get-Date).AddSeconds(15); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Server did not listen'}")
        result=verify(release)
        info['state']='INSTALLED_GATED';(release/'manifest.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8')
        return result
    except BaseException:
        base.powershell("Stop-ScheduledTask -TaskName 'GOD2 Local Server' -ErrorAction SilentlyContinue; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue); foreach($row in $rows){$p=Get-Process -Id $row.OwningProcess; if($p.Path -eq '"+str(base.ACTIVE).replace("'","''")+"'){Stop-Process -Id $p.Id}}")
        base.backup(release/'accounts.before.db',database)
        shutil.copy2(release/'god2-server.active-before.exe',base.ACTIVE);base.start();raise

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release',type=Path,required=True)
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    print(json.dumps((verify if args.verify_only else apply)(args.release.resolve()),indent=2))
