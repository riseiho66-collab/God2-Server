"""CUSTOM0078 ordinary nonmember native help087B ->7A2996 ->8D/6F acceptance.

NEW helper: physical independent client assets, explicit two MultiMessage03
resource overrides in disposable roots. No working client/resource changes.
Purpose-built hidden desktop native WM events / VM_READ only. No screenshots,
foreground input, packet injection or process memory writes. VM_READ loaded
table/row/input evidence is NOT rendered-pixel or visual typography acceptance.
Native first: ordinary toolbar4, real menu row click; no auto8D fixture shortcut.
Retains V05 real create/application/approve/memberleave/reject SQL invariants and
TEST_ONLY founder reservation simulation, which is not actual battle acceptance.
Requires root-created immutable general-entry-live-v01 contract before execution.
"""
import argparse,hashlib,json,os,re,socket,sqlite3,struct,subprocess,sys,time,traceback,importlib.util,shutil,stat
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
CONTRACT=ROOT/'artifacts/research/native-guild-membership-0078/general-entry-live-v01/contract.json'
FIELD_PROOF=ROOT/'artifacts/research/native-guild-membership-0078/general-entry-live-v01/context-e7-v01/field-pins.json'
RESOURCE_PLAN=ROOT/'artifacts/research/native-guild-membership-0078/entry-resource-consumer-v01/private-resource-profile.json'
COPY_PLAN=ROOT/'artifacts/research/native-guild-membership-0078/entry-resource-consumer-v01/required-copy-plan.json'
LOADER_RESULT=ROOT/'artifacts/research/native-guild-membership-0078/entry-resource-parser-v01/run-result-v06.json'
FROZEN_HELPER=ROOT/'tools/strike_lab/private_guild_leadership_0078_v05_20261004.py'
draw_spec=importlib.util.spec_from_file_location('guild_leadership_draw_v01',ROOT/'artifacts/research/native-guild-panel-0077/header-flow/draw-storage.py')
draw=importlib.util.module_from_spec(draw_spec);draw_spec.loader.exec_module(draw)
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

def reservation_record(database,reservation):
    return data(database,'select id,character_id,resource_revision,design_id from battle_reservations where id=?',(reservation,))

def seed_founder_reservation(database,output,quiescence):
    # This SQL is TEST_ONLY and never called against a formal/shared database.
    database=database.resolve();output=output.resolve()
    require(database.parent==output and output.name.startswith('private-native-blackbox-'), 'RESERVATION_EXCLUSIVE_CLONE_REQUIRED')
    require(quiescence['all_owned_clients_closed'] and quiescence['all_bound_sessions_disconnected'], 'RESERVATION_QUIESCENCE_REQUIRED')
    before=snapshots(database)
    with closing(sqlite3.connect(database)) as db:
        db.execute('pragma foreign_keys=on');db.execute('begin immediate')
        require(db.execute('select max(version) from schema_migrations').fetchone()==(49,), 'RESERVATION_SCHEMA49_REQUIRED')
        require(db.execute('pragma foreign_key_check').fetchall()==[], 'RESERVATION_FK_INVALID_BEFORE')
        resource=db.execute('select * from character_resources where character_id=4').fetchall()
        require(len(resource)==1 and len(resource[0])==7 and resource[0][1]>0 and resource[0][5]>0 and resource[0][6]=='CUSTOM-0012', 'RESERVATION_LIVE_CURRENT_RESOURCE_REQUIRED')
        revision=resource[0][5]
        require(not db.execute('select r.id from battle_reservations r left join battle_settlements s on s.battle_id=r.id where r.character_id=4 and s.battle_id is null').fetchall(), 'RESERVATION_EXISTING_UNSETTLED_FOUNDER')
        old_rows=db.execute('select * from battle_reservations order by id').fetchall()
        old_sequence=db.execute("select name,seq from sqlite_sequence where name='battle_reservations'").fetchall()
        other_sequences=db.execute("select name,seq from sqlite_sequence where name<>'battle_reservations' order by name").fetchall()
        require(db.execute('select character_id from owned_guild_members order by character_id').fetchall()==[(4,),(5,)], 'RESERVATION_AFTER_REAL_APPROVE_REQUIRED')
        require(db.execute('select character_id from owned_guild_applications_0078').fetchall()==[(6,)], 'RESERVATION_PENDING6_REQUIRED')
        require(db.execute('select owner_account,owner_character from owned_guild_governance_0078').fetchall()==[(4,4)], 'RESERVATION_FOUNDER4_GOVERNANCE_REQUIRED')
        cursor=db.execute("insert into battle_reservations(character_id,resource_revision,design_id) values(4,?,'CUSTOM-0012')",(revision,))
        reservation=cursor.lastrowid;record=(reservation,4,revision,'CUSTOM-0012')
        require(cursor.rowcount==1 and reservation>0, 'RESERVATION_SINGLE_INSERT_REQUIRED')
        require(db.execute('select * from battle_reservations order by id').fetchall()==sorted(old_rows+[record]), 'RESERVATION_CHANGED_OTHER_ROWS')
        require(not db.execute('select battle_id from battle_settlements where battle_id=?',(reservation,)).fetchall() and not db.execute('select battle_id from battle_checkpoints where battle_id=?',(reservation,)).fetchall(), 'RESERVATION_MUST_BE_UNSETTLED_WITHOUT_CHECKPOINT')
        require(db.execute('select * from character_resources where character_id=4').fetchall()==resource, 'RESERVATION_MUTATED_RESOURCES')
        require(db.execute("select name,seq from sqlite_sequence where name='battle_reservations'").fetchall()==[('battle_reservations',reservation)], 'RESERVATION_SEQUENCE_DELTA_WRONG')
        require(db.execute("select name,seq from sqlite_sequence where name<>'battle_reservations' order by name").fetchall()==other_sequences, 'RESERVATION_CHANGED_OTHER_SEQUENCE')
        require(db.execute('pragma foreign_key_check').fetchall()==[], 'RESERVATION_FK_INVALID_AFTER')
        db.commit()
    after=snapshots(database);delta=changed_only(before,after,{'battle_reservations','sqlite_sequence'})
    event={'authority':'TEST_ONLY_SQL_FIXTURE_NOT_NATIVE_BATTLE','actual_battle_visual_tested':False,
        'phase':'all_owned_clients_and_bound_world_sessions_closed_after_real71_before_member5_relogin',
        'reservation':list(record),'founder_resource_exact':resource,'single_gameplay_row_added':True,
        'sequence_before':old_sequence,'sequence_after':[('battle_reservations',reservation)],
        'sequence_policy':'AUTOINCREMENT metadata explicitly counted; never roll clock backwards',
        'quiescence':quiescence,'SQL_before':before,'SQL_after':after,'SQL_delta':delta,
        'all_other_tables_exact':True,'other_reservation_rows_exact':True,'no_settlement_or_checkpoint':True,
        'cleanup_completed':False}
    dump(output/'fixture-founder-reservation-setup.json',event);return event

