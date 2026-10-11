"""Gated CUSTOM-0066 owned armor instance transport release.

Never grants an item, restores an older database, or downgrades schema42.
Qualification is read-only. Stage starts the candidate only on a saved clone.
Apply is a separate explicit command with a no-player stop and fresh backup.
Bank run03 is the accepted follow-on receipt; rejected run02 is retained.
"""
import argparse
from contextlib import closing
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import socket
import struct
import subprocess
from tools.operations import native_peer_pose_release_20261002 as common
from tools.operations import packet_links_release_20260930 as snapshots
from tools.operations import verify_frozen_chat_20260927 as frozen
from tools.strike_lab import import_native_armor_20261002 as definitions

ROOT=common.ROOT
managed=common.managed
sha=managed.sha
read=common.read
write=common.write
require=common.require
CANDIDATE=ROOT/'artifacts/research/native-armor-transfer-20261002/candidate-01/god2-server.exe'
PIN='2696f4efc90648aac47df97e5dbbe80cfd1434cac936f2db36c5ec98ff6ad3d3'
CONTRACT=CANDIDATE.parent/'contract.json'
VERIFICATION=CANDIDATE.parent/'verification.json'
RELATED_LOG=CANDIDATE.parent/'ctest-related.log'
PRODUCTION_LOG=CANDIDATE.parent/'ctest-production-adapter.log'
RUN01=ROOT/'artifacts/playtests/private-native-blackbox-armor-transfer-20261002-01/run-result.json'
# Original run02 was rejected; run03 actually completed and cleaned up.
RUN02=ROOT/'artifacts/playtests/private-native-blackbox-bank-armor-projection-20261002-03/run-result.json'
RUN02_ADAPTER_READY=True
BANK_HARNESS=ROOT/'tools/strike_lab/private_bank_armor_projection_20261002_v03.py'
ROUND=ROOT/'artifacts/releases/native-armor-transfer-20261002'
DEPLOY=ROUND/'deployment'
FORMAT='native-armor-transfer-release-20261002-v1'
TABLE='character_armor_slot_metadata'
TRIGGERS={'armor_insert_guard','armor_update_guard','weapon_armor_insert_guard',
          'weapon_armor_update_guard','gem_armor_insert_guard','gem_armor_update_guard'}
ADDITIONS={TABLE,'sqlite_autoindex_'+TABLE+'_1'}|TRIGGERS
EXTRA_SOURCES={
    'src/db/NativeArmorCatalog.h','src/db/NativeArmorCatalog.cpp',
    'src/protocol/RecoveredArmorSourceSlots.h','src/protocol/RecoveredArmorInstance.h',
    'tests/CMakeLists.txt','tests/test_config.cpp','tests/test_armor_slots.cpp',
    'tests/test_owned_armor_transfer.cpp','tests/test_owned_bag_projection.cpp',
    'tests/test_recovered_armor_source_instance.cpp','tests/test_native_armor_catalog.cpp',
    'tests/test_recovered_armor_instance.cpp','tests/research/test_import_native_armor_20261002.py',
    'tools/strike_lab/private_armor_transfer_20261002.py',
    'tools/strike_lab/current_armor_20261002.py','tools/strike_lab/current_armor_projection_20261002.py',
    'tools/strike_lab/current_armor_appearance_20261002.py',
    'tools/strike_lab/current_armor_source_instance_20261002.py',
    'tools/strike_lab/import_native_armor_20261002.py',
    'artifacts/research/native-armor-20261002/records.json',
    'artifacts/research/native-armor-20261002/oracle.json',
    'tools/operations/native_armor_transfer_release_20261002.py',
    'tests/research/test_native_armor_transfer_release_20261002.py'}
