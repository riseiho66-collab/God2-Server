"""CUSTOM0075 gated guild-chat release; preserve every existing save row."""
import argparse,hashlib,json,re,shutil,subprocess,sys,time
from pathlib import Path
from tools.operations import native_quest_catalog_release as managed
from tools.operations import packet_links_release_20260930 as snapshots
from tools.operations import stage_owned_mixed_bank_v06_20261003 as ports
from tools.operations import verify_frozen_chat_20260927 as frozen
ROOT=managed.ROOT;sha=managed.sha;read=snapshots.read;write=snapshots.write;require=snapshots.require
CONTRACT=ROOT/'artifacts/research/native-guild-chat-0075/candidate-v02-20261003/contract.json'
GATE=ROOT/'artifacts/research/native-guild-chat-0075/release-gate.json'
STAGE=ROOT/'artifacts/releases/native-guild-chat-20261003/deployment'
TABLES={'owned_guilds','owned_guild_members'}
OBJECTS=TABLES|{'sqlite_autoindex_owned_guilds_1','owned_guild_member_audience','retain_owned_guild_generation'}
def schema_sql():
    text=(ROOT/'src/db/SqliteGuildRepository.cpp').read_text('utf-8')
    match=re.search(r'SqliteGuildRepository::schema\(\)\s*\{\s*return R"SQL\((.*?)\)SQL";',text,re.S)
    require(match is not None,'Exact guild schema source required');return match.group(1)
def schema_gate(before,after,template=None):
    require([r[0] for r in before['history']]==list(range(1,48)),'Formal schema47 required')
    require(not TABLES.intersection(before['tables']),'Guild tables already installed')
    require(after['pragmas']==before['pragmas'] and set(after['tables'])==set(before['tables'])|TABLES,'Unexpected table/pragma change')
    require([r for r in after['schema'] if r[1] not in OBJECTS]==before['schema'],'Existing schema changed')
    added=[r for r in after['schema'] if r[1] in OBJECTS]
    require(len(added)==len(OBJECTS) and {r[1] for r in added}==OBJECTS,'Exact new48 objects required')
    for name,rows in before['tables'].items():
        if name!='schema_migrations':require(after['tables'][name]==rows,'Existing saved rows changed: '+name)
    for name in TABLES:require(after['tables'][name]=={'rows':0,'sha256':hashlib.sha256(b'').hexdigest()},'Formal fixture/grant forbidden')
    require(after['history'][:-1]==before['history'] and len(after['history'])==48 and
        after['history'][-1][:3]==[48,'owned_guild_chat_membership',schema_sql()],'Migration history changed')
    if template is not None:require(after['schema']==template['schema'] and after['history'][-1][:3]==template['history'][-1][:3],'Installed48 differs from tested clone')
