"""Owned hidden desktop native logout/delete acceptance, read-only observer."""
import argparse,ctypes as c,hashlib,json,os,sqlite3,struct,subprocess,sys,time,traceback
from ctypes import wintypes as w
from pathlib import Path
from contextlib import closing
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).resolve().parent))
import private_weapon_peer_appearance_20260927 as shared
from tools.strike_lab import run_private_owned_companions as fixture
from private_inventory_memory import kernel,read
from private_inventory_move_ui import desktop_names,require,wait_until
from private_potion_ui import click,type_ascii,user
import private_owned_companions_ui as owned

def preserved_rows(database):
    """Hashes of every cloned table after excluding fixture character4 rows."""
    result={}
    with closing(shared.ro(database)) as db:
        for (table,) in db.execute("SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            quoted='"'+table.replace('"','""')+'"'
            columns=[r[1] for r in db.execute(f'PRAGMA table_info({quoted})')]
            condition=' WHERE character_id!=4' if 'character_id' in columns else ' WHERE id!=4' if table=='recovered_characters' else ''
            rows=db.execute('SELECT * FROM '+quoted+condition+' ORDER BY '+','.join(str(i+1) for i in range(len(columns)))).fetchall()
            encoded=json.dumps([[x.hex() if isinstance(x,bytes) else x for x in row] for row in rows],ensure_ascii=True,separators=(',',':')).encode()
            result[table]={'count':len(rows),'sha256':hashlib.sha256(encoded).hexdigest()}
    return result

def worker(args):
    client=None;result={'accepted':False,'events':[]};before=desktop_names()
    def checkpoint():shared.dump(args.output/'ui-result.json',result)
    def u32(h,a):return int.from_bytes(shared.exact(h,a,4),'little')
    def state():
        h=client['handle'];login=u32(h,0x5e00f8+0x43c);s={'login':hex(login)}
        windows=[]
        @c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
        def visit(hwnd,unused):
            pid=w.DWORD();user.GetWindowThreadProcessId(hwnd,c.byref(pid))
            if pid.value!=client['process'].pid:return True
            name=c.create_unicode_buffer(128);user.GetClassNameW(hwnd,name,128)
            row={'handle':int(hwnd),'class':name.value};windows.append(row)
            if name.value=='#32770':
                row['buttons']=[]
                @c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
                def child(button,unused):
                    child_class=c.create_unicode_buffer(128);user.GetClassNameW(button,child_class,128)
                    if child_class.value=='Button':
                        title=c.create_unicode_buffer(128)
                        user.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,c.c_int];user.GetWindowTextW(button,title,128)
                        row['buttons'].append({'handle':int(button),'title':title.value})
                    return True
                user.EnumChildWindows.argtypes=[w.HWND,type(child),w.LPARAM]
                user.EnumChildWindows(hwnd,child,0)
            return True
        user.EnumWindows(visit,0);s['owned_windows']=windows
        if login>0x10000:
            s['state']=u32(h,login+0x178cec)
            pointer=u32(h,login+0x178ce0)
            if pointer>0x10000:
                raw=shared.exact(h,pointer,74)
                s['list_count']=raw[0];s['names']=[raw[2+36*i:18+36*i].split(b'\0')[0].hex() for i in range(min(raw[0],2))]
            s['panels']={hex(off):int.from_bytes(shared.exact(h,login+off,2),'little',signed=True)
                         for off in (0x178cc8,0x178cca,0x178ccc,0x178cce,0x178cd0)}
            s['widgets']=widgets(login+0x2808c)
        if client.get('ui') and login<=0x10000:
            world=client['ui']-0xa7f2f6c
            logout_mode=read(h,client['ui']+0x86870,4)
            if logout_mode:s['native_logout_mode']=int.from_bytes(logout_mode,'little')
            world_state=read(h,world+0x30,4)
            local_id=read(h,world+0x1539683c,4)
            pose=read(h,world+0xa8797ed,1)
            if world_state and local_id and pose:
                s['native_world_state']=int.from_bytes(world_state,'little')
                s['native_local_id']=int.from_bytes(local_id,'little')
                s['native_pose']=pose[0]
                s['world_widgets']=widgets(client['ui']+0xe2170)
            else:s['native_world_released']=True
        return s
    def widgets(manager):
        h=client['handle'];rows=[]
        for i in range(128):
            base=manager+0x818+i*0x2a08;raw=read(h,base,0xa0)
            if not raw:continue
            flags=int.from_bytes(raw[:2],'little')
            if not(flags&0x28):continue
            controls=[]
            for control in range(80):
                r=read(h,base+0xa0+control*100,100)
                if not r:break
                bounds=struct.unpack_from('<4i',r,0x10)
                if 0<=bounds[0]<bounds[2]<=800 and 0<=bounds[1]<bounds[3]<=600:
                    controls.append({'control':control,'bounds':list(bounds),'flags':r[:4].hex()})
            callbacks=[hex(struct.unpack_from('<I',raw,o)[0]) for o in range(4,0xa0,4)
                       if 0x400000<=struct.unpack_from('<I',raw,o)[0]<0x570000]
            rows.append({'widget':i,'flags':flags,'callbacks':callbacks,'controls':controls})
        return rows
    try:
        require(before['current'].startswith('God2Lab-') and before['input']!=before['current'],'HIDDEN_DESKTOP_REQUIRED')
        process=subprocess.Popen([str(fixture.CLIENT),'127.0.0.1','127.0.0.1','6001','1'],cwd=fixture.CLIENT.parent,
            creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        client={'process':process};result['pid']=process.pid;checkpoint()
        hwnd=wait_until(lambda:shared.window_for(process.pid),35,'OWNED_WINDOW_MISSING');client['hwnd']=hwnd
        time.sleep(2);click(hwnd,512,464);time.sleep(3)
        click(hwnd,437,232);type_ascii(hwnd,'codexslow');click(hwnd,437,263);type_ascii(hwnd,'labtest2345')
        click(hwnd,452,304);time.sleep(4);click(hwnd,330,145);click(hwnd,452,413);time.sleep(4)
        click(hwnd,330,150);click(hwnd,452,376);time.sleep(4)
        client['handle']=kernel.OpenProcess(0x1010,False,process.pid);require(client['handle'],'READ_ONLY_OPEN_FAILED')
        image=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
        result['native_code_matches']={}
        for rva,size in ((0x15730,85),(0x15180,143),(0x152e0,210),(0x154fb,19),(0x5a51,32),(0x97e00,102),(0x97e70,96),(0x101610,240),(0x65ef0,59),(0x103820,59),(0xb1900,148),(0xf6200,168),(0xf6140,190),(0xe17c,26)):
            result['native_code_matches'][hex(rva)]=shared.exact(client['handle'],0x400000+rva,size)==image[rva:rva+size]
        require(all(result['native_code_matches'].values()),'NATIVE_LOGOUT_DELETE_CODE_MISMATCH')
        result['selection_before']=state();checkpoint()
        click(hwnd,452,370);time.sleep(8)
        client['ui']=shared.find_ui(client['handle'],4)
        result['world_before']=state();checkpoint()
        h,ui=client['handle'],client['ui']
        hud=int.from_bytes(shared.exact(h,ui+0x232db6,2),'little',signed=True)
        # Native4B1987 opens settings;4F622D control3 sets mode0;
        # 4F619B confirmation returns2 ->482972(-9) ->466BEF;
        # world loop table1 returns2 ->40E17C loginmode1 and02/01.
        click(hwnd,*owned.control_point(h,ui,hud,9))
        panel=int.from_bytes(shared.exact(h,ui+0x232dc2,2),'little',signed=True)
        result['logout_panel_widget']=panel
        result['logout_panel_control3']=owned.control_point(h,ui,panel,3)
        click(hwnd,*owned.control_point(h,ui,panel,3))
        confirm=int.from_bytes(shared.exact(h,ui+0x232e58,2),'little',signed=True)
        result['logout_confirm_widget']=confirm
        result['logout_confirm_control2']=owned.control_point(h,ui,confirm,2)
        result['logout_menu']=state();checkpoint()
        result['logout_started']=time.monotonic()
        click(hwnd,*owned.control_point(h,ui,confirm,2))
        time.sleep(.5);result['after_logout_click']=state();checkpoint()
        def selected(count=None):
            login=u32(h,0x5e00f8+0x43c)
            if login<=0x10000:return None
            native_state=u32(h,login+0x178cec)
            # Native4056B9..4056CC enters creation21 for an empty role list.
            if native_state not in ((19,21) if count==0 else (19,)):return None
            if count is not None:
                pointer=u32(h,login+0x178ce0)
                if pointer<=0x10000 or shared.exact(h,pointer,1)[0]!=count:return None
            return login
        # Original role logout reconnects login and shows its server menu.
        # Follow the native server choice before asking for a fresh role list.
        wait_until(lambda:(args.output/'server.log').read_text('utf-8',errors='replace').count('SERVER_LIST_SENT')>=2,
                   12,'LOGOUT_NATIVE_SERVER_MENU_NOT_RETURNED')
        time.sleep(.2)
        result['logout_server_menu_seconds']=time.monotonic()-result['logout_started']
        result['server_menu_after_logout']=state();checkpoint()
        # State17 reuses widget4's server confirmation at y356..394;
        # this is the second server-choice step in the qualified initial flow.
        click(hwnd,330,150);click(hwnd,452,376)
        login=wait_until(lambda:selected(1),12,'LOGOUT_NATIVE_SELECTION_NOT_RETURNED')
        result['logout_return_seconds']=time.monotonic()-result['logout_started']
        result['selection_after_logout']=state();checkpoint()
        def login_point(widget,control):
            node=login+0x2808c+0x818+widget*0x2a08
            rect=struct.unpack('<4i',shared.exact(h,node+0xa0+100*control+0x10,16))
            require(0<=rect[0]<rect[2]<=800 and 0<=rect[1]<rect[3]<=600,'NATIVE_LOGIN_CONTROL_BOUNDS')
            return ((rect[0]+rect[2])//2,(rect[1]+rect[3])//2)
        selection=int.from_bytes(shared.exact(h,login+0x178cd0,2),'little',signed=True)
        click(hwnd,*login_point(selection,9));time.sleep(1)
        result['delete_panel']=state();checkpoint()
        panel=int.from_bytes(shared.exact(h,login+0x178cca,2),'little',signed=True)
        for control,value in ((1,'slowgirl'),(2,'codexslow'),(3,'labtest2345')):
            click(hwnd,*login_point(panel,control));type_ascii(hwnd,value)
        result['delete_started']=time.monotonic()
        # Widget5's input button7 maps to native deletion action4.
        # Its graphic node4 has a decorative extended rectangle, not hit bounds.
        click(hwnd,*login_point(panel,7))
        wait_until(lambda:selected(0),12,'DELETION_NATIVE_EMPTY_SELECTION_NOT_RETURNED')
        result['delete_return_seconds']=time.monotonic()-result['delete_started']
        result['selection_after_delete']=state();checkpoint()
        # Fully exercised automatic flow; manual commands remain for inspection
        # only when a future run explicitly requests a hold.
        if not args.hold:deadline=0
        else:deadline=time.monotonic()+240
        processed=set()
        while time.monotonic()<deadline:
            command=args.output/'commands.json'
            if command.exists():
                for row in json.loads(command.read_text('utf-8')):
                    if row['id'] in processed:continue
                    processed.add(row['id'])
                    started=time.monotonic()
                    if row['action']=='click':click(hwnd,*row['point'])
                    elif row['action']=='type':type_ascii(hwnd,row['text'])
                    elif row['action']=='button':
                        owner=w.DWORD();user.GetWindowThreadProcessId(row['handle'],c.byref(owner))
                        require(owner.value==process.pid,'FOREIGN_BUTTON_HANDLE')
                        user.PostMessageW(row['handle'],0xf5,0,0)
                    elif row['action']=='key':
                        user.PostMessageW(hwnd,0x100,row['key'],1);user.PostMessageW(hwnd,0x101,row['key'],1)
                    elif row['action']=='await_selection':
                        until=time.monotonic()+row.get('timeout',12)
                        while time.monotonic()<until:
                            login=u32(client['handle'],0x5e00f8+0x43c)
                            if login>0x10000 and u32(client['handle'],login+0x178cec)==19:break
                            time.sleep(.02)
                        else:raise RuntimeError('NATIVE_SELECTION_RETURN_DEADLINE')
                    elif row['action']=='finish':deadline=0
                    time.sleep(row.get('wait',1));result['events'].append({'id':row['id'],'state':state(),'time':time.monotonic(),'elapsed':time.monotonic()-started});checkpoint()
            time.sleep(.2)
        result['inspection_complete']=True
        final=state();result['final']=final
        log=(args.output/'server.log').read_text('utf-8',errors='replace')
        result['logout_ack_observed']='NATIVE_LOGOUT_ACK_QUEUED' in log
        result['delete_commit_observed']='CHARACTER_DELETE_RESULT accepted=true' in log
        result['fresh_empty_selection_observed']=final.get('state') in (19,21) and final.get('list_count')==0 and log.count('LEGACY_CHARACTER_LIST_CANDIDATE_SENT')>=3
        result['accepted']=all(result[k] for k in ('logout_ack_observed','delete_commit_observed','fresh_empty_selection_observed'))
    except Exception as error:
        result['error']=str(error);result['traceback']=traceback.format_exc()
        if client:
            result['native_exit_code_before_cleanup']=client['process'].poll()
            if result['native_exit_code_before_cleanup'] is None:
                try:result['error_state']=state()
                except Exception as observer_error:result['error_observer_error']=str(observer_error)
    finally:
        if client:shared.close_client(client)
        result['desktop_unchanged']=desktop_names()==before;result['clients_closed']=client is None or client['process'].poll() is not None;checkpoint()
    return 0 if result['accepted'] else 1

def owner(args):
    args.output=args.output.resolve();args.server_candidate=args.server_candidate.resolve()
    before={str(p):fixture.sha(p) for p in (fixture.SOURCE_DB,fixture.LIVE_CLIENT,fixture.CLIENT)}
    with __import__('socket').socket() as probe:require(probe.connect_ex(('127.0.0.1',2598))!=0,'PRIVATE_PORT_BUSY')
    shared.prepare(args)
    preserved=preserved_rows(args.output/'town-diagnostic-accounts.db')
    env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1';env.pop('GOD2_PRIVATE_SIDECAR_COMMAND',None)
    server=runner=None;result={'source_before':before,'server_path':str(args.server_candidate),'server_sha256':fixture.sha(args.server_candidate)}
    try:
        with (args.output/'stdout.log').open('wb') as log,(args.output/'runner.log').open('wb') as runner_log:
            server=subprocess.Popen([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--run-for','340'],
                cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(3)
            command=[str(fixture.RUNNER),sys.executable,'-X','utf8','-B',str(Path(__file__).resolve()),'--worker','--output',str(args.output)]
            if args.hold:command.append('--hold')
            runner=subprocess.Popen(command,cwd=ROOT,env=env,stdout=runner_log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            result['server_pid']=server.pid;result['runner_pid']=runner.pid;shared.dump(args.output/'run-pids.json',result)
            result['runner_exit']=runner.wait(timeout=310)
            result['ui']=json.loads((args.output/'ui-result.json').read_text('utf-8'))
    except Exception as error:result['error']=str(error)
    finally:
        for p in (runner,server):
            if p and p.poll() is None:p.terminate();p.wait(timeout=5)
        result['source_after']={str(p):fixture.sha(p) for p in (fixture.SOURCE_DB,fixture.LIVE_CLIENT,fixture.CLIENT)}
        result['actual_server_sha256']=fixture.sha(args.server_candidate)
        result['preserved_rows_before']=preserved
        result['preserved_rows_after']=preserved_rows(args.output/'town-diagnostic-accounts.db')
        result['all_nonfixture_rows_preserved']=result['preserved_rows_before']==result['preserved_rows_after']
        result['source_unchanged']=result['source_after']==before;shared.dump(args.output/'run-result.json',result)
    return 0 if result.get('runner_exit')==0 and result['source_unchanged'] and result['all_nonfixture_rows_preserved'] else 1

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--server-candidate',type=Path);p.add_argument('--worker',action='store_true');p.add_argument('--hold',action='store_true');a=p.parse_args()
    raise SystemExit(worker(a) if a.worker else owner(a))
