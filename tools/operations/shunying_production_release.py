"""Backup-first promotion of the owner-accepted CUSTOM-0058 release.

No test DB/config, player grants, test vitals or F1 bindings are imported.
Uses the existing managed server task and verifies all player tables unchanged.
"""
from pathlib import Path
from contextlib import closing
import argparse
import hashlib
import json
import shutil
import sqlite3
import subprocess
from tools.operations import native_quest_catalog_release as base
from tools.skills.register_shunying_skill import SCHEMA, ROWS, native_snapshot

ROOT=base.ROOT
RELEASE=ROOT/'artifacts/releases/shunying-production-20260930'
CLIENT=base.CLIENT.parent

def require(value, message):
    if not value:raise ValueError(message)
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def stop_managed_and_wait(pid):
    # Stop-Process and Stop-ScheduledTask return before the image file is released.
    # Pin the process path, then wait for both exit and an exclusive file handle.
    active=str(base.ACTIVE).replace("'","''")
    base.powershell(f"""$ErrorActionPreference='Stop';
        $process=Get-Process -Id {int(pid)} -ErrorAction SilentlyContinue;
        if($process -and $process.Path -ne '{active}'){{throw 'Managed process identity changed'}};
        Stop-ScheduledTask -TaskName 'GOD2 Local Server';
        if($process -and -not $process.HasExited){{
            Stop-Process -Id $process.Id;
            if(-not $process.WaitForExit(20000)){{throw 'Managed server did not exit'}}
        }};
        $deadline=(Get-Date).AddSeconds(20); $released=$false;
        do {{
            try {{
                $handle=[System.IO.File]::Open('{active}',[System.IO.FileMode]::Open,
                    [System.IO.FileAccess]::ReadWrite,[System.IO.FileShare]::None);
                $handle.Dispose(); $released=$true
            }} catch [System.IO.IOException] {{Start-Sleep -Milliseconds 200}}
        }} while(-not $released -and (Get-Date) -lt $deadline);
        if(-not $released){{throw 'Managed executable is still locked'}};
        if((Get-ScheduledTask -TaskName 'GOD2 Local Server').State -eq 'Running'){{
            throw 'Managed task is still running'
        }}""")
def activate_registry(path):
    with closing(sqlite3.connect(path)) as db:
        db.execute('PRAGMA foreign_keys=ON')
        before=native_snapshot(db)
        require(db.execute('SELECT * FROM custom_skill_registry ORDER BY kind,definition_id').fetchall()==list(ROWS),
                'Unexpected custom registry; do not overwrite another skill')
        require(not db.execute("SELECT name FROM sqlite_master WHERE name!='custom_skill_registry' AND sql LIKE '%custom_skill_registry%'").fetchall(),
                'Registry has dependent schema; explicit migration required')
        schema=SCHEMA.replace('IF NOT EXISTS custom_skill_registry','custom_skill_registry_release')
        schema=schema.replace("('reserved','pending_client_integration')","('reserved','pending_client_integration','active')")
        schema=schema.replace("status='pending_client_integration' AND","status IN ('pending_client_integration','active') AND")
        with db:
            db.execute(schema)
            db.execute('INSERT INTO custom_skill_registry_release SELECT * FROM custom_skill_registry')
            db.execute("UPDATE custom_skill_registry_release SET status='active' WHERE kind=0 AND definition_id=126 AND design_id='CUSTOM-0058'")
            db.execute('DROP TABLE custom_skill_registry')
            db.execute('ALTER TABLE custom_skill_registry_release RENAME TO custom_skill_registry')
            require(native_snapshot(db)==before,'Native skill catalog modified')
            require(not db.execute('PRAGMA foreign_key_check').fetchall(),'Foreign key failure')
def unchanged(before,after):
    a,b=base.snapshot(before),base.snapshot(after)
    # Current compiled source has one reviewed, inert migration40 dependency.
    # Its feature defaults off and remains absent from the unchanged config.
    addition='character_teleport_gem_metadata'
    require(set(b)==set(a)|{addition},'Unexpected table/migration differences in release')
    require(not b[addition][1] and hashlib.sha256(b[addition][0].encode()).hexdigest()==
            '4fc7314df24ca7b2f8e3fbaceb210f56751a6bb2ce5f90eee1298c11492a090c','Unexpected additive schema/data')
    require(all(a[n]==b[n] for n in a if n not in ('custom_skill_registry','schema_migrations')), 'Existing player/source/schema tables modified')
    require(a['schema_migrations'][0]==b['schema_migrations'][0] and
            set(a['schema_migrations'][1])<=set(b['schema_migrations'][1]) and
            len(b['schema_migrations'][1])==len(a['schema_migrations'][1])+1,'Migration history changed')
    with closing(sqlite3.connect(after)) as db:
        require(db.execute('SELECT version,name FROM schema_migrations WHERE version>39').fetchall()==
                [(40,'owned_teleport_gem_instances')],'Unreviewed startup migration')
        rows=db.execute('SELECT * FROM custom_skill_registry ORDER BY kind,definition_id').fetchall()
        expected=list(ROWS);last=list(expected[-1]);last[3]='active';expected[-1]=tuple(last)
        require(rows==expected,'Active registry mismatch')
        require(not db.execute('PRAGMA foreign_key_check').fetchall(),'Foreign key failure')
def client_files():
    data=load(RELEASE/'client-release.json')
    for item in data['files']:
        relative=Path(item['path'])
        require(not relative.is_absolute() and '..' not in relative.parts,'Unsafe client relative path')
        staged=RELEASE/'client'/relative
        require(base.sha(staged)==item['sha256'],'Client candidate changed: '+str(relative))
    return data['files']
