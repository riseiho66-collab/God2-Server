"""Stage/install native daily display sources and tested gated runtime.

No source-derived availability, live issued lists, NPC coordinates or rewards.
Preserve every existing table, trigger/index, account, save, config and client.
"""
import argparse
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
from tools.operations import native_quest_catalog_release as base
from tools.strike_lab import import_native_daily_quest_parsed as parsed

CANDIDATE=base.ROOT/'build-town-visibility/Release/god2-server-owned-daily-20260927-final.exe'
TABLES={'native_daily_quest_parsed','character_daily_quest_lists'}

def require(value,message):
    if not value:raise ValueError(message)

def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')

def source_check(path):
    reader=base.ROOT/'build-town-visibility/tests/Release/native-quest-catalog-reader.exe'
    output=subprocess.run([str(reader),str(path),'--daily-parsed'],check=True,capture_output=True,text=True,creationflags=base.FLAGS)
    require(json.loads(output.stdout)==dict(rows=85,authority='NATIVE_PARSED_DISPLAY_ONLY',gameplay_quests_restored=0),'C++ source qualification failed')
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        require(db.execute('select max(version) from schema_migrations').fetchone()==(30,),'Schema30 required')
        require(db.execute('select count(*) from character_daily_quest_lists').fetchone()==(0,),'Live list autogrant refused')
        require(not db.execute('pragma foreign_key_check').fetchall(),'Foreign-key check failed')

def unchanged(before_path,after_path):
    before,after=base.snapshot(before_path),base.snapshot(after_path)
    require(not [n for n in before if n!='schema_migrations' and before[n]!=after.get(n)],'Existing saved/source table changed')
    require(set(after)-set(before)==TABLES-set(before),'Unexpected schema tables')
    require(before['schema_migrations'][0]==after['schema_migrations'][0] and set(before['schema_migrations'][1]).issubset(after['schema_migrations'][1]),'Existing migration history changed')
    def objects(path):
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
            return dict(db.execute("select name,sql from sqlite_master where type in ('trigger','index')"))
    previous,current=objects(before_path),objects(after_path)
    require(all(current.get(n)==sql for n,sql in previous.items()),'Existing indexes/triggers changed')
    source_check(after_path)

def acceptance(path,candidate):
    value=json.loads((path/'run-result.json').read_text('utf-8'))
    require(value['accepted'] and value['server_sha256']==candidate,'Actual-client acceptance candidate mismatch')
    require(value['all_clients_closed'] and value['desktop_unchanged'],'Actual-client isolation/cleanup required')
    ui=value['ui']
    require(ui['accepted'] and len(ui['stages'])==2 and not ui['native_state_diff'] and not ui['database_diff'],'Actual daily UI/state acceptance required')
    require(all(s['gameplay_state_unchanged'] and s['disabled_row_did_not_send'] and len(s['requests'])==2 for s in ui['stages']),'Incomplete daily UI lifecycle')
    require(all(value['source_files_unchanged'].values()) and value['candidate_unchanged'] and value['owned_server_closed'] and value['owned_runner_closed'],'Source/candidate/cleanup changed')
    return value