EXTRA_SOURCES.update({
    'src/db/DbTypes.h','src/db/SqliteRecoveredCharacterRepository.h',
    'src/db/SqliteSupport.h','src/db/SqliteTeleportGemRepository.h',
    'src/db/SqliteWeaponSlotRepository.h','src/db/SqliteWeaponSlotRepository.cpp',
    'src/protocol/RecoveredInventory.h','src/protocol/RecoveredInventoryProjection.h',
    'src/protocol/RecoveredWorldRecords.h','src/scripting/LuaEngine.h','src/scripting/LuaEngine.cpp',
    'tests/test_bank_items_repository.cpp','tests/test_bank_repository.cpp','tests/test_bank_service.cpp',
    'tests/test_recovered_trade.cpp','tests/test_trade_repository.cpp','tests/test_trade_service.cpp',
    'tests/test_owned_weapon_transfer.cpp','tests/test_weapon_slots.cpp',
    'tests/test_owned_bank_trade_projection.cpp','tests/test_database.cpp',
    'tests/test_sqlite_armor_production_adapter.cpp',
    'tools/strike_lab/private_bank_armor_projection_20261002.py',
    'tools/strike_lab/private_bank_armor_projection_20261002_v03.py',
    'artifacts/research/native-armor-20261002/delivery.json',
    'artifacts/research/current-armor-projection-20261002/native.json',
    'artifacts/research/current-armor-appearance-20261002/native.json',
    'artifacts/research/current-armor-appearance-20261002/contract.md',
    'artifacts/research/current-armor-source-instance-20261002/native.json',
    'docs/custom-designs.json','docs/research/native-armor-transfer-20261002.md',
    'docs/research/native-armor-definitions-20261002.md',
    'docs/research/native-armor-storage-20261002.md',
    'docs/research/packet-gap-ledger-20260930.md'})
REQUIRED_RELATED={'bank_items_repository','bank_repository','bank_service','recovered_trade',
                  'trade_repository','trade_service','owned_weapon_transfer','weapon_slots',
                  'armor_slots','owned_armor_transfer','owned_bag_projection',
                  'recovered_armor_source_instance','owned_bank_trade_projection',
                  'database','config','application_startup'}
EXTRA_TEST_SOURCES={'tests/test_config.cpp','tests/test_sqlite_armor_production_adapter.cpp',
                    'tests/CMakeLists.txt'}

def checked_path(relative):
    path=Path(relative)
    require(not path.is_absolute() and '..' not in path.parts,'Archive source must remain within repository')
    resolved=(ROOT/path).resolve();require(resolved.is_relative_to(ROOT.resolve()),'Source escapes repository')
    return resolved

def config_after(before):
    result=copy.deepcopy(before)
    require(isinstance(result.get('world'),dict),'Existing native world configuration required')
    value=result['world'].get('owned_armor_transfers')
    require(value is None or (isinstance(value,dict) and set(value)=={'enabled'} and
                             value['enabled'] is False),'Armor transport is already active or has extra keys')
    result['world']['owned_armor_transfers']={'enabled':True}
    return result

def config_gate(before,after):
    require(after==config_after(before),'Only world.owned_armor_transfers.enabled=true may change')

def new_schema_sql():
    text=(ROOT/'src/db/SqliteArmorSlotRepository.cpp').read_text('utf-8')
    match=re.search(r'std::string SqliteArmorSlotRepository::schema\(\)\{return R"SQL\((.*?)\)SQL";',text,re.S)
    require(match is not None,'Pinned schema42 SQL extractor changed');return match.group(1)

def schema_gate(before,after,template=None):
    require([r[0] for r in before['history']]==list(range(1,42)),'Exact schema1..41 history required')
    require(TABLE not in before['tables'],'Armor metadata table exists before release')
    require(after['pragmas']==before['pragmas'],'Database pragmas changed')
    require(set(after['tables'])==set(before['tables'])|{TABLE},'Unexpected table addition/removal')
    require([r for r in after['schema'] if r[1] not in ADDITIONS]==before['schema'],'Old schema objects changed')
    added=[r for r in after['schema'] if r[1] in ADDITIONS]
    require({r[1] for r in added}==ADDITIONS,'Require exact empty table, autoindex and six guards')
    require(all((r[0]=='trigger' and r[1] in TRIGGERS) or
                (r[0]=='table' and r[1]==TABLE) or
                (r[0]=='index' and r[1]=='sqlite_autoindex_'+TABLE+'_1') for r in added),'Unexpected new object kind')
    for name,value in before['tables'].items():
        if name!='schema_migrations':require(after['tables'][name]==value,'Old rows changed: '+name)
    require(after['tables'][TABLE]=={'rows':0,'sha256':hashlib.sha256(b'').hexdigest()},'Armor grant or seeded row detected')
    require(after['history'][:-1]==before['history'] and len(after['history'])==42 and
            after['history'][-1][:3]==[42,'owned_armor_instances',new_schema_sql()], 'History differs outside migration42')
    if template is not None:
        require(after['schema']==template['schema'] and after['history'][-1][:3]==template['history'][-1][:3], 'Clone and actual schema42 differ')

