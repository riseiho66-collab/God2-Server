# Legacy receipt identifiers retain their schema spelling; both cases are the
# Taiwan client using Traditional CP950 or Simplified CP936, not regional protocols.
"""NEW CUSTOM0069 full20 two original TW CP950/CP936 clients; source-only preparation.

No foreground activation, screenshots, process-memory writes or packet injection.
Only disposable copies have their port changed. Saves are an isolated backup.
"""
import argparse,json,sqlite3,struct,sys,time,traceback,subprocess,os,socket,re,copy
from contextlib import closing
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]
import psutil,pefile
import private_peer_role_text_20260930 as base
import private_peer_pose_20261002 as pose
import private_armor_transfer_20261002 as armor_live
import current_trade_world_hit_20261003 as world_hit
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import type_ascii
base.CLIENT_SHA=pose.CLIENT_SHA

def click(hwnd,x,y,double=False,interval=.15):
    import ctypes
    from ctypes import wintypes
    rect=wintypes.RECT();require(base.peer.user.GetClientRect(hwnd,ctypes.byref(rect)) and rect.right>0 and rect.bottom>0,'CLICK_CLIENT_RECT')
    x,y=round(x*rect.right/800),round(y*rect.bottom/600);position=(y<<16)|x
    require(base.peer.user.PostMessageW(hwnd,0x200,0,position),'CLICK_HOVER');time.sleep(interval)
    for message in ((0x201,0x203) if double else (0x201,)):
        try:
            require(base.peer.user.PostMessageW(hwnd,message,1,position),'CLICK_PRESS');time.sleep(interval)
        finally:
            require(base.peer.user.PostMessageW(hwnd,0x202,0,position),'CLICK_NORMAL_RELEASE');time.sleep(interval)
    return [x,y]

def drag(hwnd,start,end):
    import ctypes
    from ctypes import wintypes
    rect=wintypes.RECT();require(base.peer.user.GetClientRect(hwnd,ctypes.byref(rect)),'DRAG_CLIENT_RECT')
    sx,sy=round(start[0]*rect.right/800),round(start[1]*rect.bottom/600)
    x,y=round(end[0]*rect.right/800),round(end[1]*rect.bottom/600)
    require(base.peer.user.PostMessageW(hwnd,0x200,0,(sy<<16)|sx),'DRAG_START_HOVER');time.sleep(.12)
    try:
        require(base.peer.user.PostMessageW(hwnd,0x201,1,(sy<<16)|sx),'DRAG_START_PRESS');time.sleep(.12)
        for step in range(1,11):
            px,py=sx+(x-sx)*step//10,sy+(y-sy)*step//10
            require(base.peer.user.PostMessageW(hwnd,0x200,1,(py<<16)|px),'DRAG_NORMAL_MOVE');time.sleep(.08)
    finally:
        require(base.peer.user.PostMessageW(hwnd,0x202,0,(y<<16)|x),'DRAG_NORMAL_RELEASE_FAILED')
    return [[sx,sy],[x,y]]


def qualify():
    raw=pose.qualify_source();mapped=pefile.PE(str(base.LIVE)).get_memory_mapped_image()
    regions=((0x497250,158),(0x497a30,82),(0x49d980,1744),(0x49e380,500),
             (0x483c80,3488),(0x4a7380,35),(0x4a6760,500),(0x4835a0,250),
             (0x481f70,160),(0x465fa0,420),(0x4c9970,143),(0x4ca470,160),
             (0x4c9ed0,512),(0x498d70,89),(0x5077c0,138),
             (0x41e500,70),(0x426700,200),(0x426140,600))+tuple((va,size) for _,va,size in world_hit.SPANS)
    for va,size in regions:
        require(mapped[va-0x400000:va-0x400000+size]==raw[va-0x400000:va-0x400000+size],
                'NATIVE_TRADE_CODE_CHANGED_'+hex(va))
    return {'current_client_sha256':base.sha(base.LIVE),'regions':regions,'no_ui_started':True,'authority':'STATIC_CODE_EQUALITY_ONLY_NOT_LIVE_ACCEPTANCE',
            'cursor':'menu33 ->4A7380 mode4 ->4835A0 event3 ->481F70 -6 ->465FA0 ->49DE30/29',
            'item':'bag232DC8 sourceSlot ->trade232DAE controls0..7 ->49E440/497290 SELF sourceSlot; 49DF10 PEER offerIndex; stack dialog232DD0 mode5/control4edit/control2accept',
            'money':'trade control12 numeric edit, control11 confirm ->modal232DE6 mode2/control0 ->2B+2C',
            'cancel':'trade control10 ->49DD40(1)/2D'}


CONTRACT=ROOT/'artifacts/research/owned-instance-trade-0069/candidate-20261003/contract.json'
SOURCE_RUN=ROOT/'artifacts/playtests/private-native-blackbox-owned-foreign-bank-20261003-02'
base.SOURCE=SOURCE_RUN/'town-diagnostic-accounts.db'
SCOPE='OWNED_INSTANCE_TRADE_FULL20_TW_CN_CUSTOM_TEST_ONLY'
MUTABLE=('diagnostic_inventory_slots','character_armor_slot_metadata','character_weapon_slot_metadata','character_teleport_gem_metadata','character_trade_wallets','character_owned_instance_trade_receipts')
META={'character_armor_slot_metadata':'logical20','character_weapon_slot_metadata':'logical20','character_teleport_gem_metadata':'metadata20'}

def candidate_sha():
    c=json.loads(CONTRACT.read_text('utf-8'));value=c['candidate_sha256']
    require(re.fullmatch('[0-9a-f]{64}',value) and c['design']=='CUSTOM-0069','NEW_0069_IMMUTABLE_CONTRACT_REQUIRED')
    require(c['client_sha256']==base.CLIENT_SHA,'CURRENT_CLIENT_CONTRACT_PIN')
    return value

def source_guards():
    contract=json.loads(CONTRACT.read_text('utf-8'));expected=contract['source_sha256']
    require(len(expected)==32,'EXACT_RUNTIME32_CONTRACT_REQUIRED')
    actual={key:base.sha(ROOT/key) for key in expected}
    require(actual==expected,'OWNED_TRADE_RUNTIME_SOURCE_PINS')
    return actual

def read_saved(database):
    def normalized(row):return [v.hex() if isinstance(v,bytes) else v for v in row]
    with closing(base.peer.ro(database)) as db:
        return {name:[normalized(row) for row in db.execute('select * from "'+name+'" order by '+('receipt' if name.endswith('receipts') else 'character_id'+(',slot' if name!='character_trade_wallets' else '')))] for name in MUTABLE}