def clear_founder_reservation(database,output,event,quiescence):
    require(quiescence['all_owned_clients_closed'] and quiescence['all_bound_sessions_disconnected'], 'RESERVATION_CLEANUP_QUIESCENCE_REQUIRED')
    before=snapshots(database);record=tuple(event['reservation'])
    require(reservation_record(database,record[0])==[record], 'RESERVATION_CAS_PREIMAGE_CHANGED')
    require(data(database,'select * from character_resources where character_id=4')==event['founder_resource_exact'], 'RESERVATION_FOUNDER_RESOURCES_CHANGED')
    with closing(sqlite3.connect(database)) as db:
        db.execute('pragma foreign_keys=on');db.execute('begin immediate')
        require(db.execute('select * from battle_reservations where id=?',(record[0],)).fetchall()==[record], 'RESERVATION_CAS_TRANSACTION_PREIMAGE_CHANGED')
        cursor=db.execute('delete from battle_reservations where id=? and character_id=? and resource_revision=? and design_id=? '
            'and not exists(select 1 from battle_settlements where battle_id=?) '
            'and not exists(select 1 from battle_checkpoints where battle_id=?)',record+(record[0],record[0]))
        require(cursor.rowcount==1, 'RESERVATION_CAS_CLEANUP_NOT_SINGLE_ROW')
        require(db.execute('pragma foreign_key_check').fetchall()==[], 'RESERVATION_CLEANUP_FK_INVALID')
        db.commit()
    after=snapshots(database);delta=changed_only(before,after,{'battle_reservations'})
    require(after['tables']['battle_reservations']==sorted(r for r in before['tables']['battle_reservations'] if r!=repr(record)), 'RESERVATION_CLEANUP_CHANGED_OTHER_RESERVATIONS')
    cleanup={'authority':'TEST_ONLY_SINGLE_ROW_SQL_CAS_CLEANUP_NOT_GAMEPLAY','reservation':list(record),
        'deleted_rows':1,'SQL_before':before,'SQL_after':after,'SQL_delta':delta,'quiescence':quiescence,
        'all_other_tables_exact':True,'sequence_unchanged_during_cleanup':True,'resource_exact':True,
        'governance_pending_memberships_exact':True,'completed':True}
    event['cleanup_completed']=True;dump(output/'fixture-founder-reservation-cleanup.json',cleanup);return cleanup

def env_lab():
    env=os.environ.copy();env.update(GOD2_LOG_FILE_ONLY='1',GOD2_NATIVE_WORLD_RECORDS_LAB='1',GOD2_NATIVE_GUILD_MEMBERSHIP_LAB='1',GOD2_NATIVE_GUILD_ENTRY_LAB='1')
    env.pop('GOD2_PRIVATE_SIDECAR_COMMAND',None);return env
def qualify():
    require(base.sha(base.LIVE)==base.CLIENT_SHA,'CURRENT_CLIENT_PIN_CHANGED')
    require(base.sha(base.RUNNER)==base.RUNNER_SHA,'PRIVATE_RUNNER_PIN_CHANGED')
    proof=json.loads(PROOF.read_text('utf-8'));require(proof['client_sha256']==base.CLIENT_SHA and proof['original_sha256']==base.MAPPED_SHA,'NATIVE_MEMBERSHIP_PROOF_IDENTITY')
    mapped=pefile.PE(str(base.LIVE)).get_memory_mapped_image()
    for pin in proof['code_pins']:
        lo=int(pin['start_va'],16)-0x400000;hi=int(pin['end_va_exclusive'],16)-0x400000
        require(hashlib.sha256(mapped[lo:hi]).hexdigest()==pin['sha256'],'MEMBERSHIP_NATIVE_CODE_CHANGED')
    fields=json.loads(FIELD_PROOF.read_text('utf-8'))
    require(fields['client_sha256']==base.CLIENT_SHA,'LEADER_NATIVE_FIELD_PROOF_CHANGED')
    for pin in fields['code_pins']:
        lo=int(pin['start'],16)-0x400000;hi=int(pin['end_exclusive'],16)-0x400000
        require(hashlib.sha256(mapped[lo:hi]).hexdigest()==pin['sha256'],'LEADER_NATIVE_INPUT_CODE_CHANGED')
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
    copy_plan=json.loads(COPY_PLAN.read_text('utf-8'));resource_plan=json.loads(RESOURCE_PLAN.read_text('utf-8'))
    require(copy_plan['status']=='DESIGN_ONLY_NO_COPY_OR_UI','COPY_PLAN_REQUIRED')
    clients={};page=args.source_page
    require(page in (950,936),'EXCLUSIVE_LOCALE_CLIENT_ROOT_REQUIRED')
    private_root=args.output/'client-root';private_root.mkdir(exist_ok=False)
    manifest=[]
    def physical_file(source,target,expected_sha=None):
        require(source.is_file() and not source.is_symlink() and not (source.lstat().st_file_attributes&0x400),'SOURCE_REGULAR_NO_REPARSE_REQUIRED')
        source=source.resolve()
        require(source.is_relative_to(base.LIVE.parent.resolve()),'SOURCE_CLIENT_ROOT_ESCAPE')
        target=target.absolute();require(target.is_relative_to(private_root.absolute()) and not target.exists(),'EXCLUSIVE_PRIVATE_FILE_REQUIRED')
        target.parent.mkdir(parents=True,exist_ok=True)
        digest=base.sha(source)
        if expected_sha:require(digest==expected_sha,'COPY_SOURCE_PIN_CHANGED')
        shutil.copyfile(source,target);require(base.sha(target)==digest and target.stat().st_nlink==1,'PHYSICAL_COPY_BYTE_MISMATCH_OR_LINK')
        manifest.append({'relative_path':target.relative_to(private_root).as_posix(),'bytes':source.stat().st_size,'sha256':digest})
    # An exclusive physical tree; never links or CWD-only resource overrides.
    for entry in copy_plan['copy_directories']:
        source_root=base.LIVE.parent/entry['relative_path']
        require(not (source_root.lstat().st_file_attributes&0x400),'SOURCE_DIR_REPARSE_FORBIDDEN')
        for path,dirs,files in os.walk(source_root,followlinks=False):
            for directory in dirs:require(not ((Path(path)/directory).lstat().st_file_attributes&0x400),'NESTED_REPARSE_FORBIDDEN')
            for filename in files:
                source=Path(path)/filename;physical_file(source,private_root/source.relative_to(base.LIVE.parent))
    for entry in copy_plan['copy_root_files']:
        source=Path(entry['path']);physical_file(source,private_root/source.name,entry['sha256'])
    image=private_root/'God2.exe';require(base.sha(image)==base.CLIENT_SHA,'COPIED_CURRENT_EXE_NOT_FROZEN')
    image.write_bytes(changed)
    overrides=[]
    for entry in resource_plan['resource_profiles']:
        target=private_root/entry['client_lookup_relative_path'];artifact=Path(entry['artifact_replacement']['path'])
        require(base.sha(target)==entry['working_source']['sha256'] and base.sha(artifact)==entry['artifact_replacement']['sha256'],'RESOURCE_PROFILE_PIN_CHANGED')
        require(not target.is_symlink() and not(target.lstat().st_file_attributes&0x400),'RESOURCE_TARGET_REPARSE_FORBIDDEN')
        shutil.copyfile(artifact,target);require(base.sha(target)==entry['artifact_replacement']['sha256'],'PRIVATE_RESOURCE_REPLACEMENT_MISMATCH')
        overrides.append({'relative_path':entry['client_lookup_relative_path'],'original_sha256':entry['working_source']['sha256'],'private_sha256':base.sha(target)})
    profile=Path(str(image)+'.le.config');require(not profile.exists(),'FRESH_PRIVATE_PROFILE_REQUIRED')
    locale,zone=('zh-TW','Taipei Standard Time') if page==950 else ('zh-CN','China Standard Time')
    xml='<LEConfig><Profiles><Profile Name="God2 Chinese" Guid="9548b642-f82c-4883-a523-425904744e6f" MainMenu="false"><Parameter></Parameter><Location>'+locale+'</Location><Timezone>'+zone+'</Timezone><RunAsAdmin>false</RunAsAdmin><RedirectRegistry>false</RedirectRegistry><IsAdvancedRedirection>false</IsAdvancedRedirection><RunWithSuspend>false</RunWithSuspend></Profile></Profiles></LEConfig>'
    with profile.open('x',encoding='utf-8') as stream:stream.write(xml)
    clients[str(page)]={'path':str(image),'sha256':base.sha(image),'profile':str(profile),'profile_sha256':base.sha(profile),'physical_root':str(private_root),'resource_overrides':overrides}
    dump(args.output/'physical-copy-manifest.json',{'source_root':str(base.LIVE.parent),'private_root':str(private_root),'files':manifest,'override_records':overrides,'copied_bytes':sum(v['bytes'] for v in manifest),'no_hardlink_or_junction':True,'actual_copy':True})
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
        # TEST_ONLY login/character fixture clone; no guild/member/pending rows.
        require(not db.execute('select id from accounts where id=6').fetchall() and not db.execute('select id from recovered_characters where id=6').fetchall(),'FRESH_APPLICANT6_REQUIRED')
        account=db.execute('select password_hash,created_at from accounts where id=5').fetchone();require(account,'CLONE_ACCOUNT5_REQUIRED')
        db.execute('insert into accounts(id,username,password_hash,created_at) values(6,?,?,?)',('god2-bytes:'+b'codexreject'.hex(),*account))
        profile,created,cp=db.execute('select profile,created_at,name_codepage from recovered_characters where id=5').fetchone()
        profile=bytearray(profile);require(len(profile)==40,'SOURCE_PROFILE40_REQUIRED');profile[:27]=bytes(27)
        name_value=b'rejectgirl\0';profile[:len(name_value)]=name_value;require(len(profile)==40,'CLONED_PROFILE40_REQUIRED')
        db.execute('insert into recovered_characters(id,account_id,slot,profile,name_bytes,created_at,name_codepage) values(6,6,0,?,?,?,?)',(bytes(profile),b'rejectgirl',created,cp))
        for table in ('character_role_snapshots','character_resources'):
            columns=[r[1] for r in db.execute('pragma table_info('+table+')')];require(columns[0]=='character_id','CLONE_OWNER_COLUMN_REQUIRED')
            row=db.execute('select * from '+table+' where character_id=5').fetchone();require(row,'CLONE_ROW5_REQUIRED_'+table)
            db.execute('insert into '+table+' values('+','.join('?' for _ in columns)+')',(6,*row[1:]))
        for identity,x in ((4,126),(5,127),(6,128)):
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
        'test_only_character4':{'role_level':30,'wallet_amount':100000},'test_only_character5':{'role_level':1},'test_only_character6':{'source':5,'username':'codexreject','name':'rejectgirl','account':6,'slot':0,'role_level':1},
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
        db.execute("insert into character_trade_wallets(character_id,amount,revision,design_id) values(6,0,1,'CUSTOM-0063') on conflict(character_id) do nothing")
        db.commit();require(db.execute('pragma quick_check').fetchone()==('ok',),'WALLET_FIXTURE_CLONE_INTEGRITY')
    after=snapshots(database);delta=changed_only(before,after,{'character_trade_wallets'})
    require(data(database,'select amount from character_trade_wallets where character_id=4')==[(100000,)],'WALLET_FIXTURE_AMOUNT_WRONG')
    require(data(database,'select amount from character_trade_wallets where character_id=5')==[(0,)],'JOINER_WALLET_FIXTURE_AMOUNT_WRONG')
    before_other=[r for r in before['tables']['character_trade_wallets'] if not (r.startswith('(4,') or r.startswith('(5,') or r.startswith('(6,'))]
    after_other=[r for r in after['tables']['character_trade_wallets'] if not (r.startswith('(4,') or r.startswith('(5,') or r.startswith('(6,'))]
    require(before_other==after_other,'WALLET_FIXTURE_CHANGED_OTHER_CHARACTERS')
    dump(args.output/'fixture-wallet-provision.json',{'authority':'CUSTOM_TEST_NOT_NATIVE','phase':'runtime49_server_listening_before_hidden_runner_login','SQL_delta':delta,'other_tables_exact':True,'other_wallet_rows_exact':True})
    dump(args.output/'fixture-sql-before-login.json',after)

