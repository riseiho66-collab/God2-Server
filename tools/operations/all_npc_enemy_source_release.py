"""Promote complete RAM-qualified display catalogs, preserving all player data."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
from tools.operations import native_quest_catalog_release as base
from tools.strike_lab import import_native_enemy_display as enemy
from tools.strike_lab import import_native_npc_display as npc
CANDIDATE=base.ROOT/'build-town-visibility/Release/god2-server-fruit.exe'
NEW={'character_fruit_quest_balances','character_fruit_quest_progress','qualified_fruit_quest_sources',
     'native_npc_display_sources','native_npc_display_rows'}
def require(ok,message):
    if not ok:raise ValueError(message)
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def unchanged(before_path,after_path):
    before,after=base.snapshot(before_path),base.snapshot(after_path)
    require(set(after)==set(before)|NEW,'Unexpected table additions')
    for name in before:
        if name in {'schema_migrations','native_data_sources','native_enemy_display_catalog'}:
            require(before[name][0]==after[name][0] and set(before[name][1])<=set(after[name][1]),'Existing source/history modified')
        else:require(before[name]==after[name],'Existing table modified: '+name)
    with closing(sqlite3.connect(after_path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        require(db.execute('SELECT max(version) FROM schema_migrations').fetchone()==(33,),'Schema33 required')
        require(db.execute('SELECT count(*),sum(lookup_visible) FROM native_enemy_display_catalog').fetchone()==(7815,7791),'Enemy counts mismatch')
        require(db.execute('SELECT count(*) FROM native_npc_display_rows').fetchone()==(4043,),'NPC count mismatch')
        require(db.execute('SELECT count(*) FROM native_npc_display_sources').fetchone()==(1,),'NPC source count mismatch')
        for table in ('character_fruit_quest_balances','character_fruit_quest_progress','qualified_fruit_quest_sources'):
            require(db.execute('SELECT count(*) FROM '+table).fetchone()==(0,),'Unrequested fruit state/source grant')
        require(not db.execute('PRAGMA foreign_key_check').fetchall(),'Foreign keys failed')
        require(db.execute('SELECT * FROM native_npc_display_sources').fetchall()==[npc.source_row()],'NPC source mismatch')
        require(db.execute('SELECT * FROM native_npc_display_rows ORDER BY npc_key').fetchall()==npc.pinned_rows(base.CLIENT.parent),'NPC whole-source mismatch')
        require(db.execute('SELECT dataset_id,source_record_index,source_line,source_offset,record_sha256,raw_record,area_generation,area,scene,ordinal,lookup_visible,source_label,name_bytes FROM native_enemy_display_catalog ORDER BY source_record_index').fetchall()==enemy.pinned_rows(base.CLIENT.parent),'Enemy whole-source mismatch')
    def objects(path):
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
            return dict(db.execute("SELECT name,sql FROM sqlite_master WHERE type IN ('index','trigger')"))
    a,b=objects(before_path),objects(after_path)
    require(all(b.get(k)==v for k,v in a.items()),'Existing indexes/triggers changed')
def stage(release):
    base.listener();require(not release.exists(),'Release already exists')
    config=json.loads(base.CONFIG.read_text('utf-8'));database=Path(config['database']['path'])
    require(not config.get('world',{}).get('fruit_village_quests',{}).get('enabled',False),'Inferred gameplay must remain gated')
    release.mkdir(parents=True)
    shutil.copy2(base.ACTIVE,release/'god2-server.before.exe');shutil.copy2(CANDIDATE,release/'god2-server.candidate.exe')
    shutil.copy2(base.CONFIG,release/'server-config.before.json')
    base.backup(database,release/'accounts.before.db');base.backup(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    cfg=json.loads(json.dumps(config));cfg['database']['path']=str(release/'town-diagnostic-accounts.db');cfg['logging']['file']=str(release/'startup.log')
    cfg['server']['port']=2597;cfg['server']['character_port']=0
    with socket.socket() as probe:require(probe.connect_ex(('127.0.0.1',2597))!=0,'Stage port occupied')
    path=release/'stage-config.json';save(path,cfg)
    subprocess.run([str(CANDIDATE),'--config',str(path),'--migrate-only'],cwd=base.ROOT,check=True,capture_output=True,creationflags=base.FLAGS,timeout=30)
    with closing(sqlite3.connect(release/'town-diagnostic-accounts.db')) as db:
        imports={'enemy':enemy.import_catalog(db,base.CLIENT.parent),'npc':npc.install(db,base.CLIENT.parent)}
    unchanged(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    subprocess.run([str(CANDIDATE),'--config',str(path),'--run-for','1'],cwd=base.ROOT,check=True,capture_output=True,creationflags=base.FLAGS,timeout=30)
    text=(release/'startup.log').read_text('utf-8')
    require('NATIVE_NPC_DISPLAY_READY records=4043' in text and 'NATIVE_ENEMY_DISPLAY_READY records=7815 visible=7791 groups=96' in text,'Actual startup C++ qualification failed')
    unchanged(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    info={'state':'STAGED','live_database':str(database),'old_server_sha256':base.sha(base.ACTIVE),
        'candidate_sha256':base.sha(CANDIDATE),'original_config_sha256':base.sha(base.CONFIG),'client_sha256':base.sha(base.CLIENT),
        'source_imports':imports,'scope':'Complete native NPC/EnyName display catalogs. Original spawn/direction/combat stats remain unqualified; inferred fruit gameplay disabled.'}
    save(release/'manifest.json',info);return info
def verify(release):
    info=base.manifest(release);unchanged(release/'accounts.before.db',Path(info['live_database']))
    require(base.sha(base.ACTIVE)==info['candidate_sha256'] and base.sha(base.CONFIG)==info['original_config_sha256'] and base.sha(base.CLIENT)==info['client_sha256'],'Managed identities changed')
    result={'state':'INSTALLED_SOURCE_ONLY','schema_version':33,'npc_records':4043,'enemy_display_records':7815,
        'enemy_lookup_visible':7791,'enemy_lookup_groups':96,'player_tables_changed':[],
        'original_spawns_restored':0,'original_combat_formulas_restored':0,'inferred_fruit_gameplay_enabled':False,
        'client_unchanged':True,'config_unchanged':True,'service_pid':base.listener(allow_players=True)}
    save(release/'verification.json',result);return result
def apply(release):
    info=base.manifest(release);require(info['state']=='STAGED','Stage required')
    require(base.sha(base.ACTIVE)==info['old_server_sha256'] and base.sha(base.CONFIG)==info['original_config_sha256'],'Managed files changed; restage')
    require(base.sha(release/'god2-server.candidate.exe')==info['candidate_sha256'],'Candidate changed')
    database=Path(info['live_database']);require(base.snapshot(database)==base.snapshot(release/'accounts.before.db'),'Saves changed; restage')
    unchanged(release/'accounts.before.db',release/'town-diagnostic-accounts.db')
    pid=base.listener();base.stop(pid)
    if base.snapshot(database)!=base.snapshot(release/'accounts.before.db'):
        base.start();raise ValueError('Save changed during stop; restage')
    try:
        base.backup(release/'town-diagnostic-accounts.db',database);shutil.copy2(release/'god2-server.candidate.exe',base.ACTIVE);base.start()
        base.powershell("$deadline=(Get-Date).AddSeconds(15); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Server did not listen'}")
        result=verify(release);info['state']='INSTALLED_SOURCE_ONLY';save(release/'manifest.json',info);return result
    except BaseException:
        base.powershell("Stop-ScheduledTask -TaskName 'GOD2 Local Server' -ErrorAction SilentlyContinue; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue); foreach($row in $rows){$p=Get-Process -Id $row.OwningProcess; if($p.Path -eq '"+str(base.ACTIVE).replace("'","''")+"'){Stop-Process -Id $p.Id}}")
        base.backup(release/'accounts.before.db',database);shutil.copy2(release/'god2-server.before.exe',base.ACTIVE);base.start();raise
def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('stage','apply','verify'));p.add_argument('--release',type=Path,required=True);a=p.parse_args()
    print(json.dumps({'stage':stage,'apply':apply,'verify':verify}[a.mode](a.release.resolve()),indent=2))
if __name__=='__main__':main()
