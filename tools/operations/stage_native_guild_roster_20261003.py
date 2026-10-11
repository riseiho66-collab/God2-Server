"""CUSTOM0076 read-only roster release, schema48 unchanged, no fixture grants."""
import argparse,json,shutil,subprocess,sys,time
from pathlib import Path
import psutil
from tools.operations import native_quest_catalog_release as managed
from tools.operations import packet_links_release_20260930 as snapshots
from tools.operations import stage_owned_mixed_bank_v06_20261003 as ports
from tools.operations import verify_frozen_chat_20260927 as frozen
ROOT=managed.ROOT;sha=managed.sha;read=snapshots.read;write=snapshots.write;require=snapshots.require
HERE=ROOT/'artifacts/research/native-guild-roster-0076'
STAGE=ROOT/'artifacts/releases/native-guild-roster-20261003/deployment'
CANDIDATE=ROOT/'build-native-guild-roster-20261003/Release/god2-server.exe'
def qualify():
    validation=read(HERE/'runtime-validation-v04.json')
    require(validation['state']=='PASSED' and validation['before']==validation['after'],'Compiled unchanged runtime required')
    for path,digest in validation['after'].items():require(sha(ROOT/path)==digest,'Compiled source changed: '+path)
    for command in validation['commands']:require(command['exit']==0 and sha(HERE/command['log'])==command['sha256'],'Build/test/frozen proof changed')
    require(sha(CANDIDATE)==validation['candidate_sha256'],'Exact tested candidate required')
    contract=read(HERE/'live-contract-v01.json')
    # Documentation is reconciled after acceptance. Runtime/Lua/assets/tests and
    # frozen helpers remain pinned to the actual live compiled source closure.
    for path,digest in contract['source_sha256'].items():
        if not path.startswith('docs/'):require(sha(ROOT/path)==digest,'Live runtime closure changed: '+path)
    native=read(HERE/'native-runtime-v01.json');require(native['case_count']==24,'Native24-case proof required')
    tcp=read(HERE/'tcp-v02.json');require(tcp['state']=='PASSED' and tcp['exit']==0 and tcp['candidate_sha256']==sha(CANDIDATE),'ActualTCP proof required')
    require(sha(ROOT/'tests/research/test_native_guild_roster_server_20261003.py')==tcp['test_sha256'] and sha(HERE/'tcp-v02.log')==tcp['log_sha256'],'TCP source/log changed')
    run=read(ROOT/'artifacts/playtests/private-native-guild-roster-20261003-01/run-result.json');ui=run['ui']
    require(run['accepted'] and run['candidate_sha256']==sha(CANDIDATE) and run['runner_exit']==0,'TW/CN live acceptance required')
    for key in ('source_files_unchanged','candidate_unchanged','all_owned_processes_closed','private_files_unchanged','all_private_images_closed','runtime_sources_unchanged','frozen_files_unchanged','protected_processes_preserved','desktop_owner_unchanged','exclusive_2598_released'):
        require(run.get(key) is True,'Live guard missing: '+key)
    events=ui['native_roster_cache_events'];require(len(events)==5,'Five original-client cache observations required')
    require({(e['identity'],e['stage'],e['count']) for e in events}=={(4,'initial',50),(5,'initial',50),(4,'membership_removed',0),(4,'membership_restored',50),(5,'relogin',50)},'Native complete cache/leave/relogin proof differs')
    require({e['page'] for e in events}=={950,936},'Both client languages required')
    require(ui['all_sql_rows_preserved'] and ui['desktop_unchanged'] and ui['all_clients_closed'],'Saved data/desktop cleanup failed')
    require(len(ui['guild_chat_deliveries'])==8 and len(ui['party_chat_deliveries'])==2 and len(ui['private_chat_deliveries'])==2 and len([e for e in ui['events'] if e['operation']=='chat'])==2,'Frozen-channel client regressions missing')
    require(frozen.hashes()==read(frozen.BASELINE)['source_sha256'] and sha(managed.CLIENT)==native['client_sha256'],'Frozen client/chat differs')
    return validation
