"""NEW CUSTOM0070 native65 six-family custody UI acceptance; preparation only.

No foreground activation, screenshots, process-memory writes or packet injection.
Only disposable copies have their port changed. Saves are an isolated backup.
"""
import argparse,os,json,sqlite3,struct,sys,time,traceback,subprocess,copy
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
OLD_BANK_TOOL=ROOT/'tools/strike_lab/private_owned_foreign_bank_v02_20261003.py'
ARMOR_RUN=ROOT/'artifacts/playtests/private-native-blackbox-armor-transfer-20261002-01'
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
    require(len(value)==64 and re.fullmatch('[0-9a-f]{64}',value) and contract['design']=='CUSTOM-0070','NEW_MIXED_CANDIDATE_CONTRACT_REQUIRED')
    require(contract['client_sha256']==base.CLIENT_SHA,'CURRENT_CLIENT_CONTRACT_PIN')
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


CONTRACT=ROOT/'artifacts/research/owned-mixed-bank-0070/candidate-20261003/contract.json'
SOURCE_RUN=ROOT/'artifacts/playtests/private-native-blackbox-owned-foreign-bank-20261003-02'
base.SOURCE=SOURCE_RUN/'town-diagnostic-accounts.db'
FAMILIES=('MED','EQU','TEQ','WPN','TWP','GEM')
SCOPE='MIXED_BANK_SIX_FAMILIES_36_ORDERED_EACH_TW_CN_CUSTOM_TEST_ONLY'
TABLES=('diagnostic_inventory_slots','character_bank_item_slots','character_armor_slot_metadata','character_bank_armor_metadata','character_weapon_slot_metadata','character_teleport_gem_metadata','character_bank_foreign_metadata','character_bank_item_receipts','character_bank_armor_receipts','character_bank_foreign_receipts','character_bank_mixed_receipts','character_trade_wallets','character_bank_balances')
META=('character_armor_slot_metadata','character_weapon_slot_metadata','character_teleport_gem_metadata')
def source_guards():
    contract=json.loads(CONTRACT.read_text('utf-8'));expected=contract['source_sha256']
    require(len(expected)==36,'EXACT36_RUNTIME_SOURCES_REQUIRED')
    actual={key:base.sha(ROOT/key) for key in expected};require(actual==expected,'MIXED_BANK_ALL_RUNTIME_SOURCE_PINS');return actual
def owner_saved(database,identity):
    with closing(base.peer.ro(database)) as db:
        return {name:sorted([[v.hex() if isinstance(v,bytes) else v for v in row] for row in db.execute('select * from '+name+' where character_id=?',(identity,))],key=repr) for name in TABLES}
def metadata(saved,storage,slot):
    table='diagnostic_inventory_slots' if storage=='bag' else 'character_bank_item_slots'
    cell=next((row for row in saved[table] if row[1]==slot),None)
    if cell is None or cell[3]==0:return None
    if storage=='bag':overlay=[row[2] for name in META for row in saved[name] if row[1]==slot]
    else:overlay=[row[2] for row in saved['character_bank_armor_metadata'] if row[1]==slot]+[row[3] for row in saved['character_bank_foreign_metadata'] if row[1]==slot]
    require(len(overlay)<=1,'MIXED_OVERLAY_CONFLICT')
    return bytes.fromhex(overlay[0]) if overlay else struct.pack('<H',cell[2])+bytes(18)
def family(saved,slot):
    cell=next(row for row in saved['character_bank_item_slots'] if row[1]==slot)
    if cell[3]==0:return 'EMPTY'
    raw=metadata(saved,'vault',slot)
    if raw[2]&63==2:return 'EQU'
    if raw[2]&63==26:return 'TEQ'
    if raw[2]&63==1:return 'WPN'
    if raw[2]&63==25:return 'TWP'
    if raw[2]&63==8:return 'GEM'
    require(cell[2]==3107 and raw==struct.pack('<H',3107)+bytes(18),'UNQUALIFIED_PLAIN_FAMILY');return 'MED'
def receipt_state(owner,identity):
    scalar=lambda r:[r[2],r[3],r[4],r[5]]
    bag=[None]*50
    for r in owner['diagnostic_inventory_slots']:bag[r[1]]=scalar(r)
    vault=[None]*300
    for r in owner['character_bank_item_slots']:vault[r[1]]=scalar(r)
    armorbag=[[r[1],int.from_bytes(bytes.fromhex(r[2])[:2],'little'),1,r[3],list(bytes.fromhex(r[2])),r[4],r[5],True] for r in sorted(owner['character_armor_slot_metadata'],key=lambda r:r[1])]
    armorvault=[[r[1],list(bytes.fromhex(r[2])),*r[3:9]] for r in sorted(owner['character_bank_armor_metadata'],key=lambda r:r[1])]
    weapon=[[r[1],list(bytes.fromhex(r[2])),*r[3:9]] for r in sorted(owner['character_weapon_slot_metadata'],key=lambda r:r[1])]
    gems=[[r[1],list(bytes.fromhex(r[2])),*r[3:7],'',r[7]] for r in sorted(owner['character_teleport_gem_metadata'],key=lambda r:r[1])]
    foreign=[[r[1],r[2],list(bytes.fromhex(r[3])),*r[4:12]] for r in sorted(owner['character_bank_foreign_metadata'],key=lambda r:r[1])]
    return [identity,identity,bag,vault,armorbag,armorvault,weapon,gems,foreign]
