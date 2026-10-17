# Legacy receipt identifiers retain their schema spelling; both cases are the
# Taiwan client using Traditional CP950 or Simplified CP936, not regional protocols.
"""Exact executable-only promotion, using existing save-preserving lifecycle."""
import argparse,json
from pathlib import Path
from tools.operations import native_peer_pose_release_20261002 as lifecycle
from tools.operations import native_quest_catalog_release as managed
from tools.operations import verify_frozen_chat_20260927 as frozen

ROOT=managed.ROOT;ROUND=ROOT/'artifacts/releases/native-options-1d-20261002'
RECEIPTS=[ROOT/'artifacts/playtests/private-options-1d-20261002-02/run-result.json',
          ROOT/'artifacts/playtests/private-options-1d-20261002-03/run-result.json']
def read(path):return json.loads(path.read_text('utf-8'))
def require(ok,message):
    if not ok:raise RuntimeError(message)
def worker_source(path):return path.read_text('utf-8').split('def worker(args):',1)[1].split('\ndef main():',1)[0]
def qualify(_receipt=None):
    candidate=lifecycle.CANDIDATE;gate=read(ROUND/'manifest.json')
    require(gate['candidate_sha256']==managed.sha(candidate),'Gate candidate changed')
    for name,digest in gate['source_sha256'].items():require(managed.sha(ROOT/name)==digest,'Source changed: '+name)
    require(gate['verification']=={'tcp_cases':4,'cpp_targets':3,'inventory_cases':1,
        'native_producer_cases':20,'frozen_chat_passed':True},'Automated gate incomplete')
    script=ROOT/'tools/strike_lab/private_options_1d_20261002.py'
    require(worker_source(script)==worker_source(ROUND/'private-options-tw-tested.py'),'TW tested UI worker changed')
    values=[]
    for page,path in zip((950,936),RECEIPTS):
        data=read(path);fixture=read(path.parent/'fixture.json')
        require(data['accepted'] and data['runner_exit']==0 and fixture['source_page']==page,'Native receipt failed')
        require(data['candidate_sha256']==managed.sha(candidate),'Native tested binary differs')
        for key in ('source_files_unchanged','candidate_unchanged','all_owned_processes_closed',
                    'private_files_unchanged','all_private_images_closed'):
            require(data.get(key) is True,'Native invariant missing: '+key)
        require(data['before']==data['after'] and data['before']['live_client']==managed.sha(managed.CLIENT),
                'Native client/config/fixture changed')
        ui=data['ui'];require(ui['accepted'] and ui['desktop_unchanged'] and ui['all_clients_closed'],'UI guard failed')
        expected=[(index,mask) for index,mask in ((4,1),(5,4),(6,2),(7,8),(8,0x100)) for _ in range(2)]
        require([(e['control'],e['mask']) for e in ui['events']]==expected,'Incomplete UI option coverage')
        for event in ui['events']:require(event['after']==event['before']^event['mask'],'Wrong native toggle')
        require(ui['events'][-1]['after']==ui['original_flags'],'Option bits not restored')
        if page==936:require(data.get('harness_unchanged') and data['harness_sha256']==managed.sha(script),'TW CP936 harness changed')
        values.append(data)
    require(frozen.hashes()==read(frozen.BASELINE)['source_sha256'],'Frozen chat baseline changed')
    return {'accepted':True,'tw':values[0],'cn':values[1]}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('stage','apply'));args=parser.parse_args()
    # Reuse the tested lifecycle only in this process; do not edit the older
    # release or its manifest. Qualification above belongs to this new route.
    lifecycle.ROUND=ROUND;lifecycle.DEPLOY=ROUND/'deployment';lifecycle.qualify=qualify
    info=lifecycle.stage(RECEIPTS[1]) if args.mode=='stage' else lifecycle.apply()
    print(json.dumps({key:info.get(key) for key in ('state','server_pid','saved_rows_preserved','candidate_sha256')}))
if __name__=='__main__':main()
