"""Hidden native two-player chat after immediate login and owned room transfer.

Uses a disposable backup of the formal database. No live save/client changes,
screenshots, foreground input, injection, or client memory writes.
"""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import struct
import subprocess
import sys
import time
import traceback
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]
import private_weapon_peer_appearance_20260927 as shared
import private_current_town_doors_20260927 as doors
import private_scene_actor_route_ui as ground
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,type_ascii,user
FORMAL=ROOT/'artifacts/releases/town-chat-welcome-20260924/server-config.json'
SOURCE=Path(json.loads(FORMAL.read_text('utf-8'))['database']['path'])
shared.fixture.SOURCE_DB=SOURCE

def prepare(args):
    args.output.mkdir(parents=True,exist_ok=False)
    require(shared.fixture.sha(shared.fixture.LIVE_CLIENT)==shared.fixture.CURRENT_CLIENT_SHA,'CURRENT_CLIENT_PIN')
    raw=shared.fixture.LIVE_CLIENT.read_bytes();expected=bytearray(raw)
    at=raw.index(bytes.fromhex('68 20 0a 00 00 68 9c 47 5b 00'))
    expected[at+1:at+5]=struct.pack('<I',2598)
    require(shared.fixture.CLIENT.read_bytes()==expected,'PRIVATE_EXE_NOT_EXACT_PORT_COPY')
    database=args.output/'town-diagnostic-accounts.db'
    with closing(shared.ro(SOURCE)) as source,closing(sqlite3.connect(database)) as target:source.backup(target)
    config=json.loads(FORMAL.read_text('utf-8'))
    config['server'].update(host='127.0.0.1',port=2598)
    config['database']['path']=str(database);config['logging']['file']=str(args.output/'server.log')
    shared.dump(args.output/'server-config.json',config)
    with closing(sqlite3.connect(database)) as db:
        require(db.execute('UPDATE recovered_positions SET area=2,scene=15,x=16,y=19,revision=revision+1 WHERE character_id=2').rowcount==1,'ACTOR2_MISSING')
        require(db.execute('UPDATE recovered_positions SET area=2,scene=4,x=86,y=73,revision=revision+1 WHERE character_id=3').rowcount==1,'ACTOR3_MISSING')
        db.commit();require(db.execute('PRAGMA quick_check').fetchone()==('ok',),'CLONE_INTEGRITY')
    shared.dump(args.output/'fixture.json',{'origin':'CUSTOM_TEST_NOT_NATIVE','characters':[2,3],
        'source_database':str(SOURCE),'source_config_sha256':shared.fixture.sha(FORMAL),
        'scope':'Original saved identities/credentials, only cloned test positions relocated'})

