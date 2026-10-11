"""Owned hidden-desktop fruit quest acceptance; no screenshot or memory writes.

Each quest has a disposable DB fixture. Current source coordinates are hints;
the server's CUSTOM-0051 facing, instance, and lifecycle stay explicitly custom.
"""
import argparse
from contextlib import closing
import ctypes as c
import json
import math
import os
import re
from pathlib import Path
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
import private_owned_companions_ui as owned
from tools.strike_lab import run_private_owned_companions as fixture
from tools.strike_lab.current_inferred_quest_sources_20260927 import bundle
from private_inventory_memory import kernel,Region,read
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,type_ascii

SOURCE=ROOT/'artifacts/playtests/private-owned-companions-20260926-04/town-diagnostic-accounts.db'
CONFIG=SOURCE.with_name('server-config.json')
FORMAL=ROOT/'artifacts/releases/town-chat-welcome-20260924/server-config.json'


def source_quest(mission):
    rows=[row for row in bundle(fixture.LIVE_CLIENT.parent)['quests'] if row['mission_id']==mission]
    require(len(rows)==1,'UNKNOWN_SOURCE_QUEST');return rows[0]


def find_ui(handle):
    needle=struct.pack('<IIH',0,12,13);address=0x10000;scanned=0;matches=set()
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
                        if world>0x10000 and read(handle,role,4)==struct.pack('<I',4) and read(handle,ui+0x86888,4)==struct.pack('<I',role+0x90):matches.add(ui)
                        at=combined.find(needle,at+1)
                    tail=combined[-9:]
                offset+=size
        address=end if end>address else address+0x1000
    require(len(matches)==1,'FRUIT_UI_OWNER_AMBIGUOUS');return matches.pop()


