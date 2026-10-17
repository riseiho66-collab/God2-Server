# Legacy receipt identifiers retain their schema spelling; both cases are the
# Taiwan client using Traditional CP950 or Simplified CP936, not regional protocols.
"""NEW armor-preserving original TW CP950/CP936 dual-owner trade UI on a new, owned hidden desktop and port2598.

No foreground activation, screenshots, process-memory writes or packet injection.
Only disposable copies have their port changed. Saves are an isolated backup.
"""
import argparse,json,sqlite3,struct,sys,time,traceback,subprocess,os,socket
from contextlib import closing
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]
import psutil,pefile
import private_peer_role_text_20260930 as base
import private_peer_pose_20261002 as pose
import private_armor_transfer_20261002 as armor_live
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


CANDIDATE_SHA='2696f4efc90648aac47df97e5dbbe80cfd1434cac936f2db36c5ec98ff6ad3d3'
CONTRACT=ROOT/'artifacts/research/native-armor-transfer-20261002/candidate-01/contract.json'
SOURCE_RUN=ROOT/'artifacts/playtests/private-native-blackbox-bank-armor-projection-20261002-03'
base.SOURCE=SOURCE_RUN/'town-diagnostic-accounts.db'

def source_guards():
    expected=json.loads(CONTRACT.read_text('utf-8'))['source_sha256']
    actual={key:base.sha(ROOT/key) for key in expected}
    require(actual==expected,'TRADE_ARMOR_RUNTIME20_PINS')
    return actual

original_prepare=base.prepare