def worker(args):
    result={'accepted':False,'rendered_pixels_tested':False};clients=[];before=desktop_names()
    database=args.output/'town-diagnostic-accounts.db';log=args.output/'server.log'
    def save():shared.dump(args.output/'ui-result.json',result)
    def current_text():return log.read_text('utf-8',errors='replace')
    def saved(identity):
        with closing(shared.ro(database)) as db:return list(db.execute('SELECT area,scene,x,y,revision FROM recovered_positions WHERE character_id=?',(identity,)).fetchone())
    def stable():
        with closing(shared.ro(database)) as db:
            out={}
            for name,sql in db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"):
                table='"'+name.replace('"','""')+'"'
                rows=db.execute('SELECT * FROM '+table+(' WHERE character_id<>2' if name=='recovered_positions' else '')).fetchall()
                out[name]={'schema':sql,'count':len(rows),'sha256':hashlib.sha256('\n'.join(sorted(repr(r) for r in rows)).encode()).hexdigest()}
            return out
    def rings(client,expected):
        ui=client['ui'];handle=client['handle'];visible=struct.unpack('<I',shared.exact(handle,ui+0x39de8,4))[0]
        require(visible>0x10000,'VISIBLE_CHAT_RING_MISSING')
        rows=[]
        for name,address in (('visible',visible),('archive',ui+0x39e20)):
            raw=shared.exact(handle,address,0x67f4);count,oldest,nxt=struct.unpack_from('<3I',raw,0x67e8)
            require(count<=200 and oldest<200 and nxt<200,'CHAT_RING_BOUNDS')
            entries=[{'index':i,'channel':raw[0x6400+i],'text_hex':raw[i*128:(i+1)*128].split(b'\0')[0].hex()} for i in ((oldest+n)%200 for n in range(count))]
            joined=b''.join(bytes.fromhex(row['text_hex']) for row in entries if row['channel']==0)
            text=re.sub(rb'/c[0-9a-fA-F]',b'',joined).decode('cp'+str(client.get('codepage',950)),errors='strict')
            rows.append({'ring':name,'count':count,'entries':entries,'common_text':text,'matched':expected in text})
        return rows if all(r['matched'] for r in rows) else None
    def bubble(peer,sender):
        actor=shared.remote(peer['handle'],peer['ui'],sender)
        if actor is None or not 0<=actor['renderer']<4096:return None
        pool=int(actor['world'],16)+0xaba32e0
        node=pool+actor['renderer']*0xa7e0
        lines=struct.unpack('<H',shared.exact(peer['handle'],node+0x56,2))[0]
        graphic=struct.unpack('<i',shared.exact(peer['handle'],node+0xa4,4))[0]
        return {'sender':sender,'renderer':actor['renderer'],'line_count':lines,
            'bubble_graphic':graphic,'node':hex(node),'pixels_tested':False} if lines>0 and 0<=graphic<4096 else None
    def talk(client,text,recipients):
        name='test' if client['identity']==2 else 'test1';expected=name+': '+text
        offset=len(current_text());click(client['hwnd'],400,584);type_ascii(client['hwnd'],text)
        user.PostMessageW(client['hwnd'],0x100,13,0);user.PostMessageW(client['hwnd'],0x101,13,0)
        evidence={'sender':client['identity'],'text':text,'recipients':{}}
        try:
            for peer in recipients:
                evidence['recipients'][str(peer['identity'])]=wait_until(lambda:rings(peer,expected),10,'NATIVE_VISIBLE_CHAT_MISSING_'+str(peer['identity']))
                if peer['identity']!=client['identity']:
                    evidence.setdefault('native_bubbles',{})[str(peer['identity'])]=wait_until(lambda:bubble(peer,client['identity']),4,'NATIVE_PEER_BUBBLE_MISSING_'+str(peer['identity']))
            evidence['accepted_marker']=wait_until(lambda:next((line for line in current_text()[offset:].splitlines() if 'NATIVE_CHAT_ACCEPTED' in line),None),4,'CHAT_SERVER_MARKER_MISSING')
            if globals().get('CHAT_OBSERVER'):CHAT_OBSERVER(client,recipients,evidence)
            return evidence
        finally:evidence['server_records']=current_text()[offset:];result.setdefault('chat_attempts',[]).append(evidence);save()
    def launch(identity,scene,eager=False):
        process=subprocess.Popen([str(shared.fixture.CLIENT),'127.0.0.1','127.0.0.1','6001','1'],cwd=shared.fixture.CLIENT.parent,
            creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        client={'process':process,'identity':identity};clients.append(client)
        hwnd=wait_until(lambda:shared.window_for(process.pid),35,'OWNED_WINDOW_MISSING');client['hwnd']=hwnd
        time.sleep(2);click(hwnd,512,464);time.sleep(3)
        account='test' if identity==2 else 'test1'
        click(hwnd,437,232);type_ascii(hwnd,account);click(hwnd,437,263);type_ascii(hwnd,account)
        click(hwnd,452,304);time.sleep(4);click(hwnd,330,145);click(hwnd,452,413);time.sleep(4)
        click(hwnd,330,150);click(hwnd,452,376);time.sleep(4);click(hwnd,452,370)
        wait_until(lambda:f'EXISTING_CHARACTER_BOUND character_id={identity};' in current_text() and
            'WORLD_INITIALIZER_TAIL_ACCEPTED' in current_text(),15,'WORLD_TAIL_MISSING')
        if not eager:time.sleep(6)
        client['handle']=shared.kernel.OpenProcess(0x1010,False,process.pid);require(client['handle'],'VM_READ_OPEN_FAILED')
        client['ui']=shared.find_ui(client['handle'],identity,(2 if scene==15 else 0,scene,2))
        if globals().get('LOGIN_OBSERVER'):LOGIN_OBSERVER(client)
        result['owned_client_pids']=[c['process'].pid for c in clients];save();return client
    try:
        require(before['current'].startswith('God2Lab-') and before['current']!=before['input'],'HIDDEN_DESKTOP_REQUIRED')
        result['all_other_saved_state_before']=stable()
        actor=launch(2,15,eager=True)
        result['immediate_login_chat']=talk(actor,'early2',[actor]);save()
        observer=launch(3,4)
        result['initial_scene_isolation']=shared.remote(actor['handle'],actor['ui'],3) is None and shared.remote(observer['handle'],observer['ui'],2) is None
        require(result['initial_scene_isolation'],'INITIAL_SCENE_PEER_LEAK')
        state=ground.world_state(actor['handle'],actor['ui']);pixel=ground.ground_point(actor['handle'],state,16,20)
        offset=len(current_text());click(actor['hwnd'],*pixel,interval=.15)
        wait_until(lambda:saved(2)[1]==4,12,'OWNED_ROOM_EXIT_MISSING')
        wait_until(lambda:'DIAGNOSTIC_TOWN_SCENE_CONTEXT' in current_text()[offset:] and
            ground.world_state(actor['handle'],actor['ui'])['scene']==4,12,'IDENTITY2_RECEIPT_MISSING')
        result['room_return']={'before':state,'after':ground.world_state(actor['handle'],actor['ui']),'saved':saved(2),'server_records':current_text()[offset:]};save()
        result['actor2_to_actor3']=talk(actor,'after-room2',[actor,observer])
        result['actor3_to_actor2']=talk(observer,'reply3',[actor,observer])
        wait_until(lambda:shared.remote(actor['handle'],actor['ui'],3) and shared.remote(observer['handle'],observer['ui'],2),10,'MUTUAL_NATIVE_ACTORS_MISSING')
        result['mutual_actor_presence']=True
        if globals().get('FINAL_OBSERVER'):FINAL_OBSERVER(clients,result,args,talk)
        result['all_other_saved_state_after']=stable()
        require(result['all_other_saved_state_after']==result['all_other_saved_state_before'],'CHAT_CHANGED_OTHER_SAVED_ROWS')
        require(all(c['process'].poll() is None for c in clients),'CLIENT_EXITED')
        result['accepted']=True
    except Exception as error:
        result['error']=str(error);result['traceback']=traceback.format_exc()
        if globals().get('FAILURE_OBSERVER'):FAILURE_OBSERVER(clients,result,args)
    finally:
        for client in clients:
            try:shared.close_client(client)
            except Exception as error:result['cleanup_error']=str(error)
        result['desktop_unchanged']=desktop_names()==before;result['all_clients_closed']=all(c['process'].poll() is not None for c in clients)
        result['accepted']=bool(result['accepted'] and result['desktop_unchanged'] and result['all_clients_closed'] and not result.get('cleanup_error'));save()
    return 0 if result['accepted'] else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--server-candidate',type=Path);parser.add_argument('--worker',action='store_true');parser.add_argument('--prepare-only',action='store_true')
    args=parser.parse_args()
    if args.worker:raise SystemExit(worker(args))
    if args.server_candidate is None:parser.error('--server-candidate required')
    shared.prepare=prepare;shared.__file__=str(Path(__file__).resolve())
    raise SystemExit(shared.owner(args))