def source_catalog_gate(database):
    expected=definitions.pinned_records()
    with closing(sqlite3_connect_readonly(database)) as db:
        db.execute('BEGIN')
        actual=tuple(tuple(db.execute('SELECT * FROM '+table+' ORDER BY '+order))
                     for table,order in zip(definitions.TABLES,definitions.ORDERS))
        require(actual==expected,'Native1354 source directory differs')
        require(db.execute('PRAGMA quick_check').fetchall()==[('ok',)] and
                not db.execute('PRAGMA foreign_key_check').fetchall(),'Source database integrity failed')

def sqlite3_connect_readonly(database):
    import sqlite3
    db=sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True)
    db.execute('PRAGMA query_only=ON');return db

def process_guards(data):
    require(data.get('accepted') is True and data.get('runner_exit')==0 and data.get('candidate_sha256')==PIN,
            'Native receipt failed or differs from immutable candidate')
    for key in ('private_files_unchanged','all_private_images_closed','source_files_unchanged',
                'candidate_unchanged','all_owned_processes_closed','protected_processes_preserved',
                'desktop_owner_unchanged','exclusive2598_released'):
        require(data.get(key) is True,'Missing native cleanup guard: '+key)
    require(data.get('before')==data.get('after'),'Protected native files changed')
    require(data['before'].get('live_client')==sha(managed.CLIENT),'Native client pin differs')
    terminal=data.get('owned_pid_terminal')
    require(isinstance(terminal,dict) and terminal and all(v.get('pid_exists') is False for v in terminal.values()),'Owned native process remains')

def native_saved_matches(native,saved):
    if set(native)!=set(saved):return False
    for slot,row in saved.items():
        raw=bytes.fromhex(native[slot])
        if len(raw)!=24:return False
        if row['count']:
            metadata=bytes.fromhex(row['metadata'])
            if len(metadata)!=20 or raw!=struct.pack('<I',row['count'])+metadata:return False
        elif raw[:6]!=bytes(6):
            # Native41 clears count/key, not the opaque tail of a former item.
            return False
    return True

def run01_gate(data):
    process_guards(data);u=data['ui']
    require(data.get('armor_frozen_files_unchanged') is True and data.get('armor_files_before')==data.get('armor_files_after'), 'Armor wrapper files changed')
    require(data.get('armor_files_before'),'Armor20 evidence pins absent')
    for path,digest in data['armor_files_before'].items():require(sha(Path(path))==digest,'Native evidence file changed: '+path)
    for key in ('accepted','read_handles_closed','desktop_unchanged','all_owned_clients_closed','relogin_unrelated_tables_unchanged'):
        require(u.get(key) is True,'Run01 UI guard absent: '+key)
    require(u.get('scope')=='ARMOR_FULL20_TRANSFER_ONLY_NOT_DROP_STATS_OR_APPEARANCE_FORMULA','Run01 authority scope differs')
    events=u['events'];require(len(events)==28 and u.get('actual_mutations')==24 and u.get('actual_refusals')==4,'Native28/24 counts differ')
    for identity,page in ((4,950),(5,936)):
        own=[e for e in events if (e.get('identity'),e.get('page'))==(identity,page)]
        require(len(own)==14 and sum(e.get('refusal') is True for e in own)==2,'Each TW/CN owner needs12mutations+2refusals')
        require(sum(e.get('kind')=='28' and not e.get('refusal',False) for e in own)==10 and
                sum(e.get('kind')=='24' and not e.get('refusal',False) for e in own)==2,'Each native opcode direction coverage differs')
        for e in own:
            require('refusal' not in e or type(e['refusal']) is bool,'Refusal flag must be a native boolean')
            require(e.get('other_owner_unchanged') is True and e.get('unrelated_tables_unchanged') is True and e.get('full20_conserved') is True,'Owner or instance conservation failed')
            require(native_saved_matches(e['after']['native'],e['after']['saved']),'Native event differs from full20 durable state')
    relog=u['relogin'];require(len(relog)==2 and {(e['identity'],e['page']) for e in relog}=={(4,950),(5,936)},'TW/CN relogin coverage missing')
    for e in relog:
        require(e.get('owner34_full20_restored') is True and e.get('durable_revisions_unchanged') is True and
                set(e['saved'])=={str(i) for i in range(34)} and
                native_saved_matches(e['native'],e['saved']), 'Relogin full34 native20 differs')