def worker(args):
    before=desktop_names();clients=[];loaders=[];database=args.output/'town-diagnostic-accounts.db';log=args.output/'server.log'
    fixture=json.loads((args.output/'fixture.json').read_text('utf-8'))
    pending_fixture=None
    result={'accepted':False,'locale':args.source_page,'events':[],'entry_origin':'CUSTOM0078_ORDINARY_NATIVE_TOOLBAR4_HELP087B_NEW_RESOURCE2996_NOT_ORIGINAL_NPC','rendered_pixels_tested':False,
        'input_policy':'owned hidden desktop native WM input; VM_READ only; no memory writes/code or packet injection/screenshots/foreground'}
    def save():dump(args.output/'ui-result.json',result)
    def exact(c,address,size):return base.peer.exact(c['handle'],address,size)
    def number(c,address,size=4,signed=False):return int.from_bytes(exact(c,address,size),'little',signed=signed)
    def cstring(c,address,bound=256):
        require(address>0x10000,'NATIVE_TEXT_POINTER_MISSING');raw=exact(c,address,bound);require(b'\0' in raw,'NATIVE_TEXT_UNTERMINATED');return raw.split(b'\0',1)[0]
    def widget(c,offset=0x232e20):
        w=number(c,c['ui']+offset,2,True)
        if 0<=w<128 and exact(c,c['ui']+0xe2988+w*0x2a08,1)[0]&0x20:return w
        return None
    def control(c,w,index):
        point=base.owned.control_point(c['handle'],c['ui'],w,index)
        require(len(point)==2 and 0<=point[0]<800 and 0<=point[1]<600,'NATIVE_CONTROL_POINT_INVALID')
        result['last_control']={'identity':c['identity'],'widget':w,'control':index,'point':list(point)};save();click(c['hwnd'],*point);time.sleep(.15)
    def state(c):
        mode=number(c,c['ui']+0xd26c);w=widget(c)
        require(mode in (4,5) and w is not None and number(c,c['ui']+0x5bfa4,2)==9,'NATIVE_NAME_INPUT_NOT_READY')
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

    def all_world_sessions_closed(phase):
        require(not any(c['process'].is_running() for c in clients),'RESERVATION_ACTIVE_OWNED_CLIENT')
        def observed():
            lines=log.read_text('utf-8',errors='replace').splitlines();bound={}
            for index,line in enumerate(lines):
                if 'RECOVERED_ACCOUNT_BOUND ' not in line:continue
                account=re.search(r'account_id=(\d+)',line);sid=re.search(r'session_id=(\d+)',line)
                if account and sid and int(account[1]) in (4,5,6):bound.setdefault(sid[1],[]).append(index)
            require(bound,'RESERVATION_NO_BOUND_SESSION_EVIDENCE')
            exits={}
            for sid,indexes in bound.items():
                candidates=[i for i,line in enumerate(lines) if 'DISCONNECT_GAME_EXIT' in line and re.search(r'session_id='+sid+r'\b',line) and i>max(indexes)]
                if not candidates:return None
                require(not any('disconnect callback failed' in line and re.search(r'session_id='+sid+r'\b',line) for line in lines),'RESERVATION_SESSION_CLEANUP_CALLBACK_FAILED')
                exits[sid]={'bound_line_indices':indexes,'disconnect_exit_line_index':candidates[0],'disconnect_exit_log':lines[candidates[0]]}
            return {'phase':phase,'all_owned_clients_closed':True,'all_bound_sessions_disconnected':True,
                'owned_client_pids':[c['process'].pid for c in clients],'world_session_exit_evidence':exits,
                'authority':'actual native-close process exits plus server disconnect callback completion; no fabricated session state'}
        evidence=wait_until(observed,8,'RESERVATION_WORLD_SESSION_CLEANUP_NOT_COMPLETED')
        result.setdefault('quiescence_events',[]).append(evidence);save();return evidence
    def qualify_loaded(c):
        if result.get('native_loaded_resource_proof'):return
        expected=[case for case in json.loads(LOADER_RESULT.read_text('utf-8'))['cases'] if case['image']=='current' and case['page']==c['page'] and case['custom']]
        require(len(expected)==1,'EXACT_NATIVE_LOADER_BASELINE_REQUIRED');expected=expected[0]
        catalog=number(c,c['ui']+0xcff70);require(catalog>0x10000,'NATIVE_RESOURCE_CONTEXT_MISSING')
        count=number(c,catalog+0xb2c50,2,True);require(count==2996,'PRIVATE_NATIVE_TABLE_NOT2996')
        table=number(c,catalog+0xb2c54);require(table>0x10000,'NATIVE_MULTIMESSAGE_TABLE_MISSING')
        raw_entries=exact(c,table,2996*8);retained=[]
        for record in expected['retained_hashes']:
            offset=(record['key']-1)*8;rowcount=raw_entries[offset];pointer=int.from_bytes(raw_entries[offset+4:offset+8],'little')
            require(rowcount==len(record['rows_hex']) and pointer>0x10000,'NATIVE_GROUP_COUNT_OR_POINTER_MISMATCH')
            ptrs=exact(c,pointer,rowcount*4);rows_hex=[]
            for index,wanted_hex in enumerate(record['rows_hex']):
                wanted=bytes.fromhex(wanted_hex);textptr=int.from_bytes(ptrs[index*4:index*4+4],'little')
                require(textptr>0x10000,'NATIVE_GROUP_TEXT_POINTER_MISSING')
                require(exact(c,textptr,len(wanted)+1)==wanted+b'\0','NATIVE_ORIGINAL2995_OR_NEW2996_ROW_CHANGED_'+str(record['key']))
                rows_hex.append(wanted_hex)
            retained.append({'key':record['key'],'rows_hex':rows_hex})
        result['native_loaded_resource_proof']={'locale':c['page'],'catalog':hex(catalog),'table':hex(table),'count':count,
            'original2995_all_rows_byte_exact':True,'new2996_rows':retained[-1],
            'all_retained_rows_sha256':hashlib.sha256(json.dumps(retained,separators=(',',':')).encode()).hexdigest(),
            'comparison_source_sha256':base.sha(LOADER_RESULT),'VM_READ_only':True,'rendered_pixels_tested':False};save()
    def menu_state(c):
        w=widget(c,0x232dee)
        if w is None or number(c,c['ui']+0xccc1c,2)!=4 or number(c,c['ui']+0xccc1e,2)!=2996:return None
        require(number(c,0x5b7bf8,2)==0 and number(c,0x5b7bec)==0,'ACTIONABLE_MENU_REPLY0_REQUIRED')
        require(number(c,0x5b7bf0)==0 and number(c,0x5b7bf4)==1 and number(c,c['ui']+0xccd32,2,True)==0 and number(c,c['ui']+0xccd34,2,True)==1,'MENU_NATIVE_PAGE_OR_INTRO_CHANGED')
        require(number(c,c['ui']+0xaff00)==1 and number(c,c['ui']+0xaff04)==0,'MENU_NATIVE_PUBLICATION_FLAG_WRONG')
        require(number(c,c['ui']+0xccd36,1)==0xe7,'CUSTOM_ENTRY_CONTEXT_E7_REQUIRED')
        context=number(c,c['ui']+0xcff70);table=number(c,context+0xb2c54);entry=exact(c,table+2995*8,8)
        require(entry[0]==4,'MENU_EXACT_FOUR_LOADED_ROWS_REQUIRED')
        strings=int.from_bytes(entry[4:8],'little');ptrs=struct.unpack('<4I',exact(c,strings,16));actual=[cstring(c,p,512) for p in ptrs]
        wanted=['洞府服務：請選擇操作。','建立洞府','申請加入洞府','離開'] if c['page']==950 else ['洞府服务：请选择操作。','建立洞府','申请加入洞府','离开']
        require(actual==[v.encode('cp'+str(c['page'])) for v in wanted],'MENU_FOUR_ROWS_TEXT_MISMATCH')
        enabled=[number(c,c['ui']+0xcc9d4+0x148+i*4) for i in range(5)]
        if enabled!=[0,1,1,1,0]:return None
        return {'widget':w,'request':number(c,0x5b7bfa,2),'context':number(c,c['ui']+0xccd36,1),'mode':4,'key':2996,
            'reply':0,'row_text_hex':[v.hex() for v in actual],'row_enabled':enabled,'table':hex(c['ui']+0xcc9d4),
            'current_page':0,'threshold':0,'intro_count':1,'rendered_pixels_tested':False}
    def menu_open(c):
        require(widget(c,0x232dee) is None and widget(c) is None,'OTHER_DIALOG_OPEN_BEFORE_ORDINARY_HELP')
        before=snapshots(database);offset=len(log.read_text('utf-8',errors='replace'))
        toolbar=wait_until(lambda:widget(c,0x232db6),5,'ORDINARY_WORLD_TOOLBAR_MISSING')
        control(c,toolbar,4);observed=wait_until(lambda:menu_state(c),5,'ORDINARY_HELP_DID_NOT_OPEN2996')
        line=wait_until(lambda:next((line for line in log.read_text('utf-8',errors='replace')[offset:].splitlines()
            if 'OWNED_GUILD_ENTRY_MENU ' in line and 'character_id='+str(c['identity'])+' ' in line
            and 'request='+str(observed['request'])+' ' in line and 'published=true ' in line
            and 'key=2996 entry=native_help_CUSTOM ' in line),None),5,'ORDINARY_ENTRY_MENU_NOT_SERVER_PUBLISHED')
        require(snapshots(database)==before,'READONLY_MENU_OPEN_CHANGED_SQL')
        result.setdefault('ordinary_menu_events',[]).append({'identity':c['identity'],'operation':'normal_help087B_open','SQL_exact':True,'log':line,**observed});save();return observed
    def menu_choice(c,choice):
        require(choice in (0,1,2),'ONLY_NORMAL_MENU_OPTIONS_ALLOWED');observed=menu_state(c);require(observed,'NATIVE_MENU_NOT_READY')
        row=choice+observed['intro_count'];table=c['ui']+0xcc9d4
        mouse=number(c,table);handle=number(c,table+0x1c+row*2,2,True)
        require(mouse==number(c,c['ui']+0xcff68) and 0<=handle<0xc00,'MENU_ROW_HANDLE_UNQUALIFIED')
        node=mouse+handle*24
        def ready():
            raw=exact(c,node,24);values=struct.unpack('<6I',raw)
            return raw if values[0]==1 and number(c,table+0x148+row*4)==1 else None
        raw=wait_until(ready,3,'MENU_ROW_ALLOCATION_NOT_READY');left,top,right,bottom=struct.unpack('<iiii',raw[4:20])
        require(0<=left<right<=800 and 0<=top<bottom<=600,'MENU_ROW_RECT_INVALID')
        before=snapshots(database);offset=len(log.read_text('utf-8',errors='replace'))
        click(c['hwnd'],(left+right)//2,(top+bottom)//2)
        wait_until(lambda:widget(c,0x232dee) is None,5,'NATIVE_MENU_SELECTION_DID_NOT_CLOSE')
        input_value='true' if choice<2 else 'false'
        line=wait_until(lambda:next((line for line in log.read_text('utf-8',errors='replace')[offset:].splitlines()
            if 'OWNED_GUILD_ENTRY_CHOICE ' in line and 'character_id='+str(c['identity'])+' ' in line
            and 'choice='+str(choice)+' accepted=true input_opened='+input_value+' ' in line),None),5,'ORDINARY_ENTRY_CHOICE_NOT_SERVER_ACCEPTED')
        require(snapshots(database)==before,'SELECTOR_GRANTED_SQL_BEFORE_NAME_SUBMISSION')
        event={'identity':c['identity'],'operation':'normal_native_menu_row_click','choice':choice,'visible_row':row,
            'menu_state':observed,'node_before_hex':raw.hex(),'rectangle':[left,top,right,bottom],'VM_WRITE_or_packet_injection':False,'SQL_exact':True,'log':line}
        if choice<2:
            expected_mode=4 if choice==0 else 5
            prompt=wait_until(lambda:state(c) if widget(c) is not None and number(c,c['ui']+0xd26c)==expected_mode and number(c,c['ui']+0x5bfa4,2)==9 else None,5,'NORMAL_SELECTOR_DID_NOT_OPEN8D')
            event['prompt']=prompt;result['events'].append({'operation':'native_prompt','identity':c['identity'],**prompt})
        else:
            time.sleep(.3);require(widget(c) is None,'MENU_EXIT_OPENED_NAME_PROMPT')
            require('OWNED_GUILD_MEMBERSHIP_REQUEST ' not in log.read_text('utf-8',errors='replace')[offset:],'MENU_EXIT_SENT6F')
        result.setdefault('ordinary_menu_events',[]).append(event);save();return event
    def menu_cancel_and_reopen(c):
        observed=menu_state(c);require(observed,'MENU_CANCEL_REQUIRES_PUBLICATION')
        before=snapshots(database);offset=len(log.read_text('utf-8',errors='replace'));control(c,observed['widget'],1)
        wait_until(lambda:widget(c,0x232dee) is None,5,'MENU_CANCEL_NOT_CLOSED');time.sleep(.3)
        require(widget(c) is None and snapshots(database)==before,'MENU_CANCEL_CHANGED_STATE_OR_SQL')
        require('OWNED_GUILD_MEMBERSHIP_REQUEST ' not in log.read_text('utf-8',errors='replace')[offset:],'MENU_CANCEL_SUBMITTED6F')
        require('OWNED_GUILD_ENTRY_CHOICE ' not in log.read_text('utf-8',errors='replace')[offset:],'MENU_CANCEL_PRODUCED_SELECTION85')
        result.setdefault('ordinary_menu_events',[]).append({'identity':c['identity'],'operation':'native_control1_cancel','SQL_exact':True,'no8D':True,'no6F':True,'menu_state':observed});save()
        menu_open(c);menu_choice(c,2);menu_open(c)
    def launch(identity,expect_prompt=True):
        launch_log_offset=len(log.read_text('utf-8',errors='replace'))
        page=args.source_page;image=Path(fixture['clients'][str(page)]['path'])
        require(base.sha(image)==fixture['clients'][str(page)]['sha256'],'PRIVATE_CLIENT_PIN_CHANGED')
        loader=subprocess.Popen([str(base.LE),'-run',str(image),'127.0.0.1','127.0.0.1','6001','1'],cwd=image.parent,creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);loaders.append(loader)
        result.setdefault('owned_loader_pids',[]).append(loader.pid);save()
        def found():
            matches=[p for p in psutil.process_iter(['exe']) if p.info['exe'] and Path(p.info['exe']).resolve()==image.resolve()]
            require(len(matches)<=1,'DUPLICATE_PRIVATE_IMAGE');return matches[0] if matches else None
        process=wait_until(found,35,'PRIVATE_CLIENT_MISSING');require(Path(process.cwd()).resolve()==image.parent.resolve(),'PRIVATE_CLIENT_CWD_NOT_PHYSICAL_ROOT');c={'process':process,'identity':identity,'page':page};clients.append(c)
        result.setdefault('owned_client_pids',[]).append(process.pid);save()
        c['hwnd']=wait_until(lambda:base.peer.window_for(process.pid),35,'PRIVATE_WINDOW_MISSING')
        time.sleep(12);click(c['hwnd'],512,464);time.sleep(4)
        bound='RECOVERED_ACCOUNT_BOUND account_id='+str(identity);old=log.read_text('utf-8',errors='replace').count(bound)
        click(c['hwnd'],437,232);type_ascii(c['hwnd'],{4:'codexslow',5:'codexfixed',6:'codexreject'}[identity])
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
        # Client UI allocation precedes the server's owned world projection.
        # Wait for this fresh character session's completed projection batch;
        # do not retry an early help request or alter ordinary level1 eligibility.
        def world_ready():
            tail=log.read_text('utf-8',errors='replace')[launch_log_offset:]
            pattern=r'OWNED_WORLD_SNAPSHOT_RESTORED session_id=(\d+) character_id='+str(identity)+r' saved_player=true[^\r\n]*'
            matches=list(re.finditer(pattern,tail))
            if not matches:return None
            match=matches[-1];session=int(match.group(1));lines=tail[match.end():].splitlines()
            completed=next((line for line in lines if 'session_id='+str(session)+' RECOVERED_WORLD_BATCH_HANDLED ' in line),None)
            return {'identity':identity,'session':session,'snapshot':match.group(0),'completed_batch':completed} if completed else None
        ready=wait_until(world_ready,12,'OWNED_WORLD_PROJECTION_NOT_COMPLETED')
        result.setdefault('server_ready_before_native_help',[]).append(ready);save()
        if not expect_prompt:
            wait_until(lambda:cstring(c,number(c,c['ui']+0x86888)+6,16)==NAME.encode(),5,'LEADER_RELOGIN_NATIVE_GUILD_NAME_MISSING')
            return c
        require(widget(c) is None and number(c,c['ui']+0x5bfa4,2)!=9,'AUTO8D_ENTRY_FORBIDDEN')
        qualify_loaded(c)
        menu_open(c)
        return c
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
        require('operation='+str(0 if c['identity']==4 else 1)+' ' in line and 'context='+str(edited['context'])+' ' in line,'NATIVE_6F_CONTEXT_OPERATION_MISMATCH')
        wait_until(lambda:widget(c) is None,5,'NATIVE_NAME_INPUT_DID_NOT_CLOSE')
        event={'operation':'native_6F','identity':c['identity'],'method':method,'state':edited,'log':line,'accepted':True};result['events'].append(event);save();return event
    def cache(c,expected):
        def capture():
            count=number(c,c['ui']+0xb690);require(count<=50,'NATIVE_ROSTER_COUNT_INVALID')
            if count!=len(expected):return None
            raw=[exact(c,c['ui']+0xaf50+21*i,21) for i in range(count)]
            actual={r[5:].split(b'\0',1)[0].decode('cp'+str(c['page'])):(r[0],r[1],r[2],r[3]) for r in raw}
            if actual!=expected:return None
            require(len(actual)==count,'NATIVE_ROW_NAME_COLLISION');return {'count':count,'rows_hex':[r.hex() for r in raw],'by_name':actual}
        observed=wait_until(capture,8,'LEADER_NATIVE_CACHE_NOT_EXACT')
        result.setdefault('native_cache_events',[]).append(observed);save();return observed
    def help_open(c,members,pending):
        offset=len(log.read_text('utf-8',errors='replace'))
        toolbar=wait_until(lambda:widget(c,0x232db6),5,'LEADER_WORLD_TOOLBAR_MISSING');control(c,toolbar,4)
        line=wait_until(lambda:next((line for line in log.read_text('utf-8',errors='replace')[offset:].splitlines()
            if 'OWNED_GUILD_LEADER_PANEL_OPEN ' in line and 'character_id=4 ' in line and 'published=true ' in line),None),8,'LEADER_HELP_PANEL_NOT_PUBLISHED')
        require('members='+str(members)+' ' in line and 'pending='+str(pending)+' ' in line,'LEADER_HELP_AUDIENCE_MISMATCH')
        main=wait_until(lambda:widget(c,0x232e16),5,'LEADER_MAIN_PANEL_MISSING')
        header=exact(c,c['ui']+0xae6c,52);expected=bytearray(52);expected[13]=6;expected[19]=members;expected[23]=20
        require(header==expected,'LEADER_INACTIVE_CAPACITY_HEADER_WRONG')
        require(exact(c,c['ui']+0xaf31,1)==b'\x03','LEADER_NATIVE_SELF_ROLE_NOT3')
        for index in (18,19):
            entry=c['ui']+0xe2170+main*0x2a08+0x8b8+index*100
            require(number(c,entry+4)==0,'LEADER_NATIVE_ACTION_DISABLED')
        control(c,main,9);wait_until(lambda:number(c,c['ui']+0xaf48)==2 and widget(c,0x232e18),5,'LEADER_ROSTER_TAB_MISSING')
        result.setdefault('leader_help_events',[]).append({'native_entry':'toolbar4 new player help CUSTOM0078','header_hex':header.hex(),'log':line});save();return main
    def select_pending(c,name,slot):
        require(number(c,c['ui']+0xaf48)==2 and number(c,c['ui']+0xb69c)==0,'NATIVE_ROSTER_SELECTION_CONTEXT_WRONG')
        count=number(c,c['ui']+0xb690);require(0<count<=20,'BOUNDED_FIRST_PAGE_REQUIRED')
        sorted_list=number(c,c['ui']+0xb68c);require(sorted_list>0x10000,'NATIVE_SORTED_LIST_MISSING')
        matches=[]
        for row in range(count):
            ptr=number(c,sorted_list+row*4);require(c['ui']+0xaf50<=ptr<c['ui']+0xaf50+50*21,'NATIVE_SORTED_POINTER_OUTSIDE_CACHE')
            value=exact(c,ptr,21)
            if value[5:].split(b'\0',1)[0]==name.encode():matches.append((row,ptr,value))
        require(len(matches)==1,'PENDING_TARGET_NOT_UNIQUE');row,ptr,value=matches[0]
        require(value[0]==slot and value[1]==0,'TARGET_MUST_BE_EXPECTED_PENDING_SLOT')
        table=c['ui']+0xbbe4;input_context=number(c,table);handle=number(c,table+0x1c+row*2,2,True)
        require(input_context==number(c,c['ui']+0xcff68) and 0<=handle<0xc00,'NATIVE_ROW_INPUT_HANDLE_UNQUALIFIED')
        node=input_context+handle*0x18
        # 00418950 writes node+14 as cursor-in-RECT hit, not row availability.
        # 0050D8A0 consumes that hit only after native WM mouse delivery.
        def capture_row_input():
            raw_node=exact(c,node,24);values=struct.unpack('<6I',raw_node)
            return {'node_hex':raw_node.hex(),'active':values[0],'hit':values[5],
                'row_enabled':number(c,table+0x148+row*4),'rectangle':list(struct.unpack('<iiii',raw_node[4:20])),
                'table':hex(table),'input_context':hex(input_context),'handle':handle,'node':hex(node),
                'selected_row':number(c,c['ui']+0xbe08,2,True),'tab':number(c,c['ui']+0xaf48),
                'page':number(c,c['ui']+0xb69c),'main_widget':widget(c,0x232e16),
                'roster_widget':widget(c,0x232e18),'table_prefix_hex':exact(c,table,28).hex(),
                'mouse_context_hex':exact(c,input_context+0x12000,0x30).hex()}
        diagnostic={'name':name,'slot':slot,'visible_row':row,'pointer':hex(ptr),'before':capture_row_input(),
            'semantics':'node+14 is native cursor hit; table+148+4*row is row availability'}
        result.setdefault('native_row_input_diagnostics',[]).append(diagnostic);save()
        def settled():
            state=capture_row_input();diagnostic['latest_before_click']=state;save()
            return state if state['active']==1 and state['row_enabled']==1 and state['roster_widget'] is not None else None
        ready=wait_until(settled,3,'NATIVE_ROW_ALLOCATION_OR_AVAILABILITY_NOT_READY')
        require(ready['tab']==2 and ready['page']==0,'NATIVE_ROSTER_SELECTION_CONTEXT_CHANGED')
        rectangle=tuple(ready['rectangle']);left,top,right,bottom=rectangle
        require(0<=left<right<=800 and 0<=top<bottom<=600,'NATIVE_ROW_RECT_INVALID')
        click(c['hwnd'],(left+right)//2,(top+bottom)//2)
        wait_until(lambda:number(c,c['ui']+0xbe08,2,True)==row,4,'NATIVE_ROW_SELECTION_NOT_APPLIED')
        diagnostic['after']=capture_row_input();save()
        require(diagnostic['after']['hit']==1,'NATIVE_ROW_CLICK_NOT_HIT')
        require(number(c,sorted_list+number(c,c['ui']+0xbe08,2,True)*4)==ptr,'NATIVE_SELECTED_TARGET_CHANGED')
        event={'name':name,'slot':slot,'role':0,'visible_row':row,'pointer':hex(ptr),'input_handle':handle,'rectangle':rectangle,'normal_window_local_click':True,
            'native_input_before':ready,'native_input_after':diagnostic['after']}
        result.setdefault('native_selections',[]).append(event);save();return ptr
    def action_line(c,offset,action,slot):
        return wait_until(lambda:next((line for line in log.read_text('utf-8',errors='replace')[offset:].splitlines()
            if 'OWNED_GUILD_LEADER_ACTION ' in line and 'character_id=4 ' in line and 'action='+str(action)+' ' in line
            and 'slot='+str(slot)+' ' in line and 'committed=true ' in line),None),8,'NATIVE_LEADER_ACTION_NOT_COMMITTED')
    def member_leave(c,guild,profiles):
        require(c['identity']==5,'ORDINARY_MEMBER5_REQUIRED')
        require(exact(c,c['ui']+0xaf30,2)==bytes((0,1)),'ORDINARY_MEMBER_NATIVE_SELF_ROLE_OR_SLOT_WRONG')
        expected={'fixedgirl':(0,1,profiles[5][1],profiles[5][0]),'slowgirl':(1,3,profiles[4][1],profiles[4][0]),'rejectgirl':(2,0,profiles[6][1],profiles[6][0])}
        cache(c,expected)
        offset=len(log.read_text('utf-8',errors='replace'))
        toolbar=wait_until(lambda:widget(c,0x232db6),5,'MEMBER_HELP_TOOLBAR_MISSING');control(c,toolbar,4)
        opened=wait_until(lambda:next((line for line in log.read_text('utf-8',errors='replace')[offset:].splitlines()
            if 'OWNED_GUILD_LEADER_PANEL_OPEN ' in line and 'character_id=5 ' in line and 'members=2 ' in line
            and 'pending=1 ' in line and 'published=true ' in line),None),8,'MEMBER_HELP_PANEL_NOT_PUBLISHED')
        main=wait_until(lambda:widget(c,0x232e16),5,'MEMBER_MAIN_PANEL_MISSING')
        header=exact(c,c['ui']+0xae6c,52);wanted=bytearray(52);wanted[13]=6;wanted[19]=2;wanted[23]=20
        require(header==wanted,'MEMBER_NATIVE_HEADER_WRONG')
        def modal():
            control(c,main,16)
            w=wait_until(lambda:widget(c,0x232de6),5,'MEMBER_LEAVE_MODAL_MISSING')
            require(number(c,c['ui']+0x23d5d8)==4 and number(c,c['ui']+0xaf4c)==c['ui']+0xaf30,'MEMBER_LEAVE_MODAL_SELF_CONTEXT_WRONG')
            require(exact(c,c['ui']+0xaf30,2)==bytes((0,1)),'MEMBER_LEAVE_NATIVE_TARGET_CHANGED');return w
        before=snapshots(database);before_members=rows(database,'owned_guild_members');before_groups=rows(database,'owned_guilds')
        before_pending=rows(database,'owned_guild_applications_0078');before_governance=rows(database,'owned_guild_governance_0078')
        require(len(before_pending)==1 and before_pending[0][4]==6,'MEMBER_LEAVE_REQUIRES_REAL_PENDING6')
        revision=data(database,'select max(value) from (select revision value from owned_guilds union all select revision from owned_guild_members)')[0][0]+1
        event={'identity':5,'locale':c['page'],'entry':'normal toolbar4 CUSTOM help -> native main16 -> modal4 controls1/0',
            'open_log':opened,'native_header_hex':header.hex(),'native_self_hex':exact(c,c['ui']+0xaf30,2).hex(),
            'producer':'004EF6E0 C2S73 logical2, local slot0; no DB identity injection',
            'pending_preservation_required':6,'revision_expected':revision,'accepted':False}
        result.setdefault('ordinary_member_leave_events',[]).append(event);save()
        w=modal();cancel_offset=len(log.read_text('utf-8',errors='replace'));control(c,w,1)
        wait_until(lambda:widget(c,0x232de6) is None,5,'MEMBER_LEAVE_CANCEL_NOT_CLOSED')
        wait_until(lambda:exact(c,c['ui']+0xe2988+w*0x2a08,1)[0]&0x10,5,'MEMBER_LEAVE_CANCEL_NOT_SETTLED')
        time.sleep(.3);require(snapshots(database)==before,'MEMBER_LEAVE_CANCEL_CHANGED_SQL')
        require('OWNED_GUILD_SELF_LEAVE ' not in log.read_text('utf-8',errors='replace')[cancel_offset:],'MEMBER_LEAVE_CANCEL_SENT_MUTATION')
        require(widget(c,0x232e16)==main and cstring(c,number(c,c['ui']+0x86888)+6,16)==NAME.encode(),'MEMBER_LEAVE_CANCEL_CHANGED_NATIVE_STATE')
        event.update(cancel_no_action_log=True,cancel_SQL_exact=True,cancel_native_membership_preserved=True);save()
        w=modal();commit_offset=len(log.read_text('utf-8',errors='replace'));control(c,w,0)
        pattern=re.compile(r'OWNED_GUILD_SELF_LEAVE session_id=(\d+) character_id=5 slot=0 committed=true player_created=true\b')
        def committed():
            hits=[line for line in log.read_text('utf-8',errors='replace')[commit_offset:].splitlines() if pattern.search(line)]
            require(len(hits)<=1,'MEMBER_LEAVE_DUPLICATE_COMMIT_LOG');return hits[0] if hits else None
        line=wait_until(committed,5,'MEMBER_NATIVE73_NOT_COMMITTED')
        wait_until(lambda:not data(database,'select character_id from owned_guild_members where character_id=5'),5,'MEMBER_NATIVE73_NOT_DURABLE')
        require(rows(database,'owned_guild_members')==[r for r in before_members if r[0]!=5],'MEMBER_LEAVE_REMOVED_OTHER_MEMBERS')
        require(rows(database,'owned_guilds')==[(g[0],g[1],revision,*g[3:]) if g[0]==guild[0] else g for g in before_groups],'MEMBER_LEAVE_CHANGED_OTHER_GUILD_OR_REVISION')
        require(rows(database,'owned_guild_applications_0078')==before_pending and rows(database,'owned_guild_governance_0078')==before_governance,'MEMBER_LEAVE_CHANGED_PENDING_OR_GOVERNANCE')
        delta=changed_only(before,snapshots(database),{'owned_guilds','owned_guild_members'})
        wait_until(lambda:cstring(c,number(c,c['ui']+0x86888)+6,16)==b'',5,'MEMBER_NATIVE2D_NAME_NOT_CLEARED')
        empty_cache=cache(c,{})
        wait_until(lambda:all(widget(c,o) is None for o in (0x232e16,0x232e18,0x232de6)),5,'MEMBER_NATIVE92_SELF_DID_NOT_CLOSE_PANELS')
        tail=log.read_text('utf-8',errors='replace')[commit_offset:].splitlines();match=pattern.search(line);sid=match.group(1)
        batch=wait_until(lambda:next((line for line in log.read_text('utf-8',errors='replace')[commit_offset:].splitlines()
            if 'RECOVERED_WORLD_BATCH_HANDLED ' in line and 'session_id='+sid+' ' in line),None),5,'MEMBER_LEAVE_BATCH_NOT_HANDLED')
        require(c['process'].is_running(),'MEMBER_LEAVE_DISCONNECTED_CLIENT')
        event.update(accepted=True,commit_log=line,batch_log=batch,SQL_delta=delta,global_revision_advanced=True,
            owner_only_membership_deleted=True,pending6_exact=True,governance_exact=True,all_unrelated_tables_exact=True,
            native_2D_name_empty=True,native_92_self_cache_empty=empty_cache,all_panels_closed=True,client_still_running=True)
        save()
    def leader_exercise(c,guild):
        nonlocal pending_fixture
        profiles={identity:(bytes(profile)[29],bytes(role)[1]) for identity,profile,role in data(database,'select c.id,c.profile,r.logical from recovered_characters c join character_role_snapshots r on r.character_id=c.id where c.id in(4,5,6)')}
        expected={'slowgirl':(0,3,profiles[4][1],profiles[4][0]),'fixedgirl':(1,0,profiles[5][1],profiles[5][0]),'rejectgirl':(2,0,profiles[6][1],profiles[6][0])}
        cache(c,expected);main=help_open(c,1,2);select_pending(c,'fixedgirl',1)
        before_approve=snapshots(database);before_members=rows(database,'owned_guild_members');before_apps=rows(database,'owned_guild_applications_0078');before_guilds=rows(database,'owned_guilds')
        revision=data(database,'select max(value) from (select revision value from owned_guilds union all select revision from owned_guild_members)')[0][0]+1
        offset=len(log.read_text('utf-8',errors='replace'));control(c,main,18);line=action_line(c,offset,113,1)
        wait_until(lambda:bool(data(database,'select character_id from owned_guild_members where character_id=5')),5,'APPROVED_MEMBER_NOT_DURABLE')
        delta=changed_only(before_approve,snapshots(database),{'owned_guilds','owned_guild_members','owned_guild_applications_0078'})
        require(sorted(rows(database,'owned_guild_members'))==sorted(before_members+[(5,guild[0],revision,'CUSTOM_DESIGNED','CUSTOM-0075',base.MAPPED_SHA)]),'APPROVE_CHANGED_OTHER_MEMBERS_OR_REVISION')
        require(rows(database,'owned_guild_applications_0078')==[r for r in before_apps if r[4]!=5],'APPROVE_CHANGED_OTHER_PENDING')
        require(rows(database,'owned_guilds')==[(g[0],g[1],revision,*g[3:]) if g[0]==guild[0] else g for g in before_guilds],'APPROVE_CHANGED_OTHER_GUILDS')
        expected['fixedgirl']=(1,1,profiles[5][1],profiles[5][0]);cache(c,expected)
        result['real_native_71_approve']={'accepted':True,'log':line,'joined_character':5,'revision':revision,'SQL_delta':delta};save()
        # Ordinary member leaves through native73 while real applicant6 is pending.
        # One image per locale: sequential normal reconnect, no duplicate image or packet injection.
        close(c)
        quiet=all_world_sessions_closed('founder4_closed_after_real71_before_reservation_setup')
        pending_fixture=seed_founder_reservation(database,args.output,quiet)
        result['founder_unsettled_reservation_fixture']=pending_fixture;save()
        member=launch(5,False);member_leave(member,guild,profiles)
        record=tuple(pending_fixture['reservation'])
        require(reservation_record(database,record[0])==[record],'MEMBER_LEAVE_CHANGED_FOUNDER_RESERVATION')
        require(data(database,'select * from character_resources where character_id=4')==pending_fixture['founder_resource_exact'],'MEMBER_LEAVE_CHANGED_FOUNDER_RESOURCES')
        require(not data(database,'select battle_id from battle_settlements where battle_id=?',(record[0],)) and not data(database,'select battle_id from battle_checkpoints where battle_id=?',(record[0],)),'MEMBER_LEAVE_SETTLED_SYNTHETIC_RESERVATION')
        event=result['ordinary_member_leave_events'][-1]
        event.update(founder_unsettled_reservation_exact=True,founder_resources_exact=True,
            founder_no_active_client=True,founder_reservation_id=record[0],synthetic_fixture_not_actual_battle_visual=True)
        save();close(member)
        quiet=all_world_sessions_closed('member5_closed_after_real73_before_fixture_cleanup')
        result['founder_reservation_fixture_cleanup']=clear_founder_reservation(database,args.output,pending_fixture,quiet)
        pending_fixture=None;save()
        c=launch(4,False);expected.pop('fixedgirl');expected['rejectgirl']=(1,0,profiles[6][1],profiles[6][0]);cache(c,expected)
        # Explicit help publishes new recipient-local slots/authority after membership revision changes.
        main=help_open(c,1,1);ptr=select_pending(c,'rejectgirl',1)
        original=snapshots(database);offset=len(log.read_text('utf-8',errors='replace'))
        def reject_modal():
            control(c,main,19);modal=wait_until(lambda:widget(c,0x232de6),5,'NATIVE_REJECT_MODAL_MISSING')
            require(number(c,c['ui']+0x23d5d8)==3 and number(c,c['ui']+0xaf4c)==ptr,'NATIVE_PENDING_REJECT_MODAL_CONTEXT_WRONG')
            require(exact(c,ptr,2)==bytes((1,0)),'NATIVE_REJECT_MODAL_TARGET_CHANGED');return modal
        modal=reject_modal();control(c,modal,1);wait_until(lambda:widget(c,0x232de6) is None,5,'NATIVE_REJECT_CANCEL_NOT_CLOSED')
        time.sleep(.5);require(snapshots(database)==original,'REJECT_CANCEL_CHANGED_SQL')
        require('OWNED_GUILD_LEADER_ACTION ' not in log.read_text('utf-8',errors='replace')[offset:],'REJECT_CANCEL_SENT_MUTATION')
        result['native_72_cancel']={'accepted':True,'sql_exact':True,'no_action_log':True,'mode':3};save()
        modal=reject_modal();before_apps=rows(database,'owned_guild_applications_0078');offset=len(log.read_text('utf-8',errors='replace'));control(c,modal,0)
        line=action_line(c,offset,114,1);wait_until(lambda:not data(database,'select id from owned_guild_applications_0078 where character_id=6'),5,'REJECTED_APPLICATION_NOT_DELETED')
        delta=changed_only(original,snapshots(database),{'owned_guild_applications_0078'})
        require(rows(database,'owned_guild_applications_0078')==[r for r in before_apps if r[4]!=6] and not data(database,'select character_id from owned_guild_members where character_id=6'),'REJECT_TARGET_OR_AUTHORITY_WRONG')
        expected.pop('rejectgirl');cache(c,expected)
        result['real_native_72_reject']={'accepted':True,'log':line,'rejected_character':6,'SQL_delta':delta};save()
    try:
        qualify();require(before['current'].startswith('God2Lab-') and before['current']!=before['input'],'HIDDEN_DESKTOP_REQUIRED')
        wait_until(lambda:data(database,'select max(version) from schema_migrations')[0][0]==49,8,'CANDIDATE_SCHEMA49_NOT_STARTED')
        for table in TABLES:require(not rows(database,table),'REAL_GAMEPLAY_MUST_BEGIN_WITHOUT_GUILD_SEEDS')
        creator=launch(4);menu_cancel_and_reopen(creator);menu_choice(creator,0);before_create=snapshots(database);wallet_before=data(database,'select amount,revision from character_trade_wallets where character_id=4')[0]
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
        close(creator);joiner=launch(5);menu_cancel_and_reopen(joiner);menu_choice(joiner,1);before_apply=snapshots(database)
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
        close(joiner)
        rejecter=launch(6);menu_cancel_and_reopen(rejecter);menu_choice(rejecter,1);before_reject_apply=snapshots(database)
        reject_apply_event=submit(rejecter,'control0' if args.source_page==950 else 'Return')
        wait_until(lambda:bool(data(database,'select id from owned_guild_applications_0078 where character_id=6')),5,'REJECT_APPLICANT_NOT_DURABLE')
        second_delta=changed_only(before_reject_apply,snapshots(database),{'owned_guild_applications_0078','sqlite_sequence'})
        require(data(database,'select character_id from owned_guild_members order by character_id')==[(4,)],'SECOND_APPLICANT_BECAME_MEMBER')
        require(len(rows(database,'owned_guild_applications_0078'))==2,'TWO_REAL_APPLICATIONS_REQUIRED')
        result['second_real_pending_application']={'accepted':True,'identity':6,'native':reject_apply_event,'SQL_delta':second_delta};save()
        close(rejecter);leader=launch(4,False)
        leader_exercise(leader,guild)
        require(result.get('founder_reservation_fixture_cleanup',{}).get('completed'),'FOUNDER_RESERVATION_FIXTURE_CLEANUP_REQUIRED')
        require(len(result.get('ordinary_member_leave_events',[]))==1 and result['ordinary_member_leave_events'][0]['accepted'],'ORDINARY_MEMBER_NATIVE73_REQUIRED')
        result['ordinary_paired_entry_accepted']=True;result['ordinary_paired_entry_status']='CUSTOM_RESOURCE2996_NORMAL_TOOLBAR_HELP_CLICK_TO_SQL_ACCEPTED_NO_ORIGINAL_NPC_CLAIM'
        result['SQL_after']=snapshots(database);result['accepted']=True;save()
    except BaseException as error:result.update(error=str(error),traceback=traceback.format_exc())
    finally:
        for c in reversed(clients):
            try:close(c)
            except Exception as error:result.setdefault('cleanup_errors',[]).append(str(error))
        if pending_fixture is not None and not pending_fixture.get('cleanup_completed'):
            try:
                quiet=all_world_sessions_closed('failure_owned_clients_closed_before_fixture_cleanup')
                result['founder_reservation_fixture_cleanup_on_failure']=clear_founder_reservation(database,args.output,pending_fixture,quiet)
            except Exception as error:result.setdefault('cleanup_errors',[]).append('synthetic reservation cleanup: '+str(error))
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
    files={'working_multimessage03':base.LIVE.parent/'Data2/Patch/Comm/MultiMessage03.csvZ','working_multimessage03gb':base.LIVE.parent/'Data2/Patch/Comm/MultiMessage03-gb.csvZ','ddraw':base.LIVE.parent/'ddraw.dll','ddraw_config':base.LIVE.parent/'ddraw.ini','client':base.LIVE,'client_locale':Path(str(base.LIVE)+'.le.config'),'source_DB':base.SOURCE,'source_config':base.SOURCE.with_name('server-config.json'),
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
            server=subprocess.Popen([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--run-for','960'],cwd=ROOT,env=env_lab(),stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);result['server_pid']=server.pid
            def listening():
                require(server.poll() is None,'PRIVATE_SERVER_EXITED')
                with socket.socket() as probe:return probe.connect_ex(('127.0.0.1',base.PORT))==0
            wait_until(listening,15,'PRIVATE_SERVER_NOT_LISTENING')
            database=args.output/'town-diagnostic-accounts.db'
            wait_until(lambda:data(database,'select max(version) from schema_migrations')[0][0]==49,8,'CANDIDATE_SCHEMA49_NOT_STARTED')
            provision_wallet_fixture(args)
            runner=subprocess.Popen([str(base.RUNNER),sys.executable,'-X','utf8','-B',str(Path(__file__).resolve()),'--worker','--output',str(args.output),'--source-page',str(args.source_page)],cwd=ROOT,env=env_lab(),stdout=runnerlog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);result['runner_pid']=runner.pid
            result['runner_exit']=runner.wait(timeout=940);result['ui']=json.loads((args.output/'ui-result.json').read_text('utf-8'));result['accepted']=result['runner_exit']==0 and result['ui']['accepted']
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
    frozen_paths=[Path(__file__),args.contract,PROOF,Path(base.__spec__.origin),Path(pose.__file__),ROOT/'tools/strike_lab/private_guild_panel_v04_20261003.py',ROOT/'tools/strike_lab/private_inventory_move_ui.py',ROOT/'tools/strike_lab/private_potion_ui.py',ROOT/'tools/strike_lab/private_guild_membership_0078_v03_20261003.py',FIELD_PROOF,RESOURCE_PLAN,COPY_PLAN,LOADER_RESULT,FROZEN_HELPER,Path(draw_spec.origin)]
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
