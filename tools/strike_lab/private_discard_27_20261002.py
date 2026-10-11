"""Current native discard controls, disposable clone on a hidden desktop only."""
import argparse,json,sqlite3,struct,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]
import psutil,pefile
import private_peer_role_text_20260930 as base
import private_peer_pose_20261002 as pose
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,type_ascii,drag
base.CLIENT_SHA=pose.CLIENT_SHA
original_prepare=base.prepare
def prepare(args):
    original_prepare(args)
    config_path=args.output/'server-config.json'
    config=json.loads(config_path.read_text('utf-8'))
    config.setdefault('world',{})['owned_supply']={'enabled':True}
    base.peer.dump(config_path,config)
    with sqlite3.connect(args.output/'town-diagnostic-accounts.db') as db:
        from tools.strike_lab.discard_fixture_27_20261002 import copy_catalog
        base.peer.dump(args.output/'catalog-source.json',copy_catalog(db))
        for slot,count in ((5,7),(6,1)):
            db.execute("INSERT OR REPLACE INTO diagnostic_inventory_slots VALUES(4,?,3107,?,1,?,'CUSTOM-0015')",
                (slot,count,'70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'))
        db.commit()
base.prepare=prepare
def qualify():
    raw=pose.qualify_source();current=pefile.PE(str(base.LIVE)).get_memory_mapped_image()
    for va,size in ((0x496720,35),(0x4991e0,201),(0x49a330,1200),(0x4c9ed0,512)):
        require(current[va-0x400000:va-0x400000+size]==raw[va-0x400000:va-0x400000+size],
            'NATIVE_DISCARD_CODE_CHANGED_'+hex(va))
    return raw
def worker(args):
    import subprocess
    before=desktop_names();process=loader=None;handle=None
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'));log=args.output/'server.log'
    result={'accepted':False,'events':[],'rendered_pixels_tested':False}
    def save():base.peer.dump(args.output/'ui-result.json',result)
    try:
        qualify();require(before['current'].startswith('God2Lab-') and before['current']!=before['input'],'HIDDEN_DESKTOP_REQUIRED')
        image=Path(fixture['clients'][str(args.source_page)]['path'])
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
        ui=base.peer.find_ui(handle,4,(0,3,4))
        language,sub=struct.unpack('<HH',base.peer.exact(handle,0x59dfd8,4))
        require(language==4 and ((sub==2)==(args.source_page==936)),'NATIVE_LANGUAGE_WRONG')
        def untouched_db():
            with sqlite3.connect(f'file:{(args.output/"town-diagnostic-accounts.db").as_posix()}?mode=ro',uri=True) as db:
                value={}
                for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
                    where=' WHERE NOT(character_id=4 AND slot IN(5,6))' if name=='diagnostic_inventory_slots' else ''
                    value[name]=sorted(repr(r) for r in db.execute('SELECT * FROM "'+name.replace('"','""')+'"'+where))
                return value
        def untouched_native():
            raw=bytearray(base.peer.exact(handle,ui+0x8560c,50*24))
            for slot in (5,6):raw[slot*24:(slot+1)*24]=bytes(24)
            return raw.hex()
        baseline_db=untouched_db();baseline_native=untouched_native()
        def visible(offset):
            w=int.from_bytes(base.peer.exact(handle,ui+offset,2),'little',signed=True)
            return w if 0<=w<128 and base.peer.exact(handle,ui+0xe2988+w*0x2a08,1)[0]&0x20 else None
        def point(w,index):
            entry=ui+0xe2170+w*0x2a08+0x8b8+index*100
            hit=int.from_bytes(base.peer.exact(handle,entry+8,2),'little',signed=True)
            manager=int.from_bytes(base.peer.exact(handle,ui+0xe2174,4),'little')
            require(manager>0x10000 and 0<=hit<0xc00,'CONTROL_HIT_MISSING')
            active,left,top,right,bottom=struct.unpack('<5i',base.peer.exact(handle,manager+hit*24,20))
            require(active and 0<=left<right<=800 and 0<=top<bottom<=600,'CONTROL_RECT_INVALID')
            result['last_control']={'widget':w,'index':index,'rect':[left,top,right,bottom]};save()
            return ((left+right)//2,(top+bottom)//2)
        def state(slot):
            with sqlite3.connect(f'file:{(args.output/"town-diagnostic-accounts.db").as_posix()}?mode=ro',uri=True) as db:
                row=list(db.execute('SELECT item_id,count,revision FROM diagnostic_inventory_slots WHERE character_id=4 AND slot=?',(slot,)).fetchone())
            native=base.peer.exact(handle,ui+0x8560c+slot*24,24)
            return {'db':row,'native':native.hex(),'count':native[0],'item':int.from_bytes(native[4:6],'little')}
        click(hwnd,708,584);time.sleep(2)
        bag=wait_until(lambda:visible(0x232dc8),8,'BAG_NOT_OPEN')
        for slot,quantity,remaining in ((5,2,5),(5,5,0),(6,1,0)):
            previous=state(slot);result['initial_slot']=previous;save()
            require(previous['db'][1]==previous['count'] and previous['item']==3107,'INITIAL_SLOT_MISMATCH')
            result['pending']={'slot':slot,'before':previous};save()
            drag(hwnd,point(bag,slot),point(bag,56));time.sleep(.5)
            if previous['count']>1:
                dialog=wait_until(lambda:visible(0x232dd0),8,'QUANTITY_DIALOG_MISSING')
                click(hwnd,*point(dialog,4));time.sleep(.2)
                # Native numeric edit initially contains the full stack. Backspace
                # through its bounded decimal field before entering our choice.
                type_ascii(hwnd,'\b'*9+str(quantity));time.sleep(.5)
                result['quantity_before_confirm']=int.from_bytes(base.peer.exact(handle,ui+0x23d5e8,4),'little');save()
                click(hwnd,*point(dialog,2));time.sleep(.5)
            confirmation=visible(0x232df4)
            if confirmation is not None:click(hwnd,*point(confirmation,4))
            def changed():
                current=state(slot)
                if current['db'][1]==remaining and current['count']==remaining and current['item']==(3107 if remaining else 0):return current
                return None
            after=wait_until(changed,12,'DISCARD_NOT_PROJECTED')
            require(after['db'][2]==previous['db'][2]+1,'REVISION_MISMATCH')
            require(bytes.fromhex(previous['native'])[6:]==bytes.fromhex(after['native'])[6:],'METADATA_CHANGED')
            result['events'].append({'slot':slot,'quantity':quantity,'before':previous,'after':after});save()
            require(untouched_db()==baseline_db,'UNRELATED_SAVED_ROWS_CHANGED')
            require(untouched_native()==baseline_native,'UNRELATED_NATIVE_SLOTS_CHANGED')
        result['other_saved_rows_preserved']=True;result['other_native_slots_preserved']=True
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
