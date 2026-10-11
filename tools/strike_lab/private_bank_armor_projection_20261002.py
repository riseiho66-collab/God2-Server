"""NEW bank rejection/MED regression with preserved armor, weapon and gem full20.

No foreground activation, screenshots, process-memory writes or packet injection.
Only disposable copies have their port changed. Saves are an isolated backup.
"""
import argparse,os,json,sqlite3,struct,sys,time,traceback,subprocess
from contextlib import closing
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]
import psutil,pefile
import private_armor_transfer_20261002 as armor_live
from tools.strike_lab import import_native_armor_20261002 as armor_catalog
import hashlib,re,socket
import private_peer_role_text_20260930 as base
import private_peer_pose_20261002 as pose
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,type_ascii,drag
base.CLIENT_SHA=pose.CLIENT_SHA


def qualify():
    raw=pose.qualify_source();mapped=pefile.PE(str(base.LIVE)).get_memory_mapped_image()
    regions=((0x5068c0,88),(0x41ea00,492),(0x49b720,80),(0x471610,336),(0x471d40,272),(0x4722b0,304),(0x4723a0,320),
             (0x497510,1040),(0x49f010,2200),(0x4c9a20,432),(0x4c9ed0,1808),(0x459a60,48),
             (0x471190,848),(0x471510,128),(0x471850,352),(0x4719b0,816),(0x471e10,1104),
             (0x497380,416),(0x496860,44),(0x498d70,89),(0x5077c0,138),
             (0x41e500,70),(0x426700,200),(0x426140,600),
             (0x46a68b,1027),(0x461510,240),(0x4618b0,208),(0x4cc380,1184))
    for va,size in regions:
        require(mapped[va-0x400000:va-0x400000+size]==raw[va-0x400000:va-0x400000+size],
                'NATIVE_BANK_CODE_CHANGED_'+hex(va))
    return {'current_client_sha256':base.sha(base.LIVE),'regions':regions,
            'open':'NPC world click ->37 target -> server46 mode0; fixture CUSTOM_TEST, not native placement',
            'items':'bank slot controls0..49; bag slots5..7; actual drag63/64 and mode2/3 quantity; 65 tail1 whole swap',
            'close':'bank control54 ->471390 ->39 targetWORD/type1; localclose before queue',
            'money_label':'bank232DD2 label0 via native5077C0 renderer; purseUI85604, bankUI839C4'}


original_prepare=base.prepare