def run02_gate(data):
    require(RUN02_ADAPTER_READY,'Pending actual run02 bank/armor/weapon/gem receipt adapter; deployment blocked')
    process_guards(data)
    scope='REAL_BANK_ARMOR63_REJECTION_AND_NATIVE_MED63_64_65_WITH_ALL_ARMOR_WEAPON_GEM_FULL20_PRESERVED_CUSTOM_TEST_ONLY'
    require(data.get('scope')==scope,'Bank/owner-instance native scope differs')
    for key in ('bank_swap_harness_unchanged','runtime20_unchanged','frozen_files_unchanged'):
        require(data.get(key) is True,'Bank wrapper guard absent: '+key)
    require(data['runtime20_before']==data['runtime20_after']==read(CONTRACT)['source_sha256'],
            'Bank run did not use the exact runtime20')
    require(data['frozen_files_before']==data['frozen_files_after'] and data['frozen_files_before'],
            'Bank evidence pins differ')
    for path,digest in data['frozen_files_before'].items():
        require(sha(Path(path))==digest,'Bank evidence file changed: '+path)
    require(data['bank_swap_harness_sha256']==sha(BANK_HARNESS) and
            data['frozen_files_before'].get(str(BANK_HARNESS))==sha(BANK_HARNESS),
            'Bank native harness changed')
    u=data['ui']
    for key in ('accepted','unrelated_saved_rows_preserved','desktop_unchanged','all_clients_closed'):
        require(u.get(key) is True,'Bank UI guard absent: '+key)
    require(u.get('rendered_pixels_tested') is False,'Bank proof must not invent a pixel claim')
    initial,final=u['initial'],u['final']
    identities=[(e['identity'],e['language']) for e in final['native']]
    require(identities==[(4,950),(5,936)] and
            [(e['identity'],e['language']) for e in initial['native']]==identities,'Bank TW/CN owners differ')
    require(len(initial['instances'])==2 and initial['instances']==u['final_instances'],
            'Bank changed complete armor/weapon/gem metadata, revisions or native state')
    tables={'character_armor_slot_metadata','character_weapon_slot_metadata','character_teleport_gem_metadata'}
    for owner,state in zip((4,5),initial['instances']):
        require(set(state['tables'])==tables and
                {r[1] for r in state['tables']['character_armor_slot_metadata']}=={0,1,30,31,32,33} and
                {r[1] for r in state['tables']['character_weapon_slot_metadata']}==({8,34} if owner==4 else {8}) and
                {r[1] for r in state['tables']['character_teleport_gem_metadata']}=={12},'Bank full-instance fixture coverage differs')
        scalar={r[1]:r for r in state['scalar']}
        require(len(scalar)==len(state['scalar']) and set(state['native'])=={str(slot) for slot in scalar},
                'Bank instance scalar/native domain differs')
        for rows in state['tables'].values():
            for row in rows:
                raw=bytes.fromhex(row[2]);s=scalar[row[1]]
                require(row[0]==owner and len(raw)==20 and s[0]==owner and s[2]==int.from_bytes(raw[:2],'little') and
                        s[3]==1 and s[4]==row[3] and s[5]==definitions.SOURCE_SHA and
                        state['native'][str(row[1])]==(struct.pack('<I',1)+raw).hex(),
                        'Bank preserved-instance bytes do not match durable scalar/metadata')
    events=u['events'];commits=[e for e in events if e['operation'] in ('0x63','0x64','0x65')]
    require(len(commits)==20 and len(initial['db']['receipts'])==0 and len(final['db']['receipts'])==20,
            'Bank commit/receipt counts differ')
    previous=initial['db'];plan=[]
    for owner,page,count in ((4,950,10),(5,936,8)):
        own=[e for e in commits if (e['after']['native']['identity'],e['after']['native']['language'])==(owner,page)]
        expected=[('0x63',0,5,2,3),('0x63',0,5,3,count-3),
                  ('0x65',0,2,3,1),('0x65',0,3,2,1),('0x65',0,2,3,1),
                  ('0x64',0,3,6,1),('0x64',0,3,7,2),('0x63',1,6,2,1),
                  ('0x64',0,2,5,count-3),('0x64',1,2,6,1)]
        require([(e['operation'],e['page'],e['source'],e['destination'],e['quantity']) for e in own]==expected,
                'Bank partial/whole/swap/page/reopen native direction coverage differs')
        refusals=[e for e in events if e['operation']=='armor63_rejected' and e['identity']==owner]
        attempts=[e for e in events if e['operation']=='armor63_attempt' and e['identity']==owner]
        require(len(refusals)==len(attempts)==1,'Bank armor63 rejection coverage missing')
        rejected,attempt=refusals[0],attempts[0]
        require(rejected.get('all_saved_rows_unchanged') is True and rejected.get('full30bag24_and_instances_unchanged') is True and
                'NATIVE_BANK_ITEM_REQUEST' in rejected['server_marker'] and 'committed=false rejected=true CUSTOM-0065' in rejected['server_marker'] and
                rejected['after_db']==attempt['before_db'] and
                all(rejected['after_native'][key]==attempt['before_native'][key] for key in ('bag','vault')),
                'Bank armor refusal did not preserve canonical state')
        for e in own:
            native,durable=e['after']['native'],e['after']['db']
            require(e.get('other_owner_unchanged') is True and e.get('native_and_durable_total')==count and
                    native['mode']==0 and native['current_page']==e['page'] and
                    durable['wallets']==initial['db']['wallets'] and durable['bank_money']==initial['db']['bank_money'],
                    'Bank authority/context/money or peer conservation differs')
            for key,size in (('bag',30),('vault',300)):
                rows=[r for r in durable[key] if r[0]==owner]
                require(len(rows)==size and {r[1] for r in rows}==set(range(size)) and
                        len(native[key])==size and {r['slot'] for r in native[key]}==set(range(size)),
                        'Bank native/durable slot domain differs')
                actual={r['slot']:(r['item'],r['quantity']) for r in native[key]}
                require(all(actual[r[1]]==(r[2],r[3]) for r in rows),'Bank native/durable items differ')
                require([r for r in durable[key] if r[0]!=owner]==[r for r in previous[key] if r[0]!=owner],
                        'Bank mutation changed the other owner')
            require(sum(r['quantity'] for key in ('bag','vault') for r in native[key] if r['item']==3107)==count,
                    'Bank MED total differs')
            baseline=initial['instances'][owner-4]
            for s in baseline['scalar']:
                if s[1]>=30:continue
                require(next(r for r in durable['bag'] if r[0]==owner and r[1]==s[1])==s[:5] and
                        native['bag'][s[1]]['raw']==baseline['native'][str(s[1])],
                        'Bank replay lost armor/weapon/gem bag overlay')
            plan.append((owner,owner,int(e['operation'],16),e['page'],e['source'],e['destination'],e['quantity']))
            require(len(durable['receipts'])==len(plan),'Bank actual receipt sequence differs')
            previous=durable
        require(any(e['operation']=='close39' and e['identity']==owner for e in events) and
                sum(e['operation']=='NPC37_bank_open' and (e['native']['identity'],e['native']['language'])==(owner,page) for e in events)==3,
                'Bank native close/reopen coverage missing')
    receipts=final['db']['receipts']
    require(len({r[0] for r in receipts})==20 and sorted(tuple(r[1:8]) for r in receipts)==sorted(plan) and
            all(r[-1]=='CUSTOM-0065' for r in receipts),'Bank durable receipts differ from actual UI operations')
    require(final['db']==previous,'Bank final state differs from final native operation')
    for native in final['native']:
        for key in ('bag','vault'):
            rows=[r for r in final['db'][key] if r[0]==native['identity']]
            require({r['slot']:(r['item'],r['quantity']) for r in native[key]}==
                    {r[1]:(r[2],r[3]) for r in rows},'Bank final native snapshot differs')
        wraps=[e for e in events if e['operation']=='page_wrap' and e['identity']==native['identity']]
        require(len(wraps)==1 and wraps[0]['reachable_pages']==list(range(2 if wraps[0]['edition_field_232f64']==1 else 3)) and
                wraps[0]['native']['current_page']==wraps[0]['reachable_pages'][-1], 'Bank native page wrap proof missing')

