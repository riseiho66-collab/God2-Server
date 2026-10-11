"""Two owned hidden clients qualify room kind2 presence and movement.

Only disposable fixture positions change. Client access is VM_READ and
PID-owned window messages; the input desktop and official servers are unused.
"""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import traceback
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent));sys.path.insert(0,str(ROOT))
import private_weapon_peer_appearance_20260927 as peer
import private_scene_actor_route_ui as ground
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,type_ascii

BASE_PREPARE=peer.prepare
def prepare(args):
    BASE_PREPARE(args)
    config=json.loads((args.output/'server-config.json').read_text('utf-8'))
    town=config['development']['diagnostic_town']
    town.update(door_routes=True,all_door_routes=True,kunlun_door_routes=True,source_consensus=True,
        indoor_navigation=str(ROOT/'artifacts/world-atlas/indoor-2-15.json'),
        indoor_scenes=str(ROOT/'artifacts/world-atlas/town-doors-2.json'),
        kunlun_indoor_scenes=str(ROOT/'artifacts/world-atlas/kunlun-doors-4.json'),player_visibility=True)
    peer.dump(args.output/'server-config.json',config)
    with closing(sqlite3.connect(args.output/'town-diagnostic-accounts.db')) as db:
        for identity,x in ((4,11),(5,12)):
            db.execute('INSERT INTO recovered_positions(character_id,area,scene,x,y,revision) VALUES(?,2,5,?,12,1)',(identity,x))
        db.commit()

def worker(args):
    result={'accepted':False,'rendered_pixels_tested':False};clients=[];before=desktop_names()
    def save():peer.dump(args.output/'ui-result.json',result)
    try:
        require(before['current'].startswith('God2Lab-') and before['input']!=before['current'],'HIDDEN_DESKTOP_REQUIRED')
        def launch(identity):
            process=subprocess.Popen([str(peer.fixture.CLIENT),'127.0.0.1','127.0.0.1','6001','1'],
                cwd=peer.fixture.CLIENT.parent,creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            client={'process':process,'identity':identity};clients.append(client)
            hwnd=wait_until(lambda:peer.window_for(process.pid),35,'OWNED_WINDOW_MISSING');client['hwnd']=hwnd
            time.sleep(2);click(hwnd,512,464);time.sleep(3)
            click(hwnd,437,232);type_ascii(hwnd,'codexslow' if identity==4 else 'codexfixed')
            click(hwnd,437,263);type_ascii(hwnd,'labtest2345')
            click(hwnd,452,304);time.sleep(4);click(hwnd,330,145);click(hwnd,452,413);time.sleep(4)
            click(hwnd,330,150);click(hwnd,452,376);time.sleep(4);click(hwnd,452,370);time.sleep(8)
            client['handle']=peer.kernel.OpenProcess(0x1010,False,process.pid);require(client['handle'],'VM_READ_OPEN_FAILED')
            client['ui']=peer.find_ui(client['handle'],identity,(2,5,2))
            return client
        actor=launch(4);observer=launch(5);result['owned_client_pids']=[c['process'].pid for c in clients]
        database=args.output/'town-diagnostic-accounts.db'
        with closing(peer.ro(database)) as db:names=dict(db.execute('SELECT id,name_bytes FROM recovered_characters WHERE id IN (4,5)'))
        def visible(client,identity):
            row=peer.remote(client['handle'],client['ui'],identity)
            if not row or row['renderer']<0:return None
            if names[identity] not in [bytes.fromhex(x).strip(b' ') for x in row['display_texts']]:return None
            return row
        result['actor_sees_peer']=wait_until(lambda:visible(actor,5),12,'ROOM_PEER5_MISSING')
        result['peer_sees_actor']=wait_until(lambda:visible(observer,4),12,'ROOM_ACTOR4_MISSING');save()
        require((result['actor_sees_peer']['x'],result['actor_sees_peer']['y'])==(12,12),'PEER_POSITION_MISMATCH')
        require((result['peer_sees_actor']['x'],result['peer_sees_actor']['y'])==(11,12),'ACTOR_POSITION_MISMATCH')
        stable=peer.db_stable(database)
        state=ground.world_state(actor['handle'],actor['ui'])
        click(actor['hwnd'],*ground.ground_point(actor['handle'],state,12,12))
        def moved():
            state=ground.world_state(actor['handle'],actor['ui']);row=visible(observer,4)
            with closing(peer.ro(database)) as db:saved=db.execute('SELECT area,scene,x,y FROM recovered_positions WHERE character_id=4').fetchone()
            if saved!=(2,5,12,12) or (state['x'],state['y'])!=(12,12) or not row or (row['x'],row['y'])!=(12,12):return None
            return {'saved':list(saved),'native':state,'remote':row}
        result['movement']=wait_until(moved,12,'ROOM_REMOTE_MOVEMENT_MISSING')
        require(peer.db_stable(database)==stable,'UNRELATED_SAVED_STATE_CHANGED')
        peer.close_client(observer)
        wait_until(lambda:peer.remote(actor['handle'],actor['ui'],5) is None,12,'ROOM_DISCONNECTED_PEER_NOT_REMOVED')
        result['disconnect_removal']=True;result['accepted']=True
    except Exception as error:result['error']=str(error);result['traceback']=traceback.format_exc()
    finally:
        for client in clients:
            try:peer.close_client(client)
            except Exception as error:result['cleanup_error']=str(error)
        result['desktop_unchanged']=desktop_names()==before
        result['all_clients_closed']=all(c['process'].poll() is not None for c in clients)
        result['accepted']=bool(result['accepted'] and result['desktop_unchanged'] and result['all_clients_closed'] and not result.get('cleanup_error'));save()
    return 0 if result['accepted'] else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--server-candidate',type=Path);parser.add_argument('--worker',action='store_true');parser.add_argument('--prepare-only',action='store_true')
    args=parser.parse_args()
    if args.worker:raise SystemExit(worker(args))
    peer.prepare=prepare;peer.__file__=str(Path(__file__).resolve());raise SystemExit(peer.owner(args))
