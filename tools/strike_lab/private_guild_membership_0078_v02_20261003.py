"""CUSTOM0078 isolated native8D/6F current-client membership acceptance.

Purpose-built God2Lab hidden desktop only, port-only private client copies,
window-local native WM input and VM_READ observation. No screenshots, foreground
activation, packet injection, process memory writes or client/resource changes.
TEST_ONLY auto prompt is not an original NPC entry or complete leader UI proof.
Requires a new immutable root-created live-v02/contract.json before execution.
V02 provisions TEST_ONLY wallet only after runtime49, before hidden runner login.
"""
import argparse,hashlib,json,os,re,socket,sqlite3,struct,subprocess,sys,time,traceback
from contextlib import closing
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent),str(ROOT/'artifacts/tooling/crypto-oracle-python')]
import psutil,pefile
import private_peer_role_text_20260930 as base
import private_peer_pose_20261002 as pose
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,type_ascii
base.CLIENT_SHA=pose.CLIENT_SHA
CONTRACT=ROOT/'artifacts/research/native-guild-membership-0078/live-v02/contract.json'
PROOF=ROOT/'artifacts/research/native-guild-membership-0078/menu-trace/name-producer.json'
TABLES=('owned_guilds','owned_guild_members','owned_guild_governance_0078','owned_guild_applications_0078')
NAME='LabCave0078'

def dump(path,value):base.peer.dump(path,value)
def ro(database):return base.peer.ro(database)
def snapshots(database):
    with closing(ro(database)) as db:
        schema=db.execute("select type,name,tbl_name,coalesce(sql,'') from sqlite_master order by type,name").fetchall()
        tables={name:sorted(repr(row) for row in db.execute('select * from "'+name.replace('"','""')+'"'))
                for (name,) in db.execute("select name from sqlite_master where type='table' order by name").fetchall()}
        return {'schema':schema,'tables':tables}
def rows(database,table):
    with closing(ro(database)) as db:return db.execute('select * from '+table).fetchall()
def data(database,sql,parameters=()):
    with closing(ro(database)) as db:return db.execute(sql,parameters).fetchall()
def changed_only(before,after,allowed):
    require(before['schema']==after['schema'],'OPERATION_CHANGED_SQL_SCHEMA')
    require(set(before['tables'])==set(after['tables']),'OPERATION_CHANGED_SQL_TABLE_SET')
    for table in before['tables']:
        if table not in allowed:require(before['tables'][table]==after['tables'][table],'UNRELATED_SQL_ROWS_CHANGED_'+table)
    return {table:{'before':before['tables'].get(table),'after':after['tables'].get(table)} for table in allowed}
def env_lab():
    env=os.environ.copy();env.update(GOD2_LOG_FILE_ONLY='1',GOD2_NATIVE_WORLD_RECORDS_LAB='1',GOD2_NATIVE_GUILD_MEMBERSHIP_LAB='1')
    env.pop('GOD2_PRIVATE_SIDECAR_COMMAND',None);return env
def qualify():
    require(base.sha(base.LIVE)==base.CLIENT_SHA,'CURRENT_CLIENT_PIN_CHANGED')
    require(base.sha(base.RUNNER)==base.RUNNER_SHA,'PRIVATE_RUNNER_PIN_CHANGED')
    proof=json.loads(PROOF.read_text('utf-8'));require(proof['client_sha256']==base.CLIENT_SHA and proof['original_sha256']==base.MAPPED_SHA,'NATIVE_MEMBERSHIP_PROOF_IDENTITY')
    mapped=pefile.PE(str(base.LIVE)).get_memory_mapped_image()
    for pin in proof['code_pins']:
        lo=int(pin['start_va'],16)-0x400000;hi=int(pin['end_va_exclusive'],16)-0x400000
        require(hashlib.sha256(mapped[lo:hi]).hexdigest()==pin['sha256'],'MEMBERSHIP_NATIVE_CODE_CHANGED')
    return proof
def contract_guard(args):
    contract=json.loads(args.contract.read_text('utf-8'))
    require(contract['design']=='CUSTOM-0078','MEMBERSHIP_CONTRACT_REQUIRED')
    require(contract['candidate_sha256']==base.sha(args.server_candidate),'QUALIFIED_CANDIDATE_REQUIRED')
    require(contract['helper_sha256']==base.sha(Path(__file__)),'QUALIFIED_HELPER_REQUIRED')
    actual={p:base.sha(ROOT/p) for p in contract['source_sha256']}
    require(actual==contract['source_sha256'],'CANDIDATE_SOURCE_CLOSURE_CHANGED')
    return contract,actual

