"""Own-server71/72/78 scene-arrival route, with explicitly isolated operands.

The fixture copies an accepted current-client save/catalog. It never edits the
live server save/config/client, and does not call these placements native.
Socket checks are protocol regressions, not rendered-client acceptance.
"""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import socket
import sqlite3
import struct
import subprocess
import sys
import time

from .run_private_owned_companions import ROOT, CLIENT, LIVE_CLIENT, RUNNER, sha

SOURCE = ROOT/'artifacts/playtests/private-native-blackbox-20260927-14'
CONFIG = ROOT/'artifacts/releases/town-chat-welcome-20260924/server-config.json'


def prepare(here):
    here=here.resolve()
    if not here.name.startswith('private-native-blackbox-'):
        raise ValueError('Explicit isolated lab directory required')
    here.mkdir(parents=True,exist_ok=False)
    if not json.loads((SOURCE/'run-result.json').read_text('utf-8'))['accepted']:
        raise ValueError('Accepted source fixture required')
    db=here/'town-diagnostic-accounts.db'
    with closing(sqlite3.connect((SOURCE/db.name).resolve().as_uri()+'?mode=ro',uri=True)) as source:
        with closing(sqlite3.connect(db)) as target:source.backup(target)
    expected={}
    with closing(sqlite3.connect(db)) as c:
        templates=c.execute('select opcode,logical from world_display_records order by opcode').fetchall()
        if [r[0] for r in templates]!=[0x71,0x72]:raise ValueError('Synthetic source records unavailable')
        c.execute('pragma foreign_keys=on')
        c.execute('delete from world_monster_levels');c.execute('delete from world_display_records')
        c.execute('update recovered_positions set area=2,scene=4,x=86,y=71,revision=revision+1 where character_id=4')
        for scene,points in ((4,((87,72),(87,71))),(15,((18,19),(17,19)))):
            raw_rows={}
            for (opcode,template),(x,y) in zip(templates,points):
                raw=bytearray(template);offset=9 if opcode==0x71 else 17
                low=struct.unpack_from('<I',raw,offset)[0]&3
                struct.pack_into('<I',raw,offset,(y<<17)|(x<<2)|low)
                identity=struct.unpack_from('<H',raw,1)[0]
                c.execute('insert into world_display_records values(?,?,?,?,?,?,?,?)',
                    (2,scene,opcode,identity,bytes(raw),'ISOLATED_TEST_ONLY',
                     'scene arrival regression: supplied operands, not original spawn positions',
                     '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'))
                raw_rows[opcode]=bytes(raw)
            c.execute('insert into world_monster_levels(area,scene,identity,level,origin,provenance) values(?,?,?,?,?,?)',
                (2,scene,123,27,'ISOLATED_TEST_ONLY','scene arrival regression: supplied level27, not original monster level'))
            expected[scene]=raw_rows[0x71]+bytes((0x78,123,0,27,0))+raw_rows[0x72]
        c.commit()
        if c.execute('pragma quick_check').fetchone()!=('ok',):raise ValueError('Fixture integrity failed')
    cfg=json.loads((SOURCE/'server-config.json').read_text('utf-8'))
    cfg['server']['port']=2598;cfg['server']['character_port']=0
    cfg['database']['path']=str(db);cfg['logging']['file']=str(here/'server.log')
    for key,value in list(cfg['development'].items()):
        if key.startswith('diagnostic_battle_') and isinstance(value,bool):cfg['development'][key]=False
    cfg['development']['diagnostic_quest_dialogue']=False
    cfg['development']['native_monster_placements_only']=True
    cfg['development']['diagnostic_town'].update(native_npc_placements_only=True,door_routes=True,
        battle_after_quest=False,door_after_battle=False,return_after_battle=False,player_visibility=False)
    cfg.setdefault('world',{}).setdefault('clock',{})['enabled']=False
    path=here/'server-config.json';path.write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8')
    return db,path,expected


