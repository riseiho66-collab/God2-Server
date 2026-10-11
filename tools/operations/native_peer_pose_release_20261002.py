"""Promote the native pose route after actual isolated-client acceptance.

Executable-only release: clone/compare startup migrations, preserve all saves,
keep managed configuration and client files, and restore only the executable
on failure. Never restore an older database over current player state.
"""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
import subprocess
from tools.operations import native_quest_catalog_release as managed
from tools.operations import packet_links_release_20260930 as snapshots
from tools.operations import shunying_production_release as lifecycle
from tools.operations import verify_frozen_chat_20260927 as frozen

ROOT=managed.ROOT
ROUND=ROOT/'artifacts/releases/native-peer-pose-20261002'
DEPLOY=ROUND/'deployment'
CANDIDATE=ROOT/'build-town-visibility/Release/god2-server-native-results.exe'

def require(condition,message):
    if not condition:raise RuntimeError(message)
def read(path):return json.loads(Path(path).read_text('utf-8'))
def write(path,value):snapshots.write(path,value)
def now():return datetime.now(timezone.utc).isoformat()

def qualify(receipt_path):
    data=read(receipt_path)
    require(data.get('accepted') is True and data.get('runner_exit')==0,'Native client run did not pass')
    require(data.get('candidate_sha256')==managed.sha(CANDIDATE),'Tested candidate differs')
    for key in ('source_files_unchanged','candidate_unchanged','all_owned_processes_closed',
                'private_files_unchanged','all_private_images_closed','pose_harness_unchanged'):
        require(data.get(key) is True,'Missing native acceptance guard: '+key)
    require(data.get('before')==data.get('after') and data['before']['live_client']==managed.sha(managed.CLIENT),
            'Current client differs from tested client')
    script=ROOT/'tools/strike_lab/private_peer_pose_20261002.py'
    require(data.get('pose_harness_sha256')==managed.sha(script),'Native test source changed')
    ui=data['ui']
    for key in ('accepted','desktop_unchanged','all_clients_closed','saved_preserved'):
        require(ui.get(key) is True,'Missing native worker proof: '+key)
    events=ui['events'];require([(e['sender'],e['mode']) for e in events]==
        [(4,1),(4,2),(4,3),(5,1),(5,2),(5,3),(4,2),(4,1)],'Incomplete native two-way mode coverage')
    for event in events:
        mode=event['mode'];own,peer=event['self'],event['peer']
        require(own['state']==15+mode and own['packed']>>3==mode,'Native local state mismatch')
        require(peer['mode']==mode and peer['movement']==15+mode and
                peer['direction']==own['packed']&7 and peer.get('render_actions'),
                'Native peer animation/renderer mismatch')
    require(ui['late_observer']['peer']['mode']==2 and ui['late_observer']['peer']['movement']==17,
            'Native late observer pose missing')
    require(ui['expired_one_shot_observer']['mode']==0 and
            ui['expired_one_shot_observer']['movement']==0 and ui.get('one_shot_completed'),
            'Native one-shot lifetime not accepted')
    require(ui.get('movement'),'Native movement after pose missing')
    gate=read(ROUND/'manifest.json')
    require(gate['candidate_sha256']==managed.sha(CANDIDATE),'Automated gate candidate differs')
    for name,digest in gate['source_sha256'].items():
        require(managed.sha(ROOT/name)==digest,'Automated tested source changed: '+name)
    require(gate['verification']['native_consumer_cases']=={'passed':48,'total':48} and
            gate['verification']['tcp_cases']['passed']==5 and gate['verification']['frozen_chat_passed'],
            'Incomplete automated gate')
    require(frozen.hashes()==read(frozen.BASELINE)['source_sha256'],'Frozen chat baseline differs')
    return data