def stage(release,accepted,tcp):
    qualified=acceptance(accepted,base.sha(CANDIDATE))
    tcp_value=json.loads(tcp.read_text('utf-8'))
    require(tcp_value['status']=='PASS' and tcp_value['server_sha256']==base.sha(CANDIDATE) and
        len(tcp_value['cases'])==21 and all(c['status']=='PASS' and c['database_unchanged'] for c in tcp_value['cases']) and
        len(tcp_value['startup_denials'])==3 and all(c['returncode']==1 and c['database_unchanged'] for c in tcp_value['startup_denials']),
        'Same-candidate TCP acceptance required')
    config=json.loads(base.CONFIG.read_text('utf-8'));database=Path(config['database']['path'])
    require(not config.get('world',{}).get('owned_daily_quest_views',{}).get('enabled',False),'Production daily fixtures must remain disabled')
    release.mkdir(parents=True,exist_ok=False)
    shutil.copy2(base.ACTIVE,release/'god2-server.active-before.exe');shutil.copy2(CANDIDATE,release/'god2-server.candidate.exe')
    shutil.copy2(base.CONFIG,release/'server-config.active-before.json')
    base.backup(database,release/'accounts.before.db');base.backup(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    config['database']['path']=str(release/'town-diagnostic-accounts.db');config['logging']['file']=str(release/'migration.log')
    cfg=release/'stage-config.json';save(cfg,config)
    subprocess.run([str(CANDIDATE),'--config',str(cfg),'--migrate-only'],cwd=base.ROOT,check=True,capture_output=True,creationflags=base.FLAGS)
    with closing(sqlite3.connect(release/'town-diagnostic-accounts.db')) as db:imported=parsed.import_catalog(db,base.ROOT.parent/'God2')
    unchanged(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    info=dict(state='STAGED_NOT_INSTALLED',live_database=str(database),candidate_sha256=base.sha(CANDIDATE),
        client_sha256=base.sha(base.CLIENT),old_server_sha256=base.sha(base.ACTIVE),config_sha256=base.sha(base.CONFIG),
        acceptance=str(accepted),tcp=str(tcp),tcp_sha256=base.sha(tcp),source_import=imported,
        scope='Native85 display sources and gated owned D7/FD views. D8 intents unresolved; no live lists, NPC transport, reward or quest authority.')
    save(release/'manifest.json',info);return info

def verify(release):
    info=base.manifest(release);database=Path(info['live_database'])
    unchanged(release/'accounts.before.db',database)
    require(base.sha(base.ACTIVE)==info['candidate_sha256'],'Active executable changed')
    require(base.sha(base.CONFIG)==info['config_sha256'] and base.sha(base.CLIENT)==info['client_sha256'],'Config/client changed')
    config=json.loads(base.CONFIG.read_text('utf-8'))
    require(not config.get('world',{}).get('owned_daily_quest_views',{}).get('enabled',False),'Daily fixture activation refused')
    result=dict(state='INSTALLED_GATED',schema_version=30,parsed_daily_rows=85,owned_daily_lists=0,
        pre_existing_tables_changed=[],client_unchanged=True,config_unchanged=True,gameplay_quests_restored=0,
        candidate_sha256=info['candidate_sha256'],service_pid=base.listener(allow_players=True))
    save(release/'verification.json',result);return result

def apply(release):
    info=base.manifest(release);require(info['state']=='STAGED_NOT_INSTALLED','Qualified staged release required')
    acceptance(Path(info['acceptance']),info['candidate_sha256'])
    require(base.sha(Path(info['tcp']))==info['tcp_sha256'],'TCP evidence changed')
    require(base.sha(base.ACTIVE)==info['old_server_sha256'] and base.sha(base.CONFIG)==info['config_sha256'],'Managed files changed; restage')
    require(base.sha(release/'god2-server.candidate.exe')==info['candidate_sha256'],'Staged executable changed')
    database=Path(info['live_database']);require(base.snapshot(database)==base.snapshot(release/'accounts.before.db'),'Saves changed; restage')
    unchanged(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    pid=base.listener();base.stop(pid)
    if base.snapshot(database)!=base.snapshot(release/'accounts.before.db'):
        base.start();raise ValueError('Saves changed during stop; restage')
    try:
        base.backup(release/'town-diagnostic-accounts.db',database)
        shutil.copy2(release/'god2-server.candidate.exe',base.ACTIVE);base.start()
        base.powershell("$deadline=(Get-Date).AddSeconds(15); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Server did not listen'}")
        result=verify(release);info['state']='INSTALLED_GATED';save(release/'manifest.json',info);return result
    except BaseException:
        base.powershell("Stop-ScheduledTask -TaskName 'GOD2 Local Server' -ErrorAction SilentlyContinue; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue); foreach($row in $rows){$p=Get-Process -Id $row.OwningProcess; if($p.Path -eq '"+str(base.ACTIVE).replace("'","''")+"'){Stop-Process -Id $p.Id}}")
        base.backup(release/'accounts.before.db',database);shutil.copy2(release/'god2-server.active-before.exe',base.ACTIVE);base.start();raise

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('stage','apply','verify'))
    parser.add_argument('--release',type=Path,required=True);parser.add_argument('--acceptance',type=Path);parser.add_argument('--tcp',type=Path)
    args=parser.parse_args();release=args.release.resolve()
    if args.mode=='stage':
        require(args.acceptance and args.tcp,'Acceptance/TCP paths required');result=stage(release,args.acceptance.resolve(),args.tcp.resolve())
    else:result={'apply':apply,'verify':verify}[args.mode](release)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