def login():
    names=desktop_names();require(names['current'].startswith('God2Lab-') and names['current']!=names['input'],'HIDDEN_DESKTOP_REQUIRED')
    process=subprocess.Popen([str(fixture.CLIENT),'127.0.0.1','127.0.0.1','6001','1'],cwd=fixture.CLIENT.parent,
        creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    client={'process':process}
    try:
        hwnd=wait_until(lambda:shared.window_for(process.pid),35,'FRUIT_WINDOW_MISSING');client['hwnd']=hwnd
        time.sleep(2);click(hwnd,512,464);time.sleep(3)
        click(hwnd,437,232);type_ascii(hwnd,'codexslow');click(hwnd,437,263);type_ascii(hwnd,'labtest2345')
        click(hwnd,452,304);time.sleep(4);click(hwnd,330,145);click(hwnd,452,413);time.sleep(4)
        click(hwnd,330,150);click(hwnd,452,376);time.sleep(4);click(hwnd,452,370);time.sleep(8)
        require(process.poll() is None,'FRUIT_CLIENT_EXITED');require(Path(psutil.Process(process.pid).exe()).resolve()==fixture.CLIENT.resolve(),'WRONG_CLIENT_IDENTITY')
        client['handle']=kernel.OpenProcess(0x1010,False,process.pid);require(client['handle'],'READONLY_OPEN_FAILED')
        client['ui']=find_ui(client['handle']);require(owned.native(client['handle'],client['ui'])['world_map']=={'kind':0,'scene':12,'area':13},'FRUIT_MAP_MISMATCH');return client
    except BaseException:shared.close_client(client);raise


def npc_state(client,quest):
    handle=client['handle'];world=client['ui']-0xa7f2f6c;matches=[];all_entries=[]
    expected=quest['npc'];xy=(expected['x_text_hint'],expected['y_text_hint'])
    for offset in (0x1539aed8,0x153b8758):
        pool=world+offset
        for slot in range(256):
            address=pool+0x70+slot*0x1d8;raw=shared.exact(handle,address,0x40)
            identity=struct.unpack_from('<I',raw)[0]
            if identity==0xffffffff:continue
            x,y=struct.unpack_from('<ii',raw,0x10);projected=struct.unpack_from('<ff',raw,0x18)
            row={'identity':identity,'xy':[x,y],'projected':list(projected),'address':hex(address),'pool':hex(pool),'slot':slot,'header_hex':raw.hex()}
            all_entries.append(row)
            if identity==expected['catalog_id'] and (x,y)==xy:matches.append(row)
    require(len(matches)==1,'FRUIT_NPC_EXACT_ID_XY_MATCH_REQUIRED')
    row=matches[0];require(all(math.isfinite(v) for v in row['projected']),'FRUIT_NPC_PROJECTED_NONFINITE')
    return {'target':row,'all_entries':all_entries}


def dialogue(client):
    handle,ui=client['handle'],client['ui']
    mode,selector=struct.unpack('<HH',shared.exact(handle,ui+0xccc1c,4))
    page,pages=struct.unpack('<II',shared.exact(handle,0x5b7bf0,8))
    opened=bool(int.from_bytes(shared.exact(handle,ui+0xaff00,4),'little'))
    text_pointer=int.from_bytes(shared.exact(handle,ui+0xcff50,4),'little')
    lines=[]
    if opened:
        require(0<pages<=20 and text_pointer>0x10000,'DIALOGUE_TEXT_BUFFER_BOUNDS')
        raw=shared.exact(handle,text_pointer,pages*5*128)
        lines=[raw[i:i+128].split(b'\0')[0].hex() for i in range(0,len(raw),128)]
    return {'open':bool(int.from_bytes(shared.exact(handle,ui+0xaff00,4),'little')),
            'mode':mode,'selector':selector,'page':page,'pages':pages,'text_lines_hex':lines,
            'request_word':int.from_bytes(shared.exact(handle,0x5b7bfa,2),'little'),
            'reply_word':int.from_bytes(shared.exact(handle,0x5b7bf8,2),'little'),
            'context':shared.exact(handle,ui+0xccd36,1)[0],
            'widget':int.from_bytes(shared.exact(handle,ui+0x232dee,2),'little',signed=True)}


def open_npc(client,quest,expected_text):
    state=npc_state(client,quest);x,y=map(round,state['target']['projected'])
    require(0<=x<800 and 0<=y<560,'FRUIT_NPC_NOT_IN_VISIBLE_WORLD_VIEWPORT')
    click(client['hwnd'],x,y)
    source=[row for row in quest['dialogue_candidates'].values() if row['text_id']==expected_text]
    require(len(source)==1,'EXPECTED_DIALOGUE_SOURCE_REQUIRED')
    expected=bytes.fromhex(source[0]['raw_hex']).split(b',',1)[1]
    # Mode1 sets ccc1e=ffff; it does not retain a text ID. Compare source text
    # prefix against the actual native line buffer rather than label ffff as ID.
    expected=re.sub(rb'/c[0-9]',b'',expected).replace(b'\\n',b'').strip()[:16]
    def ready():
        actual=dialogue(client)
        text=b''.join(bytes.fromhex(line) for line in actual['text_lines_hex'])
        text=re.sub(rb'/c[0-9]',b'',text).replace(b'\\n',b'')
        return actual if actual['open'] and actual['mode']==1 and expected and expected in text else None
    return {'npc':state,'expected_text_id':expected_text,'source_prefix_hex':expected.hex(),
            'dialogue':wait_until(ready,10,'FRUIT_NATIVE_DIALOGUE_NOT_OPEN')}


def confirm(client):
    events=[]
    for _ in range(12):
        state=dialogue(client);require(state['open'] and state['mode']==1 and 0<=state['page']<state['pages']<=12,'FRUIT_DIALOGUE_PAGE_BOUNDS')
        control=3 if state['page']+1<state['pages'] else 0
        point=owned.control_point(client['handle'],client['ui'],state['widget'],control)
        click(client['hwnd'],*point);events.append({'before':state,'control':control,'point':point})
        if control==0:return events
        wait_until(lambda:dialogue(client)['page']==state['page']+1,5,'FRUIT_NEXT_PAGE_FAILED')
    raise RuntimeError('FRUIT_DIALOGUE_PAGE_BUDGET')


def native(client):
    state=owned.native(client['handle'],client['ui'])
    return {'journal':state['quest_journal'],'map':state['world_map'],
            'slots_hex':shared.exact(client['handle'],client['ui']+0x8560c,30*24).hex()}


def db_state(path):
    with closing(shared.ro(path)) as db:
        names=[row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE 'character_%' OR name LIKE '%quest%' OR name='diagnostic_inventory_slots') ORDER BY name")]
        return {name:[[v.hex() if isinstance(v,bytes) else v for v in row] for row in db.execute('SELECT * FROM "'+name+'" ORDER BY 1,2')] for name in names}


def prepare(args):
    args.output.mkdir(parents=True,exist_ok=False);quest=source_quest(args.mission)
    original=fixture.LIVE_CLIENT.read_bytes();expected=bytearray(original)
    site=original.index(bytes.fromhex('68 20 0a 00 00 68 9c 47 5b 00'));expected[site+1:site+5]=struct.pack('<I',2598)
    require(fixture.CLIENT.read_bytes()==expected,'PRIVATE_CLIENT_NOT_EXACT_PORT_COPY')
    database=args.output/'town-diagnostic-accounts.db'
    with closing(shared.ro(SOURCE)) as source,closing(sqlite3.connect(database)) as target:source.backup(target)
    config=json.loads(CONFIG.read_text('utf-8'));config['database']['path']=str(database)
    config['logging']['file']=str(args.output/'server.log');config['server'].update(host='127.0.0.1',port=2598)
    dev=config['development']
    for key,value in list(dev.items()):
        if key.startswith('diagnostic_') and isinstance(value,bool):dev[key]=False
    dev['diagnostic_town'].update(spawn_guides=False,quest_progress=False,map_probe=False,player_visibility=False,
        battle_after_quest=False,door_after_battle=False,door_routes=False,native_npc_placements_only=True)
    dev['native_monster_placements_only']=True
    config['world']={'fruit_village_quests':{'enabled':True,'allow_inferred_placements':True,'navigation':str(ROOT/'artifacts/world-atlas/fruit-13-12.json')},'clock':{'enabled':True,'sync_seconds':5}}
    shared.dump(args.output/'server-config.json',config)
    env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1'
    with (args.output/'migration.log').open('wb') as log:
        subprocess.run([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--migrate-only'],cwd=ROOT,env=env,
            stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,check=True,timeout=30)
    from tools.strike_lab import import_native_quests,import_native_quest_sources,import_fruit_quest_sources
    with closing(sqlite3.connect(database)) as db:
        imports={'descriptions':import_native_quests.import_catalog(db,fixture.LIVE_CLIENT.parent),
                 'source':import_native_quest_sources.import_catalog(db,fixture.LIVE_CLIENT.parent)}
        db.commit()
        imports['fruit']=import_fruit_quest_sources.install(db,import_fruit_quest_sources.qualified_payload(fixture.LIVE_CLIENT.parent))
        role=bytearray(db.execute('SELECT logical FROM character_role_snapshots WHERE character_id=4').fetchone()[0]);require(len(role)==25 and role[0]==0x22,'ROLE22_FIXTURE_REQUIRED');role[1]=10
        db.execute('UPDATE character_role_snapshots SET logical=? WHERE character_id=4',(bytes(role),))
        db.execute("INSERT INTO character_experience VALUES(4,0,'CUSTOM-0012') ON CONFLICT(character_id) DO UPDATE SET total=0")
        db.execute('UPDATE recovered_positions SET area=13,scene=12,x=?,y=?,revision=revision+1 WHERE character_id=4',
                   (quest['npc']['x_text_hint']+1,quest['npc']['y_text_hint']))
        db.execute('DELETE FROM character_weapon_slot_metadata WHERE character_id=4 AND slot BETWEEN 0 AND 29')
        for slot in range(30):
            item,count={0:(5098,15),1:(5091,5),2:(3464,20)}.get(slot,(0,0))
            if getattr(args,'insufficient',False) and item==quest['requirement']['item_key']:count=quest['requirement']['quantity']-1
            db.execute("INSERT INTO diagnostic_inventory_slots VALUES(4,?,?,?,1,?,'CUSTOM-0015') ON CONFLICT(character_id,slot) DO UPDATE SET item_id=excluded.item_id,count=excluded.count,revision=1,source_sha256=excluded.source_sha256,design_id=excluded.design_id",(slot,item,count,fixture.WEAPON_SOURCE_SHA))
        db.commit();require(db.execute('PRAGMA quick_check').fetchone()==('ok',),'FIXTURE_INTEGRITY')
    shared.dump(args.output/'fixture.json',{'origin':'CUSTOM_TEST_NOT_NATIVE','quest':quest,'imports':imports,'source_db_sha256':fixture.sha(SOURCE),'after':db_state(database),
        'spawn_policy':'CUSTOM-0051; nearby source-hint XY, not native birthplace','insufficient':getattr(args,'insufficient',False),'server_sha256':fixture.sha(args.server_candidate)})


def saved_summary(path):
    with closing(shared.ro(path)) as db:
        journal=db.execute('SELECT values_blob FROM character_quest_journals WHERE character_id=4').fetchone()
        xp=db.execute('SELECT total FROM character_experience WHERE character_id=4').fetchone()
        balance=db.execute('SELECT reputation FROM character_fruit_quest_balances WHERE character_id=4').fetchone()
        return {'journal':list(struct.unpack('<15I',journal[0])) if journal else [0]*15,
            'xp':xp[0] if xp else 0,'reputation':balance[0] if balance else 0,
            'bag':[list(row) for row in db.execute('SELECT slot,item_id,count FROM diagnostic_inventory_slots WHERE character_id=4 AND slot BETWEEN 0 AND 29 ORDER BY slot')]}


def projected(client,saved):
    actual=native(client)
    if actual['journal']!=saved['journal']:return None
    raw=bytes.fromhex(actual['slots_hex'])
    require(len(saved['bag'])==30,'COMPLETE_BAG_REQUIRED')
    for slot,item,count in saved['bag']:
        if raw[slot*24:slot*24+6]!=struct.pack('<IH',count,item):return None
    return actual


def worker(args):
    result={'accepted':False,'stages':[],'owned_client_pids':[],'rendered_pixels_tested':False}
    desktop=desktop_names();client=None;database=args.output/'town-diagnostic-accounts.db';quest=source_quest(args.mission)
    def save():shared.dump(args.output/'ui-result.json',result)
    def log_stage(name,value):result['stages'].append({'name':name,**value});save()
    try:
        require(desktop['current'].startswith('God2Lab-') and desktop['current']!=desktop['input'],'HIDDEN_DESKTOP_REQUIRED')
        result['desktop_before']=desktop;client=login();result['owned_client_pids'].append(client['process'].pid)
        before=saved_summary(database);initial=wait_until(lambda:projected(client,before),10,'FRUIT_INITIAL_PROJECTION');log_stage('login',{'saved':before,'native':initial})
        offer=open_npc(client,quest,quest['dialogue_candidates']['offer']['text_id']);events=confirm(client)
        def accepted():
            value=saved_summary(database)
            if (1<<16)|args.mission not in value['journal']:return None
            require(value['bag']==before['bag'] and value['xp']==before['xp'] and value['reputation']==before['reputation'],'ACCEPT_GRANTED_ASSETS')
            actual=projected(client,value)
            return {'saved':value,'native':actual} if actual else None
        acceptance=wait_until(accepted,12,'FRUIT_ACCEPT_NOT_COMMITTED');log_stage('accept',{'offer':offer,'controls':events,**acceptance})
        shared.close_client(client);client=None;time.sleep(1);client=login();result['owned_client_pids'].append(client['process'].pid)
        restored=saved_summary(database);require(restored==acceptance['saved'],'FRUIT_RELOGIN_SAVE_CHANGED')
        replay_native=wait_until(lambda:projected(client,restored),10,'FRUIT_RELOGIN_PROJECTION');log_stage('relogin',{'saved':restored,'native':replay_native})
        if args.insufficient:
            unchanged=db_state(database);response=open_npc(client,quest,quest['dialogue_candidates']['incomplete']['text_id']);events=confirm(client);time.sleep(1)
            require(db_state(database)==unchanged,'FRUIT_INSUFFICIENT_MUTATED_DB')
            require(projected(client,restored) is not None,'FRUIT_INSUFFICIENT_CHANGED_NATIVE_STATE')
            log_stage('insufficient',{'dialogue':response,'controls':events,'database_unchanged':True});result['accepted']=True
        else:
            completion=open_npc(client,quest,quest['dialogue_candidates']['completion']['text_id']);events=confirm(client)
            def completed():
                value=saved_summary(database)
                if (1<<16)|args.mission in value['journal']:return None
                require(value['xp']==before['xp']+quest['external_historical']['reward_exp_reported'],'FRUIT_XP_MISMATCH')
                require(value['reputation']==before['reputation']+1,'FRUIT_REPUTATION_MISMATCH')
                key=quest['requirement']['item_key'];quantity=quest['requirement']['quantity']
                require(sum(row[2] for row in before['bag'] if row[1]==key)-sum(row[2] for row in value['bag'] if row[1]==key)==quantity,'FRUIT_CONSUMPTION_MISMATCH')
                actual=projected(client,value)
                return {'saved':value,'native':actual} if actual else None
            settlement=wait_until(completed,12,'FRUIT_SUBMIT_NOT_COMMITTED');log_stage('submit',{'dialogue':completion,'controls':events,**settlement})
            replay_before=db_state(database);post=open_npc(client,quest,quest['dialogue_candidates']['idle_after']['text_id']);events=confirm(client);time.sleep(1)
            require(db_state(database)==replay_before,'FRUIT_COMPLETED_REOPEN_MUTATED_DB')
            require(projected(client,settlement['saved']) is not None,'FRUIT_COMPLETED_REOPEN_PROJECTION_CHANGED')
            log_stage('completed_reopen',{'dialogue':post,'controls':events,'database_unchanged':True});result['accepted']=True
    except Exception as error:result['error']=str(error);result['traceback']=traceback.format_exc()
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
    require(args.output.is_relative_to((ROOT/'artifacts/playtests').resolve()),'ISOLATED_OUTPUT_REQUIRED')
    paths={'source_db':SOURCE,'live_client':fixture.LIVE_CLIENT,'private_client':fixture.CLIENT,'formal_config':FORMAL}
    result={'accepted':False,'before':{key:fixture.sha(path) for key,path in paths.items()},'server_sha256':fixture.sha(args.server_candidate)}
    server=runner=None
    try:
        with socket.socket() as probe:require(probe.connect_ex(('127.0.0.1',2598))!=0,'PRIVATE_PORT_IN_USE')
        prepare(args)
        if args.prepare_only:result['prepared_only']=True
        else:
            env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1';env.pop('GOD2_PRIVATE_SIDECAR_COMMAND',None)
            with (args.output/'stdout.log').open('wb') as stdout,(args.output/'runner.log').open('wb') as runnerlog:
                server=subprocess.Popen([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--run-for','210'],cwd=ROOT,env=env,
                    stdout=stdout,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);result['server_pid']=server.pid
                def listening():
                    require(server.poll() is None,'SERVER_EXITED')
                    with socket.socket() as probe:return probe.connect_ex(('127.0.0.1',2598))==0
                wait_until(listening,10,'SERVER_NOT_LISTENING')
                runner=subprocess.Popen([str(fixture.RUNNER),sys.executable,'-X','utf8','-B',str(Path(__file__).resolve()),'--worker','--output',str(args.output),'--mission',str(args.mission)]+(['--insufficient'] if args.insufficient else []),
                    cwd=ROOT,env=env,stdout=runnerlog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                result['runner_pid']=runner.pid;result['runner_exit']=runner.wait(timeout=190)
                result['ui']=json.loads((args.output/'ui-result.json').read_text('utf-8'));result['accepted']=result['runner_exit']==0 and result['ui']['accepted']
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
    print(json.dumps({key:result.get(key) for key in ('accepted','prepared_only','error','server_sha256')}));return 0 if result['accepted'] or result.get('prepared_only') else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--mission',required=True,type=int,choices=(234,236,237,238));parser.add_argument('--server-candidate',type=Path)
    parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--insufficient',action='store_true')
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS);args=parser.parse_args()
    if args.worker:return worker(args)
    if args.server_candidate is None:parser.error('--server-candidate required')
    return owner(args)


if __name__=='__main__':raise SystemExit(main())
