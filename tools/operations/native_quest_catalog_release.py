"""Stage/apply/verify native quest source catalogs with owned-server rollback."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.strike_lab import import_native_quests as missions
from tools.strike_lab import import_native_quest_requirements as requirements
from tools.strike_lab import import_native_quest_sources as sources
from tools.strike_lab import import_native_multi_messages as multi_messages

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'artifacts/releases/town-chat-welcome-20260924/server-config.json'
ACTIVE=ROOT/'build-town-visibility/Release/god2-server.exe'
CANDIDATE=ROOT/'build-town-visibility/Release/god2-server-quest-catalog.exe'
READER=ROOT/'build-town-visibility/tests/Release/native-quest-catalog-reader.exe'
CLIENT=ROOT.parent/'God2/God2.exe'
FLAGS=getattr(subprocess,'CREATE_NO_WINDOW',0)
KNOWLEDGE=False

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def backup(source,target):
    with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True)) as original:
        with closing(sqlite3.connect(target)) as copied:original.backup(copied)
def snapshot(path):
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        if db.execute('pragma quick_check').fetchone()!=('ok',):raise ValueError('Database integrity failed')
        return {name:(sql,sorted(repr(row) for row in db.execute('select * from "'+name.replace('"','""')+'"')))
            for name,sql in db.execute("select name,sql from sqlite_master where type='table'").fetchall()}
def powershell(code):
    return subprocess.run(['powershell','-NoProfile','-NonInteractive','-Command',code],
        check=True,capture_output=True,text=True,creationflags=FLAGS)
def check_reader(database):
    result=subprocess.run([str(READER),str(database),'--source-records'],check=True,capture_output=True,text=True,creationflags=FLAGS)
    value=json.loads(result.stdout)
    if value['counts']!=[418,2014,169,85]:raise ValueError('Native C++ quest source counts mismatch')
    if KNOWLEDGE:
        multi=subprocess.run([str(ROOT/'build-town-visibility/tests/Release/native-multi-message.exe'),str(database)],check=True,capture_output=True,text=True,creationflags=FLAGS)
        if multi.stdout.strip()!='2995':raise ValueError('Native C++ MultiMessage source mismatch')
    return value
def manifest(release):return json.loads((release/'manifest.json').read_text('utf-8'))
def stage(release):
    release.mkdir(parents=True,exist_ok=False)
    config=json.loads(CONFIG.read_text('utf-8'));database=Path(config['database']['path'])
    shutil.copy2(ACTIVE,release/'god2-server.before.exe');shutil.copy2(CANDIDATE,release/'god2-server.candidate.exe')
    shutil.copy2(CONFIG,release/'server-config.before.json')
    backup(database,release/'accounts.before.db');backup(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    config['database']['path']=str(release/'town-diagnostic-accounts.db');config['logging']['file']=str(release/'migration.log')
    cfg=release/'stage-config.json';cfg.write_text(json.dumps(config),encoding='utf-8')
    subprocess.run([str(CANDIDATE),'--config',str(cfg),'--migrate-only'],cwd=ROOT,check=True,capture_output=True,creationflags=FLAGS)
    with closing(sqlite3.connect(release/'town-diagnostic-accounts.db')) as db:
        mission=missions.import_catalog(db,ROOT.parent/'God2')
        actmis=requirements.import_catalog(db,ROOT.parent/'God2')
        archive=sources.import_catalog(db,ROOT.parent/'God2')
        multi=multi_messages.import_catalog(db,ROOT.parent/'God2') if KNOWLEDGE else None
    output=check_reader(release/'town-diagnostic-accounts.db')
    info={'live_database':str(database),'old_server_sha256':sha(ACTIVE),'candidate_sha256':sha(CANDIDATE),
        'original_config_sha256':sha(CONFIG),'client_sha256':sha(CLIENT),
        'counts':output['counts'],'mission_import':mission,'actmis_import':actmis,'source_import':archive,
        'scope':'Native source/display catalog and D8 structural parsing only; no original acceptance/turn-in/reward rules fabricated'}
    if release.name.startswith('owned-quest-journal-'):
        info['scope']='Owned fifteen-slot journal snapshot persistence and world restoration. No quest acquisition/progression/reward rules or live journal grant.'
    if KNOWLEDGE:
        info['multi_message_import']=multi
        info['scope']='Pinned2995 MultiMessage keys and11794 CP950 source rows in formal DB, C++ key1434 validation, isolated native mode4/85 route remains disabled on live. No NPC spawn/quest event/reward authority restored.'
    (release/'manifest.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'staged':str(release),'counts':info['counts'],'gameplay_quests_restored':0}))
def stop(pid):
    powershell("$ErrorActionPreference='Stop'; Stop-ScheduledTask -TaskName 'GOD2 Local Server'; "
        f"if(Get-Process -Id {pid} -ErrorAction SilentlyContinue){{Stop-Process -Id {pid}}}")
def start():powershell("Start-ScheduledTask -TaskName 'GOD2 Local Server'")
def listener(allow_players=False):
    script="$ErrorActionPreference='Stop'; $rows=@(Get-NetTCPConnection -LocalPort 2592 -ErrorAction SilentlyContinue); "
    if not allow_players:script+="if(@($rows|Where-Object State -eq Established).Count){throw 'Player active; update retained without interruption'}; "
    script+="$list=@($rows|Where-Object State -eq Listen); if($list.Count -ne 1){throw 'Expected one managed listener'}; "
    script+="$p=Get-Process -Id $list[0].OwningProcess; @{pid=$p.Id;path=$p.Path}|ConvertTo-Json -Compress"
    info=json.loads(powershell(script).stdout)
    if Path(info['path'])!=ACTIVE:raise ValueError('Listener is not managed executable')
    return int(info['pid'])
def apply(release):
    info=manifest(release);database=Path(info['live_database'])
    if sha(ACTIVE)!=info['old_server_sha256'] or sha(CONFIG)!=info['original_config_sha256']:
        raise ValueError('Managed files changed since staging')
    if snapshot(database)!=snapshot(release/'accounts.before.db'):raise ValueError('Saved state changed since staging; restage')
    if sha(release/'god2-server.candidate.exe')!=info['candidate_sha256']:raise ValueError('Staged binary identity changed')
    check_reader(release/'town-diagnostic-accounts.db')
    pid=listener();stop(pid)
    if snapshot(database)!=snapshot(release/'accounts.before.db'):
        start();raise ValueError('Saved state changed while closing; restage')
    try:
        backup(release/'town-diagnostic-accounts.db',database)
        shutil.copy2(release/'god2-server.candidate.exe',ACTIVE);start()
        powershell("$deadline=(Get-Date).AddSeconds(15); do {Start-Sleep -Milliseconds 300; "
            "$rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} "
            "while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Server did not listen'}")
    except BaseException:
        powershell("Stop-ScheduledTask -TaskName 'GOD2 Local Server' -ErrorAction SilentlyContinue; "
            "$rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue); "
            "foreach($row in $rows){$p=Get-Process -Id $row.OwningProcess; "
            "if($p.Path -eq '"+str(ACTIVE).replace("'","''")+"'){Stop-Process -Id $p.Id}}")
        backup(release/'accounts.before.db',database);shutil.copy2(release/'god2-server.before.exe',ACTIVE);start();raise
    verify(release)
def verify(release):
    info=manifest(release);database=Path(info['live_database']);before=snapshot(release/'accounts.before.db');after=snapshot(database)
    allowed={'schema_migrations','native_data_sources','native_quest_requirement_display'}
    if KNOWLEDGE:allowed={'schema_migrations'}
    changed=[table for table in before if table not in allowed and before[table]!=after.get(table)]
    # Existing provenance/history rows may only be extended, never rewritten.
    for table in ('schema_migrations','native_data_sources'):
        if any(row not in after[table][1] for row in before[table][1]):changed.append(table)
    output=check_reader(database)
    result={'player_tables_changed':changed,'native_source_counts':output['counts'],'quick_check':'ok',
        'client_unchanged':sha(CLIENT)==info['client_sha256'],'active_binary_matches_candidate':sha(ACTIVE)==info['candidate_sha256'],
        'active_config_unchanged':sha(CONFIG)==info['original_config_sha256'],'service_pid':listener(allow_players=True),
        'gameplay_quests_restored':0}
    if release.name.startswith('owned-quest-journal-'):
        with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
            result['owned_quest_journal_rows']=db.execute('select count(*) from character_quest_journals').fetchone()[0]
    if KNOWLEDGE:
        with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
            result['multi_message_counts']=[db.execute('select count(*) from '+table).fetchone()[0] for table in multi_messages.TABLES]
            result['owned_quest_journal_rows']=db.execute('select count(*) from character_quest_journals').fetchone()[0]
        result['diagnostic_knowledge_menu_disabled']=not json.loads(CONFIG.read_text('utf-8'))['development'].get('diagnostic_knowledge_menu',False)
        if result['multi_message_counts']!=[3,2995,11794] or not result['diagnostic_knowledge_menu_disabled']:raise ValueError('Knowledge production scope mismatch')
    (release/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    if changed or not all(result[key] for key in ('client_unchanged','active_binary_matches_candidate','active_config_unchanged')):
        raise ValueError('Post-release comparison failed')
    print(json.dumps(result))
def main():
    global CANDIDATE,KNOWLEDGE
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=('stage','apply','verify'));ap.add_argument('--release-name',required=True)
    args=ap.parse_args()
    if not args.release_name.startswith(('native-quest-catalog-','owned-quest-journal-','knowledge-source-')) or '/' in args.release_name or '\\' in args.release_name:
        raise ValueError('Invalid release directory')
    if args.release_name.startswith('owned-quest-journal-'):
        CANDIDATE=ROOT/'build-town-visibility/Release/god2-server-quest-journal.exe'
    if args.release_name.startswith('knowledge-source-'):
        KNOWLEDGE=True
        CANDIDATE=ROOT/'build-town-visibility/Release/god2-server-knowledge-menu.exe'
    {'stage':stage,'apply':apply,'verify':verify}[args.mode](ROOT/'artifacts/releases'/args.release_name)
if __name__=='__main__':main()