def stage():
    qualify();require(not STAGE.exists(),'Release namespace already exists')
    config=read(managed.CONFIG);database=Path(config['database']['path']).resolve();before=snapshots.capture(database)
    require([r[0] for r in before['history']]==list(range(1,49)),'Installed schema48 required')
    STAGE.mkdir(parents=True);managed.backup(database,STAGE/'accounts.before.db')
    require(snapshots.capture(STAGE/'accounts.before.db')==before,'Consistent save backup required')
    managed.backup(STAGE/'accounts.before.db',STAGE/'town-diagnostic-accounts.db')
    clone=json.loads(json.dumps(config));clone['database']['path']=str(STAGE/'town-diagnostic-accounts.db')
    clone['logging']['file']=str(STAGE/'clone.log');clone['server'].update(host='127.0.0.1',port=0,character_port=0)
    write(STAGE/'clone-config.json',clone)
    for args,label in ((['--migrate-only'],'migrate'),(['--run-for','1'],'startup')):
        with (STAGE/('clone-'+label+'.log')).open('wb') as stream:
            subprocess.run([str(CANDIDATE),'--config',str(STAGE/'clone-config.json')]+args,cwd=ROOT,check=True,timeout=60,stdout=stream,stderr=subprocess.STDOUT,creationflags=managed.FLAGS)
        require(snapshots.capture(STAGE/'town-diagnostic-accounts.db')==before,'Read-only release changed schema/saved rows')
    require(snapshots.capture(database)==before,'Formal saves changed during staging')
    for source,name in ((managed.ACTIVE,'god2-server.before.exe'),(CANDIDATE,'god2-server.candidate.exe'),(managed.CONFIG,'server-config.before.json')):shutil.copy2(source,STAGE/name)
    info={'state':'STAGED','database':str(database),'candidate_sha256':sha(CANDIDATE),'old_server_sha256':sha(managed.ACTIVE),'config_sha256':sha(managed.CONFIG),'client_sha256':sha(managed.CLIENT),'helper_sha256':sha(Path(__file__)),'schema_before':48,'schema_after':48,'saved_rows_changed':0,'scope':'Native91/92 complete cache and B8 notification only; initial8E panel remains open.'}
    write(STAGE/'release.json',info);return info
def listener_wait():
    # Same managed task, with a bounded60s wait for its actual dynamic second
    # listener. Never infer a fixed character port from config character_port0.
    deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        for process in psutil.process_iter(['exe']):
            if process.info['exe'] and Path(process.info['exe']).resolve()==managed.ACTIVE.resolve():
                connections=process.net_connections(kind='tcp')
                listeners=[(c.laddr.ip,c.laddr.port) for c in connections if c.status=='LISTEN']
                if len(listeners)==2 and ('127.0.0.1',2592) in listeners and all(ip=='127.0.0.1' for ip,p in listeners):
                    ports.prior.formal_process_proof(process.pid);return process.pid,sorted(listeners)
        time.sleep(.5)
    raise RuntimeError('Managed process/listeners not ready after60s')
def apply():
    qualify();info=read(STAGE/'release.json');require(info['state']=='STAGED','Staged release required')
    require(sha(Path(__file__))==info['helper_sha256'] and sha(managed.ACTIVE)==info['old_server_sha256'] and sha(managed.CONFIG)==info['config_sha256'] and sha(managed.CLIENT)==info['client_sha256'],'Protected release files changed')
    subprocess.run([sys.executable,'-B','-m','tools.operations.verify_frozen_chat_20260927'],cwd=ROOT,check=True,creationflags=managed.FLAGS)
    pid=snapshots.managed_listener();first=ports.all_process_connections_idle(pid)
    database=Path(info['database']);managed.backup(database,STAGE/'accounts.at-install.db');before=snapshots.capture(STAGE/'accounts.at-install.db')
    require(snapshots.capture(database)==before,'Fresh save snapshot required');second=ports.all_process_connections_idle(pid)
    require(first['process']==second['process'],'Managed owner changed');write(STAGE/'all-port-idle.json',{'first':first,'second':second})
    snapshots.stop_idle(pid)
    try:
        require(snapshots.capture(database)==before,'Saved state changed before install')
        snapshots.install_binary(STAGE/'god2-server.candidate.exe',info['candidate_sha256'])
        managed.start();new_pid,listeners=listener_wait()
        require(snapshots.capture(database)==before,'Read-only candidate changed formal saves')
        require(sha(managed.ACTIVE)==info['candidate_sha256'] and sha(managed.CONFIG)==info['config_sha256'] and sha(managed.CLIENT)==info['client_sha256'],'Installed protected files differ')
        info.update(state='INSTALLED',server_pid=new_pid,listeners=listeners,installed_at=time.time(),saved_rows_preserved=True,database_restored=False,formal_process=ports.prior.formal_process_proof(new_pid))
    except BaseException as error:
        # Schema48 is unchanged. Preserve live data; never restore player DB.
        info.update(state='INSTALL_REQUIRES_INSPECTION',error=str(error),database_restored=False);write(STAGE/'release.json',info);raise
    write(STAGE/'release.json',info);return info
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('qualify','stage','apply'));args=p.parse_args()
    result={'qualified':bool(qualify())} if args.mode=='qualify' else stage() if args.mode=='stage' else apply()
    print(json.dumps(result))
if __name__=='__main__':main()
