"""Deploy the explicitly requested CUSTOM-0054 cosmetics with preserved saves."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import struct
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.operations import native_quest_catalog_release as managed
from tools.operations import verify_frozen_chat_20260927 as frozen
ROOT=managed.ROOT
RELEASE=ROOT/'artifacts/releases/streamer-privilege-20260927-01'
CANDIDATE=ROOT/'build-town-visibility/Release/god2-server-native-results.exe'
RECEIPT=ROOT/'artifacts/playtests/private-streamer-bold-20260927-03/run-result.json'
MODULE=ROOT.parent/'Launcher-src/launcher-native/build/Release/x86/StreamerStyle/candidate.json'

def require(value,message):
    if not value:raise RuntimeError(message)

def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def preserved(before,after):
    with closing(sqlite3.connect(before)) as old,closing(sqlite3.connect(after)) as new:
        require(new.execute('PRAGMA quick_check').fetchone()==('ok',),'Database integrity')
        tables=[r[0] for r in old.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for name in tables:
            quoted='"'+name.replace('"','""')+'"'
            cols=[r[1] for r in old.execute('PRAGMA table_info('+quoted+')')]
            selected=','.join('"'+c.replace('"','""')+'"' for c in cols)
            a=sorted(repr(r) for r in old.execute('SELECT '+selected+' FROM '+quoted))
            b=sorted(repr(r) for r in new.execute('SELECT '+selected+' FROM '+quoted))
            require(all(r in b for r in a) if name=='schema_migrations' else a==b,'Saved rows changed: '+name)
        rows=new.execute('SELECT id,profile,streamer_privilege FROM recovered_characters').fetchall()
        for identity,profile,value in rows:
            name=bytes(profile).split(b'\0')[0]
            require(value==({b'test':1,b'test1':2}.get(name,0)),'Unexpected initial privilege assignment')

def main():
    evidence=json.loads(RECEIPT.read_text('utf-8'));module=json.loads(MODULE.read_text('utf-8'))
    require(evidence['accepted'] and evidence['ui']['accepted'],'Native acceptance required')
    require(evidence['server_sha256']==managed.sha(CANDIDATE),'Server candidate drift')
    private=Path(module['candidate']).resolve()
    require(managed.sha(private)==module['candidate_sha256']==evidence['before']['private_client'],'Client candidate drift')
    require(managed.sha(managed.CLIENT)==module['source_sha256'],'Production client changed')
    # The old dispatch must differ by exactly the authorized presentation annotation.
    old_baseline=json.loads(frozen.BASELINE.read_text('utf-8'))
    source=(ROOT/'src/core/Application.cpp').read_text('utf-8');end=source.index(frozen.END);start=source.rfind(frozen.START,0,end)
    annotation='                                            if(config.streamer_privileges_enabled)\n                                                StreamerPresentation::annotate(deliveries.back().logical,speaker->streamer_privilege);\n'
    block=source[start:end];require(block.count(annotation)==1,'Expected isolated presentation annotation')
    require(hashlib.sha256(block.replace(annotation,'').encode()).hexdigest()==old_baseline['source_sha256']['src/core/Application.cpp: native chat dispatch'],'Unrelated chat change')
    for name in ('src/protocol/RecoveredChat.h','src/game/DiagnosticDoorRule.h'):
        require(managed.sha(ROOT/name)==old_baseline['source_sha256'][name],'Frozen contract changed')
    RELEASE.mkdir(exist_ok=False)
    config=json.loads(managed.CONFIG.read_text('utf-8'));database=Path(config['database']['path'])
    for origin,name in ((managed.CLIENT,'God2.before.exe'),(managed.ACTIVE,'god2-server.before.exe'),(managed.CONFIG,'server-config.before.json'),(CANDIDATE,'god2-server.candidate.exe'),(MODULE,'client-module.json'),(RECEIPT,'native-acceptance.json')):shutil.copy2(origin,RELEASE/name)
    production=bytearray(private.read_bytes());needle=bytes.fromhex('68 26 0a 00 00 68 9c 47 5b 00')
    require(production.count(needle)==1,'Private port pin');at=production.index(needle);struct.pack_into('<I',production,at+1,2592)
    (RELEASE/'God2.candidate.exe').write_bytes(production)
    config['development']['streamer_privileges']=True
    write(RELEASE/'server-config.candidate.json',config)
    # Update the formal DB in place; no test database is installed.
    pid=managed.listener(allow_players=True);managed.stop(pid)
    try:
        managed.backup(database,RELEASE/'accounts.at-install.db')
        with (RELEASE/'migration.log').open('wb') as log:
            subprocess.run([str(CANDIDATE),'--config',str(managed.CONFIG),'--migrate-only'],cwd=ROOT,check=True,stdout=log,stderr=subprocess.STDOUT,creationflags=managed.FLAGS)
        with closing(sqlite3.connect(database)) as db:
            rows=db.execute('SELECT id,profile FROM recovered_characters').fetchall()
            for name,style in ((b'test',1),(b'test1',2)):
                ids=[identity for identity,profile in rows if bytes(profile).split(b'\0')[0]==name]
                require(len(ids)==1,'Exact character assignment must be unique')
                db.execute('UPDATE recovered_characters SET streamer_privilege=? WHERE id=?',(style,ids[0]))
            db.commit()
        preserved(RELEASE/'accounts.at-install.db',database)
        shutil.copy2(RELEASE/'God2.candidate.exe',managed.CLIENT)
        shutil.copy2(RELEASE/'god2-server.candidate.exe',managed.ACTIVE)
        shutil.copy2(RELEASE/'server-config.candidate.json',managed.CONFIG)
        managed.start()
        managed.powershell("$deadline=(Get-Date).AddSeconds(15);do {Start-Sleep -Milliseconds 300;$rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline);if($rows.Count -ne 1){throw 'Server did not listen'}")
    except BaseException:
        managed.powershell("Stop-ScheduledTask -TaskName 'GOD2 Local Server' -ErrorAction SilentlyContinue")
        try:managed.stop(managed.listener(allow_players=True))
        except Exception:pass
        shutil.copy2(RELEASE/'God2.before.exe',managed.CLIENT)
        shutil.copy2(RELEASE/'god2-server.before.exe',managed.ACTIVE)
        shutil.copy2(RELEASE/'server-config.before.json',managed.CONFIG)
        # Additive column remains safe for the old binary; never replace player saves.
        managed.start();raise
    result={'deployed':True,'server_pid':managed.listener(allow_players=True),'server_sha256':managed.sha(managed.ACTIVE),'client_sha256':managed.sha(managed.CLIENT),'database':str(database),'existing_rows_preserved':True,'native_acceptance':str(RECEIPT),'assignments':{'test':1,'test1':2},'database_replaced':False}
    write(RELEASE/'verification.json',result)
    write(RELEASE/'frozen-chat.json',{'current_client_accepted':True,'authority':'Owner-requested CUSTOM-0054; original dispatch verified unchanged except metadata annotation','source_sha256':frozen.hashes(),'acceptance':str(RECEIPT),'previous_baseline':str(frozen.BASELINE)})
    print(json.dumps(result))

if __name__=='__main__':main()
