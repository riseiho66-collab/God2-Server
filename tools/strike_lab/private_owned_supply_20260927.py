"""Hidden, disposable owned multi-slot supply acceptance.

Source declarations qualify +100 HP / +50 MP. Ownership quantities/resources
are CUSTOM_TEST_NOT_NATIVE fixture operands; cap/consumption is CUSTOM-0016.
No screenshot, desktop switch, injected packet or client-memory write.
"""
import argparse
from contextlib import closing
import ctypes as c
import json
import os
from pathlib import Path
import re
import socket
import sqlite3
import struct
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]
import psutil
import private_weapon_peer_appearance_20260927 as shared
import private_daily_quest_20260927 as daily
import private_owned_companions_ui as owned
from tools.strike_lab import run_private_owned_companions as fixture
from private_inventory_memory import kernel,Region,read
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,drag,type_ascii,user

SOURCE=ROOT/'artifacts/playtests/private-owned-companions-20260926-04/town-diagnostic-accounts.db'
CONFIG=SOURCE.with_name('server-config.json')
FORMAL=ROOT/'artifacts/releases/town-chat-welcome-20260924/server-config.json'


def find_ui(handle,*,kind=0,scene=4,area=2,diagnostics=None):
    require(kind in (0,2) and 0<=scene<=1023 and 0<=area<=63,'UNQUALIFIED_WORLD_LOCATION')
    needle=struct.pack('<IIH',kind,scene,area);address=0x10000;scanned=0;matches=set()
    while address<0x80000000 and scanned<800*1024*1024:
        region=Region()
        if not kernel.VirtualQueryEx(handle,address,c.byref(region),c.sizeof(region)):break
        base=region.BaseAddress or address;end=min(base+region.RegionSize,0x80000000)
        if region.State==0x1000 and not region.Protect&0x101:
            offset=base;tail=b''
            while offset<end:
                size=min(1024*1024,end-offset);raw=read(handle,offset,size)
                if raw:
                    scanned+=len(raw);combined=tail+raw;at=combined.find(needle)
                    while at>=0:
                        role=offset-len(tail)+at-0x10;world=role-0x1539683c;ui=world+0xa7f2f6c
                        if diagnostics is not None and world>0x10000:
                            identity=read(handle,role,4);owner=read(handle,ui+0x86888,4)
                            if identity==struct.pack('<I',4):
                                diagnostics.setdefault('identity_candidates',[]).append({'position_role':hex(role),
                                    'ui':hex(ui),'pointer_hex':owner.hex() if owner else None,
                                    'expected_pointer':hex(role+0x90)})
                        if world>0x10000 and read(handle,role,4)==struct.pack('<I',4) and read(handle,ui+0x86888,4)==struct.pack('<I',role+0x90):matches.add(ui)
                        at=combined.find(needle,at+1)
                    tail=combined[-9:]
                offset+=size
        address=end if end>address else address+0x1000
    if diagnostics is not None:diagnostics.update(kind=kind,scene=scene,area=area,matching_owners=len(matches))
    require(len(matches)==1,'SUPPLY_UI_OWNER_AMBIGUOUS');return matches.pop()