def stage(receipt_path):
    native=qualify(receipt_path)
    require(not DEPLOY.exists(),'Deployment already staged; inspect its state')
    managed.listener()
    config=read(managed.CONFIG);database=Path(config['database']['path'])
    before=snapshots.capture(database)
    DEPLOY.mkdir()
    managed.backup(database,DEPLOY/'accounts.before.db')
    managed.backup(DEPLOY/'accounts.before.db',DEPLOY/'town-diagnostic-accounts.db')
    require(snapshots.capture(DEPLOY/'accounts.before.db')==before,'Live save changed while staging')
    cfg=json.loads(json.dumps(config));cfg['database']['path']=str(DEPLOY/'town-diagnostic-accounts.db')
    cfg['logging']['file']=str(DEPLOY/'stage-migration.log')
    write(DEPLOY/'stage-config.json',cfg)
    subprocess.run([str(CANDIDATE),'--config',str(DEPLOY/'stage-config.json'),'--migrate-only'],
        cwd=ROOT,check=True,capture_output=True,creationflags=managed.FLAGS)
    require(snapshots.capture(DEPLOY/'town-diagnostic-accounts.db')==before,'Candidate startup changes schema or saved rows')
    shutil.copy2(managed.ACTIVE,DEPLOY/'god2-server.before.exe')
    shutil.copy2(CANDIDATE,DEPLOY/'god2-server.candidate.exe')
    shutil.copy2(managed.CONFIG,DEPLOY/'server-config.before.json')
    write(DEPLOY/'save-snapshot.before.json',before)
    write(DEPLOY/'native-client-receipt.json',native)
    info={'state':'STAGED','time':now(),'database':str(database),
        'candidate_sha256':managed.sha(CANDIDATE),'old_server_sha256':managed.sha(managed.ACTIVE),
        'config_sha256':managed.sha(managed.CONFIG),'client_sha256':managed.sha(managed.CLIENT),
        'receipt':str(Path(receipt_path).resolve()),'migration_or_saved_row_changes':0}
    write(DEPLOY/'release.json',info)
    return info

def apply():
    info=read(DEPLOY/'release.json');require(info['state']=='STAGED','Staged release required')
    qualify(info['receipt'])
    subprocess.run([__import__('sys').executable,'-B','-m','tools.operations.verify_frozen_chat_20260927'],
                   cwd=ROOT,check=True)
    require(managed.sha(managed.ACTIVE)==info['old_server_sha256'] and
            managed.sha(managed.CONFIG)==info['config_sha256'] and
            managed.sha(managed.CLIENT)==info['client_sha256'],'Managed files changed; retain staged candidate')
    require(managed.sha(DEPLOY/'god2-server.candidate.exe')==info['candidate_sha256'],'Staged candidate changed')
    database=Path(info['database']);before=read(DEPLOY/'save-snapshot.before.json')
    require(snapshots.capture(database)==before,'Saves changed since staging; retain candidate')
    pid=managed.listener()
    managed.powershell(f"if(@(Get-NetTCPConnection -OwningProcess {pid} -State Established -ErrorAction SilentlyContinue).Count){{throw 'Player connected; retain staged candidate'}}")
    lifecycle.stop_managed_and_wait(pid)
    try:
        require(snapshots.capture(database)==before,'Saves changed while stopping; retain candidate')
        shutil.copy2(DEPLOY/'god2-server.candidate.exe',managed.ACTIVE)
        managed.start()
        managed.powershell("$deadline=(Get-Date).AddSeconds(20); do {Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)} while(-not $rows.Count -and (Get-Date) -lt $deadline); if($rows.Count -ne 1){throw 'Managed listener not ready'}")
        info['server_pid']=managed.listener(allow_players=True)
        require(managed.sha(managed.ACTIVE)==info['candidate_sha256'],'Installed executable mismatch')
        require(snapshots.capture(database)==before,'Startup unexpectedly changed saved state')
        require(managed.sha(managed.CONFIG)==info['config_sha256'] and
                managed.sha(managed.CLIENT)==info['client_sha256'],'Config or client changed')
        info.update(state='INSTALLED',installed_at=now(),saved_rows_preserved=True)
        write(DEPLOY/'release.json',info)
    except BaseException as error:
        try:lifecycle.stop_managed_and_wait(managed.listener(allow_players=True))
        except Exception:pass
        shutil.copy2(DEPLOY/'god2-server.before.exe',managed.ACTIVE)
        managed.start()
        info.update(state='ROLLED_BACK_EXECUTABLE_ONLY',error=str(error),database_restored=False)
        write(DEPLOY/'release.json',info)
        raise
    return info

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('stage','apply'))
    parser.add_argument('--receipt',type=Path);args=parser.parse_args()
    if args.mode=='stage':
        if args.receipt is None:parser.error('--receipt required')
        result=stage(args.receipt)
    else:result=apply()
    print(json.dumps({k:result.get(k) for k in ('state','server_pid','saved_rows_preserved','candidate_sha256')}))
if __name__=='__main__':main()
