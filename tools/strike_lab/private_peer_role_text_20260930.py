"""Two current port-only clients on an owned hidden desktop, per-exe TW/CN locale.

The existing launcher-supported LEProc/per-image profile selects each language.
No global launcher setting/profile/client is changed. All saves and characters
are a disposable clone; observations use read-only handles and window-local UI
input. No screenshot, foreground activation, live-memory write or packet injection.
"""
import argparse
from contextlib import closing
import hashlib
import json
import os
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
import private_weapon_peer_appearance_20260927 as peer
import private_scene_actor_route_ui as ground
import private_owned_companions_ui as owned
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,type_ascii
from tools.strike_lab.run_private_owned_companions import RUNNER

LIVE=ROOT.parent/'God2/God2.exe';CLIENT_SHA='9be38ef858bc9c63b6f296cae4a8e601ddcfaf614700e725c4bec44065b53336'
SOURCE=ROOT/'artifacts/playtests/private-weapon-peer-20260927-04/town-diagnostic-accounts.db'
LE=LIVE.parent/'compat-tools/LocaleEmulator/LEProc.exe';PORT=2598
MAPPED_SHA='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
RUNNER_SHA='8a4bd51dcf48753f5934fb1088d4aac10603ad8506ecc988a07d83febe878ef4'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read16(client):
    actor=int.from_bytes(peer.exact(client['handle'],client['ui']+0x86888,4),'little')
    localroot=actor-0x90;world=localroot-0x1539683c;index=int.from_bytes(peer.exact(client['handle'],localroot+0x4544,2),'little')
    require(index<4096,'SELF_RENDERER_SCOPE')
    text=peer.exact(client['handle'],actor+0x37,16).split(b'\0',1)[0]
    label=peer.exact(client['handle'],world+0x39c+index*0xa7e0+0x81,17).split(b'\0',1)[0]
    return {'text':text.hex(),'renderer':label.hex(),'locale':peer.exact(client['handle'],0x6f4ca8,2).hex(),
            'native_language_words':peer.exact(client['handle'],0x59dfd8,4).hex()}
