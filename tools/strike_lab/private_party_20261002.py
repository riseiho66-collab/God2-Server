"""Two original TW/CN clients, native party UI, owned hidden desktop only.

Port-only disposable client copies, read-only observation, window-local input.
No screenshots, memory writes, packet injection or input-desktop switching.
"""
import argparse,json,sqlite3,struct,sys,time,traceback
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

def qualify():
    raw=pose.qualify_source();current=pefile.PE(str(base.LIVE)).get_memory_mapped_image()
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
        text='台' if args.source_page==950 else '臺';name=text.encode('cp'+str(args.source_page))
        profile=bytearray(db.execute('select profile from recovered_characters where id=4').fetchone()[0])
        profile[:16]=name+bytes(16-len(name))
        db.execute('update recovered_characters set profile=?,name_bytes=?,name_codepage=? where id=4',
                   (profile,name,args.source_page));db.commit()
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'))
    fixture['party_names']={'4':{'raw':text,'950':'臺','936':'台'},
                            '5':{'raw':'fixedgirl','950':'fixedgirl','936':'fixedgirl'}}
    base.peer.dump(args.output/'fixture.json',fixture)
base.prepare=prepare

def worker(args):
    import subprocess
    before=desktop_names();clients=[];loaders=[]
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'))
    database=args.output/'town-diagnostic-accounts.db';log=args.output/'server.log'
    result={'accepted':False,'events':[],'rendered_pixels_tested':False,'source_page':args.source_page}
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
    def menu(client,index,mode=None):
        if mode is not None and word(client,client['ui']+0x232f36)==mode:return
        if widget(client,0x232e4e) is None:
            for message,vk,data in ((0x100,0x11,1),(0x100,0x48,1),(0x101,0x48,0xc0000001),(0x101,0x11,0xc0000001)):
                require(base.peer.user.PostMessageW(client['hwnd'],message,vk,data),'MENU_KEY_FAILED');time.sleep(.1)
        w=wait_until(lambda:widget(client,0x232e4e),8,'MAIN_MENU_NOT_OPEN')
        control(client,w,23);control(client,w,index)
        if mode is not None:wait_until(lambda:word(client,client['ui']+0x232f36)==mode,5,'PARTY_CURSOR_MODE_MISSING')
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
        # Movement is the only intended durable mutation in this UI run.
        with closing(base.peer.ro(database)) as db:
            return {name:{'sql':sql,'rows':sorted(repr(row) for row in db.execute('select * from "'+name.replace('"','""')+'"'))}
                    for name,sql in db.execute("select name,sql from sqlite_master where type='table' order by name").fetchall()
                    if name!='recovered_positions'}
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
            result['owned_client_pids']=[c['process'].pid for c in clients];save()
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
        for requester,leader in ((first,other),(other,first)):
            invitation(requester,leader,False);invitation(requester,leader,True)
            # Real native mouse movement must update the observer's56 array
            # after the movement commit, in both casting/language directions.
            state=base.ground.world_state(requester['handle'],requester['ui'])
            for destination in ((state['x']+1,state['y']),(state['x'],state['y'])):
                current=base.ground.world_state(requester['handle'],requester['ui'])
                click(requester['hwnd'],*base.ground.ground_point(requester['handle'],current,*destination))
                def moved():
                    row=snapshot(leader);peer=next((r for r in row['rows'] if r['id']==requester['identity']),None)
                    local=base.ground.world_state(requester['handle'],requester['ui'])
                    position=base.position(database,requester['identity'])
                    if peer and peer['position']==[requester['identity'],*destination] and [local['x'],local['y']]==list(destination) and position[:4]==[4,3,*destination]:
                        return {'local':local,'observer':peer,'saved':position}
                    return None
                observation=wait_until(moved,12,'PARTY_NATIVE_MOVEMENT_NOT_UPDATED')
                result['events'].append({'operation':'move','source':requester['identity'],'destination':list(destination),'native':observation});save()
            menu(requester,28);wait_until(empty,8,'NATIVE_LEAVE_NOT_CLEARED')
            result['events'].append({'operation':'leave','source':requester['identity']});save()
            invitation(requester,leader,True);target(leader,requester,27,5)
            wait_until(empty,8,'NATIVE_KICK_NOT_CLEARED');result['events'].append({'operation':'kick','source':leader['identity']});save()
        invitation(first,other,True);close(other);wait_until(empty,8,'LEADER_DISCONNECT_NOT_CLEARED')
        result['events'].append({'operation':'leader_disconnect','source':5});save()
        require(saved()==invariant,'PARTY_CHANGED_UNRELATED_SAVED_ROWS')
        with closing(base.peer.ro(database)) as db:
            final_positions=db.execute('select * from recovered_positions order by character_id').fetchall()
        require([row[:5] for row in final_positions]==[row[:5] for row in initial_positions],'PARTY_CHANGED_UNRELATED_POSITIONS')
        require(all(after==before if before[0] not in (4,5) else after[5]>=before[5]+2
                    for before,after in zip(initial_positions,final_positions)),'PARTY_POSITION_REVISION_MISMATCH')
        result['positions_after']=[list(row) for row in final_positions]
        result['unrelated_saved_rows_preserved']=True;result['accepted']=True
    except BaseException as error:result.update(error=str(error),traceback=traceback.format_exc())
    finally:
        for client in reversed(clients):
            try:close(client)
            except Exception as error:result.setdefault('cleanup_errors',[]).append(str(error))
        for loader in loaders:
            if loader.poll() is None:loader.terminate();loader.wait(timeout=5)
        result['desktop_unchanged']=before==desktop_names();result['all_clients_closed']=not any(psutil.pid_exists(c['process'].pid) for c in clients)
        result['accepted']=bool(result['accepted'] and result['desktop_unchanged'] and result['all_clients_closed'] and not result.get('cleanup_errors'));save()
    return 0 if result['accepted'] else 1

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--server-candidate',type=Path);parser.add_argument('--source-page',type=int,choices=(950,936),default=950)
    parser.add_argument('--worker',action='store_true');args=parser.parse_args()
    if args.worker:return worker(args)
    qualify();script=Path(__file__).resolve();digest=base.sha(script)
    base.__file__=str(script);code=base.owner(args)
    receipt=args.output/'run-result.json'
    if receipt.exists():
        result=json.loads(receipt.read_text('utf-8'));result['party_harness_sha256']=digest
        result['party_harness_unchanged']=base.sha(script)==digest
        result['accepted']=bool(result['accepted'] and result['party_harness_unchanged']);base.peer.dump(receipt,result)
        return 0 if result['accepted'] else 1
    return code
if __name__=='__main__':raise SystemExit(main())
