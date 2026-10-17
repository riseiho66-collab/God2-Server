# Legacy receipt identifiers retain their schema spelling; both cases are the
# Taiwan client using Traditional CP950 or Simplified CP936, not regional protocols.
"""NEW full20 foreign bank transport plus accepted armor12/MED20 regression.

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
from private_potion_ui import type_ascii
base.CLIENT_SHA=pose.CLIENT_SHA

ACCEPTED_ARMOR_TOOL=ROOT/'tools/strike_lab/private_owned_armor_bank_20261003.py'
ACCEPTED_ARMOR_SHA='bf1f8996508b7693fa984c9801f6ca7ad25ab5fc92dee1c993be7ab8d317a831'
WEAPON_RECORDS=ROOT/'artifacts/research/native-weapons-20260926/records.json'
ACCEPTED_ARMOR_RUN=ROOT/'artifacts/playtests/private-native-blackbox-owned-armor-bank-20261003-03'
FOREIGN_V01_TOOL=ROOT/'tools/strike_lab/private_owned_foreign_bank_20261003.py'
FOREIGN_RUN01=ROOT/'artifacts/playtests/private-native-blackbox-owned-foreign-bank-20261003-01'

def expected_physical_sources(before_owner,opcode,page,source,destination):
    """Derive transfer provenance from the two actual preoperation cells.

    Destination inherits source on a whole/partial transfer. The cleared or
    partially consumed source preserves its own SHA; occupied65 swaps SHAs.
    Physical cell design fields do not move. No output value is inferred from
    an after-state or relaxed to an arbitrary valid-looking source string.
    """
    source_cell=('diagnostic_inventory_slots',source) if opcode==0x63 else ('character_bank_item_slots',page*50+source)
    destination_cell=('diagnostic_inventory_slots',destination) if opcode==0x64 else ('character_bank_item_slots',page*50+destination)
    a=next(row for row in before_owner[source_cell[0]] if row[1]==source_cell[1])
    b=next(row for row in before_owner[destination_cell[0]] if row[1]==destination_cell[1])
    require(a[3]>0,'PHYSICAL_SOURCE_NOT_OCCUPIED')
    return {source_cell:b[5] if opcode==0x65 and b[3] else a[5],destination_cell:a[5]}

def native_foreign_record(storage,slot,metadata):
    require(storage in ('bag','vault') and len(metadata)==20,'NATIVE_FOREIGN_RECORD_DOMAIN')
    prefix=struct.pack('<BBH',1,slot%50,0) if storage=='vault' else struct.pack('<I',1)
    return (prefix+metadata).hex()

def candidate_sha():
    contract=json.loads(CONTRACT.read_text('utf-8'))
    value=contract['candidate_sha256']
    require(len(value)==64 and re.fullmatch('[0-9a-f]{64}',value),'NEW_FOREIGN_CANDIDATE_CONTRACT_REQUIRED')
    return value

def click(hwnd,x,y,double=False,interval=.15):
    # Same accepted native message path/timing, release is guaranteed once.
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
    # NEW literal gesture COPY: same accepted timing/10 moves, one release in
    # finally even on failure. No extra release/retry and no memory writes.
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

def weapon_groups():
    from tools.strike_lab import import_native_weapons as catalog
    groups=json.loads(WEAPON_RECORDS.read_text('utf-8-sig'))
    for row in groups[1]:
        for index in (6,8):row[index]=bytes.fromhex(row[index])
    return catalog.validate_records(groups)


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
    groups=weapon_groups();require(len(groups[1])==1259,'FULL_WEAPON_SOURCE_COUNT')
    return {'current_client_sha256':base.sha(base.LIVE),'regions':regions,'weapon_source_rows':1259,'weapon_records_sha256':base.sha(WEAPON_RECORDS),'no_ui_started':True,
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
    require(base.sha(args.server_candidate)==candidate_sha(),'IMMUTABLE_FOREIGN_BANK_CANDIDATE')
    bank_prepare(args)
    database=args.output/'town-diagnostic-accounts.db'
    config=json.loads((args.output/'server-config.json').read_text('utf-8'))
    config['world']['owned_armor_transfers']={'enabled':True};config['world']['owned_armor_bank']={'enabled':True}
    config['world']['owned_foreign_bank']={'enabled':True}
    base.peer.dump(args.output/'server-config.json',config)
    source=json.loads((ARMOR_RUN/'run-result.json').read_text('utf-8'))
    initial={row['identity']:row['saved'] for row in source['ui']['logins'][:2]}
    with closing(sqlite3.connect(database)) as db:
        db.execute('pragma foreign_keys=on')
        require(db.execute("select name from schema_migrations where version=42").fetchone()==('owned_armor_instances',),'REAL_SCHEMA42_REQUIRED')
        require(db.execute('select name from schema_migrations where version=44').fetchone()==('owned_foreign_bank_instances',),'REAL_SCHEMA44_REQUIRED')
        groups=weapon_groups()
        for table,rows,order in zip(('native_weapon_sources','native_weapon_rows'),groups,('family','family,item_id')):
            existing=tuple(db.execute('select * from '+table+' order by '+order))
            require(not existing or existing==rows,'COMPLETE_WEAPON_SOURCE_CONFLICT')
            if not existing:db.executemany('insert into '+table+' values('+','.join('?' for _ in range(10))+')',rows)
            require(tuple(db.execute('select * from '+table+' order by '+order))==rows,'ALL1259_WEAPON_RECORDS_REQUIRED')
        db.commit()
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
            require(raw[2]&63==1 and key==1,'ACCEPTED_WPN_EXACT_TYPE1')
            second=bytearray(raw);second[19]^=0x40 if identity==4 else 0x80
            db.execute('update diagnostic_inventory_slots set item_id=1,count=1,revision=1 where character_id=? and slot=9',(identity,))
            db.execute("insert into character_weapon_slot_metadata values(?,?,?,1,'CUSTOM_TEST_NOT_NATIVE',?,?,?,'CUSTOM-0046')",(identity,9,bytes(second),'CUSTOM_TEST same-ID WPN alternate opaque tail; no stat/drop claim',armor_live.SOURCE_SHA,WEAPON_CLIENT_SHA))
            definition=next(row for row in groups[1] if row[1]==19001)
            require(definition[0]=='TWP' and definition[8][0x11a]&4,'QUALIFIED_TWP19001_BANK_GUARD')
            tw=bytearray([0xc0|identity]*20);tw[:2]=struct.pack('<H',19001);tw[2]=0xc0|25
            db.execute('update diagnostic_inventory_slots set item_id=19001,count=1,revision=1 where character_id=? and slot=10',(identity,))
            db.execute("insert into character_weapon_slot_metadata values(?,?,?,1,'CUSTOM_TEST_NOT_NATIVE',?,?,?,'CUSTOM-0046')",(identity,10,bytes(tw),'CUSTOM_TEST TWP19001 opaque transport fixture; no stat/drop claim',armor_live.SOURCE_SHA,WEAPON_CLIENT_SHA))
            db.execute("update diagnostic_inventory_slots set item_id=16055,count=1,revision=1 where character_id=? and slot=12",(identity,))
            db.execute("insert into character_teleport_gem_metadata values(?,?,?,1,'CUSTOM_TEST_NOT_NATIVE',?,?,'CUSTOM-0057')",(identity,12,GEM_META,'bank-armor-run02 accepted teleport gem20 fixture; no teleport action',armor_live.SOURCE_SHA))
        db.commit()
        require(db.execute('pragma quick_check').fetchone()==('ok',) and db.execute('pragma foreign_key_check').fetchone() is None,'BANK_ARMOR_PRIVATE_DB_INTEGRITY')
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'))
    fixture['armor_bank_fixture']={'authority':'CUSTOM_TEST_NOT_NATIVE','armor_slots':[0,1,30,31,32,33],'weapon_bag_slot':8,'gem_slot':12,'gem_meta':GEM_META.hex(),'med_item':3107,'med_counts':{'4':10,'5':8},'weapon_client_sha256':WEAPON_CLIENT_SHA,'armor_client_sha256':armor_live.CLIENT_SHA,'candidate_sha256':candidate_sha(),'source_contract':source_guards()}
    fixture['foreign_bank_fixture']={'authority':'CUSTOM_TEST_NOT_NATIVE','bag_slots':[8,9,10,12],'bank_slots':[8,9,10,11],'weapon_catalog_sha256':base.sha(WEAPON_RECORDS),'weapon_definition_count':1259,'logical_types':[1,1,25,8],'expected_foreign_commits':24,'expected_cross_domain_refusals':4,'expected_armor_commits':12,'expected_med_commits':20}
    base.peer.dump(args.output/'fixture.json',fixture)
base.prepare=prepare


WEAPON_CLIENT_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
GEM_META=bytes.fromhex('b73e0804')+bytes(16)
ARMOR_RUN=ROOT/'artifacts/playtests/private-native-blackbox-armor-transfer-20261002-01'
CONTRACT=ROOT/'artifacts/research/owned-foreign-bank-0068/candidate-20261003/contract.json'

def source_guards():
    contract=json.loads(CONTRACT.read_text('utf-8'))
    actual={key:base.sha(ROOT/key) for key in contract['source_sha256']}
    require(actual==contract['source_sha256'],'FOREIGN_BANK_RUNTIME_SOURCE_PINS')
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
            mutable=('diagnostic_inventory_slots','character_bank_item_slots','character_bank_item_receipts','character_bank_armor_metadata','character_bank_armor_receipts','character_armor_slot_metadata','character_weapon_slot_metadata','character_teleport_gem_metadata','character_bank_foreign_metadata','character_bank_foreign_receipts')
            return {name:sorted(repr(row) for row in db.execute('select * from "'+name.replace('"','""')+'"'+(' where character_id not in (4,5)' if name in mutable else '')))
                    for name, in db.execute("select name from sqlite_master where type='table' order by name")}
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
        require(source_guards()==fixture['armor_bank_fixture']['source_contract'],'BANK_RUNTIME_SOURCES_CHANGED')
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
        require('OWNED_ARMOR_BANK_ENABLED' in log.read_text('utf-8',errors='replace'),'ACTUAL_ARMOR_BANK_STARTUP_MISSING')
        require('OWNED_FOREIGN_BANK_ENABLED' in log.read_text('utf-8',errors='replace'),'ACTUAL_FOREIGN_BANK_STARTUP_MISSING')
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
                        if row['item']==3107 and bytes.fromhex(row['raw'])[4:]!=struct.pack('<H',3107)+bytes(18):return None
                        if (row['item'],row['quantity'])!=expected[row['slot']]:return None
                    owned=[r for r in d[key] if r[0]==c['identity']]
                    if len(owned)!=len(expected):return None
                    if any((r[2],r[3])!=expected[r[1]] for r in owned):return None
                return {'native':now,'db':d}
            wait_until(consistent,8,'BANK_INITIAL_NATIVE_STORAGE_MISMATCH')
            # Full original C2S63/64/65, no packet injection or memory writes.
            original_instances=instances(c);before_peer=instances(peer)
            expected_armor_bag={int(row[1]):bytes.fromhex(row[2]) for row in original_instances['tables']['character_armor_slot_metadata'] if row[1]<30}
            expected_armor_vault={}
            immutable_armor=sorted(expected_armor_bag.values())
            def armor_consistent():
                if not consistent():return None
                now=snap(c)
                for cell in now['vault']:
                    if not cell['quantity'] and bytes.fromhex(cell['raw'])[4:]!=bytes(20):return None
                for i,metadata in expected_armor_bag.items():
                    if bytes.fromhex(now['bag'][i]['raw'])[4:]!=metadata:return None
                for i,metadata in expected_armor_vault.items():
                    if bytes.fromhex(now['vault'][i]['raw'])[4:]!=metadata:return None
                with closing(base.peer.ro(database)) as db:
                    bagrows=[(i,bytes(m)) for i,m in db.execute('select slot,logical20 from character_armor_slot_metadata where character_id=? and slot<30 order by slot',(c['identity'],))]
                    vaultrows=[(i,bytes(m)) for i,m in db.execute('select slot,logical20 from character_bank_armor_metadata where character_id=? order by slot',(c['identity'],))]
                if dict(bagrows)!=expected_armor_bag or dict(vaultrows)!=expected_armor_vault:return None
                require(sorted(m for _,m in bagrows+vaultrows)==immutable_armor,'FULL20_ARMOR_CUSTODY_CONSERVATION')
                return now
            def owner_full(identity):
                with closing(base.peer.ro(database)) as db:
                    tables=('diagnostic_inventory_slots','character_bank_item_slots','character_armor_slot_metadata','character_bank_armor_metadata','character_weapon_slot_metadata','character_teleport_gem_metadata','character_bank_foreign_metadata','character_bank_item_receipts','character_bank_armor_receipts','character_bank_foreign_receipts','character_trade_wallets','character_bank_balances')
                    return {name:sorted([tuple(bytes(v).hex() if isinstance(v,(bytes,bytearray)) else v for v in row) for row in db.execute('select * from '+name+' where character_id=?',(identity,))],key=repr) for name in tables}
            def armor_operation(op,source,dest):
                page=snap(c)['current_page'];offset=page*50;require(page==0,'ARMOR_TEST_PAGE_CHANGED')
                before_owner=owner_full(c['identity']);before_peer_full=owner_full(peer['identity']);peer_native=snap(peer)
                commits_before=log.read_text('utf-8',errors='replace').count('committed=true rejected=false CUSTOM-0065')
                bag=widget(c,0x232dc8);bank=widget(c,0x232dd2);require(bag is not None and bank is not None,'ARMOR_WINDOWS_MISSING')
                start=point(c,bag if op==0x63 else bank,source)
                end=unobscured_bank_point(c,bank,dest) if op==0x65 else point(c,bag if op==0x64 else bank,dest)
                result['events'].append({'operation':'armor_drag','opcode':op,'identity':c['identity'],'source':source,'destination':dest,'points':[start,end]});save()
                if op==0x65:
                    import ctypes
                    from ctypes import wintypes
                    rect=wintypes.RECT();require(base.peer.user.GetClientRect(c['hwnd'],ctypes.byref(rect)),'ARMOR_CLIENT_RECT_MISSING')
                    sx,sy=round(start[0]*rect.right/800),round(start[1]*rect.bottom/600)
                    def message(code,key,x,y):
                        require(base.peer.user.PostMessageW(c['hwnd'],code,key,(y<<16)|x),'ARMOR_NATIVE_GESTURE_FAILED');time.sleep(.25)
                    message(0x200,0,sx,sy)
                    try:
                        message(0x201,1,sx,sy)
                        require(snap(c)['selected_bank_slot']==source,'ARMOR65_SOURCE_NOT_SELECTED')
                        end=unobscured_bank_point(c,bank,dest)
                        ex,ey=round(end[0]*rect.right/800),round(end[1]*rect.bottom/600)
                        for step in range(1,11):message(0x200,1,sx+(ex-sx)*step//10,sy+(ey-sy)*step//10)
                    finally:
                        ex,ey=round(end[0]*rect.right/800),round(end[1]*rect.bottom/600);message(0x202,0,ex,ey)
                else:drag(c['hwnd'],start,end)
                if op==0x63:
                    metadata=expected_armor_bag.pop(source);expected_armor_vault[offset+dest]=metadata
                    expected_bag[source]=(0,0);expected_vault[offset+dest]=(int.from_bytes(metadata[:2],'little'),1)
                elif op==0x64:
                    metadata=expected_armor_vault.pop(offset+source);expected_armor_bag[dest]=metadata
                    expected_vault[offset+source]=(0,0);expected_bag[dest]=(int.from_bytes(metadata[:2],'little'),1)
                else:
                    expected_armor_vault[offset+source],expected_armor_vault[offset+dest]=expected_armor_vault[offset+dest],expected_armor_vault[offset+source]
                    expected_vault[offset+source],expected_vault[offset+dest]=expected_vault[offset+dest],expected_vault[offset+source]
                after=wait_until(armor_consistent,12,'ARMOR_NATIVE_OR_PERSISTENCE_MISMATCH')
                require(widget(c,0x232dd0) is None,'ARMOR_UNEXPECTED_QUANTITY_MODAL')
                current_instances=instances(c)
                for table in ('character_weapon_slot_metadata','character_teleport_gem_metadata'):
                    require(current_instances['tables'][table]==original_instances['tables'][table],'ARMOR_MUTATION_CHANGED_FOREIGN_META')
                require([row for row in current_instances['tables']['character_armor_slot_metadata'] if row[1]>=30]==[row for row in original_instances['tables']['character_armor_slot_metadata'] if row[1]>=30],'ARMOR_MUTATION_CHANGED_EQUIPPED_METADATA')
                require(instances(peer)==before_peer,'ARMOR_CHANGED_OTHER_OWNER')
                require(owner_full(peer['identity'])==before_peer_full,'ARMOR_CHANGED_PEER_FULL_DB')
                peer_after=snap(peer);require(peer_after['bag']==peer_native['bag'] and peer_after['vault']==peer_native['vault'] and peer_after['purse']==peer_native['purse'] and peer_after['bank']==peer_native['bank'],'ARMOR_CHANGED_PEER_FULL_NATIVE')
                after_owner=owner_full(c['identity'])
                source_table='diagnostic_inventory_slots' if op==0x63 else 'character_bank_item_slots'
                destination_table='diagnostic_inventory_slots' if op==0x64 else 'character_bank_item_slots'
                for table,physical in ((source_table,source if op==0x63 else offset+source),(destination_table,dest if op==0x64 else offset+dest)):
                    previous=next(row for row in before_owner[table] if row[1]==physical);current=next(row for row in after_owner[table] if row[1]==physical)
                    require(current[4]==previous[4]+1,'ARMOR_WRONG_PHYSICAL_REVISION')
                    require([row for row in before_owner[table] if row[1] not in ({source,dest} if source_table==destination_table else {physical})]==[row for row in after_owner[table] if row[1] not in ({source,dest} if source_table==destination_table else {physical})],'ARMOR_CHANGED_UNRELATED_PHYSICAL_CELL')
                for table in ('character_weapon_slot_metadata','character_teleport_gem_metadata','character_bank_foreign_metadata','character_bank_foreign_receipts','character_bank_item_receipts','character_trade_wallets','character_bank_balances'):
                    require(after_owner[table]==before_owner[table],'ARMOR_CHANGED_UNRELATED_OWNER_TABLE')
                old_receipts={row[0] for row in before_owner['character_bank_armor_receipts']};new_receipts=[row for row in after_owner['character_bank_armor_receipts'] if row[0] not in old_receipts]
                require(len(new_receipts)==1 and len(after_owner['character_bank_armor_receipts'])==len(old_receipts)+1,'ARMOR_EXACT_ONE_RECEIPT')
                receipt=new_receipts[0];require(receipt[1:8]==(c['identity'],c['identity'],op,page,source,dest,1),'ARMOR_RECEIPT_OWNER_OPCODE_ROUTE')
                require(log.read_text('utf-8',errors='replace').count('committed=true rejected=false CUSTOM-0065')==commits_before+1,'ARMOR_APPLICATION_COMMIT_MARKER_MISSING')
                result['events'].append({'operation':'armor_committed','opcode':op,'identity':c['identity'],'source':source,'destination':dest,'full20_verified':True,'native':after,'db':saved()});save()
            armor_operation(0x63,0,4);armor_operation(0x63,1,5)
            # Run foreign custody while the original armor occupies bank4/5:
            # two cross-domain65 gestures must reach the actual Application.
            foreign_original=owner_full(c['identity'])
            definitions={row[1]:row for row in weapon_groups()[1]}
            def foreign_payload(row,kind,vault=False):
                if vault:return tuple(row[2:4])+tuple(row[5:12])
                key=int.from_bytes(bytes.fromhex(row[2])[:2],'little')
                definition=definitions.get(key) if kind==1 else None
                return (kind,row[2],row[4],row[5],row[6],row[7] if kind==1 else '',row[8] if kind==1 else row[7],definition[0] if definition else '',definition[7] if definition else '')
            def foreign_maps(owner):
                bag={row[1]:foreign_payload(row,kind) for table,kind in (('character_weapon_slot_metadata',1),('character_teleport_gem_metadata',8)) for row in owner[table] if row[1]<30}
                vault={row[1]:foreign_payload(row,0,True) for row in owner['character_bank_foreign_metadata']}
                return bag,vault
            expected_foreign_bag,expected_foreign_vault=foreign_maps(foreign_original)
            require(set(expected_foreign_bag)=={8,9,10,12} and not expected_foreign_vault,'FOREIGN_INITIAL_EXACT_FIXTURE')
            immutable_foreign=sorted(expected_foreign_bag.values())
            foreign_observation={}
            def foreign_consistent():
                now=snap(c);owner=owner_full(c['identity']);bagmap,vaultmap=foreign_maps(owner)
                # One bounded last observation, no per-poll event/log growth.
                # On failure save this before normal cleanup closes both clients.
                foreign_observation.clear();foreign_observation.update(native=now,owner=owner,
                    expected_bag=expected_bag.copy(),expected_vault=expected_vault.copy(),
                    expected_armor_bag={i:m.hex() for i,m in expected_armor_bag.items()},
                    expected_armor_vault={i:m.hex() for i,m in expected_armor_vault.items()},
                    expected_foreign_bag=expected_foreign_bag.copy(),expected_foreign_vault=expected_foreign_vault.copy(),
                    predicate='scalar_or_armor_consistency')
                if not armor_consistent():return None
                foreign_observation['predicate']='foreign_bag_or_vault_payload_map'
                if bagmap!=expected_foreign_bag or vaultmap!=expected_foreign_vault:return None
                require(sorted(list(bagmap.values())+list(vaultmap.values()))==immutable_foreign,'FOREIGN_FULL20_PROVENANCE_CONSERVATION')
                for storage,mapping in (('bag',bagmap),('vault',vaultmap)):
                    for slot,payload in mapping.items():
                        # Native vault24 uses byte1=page-local source_slot;
                        # native bag24 has the accepted DWORD quantity prefix.
                        expected=native_foreign_record(storage,slot,bytes.fromhex(payload[1]))
                        foreign_observation.update(predicate='native_full24',storage=storage,slot=slot,
                            expected_native_raw=expected,actual_native_raw=now[storage][slot]['raw'])
                        if now[storage][slot]['raw']!=expected:return None
                foreign_observation['predicate']='scalar_metadata_key_revision_source'
                for table,scalar_table,revindex in (('character_weapon_slot_metadata','diagnostic_inventory_slots',3),('character_teleport_gem_metadata','diagnostic_inventory_slots',3),('character_bank_foreign_metadata','character_bank_item_slots',4)):
                    for row in owner[table]:
                        scalar=next(value for value in owner[scalar_table] if value[1]==row[1]);metadata=bytes.fromhex(row[3] if revindex==4 else row[2])
                        require(scalar[3]==1 and scalar[2]==int.from_bytes(metadata[:2],'little') and scalar[4]==row[revindex] and scalar[5]==armor_live.SOURCE_SHA,'FOREIGN_SCALAR_META_KEY_REVISION_SOURCE')
                        if revindex==4:require(row[12]=='CUSTOM-0068','FOREIGN_STORAGE_DESIGN')
                return {'native':now,'owner':owner}
            def full_state(owner):
                scalar=lambda row:[row[2],row[3],row[4],row[5]]
                bag=[None]*50
                for row in owner['diagnostic_inventory_slots']:bag[row[1]]=scalar(row)
                vault=[None]*300
                for row in owner['character_bank_item_slots']:vault[row[1]]=scalar(row)
                armorbag=[[row[1],int.from_bytes(bytes.fromhex(row[2])[:2],'little'),1,row[3],list(bytes.fromhex(row[2])),row[4],row[5],True] for row in sorted(owner['character_armor_slot_metadata'],key=lambda row:row[1])]
                armorvault=[[row[1],list(bytes.fromhex(row[2])),*row[3:9]] for row in sorted(owner['character_bank_armor_metadata'],key=lambda row:row[1])]
                weapon=[[row[1],list(bytes.fromhex(row[2])),*row[3:9]] for row in sorted(owner['character_weapon_slot_metadata'],key=lambda row:row[1])]
                gems=[[row[1],list(bytes.fromhex(row[2])),*row[3:7],'',row[7]] for row in sorted(owner['character_teleport_gem_metadata'],key=lambda row:row[1])]
                foreign=[[row[1],row[2],list(bytes.fromhex(row[3])),*row[4:12]] for row in sorted(owner['character_bank_foreign_metadata'],key=lambda row:row[1])]
                return [c['identity'],c['identity'],bag,vault,armorbag,armorvault,weapon,gems,foreign]
            def whole_gesture(op,source,destination):
                state=snap(c);require(state['current_page']==0,'FOREIGN_PAGE0_REQUIRED')
                bank=widget(c,0x232dd2);bag=widget(c,0x232dc8);require(bank is not None and bag is not None,'FOREIGN_WINDOWS_MISSING')
                start=point(c,bag if op==0x63 else bank,source)
                end=unobscured_bank_point(c,bank,destination) if op==0x65 else point(c,bag if op==0x64 else bank,destination)
                result['events'].append({'operation':'foreign_real_gesture','identity':c['identity'],'opcode':op,'source':source,'destination':destination,'points':[start,end]});save()
                if op!=0x65:drag(c['hwnd'],start,end);return
                import ctypes
                from ctypes import wintypes
                rect=wintypes.RECT();require(base.peer.user.GetClientRect(c['hwnd'],ctypes.byref(rect)),'FOREIGN_CLIENT_RECT')
                sx,sy=round(start[0]*rect.right/800),round(start[1]*rect.bottom/600)
                ex,ey=round(end[0]*rect.right/800),round(end[1]*rect.bottom/600)
                def message(code,key,x,y):
                    require(base.peer.user.PostMessageW(c['hwnd'],code,key,(y<<16)|x),'FOREIGN_MOUSE_MESSAGE');time.sleep(.25)
                message(0x200,0,sx,sy)
                try:
                    message(0x201,1,sx,sy)
                    state=snap(c);result['events'].append({'operation':'foreign_source_pressed','identity':c['identity'],'opcode':op,'selected':state['selected_bank_slot'],'cursor':state['cursor_mode']});save()
                    require(state['selected_bank_slot']==source,'FOREIGN65_SOURCE_NOT_SELECTED')
                    end=unobscured_bank_point(c,bank,destination)
                    ex,ey=round(end[0]*rect.right/800),round(end[1]*rect.bottom/600)
                    for step in range(1,11):message(0x200,1,sx+(ex-sx)*step//10,sy+(ey-sy)*step//10)
                finally:message(0x202,0,ex,ey)
            def foreign_operation(op,source,destination):
                before_owner=owner_full(c['identity']);before_peer=owner_full(peer['identity']);peer_native=snap(peer)
                commits=log.read_text('utf-8',errors='replace').count('committed=true rejected=false CUSTOM-0065')
                whole_gesture(op,source,destination)
                if op==0x63:
                    payload=expected_foreign_bag.pop(source);expected_foreign_vault[destination]=payload
                    expected_bag[source]=(0,0);expected_vault[destination]=(int.from_bytes(bytes.fromhex(payload[1])[:2],'little'),1)
                elif op==0x64:
                    payload=expected_foreign_vault.pop(source);expected_foreign_bag[destination]=payload
                    expected_vault[source]=(0,0);expected_bag[destination]=(int.from_bytes(bytes.fromhex(payload[1])[:2],'little'),1)
                else:
                    expected_foreign_vault[source],expected_foreign_vault[destination]=expected_foreign_vault[destination],expected_foreign_vault[source]
                    expected_vault[source],expected_vault[destination]=expected_vault[destination],expected_vault[source]
                try:after=wait_until(foreign_consistent,12,'FOREIGN_NATIVE_SQL_FULL20_MISMATCH')
                except BaseException:
                    result['failure_foreign_predicate']={'opcode':op,'source':source,'destination':destination,'last_observed':foreign_observation.copy()};save()
                    raise
                after_owner=after['owner']
                require(widget(c,0x232dd0) is None,'FOREIGN_WHOLE_UNEXPECTED_QUANTITY_DIALOG')
                physical={('diagnostic_inventory_slots' if op==0x63 else 'character_bank_item_slots',source),('diagnostic_inventory_slots' if op==0x64 else 'character_bank_item_slots',destination)}
                expected_sources=expected_physical_sources(before_owner,op,0,source,destination)
                for table in ('diagnostic_inventory_slots','character_bank_item_slots'):
                    allowed={slot for name,slot in physical if name==table}
                    require([row for row in before_owner[table] if row[1] not in allowed]==[row for row in after_owner[table] if row[1] not in allowed],'FOREIGN_CHANGED_UNRELATED_SCALAR')
                    for slot in allowed:
                        a=next(row for row in before_owner[table] if row[1]==slot);b=next(row for row in after_owner[table] if row[1]==slot)
                        require(b[4]==a[4]+1 and b[5]==expected_sources[(table,slot)] and b[6:]==a[6:],'FOREIGN_PHYSICAL_REVISION_OR_TRANSFER_SOURCE_DESIGN')
                for table in ('character_armor_slot_metadata','character_bank_armor_metadata','character_bank_item_receipts','character_bank_armor_receipts','character_trade_wallets','character_bank_balances'):
                    require(before_owner[table]==after_owner[table],'FOREIGN_CHANGED_ARMOR_MED_MONEY_OR_LEDGER')
                for table in ('character_weapon_slot_metadata','character_teleport_gem_metadata'):
                    require([row for row in before_owner[table] if row[1]>=30]==[row for row in after_owner[table] if row[1]>=30],'FOREIGN_CHANGED_EQUIPPED_FULL20')
                old={row[0] for row in before_owner['character_bank_foreign_receipts']};added=[row for row in after_owner['character_bank_foreign_receipts'] if row[0] not in old]
                require(len(added)==1 and len(after_owner['character_bank_foreign_receipts'])==len(old)+1,'FOREIGN_EXACT_ONE_RECEIPT')
                receipt=added[0];require(receipt[1:8]==(c['identity'],c['identity'],op,0,source,destination,1) and receipt[10]=='CUSTOM-0068','FOREIGN_RECEIPT_ROUTE_OWNER_OPCODE')
                require(json.loads(receipt[8])==full_state(before_owner) and json.loads(receipt[9])==full_state(after_owner),'FOREIGN_RECEIPT_BEFORE_AFTER_EXACT_COMPLETE_STATE')
                peer_after=snap(peer)
                require(owner_full(peer['identity'])==before_peer and all(peer_after[key]==peer_native[key] for key in ('bag','vault','purse','bank')),'FOREIGN_CHANGED_PEER_FULL20_OR_SAVES')
                require(log.read_text('utf-8',errors='replace').count('committed=true rejected=false CUSTOM-0065')==commits+1,'FOREIGN_APPLICATION_EXACT_COMMIT')
                require(untouched()==invariant,'FOREIGN_CHANGED_PROTECTED_DATABASE_ROWS')
                result['events'].append({'operation':'foreign_committed','identity':c['identity'],'opcode':op,'source':source,'destination':destination,'full20_verified':True,'physical_revision_verified':True,'provenance_verified':True,'receipt_state_verified':True,'peer_unchanged':True,'native':after['native'],'receipt':receipt,'owner':after_owner});save()
            def cross_rejected(source,destination):
                before_owner=owner_full(c['identity']);before_peer=owner_full(peer['identity']);native=snap(c);peer_native=snap(peer)
                text=log.read_text('utf-8',errors='replace');rejections=text.count('committed=false rejected=true CUSTOM-0065');commits=text.count('committed=true rejected=false CUSTOM-0065')
                whole_gesture(0x65,source,destination)
                wait_until(lambda:log.read_text('utf-8',errors='replace').count('committed=false rejected=true CUSTOM-0065')==rejections+1,10,'CROSS_DOMAIN_REAL_APPLICATION_REJECTION_MISSING')
                restored=wait_until(foreign_consistent,10,'CROSS_DOMAIN_FULL20_ROLLBACK_PROJECTION_MISSING')
                require(owner_full(c['identity'])==before_owner and owner_full(peer['identity'])==before_peer,'CROSS_DOMAIN_CHANGED_EITHER_OWNER_OR_RECEIPTS')
                peer_after=snap(peer)
                require(all(restored['native'][key]==native[key] for key in ('bag','vault','purse','bank')) and all(peer_after[key]==peer_native[key] for key in ('bag','vault','purse','bank')),'CROSS_DOMAIN_CHANGED_FULL_NATIVE_CUSTODY')
                require(log.read_text('utf-8',errors='replace').count('committed=true rejected=false CUSTOM-0065')==commits and untouched()==invariant,'CROSS_DOMAIN_COMMITTED_OR_CHANGED_PROTECTED_ROWS')
                result['events'].append({'operation':'foreign_cross_domain_rejected','identity':c['identity'],'opcode':101,'source':source,'destination':destination,'application_rejected':True,'whole_db_unchanged':True,'all_saved_rows_unchanged':True,'native_full20_preserved':True,'full_native_restored':True,'peer_unchanged':True,'native':restored['native']});save()
                # A rejected context is invalidated by the actual service. Close
                # and reopen using normal39/NPC37 before the next request.
                control(c,widget(c,0x232dd2),54);wait_until(lambda:widget(c,0x232dd2) is None,5,'REFUSAL_BANK_CLOSE_MISSING')
                opened();wait_until(foreign_consistent,8,'REFUSAL_REAL_UI_REOPEN_FULL20_MISSING')
            for bag_slot,bank_slot in ((8,8),(9,9),(10,10),(12,11)):foreign_operation(0x63,bag_slot,bank_slot)
            cross_rejected(4,8);cross_rejected(8,4)
            foreign_operation(0x65,8,9);foreign_operation(0x65,8,9)
            foreign_operation(0x65,10,11);foreign_operation(0x65,10,11)
            control(c,widget(c,0x232dd2),54);wait_until(lambda:widget(c,0x232dd2) is None,5,'FOREIGN_REOPEN_CLOSE_MISSING')
            opened();wait_until(foreign_consistent,8,'FOREIGN_FULL300_REOPEN_NOT_RESTORED')
            for bank_slot,bag_slot in ((8,8),(9,9),(10,10),(11,12)):foreign_operation(0x64,bank_slot,bag_slot)
            final_foreign=owner_full(c['identity'])
            require(foreign_maps(final_foreign)==foreign_maps(foreign_original),'FOREIGN_FINAL_SLOT_PAYLOAD_PROVENANCE_CHANGED')
            # Only verified foreign physical revisions have advanced. Preserve
            # the original armor baseline for its remaining accepted matrix.
            current_instances=instances(c)
            for table in ('character_weapon_slot_metadata','character_teleport_gem_metadata'):
                original_instances['tables'][table]=current_instances['tables'][table]
            armor_operation(0x65,4,5);armor_operation(0x65,4,5)
            control(c,widget(c,0x232dd2),54);wait_until(lambda:widget(c,0x232dd2) is None,5,'ARMOR_BANK_CLOSE_MISSING')
            opened();wait_until(armor_consistent,8,'ARMOR_BANK_FULL20_REOPEN_FAILED')
            armor_operation(0x64,4,0);armor_operation(0x64,5,1)
            restored=instances(c)
            for table in ('character_weapon_slot_metadata','character_teleport_gem_metadata'):
                require(restored['tables'][table]==original_instances['tables'][table],'ARMOR_CHANGED_FOREIGN_OVERLAY')
            original_armor=[row for row in original_instances['tables']['character_armor_slot_metadata']]
            final_armor=[row for row in restored['tables']['character_armor_slot_metadata']]
            require([[row[0],row[1],row[2],*row[4:]] for row in original_armor]==[[row[0],row[1],row[2],*row[4:]] for row in final_armor],'ARMOR_CHANGED_ORIGIN_OR_BYTES')
            c['instance_baseline']=restored
            unchanged_instances();require(untouched()==invariant,'ARMOR_CHANGED_UNRELATED_SAVES')
            def change_page(index):
                control(c,widget(c,0x232dd2),56 if index>snap(c)['current_page'] else 55)
                require(snap(c)['current_page']==index,'BANK_PAGE_DID_NOT_CHANGE');time.sleep(.6)
                require(str(index+1).encode() in bytes.fromhex(snap(c)['page_label']['text_bytes_hex']),'BANK_PAGE_LABEL_NOT_RENDERED')
                result['events'].append({'operation':'page_arrow','page':index,'native':snap(c)});save()
            def operation(op,source,dest,quantity):
                time.sleep(.3);state=snap(c);page=state['current_page'];offset=page*50;prior_db=saved()
                prior_owner=owner_full(c['identity'])
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
                    message(0x200,0,sx,sy)
                    try:
                        message(0x201,1,sx,sy);checkpoint('source_pressed')
                        require(snap(c)['selected_bank_slot']==source,'BANK_SWAP_SOURCE_NOT_SELECTED')
                        end=unobscured_bank_point(c,bank,dest)
                        ex,ey=round(end[0]*rect.right/800),round(end[1]*rect.bottom/600)
                        result['events'].append({'operation':'65_actual_drop_point_after_source_tooltip','identity':c['identity'],'source':source,'destination':dest,'point':end});save()
                        for step in range(1,11):
                            message(0x200,1,sx+(ex-sx)*step//10,sy+(ey-sy)*step//10)
                            checkpoint('move_'+str(step))
                    finally:message(0x202,0,ex,ey)
                    checkpoint('destination_released')
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
                after_owner=owner_full(c['identity'])
                for table in ('character_armor_slot_metadata','character_bank_armor_metadata','character_weapon_slot_metadata','character_teleport_gem_metadata','character_bank_foreign_metadata','character_bank_foreign_receipts','character_bank_armor_receipts','character_trade_wallets','character_bank_balances'):
                    require(after_owner[table]==prior_owner[table],'MED_CHANGED_FULL20_OR_OTHER_LEDGER_MONEY')
                physical={('diagnostic_inventory_slots' if op==0x63 else 'character_bank_item_slots',source if op==0x63 else offset+source),('diagnostic_inventory_slots' if op==0x64 else 'character_bank_item_slots',dest if op==0x64 else offset+dest)}
                expected_sources=expected_physical_sources(prior_owner,op,page,source,dest)
                for table in ('diagnostic_inventory_slots','character_bank_item_slots'):
                    allowed={slot for name,slot in physical if name==table}
                    require([row for row in prior_owner[table] if row[1] not in allowed]==[row for row in after_owner[table] if row[1] not in allowed],'MED_CHANGED_UNRELATED_PHYSICAL_SLOT')
                    for slot in allowed:
                        before_row=next(row for row in prior_owner[table] if row[1]==slot);after_row=next(row for row in after_owner[table] if row[1]==slot)
                        require(after_row[4]==before_row[4]+1 and after_row[5]==expected_sources[(table,slot)] and after_row[6:]==before_row[6:],'MED_PHYSICAL_REVISION_OR_TRANSFER_SOURCE_DESIGN')
                rendered=[];sidebar=widget(c,0x232dd4)
                for slot in {source if op!=0x63 else dest,dest if op!=0x64 else source}:
                    qty=expected_vault[offset+slot][1]
                    if qty:
                        text=label(c,sidebar,slot);require(str(qty).encode() in bytes.fromhex(text['text_bytes_hex']),'BANK_SLOT_COUNT_NOT_RENDERED')
                        rendered.append({'slot':slot,'quantity':qty,'label':text,'icon':icon(c,bank,slot,3107)})
                    else:rendered.append({'slot':slot,'quantity':0,'icon':icon(c,bank,slot,0)})
                result['events'].append({'operation':hex(op),'identity':c['identity'],'source':source,'destination':dest,'page':page,'quantity':quantity,'modal':modal,'rendered':rendered,'after':after,'other_owner_unchanged':True,'native_and_durable_total':count,'physical_revision_verified':True,'all_foreign_armor_equipped_preserved':True});save()
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
        with closing(base.peer.ro(database)) as db:
            require(db.execute('select count(*) from character_bank_armor_receipts').fetchone()[0]==12,'ARMOR12_RECEIPTS_MISSING')
            require(db.execute('select count(*) from character_bank_armor_metadata').fetchone()[0]==0,'ARMOR_FINAL_VAULT_NOT_EMPTY')
            require(db.execute('select count(*) from character_bank_foreign_receipts').fetchone()[0]==24,'FOREIGN24_RECEIPTS_MISSING')
            require(db.execute('select count(*) from character_bank_foreign_metadata').fetchone()[0]==0,'FOREIGN_FINAL_VAULT_NOT_EMPTY')
        require(sum(event['operation']=='foreign_cross_domain_rejected' for event in result['events'])==4,'FOUR_REAL_CROSS_DOMAIN_REFUSALS_REQUIRED')
        result['matrix_counts']={str(owner['identity']):{name:sum(event['operation']==name and event.get('identity')==owner['identity'] for event in result['events']) for name in ('foreign_committed','armor_committed','foreign_cross_domain_rejected','0x63','0x64','0x65')} for owner in clients}
        require(all(row=={'foreign_committed':12,'armor_committed':6,'foreign_cross_domain_rejected':2,'0x63':3,'0x64':4,'0x65':3} for row in result['matrix_counts'].values()),'BOTH_LANGUAGE_MATRIX_INCOMPLETE')
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
    require(base.sha(args.server_candidate)==candidate_sha(),'NEW_IMMUTABLE_FOREIGN_BANK_CANDIDATE')
    require(base.sha(ACCEPTED_ARMOR_TOOL)==ACCEPTED_ARMOR_SHA,'ACCEPTED_ARMOR_TOOL_CHANGED')
    source_before=source_guards();desktop_before=desktop_names()
    protected={str(p.pid):{'exe':p.info['exe'],'created':p.info['create_time']} for p in psutil.process_iter(['exe','create_time']) if p.info['exe'] and Path(p.info['exe']).name.lower() in ('god2.exe','god2-server.exe','leproc.exe','private_desktop_runner.exe')}
    frozen={str(path):base.sha(path) for path in (Path(__file__).resolve(),FOREIGN_V01_TOOL,FOREIGN_RUN01/'run-result.json',FOREIGN_RUN01/'ui-result.json',FOREIGN_RUN01/'town-diagnostic-accounts.db',ACCEPTED_ARMOR_TOOL,WEAPON_RECORDS,Path(armor_live.__file__).resolve(),Path(armor_catalog.__file__).resolve(),Path(base.__spec__.origin),Path(pose.__file__).resolve(),ROOT/'tools/strike_lab/private_potion_ui.py',ROOT/'tools/strike_lab/private_bank_swap_20261002.py',ROOT/'tools/strike_lab/private_inventory_move_ui.py',ROOT/'tools/strike_lab/private_trade_full_projection_20261003.py',CONTRACT,ARMOR_RUN/'run-result.json',ACCEPTED_ARMOR_RUN/'run-result.json',ACCEPTED_ARMOR_RUN/'ui-result.json',ACCEPTED_ARMOR_RUN/'town-diagnostic-accounts.db',ACCEPTED_ARMOR_RUN/'server-config.json')}
    os.environ['GOD2_NATIVE_WORLD_RECORDS_LAB']='1' 
    qualify();script=Path(__file__).resolve();digest=base.sha(script);base.__file__=str(script);code=bounded_owner(args)
    receipt=args.output/'run-result.json'
    if receipt.exists():
        result=json.loads(receipt.read_text('utf-8'));result['bank_swap_harness_sha256']=digest
        result['bank_swap_harness_unchanged']=base.sha(script)==digest
        result['runtime_sources_before']=source_before;result['runtime_sources_after']=source_guards();result['runtime_sources_unchanged']=result['runtime_sources_before']==result['runtime_sources_after']
        result['frozen_files_before']=frozen;result['frozen_files_after']={path:base.sha(Path(path)) for path in frozen};result['frozen_files_unchanged']=result['frozen_files_before']==result['frozen_files_after']
        after={str(p.pid):{'exe':p.info['exe'],'created':p.info['create_time']} for p in psutil.process_iter(['exe','create_time']) if str(p.pid) in protected}
        result['protected_processes_before']=protected;result['protected_processes_preserved']=after==protected
        result['desktop_owner_before']=desktop_before;result['desktop_owner_after']=desktop_names();result['desktop_owner_unchanged']=result['desktop_owner_before']==result['desktop_owner_after']
        with socket.socket() as probe:result['exclusive2598_released']=probe.connect_ex(('127.0.0.1',2598))!=0
        pids=[result.get('server_pid'),result.get('runner_pid')]+result.get('ui',{}).get('owned_client_pids',[])
        result['owned_pid_terminal']={str(pid):{'pid_exists':psutil.pid_exists(pid)} for pid in pids if pid}
        result['scope']='FOREIGN24_ARMOR12_MED20_TW_CN_CUSTOM_TEST_ONLY'
        result['accepted']=bool(result['accepted'] and result['bank_swap_harness_unchanged'] and result['runtime_sources_unchanged'] and result['frozen_files_unchanged'] and result['protected_processes_preserved'] and result['desktop_owner_unchanged'] and result['exclusive2598_released'] and not any(row['pid_exists'] for row in result['owned_pid_terminal'].values()));base.peer.dump(receipt,result)
        return 0 if result['accepted'] else 1
    return code
# NEW literal COPY of accepted owner orchestration; only timeout420/400 ->720/700.
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