def ctest_gate(log,count,required=()):
    data=Path(log).read_text('utf-8').replace('\r\n','\n')
    rows=re.findall(r'^\s*(\d+)/(\d+) Test\s+#\d+:\s+([A-Za-z0-9_]+)\s+\.+\s+(Passed|\*\*\*[^\n]*)(?:\s+[^\n]*)?$',data,re.M)
    names=[row[2] for row in rows]
    require([int(r[0]) for r in rows]==list(range(1,count+1)) and
            all(int(r[1])==count and r[3]=='Passed' for r in rows) and
            len(set(names))==count and (not required or set(names)==set(required)),
            'CTest exact suite coverage or pass status differs')
    require(re.search(r'^100% tests passed(?:, 0 tests failed)? out of '+str(count)+r'\s*$',data,re.M),
            'CTest success summary missing')
    return names

def verification_gate(verification,contract):
    require(verification.get('candidate_sha256')==PIN and verification.get('frozen_chat_passed') is True,
            'Root verification candidate/frozen-chat proof differs')
    require(verification.get('source_sha256')==contract['source_sha256'],'Root tested source20 differs')
    results={}
    for key,log,count,names in (('related',RELATED_LOG,16,REQUIRED_RELATED),
                               ('production_adapter',PRODUCTION_LOG,1,{'sqlite_armor_production_adapter'})):
        node=verification[key]
        require(node.get('exit_code')==0 and node.get('command') and
                node.get('passed')==count and node.get('total')==count and
                Path(node['log']).resolve()==log.resolve() and node.get('log_sha256')==sha(log),
                'Missing passing root CTest receipt: '+key)
        results[key]=ctest_gate(log,count,names)
        require(node.get('passed_names')==results[key],'CTest receipt and actual output differ: '+key)
    extra=verification.get('extra_test_sources',{})
    require(set(extra)==EXTRA_TEST_SOURCES,'Test source receipt differs')
    for path,digest in {**contract['source_sha256'],**extra}.items():
        require(sha(checked_path(path))==digest,'Compiled/tested source changed: '+path)
    support=verification.get('support_source_sha256',{})
    require(EXTRA_SOURCES<=set(support),'Root must pin all final supporting source/evidence/doc files')
    for path,digest in support.items():
        require(sha(checked_path(path))==digest,'Supporting archive file changed: '+path)
        if path in extra:require(digest==extra[path],'Support/tested source disagreement: '+path)
        if path in contract['source_sha256']:require(digest==contract['source_sha256'][path],'Support/runtime disagreement: '+path)
    return results,{**contract['source_sha256'],**support},extra

