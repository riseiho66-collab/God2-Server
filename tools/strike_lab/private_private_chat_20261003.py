"""Two original TW/CN clients, native directed private chat and automatic reply.

Port-only disposable client copies, read-only observation, window-local input.
No screenshots, memory writes, packet injection or input-desktop switching.
"""
import argparse,json,re,socket,sqlite3,struct,sys,time,traceback
from contextlib import closing
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]
import psutil,pefile
import private_peer_role_text_20260930 as base
import private_peer_pose_20261002 as pose
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,type_ascii
base.CLIENT_SHA=pose.CLIENT_SHA
from tools.strike_lab.current_private_chat_20261003 import REGIONS as QUERY_REGIONS
FROZEN_PARTY=ROOT/'tools/strike_lab/private_party_chat_20261003.py'
FROZEN_QUERY=ROOT/'tools/strike_lab/private_party_query_20261003.py'
CHAT_PROOF=ROOT/'artifacts/research/native-private-chat-20261003/native.json'
from tools.strike_lab.current_party_chat_20261003 import REGIONS as CHAT_REGIONS
CONTRACT=ROOT/'artifacts/research/native-private-chat-0074/candidate-20261003/contract.json'

def source_guard():
    contract=json.loads(CONTRACT.read_text('utf-8'))
    require(contract['design']=='CUSTOM-0074','PARTY_CHAT_CONTRACT_REQUIRED')
    actual={name:base.sha(ROOT/name) for name in contract['source_sha256']}
    require(actual==contract['source_sha256'],'COMPILED_PARTY_CHAT_SOURCES_CHANGED')
    return actual

def qualify():
    raw=pose.qualify_source();current=pefile.PE(str(base.LIVE)).get_memory_mapped_image()
    for start,end in CHAT_REGIONS+QUERY_REGIONS+((0x505680,0x505770),(0x505e90,0x505f70),(0x4c7460,0x4c7610)):
        require(current[start-0x400000:end-0x400000]==raw[start-0x400000:end-0x400000],'NATIVE_QUERY_CODE_CHANGED_'+hex(start))
    for va,size in ((0x497140,0x100),(0x497230,35),(0x4e9bc0,740),
                    (0x4e9ad0,150),(0x4ea140,180),(0x4ea8a0,580),(0x4ea770,230),
                    (0x4835a0,250),(0x481f70,160),(0x465fa0,420),(0x4a7300,35)):
        require(current[va-0x400000:va-0x400000+size]==raw[va-0x400000:va-0x400000+size],
                'NATIVE_PARTY_CODE_CHANGED_'+hex(va))

original_prepare=base.prepare
def prepare(args):
    original_prepare(args)
    config=json.loads((args.output/'server-config.json').read_text('utf-8'))
    config['world']['clock']={'enabled':False}
    base.peer.dump(args.output/'server-config.json',config)
    with closing(sqlite3.connect(args.output/'town-diagnostic-accounts.db')) as db:
        db.execute('update recovered_positions set x=129,y=126 where character_id=5')
        text='private4';name=text.encode('cp'+str(args.source_page))
        profile=bytearray(db.execute('select profile from recovered_characters where id=4').fetchone()[0])
        profile[:16]=name+bytes(16-len(name))
        db.execute('update recovered_characters set profile=?,name_bytes=?,name_codepage=? where id=4',
                   (profile,name,args.source_page))
        name5=b'private5';profile5=bytearray(db.execute('select profile from recovered_characters where id=5').fetchone()[0]);profile5[:16]=name5+bytes(16-len(name5))
        db.execute('update recovered_characters set profile=?,name_bytes=?,name_codepage=? where id=5',(profile5,name5,936 if args.source_page==950 else 950));db.commit()
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'))
    fixture['party_names']={'4':{'raw':text,'950':text,'936':text},
                            '5':{'raw':'private5','950':'private5','936':'private5'}}
    base.peer.dump(args.output/'fixture.json',fixture)
base.prepare=prepare