def expected_swap(before,source,destination):
    after=copy.deepcopy(before);a=next(r for r in before['character_bank_item_slots'] if r[1]==source);b=next(r for r in before['character_bank_item_slots'] if r[1]==destination)
    require(a[3]>0 and source!=destination,'WHOLE_SWAP_SOURCE_DOMAIN')
    for slot,incoming,physical in ((source,b,a),(destination,a,b)):
        row=next(r for r in after['character_bank_item_slots'] if r[1]==slot)
        row[2:4]=incoming[2:4];row[4]=physical[4]+1;row[5]=incoming[5] if incoming[3] else physical[5]
    for table,index in (('character_bank_armor_metadata',2),('character_bank_foreign_metadata',3)):
        selected=[copy.deepcopy(r) for r in before[table] if r[1] in(source,destination)]
        after[table]=[r for r in after[table] if r[1] not in(source,destination)]
        for row in selected:
            row[1]=destination if row[1]==source else source
            scalar=next(r for r in after['character_bank_item_slots'] if r[1]==row[1]);row[index+1]=scalar[4];after[table].append(row)
        after[table].sort(key=repr)
    return after
def expected_transport(before,op,source,destination,quantity):
    after=copy.deepcopy(before);source_table='diagnostic_inventory_slots' if op==0x63 else 'character_bank_item_slots';dest_table='character_bank_item_slots' if op==0x63 else 'diagnostic_inventory_slots'
    a=next(r for r in before[source_table] if r[1]==source);b=next(r for r in before[dest_table] if r[1]==destination)
    require(a[3]>=quantity>0 and b[3]==0,'TRANSPORT_QUANTITY_OR_DESTINATION')
    src=next(r for r in after[source_table] if r[1]==source);dst=next(r for r in after[dest_table] if r[1]==destination)
    src[3]-=quantity;src[2]=a[2] if src[3] else 0;src[4]+=1;dst[2:4]=[a[2],quantity];dst[4]+=1;dst[5]=a[5]
    if op==0x63:
        for table in META:
            matches=[r for r in before[table] if r[1]==source]
            for r in matches:
                require(quantity==a[3]==1,'FULL20_WHOLE_TRANSPORT_ONLY');after[table]=[v for v in after[table] if v[1]!=source]
                if table=='character_armor_slot_metadata':after['character_bank_armor_metadata'].append([r[0],destination,r[2],dst[4],*r[4:],'CUSTOM-0067'])
                else:
                    gem=table=='character_teleport_gem_metadata';definition=next((row for row in weapon_groups()[1] if row[1]==a[2]),None)
                    after['character_bank_foreign_metadata'].append([r[0],destination,8 if gem else 1,r[2],dst[4],r[4],r[5],r[6],'' if gem else r[7],r[-1],'' if gem else definition[0],'' if gem else definition[7],'CUSTOM-0068'])
    else:
        for table in('character_bank_armor_metadata','character_bank_foreign_metadata'):
            matches=[r for r in before[table] if r[1]==source]
            for r in matches:
                require(quantity==a[3]==1,'FULL20_WHOLE_TRANSPORT_ONLY');after[table]=[v for v in after[table] if v[1]!=source]
                if table=='character_bank_armor_metadata':after['character_armor_slot_metadata'].append([r[0],destination,r[2],dst[4],*r[4:9]])
                elif r[2]==1:after['character_weapon_slot_metadata'].append([r[0],destination,r[3],dst[4],*r[5:10]])
                else:after['character_teleport_gem_metadata'].append([r[0],destination,r[3],dst[4],*r[5:8],r[9]])
    for table in TABLES:after[table].sort(key=repr)
    return after
def quantity_inventory(owner):
    totals={}
    for table in('diagnostic_inventory_slots','character_bank_item_slots'):
        for r in owner[table]:
            if r[3]:totals[r[2]]=totals.get(r[2],0)+r[3]
    return totals
