"""CUSTOM0073 executable-only release after original TW CP950/CP936 own-server proof."""
import argparse,json,re,shutil,subprocess,sys,time
import psutil
from pathlib import Path
from tools.operations import native_quest_catalog_release as managed
from tools.operations import packet_links_release_20260930 as snapshots
from tools.operations import stage_owned_mixed_bank_v06_20261003 as ports
from tools.operations import verify_frozen_chat_20260927 as frozen

ROOT=managed.ROOT
CONTRACT=ROOT/'artifacts/research/native-party-chat-0073/candidate-20261003/contract.json'
GATE=ROOT/'artifacts/research/native-party-chat-0073/release-gate.json'
STAGE=ROOT/'artifacts/releases/native-party-chat-20261003/deployment'
sha=managed.sha
read=snapshots.read
write=snapshots.write
require=snapshots.require

def qualify():
    gate=read(GATE)
    for name,digest in gate['file_sha256'].items():
        require(sha(ROOT/name)==digest,'Accepted release evidence changed: '+name)
    contract=read(CONTRACT);candidate=ROOT/contract['candidate_path']
    require(contract['design']=='CUSTOM-0073' and sha(candidate)==contract['candidate_sha256'],'Exact tested candidate required')
    require((contract['schema_before'],contract['schema_after'])==(47,47),'Executable-only schema47 release required')
    validation=read(ROOT/contract['validation'])
    require(validation['state']=='PASSED' and validation['sources_before']==validation['sources_after'] and len(validation['tests'])==46,
            'Actual unchanged-source46-test validation required')
    for command in validation['commands']:
        require(command['exit_code']==0 and sha((ROOT/contract['validation']).parent/command['log'])==command['log_sha256'],
                'Actual configure/build/CTest exit0 required')
    for name,digest in contract['source_sha256'].items():require(sha(ROOT/name)==digest,'Compiled runtime changed: '+name)
    run=read(ROOT/gate['run']);ui=run['ui']
    require(run['accepted'] is True and run['runner_exit']==0 and run['candidate_sha256']==contract['candidate_sha256'],
            'Actual original-client run missing')
    for key in ('source_files_unchanged','candidate_unchanged','all_owned_processes_closed','private_files_unchanged',
                'all_private_images_closed','party_harness_unchanged','frozen_party_harness_unchanged',
                'exclusive_2598_released','runtime_sources_unchanged','frozen_files_unchanged',
                'protected_processes_preserved','desktop_owner_unchanged'):
        require(run.get(key) is True,'Missing acceptance guard: '+key)
    require(run['owned_pid_count']==4 and all(ui.get(key) is True for key in
        ('accepted','desktop_unchanged','all_clients_closed','all_sql_rows_preserved','unrelated_saved_rows_preserved')),
        'UI/save/process acceptance incomplete')
    deliveries=ui['query_deliveries']
    require(len(deliveries)==8 and {(d['source'],d['role_direction'],d['ordinal']) for d in deliveries}==
        {(source,direction,ordinal) for source in (4,5) for direction in (1,2) for ordinal in (1,2)},'Eight both-role deliveries required')
    for d in deliveries:
        received,suppressed,expired=d['received'],d['suppressed'],d['expired'];coords=d['coordinate_domain']
        require(d['native_producer'] is True and d['native_consumer_binding'] is True and d['source_page'] in (950,936),
                'Actual native producer/consumer required')
        require(received['position']==[d['target'],coords['x'],coords['y']] and received['selected']==d['target'] and
            received['valid']==received['cooldown']==1 and received['binding']['text']==d['expected_label'],
            'Actual native56 selected label/position differs')
        require(suppressed['timestamp']==received['timestamp'] and suppressed['selected']==received['selected'] and
            suppressed['binding']['text']==received['binding']['text'] and expired['cooldown']==0 and
            expired['selected']==65535 and expired['position']==received['position'] and
            expired['binding']['text']==d['initial']['binding']['text'],'Native cooldown/timeout differs')
    proof=read(ROOT/contract['native_evidence'])
    require(sha(ROOT/contract['native_evidence'])==contract['native_evidence_sha256'] and
        proof['counts']=={'producer':24,'consumer':8,'dispatch':2,'current_dispatch':2,'current_consumer':8},
        'All44 native machine cases required')
    require(run['party_chat_native_proof_sha256']==contract['native_evidence_sha256'] and
        run['party_chat_native_proof_counts']==proof['counts'],'UI run must use exact native proof')
    party=ui['party_chat_deliveries'];normal=[d for d in party if d['hidden_recipient'] is None]
    require(len(normal)==8 and {(d['source'],d['role_direction'],d['ordinal']) for d in normal}==
        {(source,direction,ordinal) for source in (4,5) for direction in (1,2) for ordinal in (1,2)},
        'Eight real native party broadcasts required')
    require(sum(d['typed_input'].startswith('!') for d in normal)==4 and
        sum(d['producer_route']=='native selected UI39E00=1' for d in normal)==4,
        'Both actual prefix and selected-channel producers required')
    for delivery in party:
        require(delivery['native_edit_hex_before_submit']==delivery['typed_input'].encode('ascii').hex(),
            'Normal native edit must contain exact submitted text')
        require(delivery['native_channel']==1 and delivery['native_color']==0xff00 and
            delivery['bubble_fields_unchanged'] is True and delivery['bubbles_before']==delivery['bubbles_after'] and
            set(delivery['recipient_rings'])=={'4','5'},'Native party channel/no-bubble proof missing')
        for recipient,rings in delivery['recipient_rings'].items():
            require({r['ring'] for r in rings}=={'visible','archive'},'Both chat rings required')
            for ring in rings:
                expected=ring['ring']=='archive' or int(recipient)!=delivery['hidden_recipient']
                require(bool(ring['matched_rows'])==expected,'Party native filter/mask differs')
                for row in ring['matched_rows']:
                    require(row['color']==0xff00 and delivery['expected_name_prefix']+delivery['token'] in row['plain'],
                        'Owned sender prefix/native party color differs')
    chatlog=(ROOT/gate['run']).parent/'server.log'
    broadcasts=re.findall(rb'NATIVE_PARTY_CHAT_REQUEST session_id=(\d+) character_id=(\d+) messages=1 delivered=2 accepted=true CUSTOM-0073',chatlog.read_bytes())
    require(len(broadcasts)==len(party) and {int(row[1]) for row in broadcasts}=={4,5},
        'Actual Application party broadcast count differs')
    events=ui['events'];chats=[e for e in events if e['operation']=='chat']
    require(len(chats)==4 and {e['source'] for e in chats}=={4,5},'Both-client chat regression missing')
    for chat in chats:
        require(set(chat['native_rings'])=={'4','5'} and all({r['ring'] for r in rings}=={'visible','archive'}
            for rings in chat['native_rings'].values()),'Visible/archive chat proof missing')
    for operation,count in (('decline',2),('leave',2),('kick',2),('leader_disconnect',1)):
        require(sum(e['operation']==operation for e in events)==count,'Existing party lifecycle regression missing: '+operation)
    log=(ROOT/gate['run']).parent/'server.log'
    markers=re.findall(rb'NATIVE_PARTY_POSITION_QUERY session_id=(\d+) character_id=(\d+) target=(\d+) delivered=true CUSTOM-0072',log.read_bytes())
    require(len(markers)==8 and {int(row[1]) for row in markers}=={4,5},'Actual Application eight delivered markers required')
    require(sha(managed.CLIENT)==contract['client_sha256'] and frozen.hashes()==read(frozen.BASELINE)['source_sha256'],
            'Frozen client/chat changed')
    return contract

