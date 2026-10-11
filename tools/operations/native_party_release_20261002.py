"""Scoped party promotion after TW/CN native UI and owned TCP acceptance.

Reuse executable-only managed lifecycle; never overwrite live player saves.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
from tools.operations import native_peer_pose_release_20261002 as lifecycle
from tools.operations import verify_frozen_chat_20260927 as frozen

ROOT=lifecycle.ROOT
ROUND=ROOT/'artifacts/releases/native-party-20261002'
SOURCES=(
    'src/game/NativeParty.h','src/protocol/RecoveredParty.h',
    'src/protocol/RecoveredWorldRecords.h','src/core/Application.cpp',
    'tests/test_native_party.cpp','tests/test_recovered_world_records.cpp',
    'tests/research/test_native_party_server.py','tests/CMakeLists.txt',
    'tools/strike_lab/current_party_20261002.py',
    'tools/strike_lab/private_party_20261002.py',
    'tools/operations/native_party_release_20261002.py',
)
TESTS=('native_party','recovered_world_service','recovered_world_records',
       'native_party_tcp','native_party_machine')
RECEIPTS=(ROOT/'artifacts/playtests/private-party-20261002-05/run-result.json',
          ROOT/'artifacts/playtests/private-party-20261002-06/run-result.json')
require=lifecycle.require
sha=lifecycle.managed.sha
read=lifecycle.read

def record_gate():
    require(not (ROUND/'manifest.json').exists(),'Inspect existing gate; do not silently overwrite')
    source=ROOT/'build-town-visibility/Testing/Temporary/LastTest.log'
    log=source.read_text('utf-8',errors='replace')
    for name in TESTS:
        block=re.search(r'Test: '+re.escape(name)+r'\n(.*?)(?=\n\d+/\d+ Testing:|\Z)',log,re.S)
        require(block is not None and 'Test Passed.' in block.group(1) and 'Test Failed.' not in block.group(1),
                'Missing passing CTest evidence: '+name)
    require('Ran 6 tests' in log and '\nOK\n' in log and sha(lifecycle.CANDIDATE) in log,
            'TCP case count/candidate does not match recorded gate')
    require(frozen.hashes()==read(frozen.BASELINE)['source_sha256'],'Frozen chat changed')
    ROUND.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,ROUND/'ctest.log')
    native=read(ROOT/'artifacts/research/native-party-20261002.json')
    require(native['producer_cases']==11 and native['roster_cases']==8 and native['position_cases']==5 and
            native['vitals_cases']==5 and native['removal_cases']==4 and len(native['bar_cases'])==30,
            'Native party oracle differs')
    native_path=ROUND/'native-machine.json';lifecycle.write(native_path,native)
    gate={'candidate_sha256':sha(lifecycle.CANDIDATE),
          'source_sha256':{name:sha(ROOT/name) for name in SOURCES},
          'verification':{'ctest_suites':{'passed':5,'total':5},'tcp_cases':{'passed':6,'total':6},
                          'ctest_log_sha256':sha(ROUND/'ctest.log'),'native_machine_sha256':sha(native_path),
                          'frozen_chat_passed':True},
          'scope':'Same-scene consent/roster/position/vitals/leave/kick/disconnect. No group battle, follow, shared rewards or original server-rule recovery.'}
    lifecycle.write(ROUND/'manifest.json',gate)
    return gate

def qualify(receipt_path):
    require(Path(receipt_path).resolve()==RECEIPTS[0].resolve(),'Use the qualified primary receipt')
    for receipt,page in zip(RECEIPTS,(950,936)):
        data=read(receipt)
        require(data.get('accepted') is True and data.get('runner_exit')==0 and
                data.get('candidate_sha256')==sha(lifecycle.CANDIDATE),'Native party candidate was not accepted')
        for name in ('source_files_unchanged','candidate_unchanged','all_owned_processes_closed',
                     'private_files_unchanged','all_private_images_closed','party_harness_unchanged'):
            require(data.get(name) is True,'Missing native guard: '+name)
        require(data['before']==data['after'] and data['before']['live_client']==sha(lifecycle.managed.CLIENT),
                'Current source/client differs from tested client')
        require(data['party_harness_sha256']==sha(ROOT/'tools/strike_lab/private_party_20261002.py'),
                'Native party harness changed')
        ui=data['ui']
        for name in ('accepted','desktop_unchanged','all_clients_closed','unrelated_saved_rows_preserved'):
            require(ui.get(name) is True,'Missing worker guard: '+name)
        require(ui['source_page']==page and ui['rendered_pixels_tested'] is False,'Acceptance scope differs')
        require([r['count'] for r in ui['initial']]==[0,0] and
                ui['initial'][0]['own_name']==('台' if page==950 else '臺'),'Raw-self name variant not covered')
        expected=[]
        for requester,leader in ((4,5),(5,4)):
            expected.extend([('decline',requester,leader),('accept',requester,leader),
                             ('move',requester,None),('move',requester,None),('leave',requester,None),
                             ('accept',requester,leader),('kick',leader,None)])
        expected.extend([('accept',4,5),('leader_disconnect',5,None)])
        actual=[(e['operation'],e.get('requester',e.get('source')),e.get('leader')) for e in ui['events']]
        require(actual==expected,'Incomplete native party two-way coverage')
        for event in ui['events']:
            if event['operation']=='accept':
                require([r['count'] for r in event['native']]==[1,1] and
                        [r['self_leader'] for r in event['native']]==[0,1] and
                        all(r['leader']==event['leader'] for r in event['native']),
                        'Native self/leader recognition failed')
            elif event['operation']=='move':
                native=event['native'];destination=event['destination']
                require(native['observer']['position']==[event['source'],*destination] and
                        [native['local']['x'],native['local']['y']]==destination and
                        native['saved'][:4]==[4,3,*destination],'Native party movement not accepted')
        require([r[:5] for r in ui['positions_before']]==[r[:5] for r in ui['positions_after']],
                'Unrelated position changed')
    gate=read(ROUND/'manifest.json')
    require(gate['candidate_sha256']==sha(lifecycle.CANDIDATE),'Gate candidate differs')
    for name,digest in gate['source_sha256'].items():require(sha(ROOT/name)==digest,'Tested source changed: '+name)
    require(sha(ROUND/'ctest.log')==gate['verification']['ctest_log_sha256'] and
            sha(ROUND/'native-machine.json')==gate['verification']['native_machine_sha256'],'Gate evidence changed')
    require(frozen.hashes()==read(frozen.BASELINE)['source_sha256'],'Frozen chat changed')
    return read(RECEIPTS[0])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('record-gate','stage','apply'));args=parser.parse_args()
    lifecycle.ROUND=ROUND;lifecycle.DEPLOY=ROUND/'deployment';lifecycle.qualify=qualify
    if args.mode=='record-gate':result=record_gate()
    elif args.mode=='stage':result=lifecycle.stage(RECEIPTS[0])
    else:result=lifecycle.apply()
    print(json.dumps({k:result.get(k) for k in ('state','server_pid','saved_rows_preserved','candidate_sha256')}))

if __name__=='__main__':main()