def qualify():
    require(sha(CANDIDATE)==PIN,'Immutable2696 candidate differs')
    contract=read(CONTRACT);require(contract['candidate_sha256']==PIN and contract['schema']==42 and
        contract['scope']=='OWNED_INSTANCE_TRANSPORT_ONLY_NO_STAT_FORMULA_OR_APPEARANCE_OR_GRANTS','Runtime contract differs')
    verification=read(VERIFICATION)
    results,sources,test_sources=verification_gate(verification,contract)
    require(frozen.hashes()==read(frozen.BASELINE)['source_sha256'],'Frozen chat baseline changed')
    run01_gate(read(RUN01));require(RUN02 is not None,'Actual run02 receipt path not delivered')
    run02_gate(read(RUN02))
    return {'format':FORMAT,'candidate_sha256':PIN,'source_sha256':sources,'source_count':len(sources),
            'verification_sha256':sha(VERIFICATION),'related_ctest_sha256':sha(RELATED_LOG),
            'production_ctest_sha256':sha(PRODUCTION_LOG),'related_tests':results['related'],
            'production_tests':results['production_adapter'],
            'compiled_source_sha256':contract['source_sha256'],'extra_test_source_sha256':test_sources,
            'support_source_sha256':verification['support_source_sha256'],
            'run01_sha256':sha(RUN01),'run02_sha256':sha(RUN02),'client_sha256':sha(managed.CLIENT),
            'scope':contract['scope']}

def candidate_run(config,migrate=False):
    require(sha(CANDIDATE)==PIN,'Candidate changed before clone/migration run')
    result=subprocess.run([str(CANDIDATE),'--config',str(config)]+(['--migrate-only'] if migrate else ['--run-for','1']),
        cwd=ROOT,capture_output=True,creationflags=managed.FLAGS,timeout=30)
    result.check_returncode();return result.stdout+result.stderr

def startup_log_gate(log_path,before):
    after=Path(log_path).read_bytes()
    require(after[:len(before)]==before and len(after)>len(before),'Formal startup log was rotated, truncated or not appended')
    appended=after[len(before):]
    text=appended.decode('utf-8',errors='replace')
    markers=('OWNED_ARMOR_TRANSFERS_ENABLED CUSTOM-0066 instance_only no_grants no_formula no_appearance',
             'NATIVE_ARMOR_DEFINITIONS equ=692 teq=662 authority=NATIVE_PARSED_DEFINITION_ONLY no_instances no_combat_formula')
    require(all(marker in text for marker in markers),'New formal Application startup did not enable the exact qualified scope')
    return {'log':str(Path(log_path).resolve()),'byte_offset':len(before),'appended_bytes':len(appended),
            'prior_sha256':hashlib.sha256(before).hexdigest(),
            'appended_sha256':hashlib.sha256(appended).hexdigest(),
            'markers':[line for line in text.splitlines() if any(marker in line for marker in markers)]}