def stage():
    contract=qualify();require(not STAGE.exists(),'Release already staged; inspect its state')
    require(sha(managed.ACTIVE)==contract['predecessor_sha256'],'Installed predecessor changed')
    config=read(managed.CONFIG);database=Path(config['database']['path']).resolve()
    before=snapshots.capture(database);require([r[0] for r in before['history']]==list(range(1,48)),'Formal schema47 required')
    STAGE.mkdir(parents=True)
    managed.backup(database,STAGE/'accounts.before.db')
    require(snapshots.capture(STAGE/'accounts.before.db')==before,'Live saves changed during backup')
    managed.backup(STAGE/'accounts.before.db',STAGE/'town-diagnostic-accounts.db')
    clone=json.loads(json.dumps(config));clone['database']['path']=str(STAGE/'town-diagnostic-accounts.db')
    clone['logging']['file']=str(STAGE/'clone.log');clone['server'].update(host='127.0.0.1',port=0,character_port=0)
    write(STAGE/'clone-config.json',clone)
    candidate=ROOT/contract['candidate_path']
    for mode in ('--migrate-only','--run-for'):
        args=[str(candidate),'--config',str(STAGE/'clone-config.json'),mode]+(['1'] if mode=='--run-for' else [])
        with (STAGE/('clone-'+mode[2:]+'.log')).open('wb') as out:
            subprocess.run(args,cwd=ROOT,check=True,timeout=60,stdout=out,stderr=subprocess.STDOUT,creationflags=managed.FLAGS)
        require(snapshots.capture(STAGE/'town-diagnostic-accounts.db')==before,'Candidate changed any schema/save row')
    for source,name in ((managed.ACTIVE,'god2-server.before.exe'),(candidate,'god2-server.candidate.exe'),(managed.CONFIG,'server-config.before.json')):
        shutil.copy2(source,STAGE/name)
    info={'state':'STAGED','database':str(database),'candidate_sha256':contract['candidate_sha256'],
        'old_server_sha256':sha(managed.ACTIVE),'config_sha256':sha(managed.CONFIG),'client_sha256':sha(managed.CLIENT),
        'gate_sha256':sha(GATE),'helper_sha256':sha(Path(__file__)),'schema_before':47,'schema_after':47,'saved_rows_changed':0}
    write(STAGE/'release.json',info);return info

