"""Hidden original-client room crossing and cold restore; VM_READ observation only.

Uses the explicitly authorized existing CreateDesktop/PostMessage harness.
Only a SQLite backup's position is relocated; no client injection/memory write,
screenshots, desktop switching, or persistent save/config changes.
"""
import argparse
import hashlib
from contextlib import closing
import json
import os
import re
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]
import psutil
import struct
import private_owned_supply_20260927 as harness
harness.SOURCE=ROOT/'artifacts/playtests/private-skill-family-cast-20260927-05/town-diagnostic-accounts.db'
import private_weapon_peer_appearance_20260927 as shared
import private_daily_quest_20260927 as daily
import private_scene_actor_route_ui as viewport
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click
from tools.strike_lab import run_private_owned_companions as fixture


def prepare(args):
    args.output.mkdir(parents=True,exist_ok=False)
    require(fixture.sha(fixture.LIVE_CLIENT)==fixture.CURRENT_CLIENT_SHA,'CURRENT_CLIENT_PIN')
    source=fixture.LIVE_CLIENT.read_bytes()
    import struct
    expected=bytearray(source);site=source.index(bytes.fromhex('68 20 0a 00 00 68 9c 47 5b 00'))
    expected[site+1:site+5]=struct.pack('<I',2598)
    require(fixture.CLIENT.read_bytes()==expected,'PRIVATE_EXE_NOT_EXACT_PORT_COPY')
    area=args.area;outdoor_scene=4 if area==2 else 3
    bundle_path=ROOT/('artifacts/world-atlas/town-doors-2.json' if area==2 else 'artifacts/world-atlas/kunlun-doors-4.json')
    bundle=json.loads(bundle_path.read_text())
    route=next(r for r in bundle['routes'] if r['scene']==args.scene)
    require(0<=args.pair_index<len(route['pairs']),'UNREGISTERED_PAIR_INDEX')
    pair=route['pairs'][args.pair_index]
    database=args.output/'town-diagnostic-accounts.db'
    with closing(shared.ro(harness.SOURCE)) as source_db,closing(sqlite3.connect(database)) as target:source_db.backup(target)
    config=json.loads(harness.CONFIG.read_text('utf-8'))
    config['database']['path']=str(database);config['logging']['file']=str(args.output/'server.log')
    config['server'].update(host='127.0.0.1',port=2598)
    dev=config['development']
    for key,value in list(dev.items()):
        if key.startswith('diagnostic_') and isinstance(value,bool):dev[key]=False
    dev['diagnostic_world_resources']=False
    dev['diagnostic_town'].update(spawn_guides=True,quest_progress=False,map_probe=False,
        player_visibility=False,battle_after_quest=False,door_after_battle=False,door_routes=True,
        all_door_routes=True,source_consensus=True,island_routes=False,native_npc_placements_only=True,
        indoor_scenes=str(ROOT/'artifacts/world-atlas/town-doors-2.json'))
    config['world']={'clock':{'enabled':True,'sync_seconds':5}}
    if area==4:
        dev['diagnostic_town'].update(kunlun_door_routes=True,kunlun_indoor_scenes=str(bundle_path))
        config['world']['new_character_birthplace']={'area':4,'scene':3,'kind':0,'x':185,'y':98,
          'navigation':str(ROOT/'artifacts/world-atlas/kunlun-4-3.json')}
    shared.dump(args.output/'server-config.json',config)
    env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1'
    with (args.output/'migration.log').open('wb') as log:
        subprocess.run([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--migrate-only'],
            cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,check=True,timeout=25)
    before=daily.stable_database(database)
    with closing(sqlite3.connect(database)) as db:
        require(db.execute('UPDATE recovered_positions SET area=?,scene=?,x=?,y=?,revision=revision+1 WHERE character_id=4',
            [area,outdoor_scene,*pair['town_arrival']]).rowcount==1,'POSITION_FIXTURE_MISSING')
        db.commit();require(db.execute('PRAGMA quick_check').fetchone()==('ok',),'CLONE_INTEGRITY')
    after=daily.stable_database(database)
    require({k:v for k,v in before.items() if k!='recovered_positions'}==
            {k:v for k,v in after.items() if k!='recovered_positions'},'FIXTURE_CHANGED_OTHER_TABLES')
    shared.dump(args.output/'fixture.json',{'origin':'CUSTOM_TEST_NOT_NATIVE','area':area,'outdoor_scene':outdoor_scene,'scene':args.scene,'pair_index':args.pair_index,'pair':pair,
        'source_database':str(harness.SOURCE),'source_sha256':fixture.sha(harness.SOURCE),
        'before':before,'after':after})


def location(database):
    with closing(shared.ro(database)) as db:
        return list(db.execute('SELECT area,scene,x,y,revision FROM recovered_positions WHERE character_id=4').fetchone())


def native(client):return daily.stable_native(client)


def all_other_saved_state(database):
    """Exact schema/row evidence; only fixture character4's position may vary."""
    with closing(shared.ro(database)) as db:
        result={}
        for name,sql in db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"):
            quoted='"'+name.replace('"','""')+'"'
            rows=db.execute('SELECT * FROM '+quoted+(' WHERE character_id<>4' if name=='recovered_positions' else '')).fetchall()
            encoded='\n'.join(sorted(repr(row) for row in rows)).encode()
            result[name]={'schema':sql,'count':len(rows),'sha256':hashlib.sha256(encoded).hexdigest()}
        return result


def navigation_observation(client,state,points):
    handle=client['handle'];read=shared.exact
    bridge=int.from_bytes(read(handle,state['world']+0xa7e05dc,4),'little')
    manager=int.from_bytes(read(handle,bridge+0xbc,4),'little')
    kind=int.from_bytes(read(handle,manager+0x30,4),'little')
    require(kind in (0,2),'UNQUALIFIED_NATIVE_NAVIGATION_KIND')
    if kind==2:
        indoor=int.from_bytes(read(handle,manager+0x1030,4),'little')
        grid,width,height=struct.unpack('<III',read(handle,indoor+0x8c,12))
        require(grid>0x10000 and 1<=width<=1025 and 1<=height<=1025,'NATIVE_GRID_BOUNDS')
        observations=[{'point':p,'value':read(handle,grid+p[1]*width+p[0],1)[0]}
          for p in points if 0<=p[0]<width and 0<=p[1]<height]
        return {'kind':kind,'width':width,'height':height,'points':observations}
    ox,oy=struct.unpack('<II',read(handle,manager+0x103c,8))
    observations=[{'point':p,'value':read(handle,manager+0x50+(p[1]-oy+21)*63+p[0]-ox+21,1)[0]}
      for p in points if 0<=p[0]-ox+21<63 and 0<=p[1]-oy+21<63]
    return {'kind':kind,'origin':[ox,oy],'points':observations}


def input_observation(client,state):
    read=shared.exact;handle=client['handle'];ui=client['ui'];world=state['world']
    # Original1024C0 path fields; original676D0 checks widget open/fade bits
    # through getters71310/71350/F96B0 etc using UI+E2988+i*2A08.
    mode,path_index,count=struct.unpack('<III',read(handle,world+0x30,12))
    widgets=[{'index':i,'flags':read(handle,ui+0xe2988+i*0x2a08,1)[0]} for i in range(128)]
    bindings=[]
    for offset in (0x232dd2,0x232e5e,0x232e6c,0x232e68,0x232ea0,0x232e9e,0x232e74,0x232e78,0x232e7a):
        widget_index=struct.unpack('<h',read(handle,ui+offset,2))[0]
        bindings.append({'offset':hex(offset),'index':widget_index,
          'flags':read(handle,ui+0xe2988+widget_index*0x2a08,1)[0] if 0<=widget_index<128 else None})
    return {'movement_mode':mode,'path_index':path_index,'path_count':count,
      'path_flag':read(handle,world+0x236,1)[0],
      'native676D0_widget_bindings':bindings,
      'open_or_fading_widgets':[w for w in widgets if w['flags']&0x28]}


def stable(value,cold=False):
    value=json.loads(json.dumps(value));state=value['state'];state.pop('world_map')
    # Original A52A0 copies the full FB body. An absent saved pet sends no FB
    # restore, so its raw cache is not owned persistent state across fresh PIDs.
    # Same-process crossings still compare every raw byte.
    if cold:
        for slot,raw in state['pet_slots'].items():
            if not any(bytes.fromhex(raw)):state['pet_cache'].pop(slot,None)
    return value


def login(scene=4,area=2,outdoor_scene=4):
    old=harness.find_ui
    try:
        harness.find_ui=lambda handle:old(handle,kind=0 if scene==outdoor_scene else 2,scene=scene,area=area)
        return harness.login()
    finally:harness.find_ui=old


def worker(args):
    result={'accepted':False,'stages':[],'owned_client_pids':[],'rendered_pixels_tested':False}
    desktop=desktop_names();client=None;database=args.output/'town-diagnostic-accounts.db';log=args.output/'server.log'
    data=json.loads((args.output/'fixture.json').read_text());scene=data['scene'];pair=data['pair'];area=data['area'];outdoor_scene=data['outdoor_scene']
    def save():shared.dump(args.output/'ui-result.json',result)
    def target(expected):
        return location(database)[:4]==[area,*expected]
    def travel(trigger,arrival,expected_scene,destination=None):
        state=viewport.world_state(client['handle'],client['ui'])
        require([state['x'],state['y']]==arrival,'NATIVE_PLAYER_POSITION_MISMATCH')
        point=viewport.ground_point(client['handle'],state,*trigger)
        nav=navigation_observation(client,state,[arrival,trigger])
        input_before=input_observation(client,state)
        before_text=log.read_text('utf-8',errors='replace')
        # Hold across native render-loop input sampling on the hidden desktop.
        # A 30ms down/up may disappear before a busy client reads it.
        click(client['hwnd'],*point,interval=.15)
        attempts={'native_camera':state,'native_navigation':nav,
          'native_input_before':input_before,'pixel':list(point),'trigger':trigger}
        try:
            wait_until(lambda:location(database)[1]==expected_scene,12,'NO_NATIVE_CROSSING')
            if destination is not None:
                require(max(abs(trigger[0]-arrival[0]),abs(trigger[1]-arrival[1]))==1,'TRANSFER_CLICK_MUST_BE_ADJACENT')
                expected=[area,expected_scene,*destination]
                next_step=[area,expected_scene,destination[0]+trigger[0]-arrival[0],destination[1]+trigger[1]-arrival[1]]
                def acknowledged():
                    emitted=log.read_text('utf-8',errors='replace')[len(before_text):]
                    commit=re.search(r'DIAGNOSTIC_DOOR_COMMITTED session_id=(\d+) source_scene='+str(state['scene'])+r' destination_scene='+str(expected_scene),emitted)
                    if not commit:return None
                    current=location(database)[:4]
                    sid=commit[1]
                    if current==expected:
                        marker='DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED session_id='+sid+'; no_save_changes'
                    elif current==next_step:
                        pending='DIAGNOSTIC_DOOR_PENDING_NEXT_MOVE session_id='+sid+f' x={current[2]} y={current[3]} sequence=1'
                        if pending not in emitted:return None
                        marker='DIAGNOSTIC_TOWN_SCENE_CONTEXT_AND_MOVE_ACCEPTED session_id='+sid
                    else:return None
                    if marker not in emitted:return None
                    now=viewport.world_state(client['handle'],client['ui'])
                    if [now[k] for k in ('area','scene','x','y')]!=current:return None
                    if input_observation(client,now)['movement_mode']!=0:return None
                    return {'saved':current,'session_id':int(sid),'receipt':marker,
                            'source_arrival':expected,'coalesced_first_step':current if current!=expected else None}
                attempts['destination_receipt']=wait_until(acknowledged,14,'DESTINATION_RECEIPT_OR_NATIVE_MISMATCH')
        finally:
            attempts['saved']=location(database)
            attempts['native_input_after']=input_observation(client,viewport.world_state(client['handle'],client['ui']))
            attempts['emitted_server_records']=log.read_text('utf-8',errors='replace')[len(before_text):]
            result.setdefault('click_records',[]).append(attempts);save()
        return attempts
    try:
        require(desktop['current'].startswith('God2Lab-') and desktop['current']!=desktop['input'],'HIDDEN_DESKTOP_REQUIRED')
        result['desktop_before']=desktop;client=login(outdoor_scene,area,outdoor_scene);result['owned_client_pids'].append(client['process'].pid)
        before=daily.stable_database(database);initial=native(client);result['before']={'db':before,'native':initial}
        result['all_other_saved_state_before']=all_other_saved_state(database);save()
        result['entry_clicks']=travel(pair['town_trigger'],pair['town_arrival'],scene,pair['indoor_arrival'])
        time.sleep(6);inside=native(client)
        require(inside['state']['world_map']=={'area':area,'scene':scene,'kind':2},'INDOOR_NATIVE_SCENE_MISMATCH')
        require(stable(initial)==stable(inside),'ENTRY_CHANGED_UNRELATED_NATIVE_STATE')
        result['inside']={'saved':location(database),'native':inside};result['stages'].append('native_entered');save()
        shared.close_client(client);client=None;time.sleep(2)
        client=login(scene,area,outdoor_scene);result['owned_client_pids'].append(client['process'].pid)
        time.sleep(6);restored=native(client);result['restored_observation']=restored;save()
        require(stable(initial,cold=True)==stable(restored,cold=True),'ROOM_RELOGIN_CHANGED_UNRELATED_STATE')
        require(restored['state']['world_map']=={'area':area,'scene':scene,'kind':2},'ROOM_RELOGIN_SCENE_MISMATCH')
        result['room_relogin']={'saved':location(database),'native':restored};result['stages'].append('room_cold_relogin');save()
        exit_start=location(database)[2:4]
        waypoint=[12,12] if area==2 and scene==5 else pair['indoor_arrival']
        if exit_start!=waypoint:
            # Stand on the original qualified arrival before the adjacent exit.
            state=viewport.world_state(client['handle'],client['ui']);pixel=viewport.ground_point(client['handle'],state,*waypoint)
            nav=navigation_observation(client,state,[pair['indoor_arrival'],waypoint,pair['indoor_trigger']])
            inputs=input_observation(client,state)
            offset=len(log.read_text('utf-8',errors='replace'));click(client['hwnd'],*pixel,interval=.15)
            try:
                wait_until(lambda:target([scene,*waypoint]),12,'NATIVE_EXIT_APPROACH_NOT_MOVED')
                wait_until(lambda:[viewport.world_state(client['handle'],client['ui'])[key] for key in ('x','y')]==waypoint and
                  input_observation(client,viewport.world_state(client['handle'],client['ui']))['movement_mode']==0,
                  12,'NATIVE_EXIT_APPROACH_ANIMATION_NOT_FINISHED')
            finally:
                result['exit_approach']={'native_camera':state,'pixel':list(pixel),'target':waypoint,
                  'native_navigation':nav,'native_input_before':inputs,
                  'native_input_after':input_observation(client,viewport.world_state(client['handle'],client['ui'])),
                  'saved':location(database),'emitted_server_records':log.read_text('utf-8',errors='replace')[offset:]};save()
            exit_start=waypoint
        result['exit_clicks']=travel(pair['indoor_trigger'],exit_start,outdoor_scene,pair['town_arrival'])
        time.sleep(6);returned=native(client);require(stable(restored)==stable(returned),'RETURN_CHANGED_UNRELATED_NATIVE_STATE')
        require(returned['state']['world_map']=={'area':area,'scene':outdoor_scene,'kind':0},'RETURN_NATIVE_SCENE_MISMATCH')
        result['returned']={'saved':location(database),'native':returned};result['stages'].append('native_returned');save()
        after=daily.stable_database(database)
        require({k:v for k,v in before.items() if k!='recovered_positions'}==
                {k:v for k,v in after.items() if k!='recovered_positions'},'TRAVEL_CHANGED_UNRELATED_TABLES')
        result['all_other_saved_state_after']=all_other_saved_state(database)
        require(result['all_other_saved_state_after']==result['all_other_saved_state_before'],'TRAVEL_CHANGED_OTHER_SAVED_ROWS_OR_SCHEMA')
        text=log.read_text('utf-8',errors='replace')
        require(text.count('DIAGNOSTIC_DOOR_COMMITTED')==2,'DOOR_COMMIT_COUNT')
        require('Recovered world record rejected' not in text,'WORLD_ROUTE_REJECTED')
        require(client['process'].poll() is None,'CURRENT_CLIENT_EXITED')
        result['accepted']=True
    except Exception as error:result['error']=str(error);result['traceback']=traceback.format_exc()
    finally:
        if client:
            try:shared.close_client(client)
            except Exception as error:result['cleanup_error']=str(error)
        result['desktop_after']=desktop_names();result['desktop_unchanged']=desktop==result['desktop_after']
        result['all_clients_closed']=not any(psutil.pid_exists(pid) for pid in result['owned_client_pids'])
        result['accepted']=bool(result['accepted'] and result['desktop_unchanged'] and result['all_clients_closed'] and not result.get('cleanup_error'));save()
    return 0 if result['accepted'] else 1


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--server-candidate',type=Path);p.add_argument('--scene',type=int,default=5)
    p.add_argument('--area',type=int,choices=(2,4),default=2)
    p.add_argument('--pair-index',type=int,default=0)
    p.add_argument('--prepare-only',action='store_true');p.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=p.parse_args()
    if args.worker:return worker(args)
    if args.server_candidate is None:p.error('--server-candidate required')
    harness.prepare=prepare;harness.__file__=str(Path(__file__).resolve())
    return harness.owner(args)


if __name__=='__main__':raise SystemExit(main())

