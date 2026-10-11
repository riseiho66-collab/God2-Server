"""Owned hidden clients: native parent crossing, kind1 presence and cold login.

Only a disposable SQLite clone changes. VM_READ observations and existing
PID-owned window messages; no foreground activation, injection or screenshots.
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
import hashlib
import re
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(Path(__file__).resolve().parent),str(ROOT)]
import private_weapon_peer_appearance_20260927 as peer
import private_scene_actor_route_ui as ground
import private_current_town_doors_20260927 as doors
import current_parent_ground_20260927 as parent_ground
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,type_ascii

BASE_PREPARE=peer.prepare
def prepare(args):
    BASE_PREPARE(args)
    config=json.loads((args.output/'server-config.json').read_text('utf-8'))
    town=config['development']['diagnostic_town']
    town.update(door_routes=True,all_door_routes=True,source_consensus=True,
        indoor_navigation=str(ROOT/'artifacts/world-atlas/indoor-2-15.json'),
        indoor_scenes=str(ROOT/'artifacts/world-atlas/town-doors-2.json'),
        island_navigation=str(ROOT/'artifacts/world-atlas/island01-full-navigation-2-0.json'),
        island_routes=args.area==2,player_visibility=True)
    if args.area==4:
        town.update(kunlun_parent_routes=True,
            kunlun_parent_navigation=str(ROOT/'artifacts/world-atlas/island03-full-navigation-4-0.json'))
    peer.dump(args.output/'server-config.json',config)
    with closing(sqlite3.connect(args.output/'town-diagnostic-accounts.db')) as db:
        positions=((4,4,56,75),(5,0,475,210)) if args.area==2 else ((4,3,50,123),(5,0,317,364))
        for identity,scene,x,y in positions:
            db.execute('INSERT INTO recovered_positions(character_id,area,scene,x,y,revision) VALUES(?,?,?,?,?,1)',(identity,args.area,scene,x,y))
        db.commit()
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'));fixture['parent_area']=args.area
    peer.dump(args.output/'fixture.json',fixture)

def worker(args):
    result={'accepted':False,'rendered_pixels_tested':False};clients=[];before=desktop_names()
    database=args.output/'town-diagnostic-accounts.db';log=args.output/'server.log'
    area=json.loads((args.output/'fixture.json').read_text('utf-8'))['parent_area']
    source_scene=4 if area==2 else 3
    entry=(55,75) if area==2 else (50,124)
    landing=(476,209) if area==2 else (318,363)
    moving=(474,209) if area==2 else (317,363)
    observer_point=(475,210) if area==2 else (317,364)
    exit_point=(477,209) if area==2 else (318,363)
    returned=(56,75) if area==2 else (50,124)
    def save():peer.dump(args.output/'ui-result.json',result)
    def saved(identity):
        with closing(peer.ro(database)) as db:
            return list(db.execute('SELECT area,scene,x,y,revision FROM recovered_positions WHERE character_id=?',(identity,)).fetchone())
    def preserved():
        # Every schema and every table except the intentional fixture position
        # changes, not just the six resource/companion tables.
        with closing(peer.ro(database)) as db:
            result={}
            for name,sql in db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"):
                quoted='"'+name.replace('"','""')+'"'
                rows=db.execute('SELECT * FROM '+quoted+(' WHERE character_id<>4' if name=='recovered_positions' else '')).fetchall()
                encoded=sorted(repr(row) for row in rows)
                result[name]={'schema':sql,'count':len(rows),'sha256':hashlib.sha256('\n'.join(encoded).encode()).hexdigest()}
            return result
    try:
        require(before['current'].startswith('God2Lab-') and before['input']!=before['current'],'HIDDEN_DESKTOP_REQUIRED')
        def launch(identity,scene):
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
            client['ui']=peer.find_ui(client['handle'],identity,(1 if scene==0 else 0,scene,area))
            result['owned_client_pids']=[c['process'].pid for c in clients];save();return client
        actor=launch(4,source_scene);observer=launch(5,0)
        with closing(peer.ro(database)) as db:names=dict(db.execute('SELECT id,name_bytes FROM recovered_characters WHERE id IN (4,5)'))
        stable=preserved();result['database_before']=stable
        def visible(client,identity):
            row=peer.remote(client['handle'],client['ui'],identity)
            if not row or not 0<=row['renderer']<4096:return None
            if names[identity] not in [bytes.fromhex(x).strip(b' ') for x in row['display_texts']]:return None
            return row
        require(peer.remote(actor['handle'],actor['ui'],5) is None and peer.remote(observer['handle'],observer['ui'],4) is None,'CROSS_SCENE_PEER_LEAK')
        result['initial_scene_isolation']=True;save()
        def travel(target,expected,label):
            state=ground.world_state(actor['handle'],actor['ui'])
            offset=len(log.read_text('utf-8',errors='replace'))
            geometry=parent_ground.ground_observation(actor['handle'],state,*target,read=peer.exact) if state['kind']==1 else None
            pixel=tuple(geometry['pixel']) if geometry else ground.ground_point(actor['handle'],state,*target)
            nav=doors.navigation_observation(actor,state,[target,[state['x'],state['y']]])
            native_input_before=doors.input_observation(actor,state)
            # Keep the native down state across render-loop sampling; the
            # two large owned clients may not consume a 30ms press in time.
            click(actor['hwnd'],*pixel,interval=.15)
            try:
                transition=state['scene']!=expected[1]
                # Original client can coalesce a first destination step with
                # its context receipt. Require that exact owned log evidence;
                # do not treat an arbitrary saved/native point as arrival.
                delta=(target[0]-state['x'],target[1]-state['y'])
                next_step=[expected[0],expected[1],expected[2]+delta[0],expected[3]+delta[1]]
                def effective_destination():
                    current=saved(4)[:4]
                    if current==expected:return current
                    if not transition or current!=next_step:return None
                    emitted=log.read_text('utf-8',errors='replace')[offset:]
                    commit=re.search(r'DIAGNOSTIC_DOOR_COMMITTED session_id=(\d+) source_scene='+str(state['scene'])+r' destination_scene='+str(expected[1]),emitted)
                    if not commit:return None
                    marker='DIAGNOSTIC_DOOR_PENDING_NEXT_MOVE session_id='+commit[1]+f' x={current[2]} y={current[3]} sequence=1'
                    if marker not in emitted or 'DIAGNOSTIC_TOWN_SCENE_CONTEXT_AND_MOVE_ACCEPTED session_id='+commit[1] not in emitted:return None
                    return current
                wait_until(effective_destination,14,label+'_SAVE')
                def native_ready():
                    now=ground.world_state(actor['handle'],actor['ui'])
                    destination=effective_destination()
                    if destination is None or [now[k] for k in ('area','scene','x','y')]!=destination:return None
                    if now['kind']!=(1 if expected[1]==0 else 0):return None
                    if doors.input_observation(actor,now)['movement_mode']!=0:return None
                    return now
                native=wait_until(native_ready,14,label+'_NATIVE')
                receipt=None
                if state['scene']!=expected[1]:
                    def acknowledged():
                        emitted=log.read_text('utf-8',errors='replace')[offset:]
                        commit=re.search(r'DIAGNOSTIC_DOOR_COMMITTED session_id=(\d+) source_scene='+str(state['scene'])+r' destination_scene='+str(expected[1]),emitted)
                        if not commit:return None
                        proof=re.search(r'DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED session_id='+commit[1]+r'; no_save_changes|DIAGNOSTIC_TOWN_SCENE_CONTEXT_AND_MOVE_ACCEPTED session_id='+commit[1],emitted[commit.end():])
                        return {'session_id':int(commit[1]),'commit':commit[0],'receipt':proof[0]} if proof else None
                    receipt=wait_until(acknowledged,14,label+'_CONTEXT_RECEIPT')
                time.sleep(2)
                return {'pixel':list(pixel),'geometry':geometry,'before':state,'native':native,'saved':saved(4),'pending_receipt':receipt,
                    'source_arrival':expected,'coalesced_native_first_step':effective_destination() if effective_destination()!=expected else None}
            finally:
                result.setdefault('clicks',[]).append({'label':label,'target':list(target),'saved':saved(4),
                  'pixel':list(pixel),'state_before':state,'native_navigation':nav,'input_before':native_input_before,
                  'state_after':ground.world_state(actor['handle'],actor['ui']),
                  'input_after':doors.input_observation(actor,ground.world_state(actor['handle'],actor['ui'])),
                  'server_records':log.read_text('utf-8',errors='replace')[offset:]});save()
        result['entry']=travel(entry,[area,0,*landing],'ISLAND_ENTRY');save()
        result['actor_sees_peer']=wait_until(lambda:visible(actor,5),14,'ISLAND_PEER5_MISSING')
        result['peer_sees_actor']=wait_until(lambda:visible(observer,4),14,'ISLAND_ACTOR4_MISSING');save()
        require((result['actor_sees_peer']['x'],result['actor_sees_peer']['y'])==observer_point,'PEER_POSITION_MISMATCH')
        result['movement']=travel(moving,[area,0,*moving],'ISLAND_MOVE')
        result['remote_movement']=wait_until(lambda:(row if row and (row['x'],row['y'])==moving else None)
            if (row:=visible(observer,4)) else None,14,'ISLAND_REMOTE_MOVE_MISSING');save()
        peer.close_client(actor)
        wait_until(lambda:peer.remote(observer['handle'],observer['ui'],4) is None,14,'DISCONNECTED_PEER_NOT_REMOVED')
        actor=launch(4,0)
        require(saved(4)[:4]==[area,0,*moving],'ISLAND_COLD_SAVE_MISMATCH')
        result['cold_restore']=ground.world_state(actor['handle'],actor['ui'])
        require([result['cold_restore'][k] for k in ('area','scene','kind','x','y')]==[area,0,1,*moving],'ISLAND_COLD_NATIVE_MISMATCH')
        result['cold_actor_peer']=wait_until(lambda:visible(actor,5),14,'COLD_PEER5_MISSING')
        result['cold_observer_peer']=wait_until(lambda:visible(observer,4),14,'COLD_ACTOR4_MISSING');save()
        if area==2:result['exit_approach']=travel(landing,[area,0,*landing],'ISLAND_APPROACH')
        result['return']=travel(exit_point,[area,source_scene,*returned],'TOWN_RETURN')
        wait_until(lambda:peer.remote(actor['handle'],actor['ui'],5) is None and peer.remote(observer['handle'],observer['ui'],4) is None,14,'RETURN_SCENE_PEER_LEAK')
        result['returned_scene_isolation']=True
        result['database_after']=preserved()
        require(result['database_after']==stable,'UNRELATED_SAVED_STATE_CHANGED')
        require(log.read_text('utf-8',errors='replace').count('DIAGNOSTIC_DOOR_COMMITTED')==2,'TRANSFER_COMMIT_COUNT')
        result['accepted']=True
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
    parser.add_argument('--area',type=int,choices=(2,4),default=2)
    args=parser.parse_args()
    if args.worker:raise SystemExit(worker(args))
    paths=[ROOT/'artifacts/releases/town-chat-welcome-20260924/server-config.json',
           ROOT/('artifacts/world-atlas/island01-full-navigation-2-0.json' if args.area==2 else 'artifacts/world-atlas/island03-full-navigation-4-0.json'),
           ROOT/'scripts/gameplay/diagnostic_door.lua']
    before={str(p):peer.fixture.sha(p) for p in paths}
    peer.prepare=prepare;peer.__file__=str(Path(__file__).resolve());status=peer.owner(args)
    receipt=args.output/'run-result.json'
    if receipt.exists():
        value=json.loads(receipt.read_text('utf-8'))
        value['actual_server_sha256']=peer.fixture.sha(args.server_candidate)
        value['route_sources_before']=before
        value['route_sources_unchanged']={str(p):peer.fixture.sha(p)==before[str(p)] for p in paths}
        value['accepted']=bool(value['accepted'] and value['server_sha256']==value['actual_server_sha256'] and all(value['route_sources_unchanged'].values()))
        peer.dump(receipt,value);status=0 if value['accepted'] else 1
    raise SystemExit(status)