def native_metadata(saved,identity,slot):
    scalar=next(row for row in saved['diagnostic_inventory_slots'] if row[0]==identity and row[1]==slot)
    if scalar[3]==0:return None
    overlays=[row for table in META for row in saved[table] if row[0]==identity and row[1]==slot]
    require(len(overlays)<=1,'FULL20_OVERLAY_CONFLICT')
    return bytes.fromhex(overlays[0][2]) if overlays else struct.pack('<H',scalar[2])+bytes(18)

def owner_state(saved,identity):
    scalar={row[1]:row for row in saved['diagnostic_inventory_slots'] if row[0]==identity}
    require(all(slot in scalar for slot in range(30)),'EXPLICIT30_CAPACITY_REQUIRED')
    wallet=next(row for row in saved['character_trade_wallets'] if row[0]==identity)
    armor=[];foreign=[]
    for row in saved['character_armor_slot_metadata']:
        if row[0]==identity:
            cell=scalar[row[1]];armor.append([row[1],cell[2],cell[3],row[3],list(bytes.fromhex(row[2])),row[4],row[5],True,row[6],row[7],row[8]])
    for table in ('character_weapon_slot_metadata','character_teleport_gem_metadata'):
        values=[]
        for row in saved[table]:
            if row[0]==identity:values.append([row[1],list(bytes.fromhex(row[2])),row[3],row[4],row[5],row[6],row[7] if table=='character_weapon_slot_metadata' else '',row[-1]])
        foreign.append(values)
    return [identity,identity,wallet[1],wallet[2],[[scalar[slot][2],scalar[slot][3],scalar[slot][4],scalar[slot][5]] if slot in scalar else None for slot in range(50)],armor,*foreign]

def expected_trade(before,order,offers,money):
    """Independent saved-row planner. Never derive an expectation from outputs."""
    after=copy.deepcopy(before);outgoing={};touched={identity:set() for identity in order};transfers=[]
    scalar=lambda state,identity,slot:next(row for row in state['diagnostic_inventory_slots'] if row[0]==identity and row[1]==slot)
    for identity in order:
        used=set();outgoing[identity]=[]
        for slot,quantity in offers[identity]:
            require(slot<30 and slot not in used,'OFFER_PROTECTED_OR_DUPLICATE');used.add(slot)
            old=scalar(before,identity,slot);require(0<quantity<=old[3],'OFFER_QUANTITY_INVALID')
            overlays=[(table,copy.deepcopy(row)) for table in META for row in before[table] if row[0]==identity and row[1]==slot]
            require(len(overlays)<=1 and (not overlays or old[3]==quantity==1),'WHOLE_INSTANCE_QUANTITY1_REQUIRED')
            item=copy.deepcopy(old);item[3]=quantity;outgoing[identity].append((slot,item,overlays))
            cell=scalar(after,identity,slot);cell[3]-=quantity;touched[identity].add(slot)
            if cell[3]==0:
                cell[2]=0
                for table in META:after[table]=[r for r in after[table] if r[:2]!=[identity,slot]]
        wallet=next(row for row in after['character_trade_wallets'] if row[0]==identity)
        peer=next(i for i in order if i!=identity);new=wallet[1]-money[identity]+money[peer]
        require(0<=new<=0xffffffff,'WALLET_RANGE');wallet[2]+=int(new!=wallet[1]);wallet[1]=new
    for destination_side,identity in enumerate(order):
        peer=order[1-destination_side]
        for source_slot,item,overlays in outgoing[peer]:
            destination=next((slot for slot in range(30) if scalar(after,identity,slot)[3]==0),None)
            require(destination is not None,'FULLBAG_PLAN_REFUSAL')
            cell=scalar(after,identity,destination);cell[2:4]=item[2:4];cell[5]=item[5];touched[identity].add(destination)
            for table in META:after[table]=[r for r in after[table] if r[:2]!=[identity,destination]]
            for table,row in overlays:row[0:2]=[identity,destination];after[table].append(row)
            transfers.append([1-destination_side,source_slot,destination_side,destination,item[3]])
        for slot in touched[identity]:
            revision=scalar(before,identity,slot)[4]+1;scalar(after,identity,slot)[4]=revision
            for table in META:
                for row in after[table]:
                    if row[:2]==[identity,slot]:row[3]=revision
    for table in META:after[table].sort(key=lambda r:(r[0],r[1]))
    before_state=[owner_state(before,i) for i in order];after_state=[owner_state(after,i) for i in order]
    offers_state=[[i,i,money[i],offers[i]] for i in order]+[transfers]
    return after,{'before_state':before_state,'after_state':after_state,'offers_state':offers_state}

def instance_inventory(saved):
    return sorted((table,repr(row[2:3]+row[4:])) for table in META for row in saved[table] if row[0] in(4,5))

