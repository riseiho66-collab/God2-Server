"""Owned hidden client: native bag25 -> menu6D -> selection99 -> transfer61.

Only an isolated fixture changes. Original9be client is copied with a private
port operand; current UI receives ordinary window messages. All observation
handles are read-only. No screenshot, foreground change, packet injection or
process-memory write. Fixture quantities are explicit CUSTOM test operands.
"""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import struct
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]
import private_pet_reserve_move_20260930 as base
import private_weapon_peer_appearance_20260927 as shared
import private_owned_companions_ui as owned
import private_owned_supply_20260927 as supply
import private_scene_actor_route_ui as ground
from tools.strike_lab import run_private_owned_companions as fixture
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click

PORT=2597
base.SOURCE=ROOT/'artifacts/playtests/private-pet-reserve-20260930-03/town-diagnostic-accounts.db'
META=bytes.fromhex('b73e0804')+bytes(16)
SEED=ROOT/'artifacts/research/teleport-gem-20260930/seed-cpp/seed.exe'


def all_saved(database,exclude_changes=False):
    with closing(shared.ro(database)) as db:
        result={}
        for name,sql in db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"):
            predicate=''
            if exclude_changes:
                if name=='recovered_positions':predicate=' WHERE character_id<>4'
                if name in ('diagnostic_inventory_slots','character_teleport_gem_metadata'):
                    predicate=' WHERE character_id<>4 OR slot<>12'
            quoted='"'+name.replace('"','""')+'"'
            rows=db.execute('SELECT * FROM '+quoted+predicate).fetchall()
            result[name]={'schema':sql,'rows':sorted(repr(row) for row in rows)}
        return result


def saved(database):
    with closing(shared.ro(database)) as db:
        return {'slot':list(db.execute('SELECT item_id,count,revision FROM diagnostic_inventory_slots WHERE character_id=4 AND slot=12').fetchone()),
            'meta':list(db.execute('SELECT hex(metadata20),revision,origin,provenance FROM character_teleport_gem_metadata WHERE character_id=4 AND slot=12').fetchone()),
            'position':list(db.execute('SELECT area,scene,x,y,revision FROM recovered_positions WHERE character_id=4').fetchone())}


def native(client):
    raw=shared.exact(client['handle'],client['ui']+0x8560c+12*24,24)
    return {'slot_hex':raw.hex(),'metadata20':raw[4:24].hex(),'count':raw[0],
            'world':ground.world_state(client['handle'],client['ui'])}