def qualify():
    gate=read(GATE)
    for name,digest in gate['file_sha256'].items():require(sha(ROOT/name)==digest,'Accepted evidence changed: '+name)
    c=read(CONTRACT);candidate=ROOT/c['candidate_path']
    require(c['design']=='CUSTOM-0075' and sha(candidate)==c['candidate_sha256'] and (c['schema_before'],c['schema_after'])==(47,48),'Exact tested guild candidate required')
    v=read(ROOT/c['validation'])
    require(v['state']=='PASSED' and v['sources_before']==v['sources_after'] and len(v['tests'])==53 and len(v['commands'])==4,'Actual unchanged53-test gate required')
    for cmd in v['commands']:require(cmd['exit_code']==0 and sha((ROOT/c['validation']).parent/cmd['log'])==cmd['log_sha256'],'Actual validation/log pin required')
    for name,digest in c['source_sha256'].items():require(sha(ROOT/name)==digest,'Compiled runtime changed: '+name)
    counts={'guild_name_update':10,'channel_selection':10,'producer':144,'consumer':80,'dispatch':4,'guild_clear_selected_lifecycle':2,'native_options_and_filter_controls':2}
    p=read(ROOT/c['native_evidence']);require(p['counts']==counts and sha(ROOT/c['native_evidence'])==c['native_evidence_sha256'],'Pinned252 native cases required')
    run=read(ROOT/gate['run']);ui=run['ui']
    require(run['accepted'] is True and run['runner_exit']==0 and run['candidate_sha256']==c['candidate_sha256'],'Actual original TW CP950/CP936 acceptance required')
    for key in ('source_files_unchanged','candidate_unchanged','all_owned_processes_closed','private_files_unchanged','all_private_images_closed',
        'guild_harness_unchanged','frozen_party_harness_unchanged','exclusive_2598_released','runtime_sources_unchanged','frozen_files_unchanged',
        'protected_processes_preserved','desktop_owner_unchanged'):
        require(run.get(key) is True,'Acceptance guard failed: '+key)
    require(run['owned_pid_count']==5 and all(ui.get(k) is True for k in
        ('accepted','desktop_unchanged','all_clients_closed','all_sql_rows_preserved','unrelated_saved_rows_preserved')),'UI/save/process acceptance incomplete')
    require(run['guild_chat_native_proof_sha256']==c['native_evidence_sha256'] and run['guild_chat_native_proof_counts']==counts,'Actual UI native pin differs')
    deliveries=ui['guild_chat_deliveries'];require(len(deliveries)==8,'Eight live guild sends required')
    require({d['source'] for d in deliveries if d['route']=='prefix'}=={4,5} and
        {d['source'] for d in deliveries if d['route']=='selected'}=={4,5},'Both native producers in both languages required')
    for d in deliveries:
        require(d['native_edit_hex_before_submit']==d['typed_input'].encode('ascii').hex() and d['source_page'] in (950,936),'Native edit input differs')
        require(d['native_channel']==3 and d['native_color']==0xffff00 and d['bubble_fields_unchanged'] is True and
            d['bubbles_before']==d['bubbles_after'] and set(d['recipient_rings'])=={'4','5'},'Native guild routing/no bubble differs')
        for recipient,rings in d['recipient_rings'].items():
            require({r['ring'] for r in rings}=={'visible','archive'},'Both native rings required')
            for ring in rings:
                expected=ring['ring']=='archive' or int(recipient)!=d['hidden_recipient']
                require(bool(ring['matched_rows'])==expected,'Guild filter differs')
                for row in ring['matched_rows']:require(row['color']==0xffff00 and d['expected'] in row['plain'],'Owned sender/body differs')
    require(len(ui['party_chat_deliveries'])==2 and len(ui['private_chat_deliveries'])==2 and
        len([e for e in ui['events'] if e['operation']=='chat'])==2,'Accepted common/party/private regressions required')
    require(ui['positions_before']==ui['positions_after'],'Chat changed positions')
    log=((ROOT/gate['run']).parent/'server.log').read_bytes()
    markers=re.findall(rb'NATIVE_GUILD_CHAT_REQUEST session_id=(\d+) character_id=(\d+) messages=1 delivered=2 accepted=true CUSTOM-0075',log)
    require(len(markers)==8 and {int(r[1]) for r in markers}=={4,5},'Eight actual server broadcasts required')
    require(re.search(rb'NATIVE_GUILD_CHAT_REQUEST .*character_id=4 .*delivered=0 accepted=false CUSTOM-0075',log),'Removed-member denial required')
    initial=re.findall(rb'OWNED_GUILD_NAME_PROJECTED session_id=\d+ character_id=(\d+) initial=true membership=true CUSTOM-0075',log)
    require(sorted(int(x) for x in initial)==[4,5,5],'Initial player projection must send guild2D without waiting for another tick')
    require(sha(managed.CLIENT)==c['client_sha256'] and frozen.hashes()==read(frozen.BASELINE)['source_sha256'],'Frozen client/chat changed')
    return c
def stage():
    c=qualify();require(not STAGE.exists(),'Release already staged')
    require(sha(managed.ACTIVE)==c['predecessor_sha256'],'Installed predecessor changed')
    config=read(managed.CONFIG);database=Path(config['database']['path']).resolve();before=snapshots.capture(database)
    STAGE.mkdir(parents=True);managed.backup(database,STAGE/'accounts.before.db')
    require(snapshots.capture(STAGE/'accounts.before.db')==before,'Saves changed during backup')
    managed.backup(STAGE/'accounts.before.db',STAGE/'town-diagnostic-accounts.db')
    clone=json.loads(json.dumps(config));clone['database']['path']=str(STAGE/'town-diagnostic-accounts.db')
    clone['logging']['file']=str(STAGE/'clone.log');clone['server'].update(host='127.0.0.1',port=0,character_port=0)
    write(STAGE/'clone-config.json',clone);candidate=ROOT/c['candidate_path'];template=None
    for mode in ('--migrate-only','--run-for'):
        args=[str(candidate),'--config',str(STAGE/'clone-config.json'),mode]+(['1'] if mode=='--run-for' else [])
        with (STAGE/('clone-'+mode[2:]+'.log')).open('wb') as out:
            subprocess.run(args,cwd=ROOT,check=True,timeout=60,stdout=out,stderr=subprocess.STDOUT,creationflags=managed.FLAGS)
        after=snapshots.capture(STAGE/'town-diagnostic-accounts.db');schema_gate(before,after,template);template=after
    require(snapshots.capture(database)==before and read(managed.CONFIG)==config,'Formal saves/config changed during clone test')
    write(STAGE/'accepted-schema48.json',template)
    for source,name in ((managed.ACTIVE,'god2-server.before.exe'),(candidate,'god2-server.candidate.exe'),(managed.CONFIG,'server-config.before.json')):shutil.copy2(source,STAGE/name)
    info={'state':'STAGED','database':str(database),'candidate_sha256':c['candidate_sha256'],'old_server_sha256':sha(managed.ACTIVE),
        'config_sha256':sha(managed.CONFIG),'client_sha256':sha(managed.CLIENT),'gate_sha256':sha(GATE),'helper_sha256':sha(Path(__file__)),
        'schema_before':47,'schema_after':48,'saved_rows_changed':0}
    write(STAGE/'release.json',info);return info