def instance_inventory(owner):
    values=[]
    for table in META:
        for r in owner[table]:values.append((r[2],*r[4:7],r[7] if table!='character_teleport_gem_metadata' else '',r[-1]))
    for r in owner['character_bank_armor_metadata']:values.append((r[2],*r[4:9]))
    for r in owner['character_bank_foreign_metadata']:values.append((r[3],*r[5:10]))
    return sorted(values)
original_prepare=base.prepare
def prepare(args):
    require(base.sha(args.server_candidate)==candidate_sha(),'IMMUTABLE_0070_CANDIDATE')
    require(json.loads((SOURCE_RUN/'run-result.json').read_text('utf-8'))['accepted'],'ACCEPTED0068_SEED_REQUIRED')
    original_prepare(args);database=args.output/'town-diagnostic-accounts.db'
    config=json.loads((args.output/'server-config.json').read_text('utf-8'))
    config['world']['owned_armor_transfers']={'enabled':True};config['world']['owned_armor_bank']={'enabled':True};config['world']['owned_foreign_bank']={'enabled':True};config['world']['owned_mixed_bank']={'enabled':True}
    base.peer.dump(args.output/'server-config.json',config)
    with closing(sqlite3.connect(database)) as db:
        db.execute('pragma foreign_keys=on');require(db.execute('select count(*) from schema_migrations where version=46').fetchone()==(1,),'REAL_SCHEMA46_REQUIRED')
        for identity in(4,5):
            other=9-identity
            for original,destination in((0,2),(1,3)):
                row=list(db.execute('select * from character_armor_slot_metadata where character_id=? and slot=?',(other,original)).fetchone());row[:2]=[identity,destination];row[3]=1;row[4]='CUSTOM_TEST_NOT_NATIVE';row[5]='NEW0070 explicit copied counterpart-family CUSTOM_TEST fixture'
                require(db.execute('select count(*) from character_armor_slot_metadata where character_id=? and slot=?',(identity,destination)).fetchone()==(0,),'NEW_COUNTERPART_SLOT_OCCUPIED')
                db.execute('update diagnostic_inventory_slots set item_id=?,count=1,revision=1 where character_id=? and slot=?',(int.from_bytes(row[2][:2],'little'),identity,destination))
                db.execute('insert into character_armor_slot_metadata values(?,?,?,?,?,?,?,?,?)',row)
            for table,source,destination in(('character_weapon_slot_metadata',10,11),('character_teleport_gem_metadata',12,13)):
                row=list(db.execute('select * from '+table+' where character_id=? and slot=?',(identity,source)).fetchone());row[1]=destination;row[3]=1;row[4]='CUSTOM_TEST_NOT_NATIVE';row[5]='NEW0070 second '+table+' CUSTOM_TEST fixture'
                if table=='character_weapon_slot_metadata':raw=bytearray(row[2]);raw[19]^=0x20;row[2]=bytes(raw)
                db.execute('update diagnostic_inventory_slots set item_id=?,count=1,revision=1 where character_id=? and slot=?',(int.from_bytes(row[2][:2],'little'),identity,destination))
                db.execute('insert into '+table+' values('+','.join('?' for _ in row)+')',row)
            for slot in(5,6,7):
                require(all(db.execute('select count(*) from '+table+' where character_id=? and slot=?',(identity,slot)).fetchone()==(0,) for table in META),'PLAIN_MED_SLOT_OVERLAY_CONFLICT')
                db.execute('update diagnostic_inventory_slots set item_id=?,count=?,revision=1 where character_id=? and slot=?',(3107 if slot==5 else 0,(10 if identity==4 else 8) if slot==5 else 0,identity,slot))
            db.execute('update character_trade_wallets set amount=1000,revision=1 where character_id=?',(identity,))
        db.execute('update recovered_positions set x=129,y=126 where character_id=5')
        db.commit();require(db.execute('pragma quick_check').fetchone()==('ok',) and db.execute('pragma foreign_key_check').fetchone() is None,'CUSTOM_PRIVATE_CLONE_INTEGRITY')
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'));fixture['mixed_bank_fixture']={'authority':'CUSTOM_TEST_NOT_NATIVE','source_contract':source_guards(),'candidate_sha256':candidate_sha(),'med_totals':{'4':10,'5':8},'families':FAMILIES,'expected_per_owner':{'deposit63':12,'pair65':36,'empty65':12,'withdraw64':12},'native65_marker':1,'whole_qty_authority':'qualified owner SQL before source.count, never wire marker1'}
    fixture['bank_fixture']=json.loads((SOURCE_RUN/'fixture.json').read_text('utf-8'))['bank_fixture'];base.peer.dump(args.output/'fixture.json',fixture)
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
        return {'identity':c['identity'],'language':c['page'],'pid':c['process'].pid,'bank_widget':bank,'bag_widget':widget(c,0x232dc8),
                'bank_label':label(c,bank,0) if bank is not None else None,
                'page_label':label(c,bank,2) if bank is not None else None,
                'target':number(c,c['ui']+0x839c0),'mode':number(c,c['ui']+0x855ed,1),
                'bank':number(c,c['ui']+0x839c4),'purse':number(c,c['ui']+0x85604),
                'current_page':number(c,c['ui']+0x839a4),'edition_field_232f64':number(c,c['ui']+0x232f64),
                'page_cache':list(struct.unpack('<6I',exact(c,c['ui']+0x839a8,24))),
                'bag':cells(c,0x8560c,50),'vault':cells(c,0x839cc,300),
                'sidebar_widget':sidebar,'selected_bank_slot':number(c,c['ui']+0x83994,2,True),'selected_bag_slot':number(c,c['ui']+0x855f0,2,True),
                'cursor_mode':number(c,c['ui']+0x232f36,2),'quantity_widget':widget(c,0x232dd0)}
    def saved():return {str(identity):owner_saved(database,identity) for identity in(4,5)}
    def untouched():
        with closing(base.peer.ro(database)) as db:
            output={}
            for name, in db.execute("select name from sqlite_master where type='table' order by name"):
                condition=' where character_id not in(4,5)' if name in TABLES else ''
                output[name]=sorted(repr(row) for row in db.execute('select * from "'+name.replace('"','""')+'"'+condition))
            return output
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
        require(source_guards()==fixture['mixed_bank_fixture']['source_contract'],'BANK_RUNTIME_SOURCES_CHANGED')
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
        require('OWNED_ARMOR_BANK_ENABLED' in log.read_text('utf-8',errors='replace'),'ACTUAL_ARMOR_BANK_STARTUP_MISSING')
        require('OWNED_FOREIGN_BANK_ENABLED' in log.read_text('utf-8',errors='replace'),'ACTUAL_FOREIGN_BANK_STARTUP_MISSING')
        for owner in clients:owner['instance_baseline']=instances(owner)
        invariant=untouched();result['initial']={'native':[snap(c) for c in clients],'db':saved(),'instances':[c['instance_baseline'] for c in clients]};save()
        contract=json.loads(CONTRACT.read_text('utf-8'));require(contract['startup_marker'] in log.read_text('utf-8',errors='replace'),'ACTUAL0070_APPLICATION_STARTUP_REQUIRED')
        def consistent(c,expected=None,check_vault=True):
            owner=owner_saved(database,c['identity']);now=snap(c);problems=[]
            if expected is not None:
                for table in TABLES:
                    if not table.endswith('receipts') and owner[table]!=expected[table]:problems.append({'table':table,'expected':expected[table],'actual':owner[table]})
            for storage,table in(('bag','diagnostic_inventory_slots'),('vault','character_bank_item_slots')):
                if storage=='vault' and not check_vault:continue
                scalar={r[1]:r for r in owner[table]}
                for cell in now[storage]:
                    slot=cell['slot'];row=scalar.get(slot);raw=bytes.fromhex(cell['raw']);qty=int.from_bytes(raw[:4],'little') if storage=='bag' else raw[0]
                    body=metadata(owner,storage,slot)
                    valid=qty==0 if row is None else qty==row[3] and cell['item']==row[2] and (body is None or raw[4:]==body)
                    if storage=='vault':valid=bool(valid and raw[1]==slot%50 and raw[2:4]==bytes(2) and (row is None or row[3]>0 or raw[4:]==bytes(20)))
                    if not valid:problems.append({'storage':storage,'slot':slot,'raw24':raw.hex(),'sql':row,'expected20':body.hex() if body else None})
            wallet=next(r for r in owner['character_trade_wallets']);bankmoney=next(r for r in owner['character_bank_balances'])
            if now['purse']!=wallet[1] or (check_vault and now['bank']!=bankmoney[1]):problems.append({'wallet':wallet,'bank':bankmoney,'native':[now['purse'],now['bank']]})
            result['last_observation']={'identity':c['identity'],'owner':owner,'native':now,'problems':problems}
            return None if problems else result['last_observation']
        def opened(c):
            state=base.ground.world_state(c['handle'],c['ui']);px,py=base.ground.ground_point(c['handle'],state,128,126);click(c['hwnd'],px,py-26)
            wait_until(lambda:widget(c,0x232dd2) is not None,8,'BANK_NOT_OPEN_BY_REAL_NPC37')
            wait_until(lambda:all(snap(c)['page_cache'][:3]),8,'BANK_ALL300_CACHE_NOT_LOADED')
            now=snap(c);require(now['target']==fixture['bank_fixture']['npc_target'] and now['mode']==0,'WRONG_NATIVE_BANK_CONTEXT')
            wait_until(lambda:consistent(c),10,'BANK_FULL50_FULL300_PROJECTION_MISMATCH')
            if widget(c,0x232dc8) is None:click(c['hwnd'],708,584);time.sleep(.5)
            wait_until(lambda:widget(c,0x232dc8) is not None,8,'BAG_NOT_OPEN')
            result['events'].append({'operation':'NPC37_bank_open','identity':c['identity'],'native':snap(c)});save()
        def page0(c):
            for _ in range(3):
                if snap(c)['current_page']==0:return
                control(c,widget(c,0x232dd2),52)
            require(snap(c)['current_page']==0,'BANK_PAGE0_UNAVAILABLE')
        def gesture(c,op,source,destination,qty,sourcecount):
            page0(c);bank=widget(c,0x232dd2);bag=widget(c,0x232dc8);require(bank is not None and bag is not None,'NATIVE_BANK_WINDOWS_REQUIRED')
            start=point(c,bag if op==0x63 else bank,source);end=unobscured_bank_point(c,bank,destination) if op==0x65 else point(c,bag if op==0x64 else bank,destination)
            result['events'].append({'operation':'actual_native_mouse_gesture','identity':c['identity'],'opcode':op,'source':source,'destination':destination,'page':0,'points':[start,end],'native65_marker':1 if op==0x65 else None});save()
            if op!=0x65:drag(c['hwnd'],start,end)
            else:
                import ctypes
                from ctypes import wintypes
                rect=wintypes.RECT();require(base.peer.user.GetClientRect(c['hwnd'],ctypes.byref(rect)),'BANK_CLIENT_RECT')
                sx,sy=round(start[0]*rect.right/800),round(start[1]*rect.bottom/600);ex,ey=round(end[0]*rect.right/800),round(end[1]*rect.bottom/600)
                def message(code,key,x,y):require(base.peer.user.PostMessageW(c['hwnd'],code,key,(y<<16)|x),'NATIVE_MOUSE_MESSAGE_FAILED');time.sleep(.25)
                message(0x200,0,sx,sy)
                try:
                    message(0x201,1,sx,sy);require(snap(c)['selected_bank_slot']==source,'NATIVE65_SOURCE_NOT_SELECTED')
                    end=unobscured_bank_point(c,bank,destination);ex,ey=round(end[0]*rect.right/800),round(end[1]*rect.bottom/600)
                    for step in range(1,11):message(0x200,1,sx+(ex-sx)*step//10,sy+(ey-sy)*step//10)
                finally:message(0x202,0,ex,ey)
            time.sleep(.45)
            if op!=0x65 and sourcecount>1:
                dialog=wait_until(lambda:widget(c,0x232dd0),8,'NATIVE_QUANTITY_MODAL_REQUIRED');require(number(c,c['ui']+0x23d5e4)==(2 if op==0x63 else 3),'NATIVE_QUANTITY_MODE')
                control(c,dialog,4);type_ascii(c['hwnd'],'\b'*9+str(qty));time.sleep(.3);require(number(c,c['ui']+0x23d5e8)==qty,'NATIVE_QUANTITY_EDIT');control(c,dialog,2)
            else:require(widget(c,0x232dd0) is None,'WHOLE_SWAP_UNEXPECTED_QUANTITY_MODAL')
        def protected(before,after):
            for table in('diagnostic_inventory_slots',*META):require([r for r in before[table] if r[1]>=30]==[r for r in after[table] if r[1]>=30],'EQUIPPED_OR_PROTECTED_FULL20_CHANGED')
            for table in('character_trade_wallets','character_bank_balances'):require(before[table]==after[table],'CURRENCY_CHANGED')
            require(quantity_inventory(before)==quantity_inventory(after),'COMPLETE_OWNER_QUANTITY_CONSERVATION')
            require(instance_inventory(before)==instance_inventory(after),'COMPLETE_INSTANCE20_ORIGIN_PROVENANCE_CONSERVATION')
            require(untouched()==invariant,'OTHER_PLAYERS_OR_PROTECTED_TABLES_CHANGED')
        def operation(c,peer,op,source,destination,qty,kind='transport',pair=None):
            before=owner_saved(database,c['identity']);peer_before=owner_saved(database,peer['identity']);peer_native=snap(peer)
            cell=next(r for r in before['diagnostic_inventory_slots' if op==0x63 else 'character_bank_item_slots'] if r[1]==source);sourcecount=cell[3]
            expected=expected_swap(before,source,destination) if op==0x65 else expected_transport(before,op,source,destination,qty)
            if pair:require([family(before,source),family(before,destination)]==list(pair),'ORDERED_PAIR_ACTUAL_START_FAMILY_MISMATCH')
            same_id_tail=pair==['WPN','WPN']
            if same_id_tail:
                a=metadata(before,'vault',source);b=metadata(before,'vault',destination)
                require(a[:2]==b[:2] and a!=b,'REAL_SAME_ID_DIFFERENT_TAILS_REQUIRED')
            markers_before=log.read_text('utf-8',errors='replace').count(contract['commit_marker'])
            gesture(c,op,source,destination,qty,sourcecount)
            wait_until(lambda:log.read_text('utf-8',errors='replace').count(contract['commit_marker'])==markers_before+1,12,'REAL_APPLICATION_EXACT_ONE_COMMIT_REQUIRED')
            proof=wait_until(lambda:consistent(c,expected),12,'MIXED_NATIVE_SQL_FULL20_FULL300_MISMATCH');after=proof['owner'];protected(before,after)
            require(owner_saved(database,peer['identity'])==peer_before and all(snap(peer)[key]==peer_native[key] for key in('bag','vault','purse','bank')),'OTHER_NATIVE_OWNER_CHANGED')
            ledger='character_bank_mixed_receipts' if op==0x65 else 'character_bank_armor_receipts' if any(r[1]==source for r in before['character_armor_slot_metadata' if op==0x63 else 'character_bank_armor_metadata']) else 'character_bank_foreign_receipts' if (any(r[1]==source for t in('character_weapon_slot_metadata','character_teleport_gem_metadata') for r in before[t]) if op==0x63 else any(r[1]==source for r in before['character_bank_foreign_metadata'])) else 'character_bank_item_receipts'
            for table in TABLES:
                if table.endswith('receipts') and table!=ledger:require(before[table]==after[table],'INCORRECT_OLD_OR_NEW_RECEIPT_LEDGER_MUTATED')
            old={r[0] for r in before[ledger]};added=[r for r in after[ledger] if r[0] not in old];require(len(added)==1 and len(after[ledger])==len(old)+1,'EXACT_ONE_ROUTE_RECEIPT_REQUIRED');receipt=added[0]
            require([r for r in after[ledger] if r[0] in old]==before[ledger],'PREEXISTING_SAME_LEDGER_RECEIPTS_CHANGED')
            require(receipt[1:8]==[c['identity'],c['identity'],op,0,source,destination,sourcecount if op==0x65 else qty],'RECEIPT_OWNER_OPCODE_WHOLE_QUANTITY_MISMATCH')
            if op==0x65:require(json.loads(receipt[8])==receipt_state(before,c['identity']) and json.loads(receipt[9])==receipt_state(expected,c['identity']) and receipt[-1]=='CUSTOM-0070','INDEPENDENT_COMPLETE_MIXED_RECEIPT_MISMATCH')
            elif ledger in('character_bank_armor_receipts','character_bank_foreign_receipts'):
                states=[receipt_state(state,c['identity']) for state in(before,expected)]
                if ledger=='character_bank_armor_receipts':states=[[*state[:5],state[6],state[7],state[5]] for state in states]
                require([json.loads(receipt[8]),json.loads(receipt[9])]==states,'EXACT_OLD_INSTANCE_RECEIPT_BEFORE_AFTER_MISMATCH')
            else:
                def plain_state(state):
                    parts=[]
                    for storage,slot in((op==0x64,source),(op==0x63,destination)):
                        r=next(row for row in state['character_bank_item_slots' if storage else 'diagnostic_inventory_slots'] if row[1]==slot)
                        parts.append(':'.join(str(v) for v in [int(storage),slot,*r[2:6],'CUSTOM-0015'])+';')
                    return ''.join(parts)
                require([receipt[8],receipt[9]]==[plain_state(before),plain_state(expected)],'EXACT_OLD_MED_RECEIPT_BEFORE_AFTER_MISMATCH')
            result['events'].append({'operation':'mixed_committed' if op==0x65 else 'transport_committed','identity':c['identity'],'language':c['page'],'opcode':op,'source':source,'destination':destination,'kind':kind,'ordered_pair':pair,'same_id_different_tail_verified':same_id_tail,'whole_qty':sourcecount,'wire65_marker':1 if op==0x65 else None,'full20_verified':True,'full50_verified':True,'full300_verified':True,'physical_revision_verified':True,'provenance_verified':True,'receipt_state_verified':True,'independent_plan_verified':True,'quantity_conservation':True,'whole_instance_conservation':True,'equipped_preserved':True,'peer_unchanged':True,'other_players_unchanged':True,'receipt':receipt,'before':before,'independently_expected':expected,'after':after,'native':proof['native']});save();return after
        for c in clients:
            peer=next(row for row in clients if row is not c);opened(c)
            count=fixture['mixed_bank_fixture']['med_totals'][str(c['identity'])]
            eqlist=[0,1] if c['identity']==4 else [2,3];teqlist=[2,3] if c['identity']==4 else [0,1]
            deposits=[(5,2,3),(5,3,count-3),*( (slot,4+i,1) for i,slot in enumerate(eqlist)),*((slot,6+i,1) for i,slot in enumerate(teqlist)),(8,8,1),(9,9,1),(10,10,1),(11,11,1),(12,12,1),(13,13,1)]
            for bag_slot,vault_slot,qty in deposits:operation(c,peer,0x63,bag_slot,vault_slot,qty)
            for a in FAMILIES:
                for b in FAMILIES:
                    current=owner_saved(database,c['identity']);sources=[r[1] for r in current['character_bank_item_slots'] if r[3] and family(current,r[1])==a];targets=[r[1] for r in current['character_bank_item_slots'] if r[3] and family(current,r[1])==b and r[1]!=sources[0]]
                    require(sources and targets,'TWO_INSTANCES_PER_FAMILY_REQUIRED');operation(c,peer,0x65,sources[0],targets[0],1,'ordered_pair',[a,b])
            for a in FAMILIES:
                current=owner_saved(database,c['identity']);source=next(r[1] for r in current['character_bank_item_slots'] if r[3] and family(current,r[1])==a)
                operation(c,peer,0x65,source,49,1,'empty_forward',[a,'EMPTY']);operation(c,peer,0x65,49,source,1,'empty_reverse',[a,'EMPTY'])
            # Close/open with a nonempty mixed bank to prove all300 cache rebuild.
            durable=owner_saved(database,c['identity']);control(c,widget(c,0x232dd2),54);wait_until(lambda:widget(c,0x232dd2) is None,5,'BANK_NORMAL39_CLOSE');opened(c);require(owner_saved(database,c['identity'])==durable,'REOPEN_CHANGED_OWNED_ROWS')
            # Return each whole record through its original class63/64 route.
            # MED arrives as two explicit cells; it never merges implicitly.
            occupied=[r[1] for r in durable['character_bank_item_slots'] if r[3]]
            destination_slots=[0,1,2,3,5,6,8,9,10,11,12,13]
            for source,destination in zip(occupied,destination_slots):
                current=owner_saved(database,c['identity']);qty=next(r[3] for r in current['character_bank_item_slots'] if r[1]==source);operation(c,peer,0x64,source,destination,qty)
            control(c,widget(c,0x232dd2),54);wait_until(lambda:widget(c,0x232dd2) is None,5,'BANK_FINAL39_CLOSE')
        durable=saved();old_pids=[c['process'].pid for c in clients]
        for c in reversed(clients):close(c)
        require(not any(psutil.pid_exists(pid) for pid in old_pids),'OLD_CLIENT_GENERATION_STILL_ALIVE');clients.clear()
        first=launch(4,950);other=launch(5,936)
        for c in clients:
            wait_until(lambda:consistent(c,durable[str(c['identity'])],False),12,'RELOGIN_FULL50_METADATA_NOT_RESTORED');opened(c);wait_until(lambda:consistent(c,durable[str(c['identity'])]),12,'RELOGIN_FULL300_METADATA_NOT_RESTORED')
            control(c,widget(c,0x232dd2),54);wait_until(lambda:widget(c,0x232dd2) is None,5,'RELOGIN_BANK_NORMAL_CLOSE')
        require(saved()==durable,'RELOGIN_CHANGED_ANY_OWNED_SAVE')
        new_pids=[c['process'].pid for c in clients];require(len(new_pids)==2 and not set(new_pids).intersection(old_pids),'NEW_REAL_CLIENT_GENERATION_REQUIRED')
        result['events'].append({'operation':'relogin_full50_full300','owners':[4,5],'old_client_pids':old_pids,'new_client_pids':new_pids,'old_clients_closed':True,'both_owner_saved_equal':True,'before':durable,'after':saved(),'native':[snap(c) for c in clients],'full20_verified':True,'full50_verified':True,'full300_verified':True})
        result['matrix_counts']={str(identity):{'pair65':sum(e['operation']=='mixed_committed' and e['identity']==identity and e['kind']=='ordered_pair' for e in result['events']),'empty65':sum(e['operation']=='mixed_committed' and e['identity']==identity and e['kind'].startswith('empty_') for e in result['events']),'deposit63':sum(e['operation']=='transport_committed' and e['identity']==identity and e['opcode']==0x63 for e in result['events']),'withdraw64':sum(e['operation']=='transport_committed' and e['identity']==identity and e['opcode']==0x64 for e in result['events'])} for identity in(4,5)}
        require(all(row==fixture['mixed_bank_fixture']['expected_per_owner'] for row in result['matrix_counts'].values()),'DUAL_LANGUAGE_ACTUAL_MATRIX_NOT_COMPLETE')
        for identity in(4,5):
            pairs=[tuple(e['ordered_pair']) for e in result['events'] if e['operation']=='mixed_committed' and e['identity']==identity and e['kind']=='ordered_pair'];require(set(pairs)=={(a,b) for a in FAMILIES for b in FAMILIES} and len(pairs)==36,'REAL_STARTING_FAMILY_MATRIX_REQUIRED')
        result['final']={'native':[snap(c) for c in clients],'db':saved()};result['scope']=SCOPE;result['unrelated_saved_rows_preserved']=True;result['accepted']=True
    except BaseException as error:
        result.update(error=str(error),traceback=traceback.format_exc())
        try:result['failure_native']=[snap(c) for c in clients if c.get('handle')];result['failure_saved']=saved()
        except Exception as checkpoint_error:result['failure_checkpoint_error']=str(checkpoint_error)
        save()
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
    parser.add_argument('--npc-hex',default='');parser.add_argument('--worker',action='store_true');parser.add_argument('--qualify-only',action='store_true');args=parser.parse_args()
    if args.qualify_only:print(json.dumps(qualify()));return 0
    if args.output is None:parser.error('--output required')
    if args.worker:return worker(args)
    if args.server_candidate is None:parser.error('--server-candidate required')
    require(base.sha(args.server_candidate)==candidate_sha(),'NEW_IMMUTABLE_FOREIGN_BANK_CANDIDATE')
    require(base.sha(ACCEPTED_ARMOR_TOOL)==ACCEPTED_ARMOR_SHA,'ACCEPTED_ARMOR_TOOL_CHANGED')
    source_before=source_guards();desktop_before=desktop_names()
    protected={str(p.pid):{'exe':p.info['exe'],'created':p.info['create_time']} for p in psutil.process_iter(['exe','create_time']) if p.info['exe'] and Path(p.info['exe']).name.lower() in ('god2.exe','god2-server.exe','leproc.exe','private_desktop_runner.exe')}
    frozen={str(path):base.sha(path) for path in (Path(__file__).resolve(),FOREIGN_V01_TOOL,FOREIGN_RUN01/'run-result.json',FOREIGN_RUN01/'ui-result.json',FOREIGN_RUN01/'town-diagnostic-accounts.db',ACCEPTED_ARMOR_TOOL,WEAPON_RECORDS,Path(armor_live.__file__).resolve(),Path(armor_catalog.__file__).resolve(),Path(base.__spec__.origin),Path(pose.__file__).resolve(),ROOT/'tools/strike_lab/private_potion_ui.py',ROOT/'tools/strike_lab/private_bank_swap_20261002.py',ROOT/'tools/strike_lab/private_inventory_move_ui.py',ROOT/'tools/strike_lab/private_trade_full_projection_20261003.py',OLD_BANK_TOOL,ROOT/'tools/strike_lab/private_owned_mixed_bank_20261003.py',ROOT/'artifacts/playtests/private-native-blackbox-owned-mixed-bank-20261003-01/run-result.json',ROOT/'tools/strike_lab/private_owned_mixed_bank_v02_20261003.py',ROOT/'artifacts/playtests/private-native-blackbox-owned-mixed-bank-20261003-02/run-result.json',ROOT/'artifacts/playtests/private-native-blackbox-owned-mixed-bank-20261003-02/ui-result.json',CONTRACT,SOURCE_RUN/'run-result.json',SOURCE_RUN/'ui-result.json',SOURCE_RUN/'town-diagnostic-accounts.db',SOURCE_RUN/'server-config.json',ARMOR_RUN/'run-result.json',ACCEPTED_ARMOR_RUN/'run-result.json',ACCEPTED_ARMOR_RUN/'ui-result.json',ACCEPTED_ARMOR_RUN/'town-diagnostic-accounts.db',ACCEPTED_ARMOR_RUN/'server-config.json')}
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
        result['scope']=SCOPE
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
            server=subprocess.Popen([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--run-for','960'],cwd=ROOT,env=env,
                stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);result['server_pid']=server.pid
            def listening():
                require(server.poll() is None,'PRIVATE_SERVER_EXITED')
                with socket.socket() as probe:return probe.connect_ex(('127.0.0.1',base.PORT))==0
            wait_until(listening,12,'PRIVATE_SERVER_NOT_LISTENING')
            runner=subprocess.Popen([str(base.RUNNER),sys.executable,'-X','utf8','-B',str(Path(__file__).resolve()),'--worker','--output',str(args.output),'--source-page',str(args.source_page)],cwd=ROOT,env=env,
                stdout=runnerlog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);result['runner_pid']=runner.pid
            result['runner_exit']=runner.wait(timeout=940);result['ui']=json.loads((args.output/'ui-result.json').read_text('utf-8'))
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