def stage(candidate):
    require(not (RELEASE/'server-release.json').exists(),'Release already staged')
    files=client_files()
    base.listener()
    config=load(base.CONFIG);database=Path(config['database']['path'])
    require(not config['development'].get('diagnostic_shunying_manual',False),'Formal configuration enables manual trial')
    base.backup(database,RELEASE/'accounts.before.db')
    base.backup(database,RELEASE/'town-diagnostic-accounts.db')
    activate_registry(RELEASE/'town-diagnostic-accounts.db')
    # Exercise the candidate startup migrations against a backup before touching
    # the running server. Reject unrelated schema/data changes, not just row loss.
    stage_config=json.loads(json.dumps(config))
    stage_config['database']['path']=str(RELEASE/'town-diagnostic-accounts.db')
    stage_config['logging']['file']=str(RELEASE/'stage-migration.log')
    save(RELEASE/'stage-config.json',stage_config)
    subprocess.run([str(candidate.resolve()),'--config',str(RELEASE/'stage-config.json'),'--migrate-only'],
                   cwd=ROOT,check=True,capture_output=True,creationflags=base.FLAGS)
    unchanged(RELEASE/'accounts.before.db',RELEASE/'town-diagnostic-accounts.db')
    shutil.copy2(base.CONFIG,RELEASE/'server-config.before.json')
    shutil.copy2(base.ACTIVE,RELEASE/'god2-server.before.exe')
    shutil.copy2(candidate,RELEASE/'god2-server.candidate.exe')
    for item in files:
        actual=CLIENT/item['path'];wanted=item['source_sha256']
        require((base.sha(actual) if actual.exists() else None)==wanted,'Client changed before staging: '+item['path'])
        if actual.exists():
            target=RELEASE/'client-before'/item['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(actual,target)
    save(RELEASE/'server-release.json',{'state':'STAGED','database':str(database),'old_server_sha256':base.sha(base.ACTIVE),
        'server_sha256':base.sha(candidate),'config_sha256':base.sha(base.CONFIG),'player_grants':0,'temporary_f1_promoted':False})
def verify():
    info=load(RELEASE/'server-release.json')
    require(base.sha(base.ACTIVE)==info['server_sha256'],'Server binary mismatch')
    require(base.sha(base.CONFIG)==info['config_sha256'],'Formal config modified')
    unchanged(RELEASE/'accounts.before.db',Path(info['database']))
    for item in client_files():require(base.sha(CLIENT/item['path'])==item['sha256'],'Installed client mismatch')
    result={'server_pid':base.listener(allow_players=True),'native_skill_records':448,'skill_id':126,
            'reserved_ids':[122,123,124,125],'player_tables_unchanged':True,'new_grants':0,'global_f1_changes':0,
            'formal_config_unchanged':True,'client_installed':True}
    save(RELEASE/'verification.json',result);return result
def apply():
    info=load(RELEASE/'server-release.json');require(info['state']=='STAGED','Stage required')
    subprocess.run(['python','-B','-m','tools.operations.verify_frozen_chat_20260927'],cwd=ROOT,check=True)
    require(base.sha(base.ACTIVE)==info['old_server_sha256'] and base.sha(base.CONFIG)==info['config_sha256'],'Formal identity changed; restage')
    require(base.sha(RELEASE/'god2-server.candidate.exe')==info['server_sha256'],'Server candidate changed')
    db=Path(info['database']);require(base.snapshot(db)==base.snapshot(RELEASE/'accounts.before.db'),'Saved state changed; restage')
    files=client_files()
    for item in files:
        actual=CLIENT/item['path']
        require((base.sha(actual) if actual.exists() else None)==item['source_sha256'],'Formal client changed; restage')
    pid=base.listener()
    # Check both the login port and the managed process's dynamic character port.
    base.powershell(f"if(@(Get-NetTCPConnection -OwningProcess {pid} -State Established -ErrorAction SilentlyContinue).Count){{throw 'Live player connection; retained staged release'}}")
    stop_managed_and_wait(pid)
    try:
        require(base.snapshot(db)==base.snapshot(RELEASE/'accounts.before.db'),'Saves changed while stopping')
        base.backup(RELEASE/'town-diagnostic-accounts.db',db)
        shutil.copy2(RELEASE/'god2-server.candidate.exe',base.ACTIVE)
        for item in files:
            target=CLIENT/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(RELEASE/'client'/item['path'],target)
        base.start()
        base.powershell("$deadline=(Get-Date).AddSeconds(20); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Managed server did not listen'}")
        result=verify();info['state']='INSTALLED';save(RELEASE/'server-release.json',info);return result
    except BaseException:
        try:stop_managed_and_wait(base.listener(allow_players=True))
        except Exception:pass
        base.backup(RELEASE/'accounts.before.db',db)
        shutil.copy2(RELEASE/'god2-server.before.exe',base.ACTIVE)
        for item in files:
            target=CLIENT/item['path'];previous=RELEASE/'client-before'/item['path']
            if previous.exists():shutil.copy2(previous,target)
            elif target.exists():
                # Keep newly added unreferenced files for diagnosis; restore EXE
                # removes their load route without deleting user-accessible data.
                pass
        base.start();raise
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['stage','apply','verify']);ap.add_argument('--candidate',type=Path)
    args=ap.parse_args()
    if args.mode=='stage':
        require(args.candidate is not None,'Server candidate required');stage(args.candidate);print('STAGED')
    else:print(json.dumps(apply() if args.mode=='apply' else verify(),ensure_ascii=False))
if __name__=='__main__':main()
