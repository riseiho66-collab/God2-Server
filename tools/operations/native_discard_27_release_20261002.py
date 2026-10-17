# Legacy receipt identifiers retain their schema spelling; both cases are the
# Taiwan client using Traditional CP950 or Simplified CP936, not regional protocols.
"""Qualified native discard promotion; executable only, never restore old saves."""
import argparse,json
from tools.operations import native_peer_pose_release_20261002 as lifecycle
from tools.operations import native_quest_catalog_release as managed
from tools.operations import verify_frozen_chat_20260927 as frozen
ROOT=managed.ROOT;ROUND=ROOT/'artifacts/releases/native-discard-27-20261002'
RECEIPTS=[ROOT/'artifacts/playtests/private-discard-27-20261002-06/run-result.json',
          ROOT/'artifacts/playtests/private-discard-27-20261002-05/run-result.json']
def read(p):return json.loads(p.read_text('utf-8'))
def require(ok,message):
    if not ok:raise RuntimeError(message)
def qualify(_receipt=None):
    candidate=lifecycle.CANDIDATE;gate=read(ROUND/'manifest.json')
    require(gate['candidate_sha256']==managed.sha(candidate),'Candidate changed after tests')
    for name,digest in gate['source_sha256'].items():require(managed.sha(ROOT/name)==digest,'Source changed: '+name)
    require(gate['verification']=={'discard_tcp_tests':2,'regression_tcp_tests':6,'cpp_targets':4,
        'native_machine_cases':24,'ledger_tests':1,'frozen_chat_passed':True},'Automated gate incomplete')
    script=ROOT/'tools/strike_lab/private_discard_27_20261002.py'
    values=[]
    for page,path in zip((950,936),RECEIPTS):
        data=read(path);fixture=read(path.parent/'fixture.json')
        require(data['accepted'] and data['runner_exit']==0 and fixture['source_page']==page,'Current native UI failed')
        require(data['candidate_sha256']==managed.sha(candidate),'UI tested candidate differs')
        require(data['harness_unchanged'] and data['harness_sha256']==managed.sha(script),'UI harness differs')
        for key in ('source_files_unchanged','candidate_unchanged','all_owned_processes_closed',
                    'private_files_unchanged','all_private_images_closed'):
            require(data.get(key) is True,'Native guard missing: '+key)
        require(data['before']==data['after'] and data['before']['live_client']==managed.sha(managed.CLIENT),
                'Live sources changed')
        ui=data['ui']
        for key in ('accepted','desktop_unchanged','all_clients_closed','other_saved_rows_preserved','other_native_slots_preserved'):
            require(ui.get(key) is True,'UI guard missing: '+key)
        require([(e['slot'],e['quantity']) for e in ui['events']]==[(5,2),(5,5),(6,1)],'UI cases incomplete')
        for event in ui['events']:
            before,after=event['before'],event['after']
            count=before['count']-event['quantity']
            require(after['count']==count and after['db'][1]==count and
                after['db'][2]==before['db'][2]+1 and after['item']==(3107 if count else 0),'Wrong debit or projection')
        values.append(data)
    require(frozen.hashes()==read(frozen.BASELINE)['source_sha256'],'Frozen baseline changed')
    return {'accepted':True,'tw':values[0],'cn':values[1]}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('stage','apply'));args=parser.parse_args()
    lifecycle.ROUND=ROUND;lifecycle.DEPLOY=ROUND/'deployment';lifecycle.qualify=qualify
    info=lifecycle.stage(RECEIPTS[1]) if args.mode=='stage' else lifecycle.apply()
    print(json.dumps({k:info.get(k) for k in ('state','server_pid','saved_rows_preserved','candidate_sha256')}))
if __name__=='__main__':main()
