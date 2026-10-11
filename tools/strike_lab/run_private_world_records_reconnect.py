"""Reopen persisted isolated71/72/78 fixtures on a fresh hidden desktop.

No seed/import resets, screenshots, desktop switching or live DB writes.
"""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import time
from .run_private_owned_companions import ROOT,CLIENT,LIVE_CLIENT,RUNNER,sha

def records(db):
    with closing(sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True)) as c:
        return {'displays':[(a,s,op,i,raw.hex(),origin,p) for a,s,op,i,raw,origin,p in c.execute(
            'select area,scene,opcode,identity,logical,origin,provenance from world_display_records order by opcode')],
            'levels':c.execute('select * from world_monster_levels order by identity').fetchall()}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--battle',action='store_true');a=ap.parse_args()
    here=a.output.resolve();here.mkdir(parents=True,exist_ok=False)
    if not here.name.startswith('private-native-blackbox-'):raise ValueError('Named isolated lab required')
    source=a.source.resolve();db=here/'town-diagnostic-accounts.db'
    if not json.loads((source/'run-result.json').read_text('utf-8'))['accepted']:raise ValueError('Prior accepted run required')
    with closing(sqlite3.connect((source/db.name).as_uri()+'?mode=ro',uri=True)) as c:
        with closing(sqlite3.connect(db)) as target:c.backup(target)
    cfg=json.loads((source/'server-config.json').read_text('utf-8'))
    if a.battle:
        cfg=json.loads((ROOT/'artifacts/playtests/private-skill-ui-20260926-18/server-config.json').read_text('utf-8'))
        cfg['development']['native_monster_placements_only']=False
        cfg['development']['diagnostic_battle_resources']=True
        cfg['development']['diagnostic_battle_after_movement']=False
        with closing(sqlite3.connect(db)) as c:
            c.execute('update recovered_positions set area=2,scene=15,x=18,y=12,revision=revision+1 where character_id=4');c.commit()
    cfg['database']['path']=str(db);cfg['logging']['file']=str(here/'server.log')
    config=here/'server-config.json';config.write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    binary=ROOT/'build-town-visibility/Release/god2-server-native-results.exe'
    result={'accepted':False,'source_db_sha256':sha(source/db.name),'live_client_sha256':sha(LIVE_CLIENT),
        'private_client_sha256':sha(CLIENT),'server_sha256':sha(binary),'persisted_records_before':records(db)}
    env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1';env['GOD2_NATIVE_WORLD_RECORDS_LAB']='1'
    flags=getattr(subprocess,'CREATE_NO_WINDOW',0);server=runner=None
    try:
        with (here/'stdout.log').open('wb') as output:
            server=subprocess.Popen([str(binary),'--config',str(config),'--run-for','100'],cwd=ROOT,
                env=env,stdout=output,stderr=subprocess.STDOUT,creationflags=flags)
            deadline=time.monotonic()+10
            while True:
                if server.poll() is not None:raise RuntimeError('Private server exited')
                try:
                    with socket.create_connection(('127.0.0.1',2598),timeout=.1):break
                except OSError:
                    if time.monotonic()>deadline:raise RuntimeError('Private server did not listen')
                    time.sleep(.1)
            observer=[sys.executable,'-X','utf8','-B',str(ROOT/'tools/strike_lab'/
                ('private_native_delta_ui.py' if a.battle else 'private_owned_companions_ui.py')),
                str(here/'ui-result.json'),str(db),str(here/'server.log'),'--client-exe',str(CLIENT)]
            if not a.battle:observer.extend(['--expect-kunlun','--expect-native-world-records'])
            private=os.environ.copy();private['GOD2_PRIVATE_SIDECAR_COMMAND']=subprocess.list2cmdline(observer)
            private['GOD2_PRIVATE_SIDECAR_WAIT_MS']='90000'
            with (here/'runner.log').open('wb') as output:
                runner=subprocess.Popen([str(RUNNER),str(CLIENT),'127.0.0.1','127.0.0.1','6001','1'],
                    cwd=CLIENT.parent,env=private,stdout=output,stderr=subprocess.STDOUT,creationflags=flags)
                runner.wait(timeout=90)
            result['ui']=json.loads((here/'ui-result.json').read_text('utf-8'))
            result['persisted_records_after']=records(db)
            result['accepted']=result['ui']['accepted'] and result['persisted_records_after']==result['persisted_records_before']
    finally:
        for child in (runner,server):
            if child and child.poll() is None:child.terminate();child.wait(timeout=5)
        result['source_db_unchanged']=sha(source/db.name)==result['source_db_sha256']
        result['live_client_unchanged']=sha(LIVE_CLIENT)==result['live_client_sha256']
        result['private_client_unchanged']=sha(CLIENT)==result['private_client_sha256']
        (here/'run-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('accepted','source_db_unchanged','live_client_unchanged')}))
    return 0 if result['accepted'] else 1
if __name__=='__main__':raise SystemExit(main())