def process_config_gate(info,args,pid):
    require(info.get('pid')==pid and Path(info['path']).resolve()==managed.ACTIVE.resolve(),
            'Formal startup PID/executable differs')
    require(args and Path(args[0]).resolve()==managed.ACTIVE.resolve() and args.count('--config')==1,
            'Formal process must have one explicit config path')
    index=args.index('--config')
    require(index+1<len(args) and Path(args[index+1]).resolve()==managed.CONFIG.resolve(),
            'Formal process uses another config')
    return {'pid':pid,'path':info['path'],'command_line':info['command_line'],'argv':args,
            'config_path':str(managed.CONFIG.resolve())}

def formal_process_proof(pid):
    # Read the actual process, rather than assuming the scheduled task's saved
    # action matches the process that now owns the listener.
    info=json.loads(managed.powershell(
        "$ErrorActionPreference='Stop'; $p=Get-CimInstance Win32_Process -Filter 'ProcessId="+str(pid)+
        "'; if(-not $p){throw 'Formal process missing'}; @{pid=[int]$p.ProcessId;path=$p.ExecutablePath;command_line=$p.CommandLine}|ConvertTo-Json -Compress").stdout)
    import ctypes
    from ctypes import wintypes
    count=ctypes.c_int()
    shell=ctypes.WinDLL('shell32',use_last_error=True);kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    shell.CommandLineToArgvW.argtypes=[wintypes.LPCWSTR,ctypes.POINTER(ctypes.c_int)]
    shell.CommandLineToArgvW.restype=ctypes.POINTER(wintypes.LPWSTR)
    kernel.LocalFree.argtypes=[wintypes.HLOCAL];kernel.LocalFree.restype=wintypes.HLOCAL
    values=shell.CommandLineToArgvW(info['command_line'],ctypes.byref(count))
    require(bool(values),'Cannot read formal command arguments')
    try:args=[values[i] for i in range(count.value)]
    finally:kernel.LocalFree(ctypes.cast(values,wintypes.HLOCAL))
    return process_config_gate(info,args,pid)

def archive_sources(sources):
    for relative,digest in sources.items():
        target=DEPLOY/'tested-source'/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(checked_path(relative),target);require(sha(target)==digest,'Source backup differs: '+relative)

def stage():
    gate=qualify();require(not DEPLOY.exists(),'Deployment already staged; inspect it')
    managed.listener() # Requires zero established managed connections.
    before_config=read(managed.CONFIG);after_config=config_after(before_config);config_gate(before_config,after_config)
    database=Path(before_config['database']['path']);before=snapshots.capture(database);source_catalog_gate(database)
    require(before['history'][-1][0]==41,'Stage expects source-only schema41')
    DEPLOY.mkdir(parents=True)
    managed.backup(database,DEPLOY/'accounts.before.db');require(snapshots.capture(DEPLOY/'accounts.before.db')==before,'Save changed while backing up')
    managed.backup(DEPLOY/'accounts.before.db',DEPLOY/'town-diagnostic-accounts.db')
    clone_config=copy.deepcopy(after_config);clone_config['database']['path']=str(DEPLOY/'town-diagnostic-accounts.db')
    clone_config['logging']['file']=str(DEPLOY/'stage.log')
    with socket.socket() as reserve:reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
    clone_config['server'].update(host='127.0.0.1',port=port,character_port=0)
    write(DEPLOY/'stage-config.json',clone_config);candidate_run(DEPLOY/'stage-config.json',True)
    output=candidate_run(DEPLOY/'stage-config.json');(DEPLOY/'stage-output.log').write_bytes(output)
    require('OWNED_ARMOR_TRANSFERS_ENABLED' in (DEPLOY/'stage.log').read_text('utf-8'),'Clone Application did not enable the qualified route')
    after=snapshots.capture(DEPLOY/'town-diagnostic-accounts.db');schema_gate(before,after);source_catalog_gate(DEPLOY/'town-diagnostic-accounts.db')
    shutil.copy2(managed.ACTIVE,DEPLOY/'god2-server.before.exe');shutil.copy2(CANDIDATE,DEPLOY/'god2-server.candidate.exe')
    shutil.copy2(managed.CONFIG,DEPLOY/'server-config.before.json');write(DEPLOY/'server-config.after.json',after_config)
    archive_sources(gate['source_sha256']);write(DEPLOY/'gate.json',gate)
    write(DEPLOY/'save-before.json',before);write(DEPLOY/'save-stage.json',after)
    info=dict(gate,state='STAGED',time=common.now(),database=str(database),old_server_sha256=sha(managed.ACTIVE),
        config_before_sha256=sha(managed.CONFIG),config_after_sha256=sha(DEPLOY/'server-config.after.json'),
        added_tables=[TABLE],added_triggers=sorted(TRIGGERS),armor_grants=0,old_saved_rows_changed=0)
    require(snapshots.capture(database)==before and read(managed.CONFIG)==before_config,'Managed save/config changed during stage')
    write(DEPLOY/'release.json',info);return info

