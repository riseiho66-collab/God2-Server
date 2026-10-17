"""Original TW CP950/CP936 trade UI on a new, owned hidden desktop and port2598.

No foreground activation, screenshots, process-memory writes or packet injection.
Only disposable copies have their port changed. Saves are an isolated backup.
"""
import argparse,json,sqlite3,struct,sys,time,traceback,subprocess
from contextlib import closing
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]
import psutil,pefile
import private_peer_role_text_20260930 as base
import private_peer_pose_20261002 as pose
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,type_ascii,drag
base.CLIENT_SHA=pose.CLIENT_SHA


def qualify():
    raw=pose.qualify_source();mapped=pefile.PE(str(base.LIVE)).get_memory_mapped_image()
    regions=((0x497250,158),(0x497a30,82),(0x49d980,1744),(0x49e380,500),
             (0x483c80,3488),(0x4a7380,35),(0x4a6760,500),(0x4835a0,250),
             (0x481f70,160),(0x465fa0,420),(0x4c9970,143),(0x4ca470,160),
             (0x4c9ed0,512),(0x498d70,89),(0x5077c0,138),
             (0x41e500,70),(0x426700,200),(0x426140,600))
    for va,size in regions:
        require(mapped[va-0x400000:va-0x400000+size]==raw[va-0x400000:va-0x400000+size],
                'NATIVE_TRADE_CODE_CHANGED_'+hex(va))
    return {'current_client_sha256':base.sha(base.LIVE),'regions':regions,
            'cursor':'menu33 ->4A7380 mode4 ->4835A0 event3 ->481F70 -6 ->465FA0 ->49DE30/29',
            'item':'bag232DC8 sourceSlot ->trade232DAE slot0 ->49E440; stack dialog232DD0 mode5/control4edit/control2accept',
            'money':'trade control12 numeric edit, control11 confirm ->modal232DE6 mode2/control0 ->2B+2C',
            'cancel':'trade control10 ->49DD40(1)/2D'}