def start(binary,here,config,*,native_records_lab=True):
    env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1';env['GOD2_NATIVE_WORLD_RECORDS_LAB']='1' if native_records_lab else '0'
    output=(here/'stdout.log').open('wb')
    process=subprocess.Popen([str(binary),'--config',str(config),'--run-for','120'],cwd=ROOT,env=env,
        stdout=output,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    deadline=time.monotonic()+10
    while True:
        if process.poll() is not None:
            output.close();raise RuntimeError('Isolated server exited: '+(here/'stdout.log').read_text('utf-8',errors='replace')[-1500:])
        try:
            with socket.create_connection(('127.0.0.1',2598),timeout=.1):break
        except OSError:
            if time.monotonic()>deadline:
                process.terminate();process.wait(timeout=5);output.close();raise RuntimeError('Isolated listener missing')
            time.sleep(.05)
    return process,output


def socket_route(db,expected):
    sys.path.insert(0,str(ROOT/'tests/research'))
    import test_recovered_dual_connection_server as dual
    from test_current_world_ready_builder import current_world_ready_wire
    from test_current_movement import movement_wire
    from test_town_player_visibility_server import TownPlayerVisibilityServerTests as visibility
    dual.RecoveredDualConnectionServerTests.setUpClass()
    h=dual.RecoveredDualConnectionServerTests('test_explicit_character_port_matches_05_and_accepts_g')
    result={'scope':'Own-server TCP regression, real-format producer operands; no rendered-client claim','arrivals':[]}
    with h.connect(('127.0.0.1',2598)) as login:
        h.handshake(login);login.sendall(h.frame(*dual.credential(4,b'codexslow',b'labtest2345')))
        h.read_frame(login,0x1d,176);h.read_frame(login,4,8)
        address=h.read_frame(login,5,12);port=int.from_bytes(address[9:11],'little')
        h.read_frame(login,6,8);h.read_frame(login,0x0a,20);h.list_characters(login)
        with h.connect(('127.0.0.1',port)) as game:
            h.handshake(game,game=True);game.sendall(h.frame(*dual.credential(0,b'codexslow',b'labtest2345')))
            h.read_frame(game,0x1f,128);game.sendall(h.frame(0x1a,dual.selection_payload(0)))
            h.read_frame(game,2,26);h.read_frame(game,0x2a,40)
            game.sendall(current_world_ready_wire(4));h.silent(game)
            game.sendall(h.frame(0x30,b'\0'))
            found=False
            while True:
                try:raw=visibility.logical(h,game)
                except socket.timeout:break
                if raw==expected[4]:found=True
            if not found:raise AssertionError('Initial supplied71/72/78 projection absent')
            game.sendall(movement_wire(86,70,1));h.read_frame(game,0x5d,5);h.read_frame(game,0x61,12)
            # A pending-arrival tick must not install destination actors early.
            game.sendall(h.frame(0x30,b'\0'));h.silent(game)
            began=time.monotonic();game.sendall(h.frame(0x1c,b'\x01\0\0\0'))
            raw=visibility.logical(h,game)
            if raw!=expected[15]:raise AssertionError('Indoor actor/level projection missing at arrival')
            result['arrivals'].append({'scene':15,'elapsed_seconds':time.monotonic()-began,'logical_hex':raw.hex()})
            # No periodic tick in this scene: return immediately via the real
            # native-format movement and the qualified owned door route.
            game.sendall(movement_wire(16,20,1));h.read_frame(game,0x5d,5);h.read_frame(game,0x61,12)
            began=time.monotonic()
            move=bytes((0x2e,87,0,71,0,1,0))
            game.sendall(h.frame(0x1c,b'\x04\0\x01\0'+move))
            h.read_frame(game,0x5d,5)  # First-step ACK remains first.
            raw=visibility.logical(h,game)
            if raw!=expected[4]:raise AssertionError('Rapid outdoor return lost actors/level')
            result['arrivals'].append({'scene':4,'elapsed_seconds':time.monotonic()-began,'logical_hex':raw.hex(),'first_step_ack_before_projection':True})
            # Already projected state is not retransmitted on idle ticks.
            game.sendall(h.frame(0x30,b'\0'))
            while True:
                try:raw=visibility.logical(h,game)
                except socket.timeout:break
                if raw==expected[4]:raise AssertionError('Idle tick duplicated actor projection')
            game.sendall(movement_wire(88,71,2));h.read_frame(game,0x5d,5)
    with closing(sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True)) as c:
        result['saved_position']=list(c.execute('select area,scene,x,y,revision from recovered_positions where character_id=4').fetchone())
        if result['saved_position'][:4]!=[2,4,88,71]:raise AssertionError('Continued movement did not persist')
        if c.execute('pragma quick_check').fetchone()!=('ok',):raise AssertionError('Integrity failed')
    result['accepted']=True;return result


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--binary',type=Path,default=ROOT/'build-town-visibility/Release/god2-server-native-results.exe')
    ap.add_argument('--current-client',action='store_true',help='Use the real client on a private desktop instead of the synthetic TCP peer')
    a=ap.parse_args();here=a.output.resolve();result={'accepted':False,'server_sha256':sha(a.binary)}
    live=json.loads(CONFIG.read_text('utf-8'));live_db=Path(live['database']['path'])
    from tools.operations.native_quest_catalog_release import snapshot
    before=snapshot(live_db);client=ROOT.parent/'God2/God2.exe';client_sha=sha(client)
    source_sha=sha(SOURCE/'town-diagnostic-accounts.db');private_client_sha=sha(CLIENT)
    process=output=runner=None
    try:
        db,cfg,expected=prepare(here);process,output=start(a.binary.resolve(),here,cfg)
        before_world={name:snapshot(db)[name] for name in ('world_display_records','world_monster_levels')}
        if a.current_client:
            observer=[sys.executable,'-X','utf8','-B',str(ROOT/'tools/strike_lab/private_scene_actor_route_ui.py'),
                str(here/'ui-result.json'),str(db),str(here/'server.log'),'--client-exe',str(CLIENT)]
            env=os.environ.copy();env['GOD2_PRIVATE_SIDECAR_COMMAND']=subprocess.list2cmdline(observer)
            env['GOD2_PRIVATE_SIDECAR_WAIT_MS']='100000'
            with (here/'runner.log').open('wb') as log:
                runner=subprocess.Popen([str(RUNNER),str(CLIENT),'127.0.0.1','127.0.0.1','6001','1'],
                    cwd=CLIENT.parent,env=env,stdout=log,stderr=subprocess.STDOUT,
                    creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));runner.wait(timeout=105)
            result['route']=json.loads((here/'ui-result.json').read_text('utf-8'))
            result['private_desktop_runner_exit']=runner.returncode
        else:result['route']=socket_route(db,expected)
        result['world_records_unchanged']=before_world=={name:snapshot(db)[name] for name in before_world}
        result['accepted']=result['route']['accepted'] and result['world_records_unchanged']
    except Exception as error:result['error']=f'{type(error).__name__}: {error}'
    finally:
        for child in (runner,process):
            if child and child.poll() is None:child.terminate();child.wait(timeout=5)
        if output:output.close()
        result['live_database_unchanged']=snapshot(live_db)==before
        result['live_client_unchanged']=sha(client)==client_sha
        result['source_database_unchanged']=sha(SOURCE/'town-diagnostic-accounts.db')==source_sha
        result['private_client_unchanged']=sha(CLIENT)==private_client_sha
        result['private_client_sha256']=private_client_sha
        result['accepted']=result['accepted'] and result['live_database_unchanged'] and result['live_client_unchanged'] and result['source_database_unchanged'] and result['private_client_unchanged']
        if here.exists():(here/'run-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='route'}));return 0 if result['accepted'] else 1

if __name__=='__main__':raise SystemExit(main())