def apply():
    info=read(STAGE/'release.json');require(info['state']=='STAGED','Staged release required');qualify()
    require(sha(GATE)==info['gate_sha256'] and sha(Path(__file__))==info['helper_sha256'],'Staged gate/helper changed')
    require(sha(managed.ACTIVE)==info['old_server_sha256'] and sha(managed.CONFIG)==info['config_sha256'] and
        sha(managed.CLIENT)==info['client_sha256'] and sha(STAGE/'god2-server.candidate.exe')==info['candidate_sha256'],'Managed/staged files changed')
    subprocess.run([sys.executable,'-B','-m','tools.operations.verify_frozen_chat_20260927'],cwd=ROOT,check=True,creationflags=managed.FLAGS)
    pid=snapshots.managed_listener();first=ports.all_process_connections_idle(pid)
    database=Path(info['database']);managed.backup(database,STAGE/'accounts.at-install.db')
    before=snapshots.capture(STAGE/'accounts.at-install.db');require(snapshots.capture(database)==before,'Saves changed during fresh backup')
    second=ports.all_process_connections_idle(pid)
    require(first['process']==second['process'],'Managed process changed before install')
    write(STAGE/'all-port-idle.json',{'first':first,'second':second})
    snapshots.stop_idle(pid)
    try:
        require(snapshots.capture(database)==before,'Final server saves changed; retain candidate')
        snapshots.install_binary(STAGE/'god2-server.candidate.exe',info['candidate_sha256'])
        managed.start();new_pid=snapshots.wait_listener()
        require(sha(managed.ACTIVE)==info['candidate_sha256'] and sha(managed.CONFIG)==info['config_sha256'] and
            sha(managed.CLIENT)==info['client_sha256'],'Installed protected files differ')
        require(snapshots.capture(database)==before,'Startup changed any saved/schema row')
        process=ports.prior.formal_process_proof(new_pid)
        info.update(state='INSTALLED',server_pid=new_pid,installed_at=time.time(),saved_rows_preserved=True,
            formal_process=process,database_restored=False)
        write(STAGE/'release.json',info)
    except BaseException as error:
        owned=[p for p in psutil.process_iter(['exe']) if p.info['exe'] and
            Path(p.info['exe']).resolve()==managed.ACTIVE.resolve()]
        if owned:
            try:
                require(len(owned)==1,'Ambiguous managed recovery process')
                current=snapshots.managed_listener(allow_players=True)
                require(current==owned[0].pid,'Recovery process differs')
                ports.all_process_connections_idle(current);snapshots.stop_idle(current)
            except BaseException:
                info.update(state='RECOVERY_REQUIRES_IDLE_SERVER',error=str(error));write(STAGE/'release.json',info);raise
        snapshots.install_binary(STAGE/'god2-server.before.exe',info['old_server_sha256']);managed.start()
        info.update(state='ROLLED_BACK_EXECUTABLE_ONLY',error=str(error),database_restored=False);write(STAGE/'release.json',info);raise
    return info

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('qualify','stage','apply'))
    args=parser.parse_args()
    if args.mode=='qualify':qualify();result={'qualified':True}
    elif args.mode=='stage':result=stage()
    else:result=apply()
    print(json.dumps({key:result.get(key) for key in ('qualified','state','server_pid','saved_rows_preserved','candidate_sha256')}))
if __name__=='__main__':main()