def login():
    process=subprocess.Popen([str(fixture.CLIENT),'127.0.0.1','127.0.0.1','6001','1'],cwd=fixture.CLIENT.parent,
        creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    client={'process':process}
    try:
        hwnd=wait_until(lambda:shared.window_for(process.pid),35,'OWNED_WINDOW_MISSING');client['hwnd']=hwnd
        time.sleep(2);click(hwnd,512,464);time.sleep(3)
        click(hwnd,437,232);type_ascii(hwnd,'codexslow');click(hwnd,437,263);type_ascii(hwnd,'labtest2345')
        click(hwnd,452,304);time.sleep(4);click(hwnd,330,145);click(hwnd,452,413);time.sleep(4)
        click(hwnd,330,150);click(hwnd,452,376);time.sleep(4);click(hwnd,452,370);time.sleep(8)
        require(process.poll() is None,'OWNED_CLIENT_EXITED')
        client['handle']=kernel.OpenProcess(0x1010,False,process.pid);require(client['handle'],'READONLY_OPEN_FAILED')
        client['ui']=find_ui(client['handle']);return client
    except BaseException:
        shared.close_client(client);raise


def db_state(path):
    value=daily.stable_database(path)
    with closing(shared.ro(path)) as db:
        value['supply_resources']=list(db.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources WHERE character_id=4').fetchone())
        value['supply_slots']={str(row[0]):list(row[1:]) for row in db.execute('SELECT slot,item_id,count,revision,source_sha256,design_id FROM diagnostic_inventory_slots WHERE character_id=4 AND slot IN(5,12) ORDER BY slot')}
    return value


def native_state(client):return daily.stable_native(client)


def untouched_db(value):
    out={key:rows for key,rows in value.items() if key not in ('supply_resources','supply_slots')}
    out['character_resources']=[r for r in out['character_resources'] if r[0]!=4]
    out['diagnostic_inventory_slots']=[r for r in out['diagnostic_inventory_slots'] if not(r[0]==4 and r[1] in (5,12))]
    return out


def untouched_native(value):
    out=json.loads(json.dumps(value));out['state'].pop('role_resources')
    slots=bytearray.fromhex(out['all50_slots'])
    for slot in (5,12):slots[slot*24:slot*24+4]=bytes(4)
    out['all50_slots']=slots.hex();return out


def check_projection(native,saved):
    require(native['state']['role_resources']==saved['supply_resources'][:4],'SUPPLY_NATIVE_RESOURCES_MISMATCH')
    raw=bytes.fromhex(native['all50_slots'])
    for slot,item in ((5,3101),(12,3107)):
        row=saved['supply_slots'][str(slot)];record=raw[slot*24:(slot+1)*24]
        require(row[0]==item and record==struct.pack('<IH',row[1],item)+bytes(18),'SUPPLY_NATIVE_SLOT_MISMATCH')


def prepare(args):
    args.output.mkdir(parents=True,exist_ok=False)
    require(fixture.sha(fixture.LIVE_CLIENT)==fixture.CURRENT_CLIENT_SHA,'CURRENT_EXE_PIN')
    original=fixture.LIVE_CLIENT.read_bytes();expected=bytearray(original)
    site=original.index(bytes.fromhex('68 20 0a 00 00 68 9c 47 5b 00'));expected[site+1:site+5]=struct.pack('<I',2598)
    require(fixture.CLIENT.read_bytes()==expected,'PRIVATE_EXE_NOT_EXACT_PORT_COPY')
    database=args.output/'town-diagnostic-accounts.db'
    with closing(shared.ro(SOURCE)) as source,closing(sqlite3.connect(database)) as target:source.backup(target)
    config=json.loads(CONFIG.read_text('utf-8'));config['database']['path']=str(database)
    config['logging']['file']=str(args.output/'server.log');config['server'].update(host='127.0.0.1',port=2598)
    dev=config['development']
    for key,value in list(dev.items()):
        if key.startswith('diagnostic_') and isinstance(value,bool):dev[key]=False
    dev['diagnostic_town'].update(spawn_guides=True,quest_progress=False,map_probe=False,player_visibility=False,
        battle_after_quest=False,door_after_battle=False,native_npc_placements_only=True)
    dev['native_monster_placements_only']=True
    config['world']={'owned_supply':{'enabled':True},'clock':{'enabled':True,'sync_seconds':5}}
    shared.dump(args.output/'server-config.json',config)
    env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1'
    with (args.output/'migration.log').open('wb') as log:
        subprocess.run([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--migrate-only'],
            cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,check=True,timeout=25)
    from tools.strike_lab.import_native_med02_recovery import import_catalog
    with closing(sqlite3.connect(database)) as db:med02_import=import_catalog(db,fixture.LIVE_CLIENT.parent)
    before=db_state(database)
    with closing(sqlite3.connect(database)) as db:
        require(db.execute('SELECT row_key FROM character_deity_selection WHERE character_id=4').fetchone() is not None,'ACTIVE_GOD_FIXTURE_MISSING')
        require(db.execute('SELECT count(*) FROM character_pet2_slots WHERE character_id=4 AND length(metadata)>0').fetchone()[0]>0,'PET_FIXTURE_MISSING')
        db.execute('UPDATE character_resources SET hp=20,max_hp=120,mp=2,max_mp=80,revision=1 WHERE character_id=4')
        for slot,item,count in ((5,3101,2),(12,3107,3)):
            require(db.execute('SELECT count(*) FROM character_weapon_slot_metadata WHERE character_id=4 AND slot=?',(slot,)).fetchone()[0]==0,'FIXTURE_SLOT_HAS_WEAPON_METADATA')
            db.execute('INSERT INTO diagnostic_inventory_slots VALUES(4,?,?,?,1,?,?) ON CONFLICT(character_id,slot) DO UPDATE SET '
                'item_id=excluded.item_id,count=excluded.count,revision=excluded.revision,source_sha256=excluded.source_sha256,design_id=excluded.design_id',
                (slot,item,count,fixture.WEAPON_SOURCE_SHA,'CUSTOM-0015'))
        db.commit();require(db.execute('PRAGMA quick_check').fetchone()==('ok',),'CLONE_INTEGRITY')
    after=db_state(database);require(untouched_db(before)==untouched_db(after),'FIXTURE_CHANGED_UNRELATED_ROWS')
    require(after['supply_resources']==[20,120,2,80,1],'FIXTURE_RESOURCES')
    shared.dump(args.output/'fixture.json',{'origin':'CUSTOM_TEST_NOT_NATIVE','source_database':str(SOURCE),
        'source_sha256':fixture.sha(SOURCE),'before':before,'after':after,'med02_import':med02_import,'source_declarations':{3101:{'hp':100},3107:{'mp':50}},
        'runtime_policy':'CUSTOM-0016','no_native_cap_or_consumption_formula_claim':True})


def worker(args):
    result={'accepted':False,'stages':[],'owned_client_pids':[],'rendered_pixels_tested':False}
    desktop=desktop_names();client=None;database=args.output/'town-diagnostic-accounts.db';log=args.output/'server.log'
    def save():shared.dump(args.output/'ui-result.json',result)
    try:
        require(desktop['current'].startswith('God2Lab-') and desktop['current']!=desktop['input'],'HIDDEN_DESKTOP_REQUIRED')
        result['desktop_before']=desktop;client=login();result['owned_client_pids'].append(client['process'].pid)
        before=db_state(database);native=native_state(client);check_projection(native,before)
        require(native['state']['deity_count']>0 and native['state']['deity_selected_key'] is not None,'ACTIVE_NATIVE_GOD_MISSING')
        require(any(bytes.fromhex(raw)[4:6]!=bytes(2) for raw in native['state']['pet_slots'].values()),'NATIVE_OWNED_PET_MISSING')
        result['before']={'db':before,'native':native};save()
        click(client['hwnd'],708,584);time.sleep(1)
        handle,ui=client['handle'],client['ui']
        inventory=int.from_bytes(shared.exact(handle,ui+0x232dc8,2),'little',signed=True)
        shortcut=int.from_bytes(shared.exact(handle,ui+0x232e54,2),'little',signed=True)
        require(0<=inventory<128 and 0<=shortcut<128,'SUPPLY_WIDGET_INVALID')
        last_slot=None
        for slot,item,consumed,hp,mp,count in ((5,3101,True,120,2,1),(5,3101,False,120,2,1),
                (12,3107,True,120,52,2),(12,3107,True,120,80,1),(12,3107,False,120,80,1)):
            prior=db_state(database)
            if last_slot!=slot:
                points=drag(client['hwnd'],owned.control_point(handle,ui,inventory,slot),owned.control_point(handle,ui,shortcut,10))
                time.sleep(.4);last_slot=slot
            else:points=None
            offset=log.stat().st_size
            for message in (0x100,0x101):
                require(user.PostMessageW(client['hwnd'],message,0x70,0),'F1_POST_FAILED');time.sleep(.12)
            def observed():
                lines=[line for line in log.read_bytes()[offset:].decode('utf-8',errors='replace').splitlines() if 'OWNED_SUPPLY_USE' in line]
                if not lines:return None
                fields={'character_id':4,'target':4,'slot':slot,'item':item}
                require(any(all(re.search(r'\b'+key+'='+str(value)+r'\b',line) for key,value in fields.items()) and
                    re.search(r'\bconsumed='+('(?:true|1)' if consumed else '(?:false|0)')+r'\b',line) for line in lines),'SUPPLY_REQUEST_FIELDS_MISMATCH')
                saved=db_state(database);actual=native_state(client)
                if actual['state']['role_resources']!=[hp,120,mp,80]:return None
                check_projection(actual,saved)
                require(saved['supply_slots'][str(slot)][1]==count,'SUPPLY_COUNT_MISMATCH')
                require(saved['supply_resources'][4]==prior['supply_resources'][4]+int(consumed),'SUPPLY_RESOURCE_REVISION')
                require(saved['supply_slots'][str(slot)][2]==prior['supply_slots'][str(slot)][2]+int(consumed),'SUPPLY_SLOT_REVISION')
                require(untouched_db(saved)==untouched_db(before),'SUPPLY_CHANGED_UNRELATED_DB')
                require(untouched_native(actual)==untouched_native(native),'SUPPLY_CHANGED_GOD_PET_OR_OTHER_NATIVE_STATE')
                if not consumed:require(saved==prior,'CAPPED_SUPPLY_MUTATED_DB')
                return {'slot':slot,'item':item,'consumed':consumed,'drag':points,'logs':lines,'db':saved,'native':actual}
            result['stages'].append(wait_until(observed,12,'NATIVE_SUPPLY_REQUEST_NOT_OBSERVED'));save()
        after=db_state(database);after_native=native_state(client)
        shared.close_client(client);client=None;time.sleep(1)
        client=login();result['owned_client_pids'].append(client['process'].pid)
        replay=db_state(database);replay_native=native_state(client);check_projection(replay_native,replay)
        require(replay==after,'SUPPLY_RELOGIN_DB_CHANGED')
        require(replay_native==after_native,'SUPPLY_RELOGIN_NATIVE_STATE_MISMATCH')
        result['relogin']={'db':replay,'native':replay_native,'persisted':True}
        result['log_count']=log.read_text('utf-8',errors='replace').count('OWNED_SUPPLY_USE')
        require(result['log_count']==5,'SUPPLY_LOG_COUNT');result['accepted']=True
    except Exception as error:
        result['error']=str(error);result['traceback']=traceback.format_exc()
    finally:
        if client:
            try:shared.close_client(client)
            except Exception as error:result['cleanup_error']=str(error)
        result['desktop_after']=desktop_names();result['desktop_unchanged']=desktop==result['desktop_after']
        result['all_clients_closed']=not any(psutil.pid_exists(pid) for pid in result['owned_client_pids'])
        result['accepted']=bool(result['accepted'] and result['desktop_unchanged'] and result['all_clients_closed'] and not result.get('cleanup_error'));save()
    return 0 if result['accepted'] else 1


def owner(args):
    args.output=args.output.resolve();args.server_candidate=args.server_candidate.resolve()
    paths={'source_db':SOURCE,'live_client':fixture.LIVE_CLIENT,'private_client':fixture.CLIENT,'formal_config':FORMAL}
    result={'accepted':False,'before':{key:fixture.sha(path) for key,path in paths.items()},'server_sha256':fixture.sha(args.server_candidate)}
    result['actual_server_sha256']=result['server_sha256'];server=runner=None
    try:
        with socket.socket() as probe:require(probe.connect_ex(('127.0.0.1',2598))!=0,'PRIVATE_PORT_IN_USE')
        prepare(args)
        if args.prepare_only:result['prepared_only']=True
        else:
            env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1';env.pop('GOD2_PRIVATE_SIDECAR_COMMAND',None)
            with (args.output/'stdout.log').open('wb') as stdout,(args.output/'runner.log').open('wb') as runnerlog:
                server=subprocess.Popen([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--run-for','210'],
                    cwd=ROOT,env=env,stdout=stdout,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                result['server_pid']=server.pid
                def listening():
                    require(server.poll() is None,'SERVER_EXITED')
                    with socket.socket() as probe:return probe.connect_ex(('127.0.0.1',2598))==0
                wait_until(listening,10,'SERVER_NOT_LISTENING')
                runner=subprocess.Popen([str(fixture.RUNNER),sys.executable,'-X','utf8','-B',str(Path(__file__).resolve()),'--worker','--output',str(args.output)],
                    cwd=ROOT,env=env,stdout=runnerlog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                result['runner_pid']=runner.pid;result['runner_exit']=runner.wait(timeout=190)
                result['ui']=json.loads((args.output/'ui-result.json').read_text('utf-8'))
                for key in ('all_clients_closed','desktop_unchanged'):result[key]=result['ui'][key]
                result['accepted']=result['runner_exit']==0 and result['ui']['accepted']
    except Exception as error:result['error']=str(error);result['traceback']=traceback.format_exc()
    finally:
        for process in (runner,server):
            if process is not None and process.poll() is None:
                children=psutil.Process(process.pid).children(recursive=True)
                for child in reversed(children):
                    try:child.terminate()
                    except psutil.NoSuchProcess:pass
                process.terminate();process.wait(timeout=5);_,alive=psutil.wait_procs(children,timeout=5)
                for child in alive:child.kill();child.wait(timeout=5)
        result['after']={key:fixture.sha(path) for key,path in paths.items()}
        result['source_files_unchanged']={key:result['before'][key]==value for key,value in result['after'].items()}
        result['candidate_unchanged']=fixture.sha(args.server_candidate)==result['server_sha256']
        result['owned_server_closed']=server is None or server.poll() is not None
        result['owned_runner_closed']=runner is None or runner.poll() is not None
        result['accepted']=bool(result['accepted'] and all(result['source_files_unchanged'].values()) and result['candidate_unchanged'] and result['owned_server_closed'] and result['owned_runner_closed'])
        if args.output.exists():shared.dump(args.output/'run-result.json',result)
    print(json.dumps({key:result.get(key) for key in ('accepted','prepared_only','error','server_sha256')}))
    return 0 if result['accepted'] or result.get('prepared_only') else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--server-candidate',type=Path);parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS);args=parser.parse_args()
    if args.worker:return worker(args)
    if args.server_candidate is None:parser.error('--server-candidate required')
    return owner(args)


if __name__=='__main__':raise SystemExit(main())