def prepare(args):
    require(args.output.name.startswith('private-native-blackbox-'),'DISPOSABLE_DB_SCOPE_REQUIRED')
    args.output.mkdir(parents=True,exist_ok=False);database=args.output/'town-diagnostic-accounts.db'
    raw=base.LIVE.read_bytes();needle=bytes.fromhex('68 20 0a 00 00 68 9c 47 5b 00')
    require(raw.count(needle)==1,'UNIQUE_NATIVE_PORT_SITE_REQUIRED')
    changed=bytearray(raw);struct.pack_into('<I',changed,raw.index(needle)+1,base.PORT)
    clients={}
    for page,locale,zone in ((950,'zh-TW','Taipei Standard Time'),(936,'zh-CN','China Standard Time')):
        image=base.LIVE.with_name(args.output.name+'-'+str(page)+'-2598.exe');profile=Path(str(image)+'.le.config')
        require(not image.exists() and not profile.exists(),'NEW_PRIVATE_CLIENT_FILES_REQUIRED')
        with image.open('xb') as stream:stream.write(changed)
        xml='<LEConfig><Profiles><Profile Name="God2 Chinese" Guid="9548b642-f82c-4883-a523-425904744e6f" MainMenu="false"><Parameter></Parameter><Location>'+locale+'</Location><Timezone>'+zone+'</Timezone><RunAsAdmin>false</RunAsAdmin><RedirectRegistry>false</RedirectRegistry><IsAdvancedRedirection>false</IsAdvancedRedirection><RunWithSuspend>false</RunWithSuspend></Profile></Profiles></LEConfig>'
        with profile.open('x',encoding='utf-8') as stream:stream.write(xml)
        clients[str(page)]={'path':str(image),'sha256':base.sha(image),'profile':str(profile),'profile_sha256':base.sha(profile)}
        # Incremental ownership receipt allows exact cleanup if prepare later fails.
        dump(args.output/'fixture.json',{'clients':clients,'authority':'CUSTOM_TEST_NOT_NATIVE','source_database':str(base.SOURCE)})
    with closing(ro(base.SOURCE)) as source,closing(sqlite3.connect(database)) as target:source.backup(target)
    config=json.loads(base.SOURCE.with_name('server-config.json').read_text('utf-8'))
    config['database']['path']=str(database);config['logging']['file']=str(args.output/'server.log')
    config['server'].update(host='127.0.0.1',port=base.PORT,character_port=0)
    config['development']['diagnostic_remote_actor_language']=int(args.source_page==936)
    config['world']['clock']={'enabled':False};dump(args.output/'server-config.json',config)
    # main --migrate-only installs default48; Application.run alone installs49.
    with (args.output/'migration.log').open('wb') as log:
        migration=subprocess.run([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--migrate-only'],cwd=ROOT,env=env_lab(),check=True,timeout=60,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    with closing(sqlite3.connect(database)) as db:
        for identity,x in ((4,126),(5,127)):
            db.execute('INSERT INTO recovered_positions VALUES(?,4,3,?,126,1) ON CONFLICT(character_id) DO UPDATE SET area=4,scene=3,x=excluded.x,y=126,revision=1',(identity,x))
        for table in ('owned_guilds','owned_guild_members'):
            require(db.execute('select count(*) from '+table).fetchone()[0]==0,'FIXTURE_MUST_NOT_HAVE_PRESEEDED_'+table)
        role=db.execute('select logical,revision from character_role_snapshots where character_id=4').fetchone();require(role and len(role[0])==25 and role[0][0]==0x22,'CHARACTER4_ROLE_REQUIRED')
        logical=bytearray(role[0]);logical[1]=30
        db.execute('update character_role_snapshots set logical=?,revision=? where character_id=4',(bytes(logical),role[1]+1))
        role5=db.execute('select logical from character_role_snapshots where character_id=5').fetchone();require(role5 and role5[0][1]==1,'JOINER_LEVEL1_FIXTURE_REQUIRED')
        db.commit();require(db.execute('pragma quick_check').fetchone()==('ok',),'CLONE_INTEGRITY')
    fixture={'clients':clients,'source_database':str(base.SOURCE),'source_sha256':base.sha(base.SOURCE),'client_source_sha256':base.CLIENT_SHA,
        'source_page':args.source_page,'authority':'CUSTOM_TEST_NOT_NATIVE','migration_exit':migration.returncode,
        'test_only_character4':{'role_level':30,'wallet_amount':100000},'test_only_character5':{'role_level':1},
        'guild_rows_seeded':0,'member_rows_seeded':0,'pending_rows_seeded':0,'changed_client_offsets':[i for i,(a,b) in enumerate(zip(raw,changed)) if a!=b]}
    dump(args.output/'fixture.json',fixture)

def provision_wallet_fixture(args):
    # Runtime installs this table outside --migrate-only. No client/runner exists
    # yet; fixture SQL belongs only to this exclusive disposable clone.
    database=args.output/'town-diagnostic-accounts.db'
    require(args.output.name.startswith('private-native-blackbox-'),'DISPOSABLE_WALLET_FIXTURE_SCOPE_REQUIRED')
    require(data(database,'select max(version) from schema_migrations')[0][0]==49,'WALLET_FIXTURE_REQUIRES_RUNTIME49')
    for table in TABLES:require(not rows(database,table),'WALLET_FIXTURE_MUST_NOT_SEED_GUILD_ROWS')
    before=snapshots(database)
    with closing(sqlite3.connect(database)) as db:
        db.execute("insert into character_trade_wallets(character_id,amount,revision,design_id) values(4,100000,1,'CUSTOM-0063') on conflict(character_id) do update set amount=100000,revision=revision+1")
        db.execute("insert into character_trade_wallets(character_id,amount,revision,design_id) values(5,0,1,'CUSTOM-0063') on conflict(character_id) do nothing")
        db.commit();require(db.execute('pragma quick_check').fetchone()==('ok',),'WALLET_FIXTURE_CLONE_INTEGRITY')
    after=snapshots(database);delta=changed_only(before,after,{'character_trade_wallets'})
    require(data(database,'select amount from character_trade_wallets where character_id=4')==[(100000,)],'WALLET_FIXTURE_AMOUNT_WRONG')
    require(data(database,'select amount from character_trade_wallets where character_id=5')==[(0,)],'JOINER_WALLET_FIXTURE_AMOUNT_WRONG')
    before_other=[r for r in before['tables']['character_trade_wallets'] if not (r.startswith('(4,') or r.startswith('(5,'))]
    after_other=[r for r in after['tables']['character_trade_wallets'] if not (r.startswith('(4,') or r.startswith('(5,'))]
    require(before_other==after_other,'WALLET_FIXTURE_CHANGED_OTHER_CHARACTERS')
    dump(args.output/'fixture-wallet-provision.json',{'authority':'CUSTOM_TEST_NOT_NATIVE','phase':'runtime49_server_listening_before_hidden_runner_login','SQL_delta':delta,'other_tables_exact':True,'other_wallet_rows_exact':True})
    dump(args.output/'fixture-sql-before-login.json',after)

def worker(args):
    before=desktop_names();clients=[];loaders=[];database=args.output/'town-diagnostic-accounts.db';log=args.output/'server.log'
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'))
    result={'accepted':False,'locale':args.source_page,'events':[],'entry_origin':'TEST_ONLY_AUTO_ENTRY_CUSTOM0078_NOT_ORIGINAL_NPC','rendered_pixels_tested':False,
        'input_policy':'owned hidden desktop native WM input; VM_READ only; no memory writes/code or packet injection/screenshots/foreground'}
    def save():dump(args.output/'ui-result.json',result)
    def exact(c,address,size):return base.peer.exact(c['handle'],address,size)
    def number(c,address,size=4,signed=False):return int.from_bytes(exact(c,address,size),'little',signed=signed)
    def cstring(c,address,bound=256):
        require(address>0x10000,'NATIVE_TEXT_POINTER_MISSING');raw=exact(c,address,bound);require(b'\0' in raw,'NATIVE_TEXT_UNTERMINATED');return raw.split(b'\0',1)[0]
    def widget(c):
        w=number(c,c['ui']+0x232e20,2,True)
        if 0<=w<128 and exact(c,c['ui']+0xe2988+w*0x2a08,1)[0]&0x20:return w
        return None
    def control(c,w,index):
        point=base.owned.control_point(c['handle'],c['ui'],w,index)
        require(len(point)==2 and 0<=point[0]<800 and 0<=point[1]<600,'NATIVE_CONTROL_POINT_INVALID')
        result['last_control']={'identity':c['identity'],'widget':w,'control':index,'point':list(point)};save();click(c['hwnd'],*point);time.sleep(.15)
    def state(c):
        mode=number(c,c['ui']+0xd26c);w=widget(c)
        require(mode in (4,5) and w is not None and number(c,c['ui']+0x232f36,2)==9,'NATIVE_NAME_INPUT_NOT_READY')
        title_ptr=number(c,0x5b88b8+4*mode);description_ptr=number(c,0x5b887c+4*mode)
        title=cstring(c,title_ptr);description=cstring(c,description_ptr)
        title_expected=('建立' if mode==4 else '加入').encode('cp'+str(c['page']))
        description_expected=(('建立洞府需求5萬' if c['page']==950 else '建立洞府需求5万') if mode==4
                              else ('請輸入洞府名稱' if c['page']==950 else '请输入洞府名称'))
        require(title==title_expected and description==description_expected.encode('cp'+str(c['page'])),'NATIVE_NAME_INPUT_LABEL_MISMATCH')
        selected=number(c,c['ui']+0x8688c);require(selected>0x10000,'NATIVE_CALLER_WORD_POINTER_MISSING')
        return {'widget':w,'mode':mode,'input_mode':9,'context':number(c,c['ui']+0xae64,2),
            'title_pointer':hex(title_ptr),'title_hex':title.hex(),'title':title.decode('cp'+str(c['page'])),
            'description_pointer':hex(description_ptr),'description_hex':description.hex(),'description':description.decode('cp'+str(c['page'])),
            'caller_word':number(c,selected,2),'input_hex':exact(c,c['ui']+0xc6fc,256).split(b'\0',1)[0].hex()}
    def close(c):
        if c.get('handle'):base.peer.kernel.CloseHandle(c.pop('handle'))
        if c['process'].is_running():
            base.peer.user.PostMessageW(c['hwnd'],0x10,0,0)
            try:c['process'].wait(timeout=4)
            except psutil.TimeoutExpired:c['process'].terminate();c['process'].wait(timeout=5)
    def launch(identity):
        page=args.source_page;image=Path(fixture['clients'][str(page)]['path'])
        require(base.sha(image)==fixture['clients'][str(page)]['sha256'],'PRIVATE_CLIENT_PIN_CHANGED')
        loader=subprocess.Popen([str(base.LE),'-run',str(image),'127.0.0.1','127.0.0.1','6001','1'],cwd=base.LIVE.parent,creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);loaders.append(loader)
        result.setdefault('owned_loader_pids',[]).append(loader.pid);save()
        def found():
            matches=[p for p in psutil.process_iter(['exe']) if p.info['exe'] and Path(p.info['exe']).resolve()==image.resolve()]
            require(len(matches)<=1,'DUPLICATE_PRIVATE_IMAGE');return matches[0] if matches else None
        process=wait_until(found,35,'PRIVATE_CLIENT_MISSING');c={'process':process,'identity':identity,'page':page};clients.append(c)
        result.setdefault('owned_client_pids',[]).append(process.pid);save()
        c['hwnd']=wait_until(lambda:base.peer.window_for(process.pid),35,'PRIVATE_WINDOW_MISSING')
        time.sleep(12);click(c['hwnd'],512,464);time.sleep(4)
        bound='RECOVERED_ACCOUNT_BOUND account_id='+str(identity);old=log.read_text('utf-8',errors='replace').count(bound)
        click(c['hwnd'],437,232);type_ascii(c['hwnd'],'codexslow' if identity==4 else 'codexfixed')
        click(c['hwnd'],437,263);type_ascii(c['hwnd'],'labtest2345');click(c['hwnd'],452,304)
        wait_until(lambda:log.read_text('utf-8',errors='replace').count(bound)>old,35,'LOGIN_FAILED')
        time.sleep(4);click(c['hwnd'],330,145);click(c['hwnd'],452,413);time.sleep(4)
        click(c['hwnd'],330,150);click(c['hwnd'],452,376);time.sleep(4);click(c['hwnd'],452,370)
        # Prompt has a30s lifetime. Do not borrow the older12s post-world sleep.
        c['handle']=base.peer.kernel.OpenProcess(0x1010,False,process.pid);require(c['handle'],'VM_READ_HANDLE_REQUIRED')
        def observed_ui():
            try:return base.peer.find_ui(c['handle'],identity,(0,3,4))
            except RuntimeError as error:
                if str(error)==f'UI_STRUCTURE_MATCHES_{identity}_0':return None
                raise
        c['ui']=wait_until(observed_ui,12,'NATIVE_UI_BASE_MISSING')
        language,sub=struct.unpack('<HH',exact(c,0x59dfd8,4));require(language==4 and (sub==2)==(page==936),'PRIVATE_LOCALE_MISMATCH')
        observed=wait_until(lambda:state(c) if widget(c) is not None and number(c,c['ui']+0xd26c)==(4 if identity==4 else 5) else None,5,'NATIVE_8D_PROMPT_NOT_VISIBLE')
        result['events'].append({'operation':'native_prompt','identity':identity,**observed});save();return c
    def submit(c,method):
        observed=state(c);require(observed['input_hex']=='','NATIVE_NAME_INPUT_NOT_EMPTY')
        control(c,observed['widget'],2);type_ascii(c['hwnd'],NAME)
        edited=wait_until(lambda:state(c) if exact(c,c['ui']+0xc6fc,len(NAME)+1)==NAME.encode()+b'\0' else None,3,'NATIVE_NAME_INPUT_NOT_APPLIED')
        offset=len(log.read_text('utf-8',errors='replace'))
        if method=='control0':control(c,edited['widget'],0)
        else:
            for message,data_value in ((0x100,1),(0x101,0xc0000001)):
                require(base.peer.user.PostMessageW(c['hwnd'],message,13,data_value),'NATIVE_INPUT_RETURN_FAILED');time.sleep(.1)
        wanted='character_id='+str(c['identity'])+' '
        line=wait_until(lambda:next((line for line in log.read_text('utf-8',errors='replace')[offset:].splitlines() if 'OWNED_GUILD_MEMBERSHIP_REQUEST ' in line and wanted in line and 'accepted=true ' in line),None),8,'NATIVE_6F_REQUEST_NOT_ACCEPTED')
        require('operation='+str(c['identity']-4)+' ' in line and 'context='+str(edited['context'])+' ' in line,'NATIVE_6F_CONTEXT_OPERATION_MISMATCH')
        wait_until(lambda:widget(c) is None,5,'NATIVE_NAME_INPUT_DID_NOT_CLOSE')
        event={'operation':'native_6F','identity':c['identity'],'method':method,'state':edited,'log':line,'accepted':True};result['events'].append(event);save();return event
    try:
        qualify();require(before['current'].startswith('God2Lab-') and before['current']!=before['input'],'HIDDEN_DESKTOP_REQUIRED')
        wait_until(lambda:data(database,'select max(version) from schema_migrations')[0][0]==49,8,'CANDIDATE_SCHEMA49_NOT_STARTED')
        for table in TABLES:require(not rows(database,table),'REAL_GAMEPLAY_MUST_BEGIN_WITHOUT_GUILD_SEEDS')
        creator=launch(4);before_create=snapshots(database);wallet_before=data(database,'select amount,revision from character_trade_wallets where character_id=4')[0]
        wallet_others_before=data(database,'select * from character_trade_wallets where character_id<>4 order by character_id')
        create_event=submit(creator,'control0' if args.source_page==950 else 'Return')
        wait_until(lambda:bool(data(database,'select id from owned_guilds where name_utf8=?',(NAME,))),5,'CREATE_NOT_DURABLE')
        after_create=snapshots(database);delta=changed_only(before_create,after_create,{'owned_guilds','owned_guild_members','owned_guild_governance_0078','character_trade_wallets'})
        guild=data(database,'select id,name_utf8,revision,origin,design_id,source_sha256 from owned_guilds')[0]
        require(len(rows(database,'owned_guilds'))==1 and guild[1]==NAME and guild[3:]==('CUSTOM_DESIGNED','CUSTOM-0075',base.MAPPED_SHA),'CREATED_GUILD_PROVENANCE_WRONG')
        members=data(database,'select character_id,guild_id,revision from owned_guild_members')
        require(members==[(4,guild[0],guild[2])],'CREATE_OWNER_MEMBERSHIP_WRONG')
        governance=data(database,'select guild_id,owner_account,owner_character,created_revision,created_cost,capacity,origin,design_id,source_sha256 from owned_guild_governance_0078')
        require(governance==[(guild[0],4,4,guild[2],50000,20,'CUSTOM_DESIGNED','CUSTOM-0078',base.MAPPED_SHA)],'CREATE_GOVERNANCE_WRONG')
        wallet_after=data(database,'select amount,revision from character_trade_wallets where character_id=4')[0]
        require(wallet_before[0]==100000 and wallet_after==(50000,wallet_before[1]+1),'CREATION_FEE_NOT_EXACT')
        unchanged_other_wallet=data(database,'select * from character_trade_wallets where character_id<>4 order by character_id')
        require(unchanged_other_wallet==wallet_others_before,'CREATE_CHANGED_OTHER_PLAYERS_WALLETS')
        require(not rows(database,'owned_guild_applications_0078'),'CREATE_INSERTED_PENDING')
        result['real_create']={'accepted':True,'fee':50000,'wallet_before':wallet_before,'wallet_after':wallet_after,'guild':guild,'members':members,'governance':governance,'SQL_delta':delta,'native':create_event};save()
        # Only one image per locale: cleanly close creator before launchjoiner.
        close(creator);joiner=launch(5);before_apply=snapshots(database)
        other_sequences_before=data(database,"select * from sqlite_sequence where name<>'owned_guild_applications_0078' order by name")
        join_event=submit(joiner,'Return' if args.source_page==950 else 'control0')
        wait_until(lambda:bool(data(database,'select id from owned_guild_applications_0078 where character_id=5')),5,'APPLICATION_NOT_DURABLE')
        after_apply=snapshots(database);delta=changed_only(before_apply,after_apply,{'owned_guild_applications_0078','sqlite_sequence'})
        applications=data(database,'select guild_id,guild_name,observed_revision,character_id,account_id,slot,name_utf8,origin,design_id,source_sha256 from owned_guild_applications_0078')
        require(len(applications)==1 and applications[0][:6]==(guild[0],NAME,guild[2],5,5,0) and applications[0][-3:]==('CUSTOM_DESIGNED','CUSTOM-0078',base.MAPPED_SHA),'APPLICATION_OWNER_PROVENANCE_WRONG')
        require(data(database,'select character_id,guild_id,revision from owned_guild_members')==members,'JOIN_APPLICATION_GRANTED_MEMBERSHIP')
        require(data(database,'select amount,revision from character_trade_wallets where character_id=4')[0]==wallet_after and data(database,'select * from character_trade_wallets where character_id<>4 order by character_id')==unchanged_other_wallet,'JOIN_APPLICATION_DEBITED_WALLET')
        require(data(database,"select * from sqlite_sequence where name<>'owned_guild_applications_0078' order by name")==other_sequences_before,'APPLICATION_CHANGED_OTHER_SEQUENCES')
        stored_identity=data(database,'select account_id,slot,profile,name_bytes,name_codepage from recovered_characters where id=5')[0]
        stored_role=data(database,'select logical,revision,design_id from character_role_snapshots where character_id=5')[0]
        pending_identity=data(database,'select account_id,slot,profile,name_bytes,name_codepage,role,role_revision,role_design from owned_guild_applications_0078 where character_id=5')[0]
        require(pending_identity==stored_identity+stored_role,'APPLICATION_RETAINED_IDENTITY_OR_ROLE_WRONG')
        require(not data(database,'select character_id from owned_guild_members where character_id=5'),'JOINER_MUST_REMAIN_NONMEMBER')
        require(data(database,'select logical from character_role_snapshots where character_id=5')[0][0][1]==1,'JOINER_LEVEL_CHANGED')
        result['real_pending_application']={'accepted':True,'joiner_still_nonmember':True,'no_fee':True,'application':applications[0],'SQL_delta':delta,'native':join_event}
        result['SQL_after']=after_apply;result['accepted']=True;save()
    except BaseException as error:result.update(error=str(error),traceback=traceback.format_exc())
    finally:
        for c in reversed(clients):
            try:close(c)
            except Exception as error:result.setdefault('cleanup_errors',[]).append(str(error))
        for loader in loaders:
            if loader.poll() is None:loader.terminate();loader.wait(timeout=5)
        result['desktop_before']=before;result['desktop_after']=desktop_names();result['desktop_unchanged']=before==result['desktop_after']
        result['all_clients_closed']=not any(psutil.pid_exists(pid) for pid in result.get('owned_client_pids',[]))
        result['all_loaders_closed']=all(loader.poll() is not None for loader in loaders)
        result['accepted']=bool(result['accepted'] and result['desktop_unchanged'] and result['all_clients_closed'] and result['all_loaders_closed'] and not result.get('cleanup_errors'));save()
    return 0 if result['accepted'] else 1

def protected():
    return {str(p.pid):{'exe':p.info['exe'],'created':p.info['create_time'],'command':p.cmdline(),'cwd':p.cwd()}
        for p in psutil.process_iter(['exe','create_time']) if p.info['exe'] and Path(p.info['exe']).name.lower() in ('god2.exe','god2-server.exe','leproc.exe','private_desktop_runner.exe')}
def guard_sources(protected_processes):
    files={'client':base.LIVE,'client_locale':Path(str(base.LIVE)+'.le.config'),'source_DB':base.SOURCE,'source_config':base.SOURCE.with_name('server-config.json'),
        'launcher_settings':base.LIVE.parent/'config/user.settings','global_locale':base.LE.with_name('LEConfig.xml'),'LE':base.LE,'loader':base.LE.with_name('LoaderDll.dll'),'locale_runtime':base.LE.with_name('LocaleEmulator.dll')}
    databases={str(base.SOURCE.resolve())}
    for pid,p in protected_processes.items():
        if Path(p['exe']).name.lower()!='god2-server.exe':continue
        command=p['command']
        if '--config' not in command:continue
        at=command.index('--config');require(at+1<len(command),'PROTECTED_SERVER_CONFIG_MISSING')
        path=Path(command[at+1]);path=path if path.is_absolute() else Path(p['cwd'])/path
        require(path.is_file(),'PROTECTED_SERVER_CONFIG_NOT_FOUND');files['protected_server_config_'+pid]=path
        config=json.loads(path.read_text('utf-8'));database=Path(config['database']['path']);database=database if database.is_absolute() else Path(p['cwd'])/database
        require(database.is_file(),'PROTECTED_SERVER_DATABASE_NOT_FOUND');databases.add(str(database.resolve()));files['formal_DB_'+pid]=database
    return files,databases
def owner_case(args):
    result={'accepted':False,'locale':args.source_page};server=runner=None
    try:
        with socket.socket() as probe:require(probe.connect_ex(('127.0.0.1',base.PORT))!=0,'PRIVATE_PORT_ALREADY_USED')
        prepare(args)
        with (args.output/'stdout.log').open('wb') as log,(args.output/'runner.log').open('wb') as runnerlog:
            server=subprocess.Popen([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--run-for','330'],cwd=ROOT,env=env_lab(),stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);result['server_pid']=server.pid
            def listening():
                require(server.poll() is None,'PRIVATE_SERVER_EXITED')
                with socket.socket() as probe:return probe.connect_ex(('127.0.0.1',base.PORT))==0
            wait_until(listening,15,'PRIVATE_SERVER_NOT_LISTENING')
            database=args.output/'town-diagnostic-accounts.db'
            wait_until(lambda:data(database,'select max(version) from schema_migrations')[0][0]==49,8,'CANDIDATE_SCHEMA49_NOT_STARTED')
            provision_wallet_fixture(args)
            runner=subprocess.Popen([str(base.RUNNER),sys.executable,'-X','utf8','-B',str(Path(__file__).resolve()),'--worker','--output',str(args.output),'--source-page',str(args.source_page)],cwd=ROOT,env=env_lab(),stdout=runnerlog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);result['runner_pid']=runner.pid
            result['runner_exit']=runner.wait(timeout=310);result['ui']=json.loads((args.output/'ui-result.json').read_text('utf-8'));result['accepted']=result['runner_exit']==0 and result['ui']['accepted']
    except BaseException as error:result.update(error=str(error),traceback=traceback.format_exc())
    finally:
        for process in (runner,server):
            if process is not None and process.poll() is None:
                children=psutil.Process(process.pid).children(recursive=True)
                for child in reversed(children):
                    try:child.terminate()
                    except psutil.NoSuchProcess:pass
                process.terminate();process.wait(timeout=5);_,alive=psutil.wait_procs(children,timeout=5)
                for child in alive:child.kill();child.wait(timeout=5)
        fixture=args.output/'fixture.json'
        if fixture.exists():
            images=json.loads(fixture.read_text('utf-8'))['clients'];paths={Path(c['path']).resolve() for c in images.values()}
            for process in psutil.process_iter(['exe']):
                if process.info['exe'] and Path(process.info['exe']).resolve() in paths:
                    try:process.terminate();process.wait(timeout=5)
                    except psutil.NoSuchProcess:pass
            result['private_files_unchanged']=all(base.sha(Path(c['path']))==c['sha256'] and base.sha(Path(c['profile']))==c['profile_sha256'] for c in images.values())
            result['all_private_images_closed']=not any(p.info['exe'] and Path(p.info['exe']).resolve() in paths for p in psutil.process_iter(['exe']))
        result['server_exit']=None if server is None else server.poll();result['all_owned_processes_closed']=(runner is None or runner.poll() is not None) and (server is None or server.poll() is not None)
        with socket.socket() as probe:result['exclusive_2598_released']=probe.connect_ex(('127.0.0.1',base.PORT))!=0
        result['accepted']=bool(result['accepted'] and result['all_owned_processes_closed'] and result['exclusive_2598_released'] and result.get('private_files_unchanged') and result.get('all_private_images_closed'))
        if args.output.exists():dump(args.output/'run-result.json',result)
    return result
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--server-candidate',type=Path)
    parser.add_argument('--contract',type=Path,default=CONTRACT);parser.add_argument('--source-page',type=int,choices=(950,936));parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS);args=parser.parse_args()
    args.output=args.output.resolve()
    if args.worker:require(args.source_page is not None,'WORKER_LOCALE_REQUIRED');return worker(args)
    if args.server_candidate is None:parser.error('--server-candidate required')
    args.server_candidate=args.server_candidate.resolve();args.contract=args.contract.resolve();qualify();contract,sources_before=contract_guard(args)
    require(not args.output.exists(),'NEW_ACCEPTANCE_OUTPUT_REQUIRED');args.output.mkdir(parents=True,exist_ok=False)
    before=desktop_names();foreground_before=int(base.peer.user.GetForegroundWindow() or 0);protected_before=protected();files,databases=guard_sources(protected_before)
    hashes_before={name:base.sha(p) for name,p in files.items()};DB_before={p:snapshots(Path(p)) for p in databases}
    frozen_paths=[Path(__file__),args.contract,PROOF,Path(base.__spec__.origin),Path(pose.__file__),ROOT/'tools/strike_lab/private_guild_panel_v04_20261003.py',ROOT/'tools/strike_lab/private_inventory_move_ui.py',ROOT/'tools/strike_lab/private_potion_ui.py']
    frozen_before={str(p):base.sha(p) for p in frozen_paths};result={'accepted':False,'contract_sha256':base.sha(args.contract),'cases':[]}
    try:
        for page in ((args.source_page,) if args.source_page else (950,936)):
            case=argparse.Namespace(**vars(args));case.source_page=page;case.output=args.output/('private-native-blackbox-0078-'+args.output.name+'-'+str(page))
            outcome=owner_case(case);result['cases'].append(outcome)
            require(outcome['accepted'],'LOCALE_ACCEPTANCE_FAILED_'+str(page))
        result['accepted']=True
    except BaseException as error:result.update(error=str(error),traceback=traceback.format_exc())
    finally:
        result['sources_before']=sources_before;result['sources_after']={p:base.sha(ROOT/p) for p in contract['source_sha256']}
        result['sources_unchanged']=result['sources_before']==result['sources_after']
        result['files_before']=hashes_before;result['files_after']={name:base.sha(p) for name,p in files.items()};result['protected_files_unchanged']=result['files_before']==result['files_after']
        result['protected_DB_before']=DB_before;result['protected_DB_after']={p:snapshots(Path(p)) for p in databases};result['protected_DB_exact']=result['protected_DB_before']==result['protected_DB_after']
        result['frozen_before']=frozen_before;result['frozen_after']={p:base.sha(Path(p)) for p in frozen_before};result['frozen_unchanged']=result['frozen_before']==result['frozen_after']
        current=protected();result['protected_processes_before']=protected_before;result['protected_processes_after']={pid:current[pid] for pid in protected_before if pid in current};result['protected_processes_exact']=result['protected_processes_after']==protected_before
        result['desktop_before']=before;result['desktop_after']=desktop_names();result['desktop_unchanged']=before==result['desktop_after']
        result['foreground_before']=foreground_before;result['foreground_after']=int(base.peer.user.GetForegroundWindow() or 0);result['foreground_unchanged']=result['foreground_before']==result['foreground_after']
        result['candidate_unchanged']=base.sha(args.server_candidate)==contract['candidate_sha256']
        result['accepted']=bool(result['accepted'] and all(result[k] for k in ('sources_unchanged','protected_files_unchanged','protected_DB_exact','frozen_unchanged','protected_processes_exact','desktop_unchanged','foreground_unchanged','candidate_unchanged')))
        dump(args.output/'run-result.json',result)
    print(json.dumps({'accepted':result['accepted'],'error':result.get('error'),'locale_cases':len(result['cases']),'output':str(args.output)}));return 0 if result['accepted'] else 1
if __name__=='__main__':raise SystemExit(main())