def prepare(args):
    original_prepare(args)
    database=args.output/'town-diagnostic-accounts.db'
    config=json.loads((args.output/'server-config.json').read_text('utf-8'))
    config['world']['clock']={'enabled':False};config['world']['owned_supply']={'enabled':True}
    base.peer.dump(args.output/'server-config.json',config)
    from tools.strike_lab.discard_fixture_27_20261002 import copy_catalog
    from tools.strike_lab.bank_fixture_catalog_20261002 import copy_npc_catalog
    with closing(sqlite3.connect(database)) as db:
        base.peer.dump(args.output/'catalog-source.json',copy_catalog(db))
        base.peer.dump(args.output/'npc-catalog-source.json',copy_npc_catalog(db))
    # Candidate owns its schemas. Only a fresh disposable DB is seeded.
    with (args.output/'bank-schema-startup.log').open('wb') as log:
        subprocess.run([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--run-for','1'],
                       cwd=ROOT,check=True,timeout=25,stdout=log,stderr=subprocess.STDOUT,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    raw=bytes.fromhex(args.npc_hex)
    # Preserve the exact old native accepted sprite/type/facing/opaque body;
    # only explicit custom test coordinates differ from that old test operand.
    require(len(raw)==21 and raw[:17]==bytes.fromhex('72d10e000058660000a1000000cf010000'),'BANK_NPC_FIXTURE_INVALID')
    target=int.from_bytes(raw[1:5],'little')
    require((int.from_bytes(raw[17:21],'little')>>2)&0x7fff==128 and int.from_bytes(raw[17:21],'little')>>17==126,'BANK_NPC_FIXTURE_WRONG_COORDINATES')
    with closing(sqlite3.connect(database)) as db:
        db.execute('pragma foreign_keys=on')
        for identity in (4,5):
            db.execute("insert into character_trade_wallets(character_id,amount,revision,design_id) values(?,1000,1,'CUSTOM-0063') "
                       "on conflict(character_id) do update set amount=1000,revision=1",(identity,))
            db.execute("insert into character_bank_balances(character_id,amount,revision,design_id) values(?,0,1,'CUSTOM-0064') "
                       "on conflict(character_id) do update set amount=0,revision=1",(identity,))
        for identity,count in ((4,10),(5,8)):
            db.execute('delete from character_weapon_slot_metadata where character_id=? and slot<30',(identity,))
            db.execute('delete from diagnostic_inventory_slots where character_id=? and slot<30',(identity,))
            for slot in range(30):
                db.execute("insert into diagnostic_inventory_slots(character_id,slot,item_id,count,revision,source_sha256,design_id) values(?,?,?,?,1,?,'CUSTOM-0015')",
                    (identity,slot,3107 if slot==5 else 0,count if slot==5 else 0,
                     '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'))
        db.execute('update recovered_positions set x=129,y=126 where character_id=5')
        db.execute('insert into world_display_records values(4,3,114,?,?,?,?,?)',
                   (target,raw,'ISOLATED_TEST_ONLY','explicit private banker CUSTOM_TEST not native location',base.MAPPED_SHA))
        db.execute("insert into world_bank_service_points values(4,3,114,?,'ISOLATED_TEST_ONLY','explicit private banker','CUSTOM-0064')",(target,))
        db.commit();require(db.execute('pragma quick_check').fetchone()==('ok',),'PRIVATE_DB_INVALID')
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'))
    fixture['bank_fixture']={'wallets':{'4':1000,'5':1000},'bank':{'4':0,'5':0},'npc':raw.hex(),
                            'npc_position':[128,126],'npc_target':target,'authority':'CUSTOM_TEST_NOT_NATIVE',
                            'sprite_prior_acceptance':'private-native-blackbox-20260927-02/03/14 native3793 sprite14 rendereractive resource45',
                            'sprite_prior_raw':'72d10e000058660000a1000000cf010000f001fc00'}
    fixture['bank_items_fixture']={'item':3107,'counts':{'4':10,'5':8},'source_slot':5,'design':'CUSTOM-0065_SCALAR_OCCUPIED_SWAP'}
    base.peer.dump(args.output/'fixture.json',fixture)
bank_prepare=prepare

def prepare(args):
    require(base.sha(args.server_candidate)==CANDIDATE_SHA,'IMMUTABLE_BANK_ARMOR_CANDIDATE')
    bank_prepare(args)
    database=args.output/'town-diagnostic-accounts.db'
    config=json.loads((args.output/'server-config.json').read_text('utf-8'))
    config['world']['owned_armor_transfers']={'enabled':True}
    base.peer.dump(args.output/'server-config.json',config)
    source=json.loads((ARMOR_RUN/'run-result.json').read_text('utf-8'))
    initial={row['identity']:row['saved'] for row in source['ui']['logins'][:2]}
    with closing(sqlite3.connect(database)) as db:
        db.execute('pragma foreign_keys=on')
        require(db.execute("select name from schema_migrations where version=42").fetchone()==('owned_armor_instances',),'REAL_SCHEMA42_REQUIRED')
        armor_catalog.import_catalog(db,records=armor_catalog.cached_records(armor_catalog.RECORDS))
        weapon=db.execute('select logical20,origin,provenance,source_sha256,client_sha256,design_id from character_weapon_slot_metadata where character_id=4 and slot=34').fetchone()
        require(weapon and weapon[3]==armor_live.SOURCE_SHA and weapon[4]==WEAPON_CLIENT_SHA and weapon[5]=='CUSTOM-0046','ACCEPTED_WEAPON_FIXTURE_PINS')
        for identity in (4,5):
            for slot,original in ((0,0),(1,1),(30,30),(31,5),(32,6),(33,7)):
                row=initial[identity][str(original)];raw=bytes.fromhex(row['metadata'])
                family=2 if identity==4 else 26
                require(raw[2]&63==family and row['client']==armor_live.CLIENT_SHA,'EXACT_ARMOR_FAMILY_AND_CLIENT')
                db.execute("insert into diagnostic_inventory_slots values(?,?,?,?,1,?,'CUSTOM-0015') on conflict(character_id,slot) do update set item_id=excluded.item_id,count=1,revision=1,source_sha256=excluded.source_sha256,design_id=excluded.design_id",(identity,slot,row['item'],1,armor_live.SOURCE_SHA))
                db.execute("insert into character_armor_slot_metadata values(?,?,?,1,'CUSTOM_TEST_NOT_NATIVE',?,?,?,'CUSTOM-0066')",(identity,slot,raw,'bank-armor-run02 accepted run01 CUSTOM_TEST fixture originalslot='+str(original),armor_live.SOURCE_SHA,armor_live.CLIENT_SHA))
            raw=weapon[0];key=int.from_bytes(raw[:2],'little')
            db.execute("update diagnostic_inventory_slots set item_id=?,count=1,revision=1 where character_id=? and slot=8",(key,identity))
            db.execute("insert into character_weapon_slot_metadata values(?,?,?,1,'CUSTOM_TEST_NOT_NATIVE',?,?,?,'CUSTOM-0046')",(identity,8,raw,'bank-armor-run02 accepted weapon34 fixture; no stat/drop claim',armor_live.SOURCE_SHA,WEAPON_CLIENT_SHA))
            db.execute("update diagnostic_inventory_slots set item_id=16055,count=1,revision=1 where character_id=? and slot=12",(identity,))
            db.execute("insert into character_teleport_gem_metadata values(?,?,?,1,'CUSTOM_TEST_NOT_NATIVE',?,?,'CUSTOM-0057')",(identity,12,GEM_META,'bank-armor-run02 accepted teleport gem20 fixture; no teleport action',armor_live.SOURCE_SHA))
        db.commit()
        require(db.execute('pragma quick_check').fetchone()==('ok',) and db.execute('pragma foreign_key_check').fetchone() is None,'BANK_ARMOR_PRIVATE_DB_INTEGRITY')
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'))
    fixture['armor_bank_fixture']={'authority':'CUSTOM_TEST_NOT_NATIVE','armor_slots':[0,1,30,31,32,33],'weapon_bag_slot':8,'gem_slot':12,'gem_meta':GEM_META.hex(),'med_item':3107,'med_counts':{'4':10,'5':8},'weapon_client_sha256':WEAPON_CLIENT_SHA,'armor_client_sha256':armor_live.CLIENT_SHA,'candidate_sha256':CANDIDATE_SHA,'source_contract':source_guards()}
    base.peer.dump(args.output/'fixture.json',fixture)
base.prepare=prepare


CANDIDATE_SHA='2696f4efc90648aac47df97e5dbbe80cfd1434cac936f2db36c5ec98ff6ad3d3'
WEAPON_CLIENT_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
GEM_META=bytes.fromhex('b73e0804')+bytes(16)
ARMOR_RUN=ROOT/'artifacts/playtests/private-native-blackbox-armor-transfer-20261002-01'
CONTRACT=ROOT/'artifacts/research/native-armor-transfer-20261002/candidate-01/contract.json'

def source_guards():
    contract=json.loads(CONTRACT.read_text('utf-8'))
    actual={key:base.sha(ROOT/key) for key in contract['source_sha256']}
    require(actual==contract['source_sha256'],'BANK_ARMOR_RUNTIME20_PINS')
    return actual

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
    def hit_layout(c):
        manager=c['ui']+0xe2170;mouse=number(c,manager+4);node=number(c,manager+0x14)
        require(mouse>0x10000,'BANK_HIT_MOUSE_MISSING')
        rectangles=exact(c,mouse,0xc00*24);rows=[];seen=set()
        while node:
            require(node not in seen and len(seen)<128,'BANK_HIT_LIST_CYCLE');seen.add(node)
            w=number(c,node,2,True);require(0<=w<128,'BANK_HIT_LIST_WIDGET_INVALID')
            flags=number(c,manager+w*0x2a08+0x818,2)
            if flags&0x20:
                header=number(c,node+8,2,True)
                if 0<=header<0xc00:
                    active,left,top,right,bottom,inside=struct.unpack_from('<6i',rectangles,header*24)
                    if active:rows.append({'widget':w,'index':-1,'header':True,'widget_flags':flags,'hit_id':header,'rect':[left,top,right,bottom],'inside_last_mouse':inside})
                controls=exact(c,manager+w*0x2a08+0x8b8,106*100)
                for i in range(106):
                    r=controls[i*100:(i+1)*100];hit=int.from_bytes(r[8:10],'little',signed=True)
                    if not r[0] or not 0<=hit<0xc00:continue
                    active,left,top,right,bottom,inside=struct.unpack_from('<6i',rectangles,hit*24)
                    if active:rows.append({'widget':w,'index':i,'flags':r[0],'type4':int.from_bytes(r[4:8],'little'),
                        'widget_flags':flags,'hit_id':hit,'rect':[left,top,right,bottom],'inside_last_mouse':inside})
            node=number(c,node+0xc)
        return rows
    def hits(rows,xy):
        x,y=xy;matches=[r for r in rows if r['rect'][0]<=x<=r['rect'][2] and r['rect'][1]<=y<=r['rect'][3]]
        headers=[r for r in matches if r.get('header')]
        if not headers:return []
        front=headers[0];controls=[r for r in matches if r['widget']==front['widget'] and not r.get('header')]
        return (controls or [front])+[r for r in matches if r['widget']!=front['widget']]
    def unobscured_bank_point(c,w,index):
        point(c,w,index);rect=result['last_control']['rect'];left,top,right,bottom=rect
        rows=hit_layout(c);options=[]
        for fy in (.2,.5,.8):
            for fx in (.2,.5,.8):
                xy=(round(left+(right-left)*fx),round(top+(bottom-top)*fy));intersections=hits(rows,xy)
                options.append({'point':xy,'hits':intersections})
        eligible=[v for v in options if v['hits'] and v['hits'][0]['widget']==w and v['hits'][0]['index']==index]
        result['events'].append({'operation':'65_target_hit_selection','identity':c['identity'],'widget':w,'index':index,'options':options});save()
        require(eligible,'BANK_OCCUPIED_TARGET_FULLY_OBSCURED_BY_NATIVE_INPUT')
        chosen=min(eligible,key=lambda v:len(v['hits']))['point'];return chosen
    def label(c,w,index):
        # 5077C0 ->41E500 ->426700 ->426140 native renderer/text chain.
        pool=number(c,c['ui']+0xe2178)
        renderer=number(c,c['ui']+0xe2170+w*0x2a08+0x81c,2,True)
        require(pool>0x10000 and 0<=renderer<4096,'BANK_LABEL_RENDERER_MISSING')
        command=number(c,pool+0x10+renderer*0x290+0xe,2)
        surface=number(c,pool+4);require(surface>0x10000 and command<5000,'BANK_LABEL_COMMAND_MISSING')
        text=number(c,surface+0x1264+command*200+index*2,2,True)
        require(0<=text<30000,'BANK_LABEL_TEXT_MISSING')
        raw=exact(c,surface+0xf66e4+text*0x8c,0x8c)
        return {'renderer':renderer,'command':command,'index':text,'raw_hex':raw.hex(),
                'text_bytes_hex':raw[12:].hex()}
    def icon(c,w,index,item):
        pool=number(c,c['ui']+0xe2178)
        renderer=number(c,c['ui']+0xe2170+w*0x2a08+0x81c,2,True)
        require(pool>0x10000 and 0<=renderer<4096,'BANK_ICON_RENDERER_MISSING')
        node=pool+0x10+renderer*0x290
        frame=number(c,node+0x180+index*2,2,True)
        command=number(c,node+0xac+index*2,2)
        require(command<5000,'BANK_ICON_COMMAND_MISSING')
        surface=number(c,pool+4)
        catalog=number(c,c['ui']+0xcff70)
        record=number(c,catalog+0xb2d40+item*4) if item else 0
        expected=number(c,record+0x118,2) if record else 0xffff
        if item:require(frame==expected and number(c,surface+0x12e4+command*200)>0,'BANK_ITEM_ICON_NOT_RENDERED')
        else:require(frame==-1,'BANK_EMPTY_ICON_NOT_CLEARED')
        return {'renderer':renderer,'command':command,'frame':frame,'item':item,'expected_frame':expected,
                'kind':number(c,record+0x116,2) if record else 0x41,
                'surface_resource':number(c,surface+0x12e4+command*200)}
    def cells(c,offset,count):
        raw=exact(c,c['ui']+offset,count*24)
        return [{'slot':i,'quantity':r[0],'source_slot':r[1],'item':int.from_bytes(r[4:6],'little'),'raw':r.hex()}
                for i in range(count) for r in [raw[i*24:(i+1)*24]]]
    def snap(c):
        bank=widget(c,0x232dd2);sidebar=widget(c,0x232dd4)
        return {'identity':c['identity'],'language':c['page'],'bank_widget':bank,'bag_widget':widget(c,0x232dc8),
                'bank_label':label(c,bank,0) if bank is not None else None,
                'page_label':label(c,bank,2) if bank is not None else None,
                'target':number(c,c['ui']+0x839c0),'mode':number(c,c['ui']+0x855ed,1),
                'bank':number(c,c['ui']+0x839c4),'purse':number(c,c['ui']+0x85604),
                'current_page':number(c,c['ui']+0x839a4),'edition_field_232f64':number(c,c['ui']+0x232f64),
                'page_cache':list(struct.unpack('<6I',exact(c,c['ui']+0x839a8,24))),
                'bag':cells(c,0x8560c,30),'vault':cells(c,0x839cc,300),
                'sidebar_widget':sidebar,'selected_bank_slot':number(c,c['ui']+0x83994,2,True),'selected_bag_slot':number(c,c['ui']+0x855f0,2,True),
                'cursor_mode':number(c,c['ui']+0x232f36,2),'quantity_widget':widget(c,0x232dd0)}
    def saved():
        with closing(base.peer.ro(database)) as db:
            return {'wallets':[list(r) for r in db.execute('select character_id,amount,revision from character_trade_wallets order by character_id')],
                    'bank_money':[list(r) for r in db.execute('select character_id,amount,revision from character_bank_balances order by character_id')],
                    'bag':[list(r) for r in db.execute('select character_id,slot,item_id,count,revision from diagnostic_inventory_slots where character_id in(4,5) and slot<30 order by character_id,slot')],
                    'vault':[list(r) for r in db.execute('select character_id,slot,item_id,count,revision from character_bank_item_slots order by character_id,slot')],
                    'receipts':[list(r) for r in db.execute('select * from character_bank_item_receipts order by receipt')]}
    def untouched():
        with closing(base.peer.ro(database)) as db:
            return {name:sorted(repr(row) for row in db.execute('select * from "'+name.replace('"','""')+'"'))
                    for name, in db.execute("select name from sqlite_master where type='table' order by name")
                    if name not in ('diagnostic_inventory_slots','character_bank_item_slots','character_bank_item_receipts')}
    def instances(c):
        with closing(base.peer.ro(database)) as db:
            tables={name:[list(row) for row in db.execute('select * from '+name+' where character_id=? order by slot',(c['identity'],))] for name in ('character_armor_slot_metadata','character_weapon_slot_metadata','character_teleport_gem_metadata')}
            slots=sorted({row[1] for rows in tables.values() for row in rows})
            scalar=[list(db.execute('select * from diagnostic_inventory_slots where character_id=? and slot=?',(c['identity'],slot)).fetchone()) for slot in slots]
        native={str(slot):exact(c,c['ui']+0x8560c+slot*24,24).hex() for slot in slots}
        for name,rows in tables.items():
            for row in rows:
                current=next(value for value in scalar if value[1]==row[1])
                require(current[3]==1 and current[4]==row[3] and current[5]==armor_live.SOURCE_SHA,'INSTANCE_SCALAR_META_REVISION')
                require(native[str(row[1])]==(struct.pack('<I',1)+row[2]).hex(),'BANK_OWNER_INSTANCE_FULL20_NOT_PRESERVED')
                row[2]=row[2].hex()
        return {'tables':tables,'scalar':scalar,'native':native}
    def unchanged_instances():
        for owner in clients:require(instances(owner)==owner['instance_baseline'],'BANK_CHANGED_ARMOR_WEAPON_OR_GEM_FULL20')
        require(source_guards()==fixture['armor_bank_fixture']['source_contract'],'BANK_RUNTIME20_CHANGED')
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
        require('OWNED_ARMOR_TRANSFERS_ENABLED' in log.read_text('utf-8',errors='replace'),'ACTUAL_ARMOR_ENABLED_STARTUP_MISSING')
        for owner in clients:owner['instance_baseline']=instances(owner)
        invariant=untouched();result['initial']={'native':[snap(c) for c in clients],'db':saved(),'instances':[c['instance_baseline'] for c in clients]};save()
        def owner_rows(identity):
            d=saved();return {k:[r for r in d[k] if r[0]==identity] for k in ('bag','vault')}
        for c in clients:
            require(snap(c)['purse']==1000,'WALLET_27_NOT_LOADED')
            count=fixture['bank_items_fixture']['counts'][str(c['identity'])]
            require(snap(c)['bag'][5]['item']==3107 and snap(c)['bag'][5]['quantity']==count,'BAG_NOT_LOADED')
            native_npc=wait_until(lambda:base.owned.native_world_records(c['handle'],c['ui']).get('npc'),8,'BANK_NPC_NATIVE_RENDERER_UNAVAILABLE')
            require(native_npc['identity']==fixture['bank_fixture']['npc_target'] and
                    [native_npc['x'],native_npc['y']]==[128,126] and native_npc['renderer_active'],
                    'BANK_NPC_WRONG_NATIVE_INSTANCE')
            result.setdefault('qualified_native_npc',[]).append(native_npc);save()
            def opened():
                state=base.ground.world_state(c['handle'],c['ui'])
                px,py=base.ground.ground_point(c['handle'],state,128,126);click(c['hwnd'],px,py-26)
                wait_until(lambda:widget(c,0x232dd2) is not None,8,'BANK_NOT_OPEN_BY_NPC37')
                now=snap(c);require(now['target']==fixture['bank_fixture']['npc_target'] and now['mode']==0,'WRONG_BANK_CONTEXT')
                wait_until(lambda:all(snap(c)['page_cache'][:3]),8,'BANK_SNAPSHOT_CACHE_NOT_LOADED')
                result['events'].append({'operation':'NPC37_bank_open','native':snap(c),'db':saved()});save()
            opened()
            if widget(c,0x232dc8) is None:click(c['hwnd'],708,584);time.sleep(.5)
            wait_until(lambda:widget(c,0x232dc8) is not None,8,'BAG_NOT_OPEN')
            peer=next(row for row in clients if row is not c)
            with closing(base.peer.ro(database)) as db:
                expected_bag={i:(item,qty) for i,item,qty in db.execute('select slot,item_id,count from diagnostic_inventory_slots where character_id=? and slot<30 order by slot',(c['identity'],))}
            require(expected_bag[5]==(3107,count) and expected_bag[12]==(16055,1),'MED_GEM_MUST_NOT_BE_ARMOR')
            expected_vault={i:(0,0) for i in range(300)}
            def consistent():
                now=snap(c);d=saved()
                if now['purse']!=1000 or now['bank']!=0:return None
                for key,expected in (('bag',expected_bag),('vault',expected_vault)):
                    for row in now[key]:
                        if (row['item'],row['quantity'])!=expected[row['slot']]:return None
                    owned=[r for r in d[key] if r[0]==c['identity']]
                    if len(owned)!=len(expected):return None
                    if any((r[2],r[3])!=expected[r[1]] for r in owned):return None
                return {'native':now,'db':d}
            wait_until(consistent,8,'BANK_INITIAL_NATIVE_STORAGE_MISMATCH')
            # Actual source0 armor -> bank4 real drag63, no quantity prompt.
            before_reject=saved();before_native=snap(c);before_instances=instances(c)
            reject_lines=[line for line in log.read_text('utf-8',errors='replace').splitlines() if 'NATIVE_BANK_ITEM_REQUEST' in line and 'rejected=1' in line]
            start=point(c,widget(c,0x232dc8),0);end=point(c,widget(c,0x232dd2),4)
            result['events'].append({'operation':'armor63_attempt','identity':c['identity'],'source':0,'destination':4,'points':[start,end],'before_native':before_native,'before_db':before_reject,'before_instances':before_instances});save()
            drag(c['hwnd'],start,end)
            def actual_rejected():
                lines=[line for line in log.read_text('utf-8',errors='replace').splitlines() if 'NATIVE_BANK_ITEM_REQUEST' in line and 'rejected=1' in line]
                return lines[-1] if len(lines)==len(reject_lines)+1 else None
            rejection=wait_until(actual_rejected,12,'ARMOR_BANK63_REAL_SERVER_REJECTION_MISSING')
            wait_until(lambda:saved()==before_reject and snap(c)['bag']==before_native['bag'] and snap(c)['vault']==before_native['vault'],8,'ARMOR_BANK_REJECTION_ROLLBACK_NOT_CANONICAL')
            require(instances(c)==before_instances,'ARMOR_BANK_REJECTION_LOST_FULL_OWNER_STATE')
            unchanged_instances();require(untouched()==invariant,'ARMOR_BANK_REJECTION_CHANGED_SAVES')
            result['events'].append({'operation':'armor63_rejected','identity':c['identity'],'server_marker':rejection,'source':0,'destination':4,'all_saved_rows_unchanged':True,'full30bag24_and_instances_unchanged':True,'after_native':snap(c),'after_db':saved()});save()
            # Normal close/open guarantees fresh native37 context, including
            # the case where server refusal intentionally retires the context.
            if widget(c,0x232dd2) is not None:
                control(c,widget(c,0x232dd2),54);wait_until(lambda:widget(c,0x232dd2) is None,5,'REJECT_CONTEXT_NATIVE_CLOSE_MISSING')
            opened();wait_until(consistent,8,'ARMOR_REJECT_BANK_REOPEN_FAILED')
            def change_page(index):
                control(c,widget(c,0x232dd2),56 if index>snap(c)['current_page'] else 55)
                require(snap(c)['current_page']==index,'BANK_PAGE_DID_NOT_CHANGE');time.sleep(.6)
                require(str(index+1).encode() in bytes.fromhex(snap(c)['page_label']['text_bytes_hex']),'BANK_PAGE_LABEL_NOT_RENDERED')
                result['events'].append({'operation':'page_arrow','page':index,'native':snap(c)});save()
            def operation(op,source,dest,quantity):
                time.sleep(.3);state=snap(c);page=state['current_page'];offset=page*50;prior_db=saved()
                prior_peer=owner_rows(peer['identity']);prior_peer_native=snap(peer);prior_peer_bag=prior_peer_native['bag'];prior_peer_vault=prior_peer_native['vault']
                source_count=(expected_bag[source] if op==0x63 else expected_vault[offset+source])[1]
                bag=widget(c,0x232dc8);bank=widget(c,0x232dd2)
                require(bag is not None and bank is not None,'BANK_OR_BAG_CLOSED')
                if op!=0x63:icon(c,bank,source,3107)
                start=point(c,bag if op==0x63 else bank,source)
                end=unobscured_bank_point(c,bank,dest) if op==0x65 else point(c,bag if op==0x64 else bank,dest)
                result['events'].append({'operation':'drag_start','opcode':op,'source':source,'destination':dest,'page':page,'quantity':quantity,'points':[start,end]});save()
                if op==0x65:
                    # Observe real input dispatch at each phase. No direct native
                    # calls or process-memory writes; occupied target may receive
                    # a distinct overlay handler from an empty target.
                    def checkpoint(phase):
                        now=snap(c)
                        result['events'].append({'operation':'65_gesture_checkpoint','phase':phase,
                            'native':{key:now[key] for key in ('identity','cursor_mode','selected_bank_slot','selected_bag_slot','bank_widget','bag_widget')},
                            'bank_coordinates':[number(c,c['ui']+offset,2,True) for offset in (0x83996,0x83998,0x8399a,0x8399c)],
                            'cells':[now['vault'][offset+source],now['vault'][offset+dest]],
                            'receipt_count':len(saved()['receipts']),
                            'mouse_flags':exact(c,number(c,c['ui']+0xcff68)+0x12014,28).hex(),
                            'bank_control_rows':[exact(c,c['ui']+0xe2170+bank*0x2a08+0x8b8+i*100,100).hex() for i in (source,dest)],
                            'destination_hits':hits(hit_layout(c),end) if phase in ('before_source','source_pressed','move_10') else []});save()
                    import ctypes
                    from ctypes import wintypes
                    rect=wintypes.RECT();require(base.peer.user.GetClientRect(c['hwnd'],ctypes.byref(rect)),'BANK_CLIENT_RECT_MISSING')
                    sx,sy=round(start[0]*rect.right/800),round(start[1]*rect.bottom/600)
                    ex,ey=round(end[0]*rect.right/800),round(end[1]*rect.bottom/600)
                    def message(code,key,x,y):
                        require(base.peer.user.PostMessageW(c['hwnd'],code,key,(y<<16)|x),'BANK_SWAP_MOUSE_MESSAGE_FAILED')
                        time.sleep(.25)
                    checkpoint('before_source')
                    message(0x200,0,sx,sy);message(0x201,1,sx,sy);checkpoint('source_pressed')
                    require(snap(c)['selected_bank_slot']==source,'BANK_SWAP_SOURCE_NOT_SELECTED')
                    end=unobscured_bank_point(c,bank,dest)
                    ex,ey=round(end[0]*rect.right/800),round(end[1]*rect.bottom/600)
                    result['events'].append({'operation':'65_actual_drop_point_after_source_tooltip','identity':c['identity'],'source':source,'destination':dest,'point':end});save()
                    for step in range(1,11):
                        message(0x200,1,sx+(ex-sx)*step//10,sy+(ey-sy)*step//10)
                        checkpoint('move_'+str(step))
                    message(0x202,0,ex,ey);checkpoint('destination_released')
                else:drag(c['hwnd'],start,end)
                time.sleep(.45)
                modal=None
                if op!=0x65 and source_count>1:
                    dialog=wait_until(lambda:widget(c,0x232dd0),8,'BANK_ITEM_QUANTITY_DIALOG_MISSING')
                    mode=number(c,c['ui']+0x23d5e4);require(mode==(2 if op==0x63 else 3),'BANK_QUANTITY_WRONG_MODE')
                    modal={'mode':mode,'maximum':number(c,c['ui']+0x23d5ec),'initial':number(c,c['ui']+0x23d5e8)}
                    require(modal['maximum']==source_count,'BANK_QUANTITY_WRONG_MAXIMUM')
                    control(c,dialog,4);type_ascii(c['hwnd'],'\b'*9+str(quantity));time.sleep(.3)
                    require(number(c,c['ui']+0x23d5e8)==quantity,'BANK_QUANTITY_NOT_EDITED');control(c,dialog,2)
                else:require(widget(c,0x232dd0) is None,'UNEXPECTED_QUANTITY_MODAL')
                if op==0x63:
                    expected_bag[source]=(3107,source_count-quantity) if source_count>quantity else (0,0)
                    expected_vault[offset+dest]=(3107,quantity)
                elif op==0x64:
                    expected_vault[offset+source]=(3107,source_count-quantity) if source_count>quantity else (0,0)
                    expected_bag[dest]=(3107,quantity)
                else:
                    require(quantity==1,'BANK65_TAIL_IS_MARKER_NOT_QUANTITY')
                    expected_vault[offset+source],expected_vault[offset+dest]=expected_vault[offset+dest],expected_vault[offset+source]
                try:after=wait_until(consistent,10,'BANK_ITEM_NATIVE_OR_DURABLE_MISMATCH')
                except RuntimeError:
                    now=snap(c)
                    result['failure_native']=now;result['failure_db']=saved();save()
                    # Retry only a native mouse gesture known not to have emitted a
                    # singleton64 mutation: byte-identical inventory plus identical
                    # durable snapshot/receipt set prevents replaying a committed op.
                    if not (saved()==prior_db and now['bag']==state['bag'] and now['vault']==state['vault'] and
                            widget(c,0x232dd0) is None):raise
                    if op==0x65 and now['cursor_mode']==1 and now['selected_bank_slot']==-1:
                        result['events'].append({'operation':'65_pending_cursor_destination_click_no_request','native':now});save()
                        click(c['hwnd'],*end)
                        after=wait_until(consistent,10,'BANK_OCCUPIED_NATIVE_CURSOR_CLICK_FAILED')
                    elif op==0x64 and source_count==1:
                        result['events'].append({'operation':'singleton_UI_retry_no_request','native':now});save()
                        drag(c['hwnd'],start,end)
                        after=wait_until(consistent,10,'BANK_SINGLETON_UI_RETRY_FAILED')
                    else:raise
                require(owner_rows(peer['identity'])==prior_peer and snap(peer)['bag']==prior_peer_bag and snap(peer)['vault']==prior_peer_vault,'BANK_ITEM_CHANGED_OTHER_OWNER')
                require(sum(r['quantity'] for key in ('bag','vault') for r in after['native'][key] if r['item']==3107)==count,'BANK_MED_NATIVE_CONSERVATION_FAILED')
                require(sum(r[3] for key in ('bag','vault') for r in after['db'][key] if r[0]==c['identity'] and r[2]==3107)==count,'BANK_MED_DURABLE_CONSERVATION_FAILED')
                rendered=[];sidebar=widget(c,0x232dd4)
                for slot in {source if op!=0x63 else dest,dest if op!=0x64 else source}:
                    qty=expected_vault[offset+slot][1]
                    if qty:
                        text=label(c,sidebar,slot);require(str(qty).encode() in bytes.fromhex(text['text_bytes_hex']),'BANK_SLOT_COUNT_NOT_RENDERED')
                        rendered.append({'slot':slot,'quantity':qty,'label':text,'icon':icon(c,bank,slot,3107)})
                    else:rendered.append({'slot':slot,'quantity':0,'icon':icon(c,bank,slot,0)})
                result['events'].append({'operation':hex(op),'source':source,'destination':dest,'page':page,'quantity':quantity,'modal':modal,'rendered':rendered,'after':after,'other_owner_unchanged':True,'native_and_durable_total':count});save()
                unchanged_instances();require(untouched()==invariant,'BANK_ITEMS_CHANGED_UNRELATED_ROWS')
            operation(0x63,5,2,3);operation(0x63,5,3,count-3)
            operation(0x65,2,3,1);operation(0x65,3,2,1);operation(0x65,2,3,1)
            operation(0x64,3,6,1);operation(0x64,3,7,2)
            change_page(1);operation(0x63,6,2,1);change_page(0)
            control(c,widget(c,0x232dd2),54);wait_until(lambda:widget(c,0x232dd2) is None,5,'BANK_CLOSE39_NOT_LOCAL')
            result['events'].append({'operation':'close39','identity':c['identity']});save()
            opened();wait_until(consistent,8,'BANK_REOPEN_SNAPSHOT_MISSING')
            operation(0x64,2,5,count-3);change_page(1);operation(0x64,2,6,1)
            edition=snap(c)['edition_field_232f64'];maximum=1 if edition==1 else 2
            if maximum==2:change_page(2)
            control(c,widget(c,0x232dd2),56);require(snap(c)['current_page']==0,'BANK_NEXT_WRAP_WRONG')
            control(c,widget(c,0x232dd2),55);require(snap(c)['current_page']==maximum,'BANK_PREVIOUS_WRAP_WRONG')
            result['events'].append({'operation':'page_wrap','identity':c['identity'],'edition_field_232f64':edition,'reachable_pages':list(range(maximum+1)),'native':snap(c)});save()
            control(c,widget(c,0x232dd2),54);wait_until(lambda:widget(c,0x232dd2) is None,5,'BANK_FINAL_CLOSE_MISSING')
            require(untouched()==invariant,'BANK_ITEMS_CHANGED_UNRELATED_SAVED_ROWS')
        result['final']={'native':[snap(c) for c in clients],'db':saved()}
        require(len(result['final']['db']['receipts'])==20,'BANK_SWAP_RECEIPTS_MISSING')
        unchanged_instances();result['final_instances']=[instances(c) for c in clients];result['unrelated_saved_rows_preserved']=True;result['accepted']=True
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
    parser.add_argument('--npc-hex',default='');parser.add_argument('--worker',action='store_true');parser.add_argument('--qualify-only',action='store_true');args=parser.parse_args()
    if args.qualify_only:print(json.dumps(qualify()));return 0
    if args.output is None:parser.error('--output required')
    if args.worker:return worker(args)
    if args.server_candidate is None:parser.error('--server-candidate required')
    if not args.npc_hex:parser.error('--npc-hex required for explicit qualified CUSTOM_TEST fixture')
    require(base.sha(args.server_candidate)==CANDIDATE_SHA,'NEW_IMMUTABLE_BANK_ARMOR_CANDIDATE')
    source_before=source_guards();desktop_before=desktop_names()
    protected={str(p.pid):{'exe':p.info['exe'],'created':p.info['create_time']} for p in psutil.process_iter(['exe','create_time']) if p.info['exe'] and Path(p.info['exe']).name.lower() in ('god2.exe','god2-server.exe','leproc.exe','private_desktop_runner.exe')}
    frozen={str(path):base.sha(path) for path in (Path(__file__).resolve(),Path(armor_live.__file__).resolve(),Path(armor_catalog.__file__).resolve(),Path(base.__spec__.origin),ROOT/'tools/strike_lab/private_bank_swap_20261002.py',ROOT/'tools/strike_lab/private_inventory_move_ui.py',CONTRACT,ARMOR_RUN/'run-result.json')}
    os.environ['GOD2_NATIVE_WORLD_RECORDS_LAB']='1' 
    qualify();script=Path(__file__).resolve();digest=base.sha(script);base.__file__=str(script);code=base.owner(args)
    receipt=args.output/'run-result.json'
    if receipt.exists():
        result=json.loads(receipt.read_text('utf-8'));result['bank_swap_harness_sha256']=digest
        result['bank_swap_harness_unchanged']=base.sha(script)==digest
        result['runtime20_before']=source_before;result['runtime20_after']=source_guards();result['runtime20_unchanged']=result['runtime20_before']==result['runtime20_after']
        result['frozen_files_before']=frozen;result['frozen_files_after']={path:base.sha(Path(path)) for path in frozen};result['frozen_files_unchanged']=result['frozen_files_before']==result['frozen_files_after']
        after={str(p.pid):{'exe':p.info['exe'],'created':p.info['create_time']} for p in psutil.process_iter(['exe','create_time']) if str(p.pid) in protected}
        result['protected_processes_before']=protected;result['protected_processes_preserved']=after==protected
        result['desktop_owner_before']=desktop_before;result['desktop_owner_after']=desktop_names();result['desktop_owner_unchanged']=result['desktop_owner_before']==result['desktop_owner_after']
        with socket.socket() as probe:result['exclusive2598_released']=probe.connect_ex(('127.0.0.1',2598))!=0
        pids=[result.get('server_pid'),result.get('runner_pid')]+result.get('ui',{}).get('owned_client_pids',[])
        result['owned_pid_terminal']={str(pid):{'pid_exists':psutil.pid_exists(pid)} for pid in pids if pid}
        result['scope']='REAL_BANK_ARMOR63_REJECTION_AND_NATIVE_MED63_64_65_WITH_ALL_ARMOR_WEAPON_GEM_FULL20_PRESERVED_CUSTOM_TEST_ONLY'
        result['accepted']=bool(result['accepted'] and result['bank_swap_harness_unchanged'] and result['runtime20_unchanged'] and result['frozen_files_unchanged'] and result['protected_processes_preserved'] and result['desktop_owner_unchanged'] and result['exclusive2598_released'] and not any(row['pid_exists'] for row in result['owned_pid_terminal'].values()));base.peer.dump(receipt,result)
        return 0 if result['accepted'] else 1
    return code
if __name__=='__main__':raise SystemExit(main())
