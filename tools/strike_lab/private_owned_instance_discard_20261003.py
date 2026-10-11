"""NEW CUSTOM0071 whole owned typed27 discard UI acceptance; preparation only.

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

def compact_dump(path,value):
    # Lossless JSON: every event, full snapshot and raw receipt is retained.
    with path.open('w',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,separators=(',',':'))

EVENT_INDEX_KEYS=('operation','identity','account','language','opcode','source','quantity','kind','representative','family','charges','confirmation_enabled','confirmation_action')
EVENT_EVIDENCE_FORMAT='LOSSLESS_SHA256_EVENT_FILES_V1'

class EventJournal(list):
    """Persist every complete event exactly once; keep only its small index."""
    def __init__(self,output):
        super().__init__();self.output=output;self.directory=output/'ui-events'
        self.directory.mkdir(exist_ok=False)
    def append(self,event):
        relative=f'ui-events/event-{len(self):06d}.json'
        path=self.output/relative;temporary=path.with_suffix('.json.tmp')
        require(not path.exists() and not temporary.exists(),'EVENT_EVIDENCE_OVERWRITE_FORBIDDEN')
        compact_dump(temporary,event);os.replace(temporary,path)
        digest=hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
        index={key:event[key] for key in EVENT_INDEX_KEYS if key in event}
        index['evidence']={'path':relative,'sha256':digest.hexdigest(),'bytes':path.stat().st_size}
        super().append(index)

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


CONTRACT=ROOT/'artifacts/research/owned-instance-discard-0071/candidate-20261003/contract.json'
SOURCE=ROOT/'artifacts/releases/owned-mixed-bank-20261003/clone-stage/accounts.at-install.db'
SOURCE_CONFIG=SOURCE.with_name('server-config.after.json')
CREDENTIAL_FIXTURE=ROOT/'artifacts/playtests/private-native-blackbox-owned-foreign-bank-20261003-02/town-diagnostic-accounts.db'
PREDECESSOR=ROOT/'artifacts/research/owned-instance-discard-0071/predecessor-20261003'
SCOPE='OWNED_INSTANCE_DISCARD_TYPED27_TW_CN_CUSTOM_TEST_ONLY'
META={'character_armor_slot_metadata':'logical20','character_weapon_slot_metadata':'logical20','character_teleport_gem_metadata':'metadata20'}
LEDGER='character_owned_instance_discard_receipts'
SOURCE_SHA='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
GUIDE_SHA='1ff497204b5cf77cbbccffdf1836d7aeee30e46980ac1e85d8d0a08a0a4bcda7'
WEAPON_CLIENT='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
REPRESENTATIVES=[('EQU_HEAD',1201,2,0),('EQU_BODY',1001,2,0),('EQU_HAND',1501,2,0),('EQU_SHOE',1601,2,0),('TEQ_HEAD',20201,26,0),('TEQ_BODY',20001,26,0),('TEQ_HAND',20501,26,0),('TEQ_SHOE',20601,26,0),('WPN',1,1,0),('TWP',19001,25,0),('GEM1',16055,8,1),('GEM10',16055,8,10)]

def candidate_sha():
    contract=json.loads(CONTRACT.read_text('utf-8'));value=contract['candidate_sha256']
    require(re.fullmatch('[0-9a-f]{64}',value) and contract['design']=='CUSTOM-0071','NEW0071_CANDIDATE_CONTRACT_REQUIRED')
    require(contract['client_sha256']==base.CLIENT_SHA,'CURRENT_CLIENT_CONTRACT_PIN');return value

def source_guards():
    contract=json.loads(CONTRACT.read_text('utf-8'));expected=contract['source_sha256']
    require(expected and len(expected)>=36,'EXACT_FROZEN_RUNTIME_CONTRACT_REQUIRED')
    actual={key:base.sha(ROOT/key) for key in expected};require(actual==expected,'OWNED_DISCARD_RUNTIME_SOURCE_PINS');return actual

def qualify():
    raw=pose.qualify_source();mapped=pefile.PE(str(base.LIVE)).get_memory_mapped_image()
    regions=((0x496720,35),(0x4991e0,201),(0x49a330,1200),(0x4c9ed0,512),(0x4ca470,160),(0x4ea770,250),(0x4eb620,112),(0x4eaef0,600),(0x4f4f62,190),(0x4f5150,91),(0x4a6740,144),(0x4c7460,160))
    for va,size in regions:require(mapped[va-0x400000:va-0x400000+size]==raw[va-0x400000:va-0x400000+size],'NATIVE_DISCARD_CODE_CHANGED_'+hex(va))
    return {'current_client_sha256':base.sha(base.LIVE),'regions':regions,'no_ui_started':True,'authority':'STATIC_CODE_EQUALITY_ONLY_NOT_LIVE_ACCEPTANCE','source':'bag232DC8 selected855F0','delete':'bag control56 dragrelease/event20 ->27','confirmation':'actor449E bit10; option232DBC control11/event1; confirm232DF4 accept4/cancel3','quantity':'232DD0 mode4 accept2/cancel3','clear':'41 key/count clear; unused upper18 preserved permitted'}

def norm(v):return v.hex() if isinstance(v,bytes) else v

def saved(database):
    with closing(base.peer.ro(database)) as db:
        result={}
        for name, in db.execute("select name from sqlite_schema where type='table' order by name"):
            result[name]=[[norm(v) for v in row] for row in db.execute('select * from "'+name.replace('"','""')+'" order by rowid')]
        return result

def typed_rows(database,name,exclude_owner=None):
    with closing(base.peer.ro(database)) as db:
        sql='select * from "'+name+'"'+(' where character_id<>?' if exclude_owner is not None else '')+' order by rowid'
        records=db.execute(sql,(exclude_owner,) if exclude_owner is not None else ())
        def typed(v):
            if v is None:return [5,None]
            if isinstance(v,int):return [1,v]
            if isinstance(v,float):return [2,v]
            if isinstance(v,bytes):return [4,list(v)]
            return [3,list(v.encode('utf-8'))]
        return json.dumps([[typed(v) for v in row] for row in records],ensure_ascii=False,separators=(',',':'))

def peripheral(database,identity):
    with closing(base.peer.ro(database)) as db:
        names=[row[0] for row in db.execute("select name from sqlite_schema where type='table' and (name glob 'character_*' or name glob 'diagnostic_*' or name glob 'recovered_*' or name glob 'battle_*' or name in('characters','accounts')) and name<>? order by name",(LEDGER,))]
    return json.dumps([[name,typed_rows(database,name,identity if name in ('diagnostic_inventory_slots',*META) else None)] for name in names],ensure_ascii=False,separators=(',',':'))

def snapshot_state(state,identity,account,peripheral_text):
    scalar={r[1]:r for r in state['diagnostic_inventory_slots'] if r[0]==identity}
    armor=[];weapons=[];gems=[]
    for r in state['character_armor_slot_metadata']:
        if r[0]==identity:
            cell=scalar[r[1]];armor.append([r[1],cell[2],cell[3],r[3],list(bytes.fromhex(r[2])),r[4],r[5],True,SOURCE_SHA,base.CLIENT_SHA,'CUSTOM-0066'])
    for table,target in [('character_weapon_slot_metadata',weapons),('character_teleport_gem_metadata',gems)]:
        for r in state[table]:
            if r[0]==identity:target.append([r[1],list(bytes.fromhex(r[2])),r[3],r[4],r[5],r[6],r[7] if table=='character_weapon_slot_metadata' else '',r[-1]])
    return [account,identity,[[scalar[i][2],scalar[i][3],scalar[i][4],scalar[i][5]] if i in scalar else None for i in range(50)],sorted(armor),sorted(weapons),sorted(gems),peripheral_text]

def metadata(state,identity,slot):
    cell=next((r for r in state['diagnostic_inventory_slots'] if r[:2]==[identity,slot]),None)
    if cell is None or cell[3]==0:return None
    overlays=[r for table in META for r in state[table] if r[:2]==[identity,slot]]
    require(len(overlays)<=1,'OWNED_OVERLAY_CONFLICT')
    return bytes.fromhex(overlays[0][2]) if overlays else struct.pack('<H',cell[2])+bytes(18)

def expected_discard(before,identity,slot,quantity,typed=True):
    after=copy.deepcopy(before);cell=next(r for r in after['diagnostic_inventory_slots'] if r[:2]==[identity,slot]);old=list(cell)
    require(0<quantity<=cell[3] and slot<30 and (not typed or quantity==cell[3]==1),'DISCARD_REQUEST_AUTHORITY')
    cell[3]-=quantity;cell[2]=cell[2] if cell[3] else 0;cell[4]+=1
    if not cell[3]:
        for table in META:after[table]=[r for r in after[table] if r[:2]!=[identity,slot]]
    return after,old

def private_copy(args):
    require(base.sha(base.LIVE)==base.CLIENT_SHA and base.sha(base.RUNNER)==base.RUNNER_SHA,'CURRENT_CLIENT_OR_RUNNER_PIN_CHANGED')
    args.output.mkdir(parents=True,exist_ok=False);database=args.output/'town-diagnostic-accounts.db'
    raw=base.LIVE.read_bytes();needle=bytes.fromhex('68 20 0a 00 00 68 9c 47 5b 00');require(raw.count(needle)==1,'UNIQUE_base.PORT_SITE_REQUIRED')
    changed=bytearray(raw);offset=raw.index(needle)+1;struct.pack_into('<I',changed,offset,base.PORT)
    clients={}
    for page,locale,zone in ((950,'zh-TW','Taipei Standard Time'),(936,'zh-CN','China Standard Time')):
        image=base.LIVE.with_name(args.output.name+'-'+str(page)+'-2598.exe');profile=Path(str(image)+'.le.config')
        require(not image.exists() and not profile.exists(),'NEW_PRIVATE_IMAGE_AND_PROFILE_REQUIRED')
        with image.open('xb') as stream:stream.write(changed)
        xml='<LEConfig><Profiles><Profile Name="God2 Chinese" Guid="9548b642-f82c-4883-a523-425904744e6f" MainMenu="false"><Parameter></Parameter><Location>'+locale+'</Location><Timezone>'+zone+'</Timezone><RunAsAdmin>false</RunAsAdmin><RedirectRegistry>false</RedirectRegistry><IsAdvancedRedirection>false</IsAdvancedRedirection><RunWithSuspend>false</RunWithSuspend></Profile></Profiles></LEConfig>'
        with profile.open('x',encoding='utf-8') as stream:stream.write(xml)
        clients[str(page)]={'path':str(image),'sha256':base.sha(image),'profile':str(profile),'profile_sha256':base.sha(profile)}
    global PRIVATE_CLIENTS
    PRIVATE_CLIENTS=clients
    with closing(base.peer.ro(SOURCE)) as source,closing(sqlite3.connect(database)) as target:source.backup(target)
    config=json.loads(SOURCE_CONFIG.read_text('utf-8'));config['database']['path']=str(database)
    config['logging']['file']=str(args.output/'server.log');config['server'].update(host='127.0.0.1',port=base.PORT,character_port=0)
    config['development']['diagnostic_remote_actor_language']=int(args.source_page==936)
    base.peer.dump(args.output/'server-config.json',config)
    env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1'
    with (args.output/'migration.log').open('wb') as log:
        subprocess.run([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--migrate-only'],cwd=ROOT,env=env,
            check=True,timeout=60,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)

def prepare(args):
    require(base.sha(args.server_candidate)==candidate_sha(),'IMMUTABLE0071_CANDIDATE');private_copy(args)
    database=args.output/'town-diagnostic-accounts.db'
    config=json.loads((args.output/'server-config.json').read_text('utf-8'));config['world']['owned_instance_discard']={'enabled':True}
    require(config['world']['owned_armor_transfers']['enabled'] and config['world']['owned_supply']['enabled'],'FORMAL_EXISTING_ARMOR_MED_FLAGS_REQUIRED');require(not config['world'].get('owned_weapon_transfers',{}).get('enabled',False),'FORMAL_WEAPON_TRANSFER_FALSE_BASELINE_REQUIRED')
    base.peer.dump(args.output/'server-config.json',config)
    owners=[];original_saved=saved(database)
    with closing(sqlite3.connect(database)) as db,closing(base.peer.ro(CREDENTIAL_FIXTURE)) as credentials:
        db.execute('pragma foreign_keys=on');require(db.execute('select count(*) from schema_migrations where version=47').fetchone()==(1,),'REAL_SCHEMA47_REQUIRED')
        next_account=db.execute('select coalesce(max(id),0)+1 from accounts').fetchone()[0];next_identity=db.execute('select coalesce(max(id),0)+1 from recovered_characters').fetchone()[0]
        for ordinal,page in enumerate((950,936)):
            account=next_account+ordinal;identity=next_identity+ordinal;username='codexdiscard'+str(ordinal);name=('D071TW' if page==950 else 'D071CN').encode('ascii')
            hash_value=credentials.execute('select password_hash from accounts where id=?',(4+ordinal,)).fetchone()[0]
            profile=bytearray(credentials.execute('select profile from recovered_characters where id=?',(4+ordinal,)).fetchone()[0]);profile[:28]=name+bytes(28-len(name))
            db.execute('insert into accounts(id,username,password_hash) values(?,?,?)',(account,'god2-bytes:'+username.encode('ascii').hex(),hash_value))
            db.execute('insert into recovered_characters(id,account_id,slot,profile,name_bytes,name_codepage,streamer_privilege) values(?,?,0,?,?,?,0)',(identity,account,bytes(profile),name,page))
            db.execute('insert into recovered_positions values(?,4,3,?,132,1)',(identity,126+3*ordinal))
            guide_enabled=config['development'].get('diagnostic_town',{}).get('quest_progress',False)
            if guide_enabled:
                # Isolated CUSTOM_TEST prerequisite, including its real paired
                # reward receipt. Never bypass or weaken the production slot0 guard.
                db.execute("insert into diagnostic_town_guide_progress values(?,3,0,1,?,'CUSTOM-0021')",(identity,GUIDE_SHA))
                db.execute("insert into diagnostic_town_guide_reward values(?,1,28,1,5569,1,?,'CUSTOM-0022')",(identity,SOURCE_SHA))
            for slot in range(50):db.execute("insert into diagnostic_inventory_slots values(?,?,0,0,1,?,'CUSTOM-0015')",(identity,slot,SOURCE_SHA))
            if guide_enabled:db.execute('update diagnostic_inventory_slots set item_id=5569,count=1 where character_id=? and slot=28',(identity,))
            phases=[]
            for phase in range(2):
                batch=[]
                for index,(label,key,family,charges) in enumerate(REPRESENTATIVES):
                    slot=(0 if phase==0 else 29) if label=='WPN' else next(s for s in range(1,23) if all(s!=r['source'] for group in phases for r in group) and all(s!=r['source'] for r in batch))
                    raw=bytearray(20);struct.pack_into('<H',raw,0,key);raw[2]=family;raw[3]=charges<<1 if family==8 else 0;raw[8:12]=bytes([identity&255,index+1,phase+1,9]);raw[19]=0x21+phase
                    db.execute('update diagnostic_inventory_slots set item_id=?,count=1 where character_id=? and slot=?',(key,identity,slot))
                    origin='CUSTOM_TEST_NOT_NATIVE';provenance=f'NEW0071 owner={identity} phase={phase} representative={label} synthetic opaque20 not native drop/stat'
                    if family in(2,26):db.execute("insert into character_armor_slot_metadata values(?,?,?,1,?,?,?,?,'CUSTOM-0066')",(identity,slot,bytes(raw),origin,provenance,SOURCE_SHA,base.CLIENT_SHA))
                    elif family in(1,25):db.execute("insert into character_weapon_slot_metadata values(?,?,?,1,?,?,?,?,'CUSTOM-0046')",(identity,slot,bytes(raw),origin,provenance,SOURCE_SHA,WEAPON_CLIENT))
                    else:db.execute("insert into character_teleport_gem_metadata values(?,?,?,1,?,?,?,'CUSTOM-0057')",(identity,slot,bytes(raw),origin,provenance,SOURCE_SHA))
                    batch.append({'representative':label,'item':key,'family':family,'charges':charges,'source':slot,'logical20':raw.hex()})
                phases.append(batch)
            for slot,count in ((24,7),(25,1)):db.execute('update diagnostic_inventory_slots set item_id=3107,count=? where character_id=? and slot=?',(count,identity,slot))
            for slot in(27,):
                raw=struct.pack('<H',1)+bytes([1,0])+bytes([identity&255,slot])+bytes(14)
                db.execute('update diagnostic_inventory_slots set item_id=1,count=1 where character_id=? and slot=?',(identity,slot))
                db.execute("insert into character_weapon_slot_metadata values(?,?,?,1,'CUSTOM_TEST_NOT_NATIVE',?,?,?,'CUSTOM-0046')",(identity,slot,raw,'NEW0071 preserved trade/equipped fixture',SOURCE_SHA,WEAPON_CLIENT))
            raw=struct.pack('<H',1201)+bytes([2,0])+bytes([identity&255,30])+bytes(14)
            db.execute('update diagnostic_inventory_slots set item_id=1201,count=1 where character_id=? and slot=30',(identity,))
            db.execute("insert into character_armor_slot_metadata values(?,30,?,1,'CUSTOM_TEST_NOT_NATIVE',?,?,?,'CUSTOM-0066')",(identity,raw,'NEW0071 protected native head30 fixture',SOURCE_SHA,base.CLIENT_SHA))
            owners.append({'identity':identity,'account':account,'username':username,'page':page,'phases':phases,'ordinary_trade_source':27,'equipped_source':30})
        db.commit();require(db.execute('pragma quick_check').fetchone()==('ok',) and db.execute('pragma foreign_key_check').fetchone() is None,'NEW0071_CLONE_INTEGRITY')
    seeded=saved(database);require(all(seeded[name][:len(rows)]==rows for name,rows in original_saved.items() if name!='sqlite_sequence'),'ALL_SOURCE_PLAYERS_ROWS_NOT_PRESERVED_IN_CLONE')
    created_rows={name:rows[len(original_saved.get(name,[])):] for name,rows in seeded.items() if name!='sqlite_sequence'}
    fixture={'source_saved_rows_preserved':True,'created_rows':created_rows,'formal_owned_weapon_transfers_enabled':False,'authority':'CUSTOM_TEST_NOT_NATIVE','source_database':str(SOURCE),'source_sha256':base.sha(SOURCE),'client_source_sha256':base.CLIENT_SHA,'owners':owners,'candidate_sha256':candidate_sha(),'source_contract':source_guards(),'clients':PRIVATE_CLIENTS,'source_page':args.source_page,'expected_counts':{'typed_discard':48,'confirmation_cancel':24,'med_discard':4,'equipped_refusal':2,'trade_refusal':2,'relogin_full50':1}}
    base.peer.dump(args.output/'fixture.json',fixture)


def worker(args):
    import ctypes
    from ctypes import wintypes
    before_desktop=desktop_names();clients=[];loaders=[]
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'));database=args.output/'town-diagnostic-accounts.db';log=args.output/'server.log';contract=json.loads(CONTRACT.read_text('utf-8'))
    result={'accepted':False,'events':EventJournal(args.output),'event_evidence_format':EVENT_EVIDENCE_FORMAT,'rendered_pixels_tested':False,'source_page':args.source_page};last_saved=0.0
    def save(force=False):
        nonlocal last_saved
        if force or time.monotonic()-last_saved>=30:compact_dump(args.output/'ui-result.json',result);last_saved=time.monotonic()
    def exact(c,a,n):return base.peer.exact(c['handle'],a,n)
    def number(c,a,n=4,signed=False):return int.from_bytes(exact(c,a,n),'little',signed=signed)
    def widget(c,offset):
        w=number(c,c['ui']+offset,2,True)
        return w if 0<=w<128 and exact(c,c['ui']+0xe2988+w*0x2a08,1)[0]&0x20 else None
    def visible(c,offset,timeout,message):return wait_until(lambda:{'w':widget(c,offset)} if widget(c,offset) is not None else None,timeout,message)['w']
    def event(value):result['events'].append(value);save()
    def msg(c,code,key,xy,delay=.12):
        rect=wintypes.RECT();require(base.peer.user.GetClientRect(c['hwnd'],ctypes.byref(rect)),'NATIVE_CLIENT_RECT')
        x,y=round(xy[0]*rect.right/800),round(xy[1]*rect.bottom/600)
        require(base.peer.user.PostMessageW(c['hwnd'],code,key,(y<<16)|x),'NORMAL_NATIVE_MESSAGE_FAILED');time.sleep(delay)
    def point(c,w,index):
        xy,proof=armor_live.hit_point(c,w,index);event({'operation':'native_control_hit_selection','identity':c['identity'],'widget':w,'index':index,'proof':proof});return xy
    def checkpoint(c,w,index,xy,phase):
        entry=c['ui']+0xe2170+w*0x2a08+0x8b8+index*100;raw=exact(c,entry,100);hit=int.from_bytes(raw[8:10],'little',signed=True)
        require(0<=hit<0xc00,'REGISTERED_CONTROL_HIT_DOMAIN');mouse=number(c,c['ui']+0xe2174)
        registered=list(struct.unpack('<6i',exact(c,mouse+hit*24,24)));layout=armor_live.hit_layout(c);matches=armor_live.hits(layout,xy);network=number(c,c['ui']+0x86874)
        length=number(c,network+0x36c4);require(length<=0xa00,'NATIVE_QUEUE_BOUNDS')
        value={'operation':'native27_input_checkpoint','identity':c['identity'],'widget':w,'index':index,'phase':phase,'point':list(xy),'control_raw100':raw.hex(),'hit_id':hit,'registered_hit24':registered,'layout':layout,'point_hits':matches,'selected_bag_source':number(c,c['ui']+0x855f0,2,True),'queue_length':length,'queue':exact(c,network+0x36c8,length).hex(),'confirmation_mode':number(c,c['ui']+0xafece,1),'trade_active':number(c,c['ui']+0x866e4)}
        if index<50:value.update(source_native24=exact(c,c['ui']+0x8560c+index*24,24).hex(),source_cached_key=number(c,c['ui']+0x85610+index*24,2))
        event(value);return value
    def hit_matches(value,w,index):
        top=value['point_hits'][0] if value['point_hits'] else None;raw=bytes.fromhex(value['control_raw100']);rect=value['registered_hit24']
        return bool(raw[0] and rect[0] and top and top['widget']==w and top['index']==index and top['hit_id']==value['hit_id'] and top['rect']==rect[1:5])
    def control(c,w,index):
        xy=point(c,w,index);msg(c,0x200,0,xy);xy=point(c,w,index);check=checkpoint(c,w,index,xy,'before_control_press');require(hit_matches(check,w,index),'NORMAL_CONTROL_TOP_HIT_REQUIRED')
        try:msg(c,0x201,1,xy)
        finally:msg(c,0x202,0,xy)
    def snap(c):
        actor=number(c,c['ui']+0x86888);require(actor>0x10000,'CURRENT_LOCAL_ACTOR_REQUIRED')
        return {'identity':c['identity'],'account':c['account'],'language':c['page'],'pid':c['process'].pid,'actor':actor,'option449E':number(c,actor+0x449e,1),'bag_widget':widget(c,0x232dc8),'options_widget':widget(c,0x232dbc),'confirmation_widget':widget(c,0x232df4),'confirmation_mode':number(c,c['ui']+0xafece,1),'confirmation_item':number(c,c['ui']+0xafecc,2),'confirmation_source':number(c,c['ui']+0xafec8,4),'confirmation_quantity':number(c,c['ui']+0xafecf,1),'quantity_widget':widget(c,0x232dd0),'selected_bag_source':number(c,c['ui']+0x855f0,2,True),'trade_active':number(c,c['ui']+0x866e4),'trade_widget':widget(c,0x232dae),'peer':number(c,c['ui']+0x866d0,2),'bag':[{'slot':s,'raw24':exact(c,c['ui']+0x8560c+s*24,24).hex()} for s in range(50)]}
    def consistent(c):
        current=saved(database);native=snap(c);scalar={r[1]:r for r in current['diagnostic_inventory_slots'] if r[0]==c['identity']};rows=[];problems=[]
        for cell in native['bag']:
            slot=cell['slot'];row=scalar.get(slot);raw=bytes.fromhex(cell['raw24']);quantity=int.from_bytes(raw[:4],'little');body=metadata(current,c['identity'],slot)
            valid=quantity==0 if row is None or row[3]==0 else quantity==row[3] and int.from_bytes(raw[4:6],'little')==row[2] and raw[4:]==body
            data={'slot':slot,'raw24':raw.hex(),'sql_scalar':row,'expected20':body.hex() if body else None,'valid':valid};rows.append(data)
            if not valid:problems.append(data)
        result['last_projection']={'identity':c['identity'],'native':native,'full50':rows,'problems':problems}
        return None if problems else result['last_projection']
    def bag(c):
        if widget(c,0x232dc8) is None:click(c['hwnd'],708,584)
        return visible(c,0x232dc8,8,'REAL_BAG_NOT_OPEN')
    def requests(c):
        return [line for line in log.read_text('utf-8',errors='replace').splitlines() if contract['request_marker'] in line and 'session_id='+str(c['session'])+' ' in line]
    def discard_gesture(c,slot,assert_selected=True):
        w=bag(c);before=saved(database);source=exact(c,c['ui']+0x8560c+slot*24,24);body=metadata(before,c['identity'],slot)
        require(body is not None and source[4:]==body and int.from_bytes(source[:4],'little')==next(r[3] for r in before['diagnostic_inventory_slots'] if r[:2]==[c['identity'],slot]),'DISCARD_SOURCE_FULL24_QUALIFIED_SQL')
        msg(c,0x200,0,(350,410));xy=point(c,w,slot);msg(c,0x200,0,xy);xy=point(c,w,slot);hover=checkpoint(c,w,slot,xy,'after_source_hover');require(hit_matches(hover,w,slot),'SOURCE_REGISTERED_TOP_HIT_REQUIRED')
        require(hover['source_native24']==source.hex() and hover['source_cached_key']==int.from_bytes(body[:2],'little'),'SOURCE_FULL24_CACHED_KEY_REQUIRED')
        release=xy;pressed=False
        try:
            msg(c,0x201,1,xy);pressed=True;selected=checkpoint(c,w,slot,xy,'source_pressed')
            if assert_selected:require(selected['selected_bag_source']==slot,'NATIVE27_SOURCE_NOT_SELECTED')
            require(selected['source_native24']==source.hex() and selected['source_cached_key']==int.from_bytes(body[:2],'little'),'SELECTED_SOURCE_FULL24_KEY_REQUIRED')
            end=point(c,w,56)
            for step in range(1,11):release=(round(xy[0]+(end[0]-xy[0])*step/10),round(xy[1]+(end[1]-xy[1])*step/10));msg(c,0x200,1,release,.08)
            target=checkpoint(c,w,56,end,'before_delete_release');require(hit_matches(target,w,56),'NATIVE_DISCARD_CONTROL56_TOP_HIT_REQUIRED')
        finally:
            if pressed:msg(c,0x202,0,release)
        event({'operation':'actual_native27_drag','identity':c['identity'],'source':slot,'source_native24':source.hex(),'normal_release_posted':pressed,'release_point':list(release)})
    def open_options(c):
        if widget(c,0x232dbc) is not None:return
        if widget(c,0x232e4e) is None:
            for code,key,data in ((0x100,0x11,1),(0x100,0x48,1),(0x101,0x48,0xc0000001),(0x101,0x11,0xc0000001)):
                require(base.peer.user.PostMessageW(c['hwnd'],code,key,data),'OPTIONS_NORMAL_MENU_KEY_FAILED');time.sleep(.1)
        w=visible(c,0x232e4e,8,'OPTIONS_NATIVE_MAIN_MENU_REQUIRED');control(c,w,26)
        wait_until(lambda:number(c,c['ui']+0xa3cf4)==26,5,'OPTIONS_NATIVE_CATEGORY26_NOT_SELECTED');control(c,w,27)
        visible(c,0x232dbc,8,'OPTIONS_NATIVE_SUBMENU27_NOT_OPEN')
        event({'operation':'normal_options_open','identity':c['identity'],'category26':number(c,c['ui']+0xa3cf4),'widget':widget(c,0x232dbc),'caller':'4A6D90 controls26/27 ->4A6760(4,0) ->4F4A80/4F4AC0'})
    def close_options(c):
        w=visible(c,0x232dbc,8,'OPTIONS_NATIVE_CLOSE_WINDOW_REQUIRED');control(c,w,14)
        wait_until(lambda:widget(c,0x232dbc) is None,8,'OPTIONS_CONTROL14_NOT_CLOSED')
    def set_confirmation(c,enabled):
        before=saved(database);old=snap(c);actor=old['actor']
        if bool(old['option449E']&0x10)!=enabled:
            open_options(c);w=visible(c,0x232dbc,8,'ORIGINAL_OPTIONS_WIDGET_REQUIRED');control(c,w,11)
            wait_until(lambda:bool(number(c,actor+0x449e,1)&0x10)==enabled,5,'NORMAL_OPTION_BIT10_NOT_TOGGLED')
            close_options(c)
        after=snap(c);require(bool(after['option449E']&0x10)==enabled and (old['option449E']^after['option449E']) in (0,0x10),'OPTION_CHANGED_UNRELATED_BITS');require(saved(database)==before,'OPTION_CHANGED_SAVED_PLAYER_ROWS')
        event({'operation':'normal_option_toggle','identity':c['identity'],'account':c['account'],'language':c['page'],'confirmation_enabled':enabled,'before':old,'after':after,'all_saved_rows_unchanged':True,'normal_UI_only':True})
    def verify_discard(c,definition,confirmation,quantity=1,typed=True):
        slot=definition['source'];before=saved(database);periph=peripheral(database,c['identity']);prior=requests(c);expected,source=expected_discard(before,c['identity'],slot,quantity,typed);before_native=snap(c)
        before_state=snapshot_state(before,c['identity'],c['account'],periph);after_state=snapshot_state(expected,c['identity'],c['account'],periph)
        discard_gesture(c,slot)
        if source[3]>1:
            q=visible(c,0x232dd0,8,'QUANTITY_DIALOG_REQUIRED');require(number(c,c['ui']+0x23d5e4)==4,'DISCARD_QUANTITY_NATIVE_MODE4');control(c,q,4);type_ascii(c['hwnd'],'\b'*9+str(quantity));time.sleep(.3);require(number(c,c['ui']+0x23d5e8)==quantity,'DISCARD_QUANTITY_EDIT');control(c,q,2)
        if confirmation:
            w=visible(c,0x232df4,8,'CONFIRMATION_REQUIRED');n=snap(c);require([n['confirmation_mode'],n['confirmation_item'],n['confirmation_source'],n['confirmation_quantity']]==[5,source[2],slot,quantity],'NATIVE_CONFIRMATION_TYPED_SOURCE');require(saved(database)==before,'CONFIRM_PRECOMMIT_SAVED_MUTATION');control(c,w,4)
        def changed():
            actual=saved(database)
            for table in before:
                if table==LEDGER:continue
                if actual[table]!=expected[table]:return None
            proof=consistent(c)
            return {'after':actual,'projection':proof} if proof else None
        try:observed=wait_until(changed,12,'DISCARD_COMPLETE_SQL_NATIVE_PROJECTION_MISMATCH')
        except BaseException:
            result['last_failed_expected']=expected;result['last_failed_actual']=saved(database);save(True);raise
        after=observed['after'];native=observed['projection'];deleted=bytes.fromhex(native['native']['bag'][slot]['raw24'])
        require(int.from_bytes(deleted[:4],'little')==source[3]-quantity and int.from_bytes(deleted[4:6],'little')==(source[2] if source[3]>quantity else 0),'NATIVE41_ACTIVE_KEY_COUNT_NOT_CLEARED')
        require(before_native['bag'][slot]['raw24'][12:]==native['native']['bag'][slot]['raw24'][12:],'NATIVE41_INACTIVE_UPPER18_UNEXPECTED_REWRITE')
        for other in clients:
            if other is not c:require(consistent(other),'PEER_FULL50_NOT_PRESERVED')
        guards={'full50_verified':True,'full20_verified':True,'all_other_saved_rows_unchanged':True,'equipped_preserved':True,'other_players_unchanged':True,'physical_revisions_verified':True}
        receipt=None
        if typed:
            old_receipts=before[LEDGER];new=after[LEDGER];require(len(new)==len(old_receipts)+1 and new[:-1]==old_receipts,'EXACT_NEW_DISCARD_LEDGER_ADDITION');receipt=new[-1]
            overlay=[(table,r) for table in META for r in before[table] if r[:2]==[c['identity'],slot]];require(len(overlay)==1,'TYPED_SELECTED_OVERLAY_REQUIRED');table,row=overlay[0];kind=1 if table=='character_armor_slot_metadata' else 2 if table=='character_weapon_slot_metadata' else 3
            require(receipt[1:7]==[c['account'],c['identity'],39,source[2],slot,1] and receipt[7]==kind and receipt[8]==row[2] and receipt[9:12]==row[4:7] and receipt[12]==(row[7] if kind in(1,2) else '') and receipt[13]==row[-1] and json.loads(receipt[14])==before_state and json.loads(receipt[15])==after_state and receipt[16]=='CUSTOM-0071','DISCARD_EXACT_FULL20_PROVENANCE_RECEIPT_MISMATCH')
            new_markers=requests(c)[len(prior):];require(len(new_markers)==1 and contract['commit_marker'] in new_markers[0],'ACTUAL_APPLICATION_TYPED27_COMMIT_REQUIRED');guards.update(receipt_verified=True,independent_plan_verified=True,provenance_preserved=True)
        else:require(after[LEDGER]==before[LEDGER],'SCALAR_MED_WRONG_TYPED_LEDGER')
        event({'operation':'typed_discard' if typed else 'med_discard','identity':c['identity'],'account':c['account'],'language':c['page'],'opcode':39,'source':slot,'quantity':quantity,'kind':definition.get('representative','MED'),'representative':definition.get('representative','MED'),'family':definition.get('family','MED'),'charges':definition.get('charges',0),'confirmation_enabled':confirmation,'confirmation_action':'accept' if confirmation else 'none','before':before,'independently_expected':expected,'after':after,'before_expected':before_state,'after_expected':after_state,'actual_receipt':receipt,'native_before':before_native,'native_after':native,**guards})
    def cancel_confirmation(c,definition):
        before=saved(database);prior=requests(c);native=snap(c);discard_gesture(c,definition['source']);w=visible(c,0x232df4,8,'CANCEL_CONFIRMATION_REQUIRED');pending=snap(c)
        require(pending['confirmation_mode']==5 and pending['confirmation_item']==definition['item'] and pending['confirmation_source']==definition['source'] and pending['confirmation_quantity']==1,'CONFIRM_CANCEL_REAL_SOURCE')
        control(c,w,3);wait_until(lambda:number(c,c['ui']+0xafece,1)==255 and widget(c,0x232df4) is None,8,'CANCEL_CONFIRMATION_NOT_RETIRED')
        require(saved(database)==before and requests(c)==prior and consistent(c),'CONFIRM_CANCEL_CHANGED_DB_OR_SENT27');after=snap(c)
        require(native['bag']==after['bag'],'CONFIRM_CANCEL_CHANGED_FULL50_NATIVE_RAW24')
        event({'operation':'confirmation_cancel','identity':c['identity'],'account':c['account'],'language':c['page'],'source':definition['source'],'opcode':39,'quantity':1,'representative':definition['representative'],'family':definition['family'],'charges':definition['charges'],'confirmation_enabled':True,'confirmation_action':'cancel','before':before,'after':saved(database),'native_before':native,'pending_confirmation':pending,'native_after':after,'all_saved_rows_unchanged':True,'full_native_restored':True,'no27_request_sent':True,'full50_verified':True,'full20_verified':True})
    def close(c):
        if c.get('handle'):base.peer.kernel.CloseHandle(c.pop('handle'))
        if c['process'].is_running():
            base.peer.user.PostMessageW(c['hwnd'],0x10,0,0)
            try:c['process'].wait(timeout=4)
            except psutil.TimeoutExpired:c['process'].terminate();c['process'].wait(timeout=5)
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
        before_db=saved(database);lines=log.read_text('utf-8',errors='replace').splitlines()
        bound=[line for line in lines if 'RECOVERED_ACCOUNT_BOUND account_id='+str(source['account'])+';' in line]
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
        require(saved(database)==before_db,'ACTOR_OPEN_CHANGED_DURABLE_STATE')
    def opened(source,target):
        result['trade_before']=saved(database)
        for c in (source,target):
            if widget(c,0x232dc8) is not None:click(c['hwnd'],708,584)
        for c,peer in ((source,target),(target,source)):wait_until(lambda:base.peer.remote(c['handle'],c['ui'],peer['identity']),10,'NATIVE_PEER_NOT_VISIBLE')
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
    def refusal(c,slot,kind):
        before=saved(database);native=snap(c);prior=requests(c)
        if kind=='trade_refusal':require(native['trade_active']!=0 and native['trade_widget'] is not None,'REAL_ACTIVE_TRADE_REQUIRED')
        discard_gesture(c,slot,assert_selected=False);time.sleep(.6)
        require(saved(database)==before and requests(c)==prior,'REFUSAL_CHANGED_DB_OR_SENT_TYPED27');require(consistent(c),'REFUSAL_FULL50_NOT_PRESERVED')
        after=snap(c);require(native['bag']==after['bag'],'REFUSAL_CHANGED_NATIVE_FULL20')
        require(widget(c,0x232df4) is None,'LOCAL_REFUSAL_UNEXPECTED_CONFIRMATION')
        event({'operation':kind,'identity':c['identity'],'account':c['account'],'language':c['page'],'source':slot,'opcode':39,'before':before,'after':saved(database),'native_before':native,'native_after':after,'all_saved_rows_unchanged':True,'full_native_restored':True,'full50_verified':True,'full20_verified':True,'scope':'ORIGINAL_CLIENT_LOCAL_SUPPRESSION_NOT_SERVER_REJECTION','no27_request_sent':True})
    try:
        result['qualified']=qualify();require(before_desktop['current'].startswith('God2Lab-') and before_desktop['current']!=before_desktop['input'],'HIDDEN_DESKTOP_REQUIRED')
        require(contract['startup_marker'] in log.read_text('utf-8',errors='replace'),'ACTUAL0071_STARTUP_REQUIRED')
        def launch(owner):
            image=Path(fixture['clients'][str(owner['page'])]['path']);require(base.sha(image)==fixture['clients'][str(owner['page'])]['sha256'],'PRIVATE_IMAGE_CHANGED')
            loader=subprocess.Popen([str(base.LE),'-run',str(image),'127.0.0.1','127.0.0.1','6001','1'],cwd=base.LIVE.parent,creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);loaders.append(loader)
            def found():
                rows=[p for p in psutil.process_iter(['exe']) if p.info['exe'] and Path(p.info['exe']).resolve()==image.resolve()];require(len(rows)<=1,'DUPLICATE_PRIVATE_CLIENT');return rows[0] if rows else None
            process=wait_until(found,35,'PRIVATE_CLIENT_MISSING');c={'process':process,'identity':owner['identity'],'account':owner['account'],'page':owner['page'],'fixture':owner};clients.append(c);result.setdefault('owned_client_pids',[]).append(process.pid);save(True)
            c['hwnd']=wait_until(lambda:base.peer.window_for(process.pid),35,'OWNED_WINDOW_MISSING');hwnd=c['hwnd'];time.sleep(12);click(hwnd,512,464);time.sleep(4)
            bound='RECOVERED_ACCOUNT_BOUND account_id='+str(c['account']);previous=log.read_text('utf-8',errors='replace').count(bound);click(hwnd,437,232);type_ascii(hwnd,owner['username']);click(hwnd,437,263);type_ascii(hwnd,'labtest2345');click(hwnd,452,304)
            wait_until(lambda:log.read_text('utf-8',errors='replace').count(bound)>previous,35,'PRIVATE_LOGIN_FAILED');time.sleep(4);click(hwnd,330,145);click(hwnd,452,413);time.sleep(4);click(hwnd,330,150);click(hwnd,452,376);time.sleep(4);click(hwnd,452,370);time.sleep(12)
            c['handle']=base.peer.kernel.OpenProcess(0x1010,False,process.pid);require(c['handle'],'READONLY_PROCESS_HANDLE_REQUIRED');c['ui']=base.peer.find_ui(c['handle'],c['identity'],(0,3,4));lang,sub=struct.unpack('<HH',exact(c,0x59dfd8,4));require(lang==4 and (sub==2)==(c['page']==936),'TW_CN_NATIVE_LANGUAGE_REQUIRED')
            lines=[line for line in log.read_text('utf-8',errors='replace').splitlines() if bound+';' in line];c['session']=int(re.search(r'session_id=(\d+)',lines[-1]).group(1));wait_until(lambda:consistent(c),10,'INITIAL_FULL50_FULL20_NOT_PROJECTED');return c
        for owner in fixture['owners']:launch(owner)
        result['initial']={'db':saved(database),'native':[snap(c) for c in clients]};save(True)
        for c in clients:
            set_confirmation(c,False)
            for definition in c['fixture']['phases'][0]:verify_discard(c,definition,False)
            set_confirmation(c,True)
            for definition in c['fixture']['phases'][1]:cancel_confirmation(c,definition);verify_discard(c,definition,True)
            set_confirmation(c,False)
            for quantity in(2,5):verify_discard(c,{'source':24,'representative':'MED'},False,quantity,False)
            refusal(c,c['fixture']['equipped_source'],'equipped_refusal')
        opened(clients[0],clients[1])
        for c in clients:refusal(c,27,'trade_refusal')
        control(clients[0],visible(clients[0],0x232dae,8,'TRADE_CANCEL_WINDOW_REQUIRED'),10)
        wait_until(lambda:all(widget(c,0x232dae) is None and snap(c)['trade_active']==0 for c in clients),8,'TRADE_CANCELLATION_NOT_CLOSED');require(saved(database)==result['trade_before'],'TRADE_REFUSAL_CANCEL_MUTATED_SAVES')
        durable=saved(database);old=list(clients);old_pids=[c['process'].pid for c in old]
        for c in old:close(c)
        require(all(not psutil.pid_exists(pid) for pid in old_pids),'OLD_CLIENTS_NOT_CLOSED');clients.clear()
        for owner in fixture['owners']:launch(owner)
        actual=saved(database);require(actual==durable,'RELOGIN_CHANGED_SAVED_STATE');native=[wait_until(lambda:consistent(c),10,'RELOGIN_FULL50_FULL20_FAILED') for c in clients];new_pids=[c['process'].pid for c in clients];require(len(set(old_pids+new_pids))==4,'RELOGIN_MUST_HAVE_NEW_CLIENT_PIDS')
        event({'operation':'relogin_full50','before':durable,'after':actual,'old_client_pids':old_pids,'new_client_pids':new_pids,'old_clients_closed':True,'native':native,'both_owner_saved_equal':True,'full50_verified':True,'full20_verified':True})
        result['final']={'db':actual,'native':native};result['scenario_counts']={kind:sum(e.get('operation')==kind for e in result['events']) for kind in fixture['expected_counts']};require(result['scenario_counts']==fixture['expected_counts'],'EXACT_TYPED48_CANCEL24_MED4_REFUSAL4_RELOGIN1_COUNTS');require(source_guards()==fixture['source_contract'],'FROZEN_RUNTIME_SOURCE_CHANGED');result['accepted']=True
    except BaseException as error:result.update(error=str(error),traceback=traceback.format_exc());save(True)
    finally:
        for c in clients:
            try:close(c)
            except BaseException as error:result.setdefault('cleanup_errors',[]).append(str(error))
        for loader in loaders:
            if loader.poll() is None:loader.terminate();loader.wait(timeout=5)
        result['all_clients_closed']=all(not psutil.pid_exists(pid) for pid in result.get('owned_client_pids',[]));result['desktop_unchanged']=before_desktop==desktop_names();result['accepted']=bool(result['accepted'] and result['all_clients_closed'] and result['desktop_unchanged'] and not result.get('cleanup_errors'));save(True)
    return 0 if result['accepted'] else 1

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);parser.add_argument('--server-candidate',type=Path);parser.add_argument('--source-page',type=int,choices=(950,936),default=950);parser.add_argument('--worker',action='store_true');parser.add_argument('--qualify-only',action='store_true');parser.add_argument('--prepare-only',action='store_true');args=parser.parse_args()
    if args.qualify_only:print(json.dumps(qualify()));return 0
    if args.output is None:parser.error('--output required')
    if args.worker:return worker(args)
    if args.server_candidate is None:parser.error('--server-candidate required')
    require(base.sha(args.server_candidate)==candidate_sha(),'NEW0071_IMMUTABLE_CANDIDATE');source_before=source_guards();desktop_before=desktop_names();script=Path(__file__).resolve();digest=base.sha(script)
    files=[script,CONTRACT,SOURCE,SOURCE_CONFIG,CREDENTIAL_FIXTURE,Path(armor_live.__file__).resolve(),Path(base.__spec__.origin),Path(pose.__file__).resolve(),ROOT/'tools/strike_lab/private_inventory_move_ui.py',ROOT/'tools/strike_lab/private_potion_ui.py',ROOT/'tools/strike_lab/private_owned_mixed_bank_v06_20261003.py',ROOT/'artifacts/playtests/private-native-blackbox-owned-mixed-bank-20261003-06/run-result.json',ROOT/'artifacts/playtests/private-native-blackbox-owned-mixed-bank-20261003-06/ui-result.json',ROOT/'tools/strike_lab/private_owned_instance_trade_20261003.py',ROOT/'tools/strike_lab/private_discard_27_20261002.py',ROOT/'tools/strike_lab/current_discard_instances_20261003.py',*sorted(PREDECESSOR.rglob('*'))]
    files=[p for p in files if p.is_file()];frozen={str(p):base.sha(p) for p in files}
    protected={str(p.pid):{'exe':p.info['exe'],'created':p.info['create_time']} for p in psutil.process_iter(['exe','create_time']) if p.info['exe'] and Path(p.info['exe']).name.lower() in ('god2.exe','god2-server.exe','leproc.exe','private_desktop_runner.exe')}
    qualify();os.environ['GOD2_NATIVE_WORLD_RECORDS_LAB']='1'
    if args.prepare_only:
        prepare(args);compact_dump(args.output/'preparation-result.json',{'accepted':True,'scope':'ISOLATED_FIXTURE_PREPARATION_ONLY_NOT_UI_RUN','harness_sha256':digest,'source_contract':source_before,'frozen_before':frozen,'frozen_after':{p:base.sha(Path(p)) for p in frozen},'fixture':json.loads((args.output/'fixture.json').read_text('utf-8'))});return 0
    code=bounded_owner(args);receipt=args.output/'run-result.json'
    if receipt.exists():
        result=json.loads(receipt.read_text('utf-8'));result['discard_harness_sha256']=digest;result['discard_harness_unchanged']=base.sha(script)==digest;result['runtime_sources_before']=source_before;result['runtime_sources_after']=source_guards();result['runtime_sources_unchanged']=result['runtime_sources_before']==result['runtime_sources_after']
        result['frozen_files_before']=frozen;result['frozen_files_after']={p:base.sha(Path(p)) for p in frozen};result['frozen_files_unchanged']=result['frozen_files_before']==result['frozen_files_after']
        after={str(p.pid):{'exe':p.info['exe'],'created':p.info['create_time']} for p in psutil.process_iter(['exe','create_time']) if str(p.pid) in protected};result['protected_processes_before']=protected;result['protected_processes_preserved']=after==protected
        result['desktop_owner_before']=desktop_before;result['desktop_owner_after']=desktop_names();result['desktop_owner_unchanged']=result['desktop_owner_before']==result['desktop_owner_after']
        with socket.socket() as probe:result['exclusive2598_released']=probe.connect_ex(('127.0.0.1',2598))!=0
        pids=[result.get('server_pid'),result.get('runner_pid')]+result.get('ui',{}).get('owned_client_pids',[]);result['owned_pid_terminal']={str(pid):{'pid_exists':psutil.pid_exists(pid)} for pid in pids if pid};result['scope']=SCOPE
        result['accepted']=bool(result['accepted'] and result['discard_harness_unchanged'] and result['runtime_sources_unchanged'] and result['frozen_files_unchanged'] and result['protected_processes_preserved'] and result['desktop_owner_unchanged'] and result['exclusive2598_released'] and len(result['owned_pid_terminal'])==6 and not any(row['pid_exists'] for row in result['owned_pid_terminal'].values()));compact_dump(receipt,result);return 0 if result['accepted'] else 1
    return code

def bounded_owner(args):
    args.output=args.output.resolve();args.server_candidate=args.server_candidate.resolve()
    sources={'live_client':base.LIVE,'live_locale_profile':Path(str(base.LIVE)+'.le.config'),'source_database':SOURCE,
        'source_config':SOURCE_CONFIG,'launcher_settings':base.LIVE.parent/'config/user.settings',
        'locale_global_config':base.LE.with_name('LEConfig.xml'),'locale_launcher':base.LE,'locale_loader':base.LE.with_name('LoaderDll.dll'),
        'locale_runtime':base.LE.with_name('LocaleEmulator.dll')}
    result={'accepted':False,'before':{k:base.sha(p) for k,p in sources.items()},'candidate_sha256':base.sha(args.server_candidate)};server=runner=None
    try:
        with socket.socket() as probe:require(probe.connect_ex(('127.0.0.1',base.PORT))!=0,'PRIVATE_PORT_ALREADY_USED')
        prepare(args);env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1';env.pop('GOD2_PRIVATE_SIDECAR_COMMAND',None)
        with (args.output/'stdout.log').open('wb') as log,(args.output/'runner.log').open('wb') as runnerlog:
            server=subprocess.Popen([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--run-for','1500'],cwd=ROOT,env=env,
                stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);result['server_pid']=server.pid
            def listening():
                require(server.poll() is None,'PRIVATE_SERVER_EXITED')
                with socket.socket() as probe:return probe.connect_ex(('127.0.0.1',base.PORT))==0
            wait_until(listening,12,'PRIVATE_SERVER_NOT_LISTENING')
            runner=subprocess.Popen([str(base.RUNNER),sys.executable,'-X','utf8','-B',str(Path(__file__).resolve()),'--worker','--output',str(args.output),'--source-page',str(args.source_page)],cwd=ROOT,env=env,
                stdout=runnerlog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);result['runner_pid']=runner.pid
            result['runner_exit']=runner.wait(timeout=1480);result['ui']=json.loads((args.output/'ui-result.json').read_text('utf-8'))
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
        if args.output.exists():compact_dump(args.output/'run-result.json',result)
    print(json.dumps({k:result.get(k) for k in ('accepted','error','candidate_sha256','source_files_unchanged','all_owned_processes_closed')}));return 0 if result['accepted'] else 1


if __name__=='__main__':raise SystemExit(main())
