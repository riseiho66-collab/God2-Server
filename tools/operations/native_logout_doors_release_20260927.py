"""Install qualified native logout/delete and optional source-pinned door routes.

Code/config-only release: never replace the live account database.
"""
import argparse
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.operations import native_quest_catalog_release as managed

ROOT=managed.ROOT
CANDIDATE=ROOT/'build-town-visibility/Release/god2-server-native-results.exe'

def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def require(value,message):
    if not value:raise ValueError(message)

def accepted(path):
    value=json.loads(path.read_text('utf-8'))
    unchanged=value.get('source_unchanged') or (value.get('source_files_unchanged') and all(value['source_files_unchanged'].values()))
    require(unchanged and value.get('runner_exit')==0,'Unqualified private client receipt')
    require(value.get('ui',{}).get('accepted'),'Native UI did not accept the result')
    require(value.get('server_sha256')==managed.sha(CANDIDATE) and
            value.get('actual_server_sha256')==managed.sha(CANDIDATE),'Acceptance is for a different candidate')
    return value

def stage(args,release):
    logout=accepted(args.logout_receipt.resolve())
    require(logout.get('all_nonfixture_rows_preserved'),'Delete modified unrelated saved rows')
    doors=[accepted(p.resolve()) for p in args.door_receipt]
    if args.town_doors or args.kunlun_doors:
        areas={d['ui']['room_relogin']['native']['state']['world_map']['area'] for d in doors}
        if args.town_doors:require(2 in areas,'Town room roundtrip/relogin acceptance required')
        if args.kunlun_doors:require(4 in areas,'Kunlun room roundtrip/relogin acceptance required')
        require(args.presence_receipt is not None,'Room multiplayer acceptance required')
        presence=json.loads(args.presence_receipt.read_text('utf-8'))
        require(presence.get('accepted') and presence.get('ui',{}).get('accepted') and
                presence.get('server_sha256')==managed.sha(CANDIDATE) and
                all(presence.get('source_files_unchanged',{}).values()),'Unqualified room multiplayer receipt')
    release.mkdir(parents=True,exist_ok=False)
    before=json.loads(managed.CONFIG.read_text('utf-8'));database=Path(before['database']['path'])
    shutil.copy2(managed.ACTIVE,release/'god2-server.before.exe')
    shutil.copy2(CANDIDATE,release/'god2-server.candidate.exe')
    shutil.copy2(managed.CONFIG,release/'server-config.before.json')
    managed.backup(database,release/'accounts.before.db')
    managed.backup(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    config=json.loads(json.dumps(before));town=config['development']['diagnostic_town']
    if args.town_doors:
        town['all_door_routes']=True;town['indoor_scenes']=str(ROOT/'artifacts/world-atlas/town-doors-2.json')
    if args.kunlun_doors:
        town['kunlun_door_routes']=True;town['kunlun_indoor_scenes']=str(ROOT/'artifacts/world-atlas/kunlun-doors-4.json')
    write(release/'server-config.candidate.json',config)
    check=json.loads(json.dumps(config));check['database']['path']=str(release/'town-diagnostic-accounts.db')
    check['logging']['file']=str(release/'migration.log');write(release/'migration-config.json',check)
    with (release/'migration.stdout.log').open('wb') as log:
        subprocess.run([str(CANDIDATE),'--config',str(release/'migration-config.json'),'--migrate-only'],
                       cwd=ROOT,check=True,stdout=log,stderr=subprocess.STDOUT,creationflags=managed.FLAGS)
    require(managed.snapshot(release/'accounts.before.db')==managed.snapshot(release/'town-diagnostic-accounts.db'),
            'Code-only release attempted to change saved data')
    write(release/'manifest.json',{'candidate_sha256':managed.sha(CANDIDATE),'old_server_sha256':managed.sha(managed.ACTIVE),
        'config_sha256':managed.sha(managed.CONFIG),'client_sha256':managed.sha(managed.CLIENT),'database':str(database),
        'logout_receipt':str(args.logout_receipt.resolve()),'door_receipts':[str(p.resolve()) for p in args.door_receipt],
        'town_doors':args.town_doors,'kunlun_doors':args.kunlun_doors,'database_replacement':False,
        'presence_receipt':str(args.presence_receipt.resolve()) if args.presence_receipt else None})
    print(json.dumps({'staged':str(release),'database_unchanged':True}))

def apply(release):
    from tools.operations import verify_frozen_chat_20260927 as frozen
    frozen.main() # Owner freeze: reject drift before stopping the managed server.
    info=json.loads((release/'manifest.json').read_text('utf-8'));database=Path(info['database'])
    require(managed.sha(managed.ACTIVE)==info['old_server_sha256'] and managed.sha(managed.CONFIG)==info['config_sha256'],
            'Managed executable/config changed since staging')
    require(managed.sha(release/'god2-server.candidate.exe')==info['candidate_sha256'],'Candidate changed')
    pid=managed.listener();managed.stop(pid)
    try:
        managed.backup(database,release/'accounts.at-install.db')
        shutil.copy2(release/'god2-server.candidate.exe',managed.ACTIVE)
        shutil.copy2(release/'server-config.candidate.json',managed.CONFIG)
        managed.start()
        managed.powershell("$deadline=(Get-Date).AddSeconds(15); do {Start-Sleep -Milliseconds 300; "
            "$rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} "
            "while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Server did not listen'}")
    except BaseException:
        # Roll back code/config only. Never overwrite player data with an older backup.
        managed.powershell("Stop-ScheduledTask -TaskName 'GOD2 Local Server' -ErrorAction SilentlyContinue")
        try:managed.stop(managed.listener(allow_players=True))
        except (ValueError,subprocess.CalledProcessError):pass
        shutil.copy2(release/'god2-server.before.exe',managed.ACTIVE)
        shutil.copy2(release/'server-config.before.json',managed.CONFIG);managed.start();raise
    result={'candidate_installed':managed.sha(managed.ACTIVE)==info['candidate_sha256'],
        'client_unchanged':managed.sha(managed.CLIENT)==info['client_sha256'],
        'saved_database_unchanged':managed.snapshot(database)==managed.snapshot(release/'accounts.at-install.db'),
        'service_pid':managed.listener(allow_players=True),'town_doors':info['town_doors'],'kunlun_doors':info['kunlun_doors']}
    write(release/'verification.json',result)
    require(all(result[k] for k in ('candidate_installed','client_unchanged','saved_database_unchanged')),'Release verification failed')
    print(json.dumps(result))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('stage','apply'))
    parser.add_argument('--release-name',required=True);parser.add_argument('--logout-receipt',type=Path)
    parser.add_argument('--door-receipt',type=Path,action='append',default=[])
    parser.add_argument('--presence-receipt',type=Path)
    parser.add_argument('--town-doors',action='store_true');parser.add_argument('--kunlun-doors',action='store_true')
    args=parser.parse_args();require(args.release_name.startswith('native-logout-doors-') and
        '/' not in args.release_name and '\\' not in args.release_name,'Invalid release directory')
    release=ROOT/'artifacts/releases'/args.release_name
    if args.mode=='stage':require(args.logout_receipt is not None,'Logout acceptance receipt required');stage(args,release)
    else:apply(release)
