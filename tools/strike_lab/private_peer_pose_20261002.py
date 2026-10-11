"""Native66/77 peer acceptance on the owner's requested hidden desktop.

Uses disposable port-only copies of the current client and cloned saves. Only
the original window's402 pose event is posted; packet production/transport and
consumer/renderer execution belong to the real clients. Observer handles are
VM_READ only. No input-desktop switch, screenshots or live client-file edits.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]
import psutil
import pefile
import private_peer_role_text_20260930 as base
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,type_ascii

CLIENT_SHA='c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575'
REGIONS=((0x4fb980,320),(0x4fc960,64),(0x501610,240),(0x503820,66),
         (0x497e00,128),(0x469bba,83),(0x4fd160,388),(0x465ef0,59),
         (0x502570,340),(0x4fb290,430),(0x4ffcb0,68))
base.CLIENT_SHA=CLIENT_SHA

def qualify_source():
    require(base.sha(base.LIVE)==CLIENT_SHA,'CURRENT_CLIENT_IDENTITY_CHANGED')
    current=pefile.PE(str(base.LIVE)).get_memory_mapped_image()
    captured=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    require(hashlib.sha256(captured).hexdigest()==base.MAPPED_SHA,'CAPTURE_IDENTITY_CHANGED')
    for va,size in REGIONS:
        rva=va-0x400000
        require(current[rva:rva+size]==captured[rva:rva+size],'CURRENT_POSE_CODE_CHANGED_'+hex(va))
    return captured

def worker(args):
    import subprocess
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'))
    database=args.output/'town-diagnostic-accounts.db'
    before=desktop_names();clients=[];loaders=[]
    result={'accepted':False,'rendered_pixels_tested':False,'events':[],
            'native_client_sha256':CLIENT_SHA,'source_page':args.source_page}
    def save():base.peer.dump(args.output/'ui-result.json',result)
    def u32(client,address):return int.from_bytes(base.peer.exact(client['handle'],address,4),'little')
    def own(client):
        world=base.ground.world_state(client['handle'],client['ui'])['world']
        return {'world':hex(world),'identity':u32(client,world+0x1539683c),
                'state':u32(client,world+0x30),'packed':base.peer.exact(client['handle'],world+0xa8797ed,1)[0],
                'mounted':int.from_bytes(base.peer.exact(client['handle'],world+0xa7e04fc,2),'little',signed=True)}
    def remote(client,identity):
        row=base.peer.remote(client['handle'],client['ui'],identity)
        if not row:return None
        actor=int(row['entry'],16)
        row['direction']=int.from_bytes(base.peer.exact(client['handle'],actor+0x3a,2),'little')
        row['mode']=base.peer.exact(client['handle'],actor+0x79,1)[0]
        row['mount']=int.from_bytes(base.peer.exact(client['handle'],actor+0x3e,2),'little',signed=True)
        pool=u32(client,actor+0x24c)
        require(pool>0x10000,'REMOTE_ACT_POOL_MISSING')
        row['render_actions']=[]
        for index in range(4):
            resource,display=struct.unpack('<HH',base.peer.exact(client['handle'],actor+0x228+index*6,4))
            if resource>=512 or display>=4096:continue
            entry=pool+0x10+display*0x290
            raw=base.peer.exact(client['handle'],entry,0x40)
            group,track=struct.unpack_from('<II',raw,0x34)
            require(group>0x10000 and track>0x10000,'REMOTE_ACT_TRACK_MISSING')
            action=raw[1];count=u32(client,group+0x108c)
            require(action<count and count<=512,'REMOTE_ACT_ACTION_OUTSIDE_GROUP')
            require(u32(client,group+0x1090+action*4)==track,'REMOTE_ACT_TRACK_BINDING_MISMATCH')
            row['render_actions'].append({'component':index,'resource':resource,'display':display,
                'action':action,'group':hex(group),'track':hex(track),'active':raw[0],
                'loaded_resource':int.from_bytes(raw[0x16:0x18],'little')})
        return row
    def close(client):
        if client.get('handle'):base.peer.kernel.CloseHandle(client.pop('handle'))
        process=client['process']
        if process.is_running():
            if client.get('hwnd'):base.peer.user.PostMessageW(client['hwnd'],0x10,0,0)
            try:process.wait(timeout=4)
            except psutil.TimeoutExpired:process.terminate();process.wait(timeout=5)
    try:
        captured=qualify_source()
        require(before['current'].startswith('God2Lab-') and before['current']!=before['input'],'HIDDEN_DESKTOP_REQUIRED')
        result['desktop_before']=before
        def launch(identity,page):
            image=Path(fixture['clients'][str(page)]['path'])
            require(base.sha(image)==fixture['clients'][str(page)]['sha256'],'PRIVATE_CLIENT_CHANGED')
            launcher=subprocess.Popen([str(base.LE),'-run',str(image),'127.0.0.1','127.0.0.1','6001','1'],
                cwd=base.LIVE.parent,creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);loaders.append(launcher)
            def find():
                found=[p for p in psutil.process_iter(['exe']) if p.info['exe'] and Path(p.info['exe']).resolve()==image.resolve()]
                require(len(found)<=1,'DUPLICATE_PRIVATE_PROCESS');return found[0] if found else None
            process=wait_until(find,35,'PRIVATE_CLIENT_NOT_CREATED')
            client={'process':process,'identity':identity,'page':page};clients.append(client)
            result['owned_client_pids']=[c['process'].pid for c in clients];save()
            hwnd=wait_until(lambda:base.peer.window_for(process.pid),35,'PRIVATE_WINDOW_NOT_CREATED');client['hwnd']=hwnd
            time.sleep(12);click(hwnd,512,464);time.sleep(4)
            click(hwnd,437,232);type_ascii(hwnd,'codexslow' if identity==4 else 'codexfixed')
            marker='RECOVERED_ACCOUNT_BOUND account_id='+str(identity)
            count=(args.output/'server.log').read_text('utf-8',errors='replace').count(marker)
            click(hwnd,437,263);type_ascii(hwnd,'labtest2345');click(hwnd,452,304)
            wait_until(lambda:(args.output/'server.log').read_text('utf-8',errors='replace').count(marker)>count,35,'PRIVATE_LOGIN_FAILED')
            time.sleep(4);click(hwnd,330,145);click(hwnd,452,413);time.sleep(4)
            click(hwnd,330,150);click(hwnd,452,376);time.sleep(4);click(hwnd,452,370);time.sleep(12)
            client['handle']=base.peer.kernel.OpenProcess(0x1010,False,process.pid)
            require(client['handle'],'READONLY_HANDLE_FAILED')
            client['ui']=base.peer.find_ui(client['handle'],identity,(0,3,4))
            for va,size in REGIONS:
                require(base.peer.exact(client['handle'],va,size)==captured[va-0x400000:va-0x400000+size],
                        'RUNNING_NATIVE_POSE_CODE_CHANGED_'+hex(va))
            require(own(client)['identity']==identity,'CLIENT_IDENTITY_MISMATCH')
            return client
        actor=launch(4,args.source_page)
        observer=launch(5,936 if args.source_page==950 else 950)
        wait_until(lambda:remote(actor,5) and remote(observer,4),15,'NATIVE_PEERS_MISSING')
        result['initial']={'actor':own(actor),'observer':own(observer),'remote':remote(observer,4)}
        invariant=base.peer.db_stable(database);save()
        def request(sender,receiver,mode):
            # Native497E00 silently drops pose requests inside500ms. Do not
            # mistake a deliberately throttled UI event for a server failure.
            time.sleep(.65)
            expected_direction=own(sender)['packed']&7
            require(base.peer.user.PostMessageW(sender['hwnd'],0x402,mode,0),'NATIVE_POSE_EVENT_FAILED')
            def accepted():
                local=own(sender);other=remote(receiver,sender['identity'])
                result['pending_pose']={'sender':sender['identity'],'mode':mode,'self':local,'peer':other}
                save()
                if local['state']==15+mode and local['packed']>>3==mode and other and other['mode']==mode:
                    require(other['direction']==expected_direction,'REMOTE_DIRECTION_MISMATCH')
                    require(other['movement']==15+mode,'REMOTE_ANIMATION_MISMATCH')
                    require(0<=other['renderer']<4096,'REMOTE_RENDERER_MISSING')
                    require(other['render_actions'],'REMOTE_POSE_ACTS_MISSING')
                    return {'sender':sender['identity'],'mode':mode,'self':local,'peer':other}
                return None
            row=wait_until(accepted,12,'NATIVE_PEER_POSE_NOT_ACCEPTED')
            result['events'].append(row);save();return row
        for sender,receiver in ((actor,observer),(observer,actor)):
            for mode in (1,2,3):request(sender,receiver,mode)
        def completed():
            locals=[own(actor),own(observer)]
            peers=[remote(actor,5),remote(observer,4)]
            if all(r['state']==0 and r['packed']>>3==0 for r in locals) and all(
                    r and r['mode']==0 and r['movement']==0 for r in peers):
                return {'self':locals,'peers':peers}
            return None
        result['one_shot_completed']=wait_until(completed,20,'NATIVE_ONE_SHOT_DID_NOT_RETURN_IDLE');save()
        close(observer);wait_until(lambda:remote(actor,5) is None,12,'OBSERVER_REMOVAL_MISSING')
        observer=launch(5,936 if args.source_page==950 else 950)
        def late():
            row=remote(observer,4)
            result['late_pending']={'self':own(actor),'peer':row};save()
            return row if row and row['mode']==0 and row['movement']==0 else None
        result['expired_one_shot_observer']=wait_until(late,15,'STALE_ONE_SHOT_REPLAYED');save()
        request(actor,observer,2)
        close(observer);wait_until(lambda:remote(actor,5) is None,12,'OBSERVER_REMOVAL_MISSING')
        observer=launch(5,936 if args.source_page==950 else 950)
        def persistent():
            row=remote(observer,4);local=own(actor)
            if row and row['mode']==2 and row['movement']==17 and local['state']==17:
                return {'self':local,'peer':row}
            return None
        result['late_observer']=wait_until(persistent,15,'PERSISTENT_POSE_NOT_REPLAYED');save()
        state=base.ground.world_state(actor['handle'],actor['ui']);target=(state['x']+1,state['y'])
        click(actor['hwnd'],*base.ground.ground_point(actor['handle'],state,*target))
        def moved():
            local=base.ground.world_state(actor['handle'],actor['ui']);row=remote(observer,4)
            saved=base.position(database,4)
            if row and [row['x'],row['y']]==list(target) and [local['x'],local['y']]==list(target) and saved[:4]==[4,3,*target]:
                return {'self':local,'peer':row,'saved':saved}
            return None
        result['movement']=wait_until(moved,15,'NATIVE_MOVEMENT_AFTER_POSE_FAILED')
        request(actor,observer,1)
        require(base.peer.db_stable(database)==invariant,'UNRELATED_SAVES_CHANGED')
        require(all(c['process'].is_running() for c in (actor,observer)),'CURRENT_CLIENT_EXITED')
        result['saved_preserved']=True;result['accepted']=True
    except BaseException as error:
        result['error']=str(error);result['traceback']=traceback.format_exc()
    finally:
        for client in reversed(clients):
            try:close(client)
            except Exception as error:result.setdefault('cleanup_errors',[]).append(str(error))
        for loader in loaders:
            if loader.poll() is None:loader.terminate();loader.wait(timeout=5)
        result['desktop_after']=desktop_names();result['desktop_unchanged']=before==result['desktop_after']
        result['all_clients_closed']=not any(psutil.pid_exists(c['process'].pid) for c in clients)
        result['accepted']=bool(result['accepted'] and result['desktop_unchanged'] and result['all_clients_closed'] and not result.get('cleanup_errors'))
        save()
    return 0 if result['accepted'] else 1

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--server-candidate',type=Path)
    parser.add_argument('--source-page',type=int,choices=(950,936),default=950)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.worker:return worker(args)
    if args.server_candidate is None:parser.error('--server-candidate required')
    qualify_source()
    # Reuse the established owner wrapper, but dispatch this worker rather
    # than the dated role-text worker. Its source/config/desktop/process guards
    # and candidate identity checks are preserved.
    base.__file__=str(Path(__file__).resolve())
    harness_before=base.sha(Path(__file__))
    code=base.owner(args)
    receipt_path=args.output/'run-result.json'
    receipt=json.loads(receipt_path.read_text('utf-8'))
    receipt['pose_harness_sha256']=harness_before
    receipt['pose_harness_unchanged']=harness_before==base.sha(Path(__file__))
    receipt['accepted']=bool(receipt['accepted'] and receipt['pose_harness_unchanged'])
    base.peer.dump(receipt_path,receipt)
    return 0 if receipt['accepted'] else 1

if __name__=='__main__':raise SystemExit(main())