def apply():
    info=read(STAGE/'release.json');require(info['state']=='STAGED','Staged release required');qualify()
    require(sha(GATE)==info['gate_sha256'] and sha(Path(__file__))==info['helper_sha256'],'Staged gate/helper changed')
    require(sha(managed.ACTIVE)==info['old_server_sha256'] and sha(managed.CONFIG)==info['config_sha256'] and
        sha(managed.CLIENT)==info['client_sha256'] and sha(STAGE/'god2-server.candidate.exe')==info['candidate_sha256'],'Protected files changed')
    subprocess.run([sys.executable,'-B','-m','tools.operations.verify_frozen_chat_20260927'],cwd=ROOT,check=True,creationflags=managed.FLAGS)
    pid=snapshots.managed_listener();first=ports.all_process_connections_idle(pid)
    database=Path(info['database']);managed.backup(database,STAGE/'accounts.at-install.db');before=snapshots.capture(STAGE/'accounts.at-install.db')
    require(snapshots.capture(database)==before,'Saves changed during fresh backup');second=ports.all_process_connections_idle(pid)
    require(first['process']==second['process'],'Managed process changed');write(STAGE/'all-port-idle.json',{'first':first,'second':second})
    snapshots.stop_idle(pid)
    try:
        require(snapshots.capture(database)==before,'Final server saves changed')
        snapshots.install_binary(STAGE/'god2-server.candidate.exe',info['candidate_sha256'])
        with (STAGE/'formal-migration.log').open('wb') as out:
            subprocess.run([str(managed.ACTIVE),'--config',str(managed.CONFIG),'--migrate-only'],cwd=ROOT,check=True,timeout=60,
                stdout=out,stderr=subprocess.STDOUT,creationflags=managed.FLAGS)
        schema_gate(before,snapshots.capture(database),read(STAGE/'accepted-schema48.json'))
        managed.start();new_pid=snapshots.wait_listener();after=snapshots.capture(database)
        schema_gate(before,after,read(STAGE/'accepted-schema48.json'))
        require(sha(managed.ACTIVE)==info['candidate_sha256'] and sha(managed.CONFIG)==info['config_sha256'] and sha(managed.CLIENT)==info['client_sha256'],'Installed protected files differ')
        info.update(state='INSTALLED',server_pid=new_pid,installed_at=time.time(),saved_rows_preserved=True,database_restored=False,
            formal_process=ports.prior.formal_process_proof(new_pid))
        write(STAGE/'release.json',info)
    except BaseException as error:
        # The old schema47 executable cannot be run after a committed48. Retain
        # live saves and the candidate; never restore or downgrade the database.
        after=snapshots.capture(database)
        if after==before:
            snapshots.install_binary(STAGE/'god2-server.before.exe',info['old_server_sha256']);managed.start()
            state='ROLLED_BACK_EXECUTABLE_ONLY'
        else:state='RECOVERY_REQUIRES_SCHEMA48_CANDIDATE'
        info.update(state=state,error=str(error),database_restored=False);write(STAGE/'release.json',info);raise
    return info
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('qualify','stage','apply'));args=p.parse_args()
    if args.mode=='qualify':qualify();r={'qualified':True}
    else:r=stage() if args.mode=='stage' else apply()
    print(json.dumps({key:r.get(key) for key in ('qualified','state','server_pid','saved_rows_preserved','candidate_sha256')}))
if __name__=='__main__':main()