original_prepare=base.prepare
def prepare(args):
    require(base.sha(args.server_candidate)==candidate_sha(),'IMMUTABLE_0069_CANDIDATE')
    require(json.loads((SOURCE_RUN/'run-result.json').read_text('utf-8'))['accepted'],'ACCEPTED_FULL20_SEED_REQUIRED')
    original_prepare(args)
    database=args.output/'town-diagnostic-accounts.db';config=json.loads((args.output/'server-config.json').read_text('utf-8'))
    config['world']['owned_armor_transfers']={'enabled':True};config['world']['owned_instance_trade']={'enabled':True}
    base.peer.dump(args.output/'server-config.json',config)
    with closing(sqlite3.connect(database)) as db:
        db.execute('pragma foreign_keys=on')
        require(db.execute('select count(*) from schema_migrations where version=45').fetchone()==(1,),'REAL_SCHEMA45_REQUIRED')
        require(db.execute("select count(*) from sqlite_master where name='character_owned_instance_trade_receipts'").fetchone()==(1,),'REAL_0069_RECEIPT_TABLE_REQUIRED')
        for identity,count,balance in ((4,10,1000),(5,8,2000)):
            require(db.execute('select count(*) from character_armor_slot_metadata where character_id=?',(identity,)).fetchone()==(6,),'SIX_ARMOR_FIXTURES')
            for slot in (5,6,7):
                require(all(db.execute('select count(*) from '+table+' where character_id=? and slot=?',(identity,slot)).fetchone()==(0,) for table in META),'MED_FIXTURE_OVERLAY_CONFLICT')
                db.execute('update diagnostic_inventory_slots set item_id=?,count=?,revision=1 where character_id=? and slot=?',(3107 if slot==5 else 0,count if slot==5 else 0,identity,slot))
            db.execute('update character_trade_wallets set amount=?,revision=1 where character_id=?',(balance,identity))
        db.execute('update recovered_positions set area=4,scene=3,x=126,y=132 where character_id=4')
        db.execute('update recovered_positions set area=4,scene=3,x=129,y=132 where character_id=5')
        db.commit();require(db.execute('pragma quick_check').fetchone()==('ok',) and db.execute('pragma foreign_key_check').fetchone() is None,'PRIVATE_DB_INTEGRITY')
    seed=read_saved(database)
    for identity in (4,5):
        for slot,kind in ((0,2 if identity==4 else 26),(1,2 if identity==4 else 26),(8,1),(9,1),(10,25),(12,8)):
            raw=native_metadata(seed,identity,slot);require(raw and raw[2]&63==kind,'EXACT_INSTANCE_FIXTURE_FAMILY')
        require(native_metadata(seed,identity,8)!=native_metadata(seed,identity,9),'SAME_ID_DIFFERENT_TAIL_FIXTURE')
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'))
    fixture['trade_fixture']={'authority':'CUSTOM_TEST_NOT_NATIVE','source_run':str(SOURCE_RUN),'wallets':{'4':1000,'5':2000},'counts':{'4':10,'5':8},'positions':{'4':[126,132],'5':[129,132]},'instance_slots':[0,1,8,9,10,12],'med_slot':5,'all_fixture_rows':seed,'candidate_sha256':candidate_sha(),'source_contract':source_guards(),'normal_acceptance':'native29 opens both; true2A then2B/2C, no fabricated accept opcode'}
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
    def input_checkpoint(c,w,index,phase,xy=None):
        entry=c['ui']+0xe2170+w*0x2a08+0x8b8+index*100
        raw=exact(c,entry,100);hit=int.from_bytes(raw[8:10],'little',signed=True)
        rows=armor_live.hit_layout(c)
        network=number(c,c['ui']+0x86874)
        layout_dir=args.output/'native-control-layouts';layout_dir.mkdir(exist_ok=True)
        layout_path=layout_dir/(str(len(result['events'])).zfill(4)+'.json');require(not layout_path.exists(),'NEW_LAYOUT_ARTIFACT_ONLY')
        base.peer.dump(layout_path,{'authority':'READ_ONLY_REAL_CURRENT_CLIENT_NATIVE_WIDGET_STATE','character':c['identity'],'widget':w,'index':index,'phase':phase,'rows':rows})
        data={'operation':'native_control_input_checkpoint','phase':phase,'source':c['identity'],'widget':w,'index':index,
            'widget_flags':number(c,c['ui']+0xe2170+w*0x2a08+0x818,2),'control_raw100':raw.hex(),'control_flags':raw[0],
            'control_type4':int.from_bytes(raw[4:8],'little'),'native_hit_id':hit,'point':xy,
            'complete_active_layout_artifact':str(layout_path),'complete_active_layout_sha256':base.sha(layout_path),'complete_active_layout_rows':len(rows),'point_hits':armor_live.hits(rows,xy) if xy else [],
            'queue_length':number(c,network+0x36c4),'queue10':exact(c,network+0x36c8,10).hex(),
            'input_lock':number(c,c['ui']+0x232f68),'input_mode':number(c,c['ui']+0x5bfa4,2),
            'cursor_mode':number(c,c['ui']+0x232f36,2),'selected_bag_slot':number(c,c['ui']+0x855f0,2,True),
            'native_trade_request_count':log.read_text('utf-8',errors='replace').count('NATIVE_TRADE_REQUEST')}
        result['events'].append(data);save();return data
    def point(c,w,index):
        require(number(c,c['ui']+0xe2170+w*0x2a08+0x818,2)&0x20,'CONTROL_WIDGET_NOT_NATIVE_VISIBLE')
        xy,evidence=armor_live.hit_point(c,w,index)
        data=input_checkpoint(c,w,index,'point_selection',xy)
        top=data['point_hits'][0] if data['point_hits'] else None
        require(data['control_flags'] and top and top['widget']==w and top['index']==index and top['hit_id']==data['native_hit_id'],'CONTROL_NATIVE_TOP_HIT_MISMATCH')
        result['last_control']={'character':c['identity'],'widget':w,'index':index,'point':xy,'native_hit_id':data['native_hit_id'],'rect':top['rect'],'options':evidence['options']};save()
        return xy
    def control(c,w,index):
        import ctypes
        from ctypes import wintypes
        for calibration in range(3):
            xy=point(c,w,index);rect=wintypes.RECT()
            require(base.peer.user.GetClientRect(c['hwnd'],ctypes.byref(rect)),'CONTROL_CLIENT_RECT_MISSING')
            mx,my=round(xy[0]*rect.right/800),round(xy[1]*rect.bottom/600)
            require(base.peer.user.PostMessageW(c['hwnd'],0x200,0,(my<<16)|mx),'CONTROL_NATIVE_HOVER_FAILED');time.sleep(.1)
            post=input_checkpoint(c,w,index,'hover_'+str(calibration),xy)
            top=post['point_hits'][0] if post['point_hits'] else None
            if top and top['widget']==w and top['index']==index and top['hit_id']==post['native_hit_id']:
                click(c['hwnd'],*xy)
                input_checkpoint(c,w,index,'after_click_immediate',xy);time.sleep(.25)
                input_checkpoint(c,w,index,'after_click_frame',xy)
                return
        raise RuntimeError('CONTROL_HOVER_CHANGED_NATIVE_TOP_HIT_NO_FORCED_CLICK')
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
        return {'identity':c['identity'],'language':c['page'],'pid':c['process'].pid,'trade_widget':widget(c,0x232dae),
                'peer_labels':{'name':label(c,peer_widget,0),'money':label(c,peer_widget,1)} if peer_widget is not None else None,
                'peer':number(c,c['ui']+0x866d0,2),'purse':number(c,c['ui']+0x85604),
                'escrow_money':number(c,c['ui']+0x866d4),'money_sent':number(c,c['ui']+0x866dc),
                'confirmed':number(c,c['ui']+0x866e0),'active':number(c,c['ui']+0x866e4),
                'global_input_lock_232f68':number(c,c['ui']+0x232f68),'generic_input_mode_5bfa4':number(c,c['ui']+0x5bfa4,2),
                'cursor_mode_232f36':number(c,c['ui']+0x232f36,2),'selected_bag_slot_855f0':number(c,c['ui']+0x855f0,2,True),
                'visible_headers':[v for v in armor_live.hit_layout(c) if v.get('header')],
                'generic_widget_232dda':widget(c,0x232dda),
                'self_items':items(0x866e8,8),'peer_items':items(0x867a8,8),'bag':items(0x8560c,30)}
    def saved():return read_saved(database)
    def untouched():
        with closing(base.peer.ro(database)) as db:
            output={}
            for name, in db.execute("select name from sqlite_master where type='table' order by name"):
                where=' where character_id not in(4,5)' if name in MUTABLE and name!='character_owned_instance_trade_receipts' else ''
                if name=='character_owned_instance_trade_receipts':continue
                output[name]=sorted(repr(row) for row in db.execute('select * from "'+name.replace('"','""')+'"'+where))
            return output
    def consistent(expected=None):
        actual=saved();observed=[];problems=[]
        if expected is not None:
            for table in MUTABLE:
                if table!='character_owned_instance_trade_receipts' and actual[table]!=expected[table]:problems.append({'table':table,'expected':expected[table],'actual':actual[table]})
        for c in clients:
            scalar={row[1]:row for row in actual['diagnostic_inventory_slots'] if row[0]==c['identity']}
            rows=[]
            for slot in range(50):
                cell=scalar.get(slot)
                raw=exact(c,c['ui']+0x8560c+slot*24,24);qty=int.from_bytes(raw[:4],'little');metadata=native_metadata(actual,c['identity'],slot) if cell is not None else None
                # Native41 only clears active key/count; inactive old20 is not authority.
                # Absent scalar cells have no authoritative item20 to compare.
                valid=qty==0 if cell is None else qty==cell[3] and int.from_bytes(raw[4:6],'little')==cell[2] and (metadata is None or raw[4:]==metadata)
                rows.append({'slot':slot,'raw24':raw.hex(),'sql_scalar':cell,'expected20':metadata.hex() if metadata else None,'valid':valid})
                if not valid:problems.append({'owner':c['identity'],'slot':slot,'observed':rows[-1]})
            native=snap(c);wallet=next(row for row in actual['character_trade_wallets'] if row[0]==c['identity'])
            if native['purse']!=wallet[1]:problems.append({'owner':c['identity'],'wallet':wallet,'native_purse':native['purse']})
            observed.append({'identity':c['identity'],'full50':rows,'native':native})
        result['last_saved_projection_observation']={'db':actual,'native':observed,'problems':problems}
        return None if problems else result['last_saved_projection_observation']
    def instance_guard():
        now=saved()
        for table in ('diagnostic_inventory_slots',*META):
            initial=[r for r in result['initial']['db'][table] if r[0] in(4,5) and r[1]>=30]
            require([r for r in now[table] if r[0] in(4,5) and r[1]>=30]==initial,'EQUIPPED_PROTECTED_FULL20_CHANGED_'+table)
        require(untouched()==invariant,'UNRELATED_OR_OTHER_OWNER_ROWS_CHANGED')
        require(consistent(),'FULL50_PROJECTION_REQUIRED')
        require(instance_inventory(now)==instance_inventory(result['initial']['db']),'WHOLE_INSTANCE_METADATA_PROVENANCE_NOT_CONSERVED')
        return {'full50_verified':True,'equipped_preserved':True,'other_players_preserved':True,'whole_instance_conservation':True,'provenance_preserved':True}
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
            result.setdefault('owned_client_pids',[]).append(process.pid);save()
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
        invariant=untouched();result['initial']={'native':[snap(c) for c in clients],'db':saved()};wait_until(consistent,8,'INITIAL_FULL50_NOT_LOADED');save()
        def actor_hit(source,target,xy=None):
            world=base.ground.world_state(source['handle'],source['ui'])
            remote=base.peer.remote(source['handle'],source['ui'],target['identity'])
            require(remote and remote['renderer']>=0,'REGISTERED_REMOTE_RENDERER_REQUIRED')
            manager=world['world']+0x15383410;display=number(source,manager+8)
            require(display==world['world']+0xaba32e0,'CURRENT_REMOTE_DISPLAY_BINDING')
            count=number(source,display+0xa7e001c);renderer=remote['renderer']
            require(0<=renderer<count<=4096,'CURRENT_REMOTE_NODE_COUNT')
            node=display+0x1c+renderer*0xa7e0
            active=number(source,node);hit=number(source,node+0x10,4,True);category=number(source,node+0xa7d0)
            require(active==2 and 0<=hit<0xc00 and category<4,'CURRENT_REMOTE_NATIVE_HIT_ELIGIBILITY')
            mouse=number(source,display+8)
            require(mouse==number(source,source['ui']+0xcff68)==number(source,world['world']+0xa7e05c8),'CURRENT_MOUSE_POINTER_BINDING')
            registered=struct.unpack('<6i',exact(source,mouse+hit*24,24))
            cache=[list(row) for row in struct.iter_unpack('<6h',exact(source,display+0xa7e005a,84))]
            network=number(source,source['ui']+0x86874);length=number(source,network+0x36c4)
            require(network>0x10000 and length<=0xa00,'CURRENT_NETWORK_QUEUE_BOUNDS')
            # Never treat the stale prefix beyond queue length as a request.
            prefix=exact(source,network+0x36c8,min(length,5)).hex() if length else ''
            return {'world':world,'remote_identity':remote['identity'],'remote_entry':remote['entry'],
                'renderer':renderer,'display':hex(display),'node':hex(node),'node_active':active,
                'node_hit_id':hit,'category':category,'node_count':count,'mouse':hex(mouse),
                'registered':list(registered),'cache7x6':cache,
                'current_xy':list(struct.unpack('<hh',exact(source,mouse+0x12000,4))),
                'mouse_flags':{hex(off):number(source,mouse+off) for off in (0x12014,0x12018,0x12020,0x12024,0x1202c)},
                'cursor':number(source,source['ui']+0x232f36,2),'input_lock':number(source,source['ui']+0x232f68),
                'queue_length':length,'valid_queue_prefix5':prefix,
                'visible_widget_hits':armor_live.hits(armor_live.hit_layout(source),xy) if xy else []}
        def actor_press(source,target):
            import ctypes
            from ctypes import wintypes
            start=actor_hit(source,target);active,left,top,right,bottom,_=start['registered']
            require(active==1 and 0<=left<right<800 and 0<=top<bottom<600,'CURRENT_ACTOR_REGISTERED_RECTANGLE')
            require(start['cursor']==4 and start['input_lock']==0,'CURRENT_ACTOR_CURSOR_NOT_READY')
            rect=wintypes.RECT();require(base.peer.user.GetClientRect(source['hwnd'],ctypes.byref(rect)),'TRADE_CLIENT_RECT_MISSING')
            def message(code,key,xy):
                mx,my=round(xy[0]*rect.right/800),round(xy[1]*rect.bottom/600)
                require(base.peer.user.PostMessageW(source['hwnd'],code,key,(my<<16)|mx),'TRADE_REGISTERED_MOUSE_MESSAGE_FAILED')
            attempts=[];selected=None
            # Only hover calibration within actual registered geometry; no press retries.
            for fx,fy in ((.5,.5),(.2,.2),(.8,.2),(.2,.8),(.8,.8),(.5,.2),(.5,.8),(.2,.5),(.8,.5)):
                xy=(round(left+(right-left)*fx),round(top+(bottom-top)*fy))
                message(0x200,0,xy)
                deadline=time.monotonic()+1.5;observed=None
                while time.monotonic()<deadline:
                    now=actor_hit(source,target,xy)
                    a,l,t,r,b,inside=now['registered'];cat=now['category']
                    require(now['renderer']==start['renderer'] and now['node_hit_id']==start['node_hit_id'],'ACTOR_CHANGED_DURING_HOVER_NO_GUESSING')
                    if a==1 and l<=xy[0]<=r and t<=xy[1]<=b and inside and now['cache7x6'][cat][5]==now['renderer'] and not now['visible_widget_hits']:
                        observed=now;break
                    time.sleep(.04)
                attempts.append({'point':xy,'last':now,'native_hover_confirmed':observed is not None})
                if observed is not None:selected=(xy,observed);break
            result['events'].append({'operation':'registered_actor_hover','source':source['identity'],'target':target['identity'],'attempts':attempts});save()
            require(selected,'REGISTERED_ACTOR_NATIVE_HOVER_NOT_CONFIRMED')
            xy,hover=selected
            require(hover['queue_length']==0,'ACTOR_PRESS_REQUIRES_DRAINED_NATIVE_QUEUE')
            before_db=saved();lines=log.read_text('utf-8',errors='replace').splitlines()
            bound=[line for line in lines if 'RECOVERED_ACCOUNT_BOUND account_id='+str(source['identity'])+';' in line]
            require(bound,'CURRENT_OWNER_NATIVE_SESSION_REQUIRED')
            session=int(re.search(r'session_id=(\d+)',bound[-1]).group(1))
            def requests():
                return [line for line in log.read_text('utf-8',errors='replace').splitlines()
                        if 'NATIVE_TRADE_REQUEST session_id='+str(session)+' ' in line]
            prior_requests=requests();pressed=False;samples=[];observed_producer=None
            expected29=(b'\x29'+struct.pack('<HH',target['identity'],0)).hex()
            try:
                message(0x201,1,xy);pressed=True
                deadline=time.monotonic()+5
                while time.monotonic()<deadline:
                    now=actor_hit(source,target,xy);new=requests()[len(prior_requests):]
                    # One legal press only. A rejection/foreign target is a failure,
                    # never a reason to replay after a possible successful request.
                    require(len(new)<=1,'ACTOR_PRESS_DUPLICATE_NATIVE_REQUEST')
                    if new:require('records=1 committed=false rejected=false' in new[0],'ACTOR_PRESS_NATIVE_REQUEST_REJECTED')
                    if now['queue_length']:
                        require(now['queue_length']==5 and now['valid_queue_prefix5']==expected29,'ACTOR_PRESS_UNEXPECTED_NATIVE_QUEUE')
                    cat=now['category'];press_match=now['cache7x6'][cat][0]==now['renderer']
                    producer=bool(now['queue_length']==5 or new or
                                  (press_match and now['cursor']==1))
                    samples.append({'time':time.monotonic(),'state':now,'new_request_markers':new,'press_cache_matches':press_match,'producer_observed':producer})
                    if producer:observed_producer=samples[-1];break
                    time.sleep(.04)
            finally:
                if pressed:message(0x202,0,xy)
                result['events'].append({'operation':'registered_actor_held_press','source':source['identity'],'target':target['identity'],'point':xy,'session_id':session,'samples':samples,'observed_producer':observed_producer,'normal_release_posted':pressed});save()
            require(observed_producer,'ACTOR_PRESS_PRODUCER_NOT_OBSERVED_NO_REPLAY')
            require(saved()==before_db,'ACTOR_OPEN_CHANGED_DURABLE_STATE')
        def opened(source,target):
            result['events'].append({'operation':'open_input_state','source':source['identity'],'native':[snap(c) for c in clients]});save()
            if widget(source,0x232e4e) is None:
                for message,vk,data in ((0x100,0x11,1),(0x100,0x48,1),(0x101,0x48,0xc0000001),(0x101,0x11,0xc0000001)):
                    require(base.peer.user.PostMessageW(source['hwnd'],message,vk,data),'MENU_KEY_FAILED');time.sleep(.1)
            main=wait_until(lambda:widget(source,0x232e4e),8,'MAIN_MENU_NOT_OPEN');control(source,main,23);control(source,main,33)
            wait_until(lambda:number(source,source['ui']+0x232f36,2)==4,5,'TRADE_CURSOR_MISSING')
            actor_press(source,target)
            wait_until(lambda:all(widget(c,0x232dae) is not None for c in (source,target)),8,'TRADE_WINDOWS_NOT_OPEN')
            require(snap(source)['peer']==target['identity'] and snap(target)['peer']==source['identity'],'TRADE_WRONG_PEER')
            result['events'].append({'operation':'open29','requester':source['identity'],'native':[snap(c) for c in clients]});save()
        def offer(c,peer,slot,quantity,offer_index):
            before=saved();metadata=native_metadata(before,c['identity'],slot);require(metadata is not None,'OFFER_EMPTY_SOURCE')
            if widget(c,0x232dc8) is None:click(c['hwnd'],708,584);time.sleep(.5)
            bag=wait_until(lambda:widget(c,0x232dc8),8,'BAG_NOT_OPEN');trade=widget(c,0x232dae)
            require(trade is not None and offer_index<8,'TRADE_CLOSED_OR_OFFER_LIMIT')
            source_record=exact(c,c['ui']+0x8560c+slot*24,24)
            require(source_record[4:]==metadata,'OFFER_SOURCE_FULL20_MISMATCH')
            drag(c['hwnd'],point(c,bag,slot),point(c,trade,offer_index));time.sleep(.5)
            if int.from_bytes(source_record[:4],'little')>1:
                dialog=wait_until(lambda:widget(c,0x232dd0),8,'QUANTITY_DIALOG_NOT_OPEN')
                require(number(c,c['ui']+0x23d5e4)==5,'QUANTITY_NOT_TRADE_MODE5')
                control(c,dialog,4);type_ascii(c['hwnd'],'\b'*9+str(quantity));time.sleep(.4)
                require(number(c,c['ui']+0x23d5e8)==quantity,'NATIVE_QUANTITY_NOT_EDITED');control(c,dialog,2)
            own=bytes([quantity,slot])+source_record[2:4]+metadata
            other=bytes([quantity,offer_index,0,0])+metadata
            def offered():
                observed={'self_raw24':exact(c,c['ui']+0x866e8+offer_index*24,24).hex(),'peer_raw24':exact(peer,peer['ui']+0x867a8+offer_index*24,24).hex()}
                result['last_offer_projection_observation']=observed
                return observed if observed=={'self_raw24':own.hex(),'peer_raw24':other.hex()} else None
            proof=wait_until(offered,8,'SELF_SOURCE_OR_PEER_OFFER_INDEX_FULL20_MISMATCH')
            require(saved()==before,'TRANSIENT_OFFER_CHANGED_DURABLE_ROWS')
            result['events'].append({'operation':'offer2A','source':c['identity'],'slot':slot,'quantity':quantity,'offer_index':offer_index,'full20_verified':True,'self_source_slot':slot,'peer_offer_index':offer_index,'expected_self24':own.hex(),'expected_peer24':other.hex(),'observed':proof});save()
        def confirm(c,money,settles=False):
            trade=widget(c,0x232dae);require(trade is not None,'TRADE_NOT_OPEN_FOR_CONFIRM')
            control(c,trade,12);type_ascii(c['hwnd'],'\b'*9+str(money));time.sleep(.3)
            control(c,trade,11);dialog=wait_until(lambda:widget(c,0x232de6),8,'TRADE_CONFIRM_MODAL_MISSING')
            require(number(c,c['ui']+0x23d5d8)==2,'TRADE_CONFIRM_WRONG_MODE')
            before_confirm=saved();before_peer=snap(c)['peer'];before_requests=log.read_text('utf-8',errors='replace').count('NATIVE_TRADE_REQUEST')
            control(c,dialog,0)
            peer=next(row for row in clients if row is not c)
            def money_seen():
                current=snap(peer)
                if current['peer_labels'] is not None and str(money).encode('ascii') in bytes.fromhex(current['peer_labels']['money']['text_bytes_hex']):
                    return 'native51_label_observed'
                if settles and current['trade_widget'] is None:return 'settlement_closed_before_label_observation'
                return None
            try:observation=wait_until(money_seen,8,'PEER_51_MONEY_NOT_DISPLAYED')
            except RuntimeError:
                current=snap(c);checkpoint=input_checkpoint(c,dialog,0,'confirm_not_sent_same_live_control_read')
                require(log.read_text('utf-8',errors='replace').count('NATIVE_TRADE_REQUEST')==before_requests and saved()==before_confirm and current['money_sent']==0 and current['confirmed']==0 and current['peer']==before_peer==peer['identity'] and widget(c,0x232de6)==dialog and number(c,c['ui']+0x23d5d8)==2,'CONFIRM_REPOINT_REPLAY_OR_STATE_CHANGE_FORBIDDEN')
                result['events'].append({'operation':'same_native_confirm_modal_legal_repoint_no_request','source':c['identity'],'native':current,'db':saved(),'checkpoint':checkpoint});save()
                control(c,dialog,0)
                observation=wait_until(money_seen,8,'CONFIRM_MODAL_STILL_NOT_SENT_AFTER_NATIVE_HIT_REPOINT')
            result['events'].append({'operation':'confirm2B2C','source':c['identity'],'amount':money,
                                     'peer_money_observation':observation,'native':[snap(row) for row in clients]});save()
        def closed():return all(widget(c,0x232dae) is None and snap(c)['active']==0 for c in clients)
        def matrix(source,target,slots,amounts,settle,whole_med=False):
            prior=saved();order=[source['identity'],target['identity']];offers={}
            opened(source,target)
            for c,peer in ((source,target),(target,source)):
                scalar={r[1]:r for r in prior['diagnostic_inventory_slots'] if r[0]==c['identity']}
                offers[c['identity']]=[[slot,scalar[slot][3] if whole_med else min(scalar[slot][3],2 if c['identity']==4 else 3)] if scalar[slot][2]==3107 else [slot,1] for slot in slots]
                for index,(slot,quantity) in enumerate(offers[c['identity']]):offer(c,peer,slot,quantity,index)
            confirm(source,amounts[source['identity']])
            if not settle:
                control(target,widget(target,0x232dae),10);wait_until(closed,8,'CANCEL2D_NOT_CLOSED')
                restored=wait_until(lambda:consistent(prior),8,'CANCEL_FULL50_WALLET_NOT_RESTORED')
                require(restored['db']==prior,'CANCEL_CHANGED_ANY_DURABLE_ROW');guards=instance_guard()
                result['events'].append({'operation':'cancel2D','requester':source['identity'],'source':target['identity'],'offers':offers,'after':restored,'guards':guards,'all_saved_rows_unchanged':True,'full_native_restored':True});save();return
            expected,proof=expected_trade(prior,order,offers,amounts)
            confirm(target,amounts[target['identity']],settles=True);wait_until(closed,8,'CONFIRM2C_NOT_SETTLED')
            settled=wait_until(lambda:consistent(expected),8,'SETTLED_FULL50_METADATA_REVISION_PROVENANCE_MISMATCH')
            old={r[0] for r in prior['character_owned_instance_trade_receipts']};receipts=[r for r in settled['db']['character_owned_instance_trade_receipts'] if r[0] not in old]
            require(len(receipts)==1 and len(settled['db']['character_owned_instance_trade_receipts'])==len(old)+1,'ONE_EXACT_NEW0069_RECEIPT_REQUIRED')
            receipt=receipts[0];require(receipt[1:5]==[order[0],order[0],order[1],order[1]] and receipt[-1]=='CUSTOM-0069','RECEIPT_OWNER_DESIGN_MISMATCH')
            require({k:json.loads(receipt[5+i]) for i,k in enumerate(('before_state','after_state','offers_state'))}==proof,'EXACT_RECEIPT_FULL50_OFFERS_OR_TRANSFERS_MISMATCH')
            markers=[line for line in log.read_text('utf-8',errors='replace').splitlines() if 'NATIVE_TRADE_REQUEST' in line and 'committed=true rejected=false CUSTOM-0069' in line]
            require(len(markers)==len([e for e in result['events'] if e['operation']=='settle'])+1,'REAL_APPLICATION0069_COMMIT_MARKER_REQUIRED')
            guards=instance_guard();result['events'].append({'operation':'settle','requester':source['identity'],'offers':offers,'money':amounts,'independently_expected':proof,'receipt':receipt,'actual_receipt':{k:json.loads(receipt[5+i]) for i,k in enumerate(('before_state','after_state','offers_state'))},'before_expected':proof['before_state'],'after_expected':proof['after_state'],'offers_expected':proof['offers_state'],'after':settled,'guards':guards,'application_marker':markers[-1],'independent_plan_verified':True,'full50_verified':True,'provenance_preserved':True,'equipped_preserved':True,'other_players_unchanged':True,'receipt_verified':True,'physical_revisions_verified':True,'whole_instance_conservation':True});save()
        require('OWNED_INSTANCE_TRADE_ENABLED CUSTOM-0069 full_instance no_grants no_formula' in log.read_text('utf-8',errors='replace'),'REAL_APPLICATION0069_STARTUP_REQUIRED')
        initial_slots=[0,1,8,9,10,12,5]
        for source,target in ((first,other),(other,first)):matrix(source,target,initial_slots,{4:50,5:20},False)
        matrix(first,other,initial_slots,{4:100,5:40},True)
        matrix(other,first,[0,1,2,3,4,6,7],{4:40,5:100},True,whole_med=True)
        durable=saved();opened(first,other);wait_until(lambda:consistent(durable),8,'REOPEN_FULL50_PERSISTENCE_MISMATCH')
        control(other,widget(other,0x232dae),10);wait_until(closed,8,'REOPEN_CANCEL_NOT_CLOSED')
        wait_until(lambda:consistent(durable),8,'REOPEN_CANCEL_RESTORE_MISMATCH');require(saved()==durable,'REOPEN_CHANGED_DURABLE_ROWS')
        result['events'].append({'operation':'durability_reopen','full50_verified':True,'before':durable,'after':saved()})
        old_client_pids=[c['process'].pid for c in clients]
        for c in reversed(clients):close(c)
        require(not any(psutil.pid_exists(pid) for pid in old_client_pids),'FIRST_CLIENT_GENERATION_NOT_CLOSED')
        clients.clear()
        first=launch(4,950);other=launch(5,936)
        for c,peer in ((first,other),(other,first)):
            wait_until(lambda:base.peer.remote(c['handle'],c['ui'],peer['identity']),15,'RELOGIN_PEER_NOT_VISIBLE')
        relogin=wait_until(lambda:consistent(durable),12,'RELOGIN_FULL50_WALLET_OR_METADATA_NOT_RESTORED')
        require(saved()==durable,'RELOGIN_CHANGED_DURABLE_ROWS');relogin_guards=instance_guard()
        new_client_pids=[c['process'].pid for c in clients]
        require(len(new_client_pids)==2 and not set(new_client_pids).intersection(old_client_pids),'REAL_NEW_CLIENT_GENERATION_REQUIRED')
        result['events'].append({'operation':'relogin_full50','owners':[4,5],'languages':{'4':950,'5':936},'old_client_pids':old_client_pids,'new_client_pids':new_client_pids,'old_clients_closed':True,'both_owner_saved_equal':True,'full20_verified':True,'full50_verified':True,'before':durable,'after':saved(),'native':relogin['native'],'guards':relogin_guards})
        result['final']={'native':[snap(c) for c in clients],'db':saved(),'guards':instance_guard()}
        result['scenario_counts']={key:sum(e['operation']==key for e in result['events']) for key in ('cancel2D','settle','open29','offer2A','durability_reopen','relogin_full50')}
        require(result['scenario_counts']=={'cancel2D':2,'settle':2,'open29':5,'offer2A':56,'durability_reopen':1,'relogin_full50':1},'SAME_RUN_BOTH_DIRECTION_FULL_INSTANCE_MATRIX_REQUIRED')
        require(sum(r[1] for r in result['final']['db']['character_trade_wallets'] if r[0] in(4,5))==3000,'TRADE_MONEY_CONSERVATION')
        require(sum(r[3] for r in result['final']['db']['diagnostic_inventory_slots'] if r[0] in(4,5) and r[1]<30 and r[2]==3107)==18,'MED_QUANTITY_CONSERVATION')
        result['scope']=SCOPE;result['unrelated_saved_rows_preserved']=True;result['accepted']=True
    except BaseException as error:
        result.update(error=str(error),traceback=traceback.format_exc())
        try:
            result['failure_native']=[snap(c) for c in clients if c.get('handle')]
            result['failure_saved']=saved()
            result['failure_full50']=consistent()
        except Exception as checkpoint_error:result['failure_checkpoint_error']=str(checkpoint_error)
    finally:
        for c in reversed(clients):
            try:close(c)
            except Exception as error:result.setdefault('cleanup_errors',[]).append(str(error))
        for loader in loaders:
            if loader.poll() is None:loader.terminate();loader.wait(timeout=5)
        result['desktop_unchanged']=before==desktop_names();result['all_clients_closed']=not any(psutil.pid_exists(pid) for pid in result.get('owned_client_pids',[]))
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
    require(base.sha(args.server_candidate)==candidate_sha(),'IMMUTABLE_0069_CANDIDATE')
    source_before=source_guards();desktop_before=desktop_names()
    protected={str(p.pid):{'exe':p.info['exe'],'created':p.info['create_time']} for p in psutil.process_iter(['exe','create_time']) if p.info['exe'] and Path(p.info['exe']).name.lower() in ('god2.exe','god2-server.exe','leproc.exe','private_desktop_runner.exe')}
    frozen={str(path):base.sha(path) for path in (Path(__file__).resolve(),Path(base.__spec__.origin),Path(pose.__file__).resolve(),Path(world_hit.__file__).resolve(),ROOT/'tools/strike_lab/private_trade_armor_projection_20261002_v06.py',ROOT/'artifacts/playtests/private-native-blackbox-trade-armor-projection-20261002-06/run-result.json',ROOT/'artifacts/playtests/private-native-blackbox-trade-armor-projection-20261002-06/ui-result.json',ROOT/'tools/strike_lab/private_trade_20261002.py',ROOT/'tools/strike_lab/private_bank_armor_projection_20261002_v03.py',ROOT/'tools/strike_lab/private_armor_transfer_20261002.py',ROOT/'tools/strike_lab/private_inventory_move_ui.py',ROOT/'tools/strike_lab/private_trade_full_projection_20261003.py',ROOT/'tools/strike_lab/private_owned_foreign_bank_v02_20261003.py',CONTRACT,SOURCE_RUN/'ui-result.json',SOURCE_RUN/'run-result.json',SOURCE_RUN/'town-diagnostic-accounts.db',SOURCE_RUN/'server-config.json',ROOT/'artifacts/playtests/private-native-blackbox-armor-transfer-20261002-01/run-result.json')}
    os.environ['GOD2_NATIVE_WORLD_RECORDS_LAB']='1'
    qualify();script=Path(__file__).resolve();digest=base.sha(script);base.__file__=str(script);code=bounded_owner(args)
    receipt=args.output/'run-result.json'
    if receipt.exists():
        result=json.loads(receipt.read_text('utf-8'));result['trade_harness_sha256']=digest
        result['trade_harness_unchanged']=base.sha(script)==digest
        result['runtime_sources_before']=source_before;result['runtime_sources_after']=source_guards();result['runtime_sources_unchanged']=result['runtime_sources_before']==result['runtime_sources_after']
        result['frozen_files_before']=frozen;result['frozen_files_after']={path:base.sha(Path(path)) for path in frozen};result['frozen_files_unchanged']=result['frozen_files_before']==result['frozen_files_after']
        after={str(p.pid):{'exe':p.info['exe'],'created':p.info['create_time']} for p in psutil.process_iter(['exe','create_time']) if str(p.pid) in protected}
        result['protected_processes_before']=protected;result['protected_processes_preserved']=after==protected
        result['desktop_owner_before']=desktop_before;result['desktop_owner_after']=desktop_names();result['desktop_owner_unchanged']=desktop_before==result['desktop_owner_after']
        with socket.socket() as probe:result['exclusive2598_released']=probe.connect_ex(('127.0.0.1',2598))!=0
        pids=[result.get('server_pid'),result.get('runner_pid')]+result.get('ui',{}).get('owned_client_pids',[])
        result['owned_pid_terminal']={str(pid):{'pid_exists':psutil.pid_exists(pid)} for pid in pids if pid}
        result['control_layouts_verified']=all(Path(e['complete_active_layout_artifact']).exists() and base.sha(Path(e['complete_active_layout_artifact']))==e['complete_active_layout_sha256'] for e in result.get('ui',{}).get('events',[]) if e['operation']=='native_control_input_checkpoint')
        result['scope']=SCOPE
        result['accepted']=bool(result['accepted'] and result['trade_harness_unchanged'] and result['control_layouts_verified'] and result['runtime_sources_unchanged'] and result['frozen_files_unchanged'] and result['protected_processes_preserved'] and result['desktop_owner_unchanged'] and result['exclusive2598_released'] and not any(row['pid_exists'] for row in result['owned_pid_terminal'].values()));base.peer.dump(receipt,result)
        return 0 if result['accepted'] else 1
    return code
