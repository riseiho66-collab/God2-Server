"""Actual Application -> Lua -> atomic SQLite -> native22, isolated own server."""
from contextlib import closing
import argparse
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from . import run_private_scene_actor_route as scene
from tools.operations.native_quest_catalog_release import snapshot

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,
        default=scene.ROOT/'artifacts/playtests/private-native-blackbox-character-growth-20260927-01')
    ap.add_argument('--wire-profession',type=int,choices=range(1,9),default=2)
    ap.add_argument('--reconnect',action='store_true');a=ap.parse_args()
    here=a.output.resolve()
    binary=scene.ROOT/'build-town-visibility/Release/god2-server-native-results.exe'
    formal=Path(json.loads(scene.CONFIG.read_text('utf-8'))['database']['path'])
    before=snapshot(formal);client_sha=scene.sha(scene.LIVE_CLIENT);private_sha=scene.sha(scene.CLIENT)
    source_sha=scene.sha(scene.SOURCE/'town-diagnostic-accounts.db')
    profession=[1,2,4,3][(a.wire_profession-1)//2]
    result={'accepted':False,'server_sha256':scene.sha(binary),'wire_profession':a.wire_profession,
            'catalog_profession':profession};server=runner=output=None
    try:
        db,cfg,_=scene.prepare(here)
        with closing(sqlite3.connect(db)) as c:
            c.execute('pragma foreign_keys=on')
            for table in ('battle_settlements','battle_checkpoints'):
                c.execute(f'delete from {table} where battle_id in (select id from battle_reservations where character_id=4)')
            c.execute('delete from battle_reservations where character_id=4')
            for table in ('character_role_snapshots','character_experience','character_resources'):c.execute(f'delete from {table} where character_id=4')
            c.execute('delete from world_monster_levels');c.execute('delete from world_display_records')
            profile=bytearray(c.execute('select profile from recovered_characters where id=4').fetchone()[0])
            profile[29]=a.wire_profession;profile[33]=(a.wire_profession-1)&1
            profile[38]=(profile[38]&0xf0)|profile[33]
            c.execute('update recovered_characters set profile=? where id=4',(bytes(profile),))
            c.execute('update recovered_positions set area=2,scene=15,x=18,y=12,revision=revision+1 where character_id=4');c.commit()
        destination=here/'diagnostic-accounts.db'
        if destination.exists() or db.parent.resolve()!=here:raise ValueError('Unexpected isolated database path')
        db.rename(destination);db=destination
        settings=json.loads((scene.ROOT/'artifacts/playtests/private-skill-ui-20260926-18/server-config.json').read_text('utf-8'))
        settings['database']['path']=str(db);settings['logging']['file']=str(here/'server.log')
        settings['server']['port']=2598;settings['server']['character_port']=0
        settings['development'].update(diagnostic_battle_experience=250,diagnostic_role_progress=True,
            diagnostic_progress_span=200,diagnostic_level_snapshot=True,diagnostic_character_growth=True,
            diagnostic_world_resources=True,diagnostic_battle_skill_seed=True,diagnostic_battle_skill_settlement=True)
        settings['development'].pop('diagnostic_town',None)
        settings['development']['recovered_navigation']=str(scene.ROOT/'artifacts/world-atlas/indoor-2-15.json')
        cfg.write_text(json.dumps(settings,indent=2),encoding='utf-8')
        server,output=scene.start(binary,here,cfg,native_records_lab=False)
        observer=[sys.executable,'-X','utf8','-B',str(scene.ROOT/'tools/strike_lab/private_character_growth_ui.py'),
                  str(here/'ui-result.json'),str(db),str(here/'server.log'),'--client-exe',str(scene.CLIENT),
                  '--profession',str(profession)]
        env=os.environ.copy();env['GOD2_PRIVATE_SIDECAR_COMMAND']=subprocess.list2cmdline(observer);env['GOD2_PRIVATE_SIDECAR_WAIT_MS']='110000'
        with (here/'runner.log').open('wb') as log:
            runner=subprocess.Popen([str(scene.RUNNER),str(scene.CLIENT),'127.0.0.1','127.0.0.1','6001','1'],cwd=scene.CLIENT.parent,
                env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));runner.wait(timeout=115)
        result['ui']=json.loads((here/'ui-result.json').read_text('utf-8'));result['accepted']=result['ui']['accepted']
        if result['accepted'] and a.reconnect:
            server.terminate();server.wait(timeout=5);output.close();output=None
            durable_before=snapshot(db)
            for key,value in list(settings['development'].items()):
                if key.startswith('diagnostic_battle_') and isinstance(value,bool):settings['development'][key]=False
            settings['development'].update(diagnostic_battle_experience=0,diagnostic_role_progress=False,
                diagnostic_progress_span=0,diagnostic_level_snapshot=False,diagnostic_character_growth=False)
            settings['logging']['file']=str(here/'restore-server.log')
            restore_cfg=here/'restore-config.json';restore_cfg.write_text(json.dumps(settings,indent=2),encoding='utf-8')
            server,output=scene.start(binary,here,restore_cfg,native_records_lab=False)
            restore_observer=[sys.executable,'-X','utf8','-B',str(scene.ROOT/'tools/strike_lab/private_character_growth_ui.py'),
                str(here/'restore-ui-result.json'),str(db),str(here/'restore-server.log'),'--client-exe',str(scene.CLIENT),
                '--profession',str(profession),'--restore']
            env['GOD2_PRIVATE_SIDECAR_COMMAND']=subprocess.list2cmdline(restore_observer)
            with (here/'restore-runner.log').open('wb') as log:
                runner=subprocess.Popen([str(scene.RUNNER),str(scene.CLIENT),'127.0.0.1','127.0.0.1','6001','1'],cwd=scene.CLIENT.parent,
                    env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));runner.wait(timeout=115)
            result['restore_ui']=json.loads((here/'restore-ui-result.json').read_text('utf-8'))
            result['durable_state_unchanged_on_reconnect']=snapshot(db)==durable_before
            result['accepted']=result['restore_ui']['accepted'] and result['durable_state_unchanged_on_reconnect']
    except Exception as error:result['error']=f'{type(error).__name__}: {error}'
    finally:
        for process in (runner,server):
            if process and process.poll() is None:process.terminate();process.wait(timeout=5)
        if output:output.close()
        result.update(live_database_unchanged=snapshot(formal)==before,live_client_unchanged=scene.sha(scene.LIVE_CLIENT)==client_sha,
            source_database_unchanged=scene.sha(scene.SOURCE/'town-diagnostic-accounts.db')==source_sha,private_client_unchanged=scene.sha(scene.CLIENT)==private_sha)
        result['accepted']=result['accepted'] and all(result[k] for k in ('live_database_unchanged','live_client_unchanged','source_database_unchanged','private_client_unchanged'))
        if here.exists():(here/'run-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('ui','restore_ui')}));return 0 if result['accepted'] else 1

if __name__=='__main__':raise SystemExit(main())
