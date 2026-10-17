"""Two original TW CP950/CP936 clients, native guild chat on disposable owned membership.

Port-only disposable client copies, read-only observation, window-local input.
No screenshots, memory writes, packet injection or input-desktop switching.
"""
import argparse,json,re,socket,sqlite3,struct,sys,time,traceback
from contextlib import closing
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]
import psutil,pefile,importlib.util
draw_spec=importlib.util.spec_from_file_location('guild_panel_draw',ROOT/'artifacts/research/native-guild-panel-0077/header-flow/draw-storage.py')
draw=importlib.util.module_from_spec(draw_spec);draw_spec.loader.exec_module(draw)
import private_peer_role_text_20260930 as base
import private_peer_pose_20261002 as pose
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,type_ascii
base.CLIENT_SHA=pose.CLIENT_SHA
from tools.strike_lab.current_private_chat_20261003 import REGIONS as QUERY_REGIONS
FROZEN_PARTY=ROOT/'tools/strike_lab/private_party_chat_20261003.py'
FROZEN_QUERY=ROOT/'tools/strike_lab/private_party_query_20261003.py'
CHAT_PROOF=ROOT/'artifacts/research/native-guild-chat-20261003/native.json'
from tools.strike_lab.current_party_chat_20261003 import REGIONS as CHAT_REGIONS
CONTRACT=ROOT/'artifacts/research/native-guild-panel-0077/live-contract-v02.json'

def source_guard():
    contract=json.loads(CONTRACT.read_text('utf-8'))
    require(contract['design']=='CUSTOM-0077','GUILD_PANEL_CONTRACT_REQUIRED')
    actual={name:base.sha(ROOT/name) for name in contract['source_sha256']}
    require(actual==contract['source_sha256'],'COMPILED_PARTY_CHAT_SOURCES_CHANGED')
    return actual

def qualify():
    mapped=pefile.PE(str(base.LIVE)).get_memory_mapped_image()
    for name in ('header-flow/native.json','header-flow/draw-storage.json'):
        proof=json.loads((ROOT/'artifacts/research/native-guild-panel-0077'/name).read_text('utf-8'))
        for pin in proof['pins']:
            a=int(pin['start'],16)-0x400000;b=int(pin.get('end',pin.get('end_exclusive')),16)-0x400000
            require(base.hashlib.sha256(mapped[a:b]).hexdigest()==pin.get('current_sha256',pin['sha256']),'NATIVE_PANEL_CODE_CHANGED')
    proof=json.loads((ROOT/'artifacts/research/native-guild-panel-0077/entry-trace/evidence.json').read_text('utf-8'))
    for pin in proof['code_intervals']:
        a=int(pin['start_va'],16)-0x400000;b=int(pin['end_va_exclusive'],16)-0x400000
        require(base.hashlib.sha256(mapped[a:b]).hexdigest()==pin['sha256'],'NATIVE_HELP_CODE_CHANGED')
    rosterproof=json.loads((ROOT/'artifacts/research/native-guild-roster-0076/native-runtime-v01.json').read_text('utf-8'))
    mapped=pefile.PE(str(base.LIVE)).get_memory_mapped_image()
    for pin in rosterproof['pins']:
        a=int(pin['start'],16)-0x400000;b=int(pin['end'],16)-0x400000
        require(base.hashlib.sha256(mapped[a:b]).hexdigest()==pin['sha256'],'NATIVE_ROSTER_CODE_CHANGED')
    raw=pose.qualify_source();current=pefile.PE(str(base.LIVE)).get_memory_mapped_image()
    guildproof=json.loads(CHAT_PROOF.read_text('utf-8'))
    for interval in guildproof['code_intervals']:
        a=int(interval['start_va'],16)-0x400000;b=int(interval['end_va_exclusive'],16)-0x400000
        require(base.hashlib.sha256(current[a:b]).hexdigest()==interval['sha256'],'GUILD_NATIVE_CODE_CHANGED')
    for start,end in CHAT_REGIONS+QUERY_REGIONS+((0x505680,0x505770),(0x505e90,0x505f70),(0x4c7460,0x4c7610)):
        require(current[start-0x400000:end-0x400000]==raw[start-0x400000:end-0x400000],'NATIVE_QUERY_CODE_CHANGED_'+hex(start))
    for va,size in ((0x497140,0x100),(0x497230,35),(0x4e9bc0,740),
                    (0x4e9ad0,150),(0x4ea140,180),(0x4ea8a0,580),(0x4ea770,230),
                    (0x4835a0,250),(0x481f70,160),(0x465fa0,420),(0x4a7300,35)):
        require(current[va-0x400000:va-0x400000+size]==raw[va-0x400000:va-0x400000+size],
                'NATIVE_PARTY_CODE_CHANGED_'+hex(va))


def seed_guild_fixture(db):
    def insert(table, values):
        columns=[row[1] for row in db.execute('pragma table_info("'+table+'")')]
        require(columns and all(c in values for c in columns),'GUILD_FIXTURE_SCHEMA_UNEXPECTED_'+table)
        sql='insert into "'+table+'"('+','.join('"'+c+'"' for c in columns)+') values('+','.join('?' for c in columns)+')'
        db.execute(sql,tuple(values[c] for c in columns))
    common={'revision':1,'origin':'CUSTOM_DESIGNED','source_sha256':base.MAPPED_SHA,'design_id':'CUSTOM-0075','custom_design_id':'CUSTOM-0075'}
    insert('owned_guilds',{**common,'id':1,'name_utf8':'labguild'})
    for identity in (4,5):insert('owned_guild_members',{**common,'character_id':identity,'guild_id':1})
    def cloned(table,key,identity):
        columns=[r[1] for r in db.execute('pragma table_info("'+table+'")')]
        row=db.execute('select * from "'+table+'" where "'+key+'"=?',(identity,)).fetchone()
        require(row is not None,'ROSTER_FIXTURE_TEMPLATE_REQUIRED_'+table)
        return dict(zip(columns,row))
    template=cloned('recovered_characters','id',4)
    owner=cloned('accounts','id',template['account_id'])
    role=cloned('character_role_snapshots','character_id',4)
    # Exclusive disposable CUSTOM_TEST_NOT_NATIVE fixtures, NEVER formal DB.
    for ordinal in range(48):
        identity=10000+ordinal;name=('offline076'+str(ordinal).zfill(2)).encode('ascii')
        account=dict(owner);account['id']=identity;account['username']='Roster076Offline'+str(ordinal)
        insert('accounts',account)
        character=dict(template);character.update(id=identity,account_id=identity,slot=0,name_bytes=name,name_codepage=950,streamer_privilege=0)
        profile=bytearray(character['profile']);profile[:16]=name+bytes(16-len(name));character['profile']=bytes(profile)
        insert('recovered_characters',character)
        snapshot=dict(role);snapshot['character_id']=identity;insert('character_role_snapshots',snapshot)
        insert('owned_guild_members',{**common,'character_id':identity,'guild_id':1})

original_prepare=base.prepare
def prepare(args):
    original_prepare(args)
    config=json.loads((args.output/'server-config.json').read_text('utf-8'))
    config['world']['clock']={'enabled':False}
    base.peer.dump(args.output/'server-config.json',config)
    with closing(sqlite3.connect(args.output/'town-diagnostic-accounts.db')) as db:
        db.execute('update recovered_positions set x=129,y=126 where character_id=5')
        seed_guild_fixture(db)
        text='guild4';name=text.encode('cp'+str(args.source_page))
        profile=bytearray(db.execute('select profile from recovered_characters where id=4').fetchone()[0])
        profile[:16]=name+bytes(16-len(name))
        db.execute('update recovered_characters set profile=?,name_bytes=?,name_codepage=? where id=4',
                   (profile,name,args.source_page))
        name5=b'guild5';profile5=bytearray(db.execute('select profile from recovered_characters where id=5').fetchone()[0]);profile5[:16]=name5+bytes(16-len(name5))
        db.execute('update recovered_characters set profile=?,name_bytes=?,name_codepage=? where id=5',(profile5,name5,936 if args.source_page==950 else 950));db.commit()
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'))
    fixture['party_names']={'4':{'raw':text,'950':text,'936':text},
                            '5':{'raw':'guild5','950':'guild5','936':'guild5'}}
    base.peer.dump(args.output/'fixture.json',fixture)