def menu(client):
    handle,ui=client['handle'],client['ui']
    def uint(address,size=4):return int.from_bytes(shared.exact(handle,address,size),'little')
    widget=int.from_bytes(shared.exact(handle,ui+0x232e38,2),'little',signed=True)
    if widget==-1:return {'widget':widget,'open':False}
    require(0<=widget<128,'TELEPORT_DIALOG_UNAVAILABLE')
    opened=bool(uint(ui+0xe2988+widget*0x2a08)&0x20)
    value={'widget':widget,'open':opened,'body':shared.exact(handle,ui+0x790ec,28).hex(),
        'selected':uint(ui+0x790e0),'page':uint(ui+0x790e4),'pages':uint(ui+0x790e8)}
    if opened:
        listing=ui+0x79108;index=int.from_bytes(shared.exact(handle,listing+0x1c,2),'little',signed=True)
        require(0<=index<10000,'MENU_INPUT_INDEX_INVALID')
        entry=uint(listing)+index*0x18
        require(uint(entry)==1,'MENU_ROW_INPUT_NOT_ACTIVE')
        rect=struct.unpack('<4i',shared.exact(handle,entry+4,16))
        require(0<=rect[0]<rect[2]<=800 and 0<=rect[1]<rect[3]<=600,'MENU_RECT_OUTSIDE_CLIENT')
        value.update(row_enabled=uint(listing+0x148),rect=list(rect),point=[(rect[0]+rect[2])//2,(rect[1]+rect[3])//2])
    return value


def worker(args):
    fixture.CLIENT=args.client.resolve();database=args.output/'town-diagnostic-accounts.db';log=args.output/'server.log'
    result={'accepted':False,'rendered_pixels_tested':False,'owned_client_pids':[]};client=None;desktop=desktop_names()
    def dump():shared.dump(args.output/'ui-result.json',result)
    def login(kind,scene):
        supply.find_ui=lambda handle:shared.find_ui(handle,4,(kind,scene,2))
        value=supply.login();result['owned_client_pids'].append(value['process'].pid);return value
    def emitted(offset):return log.read_bytes()[offset:].decode('utf-8',errors='replace')
    try:
        require(desktop['current'].startswith('God2Lab-') and desktop['current']!=desktop['input'],'HIDDEN_DESKTOP_REQUIRED')
        result['desktop_before']=desktop;client=login(1,0)
        wait_until(lambda:'OWNED_TELEPORT_GEM_RESTORED' in log.read_text('utf-8',errors='replace'),8,'WORLD_GEM_PROJECTION_NOT_COMPLETED')
        before=saved(database);preserved=all_saved(database,True);initial_native=native(client)
        require(initial_native['metadata20']==META.hex() and initial_native['count']==1,'INITIAL_NATIVE_FULL20_MISMATCH')
        require(before['position'][:4]==[2,0,474,209],'INITIAL_SOURCE_POSITION_MISMATCH')
        result['initial']={'saved':before,'native':initial_native};dump()
        def open_menu():
            inventory=int.from_bytes(shared.exact(client['handle'],client['ui']+0x232dc8,2),'little',signed=True)
            if not (0<=inventory<128 and int.from_bytes(shared.exact(client['handle'],client['ui']+0xe2988+inventory*0x2a08,4),'little')&0x20):
                click(client['hwnd'],708,584);time.sleep(.7)
                inventory=int.from_bytes(shared.exact(client['handle'],client['ui']+0x232dc8,2),'little',signed=True)
            point=owned.control_point(client['handle'],client['ui'],inventory,12)
            offset=log.stat().st_size;click(client['hwnd'],*point,double=True)
            value=wait_until(lambda:(state if (state:=menu(client))['open'] else None),10,'NATIVE6D_MENU_DID_NOT_OPEN')
            require(value['row_enabled']!=0 and value['body']==(bytes.fromhex('b73e180181000a0005000000')+bytes(16)).hex(),'NATIVE_MENU_BODY_OR_ENABLE_MISMATCH')
            require(saved(database)==before,'OPEN_MENU_MUTATED_CHARGE_OR_POSITION')
            return {'menu':value,'bag_point':point,'server_records':emitted(offset)}
        result['opened_for_cancel']=open_menu();dump()
        offset=log.stat().st_size;cancelpoint=owned.control_point(client['handle'],client['ui'],menu(client)['widget'],4)
        click(client['hwnd'],*cancelpoint)
        wait_until(lambda:not menu(client)['open'],6,'MENU_CANCEL_DID_NOT_CLOSE');time.sleep(.5)
        require(saved(database)==before,'CANCEL_MUTATED_CHARGE_OR_POSITION')
        result['cancel']={'point':cancelpoint,'unchanged':True,'server_records':emitted(offset)};dump()
        result['opened_for_select']=open_menu();state=menu(client);click(client['hwnd'],*state['point'])
        wait_until(lambda:menu(client)['selected']==5,5,'NATIVE_SELECTED_ID_NOT_FIVE')
        confirm=owned.control_point(client['handle'],client['ui'],state['widget'],3)
        offset=log.stat().st_size;click(client['hwnd'],*confirm)
        def transferred():
            now=saved(database);observed=native(client)
            result['last_observed']={'saved':now,'native':observed,'server_records':emitted(offset)};dump()
            if now['position'][:4]!=[2,4,56,75]:return None
            if [observed['world'][key] for key in ('area','scene','kind','x','y')]!=[2,4,0,56,75]:return None
            expected=bytearray(META);expected[3]=2
            require(now['slot']==[16055,1,before['slot'][2]+1],'CHARGE_TRANSACTION_SCALAR_MISMATCH')
            require(now['meta']==[bytes(expected).hex().upper(),before['meta'][1]+1,*before['meta'][2:]],'CHARGE_TRANSACTION_FULL20_MISMATCH')
            require(now['position'][4]==before['position'][4]+1,'POSITION_REVISION_MISMATCH')
            if observed['metadata20']!=bytes(expected).hex() or observed['count']!=1:return None
            lines=emitted(offset)
            if 'SCENE_CONTEXT_ACCEPTED' not in lines and 'SCENE_CONTEXT_AND_MOVE_ACCEPTED' not in lines:return None
            require(all_saved(database,True)==preserved,'UNRELATED_DATABASE_CHANGED')
            return {'saved':now,'native':observed,'server_records':lines,'row_point':state['point'],'confirm_point':confirm,
                'native25_6d_99_61_flow_observed':True,'one_charge_only':True,'pending_receipt_observed':True}
        result['transfer']=wait_until(transferred,18,'NATIVE_SELECTION_TRANSFER_OR_RECEIPT_NOT_ACCEPTED');dump()
        final=all_saved(database);shared.close_client(client);client=None;time.sleep(1)
        client=login(0,4);restored=native(client)
        require(restored['metadata20']==result['transfer']['native']['metadata20'] and restored['count']==1,'RELOGIN_GEM_NOT_RESTORED')
        require([restored['world'][k] for k in ('area','scene','kind','x','y')]==[2,4,0,56,75],'RELOGIN_POSITION_NOT_RESTORED')
        require(all_saved(database)==final,'RELOGIN_CHANGED_SAVED_STATE')
        result['reconnect']={'native':restored,'saved_unchanged':True};result['accepted']=True
    except Exception as error:result['error']=str(error);result['traceback']=traceback.format_exc()
    finally:
        if client:
            try:shared.close_client(client)
            except Exception as error:result['cleanup_error']=str(error)
        result['desktop_after']=desktop_names();result['desktop_unchanged']=result['desktop_after']==desktop
        result['all_clients_closed']=not any(base.psutil.pid_exists(pid) for pid in result['owned_client_pids'])
        result['accepted']=bool(result['accepted'] and result['desktop_unchanged'] and result['all_clients_closed'] and not result.get('cleanup_error'));dump()
    return 0 if result['accepted'] else 1


def prepare(args):
    require(base.sha(base.LIVE)==base.PIN and base.sha(fixture.RUNNER)==base.RUNNER_PIN,'CURRENT_INPUT_PIN_CHANGED')
    require(SEED.is_file(),'FIXTURE_REPOSITORY_IMPORTER_NOT_BUILT')
    args.output.mkdir(parents=True,exist_ok=False)
    require(not args.client.exists() and args.client.parent.resolve()==base.LIVE.parent.resolve() and args.client.resolve()!=base.LIVE.resolve(),'NEW_PRIVATE_CLIENT_REQUIRED')
    original=base.LIVE.read_bytes();site=bytes.fromhex('68 20 0a 00 00 68 9c 47 5b 00');require(original.count(site)==1,'PORT_SITE_NOT_UNIQUE')
    at=original.index(site)+1;changed=bytearray(original);changed[at:at+4]=struct.pack('<I',PORT)
    require(sum(a!=b for a,b in zip(original,changed))<=4,'NONPORT_CLIENT_CHANGE')
    with args.client.open('xb') as output:output.write(changed)
    shared.dump(args.output/'client-copy.json',{'source_sha256':base.PIN,'copy_sha256':base.sha(args.client),'port':PORT,'port_file_offset':at})
    database=args.output/'town-diagnostic-accounts.db'
    with closing(shared.ro(base.SOURCE)) as source,closing(sqlite3.connect(database)) as target:source.backup(target)
    config=json.loads(base.SOURCE.with_name('server-config.json').read_text('utf-8'))
    config['database']['path']=str(database);config['logging']['file']=str(args.output/'server.log')
    config['server'].update(host='127.0.0.1',port=PORT,character_port=0)
    config.setdefault('world',{})['owned_teleport_gem']={'enabled':True}
    config['development']['diagnostic_town'].update(player_visibility=False,all_door_routes=True,island_routes=True,
        indoor_scenes=str(ROOT/'artifacts/world-atlas/town-doors-2.json'),
        island_navigation=str(ROOT/'artifacts/world-atlas/island01-full-navigation-2-0.json'))
    cfg=args.output/'server-config.json';shared.dump(cfg,config)
    env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1';env.pop('GOD2_PRIVATE_SIDECAR_COMMAND',None)
    with (args.output/'migration.log').open('wb') as output:
        subprocess.run([str(args.server_candidate),'--config',str(cfg),'--migrate-only'],cwd=ROOT,env=env,
            stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,check=True,timeout=30)
    with closing(sqlite3.connect(database)) as db:
        require(db.execute('SELECT 1 FROM character_weapon_slot_metadata WHERE character_id=4 AND slot=12').fetchone() is None,'FIXTURE_SLOT_WEAPON_CONFLICT')
        db.execute('INSERT INTO recovered_positions VALUES(4,2,0,474,209,1) ON CONFLICT(character_id) DO UPDATE SET area=2,scene=0,x=474,y=209,revision=1')
        db.execute("INSERT INTO diagnostic_inventory_slots VALUES(4,12,16055,1,1,?,'CUSTOM-0015') ON CONFLICT(character_id,slot) DO UPDATE SET item_id=16055,count=1,revision=1,source_sha256=excluded.source_sha256,design_id=excluded.design_id",('70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731',))
        db.commit()
    attach=subprocess.run([str(SEED),str(database)],cwd=ROOT,capture_output=True,text=True,check=True,timeout=20)
    shared.dump(args.output/'fixture.json',{'source_database':str(base.SOURCE),'source_sha256':base.sha(base.SOURCE),
        'authority':'CUSTOM_TEST_NOT_NATIVE','explicit_test_charges':2,'metadata20':META.hex(),
        'repository_importer_sha256':base.sha(SEED),'repository_importer_output':attach.stdout,'saved':saved(database)})


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--client',type=Path,required=True);parser.add_argument('--server-candidate',type=Path)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS);args=parser.parse_args()
    if args.worker:return worker(args)
    if args.server_candidate is None:parser.error('--server-candidate required')
    args.role_text=False;base.PORT=PORT;base.prepare=prepare;base.__file__=__file__
    return base.owner(args)


if __name__=='__main__':raise SystemExit(main())