def worker(args):
    import subprocess
    before=desktop_names();clients=[];loaders=[]
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'))
    database=args.output/'town-diagnostic-accounts.db';log=args.output/'server.log'
    result={'accepted':False,'events':[],'party_chat_deliveries':[],'filter_events':[],'query_deliveries':[],'private_chat_deliveries':[],'lifecycle_events':[],'automatic_reply_events':[],'rendered_pixels_tested':False,'source_page':args.source_page,'input_policy':'Window-local native WM events; normal Backspace clears observed shortcut residue; $prefix and Shift+native control13 selected private input; read-only memory; no packets or code injection; no movements'}
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
            bit=0x10 if index==5 else 0x20
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
        result['reception_initial']={str(c['identity']):input_options(c) for c in clients};save()
        result['reception_setup']=[]
        for client in clients:
            for index,bit in ((5,0x10),(6,0x20)):
                if input_options(client)['options']&bit==0:result['reception_setup'].append(reception_toggle(client,index))
            if not input_options(client)['visible_mask']&8:result['filter_events'].append({'initial_enable':private_filter(client)})
        for sender,recipient in ((first,other),(other,first)):
            for route in ('prefix','selected'):private_chat(sender,recipient,route,route)
        select_channel(other,0);toggle=private_filter(other);require(toggle['after']['visible_mask']&8==0,'PRIVATE_FILTER_EXPECTED_HIDDEN')
        filtered=private_chat(first,other,'filtered','prefix',hidden=other['identity'])
        restored=private_filter(other);require(restored['after']==toggle['before'],'PRIVATE_FILTER_NOT_RESTORED')
        replay=wait_until(lambda:channel_ring(other,2,filtered['token']) if channel_ring(other,2,filtered['token'])[0]['matched_rows'] else None,4,'PRIVATE_HISTORY_REPLAY_MISSING')
        result['filter_events'].append({'hide':toggle,'restore':restored,'archive_replay':replay});save()
        template=away(other,True)
        require(template,'NATIVE_AWAY_TEMPLATE0_EMPTY')
        old_reply=len(log.read_text('utf-8',errors='replace'))
        auto_before={str(c['identity']):channel_ring(c,2) for c in clients}
        expected_body=template.decode('cp'+str(other['page']))
        require(expected_body=='嗨~安安!','QUALIFIED_DEFAULT_AWAY_TEMPLATE_CHANGED')
        expected_auto={str(c['identity']):fixture['party_names'][str(other['identity'])]['raw']+': ['+fixture['party_names'][str(first['identity'])]['raw']+'] '+expected_body for c in clients}
        origin=private_chat(first,other,'away','prefix')
        def auto_received(client):
            rings=channel_ring(client,2);matching=[]
            expected=expected_auto[str(client['identity'])]
            for ring_index,ring in enumerate(rings):
                old_rows=auto_before[str(client['identity'])][ring_index]['matched_rows']
                old_keys={(row['index'],row['text_hex']) for row in old_rows}
                require(not any(row['plain'].endswith(expected) for row in old_rows),'AWAY_EXACT_ROW_EXISTED_BEFORE')
                rows=[row for row in ring['matched_rows'] if row['plain'].endswith(expected) and (row['index'],row['text_hex']) not in old_keys]
                if not rows:return None
                require(len(rows)==1,'AWAY_MULTIPLE_EXACT_REPLIES')
                require(rows[0]['color']==0xffff,'AWAY_NATIVE_COLOR_WRONG')
                matching.append({'ring':ring['ring'],'expected_text':expected,'before_count':len(old_rows),'matched_rows':rows,'only_new_exact_rows':True})
            return matching
        received={str(c['identity']):wait_until(lambda c=c:auto_received(c),8,'NATIVE_AWAY_REPLY_RING_MISSING') for c in clients}
        time.sleep(1)
        markers=[line for line in log.read_text('utf-8',errors='replace')[old_reply:].splitlines() if 'NATIVE_PRIVATE_CHAT_REQUEST ' in line and 'accepted=true' in line]
        require(len(markers)==2 and sum('character_id=5 ' in line for line in markers)==1,'NATIVE_AWAY_REPLY_LOOP_OR_MISSING')
        require(saved()==invariant,'AUTOREPLY_CHANGED_SQL')
        result['automatic_reply_events'].append({'source':4,'away_recipient':5,'native_away_flag':exact(other,other['ui']+0x23d89c,1)[0],'template0_hex':template.hex(),'native_channel':2,'native_color':0xffff,'rings':received,'before_rings':auto_before,'expected_text_by_recipient':expected_auto,'only_new_exact_rows':True,'new_exact_rows_verified':True,'server_lines':markers,'single_native_mode9_reply':True,'live_scope':'one actual Away recipient; no repeated reply; both enabled incoming9 behavior is machine qualified','rendered_pixels_tested':False});save()
        away(other,False)
        for client in clients:select_channel(client,0)
        chat(first,1);chat(other,1)
        invitation(first,other,True)
        for sender in (first,other):party_chat(sender,'regression',1)
        menu(first,28);wait_until(empty,8,'PRIVATE_REGRESSION_PARTY_LEAVE_FAILED')
        for client in clients:select_channel(client,0)
        old_other=other;close(other);wait_until(lambda:base.peer.remote(first['handle'],first['ui'],5) is None,10,'PRIVATE_PEER_DISCONNECT_NOT_CLEARED')
        token='pv74-offline';clear_input(first);type_ascii(first['hwnd'],'$private5 '+token);submit(first);time.sleep(1)
        require(not any(r['matched_rows'] for r in channel_ring(first,2,token)),'OFFLINE_PRIVATE_LEAKED_SELF_SUCCESS')
        result['lifecycle_events'].append({'operation':'target_disconnect','target':5,'offline_message_absent':True});save()
        other=launch(5,936 if args.source_page==950 else 950)
        clients.remove(old_other)
        wait_until(lambda:base.peer.remote(first['handle'],first['ui'],5),15,'PRIVATE_RELOGIN_NOT_VISIBLE')
        private_chat(first,other,'after-relogin','prefix');private_chat(other,first,'reverse-relogin','prefix')
        result['lifecycle_events'].append({'operation':'target_relogin','target':5});save()
        result['reception_restore']=[]
        for client in clients:
            for index,bit in ((5,0x10),(6,0x20)):
                if (input_options(client)['options']^result['reception_initial'][str(client['identity'])]['options'])&bit:result['reception_restore'].append(reception_toggle(client,index))
            if input_options(client)['visible_mask']!=result['reception_initial'][str(client['identity'])]['visible_mask']:private_filter(client)
            select_channel(client,0)
            require(input_options(client)==result['reception_initial'][str(client['identity'])],'PRIVATE_CHAT_SETTINGS_NOT_RESTORED')
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
        result['desktop_unchanged']=before==desktop_names();result['all_clients_closed']=not any(psutil.pid_exists(pid) for pid in result.get('owned_client_pids',[]))
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
    proof=json.loads(CHAT_PROOF.read_text('utf-8'));require(proof['native_image_sha256']==base.MAPPED_SHA and proof['current_exe_sha256']==base.CLIENT_SHA and proof['counts']=={'producer':72,'consumer':48,'dispatch':8,'dedicated_conversation':10,'automatic_reply':4,'speaker_extraction':8,'ui_state':2},'PARTY_CHAT_NATIVE_PROOF_PIN_REQUIRED')
    files=[script,CONTRACT,FROZEN_PARTY,FROZEN_QUERY,CHAT_PROOF,ROOT/'tools/strike_lab/current_private_chat_20261003.py',ROOT/'tools/strike_lab/current_party_chat_20261003.py',Path(base.__spec__.origin),Path(pose.__file__),
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
        result=json.loads(receipt.read_text('utf-8'));result['private_harness_sha256']=digest
        result['private_harness_unchanged']=base.sha(script)==digest
        result['frozen_party_harness_unchanged']=base.sha(FROZEN_PARTY)==frozen_sha
        result['private_chat_native_proof_sha256']=frozen[str(CHAT_PROOF.resolve())]
        result['private_chat_native_proof_counts']=proof['counts']
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
        result['accepted']=bool(result['accepted'] and result['private_harness_unchanged'] and result['frozen_party_harness_unchanged'] and result['exclusive_2598_released'] and result['owned_pid_count']==5 and result['runtime_sources_unchanged'] and result['frozen_files_unchanged'] and result['protected_processes_preserved'] and result['desktop_owner_unchanged']);base.peer.dump(receipt,result)
        return 0 if result['accepted'] else 1
    return code
if __name__=='__main__':raise SystemExit(main())