base.prepare=prepare

def worker(args):
    import subprocess
    before=desktop_names();clients=[];loaders=[]
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'))
    database=args.output/'town-diagnostic-accounts.db';log=args.output/'server.log'
    result={'accepted':False,'events':[],'party_chat_deliveries':[],'filter_events':[],'query_deliveries':[],'private_chat_deliveries':[],'guild_chat_deliveries':[],'guild_membership_events':[],'lifecycle_events':[],'automatic_reply_events':[],'rendered_pixels_tested':False,'source_page':args.source_page,'input_policy':'Window-local native WM events; normal Backspace clears observed shortcut residue; #prefix and Shift+native control12 selectedguildinput; read-only memory; no packet/code injection; no movements; adminfixture membership changes only in exclusive disposable database'}
    def save():base.peer.dump(args.output/'ui-result.json',result)
    def exact(client,address,size):return base.peer.exact(client['handle'],address,size)
    def word(client,address):return int.from_bytes(exact(client,address,2),'little',signed=True)
    def widget(client,offset):
        w=word(client,client['ui']+offset)
        return w if 0<=w<128 and exact(client,client['ui']+0xe2988+w*0x2a08,1)[0]&0x20 else None
    def control(client,w,index):
        entry=client['ui']+0xe2170+w*0x2a08+0x8b8+index*100
        hit=word(client,entry+8);manager=int.from_bytes(exact(client,client['ui']+0xe2174,4),'little')
        require(manager>0x10000 and 0<=hit<0xc00,'NATIVE_CONTROL_MISSING')
        active,left,top,right,bottom=struct.unpack('<5i',exact(client,manager+hit*24,20))
        require(active and 0<=left<right<=800 and 0<=top<bottom<=600,'NATIVE_CONTROL_RECT_INVALID')
        result['last_control']={'identity':client['identity'],'widget':w,'index':index,'rect':[left,top,right,bottom]};save()
        click(client['hwnd'],(left+right)//2,(top+bottom)//2);time.sleep(.25)
    def menu(client,index,mode=None,group=23):
        if mode is not None and word(client,client['ui']+0x232f36)==mode:return
        if widget(client,0x232e4e) is None:
            for message,vk,data in ((0x100,0x11,1),(0x100,0x48,1),(0x101,0x48,0xc0000001),(0x101,0x11,0xc0000001)):
                require(base.peer.user.PostMessageW(client['hwnd'],message,vk,data),'MENU_KEY_FAILED');time.sleep(.1)
        w=wait_until(lambda:widget(client,0x232e4e),8,'MAIN_MENU_NOT_OPEN')
        control(client,w,group);control(client,w,index)
        if mode is not None:wait_until(lambda:word(client,client['ui']+0x232f36)==mode,5,'PARTY_CURSOR_MODE_MISSING')
    def clear_input(client):
        click(client['hwnd'],400,584)
        def content():return exact(client,client['ui']+0x57bc4,256).split(b'\0',1)[0]
        before=content();previous=before
        for unused in range(256):
            if not previous:break
            for message,key,data in ((0x100,8,1),(0x102,8,1),(0x101,8,0xc0000001)):
                require(base.peer.user.PostMessageW(client['hwnd'],message,key,data),'CHAT_INPUT_BACKSPACE_FAILED');time.sleep(.06)
            current=content();require(len(current)<len(previous),'CHAT_INPUT_BACKSPACE_NOT_APPLIED');previous=current
        require(not content(),'CHAT_INPUT_NOT_EMPTY')
        result.setdefault('input_clears',[]).append({'identity':client['identity'],'before_hex':before.hex(),'after_hex':content().hex(),'action':'native Backspace WM'});save()
    def snapshot(client):
        actor=int.from_bytes(exact(client,client['ui']+0x86888,4),'little')
        count=int.from_bytes(exact(client,actor+0x3f98,4),'little')
        require(count<=4,'NATIVE_ROSTER_COUNT_INVALID');rows=[]
        for i in range(count):
            raw=exact(client,actor+0x3f9c+i*24,24)
            rows.append({'id':int.from_bytes(raw[:2],'little'),'leader':raw[3],
                'name':raw[8:24].split(b'\0',1)[0].decode('cp'+str(client['page'])),
                'hud':raw[4:8].hex(),'position':list(struct.unpack('<3H',exact(client,actor+0x3ffc+i*6,6))),
                'vitals':list(struct.unpack('<HHIIII',exact(client,actor+0x4014+i*20,20)))})
        return {'count':count,'rows':rows,'own_name':exact(client,actor+0x27,16).split(b'\0',1)[0].decode('cp'+str(client['page'])),
                'leader':int.from_bytes(exact(client,client['ui']+0xafed0,4),'little'),
                'self_leader':exact(client,client['ui']+0xafeea,1)[0]}
    def saved():
        # Query, chat, consenting party membership and departure are transient.
        with closing(base.peer.ro(database)) as db:
            return {name:{'sql':sql,'rows':sorted(repr(row) for row in db.execute('select * from "'+name.replace('"','""')+'"'))}
                    for name,sql in db.execute("select name,sql from sqlite_master where type='table' order by name").fetchall()
                    }
    def close(client):
        if client.get('handle'):base.peer.kernel.CloseHandle(client.pop('handle'))
        if client['process'].is_running():
            base.peer.user.PostMessageW(client['hwnd'],0x10,0,0)
            try:client['process'].wait(timeout=4)
            except psutil.TimeoutExpired:client['process'].terminate();client['process'].wait(timeout=5)
    try:
        qualify();require(before['current'].startswith('God2Lab-') and before['current']!=before['input'],'HIDDEN_DESKTOP_REQUIRED')
        def launch(identity,page):
            image=Path(fixture['clients'][str(page)]['path']);require(base.sha(image)==fixture['clients'][str(page)]['sha256'],'PRIVATE_IMAGE_CHANGED')
            loader=subprocess.Popen([str(base.LE),'-run',str(image),'127.0.0.1','127.0.0.1','6001','1'],cwd=base.LIVE.parent,
                creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);loaders.append(loader)
            def found():
                rows=[p for p in psutil.process_iter(['exe']) if p.info['exe'] and Path(p.info['exe']).resolve()==image.resolve()]
                require(len(rows)<=1,'DUPLICATE_PRIVATE_CLIENT');return rows[0] if rows else None
            process=wait_until(found,35,'CLIENT_MISSING');client={'process':process,'identity':identity,'page':page};clients.append(client)
            result.setdefault('owned_client_pids',[]).append(process.pid);save()
            hwnd=wait_until(lambda:base.peer.window_for(process.pid),35,'WINDOW_MISSING');client['hwnd']=hwnd
            time.sleep(12);click(hwnd,512,464);time.sleep(4)
            bound='RECOVERED_ACCOUNT_BOUND account_id='+str(identity);old=log.read_text('utf-8',errors='replace').count(bound)
            click(hwnd,437,232);type_ascii(hwnd,'codexslow' if identity==4 else 'codexfixed')
            click(hwnd,437,263);type_ascii(hwnd,'labtest2345');click(hwnd,452,304)
            wait_until(lambda:log.read_text('utf-8',errors='replace').count(bound)>old,35,'LOGIN_FAILED')
            time.sleep(4);click(hwnd,330,145);click(hwnd,452,413);time.sleep(4)
            click(hwnd,330,150);click(hwnd,452,376);time.sleep(4);click(hwnd,452,370);time.sleep(12)
            client['handle']=base.peer.kernel.OpenProcess(0x1010,False,process.pid);require(client['handle'],'READ_HANDLE_MISSING')
            client['ui']=base.peer.find_ui(client['handle'],identity,(0,3,4))
            language,sub=struct.unpack('<HH',exact(client,0x59dfd8,4))
            require(language==4 and (sub==2)==(page==936),'NATIVE_LANGUAGE_NOT_SELECTED')
            return client
        first=launch(4,args.source_page);other=launch(5,936 if args.source_page==950 else 950)
        wait_until(lambda:base.peer.remote(first['handle'],first['ui'],5),15,'PEER_NOT_VISIBLE')
        wait_until(lambda:base.peer.remote(other['handle'],other['ui'],4),15,'REVERSE_PEER_NOT_VISIBLE')
        invariant=saved();result['initial']=[snapshot(c) for c in clients]
        with closing(base.peer.ro(database)) as db:
            initial_positions=db.execute('select * from recovered_positions order by character_id').fetchall()
        result['positions_before']=[list(row) for row in initial_positions]
        require(all(r['own_name']==fixture['party_names'][str(c['identity'])]['raw'] for c,r in zip(clients,result['initial'])),
                'RAW_SELF_NAME_NOT_RETAINED');save()
        def target(source,target_client,index,mode):
            menu(source,index,mode)
            self_state=base.ground.world_state(source['handle'],source['ui'])
            other_state=base.ground.world_state(target_client['handle'],target_client['ui'])
            px,py=base.ground.ground_point(source['handle'],self_state,other_state['x'],other_state['y'])
            result['last_target']={'source':source['identity'],'target':target_client['identity'],'point':[px,py-26]};save()
            click(source['hwnd'],px,py-26)
        def invitation(requester,leader,accept):
            # 4A7300 sets mode6;4835A0 maps6->5;481F70 maps5->-11;
            # 465FA0(-11) queues6A. Menu27/mode5 instead queues57.
            target(requester,leader,31,6)
            w=wait_until(lambda:widget(leader,0x232df4),8,'PARTY_CONFIRM_NOT_OPEN')
            require(word(leader,leader['ui']+0xafecc)==requester['identity'] and exact(leader,leader['ui']+0xafece,1)[0]==0,'PARTY_CONFIRM_WRONG_OWNER')
            control(leader,w,4 if accept else 3)
            if accept:
                def agreed():
                    rows=[snapshot(c) for c in (requester,leader)]
                    if all(r['count']==1 for r in rows):return rows
                    return None
                rows=wait_until(agreed,8,'NATIVE_ROSTER_NOT_ACCEPTED')
                for c,peer_c,row in zip((requester,leader),(leader,requester),rows):
                    require(row['leader']==leader['identity'] and row['self_leader']==int(c is leader),'NATIVE_LEADER_WRONG')
                    peer_row=row['rows'][0];require(peer_row['id']==peer_c['identity'],'NATIVE_PEER_WRONG')
                    require(peer_row['name']==fixture['party_names'][str(peer_c['identity'])][str(c['page'])],'NATIVE_ROSTER_NAME_WRONG')
                    require(peer_row['vitals']==[peer_c['identity'],0,52,26,120,80],'NATIVE_PARTY_VITALS_WRONG')
            else:
                time.sleep(.5);rows=[snapshot(c) for c in (requester,leader)];require(all(r['count']==0 for r in rows),'DECLINE_CREATED_ROSTER')
            result['events'].append({'operation':'accept' if accept else 'decline','requester':requester['identity'],'leader':leader['identity'],'native':rows});save()
        def empty():return all(snapshot(c)['count']==0 for c in clients if c.get('handle'))
        def chat(client,ordinal):
            token='private74-common-'+str(client['identity'])+'-'+str(ordinal)
            old=len(log.read_text('utf-8',errors='replace'))
            clear_input(client);type_ascii(client['hwnd'],token)
            for message in (0x100,0x101):
                require(base.peer.user.PostMessageW(client['hwnd'],message,13,0),'QUERY_CHAT_ENTER_FAILED')
                time.sleep(.15)
            def rings(peer_client):
                visible=int.from_bytes(exact(peer_client,peer_client['ui']+0x39de8,4),'little')
                require(visible>0x10000,'QUERY_VISIBLE_CHAT_RING_MISSING')
                evidence=[]
                for name,address in (('visible',visible),('archive',peer_client['ui']+0x39e20)):
                    raw=exact(peer_client,address,0x67f4)
                    count,oldest,nxt=struct.unpack_from('<3I',raw,0x67e8)
                    require(count<=200 and oldest<200 and nxt<200,'QUERY_CHAT_RING_BOUNDS')
                    lines=[raw[i*128:(i+1)*128].split(b'\0',1)[0] for i in ((oldest+n)%200 for n in range(count)) if raw[0x6400+i]==0]
                    text=re.sub(rb'/c[0-9a-fA-F]',b'',b''.join(lines))
                    if token.encode('ascii') not in text:return None
                    evidence.append({'ring':name,'count':count,'common_text_hex':text.hex()})
                return evidence
            observations={str(c['identity']):wait_until(lambda c=c:rings(c),8,'QUERY_CHAT_REGRESSION_MISSING') for c in clients}
            marker=wait_until(lambda:next((line for line in log.read_text('utf-8',errors='replace')[old:].splitlines() if 'NATIVE_CHAT_ACCEPTED' in line),None),4,'QUERY_CHAT_SERVER_MARKER_MISSING')
            require(saved()==invariant,'QUERY_CHAT_CHANGED_SQL_STATE')
            result['events'].append({'operation':'chat','source':client['identity'],'token':token,'native_rings':observations,'marker':marker});save()
        def channel_ring(client,channel,token=None):
            visible=int.from_bytes(exact(client,client['ui']+0x39de8,4),'little')
            require(visible>0x10000,'PARTY_CHAT_VISIBLE_RING_MISSING')
            rings=[]
            for name,address in (('visible',visible),('archive',client['ui']+0x39e20)):
                raw=exact(client,address,0x67f4)
                count,oldest,nxt=struct.unpack_from('<3I',raw,0x67e8)
                require(count<=200 and oldest<200 and nxt<200,'PARTY_CHAT_RING_BOUNDS')
                rows=[]
                for index in ((oldest+n)%200 for n in range(count)):
                    if raw[0x6400+index]!=channel:continue
                    text=raw[index*128:(index+1)*128].split(b'\0',1)[0]
                    plain=re.sub(rb'/c[0-9a-fA-F]',b'',text)
                    decoded=plain.decode('cp'+str(client['page']))
                    if token is None or token in decoded:
                        rows.append({'index':index,'channel':channel,'color':struct.unpack_from('<I',raw,0x64c8+index*4)[0],
                            'text_hex':text.hex(),'plain':decoded})
                rings.append({'ring':name,'total_count':count,'matched_rows':rows})
            return rings
        def bubble_fields(client,sender):
            if sender==client['identity']:
                actor=int.from_bytes(exact(client,client['ui']+0x86888,4),'little')
                localroot=actor-0x90;world=localroot-0x1539683c
                renderer=int.from_bytes(exact(client,localroot+0x4544,2),'little')
            else:
                remote=base.peer.remote(client['handle'],client['ui'],sender)
                require(remote is not None,'PARTY_CHAT_REMOTE_ACTOR_MISSING')
                world=int(remote['world'],16);renderer=remote['renderer']
            require(0<=renderer<4096,'PARTY_CHAT_BUBBLE_RENDERER_INVALID')
            node=world+0xaba32e0+renderer*0xa7e0
            return {'renderer':renderer,'node':hex(node),'line_count':int.from_bytes(exact(client,node+0x56,2),'little'),
                'graphic':int.from_bytes(exact(client,node+0xa4,4),'little',signed=True)}
        def all_bubbles():
            return {str(client['identity']):{str(sender):bubble_fields(client,sender) for sender in (4,5)} for client in clients}
        def input_options(client):
            actor=int.from_bytes(exact(client,client['ui']+0x86888,4),'little')
            return {'options':int.from_bytes(exact(client,actor+0x449c,2),'little'),
                'visible_mask':int.from_bytes(exact(client,client['ui']+0x39e04,4),'little'),
                'selected_channel':int.from_bytes(exact(client,client['ui']+0x39e00,4),'little'),
                'private_view':exact(client,client['ui']+0x39e18,1)[0]}
        def party_chat(sender,direction,ordinal,hidden=None):
            token='pc73-'+str(sender['identity'])+'-'+str(direction)+'-'+str(ordinal)
            prefix=ordinal==1
            select_channel(sender,0 if prefix else 1)
            options={str(c['identity']):input_options(c) for c in clients}
            require(all(value['options']&0x20 and value['private_view']==0 for value in options.values()),'PARTY_CHAT_NATIVE_RECEPTION_FILTER_DISABLED')
            require(options[str(sender['identity'])]['selected_channel']==(0 if prefix else 1),'PARTY_CHAT_NATIVE_INPUT_CHANNEL_WRONG')
            require(all(value['visible_mask']&2 or c['identity']==hidden for c,value in zip(clients,options.values())),'PARTY_CHAT_VISIBLE_MASK_DISABLED')
            before=all_bubbles();old=len(log.read_text('utf-8',errors='replace'))
            clear_input(sender);typed=('!' if prefix else '')+token;type_ascii(sender['hwnd'],typed);time.sleep(.2)
            result['pending_party_chat']={'source':sender['identity'],'token':token,'typed_input':typed,
                'options':options,'native_edit_hex':exact(sender,sender['ui']+0x57bc4,256).split(b'\0',1)[0].hex()};save()
            require(result['pending_party_chat']['native_edit_hex']==typed.encode('ascii').hex(),'PARTY_CHAT_NATIVE_EDIT_TEXT_DIFFERENT')
            for message in (0x100,0x101):
                require(base.peer.user.PostMessageW(sender['hwnd'],message,13,0),'PARTY_CHAT_ENTER_FAILED');time.sleep(.15)
            expected_name=fixture['party_names'][str(sender['identity'])]['raw']
            expected=expected_name+': '+token
            observations={}
            for client in clients:
                def consumed(client=client):
                    rows=channel_ring(client,1,token)
                    archive=rows[1]['matched_rows'];visible=rows[0]['matched_rows']
                    if not archive:return None
                    if client['identity']!=hidden and not visible:return None
                    if client['identity']==hidden and visible:return None
                    for row in archive+visible:
                        require(expected in row['plain'],'PARTY_CHAT_NAME_PREFIX_WRONG')
                        require(row['color']==0xff00,'PARTY_CHAT_NATIVE_COLOR_WRONG')
                        require('!'+token not in row['plain'],'PARTY_CHAT_PREFIX_NOT_STRIPPED')
                    return rows
                observations[str(client['identity'])]=wait_until(consumed,8,'NATIVE_PARTY_CHAT_RINGS_MISSING_'+str(client['identity']))
            marker=wait_until(lambda:next((line for line in log.read_text('utf-8',errors='replace')[old:].splitlines()
                if 'NATIVE_PARTY_CHAT_REQUEST ' in line and 'character_id='+str(sender['identity'])+' ' in line
                and 'delivered=2' in line and 'accepted=true' in line),None),4,'PARTY_CHAT_SERVER_ACCEPTANCE_MISSING')
            after=all_bubbles();require(before==after,'PARTY_CHAT_CHANGED_NATIVE_BUBBLE_FIELDS')
            require(saved()==invariant,'PARTY_CHAT_CHANGED_ANY_SQL_ROW')
            receipt={'source':sender['identity'],'source_page':sender['page'],'role_direction':direction,'ordinal':ordinal,
                'token':token,'typed_input':typed,'producer_route':'native !prefix' if prefix else 'native selected UI39E00=1','expected_name_prefix':expected_name+': ',
                'native_edit_hex_before_submit':result['pending_party_chat']['native_edit_hex'],
                'native_channel':1,'native_color':0xff00,'recipient_rings':observations,'options_before':options,
                'bubbles_before':before,'bubbles_after':after,'bubble_fields_unchanged':True,
                'hidden_recipient':hidden,'server_line':marker,'rendered_pixels_tested':False}
            result['party_chat_deliveries'].append(receipt);result.pop('pending_party_chat',None);save();return receipt
        def select_channel(client,channel):
            panel=wait_until(lambda:widget(client,0x232e10),4,'NATIVE_CHAT_CHANNEL_PANEL_MISSING')
            before=input_options(client)
            # Native47F270 calls418300(0x10): Shift selects input channel.
            require(base.peer.user.PostMessageW(client['hwnd'],0x100,0x10,1),'CHAT_CHANNEL_SHIFT_DOWN_FAILED')
            time.sleep(.15);control(client,panel,10+channel)
            require(base.peer.user.PostMessageW(client['hwnd'],0x101,0x10,0xc0000001),'CHAT_CHANNEL_SHIFT_UP_FAILED')
            state=wait_until(lambda:input_options(client) if input_options(client)['selected_channel']==channel else None,4,'NATIVE_CHAT_CHANNEL_SELECTION_MISSING')
            require(state['visible_mask']==before['visible_mask'] and state['options']==before['options'],'CHAT_CHANNEL_SELECTION_CHANGED_FILTER')
            require(saved()==invariant,'CHAT_CHANNEL_SELECTION_CHANGED_SQL')
            result.setdefault('channel_selection',[]).append({'identity':client['identity'],'channel':channel,'control':10+channel,'before':before,'after':state});save()
        def filter_toggle(client):
            panel=widget(client,0x232e10)
            if panel is None:return None
            before=input_options(client)
            # Release Shift before the native filter release-event branch.
            require(base.peer.user.PostMessageW(client['hwnd'],0x101,0x10,0xc0000001),'PARTY_FILTER_SHIFT_RELEASE_FAILED')
            time.sleep(.15);control(client,panel,11)
            state=wait_until(lambda:input_options(client) if input_options(client)['visible_mask']==before['visible_mask']^2 else None,3,'PARTY_FILTER11_DID_NOT_TOGGLE_MASK')
            require(state['selected_channel']==before['selected_channel'] and state['options']==before['options'],'PARTY_FILTER_CHANGED_INPUT_OR_OPTIONS')
            return {'identity':client['identity'],'control':11,'panel':panel,'before':before,'after':state}
        def reception_toggle(client,index=6):
            # Main menu group22/control36 ->4C7460 opens chat settings232DC6.
            # Native4C7520 controls5/6 toggle common10/party20 and emit1D.
            bit={5:0x10,6:0x20,7:0x40}[index]
            before=input_options(client);menu(client,36,group=22)
            panel=wait_until(lambda:widget(client,0x232dc6),5,'PARTY_RECEPTION_SETTINGS_NOT_OPEN')
            control(client,panel,index)
            state=wait_until(lambda:input_options(client) if input_options(client)['options']==before['options']^bit else None,4,'PARTY_RECEPTION_SETTINGS_DID_NOT_TOGGLE')
            control(client,panel,4)
            require(saved()==invariant,'PARTY_RECEPTION_SETTINGS_CHANGED_SQL')
            return {'identity':client['identity'],'menu_group':22,'menu_control':36,'settings_control':index,'toggle_bit':bit,'panel':panel,'before':before,'after':state}
        def submit(client):
            for message in (0x100,0x101):
                require(base.peer.user.PostMessageW(client['hwnd'],message,13,0),'PRIVATE_CHAT_ENTER_FAILED');time.sleep(.15)
        def recipient_edit(client,recipient):
            hud=word(client,client['ui']+0x232db6);control(client,hud,13)
            wait_until(lambda:word(client,client['ui']+0x5bfa4)==1,3,'PRIVATE_RECIPIENT_EDIT_NOT_FOCUSED')
            address=client['ui']+0x58718
            for unused in range(16):
                if not exact(client,address,16).split(b'\0',1)[0]:break
                for message,key,data in ((0x100,8,1),(0x102,8,1),(0x101,8,0xc0000001)):
                    require(base.peer.user.PostMessageW(client['hwnd'],message,key,data),'RECIPIENT_BACKSPACE_FAILED');time.sleep(.07)
            require(not exact(client,address,16).split(b'\0',1)[0],'RECIPIENT_EDIT_NOT_EMPTY')
            type_ascii(client['hwnd'],recipient);time.sleep(.25)
            observed=exact(client,address,16).split(b'\0',1)[0]
            require(observed==recipient.encode('ascii'),'RECIPIENT_EDIT_TEXT_WRONG')
            result.setdefault('recipient_edits',[]).append({'identity':client['identity'],'expected':recipient,'observed_hex':observed.hex(),'native_edit_state':word(client,client['ui']+0x5bfa4)});save()
        def private_chat(sender,recipient,ordinal,route='prefix',hidden=None):
            token='pv74-'+str(sender['identity'])+'-'+str(ordinal)
            select_channel(sender,0 if route=='prefix' else 3)
            target_name=fixture['party_names'][str(recipient['identity'])]['raw']
            source_name=fixture['party_names'][str(sender['identity'])]['raw']
            expected=source_name+': ['+target_name+'] '+token
            options={str(c['identity']):input_options(c) for c in clients if c.get('handle')}
            before=all_bubbles();old=len(log.read_text('utf-8',errors='replace'))
            clear_input(sender);typed=('$'+target_name+' ' if route=='prefix' else '')+token
            type_ascii(sender['hwnd'],typed);time.sleep(.2)
            observed=exact(sender,sender['ui']+0x57bc4,256).split(b'\0',1)[0]
            result['pending_private_chat']={'source':sender['identity'],'target':recipient['identity'],'token':token,'typed_input':typed,'native_edit_hex':observed.hex(),'options':options};save()
            require(observed==typed.encode('ascii'),'PRIVATE_NATIVE_EDIT_TEXT_DIFFERENT')
            if route=='selected':recipient_edit(sender,target_name)
            submit(sender)
            observations={}
            for client in (sender,recipient):
                def consumed(client=client):
                    rings=channel_ring(client,2,token);visible,archive=(rings[0]['matched_rows'],rings[1]['matched_rows'])
                    if not archive:return None
                    if client['identity']==hidden:
                        if visible:return None
                    elif not visible:return None
                    for row in visible+archive:
                        require(expected in row['plain'],'PRIVATE_CHAT_NAME_TARGET_PREFIX_WRONG')
                        require(row['color']==0xffff,'PRIVATE_CHAT_NATIVE_COLOR_WRONG')
                    return rings
                observations[str(client['identity'])]=wait_until(consumed,8,'PRIVATE_NATIVE_RING_MISSING_'+str(client['identity']))
            marker=wait_until(lambda:next((line for line in log.read_text('utf-8',errors='replace')[old:].splitlines() if 'NATIVE_PRIVATE_CHAT_REQUEST ' in line and 'character_id='+str(sender['identity'])+' ' in line and 'delivered=2' in line and 'accepted=true' in line),None),4,'PRIVATE_SERVER_ACCEPTANCE_MISSING')
            after=all_bubbles();require(before==after,'PRIVATE_CHAT_CHANGED_BUBBLE_FIELDS');require(saved()==invariant,'PRIVATE_CHAT_CHANGED_SQL')
            receipt={'source':sender['identity'],'source_page':sender['page'],'target':recipient['identity'],'token':token,'typed_input':typed,'route':route,'expected':expected,'native_edit_hex_before_submit':observed.hex(),'native_channel':2,'native_color':0xffff,'recipient_rings':observations,'bubbles_before':before,'bubbles_after':after,'bubble_fields_unchanged':True,'hidden_recipient':hidden,'server_line':marker,'rendered_pixels_tested':False}
            result['private_chat_deliveries'].append(receipt);result.pop('pending_private_chat',None);save();return receipt
        def private_filter(client):
            before=input_options(client);panel=widget(client,0x232e10);require(panel is not None,'PRIVATE_FILTER_PANEL_MISSING')
            require(base.peer.user.PostMessageW(client['hwnd'],0x101,0x10,0xc0000001),'PRIVATE_FILTER_SHIFT_UP_FAILED');time.sleep(.15)
            control(client,panel,13)
            state=wait_until(lambda:input_options(client) if input_options(client)['visible_mask']==before['visible_mask']^8 else None,4,'PRIVATE_FILTER_NOT_TOGGLED')
            require(state['selected_channel']==before['selected_channel'] and state['options']==before['options'],'PRIVATE_FILTER_CHANGED_INPUT_OPTIONS')
            return {'identity':client['identity'],'before':before,'after':state,'control':13}
        def away(client,enabled):
            current=exact(client,client['ui']+0x23d89c,1)[0]
            require(current in (0,1),'NATIVE_AWAY_STATE_INVALID')
            menu(client,32,group=22)
            panel=wait_until(lambda:widget(client,0x232dbe),5,'NATIVE_AWAY_PANEL_NOT_OPEN')
            before=exact(client,0x5b7698,0x33).split(b'\0',1)[0]
            if current!=int(enabled):control(client,panel,11)
            wait_until(lambda:exact(client,client['ui']+0x23d89c,1)[0]==int(enabled),4,'NATIVE_AWAY_NOT_TOGGLED')
            control(client,panel,10)
            require(exact(client,0x5b7698,0x33).split(b'\0',1)[0]==before,'NATIVE_AWAY_TEMPLATE_CHANGED')
            require(saved()==invariant,'AWAY_CHANGED_SQL')
            result.setdefault('away_toggles',[]).append({'identity':client['identity'],'enabled':enabled,'menu_group':22,'menu_control':32,'toggle_control':11,'template0_hex':before.hex(),'template0_text':before.decode('cp'+str(client['page']))});save()
            return before
        original_invariant=invariant
        result['all_tables_before']=original_invariant
        def guild_name(client):
            actor=int.from_bytes(exact(client,client['ui']+0x86888,4),'little')
            return exact(client,actor+6,16).split(b'\0',1)[0].decode('cp'+str(client['page']))
        def initial_guild_projection(client,stage):
            started=time.monotonic();first_observed=guild_name(client)
            wait_until(lambda:guild_name(client)=='labguild',5,'NATIVE_2D_'+stage.upper()+'_GUILD_NAME_MISSING')
            lines=log.read_text('utf-8',errors='replace').splitlines()
            matches=[(i,line) for i,line in enumerate(lines) if 'OWNED_GUILD_NAME_PROJECTED ' in line and 'character_id='+str(client['identity'])+' ' in line]
            require(matches,'GUILD_FIRST_INITIALIZER_PROJECTION_LOG_MISSING')
            projection_index,projection_line=matches[-1]
            session=re.search(r'session_id=(\d+)',projection_line)
            require(session,'GUILD_PROJECTION_SESSION_MARKER_MISSING');session_marker='session_id='+session.group(1)+' '
            require('initial=true ' in projection_line and 'membership=true ' in projection_line,'GUILD_INITIAL_OWNED_PROJECTION_FLAG_MISSING')
            tails=[(i,line) for i,line in enumerate(lines) if session_marker in line and 'WORLD_INITIALIZER_TAIL_ACCEPTED ' in line]
            require(tails,'GUILD_INITIALIZER_TAIL_LOG_MISSING')
            tail_index,tail_line=tails[0]
            snapshots=[(i,line) for i,line in enumerate(lines) if session_marker in line and 'OWNED_WORLD_SNAPSHOT_RESTORED ' in line]
            require(snapshots,'GUILD_FIRST_INITIALIZER_SNAPSHOT_LOG_MISSING')
            snapshot_index,snapshot_line=snapshots[0]
            handled=[(i,line) for i,line in enumerate(lines) if i>tail_index and session_marker in line and 'RECOVERED_WORLD_BATCH_HANDLED ' in line]
            require(handled and tail_index<projection_index<handled[0][0] and tail_index<snapshot_index<handled[0][0],'GUILD_NAME_DEFERRED_AFTER_FIRST_OWNED_INITIALIZER_BATCH')
            event={'identity':client['identity'],'stage':stage,'first_name':first_observed,'final_name':guild_name(client),
                'elapsed_seconds':time.monotonic()-started,'bounded_seconds':5,'additional_input_or_packets':False,
                'next_normal_tick_projection_allowed':False,'initializer_tail_line':tail_line,'snapshot_line':snapshot_line,'projection_line':projection_line,
                'line_indexes':{'tail':tail_index,'projection':projection_index,'snapshot':snapshot_index,'first_handled':handled[0][0]},
                'projection_precedes_snapshot_success_log':projection_index<snapshot_index,
                'first_owned_batch_handled_line':handled[0][1],'first_owned_initializer_batch_projection_verified':True}
            result.setdefault('first_initializer_guild_name_proofs',[]).append(event);save();return event
        def roster_cache(client,stage,expected=50):
            def capture():
                count=int.from_bytes(exact(client,client['ui']+0xb690,4),'little')
                require(count<=50,'NATIVE_GUILD_ROSTER_OVERFLOW')
                if count!=expected:return None
                rows=[exact(client,client['ui']+0xaf50+21*i,21) for i in range(count)]
                require(len({r[0] for r in rows})==count,'NATIVE_GUILD_ROSTER_SLOT_COLLISION')
                names=[r[5:21].split(b'\0',1)[0].decode('cp'+str(client['page'])) for r in rows]
                wanted=({'guild4','guild5'}|{'offline076'+str(i).zfill(2) for i in range(48)}) if expected else set()
                if set(names)!=wanted:return None
                with closing(base.peer.ro(database)) as db:
                    members=db.execute('select c.id,c.profile,c.name_bytes,c.name_codepage,r.logical from owned_guild_members m join recovered_characters c on c.id=m.character_id join character_role_snapshots r on r.character_id=c.id order by c.id').fetchall()
                byname={bytes(n).decode('cp'+str(cp)):(identity,bytes(profile)[29],bytes(role)[1]) for identity,profile,n,cp,role in members}
                for row,name in zip(rows,names):
                    identity,profession,level=byname[name]
                    require(row[1]==1 and row[2]==level and row[3]==profession,'NATIVE_GUILD_ROSTER_ROLE_LEVEL_CLASS_WRONG')
                    require((row[0]==0)==(identity==client['identity']),'NATIVE_GUILD_ROSTER_SELF_SLOT_WRONG')
                return {'count':count,'pages':int.from_bytes(exact(client,client['ui']+0xb6a0,4),'little'),'rows_hex':[r.hex() for r in rows],'names':names}
            observed=wait_until(capture,8,'NATIVE_GUILD_ROSTER_'+stage.upper()+'_MISSING')
            result.setdefault('native_roster_cache_events',[]).append({'identity':client['identity'],'page':client['page'],'stage':stage,**observed,'readonly_memory':True,'panel_open_or_rendered_pixels_claimed':False});save()
            return observed
        for client in clients:
            initial_guild_projection(client,'initial');roster_cache(client,'initial')
        def panel_exercise(client,stage):
            reader=draw.DrawReader(lambda address,count:exact(client,address,count),client['ui'],client['page'])
            def opened_count():
                return len([line for line in log.read_text('utf-8',errors='replace').splitlines()
                    if 'OWNED_GUILD_READONLY_PANEL_OPEN ' in line and 'character_id='+str(client['identity'])+' ' in line])
            def help_open():
                before_open=opened_count()
                toolbar=wait_until(lambda:widget(client,0x232db6),5,'WORLD_TOOLBAR_NOT_VISIBLE')
                control(client,toolbar,4) # original tooltip637 new player help
                wait_until(lambda:opened_count()==before_open+1,8,'CUSTOM_HELP_PANEL_ROUTE_MISSING')
                panel_widget=wait_until(lambda:widget(client,0x232e16),8,'NATIVE_8E_PANEL_NOT_VISIBLE')
                wait_until(lambda:widget(client,0x232e18),8,'NATIVE_8E_ROSTER_NOT_VISIBLE')
                return panel_widget
            initial_seen=int.from_bytes(exact(client,client['ui']+0x234c4,4),'little')
            main=help_open()
            require(initial_seen==0 and int.from_bytes(exact(client,client['ui']+0x234c4,4),'little')==1,'NATIVE_FIRST_PANEL_SEEN_WRONG')
            header=exact(client,client['ui']+0xae6c,52)
            expected=bytearray(52);expected[13]=6;expected[19]=50;expected[23]=50
            require(header==bytes(expected),'CUSTOM_READONLY_NATIVE_HEADER_DIFFERS')
            labels={str(i):reader.main_text(i) for i in (4,5,8)}
            require(labels['4']['text'].endswith('labguild'),'GUILD_DRAW_NAME_MISSING')
            require('50/50' in labels['8']['text'],'GUILD_DRAW_COUNT_MISSING')
            # Use ordinary widget click, not a disabled callback invocation.
            control(client,main,9)
            child=wait_until(lambda:widget(client,0x232e18),5,'ROSTER_TAB_NOT_VISIBLE')
            with closing(base.peer.ro(database)) as db:
                members=db.execute('select c.profile,c.name_bytes,c.name_codepage,r.logical from owned_guild_members m join recovered_characters c on c.id=m.character_id join character_role_snapshots r on r.character_id=c.id').fetchall()
            classes=['','男劍','女劍','男仙','女仙','男謀','女謀','男藥','女藥'] if client['page']==950 else ['','男剑','女剑','男仙','女仙','男谋','女谋','男药','女药']
            wanted={bytes(n).decode('cp'+str(cp)):('Lv'+str(bytes(level)[1]),classes[bytes(profile)[29]]) for profile,n,cp,level in members}
            pages=[];names=[]
            def observe(index):
                require(int.from_bytes(exact(client,client['ui']+0xb69c,4),'little')==index,'NATIVE_PAGE_INDEX_WRONG')
                rows=[]
                for row in range(20):
                    active=int.from_bytes(exact(client,client['ui']+0xbbe4+0x148+row*4,4),'little')
                    require(active in (0,1),'NATIVE_ROW_ENABLED_INVALID')
                    if not active:continue
                    value=reader.table_row(row);name=value['name']['text']
                    result['panel_last_row']={'actual':value,'wanted':wanted.get(name)};save()
                    require(name in wanted and (value['level']['text'],value['class']['text'])==wanted[name],'NATIVE_DRAW_MEMBER_DATA_WRONG')
                    require(all(image['sprite_handle']!=0xffff for image in value['image_frames']),'NATIVE_ROSTER_ICON_UNBOUND')
                    rows.append(value)
                require(len(rows)==(20 if index<2 else 10),'NATIVE_DRAW_PAGE_ROW_COUNT_WRONG')
                page=reader.roster_page();require(page['text']==str(index+1)+'/3','NATIVE_DRAW_PAGE_LABEL_WRONG')
                entry={'page_index':index,'page_text':page,'rows':rows};pages.append(entry)
                return [r['name']['text'] for r in rows]
            for index in range(3):
                names.extend(observe(index));control(client,child,5)
            require(len(names)==len(set(names))==50 and set(names)==set(wanted),'NATIVE_VISIBLE_THREE_PAGES_NOT_COMPLETE')
            require(int.from_bytes(exact(client,client['ui']+0xb69c,4),'little')==0,'NATIVE_NEXT_PAGE_WRAP_FAILED')
            control(client,child,4);observe(2);control(client,child,5)
            control(client,child,9) # native sort selector2 name
            require(int.from_bytes(exact(client,client['ui']+0xb698,4),'little')==2,'NATIVE_NAME_SORT_NOT_APPLIED')
            sorted_names=[]
            for index in range(3):
                sorted_names.extend(observe(index));control(client,child,5)
            require(set(sorted_names)==set(wanted),'NATIVE_SORT_LOST_MEMBERS')
            permission=[]
            for index in (11,23):
                entry=client['ui']+0xe2170+main*0x2a08+0x8b8+index*100
                disabled=int.from_bytes(exact(client,entry+4,4),'little')
                require(disabled==1,'NATIVE_READONLY_MANAGEMENT_CONTROL_ENABLED')
                permission.append({'control':index,'native_disabled_value':disabled})
                old=opened_count();control(client,main,index)
                require(opened_count()==old and widget(client,0x232e16)==main,'DISABLED_CONTROL_CHANGED_PANEL')
            require(saved()==invariant,'PANEL_OR_PAGING_CHANGED_SAVED_ROWS')
            control(client,main,26)
            wait_until(lambda:widget(client,0x232e16) is None and widget(client,0x232e18) is None,5,'NATIVE_PANEL_CLOSE_FAILED')
            # Wait for native ready10 after its actual close animation.
            wait_until(lambda:exact(client,client['ui']+0xe2988+main*0x2a08,1)[0]&0x10,5,'NATIVE_PANEL_CLOSE_NOT_SETTLED')
            before_b8=log.read_text('utf-8',errors='replace').count('OWNED_GUILD_PANEL_NOTIFICATION ')
            main=help_open()
            time.sleep(.6)
            require(log.read_text('utf-8',errors='replace').count('OWNED_GUILD_PANEL_NOTIFICATION ')==before_b8,'REOPEN_WRONGLY_REQUIRES_SECOND_B8')
            require(reader.main_text(4)['text'].endswith('labguild') and int.from_bytes(exact(client,client['ui']+0xb690,4),'little')==50,'REOPEN_LOST_GUILD_IDENTITY_OR_MEMBERS')
            control(client,main,26)
            wait_until(lambda:widget(client,0x232e16) is None and widget(client,0x232e18) is None,5,'REOPENED_PANEL_CLOSE_FAILED')
            require(saved()==invariant,'REOPEN_CHANGED_SQL')
            result.setdefault('native_panel_events',[]).append({'identity':client['identity'],'locale':client['page'],'stage':stage,'header_hex':header.hex(),'main_labels':labels,'pages':pages,'drawn_names_complete':names,'sorted_names':sorted_names,'management_controls':permission,'first_seen_before':initial_seen,'first_seen_after':1,'reopen_second_B8':False,'entry':'CUSTOM0077 native new player help toolbar control4','pixels_certified':False,'saved_rows_unchanged':True});save()
        for client in clients:panel_exercise(client,'initial')

        result['native_guild_names_initial']={str(c['identity']):guild_name(c) for c in clients}
        def guild_filter(client):
            before=input_options(client);panel=widget(client,0x232e10)
            require(panel is not None,'GUILD_FILTER_PANEL_MISSING')
            require(base.peer.user.PostMessageW(client['hwnd'],0x101,0x10,0xc0000001),'GUILD_FILTER_SHIFT_UP_FAILED')
            time.sleep(.15);control(client,panel,12)
            after=wait_until(lambda:input_options(client) if input_options(client)['visible_mask']==before['visible_mask']^4 else None,4,'GUILD_FILTER_NOT_TOGGLED')
            require(after['selected_channel']==before['selected_channel'] and after['options']==before['options'],'GUILD_FILTER_CHANGED_INPUT_OPTIONS')
            require(saved()==invariant,'GUILD_FILTER_CHANGED_SQL')
            return {'identity':client['identity'],'control':12,'before':before,'after':after}
        def guild_chat(sender,ordinal,route='prefix',hidden=None,select=True):
            token='gc75-'+str(sender['identity'])+'-'+str(ordinal)
            if select:select_channel(sender,0 if route=='prefix' else 2)
            before=all_bubbles();old=len(log.read_text('utf-8',errors='replace'))
            expected=fixture['party_names'][str(sender['identity'])]['raw']+': '+token
            clear_input(sender);typed=('#' if route=='prefix' else '')+token
            type_ascii(sender['hwnd'],typed);time.sleep(.2)
            observed=exact(sender,sender['ui']+0x57bc4,256).split(b'\0',1)[0]
            result['pending_guild_chat']={'source':sender['identity'],'token':token,'typed_input':typed,'native_edit_hex':observed.hex(),'options':input_options(sender)};save()
            require(observed==typed.encode('ascii'),'GUILD_NATIVE_EDIT_TEXT_DIFFERENT')
            submit(sender);observations={}
            for client in clients:
                def consumed(client=client):
                    rings=channel_ring(client,3,token)
                    visible,archive=rings[0]['matched_rows'],rings[1]['matched_rows']
                    if not archive:return None
                    if client['identity']==hidden:
                        if visible:return None
                    elif not visible:return None
                    for row in visible+archive:
                        require(expected in row['plain'],'GUILD_CHAT_NAME_PREFIX_WRONG')
                        require(row['color']==0xffff00,'GUILD_CHAT_NATIVE_COLOR_WRONG')
                    return rings
                observations[str(client['identity'])]=wait_until(consumed,8,'GUILD_NATIVE_RING_MISSING_'+str(client['identity']))
            marker=wait_until(lambda:next((line for line in log.read_text('utf-8',errors='replace')[old:].splitlines() if 'NATIVE_GUILD_CHAT_REQUEST ' in line and 'character_id='+str(sender['identity'])+' ' in line and 'delivered=2' in line and 'accepted=true' in line),None),4,'GUILD_SERVER_ACCEPTANCE_MISSING')
            after=all_bubbles();require(before==after,'GUILD_CHAT_CHANGED_BUBBLE_FIELDS')
            require(saved()==invariant,'GUILD_CHAT_CHANGED_SQL')
            receipt={'source':sender['identity'],'source_page':sender['page'],'token':token,'typed_input':typed,'route':route,'expected':expected,'native_edit_hex_before_submit':observed.hex(),'native_channel':3,'native_color':0xffff00,'recipient_rings':observations,'bubbles_before':before,'bubbles_after':after,'bubble_fields_unchanged':True,'hidden_recipient':hidden,'server_line':marker,'native_guild_name_after':guild_name(sender),'rendered_pixels_tested':False}
            result['guild_chat_deliveries'].append(receipt);result.pop('pending_guild_chat',None);save();return receipt
        def enable_reception(client):
            for index,bit in ((5,0x10),(6,0x20),(7,0x40)):
                if not input_options(client)['options']&bit:result['reception_setup'].append(reception_toggle(client,index))
            if not input_options(client)['visible_mask']&4:result['filter_events'].append({'initial_enable_guild':guild_filter(client)})
        result['reception_initial']={str(c['identity']):input_options(c) for c in clients}
        result['reception_setup']=[]
        for c in clients:enable_reception(c)
        for sender in (first,other):
            for route in ('prefix','selected'):guild_chat(sender,route,route)
        select_channel(other,0);hidden=guild_filter(other)
        require(not hidden['after']['visible_mask']&4,'GUILD_FILTER_EXPECTED_HIDDEN')
        filtered=guild_chat(first,'filtered','prefix',hidden=other['identity'])
        restore=guild_filter(other);require(restore['after']==hidden['before'],'GUILD_FILTER_NOT_RESTORED')
        replay=wait_until(lambda:channel_ring(other,3,filtered['token']) if channel_ring(other,3,filtered['token'])[0]['matched_rows'] else None,4,'GUILD_ARCHIVE_REPLAY_MISSING')
        result['filter_events'].append({'guild_hide':hidden,'guild_restore':restore,'guild_archive_replay':replay});save()
        select_channel(first,2)
        with closing(sqlite3.connect(database)) as db:
            columns=[row[1] for row in db.execute('pragma table_info(owned_guild_members)')]
            member_row=db.execute('select * from owned_guild_members where character_id=4').fetchone()
            require(member_row is not None,'DISPOSABLE_ADMIN_MEMBER_ROW_REQUIRED')
            db.execute('delete from owned_guild_members where character_id=4');db.commit()
        invariant=saved()
        denial_bubbles_before=all_bubbles();old=len(log.read_text('utf-8',errors='replace'))
        clear_input(first);denied_token='gc75-denied-stale-selected';type_ascii(first['hwnd'],denied_token);submit(first)
        cleared=wait_until(lambda:input_options(first) if guild_name(first)=='' else None,5,'NATIVE_2D_REMOVAL_CLEAR_MISSING')
        require(cleared['selected_channel']==2,'NATIVE_2D_CLEAR_UNEXPECTED_INPUT_RESET')
        roster_cache(first,'membership_removed',0)
        denied_line=wait_until(lambda:next((line for line in log.read_text('utf-8',errors='replace')[old:].splitlines() if 'NATIVE_GUILD_CHAT_REQUEST ' in line and 'character_id=4 ' in line and 'accepted=false' in line),None),5,'GUILD_STALE_MEMBERSHIP_DENIAL_MISSING')
        time.sleep(.5)
        denied_rings={str(c['identity']):{str(channel):channel_ring(c,channel,denied_token) for channel in (0,1,2,3)} for c in clients}
        require(not any(r['matched_rows'] for channels in denied_rings.values() for rings in channels.values() for r in rings),'GUILD_DENIED_TEXT_LEAKED')
        require(denial_bubbles_before==all_bubbles(),'GUILD_DENIAL_CHANGED_BUBBLES');require(saved()==invariant,'GUILD_DENIAL_CHANGED_SQL')
        result['guild_membership_events'].append({'operation':'exclusive_disposable_admin_remove','character_id':4,'native_name_after':'','selected_input_after':2,'server_line':denied_line,'all_channel_rings':denied_rings,'no_common_fallback':True});save()
        with closing(sqlite3.connect(database)) as db:
            db.execute('insert into owned_guild_members('+','.join('"'+c+'"' for c in columns)+') values('+','.join('?' for c in columns)+')',member_row);db.commit()
        invariant=saved();require(invariant==original_invariant,'ADMIN_MEMBERSHIP_RESTORE_NOT_EXACT')
        # Native selected2 intentionally survives empty2D; normal plaintext now
        # makes server reload membership and publish actualname beforechat.
        guild_chat(first,'after-admin-restore','selected',select=False)
        require(guild_name(first)=='labguild','NATIVE_2D_REASSIGN_NAME_MISSING')
        roster_cache(first,'membership_restored')
        result['guild_membership_events'].append({'operation':'exclusive_disposable_admin_restore','character_id':4,'native_name_after':guild_name(first),'exact_original_member_row_restored':True});save()
        for c in clients:select_channel(c,0)
        chat(first,'guild-regression');chat(other,'guild-regression')
        invitation(first,other,True)
        for sender in (first,other):party_chat(sender,'guild-regression',1)
        menu(first,28);wait_until(empty,8,'GUILD_REGRESSION_PARTY_LEAVE_FAILED')
        for c in clients:select_channel(c,0)
        private_chat(first,other,'guild-regression','prefix');private_chat(other,first,'guild-regression','prefix')
        for c in clients:select_channel(c,0)
        old_other=other;close(other)
        wait_until(lambda:base.peer.remote(first['handle'],first['ui'],5) is None,10,'GUILD_PEER_DISCONNECT_NOT_CLEARED')
        other=launch(5,936 if args.source_page==950 else 950);clients.remove(old_other)
        wait_until(lambda:base.peer.remote(first['handle'],first['ui'],5),15,'GUILD_RELOGIN_NOT_VISIBLE')
        initial_guild_projection(other,'relogin')
        enable_reception(other)
        guild_chat(first,'after-relogin','prefix');guild_chat(other,'reverse-relogin','selected')
        roster_cache(other,'relogin')
        result['lifecycle_events'].append({'operation':'target_relogin','target':5,'native_2D_guild_name':guild_name(other)});save()
        result['reception_restore']=[]
        for client in clients:
            for index,bit in ((5,0x10),(6,0x20),(7,0x40)):
                if (input_options(client)['options']^result['reception_initial'][str(client['identity'])]['options'])&bit:result['reception_restore'].append(reception_toggle(client,index))
            if input_options(client)['visible_mask']!=result['reception_initial'][str(client['identity'])]['visible_mask']:guild_filter(client)
            select_channel(client,0)
            require(input_options(client)==result['reception_initial'][str(client['identity'])],'GUILD_CHAT_SETTINGS_NOT_RESTORED')
        require(saved()==original_invariant,'GUILD_CHANGED_ANY_SQL_ROW')
        result['all_tables_after']=saved();result['all_tables_exact']=True
        require(saved()==invariant,'PRIVATE_CHANGED_ANY_SQL_ROW')
        with closing(base.peer.ro(database)) as db:final_positions=db.execute('select * from recovered_positions order by character_id').fetchall()
        require(final_positions==initial_positions,'PRIVATE_CHANGED_POSITIONS_OR_REVISION')
        result['positions_after']=[list(row) for row in final_positions]
        result['all_sql_rows_preserved']=True;result['unrelated_saved_rows_preserved']=True;result['accepted']=True
    except BaseException as error:
        result.update(error=str(error),traceback=traceback.format_exc())
        if result.get('pending_private_chat'):
            try:
                result['failed_chat_rings']={str(c['identity']):{str(channel):channel_ring(c,channel) for channel in (0,1,2)} for c in clients}
            except Exception as diagnostic_error:result['failed_chat_diagnostic_error']=str(diagnostic_error)
    finally:
        for client in reversed(clients):
            try:close(client)
            except Exception as error:result.setdefault('cleanup_errors',[]).append(str(error))
        for loader in loaders:
            if loader.poll() is None:loader.terminate();loader.wait(timeout=5)
        result['desktop_before']=before;result['desktop_after']=desktop_names()
        result['desktop_unchanged']=before==result['desktop_after'];result['all_clients_closed']=not any(psutil.pid_exists(pid) for pid in result.get('owned_client_pids',[]))
        result['accepted']=bool(result['accepted'] and result['desktop_unchanged'] and result['all_clients_closed'] and not result.get('cleanup_errors'));save()
    return 0 if result['accepted'] else 1

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--server-candidate',type=Path);parser.add_argument('--source-page',type=int,choices=(950,936),default=950)
    parser.add_argument('--worker',action='store_true');args=parser.parse_args()
    if args.worker:return worker(args)
    if args.server_candidate is None:parser.error('--server-candidate required')
    qualify();script=Path(__file__).resolve();digest=base.sha(script);frozen_sha=base.sha(FROZEN_PARTY)
    contract=json.loads(CONTRACT.read_text('utf-8'))
    require(base.sha(args.server_candidate)==contract['candidate_sha256'],'TESTED_PARTY_CHAT_CANDIDATE_REQUIRED')
    sources_before=source_guard();desktop_before=desktop_names()
    proof=json.loads(CHAT_PROOF.read_text('utf-8'));require(proof['native_image_sha256']==base.MAPPED_SHA and proof['current_exe_sha256']==base.CLIENT_SHA and proof['counts']=={'guild_name_update':10,'channel_selection':10,'producer':144,'consumer':80,'dispatch':4,'guild_clear_selected_lifecycle':2,'native_options_and_filter_controls':2},'PARTY_CHAT_NATIVE_PROOF_PIN_REQUIRED')
    files=[script,CONTRACT,FROZEN_PARTY,FROZEN_QUERY,CHAT_PROOF,ROOT/'tools/strike_lab/current_guild_chat_20261003.py',ROOT/'tools/strike_lab/private_private_chat_20261003.py',ROOT/'tools/strike_lab/current_party_chat_20261003.py',Path(base.__spec__.origin),Path(pose.__file__),
           ROOT/'tools/strike_lab/private_inventory_move_ui.py',ROOT/'tools/strike_lab/private_potion_ui.py',
           ROOT/'tools/strike_lab/current_party_query_20261003.py']
    frozen={str(p.resolve()):base.sha(p) for p in files}
    protected={str(p.pid):{'exe':p.info['exe'],'created':p.info['create_time']}
        for p in psutil.process_iter(['exe','create_time'])
        if p.info['exe'] and Path(p.info['exe']).name.lower() in
        ('god2.exe','god2-server.exe','leproc.exe','private_desktop_runner.exe')}
    base.__file__=str(script);code=base.owner(args)
    receipt=args.output/'run-result.json'
    if receipt.exists():
        result=json.loads(receipt.read_text('utf-8'));result['guild_harness_sha256']=digest
        result['guild_harness_unchanged']=base.sha(script)==digest
        result['frozen_party_harness_unchanged']=base.sha(FROZEN_PARTY)==frozen_sha
        result['guild_chat_native_proof_sha256']=frozen[str(CHAT_PROOF.resolve())]
        result['guild_chat_native_proof_counts']=proof['counts']
        result['runtime_sources_before']=sources_before;result['runtime_sources_after']=source_guard()
        result['runtime_sources_unchanged']=result['runtime_sources_before']==result['runtime_sources_after']
        result['frozen_files_before']=frozen;result['frozen_files_after']={p:base.sha(Path(p)) for p in frozen}
        result['frozen_files_unchanged']=result['frozen_files_before']==result['frozen_files_after']
        protected_after={str(p.pid):{'exe':p.info['exe'],'created':p.info['create_time']}
            for p in psutil.process_iter(['exe','create_time']) if str(p.pid) in protected}
        result['protected_processes_before']=protected;result['protected_processes_after']=protected_after;result['protected_processes_preserved']=protected_after==protected
        result['desktop_owner_unchanged']=desktop_before==desktop_names()
        with socket.socket() as probe:result['exclusive_2598_released']=probe.connect_ex(('127.0.0.1',base.PORT))!=0
        result['owned_pid_count']=len(set([result.get('server_pid'),result.get('runner_pid')]+result.get('ui',{}).get('owned_client_pids',[]))-{None})
        result['accepted']=bool(result['accepted'] and result['guild_harness_unchanged'] and result['frozen_party_harness_unchanged'] and result['exclusive_2598_released'] and result['owned_pid_count']==5 and result['runtime_sources_unchanged'] and result['frozen_files_unchanged'] and result['protected_processes_preserved'] and result['desktop_owner_unchanged']);base.peer.dump(receipt,result)
        return 0 if result['accepted'] else 1
    return code
if __name__=='__main__':raise SystemExit(main())
