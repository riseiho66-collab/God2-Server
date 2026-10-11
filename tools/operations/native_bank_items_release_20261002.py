"""Qualified native scalar bank item deployment with additive schema and preserved saves.

Only the executable is replaced. Candidate startup installs two empty tables;
existing schema/history/rows must exactly match the staged read snapshot.
Failure restores only the executable, never an old player database.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
from tools.operations import native_peer_pose_release_20261002 as lifecycle
from tools.operations import packet_links_release_20260930 as snapshots
from tools.operations import verify_frozen_chat_20260927 as frozen

managed=lifecycle.managed
ROOT=lifecycle.ROOT
ROUND=ROOT/'artifacts/releases/native-bank-items-20261002'
DEPLOY=ROUND/'deployment'
CANDIDATE=ROOT/'artifacts/research/native-bank-items-20261002/candidate-02/god2-server.exe'
RECEIPT=ROOT/'artifacts/playtests/private-native-blackbox-bank-items-20261002-03/run-result.json'
TABLES={'character_bank_item_slots','character_bank_item_receipts'}
SCHEMA_NAMES=TABLES|{'sqlite_autoindex_character_bank_item_slots_1','sqlite_autoindex_character_bank_item_receipts_1'}
TESTS=('bank_items_repository','native_bank_items_machine','native_bank_items_tcp',
       'bank_repository','bank_service','native_bank_machine','native_bank_tcp',
       'recovered_trade','trade_repository','trade_service','native_trade_machine',
       'native_trade_tcp','native_party','native_party_tcp',
       'recovered_world_records','recovered_world_service')
SOURCES=('src/protocol/RecoveredBank.h', 'src/protocol/RecoveredWorldRecords.h', 'src/db/SqliteBankRepository.h', 'src/db/SqliteBankRepository.cpp', 'src/db/SqliteBankAccessRepository.h', 'src/db/SqliteBankAccessRepository.cpp', 'src/db/SqliteDatabase.h', 'src/db/SqliteDatabase.cpp', 'src/core/Application.cpp', 'src/handlers/RecoveredBankService.h', 'src/handlers/RecoveredBankService.cpp', 'tests/test_bank_repository.cpp', 'tests/test_bank_service.cpp', 'tests/test_recovered_world_records.cpp', 'tests/research/test_native_bank_server.py', 'tests/research/test_current_packet_gap_ledger.py', 'tests/CMakeLists.txt', 'tools/strike_lab/current_bank_20261002.py', 'tools/strike_lab/private_bank_20261002.py', 'tools/strike_lab/bank_fixture_catalog_20261002.py', 'src/protocol/RecoveredBankItems.h', 'src/db/SqliteBankItemsRepository.h', 'src/db/SqliteBankItemsRepository.cpp', 'src/handlers/RecoveredBankItemsService.h', 'src/handlers/RecoveredBankItemsService.cpp', 'tests/test_bank_items_repository.cpp', 'tests/research/test_native_bank_items_server.py', 'tools/strike_lab/current_bank_items_20261002.py', 'tools/strike_lab/private_bank_items_20261002.py', 'tools/operations/native_bank_items_release_20261002.py')
sha=managed.sha
read=lifecycle.read
write=lifecycle.write
require=lifecycle.require


def schema_gate(before,after,template=None):
    require(not TABLES & set(before['tables']),'Unexpected pre-existing bank tables')
    require(set(after['tables'])==set(before['tables'])|TABLES,'Unexpected table additions')
    require([r for r in after['schema'] if r[1] not in SCHEMA_NAMES]==before['schema'],
            'Existing schema changed')
    addition=[r for r in after['schema'] if r[1] in SCHEMA_NAMES]
    require({r[1] for r in addition}==SCHEMA_NAMES and len(addition)==4,'Unexpected bank schema objects')
    require(after['history']==before['history'] and after['pragmas']==before['pragmas'],
            'Migration history or database metadata changed')
    for table,value in before['tables'].items():
        require(after['tables'][table]==value,'Existing saved rows changed: '+table)
    require(all(after['tables'][t]['rows']==0 for t in TABLES),'Startup granted assets or configured an NPC')
    if template is not None:
        require(addition==[r for r in template['schema'] if r[1] in SCHEMA_NAMES],
                'Live bank schema differs from staged candidate')


def native_gate():
    d=read(RECEIPT);u=d['ui']
    require(d.get('accepted') is True and d.get('runner_exit')==0 and
            d['candidate_sha256']==sha(CANDIDATE),'Native bank item candidate differs or failed')
    for key in ('source_files_unchanged','candidate_unchanged','all_owned_processes_closed',
                'private_files_unchanged','all_private_images_closed','bank_items_harness_unchanged'):
        require(d.get(key) is True,'Missing native guard: '+key)
    require(d['before']==d['after'] and d['before']['live_client']==sha(managed.CLIENT),
            'Current client does not match native evidence')
    require(d['bank_items_harness_sha256']==sha(ROOT/'tools/strike_lab/private_bank_items_20261002.py'),
            'Native bank items harness changed')
    for key in ('accepted','desktop_unchanged','all_clients_closed','unrelated_saved_rows_preserved'):
        require(u.get(key) is True,'Missing native worker guard: '+key)
    require(u['rendered_pixels_tested'] is False,'Native observation scope changed')
    require({r['language'] for r in u['initial']['native']}=={950,936},'Both native languages required')
    npcs=u.get('qualified_native_npc',[])
    require(len(npcs)==2 and all(n['identity']==3793 and n['renderer_active'] is True and
            n['resource']>0 and (n['x'],n['y'])==(128,126) for n in npcs),'Native private banker renderer missing')
    expected=['0x63','0x63','0x65','0x64','0x64','0x63','0x64','0x64']
    mutations=[e for e in u['events'] if e['operation'] in expected]
    require(len(mutations)==16,'Incomplete native mutation coverage')
    for identity,count in ((4,10),(5,8)):
        events=[e for e in mutations if e['after']['native']['identity']==identity]
        require([e['operation'] for e in events]==expected,'Native mutation direction/order differs')
        require([e['quantity'] for e in events]==[3,count-3,1,1,2,1,count-3,1],
                'Native whole/partial quantity coverage differs')
        for e in events:
            require(e['other_owner_unchanged'] is True and e['rendered'],'No two-owner/rendered-cell proof')
            if e['operation']!='0x65' and e['quantity']>1:
                require(e['modal'] is not None and e['modal']['mode']==(2 if e['operation']=='0x63' else 3),
                        'Real native quantity modal missing')
        wrap=next(e for e in u['events'] if e['operation']=='page_wrap' and e['identity']==identity)
        require(wrap['reachable_pages']==([0,1] if wrap['edition_field_232f64']==1 else [0,1,2]),
                'Native edition page wrap missing')
        final=next(r for r in u['final']['native'] if r['identity']==identity)
        require(final['bank_widget'] is None and final['purse']==1000 and final['bank']==0,
                'Native final close/money preserved check failed')
    end=u['final']['db']
    require(end['wallets']==[[4,1000,1],[5,1000,1]] and end['bank_money']==[[4,0,1],[5,0,1]],
            'Item operation changed money')
    require(len(end['receipts'])==16 and len(end['vault'])==600 and all(r[2]==r[3]==0 for r in end['vault']),
            'Native final bank item conservation failed')
    require([(r[0],r[1],r[2],r[3]) for r in end['bag'] if r[3]]==
        [(4,5,3107,7),(4,6,3107,1),(4,7,3107,2),(5,5,3107,5),(5,6,3107,1),(5,7,3107,2)],
        'Native final bag conservation failed')
    oracle=read(ROOT/'artifacts/research/native-bank-items-20261002/oracle.json')
    require(oracle.get('passed')==80 and oracle.get('failed')==0,'Native item machine evidence missing')
    return d


def record_gate():
    require(not (ROUND/'manifest.json').exists(),'Gate already exists; inspect it')
    native_gate()
    source=ROOT/'build-town-visibility/Testing/Temporary/LastTest.log'
    # MSBuild output may be CP950; gate markers and candidate hashes are ASCII.
    log=source.read_bytes().replace(b'\r\n',b'\n')
    for name in TESTS:
        block=re.search(b'Test: '+name.encode()+br'\n(.*?)(?=\n\d+/\d+ Testing:|\Z)',log,re.S)
        require(block is not None and b'Test Passed.' in block.group(1) and
                b'Test Failed.' not in block.group(1),'Missing passing CTest: '+name)
    require(b'Ran 4 tests' in log and b'Ran 3 tests' in log and b'Ran 6 tests' in log and sha(CANDIDATE).encode() in log,
            'TCP count/candidate differs from gate')
    require(frozen.hashes()==read(frozen.BASELINE)['source_sha256'],'Frozen chat changed')
    ROUND.mkdir(parents=True,exist_ok=True);shutil.copy2(source,ROUND/'ctest.log')
    gate={'candidate_sha256':sha(CANDIDATE),'source_sha256':{p:sha(ROOT/p) for p in SOURCES},
          'receipt_sha256':sha(RECEIPT),'ctest_sha256':sha(ROUND/'ctest.log'),
          'verification':{'ctest_suites':16,'bank_items_tcp_cases':3,'bank_money_tcp_cases':4,'trade_tcp_cases':3,'party_tcp_cases':6,
                          'native_bank_items_cases':80,'native_ui_mutations':16,'frozen_chat_passed':True},
          'scope':'Native scalar MED02 bank items; CUSTOM-0065 authority. No enhanced/equipment/bound instances, merging/swap, official rules or NPC positions. Isolated real native controls/icons/count labels only; no pixels or load acceptance.'}
    write(ROUND/'manifest.json',gate);return gate


def qualify():
    native_gate();gate=read(ROUND/'manifest.json')
    require(gate['candidate_sha256']==sha(CANDIDATE),'Candidate changed since gate')
    for p,digest in gate['source_sha256'].items():require(sha(ROOT/p)==digest,'Tested source changed: '+p)
    require(sha(RECEIPT)==gate['receipt_sha256'] and sha(ROUND/'ctest.log')==gate['ctest_sha256'],
            'Gate evidence changed')
    require(frozen.hashes()==read(frozen.BASELINE)['source_sha256'],'Frozen chat changed')


def stage():
    qualify();require(not DEPLOY.exists(),'Deployment already staged')
    managed.listener()
    cfg=read(managed.CONFIG);database=Path(cfg['database']['path'])
    before=snapshots.capture(database);DEPLOY.mkdir()
    managed.backup(database,DEPLOY/'accounts.before.db')
    require(snapshots.capture(DEPLOY/'accounts.before.db')==before,'Live save changed during stage')
    managed.backup(DEPLOY/'accounts.before.db',DEPLOY/'town-diagnostic-accounts.db')
    cfg['database']['path']=str(DEPLOY/'town-diagnostic-accounts.db')
    cfg['logging']['file']=str(DEPLOY/'stage.log')
    with socket.socket() as reserved:reserved.bind(('127.0.0.1',0));port=reserved.getsockname()[1]
    cfg['server'].update(host='127.0.0.1',port=port,character_port=0)
    write(DEPLOY/'stage-config.json',cfg)
    # --migrate-only does not run Application's explicit bank schema install.
    result=subprocess.run([str(CANDIDATE),'--config',str(DEPLOY/'stage-config.json'),'--run-for','1'],
        cwd=ROOT,capture_output=True,creationflags=managed.FLAGS,timeout=20)
    (DEPLOY/'stage-stdout.log').write_bytes(result.stdout+result.stderr);result.check_returncode()
    after=snapshots.capture(DEPLOY/'town-diagnostic-accounts.db');schema_gate(before,after)
    shutil.copy2(managed.ACTIVE,DEPLOY/'god2-server.before.exe')
    shutil.copy2(CANDIDATE,DEPLOY/'god2-server.candidate.exe')
    shutil.copy2(managed.CONFIG,DEPLOY/'server-config.before.json')
    write(DEPLOY/'save-snapshot.before.json',before);write(DEPLOY/'save-snapshot.stage.json',after)
    info={'state':'STAGED','time':lifecycle.now(),'database':str(database),
          'old_server_sha256':sha(managed.ACTIVE),'candidate_sha256':sha(CANDIDATE),
          'config_sha256':sha(managed.CONFIG),'client_sha256':sha(managed.CLIENT),
          'added_tables':sorted(TABLES),'existing_saved_rows_changed':0,
          'native_bank_service_points':0,'bank_items_implemented':'SCALAR_MED02_EMPTY_DESTINATION_ONLY'}
    write(DEPLOY/'release.json',info);return info


def apply():
    qualify();info=read(DEPLOY/'release.json');require(info['state']=='STAGED','Staged release required')
    subprocess.run([sys.executable,'-B','-m','tools.operations.verify_frozen_chat_20260927'],cwd=ROOT,check=True)
    require(sha(managed.ACTIVE)==info['old_server_sha256'] and sha(managed.CONFIG)==info['config_sha256'] and
            sha(managed.CLIENT)==info['client_sha256'],'Managed files changed')
    require(sha(DEPLOY/'god2-server.candidate.exe')==info['candidate_sha256'],'Staged candidate changed')
    database=Path(info['database']);before=read(DEPLOY/'save-snapshot.before.json')
    require(snapshots.capture(database)==before,'Live saves changed since stage')
    pid=managed.listener()
    lifecycle.lifecycle.stop_managed_and_wait(pid)
    try:
        require(snapshots.capture(database)==before,'Saves changed while stopping')
        shutil.copy2(DEPLOY/'god2-server.candidate.exe',managed.ACTIVE);managed.start()
        managed.powershell("$deadline=(Get-Date).AddSeconds(20); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Managed listener not ready'}")
        info['server_pid']=managed.listener(allow_players=True)
        require(sha(managed.ACTIVE)==info['candidate_sha256'],'Installed candidate mismatch')
        after=snapshots.capture(database)
        schema_gate(before,after,read(DEPLOY/'save-snapshot.stage.json'))
        require(sha(managed.CONFIG)==info['config_sha256'] and sha(managed.CLIENT)==info['client_sha256'],
                'Client/config changed')
        info.update(state='INSTALLED',installed_at=lifecycle.now(),saved_rows_preserved=True)
        write(DEPLOY/'save-snapshot.installed.json',after);write(DEPLOY/'release.json',info)
    except BaseException as error:
        try:lifecycle.lifecycle.stop_managed_and_wait(managed.listener(allow_players=True))
        except Exception:pass
        shutil.copy2(DEPLOY/'god2-server.before.exe',managed.ACTIVE);managed.start()
        info.update(state='ROLLED_BACK_EXECUTABLE_ONLY',error=str(error),database_restored=False)
        write(DEPLOY/'release.json',info);raise
    return info


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('record-gate','stage','apply'));args=parser.parse_args()
    result={'record-gate':record_gate,'stage':stage,'apply':apply}[args.mode]()
    print(json.dumps({k:result.get(k) for k in ('state','server_pid','saved_rows_preserved','candidate_sha256')}))

if __name__=='__main__':main()
