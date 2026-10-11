"""Bounded owner for one isolated server and two native visibility probes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import sqlite3
from contextlib import closing

import psutil
from lab import HOME,CLIENT,PROFILES,profile_context,write_json
from shared_cpp_server import SharedCppServer
from current_skill_hotbar_fixture import isolated_hotbar


def stop_owned(process):
    if process.poll() is not None:return
    try:children=psutil.Process(process.pid).children(recursive=True)
    except psutil.NoSuchProcess:children=[]
    for child in reversed(children):
        try:child.terminate()
        except psutil.NoSuchProcess:pass
    process.terminate()
    try:process.wait(timeout=10)
    except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
    _,alive=psutil.wait_procs(children,timeout=5)
    for child in alive:
        try:child.kill()
        except psutil.NoSuchProcess:pass
    psutil.wait_procs(alive,timeout=5)


def wait_catalog_ready(child,name,timeout=90):
    # Native decompression uses cwd/tmp/tmp.N: serialize shared-copy startup.
    path=HOME/'artifacts/runs'/name/'catalog-ready.json'
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if child.poll() is not None:raise RuntimeError('Native client ended before catalog readiness')
        if path.exists():
            ready=json.loads(path.read_text())
            descendants={process.pid for process in psutil.Process(child.pid).children(recursive=True)}
            if (ready.get('run_id')!=name or ready.get('client_pid') not in descendants or
                ready.get('stage')!='FIRST_BIND' or ready.get('count')!=144 or not ready.get('table')):
                raise ValueError('Native catalog readiness ownership/state mismatch')
            return ready
        time.sleep(.1)
    raise TimeoutError('Native catalog readiness deadline')


def restore_copy(source,target):
    source=Path(source).resolve(strict=True)
    if not source.is_relative_to((HOME/'artifacts/runs').resolve()) or source.name!='player-visibility-diagnostic.db':
        raise ValueError('Restore requires isolated shared visibility evidence')
    report=json.loads((source.parent/'shared-result.json').read_text())
    if report.get('result')!='TWO_NATIVE_PLAYER_POOLS_OBSERVED' or not report.get('simultaneous_movement'):
        raise ValueError('Restore requires qualified two-player movement')
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as original:
        rows=original.execute('select * from recovered_positions order by character_id').fetchall()
        if len(rows)!=2 or any(tuple(row[1:])!=(2,15,18,12,3) for row in rows):
            raise ValueError('Restore source positions differ')
        if original.execute('pragma integrity_check').fetchall()!=[('ok',)]:raise ValueError('Source integrity failed')
        with closing(sqlite3.connect(target)) as destination:original.backup(destination)
    return dict(path=str(source),sha256=digest,positions=rows)


def reconnect_pair(run,manifest,commands,server,timeout,clients,logs):
    folder=run/'reconnect';folder.mkdir()
    document=json.loads(manifest.read_text())
    peers={str(i):run.name+f'-again{i}' for i in (0,1)}
    document['peers']=peers
    next_manifest=folder/'shared-server.json';write_json(next_manifest,document)
    attachment=SharedCppServer(next_manifest,HOME)
    attachment.verify_client_profile(CLIENT)
    started=[]
    for peer,original in enumerate(commands):
        command=list(original)
        command[command.index('--run-id')+1]=peers[str(peer)]
        command[command.index('--shared-server-manifest')+1]=str(next_manifest)
        log=(folder/f'peer-{peer}-stdout.log').open('xb');logs.append(log)
        child=subprocess.Popen(command,cwd=HOME,stdout=log,stderr=subprocess.STDOUT,
                               creationflags=subprocess.CREATE_NO_WINDOW)
        started.append(child);clients.append(child)
        wait_catalog_ready(child,peers[str(peer)])
    released=False;until=time.monotonic()+timeout+10
    while time.monotonic()<until:
        if server.poll() is not None or attachment.process.poll() is not None:
            raise RuntimeError('Original shared server stopped during reconnect')
        paths=[folder/f'peer-{i}-visible.json' for i in (0,1)]
        if not released and all(p.exists() for p in paths):
            samples=[json.loads(p.read_text()) for p in paths]
            if samples[0]['client_pid']==samples[1]['client_pid']:raise ValueError('Reconnect requires distinct clients')
            for i,sample in enumerate(samples):
                before=json.loads((run/f'peer-{i}-visible.json').read_text())
                if (sample['run_id']!=peers[str(i)] or sample['local_identity']!=before['local_identity'] or
                        sample['sample']['entries'][0]['identity']!=samples[1-i]['local_identity']):
                    raise ValueError('Reconnect role identity mismatch')
            write_json(folder/'release-visible.json',{'peers':peers});released=True
        if not released and any(p.poll() is not None for p in started):raise RuntimeError('Reconnect exited before visibility')
        if all(p.poll() is not None for p in started):break
        time.sleep(.1)
    else:raise TimeoutError('Native reconnect deadline')
    for name in peers.values():
        report=json.loads((HOME/'artifacts/runs'/name/'run.json').read_text())
        if report.get('result')!='NATIVE_SHARED_PLAYER_VISIBILITY_OBSERVED' or report.get('error'):
            raise RuntimeError('Native reconnect observer rejected')
    if not released:raise ValueError('Reconnect barrier missing')
    attachment.verify_client_profile(CLIENT)
    return dict(peers=peers,server_pid=document['pid'],server_create_time=document['create_time'],
                client_pids=[s['client_pid'] for s in samples])


def checkpoint_rows(database):
    with closing(sqlite3.connect(database)) as db:
        return {table:db.execute('select * from '+table).fetchall() for table in
                ('battle_checkpoints','character_resources','battle_reservations','battle_settlements')}


def server_listeners(server):
    process=psutil.Process(server.pid)
    until=time.monotonic()+5
    while time.monotonic()<until:
        if server.poll() is not None:raise RuntimeError('Shared server exited during startup')
        ports=[c.laddr.port for c in process.net_connections(kind='tcp') if c.status==psutil.CONN_LISTEN]
        if len(ports)==2 and 2592 in ports:return process,ports
        time.sleep(.05)
    raise RuntimeError('Shared listeners not ready')


def run(name,timeout,observe_departure=False,observe_movement=False,simultaneous_movement=False,restore_database=None,reconnect=False,held_reconnect=False,observe_battle=False,post_battle_movement=False,persist_battle=False,checkpoint_battle=False,checkpoint_reconnect=False,terminal_reconnect=False,skill_battle=False,skill_reconnect=False,server_restart=False):
    if server_restart and not skill_reconnect:raise ValueError('Server restart requires skill reconnect')
    if skill_reconnect and (not skill_battle or checkpoint_reconnect or terminal_reconnect):
        raise ValueError('Skill reconnect requires independent skill battle')
    if skill_battle and (not checkpoint_battle or checkpoint_reconnect or terminal_reconnect):
        raise ValueError('Skill battle requires independent checkpoint battle')
    if skill_reconnect:checkpoint_reconnect=True
    if terminal_reconnect and (not checkpoint_battle or checkpoint_reconnect):raise ValueError('Choose one checkpoint disconnect phase')
    if checkpoint_reconnect and not checkpoint_battle:raise ValueError('Checkpoint reconnect requires checkpoint battle')
    if checkpoint_battle and not persist_battle:raise ValueError('Checkpoint battle requires persistent battle')
    if persist_battle and not observe_battle:raise ValueError('Persistent battle requires battle mode')
    if post_battle_movement and not observe_battle:raise ValueError('Post-battle movement requires battle mode')
    if observe_battle and any((observe_departure,observe_movement,simultaneous_movement,restore_database,reconnect,held_reconnect)):
        raise ValueError('Battle visibility requires a fresh independent run')
    observe_movement=observe_movement or simultaneous_movement
    if observe_departure and observe_movement:raise ValueError('Choose one lifecycle probe')
    if restore_database and (observe_departure or observe_movement):raise ValueError('Restore is a stationary acceptance run')
    if reconnect and not restore_database:raise ValueError('Reconnect requires qualified saved two-player positions')
    if held_reconnect:
        if restore_database or reconnect or observe_movement or observe_departure:raise ValueError('Held reconnect requires a fresh independent run')
        observe_departure=True
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,45}',name):raise ValueError('Bounded run ID required')
    run=HOME/'artifacts/runs'/name
    run.mkdir(exist_ok=False)
    peers={str(i):f'{name}-peer{i}' for i in (0,1)}
    settings=json.loads((HOME/'config/recovered-movement.json').read_text())
    settings['database']['path']=str(run/'player-visibility-diagnostic.db')
    settings['logging']['file']=str(run/'server.log')
    settings['lua'].update(bootstrap=str(HOME/'scripts/bootstrap.lua'),script_root=str(HOME/'scripts'),hot_reload=False)
    settings['development']['recovered_navigation']=str(HOME/'artifacts/world-atlas/indoor-2-15.json')
    settings['development'].update(diagnostic_player_visibility=True,diagnostic_remote_actor_language=0)
    if observe_battle:
        for flag in ('diagnostic_visibility_battle','diagnostic_battle_transition','diagnostic_battle_participants',
                     'diagnostic_battle_player_appearance','diagnostic_battle_animations','diagnostic_battle_terminal'):
            settings['development'][flag]=True
        settings['development']['diagnostic_battle_resources']=persist_battle
        settings['development']['diagnostic_visibility_checkpoint']=checkpoint_battle
        if skill_battle:
            settings['development'].update(diagnostic_visibility_skill_recovery=True,
                diagnostic_battle_skill_seed=True,diagnostic_battle_skill_settlement=True,diagnostic_battle_rounds=3)
    config=run/'config.json';write_json(config,settings)
    server=None;clients=[];logs=[]
    result={'result':'FAILED','world_accepted':False,'peers':peers}
    try:
        restored=restore_copy(restore_database,Path(settings['database']['path'])) if restore_database else None
        if restored:result['restored_source']=restored
        with (run/'server-stdout.log').open('xb') as server_log:
            server=subprocess.Popen([str(HOME/'build/Release/god2-server.exe'),'--config',str(config),
                '--run-for',str(timeout*(2 if reconnect or checkpoint_reconnect or terminal_reconnect else 1)+60)],cwd=HOME,stdout=server_log,stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW)
            process,ports=server_listeners(server)
            with profile_context(PROFILES[2],CLIENT,run),isolated_hotbar(CLIENT,run,skill_battle):
                manifest=run/'shared-server.json'
                write_json(manifest,dict(schema='god2-shared-loopback-server-v1',pid=server.pid,
                    create_time=process.create_time(),config=str(config),
                    config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),ports=ports,peers=peers,
                    observe_departure=observe_departure,
                    observe_battle=observe_battle,
                    post_battle_movement=post_battle_movement,
                    persist_battle=persist_battle,
                    checkpoint_battle=checkpoint_battle,
                    skill_battle=skill_battle,
                    hold_pre_action_disconnect=checkpoint_reconnect and not skill_reconnect,
                    hold_skill_disconnect=skill_reconnect,
                    hold_terminal_disconnect=terminal_reconnect,
                    held_reconnect=held_reconnect,
                    observe_movement=observe_movement,
                    simultaneous_movement=simultaneous_movement,
                    restored_source=restored,
                    client_profile=dict(root=str(CLIENT),sha256={name:hashlib.sha256((CLIENT/name).read_bytes()).hexdigest()
                        for name in ('config/display.settings','ctserver.ini','ddraw.ini')})))
                SharedCppServer(manifest,HOME).verify_client_profile(CLIENT)
                flags=('zero-ui-prefix warning-input-trace auto-pagefile-capacity taiwan-resource-locale '
                       'network-strike cpp-server post-seed c2s-strike s2c0003 login-terminal server-list '
                       'legacy-character-list-candidate recovered-account-auth recovered-character-create '
                       'recovered-dual-connection recovered-world-entry isolated-database movement-lab '
                       'observe-login-entry probe-login-command probe-login-panel probe-login-submit '
                       'probe-server-confirm observe-character-create probe-character-create observe-created-refresh '
                       'probe-character-select observe-world-entry observe-world-loop observe-world-frames').split()
                try:
                    commands=[]
                    for peer in (0,1):
                        log=(run/f'peer-{peer}-stdout.log').open('xb');logs.append(log)
                        command=[sys.executable,str(HOME/'tools/strike_lab/apex.py'),'God2CompatHost',
                            '--mode','MODE_COMPAT','--run-id',peers[str(peer)],'--timeout',str(timeout),
                            '--lab-case','A','--lab-peer',str(peer),'--shared-server-manifest',str(manifest)]
                        command.extend('--'+flag for flag in flags)
                        if observe_battle and peer==0:
                            command.extend('--'+flag for flag in (
                                'diagnostic-battle-transition','diagnostic-battle-participants',
                                'diagnostic-battle-player-appearance','diagnostic-battle-animations',
                                'diagnostic-battle-terminal','observe-socket-battle-vitals',
                                'probe-socket-battle-action','observe-socket-outcome-panel','observe-socket-battle-exit'))
                            if post_battle_movement:command.append('--probe-post-battle-movement')
                            if skill_battle:
                                command.remove('--probe-socket-battle-action')
                                command.extend('--'+flag for flag in ('diagnostic-battle-skill-seed',
                                    'diagnostic-battle-hotbar','diagnostic-battle-skill-settlement',
                                    'probe-socket-skill-select','probe-socket-skill-command'))
                                command.extend(('--diagnostic-battle-rounds','3'))
                        commands.append(command)
                        clients.append(subprocess.Popen(command,cwd=HOME,stdout=log,stderr=subprocess.STDOUT,
                            creationflags=subprocess.CREATE_NO_WINDOW))
                        wait_catalog_ready(clients[-1],peers[str(peer)])
                        if observe_battle and peer==0:
                            deadline=time.monotonic()+90
                            while True:
                                if clients[0].poll() is not None:raise RuntimeError('Combatant ended before character creation')
                                with closing(sqlite3.connect(settings['database']['path'])) as db:
                                    rows=db.execute('select id,name_bytes from recovered_characters').fetchall()
                                if rows:
                                    from current_login_command import lab_identity
                                    if len(rows)!=1 or rows[0][0]!=1 or bytes(rows[0][1])!=lab_identity(0)[1]:
                                        raise ValueError('Combatant must own isolated character1')
                                    break
                                if time.monotonic()>=deadline:raise TimeoutError('Combatant creation deadline')
                                time.sleep(.1)
                    until=time.monotonic()+timeout+10
                    released=False
                    rejoin=None;rejoin_released=False
                    disconnected_checkpoint=None
                    hold_marker='peer-0-skill-held.json' if skill_reconnect else 'peer-0-terminal-held.json' if terminal_reconnect else 'peer-0-pre-action-held.json'
                    while time.monotonic()<until:
                        if server.poll() is not None:raise RuntimeError('Shared server exited during probes')
                        evidence=[run/f'peer-{peer}-visible.json' for peer in (0,1)]
                        if observe_battle and not released and (run/'peer-0-battle-started.json').exists() and evidence[1].exists():
                            combatant=json.loads((run/'peer-0-battle-started.json').read_text())
                            observer=json.loads(evidence[1].read_text())
                            if (combatant['run_id']!=peers['0'] or observer['run_id']!=peers['1'] or
                                combatant['client_pid']==observer['client_pid'] or observer['local_identity']!=2 or
                                observer['sample']['entries'][0]['identity']!=1):
                                raise ValueError('Native battle participants mismatch')
                            samples=[combatant,observer]
                            if disconnected_checkpoint is not None:
                                resumed=checkpoint_rows(settings['database']['path'])
                                if terminal_reconnect:
                                    if (resumed['battle_checkpoints'][:1]!=disconnected_checkpoint['battle_checkpoints'] or
                                        resumed['battle_settlements']!=disconnected_checkpoint['battle_settlements'] or
                                        resumed['battle_reservations']!=[(1,1,1,'CUSTOM-0012'),(2,1,3,'CUSTOM-0012')] or
                                        resumed['character_resources']!=[(1,100,120,50,80,4,'CUSTOM-0012')] or
                                        len(resumed['battle_checkpoints'])!=2):
                                        raise ValueError('Terminal reconnect replayed or changed the committed battle')
                                    next_state=json.loads(resumed['battle_checkpoints'][1][1])
                                    if (next_state['id'],next_state['revision'],next_state['state'])!=(2,1,'active'):
                                        raise ValueError('Expected a distinct new diagnostic encounter')
                                elif resumed!=disconnected_checkpoint:
                                    raise ValueError('Reconnected battle changed pre-action durable state')
                                write_json(run/'reconnected-checkpoint-rows.json',resumed)
                                previous=json.loads((run/'disconnected'/hold_marker).read_text())
                                if previous['client_pid']==combatant['client_pid']:
                                    raise ValueError('Battle recovery requires a fresh native process')
                                result['terminal_settlement_preserved' if terminal_reconnect else 'first_skill_checkpoint_restored' if skill_reconnect else 'pre_action_checkpoint_restored']=True
                            write_json(run/'release-visible.json',{'peers':peers});released=True
                        if (checkpoint_reconnect or terminal_reconnect) and disconnected_checkpoint is None and (run/hold_marker).exists():
                            disconnected_checkpoint=checkpoint_rows(settings['database']['path'])
                            rows=disconnected_checkpoint
                            if (len(rows['battle_checkpoints'])!=1 or len(rows['battle_settlements'])!=(1 if terminal_reconnect else 0) or
                                rows['character_resources']!=[(1,88 if skill_reconnect else 100,120,42 if skill_reconnect else 50,80,3 if terminal_reconnect or skill_reconnect else 2,'CUSTOM-0012')] or
                                rows['battle_reservations']!=[(1,1,1,'CUSTOM-0012')]):
                                raise ValueError('Disconnect checkpoint baseline differs')
                            state=json.loads(rows['battle_checkpoints'][0][1])
                            if (state['id'],state['revision'],state['state'])!=((1,2,'finished') if terminal_reconnect else (1,3,'active') if skill_reconnect else (1,1,'active')):
                                raise ValueError('Disconnect phase differs')
                            for child in clients:stop_owned(child)
                            if checkpoint_rows(settings['database']['path'])!=rows:
                                raise ValueError('Disconnect changed checkpoint')
                            archive=run/'disconnected';archive.mkdir()
                            for path in list(run.glob('peer-*.json'))+[run/'release-visible.json']:
                                if path.exists():path.rename(archive/path.name)
                            write_json(archive/'checkpoint-rows.json',rows)
                            document=json.loads(manifest.read_text())
                            write_json(archive/'shared-server.json',document)
                            if server_restart:
                                old_generation=(document['pid'],document['create_time'])
                                stop_owned(server)
                                if checkpoint_rows(settings['database']['path'])!=rows:
                                    raise ValueError('Server stop changed durable checkpoint')
                                log=(run/'restarted-server-stdout.log').open('xb');logs.append(log)
                                server=subprocess.Popen([str(HOME/'build/Release/god2-server.exe'),
                                    '--config',str(config),'--run-for',str(timeout+60)],cwd=HOME,
                                    stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                                process,ports=server_listeners(server)
                                generation=(server.pid,process.create_time())
                                if generation==old_generation:raise ValueError('Server generation did not change')
                                if checkpoint_rows(settings['database']['path'])!=rows:
                                    raise ValueError('Server startup changed durable checkpoint')
                                document.update(pid=server.pid,create_time=generation[1],ports=ports)
                                result['server_restart']={'before':old_generation,'after':generation}
                            peers={str(i):name+f'-again{i}' for i in (0,1)}
                            document.update(peers=peers,existing_characters=True,hold_pre_action_disconnect=False,
                                hold_terminal_disconnect=False,hold_skill_disconnect=False,resume_skill_checkpoint=skill_reconnect)
                            manifest=run/'recovery-server.json'
                            write_json(manifest,document)
                            SharedCppServer(manifest,HOME).verify_client_profile(CLIENT)
                            result['peers']=peers
                            clients=[]
                            for peer,original in enumerate(commands):
                                command=list(original);command[command.index('--run-id')+1]=peers[str(peer)]
                                command[command.index('--shared-server-manifest')+1]=str(manifest)
                                log=(run/f'again-{peer}-stdout.log').open('xb');logs.append(log)
                                clients.append(subprocess.Popen(command,cwd=HOME,stdout=log,stderr=subprocess.STDOUT,
                                    creationflags=subprocess.CREATE_NO_WINDOW))
                                wait_catalog_ready(clients[-1],peers[str(peer)])
                            released=False;until=time.monotonic()+timeout+10
                            continue
                        if not observe_battle and not released and all(path.exists() for path in evidence):
                            samples=[json.loads(path.read_text()) for path in evidence]
                            if (samples[0]['client_pid']==samples[1]['client_pid'] or
                                    samples[0]['local_identity']==samples[1]['local_identity']):
                                raise ValueError('Shared probes did not use distinct clients/characters')
                            for peer,sample in enumerate(samples):
                                if (sample['run_id']!=peers[str(peer)] or
                                        sample['sample']['entries'][0]['identity']!=samples[1-peer]['local_identity']):
                                    raise ValueError('Shared observer peer binding mismatch')
                            write_json(run/'release-visible.json',{'peers':peers});released=True
                        if held_reconnect and (run/'peer-0-departed.json').exists() and clients[1].poll() is not None and rejoin is None:
                            folder=run/'rejoin';folder.mkdir()
                            document=json.loads(manifest.read_text())
                            document.update(held_reconnect=False,observe_departure=False,existing_characters=True,
                                            peers={'0':peers['0'],'1':name+'-again1'})
                            next_manifest=folder/'shared-server.json';write_json(next_manifest,document)
                            SharedCppServer(next_manifest,HOME).verify_client_profile(CLIENT)
                            command=list(commands[1]);command[command.index('--run-id')+1]=document['peers']['1']
                            command[command.index('--shared-server-manifest')+1]=str(next_manifest)
                            log=(folder/'peer-1-stdout.log').open('xb');logs.append(log)
                            child=subprocess.Popen(command,cwd=HOME,stdout=log,stderr=subprocess.STDOUT,
                                                   creationflags=subprocess.CREATE_NO_WINDOW)
                            clients.append(child);rejoin=document
                        if rejoin and not rejoin_released:
                            old=run/'peer-0-rejoined.json';new=run/'rejoin/peer-1-visible.json'
                            if old.exists() and new.exists():
                                a=json.loads(old.read_text());b=json.loads(new.read_text())
                                if (a['client_pid']!=samples[0]['client_pid'] or
                                        a['sample']['entries'][0]['identity']!=b['local_identity'] or
                                        b['sample']['entries'][0]['identity']!=a['local_identity']):
                                    raise ValueError('Held reconnect identity mismatch')
                                write_json(run/'release-rejoined.json',{'peers':rejoin['peers']})
                                write_json(run/'rejoin/release-visible.json',{'peers':rejoin['peers']})
                                rejoin_released=True
                            elif clients[0].poll() is not None or clients[2].poll() is not None:
                                raise RuntimeError('Held reconnect observer ended early')
                        if not released and any(child.poll() is not None for child in clients):
                            raise RuntimeError('A native probe exited before mutual visibility')
                        if all(child.poll() is not None for child in clients):break
                        time.sleep(.1)
                    else:raise TimeoutError('Shared native probe deadline')
                    reports=[json.loads((HOME/'artifacts/runs'/peers[str(peer)]/'run.json').read_text()) for peer in (0,1)]
                    expected=['NATIVE_SHARED_PLAYER_DEPARTURE_OBSERVED' if observe_departure else
                              'NATIVE_SHARED_PLAYER_VISIBILITY_OBSERVED','NATIVE_SHARED_PLAYER_VISIBILITY_OBSERVED']
                    if observe_movement:
                        expected=['NATIVE_SHARED_PLAYER_MOVEMENT_OBSERVED','NATIVE_MOVEMENT_PATH_COMPLETED']
                    if simultaneous_movement:
                        expected=['NATIVE_SHARED_PLAYER_MOVEMENT_OBSERVED']*2
                    if held_reconnect:expected[0]='NATIVE_SHARED_PLAYER_REJOIN_OBSERVED'
                    if observe_battle:
                        expected=['NATIVE_SOCKET_BATTLE_RETURNED_TO_WORLD_LOOP','NATIVE_SHARED_PLAYER_BATTLE_TITLE_CLEARED']
                        if post_battle_movement:expected=['NATIVE_MOVEMENT_PATH_COMPLETED','NATIVE_SHARED_PLAYER_BATTLE_MOVEMENT_OBSERVED']
                    if not released or any(r.get('result')!=expected[i] or r.get('error') for i,r in enumerate(reports)):
                        raise RuntimeError('Native shared observer did not qualify both peers')
                    if checkpoint_reconnect and not result.get('first_skill_checkpoint_restored' if skill_reconnect else 'pre_action_checkpoint_restored'):
                        raise ValueError('Native checkpoint reconnect was not observed')
                    if terminal_reconnect and not result.get('terminal_settlement_preserved'):
                        raise ValueError('Native terminal reconnect was not observed')
                    if observe_departure:
                        departure=json.loads((run/'peer-0-departed.json').read_text())
                        if departure['departure_sample']['entries']:
                            raise ValueError('Native departed role still present')
                        result['departure_observed']=True
                    if held_reconnect:
                        report=json.loads((HOME/'artifacts/runs'/rejoin['peers']['1']/'run.json').read_text()) if rejoin else {}
                        if not rejoin_released or report.get('result')!='NATIVE_SHARED_PLAYER_VISIBILITY_OBSERVED' or report.get('error'):
                            raise ValueError('Held reconnect did not complete')
                        result['held_reconnect_observed']=True
                    if observe_movement:
                        result['movement_observed']=True
                        result['simultaneous_movement']=simultaneous_movement
                    if observe_battle:
                        if not all((run/name).exists() for name in ('peer-1-fight.json','peer-1-fight-cleared.json','peer-0-battle-returned.json')):
                            raise ValueError('Shared native battle evidence missing')
                        result['battle_title_observed']=True
                        if persist_battle:
                            resource_revision=5 if terminal_reconnect or skill_battle else 3 if checkpoint_battle else 2
                            with closing(sqlite3.connect(settings['database']['path'])) as db:
                                if db.execute('pragma integrity_check').fetchall()!=[('ok',)]:
                                    raise ValueError('Battle database integrity failed')
                                if db.execute('select * from character_resources').fetchall()!=[(1,76 if skill_battle else 100,120,26 if skill_battle else 50,80,resource_revision,'CUSTOM-0012')]:
                                    raise ValueError('Durable battle resources differ')
                                reservations=[(1,1,1,'CUSTOM-0012')]+([(2,1,3,'CUSTOM-0012')] if terminal_reconnect else [])
                                if db.execute('select * from battle_reservations order by id').fetchall()!=reservations:
                                    raise ValueError('Durable battle reservation differs')
                                if db.execute('select * from character_experience').fetchall()!=[(1,0,'CUSTOM-0012')]:
                                    raise ValueError('Durable zero-award XP differs')
                                settlements=[(1,3,0,'CUSTOM-0012'),(2,5,0,'CUSTOM-0012')] if terminal_reconnect else [(1,resource_revision,0,'CUSTOM-0012')]
                                if db.execute('select battle_id,resource_revision,total_experience,design_id from battle_settlements order by battle_id').fetchall()!=settlements:
                                    raise ValueError('Durable battle settlement differs')
                                checkpoints=db.execute('select battle_id,document,resource_revision,policy_id,revival_document from battle_checkpoints').fetchall()
                                if checkpoint_battle:
                                    if len(checkpoints)!=(2 if terminal_reconnect else 1):
                                        raise ValueError('Terminal checkpoint ownership/revision differs')
                                    for identity,row in enumerate(checkpoints,1):
                                        if (row[0],*row[2:])!=(identity,5 if skill_battle else 1+2*identity,'CUSTOM-0012/diagnostic-v1',None):
                                            raise ValueError('Terminal checkpoint ownership/revision differs')
                                        state=json.loads(row[1])
                                        if (state['id'],state['revision'],state['state'],state['winner'])!=(identity,6 if skill_battle else 2,'finished',0):
                                            raise ValueError('Terminal checkpoint state differs')
                                elif checkpoints:raise ValueError('Unexpected checkpoint in basic battle')
                            result['battle_settlement_persisted']=True
                            result['terminal_checkpoint_persisted']=checkpoint_battle
                            result['skill_battle_observed']=skill_battle
                        if post_battle_movement:
                            if not all((run/name).exists() for name in ('peer-0-repopulated.json','peer-0-path-completed.json','peer-1-moved.json')):
                                raise ValueError('Post-battle world/movement evidence missing')
                            with closing(sqlite3.connect(settings['database']['path'])) as db:
                                if db.execute('select * from recovered_positions').fetchall()!=[(1,2,15,18,12,3)]:
                                    raise ValueError('Post-battle saved position differs')
                            result['post_battle_movement_observed']=True
                    result['result']='TWO_NATIVE_PLAYER_POOLS_OBSERVED'
                    if observe_battle:result['result']='TWO_NATIVE_BATTLE_TITLE_LIFECYCLE_OBSERVED'
                    result['client_pids']=[sample['client_pid'] for sample in samples]
                    if reconnect:
                        result['live_reconnect']=reconnect_pair(run,manifest,commands,server,timeout,clients,logs)
                    if restored:
                        if hashlib.sha256(Path(restored['path']).read_bytes()).hexdigest()!=restored['sha256']:
                            raise ValueError('Restore source changed')
                        with closing(sqlite3.connect(settings['database']['path'])) as db:
                            if db.execute('select * from recovered_positions order by character_id').fetchall()!=restored['positions']:
                                raise ValueError('Reconnect mutated saved positions')
                        result['restored_positions_observed']=True
                finally:
                    for child in clients:stop_owned(child)
                    for log in logs:log.close()
    except Exception as error:
        result['result']='FAILED'
        result['error']=repr(error)
    finally:
        if server is not None:stop_owned(server)
        write_json(run/'shared-result.json',result)
    print(json.dumps(result))
    return 0 if result['result'] in ('TWO_NATIVE_PLAYER_POOLS_OBSERVED','TWO_NATIVE_BATTLE_TITLE_LIFECYCLE_OBSERVED') else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--timeout',type=int,default=240,choices=range(60,301))
    parser.add_argument('--observe-departure',action='store_true')
    parser.add_argument('--observe-movement',action='store_true')
    parser.add_argument('--simultaneous-movement',action='store_true')
    parser.add_argument('--restore-database',type=Path)
    parser.add_argument('--reconnect',action='store_true')
    parser.add_argument('--held-reconnect',action='store_true')
    parser.add_argument('--observe-battle',action='store_true')
    parser.add_argument('--post-battle-movement',action='store_true')
    parser.add_argument('--persist-battle',action='store_true')
    parser.add_argument('--checkpoint-battle',action='store_true')
    parser.add_argument('--checkpoint-reconnect',action='store_true')
    parser.add_argument('--terminal-reconnect',action='store_true')
    parser.add_argument('--skill-battle',action='store_true')
    parser.add_argument('--skill-reconnect',action='store_true')
    parser.add_argument('--server-restart',action='store_true')
    args=parser.parse_args()
    raise SystemExit(run(args.run_id,args.timeout,args.observe_departure,args.observe_movement,args.simultaneous_movement,args.restore_database,args.reconnect,args.held_reconnect,args.observe_battle,args.post_battle_movement,args.persist_battle,args.checkpoint_battle,args.checkpoint_reconnect,args.terminal_reconnect,args.skill_battle,args.skill_reconnect,args.server_restart))