def prepare(args):
    require(base.sha(args.server_candidate)==CANDIDATE_SHA,'IMMUTABLE_TRADE_ARMOR_CANDIDATE')
    original_prepare(args)
    database=args.output/'town-diagnostic-accounts.db'
    config=json.loads((args.output/'server-config.json').read_text('utf-8'))
    require(config['world']['owned_armor_transfers']['enabled'],'ARMOR_OVERLAY_CONFIG_REQUIRED')
    with closing(sqlite3.connect(database)) as db:
        db.execute('pragma foreign_keys=on')
        require(db.execute("select name from schema_migrations where version=42").fetchone()==('owned_armor_instances',),'REAL_SCHEMA42_REQUIRED')
        for identity,balance in ((4,1000),(5,2000)):
            require(db.execute('select count(*) from character_armor_slot_metadata where character_id=?',(identity,)).fetchone()[0]==6,'SIX_ORIGINAL_ARMOR_FIXTURES_REQUIRED')
            db.execute("update character_trade_wallets set amount=?,revision=1 where character_id=?",(balance,identity))
        db.execute('update recovered_positions set x=126,y=132 where character_id=4')
        db.execute('update recovered_positions set x=129,y=132 where character_id=5')
        db.commit()
        require(db.execute('pragma quick_check').fetchone()==('ok',) and db.execute('pragma foreign_key_check').fetchone() is None,'PRIVATE_TRADE_DB_INTEGRITY')
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'))
    fixture['trade_fixture']={'item':3107,'bag_slot':5,'counts':{'4':7,'5':5},'med_totals':{'4':10,'5':8},'wallets':{'4':1000,'5':2000},'authority':'CUSTOM_TEST_NOT_NATIVE','custom_positions':{'4':[126,132],'5':[129,132]},'custom_peer_position_reason':'Preserve accepted relative3 geometry away from original custom NPC128/126; read actual widget intersections before each click, no forced input','armor_per_owner':6,'armor_attempt_slot':0,'source_run':str(SOURCE_RUN),'runtime20':source_guards(),'candidate_sha256':CANDIDATE_SHA,'native_accept_contract':'29/4E directly opens both; actual target offer and 2C confirm, no separate invented accept opcode'}
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
                'global_input_lock_232f68':number(c,c['ui']+0x232f68),'generic_input_mode_5bfa4':number(c,c['ui']+0x5bfa4,2),
                'cursor_mode_232f36':number(c,c['ui']+0x232f36,2),'selected_bag_slot_855f0':number(c,c['ui']+0x855f0,2,True),
                'visible_headers':[v for v in armor_live.hit_layout(c) if v.get('header')],
                'generic_widget_232dda':widget(c,0x232dda),
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
    def instances(c):
        rows=[]
        with closing(base.peer.ro(database)) as db:
            for table,field in (('character_armor_slot_metadata','logical20'),('character_weapon_slot_metadata','logical20'),('character_teleport_gem_metadata','metadata20')):
                for slot,raw,revision,origin,provenance,source,*tail in db.execute('select slot,'+field+',revision,origin,provenance,source_sha256'+(',client_sha256' if 'gem' not in table else '')+',design_id from '+table+' where character_id=? order by slot',(c['identity'],)):
                    native=exact(c,c['ui']+0x8560c+slot*24+4,20)
                    require(native==raw,'TRADE_LOST_FULL20_'+table+'_'+str(slot))
                    rows.append({'table':table,'slot':slot,'metadata':raw.hex(),'native_metadata':native.hex(),'revision':revision,'origin':origin,'provenance':provenance,'source':source,'client_design':tail})
        return rows
    def instance_guard():
        observed=[instances(c) for c in clients]
        require(observed==result['initial_instances'],'TRADE_CHANGED_INSTANCE_METADATA_OR_REVISION')
        return observed
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
            require(s['bag'][5]['item']==3107 and s['bag'][5]['quantity']==fixture['trade_fixture']['counts'][str(c['identity'])],'BAG_NOT_LOADED')
        invariant=untouched();result['initial_instances']=[instances(c) for c in clients];result['initial']={'native':[snap(c) for c in clients],'db':saved()};save()
        def opened(source,target,allow_cancel=True):
            result['events'].append({'operation':'open_input_state','source':source['identity'],'native':[snap(c) for c in clients]});save()
            if widget(source,0x232e4e) is None:
                for message,vk,data in ((0x100,0x11,1),(0x100,0x48,1),(0x101,0x48,0xc0000001),(0x101,0x11,0xc0000001)):
                    require(base.peer.user.PostMessageW(source['hwnd'],message,vk,data),'MENU_KEY_FAILED');time.sleep(.1)
            main=wait_until(lambda:widget(source,0x232e4e),8,'MAIN_MENU_NOT_OPEN');control(source,main,23);control(source,main,33)
            wait_until(lambda:number(source,source['ui']+0x232f36,2)==4,5,'TRADE_CURSOR_MISSING')
            state=base.ground.world_state(source['handle'],source['ui']);targetstate=base.ground.world_state(target['handle'],target['ui'])
            px,py=base.ground.ground_point(source['handle'],state,targetstate['x'],targetstate['y'])
            network=number(source,source['ui']+0x86874)
            require(network>0x10000,'TRADE_NATIVE_NETWORK_OBJECT_MISSING')
            def target_checkpoint(phase):
                data={'operation':'native29_target_checkpoint','phase':phase,'source':source['identity'],'intended_target':target['identity'],'source_world':state,'target_world':targetstate,'click':[px,py-26],
                    'world_1539689c_hitarray':list(struct.unpack('<4i',exact(source,state['world']+0x1539689c,16))),
                    'world_153968ac_hitarray':list(struct.unpack('<4i',exact(source,state['world']+0x153968ac,16))),
                    'world_153968bc_hitarray':list(struct.unpack('<4i',exact(source,state['world']+0x153968bc,16))),
                    'queue_length':number(source,network+0x36c4),'queue_prefix':exact(source,network+0x36c8,10).hex(),
                    'trade_native':[snap(c) for c in clients],
                    'actual_visible_widget_hits':armor_live.hits(armor_live.hit_layout(source),(px,py-26)),
                    'input_mouse_12000_12034':exact(source,number(source,source['ui']+0xcff68)+0x12000,52).hex(),
                    'actual_remote_peer':base.peer.remote(source['handle'],source['ui'],target['identity'])}
                result['events'].append(data);save()
            target_checkpoint('before_hover')
            import ctypes
            from ctypes import wintypes
            rect=wintypes.RECT();require(base.peer.user.GetClientRect(source['hwnd'],ctypes.byref(rect)),'TRADE_CLIENT_RECT_MISSING')
            mx,my=round(px*rect.right/800),round((py-26)*rect.bottom/600)
            require(base.peer.user.PostMessageW(source['hwnd'],0x200,0,(my<<16)|mx),'TRADE_HOVER_MESSAGE_FAILED');time.sleep(.25)
            target_checkpoint('after_hover')
            selected_peer=base.peer.remote(source['handle'],source['ui'],target['identity'])
            require(selected_peer and selected_peer['renderer']>=0 and [selected_peer['x'],selected_peer['y']]==[targetstate['x'],targetstate['y']],'NATIVE_REMOTE_RENDERER_GEOMETRY_NOT_CONFIRMED')
            click(source['hwnd'],px,py-26,interval=.03)
            for sequence in range(6):
                target_checkpoint('after_click_'+str(sequence));time.sleep(.04)
            try:
                wait_until(lambda:all(widget(c,0x232dae) is not None for c in (source,target)),8,'TRADE_WINDOWS_NOT_OPEN')
            except RuntimeError:
                failure=snap(source)
                result['events'].append({'operation':'open_no29_live_diagnostic','source':source['identity'],'native':[snap(c) for c in clients],'db':saved(),'queue10':exact(source,network+0x36c8,10).hex(),'guard':'No window and no replay; only native input cancellation if a selected bag drag exists and global input lock is zero'});save()
                # Escape has a real original handler 4AB3A7 ->4F5E50. It is
                # only applicable with no native modal lock and selected drag.
                # This step is disclosed separately, never called auto recovery.
                if allow_cancel and failure['global_input_lock_232f68']==0 and failure['selected_bag_slot_855f0']>=0:
                    require(base.peer.user.PostMessageW(source['hwnd'],0x100,0x1b,0x00010001),'NATIVE_CANCEL_ESCAPE_DOWN_FAILED');time.sleep(.15)
                    require(base.peer.user.PostMessageW(source['hwnd'],0x101,0x1b,0xc0010001),'NATIVE_CANCEL_ESCAPE_UP_FAILED');time.sleep(.5)
                    result['events'].append({'operation':'native_selected_drag_escape_cancel','source':source['identity'],'before':failure,'after':snap(source),'automatic_recovery':False});save()
                    return opened(source,target,False)
                # Stay in this owned live handle long enough for exact read-only
                # diagnostics. No restart, fixture guessing or forced click.
                for stage in range(4):
                    time.sleep(5)
                    result['events'].append({'operation':'blocked_native_input_read','stage':stage,'source':source['identity'],'native':[snap(c) for c in clients]});save()
                raise
            require(snap(source)['peer']==target['identity'] and snap(target)['peer']==source['identity'],'TRADE_WRONG_PEER')
            result['events'].append({'operation':'open29','requester':source['identity'],'native':[snap(c) for c in clients]});save()
        def armor_reject(source,target):
            prior=saved();before_native=[snap(c) for c in clients]
            if widget(source,0x232dc8) is None:click(source['hwnd'],708,584);time.sleep(.5)
            bag=wait_until(lambda:widget(source,0x232dc8),8,'ARMOR_TRADE_BAG_NOT_OPEN')
            trade=widget(source,0x232dae);require(trade is not None,'ARMOR_TRADE_NOT_OPEN')
            prior_lines=[line for line in log.read_text('utf-8',errors='replace').splitlines() if 'NATIVE_TRADE_REQUEST' in line and 'rejected=true' in line]
            start=point(source,bag,0);end=point(source,trade,0)
            result['events'].append({'operation':'armor2A_attempt','source':source['identity'],'slot':0,'points':[start,end],'before_db':prior,'before_native':before_native});save()
            drag(source['hwnd'],start,end)
            def actual_reject():
                lines=[line for line in log.read_text('utf-8',errors='replace').splitlines() if 'NATIVE_TRADE_REQUEST' in line and 'rejected=true' in line]
                return lines[-1] if len(lines)==len(prior_lines)+1 else None
            marker=wait_until(actual_reject,12,'ARMOR_TRADE_REAL_SERVER_REJECTION_MISSING')
            wait_until(lambda:all(widget(c,0x232dae) is None and snap(c)['active']==0 for c in clients),8,'ARMOR_TRADE_REJECTION_NOT_CLOSED')
            wait_until(lambda:saved()==prior and all(snap(c)['bag']==before_native[i]['bag'] and snap(c)['purse']==before_native[i]['purse'] for i,c in enumerate(clients)),8,'ARMOR_TRADE_BOTH_FULL30BAG_ROLLBACK_FAILED')
            require(untouched()==invariant,'ARMOR_TRADE_REJECTION_CHANGED_UNRELATED_ROWS')
            result['events'].append({'operation':'armor2A_rejected','source':source['identity'],'marker':marker,'after_db':saved(),'native':[snap(c) for c in clients],'full20_instances':instance_guard(),'both_owner_full30bag24_restored':True});save()
        def offer(c,peer,quantity):
            if widget(c,0x232dc8) is None:click(c['hwnd'],708,584);time.sleep(.5)
            bag=wait_until(lambda:widget(c,0x232dc8),8,'BAG_NOT_OPEN')
            trade=widget(c,0x232dae);require(trade is not None,'TRADE_CLOSED_BEFORE_OFFER')
            drag(c['hwnd'],point(c,bag,5),point(c,trade,0));time.sleep(.5)
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
            opened(source,target);armor_reject(source,target)
            prior=saved();opened(source,target);offer(source,target,2);confirm(source,50)
            control(target,widget(target,0x232dae),10);wait_until(closed,8,'CANCEL2D_NOT_CLOSED')
            cancel=wait_until(consistent,8,'CANCEL_INVENTORY_WALLET_NOT_RESTORED')
            require(cancel['db']==prior,'CANCEL_CHANGED_DURABLE_STATE');instance_guard();require(untouched()==invariant,'CANCEL_CHANGED_UNRELATED_ROWS')
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
            instance_guard();require(untouched()==invariant,'TRADE_CHANGED_UNRELATED_SAVED_ROWS')
            result['events'].append({'operation':'settle','requester':source['identity'],'after':settled});save()
        result['final']={'native':[snap(c) for c in clients],'db':saved(),'instances':instance_guard()};require(len(result['final']['db']['receipts'])==len(result['initial']['db']['receipts'])+2,'TWO_REAL_SETTLEMENT_RECEIPTS_REQUIRED')
        require(sum(r[1] for r in result['final']['db']['wallets'] if r[0] in (4,5))==3000,'TRADE_MONEY_TOTAL_NOT_3000')
        require(sum(r[3] for r in result['final']['db']['bag'] if r[2]==3107)==18,'TRADE_MED_TOTAL_NOT_18')
        result['unrelated_saved_rows_preserved']=True;result['accepted']=True
    except BaseException as error:
        result.update(error=str(error),traceback=traceback.format_exc())
        try:result['failure_native']=[snap(c) for c in clients if c.get('handle')]
        except Exception as checkpoint_error:result['failure_checkpoint_error']=str(checkpoint_error)
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
    require(base.sha(args.server_candidate)==CANDIDATE_SHA,'IMMUTABLE_TRADE_ARMOR_CANDIDATE')
    source_before=source_guards();desktop_before=desktop_names()
    protected={str(p.pid):{'exe':p.info['exe'],'created':p.info['create_time']} for p in psutil.process_iter(['exe','create_time']) if p.info['exe'] and Path(p.info['exe']).name.lower() in ('god2.exe','god2-server.exe','leproc.exe','private_desktop_runner.exe')}
    frozen={str(path):base.sha(path) for path in (Path(__file__).resolve(),Path(base.__spec__.origin),Path(pose.__file__).resolve(),ROOT/'tools/strike_lab/private_trade_20261002.py',ROOT/'tools/strike_lab/private_bank_armor_projection_20261002_v03.py',ROOT/'tools/strike_lab/private_armor_transfer_20261002.py',ROOT/'tools/strike_lab/private_inventory_move_ui.py',CONTRACT,SOURCE_RUN/'run-result.json',SOURCE_RUN/'town-diagnostic-accounts.db',SOURCE_RUN/'server-config.json',ROOT/'artifacts/playtests/private-native-blackbox-armor-transfer-20261002-01/run-result.json')}
    os.environ['GOD2_NATIVE_WORLD_RECORDS_LAB']='1'
    qualify();script=Path(__file__).resolve();digest=base.sha(script);base.__file__=str(script);code=base.owner(args)
    receipt=args.output/'run-result.json'
    if receipt.exists():
        result=json.loads(receipt.read_text('utf-8'));result['trade_harness_sha256']=digest
        result['trade_harness_unchanged']=base.sha(script)==digest
        result['runtime20_before']=source_before;result['runtime20_after']=source_guards();result['runtime20_unchanged']=result['runtime20_before']==result['runtime20_after']
        result['frozen_files_before']=frozen;result['frozen_files_after']={path:base.sha(Path(path)) for path in frozen};result['frozen_files_unchanged']=result['frozen_files_before']==result['frozen_files_after']
        after={str(p.pid):{'exe':p.info['exe'],'created':p.info['create_time']} for p in psutil.process_iter(['exe','create_time']) if str(p.pid) in protected}
        result['protected_processes_before']=protected;result['protected_processes_preserved']=after==protected
        result['desktop_owner_before']=desktop_before;result['desktop_owner_after']=desktop_names();result['desktop_owner_unchanged']=desktop_before==result['desktop_owner_after']
        with socket.socket() as probe:result['exclusive2598_released']=probe.connect_ex(('127.0.0.1',2598))!=0
        pids=[result.get('server_pid'),result.get('runner_pid')]+result.get('ui',{}).get('owned_client_pids',[])
        result['owned_pid_terminal']={str(pid):{'pid_exists':psutil.pid_exists(pid)} for pid in pids if pid}
        result['scope']='REAL_DUAL_OWNER_TW_CN_TRADE_ARMOR2A_REJECTION_MED_MONEY_2B_2C_COMMIT_AND_CANCEL_WITH_ARMOR_WEAPON_GEM_FULL20_PRESERVED_CUSTOM_TEST_ONLY'
        result['accepted']=bool(result['accepted'] and result['trade_harness_unchanged'] and result['runtime20_unchanged'] and result['frozen_files_unchanged'] and result['protected_processes_preserved'] and result['desktop_owner_unchanged'] and result['exclusive2598_released'] and not any(row['pid_exists'] for row in result['owned_pid_terminal'].values()));base.peer.dump(receipt,result)
        return 0 if result['accepted'] else 1
    return code
if __name__=='__main__':raise SystemExit(main())