def bounded_owner(args):
    args.output=args.output.resolve();args.server_candidate=args.server_candidate.resolve()
    sources={'live_client':base.LIVE,'live_locale_profile':Path(str(base.LIVE)+'.le.config'),'source_database':base.SOURCE,
        'source_config':base.SOURCE.with_name('server-config.json'),'launcher_settings':base.LIVE.parent/'config/user.settings',
        'locale_global_config':base.LE.with_name('LEConfig.xml'),'locale_launcher':base.LE,'locale_loader':base.LE.with_name('LoaderDll.dll'),
        'locale_runtime':base.LE.with_name('LocaleEmulator.dll')}
    result={'accepted':False,'before':{k:base.sha(p) for k,p in sources.items()},'candidate_sha256':base.sha(args.server_candidate)};server=runner=None
    try:
        with socket.socket() as probe:require(probe.connect_ex(('127.0.0.1',base.PORT))!=0,'PRIVATE_PORT_ALREADY_USED')
        prepare(args);env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1';env.pop('GOD2_PRIVATE_SIDECAR_COMMAND',None)
        with (args.output/'stdout.log').open('wb') as log,(args.output/'runner.log').open('wb') as runnerlog:
            server=subprocess.Popen([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--run-for','720'],cwd=ROOT,env=env,
                stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);result['server_pid']=server.pid
            def listening():
                require(server.poll() is None,'PRIVATE_SERVER_EXITED')
                with socket.socket() as probe:return probe.connect_ex(('127.0.0.1',base.PORT))==0
            wait_until(listening,12,'PRIVATE_SERVER_NOT_LISTENING')
            runner=subprocess.Popen([str(base.RUNNER),sys.executable,'-X','utf8','-B',str(Path(__file__).resolve()),'--worker','--output',str(args.output),'--source-page',str(args.source_page)],cwd=ROOT,env=env,
                stdout=runnerlog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);result['runner_pid']=runner.pid
            result['runner_exit']=runner.wait(timeout=700);result['ui']=json.loads((args.output/'ui-result.json').read_text('utf-8'))
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
            result['private_files_unchanged']=all(base.sha(Path(value['path']))==value['sha256'] and base.sha(Path(value['profile']))==value['profile_sha256'] for value in clients.values())
            result['all_private_images_closed']=not any(process.info['exe'] and Path(process.info['exe']).resolve() in paths for process in psutil.process_iter(['exe']))
        result['after']={k:base.sha(p) for k,p in sources.items()};result['source_files_unchanged']=result['before']==result['after']
        result['candidate_unchanged']=base.sha(args.server_candidate)==result['candidate_sha256']
        result['all_owned_processes_closed']=(runner is None or runner.poll() is not None) and (server is None or server.poll() is not None)
        result['accepted']=bool(result['accepted'] and result['source_files_unchanged'] and result['candidate_unchanged'] and result['all_owned_processes_closed'] and result.get('private_files_unchanged') and result.get('all_private_images_closed'))
        if args.output.exists():base.peer.dump(args.output/'run-result.json',result)
    print(json.dumps({k:result.get(k) for k in ('accepted','error','candidate_sha256','source_files_unchanged','all_owned_processes_closed')}));return 0 if result['accepted'] else 1


if __name__=='__main__':raise SystemExit(main())