def centered(text):return b' '*max(0,(14-len(text))//2)+text
def stable(database):
    with closing(peer.ro(database)) as db:
        result={}
        for name,sql in db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
            condition=' WHERE character_id<>4' if name in ('recovered_positions','character_role_text') else ''
            rows=sorted(repr(row) for row in db.execute('SELECT * FROM "'+name.replace('"','""')+'"'+condition))
            result[name]={'sql':sql,'rows':len(rows),'sha256':hashlib.sha256('\n'.join(rows).encode()).hexdigest()}
        return result
def roles(database):
    with closing(peer.ro(database)) as db:return [list(row) for row in db.execute('SELECT character_id,hex(legacy_text),utf8_text,codepage,revision FROM character_role_text ORDER BY character_id')]
def position(database,identity):
    with closing(peer.ro(database)) as db:return list(db.execute('SELECT area,scene,x,y,revision FROM recovered_positions WHERE character_id=?',(identity,)).fetchone())

def worker(args):
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'));database=args.output/'town-diagnostic-accounts.db'
    before=desktop_names();clients=[];loaders=[];result={'accepted':False,'rendered_pixels_tested':False,'source_page':args.source_page}
    def save():peer.dump(args.output/'ui-result.json',result)
    try:
        require(before['current'].startswith('God2Lab-') and before['current']!=before['input'],'HIDDEN_DESKTOP_REQUIRED');result['desktop_before']=before
        def launch(identity,page):
            image=Path(fixture['clients'][str(page)]['path']);require(sha(image)==fixture['clients'][str(page)]['sha256'],'PRIVATE_IMAGE_CHANGED')
            launcher=subprocess.Popen([str(LE),'-run',str(image),'127.0.0.1','127.0.0.1','6001','1'],cwd=LIVE.parent,
                creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);loaders.append(launcher)
            def find():
                found=[]
                for process in psutil.process_iter(['pid','exe']):
                    if process.info['exe'] and Path(process.info['exe']).resolve()==image.resolve():found.append(process)
                require(len(found)<=1,'MULTIPLE_PRIVATE_IMAGE_PROCESSES');return found[0] if found else None
            process=wait_until(find,35,'LOCALE_CLIENT_NOT_CREATED')
            client={'process':process,'identity':identity,'page':page};clients.append(client)
            result['owned_client_pids']=[c['process'].pid for c in clients];save()
            hwnd=wait_until(lambda:peer.window_for(process.pid),35,'OWNED_WINDOW_MISSING');client['hwnd']=hwnd
            # A cold Locale Emulator process can expose its window before the
            # title screen accepts the first click. Give that transition a
            # bounded window, then wait for this exact owner's server bind.
            time.sleep(12);click(hwnd,512,464);time.sleep(4)
            click(hwnd,437,232);type_ascii(hwnd,'codexslow' if identity==4 else 'codexfixed')
            bound='RECOVERED_ACCOUNT_BOUND account_id='+str(identity)
            previous_bound=(args.output/'server.log').read_text('utf-8',errors='replace').count(bound)
            click(hwnd,437,263);type_ascii(hwnd,'labtest2345');click(hwnd,452,304)
            wait_until(lambda:(args.output/'server.log').read_text('utf-8',errors='replace').count(bound)>previous_bound,35,'OWNED_LOGIN_NOT_BOUND')
            time.sleep(4)
            click(hwnd,330,145);click(hwnd,452,413);time.sleep(4);click(hwnd,330,150);click(hwnd,452,376);time.sleep(4);click(hwnd,452,370);time.sleep(12)
            client['handle']=peer.kernel.OpenProcess(0x1010,False,process.pid);require(client['handle'],'READONLY_PROCESS_OPEN')
            client['ui']=peer.find_ui(client['handle'],identity,(0,3,4));current=read16(client)
            language,sub_language=struct.unpack('<HH',bytes.fromhex(current['native_language_words']))
            require(language==4 and ((sub_language==2)==(page==936)),'NATIVE_LANGUAGE_NOT_SELECTED')
            return client
        def close(client):
            if client.get('handle'):peer.kernel.CloseHandle(client.pop('handle'))
            process=client['process']
            if process.is_running():
                if client.get('hwnd'):peer.user.PostMessageW(client['hwnd'],0x10,0,0)
                try:process.wait(timeout=4)
                except psutil.TimeoutExpired:process.terminate();process.wait(timeout=5)
        def sees(observer,identity,text):
            row=peer.remote(observer['handle'],observer['ui'],identity)
            if row and row['renderer']>=0 and row['text_fields'][1]==text.hex() and row['display_texts'][1]==centered(text).hex():return row
            return None
        source=args.source_page;recipient=936 if source==950 else 950
        actor=launch(4,source);observer=launch(5,recipient)
        original='測試' if source==950 else '测试';converted='测试' if recipient==936 else '測試'
        own=read16(actor);require(own['text']==original.encode('cp'+str(source)).hex(),'SELF_SEEDED_CJK_TEXT_MISMATCH')
        result['initial']={'self':own,'observer_self':read16(observer),
            'observer_sees_actor':wait_until(lambda:sees(observer,4,converted.encode('cp'+str(recipient))),15,'PEER_CJK_NATIVE_RECEIVER_MISSING'),
            'actor_sees_observer':wait_until(lambda:sees(actor,5,'神仙'.encode('cp'+str(source))),15,'REVERSE_PEER_CJK_MISSING'),
            'roles':roles(database)}
        invariant=stable(database);save()
        initial_state=ground.world_state(actor['handle'],actor['ui']);initial_target=(initial_state['x']+1,initial_state['y'])
        click(actor['hwnd'],*ground.ground_point(actor['handle'],initial_state,*initial_target))
        def initially_moved():
            saved_position=position(database,4);local=ground.world_state(actor['handle'],actor['ui'])
            remote=sees(observer,4,converted.encode('cp'+str(recipient)))
            if saved_position[:4]==[4,3,*initial_target] and [local['x'],local['y']]==list(initial_target) and remote and [remote['x'],remote['y']]==list(initial_target):
                return {'before':initial_state,'saved':saved_position,'self':local,'remote':remote}
            return None
        result['movement_before_update']=wait_until(initially_moved,15,'MOVEMENT_BEFORE_TEXT_UPDATE_FAILED');save()
        baseline=result['movement_before_update']['remote'];text='PeerNativeProof';require(len(text)==15,'ASCII_FIELD_BOUND')
        result['ui_edits']=[]
        for value,revision in (('',8),(text,9)):
            hud=int.from_bytes(peer.exact(actor['handle'],actor['ui']+0x232db6,2),'little');click(actor['hwnd'],*owned.control_point(actor['handle'],actor['ui'],hud,5))
            def panel():
                widget=int.from_bytes(peer.exact(actor['handle'],actor['ui']+0x232dda,2),'little')
                if widget<128 and int.from_bytes(peer.exact(actor['handle'],actor['ui']+0x5bfa4,2),'little')==2:return widget
                return None
            widget=wait_until(panel,5,'ROLE_INPUT_MODE_MISSING')
            for _ in range(16):
                require(peer.user.PostMessageW(actor['hwnd'],0x100,8,0x000e0001),'BACKSPACE_KEYDOWN_FAILED');time.sleep(.06)
                require(peer.user.PostMessageW(actor['hwnd'],0x101,8,0xc00e0001),'BACKSPACE_KEYUP_FAILED');time.sleep(.06)
            type_ascii(actor['hwnd'],value);time.sleep(.5)
            input_text=peer.exact(actor['handle'],0x596e54,16).split(b'\0',1)[0]
            result['last_ui_input']={'expected':value.encode().hex(),'observed':input_text.hex()};save()
            require(input_text==value.encode(),'ROLE_UI_INPUT_NOT_EDITED')
            click(actor['hwnd'],*owned.control_point(actor['handle'],actor['ui'],widget,0x10))
            updated=wait_until(lambda:sees(observer,4,value.encode()),12,'EXISTING_PEER_UI_EDIT_NOT_UPDATED')
            require(read16(actor)['text']==value.encode().hex(),'OWNER_UI_EDIT_NOT_VISIBLE')
            for key in ('identity','x','y','status','spawn_components','scalar5','scalar6','live_components'):
                require(updated[key]==baseline[key],'PEER_NON_TEXT_FIELD_CHANGED_'+key)
            for index in (0,2):
                require(updated['text_fields'][index]==baseline['text_fields'][index] and updated['display_texts'][index]==baseline['display_texts'][index],'PRIMARY_OR_THIRD_TEXT_CHANGED')
            saved=roles(database);row=next(r for r in saved if r[0]==4)
            require(row[1]==(value.encode()+bytes(16-len(value))).hex().upper() and row[2:]==[value,source,revision],'EDIT_DURABLE_ROW_MISMATCH')
            result['ui_edits'].append({'native20_and_peer6f':True,'self':read16(actor),'remote':updated,'saved':row});save()
        state=ground.world_state(actor['handle'],actor['ui']);target=(state['x']+1,state['y'])
        click(actor['hwnd'],*ground.ground_point(actor['handle'],state,*target))
        def moved():
            saved_position=position(database,4);local=ground.world_state(actor['handle'],actor['ui']);remote=sees(observer,4,text.encode())
            if saved_position[:4]==[4,3,*target] and [local['x'],local['y']]==list(target) and remote and [remote['x'],remote['y']]==list(target):
                return {'before':state,'saved':saved_position,'self':local,'remote':remote}
            return None
        result['movement_after_update']=wait_until(moved,15,'MOVEMENT_AFTER_TEXT_UPDATE_FAILED');save()
        close(observer);wait_until(lambda:peer.remote(actor['handle'],actor['ui'],5) is None,12,'OBSERVER_DEPARTURE_MISSING')
        observer=launch(5,recipient)
        result['late_observer']=wait_until(lambda:sees(observer,4,text.encode()),15,'LATE_OBSERVER_ROLE_TEXT_MISSING')
        require([result['late_observer']['x'],result['late_observer']['y']]==list(target),'LATE_OBSERVER_POSITION_REGRESSED')
        close(actor);wait_until(lambda:peer.remote(observer['handle'],observer['ui'],4) is None,12,'ACTOR_DEPARTURE_MISSING')
        actor=launch(4,source);result['actor_relogin']={'self':read16(actor),
            'remote':wait_until(lambda:sees(observer,4,text.encode()),15,'RELOGIN_PEER_ROLE_TEXT_MISSING')}
        require(result['actor_relogin']['self']['text']==text.encode().hex(),'RELOGIN_SELF_ROLE_TEXT_MISSING')
        require(position(database,4)[:4]==[4,3,*target] and [result['actor_relogin']['remote']['x'],result['actor_relogin']['remote']['y']]==list(target),'RELOGIN_POSITION_REGRESSED')
        require(roles(database)==saved,'RELOGIN_CHANGED_SAVED_TEXT');require(stable(database)==invariant,'UNRELATED_DATABASE_STATE_CHANGED')
        result['saved_preserved']=True;result['accepted']=True
    except BaseException as error:result['error']=str(error);result['traceback']=traceback.format_exc()
    finally:
        for client in reversed(clients):
            try:close(client)
            except Exception as error:result.setdefault('cleanup_errors',[]).append(str(error))
        for process in loaders:
            if process.poll() is None:process.terminate();process.wait(timeout=5)
        result['desktop_after']=desktop_names();result['desktop_unchanged']=before==result['desktop_after']
        result['all_clients_closed']=not any(psutil.pid_exists(c['process'].pid) for c in clients)
        result['accepted']=bool(result['accepted'] and result['desktop_unchanged'] and result['all_clients_closed'] and not result.get('cleanup_errors'));save()
    return 0 if result['accepted'] else 1

def prepare(args):
    require(sha(LIVE)==CLIENT_SHA and sha(RUNNER)==RUNNER_SHA,'CURRENT_CLIENT_OR_RUNNER_PIN_CHANGED')
    args.output.mkdir(parents=True,exist_ok=False);database=args.output/'town-diagnostic-accounts.db'
    raw=LIVE.read_bytes();needle=bytes.fromhex('68 20 0a 00 00 68 9c 47 5b 00');require(raw.count(needle)==1,'UNIQUE_PORT_SITE_REQUIRED')
    changed=bytearray(raw);offset=raw.index(needle)+1;struct.pack_into('<I',changed,offset,PORT)
    clients={}
    for page,locale,zone in ((950,'zh-TW','Taipei Standard Time'),(936,'zh-CN','China Standard Time')):
        image=LIVE.with_name(args.output.name+'-'+str(page)+'-2598.exe');profile=Path(str(image)+'.le.config')
        require(not image.exists() and not profile.exists(),'NEW_PRIVATE_IMAGE_AND_PROFILE_REQUIRED')
        with image.open('xb') as stream:stream.write(changed)
        xml='<LEConfig><Profiles><Profile Name="God2 Chinese" Guid="9548b642-f82c-4883-a523-425904744e6f" MainMenu="false"><Parameter></Parameter><Location>'+locale+'</Location><Timezone>'+zone+'</Timezone><RunAsAdmin>false</RunAsAdmin><RedirectRegistry>false</RedirectRegistry><IsAdvancedRedirection>false</IsAdvancedRedirection><RunWithSuspend>false</RunWithSuspend></Profile></Profiles></LEConfig>'
        with profile.open('x',encoding='utf-8') as stream:stream.write(xml)
        clients[str(page)]={'path':str(image),'sha256':sha(image),'profile':str(profile),'profile_sha256':sha(profile)}
    with closing(peer.ro(SOURCE)) as source,closing(sqlite3.connect(database)) as target:source.backup(target)
    config=json.loads(SOURCE.with_name('server-config.json').read_text('utf-8'));config['database']['path']=str(database)
    config['logging']['file']=str(args.output/'server.log');config['server'].update(host='127.0.0.1',port=PORT,character_port=0)
    config['development']['diagnostic_remote_actor_language']=int(args.source_page==936)
    peer.dump(args.output/'server-config.json',config)
    env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1'
    with (args.output/'migration.log').open('wb') as log:
        subprocess.run([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--migrate-only'],cwd=ROOT,env=env,
            check=True,timeout=60,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    with closing(sqlite3.connect(database)) as db:
        for identity,x,text,page in ((4,126,'測試' if args.source_page==950 else '测试',args.source_page),(5,127,'神仙',950)):
            db.execute('INSERT INTO recovered_positions VALUES(?,4,3,?,126,1) ON CONFLICT(character_id) DO UPDATE SET area=4,scene=3,x=excluded.x,y=126,revision=1',(identity,x))
            encoded=text.encode('cp'+str(page));db.execute('DELETE FROM character_role_text WHERE character_id=?',(identity,))
            db.execute("INSERT INTO character_role_text VALUES(?,?,?,?,7,'CUSTOM_DESIGNED',?,'CUSTOM-0056')",(identity,encoded+bytes(16-len(encoded)),text,page,MAPPED_SHA))
        db.commit();require(db.execute('PRAGMA quick_check').fetchone()==('ok',),'CLONE_INTEGRITY')
    peer.dump(args.output/'fixture.json',{'source_database':str(SOURCE),'source_sha256':sha(SOURCE),'clients':clients,
        'client_source_sha256':CLIENT_SHA,'changed_offsets':[i for i,(a,b) in enumerate(zip(raw,changed)) if a!=b],
        'source_page':args.source_page,'authority':'CUSTOM_TEST_NOT_NATIVE','seeded_role_text':roles(database)})

def owner(args):
    args.output=args.output.resolve();args.server_candidate=args.server_candidate.resolve()
    sources={'live_client':LIVE,'live_locale_profile':Path(str(LIVE)+'.le.config'),'source_database':SOURCE,
        'source_config':SOURCE.with_name('server-config.json'),'launcher_settings':LIVE.parent/'config/user.settings',
        'locale_global_config':LE.with_name('LEConfig.xml'),'locale_launcher':LE,'locale_loader':LE.with_name('LoaderDll.dll'),
        'locale_runtime':LE.with_name('LocaleEmulator.dll')}
    result={'accepted':False,'before':{k:sha(p) for k,p in sources.items()},'candidate_sha256':sha(args.server_candidate)};server=runner=None
    try:
        with socket.socket() as probe:require(probe.connect_ex(('127.0.0.1',PORT))!=0,'PRIVATE_PORT_ALREADY_USED')
        prepare(args);env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1';env.pop('GOD2_PRIVATE_SIDECAR_COMMAND',None)
        with (args.output/'stdout.log').open('wb') as log,(args.output/'runner.log').open('wb') as runnerlog:
            server=subprocess.Popen([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--run-for','420'],cwd=ROOT,env=env,
                stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);result['server_pid']=server.pid
            def listening():
                require(server.poll() is None,'PRIVATE_SERVER_EXITED')
                with socket.socket() as probe:return probe.connect_ex(('127.0.0.1',PORT))==0
            wait_until(listening,12,'PRIVATE_SERVER_NOT_LISTENING')
            runner=subprocess.Popen([str(RUNNER),sys.executable,'-X','utf8','-B',str(Path(__file__).resolve()),'--worker','--output',str(args.output),'--source-page',str(args.source_page)],cwd=ROOT,env=env,
                stdout=runnerlog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);result['runner_pid']=runner.pid
            result['runner_exit']=runner.wait(timeout=400);result['ui']=json.loads((args.output/'ui-result.json').read_text('utf-8'))
            result['accepted']=runner.returncode==0 and result['ui']['accepted']
    except BaseException as error:result['error']=str(error);result['traceback']=traceback.format_exc()
    finally:
        for process in (runner,server):
            if process is not None and process.poll() is None:
                children=psutil.Process(process.pid).children(recursive=True)
                for child in reversed(children):
                    try:child.terminate()
                    except psutil.NoSuchProcess:pass
                process.terminate();process.wait(timeout=5);_,alive=psutil.wait_procs(children,timeout=5)
                for child in alive:child.kill();child.wait(timeout=5)
        fixture_path=args.output/'fixture.json'
        if fixture_path.exists():
            clients=json.loads(fixture_path.read_text('utf-8'))['clients']
            paths={Path(value['path']).resolve() for value in clients.values()}
            for process in psutil.process_iter(['pid','exe']):
                if process.info['exe'] and Path(process.info['exe']).resolve() in paths:
                    try:process.terminate();process.wait(timeout=5)
                    except psutil.NoSuchProcess:pass
            result['private_files_unchanged']=all(sha(Path(value['path']))==value['sha256'] and sha(Path(value['profile']))==value['profile_sha256'] for value in clients.values())
            result['all_private_images_closed']=not any(process.info['exe'] and Path(process.info['exe']).resolve() in paths for process in psutil.process_iter(['exe']))
        result['after']={k:sha(p) for k,p in sources.items()};result['source_files_unchanged']=result['before']==result['after']
        result['candidate_unchanged']=sha(args.server_candidate)==result['candidate_sha256']
        result['all_owned_processes_closed']=(runner is None or runner.poll() is not None) and (server is None or server.poll() is not None)
        result['accepted']=bool(result['accepted'] and result['source_files_unchanged'] and result['candidate_unchanged'] and result['all_owned_processes_closed'] and result.get('private_files_unchanged') and result.get('all_private_images_closed'))
        if args.output.exists():peer.dump(args.output/'run-result.json',result)
    print(json.dumps({k:result.get(k) for k in ('accepted','error','candidate_sha256','source_files_unchanged','all_owned_processes_closed')}));return 0 if result['accepted'] else 1

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--server-candidate',type=Path);parser.add_argument('--source-page',type=int,choices=(950,936),default=950);parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.worker:return worker(args)
    if args.server_candidate is None:parser.error('--server-candidate required')
    return owner(args)
if __name__=='__main__':raise SystemExit(main())
