"""Promote qualified owned non-revival supply without granting items or stats."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
from tools.operations import native_quest_catalog_release as base
from tools.strike_lab import import_native_med02_recovery as med

CANDIDATE=base.ROOT/'build-town-visibility/Release/god2-server-owned-supply-20260927-04.exe'
SOURCE_TABLES={'native_data_sources','native_med02_recovery_declarations'}
BALANCE=base.ROOT/'docs/research/current-med02-self-supply-20260927.md'

def require(ok,message):
    if not ok:raise ValueError(message)
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')

def source_check(path):
    binary=base.ROOT/'build-town-visibility/tests/Release/native-supply-catalog-integrity.exe'
    result=subprocess.run([str(binary),str(path)],check=True,capture_output=True,text=True,creationflags=base.FLAGS)
    require(result.stdout.strip()=='71','Full C++ source gate failed')

def unchanged(before_path,after_path):
    before,after=base.snapshot(before_path),base.snapshot(after_path)
    require(set(before)==set(after),'Unexpected schema change')
    require(not [n for n in before if n not in SOURCE_TABLES and before[n]!=after[n]],'Existing saved/migration table changed')
    for name in SOURCE_TABLES:
        require(before[name][0]==after[name][0] and set(before[name][1]).issubset(after[name][1]),'Original source rows/schema changed')
    allowed={repr(med.SOURCE_ROW)}
    require(set(after['native_data_sources'][1])-set(before['native_data_sources'][1])<=allowed,'Unexpected source additions')
    source_check(after_path)
    def objects(path):
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
            return dict(db.execute("SELECT name,sql FROM sqlite_master WHERE type IN ('trigger','index')"))
    require(objects(before_path)==objects(after_path),'Indexes/triggers changed')
    with closing(sqlite3.connect(after_path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        require(db.execute('SELECT max(version) FROM schema_migrations').fetchone()==(30,),'Schema30 required')
        require(not db.execute('PRAGMA foreign_key_check').fetchall(),'Foreign-key check failed')

def acceptance(path,expected):
    result=json.loads((path/'run-result.json').read_text('utf-8'))
    require(result['accepted'] and result['server_sha256']==expected,'Actual-client candidate mismatch')
    require(result['all_clients_closed'] and result['desktop_unchanged'] and result['candidate_unchanged'] and
        result['owned_server_closed'] and result['owned_runner_closed'] and all(result['source_files_unchanged'].values()),'Actual-client preservation/cleanup failed')
    ui=result['ui'];require(ui['accepted'] and ui['relogin']['persisted'] and len(ui['stages'])==5 and ui['log_count']==5,'Supply use/cap/relogin not accepted')
    require([row['consumed'] for row in ui['stages']]==[True,False,True,True,False],'Unexpected native consume sequence')
    return result

def stage(release,accepted,tcp):
    candidate=base.sha(CANDIDATE);acceptance(accepted,candidate)
    value=json.loads(tcp.read_text('utf-8'))
    require(value['status']=='PASS' and value['server_sha256']==candidate and len(value['startup_denials'])==4,'Same-candidate TCP required')
    require(len(value['cases'])>=22 and all(c['status']=='PASS' for c in value['cases']),'Incomplete TCP owner/empty/unknown-bag cases')
    require(BALANCE.is_file() and 'Historical references and CUSTOM-0016 balance review' in BALANCE.read_text('utf-8'),'Supply policy balance review required')
    original=json.loads(base.CONFIG.read_text('utf-8'))
    require(not original['development'].get('diagnostic_world_supply',False),'Legacy diagnostic supply must remain disabled')
    require(not original['development'].get('diagnostic_world_resources',False),'Legacy diagnostic resources must remain disabled')
    database=Path(original['database']['path']);release.mkdir(parents=True,exist_ok=False)
    shutil.copy2(base.ACTIVE,release/'god2-server.active-before.exe');shutil.copy2(CANDIDATE,release/'god2-server.candidate.exe')
    shutil.copy2(base.CONFIG,release/'server-config.active-before.json')
    base.backup(database,release/'accounts.before.db');base.backup(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    updated=json.loads(json.dumps(original));updated.setdefault('world',{})['owned_supply']={'enabled':True}
    save(release/'server-config.candidate.json',updated)
    migration=json.loads(json.dumps(updated));migration['database']['path']=str(release/'town-diagnostic-accounts.db');migration['logging']['file']=str(release/'migration.log')
    with socket.socket() as probe:require(probe.connect_ex(('127.0.0.1',2597))!=0,'Stage source probe port occupied')
    migration['server']['port']=2597;migration['server']['character_port']=0
    cfg=release/'stage-config.json';save(cfg,migration)
    subprocess.run([str(CANDIDATE),'--config',str(cfg),'--migrate-only'],cwd=base.ROOT,check=True,capture_output=True,creationflags=base.FLAGS)
    with closing(sqlite3.connect(release/'town-diagnostic-accounts.db')) as db:imported=med.import_catalog(db,base.ROOT.parent/'God2')
    unchanged(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    subprocess.run([str(CANDIDATE),'--config',str(cfg),'--run-for','1'],cwd=base.ROOT,check=True,capture_output=True,timeout=15,creationflags=base.FLAGS)
    unchanged(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    info=dict(state='STAGED_NOT_INSTALLED',live_database=str(database),candidate_sha256=candidate,
        old_server_sha256=base.sha(base.ACTIVE),client_sha256=base.sha(base.CLIENT),config_sha256_before=base.sha(base.CONFIG),
        config_sha256_after=base.sha(release/'server-config.candidate.json'),acceptance=str(accepted),tcp=str(tcp),tcp_sha256=base.sha(tcp),
        balance_path=str(BALANCE),balance_sha256=base.sha(BALANCE),source_import=imported,
        scope='Owned self-player world MED02 recovery only. Source text amounts, CUSTOM-0016 cap/living/debit. No grants, revival, other-target/battle supply or original formula claim.')
    save(release/'manifest.json',info);return info

def verify(release):
    info=base.manifest(release);database=Path(info['live_database'])
    unchanged(release/'accounts.before.db',database)
    require(base.sha(base.ACTIVE)==info['candidate_sha256'] and base.sha(base.CLIENT)==info['client_sha256'],'Server/client identity changed')
    require(base.sha(base.CONFIG)==info['config_sha256_after'],'Active config changed')
    before=json.loads((release/'server-config.active-before.json').read_text('utf-8'));expected=json.loads(json.dumps(before))
    expected.setdefault('world',{})['owned_supply']={'enabled':True}
    require(json.loads(base.CONFIG.read_text('utf-8'))==expected,'Unrelated config changed')
    result=dict(state='INSTALLED_ENABLED',schema_version=30,med02_declarations=71,
        player_tables_changed=[],client_unchanged=True,config_changes=['world.owned_supply.enabled=true'],
        synthetic_grants=0,original_supply_formula_restored=False,candidate_sha256=info['candidate_sha256'],service_pid=base.listener(allow_players=True))
    save(release/'verification.json',result);return result

def apply(release):
    info=base.manifest(release);require(info['state']=='STAGED_NOT_INSTALLED','Qualified stage required')
    acceptance(Path(info['acceptance']),info['candidate_sha256'])
    require(base.sha(Path(info['tcp']))==info['tcp_sha256'] and base.sha(Path(info['balance_path']))==info['balance_sha256'],'TCP/balance evidence changed')
    require(base.sha(base.ACTIVE)==info['old_server_sha256'] and base.sha(base.CONFIG)==info['config_sha256_before'],'Managed files changed; restage')
    require(base.sha(release/'god2-server.candidate.exe')==info['candidate_sha256'] and
        base.sha(release/'server-config.candidate.json')==info['config_sha256_after'],'Staged managed files changed')
    database=Path(info['live_database']);require(base.snapshot(database)==base.snapshot(release/'accounts.before.db'),'Saves changed; restage')
    unchanged(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    pid=base.listener();base.stop(pid)
    if base.snapshot(database)!=base.snapshot(release/'accounts.before.db'):
        base.start();raise ValueError('Saves changed during stop; restage')
    try:
        base.backup(release/'town-diagnostic-accounts.db',database);shutil.copy2(release/'god2-server.candidate.exe',base.ACTIVE)
        shutil.copy2(release/'server-config.candidate.json',base.CONFIG);base.start()
        base.powershell("$deadline=(Get-Date).AddSeconds(15); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Server did not listen'}")
        result=verify(release);info['state']='INSTALLED_ENABLED';save(release/'manifest.json',info);return result
    except BaseException:
        base.powershell("Stop-ScheduledTask -TaskName 'GOD2 Local Server' -ErrorAction SilentlyContinue; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue); foreach($row in $rows){$p=Get-Process -Id $row.OwningProcess; if($p.Path -eq '"+str(base.ACTIVE).replace("'","''")+"'){Stop-Process -Id $p.Id}}")
        base.backup(release/'accounts.before.db',database);shutil.copy2(release/'god2-server.active-before.exe',base.ACTIVE)
        shutil.copy2(release/'server-config.active-before.json',base.CONFIG);base.start();raise

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('stage','apply','verify'))
    parser.add_argument('--release',type=Path,required=True);parser.add_argument('--acceptance',type=Path);parser.add_argument('--tcp',type=Path)
    args=parser.parse_args();release=args.release.resolve()
    if args.mode=='stage':
        require(args.acceptance and args.tcp,'Acceptance/TCP paths required');result=stage(release,args.acceptance.resolve(),args.tcp.resolve())
    else:result={'apply':apply,'verify':verify}[args.mode](release)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
