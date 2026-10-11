"""Actual client options controls on hidden desktop; no memory writes/screenshots."""
import argparse,json,struct,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]
import psutil,pefile
import private_peer_role_text_20260930 as base
import private_peer_pose_20261002 as pose
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,type_ascii
from private_panel_88_74_20260930 import ctrl_f
base.CLIENT_SHA=pose.CLIENT_SHA

def qualify():
    raw=pose.qualify_source();current=pefile.PE(str(base.LIVE)).get_memory_mapped_image()
    for va,size in ((0x497d80,23),(0x4f4b50,1030),(0x4a6760,900)):
        require(current[va-0x400000:va-0x400000+size]==raw[va-0x400000:va-0x400000+size],
                'NATIVE_OPTIONS_CODE_CHANGED_'+hex(va))
    return raw

def worker(args):
    import subprocess
    before=desktop_names();process=loader=None;handle=None
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'));log=args.output/'server.log'
    result={'accepted':False,'events':[],'rendered_pixels_tested':False}
    def save():base.peer.dump(args.output/'ui-result.json',result)
    try:
        qualify();require(before['current'].startswith('God2Lab-') and before['current']!=before['input'],'HIDDEN_DESKTOP_REQUIRED')
        page=args.source_page;image=Path(fixture['clients'][str(page)]['path'])
        loader=subprocess.Popen([str(base.LE),'-run',str(image),'127.0.0.1','127.0.0.1','6001','1'],cwd=base.LIVE.parent,
            creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        def found():
            rows=[p for p in psutil.process_iter(['exe']) if p.info['exe'] and Path(p.info['exe']).resolve()==image.resolve()]
            require(len(rows)<=1,'DUPLICATE_CLIENT');return rows[0] if rows else None
        process=wait_until(found,35,'CLIENT_MISSING');result['owned_client_pids']=[process.pid];save()
        hwnd=wait_until(lambda:base.peer.window_for(process.pid),35,'WINDOW_MISSING')
        time.sleep(12);click(hwnd,512,464);time.sleep(4)
        click(hwnd,437,232);type_ascii(hwnd,'codexslow');click(hwnd,437,263);type_ascii(hwnd,'labtest2345');click(hwnd,452,304)
        wait_until(lambda:'RECOVERED_ACCOUNT_BOUND account_id=4' in log.read_text('utf-8',errors='replace'),35,'LOGIN_FAILED')
        time.sleep(4);click(hwnd,330,145);click(hwnd,452,413);time.sleep(4)
        click(hwnd,330,150);click(hwnd,452,376);time.sleep(4);click(hwnd,452,370);time.sleep(12)
        handle=base.peer.kernel.OpenProcess(0x1010,False,process.pid);require(handle,'READ_HANDLE_MISSING')
        ui=base.peer.find_ui(handle,4,(0,3,4));world=int.from_bytes(base.peer.exact(handle,ui+0x86888,4),'little')
        def flags():return int.from_bytes(base.peer.exact(handle,world+0x449c,2),'little')
        def widget(offset):
            value=int.from_bytes(base.peer.exact(handle,ui+offset,2),'little',signed=True)
            require(0<=value<128,'WIDGET_MISSING');return value
        def visible(offset):
            value=widget(offset);return value if base.peer.exact(handle,ui+0xe2988+value*0x2a08,1)[0]&0x20 else None
        def control(w,index):
            entry=ui+0xe2170+w*0x2a08+0x8b8+index*100
            hit=int.from_bytes(base.peer.exact(handle,entry+8,2),'little',signed=True)
            manager=int.from_bytes(base.peer.exact(handle,ui+0xe2174,4),'little')
            require(manager>0x10000 and 0<=hit<0xc00,'CONTROL_HIT_MISSING')
            active,left,top,right,bottom=struct.unpack('<5i',base.peer.exact(handle,manager+hit*24,20))
            require(active and 0<=left<right<=800 and 0<=top<bottom<=600,'CONTROL_RECT_INVALID')
            result['last_control']={'widget':w,'index':index,'rect':[left,top,right,bottom]};save()
            click(hwnd,(left+right)//2,(top+bottom)//2);time.sleep(.3)
        original=flags();result['original_flags']=original;save()
        # Ctrl+H is the native main menu shortcut (4AACD0 ->4A65B0).
        for message,vk,data in ((0x100,0x11,1),(0x100,0x48,1),(0x101,0x48,0xc0000001),(0x101,0x11,0xc0000001)):
            require(base.peer.user.PostMessageW(hwnd,message,vk,data),'MENU_KEY_FAILED');time.sleep(.1)
        menu=wait_until(lambda:visible(0x232e4e),8,'MAIN_MENU_NOT_OPEN')
        # Native4A6D90:22..26 select the category;27 is its first action.
        control(menu,26);control(menu,27)
        options=wait_until(lambda:visible(0x232dbc),8,'OPTIONS_NOT_OPEN')
        saved=base.peer.db_stable(args.output/'town-diagnostic-accounts.db')
        for index,mask in ((4,1),(5,4),(6,2),(7,8),(8,0x100)):
            for _ in range(2):
                old=flags();count=log.read_text('utf-8',errors='replace').count('NATIVE_OPTIONS_TRANSPORT_ADMITTED')
                control(options,index)
                def received():
                    text=log.read_text('utf-8',errors='replace');actual=flags()
                    if text.count('NATIVE_OPTIONS_TRANSPORT_ADMITTED')>count and actual==old^mask:
                        require(f'flags={actual:04x} no_state_change no_reply' in text,'WIRE_FLAGS_DIFFER')
                        return {'control':index,'mask':mask,'before':old,'after':actual}
                    return None
                result['events'].append(wait_until(received,8,'NATIVE_1D_NOT_ACCEPTED'));save()
        require(flags()==original,'OPTIONS_NOT_RESTORED')
        require(base.peer.db_stable(args.output/'town-diagnostic-accounts.db')==saved,'SAVES_CHANGED')
        require(process.is_running(),'CLIENT_EXITED');result['accepted']=True
    except BaseException as error:result.update(error=str(error),traceback=traceback.format_exc())
    finally:
        if handle:base.peer.kernel.CloseHandle(handle)
        if process and process.is_running():process.terminate();process.wait(timeout=5)
        if loader and loader.poll() is None:loader.terminate();loader.wait(timeout=5)
        result['desktop_unchanged']=before==desktop_names();result['all_clients_closed']=not process or not psutil.pid_exists(process.pid)
        result['accepted']=bool(result['accepted'] and result['desktop_unchanged'] and result['all_clients_closed']);save()
    return 0 if result['accepted'] else 1

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--server-candidate',type=Path);parser.add_argument('--source-page',type=int,choices=(950,936),default=950)
    parser.add_argument('--worker',action='store_true');args=parser.parse_args()
    if args.worker:return worker(args)
    qualify();base.__file__=str(Path(__file__).resolve());before=base.sha(Path(__file__))
    base.owner(args)
    receipt=args.output/'run-result.json';value=json.loads(receipt.read_text('utf-8'))
    value['harness_sha256']=before;value['harness_unchanged']=before==base.sha(Path(__file__))
    value['accepted']=bool(value['accepted'] and value['harness_unchanged'])
    base.peer.dump(receipt,value);return 0 if value['accepted'] else 1
if __name__=='__main__':raise SystemExit(main())
