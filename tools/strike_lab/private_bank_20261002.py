"""Original TW/CN bank money UI on a new, owned hidden desktop and port2598.

No foreground activation, screenshots, process-memory writes or packet injection.
Only disposable copies have their port changed. Saves are an isolated backup.
"""
import argparse,os,json,sqlite3,struct,sys,time,traceback,subprocess
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
    regions=((0x471190,848),(0x471510,128),(0x4719b0,816),(0x471e10,1104),
             (0x497380,416),(0x496860,44),(0x498d70,89),(0x5077c0,138),
             (0x41e500,70),(0x426700,200),(0x426140,600),
             (0x46a68b,1027),(0x461510,240),(0x4618b0,208),(0x4cc380,1184))
    for va,size in regions:
        require(mapped[va-0x400000:va-0x400000+size]==raw[va-0x400000:va-0x400000+size],
                'NATIVE_BANK_CODE_CHANGED_'+hex(va))
    return {'current_client_sha256':base.sha(base.LIVE),'regions':regions,
            'open':'NPC world click ->37 target -> server46 mode0; fixture CUSTOM_TEST, not native placement',
            'money':'bank232DD2 edit59 ->deposit57/withdraw58 ->61/62 body8',
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
        require(pool>0x10000 and 0<=renderer<4096,'BANK_LABEL_RENDERER_MISSING')
        command=number(c,pool+0x10+renderer*0x290+0xe,2)
        surface=number(c,pool+4);require(surface>0x10000 and command<5000,'BANK_LABEL_COMMAND_MISSING')
        text=number(c,surface+0x1264+command*200+index*2,2,True)
        require(0<=text<30000,'BANK_LABEL_TEXT_MISSING')
        raw=exact(c,surface+0xf66e4+text*0x8c,0x8c)
        return {'renderer':renderer,'command':command,'index':text,'raw_hex':raw.hex(),
                'text_bytes_hex':raw[12:].hex()}
    def snap(c):
        bank=widget(c,0x232dd2)
        return {'identity':c['identity'],'language':c['page'],'bank_widget':bank,
                'bank_label':label(c,bank,0) if bank is not None else None,
                'target':number(c,c['ui']+0x839c0),'mode':number(c,c['ui']+0x855ed,1),
                'bank':number(c,c['ui']+0x839c4),'input':number(c,c['ui']+0x839c8),
                'purse':number(c,c['ui']+0x85604)}
    def saved():
        with closing(base.peer.ro(database)) as db:
            return {'wallets':[list(r) for r in db.execute('select character_id,amount,revision from character_trade_wallets order by character_id')],
                    'bank':[list(r) for r in db.execute('select character_id,amount,revision from character_bank_balances order by character_id')],
                    'receipts':[list(r) for r in db.execute('select * from character_bank_receipts order by receipt')]}
    def untouched():
        with closing(base.peer.ro(database)) as db:
            return {name:sorted(repr(row) for row in db.execute('select * from "'+name.replace('"','""')+'"'))
                    for name, in db.execute("select name from sqlite_master where type='table' order by name")
                    if name not in ('character_bank_balances','character_trade_wallets','character_bank_receipts')}
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
        invariant=untouched();result['initial']={'native':[snap(c) for c in clients],'db':saved()};save()
        for c in clients:
            require(snap(c)['purse']==1000,'WALLET_27_NOT_LOADED')
            native_npc=wait_until(lambda:base.owned.native_world_records(c['handle'],c['ui']).get('npc'),8,'BANK_NPC_NATIVE_RENDERER_UNAVAILABLE')
            require(native_npc['identity']==fixture['bank_fixture']['npc_target'] and
                    [native_npc['x'],native_npc['y']]==[128,126] and native_npc['renderer_active'],
                    'BANK_NPC_WRONG_NATIVE_INSTANCE')
            result.setdefault('qualified_native_npc',[]).append(native_npc);save()
            def opened():
                state=base.ground.world_state(c['handle'],c['ui'])
                px,py=base.ground.ground_point(c['handle'],state,128,126)
                click(c['hwnd'],px,py-26)
                wait_until(lambda:widget(c,0x232dd2) is not None,8,'BANK_NOT_OPEN_BY_NPC37')
                now=snap(c);require(now['target']==fixture['bank_fixture']['npc_target'] and now['mode']==0,'WRONG_BANK_CONTEXT')
                result['events'].append({'operation':'NPC37_bank_open','native':now,'db':saved()});save()
            def operation(control_id,amount,expected_purse,expected_bank):
                w=widget(c,0x232dd2);require(w is not None,'BANK_CLOSED_BEFORE_MONEY')
                control(c,w,59);type_ascii(c['hwnd'],'\b'*10+str(amount));time.sleep(.4)
                require(snap(c)['input']==amount,'BANK_INPUT_NOT_EDITED');control(c,w,control_id)
                wait_until(lambda:snap(c)['purse']==expected_purse and snap(c)['bank']==expected_bank,8,'BANK_MONEY_NOT_UPDATED')
                now=snap(c);require(str(expected_bank).encode() in bytes.fromhex(now['bank_label']['text_bytes_hex']),'BANK_LABEL_NOT_RENDERED')
                db=saved();require(next(row[1] for row in db['wallets'] if row[0]==c['identity'])==expected_purse,'BANK_WALLET_NOT_DURABLE')
                require(next(row[1] for row in db['bank'] if row[0]==c['identity'])==expected_bank,'BANK_BALANCE_NOT_DURABLE')
                result['events'].append({'operation':'deposit61' if control_id==57 else 'withdraw62','amount':amount,'native':now,'db':db});save()
            opened();operation(57,250,750,250);operation(58,100,850,150)
            control(c,widget(c,0x232dd2),54)
            wait_until(lambda:widget(c,0x232dd2) is None,5,'BANK_CLOSE39_NOT_LOCAL')
            result['events'].append({'operation':'close39','identity':c['identity']});save()
            opened();require(snap(c)['bank']==150 and snap(c)['purse']==850,'REOPEN_DURABLE_STATE_MISSING')
            operation(58,150,1000,0);control(c,widget(c,0x232dd2),54)
            wait_until(lambda:widget(c,0x232dd2) is None,5,'BANK_FINAL_CLOSE_MISSING')
            require(untouched()==invariant,'BANK_CHANGED_UNRELATED_SAVED_ROWS')
        result['final']={'native':[snap(c) for c in clients],'db':saved()}
        require(len(result['final']['db']['receipts'])==6,'BANK_RECEIPTS_MISSING')
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
    parser.add_argument('--npc-hex',default='');parser.add_argument('--worker',action='store_true');parser.add_argument('--qualify-only',action='store_true');args=parser.parse_args()
    if args.qualify_only:print(json.dumps(qualify()));return 0
    if args.output is None:parser.error('--output required')
    if args.worker:return worker(args)
    if args.server_candidate is None:parser.error('--server-candidate required')
    if not args.npc_hex:parser.error('--npc-hex required for explicit qualified CUSTOM_TEST fixture')
    os.environ['GOD2_NATIVE_WORLD_RECORDS_LAB']='1'
    qualify();script=Path(__file__).resolve();digest=base.sha(script);base.__file__=str(script);code=base.owner(args)
    receipt=args.output/'run-result.json'
    if receipt.exists():
        result=json.loads(receipt.read_text('utf-8'));result['bank_harness_sha256']=digest
        result['bank_harness_unchanged']=base.sha(script)==digest
        result['accepted']=bool(result['accepted'] and result['bank_harness_unchanged']);base.peer.dump(receipt,result)
        return 0 if result['accepted'] else 1
    return code
if __name__=='__main__':raise SystemExit(main())