def apply():
    gate=qualify();info=read(DEPLOY/'release.json');require(info['state']=='STAGED','Staged release required')
    require(gate==read(DEPLOY/'gate.json'),'Qualification changed after stage')
    require(sha(managed.ACTIVE)==info['old_server_sha256'] and sha(managed.CONFIG)==info['config_before_sha256'] and
            sha(managed.CLIENT)==info['client_sha256'],'Managed files changed')
    require(sha(DEPLOY/'god2-server.candidate.exe')==PIN and sha(DEPLOY/'server-config.after.json')==info['config_after_sha256'],'Staged files changed')
    config_gate(read(managed.CONFIG),read(DEPLOY/'server-config.after.json'))
    for path,digest in gate['source_sha256'].items():require(sha(DEPLOY/'tested-source'/path)==digest,'Archived tested source changed')
    database=Path(info['database']);before=read(DEPLOY/'save-before.json')
    require(snapshots.capture(database)==before,'Save changed since stage; restage required')
    pid=managed.listener();managed.backup(database,DEPLOY/'accounts.at-install.db')
    require(snapshots.capture(DEPLOY/'accounts.at-install.db')==before and snapshots.capture(database)==before,'Fresh pre-stop backup differs')
    common.lifecycle.stop_managed_and_wait(pid)
    if snapshots.capture(database)!=before:
        managed.start();raise RuntimeError('Save changed during no-player stop; install was not attempted')
    try:
        # Compatible schema42 code is installed before migration; no DB copyback.
        shutil.copy2(DEPLOY/'god2-server.candidate.exe',managed.ACTIVE)
        shutil.copy2(DEPLOY/'server-config.after.json',managed.CONFIG)
        candidate_run(managed.CONFIG,True)
        after=snapshots.capture(database);schema_gate(before,after,read(DEPLOY/'save-stage.json'));source_catalog_gate(database)
        require(sha(managed.ACTIVE)==PIN and sha(managed.CLIENT)==info['client_sha256'] and sha(managed.CONFIG)==info['config_after_sha256'],'Installed files differ')
        formal_log=Path(read(managed.CONFIG)['logging']['file'])
        formal_log_before=formal_log.read_bytes() if formal_log.exists() else b''
        managed.start()
        managed.powershell("$deadline=(Get-Date).AddSeconds(20); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Managed listener not ready'}")
        # No-player receipt: a newly connected player blocks final equality, not
        # a permission to overwrite that player's newer saved data.
        server_pid=managed.listener()
        formal_startup={'process':formal_process_proof(server_pid),
                        'application':startup_log_gate(formal_log,formal_log_before)}
        write(DEPLOY/'formal-startup-proof.json',formal_startup)
        installed=snapshots.capture(database);schema_gate(before,installed,read(DEPLOY/'save-stage.json'));source_catalog_gate(database)
        require(sha(managed.CLIENT)==info['client_sha256'] and sha(managed.CONFIG)==info['config_after_sha256'],'Client/config changed during start')
        info.update(state='INSTALLED',installed_at=common.now(),server_pid=server_pid,saved_rows_preserved=True,
                    armor_grants=0,formal_startup_proof_sha256=sha(DEPLOY/'formal-startup-proof.json'))
        write(DEPLOY/'save-installed.json',installed);write(DEPLOY/'release.json',info)
    except BaseException as error:
        info.update(state='REPAIR_REQUIRED_SCHEMA42_COMPATIBLE_CANDIDATE_RETAINED',error=str(error),database_restored=False,old_executable_restored=False)
        write(DEPLOY/'release.json',info)
        # Never launch schema41 binary against migrated data or replace saves.
        if sha(managed.ACTIVE)==PIN:
            try:managed.start()
            except Exception:pass
        raise
    return info

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('qualify','stage','apply'))
    result={'qualify':qualify,'stage':stage,'apply':apply}[parser.parse_args().mode]()
    print(json.dumps({k:result.get(k) for k in ('state','candidate_sha256','source_count','server_pid','armor_grants')}))
if __name__=='__main__':main()