original_prepare=base.prepare
def prepare(args):
    original_prepare(args)
    database=args.output/'town-diagnostic-accounts.db'
    config=json.loads((args.output/'server-config.json').read_text('utf-8'))
    config['world']['clock']={'enabled':False};config['world']['owned_supply']={'enabled':True}
    base.peer.dump(args.output/'server-config.json',config)
    from tools.strike_lab.discard_fixture_27_20261002 import copy_catalog
    with closing(sqlite3.connect(database)) as db:
        base.peer.dump(args.output/'catalog-source.json',copy_catalog(db))
    # Candidate installs trade schema during normal recovered-server startup,
    # after its migrate-only early return. Let the candidate own that schema.
    with (args.output/'trade-schema-startup.log').open('wb') as log:
        subprocess.run([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--run-for','1'],
                       cwd=ROOT,check=True,timeout=25,stdout=log,stderr=subprocess.STDOUT,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    with closing(sqlite3.connect(database)) as db:
        require(db.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='character_trade_wallets'").fetchone()[0],
                'CANDIDATE_TRADE_WALLET_SCHEMA_REQUIRED')
        for identity,count,balance in ((4,10,1000),(5,8,2000)):
            # Deliberate test fixture in this newly cloned DB, never official data.
            db.execute('delete from diagnostic_inventory_slots where character_id=? and slot<30',(identity,))
            db.execute('delete from character_weapon_slot_metadata where character_id=? and slot<30',(identity,))
            for slot in range(30):
                db.execute("insert into diagnostic_inventory_slots(character_id,slot,item_id,count,revision,source_sha256,design_id) values(?,?,?,?,1,?,'CUSTOM-0015')",
                    (identity,slot,3107 if slot==0 else 0,count if slot==0 else 0,
                     '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'))
            db.execute("insert into character_trade_wallets(character_id,amount,revision,design_id) values(?,?,1,'CUSTOM-0063') "
                       "on conflict(character_id) do update set amount=excluded.amount,revision=1",(identity,balance))
        db.execute('update recovered_positions set x=129,y=126 where character_id=5')
        db.commit();require(db.execute('pragma quick_check').fetchone()==('ok',),'PRIVATE_DB_INVALID')
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'))
    fixture['trade_fixture']={'item':3107,'bag_slot':0,'counts':{'4':10,'5':8},'wallets':{'4':1000,'5':2000},
                             'authority':'CUSTOM_TEST_NOT_NATIVE'}
    base.peer.dump(args.output/'fixture.json',fixture)
base.prepare=prepare


def worker(args):
    before=desktop_names();clients=[];loaders=[]
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'))
    database=args.output/'town-diagnostic-accounts.db';log=args.output/'server.log'
    result={'accepted':False,'events':[],'rendered_pixels_tested':False,'source_page':args.source_page}
    def save():base.peer.dump(args.output/'ui-result.json',result)
    def exact(c,a,n):return base.peer.exact(c['handle'],a,n)
    def number(c,a,n=4,signed=False):return int.from_bytes(exact(c,a,n),'little',signed=signed)
    def widget(c,offset):
        w=number(c,c['ui']+offset,2,True)
        return w if 0<=w<128 and exact(c,c['ui']+0xe2988+w*0x2a08,1)[0]&0x20 else None
    def point(c,w,index):
        entry=c['ui']+0xe2170+w*0x2a08+0x8b8+index*100
        hit=number(c,entry+8,2,True);manager=number(c,c['ui']+0xe2174)
        require(manager>0x10000 and 0<=hit<0xc00,'NATIVE_CONTROL_MISSING')
        active,left,top,right,bottom=struct.unpack('<5i',exact(c,manager+hit*24,20))
        require(active and 0<=left<right<=800 and 0<=top<bottom<=600,'NATIVE_CONTROL_RECT_INVALID')
        result['last_control']={'character':c['identity'],'widget':w,'index':index,'rect':[left,top,right,bottom]};save()
        return ((left+right)//2,(top+bottom)//2)
    def control(c,w,index):click(c['hwnd'],*point(c,w,index));time.sleep(.25)
    def label(c,w,index):
        # 5077C0 ->41E500 ->426700 ->426140 native renderer/text chain.
        pool=number(c,c['ui']+0xe2178)
        renderer=number(c,c['ui']+0xe2170+w*0x2a08+0x81c,2,True)
        require(pool>0x10000 and 0<=renderer<4096,'TRADE_LABEL_RENDERER_MISSING')
        command=number(c,pool+0x10+renderer*0x290+0xe,2)
        surface=number(c,pool+4);require(surface>0x10000 and command<5000,'TRADE_LABEL_COMMAND_MISSING')
        text=number(c,surface+0x1264+command*200+index*2,2,True)
        require(0<=text<30000,'TRADE_LABEL_TEXT_MISSING')
        raw=exact(c,surface+0xf66e4+text*0x8c,0x8c)
        return {'renderer':renderer,'command':command,'index':text,'raw_hex':raw.hex(),
                'text_bytes_hex':raw[12:].hex()}
    def snap(c):
        def items(offset,count):
            raw=exact(c,c['ui']+offset,count*24)
            return [{'slot':i,'quantity':r[0],'source_slot':r[1],'item':int.from_bytes(r[4:6],'little'),'raw':r.hex()}
                    for i in range(count) for r in [raw[i*24:(i+1)*24]]]
        peer_widget=widget(c,0x232db2)
        return {'identity':c['identity'],'language':c['page'],'trade_widget':widget(c,0x232dae),
                'peer_labels':{'name':label(c,peer_widget,0),'money':label(c,peer_widget,1)} if peer_widget is not None else None,
                'peer':number(c,c['ui']+0x866d0,2),'purse':number(c,c['ui']+0x85604),
                'escrow_money':number(c,c['ui']+0x866d4),'money_sent':number(c,c['ui']+0x866dc),
                'confirmed':number(c,c['ui']+0x866e0),'active':number(c,c['ui']+0x866e4),
                'self_items':items(0x866e8,8),'peer_items':items(0x867a8,8),'bag':items(0x8560c,30)}
    def saved():
        with closing(base.peer.ro(database)) as db:
            return {'wallets':[list(r) for r in db.execute('select character_id,amount,revision from character_trade_wallets order by character_id')],
                    'bag':[list(r) for r in db.execute('select character_id,slot,item_id,count,revision from diagnostic_inventory_slots where character_id in(4,5) and slot<30 order by character_id,slot')],
                    'receipts':[list(r) for r in db.execute('select * from character_trade_receipts order by receipt')]}
    def untouched():
        with closing(base.peer.ro(database)) as db:
            return {name:sorted(repr(row) for row in db.execute('select * from "'+name.replace('"','""')+'"'))
                    for name, in db.execute("select name from sqlite_master where type='table' order by name")
                    if name not in ('diagnostic_inventory_slots','character_trade_wallets','character_trade_receipts')}
    def close(c):
        if c.get('handle'):base.peer.kernel.CloseHandle(c.pop('handle'))
        if c['process'].is_running():
            base.peer.user.PostMessageW(c['hwnd'],0x10,0,0)
            try:c['process'].wait(timeout=4)
            except psutil.TimeoutExpired:c['process'].terminate();c['process'].wait(timeout=5)
    try:
        result['qualified']=qualify()
        require(before['current'].startswith('God2Lab-') and before['current']!=before['input'],'HIDDEN_DESKTOP_REQUIRED')
        def launch(identity,page):
            image=Path(fixture['clients'][str(page)]['path']);require(base.sha(image)==fixture['clients'][str(page)]['sha256'],'PRIVATE_IMAGE_CHANGED')
            loader=subprocess.Popen([str(base.LE),'-run',str(image),'127.0.0.1','127.0.0.1','6001','1'],cwd=base.LIVE.parent,
                creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);loaders.append(loader)
            def found():
                rows=[p for p in psutil.process_iter(['exe']) if p.info['exe'] and Path(p.info['exe']).resolve()==image.resolve()]
                require(len(rows)<=1,'DUPLICATE_PRIVATE_CLIENT');return rows[0] if rows else None
            process=wait_until(found,35,'CLIENT_MISSING');c={'process':process,'identity':identity,'page':page};clients.append(c)
            result['owned_client_pids']=[row['process'].pid for row in clients];save()
            c['hwnd']=wait_until(lambda:base.peer.window_for(process.pid),35,'WINDOW_MISSING')
            hwnd=c['hwnd'];time.sleep(12);click(hwnd,512,464);time.sleep(4)
            bound='RECOVERED_ACCOUNT_BOUND account_id='+str(identity);old=log.read_text('utf-8',errors='replace').count(bound)
            click(hwnd,437,232);type_ascii(hwnd,'codexslow' if identity==4 else 'codexfixed')
            click(hwnd,437,263);type_ascii(hwnd,'labtest2345');click(hwnd,452,304)
            wait_until(lambda:log.read_text('utf-8',errors='replace').count(bound)>old,35,'LOGIN_FAILED')
            time.sleep(4);click(hwnd,330,145);click(hwnd,452,413);time.sleep(4)
            click(hwnd,330,150);click(hwnd,452,376);time.sleep(4);click(hwnd,452,370);time.sleep(12)
            c['handle']=base.peer.kernel.OpenProcess(0x1010,False,process.pid);require(c['handle'],'READ_HANDLE_MISSING')
            c['ui']=base.peer.find_ui(c['handle'],identity,(0,3,4))
            language,sub=struct.unpack('<HH',exact(c,0x59dfd8,4));require(language==4 and (sub==2)==(page==936),'NATIVE_LANGUAGE_NOT_SELECTED')
            return c
        first=launch(4,args.source_page);other=launch(5,936 if args.source_page==950 else 950)
        for c,peer in ((first,other),(other,first)):
            wait_until(lambda:base.peer.remote(c['handle'],c['ui'],peer['identity']),15,'PEER_NOT_VISIBLE')
            s=snap(c);require(s['purse']==fixture['trade_fixture']['wallets'][str(c['identity'])],'WALLET_27_NOT_LOADED')
            require(s['bag'][0]['item']==3107 and s['bag'][0]['quantity']==fixture['trade_fixture']['counts'][str(c['identity'])],'BAG_NOT_LOADED')
        invariant=untouched();result['initial']={'native':[snap(c) for c in clients],'db':saved()};save()
        def opened(source,target):
            if widget(source,0x232e4e) is None:
                for message,vk,data in ((0x100,0x11,1),(0x100,0x48,1),(0x101,0x48,0xc0000001),(0x101,0x11,0xc0000001)):
                    require(base.peer.user.PostMessageW(source['hwnd'],message,vk,data),'MENU_KEY_FAILED');time.sleep(.1)
            main=wait_until(lambda:widget(source,0x232e4e),8,'MAIN_MENU_NOT_OPEN');control(source,main,23);control(source,main,33)
            wait_until(lambda:number(source,source['ui']+0x232f36,2)==4,5,'TRADE_CURSOR_MISSING')
            state=base.ground.world_state(source['handle'],source['ui']);targetstate=base.ground.world_state(target['handle'],target['ui'])
            px,py=base.ground.ground_point(source['handle'],state,targetstate['x'],targetstate['y']);click(source['hwnd'],px,py-26)
            wait_until(lambda:all(widget(c,0x232dae) is not None for c in (source,target)),8,'TRADE_WINDOWS_NOT_OPEN')
            require(snap(source)['peer']==target['identity'] and snap(target)['peer']==source['identity'],'TRADE_WRONG_PEER')
            result['events'].append({'operation':'open29','requester':source['identity'],'native':[snap(c) for c in clients]});save()
        def offer(c,peer,quantity):
            if widget(c,0x232dc8) is None:click(c['hwnd'],708,584);time.sleep(.5)
            bag=wait_until(lambda:widget(c,0x232dc8),8,'BAG_NOT_OPEN')
            trade=widget(c,0x232dae);require(trade is not None,'TRADE_CLOSED_BEFORE_OFFER')
            drag(c['hwnd'],point(c,bag,0),point(c,trade,0));time.sleep(.5)
            dialog=wait_until(lambda:widget(c,0x232dd0),8,'QUANTITY_DIALOG_NOT_OPEN')
            require(number(c,c['ui']+0x23d5e4)==5,'QUANTITY_NOT_TRADE_MODE5')
            control(c,dialog,4);type_ascii(c['hwnd'],'\b'*9+str(quantity));time.sleep(.4)
            require(number(c,c['ui']+0x23d5e8)==quantity,'NATIVE_QUANTITY_NOT_EDITED');control(c,dialog,2)
            wait_until(lambda:any(row['item']==3107 and row['quantity']==quantity for row in snap(peer)['peer_items']),8,'PEER_50_ITEM_NOT_DISPLAYED')
            result['events'].append({'operation':'offer2A','source':c['identity'],'quantity':quantity,'native':[snap(row) for row in clients]});save()
        def confirm(c,money,settles=False):
            trade=widget(c,0x232dae);require(trade is not None,'TRADE_NOT_OPEN_FOR_CONFIRM')
            control(c,trade,12);type_ascii(c['hwnd'],'\b'*9+str(money));time.sleep(.3)
            control(c,trade,11);dialog=wait_until(lambda:widget(c,0x232de6),8,'TRADE_CONFIRM_MODAL_MISSING')
            require(number(c,c['ui']+0x23d5d8)==2,'TRADE_CONFIRM_WRONG_MODE');control(c,dialog,0)
            peer=next(row for row in clients if row is not c)
            def money_seen():
                current=snap(peer)
                if current['peer_labels'] is not None and str(money).encode('ascii') in bytes.fromhex(current['peer_labels']['money']['text_bytes_hex']):
                    return 'native51_label_observed'
                if settles and current['trade_widget'] is None:return 'settlement_closed_before_label_observation'
                return None
            observation=wait_until(money_seen,8,'PEER_51_MONEY_NOT_DISPLAYED')
            result['events'].append({'operation':'confirm2B2C','source':c['identity'],'amount':money,
                                     'peer_money_observation':observation,'native':[snap(row) for row in clients]});save()
        def closed():return all(widget(c,0x232dae) is None and snap(c)['active']==0 for c in clients)
        def consistent():
            db=saved();wallet={row[0]:row[1] for row in db['wallets']};bag={(row[0],row[1]):row[2:4] for row in db['bag']}
            for c in clients:
                s=snap(c)
                if s['purse']!=wallet[c['identity']]:return None
                for row in s['bag']:
                    if [row['item'],row['quantity']]!=bag[(c['identity'],row['slot'])]:return None
            return {'db':db,'native':[snap(c) for c in clients]}
        for source,target in ((first,other),(other,first)):
            prior=saved();opened(source,target);offer(source,target,2);confirm(source,50)
            control(target,widget(target,0x232dae),10);wait_until(closed,8,'CANCEL2D_NOT_CLOSED')
            cancel=wait_until(consistent,8,'CANCEL_INVENTORY_WALLET_NOT_RESTORED')
            require(cancel['db']==prior,'CANCEL_CHANGED_DURABLE_STATE')
            result['events'].append({'operation':'cancel2D','source':target['identity'],'after':cancel});save()
            prior=saved();opened(source,target);offer(source,target,3);offer(target,source,2)
            confirm(source,100);confirm(target,20,settles=True);wait_until(closed,8,'CONFIRM2C_NOT_SETTLED')
            settled=wait_until(consistent,8,'SETTLED_INVENTORY_WALLET_NOT_PROJECTED')
            beforewallet={r[0]:r[1] for r in prior['wallets']};afterwallet={r[0]:r[1] for r in settled['db']['wallets']}
            require(afterwallet[source['identity']]==beforewallet[source['identity']]-80 and
                    afterwallet[target['identity']]==beforewallet[target['identity']]+80,'SETTLEMENT_WALLET_WRONG')
            def total(db,identity):return sum(row[3] for row in db['bag'] if row[0]==identity and row[2]==3107)
            require(total(settled['db'],source['identity'])==total(prior,source['identity'])-1 and
                    total(settled['db'],target['identity'])==total(prior,target['identity'])+1,'SETTLEMENT_ITEMS_WRONG')
            require(len(settled['db']['receipts'])==len(prior['receipts'])+1,'SETTLEMENT_RECEIPT_MISSING')
            require(untouched()==invariant,'TRADE_CHANGED_UNRELATED_SAVED_ROWS')
            result['events'].append({'operation':'settle','requester':source['identity'],'after':settled});save()
        result['unrelated_saved_rows_preserved']=True;result['accepted']=True
    except BaseException as error:result.update(error=str(error),traceback=traceback.format_exc())
    finally:
        for c in reversed(clients):
            try:close(c)
            except Exception as error:result.setdefault('cleanup_errors',[]).append(str(error))
        for loader in loaders:
            if loader.poll() is None:loader.terminate();loader.wait(timeout=5)
        result['desktop_unchanged']=before==desktop_names();result['all_clients_closed']=not any(psutil.pid_exists(c['process'].pid) for c in clients)
        result['accepted']=bool(result['accepted'] and result['desktop_unchanged'] and result['all_clients_closed'] and not result.get('cleanup_errors'));save()
    return 0 if result['accepted'] else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    parser.add_argument('--server-candidate',type=Path);parser.add_argument('--source-page',type=int,choices=(950,936),default=950)
    parser.add_argument('--worker',action='store_true');parser.add_argument('--qualify-only',action='store_true');args=parser.parse_args()
    if args.qualify_only:print(json.dumps(qualify()));return 0
    if args.output is None:parser.error('--output required')
    if args.worker:return worker(args)
    if args.server_candidate is None:parser.error('--server-candidate required')
    qualify();script=Path(__file__).resolve();digest=base.sha(script);base.__file__=str(script);code=base.owner(args)
    receipt=args.output/'run-result.json'
    if receipt.exists():
        result=json.loads(receipt.read_text('utf-8'));result['trade_harness_sha256']=digest
        result['trade_harness_unchanged']=base.sha(script)==digest
        result['accepted']=bool(result['accepted'] and result['trade_harness_unchanged']);base.peer.dump(receipt,result)
        return 0 if result['accepted'] else 1
    return code
if __name__=='__main__':raise SystemExit(main())
