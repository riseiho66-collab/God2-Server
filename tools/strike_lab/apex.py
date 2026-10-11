"""One controlled compatibility intervention, one session, stop at next blocker."""
import argparse
import itertools
import os
from contextlib import redirect_stdout,redirect_stderr
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import socket
import struct
import subprocess
import sys
import threading
import time
from lab import HOME,CLIENT,PROFILES,profile_context,sha,write_json
from capture import Observer as ReadObserver,parse_marker,WS
from trace_qualification import native,interactive
from network_driver import NetworkDriver
from shared_cpp_server import SharedCppServer

COUNTS={**WS,'WSAGetLastError':0,'WSASocketA':6,'WSASocketW':6,'WSAConnect':7,'shutdown':2}
APIS=list(COUNTS)
SOCKET_APIS=('socket','WSASocketA','WSASocketW')
CONNECT_APIS=('connect','WSAConnect')
MEMORY_WARNING=('\u7cfb\u7d71\u865b\u64ec\u8a18\u61b6\u9ad4\u4e0d\u8db3\uff0c'
    '\u53ef\u80fd\u9020\u6210\u904a\u6232\u7121\u6cd5\u6b63\u5e38\u904b\u4f5c\uff0c'
    '\u8acb\u78ba\u4fdd\u7cfb\u7d71\u865b\u64ec\u8a18\u61b6\u9ad4\u5728700MB\u4ee5\u4e0a')
SITES={4:(0x40dbd0,'GRAPHICS_CALL'),5:(0x40dbd5,'GRAPHICS_RETURN'),6:(0x40dbf3,'TABLE_ENUMERATION'),
    7:(0x456130,'INPUT_LOADER'),8:(0x456682,'SYSTEMMESSAGE_DISPATCH'),9:(0x458ff0,'STRING_LOADER'),
    10:(0x459012,'POINTER_STORE'),11:(0x459112,'COUNT_STORE'),12:(0x45b665,'COMPAT_BRANCH'),
    13:(0x45b7a4,'OLD_FAILURE'),14:(0x459141,'STRING_LOADER_RETURN'),
    15:(0x40e42c,'FOCUS_PATH'),16:(0x53c262,'COOPERATIVE_RETURN')}


def milestones(events):
    kinds={e.get('event_type') for e in events}
    return {'GRAPHICS_RETURNED':any(e.get('event_type')=='GRAPHICS_RETURN' and e.get('eax',0)!=0 for e in events),
        'TABLE_ENUMERATION_REACHED':'TABLE_ENUMERATION' in kinds,
        'STRING_TABLE_INITIALIZED':all(k in kinds for k in ('INPUT_LOADER','SYSTEMMESSAGE_DISPATCH','STRING_LOADER')) and
            any(e.get('after_store',{}).get('pointer',0) and e.get('after_store',{}).get('count',0)>0 for e in events),
        'WINSOCK_REACHED':any(e.get('event_type')=='API_ENTRY' and e.get('api') in APIS for e in events),
        'CONNECTED':any(e.get('event_type')=='API_RETURN' and e.get('api') in CONNECT_APIS and e.get('eax')==0 and e.get('matched') for e in events),
        'FIRST_TX':any(e.get('event_type')=='API_RETURN' and e.get('api')=='send' and 0<e.get('eax',0)<0x80000000 and e.get('matched') for e in events)}


def progression(events):
    state=milestones(events)
    state.update(TABLE_ENUMERATION=state['TABLE_ENUMERATION_REACHED'],
        SYSTEMMESSAGE_LOADED=state['STRING_TABLE_INITIALIZED'],
        STRING_TABLE_READY=state['STRING_TABLE_INITIALIZED'],
        MEMORY_WARNING_SEEN=any(e.get('message_text')==MEMORY_WARNING for e in events),
        MEMORY_WARNING_PASSED=warning_path_passed(events),
        SOCKET_CREATED=any(e.get('event_type')=='API_RETURN' and e.get('api') in SOCKET_APIS
            and e.get('matched') and e.get('eax') not in (None,0xffffffff) for e in events),
        CONNECT_ATTEMPTED=any(e.get('event_type')=='API_ENTRY' and e.get('api') in CONNECT_APIS for e in events),
        FIRST_RX=any(e.get('event_type')=='API_RETURN' and e.get('api')=='recv'
            and e.get('matched') and 0<e.get('eax',0)<0x80000000 for e in events))
    # These require downstream evidence; acknowledging a dialog alone is insufficient.
    for key in ('HANDSHAKE','LOGIN','CHARACTER_SCREEN','WORLD','HEARTBEAT','MOVEMENT'):
        state[key]=False
    state['LOGIN']=any(e.get('event_type')=='LOGIN_ACCEPTED_VERIFIED' for e in events)
    ui=[e.get('ui',{}) for e in events]
    state.update(MEMORY_WARNING_MATCHED=any(e.get('matched') for e in ui),
        MEMORY_WARNING_OK_SENT=any(e.get('ok_sent') for e in ui),
        MEMORY_WARNING_CLOSED=any(e.get('closed') for e in ui),
        POST_WARNING_EXECUTION=any(e.get('event_type')=='POST_WARNING_EXECUTION' for e in events))
    state['state']=next((key for key in ('FIRST_TX','FIRST_RX','CONNECTED','CONNECT_ATTEMPTED','SOCKET_CREATED') if state[key]),None) or ('WINSOCK_REACHED' if state['WINSOCK_REACHED'] else
        'POST_WARNING_RUNNING' if state['POST_WARNING_EXECUTION'] else
        'MEMORY_WARNING_ACKNOWLEDGED' if state['MEMORY_WARNING_CLOSED'] else
        'MEMORY_WARNING_SEEN' if state['MEMORY_WARNING_SEEN'] else
        'WAITING_FOR_MEMORY_WARNING' if state['STRING_TABLE_READY'] else
        'STARTUP' if events else 'WAITING_FOR_CLIENT')
    return state


def warning_path_passed(events):
    if any(e.get('event_type')=='POST_WARNING_EXECUTION' and e.get('ui',{}).get('closed') for e in events):
        return True
    # Accept the no-dialog route only with the ordered, same-thread branch proof.
    groups={}
    for event in events:
        if event.get('pid') is None or event.get('tid') is None:
            continue
        groups.setdefault((event['pid'],event['tid']),[]).append(event)
    for stream in groups.values():
        stream=sorted(stream,key=lambda e:e.get('global_sequence',-1))
        position=0
        for event in stream:
            pc=event.get('pc')
            if pc in (0x40f1f5,0x40f24c):
                position=0
            elif position==0 and pc==0x40f186 and '[br=1]' in event.get('native_stop',''):
                position=1
            elif position==1 and pc==0x40f246 and '[br=1]' in event.get('native_stop',''):
                position=2
            elif position==2 and pc==0x40f2d0:
                position=3
            elif position==3 and event.get('event_type')=='API_RETURN' and event.get('api')=='WSAStartup' and event.get('matched') and event.get('eax')==0:
                return True
    return False


def update_progress(run,events):
    temporary=run/'milestones.tmp'
    temporary.write_text(json.dumps(progression(events),indent=2),encoding='utf-8')
    temporary.replace(run/'milestones.json')


def execution_summary(result,run):
    if 'login_entry' in result:
        consumer = result.get('character_list_consumer', {})
        logical = bytes.fromhex(consumer.get('logical_hex', ''))
        copied = bytes.fromhex(consumer.get('copied_hex', ''))
        consumed = (consumer.get('return_eax') == 0 and len(logical) == 75
                    and logical[0] == 7 and copied == logical[1:])
        return {'run': str(run), 'result': result.get('result'), 'error': result.get('error'),
                'connected': result.get('milestones', {}).get('CONNECTED', False),
                'character_list_consumed': consumed,
                'character_count': bytes.fromhex(consumer['copied_hex'])[0] if consumed else None,
                'world_accepted': False,
                'scope': 'Native probe result; historical golden-prefix classifiers reported separately'}
    # A downstream scenario that never started cannot supersede the actual
    # startup outcome with its own missing-packet regression label.
    connected=result.get('milestones',{}).get('CONNECTED',False)
    if connected:
        for key in ('server_list','login_terminal','c2s0002','post_seed','server_first'):
            if key in result:
                return result[key]
    last=result.get('last_successful_network_event') or {}
    return {'run':str(run),'furthest_milestone':result.get('furthest_milestone'),
        'last_successful_network_event':last.get('api'),'last_client_caller_rva':last.get('caller_rva'),
        'last_packet_artifact':result.get('last_packet_artifact'),'next_blocker':result.get('next_blocker'),
        'result':result.get('result'),'error':result.get('error'),
        'downstream_protocol_execution':'STARTED' if connected else 'NOT_REACHED'}


def require_available_loopback_port(port):
    """Reject a native probe before it can attach to another local server."""
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as probe:
        if hasattr(socket,'SO_EXCLUSIVEADDRUSE'):
            probe.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        try:
            probe.bind(('127.0.0.1',port))
        except OSError as error:
            raise RuntimeError(f'Loopback port {port} is occupied; refusing isolated client probe') from error


class Sink:
    def __init__(self,port,run,initial=None):
        self.run=run;self.events=[];self.done=threading.Event()
        self.initial=initial;self.hello_gate=threading.Event()
        self.server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.server.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
            self.server.bind(('127.0.0.1',port));self.server.listen(1);self.server.settimeout(.25)
        except Exception:
            self.server.close();raise
        self.worker=threading.Thread(target=self.read);self.worker.start()

    def read(self):
        try:
            while not self.done.is_set():
                try: conn,peer=self.server.accept();break
                except socket.timeout: continue
            else:return
            self.events.append({'event_type':'LOOPBACK_ACCEPT','peer':peer,'time':time.time()})
            with conn, (self.run/'c2s/loopback-stream.bin').open('xb') as stream:
                conn.settimeout(.25);total=0
                if self.initial is not None:
                    while not self.done.is_set() and not self.hello_gate.wait(.05):pass
                    if self.done.is_set():return
                    conn.sendall(self.initial)
                    self.events.append({'event_type':'INITIAL_S2C_SENT','length':len(self.initial),'time':time.time()})
                while not self.done.is_set() and total<1048576:
                    try: data=conn.recv(min(4096,1048576-total))
                    except socket.timeout:continue
                    if not data:break
                    stream.write(data);total+=len(data)
                    self.events.append({'event_type':'LOOPBACK_READ','length':len(data),'time':time.time()})
        except OSError as error:self.events.append({'event_type':'LISTENER_ERROR','error':str(error)})

    def close(self):
        self.done.set();self.worker.join(timeout=2);self.server.close()
        if self.worker.is_alive():raise RuntimeError('Listener worker failed to stop')


class CppSeedServer:
    def __init__(self,run,timeout,post_seed=False,s2c0003=False,terminal=False,server_list=False,long_lived=False,post_select=False,legacy_character_list_candidate=False,recovered_account_auth=False,recovered_character_create=False,recovered_dual_connection=False,recovered_world_entry=False,isolated_database=False,movement_lab=False,restore_movement_database=None,diagnostic_battle_transition=False,diagnostic_battle_participants=False,diagnostic_battle_rounds=1,diagnostic_battle_terminal=False,diagnostic_battle_player_appearance=False,diagnostic_battle_animations=False,diagnostic_battle_skill_seed=False,diagnostic_battle_skill_settlement=False,diagnostic_battle_mp_refusal=False,*,diagnostic_battle_resources=False,diagnostic_world_resources=False,diagnostic_battle_experience=0,diagnostic_role_progress=False,diagnostic_progress_span=0,diagnostic_level_snapshot=False,diagnostic_resume_checkpoint=False,diagnostic_battle_after_movement=False,diagnostic_encounter_limit=1,diagnostic_world_supply=False,diagnostic_battle_revival=False,diagnostic_quest_dialogue=False,diagnostic_quest_npc=False,town_entry_lab=False,town_consensus_path=False,restore_town_database=None,town_fresh_spawn=False,town_spawn_guides=False,town_quest_progress=False,town_map_probe=False,town_scene_probe=False,town_scene_relocate=False,town_scene_indoor_probe=False,town_scene_indoor_transfer=False,town_scene_return_probe=False,town_scene_return_commit=False,town_door_routes=False,town_battle_after_quest=False,town_return_after_battle=False,town_door_after_battle=False,town_door_reconnect=False,town_post_battle_position_restore=False,remote_actor_probe_language=None):
        if town_quest_progress and not town_spawn_guides:
            raise ValueError('Town quest progress requires town guides')
        if town_spawn_guides and not (restore_town_database or town_fresh_spawn):
            raise ValueError('Town guide spawn requires qualified restored or fresh town placement')
        if restore_town_database and not (town_entry_lab and town_consensus_path):
            raise ValueError('Town restore requires isolated source-agreement mode')
        if town_consensus_path and not town_entry_lab:raise ValueError('Source agreement requires town lab')
        if town_entry_lab and (not movement_lab or not isolated_database or restore_movement_database or
                              (diagnostic_battle_transition and not town_battle_after_quest) or diagnostic_quest_dialogue or diagnostic_world_resources):
            raise ValueError('Town entry requires fresh standalone isolated movement lab')
        if recovered_world_entry and not recovered_dual_connection:
            raise ValueError('World entry candidate requires dual connection')
        if recovered_dual_connection and not recovered_character_create:
            raise ValueError('Dual connection requires recovered character persistence')
        if recovered_character_create and not recovered_account_auth:
            raise ValueError('Recovered character creation requires account authentication')
        if recovered_account_auth and not legacy_character_list_candidate:
            raise ValueError('Recovered account authentication requires character-list candidate mode')
        require_available_loopback_port(2592)
        self.events=[];self.hello_gate=threading.Event();self.closed=False
        self.allowed_ports = {2592}
        self.log_path=run/'cpp-server.log';self.log=self.log_path.open('xb')
        config='recovered-post-seed.json' if post_seed else 'recovered-seed.json'
        if s2c0003:config='recovered-c2s0002.json'
        if terminal:config='recovered-login-terminal.json'
        if server_list:config='recovered-server-list.json'
        if post_select:config='recovered-post-server-select.json'
        if legacy_character_list_candidate:config='legacy-character-list-candidate.json'
        if recovered_account_auth:config='recovered-account-login.json'
        if recovered_character_create:config='recovered-character-create.json'
        if recovered_dual_connection:config='recovered-dual-connection.json'
        if recovered_world_entry:config='recovered-world-entry.json'
        if movement_lab:
            if not (isolated_database and recovered_world_entry):
                raise ValueError('Movement lab requires isolated world-entry run')
            config='recovered-movement.json'
        self.long_lived=long_lived
        self.hold_control=run/'session-hold.json'
        env=os.environ.copy()
        env.pop('GOD2_UI_GATE_CONTROL',None)
        if long_lived:env['GOD2_UI_GATE_CONTROL']=str(self.hold_control.resolve())
        command=[str(HOME/'build/Release/god2-server.exe'),'--config',str(HOME/'config'/config)]
        if isolated_database:
            if restore_town_database:
                import sqlite3
                from contextlib import closing
                source=Path(restore_town_database).resolve(strict=True)
                target=run/'town-diagnostic-accounts.db'
                if source.name!='town-diagnostic-accounts.db' or not source.is_relative_to((HOME/'artifacts/runs').resolve()) or target.exists():
                    raise ValueError('Town restore requires owned evidence and a new target')
                before=sha(source)
                with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as original:
                    rows=original.execute('SELECT character_id,area,scene,x,y,revision FROM recovered_positions').fetchall()
                    qualified=([(1,2,4,110,70,53)],[(1,2,4,111,70,54)],[(1,2,4,112,70,55)],
                               [(1,2,4,110,72,55)],
                               [(1,2,4,110,70,56)],[(1,2,4,111,70,57)],[(1,2,4,86,71,91)])
                    if town_scene_indoor_transfer:
                        # Revision 2 is the independently verified fresh-character
                        # quest -> first transfer -> first indoor movement path.
                        qualified+=([(1,2,15,17,13,54)],[(1,2,15,18,12,55)],
                                    [(1,2,15,18,12,2)])
                    if town_door_reconnect:
                        qualified+=([(1,2,4,86,71,64)],)
                    if town_post_battle_position_restore:
                        qualified=[[(1,2,15,19,12,58)],[(1,2,15,19,12,5)]]
                    if town_battle_after_quest and rows!=[(1,2,15,18,12,55)]:
                        raise ValueError('Town battle requires the qualified indoor stage-3 checkpoint')
                    if rows not in qualified:
                        raise ValueError('Town restore requires qualified cross-window or relocation checkpoint')
                    if original.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:raise ValueError('Town source integrity failed')
                    with closing(sqlite3.connect(target)) as copied:original.backup(copied)
                if sha(source)!=before:raise ValueError('Town source changed during snapshot')
                self.restored_town_position=tuple(rows[0][3:5])
                self.restored_town_scene=rows[0][2]
                write_json(run/'town-restore.json',{'source':str(source),'source_sha256':before,'position':rows[0],
                                                  'scope':'READ_ONLY_BACKUP_NO_SOURCE_MUTATION'})
            if restore_movement_database:
                import sqlite3
                source=Path(restore_movement_database).resolve(strict=True)
                if source.name!='diagnostic-accounts.db' or not source.is_relative_to((HOME/'artifacts/runs').resolve()):
                    raise ValueError('Restore source must be an isolated run database')
                original=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)
                target=sqlite3.connect(run/'diagnostic-accounts.db')
                try:
                    positions=original.execute('SELECT character_id,area,scene,x,y,revision FROM recovered_positions').fetchall()
                    expected_positions=[(1,2,15,18,12,3)]
                    if (diagnostic_world_resources and not diagnostic_battle_transition and not diagnostic_world_supply and
                            positions in ([],[(1,2,15,18,12,1)])):
                        # A committed terminal exchange can disconnect before its result/first movement.
                        resources=original.execute('SELECT hp,max_hp,mp,max_mp,revision,design_id FROM character_resources').fetchall()
                        xp=original.execute('SELECT total,design_id FROM character_experience').fetchall()
                        checkpoints=original.execute('SELECT document,resource_revision,policy_id,revival_document FROM battle_checkpoints').fetchall()
                        ledgers=original.execute('SELECT request,total_experience,resource_revision FROM battle_settlements').fetchall()
                        if resources!=[(76,120,26,80,6,'CUSTOM-0012')] or xp!=[(250,'CUSTOM-0012')] or len(checkpoints)!=1 or len(ledgers)!=1:
                            raise ValueError('World restore requires the committed terminal diagnostic fixture')
                        checkpoint=json.loads(checkpoints[0][0]);request=json.loads(ledgers[0][0])
                        if ((checkpoint['state'],checkpoint['revision'],checkpoint['winner'])!=('finished',6,0) or
                            checkpoints[0][1:]!=(6,'CUSTOM-0012/diagnostic-v1',None) or ledgers[0][1:]!=(250,6) or
                            request.get('checkpoint',{}).get('after')!=checkpoints[0][0] or
                            original.execute('SELECT count(*) FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE s.battle_id IS NULL').fetchone()[0]):
                            raise ValueError('Terminal checkpoint and settlement ledger differ')
                        self.restored_terminal_no_position=not positions
                        self.restored_terminal_after_move=bool(positions)
                        expected_positions=positions
                        write_json(run/'terminal-restore.json',{'source':str(source),'source_sha256':sha(source),
                            'position':positions[0] if positions else None,
                            'scope':('COMMITTED_TERMINAL_AFTER_FIRST_MOVE_NO_REAWARD' if positions else
                                     'COMMITTED_TERMINAL_BEFORE_RESULT_NO_POSITION_NO_REAWARD')})
                    if diagnostic_world_supply:
                        slots=original.execute('SELECT item_id,count FROM diagnostic_inventory_slots WHERE character_id=1 AND slot=0').fetchall()
                        if len(slots)!=1 or not (slots[0]==(0,0) or
                                (slots[0][0] in (3101,3107) and 1<=slots[0][1]<=127)):
                            raise ValueError('Supply projection requires explicit saved3107 or empty tombstone')
                        self.expected_supply_slot=slots[0]
                    if diagnostic_battle_resources:
                        rows=original.execute(
                            'SELECT character_id,hp,max_hp,mp,max_mp,revision,design_id FROM character_resources'
                        ).fetchall()
                        if diagnostic_resume_checkpoint and diagnostic_battle_revival:
                            if len(rows)!=1 or rows[0][:5]!=(1,100,120,14,80) or rows[0][5]<5 or rows[0][6]!='CUSTOM-0012':
                                raise ValueError('Revival resume requires qualified durable resources')
                            checkpoints=original.execute('SELECT document,resource_revision,revival_document FROM battle_checkpoints').fetchall()
                            if len(checkpoints)!=1 or checkpoints[0][1]!=rows[0][5] or not checkpoints[0][2]:
                                raise ValueError('Revival resume checkpoint missing')
                            phase=json.loads(checkpoints[0][2])
                            if json.loads(checkpoints[0][0]).get('revision')!=rows[0][5]-1:
                                raise ValueError('Revival checkpoint/resource revision mismatch')
                            if phase.get('battle')!=checkpoints[0][0] or not phase.get('action') or not phase.get('control'):
                                raise ValueError('Revival resume phase is not receipt-complete')
                            if original.execute('SELECT count(*) FROM battle_settlements').fetchone()[0]:
                                raise ValueError('Revival resume fixture settled')
                            self.restored_battle_resources=(100,14);expected_positions=[]
                        elif diagnostic_resume_checkpoint:
                            if rows not in ([(1,88,120,42,80,4,'CUSTOM-0012')],[(1,76,120,34,80,5,'CUSTOM-0012')]):
                                raise ValueError('Resume requires qualified pending resource fixture')
                            self.restored_exchanges=rows[0][5]-3
                            checkpoints=original.execute('SELECT document,resource_revision FROM battle_checkpoints').fetchall()
                            if len(checkpoints)!=1 or checkpoints[0][1]!=rows[0][5]:
                                raise ValueError('Resume checkpoint missing')
                            checkpoint=json.loads(checkpoints[0][0])
                            if (checkpoint['state'],checkpoint['revision'],checkpoint['actors'][14][2])!=('active',2*self.restored_exchanges+1,150-54*self.restored_exchanges):
                                raise ValueError('Resume requires completed diagnostic exchange snapshot')
                            if original.execute('SELECT count(*) FROM battle_settlements').fetchone()[0]:
                                raise ValueError('Resume fixture already settled')
                            self.restored_battle_resources=(rows[0][1],rows[0][3]);expected_positions=[]
                        elif rows==[(1,100,120,42,80,2,'CUSTOM-0012')]:
                            self.restored_battle_resources=(100,42)
                        elif rows==[(1,76,120,34,80,3,'CUSTOM-0012')]:
                            self.restored_battle_resources=(76,34)
                            expected_positions=[]
                        elif diagnostic_world_supply and diagnostic_battle_transition and rows==[(1,52,120,80,80,13,'CUSTOM-0012')]:
                            self.restored_battle_resources=(52,80)
                        elif diagnostic_battle_transition and not diagnostic_level_snapshot and rows==[(1,28,120,80,80,17,'CUSTOM-0012')]:
                            if original.execute('SELECT item_id,count,revision FROM diagnostic_inventory_slots WHERE character_id=1 AND slot=0').fetchall()!=[(0,0,4)]:
                                raise ValueError('Post-supply battle requires saved depleted inventory')
                            self.restored_battle_resources=(28,80)
                        elif diagnostic_battle_transition and diagnostic_battle_rounds==3 and diagnostic_battle_terminal and not diagnostic_level_snapshot and rows==[(1,4,120,56,80,20,'CUSTOM-0012')]:
                            if original.execute('SELECT item_id,count,revision FROM diagnostic_inventory_slots WHERE character_id=1 AND slot=0').fetchall()!=[(0,0,4)]:
                                raise ValueError('Defeat observation requires depleted post-battle save')
                            self.restored_battle_resources=(4,56)
                        else:
                            raise ValueError('Resource restore requires a verified terminal or damaged skill save')
                    if positions!=expected_positions:
                        raise ValueError('Restore source differs from verified position fixture')
                    original.backup(target)
                finally:
                    target.close()
                    original.close()
            settings=json.loads((HOME/'config'/config).read_text(encoding='utf-8'))
            settings['development']['diagnostic_battle_transition']=diagnostic_battle_transition
            settings['development']['diagnostic_battle_participants']=diagnostic_battle_participants
            settings['development']['diagnostic_battle_player_appearance']=diagnostic_battle_player_appearance
            settings['development']['diagnostic_battle_animations']=diagnostic_battle_animations
            settings['development']['diagnostic_battle_skill_seed']=diagnostic_battle_skill_seed
            settings['development']['diagnostic_battle_revival']=diagnostic_battle_revival
            settings['development']['diagnostic_battle_skill_settlement']=diagnostic_battle_skill_settlement
            settings['development']['diagnostic_battle_mp_refusal']=diagnostic_battle_mp_refusal
            settings['development']['diagnostic_battle_resources']=diagnostic_battle_resources
            settings['development']['diagnostic_battle_experience']=diagnostic_battle_experience
            settings['development']['diagnostic_role_progress']=diagnostic_role_progress
            settings['development']['diagnostic_progress_span']=diagnostic_progress_span
            settings['development']['diagnostic_level_snapshot']=diagnostic_level_snapshot
            settings['development']['diagnostic_resume_checkpoint']=diagnostic_resume_checkpoint
            settings['development']['diagnostic_battle_after_movement']=diagnostic_battle_after_movement
            settings['development']['diagnostic_encounter_limit']=diagnostic_encounter_limit
            settings['development']['diagnostic_world_resources']=diagnostic_world_resources
            settings['development']['diagnostic_world_supply']=diagnostic_world_supply
            settings['development']['diagnostic_quest_dialogue']=diagnostic_quest_dialogue
            settings['development']['diagnostic_quest_npc']=diagnostic_quest_npc
            settings['development']['diagnostic_battle_rounds']=diagnostic_battle_rounds
            settings['development']['diagnostic_battle_terminal']=diagnostic_battle_terminal
            settings['database']={'type':'sqlite','path':str((run/'diagnostic-accounts.db').resolve())}
            settings['logging']['file']=str((run/'diagnostic-server.log').resolve())
            for key in ('bootstrap','script_root'):
                settings['lua'][key]=str((HOME/settings['lua'][key]).resolve())
            if movement_lab:
                settings['development']['recovered_navigation']=str((HOME/settings['development']['recovered_navigation']).resolve())
            if town_entry_lab:
                navigation=HOME/'artifacts/world-atlas/town-2-4.json'
                atlas=json.loads(navigation.read_text())
                window=atlas['windows'][30]
                def known_cell(x,y):
                    offset=((y-window['origin_y'])*63+x-window['origin_x'])*2
                    return window['cells_hex'][offset:offset+2] in ('01','02')
                x,y=next((x,y) for y in range(64,80) for x in range(63,79)
                         if known_cell(x,y) and known_cell(x+1,y))
                settings['development']['recovered_navigation']=str(navigation.resolve())
                settings['development']['diagnostic_town']={'center_x':3,'center_y':3,'x':x,'y':y}
                settings['development']['diagnostic_town']['spawn_guides']=town_spawn_guides
                settings['development']['diagnostic_town']['quest_progress']=town_quest_progress
                settings['development']['diagnostic_town']['map_probe']=town_map_probe
                settings['development']['diagnostic_town']['scene_probe']=town_scene_probe
                settings['development']['diagnostic_town']['scene_relocate']=town_scene_relocate
                settings['development']['diagnostic_town']['scene_indoor_probe']=town_scene_indoor_probe
                settings['development']['diagnostic_town']['scene_indoor_transfer']=town_scene_indoor_transfer
                settings['development']['diagnostic_town']['scene_return_probe']=town_scene_return_probe
                settings['development']['diagnostic_town']['scene_return_commit']=town_scene_return_commit
                settings['development']['diagnostic_town']['door_routes']=town_door_routes
                settings['development']['diagnostic_town']['battle_after_quest']=town_battle_after_quest
                settings['development']['diagnostic_town']['return_after_battle']=town_return_after_battle
                settings['development']['diagnostic_town']['door_after_battle']=town_door_after_battle
                if town_scene_indoor_transfer or town_door_routes:
                    settings['development']['diagnostic_town']['indoor_navigation']=str((HOME/'artifacts/world-atlas/indoor-2-15.json').resolve())
                self.town_start=(x,y)
                self.town_window=window
                self.town_windows=atlas['windows']
                if town_consensus_path:
                    from town_probe_route import agreement_window
                    self.town_window=agreement_window(atlas)
                    self.town_target_x=110
                    settings['development']['diagnostic_town']['source_consensus']=True
                if town_fresh_spawn:
                    settings['development']['diagnostic_town'].update(center_x=4,center_y=3,x=110,y=70)
                    self.town_start=(110,70)
                if restore_town_database:
                    settings['development']['local_account_registration']=False
                    self.town_start=self.restored_town_position
                settings['database']['path']=str((run/'town-diagnostic-accounts.db').resolve())
            if remote_actor_probe_language is not None:
                from current_remote_actor_live import configure_probe
                settings=configure_probe(settings,run,remote_actor_probe_language)
            isolated_config=run/'diagnostic-server-config.json'
            write_json(isolated_config,settings)
            command[-1]=str(isolated_config)
        if diagnostic_quest_npc or town_quest_progress:
            # Import pinned display metadata into the owned run DB before listening.
            import sqlite3
            from contextlib import closing
            if str(HOME) not in sys.path:sys.path.insert(0,str(HOME))
            from tools.strike_lab.import_native_quests import import_catalog
            subprocess.run(command+['--migrate-only'],cwd=HOME,stdout=self.log,
                           stderr=subprocess.STDOUT,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
            with closing(sqlite3.connect(run/('town-diagnostic-accounts.db' if town_quest_progress else 'diagnostic-accounts.db'))) as connection:
                import_catalog(connection,HOME.parent/'God2')
                saved=connection.execute('SELECT slots,revision FROM diagnostic_quest_journal WHERE character_id=1').fetchall()
                if saved:
                    self.restored_quest_journal={'slots_hex':saved[0][0].hex(),'revision':saved[0][1]}
                if town_quest_progress:
                    progress=connection.execute('SELECT stage,journal_description,revision,source_sha256,design_id FROM diagnostic_town_guide_progress WHERE character_id=1').fetchall()
                    self.town_guide_start_stage=0
                    if progress:
                        stage,description,revision,source,design=progress[0]
                        if (stage not in (1,2,3) or description!=(0 if stage==3 else stage) or revision<1 or
                                source!='1ff497204b5cf77cbbccffdf1836d7aeee30e46980ac1e85d8d0a08a0a4bcda7' or design!='CUSTOM-0021' or saved):
                            raise ValueError('Town guide restore provenance/slot ownership mismatch')
                        self.town_guide_start_stage=stage
                        if stage==3:
                            receipt=connection.execute('SELECT progress_revision,slot,item_id,count,source_sha256,design_id FROM diagnostic_town_guide_reward WHERE character_id=1').fetchall()
                            if receipt!=[(revision,0,5569,1,'70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731','CUSTOM-0022')]:
                                raise ValueError('Completed town quest receipt mismatch')
                        self.restored_quest_journal={'slots_hex':(struct.pack('<I',(description<<16)|1 if description else 0)+bytes(56)).hex(),
                                                     'revision':revision,'origin':'CUSTOM-0021'}
                    if town_battle_after_quest and not town_fresh_spawn and self.town_guide_start_stage!=3:
                        raise ValueError('Town battle requires completed guide stage3')
        if not long_lived:command+=['--run-for',str(timeout+3)]
        self.process=subprocess.Popen(command,cwd=HOME,stdout=self.log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,env=env)
        until=time.monotonic()+5
        while time.monotonic()<until:
            if self.process.poll() is not None:break
            log = self.log_path.read_text(encoding='utf-8',errors='replace')
            if 'listening on 127.0.0.1:2592' in log:
                if recovered_dual_connection:
                    match = re.search(r'Character connection listening on 127\.0\.0\.1:(\d+);', log)
                    if not match:
                        time.sleep(.05)
                        continue
                    self.allowed_ports.add(int(match[1]))
                return
            time.sleep(.05)
        self.process.terminate();self.process.wait(timeout=5);self.log.close()
        raise RuntimeError('C++ seed listener not ready')

    def request_hold(self,enabled,wait=False):
        if not self.long_lived:return
        from ui_gate import atomic_json
        atomic_json(self.hold_control,{'session_id':1,'hold':enabled,'lease_until_ms':int(time.time()*1000)+10000})
        if wait:
            until=time.monotonic()+3
            while time.monotonic()<until:
                status=self.hold_status()
                if status and status.get('ui_gate_hold_active') is enabled:return
                if self.process.poll() is not None:break
                time.sleep(.05)
            if enabled:raise RuntimeError('Server did not confirm UiGateHold')

    def hold_status(self):
        try:
            status=json.loads(Path(str(self.hold_control)+'.status').read_text())
            if status.get('session_id')==1 and 0<=time.time()*1000-status['updated_at']<3000:return status
        except (OSError,ValueError,KeyError):pass
        return {}

    def close(self):
        if self.closed:return
        self.closed=True
        if self.long_lived and self.process.poll() is None:self.request_hold(False,wait=True)
        if self.long_lived and self.process.poll() is None:self.process.terminate()
        try:self.process.wait(timeout=8)
        except subprocess.TimeoutExpired:self.process.terminate();self.process.wait(timeout=5)
        self.log.close()
        log=self.log_path.read_text(encoding='utf-8',errors='replace')
        for marker,event in (('GOD2_INITIAL_S2C_SENT','INITIAL_S2C_SENT'),('GOD2_SEED_EXCHANGE_ACCEPTED','SEED_RESPONSE_ACCEPTED')):
            if marker in log:self.events.append({'event_type':event,'source':'cpp-server.log'})


class Observer(ReadObserver):
    def __init__(self,run,mode,timeout=60,enter_game=False,test_login=False,ceiling='NONE',network_strike=False):
        super().__init__(run,HOME/'build-strike-lab/Release/God2Probe.dll')
        self.mode=mode;self.sink=None;self.installed=False;self.result={};self.dialog=None
        self.timeout=timeout
        self.enter_game=enter_game;self.enter_game_armed=False
        self.test_login=test_login
        self.ceiling=ceiling
        self.network_strike=network_strike;self.reference_image=None

    def arm(self,driver,result,name):
        driver.deadline=None if getattr(self,'rendezvous',False) else time.monotonic()+self.timeout
        if getattr(self, 'owner_ui', False):
            driver.deadline = time.monotonic() + self.timeout
        if getattr(self,'rendezvous',False):
            from ui_gate_live import LongLivedRunContext
            gate_type=LongLivedRunContext
            if getattr(self,'post_select_follow',False):
                from post_server_select_observer import PostServerSelectObserver
                gate_type=PostServerSelectObserver
            self.gate=gate_type(HOME,self.run,self.sink,driver,getattr(self,'gate_max_wait',None))
            driver.gate_tick=self.gate.tick
        def snapshot_window(pid):
            if getattr(self, 'zero_ui_prefix', False):
                result['window_capture'] = 'DISABLED_ZERO_UI_PREFIX'
                return
            if getattr(self, 'owner_ui', False):
                result['window_capture'] = 'DISABLED_OWNER_UI_MODE'
                return
            try:
                from window_snapshot import capture
                result['windows']=capture(pid,self.run)
            except Exception as error:result['window_capture_error']=repr(error)
        driver.capture_window=snapshot_window
        driver.command(f'.load "{self.dll.as_posix()}"')
        for index,api in enumerate(APIS,100):
            driver.command(f'bu{index} ws2_32!{api} ".printf \\"APEX_EARLY api={api} pid=%x tid=%x\\\\n\\", @$tpid, @$tid; gc"')

    def collect(self,driver,result,name):
        outcome='EVENT_BUDGET_END';pending=None;warning=None;returns={};select_samples=0
        try:
            if self.mode=='MODE_COMPAT':
                driver.command(f'.load "{(HOME/"build-strike-lab/Release/God2Compat.dll").as_posix()}"')
                applied=driver.command('!God2Compat.install')
                result['intervention']=applied
                if 'GOD2_COMPAT installed' not in applied:raise ValueError('Compatibility installation refused: '+applied)
                self.installed=True
                result['bridge_disassembly']=driver.command('u poi(5707bc) L2')
            for index,(pc,label) in SITES.items():driver.command(f'bp{index} {pc:x}')
            for index,api in enumerate(APIS,100):
                driver.command(f'bc {index}');driver.command(f'bu{index} ws2_32!{api}')
            for index,api in ((200,'kernel32!ExitProcess'),(201,'user32!MessageBoxA'),(202,'user32!MessageBoxW')):
                driver.command(f'bu{index} {api}')
            if self.network_strike:
                from crypto_runtime_observer import CryptoRuntimeObserver
                self.crypto_observer=CryptoRuntimeObserver(self.run)
                self.crypto_observer.arm(driver)
                if getattr(self,'c2s_strike',False):
                    driver.command('bp233 413e10');driver.command('bp234 40b010')
                    for index,pc in ((235,0x414091),(236,0x4141b1),(237,0x4141c9),(238,0x4141dd),(239,0x4141ec)):
                        driver.command(f'bp{index} {pc:x}')
                if getattr(self,'terminal',False):
                    for index,pc in ((240,0x414386),(241,0x40b0d9),(242,0x40b39a),(243,0x40b3a3)):
                        driver.command(f'bp{index} {pc:x}')
                if getattr(self,'server_list_probe',False):
                    for index,pc in ((245,0x406ee0),(246,0x406f0e),(247,0x414234),(248,0x414250)):
                        driver.command(f'bp{index} {pc:x}')
                for index,pc in ((220,0x410e20),(221,0x410e80),(222,0x410e9f),(223,0x410ec2),(224,0x411e9f)):
                    driver.command(f'bp{index} {pc:x}')
                for index,pc in ((228,0x413270),(229,0x4132ce),(230,0x413f2d)):
                    driver.command(f'bp{index} {pc:x}')
            if getattr(self, 'observe_login_entry', False):
                driver.command('bp394 404da0')
            if getattr(self,'town_entry_lab',False):
                driver.command('bp498 447440')
            if getattr(self,'diagnostic_quest_dialogue',False):
                driver.command('bp490 4c7f10')
                driver.command('bp492 4c8234')
                if getattr(self,'complete_npc_conversation',False):driver.command('bp495 4c9670')
            if getattr(self,'town_completed_quest_restore',False) or getattr(self,'town_battle_after_quest',False):
                driver.command('bp495 4c9670')
            if getattr(self, 'probe_server_confirm', False):
                driver.command('bp400 4053a8')
                driver.command('bp404 4148b9')
                driver.command('bp405 414963')
            if getattr(self,'diagnostic_battle_player_appearance',False):
                driver.command('bp449 4b0125')
            if getattr(self,'shared_visibility',False):
                driver.command('bp600 459a80')
                driver.command('bp602 459e70')
                driver.command('bp603 4565ab')
                driver.command('bp605 45198e')
                driver.command('bp606 402630')
            result['armed']=driver.command('bl');driver.command('sxe av')
            if getattr(self,'warning_input_trace',False):
                from warning_input_trace import arm
                arm(driver)
            if getattr(self,'pagefile_adapter',None):
                self.pagefile_adapter.arm(driver)
            for sequence in itertools.count() if getattr(self,'rendezvous',False) else range(8000 if getattr(self,'ui_world_movement',False) or getattr(self,'ui_npc_dialogue',False) or getattr(self,'remote_actor_probe_language',None) is not None or getattr(self,'shared_visibility',False) else 4000 if getattr(self,'diagnostic_battle_player_appearance',False) or getattr(self,'town_detour_path',False) or getattr(self,'town_auto_door',False) else 1000 if getattr(self,'observe_created_refresh',False) else 350):
                update_progress(self.run,self.events)
                stop=driver.command('g')
                if driver.interrupted:
                    if getattr(self,'gate',None) and self.gate.reason:
                        outcome=self.gate.reason;break
                    result['timeout_context']={'stop':stop,'threads':driver.command('~* k')}
                    result['timeout_context']['main_thread']=driver.command('~0s')
                    result['timeout_context']['wow64_stack']=driver.command('!wow64exts.k')
                    if getattr(self,'diagnostic_battle_animations',False) and 'socket_battle_entry' in result:
                        from pagefile_capacity_compat import memory,number
                        battle=result['socket_battle_entry']['battle']
                        try:
                            driver.command('.effmach x86')
                            result['timeout_battle_state']={name:number(driver,f'poi({battle+offset:x})') for name,offset in
                                (('stage',0x44),('result_received',0xa9df6bc),('manager_event',0x144c1c),
                                 ('control_sent',0xa9e9c44),('bulk_seen',0xa9e9c48),
                                 ('counter',0xa9e9c64),('completed_counter',0xa9e9c68),
                                 ('queue_gate',0xa9ea4c4),('queue_hold',0xa9df6c4),
                                 ('batch_ended',0xa9df6c0),('actions_expected',0xa94059c),
                                 ('actions_completed',0xa9405a0))}
                            result['timeout_battle_state']['actors']=[]
                            for slot in (0,14):
                                actor=number(driver,f'poi({battle+0x144938+0x38+slot*24:x})')
                                result['timeout_battle_state']['actors'].append({
                                    'slot':slot,'animation_hex':memory(driver,actor+0x1e7,5).hex(),
                                    'queue_hex':memory(driver,actor+0x233,8).hex(),
                                    'target_counter':memory(driver,actor+0x277,1).hex()})
                        except Exception as snapshot_error:
                            result['timeout_battle_snapshot_error']=str(snapshot_error)
                    outcome='HARD_TIMEOUT';break
                mode=driver.command('.effmach #')
                if 'x64' in mode:
                    self.events.append({'event_type':'NATIVE_STOP','stop':stop,'registers':driver.command('r')});outcome='NATIVE_STOP';break
                raw=driver.command('.printf "LAB_STOP pid=%x tid=%x pc=%p sp=%p ret=%p a0=%p a1=%p a2=%p a3=%p eax=%p time=%I64x\\n", @$tpid, @$tid, @eip, @esp, poi(@esp), poi(@esp+4), poi(@esp+8), poi(@esp+c), poi(@esp+10), @eax, @$dbgtime')
                event=parse_marker(raw);event.update(sequence=sequence,global_sequence=sequence,
                    native_timestamp=event.get('time'),timestamp=time.time(),run_id=name,native_stop=stop)
                self.events.append(event)
                driver.client_pid=event['pid']
                found=re.search(r'Breakpoint (\d+) hit',stop);index=int(found[1]) if found else None
                if (getattr(self,'ui_npc_follow_until',None) is not None and
                        index==424 and time.monotonic()>=self.ui_npc_follow_until):
                    from pagefile_capacity_compat import memory,number
                    world=result['world_initializer']['world_object']
                    ui=world+0xa7f2f6c
                    action='confirm' if self.ui_npc_follow_opcode==0x85 else 'cancel'
                    result['ui_npc_post_action']=dict(page_index=number(driver,'poi(5b7bf0)'),
                        page_count=number(driver,'poi(5b7bf4)'),
                        widget=int.from_bytes(memory(driver,ui+0x232dee,2),'little',signed=True),
                        observation_seconds=3,
                        scope='NATIVE_WORLD_FRAME_RETURN_AFTER_'+action.upper()+'_NO_CLIENT_EXCEPTION_OBSERVED')
                    write_json(self.run/f'ui-npc-post-{action}.json',result['ui_npc_post_action'])
                    outcome=f'NATIVE_UI_NPC_{action.upper()}_POST_SEND_STABLE';break
                if index in (510,511) and getattr(self,'observe_ui_npc_buttons',False):
                    from pagefile_capacity_compat import memory,number
                    ui=result['world_initializer']['world_object']+0xa7f2f6c
                    def dialogue_state():
                        return dict(page_index=number(driver,'poi(5b7bf0)'),
                                    page_count=number(driver,'poi(5b7bf4)'),
                                    widget=int.from_bytes(memory(driver,ui+0x232dee,2),'little',signed=True))
                    if index==510:
                        if number(driver,'@ecx')!=ui:raise ValueError('NPC UI button owner changed')
                        self.ui_npc_button_entry=dict(sequence=sequence,sp=event['sp'],return_address=event['ret'],
                            button=event['a0']&0xffff,event_flags=event['a1']&0xff,before=dialogue_state())
                        driver.command(f'bp511 {event["ret"]:x}')
                    else:
                        entry=self.ui_npc_button_entry
                        if event['sp']!=entry['sp']+12:raise ValueError('NPC UI button return ABI changed')
                        item=dict(entry,return_sequence=sequence,after=dialogue_state())
                        observed=result.setdefault('ui_npc_button_events',[])
                        observed.append(item)
                        write_json(self.run/f'ui-npc-button-{sequence:04}.json',item)
                        driver.command('bc 511')
                        if len(observed)>=128:driver.command('bc 510')
                        if (getattr(self,'ui_npc_dialogue',False) and
                                getattr(self,'ui_npc_stop',None)=='page' and
                                item['button']==3 and item['event_flags']&1 and
                                item['after']['page_index']>item['before']['page_index']):
                            result['ui_npc_page_advanced']=item
                            outcome='NATIVE_UI_NPC_PAGE_ADVANCED'
                            break
                    continue
                if index in (7,605,606,607) and getattr(self,'shared_visibility',False):
                    from pagefile_capacity_compat import memory,number
                    if index==7:
                        loads=result.setdefault('map_file_loads',[])
                        if len(loads)>=128:raise ValueError('Table file observation bound')
                        loads.append(dict(entry_sequence=sequence,owner=number(driver,'@ecx'),
                            source_hex=memory(driver,event['a0'],260).split(b'\0',1)[0].hex(),temporary=[]))
                        self.active_map_file=loads[-1]
                        driver.command(f'bp607 {event["ret"]:x}')
                    elif getattr(self,'active_map_file',None) is not None:
                        active=self.active_map_file
                        if index==605:active['open_result']=event['eax']
                        elif index==606:
                            active['temporary'].append(dict(sequence=sequence,handle=event['eax'],
                                path_hex=memory(driver,number(driver,'poi(@esp)'),260).split(b'\0',1)[0].hex()))
                        else:
                            active.update(return_sequence=sequence,return_value=event['eax'])
                            write_json(self.run/f'map-file-{len(result["map_file_loads"]):03d}.json',active)
                            self.active_map_file=None;driver.command('bc 607')
                    if index!=7:
                        event['event_type']='TABLE_FILE_TRACE'
                        continue
                if index==603 and getattr(self,'shared_visibility',False):
                    from pagefile_capacity_compat import memory,number
                    sections=result.setdefault('map_section_dispatch',[])
                    if len(sections)>=256:raise ValueError('Map section dispatch observation bound')
                    sections.append(dict(sequence=sequence,owner=number(driver,'@edi'),
                        loader_argument=number(driver,'poi(@esp+c)'),
                        section_hex=memory(driver,event['sp']+0x18,40).split(b'\0',1)[0].hex()))
                    event['event_type']='MAP_SECTION_DISPATCH'
                    continue
                if index in (600,601,602) and getattr(self,'shared_visibility',False):
                    from pagefile_capacity_compat import memory,number
                    trace=result.setdefault('map_catalog_trace',[])
                    owner=trace[-1]['owner'] if index==601 else number(driver,'@ecx')
                    entry=dict(stage={600:'LOADER_ENTRY',601:'LOADER_RETURN',602:'FIRST_BIND'}[index],
                               owner=owner,sequence=sequence,
                               count=int.from_bytes(memory(driver,owner+0xd2aba,2),'little',signed=True),
                               table=int.from_bytes(memory(driver,owner+0xd2abc,4),'little'))
                    trace.append(entry)
                    if index==600:
                        driver.command(f'bp601 {event["ret"]:x}')
                    elif index==601:
                        driver.command('bc 601')
                    else:
                        driver.command('bc 602')
                        if entry['count']==144 and entry['table']:
                            write_json(self.run/'catalog-ready.json',dict(entry,run_id=self.run.name,client_pid=driver.client_pid))
                    event['event_type']='MAP_CATALOG_'+entry['stage']
                    continue
                if index in (498,499) and getattr(self,'town_entry_lab',False):
                    from pagefile_capacity_compat import memory,number
                    if index==498:
                        manager=number(driver,'@ecx')
                        raw=memory(driver,manager+0x103c,8)
                        origin=[int.from_bytes(raw[i:i+4],'little',signed=True) for i in (0,4)]
                        entry={'manager':manager,'origin':origin,'caller':event['ret'],
                               'entry_sequence':sequence,'entry_sp':event['sp']}
                        result.setdefault('town_window_builds',[]).append(entry)
                        if len(result['town_window_builds'])>128:raise ValueError('Town window observation bound')
                        driver.command(f'bp499 {event["ret"]:x}')
                    else:
                        entry=result['town_window_builds'][-1]
                        if event['sp']!=entry['entry_sp']+4:raise ValueError('Town window return stack mismatch')
                        ox,oy=entry['origin']
                        if ox%21 or oy%21 or not (0<=ox//21<9 and 0<=oy//21<9):
                            raise ValueError('Town window center outside qualified map')
                        actual=memory(driver,entry['manager']+0x50,3969)
                        expected=self.sink.town_windows[(oy//21)*9+ox//21]['cells_hex']
                        mismatch=[i for i,v in enumerate(actual) if expected[2*i:2*i+2]!='??' and
                                  v!=int(expected[2*i:2*i+2],16)]
                        entry.update(return_sequence=sequence,known_cell_mismatches=len(mismatch),
                                     first_mismatches=mismatch[:16],center=[ox//21,oy//21])
                        driver.command('bc 499')
                        if mismatch:raise ValueError('Live town navigation differs from qualified static window')
                    continue
                if index==497 and getattr(self,'probe_town_guide_resource',False):
                    from current_npc_live_state import snapshot
                    state=result['town_resource_probe']
                    if event['sp']!=state['entry_sp']:raise ValueError('NPC resource thunk ABI mismatch')
                    after=snapshot(driver,result['world_initializer']['world_object'])
                    result['town_resource_return']=dict(event,state=after)
                    row=next(r for r in after['resources'] if r['ordinal']==19)
                    if row['loaded_slot']<0:raise ValueError('Native town resource load did not produce a slot')
                    driver.command('bc 497');driver.command(f'r eip={state["resume_pc"]:x}')
                    continue
                if index in (495,496) and (getattr(self,'complete_npc_conversation',False) or
                                           getattr(self,'town_completed_quest_restore',False) or
                                           getattr(self,'town_battle_after_quest',False)):
                    from pagefile_capacity_compat import memory,number
                    saved=getattr(self.sink,'restored_quest_journal',None)
                    if saved and len(result.get('journal_restore_returns',[]))<15:
                        if index==495:
                            slot=len(result.get('journal_restore_returns',[]))
                            expected=bytes.fromhex(saved['slots_hex'])
                            if slot>=15 or event['a0']!=slot or event['a1']!=int.from_bytes(expected[4*slot:4*slot+4],'little'):
                                raise ValueError('Restored journal differs from saved slot')
                            ui=number(driver,'@ecx')
                            result['journal_restore_entry']=dict(event,ui=ui,slots_hex=memory(driver,ui+0xc2104,60).hex())
                            driver.command('bc 495');driver.command(f'bp496 {event["ret"]:x}')
                        else:
                            entry=result['journal_restore_entry']
                            if event['sp']!=entry['sp']+12:raise ValueError('Restored journal ABI mismatch')
                            result.setdefault('journal_restore_returns',[]).append(dict(event,slot=entry['a0'],value=entry['a1'],
                                slots_hex=memory(driver,entry['ui']+0xc2104,60).hex()))
                            driver.command('bc 496')
                            if len(result['journal_restore_returns'])<15 or getattr(self,'town_quest_progress',False):
                                driver.command('bp495 4c9670')
                        continue
                    if index==495:
                        if 'npc_request_transport' not in result:continue
                        expected=((self.sink.town_guide_start_stage+len(result.get('town_completed_conversations',[]))+1)<<16)|1 if getattr(self,'town_quest_progress',False) else 1
                        if (getattr(self,'town_quest_progress',False) and
                                self.sink.town_guide_start_stage+len(result.get('town_completed_conversations',[]))>=2):
                            expected=0
                        if event['a0']!=0 or event['a1']!=expected:raise ValueError('Unexpected diagnostic journal slot/value')
                        ui=number(driver,'@ecx')
                        result['npc_journal_entry']=dict(event,ui=ui,
                            slots_hex=memory(driver,ui+0xc2104,60).hex())
                        driver.command('bc 495')
                        driver.command(f'bp496 {event["ret"]:x}')
                    else:
                        entry=result['npc_journal_entry']
                        if event['sp']!=entry['sp']+12:raise ValueError('Journal slot consumer ABI mismatch')
                        result['npc_journal_return']=dict(event,
                            slots_hex=memory(driver,entry['ui']+0xc2104,60).hex())
                        driver.command('bc 496')
                    continue
                if index in (500,501,502) and getattr(self,'town_map_probe',False):
                    from pagefile_capacity_compat import memory,number
                    from current_quest_live import map_panel_snapshot
                    state=result['town_map_probe']
                    if index in (501,502) and getattr(self,'town_scene_probe',False):
                        from current_scene_live import scene_snapshot
                        if index==501:
                            world=number(driver,'@ecx')
                            if world!=result['world_initializer']['world_object']:raise ValueError('Scene receiver owner mismatch')
                            body=memory(driver,event['a0'],8)
                            target_x=111 if getattr(self,'town_scene_relocate',False) else 110
                            expected=(0x10000|(target_x<<2)|(70<<17)).to_bytes(4,'little')
                            expected_body=(bytes.fromhex('c203000046001a00') if getattr(self,'town_scene_indoor_probe',False)
                                           else bytes.fromhex('02010000')+expected)
                            if getattr(self,'town_scene_return_probe',False):expected_body=bytes.fromhex('02010000b8018c00')
                            if body!=expected_body or event['a1']!=1:
                                raise ValueError('Scene receiver arguments mismatch')
                            result['town_scene_entry']=dict(event,body_hex=body.hex(),snapshot=scene_snapshot(driver,world))
                            driver.command('bc 501');driver.command(f'bp502 {event["ret"]:x}')
                        else:
                            entry=result['town_scene_entry']
                            if event['sp']!=entry['sp']+12:raise ValueError('Scene receiver ABI mismatch')
                            snapshot=scene_snapshot(driver,entry['snapshot']['world'])
                            result['town_scene_return']=dict(event,snapshot=snapshot,
                                body_hex=memory(driver,entry['a0'],8).hex())
                            target_x=111 if getattr(self,'town_scene_relocate',False) else 110
                            target=(2,15,2,17,13) if getattr(self,'town_scene_indoor_probe',False) else (2,4,0,target_x,70)
                            if getattr(self,'town_scene_return_probe',False):target=(2,4,0,110,70)
                            if (snapshot['area'],snapshot['scene'],snapshot['kind'],snapshot['x'],snapshot['y'])!=target:
                                raise ValueError('Scene receiver changed destination unexpectedly')
                            if snapshot['ring_hex']!='010001':raise ValueError('Scene receiver did not reset movement ring')
                            if snapshot['slot0_hex']!=entry['snapshot']['slot0_hex']:
                                raise ValueError('Scene probe changed inventory')
                            driver.command('bc 502')
                            if getattr(self,'town_return_after_battle',False):
                                driver.command('bp424 467bd7')
                        continue
                    if index==500:
                        if event['sp']!=state['entry_sp']:raise ValueError('Map request ABI mismatch')
                        count=number(driver,f'poi({state["net"]+0x36c4:x})')
                        if count!=5:raise ValueError('Map request did not queue one native25')
                        queued=memory(driver,state['net']+0x36c8,count)
                        if queued[:4]!=bytes.fromhex('25c11500'):raise ValueError('Unexpected native map request')
                        result['town_map_request_return']=dict(event,queued_hex=queued.hex())
                        driver.command('bc 500');driver.command(f'r eip={state["resume_pc"]:x}')
                    elif index==501:
                        ui=number(driver,'@ecx')
                        result['town_map_control_entry']=dict(event,snapshot=map_panel_snapshot(driver,ui))
                        if event['a0']&255!=1:raise ValueError('Map response argument mismatch')
                        driver.command('bc 501');driver.command(f'bp502 {event["ret"]:x}')
                    else:
                        entry=result['town_map_control_entry']
                        if event['sp']!=entry['sp']+8:raise ValueError('Map response ABI mismatch')
                        snapshot=map_panel_snapshot(driver,entry['snapshot']['ui'])
                        result['town_map_control_return']=dict(event,snapshot=snapshot)
                        if snapshot.get('flags',0)&0x30!=0x20:raise ValueError('Map candidate did not set panel state20')
                        if snapshot['slot0_hex']!=state['before']['slot0_hex']:raise ValueError('Map probe changed inventory')
                        driver.command('bc 502')
                    continue
                if index==493 and getattr(self,'probe_quest_confirm',False):
                    from pagefile_capacity_compat import memory,number
                    state=result['quest_confirm_probe']
                    if event['sp']!=state['entry_sp']:
                        raise ValueError('Quest confirm return ABI mismatch')
                    net=state['net']
                    count=number(driver,f'poi({net+0x36c4:x})')
                    if not 0<=count<=0xa00:raise ValueError('Quest queue outside native bounds')
                    result['quest_confirm_return']=dict(event,queued_length=count,
                        queued_hex=memory(driver,net+0x36c8,count).hex() if count else '')
                    if (getattr(self,'town_spawn_guides',False) and state['action']=='DIALOGUE_ADVANCE_OR_CONFIRM_NATIVE' and
                            count==0):
                        page_index=number(driver,'poi(5b7bf0)')
                        page_count=number(driver,'poi(5b7bf4)')
                        history=result.setdefault('town_dialogue_page_returns',[])
                        previous=history[-1]['page_index'] if history else state['page_index']
                        if not (page_index>previous and page_index<page_count<=64 and len(history)<63):
                            raise ValueError('Town dialogue did not advance a bounded native page')
                        history.append(dict(event,page_index=page_index,page_count=page_count,
                                            queued_length=0))
                        driver.command(f'r eip={state["page"]["address"]:x}')
                        continue
                    if getattr(self,'observe_quest_transport',False):
                        driver.command('bc 493')
                        driver.command(f'r eip={state["resume_pc"]:x}')
                        continue
                    outcome='NATIVE_QUEST_CONFIRM_RETURNED'
                    break
                if index in (490,491,492) and getattr(self,'diagnostic_quest_dialogue',False):
                    from pagefile_capacity_compat import memory,number
                    if index==490:
                        ui=number(driver,'@ecx')
                        payload=number(driver,'poi(@esp+4)')
                        result['quest_dialogue_entry']=dict(event,ui=ui,
                            payload_hex=memory(driver,payload,26).hex(),
                            widget_signed=int.from_bytes(memory(driver,ui+0x232dee,2),'little',signed=True))
                        driver.command('bc 490')
                        driver.command(f'bp491 {event["ret"]:x}')
                    elif index==492:
                        result['quest_dialogue_header']=dict(event,
                            request_word=number(driver,'wo(5b7bfa)'),reply_word=number(driver,'wo(5b7bf8)'))
                        driver.command('bc 492')
                    else:
                        entry=result['quest_dialogue_entry']
                        if event['sp']!=entry['sp']+8:raise ValueError('Quest dialogue return ABI mismatch')
                        result['quest_dialogue_return']=dict(event)
                        if getattr(self,'diagnostic_quest_npc',False):
                            from current_npc_live_state import snapshot
                            world=result['world_initializer']['world_object']
                            result['npc_after_spawn']=dict(snapshot(driver,world),sequence=sequence)
                            if getattr(self,'probe_npc_request',False) and 'quest_confirm_transport' in result:
                                if not getattr(self,'complete_npc_conversation',False):
                                    outcome='NATIVE_NPC_DIALOGUE_RESPONSE_RETURNED'
                                    break
                                for suffix in ('probe','return','transport'):
                                    result['npc_request_'+suffix]=result.pop('quest_confirm_'+suffix)
                        if getattr(self,'probe_quest_confirm',False) and 'quest_dialogue_header' in result:
                            from current_offline_client_run import install_owned_page
                            from current_quest_live import confirm_page
                            ui=entry['ui']
                            net=number(driver,f'poi({ui+0x86874:x})')
                            count=number(driver,f'poi({net+0x36c4:x})')
                            if not 0<=count<=0xa00:raise ValueError('Quest queue outside native bounds')
                            action='DIALOGUE_CONFIRM_C8500'
                            if getattr(self,'probe_npc_request',False) and 'npc_request_transport' not in result:
                                from current_quest_live import npc_request_page
                                entries=result['npc_after_spawn']['pools'][0]['entries']
                                if entries!=[dict(slot=0,identity=531,x=17,y=12)]:
                                    raise ValueError('NPC request requires exact observed diagnostic actor')
                                page=install_owned_page(driver,lambda address:npc_request_page(address,ui,entries[0]['identity']))
                                action='NPC_REQUEST_96750_SELECTION_BYPASSED'
                            else:
                                if getattr(self,'probe_quest_close',False):
                                    from current_quest_live import close_page
                                    page=install_owned_page(driver,lambda address:close_page(address,ui))
                                    action='DIALOGUE_CLOSE_C8350'
                                else:
                                    if getattr(self,'town_spawn_guides',False):
                                        from current_quest_live import advance_or_confirm_page
                                        page=install_owned_page(driver,lambda address:advance_or_confirm_page(address,ui))
                                        action='DIALOGUE_ADVANCE_OR_CONFIRM_NATIVE'
                                    else:
                                        page=install_owned_page(driver,lambda address:confirm_page(address,ui))
                            result['quest_confirm_probe']=dict(page=page,entry_sp=event['sp'],
                                action=action,
                                resume_pc=event['pc'],net=net,queued_before=count,
                                queued_hex_before=memory(driver,net+0x36c8,count).hex() if count else '',
                                page_index=number(driver,'poi(5b7bf0)'),
                                page_count=number(driver,'poi(5b7bf4)'),
                                scope='NATIVE_CALL_NOT_PHYSICAL_INPUT_NO_QUEST_AUTHORIZATION')
                            driver.command('bc 491')
                            driver.command(f'bp493 {page["return_trap"]:x}')
                            driver.command(f'r eip={page["address"]:x}')
                            continue
                        outcome=('NATIVE_QUEST_DIALOGUE_CONSUMER_RETURNED' if 'quest_dialogue_header' in result
                                 else 'NATIVE_QUEST_DIALOGUE_EARLY_RETURN')
                        break
                    continue
                if index in (455,456) and getattr(self,'diagnostic_battle_skill_settlement',False):
                    from pagefile_capacity_compat import memory
                    battle=result['socket_battle_entry']['battle']
                    result.setdefault('skill_target_mask_writes',[]).append({
                        'sequence':sequence,'pc':event['pc'],'watch':index-455,
                        'masks_hex':memory(driver,battle+0x144938+0x2f4,8).hex(),
                        'preceding_instructions':driver.command('ub @eip L5')})
                    continue
                if index==449 and getattr(self,'diagnostic_battle_player_appearance',False):
                    from pagefile_capacity_compat import memory,number
                    pointer=number(driver,'poi(@esp)')
                    path=bytearray()
                    for offset in range(260):
                        value=memory(driver,pointer+offset,1)[0]
                        if value==0:break
                        path.append(value)
                    else:raise ValueError('Native hotbar path is not bounded/NUL terminated')
                    result['native_hotbar_load']={'scope':'READ_ONLY_NATIVE_FILE_OPEN',
                                                 'path_hex':path.hex(),'sequence':sequence}
                    driver.command('bc 449')
                    driver.command('bp450 4b012a')
                    continue
                if index==450 and getattr(self,'diagnostic_battle_player_appearance',False):
                    result['native_hotbar_load']['opened']=bool(event['eax'])
                    result['native_hotbar_load']['return_sequence']=sequence
                    driver.command('bc 450')
                    continue
                if index==451 and getattr(self,'probe_socket_skill_select',False):
                    from pagefile_capacity_compat import memory,number
                    state=result['socket_skill_select_probe']
                    raw=bytes.fromhex(state['page']['hex'])
                    if event['sp']!=state['entry_sp'] or memory(driver,state['page']['address'],len(raw))!=raw:
                        raise ValueError('Native skill selection stack or immutable page mismatch')
                    battle=result['socket_battle_entry']['battle']
                    selected=int.from_bytes(memory(driver,battle+0xa9df73c,4),'little',signed=True)
                    mode=number(driver,f'poi({battle+0x46c:x})')
                    result['socket_skill_select_return']={
                        'sequence':sequence,'selected_index':selected,'battle_action_mode':mode,
                        'target_masks_hex':memory(driver,battle+0x434,8).hex(),
                        'target_setup_hex':memory(driver,battle+0x45c,16).hex(),
                        'target_counts_hex':memory(driver,event['sp']-4,2).hex(),
                        'scope':'NATIVE_CALL_NOT_PHYSICAL_INPUT_NOT_CAST'}
                    if selected!=0 or mode!=3:
                        raise ValueError('Native skill selection did not select the fixture entry')
                    if getattr(self,'diagnostic_battle_skill_settlement',False) and (
                            result['socket_skill_select_return']['target_masks_hex']!='0100000001000000' or
                            result['socket_skill_select_return']['target_counts_hex']!='0101'):
                        raise ValueError('Living diagnostic participants disappeared from native skill targeting')
                    if getattr(self,'probe_socket_skill_command',False):
                        from current_offline_client_run import install_owned_page
                        from current_offline_vitals_live import action_call_page
                        target=1 if getattr(self,'diagnostic_battle_revival',False) else 14
                        page=install_owned_page(driver,lambda address:action_call_page(address,battle,skill=True,target=target))
                        result['socket_skill_command_probe']={'page':page,'entry_sp':event['sp'],
                            'target':target,'scope':'NATIVE_CALL_EXPLICIT_TARGET_NOT_PHYSICAL_INPUT'}
                        driver.command('bc 451')
                        driver.command(f'bp452 {page["return_trap"]:x}')
                        driver.command(f'r eip={page["address"]:x}')
                        continue
                    outcome='NATIVE_SOCKET_SKILL_SELECTED'
                    break
                if index==452 and getattr(self,'probe_socket_skill_command',False):
                    from pagefile_capacity_compat import memory,number
                    state=result['socket_skill_command_probe']
                    raw=bytes.fromhex(state['page']['hex'])
                    if event['sp']!=state['entry_sp'] or event['eax']!=1 or memory(driver,state['page']['address'],len(raw))!=raw:
                        raise ValueError('Native skill command ABI or page mismatch')
                    battle=result['socket_battle_entry']['battle']
                    net=number(driver,f'poi({battle+0x10:x})')
                    queued=number(driver,f'poi({net+0x36c4:x})')
                    if not 0<queued<=0xa00:raise ValueError('Native skill command queue missing or out of bounds')
                    result['socket_skill_command_return']={'sequence':sequence,'queued_length':queued,
                        'queued_logical_hex':memory(driver,net+0x36c8,queued).hex(),
                        'controls_hex':memory(driver,battle+0xa9e9c34,12).hex(),
                        'scope':'NATIVE_QUEUE_ONLY_NOT_SERVER_SETTLEMENT'}
                    from current_offline_vitals_live import control_snapshot
                    result['socket_skill_command_return']['control_state']=control_snapshot(driver,battle)
                    result.setdefault('socket_skill_commands',[]).append(dict(result['socket_skill_command_return']))
                    if getattr(self,'shared_visibility',False) and self.sink.document.get('skill_battle') and len(result['socket_skill_commands'])==1:
                        write_json(self.sink.manifest.parent/'peer-0-battle-started.json',
                            dict(run_id=self.run.name,client_pid=driver.client_pid,event=result['socket_skill_command_return']))
                        until=time.monotonic()+20
                        while not (self.sink.manifest.parent/'peer-1-fight.json').exists():
                            if time.monotonic()>=until or self.sink.process.poll() is not None:
                                raise TimeoutError('Shared observer did not see Fight before skill')
                            time.sleep(.1)
                    if getattr(self,'diagnostic_battle_revival',False):
                        driver.command('bc 452')
                        driver.command('bp478 517230')
                        driver.command('bp480 5267c0')
                        driver.command(f'r eip={result["socket_skill_select_probe"]["resume_pc"]:x}')
                        continue
                    if getattr(self,'diagnostic_battle_skill_settlement',False):
                        driver.command('bc 452')
                        driver.command('bp453 5173a0')
                        if getattr(self,'diagnostic_battle_animations',False):
                            driver.command('bp447 5294b6')
                        driver.command(f'r eip={result["socket_skill_select_probe"]["resume_pc"]:x}')
                        continue
                    outcome='NATIVE_SOCKET_SKILL_COMMAND_QUEUED'
                    break
                if index in (457,458) and getattr(self,'diagnostic_world_resources',False):
                    if getattr(self,'expect_no_world_resources',False):
                        raise ValueError('Unexpected resource update for the missing-row fixture')
                    from pagefile_capacity_compat import memory,number
                    if index==457:
                        ui=number(driver,'@ecx')
                        role=number(driver,f'poi({ui+0x86888:x})')
                        if not role:raise ValueError('World resource consumer has no role owner')
                        result['world_resource_update_entry']={
                            'ui':ui,'source':role,'sequence':sequence,
                            'body_hex':memory(driver,number(driver,'poi(@esp+4)'),16).hex(),
                            'role_snapshot_hex':memory(driver,role,0x94).hex(),
                            'before_hex':memory(driver,role+0x5c,16).hex()}
                        driver.command('bc 457')
                        driver.command(f'bp458 {event["ret"]:x}')
                    else:
                        entry=result['world_resource_update_entry']
                        result['world_resource_update_return']={
                            'sequence':sequence,'values_hex':memory(driver,entry['source']+0x5c,16).hex(),
                            'role_snapshot_hex':memory(driver,entry['source'],0x94).hex()}
                        driver.command('bc 458')
                    continue
                if index in (453,454) and getattr(self,'diagnostic_battle_skill_settlement',False):
                    from pagefile_capacity_compat import memory,number
                    battle=result['socket_battle_entry']['battle']
                    if index==453:
                        if number(driver,'@ecx')!=battle:raise ValueError('Skill vitals receiver object mismatch')
                        logical=memory(driver,number(driver,'poi(@esp+4)'),17)
                        if logical[0]!=0x86 or (logical[1],logical[2]) not in ((1,0),(0,14),(0,0)):
                            raise ValueError('Unexpected skill settlement record')
                        event['logical_hex']=logical.hex()
                        result['skill_vitals_pending']=dict(event)
                        driver.command('bc 453')
                        driver.command(f'bp454 {event["ret"]:x}')
                        continue
                    entry=result.pop('skill_vitals_pending')
                    if event['sp']!=entry['sp']+8:raise ValueError('Skill vitals return ABI mismatch')
                    logical=bytes.fromhex(entry['logical_hex']);target=logical[2]
                    pointer=number(driver,f'poi({battle+0x144938+0x38+target*24:x})')
                    values=memory(driver,pointer+0xde8,16)
                    observed={'logical_hex':logical.hex(),'actor_vitals_hex':values.hex(),'sequence':sequence}
                    if getattr(self,'observe_socket_defeat',False):
                        observed['entity_word_1a_hex']=memory(driver,pointer+0x1a,2).hex()
                        observed['entity_pointer']=pointer
                    if getattr(self,'diagnostic_battle_mp_refusal',False):
                        if logical[:3]!=bytes((0x86,1,0)) or values!=bytes.fromhex('64000000070000007800000050000000'):
                            raise ValueError('Refused skill changed native player vitals')
                        result['socket_mp_refusal']=observed
                        self.probe_socket_skill_select=False
                        self.probe_socket_battle_action=True
                        self.observe_socket_retaliation=True
                        driver.command('bc 454')
                        driver.command('bp435 517590')
                        continue
                    records=result.setdefault('socket_skill_settlement',[]);records.append(observed)
                    round_number=(len(records)-1)//3+1
                    defeat=getattr(self,'observe_socket_defeat',False)
                    player_hp=getattr(self,'initial_battle_hp',100)-12*round_number
                    kind=logical[1];expected={(1,0):getattr(self,'initial_battle_mp',50)-8*round_number,(0,14):getattr(self,'initial_enemy_hp',150)-54*round_number,(0,0):max(0,player_hp) if defeat else player_hp}[(kind,target)]
                    terminal=getattr(self,'diagnostic_battle_terminal',False) and round_number==getattr(self,'diagnostic_battle_rounds',1)
                    if terminal and (kind,target)==(0,14):expected=0
                    if int.from_bytes(values[4*kind:4*kind+4],'little')!=expected:
                        raise ValueError('Native skill settlement value mismatch')
                    driver.command('bc 454')
                    if defeat and (kind,target)==(0,0):
                        if round_number!=1 or expected!=0 or [(bytes.fromhex(x['logical_hex'])[1],bytes.fromhex(x['logical_hex'])[2]) for x in records]!=[(1,0),(0,14),(0,0)]:
                            raise ValueError('Defeat must follow exactly one skill and lethal retaliation')
                        result['socket_defeat_vitals']=list(records)
                        driver.command('bp440 518bf0')
                        continue
                    if terminal and len(records)==3*(round_number-1)+2:
                        if [(bytes.fromhex(x['logical_hex'])[1],bytes.fromhex(x['logical_hex'])[2]) for x in records[-2:]]!=[(1,0),(0,14)]:
                            raise ValueError('Terminal skill must debit MP then settle enemy death without retaliation')
                        result['socket_skill_terminal_vitals']=list(records[-2:])
                        driver.command('bp440 518bf0')
                        continue
                    if len(records)%3==0:
                        if [(bytes.fromhex(x['logical_hex'])[1],bytes.fromhex(x['logical_hex'])[2]) for x in records[-3:]]!=[(1,0),(0,14),(0,0)]:
                            raise ValueError('Skill settlement order mismatch')
                        result.setdefault('socket_skill_rounds',[]).append({
                            'round':round_number,'grant_entry':dict(result['socket_grant_entry']),
                            'grant_return':dict(result['socket_grant_return']),
                            'selection':dict(result['socket_skill_select_return']),
                            'command':dict(result['socket_skill_command_return']),
                            'vitals':list(records[-3:])})
                        if round_number<getattr(self,'diagnostic_battle_rounds',1):
                            driver.command('bp435 517590')
                            continue
                        if getattr(self,'diagnostic_battle_animations',False):continue
                        outcome='NATIVE_SOCKET_SKILL_VITALS_SETTLED'
                        break
                    driver.command('bp453 517230')
                    continue
                if index in (482,483,484) and getattr(self,'diagnostic_battle_revival',False):
                    from pagefile_capacity_compat import memory,number
                    battle=result['socket_battle_entry']['battle']
                    if index==482:
                        state=result['revival_followup_probe']
                        if event['sp']!=state['entry_sp'] or event['eax']!=1:
                            raise ValueError('Followup basic-call ABI mismatch')
                        net=number(driver,f'poi({battle+0x10:x})')
                        length=number(driver,f'poi({net+0x36c4:x})')
                        if not 0<length<=0xa00:raise ValueError('Followup command queue missing')
                        result['revival_followup_command']={'sequence':sequence,
                            'logical_hex':memory(driver,net+0x36c8,length).hex()}
                        driver.command('bc 482')
                        driver.command('bp483 517230')
                        driver.command(f'r eip={state["resume_pc"]:x}')
                        continue
                    if index==483:
                        logical=memory(driver,number(driver,'poi(@esp+4)'),17)
                        if number(driver,'@ecx')!=battle or logical[:3]!=bytes((0x86,0,14)):
                            raise ValueError('Unexpected post-revival damage target')
                        result['revival_followup_damage_entry']={'sequence':sequence,'sp':event['sp'],'logical_hex':logical.hex()}
                        driver.command('bc 483')
                        driver.command(f'bp484 {event["ret"]:x}')
                        continue
                    if event['sp']!=result['revival_followup_damage_entry']['sp']+8:
                        raise ValueError('Post-revival damage receiver stack mismatch')
                    result['revival_followup_damage']={'sequence':sequence,'actors':[
                        {'slot':slot,'vitals_hex':memory(driver,number(driver,f'poi({battle+0x144938+0x38+slot*24:x})')+0xde8,16).hex()}
                        for slot in (0,1,14)]}
                    driver.command('bc 484')
                    driver.command('bp447 5294b6')
                    if getattr(self,'diagnostic_battle_terminal',False):
                        driver.command('bp440 518bf0')
                    continue
                if index in (480,481) and getattr(self,'diagnostic_battle_revival',False):
                    from pagefile_capacity_compat import memory,number
                    if index==480:
                        manager=number(driver,'@ecx')
                        actor=number(driver,'poi(@esp+4)')
                        argument=number(driver,'poi(@esp+8)')
                        battle=result['socket_battle_entry']['battle']
                        if manager!=battle+0x144938 or actor!=number(driver,f'poi({manager+0x38+24:x})') or argument!=89:
                            raise ValueError('Revival consumer manager/ally/state mismatch')
                        result['revival_native_consumer_entry']={'sequence':sequence,'actor':actor,
                            'manager':manager,'argument':argument,'sp':event['sp'],
                            'target_masks_hex':memory(driver,manager+0x2f4,8).hex(),
                            'state_hex':memory(driver,actor+0x1de,16).hex(),
                            'vitals_hex':memory(driver,actor+0xde8,16).hex()}
                        driver.command('bc 480')
                        driver.command(f'bp481 {event["ret"]:x}')
                    else:
                        actor=result['revival_native_consumer_entry']['actor']
                        if event['sp']!=result['revival_native_consumer_entry']['sp']+12:
                            raise ValueError('Revival consumer return stack mismatch')
                        manager=result['revival_native_consumer_entry']['manager']
                        result['revival_native_consumer_return']={'sequence':sequence,
                            'target_masks_hex':memory(driver,manager+0x2f4,8).hex(),
                            'state_hex':memory(driver,actor+0x1de,16).hex(),
                            'vitals_hex':memory(driver,actor+0xde8,16).hex()}
                        driver.command('bc 481')
                    continue
                if index in (478,479) and getattr(self,'diagnostic_battle_revival',False):
                    from pagefile_capacity_compat import memory,number
                    battle=result['socket_battle_entry']['battle']
                    if index==478:
                        logical=memory(driver,number(driver,'poi(@esp+4)'),17)
                        if logical[:3]!=bytes((0x86,0,1)) or number(driver,'@ecx')!=battle:
                            raise ValueError('Unexpected revival HP projection')
                        result['revival_hp_entry']={'logical_hex':logical.hex(),'sequence':sequence,'sp':event['sp']}
                        driver.command('bc 478')
                        driver.command(f'bp479 {event["ret"]:x}')
                        continue
                    if event['sp']!=result['revival_hp_entry']['sp']+8:
                        raise ValueError('Revival HP receiver stack mismatch')
                    states=[]
                    for slot in (0,1):
                        actor=number(driver,f'poi({battle+0x144938+0x38+slot*24:x})')
                        states.append({'slot':slot,'vitals_hex':memory(driver,actor+0xde8,16).hex(),
                            'presentation_state':memory(driver,actor+0x1eb,1)[0],
                            'pending_state':memory(driver,actor+0x232,1)[0]})
                    result['revival_cast_projection']={'sequence':sequence,'actors':states}
                    driver.command('bc 479')
                    driver.command('bp447 5294b6')
                    continue
                if index==447 and getattr(self,'diagnostic_battle_animations',False):
                    from pagefile_capacity_compat import number,memory
                    manager=result['socket_battle_entry']['battle']+0x144938
                    if number(driver,'@edi')!=manager:raise ValueError('Animation completion manager mismatch')
                    expected=number(driver,f'poi({manager+0xa7fbc64:x})')
                    completed=number(driver,f'poi({manager+0xa7fbc68:x})')
                    if expected and expected<0x80000000:
                        elapsed=number(driver,'@eax')
                        signed_completed=completed if completed<0x80000000 else completed-0x100000000
                        event.update(event_type='ANIMATION_BATCH_COMPLETION',expected=expected,
                                     completed=signed_completed,elapsed_ms=elapsed,
                                     timeout_fallback=signed_completed<expected)
                        result.setdefault('animation_batch_completions',[]).append(dict(event))
                        if (getattr(self,'shared_visibility',False) and self.sink.document.get('hold_skill_disconnect') and
                            len(result['animation_batch_completions'])==2):
                            if any(v['timeout_fallback'] for v in result['animation_batch_completions']):
                                raise ValueError('Skill disconnect requires natural animation completion')
                            write_json(self.sink.manifest.parent/'peer-0-skill-held.json',
                                dict(run_id=self.run.name,client_pid=driver.client_pid,
                                     animations=result['animation_batch_completions'],settlement=result['socket_skill_settlement']))
                            until=time.monotonic()+60
                            while time.monotonic()<until and self.sink.process.poll() is None:time.sleep(.1)
                            raise TimeoutError('Skill disconnect owner did not stop this probe')
                        if getattr(self,'diagnostic_battle_revival',False):
                            driver.command('bc 447')
                            driver.command('bp448 5294c7')
                            continue
                        stop_exchange=2 if getattr(self,'stop_after_second_checkpoint',False) else (1 if getattr(self,'stop_after_first_checkpoint',False) else 0)
                        if stop_exchange and len(result['animation_batch_completions'])==2*stop_exchange:
                            if any(v['timeout_fallback'] for v in result['animation_batch_completions']):
                                raise ValueError('Interrupted checkpoint requires natural animation completion')
                            import sqlite3
                            with sqlite3.connect((self.run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as check:
                                rows=check.execute('SELECT document,resource_revision FROM battle_checkpoints').fetchall()
                                if len(rows)!=1:raise ValueError('Missing exchange checkpoint')
                                checkpoint=json.loads(rows[0][0])
                                if (checkpoint['state'],checkpoint['revision'],rows[0][1])!=('active',2*stop_exchange+1,stop_exchange+3):
                                    raise ValueError('Checkpoint is not requested completed exchange')
                                if check.execute('SELECT count(*) FROM battle_settlements').fetchone()[0]:
                                    raise ValueError('Interrupted battle unexpectedly settled')
                            result['interrupted_checkpoint']={'battle_id':checkpoint['id'],'battle_revision':checkpoint['revision'],
                                'resource_revision':rows[0][1],'completed_exchanges':stop_exchange,
                                'scope':'AFTER_TWO_ANIMATIONS_BEFORE_NEXT_ACTION_NOT_RECEIPT_ACCEPTANCE' if stop_exchange==1 else
                                        'AFTER_FOUR_ANIMATIONS_BEFORE_NEXT_ACTION_NOT_RECEIPT_ACCEPTANCE'}
                            outcome='NATIVE_FIRST_EXCHANGE_CHECKPOINT_CAPTURED' if stop_exchange==1 else 'NATIVE_SECOND_EXCHANGE_CHECKPOINT_CAPTURED'
                            break
                        skill=getattr(self,'diagnostic_battle_skill_settlement',False) and 'socket_mp_refusal' not in result
                        if skill and len(result['animation_batch_completions'])==1:
                            actor=number(driver,f'poi({manager+0x38:x})')
                            definition=number(driver,f'poi({actor+0xec4:x})')
                            result['skill_animation_definition_hex']=memory(driver,definition,2).hex() if definition else None
                            if result['skill_animation_definition_hex']!='0100':
                                raise ValueError('Skill animation did not retain selected native definition')
                        terminal=getattr(self,'diagnostic_battle_terminal',False)
                        required=2*getattr(self,'diagnostic_battle_rounds',1) if (getattr(self,'observe_socket_retaliation',False) or skill) and not terminal else 1
                        if terminal and skill:required=2*getattr(self,'diagnostic_battle_rounds',1)-1
                        if getattr(self,'observe_socket_defeat',False):required=2
                        if len(result['animation_batch_completions'])>=required:
                            driver.command('bc 447')
                            if not terminal and (getattr(self,'observe_socket_retaliation',False) or skill):driver.command('bp448 5294c7')
                    continue
                if index==448 and getattr(self,'diagnostic_battle_animations',False):
                    event.update(event_type='ANIMATION_FINALIZATION_RETURN')
                    result['animation_finalization_return']=dict(event)
                    driver.command('bc 448')
                    if getattr(self,'diagnostic_battle_revival',False) and result.get('revival_followup_damage'):
                        result['revival_followup_animation_return']=dict(event)
                        result['revival_followup_receipt_observation']=True
                        if getattr(self,'diagnostic_resume_checkpoint',False):
                            rounds=result.setdefault('revival_resumed_rounds',[])
                            rounds.append({'command':result['revival_followup_command'],
                                           'damage':result['revival_followup_damage'],
                                           'animation_return':dict(event)})
                            if len(rounds)<getattr(self,'diagnostic_battle_rounds',1):
                                driver.command('bp435 517590')
                        continue
                    if getattr(self,'diagnostic_battle_revival',False) and result.get('revival_cast_projection'):
                        from pagefile_capacity_compat import memory,number
                        battle=result['socket_battle_entry']['battle']
                        states=[]
                        for slot in (0,1):
                            actor=number(driver,f'poi({battle+0x144938+0x38+slot*24:x})')
                            states.append({'slot':slot,'vitals_hex':memory(driver,actor+0xde8,16).hex(),
                                'presentation_state':memory(driver,actor+0x1eb,1)[0],
                                'pending_state':memory(driver,actor+0x232,1)[0]})
                        result['revival_animation_state']={'sequence':sequence,'actors':states}
                        if getattr(self,'diagnostic_battle_rounds',1)==2:
                            result['revival_await_followup_grant']=True
                            driver.command('bp435 517590')
                            continue
                        outcome='NATIVE_REVIVAL_ANIMATION_OBSERVED'
                        break
                    if getattr(self,'diagnostic_battle_revival',False):
                        from pagefile_capacity_compat import memory,number
                        battle=result['socket_battle_entry']['battle']
                        actor=number(driver,f'poi({battle+0x144938+0x38+24:x})')
                        result['revival_death_state']={'actor':actor,'sequence':sequence,
                            'vitals_hex':memory(driver,actor+0xde8,16).hex(),
                            'presentation_state':memory(driver,actor+0x1eb,1)[0],
                            'pending_state':memory(driver,actor+0x232,1)[0]}
                        result['revival_waiting_for_regrant']=True
                        from current_offline_vitals_live import control_snapshot
                        result['revival_post_death_controls']=control_snapshot(driver,battle)
                        if result.get('revival_early_regrant'):
                            from current_offline_client_run import install_owned_page
                            from current_offline_vitals_live import skill_select_call_page
                            page=install_owned_page(driver,lambda address:skill_select_call_page(address,battle))
                            result['socket_skill_select_probe']={'page':page,'entry_sp':event['sp'],
                                'resume_pc':event['pc'],'scope':'NATIVE_CALL_AFTER_OBSERVED_GRANT_AND_ANIMATION'}
                            self.probe_socket_skill_select=True
                            self.probe_socket_skill_command=True
                            driver.command(f'bp451 {page["return_trap"]:x}')
                            driver.command(f'r eip={page["address"]:x}')
                            continue
                        driver.command('bp435 517590')
                        continue
                    if getattr(self,'diagnostic_battle_skill_settlement',False) and 'socket_mp_refusal' not in result:
                        if len(result.get('socket_skill_settlement',[]))!=3*getattr(self,'diagnostic_battle_rounds',1):
                            raise ValueError('Skill animation finalized before required vitals')
                        outcome=('NATIVE_SOCKET_SKILL_ANIMATION_TIMEOUT_FALLBACK' if any(
                            item['timeout_fallback'] for item in result['animation_batch_completions'])
                            else 'NATIVE_SOCKET_SKILL_ANIMATIONS_COMPLETED')
                        break
                    if len(result.get('socket_completed_rounds',[]))!=getattr(self,'diagnostic_battle_rounds',1):
                        raise ValueError('Animation completion before required HP exchanges')
                    outcome=('NATIVE_SOCKET_ANIMATION_TIMEOUT_FALLBACK' if any(
                        item['timeout_fallback'] for item in result['animation_batch_completions'])
                        else 'NATIVE_SOCKET_ANIMATION_ROUNDS_COMPLETED')
                    break
                if index in (444,445,446) and getattr(self,'observe_socket_battle_exit',False):
                    from pagefile_capacity_compat import number
                    battle=result['socket_battle_entry']['battle']
                    if index==444:
                        event.update(event_type='SOCKET_BATTLE_CLEANUP_ENTRY',
                            stage=number(driver,f'poi({battle+0x44:x})'))
                        if event['stage']!=5:raise ValueError('Battle cleanup did not follow result stage5')
                        result['socket_battle_cleanup_entry']=dict(event)
                        driver.command('bc 444')
                        continue
                    if index==445:
                        if 'socket_battle_cleanup_entry' not in result or event['sp']!=result['socket_battle_cleanup_entry']['sp']+0x68:
                            raise ValueError('Battle loop return did not match cleanup stack')
                        event.update(event_type='SOCKET_BATTLE_LOOP_RETURN')
                        result['socket_battle_loop_return']=dict(event)
                        driver.command('bc 445')
                        driver.command('bp446 467860')
                        continue
                    event.update(event_type='SOCKET_POST_BATTLE_WORLD_LOOP_ENTRY',world=number(driver,'@ecx'))
                    result['socket_post_battle_world_loop_entry']=dict(event)
                    if 'world_resource_before_battle' in result:
                        from pagefile_capacity_compat import memory
                        prior=result['world_resource_before_battle']
                        source=number(driver,f'poi({prior["ui"]+0x86888:x})')
                        if not source:raise ValueError('Post-battle world resource owner missing')
                        result['world_resource_after_battle']={
                            'ui':prior['ui'],'source':source,'sequence':sequence,
                            'hp_maxhp_mp_maxmp_hex':memory(driver,source+0x5c,16).hex(),
                            'same_source':source==prior['source'],
                            'scope':'READ_ONLY_ROLE_SOURCE_NOT_VISUAL_HUD_ACCEPTANCE'}
                    if getattr(self,'probe_supply_use',False):
                        if event['world']!=result['world_initializer']['world_object']:
                            raise ValueError('Post-battle supply world owner changed')
                        driver.command('bc 446')
                        driver.command('bp423 467bca')
                        driver.command('bp424 467bd7')
                        continue
                    if getattr(self,'probe_post_battle_movement',False):
                        if event['world']!=result['world_initializer']['world_object']:
                            raise ValueError('Post-battle world owner changed')
                        if getattr(self,'shared_visibility',False) and self.sink.document.get('post_battle_movement'):
                            write_json(self.sink.manifest.parent/'peer-0-battle-returned.json',
                                dict(run_id=self.run.name,client_pid=driver.client_pid,event=event))
                        self.probe_movement_step=True
                        self.movement_sequence_offset=len(result.get('movement_steps',[]))
                        self.movement_steps=3
                        if getattr(self,'town_battle_after_quest',False):
                            # CUSTOM-0028: the completed indoor battle is now the
                            # sole observer path; do not re-enter town restore probes.
                            self.restore_town_database=None
                            self.town_spawn_guides=False
                            self.town_scene_follow_move=False
                            self.diagnostic_quest_dialogue=False
                            self.probe_npc_request=False
                            result.pop('quest_confirm_transport',None)
                            self.town_post_battle_movement=True
                            if getattr(self,'town_fresh_spawn',False):
                                self.sink.town_start=(18,12)
                                result['pre_battle_movement_steps']=result.pop('movement_steps',[])
                                result.pop('movement_step',None)
                                self.movement_sequence_offset=0
                        driver.command('bc 446')
                        driver.command('bp423 467bca')
                        driver.command('bp424 467bd7')
                        continue
                    if getattr(self,'town_door_after_battle',False):
                        if event['world']!=result['world_initializer']['world_object']:
                            raise ValueError('Post-battle door world owner changed')
                        self.restore_town_database=None
                        self.town_spawn_guides=False
                        self.town_post_battle_movement=True
                        self.indoor_door_probe=True
                        result['door_probe']=dict(index=0,
                            path=[[17,13],[16,14],[15,15],[14,16],[14,17],[15,18],[16,19],[16,20]],
                            started=time.monotonic(),
                            scope='CUSTOM-0028_POST_BATTLE_NATIVE_PATH_TO_CUSTOM_0025_DOOR')
                        driver.command('bc 446')
                        driver.command('bp424 467bd7')
                        continue
                    if getattr(self,'town_return_after_battle',False):
                        if event['world']!=result['world_initializer']['world_object']:
                            raise ValueError('Post-battle return world owner changed')
                        self.restore_town_database=None
                        self.town_spawn_guides=False
                        self.town_post_battle_movement=True
                        self.town_post_battle_return_pending=time.monotonic()
                        driver.command('bc 446')
                        driver.command('bp424 467bd7')
                        continue
                    outcome=('NATIVE_SOCKET_DEFEAT_RETURNED_TO_WORLD_LOOP' if getattr(self,'observe_socket_defeat',False)
                             else 'NATIVE_SOCKET_BATTLE_RETURNED_TO_WORLD_LOOP')
                    if getattr(self,'shared_visibility',False) and self.sink.document.get('observe_battle'):
                        folder=self.sink.manifest.parent
                        write_json(folder/'peer-0-battle-returned.json',dict(run_id=self.run.name,client_pid=driver.client_pid,event=event))
                        until=time.monotonic()+20
                        while not (folder/'peer-1-fight-cleared.json').exists():
                            if time.monotonic()>=until or self.sink.process.poll() is not None:
                                raise TimeoutError('Shared observer did not clear Fight')
                            time.sleep(.1)
                    break
                if index in (442,443) and getattr(self,'observe_socket_outcome_panel',False):
                    from pagefile_capacity_compat import memory,number
                    battle=result['socket_battle_entry']['battle']
                    ui=number(driver,f'poi({battle+0x20:x})')
                    if index==442:
                        if number(driver,'@ecx')!=ui:raise ValueError('Outcome panel owner mismatch')
                        event.update(event_type='SOCKET_OUTCOME_PANEL_ENTRY',panel_owner=ui)
                        result['socket_outcome_panel_entry']=dict(event)
                        driver.command('bc 442')
                        driver.command(f'bp443 {event["ret"]:x}')
                        continue
                    entry=result['socket_outcome_panel_entry']
                    if event['sp']!=entry['sp']+4:raise ValueError('Outcome panel ABI mismatch')
                    event.update(event_type='SOCKET_OUTCOME_PANEL_RETURN',
                        panel_latch=number(driver,f'poi({battle+0xa9e9c50:x})'),
                        panel_mode=number(driver,f'poi({ui+0x23d620:x})'),
                        handles_hex=memory(driver,ui+0x232df0,4).hex())
                    if event['panel_latch']!=1:raise ValueError('Outcome panel latch missing')
                    result['socket_outcome_panel_return']=dict(event)
                    if getattr(self,'observe_socket_battle_exit',False):
                        driver.command('bc 443')
                        driver.command('bp444 515c40')
                        driver.command('bp445 4658de')
                        continue
                    outcome='NATIVE_SOCKET_OUTCOME_PANEL_FUNCTION_RETURNED'
                    break
                if index in (463,464) and getattr(self,'diagnostic_level_snapshot',False):
                    from pagefile_capacity_compat import memory,number
                    if index==463:
                        sequence=len(result.get('role_level_returns',[]))
                        if sequence>1:raise ValueError('Unexpected extra level snapshot')
                        total=getattr(self,'initial_experience',0)+(self.diagnostic_battle_experience if sequence else 0)
                        span=self.diagnostic_progress_span
                        level=3 if total>=3*span else (2 if total>=span else 1)
                        progress=10000 if level==3 else ((total-span)*10000//(2*span) if level==2 else total*10000//span)
                        expected=bytearray(24);expected[0]=level
                        for offset in (4,6,8,10):expected[offset]=10
                        expected[12:14]=progress.to_bytes(2,'little');expected[16]=120;expected[20]=80
                        ui=number(driver,'@ecx');role=number(driver,f'poi({ui+0x86888:x})')
                        body=memory(driver,number(driver,'poi(@esp+4)'),24)
                        if body!=bytes(expected):raise ValueError('Level snapshot differs from committed fixture')
                        event.update(event_type='ROLE_LEVEL_ENTRY',level_sequence=sequence,ui_pointer=ui,role=role,
                                     body_hex=body.hex(),expected_level=level,expected_progress=progress)
                        result['role_level_entry']=dict(event)
                        result.setdefault('role_level_entries',[]).append(dict(event))
                        driver.command(f'bp464 {event["ret"]:x}')
                    else:
                        entry=result['role_level_entry'];role=entry['role']
                        if event['sp']!=entry['sp']+8:raise ValueError('Level snapshot ABI mismatch')
                        actual=memory(driver,role,0x94)
                        body=bytes.fromhex(entry['body_hex'])
                        for src,dst,width in ((0,0x26,1),(2,0x90,2),(12,0x58,2),(16,0x60,4),(20,0x68,4)):
                            if actual[dst:dst+width]!=body[src:src+width]:raise ValueError('Level snapshot native field mismatch')
                        for src,dst in ((4,0x78),(6,0x7c),(8,0x80),(10,0x84)):
                            if actual[dst:dst+4]!=body[src:src+2]+bytes(2):raise ValueError('Level snapshot base field mismatch')
                        event.update(event_type='ROLE_LEVEL_RETURN',level_sequence=entry['level_sequence'],
                                     level=actual[0x26],progress=int.from_bytes(actual[0x58:0x5a],'little'),
                                     resources_hex=actual[0x5c:0x6c].hex(),base_hex=actual[0x78:0x88].hex())
                        result.setdefault('role_level_returns',[]).append(dict(event))
                        driver.command('bc 464')
                        if entry['level_sequence']==1:driver.command('bc 463')
                    continue
                if index in (460,461,462) and getattr(self,'diagnostic_role_progress',False):
                    from pagefile_capacity_compat import memory,number
                    span=getattr(self,'diagnostic_progress_span',0)
                    progress=self.diagnostic_battle_experience*10000//span if span else 2500
                    if getattr(self,'diagnostic_level_snapshot',False):
                        total=getattr(self,'initial_experience',0)+self.diagnostic_battle_experience
                        progress=10000 if total>=3*span else ((total-span)*10000//(2*span) if total>=span else total*10000//span)
                    if index==460:
                        ui=number(driver,'@ecx')
                        role=number(driver,f'poi({ui+0x86888:x})')
                        body=memory(driver,number(driver,'poi(@esp+4)'),20)
                        expected_hp=getattr(self,'initial_battle_hp',100)-12*(self.diagnostic_battle_rounds-1)
                        expected_mp=getattr(self,'initial_battle_mp',50)-8*self.diagnostic_battle_rounds
                        expected=(expected_hp.to_bytes(4,'little')+bytes(4)+expected_mp.to_bytes(4,'little')+
                                  bytes(4)+progress.to_bytes(2,'little')+bytes(2))
                        if body!=expected:raise ValueError('Role progress body differs from isolated fixture')
                        event.update(event_type='ROLE_PROGRESS_ENTRY',ui_pointer=ui,role=role,body_hex=body.hex(),
                                     before_hex=memory(driver,role+0x58,20).hex())
                        result['role_progress_entry']=dict(event)
                        driver.command('bc 460')
                        driver.command(f'bp461 {event["ret"]:x}')
                        driver.command('bp462 4ac2ff')
                    elif index==462:
                        role=result['role_progress_entry']['role']
                        event.update(event_type='ROLE_PROGRESS_BAR_ARGUMENT',amount=number(driver,'@eax'),
                                     role_progress_hex=memory(driver,role+0x58,2).hex())
                        import struct
                        scale=struct.unpack('<f',bytes.fromhex('0ad7233c'))[0]
                        expected_bar=int(struct.unpack('<f',struct.pack('<f',progress*scale))[0])
                        if event['amount']!=expected_bar or event['role_progress_hex']!=progress.to_bytes(2,'little').hex():
                            raise ValueError('Native progress bar differs from expected packet proportion')
                        result['role_progress_bar_argument']=dict(event)
                        driver.command('bc 462')
                    else:
                        entry=result['role_progress_entry']
                        if event['sp']!=entry['sp']+8:raise ValueError('Role progress return ABI mismatch')
                        event.update(event_type='ROLE_PROGRESS_RETURN',after_hex=memory(driver,entry['role']+0x58,20).hex())
                        if event['after_hex'][:4]!=progress.to_bytes(2,'little').hex():raise ValueError('Role progress WORD not retained')
                        result['role_progress_return']=dict(event)
                        driver.command('bc 461')
                    continue
                if index==459 and getattr(self,'diagnostic_battle_experience',0):
                    from pagefile_capacity_compat import number
                    amount=number(driver,'poi(@esp+10)')
                    if amount!=self.diagnostic_battle_experience:
                        raise ValueError('Native character EXP formatter amount mismatch')
                    event.update(event_type='SOCKET_CHARACTER_EXP_FORMAT_CALL',amount=amount)
                    result['socket_character_exp_format_call']=dict(event)
                    driver.command('bc 459')
                    continue
                if index in (440,441) and getattr(self,'diagnostic_battle_terminal',False):
                    from pagefile_capacity_compat import memory,number
                    battle=result['socket_battle_entry']['battle']
                    if index==440:
                        if number(driver,'@ecx')!=battle:raise ValueError('Outcome receiver object mismatch')
                        logical=memory(driver,number(driver,'poi(@esp+4)'),57)
                        expected=bytearray(b'\x89'+bytes(56))
                        award=getattr(self,'diagnostic_battle_experience',0)
                        expected[5:9]=award.to_bytes(4,'little')
                        if logical!=bytes(expected):raise ValueError('Diagnostic outcome amount mismatch')
                        if award:driver.command('bp459 518c82')
                        event.update(event_type='SOCKET_OUTCOME_ENTRY',logical_hex=logical.hex())
                        result['socket_outcome_entry']=dict(event)
                        driver.command('bc 440')
                        driver.command(f'bp441 {event["ret"]:x}')
                        continue
                    entry=result['socket_outcome_entry']
                    if event['sp']!=entry['sp']+8 or event['eax']!=1:
                        raise ValueError('Outcome receiver ABI mismatch')
                    received=number(driver,f'poi({battle+0xa9df6bc:x})')
                    if received!=1:raise ValueError('Outcome receiver did not mark result received')
                    event.update(event_type='SOCKET_OUTCOME_RETURN',result_received=received)
                    result['socket_outcome_return']=dict(event)
                    if getattr(self,'observe_socket_outcome_panel',False):
                        driver.command('bc 441')
                        driver.command('bp442 485070')
                        continue
                    outcome=('NATIVE_SOCKET_TEST_AWARD_OUTCOME_CONSUMED' if getattr(self,'diagnostic_battle_experience',0)
                             else 'NATIVE_SOCKET_ZERO_AWARD_OUTCOME_CONSUMED')
                    break
                if index in (438,439) and getattr(self,'probe_socket_battle_action',False):
                    from pagefile_capacity_compat import memory,number
                    battle=result['socket_battle_entry']['battle']
                    retaliation=getattr(self,'observe_socket_retaliation',False) and 'socket_damage_return' in result
                    key='socket_retaliation' if retaliation else 'socket_damage'
                    target=0 if retaliation else 14
                    if index==438:
                        if number(driver,'@ecx')!=battle:raise ValueError('Damage receiver object mismatch')
                        logical=memory(driver,number(driver,'poi(@esp+4)'),17)
                        if logical[:3]!=bytes([0x86,0,target]):raise ValueError('Unexpected diagnostic damage target')
                        event.update(event_type='SOCKET_DAMAGE_ENTRY',logical_hex=logical.hex())
                        result[key+'_entry']=dict(event)
                        driver.command('bc 438')
                        driver.command(f'bp439 {event["ret"]:x}')
                        continue
                    entry=result[key+'_entry']
                    if event['sp']!=entry['sp']+8:raise ValueError('Damage receiver ABI mismatch')
                    pointer=number(driver,f'poi({battle+0x144938+0x38+target*24:x})')
                    event.update(event_type='SOCKET_DAMAGE_RETURN',enemy_vitals_hex=memory(driver,pointer+0xde8,16).hex())
                    if getattr(self,'diagnostic_battle_player_appearance',False):
                        event['control_gate']={name:number(driver,f'poi({battle+offset:x})') for name,offset in
                            (('result_received',0xa9df6bc),('manager_event',0x144c1c),
                             ('control_sent',0xa9e9c44),('bulk_seen',0xa9e9c48),
                             ('counter',0xa9e9c64),('completed_counter',0xa9e9c68),
                             ('target_count',0x45c))}
                        event['actor_animation_states']=[memory(driver,number(driver,f'poi({battle+0x144938+0x38+slot*24:x})')+0x1e7,5).hex() for slot in (0,14)]
                    values=bytes.fromhex(event['enemy_vitals_hex'])
                    round_number=len(result.get('socket_completed_rounds',[]))+1
                    expected_hp=100-12*round_number if retaliation else 150-18*round_number
                    if getattr(self,'diagnostic_battle_terminal',False):expected_hp=0
                    if int.from_bytes(values[:4],'little')!=expected_hp or int.from_bytes(values[8:12],'little')!=(120 if retaliation else 150):
                        raise ValueError('Diagnostic damage did not reach expected enemy HP')
                    result[key+'_return']=dict(event)
                    if getattr(self,'shared_visibility',False) and self.sink.document.get('hold_terminal_disconnect'):
                        write_json(self.sink.manifest.parent/'peer-0-terminal-held.json',
                            dict(run_id=self.run.name,client_pid=driver.client_pid,event=event))
                        until=time.monotonic()+60
                        while time.monotonic()<until and self.sink.process.poll() is None:
                            time.sleep(.1)
                        raise TimeoutError('Terminal disconnect owner did not stop this probe')
                    if getattr(self,'diagnostic_battle_animations',False) and not result.get('animation_completion_armed'):
                        driver.command('bp447 5294b6')
                        result['animation_completion_armed']=True
                    if getattr(self,'diagnostic_battle_terminal',False):
                        driver.command('bc 439')
                        driver.command('bp440 518bf0')
                        continue
                    if retaliation:
                        result.setdefault('socket_completed_rounds',[]).append({name:result[name] for name in
                            ('socket_grant_entry','socket_grant_return','socket_action_return','socket_damage_entry',
                             'socket_damage_return','socket_retaliation_entry','socket_retaliation_return')})
                        if round_number<getattr(self,'diagnostic_battle_rounds',1):
                            del result['socket_damage_return']
                            driver.command('bc 439')
                            driver.command('bp435 517590')
                            continue
                    if getattr(self,'observe_socket_retaliation',False) and not retaliation:
                        driver.command('bc 439')
                        driver.command('bp438 517230')
                        continue
                    if retaliation and getattr(self,'diagnostic_battle_animations',False):
                        driver.command('bc 439')
                        continue
                    # Read-only exit prerequisites; never force the panel or end state.
                    ui=number(driver,f'poi({battle+0x20:x})')
                    exit_state={name:number(driver,f'poi({battle+offset:x})') for name,offset in
                        (('result_received',0xa9df6bc),('manager_ready',0x144c18),
                         ('panel_latch',0xa9e9c50),('stage',0x44))}
                    exit_state.update(ui=ui,sequence=sequence,pid=event['pid'],tid=event['tid'])
                    exit_state['panel_mode']=number(driver,f'poi({ui+0x23d620:x})')
                    exit_state['handles_hex']=memory(driver,ui+0x232df0,4).hex()
                    mode=exit_state['panel_mode']
                    if mode in (0,1):
                        handle=int.from_bytes(bytes.fromhex(exit_state['handles_hex'])[mode*2:mode*2+2],'little',signed=True)
                        exit_state['selected_handle']=handle
                        if handle>=0:
                            exit_state['control_flags']=memory(driver,ui+0xe2988+10760*handle,1)[0]
                    result['socket_exit_prerequisites']=exit_state
                    outcome='NATIVE_SOCKET_DIAGNOSTIC_RETALIATION_APPLIED' if retaliation else 'NATIVE_SOCKET_DIAGNOSTIC_DAMAGE_APPLIED'
                    break
                if index==437 and getattr(self,'probe_socket_battle_action',False):
                    from pagefile_capacity_compat import memory,number
                    state=result['socket_action_probe']
                    raw=bytes.fromhex(state['page']['hex'])
                    if event['sp']!=state['entry_sp'] or event['eax']!=1 or memory(driver,state['page']['address'],len(raw))!=raw:
                        raise ValueError('Native socket action return or immutable page mismatch')
                    battle=result['socket_battle_entry']['battle']
                    controls=memory(driver,battle+0xa9e9c34,12).hex()
                    if controls!='010000000000000000000000':
                        raise ValueError('Native socket action did not consume first grant')
                    event.update(event_type='SOCKET_NATIVE_ACTION_RETURN',controls_hex=controls)
                    if getattr(self,'diagnostic_battle_player_appearance',False):
                        net=number(driver,f'poi({battle+0x10:x})')
                        queued=number(driver,f'poi({net+0x36c4:x})')
                        if queued>0xa00:raise ValueError('Native send queue exceeds capacity')
                        event.update(network_owner=net,network_active=memory(driver,net+0x2cb8,1)[0],
                                     queued_length=queued,queued_logical_hex=memory(driver,net+0x36c8,queued).hex() if queued else '',
                                     staged_action_hex=memory(driver,battle+0x470,24).hex())
                    result['socket_action_return']=dict(event)
                    if getattr(self,'shared_visibility',False) and self.sink.document.get('observe_battle'):
                        write_json(self.sink.manifest.parent/'peer-0-battle-started.json',
                            dict(run_id=self.run.name,client_pid=driver.client_pid,event=event))
                        until=time.monotonic()+20
                        while not (self.sink.manifest.parent/'peer-1-fight.json').exists():
                            if time.monotonic()>=until or self.sink.process.poll() is not None:
                                raise TimeoutError('Shared observer did not see Fight before attack')
                            time.sleep(.1)
                        if self.sink.document.get('hold_pre_action_disconnect'):
                            write_json(self.sink.manifest.parent/'peer-0-pre-action-held.json',
                                dict(run_id=self.run.name,client_pid=driver.client_pid,event=event))
                            until=time.monotonic()+60
                            while time.monotonic()<until and self.sink.process.poll() is None:
                                time.sleep(.1)
                            raise TimeoutError('Pre-action disconnect owner did not stop this probe')
                    driver.command('bc 437')
                    driver.command('bp438 517230')
                    driver.command(f'r eip={state["resume_pc"]:x}')
                    continue
                if index in (434,435,436) and getattr(self,'diagnostic_battle_participants',False):
                    from pagefile_capacity_compat import memory,number
                    battle=result['socket_battle_entry']['battle']
                    if index in (434,435):
                        if number(driver,'@ecx')!=battle:
                            raise ValueError('Socket participant/grant object mismatch')
                        logical=memory(driver,number(driver,'poi(@esp+4)'),45 if index==434 else 17)
                        event.update(event_type='SOCKET_PARTICIPANT_ENTRY' if index==434 else 'SOCKET_GRANT_ENTRY',logical_hex=logical.hex())
                        if index==434:
                            slot=logical[1]
                            actor=number(driver,f'poi({battle+0x144938+0x38+slot*24:x})')
                            if not actor:raise ValueError('Participant actor storage missing')
                            event.update(actor=actor,
                                prior_render_handle=int.from_bytes(memory(driver,actor+0x1a,2),'little',signed=True),
                                prior_metadata_hex=memory(driver,actor+0xdb0,56).hex(),
                                local_player_identity=number(driver,f'poi({battle+0x48:x})'))
                            result.setdefault('socket_participants',[]).append(dict(event))
                            if len(result['socket_participants'])==(3 if getattr(self,'diagnostic_battle_revival',False) else 2):driver.command('bc 434')
                        else:
                            from current_offline_vitals_live import grant_record,control_snapshot
                            if logical!=grant_record():raise ValueError('Socket grant bytes mismatch')
                            event['control_state']=control_snapshot(driver,battle)
                            result['socket_grant_entry']=dict(event)
                            driver.command('bc 435')
                            driver.command(f'bp436 {event["ret"]:x}')
                        continue
                    entry=result['socket_grant_entry']
                    if event['sp']!=entry['sp']+8 or event['eax']!=1:
                        raise ValueError('Socket grant return ABI mismatch')
                    event.update(event_type='SOCKET_GRANT_RETURN',
                                 selectors_hex=memory(driver,battle+0x51,2).hex(),
                                 first_grant=number(driver,f'poi({battle+0xa9e9c38:x})'))
                    if not event['selectors_hex'].startswith('00') or event['first_grant']!=1:
                        raise ValueError('Socket grant did not enable actor zero')
                    from current_offline_vitals_live import control_snapshot
                    event['control_state']=control_snapshot(driver,battle)
                    result['socket_grant_return']=dict(event)
                    if getattr(self,'diagnostic_battle_revival',False) and result.get('revival_await_followup_grant'):
                        result['revival_followup_grant']=dict(event)
                        from current_offline_client_run import install_owned_page
                        from current_offline_vitals_live import action_call_page
                        page=install_owned_page(driver,lambda address:action_call_page(address,battle))
                        result['revival_followup_probe']={'page':page,'entry_sp':event['sp'],'resume_pc':event['pc']}
                        driver.command('bc 436')
                        driver.command(f'bp482 {page["return_trap"]:x}')
                        driver.command(f'r eip={page["address"]:x}')
                        continue
                    if getattr(self,'diagnostic_battle_revival',False) and result.get('revival_grant_observer_armed') and not result.get('revival_waiting_for_regrant'):
                        result['revival_early_regrant']=dict(event)
                        driver.command('bc 436')
                        continue
                    if getattr(self,'diagnostic_battle_revival',False) and result.get('revival_waiting_for_regrant'):
                        result['revival_regrant']=dict(event)
                        from current_offline_client_run import install_owned_page
                        from current_offline_vitals_live import skill_select_call_page
                        page=install_owned_page(driver,lambda address:skill_select_call_page(address,battle))
                        result['socket_skill_select_probe']={'page':page,'entry_sp':event['sp'],
                            'resume_pc':event['pc'],'scope':'NATIVE_CALL_NOT_PHYSICAL_INPUT'}
                        self.probe_socket_skill_select=True
                        self.probe_socket_skill_command=True
                        driver.command('bc 436')
                        driver.command(f'bp451 {page["return_trap"]:x}')
                        driver.command(f'r eip={page["address"]:x}')
                        continue
                    if 'socket_mp_refusal' in result:
                        if event['control_state']['waiting']!=0:
                            raise ValueError('Refusal regrant left native input blocked')
                        result['socket_mp_refusal']['regrant']=dict(event)
                    if getattr(self,'diagnostic_battle_skill_settlement',False) and not result.get('skill_target_mask_watch'):
                        result['skill_target_mask_watch']={'initial_hex':memory(driver,battle+0x144938+0x2f4,8).hex(),
                            'scope':'READ_ONLY_HARDWARE_WRITE_OBSERVATION'}
                        driver.command(f'ba455 w4 {battle+0x144938+0x2f4:x}')
                        driver.command(f'ba456 w4 {battle+0x144938+0x2f8:x}')
                    if getattr(self,'diagnostic_battle_player_appearance',False):
                        selector=battle+0xa9dc198
                        header=memory(driver,selector+4,2)
                        banks=header[1]
                        if banks>16:raise ValueError('Skill selector bank count exceeds qualified storage')
                        result['socket_skill_prerequisites']={
                            'scope':'READ_ONLY_NOT_LEARNED_OWNERSHIP',
                            'current_bank':int.from_bytes(header[:1],'little',signed=True),
                            'bank_count':banks,
                            'selected_index':int.from_bytes(memory(driver,battle+0xa9df73c,4),'little',signed=True),
                            'banks':[{'index':i,'entry_count':number(driver,f'poi({selector+0x10+i*0x2d0:x})'),
                                      'raw_state':memory(driver,selector+0x10+i*0x2d0+0x2c0,1)[0]}
                                     for i in range(banks)]}
                        source=number(driver,f'poi({battle+0x14:x})')+0x90
                        result['socket_skill_prerequisites']['source_current']=int.from_bytes(memory(driver,source+0xcf,1),'little',signed=True)
                        result['socket_skill_prerequisites']['source_row_count']=memory(driver,source+0xd4,1)[0]
                        if result['socket_skill_prerequisites']['source_row_count']:
                            result['socket_skill_prerequisites']['first_source_learned_count']=memory(driver,source+0xd8+0x1f0,1)[0]
                        for bank in result['socket_skill_prerequisites']['banks']:
                            if bank['entry_count']:
                                at=selector+0x10+bank['index']*0x2d0
                                bank['first_state_word']=int.from_bytes(memory(driver,at+4,2),'little')
                                pointer=number(driver,f'poi({at+0xcc:x})')
                                bank['first_definition_identity_hex']=memory(driver,pointer,2).hex()
                        ui=number(driver,f'poi({battle+0x20:x})')
                        hotbar_source=number(driver,f'poi({ui+0x86888:x})')
                        if hotbar_source and 'world_resource_before_battle' not in result:
                            result['world_resource_before_battle']={
                                'ui':ui,'source':hotbar_source,'sequence':sequence,
                                'hp_maxhp_mp_maxmp_hex':memory(driver,hotbar_source+0x5c,16).hex(),
                                'scope':'READ_ONLY_ROLE_SOURCE_NOT_VISUAL_HUD_ACCEPTANCE'}
                        hotbar_row=int.from_bytes(memory(driver,hotbar_source+0xcf,1),'little',signed=True) if hotbar_source else None
                        hotbar_mode=number(driver,f'poi({ui+0xa3d08:x})')
                        hotbar={'scope':'READ_ONLY_NATIVE_GETTER_INPUTS', 'mode':hotbar_mode,
                                'source_present':bool(hotbar_source), 'source_row':hotbar_row,
                                'battle_action_mode':number(driver,f'poi({battle+0x46c:x})'),
                                'alternate_records_hex':memory(driver,ui+0xa4114,60).hex()}
                        if hotbar_row is not None and 0<=hotbar_row<16:
                            hotbar['primary_records_hex']=memory(driver,ui+0xa3d54+hotbar_row*60,60).hex()
                        result['socket_skill_prerequisites']['hotbar']=hotbar
                        metadata_owner=number(driver,f'poi({ui+0xcff70:x})')
                        result['socket_skill_prerequisites']['god_name_metadata']=[]
                        for key in range(2801,2835):
                            pointer=number(driver,f'poi({metadata_owner+0xb2d40+4*key:x})')
                            result['socket_skill_prerequisites']['god_name_metadata'].append({
                                'key':key,'present':bool(pointer),
                                'name_hex':memory(driver,pointer+8,38).split(b'\0',1)[0].hex() if pointer else None})
                    result['socket_actor_vitals']=[memory(driver,number(driver,f'poi({battle+0x144938+0x38+slot*24:x})')+0xde8,16).hex() for slot in (0,14)]
                    if getattr(self,'diagnostic_battle_revival',False):
                        result['revival_actor_states']=[]
                        for slot in (0,1,14):
                            actor=number(driver,f'poi({battle+0x144938+0x38+slot*24:x})')
                            result['revival_actor_states'].append({'slot':slot,'actor':actor,
                                'vitals_hex':memory(driver,actor+0xde8,16).hex(),
                                'presentation_state':memory(driver,actor+0x1eb,1)[0],
                                'pending_state':memory(driver,actor+0x232,1)[0]})
                        result['revival_scope']='LETHAL_ALLY_PRELUDE_NO_REVIVAL_CAST'
                        if getattr(self,'diagnostic_resume_checkpoint',False):
                            result['revival_scope']='SAVED_THREE_ACTOR_PROJECTION_NO_REARM_OR_ACTION'
                            result['revival_restored_participants_observed']=True
                            driver.command('bc 436')
                            result['revival_scope']='SAVED_THREE_ACTOR_REARM_BASIC_PROBE_NOT_UI_ACCEPTANCE'
                            result['revival_await_followup_grant']=True
                            driver.command('bp435 517590')
                            continue
                        driver.command('bc 436')
                        result['revival_grant_observer_armed']=True
                        driver.command('bp435 517590')
                        driver.command('bp447 5294b6')
                        continue
                    if getattr(self,'probe_socket_skill_select',False):
                        from current_offline_client_run import install_owned_page
                        from current_offline_vitals_live import skill_select_call_page
                        page=install_owned_page(driver,lambda address:skill_select_call_page(address,battle))
                        result['socket_skill_select_probe']={'page':page,'entry_sp':event['sp'],
                            'resume_pc':event['pc'],'scope':'NATIVE_CALL_NOT_PHYSICAL_INPUT'}
                        driver.command('bc 436')
                        driver.command(f'bp451 {page["return_trap"]:x}')
                        driver.command(f'r eip={page["address"]:x}')
                        continue
                    if getattr(self,'probe_socket_battle_action',False):
                        from current_offline_client_run import install_owned_page
                        from current_offline_vitals_live import action_call_page
                        page=install_owned_page(driver,lambda address:action_call_page(address,battle))
                        result['socket_action_probe']={'page':page,'entry_sp':event['sp'],'resume_pc':event['pc'],
                                                       'scope':'NATIVE_CALL_NOT_PHYSICAL_INPUT','start_sequence':sequence}
                        driver.command('bc 436')
                        driver.command(f'bp437 {page["return_trap"]:x}')
                        driver.command(f'r eip={page["address"]:x}')
                        continue
                    outcome='NATIVE_SOCKET_PARTICIPANTS_GRANTED'
                    break
                if index in (432,433) and getattr(self,'observe_socket_battle_vitals',False):
                    from pagefile_capacity_compat import memory,number
                    battle=result['socket_battle_entry']['battle']
                    if index==432:
                        event.update(event_type='SOCKET_BATTLE_QUEUE_FORWARD',
                                     opcode=memory(driver,number(driver,'@esi'),1)[0],
                                     battle_matches=number(driver,'@ebp')==battle)
                    else:
                        event.update(event_type='SOCKET_BATTLE_DISPATCH_ENTRY',
                                     battle_matches=number(driver,'@ecx')==battle)
                    result.setdefault('socket_battle_queue_events',[]).append(dict(event))
                    if len(result['socket_battle_queue_events'])>=20:
                        driver.command('bc 433')
                    if index==432:
                        driver.command('bc 432')
                    continue
                if index in (430,431) and getattr(self,'observe_socket_battle_vitals',False):
                    from pagefile_capacity_compat import memory,number
                    battle=result['socket_battle_entry']['battle']
                    if index==430:
                        if number(driver,'@ecx')!=battle:
                            raise ValueError('Socket vitals battle object mismatch')
                        logical=memory(driver,number(driver,'poi(@esp+4)'),121)
                        from current_offline_vitals_live import diagnostic_record
                        expected=diagnostic_record(True) if getattr(self,'diagnostic_battle_participants',False) else b'\x88'+bytes(120)
                        if getattr(self,'diagnostic_battle_participants',False):
                            expected=expected[:5]+bytes((getattr(self,'initial_battle_hp',100),))+expected[6:]
                            expected=expected[:9]+bytes((getattr(self,'initial_battle_mp',50),))+expected[10:]
                        if getattr(self,'diagnostic_battle_revival',False):
                            expected=bytearray(expected)
                            resumed=getattr(self,'diagnostic_resume_checkpoint',False)
                            expected[9]=14 if resumed else 80;expected[13]=1 if resumed else 4;expected[17]=5
                            expected=bytes(expected)
                        if logical!=expected:
                            raise ValueError('Socket vitals differ from diagnostic wire payload')
                        event.update(event_type='SOCKET_BATTLE_VITALS_ENTRY',logical_hex=logical.hex(),
                                     counter_before=number(driver,f'poi({battle+0xa9e9c64:x})'))
                        result['socket_battle_vitals_entry']=dict(event)
                        driver.command('bc 430')
                        driver.command(f'bp431 {event["ret"]:x}')
                        continue
                    entry=result['socket_battle_vitals_entry']
                    if event['sp']!=entry['sp']+8 or event['eax']!=1:
                        raise ValueError('Socket vitals receiver failed or ABI mismatch')
                    event.update(event_type='SOCKET_BATTLE_VITALS_RETURN',
                                 counter_after=number(driver,f'poi({battle+0xa9e9c64:x})'))
                    if event['counter_after']!=0:
                        raise ValueError('Socket vitals counter was not initialized')
                    result['socket_battle_vitals_return']=dict(event)
                    if getattr(self,'diagnostic_battle_participants',False):
                        driver.command('bc 431')
                        continue
                    outcome='NATIVE_SOCKET_BATTLE_VITALS_CONSUMED'
                    break
                if index in (428,429) and getattr(self,'diagnostic_battle_transition',False):
                    from pagefile_capacity_compat import number,memory
                    if index==428:
                        event.update(event_type='SOCKET_BATTLE_INITIALIZER_ENTRY',battle=number(driver,'@ecx'),
                                     argument_hex=memory(driver,event['sp']+4,4).hex())
                        result['socket_battle_entry']=dict(event)
                        if getattr(self,'diagnostic_role_progress',False):driver.command('bp460 4e6390')
                        if getattr(self,'diagnostic_level_snapshot',False):driver.command('bp463 4e6b40')
                        driver.command('bc 428')
                        driver.command(f'bp429 {event["ret"]:x}')
                        continue
                    entry=result['socket_battle_entry']
                    if event['sp']!=entry['sp']+8 or event['eax']!=1:
                        raise ValueError('Socket-fed native battle initializer failed or ABI mismatch')
                    event['event_type']='SOCKET_BATTLE_INITIALIZER_RETURN'
                    result['socket_battle_return']=dict(event)
                    if getattr(self,'observe_socket_battle_vitals',False):
                        driver.command('bc 429')
                        driver.command('bp430 518a90')
                        driver.command('bp432 5195b1')
                        driver.command('bp433 5140c0')
                        if getattr(self,'diagnostic_battle_participants',False):
                            driver.command('bp434 515c90')
                            driver.command('bp435 517590')
                        continue
                    outcome='NATIVE_SOCKET_BATTLE_INITIALIZED'
                    break
                if index==465 and getattr(self,'probe_supply_use',False):
                    from pagefile_capacity_compat import memory
                    state=result['supply_calls'][-1]
                    raw=bytes.fromhex(state['page']['hex'])
                    if event['sp']!=state['entry_sp'] or memory(driver,state['page']['address'],len(raw))!=raw:
                        raise ValueError('Native supply call stack/page mismatch')
                    state['returned']=True
                    driver.command('bc 465')
                    driver.command('r eip=467bd7')
                    continue
                if index==425 and getattr(self,'probe_movement_step',False):
                    from pagefile_capacity_compat import memory
                    state=result['movement_step']
                    if event['sp']!=state['entry_sp']:
                        raise ValueError('Native movement step stack mismatch')
                    raw=bytes.fromhex(state['page']['hex'])
                    if memory(driver,state['page']['address'],len(raw))!=raw:
                        raise ValueError('Native movement page changed')
                    state['return_eax']=event['eax']
                    state['ring_after']=memory(driver,state['world']+0x234,3).hex()
                    event['event_type']='LIVE_MOVEMENT_STEP_RETURN'
                    driver.command('bc 425')
                    driver.command('bp426 4692fa')
                    if state.get('special_entry_probe'):
                        driver.command('bp424 467bd7')
                    driver.command('r eip=467bd7')
                    continue
                if index==426 and getattr(self,'probe_movement_step',False):
                    from pagefile_capacity_compat import memory,number
                    state=result['movement_step']
                    if number(driver,'@ebp')!=state['world']:
                        raise ValueError('Movement ACK world mismatch')
                    ack=memory(driver,number(driver,'@ebx'),2)
                    if ack!=bytes([0x5d,state.get('queue_sequence',state['step'])]):
                        raise ValueError('Movement ACK token mismatch')
                    state['ack_hex']=ack.hex()
                    event['event_type']='LIVE_MOVEMENT_ACK_ENTRY'
                    driver.command('bc 426')
                    driver.command('bp427 46b517')
                    continue
                if index==427 and getattr(self,'probe_movement_step',False):
                    from pagefile_capacity_compat import memory,number
                    state=result['movement_step']
                    if number(driver,'@ebp')!=state['world']:
                        raise ValueError('Movement ACK completion world mismatch')
                    state['ack_token_after']=memory(driver,state['world']+0x231,1).hex()
                    state['ring_after_ack']=memory(driver,state['world']+0x234,3).hex()
                    step=state.get('queue_sequence',state['step'])
                    if state['ack_token_after']!=bytes([step]).hex() or state['ring_after_ack']!=bytes([1,step,(step+1)%40]).hex():
                        raise ValueError('Movement ACK did not advance native queue')
                    event['event_type']='LIVE_MOVEMENT_ACK_APPLIED'
                    result.setdefault('movement_steps',[]).append(dict(state))
                    if getattr(self,'indoor_door_probe',False) or getattr(self,'town_door_probe',False):
                        result['door_probe_ack']=dict(event)
                        driver.command('bc 427');driver.command('bp424 467bd7')
                        continue
                    if getattr(self,'town_scene_follow_move',False):
                        result['town_scene_movement_ack']=dict(event)
                        driver.command('bc 427');driver.command('bp424 467bd7')
                        continue
                    if getattr(self,'diagnostic_battle_after_movement',False) and 'pre_battle_movement' not in result:
                        result['pre_battle_movement']=dict(state,ack_sequence=sequence)
                        self.probe_movement_step=False
                        driver.command('bc 427')
                        continue
                    if getattr(self,'movement_steps',1)>1:
                        driver.command('bc 427')
                        driver.command('bp424 467bd7')
                        continue
                    outcome='NATIVE_MOVEMENT_ACK_APPLIED'
                    break
                if index in (423,424) and getattr(self,'observe_world_frames',False):
                    from pagefile_capacity_compat import number
                    world=result['world_initializer']['world_object']
                    if number(driver,'@esi')!=world:
                        raise ValueError('Native world frame object mismatch')
                    event.update(event_type='LIVE_WORLD_PRESENT_RETURN' if index==423 else 'LIVE_WORLD_FRAME_RETURN',
                                 frame_counter=number(driver,f'poi({world+0xa7f2f04:x})'))
                    samples=result.setdefault('world_frame_samples',[])
                    samples.append(dict(event))
                    if (index==424 and getattr(self,'ui_npc_dialogue_ready',False) and
                            len(samples)%8==0 and 'ui_npc_dialogue_open' not in result):
                        from pagefile_capacity_compat import memory
                        requests=[item for item in result.get('ui_npc_physical_packets',[])
                                  if item['opcode']==0x37 and item['client_plaintext_match'] is True]
                        if requests:
                            request=requests[-1]
                            frame=bytes.fromhex(request['plain_frame_hex'])
                            if len(frame)!=8 or frame[2]!=0x37 or int.from_bytes(frame[3:7],'little') not in (1606,1607):
                                raise ValueError('External NPC request did not target a bounded town guide')
                            ui=world+0xa7f2f6c
                            page_index=number(driver,'poi(5b7bf0)')
                            page_count=number(driver,'poi(5b7bf4)')
                            widget=int.from_bytes(memory(driver,ui+0x232dee,2),'little',signed=True)
                            if page_count in (5,7) and page_index==0 and widget>=0:
                                result['ui_npc_dialogue_open']=dict(event,request=request,
                                    target=int.from_bytes(frame[3:7],'little'),page_index=page_index,
                                    page_count=page_count,widget=widget,
                                    scope='ORIGINAL_CLIENT_NATURAL_REQUEST_AND_NATIVE_DIALOGUE_STATE_NOT_SCREENSHOT')
                                write_json(self.run/'ui-npc-dialogue-open.json',result['ui_npc_dialogue_open'])
                                if getattr(self,'ui_npc_stop',None)=='open':
                                    outcome='NATIVE_UI_NPC_DIALOGUE_OPEN';break
                    if (index==424 and getattr(self,'ui_npc_stop',None)=='reopen' and
                            'ui_npc_reopen_request' in result and 'ui_npc_reopened' not in result):
                        from pagefile_capacity_compat import memory
                        ui=world+0xa7f2f6c
                        page_index=number(driver,'poi(5b7bf0)')
                        page_count=number(driver,'poi(5b7bf4)')
                        widget=int.from_bytes(memory(driver,ui+0x232dee,2),'little',signed=True)
                        if page_index==0 and page_count in (5,7) and widget>=0:
                            result['ui_npc_reopened']=dict(event,request=result['ui_npc_reopen_request'],
                                page_index=page_index,page_count=page_count,widget=widget,
                                scope='ORIGINAL_CLIENT_SECOND_NATURAL_NPC_REQUEST_AND_NATIVE_DIALOGUE_STATE')
                            write_json(self.run/'ui-npc-reopened.json',result['ui_npc_reopened'])
                            outcome='NATIVE_UI_NPC_REOPENED';break
                    if index==424 and getattr(self,'ui_world_movement_ready',False) and len(samples)%8==0:
                        import sqlite3
                        from current_scene_live import scene_snapshot
                        with sqlite3.connect(f'file:{(self.run/"town-diagnostic-accounts.db").as_posix()}?mode=ro',uri=True) as check_db:
                            saved=check_db.execute('SELECT area,scene,x,y,revision FROM recovered_positions WHERE character_id=1').fetchone()
                        before=self.ui_world_saved_before
                        if saved and saved[4]>before[4] and saved[:2]==before[:2] and saved[2:4]!=before[2:4]:
                            native_position=scene_snapshot(driver,world)
                            if (native_position['area'],native_position['scene'],native_position['x'],native_position['y'])==saved[:4] and number(driver,f'poi({world+0x30:x})')==0:
                                result['ui_world_movement']=dict(event,saved_before=list(before),saved_after=list(saved),
                                    native=native_position,input_origin='EXTERNAL_INPUT_UNATTRIBUTED_NO_NATIVE_CALL_PAGE')
                                outcome='NATIVE_UI_WORLD_MOVEMENT_SAVED';break
                    if index==424 and 'world_resource_at_entry' not in result:
                        from pagefile_capacity_compat import memory
                        if getattr(self,'observe_npc_state',False):
                            from current_npc_live_state import snapshot
                            result['npc_live_state']=dict(snapshot(driver,world),sequence=sequence)
                        ui=world+0xa7f2f6c
                        source=number(driver,f'poi({ui+0x86888:x})')
                        if not source:raise ValueError('World entry role source missing')
                        result['world_resource_at_entry']={
                            'ui':ui,'source':source,'sequence':sequence,
                            'hp_maxhp_mp_maxmp_hex':memory(driver,source+0x5c,16).hex(),
                            'scope':'READ_ONLY_FIRST_WORLD_FRAME_NOT_VISUAL_HUD_ACCEPTANCE'}
                        if getattr(self,'observe_quest_text_table',False):
                            resource=number(driver,f'poi({ui+0xcff70:x})')
                            if not resource:raise ValueError('Quest text resource owner missing')
                            count=int.from_bytes(memory(driver,resource+0xb2c48,2),'little',signed=True)
                            table=number(driver,f'poi({resource+0xb2c4c:x})')
                            if not 0<count<=32767 or not table:
                                raise ValueError('Quest text table not loaded')
                            entries=[]
                            for key in range(1,min(count,4)+1):
                                pointer=number(driver,f'poi({table+4*(key-1):x})')
                                if not pointer:raise ValueError('Null quest text entry')
                                raw=memory(driver,pointer,256)
                                text=raw.split(b'\0',1)[0]
                                entries.append({'key':key,'pointer':pointer,'text_hex':text.hex(),
                                                'terminated_within_256':b'\0' in raw})
                            result['quest_text_table']={'sequence':sequence,'resource':resource,
                                'table':table,'count':count,'entries':entries,
                                'scope':'READ_ONLY_NATIVE_LOADED_TEXT_NOT_DIALOGUE_ACCEPTANCE'}
                            if getattr(self,'town_spawn_guides',False):
                                town_texts=[]
                                for key in range(894,902):
                                    if key>count:raise ValueError('Town dialogue outside native table')
                                    pointer=number(driver,f'poi({table+4*(key-1):x})')
                                    if not pointer:raise ValueError('Missing town dialogue pointer')
                                    text=bytearray()
                                    for offset in range(0,4096,64):
                                        block=memory(driver,pointer+offset,64)
                                        text.extend(block.split(b'\0',1)[0])
                                        if b'\0' in block:break
                                    else:raise ValueError('Town dialogue exceeds bounded observation')
                                    town_texts.append(dict(key=key,pointer=pointer,text_hex=text.hex(),
                                                           length=len(text),terminated=True))
                                result['town_quest_texts']=dict(sequence=sequence,entries=town_texts,
                                    scope='READ_ONLY_SOURCE_TEXT_NOT_QUEST_STAGE_AUTHORITY')
                                item=5569
                                pointer=number(driver,f'poi({resource+0xb2d40+4*item:x})')
                                result['town_reward_item']=dict(sequence=sequence,item_id=item,
                                    resource=resource,pointer=pointer,
                                    record_hex=memory(driver,pointer,0x18c).hex() if pointer else None,
                                    scope='READ_ONLY_LOADED_ITEM_NOT_REWARD_OR_ITEM_USE_ACCEPTANCE')
                    if index==424 and getattr(self,'town_post_battle_return_pending',None):
                        from current_quest_live import map_item_request_page
                        from current_offline_client_run import install_owned_page
                        ui=world+0xa7f2f6c
                        net=number(driver,f'poi({ui+0x86874:x})')
                        if number(driver,f'poi({net+0x36c4:x})')==0:
                            page=install_owned_page(driver,lambda address:map_item_request_page(address,ui))
                            result['town_map_probe']=dict(page=page,entry_sp=event['sp'],resume_pc=event['pc'],net=net,
                                scope='CUSTOM-0028_POST_BATTLE_NATIVE_MAP_CALL_NOT_PHYSICAL_INPUT')
                            self.town_post_battle_return_pending=None
                            driver.command('bc 424')
                            driver.command(f'bp500 {page["return_trap"]:x}')
                            driver.command('bp501 46bcc0')
                            driver.command(f'r eip={page["address"]:x}')
                        elif time.monotonic()-self.town_post_battle_return_pending>10:
                            raise TimeoutError('Post-battle map request queue did not drain')
                        continue
                    if index==424 and sum(e['event_type']=='LIVE_WORLD_FRAME_RETURN' for e in samples)>=3:
                        if (getattr(self,'indoor_door_probe',False) or getattr(self,'town_door_probe',False)) and 'door_probe' in result:
                            from current_scene_live import scene_snapshot
                            route=result['door_probe']
                            observed=scene_snapshot(driver,world)
                            if getattr(self,'town_door_after_battle',False) and route['index']>=len(route['path'])-1:
                                log=(self.run/'cpp-server.log').read_text(encoding='utf-8',errors='replace')
                                if 'policy or response rejected' in log:
                                    raise ValueError('Post-battle doorway server rejected followup')
                                if tuple(observed[key] for key in ('area','scene','kind','x','y'))==(2,4,0,86,71):
                                    from current_scene_live import outdoor_scene_snapshot
                                    from current_npc_live_state import snapshot as npc_snapshot
                                    loaded=outdoor_scene_snapshot(driver,world)
                                    npcs=npc_snapshot(driver,world)
                                    entries=[entry for pool in npcs['pools'] for entry in pool['entries']]
                                    identities=sorted((entry['identity'],entry['x'],entry['y']) for entry in entries)
                                    if (loaded['loaded_scene_id']==258 and loaded['ring_hex']=='010001' and
                                            bytes.fromhex(loaded['metadata_hex']).startswith(b'CityI1\0') and
                                            identities==[(1606,110,69),(1607,112,70)] and
                                            'DIAGNOSTIC_DOOR_COMMITTED' in log and
                                            'DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED' in log):
                                        import sqlite3
                                        with sqlite3.connect(f'file:{(self.run/"town-diagnostic-accounts.db").as_posix()}?mode=ro',uri=True) as check_db:
                                            saved=check_db.execute('SELECT * FROM recovered_positions WHERE character_id=1').fetchone()
                                        if saved!=(1,2,4,86,71,64):
                                            raise ValueError('Post-battle doorway save mismatch')
                                        result['town_post_battle_door_final']=dict(event,snapshot=loaded,npcs=npcs,
                                            saved_position=list(saved))
                                        outcome='NATIVE_POST_BATTLE_DOORWAY_TOWN_RETURN';break
                                if time.monotonic()-route['started']>45:
                                    raise TimeoutError('Post-battle doorway destination/projection not observed')
                                if route['index']==len(route['path']):continue
                            if 'special_entry_started' in route:
                                log=(self.run/'cpp-server.log').read_text(encoding='utf-8',errors='replace')
                                if 'policy or response rejected' in log:
                                    result['special_entry_final']=dict(event,snapshot=observed)
                                    outcome='NATIVE_TOWN_SPECIAL_ENTRY_SERVER_REJECTED';break
                                if getattr(self,'town_auto_door',False):
                                    hops=result.setdefault('automatic_door_hops',[])
                                    indoor=len(hops)%2==0
                                    expected=(2,15,2,16,19) if indoor else (2,4,0,86,71)
                                    projection_ready=(log.count('DIAGNOSTIC_INDOOR_SAVE_RESTORED')>=len(hops)//2+1 if indoor
                                        else log.count('DIAGNOSTIC_TOWN_GUIDES_SENT')>=len(hops)//2+2)
                                    if tuple(observed[k] for k in ('area','scene','kind','x','y'))==expected and log.count('DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED')>=len(hops)+1 and projection_ready:
                                        from current_scene_live import loaded_scene_snapshot,outdoor_scene_snapshot
                                        from current_npc_live_state import snapshot as npc_snapshot
                                        loaded=loaded_scene_snapshot(driver,world) if indoor else outdoor_scene_snapshot(driver,world)
                                        if loaded['ring_hex']!='010001':
                                            raise ValueError('Automatic doorway destination grid/ring mismatch')
                                        if indoor:
                                            grid=json.loads((HOME/'artifacts/world-atlas/indoor-2-15.json').read_text())['grid']
                                            if loaded['grid_hex']!=grid['cells_hex']:raise ValueError('Automatic doorway indoor grid mismatch')
                                        elif loaded['loaded_scene_id']!=258 or not bytes.fromhex(loaded['metadata_hex']).startswith(b'CityI1\0'):
                                            raise ValueError('Automatic doorway did not restore town resource')
                                        npcs=npc_snapshot(driver,world)
                                        entries=[e for pool in npcs['pools'] for e in pool['entries']]
                                        identities=sorted((e['identity'],e['x'],e['y']) for e in entries)
                                        if identities!=([] if indoor else [(1606,110,69),(1607,112,70)]):
                                            # Server projection logs precede client receive/dispatch.
                                            result['automatic_door_npc_pending']=dict(event,hop=len(hops),npcs=npcs)
                                            if time.monotonic()-route['special_entry_started']>30:
                                                raise ValueError('Automatic doorway NPC scene isolation mismatch')
                                            continue
                                        hop=dict(event,snapshot=loaded,npcs=npcs,movement=dict(result['movement_step']))
                                        hops.append(hop)
                                        result['automatic_door_final']=hop
                                        rounds=getattr(self,'town_auto_door_roundtrips',0)
                                        if not rounds or len(hops)>=rounds*2:
                                            outcome='NATIVE_AUTOMATIC_GROCERY_ROUNDTRIPS_ACCEPTED' if rounds else 'NATIVE_AUTOMATIC_GROCERY_ENTRY_ACCEPTED';break
                                        from current_login_command import town_movement_path_page
                                        from current_offline_client_run import install_owned_page
                                        x,y=(16,20) if indoor else (86,70)
                                        page=install_owned_page(driver,lambda address:town_movement_path_page(address,world,x,y))
                                        result['movement_step']=dict(world=world,page=page,entry_sp=event['sp'],step=1,
                                            queue_sequence=1,special_entry_probe=True)
                                        route['special_entry_started']=time.monotonic()
                                        driver.command('bc 424');driver.command(f'bp425 {page["return_trap"]:x}')
                                        driver.command(f'r eip={page["address"]:x}')
                                        continue
                                    if time.monotonic()-route['special_entry_started']>30:
                                        raise ValueError('Automatic doorway destination/context not observed')
                                    continue
                                if (observed['x'],observed['y'])==(86,70) and number(driver,f'poi({world+0x30:x})')==0 and result['movement_step'].get('ack_hex')=='5d1b':
                                    if 'special_entry_arrival' not in result:
                                        result['special_entry_arrival']=dict(event,snapshot=observed)
                                        route['special_entry_settle']=time.monotonic()+1.0
                                    if time.monotonic()>=route['special_entry_settle']:
                                        result['special_entry_final']=dict(event,snapshot=observed)
                                        outcome='NATIVE_TOWN_SPECIAL_ENTRY_MOVEMENT_ACCEPTED';break
                                if time.monotonic()-route['special_entry_started']>5:
                                    result['special_entry_final']=dict(event,snapshot=observed)
                                    outcome='NATIVE_TOWN_SPECIAL_ENTRY_OBSERVATION_ENDED';break
                                continue
                            if 'movement_step' in result:
                                if 'door_probe_ack' not in result:continue
                                target=route['path'][route['index']]
                                if [observed['x'],observed['y']]!=target or number(driver,f'poi({world+0x30:x})')!=0:continue
                                route.setdefault('arrivals',[]).append(dict(event,snapshot=observed))
                                route['index']+=1
                                result.pop('movement_step');result.pop('door_probe_ack')
                            if route['index']==len(route['path']):
                                if 'settle_until' not in route:route['settle_until']=time.monotonic()+1.0
                                if time.monotonic()<route['settle_until']:continue
                                log=(self.run/'cpp-server.log').read_text(encoding='utf-8',errors='replace')
                                if 'policy or response rejected' in log:raise ValueError('Door route server rejected followup')
                                result['door_probe_final']=dict(event,snapshot=observed)
                                if getattr(self,'town_special_entry_probe',False):
                                    from current_login_command import town_movement_path_page
                                    from current_offline_client_run import install_owned_page
                                    page=install_owned_page(driver,lambda address:town_movement_path_page(address,world,86,70))
                                    route['special_entry_started']=time.monotonic()
                                    result['movement_step']=dict(world=world,page=page,entry_sp=event['sp'],step=27,
                                        queue_sequence=27,special_entry_probe=True)
                                    driver.command('bc 424')
                                    driver.command(f'bp425 {page["return_trap"]:x}')
                                    driver.command(f'r eip={page["address"]:x}')
                                    continue
                                outcome=('NATIVE_TOWN_GROCERY_APPROACH_COMPLETED' if getattr(self,'town_door_probe',False)
                                         else 'NATIVE_INDOOR_CONNECTION_CELLS_VISITED');break
                            from current_login_command import town_movement_path_page
                            from current_offline_client_run import install_owned_page
                            x,y=route['path'][route['index']]
                            page=install_owned_page(driver,lambda address:town_movement_path_page(address,world,x,y))
                            token=route['index']+1
                            result['movement_step']=dict(world=world,page=page,entry_sp=event['sp'],step=token,queue_sequence=token)
                            self.probe_movement_step=True
                            driver.command('bc 423');driver.command('bc 424')
                            driver.command(f'bp425 {page["return_trap"]:x}')
                            driver.command(f'r eip={page["address"]:x}')
                            continue
                        if getattr(self,'town_scene_return_probe',False) and 'town_scene_return' in result:
                            server_log=(self.run/'cpp-server.log').read_text(encoding='utf-8',errors='replace')
                            if 'policy or response rejected' in server_log:raise ValueError('Return probe followup rejected')
                            if 'DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED' not in server_log:continue
                            from current_scene_live import outdoor_scene_snapshot
                            loaded=outdoor_scene_snapshot(driver,world)
                            if getattr(self,'town_scene_follow_move',False) and 'movement_step' in result:
                                if 'town_scene_movement_ack' not in result:continue
                                if (loaded['x'],loaded['y'])!=(111,70) or number(driver,f'poi({world+0x30:x})')!=0:continue
                                if (loaded['area'],loaded['scene'],loaded['kind'],loaded['ring_hex'])!=(2,4,0,'010102'):
                                    raise ValueError('Return movement map or ring mismatch')
                                import sqlite3
                                with sqlite3.connect(f'file:{(self.run/"town-diagnostic-accounts.db").as_posix()}?mode=ro',uri=True) as check_db:
                                    saved=check_db.execute('SELECT * FROM recovered_positions WHERE character_id=1').fetchone()
                                if saved!=(1,2,4,111,70,57):raise ValueError('Return movement save mismatch')
                                result['town_return_walk']=dict(event,snapshot=loaded,saved_position=list(saved))
                                outcome='NATIVE_DURABLE_RETURN_AND_MOVEMENT_COMPLETED';break
                            if (loaded['area'],loaded['scene'],loaded['kind'],loaded['x'],loaded['y'],loaded['ring_hex'])!=(2,4,0,110,70,'010001'):
                                raise ValueError('Return destination mismatch')
                            if loaded['loaded_scene_id']!=258 or not bytes.fromhex(loaded['metadata_hex']).startswith(b'CityI1\0'):
                                raise ValueError('Return did not load CityI1 metadata')
                            result['town_return_final']=dict(event,snapshot=loaded)
                            if getattr(self,'town_scene_return_commit',False):
                                if 'DIAGNOSTIC_RETURN_TOWN_COMMITTED' not in server_log:raise ValueError('Return commit missing')
                                from current_npc_live_state import snapshot
                                npcs=snapshot(driver,world)
                                entries=[entry for pool in npcs['pools'] for entry in pool['entries']]
                                if sorted((e['identity'],e['x'],e['y']) for e in entries)!=[(1606,110,69),(1607,112,70)]:continue
                                import sqlite3
                                with sqlite3.connect(f'file:{(self.run/"town-diagnostic-accounts.db").as_posix()}?mode=ro',uri=True) as check_db:
                                    saved=check_db.execute('SELECT * FROM recovered_positions WHERE character_id=1').fetchone()
                                if saved!=(1,2,4,110,70,56):raise ValueError('Durable return save mismatch')
                                result['town_return_durable']=dict(event,snapshot=loaded,npcs=npcs,saved_position=list(saved))
                                if getattr(self,'town_scene_follow_move',False):
                                    from current_login_command import town_movement_path_page
                                    from current_offline_client_run import install_owned_page
                                    page=install_owned_page(driver,lambda address:town_movement_path_page(address,world,111,70))
                                    result['movement_step']=dict(world=world,page=page,entry_sp=event['sp'],step=1,queue_sequence=1)
                                    self.probe_movement_step=True
                                    driver.command('bc 423');driver.command('bc 424')
                                    driver.command(f'bp425 {page["return_trap"]:x}')
                                    driver.command(f'r eip={page["address"]:x}')
                                    continue
                                outcome=('NATIVE_POST_BATTLE_DURABLE_TOWN_RETURN' if getattr(self,'town_return_after_battle',False)
                                         else 'NATIVE_DURABLE_RETURN_WITH_TOWN_NPCS');break
                            outcome='NATIVE_INDOOR_TO_TOWN_RECEIVER_RETURNED';break
                        if (getattr(self.sink,'restored_town_scene',None)==4 and
                            getattr(self.sink,'restored_town_position',None)==(86,71)):
                            server_log=(self.run/'cpp-server.log').read_text(encoding='utf-8',errors='replace')
                            if 'policy or response rejected' in server_log:raise ValueError('Door checkpoint reconnect rejected')
                            restored_slots=result.get('journal_restore_returns',[])
                            if 'DIAGNOSTIC_TOWN_GUIDES_SENT' not in server_log or len(restored_slots)!=15:continue
                            from current_scene_live import outdoor_scene_snapshot
                            from current_npc_live_state import snapshot
                            loaded=outdoor_scene_snapshot(driver,world)
                            if tuple(loaded[k] for k in ('area','scene','kind','x','y','ring_hex'))!=(2,4,0,86,71,'010001'):
                                raise ValueError('Door checkpoint scene/position/ring mismatch')
                            if loaded['loaded_scene_id']!=258 or not bytes.fromhex(loaded['metadata_hex']).startswith(b'CityI1\0'):
                                raise ValueError('Door checkpoint resource mismatch')
                            if loaded['slot0_hex']!='01000000c115000000000000000000000000000000000000':continue
                            npcs=snapshot(driver,world)
                            identities=sorted((e['identity'],e['x'],e['y']) for p in npcs['pools'] for e in p['entries'])
                            if identities!=[(1606,110,69),(1607,112,70)]:continue
                            if [slot['slot'] for slot in restored_slots]!=list(range(15)) or restored_slots[-1]['slots_hex']!='00'*60:
                                raise ValueError('Door checkpoint completed journal mismatch')
                            from current_remote_actor_live import snapshot as remote_snapshot
                            result['door_reconnect_final']=dict(event,snapshot=loaded,npcs=npcs,
                                remote_actors=remote_snapshot(driver,world))
                            outcome='NATIVE_DOOR_ROUNDTRIP_RECONNECT_RESTORED';break
                        if (getattr(self.sink,'restored_town_scene',4)==15 and
                                not getattr(self,'town_post_battle_movement',False)):
                            server_log=(self.run/'cpp-server.log').read_text(encoding='utf-8',errors='replace')
                            if 'policy or response rejected' in server_log:raise ValueError('Indoor reconnect rejected')
                            restored_slots=result.get('journal_restore_returns',[])
                            if 'DIAGNOSTIC_INDOOR_SAVE_RESTORED' not in server_log or len(restored_slots)!=15:continue
                            from current_scene_live import loaded_scene_snapshot
                            from current_npc_live_state import snapshot
                            loaded=loaded_scene_snapshot(driver,world)
                            target=self.sink.restored_town_position
                            if (loaded['area'],loaded['scene'],loaded['kind'],loaded['x'],loaded['y'],loaded['ring_hex'])!=(2,15,2,*target,'010001'):
                                raise ValueError('Indoor reconnect scene/position/ring mismatch')
                            expected_grid=json.loads((HOME/'artifacts/world-atlas/indoor-2-15.json').read_text())['grid']
                            if loaded['grid_hex']!=expected_grid['cells_hex']:raise ValueError('Indoor reconnect grid mismatch')
                            if loaded['slot0_hex']!='01000000c115000000000000000000000000000000000000':continue
                            npcs=snapshot(driver,world)
                            if any(pool['entries'] for pool in npcs['pools']):raise ValueError('Town NPCs leaked into indoor reconnect')
                            if [slot['slot'] for slot in restored_slots]!=list(range(15)) or restored_slots[-1]['slots_hex']!='00'*60:
                                raise ValueError('Completed journal not restored')
                            result['indoor_reconnect_final']=dict(event,snapshot=loaded,npcs=npcs)
                            if getattr(self,'town_battle_after_quest',False):
                                if target!=(18,12) or self.sink.town_guide_start_stage!=3:
                                    raise ValueError('Town battle requires saved indoor18,12 and completed guide')
                                driver.command('bc 423');driver.command('bc 424')
                                continue
                            if getattr(self,'indoor_door_probe',False):
                                if target!=(18,12):raise ValueError('Door probe requires qualified indoor18,12 restore')
                                result['door_probe']=dict(index=0,path=[[17,13],[16,14],[15,15],[14,16],[14,17],[15,18],[16,19],[16,20]],
                                    scope='NATIVE_PATH_CALLS_TO_SOURCE_PAIRS_NOT_PROVEN_PORTAL_ACTIVATION')
                                continue
                            if getattr(self,'town_scene_return_probe',False):
                                if 'town_map_probe' not in result:
                                    from current_quest_live import map_item_request_page
                                    from current_offline_client_run import install_owned_page
                                    ui=world+0xa7f2f6c
                                    net=number(driver,f'poi({ui+0x86874:x})')
                                    if number(driver,f'poi({net+0x36c4:x})')!=0:continue
                                    page=install_owned_page(driver,lambda address:map_item_request_page(address,ui))
                                    result['town_map_probe']=dict(page=page,entry_sp=event['sp'],resume_pc=event['pc'],net=net,
                                        scope='CUSTOM-0024_RETURN_REQUEST_NOT_PHYSICAL_INPUT')
                                    driver.command(f'bp500 {page["return_trap"]:x}')
                                    driver.command('bp501 46bcc0');driver.command(f'r eip={page["address"]:x}')
                                continue
                            outcome='NATIVE_CROSS_MAP_RECONNECT_RESTORED';break
                        if getattr(self,'town_scene_indoor_probe',False) and 'town_scene_return' in result:
                            server_log=(self.run/'cpp-server.log').read_text(encoding='utf-8',errors='replace')
                            if 'policy or response rejected' in server_log:raise ValueError('Indoor probe followup rejected')
                            if 'DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED' not in server_log:continue
                            from current_scene_live import loaded_scene_snapshot
                            loaded=loaded_scene_snapshot(driver,world)
                            if getattr(self,'town_scene_follow_move',False) and 'movement_step' in result:
                                if 'town_scene_movement_ack' not in result:continue
                                if (loaded['x'],loaded['y'])!=(18,12) or number(driver,f'poi({world+0x30:x})')!=0:continue
                                if (loaded['area'],loaded['scene'],loaded['kind'],loaded['ring_hex'])!=(2,15,2,'010102'):
                                    raise ValueError('Post-crossing movement scene or ring mismatch')
                                import sqlite3
                                with sqlite3.connect(f'file:{(self.run/"town-diagnostic-accounts.db").as_posix()}?mode=ro',uri=True) as check_db:
                                    saved=check_db.execute('SELECT * FROM recovered_positions WHERE character_id=1').fetchone()
                                expected_revision=2 if getattr(self,'town_fresh_spawn',False) else 55
                                if saved!=(1,2,15,18,12,expected_revision):raise ValueError('Post-crossing movement save mismatch')
                                result['town_indoor_movement_complete']=dict(event,snapshot=loaded,saved_position=list(saved))
                                if getattr(self,'town_battle_after_quest',False):
                                    self.town_scene_indoor_probe=False
                                    self.town_spawn_guides=False
                                    self.town_map_probe=False
                                    self.probe_npc_request=False
                                    self.town_quest_chain=False
                                    self.town_quest_progress=False
                                    driver.command('bc 423');driver.command('bc 424')
                                    continue
                                outcome='NATIVE_TOWN_TO_INDOOR_AND_MOVEMENT_COMPLETED';break
                            result['town_indoor_loaded_scene']=dict(event,snapshot=loaded)
                            if (loaded['area'],loaded['scene'],loaded['kind'],loaded['x'],loaded['y'])!=(2,15,2,17,13):
                                raise ValueError('Indoor loaded destination mismatch')
                            expected_grid=json.loads((HOME/'artifacts/world-atlas/indoor-2-15.json').read_text())['grid']
                            if (loaded['grid_width'],loaded['grid_height'])!=(expected_grid['side'],expected_grid['side']) or loaded['grid_hex']!=expected_grid['cells_hex']:
                                raise ValueError('Indoor live collision grid differs from pinned native scene')
                            result['town_scene_final_frame']=dict(event)
                            if getattr(self,'town_scene_indoor_transfer',False):
                                if 'DIAGNOSTIC_INDOOR_TRANSFER_COMMITTED' not in server_log:
                                    raise ValueError('Missing durable indoor transfer commit')
                                import sqlite3
                                with sqlite3.connect(f'file:{(self.run/"town-diagnostic-accounts.db").as_posix()}?mode=ro',uri=True) as check_db:
                                    saved=check_db.execute('SELECT * FROM recovered_positions WHERE character_id=1').fetchone()
                                result['town_indoor_saved_position']=list(saved) if saved else None
                                expected_revision=1 if getattr(self,'town_fresh_spawn',False) else 54
                                if saved!=(1,2,15,17,13,expected_revision):raise ValueError('Durable indoor transfer save mismatch')
                                if getattr(self,'town_scene_follow_move',False):
                                    from current_login_command import movement_path_page
                                    from current_offline_client_run import install_owned_page
                                    page=install_owned_page(driver,lambda address:movement_path_page(address,world,1))
                                    result['movement_step']=dict(world=world,page=page,entry_sp=event['sp'],step=1,queue_sequence=1)
                                    self.probe_movement_step=True
                                    driver.command('bc 423');driver.command('bc 424')
                                    driver.command(f'bp425 {page["return_trap"]:x}')
                                    driver.command(f'r eip={page["address"]:x}')
                                    continue
                                outcome='NATIVE_TOWN_TO_INDOOR_DURABLE_RECEIVER_RETURNED'
                            else:outcome='NATIVE_TOWN_TO_INDOOR_RECEIVER_RETURNED'
                            break
                        if getattr(self,'town_spawn_guides',False):
                            from current_npc_live_state import snapshot,render_slots
                            observed=snapshot(driver,world)
                            entries=[entry for pool in observed['pools'] for entry in pool['entries']]
                            actual=sorted((entry['identity'],entry['x'],entry['y']) for entry in entries)
                            if actual!=[(1606,110,69),(1607,112,70)]:continue
                            result['town_guides_after_spawn']=dict(observed,sequence=sequence)
                            if getattr(self,'observe_town_npc_render',False):
                                result['town_npc_render_slots']=dict(render_slots(driver,observed),sequence=sequence)
                            result['town_guides_final_frame']=dict(event)
                            if (not getattr(self,'probe_npc_request',False) and not getattr(self,'ui_world_movement',False)
                                    and not getattr(self,'ui_npc_dialogue',False)
                                    and not getattr(self,'verify_restored_town_position',False)):
                                outcome='NATIVE_TOWN_GUIDES_ALLOCATED';break
                        if getattr(self,'probe_town_guide_resource',False):
                            if 'town_resource_return' in result:
                                result['town_resource_final_frame']=dict(event)
                                outcome='NATIVE_TOWN_RESOURCE_LOADED';break
                            if 'town_resource_probe' not in result:
                                from current_offline_client_run import install_owned_page
                                from current_quest_live import town_resource_page
                                state=result['npc_live_state']
                                page=install_owned_page(driver,lambda address:town_resource_page(address,state['table']))
                                result['town_resource_probe']=dict(page=page,entry_sp=event['sp'],resume_pc=event['pc'],
                                    scope='NATIVE_RESOURCE_CALL_NOT_SCENE_PRELOAD_OR_RENDER_ACCEPTANCE')
                                driver.command(f'bp497 {page["return_trap"]:x}');driver.command(f'r eip={page["address"]:x}')
                            continue
                        if getattr(self.sink,'restored_quest_journal',None):
                            if len(result.get('journal_restore_returns',[]))<15:continue
                            if result['journal_restore_returns'][-1]['slots_hex']!=self.sink.restored_quest_journal['slots_hex']:
                                raise ValueError('Restored full journal mismatch')
                            result.setdefault('journal_restore_final_frame',dict(event))
                            if not getattr(self,'town_quest_progress',False):
                                outcome='NATIVE_SAVED_JOURNAL_RESTORED';break
                        if getattr(self,'probe_npc_request',False) and 'quest_confirm_probe' not in result:
                            if time.monotonic()<getattr(self,'npc_reopen_not_before',0):continue
                            from current_npc_live_state import snapshot
                            observed=snapshot(driver,world)
                            target=531
                            if getattr(self,'town_spawn_guides',False):
                                target=self.town_guide_target
                                entries=[e for pool in observed['pools'] for e in pool['entries']]
                                if sorted((e['identity'],e['x'],e['y']) for e in entries)!=[(1606,110,69),(1607,112,70)]:continue
                            elif observed['pools'][0]['entries']!=[dict(slot=0,identity=531,x=17,y=12)]:continue
                            from current_offline_client_run import install_owned_page
                            from current_quest_live import npc_request_page
                            from pagefile_capacity_compat import memory
                            result['npc_before_request']=dict(observed,sequence=sequence)
                            ui=world+0xa7f2f6c
                            net=number(driver,f'poi({ui+0x86874:x})')
                            count=number(driver,f'poi({net+0x36c4:x})')
                            if count!=0:continue
                            page=install_owned_page(driver,lambda address:npc_request_page(address,ui,target))
                            result['quest_confirm_probe']=dict(page=page,entry_sp=event['sp'],resume_pc=event['pc'],
                                net=net,queued_before=0,action='NPC_REQUEST_96750_SELECTION_BYPASSED',
                                scope='NATIVE_CALL_NOT_PHYSICAL_INPUT')
                            driver.command(f'bp493 {page["return_trap"]:x}')
                            driver.command(f'r eip={page["address"]:x}')
                            continue
                        if 'quest_confirm_transport' in result:
                            if 'npc_request_transport' in result:
                                if getattr(self,'probe_quest_close',False):
                                    result['quest_cancel_final_frame']=dict(event)
                                    if getattr(self,'probe_npc_reopen',False):
                                        keys=('npc_before_request','npc_after_spawn','npc_request_probe','npc_request_return',
                                              'npc_request_transport','quest_dialogue_entry','quest_dialogue_header',
                                              'quest_dialogue_return','quest_confirm_probe','quest_confirm_return',
                                              'quest_confirm_transport','quest_cancel_final_frame')
                                        result['cancelled_conversation']={key:result.pop(key) for key in keys if key in result}
                                        self.probe_quest_close=False
                                        self.npc_reopen_not_before=time.monotonic()+1.1
                                        driver.command('bp490 4c7f10');driver.command('bp492 4c8234')
                                        continue
                                    outcome='NATIVE_NPC_DIALOGUE_CANCEL_TRANSPORT_OBSERVED';break
                                if (not getattr(self,'town_spawn_guides',False) or getattr(self,'town_quest_progress',False)) and 'npc_journal_return' not in result:continue
                                result['npc_conversation_final_frame']=dict(event)
                                if getattr(self,'town_quest_chain',False) and 'town_reward_chain_completed' not in result:
                                    if self.sink.town_guide_start_stage!=0:
                                        raise ValueError('Town chain requires an unstarted baseline')
                                    completed=len(result.get('town_completed_conversations',[]))
                                    if completed<(2 if getattr(self,'town_quest_reward_chain',False) else 1):
                                        keys=('npc_before_request','npc_after_spawn','npc_request_probe','npc_request_return',
                                              'npc_request_transport','quest_dialogue_entry','quest_dialogue_header',
                                              'quest_dialogue_return','quest_confirm_probe','quest_confirm_return',
                                              'quest_confirm_transport','town_dialogue_page_returns',
                                              'npc_journal_entry','npc_journal_return','npc_conversation_final_frame')
                                        result.setdefault('town_completed_conversations',[]).append({key:result.pop(key) for key in keys if key in result})
                                        self.town_guide_target=1607 if completed==0 else 1606
                                        self.npc_reopen_not_before=time.monotonic()+1.1
                                        driver.command('bp490 4c7f10');driver.command('bp492 4c8234')
                                        driver.command('bp495 4c9670')
                                        continue
                                    if getattr(self,'town_quest_reward_chain',False):
                                        from pagefile_capacity_compat import memory
                                        slot=memory(driver,world+0xa7f2f6c+0x8560c,24)
                                        if slot[0]!=1 or int.from_bytes(slot[4:6],'little')!=5569:
                                            raise ValueError('Full town quest chain missing native map reward')
                                        result['town_reward_inventory']=dict(sequence=sequence,slot=0,record_hex=slot.hex(),
                                            scope='NATIVE_OCCUPANCY_NOT_VISIBLE_ICON_OR_MAP_USE_ACCEPTANCE')
                                        result['town_reward_chain_completed']=dict(sequence=sequence)
                                        if getattr(self,'town_map_probe',False):continue
                                        outcome='NATIVE_TOWN_QUEST_THREE_STAGES_AND_REWARD_COMMITTED';break
                                    outcome='NATIVE_TOWN_QUEST_TWO_STAGES_COMMITTED';break
                                if getattr(self,'town_quest_progress',False) and (self.sink.town_guide_start_stage>=2 or 'town_reward_chain_completed' in result):
                                    from pagefile_capacity_compat import memory
                                    slot=memory(driver,world+0xa7f2f6c+0x8560c,24)
                                    if slot[0]!=1 or int.from_bytes(slot[4:6],'little')!=5569:
                                        raise ValueError('Town map reward did not reach native inventory slot0')
                                    result['town_reward_inventory']=dict(sequence=sequence,slot=0,record_hex=slot.hex(),
                                        scope='NATIVE_OCCUPANCY_NOT_VISIBLE_ICON_OR_MAP_USE_ACCEPTANCE')
                                    if getattr(self,'town_map_probe',False):
                                        if getattr(self,'town_scene_probe',False) and 'town_scene_return' in result:
                                            server_log=(self.run/'cpp-server.log').read_text(encoding='utf-8',errors='replace')
                                            if 'closing: Recovered world policy or response rejected' in server_log:
                                                raise ValueError('Scene receiver returned but server rejected followup')
                                            if 'DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED' not in server_log:continue
                                            if getattr(self,'town_scene_follow_move',False):
                                                if 'town_scene_movement_ack' in result:
                                                    position=memory(driver,world+0x224,8)
                                                    if position!=bytes.fromhex('7000000046000000') or number(driver,f'poi({world+0x30:x})')!=0:continue
                                                    result['town_scene_movement_complete']=dict(event,position_hex=position.hex(),
                                                        ring_hex=memory(driver,world+0x234,3).hex())
                                                    outcome='NATIVE_TOWN_RELOCATION_AND_MOVEMENT_COMPLETED';break
                                                if 'movement_step' not in result:
                                                    from current_login_command import town_movement_path_page
                                                    from current_offline_client_run import install_owned_page
                                                    page=install_owned_page(driver,lambda address:town_movement_path_page(address,world,112,70))
                                                    result['movement_step']=dict(world=world,page=page,entry_sp=event['sp'],step=1,queue_sequence=1)
                                                    self.probe_movement_step=True
                                                    driver.command('bc 423');driver.command('bc 424')
                                                    driver.command(f'bp425 {page["return_trap"]:x}')
                                                    driver.command(f'r eip={page["address"]:x}')
                                                continue
                                            result['town_scene_final_frame']=dict(event)
                                            if getattr(self,'town_scene_indoor_probe',False):
                                                outcome='NATIVE_TOWN_TO_INDOOR_RECEIVER_RETURNED';break
                                            outcome=('NATIVE_TOWN_RELOCATION_COMMITTED_AND_ACCEPTED' if getattr(self,'town_scene_relocate',False)
                                                     else 'NATIVE_TOWN_SAME_SCENE_TRANSFER_RETURNED');break
                                        if 'town_map_control_return' in result:
                                            result['town_map_final_frame']=dict(event)
                                            outcome='NATIVE_TOWN_MAP_CANDIDATE_PANEL_STATE_OBSERVED';break
                                        if 'town_map_probe' not in result:
                                            from current_quest_live import map_item_request_page,map_panel_snapshot
                                            from current_offline_client_run import install_owned_page
                                            ui=world+0xa7f2f6c
                                            before=map_panel_snapshot(driver,ui)
                                            if not before.get('node') or not before['scene']:raise ValueError('Native map panel unavailable')
                                            net=number(driver,f'poi({ui+0x86874:x})')
                                            if number(driver,f'poi({net+0x36c4:x})')!=0:continue
                                            page=install_owned_page(driver,lambda address:map_item_request_page(address,ui))
                                            result['town_map_probe']=dict(page=page,entry_sp=event['sp'],resume_pc=event['pc'],
                                                net=net,before=before,scope='CUSTOM-0023_NATIVE_CALL_NOT_PHYSICAL_INPUT')
                                            driver.command(f'bp500 {page["return_trap"]:x}')
                                            driver.command('bp501 46bcc0' if getattr(self,'town_scene_probe',False) else 'bp501 4c3890')
                                            driver.command(f'r eip={page["address"]:x}')
                                        continue
                                    from current_scene_live import scene_snapshot
                                    restored_scene=scene_snapshot(driver,world)
                                    if (restored_scene['x'],restored_scene['y'])!=self.sink.restored_town_position:
                                        raise ValueError('Completed town quest did not preserve restored position')
                                    result['town_completed_world_snapshot']=dict(event,snapshot=restored_scene)
                                    if getattr(self,'town_door_probe',False):
                                        from town_probe_route import east_detour
                                        if (restored_scene['area'],restored_scene['scene'],restored_scene['kind'])!=(2,4,0):
                                            raise ValueError('Town doorway probe requires restored town')
                                        path=east_detour(self.sink.town_window,self.sink.restored_town_position,86,71)[1:]
                                        if not 1<=len(path)<=38:raise ValueError('Town doorway route exceeds bounded sequence window')
                                        result['door_probe']=dict(index=0,path=[list(p) for p in path],
                                            scope='NATIVE_PATH_CALLS_TO_TOWN_GROCERY_PAIR3_NOT_PORTAL_ACCEPTANCE')
                                        continue
                                    outcome=('NATIVE_TOWN_COMPLETED_QUEST_RESTORED' if self.sink.town_guide_start_stage==3
                                             else 'NATIVE_TOWN_QUEST_REWARD_OCCUPANCY_OBSERVED');break
                                outcome=(('NATIVE_TOWN_QUEST_VISIT_COMMITTED' if self.sink.town_guide_start_stage else 'NATIVE_TOWN_QUEST_ACCEPTED') if getattr(self,'town_quest_progress',False)
                                         else 'NATIVE_TOWN_NPC_CONVERSATION_CONFIRMED' if getattr(self,'town_spawn_guides',False)
                                         else 'NATIVE_NPC_CONVERSATION_CONFIRM_TRANSPORT_OBSERVED')
                                break
                            if getattr(self,'probe_npc_request',False):continue
                            result['quest_post_transport_frame']=dict(event)
                            outcome=('NATIVE_NPC_REQUEST_TRANSPORT_OBSERVED' if getattr(self,'probe_npc_request',False)
                                     else 'NATIVE_QUEST_CONFIRM_TRANSPORT_OBSERVED')
                            break
                        if getattr(self,'diagnostic_quest_dialogue',False):continue
                        if (getattr(self,'diagnostic_encounter_limit',1)==2 and not result.get('completed_encounters') and
                                'socket_post_battle_world_loop_entry' in result):
                            if 'role_progress_return' not in result or len(result.get('role_level_returns',[]))!=2:
                                continue
                            from encounter_evidence import archive_first_encounter
                            archived=archive_first_encounter(result)
                            archived['pre_battle_movement']=result.pop('pre_battle_movement')
                            self.initial_battle_hp=76;self.initial_battle_mp=26;self.initial_experience=250
                            for breakpoint in range(428,465):driver.command(f'bc {breakpoint}')
                            driver.command('bp428 5112c0')
                        if (getattr(self,'diagnostic_world_resources',False) and
                            not getattr(self,'expect_no_world_resources',False) and 'world_resource_update_return' not in result):
                            continue
                        if (getattr(self,'diagnostic_battle_transition',False) and 'socket_post_battle_world_loop_entry' not in result and
                            not (getattr(self,'diagnostic_battle_after_movement',False) and 'pre_battle_movement' not in result)):
                            driver.command('bc 423')
                            driver.command('bc 424')
                            continue
                        if getattr(self,'restore_town_database',None) and 'restored_town_position_hex' not in result:
                            from pagefile_capacity_compat import memory
                            position=memory(driver,world+0x224,8)
                            expected=b''.join(v.to_bytes(4,'little') for v in self.sink.restored_town_position)
                            result['restored_town_position_hex']=position.hex()
                            result['restored_town_ring_hex']=memory(driver,world+0x234,3).hex()
                            if position!=expected:raise ValueError('Native town restore position mismatch')
                            if result['restored_town_ring_hex']!='010001':raise ValueError('Town reconnect ring not reset')
                            if getattr(self,'ui_world_movement',False) or getattr(self,'ui_npc_dialogue',False):
                                import sqlite3
                                with sqlite3.connect(f'file:{(self.run/"town-diagnostic-accounts.db").as_posix()}?mode=ro',uri=True) as check_db:
                                    saved=check_db.execute('SELECT area,scene,x,y,revision FROM recovered_positions WHERE character_id=1').fetchone()
                                if saved is None or saved[:4]!=(2,4,*self.sink.restored_town_position):
                                    raise ValueError('UI movement start does not match restored town save')
                                if getattr(self,'ui_world_movement',False):
                                    self.ui_world_saved_before=saved
                                    self.ui_world_movement_ready=True
                                if getattr(self,'ui_npc_dialogue',False):
                                    self.ui_npc_dialogue_ready=True
                                if getattr(self,'observe_ui_npc_buttons',False):
                                    driver.command('bp510 4c85b0')
                                write_json(self.run/'ui-world-ready.json',dict(run_id=self.run.name,pid=driver.client_pid,
                                    saved_before=list(saved),scope='WORLD_READY_FOR_EXTERNAL_UI_INPUT'))
                                continue
                            if not getattr(self,'probe_movement_step',False):
                                outcome='NATIVE_TOWN_SAVED_POSITION_RESTORED'
                                break
                        if getattr(self,'restore_movement_database',None) and not getattr(self,'diagnostic_resume_checkpoint',False):
                            from pagefile_capacity_compat import memory
                            position=memory(driver,world+0x224,8)
                            result['restored_position_hex']=position.hex()
                            expected_position=('110000000d000000' if getattr(self.sink,'restored_terminal_no_position',False)
                                               else '120000000c000000')
                            if position!=bytes.fromhex(expected_position):
                                raise ValueError('Native restored coordinates differ from saved position')
                            if getattr(self,'diagnostic_world_supply',False):
                                slot=memory(driver,world+0xa7f2f6c+0x8560c,24)
                                if getattr(self,'probe_supply_use',False):
                                    from current_offline_client_run import install_owned_page
                                    from current_login_command import supply_use_page
                                    ui=world+0xa7f2f6c
                                    source=number(driver,f'poi({ui+0x86888:x})')
                                    values=memory(driver,source+0x5c,16)
                                    mp=int.from_bytes(values[8:12],'little')
                                    hp=int.from_bytes(values[:4],'little')
                                    healing=self.expected_supply_slot[0]==3101
                                    calls=result.setdefault('supply_calls',[])
                                    done=result.setdefault('supply_results',[])
                                    exhaustion=getattr(self,'probe_supply_exhaustion',False)
                                    post_battle=getattr(self,'diagnostic_battle_transition',False)
                                    expected_results=((0,80),(0,80)) if post_battle else (((0,52),(0,52)) if exhaustion else ((2,52),(1,80),(1,80)))
                                    if healing:
                                        if post_battle or exhaustion:raise ValueError('Healing probe requires standalone three-unit fixture')
                                        expected_results=((2,56),(1,56),(1,56))
                                    if len(calls)>len(done):
                                        expected=expected_results[len(done)]
                                        if not calls[-1].get('returned') or (slot[0],mp)!=expected:
                                            continue
                                        if healing and hp!=(104,120,120)[len(done)]:continue
                                        if len(done)==len(expected_results)-1:
                                            waited=calls[-1].setdefault('observation_start',event['timestamp'])
                                            if event['timestamp']-waited<3:continue
                                        done.append({'slot_hex':slot.hex(),'resource_hex':values.hex(),'sequence':sequence})
                                    if len(done)==len(expected_results):
                                        outcome=('NATIVE_HEALING_USE_SEQUENCE_OBSERVED' if healing else 'NATIVE_POST_BATTLE_SUPPLY_OBSERVED' if post_battle else
                                                 ('NATIVE_SUPPLY_EXHAUSTION_OBSERVED' if exhaustion else 'NATIVE_SUPPLY_USE_SEQUENCE_OBSERVED'))
                                        break
                                    if not calls and (slot[0]!=(1 if exhaustion or post_battle else 3) or
                                            int.from_bytes(slot[4:6],'little')!=self.expected_supply_slot[0] or
                                            mp!=(56 if post_battle or healing else 2) or (healing and hp!=4)):
                                        raise ValueError('Native supply initial fixture mismatch')
                                    page=install_owned_page(driver,lambda address:supply_use_page(address,world))
                                    calls.append({'page':page,'entry_sp':event['sp'],'sequence':sequence})
                                    driver.command(f'bp465 {page["return_trap"]:x}')
                                    driver.command(f'r eip={page["address"]:x}')
                                    continue
                                result['supply_slot_projection']={'slot':0,'bytes_hex':slot.hex(),
                                    'scope':'READ_ONLY_NATIVE_OCCUPANCY_NOT_VISIBLE_UI_OR_USE_ACCEPTANCE'}
                                expected_item,expected_count=self.expected_supply_slot
                                if slot[0]!=expected_count or int.from_bytes(slot[4:6],'little')!=expected_item:
                                    raise ValueError('Native supply slot differs from explicit saved fixture')
                            if getattr(self.sink,'restored_terminal_no_position',False) and getattr(self,'probe_movement_step',False):
                                result['terminal_restore_world_ready']={'position_hex':position.hex(),'sequence':sequence}
                            else:
                                outcome=('NATIVE_SETTLED_BATTLE_POSITION_RESTORED' if getattr(self.sink,'restored_terminal_after_move',False) else
                                         'NATIVE_SETTLED_BATTLE_RESTORED_TO_WORLD' if getattr(self.sink,'restored_terminal_no_position',False)
                                     else 'NATIVE_SAVED_POSITION_RESTORED')
                                break
                        if getattr(self,'probe_movement_step',False):
                            if getattr(self,'shared_visibility',False) and self.sink.document.get('post_battle_movement'):
                                restored=self.sink.manifest.parent/'peer-0-repopulated.json'
                                if not restored.exists():
                                    from current_remote_actor_live import snapshot
                                    from shared_visibility_probe import observe
                                    sample=snapshot(driver,world,include_status=True)
                                    result['post_battle_remote_pool']=sample
                                    if (sample['clear_mode']!=1 or len(sample['entries'])!=1 or
                                        sample['entries'][0]['render_handle']<0):continue
                                    _,evidence=observe(self.sink,self.lab_peer,self.run.name,driver.client_pid,sample)
                                    if not evidence:continue
                                    write_json(restored,evidence)
                            from pagefile_capacity_compat import memory
                            from current_offline_client_run import install_owned_page
                            from current_login_command import movement_step_page,movement_path_page
                            position=memory(driver,world+0x224,8)
                            ring=memory(driver,world+0x234,3)
                            step=len(result.get('movement_steps',[]))+1
                            queue_sequence=step-getattr(self,'movement_sequence_offset',0)
                            queue_sequence%=40
                            precondition={'position_hex':position.hex(),'ring_hex':ring.hex()}
                            if getattr(self,'town_entry_lab',False) and result.get('town_window_builds'):
                                manager=result['town_window_builds'][-1]['manager']
                                header=memory(driver,manager+0x30,8)
                                origin=memory(driver,manager+0x103c,8)
                                precondition['town_navigation']={
                                    'manager':manager,'kind':int.from_bytes(header[:4],'little'),
                                    'mode':int.from_bytes(header[4:],'little'),
                                    'origin':[int.from_bytes(origin[i:i+4],'little',signed=True) for i in (0,4)],
                                    'camera_hex':memory(driver,world+0x21c,8).hex()}
                            result.setdefault('movement_precondition',precondition)
                            result.setdefault('movement_readiness',[]).append(dict(precondition,step=step))
                            expected_position=bytes.fromhex('110000000d000000' if step%2 else '120000000c000000')
                            town_start=getattr(self.sink,'town_start',None)
                            if town_start:
                                x,y=town_start
                                offset=step-1 if getattr(self,'town_east_path',False) else (0 if step%2 else 1)
                                expected_position=(x+offset).to_bytes(4,'little')+y.to_bytes(4,'little')
                                if getattr(self,'town_post_battle_movement',False):
                                    expected_position=(x+(0 if step%2 else 1)).to_bytes(4,'little')+y.to_bytes(4,'little')
                                if getattr(self,'town_detour_path',False):
                                    from town_probe_route import east_detour
                                    route=east_detour(self.sink.town_window,town_start,getattr(self.sink,'town_target_x',100))
                                    if self.movement_steps!=len(route)-1:raise ValueError('Town route length differs from requested steps')
                                    result['town_route']=route
                                    expected_position=b''.join(v.to_bytes(4,'little') for v in route[step-1])
                            if ring!=bytes([1,(queue_sequence-1)%40,queue_sequence]):
                                raise ValueError('Native movement spawn/ring precondition mismatch')
                            if position!=expected_position:
                                if step==1 or sum(e['step']==step for e in result['movement_readiness'])>=100:
                                    raise ValueError('Native movement coordinates did not reach next step')
                                continue
                            if step>getattr(self,'movement_steps',1):
                                motion_state=number(driver,f'poi({world+0x30:x})')
                                if motion_state!=0:
                                    if sum(e['step']==step for e in result['movement_readiness'])>=100:
                                        raise ValueError('Native movement did not return to idle')
                                    continue
                                result['movement_completion']={'position_hex':position.hex(),
                                    'ring_hex':ring.hex(),'motion_state':motion_state,'event':dict(event)}
                                if getattr(self,'expect_no_world_resources',False):
                                    started=result.setdefault('missing_resource_observation_started',event['timestamp'])
                                    if event['timestamp']-started<5:
                                        continue
                                outcome='NATIVE_MOVEMENT_PATH_COMPLETED'
                                if getattr(self,'shared_visibility',False):
                                    marker=self.sink.manifest.parent/f'peer-{self.lab_peer}-path-completed.json'
                                    if not marker.exists():
                                        temporary=marker.with_suffix('.tmp')
                                        write_json(temporary,{'run_id':self.run.name,'steps':result['movement_steps'],
                                                           'completion':result['movement_completion']})
                                        temporary.replace(marker)
                                    if self.sink.document.get('simultaneous_movement'):
                                        from current_remote_actor_live import snapshot
                                        from shared_visibility_probe import observe
                                        moved=[self.sink.manifest.parent/f'peer-{i}-moved.json' for i in (0,1)]
                                        if not all(p.exists() for p in moved):
                                            sample=snapshot(driver,world)
                                            result['shared_visibility_last_sample']=sample
                                            done,evidence=observe(self.sink,self.lab_peer,self.run.name,driver.client_pid,sample)
                                            if evidence:result['shared_visibility']=evidence
                                            if not done or not all(p.exists() for p in moved):continue
                                        outcome='NATIVE_SHARED_PLAYER_MOVEMENT_OBSERVED'
                                    elif self.sink.document.get('post_battle_movement'):
                                        if not (self.sink.manifest.parent/'peer-1-moved.json').exists():continue
                                    elif not (self.sink.manifest.parent/'peer-0-moved.json').exists():continue
                                break
                            builder=movement_path_page if getattr(self,'movement_steps',1)>1 else movement_step_page
                            if town_start:
                                from current_login_command import town_movement_path_page
                                offset=step if getattr(self,'town_east_path',False) else (1 if step%2 else 0)
                                target=(town_start[0]+offset,town_start[1])
                                if getattr(self,'town_detour_path',False):target=route[step]
                                if getattr(self,'town_post_battle_movement',False):
                                    target=(town_start[0]+(1 if step%2 else 0),town_start[1])
                                    grid=json.loads((HOME/'artifacts/world-atlas/indoor-2-15.json').read_text())['grid']
                                    lx,ly=target
                                    side=grid['side']
                                    cells=grid['cells_hex']
                                else:
                                    window=self.sink.town_window
                                    lx,ly=target[0]-window['origin_x'],target[1]-window['origin_y']
                                    side=window.get('side',63)
                                    cells=window['cells_hex']
                                cell_offset=(ly*side+lx)*2
                                if not (0<=lx<side and 0<=ly<side) or cells[cell_offset:cell_offset+2] not in ('01','02'):
                                    raise ValueError('Movement probe target lacks qualified static coverage')
                                page=install_owned_page(driver,lambda address:town_movement_path_page(address,world,*target))
                            else:
                                page=install_owned_page(driver,lambda address:builder(address,world,step))
                            result['movement_step']={'world':world,'page':page,'entry_sp':event['sp'],
                                                     'step':step,'queue_sequence':queue_sequence,'precondition':precondition}
                            if town_start:result['movement_step']['town_target']=target
                            driver.command('bc 423')
                            driver.command('bc 424')
                            driver.command(f'bp425 {page["return_trap"]:x}')
                            driver.command(f'r eip={page["address"]:x}')
                            continue
                        if getattr(self,'shared_visibility',False):
                            from current_remote_actor_live import snapshot
                            from shared_visibility_probe import observe
                            sample=snapshot(driver,world,include_status=self.sink.document.get('observe_battle',False))
                            if self.sink.document.get('restored_source'):
                                from pagefile_capacity_compat import memory
                                sample['local_position_hex']=memory(driver,world+0x224,8).hex()
                                sample['local_ring_hex']=memory(driver,world+0x234,3).hex()
                            result['shared_visibility_last_sample']=sample
                            done,evidence=observe(self.sink,self.lab_peer,self.run.name,driver.client_pid,sample)
                            if evidence:result['shared_visibility']=evidence
                            if evidence and evidence.get('phase')=='MOVEMENT_REQUEST':
                                self.probe_movement_step=True
                                self.movement_steps=3
                            if not done:continue
                            outcome='NATIVE_SHARED_PLAYER_VISIBILITY_OBSERVED'
                            if evidence.get('phase')=='REMOTE_DEPARTURE_OBSERVED':
                                outcome='NATIVE_SHARED_PLAYER_DEPARTURE_OBSERVED'
                            if evidence.get('phase')=='REMOTE_MOVEMENT_OBSERVED':
                                outcome='NATIVE_SHARED_PLAYER_MOVEMENT_OBSERVED'
                            if evidence.get('phase')=='REMOTE_REJOIN_OBSERVED':
                                outcome='NATIVE_SHARED_PLAYER_REJOIN_OBSERVED'
                            if evidence.get('phase')=='REMOTE_BATTLE_TITLE_CLEARED':
                                outcome='NATIVE_SHARED_PLAYER_BATTLE_TITLE_CLEARED'
                            if evidence.get('phase')=='REMOTE_BATTLE_MOVEMENT_OBSERVED':
                                outcome='NATIVE_SHARED_PLAYER_BATTLE_MOVEMENT_OBSERVED'
                            break
                        if getattr(self,'remote_actor_probe_language',None) is not None:
                            from current_remote_actor_live import snapshot,RemoteActorStatusLifecycle
                            if not hasattr(self,'remote_actor_lifecycle'):
                                self.remote_actor_lifecycle=RemoteActorStatusLifecycle((0x100,0,0x200,0,0x400,0,0x800,0,0x1000,0,1,0))
                            sample=snapshot(driver,world,include_status=True)
                            done=self.remote_actor_lifecycle.observe(sample)
                            result['remote_actor_lifecycle']={'stage':self.remote_actor_lifecycle.stage,
                                'evidence':self.remote_actor_lifecycle.evidence,
                                'scope':'NATIVE_POOL_OBSERVATION_NOT_RENDERED_MULTIPLAYER_ACCEPTANCE'}
                            if not done:continue
                            outcome='NATIVE_REMOTE_ACTOR_POOL_LIFECYCLE_OBSERVED'
                            break
                        if getattr(self,'ui_world_movement_ready',False) or getattr(self,'ui_npc_dialogue_ready',False):continue
                        outcome='NATIVE_WORLD_FRAMES_OBSERVED'
                        break
                    continue
                if index in (421,422) and getattr(self,'observe_world_loop',False):
                    from pagefile_capacity_compat import number
                    world=result['world_initializer']['world_object']
                    if number(driver,'@ecx' if index==421 else '@ebx')!=world:
                        raise ValueError('Original world loop object mismatch')
                    event['event_type']='LIVE_WORLD_LOOP_ENTRY' if index==421 else 'LIVE_WORLD_LOOP_DISPATCH'
                    if index==421:
                        result['world_loop_entry']=dict(event)
                        driver.command('bc 421')
                    else:
                        event['world_state']=number(driver,'@ecx')
                        states=result.setdefault('world_loop_dispatches',[])
                        states.append(dict(event))
                        if len(states)>=8:
                            driver.command('bc 422')
                    continue
                if index in (418,419,420) and getattr(self,'observe_world_entry',False):
                    from pagefile_capacity_compat import number,memory
                    event['event_type']={418:'LIVE_WORLD_CONSTRUCTOR',419:'LIVE_WORLD_INITIALIZER',420:'LIVE_WORLD_INITIALIZER_RETURN'}[index]
                    if index!=420:
                        event['world_object']=number(driver,'@ecx')
                        if index==419:
                            event['arguments_hex']=memory(driver,event['sp']+4,24).hex()
                        result['world_constructor' if index==418 else 'world_initializer']=dict(event)
                        driver.command(f'bc {index}')
                        continue
                    result['world_initializer_return']=dict(event)
                    if event['eax'] and getattr(self,'observe_world_loop',False):
                        if getattr(self,'diagnostic_battle_transition',False):
                            driver.command('bp428 5112c0')
                        driver.command('bc 420')
                        driver.command('bp421 4655e0')
                        if getattr(self,'diagnostic_world_resources',False):
                            driver.command('bp457 4e71e0')
                        driver.command('bp422 465638')
                        if getattr(self,'observe_world_frames',False):
                            driver.command('bp423 467bca')
                            driver.command('bp424 467bd7')
                        continue
                    outcome='NATIVE_WORLD_INITIALIZER_SUCCEEDED' if event['eax'] else 'NATIVE_WORLD_INITIALIZER_FAILED'
                    break
                if index in (416,417) and getattr(self,'probe_character_select',False):
                    from pagefile_capacity_compat import memory,number
                    c=result['character_selection_command']
                    if index==416:
                        raw=bytes.fromhex(c['page']['hex'])
                        if memory(driver,c['page']['address'],len(raw))!=raw:
                            raise ValueError('Character selection command page changed')
                        state=number(driver,f'poi({c["login_object"]+0x178cec:x})')
                        if event['sp']!=c['entry_sp'] or event['eax']!=1 or state!=20:
                            raise ValueError('Native character selection command rejected')
                        c.update(state_after=state,return_eax=event['eax'])
                        event['event_type']='CHARACTER_SELECTION_COMMAND_RETURN'
                        driver.command('bc 416')
                        driver.command('bp417 40df8c')
                        driver.command('r eip=40557e')
                        continue
                    if event['eax']!=1:
                        raise ValueError('Native login loop did not return selected character')
                    event['event_type']='CHARACTER_SELECTION_LOOP_RETURN'
                    result['character_selection_return']=dict(event)
                    if getattr(self,'observe_world_entry',False):
                        driver.command('bc 417')
                        driver.command('bp418 4643b0')
                        driver.command('bp419 464910')
                        driver.command('bp420 40e0db')
                        continue
                    outcome='NATIVE_CHARACTER_SELECTION_RETURNED'
                    break
                if index in (414, 415) and getattr(self, 'observe_created_refresh', False):
                    from pagefile_capacity_compat import memory, number
                    login=result['login_entry']['login_object']
                    state=number(driver,f'poi({login+0x178cec:x})')
                    if number(driver,'@esi' if index==414 else '@ebp')!=login or state!=(4 if index==414 else 19):
                        raise ValueError('Native created refresh state/object mismatch')
                    record=memory(driver,number(driver,f'poi({login+0x178ce0:x})'),74)
                    event.update(event_type='CREATED_REFRESH_RETURN' if index==414 else 'CREATED_SELECTION_READY',
                                 login_state=state,character_list_hex=record.hex())
                    if index==414:
                        result['created_refresh']=dict(event)
                        driver.command('bc 414')
                        continue
                    panel=int.from_bytes(memory(driver,login+0x178cd0,2),'little',signed=True)
                    if not 1<=record[0]<=2 or panel<0:
                        raise ValueError('Native refreshed character list/panel missing')
                    event['panel_handle']=panel
                    result['created_selection_ready']=dict(event)
                    if getattr(self,'probe_character_select',False):
                        from current_login_command import character_select_page
                        from current_offline_client_run import install_owned_page
                        selected=int.from_bytes(memory(driver,login+0x178ce4,2),'little',signed=True)
                        if not 0<=selected<record[0]:
                            raise ValueError('Native selected character out of bounds')
                        page=install_owned_page(driver,lambda address:character_select_page(address,login))
                        result['character_selection_command']={'page':page,'login_object':login,
                            'entry_sp':event['sp'],'selected':selected}
                        driver.command('bc 415')
                        driver.command(f'bp416 {page["return_trap"]:x}')
                        driver.command(f'r eip={page["address"]:x}')
                        continue
                    outcome='NATIVE_CREATED_SELECTION_READY'
                    break
                if index in (411, 412, 413) and getattr(self, 'probe_character_create', False):
                    from pagefile_capacity_compat import memory, number
                    if index == 411:
                        logical=memory(driver,number(driver,'@eax'),3)
                        if logical[0]!=0x18:
                            raise ValueError('Native creation slot reply opcode mismatch')
                        result['create_slot_ack']={'logical_hex':logical.hex(),'entry_sp':event['sp'],
                            'output':number(driver,'poi(@esp+c)'), 'return_pc':number(driver,'poi(@esp+8)')}
                        event['event_type']='CREATE_SLOT_ACK_ENTRY'
                        driver.command('bp412 4152d0')
                    elif index == 412:
                        ack=result['create_slot_ack']
                        token=memory(driver,ack['output'],1)[0]
                        if token!=bytes.fromhex(ack['logical_hex'])[1]:
                            raise ValueError('Native creation slot copy mismatch')
                        ack['copied_slot']=token
                        event['event_type']='CREATE_SLOT_ACK_CONSUMED'
                        driver.command(f'bp413 {ack["return_pc"]:x}')
                    else:
                        ack=result['create_slot_ack']
                        if event['eax']!=0 or event['sp']!=ack['entry_sp']+20:
                            raise ValueError('Native creation slot return mismatch')
                        ack['return_eax']=0
                        event['event_type']='CREATE_SLOT_ACK_RETURN'
                        if getattr(self,'observe_created_refresh',False):
                            driver.command('bc 413')
                            driver.command('bp414 40c099')
                            driver.command('bp415 40557e')
                            continue
                        outcome='NATIVE_CREATE_SLOT_ACK_RETURNED'
                        break
                    driver.command(f'bc {index}')
                    continue
                if index in (408, 410) and getattr(self, 'probe_character_create', False):
                    from pagefile_capacity_compat import memory, number
                    key = 'creation_submit' if index == 410 else 'creation_next'
                    c = result[key]
                    raw = bytes.fromhex(c['page']['hex'])
                    if memory(driver, c['page']['address'], len(raw)) != raw:
                        raise ValueError('Native creation command page changed')
                    state = number(driver, f'poi({c["login_object"] + 0x178cec:x})')
                    if event['sp'] != c['entry_sp'] or state != (24 if index == 410 else 6):
                        raise ValueError('Native creation command return/state mismatch')
                    c.update(state_after=state, return_eax=event['eax'])
                    event['event_type'] = 'CHARACTER_CREATE_SUBMIT_RETURN' if index == 410 else 'CHARACTER_CREATE_NEXT_RETURN'
                    driver.command(f'bc {index}')
                    if index == 408:
                        driver.command('bp409 4057e3')
                    else:
                        driver.command('bp411 4152be')
                    driver.command(f'r eip={0x4057e3 if index == 410 else 0x4056db:x}')
                    continue
                if index == 409 and getattr(self, 'probe_character_create', False):
                    from pagefile_capacity_compat import memory, number
                    from current_login_command import creation_page
                    from current_offline_client_run import install_owned_page
                    login = result['login_entry']['login_object']
                    panel = int.from_bytes(memory(driver, login + 0x178cce, 2), 'little', signed=True)
                    if number(driver, '@ebp') != login or number(driver, f'poi({login + 0x178cec:x})') != 23 or panel < 0:
                        raise ValueError('Native creation detail panel not ready')
                    page = install_owned_page(driver, lambda address: creation_page(address, login, True, self.lab_peer))
                    result['creation_submit'] = {'page': page, 'entry_sp': event['sp'], 'login_object': login, 'panel_handle': panel}
                    event['event_type'] = 'CHARACTER_CREATE_DETAIL_READY'
                    driver.command('bc 409')
                    driver.command(f'bp410 {page["return_trap"]:x}')
                    driver.command(f'r eip={page["address"]:x}')
                    continue
                if index == 407 and getattr(self, 'observe_character_create', False):
                    from pagefile_capacity_compat import memory, number
                    login = result['login_entry']['login_object']
                    panel = int.from_bytes(memory(driver, login + 0x178ccc, 2), 'little', signed=True)
                    state = number(driver, f'poi({login + 0x178cec:x})')
                    if number(driver, '@ebp') != login or state != 21 or panel < 0:
                        raise ValueError('Native creation initializer/state/handle mismatch')
                    event.update(event_type='CHARACTER_CREATE_PANEL_READY', login_state=state,
                                 panel_handle=panel,
                                 draft_hex=memory(driver, login + 0x15280, 40).hex())
                    result['character_create_panel'] = dict(event)
                    if getattr(self, 'probe_character_create', False):
                        from current_login_command import creation_page
                        from current_offline_client_run import install_owned_page
                        page = install_owned_page(driver, lambda address: creation_page(address, login))
                        result['creation_next'] = {'page': page, 'entry_sp': event['sp'], 'login_object': login}
                        driver.command('bc 407')
                        driver.command(f'bp408 {page["return_trap"]:x}')
                        driver.command(f'r eip={page["address"]:x}')
                        continue
                    outcome = 'NATIVE_CHARACTER_CREATE_PANEL_READY'
                    break
                if index in (404, 405, 406) and getattr(self, 'probe_server_confirm', False):
                    from pagefile_capacity_compat import memory, number
                    if index == 404:
                        packet = memory(driver, number(driver, '@eax'), 75)
                        if packet[0] != 7 or packet[1] > 2:
                            raise ValueError('Unsupported native character-list body')
                        result['character_list_consumer'] = {
                            'entry_sp': event['sp'], 'logical_hex': packet.hex(),
                            'output': number(driver, 'poi(@esp+28)'),
                            'converted': number(driver, 'poi(@esp+2c)'),
                            'return_pc': number(driver, 'poi(@esp+14)')}
                        event['event_type'] = 'CHARACTER_LIST_NATIVE_ENTRY'
                    elif index == 405:
                        state = result['character_list_consumer']
                        copied = memory(driver, state['output'], 74)
                        if copied != bytes.fromhex(state['logical_hex'])[1:]:
                            raise ValueError('Native character-list copy differs')
                        state['copied_hex'] = copied.hex()
                        if state['converted']:
                            state['converted_hex'] = memory(driver, state['converted'], 124).hex()
                        event['event_type'] = 'CHARACTER_LIST_CONSUMED'
                        driver.command(f'bp406 {state["return_pc"]:x}')
                    else:
                        state = result['character_list_consumer']
                        if event['eax'] != 0 or event['sp'] != state['entry_sp'] + 48:
                            raise ValueError('Native character-list return ABI differs')
                        state['return_eax'] = event['eax']
                        event['event_type'] = 'CHARACTER_LIST_NATIVE_RETURN'
                        if (getattr(self,'restore_movement_database',None) or getattr(self,'restore_town_database',None) or
                                (getattr(self,'shared_visibility',False) and
                                 (self.sink.document.get('restored_source') or self.sink.document.get('existing_characters')))):
                            if bytes.fromhex(state['copied_hex'])[0]!=1:
                                raise ValueError('Restore requires one persisted character')
                            driver.command('bc 406')
                            driver.command('bp415 40557e')
                            continue
                        if getattr(self, 'observe_character_create', False):
                            if bytes.fromhex(state['copied_hex'])[0] != 0:
                                raise ValueError('Creation observation requires an empty account list')
                            driver.command('bc 406')
                            driver.command('bp407 4056db')
                            continue
                        outcome = 'NATIVE_CHARACTER_LIST_CONSUMER_RETURNED'
                        break
                    driver.command(f'bc {index}')
                    continue
                if index == 402 and getattr(self, 'probe_server_confirm', False):
                    from pagefile_capacity_compat import memory, number
                    from current_offline_client_run import install_owned_page
                    from current_login_command import select_page
                    login = result['login_entry']['login_object']
                    if number(driver, '@ebp') != login or number(driver, f'poi({login + 0x178cec:x})') != 17:
                        raise ValueError('Native second list waiting state required')
                    panel = int.from_bytes(memory(driver, login + 0x178cc8, 2), 'little', signed=True)
                    if panel < 0:
                        raise ValueError('Missing second list panel')
                    page = install_owned_page(driver, lambda address: select_page(address, login, True))
                    result['channel_confirm'] = {'page': page, 'entry_sp': event['sp'], 'panel_handle': panel,
                        'selected': int.from_bytes(memory(driver, login + 0xb40, 2), 'little')}
                    event['event_type'] = 'CHANNEL_CONFIRM_READY'
                    driver.command('bc 402')
                    driver.command(f'bp403 {page["return_trap"]:x}')
                    driver.command(f'r @eip = {page["address"]:x}')
                    continue
                if index == 403 and getattr(self, 'probe_server_confirm', False):
                    from pagefile_capacity_compat import number
                    confirmation = result['channel_confirm']
                    login = result['login_entry']['login_object']
                    confirmation['state_after'] = number(driver, f'poi({login + 0x178cec:x})')
                    confirmation['return_eax'] = event['eax']
                    if event['sp'] != confirmation['entry_sp'] or event['eax'] != 1 or confirmation['state_after'] != 18:
                        raise ValueError('Native channel confirmation did not accept the list')
                    event['event_type'] = 'CHANNEL_CONFIRM_RETURN'
                    driver.command('bc 403')
                    driver.command('r @eip = 40540b')
                    continue
                if index == 400 and getattr(self, 'probe_server_confirm', False):
                    from pagefile_capacity_compat import memory, number
                    from current_offline_client_run import install_owned_page
                    from current_login_command import select_page
                    login = result['login_entry']['login_object']
                    if number(driver, '@ebp') != login or number(driver, f'poi({login + 0x178cec:x})') != 16:
                        raise ValueError('Native server-list waiting state required')
                    if not any(e.get('event_type') == 'SERVER_LIST_UI_READY' for e in self.events):
                        raise ValueError('Native server list not observed')
                    page = install_owned_page(driver, lambda address: select_page(address, login))
                    result['server_confirm'] = {'page': page, 'entry_sp': event['sp'],
                        'selected': int.from_bytes(memory(driver, login + 0x8f4, 2), 'little'),
                        'scope': 'NATIVE_CONFIRM_EVENT_EXISTING_SELECTION_NOT_AUTH_BYPASS'}
                    event['event_type'] = 'SERVER_CONFIRM_READY'
                    driver.command('bc 400')
                    driver.command(f'bp401 {page["return_trap"]:x}')
                    driver.command(f'r @eip = {page["address"]:x}')
                    continue
                if index == 401 and getattr(self, 'probe_server_confirm', False):
                    from pagefile_capacity_compat import number
                    confirmation = result['server_confirm']
                    login = result['login_entry']['login_object']
                    confirmation['state_after'] = number(driver, f'poi({login + 0x178cec:x})')
                    confirmation['return_eax'] = event['eax']
                    if event['sp'] != confirmation['entry_sp'] or event['eax'] != 0 or confirmation['state_after'] != 3:
                        raise ValueError('Native server confirmation did not accept the list')
                    event['event_type'] = 'SERVER_CONFIRM_RETURN'
                    driver.command('bc 401')
                    driver.command('bp402 40540b')
                    driver.command('r @eip = 4053a8')
                    continue
                if index == 399 and getattr(self, 'probe_login_submit', False):
                    from pagefile_capacity_compat import number
                    submission = result['login_submission']
                    login = submission['login_object']
                    submission['state_after'] = number(driver, f'poi({login + 0x178cec:x})')
                    submission['return_eax'] = event['eax']
                    if event['sp'] != submission['entry_sp'] or event['eax'] != 1 or submission['state_after'] != 15:
                        raise ValueError('Native credential submit transition differs')
                    event['event_type'] = 'LOGIN_TEST_SUBMIT_RETURN'
                    driver.command('bc 399')
                    driver.command('r @eip = 405336')
                    continue
                if index in (397, 398) and getattr(self, 'probe_login_panel', False):
                    from pagefile_capacity_compat import memory, number
                    login = result['login_command']['login_object']
                    if number(driver, '@ebp') != login:
                        raise ValueError('Login panel object changed')
                    event['event_type'] = 'LOGIN_PANEL_INITIALIZER_RETURN' if index == 397 else 'LOGIN_PANEL_READY'
                    event['login_state'] = number(driver, f'poi({login + 0x178cec:x})')
                    event['panel_handle'] = int.from_bytes(memory(driver, login + 0x178cc4, 2), 'little', signed=True)
                    driver.command(f'bc {index}')
                    if index == 397:
                        if event['login_state'] != 1 or event['panel_handle'] < 0:
                            raise ValueError('Native login panel initialization failed')
                        result['login_panel_initialization'] = dict(event)
                        continue
                    if event['login_state'] != 14 or event['panel_handle'] != result['login_panel_initialization']['panel_handle']:
                        raise ValueError('Native login input state differs')
                    result['login_panel_ready'] = dict(event)
                    if getattr(self, 'probe_login_submit', False):
                        from current_offline_client_run import install_owned_page
                        from current_login_command import submit_page
                        page = install_owned_page(driver, lambda address: submit_page(address, login, self.lab_peer))
                        result['login_submission'] = {'login_object': login, 'entry_sp': event['sp'],
                            'page': page, 'lab_peer': self.lab_peer, 'scope': 'PUBLIC_LAB_NATIVE_TEXT_SETTERS_AND_SUBMIT'}
                        driver.command(f'bp399 {page["return_trap"]:x}')
                        driver.command(f'r @eip = {page["address"]:x}')
                        continue
                    outcome = 'NATIVE_LOGIN_PANEL_READY'
                    break
                if index == 395 and getattr(self, 'probe_login_command', False):
                    from pagefile_capacity_compat import memory, number
                    from current_offline_client_run import install_owned_page
                    from current_login_command import call_page
                    login = result['login_entry']['login_object']
                    if number(driver, '@ebp') != login or number(driver, f'poi({login + 0x178cec:x})') != 0:
                        raise ValueError('Initialized login state0 required')
                    result['login_command'] = {'entry_sp': event['sp'], 'login_object': login,
                        'scope': 'DIAGNOSTIC_NATIVE_MENU_COMMAND_NOT_DESKTOP_INPUT_NOT_AUTHENTICATION'}
                    page = install_owned_page(driver, lambda address: call_page(address, login))
                    result['login_command']['page'] = page
                    event['event_type'] = 'LOGIN_MENU_INITIALIZED'
                    driver.command('bc 395')
                    driver.command(f'bp396 {page["return_trap"]:x}')
                    driver.command(f'r @eip = {page["address"]:x}')
                    continue
                if index == 396 and getattr(self, 'probe_login_command', False):
                    from pagefile_capacity_compat import memory, number
                    command = result['login_command']
                    login = command['login_object']
                    command['state_after'] = number(driver, f'poi({login + 0x178cec:x})')
                    command['previous_after'] = number(driver, f'poi({login + 0x178cf0:x})')
                    command['return_eax'] = event['eax']
                    if event['sp'] != command['entry_sp'] or event['eax'] != 1 or command['state_after'] != 1 or command['previous_after'] != 0:
                        raise ValueError('Native menu command transition differs')
                    raw = bytes.fromhex(command['page']['hex'])
                    if memory(driver, command['page']['address'], len(raw)) != raw:
                        raise ValueError('Diagnostic command page changed')
                    event['event_type'] = 'LOGIN_MENU_COMMAND_RETURN'
                    if getattr(self, 'probe_login_panel', False):
                        driver.command('bc 396')
                        driver.command('bp397 405325')
                        driver.command('bp398 405336')
                        # Rejoin the original loop at the instruction interrupted
                        # before the diagnostic call; no state or grant is set here.
                        driver.command('r @eip = 404f2b')
                        continue
                    outcome = 'NATIVE_LOGIN_MENU_COMMAND_RETURNED'
                    break
                if index == 394 and getattr(self, 'observe_login_entry', False):
                    from pagefile_capacity_compat import memory, number
                    login = number(driver, '@ecx')
                    application = number(driver, '@ebp')
                    if event['ret'] != 0x40df8c or not 0x10000 <= login < 0x7fffffff:
                        raise ValueError('Unexpected original login loop ABI')
                    if number(driver, f'poi({application + 0x43c:x})') != login:
                        raise ValueError('Login object not owned by native application')
                    event.update(event_type='NATIVE_LOGIN_LOOP_ENTRY', login_object=login,
                        application=application, login_state=number(driver, f'poi({login + 0x178cec:x})'),
                        previous_login_state=number(driver, f'poi({login + 0x178cf0:x})'),
                        arguments_hex=memory(driver, event['sp'] + 4, 20).hex(),
                        scope='ENTRY_OBSERVATION_ONLY_NO_INPUT_NO_AUTH_BYPASS')
                    driver.command('bc 394')
                    result['login_entry'] = dict(event)
                    if getattr(self, 'probe_login_command', False):
                        driver.command('bp395 404f2b')
                        continue
                    outcome='NATIVE_LOGIN_LOOP_ENTRY_OBSERVED'
                    break
                if getattr(self,'pagefile_adapter',None) and self.pagefile_adapter.handle(index,event,driver):
                    continue
                if getattr(self,'warning_input_trace',False):
                    from warning_input_trace import SITES as warning_sites, capture as warning_capture
                    if index in warning_sites:
                        if warning_capture(index,event,driver):
                            outcome='WARNING_PREDICATE_OBSERVED_BEFORE_DIALOG';break
                        continue
                if getattr(self,'crypto_observer',None) and self.crypto_observer.handle(index,event,driver):
                    continue
                if index in (249,250) and getattr(self,'gate',None):
                    event['event_type']='UI_PATH_A_HIT' if index==249 else 'UI_PATH_B_HIT'
                    self.gate.path(event)
                    continue
                if index in (245,246,247,248):
                    event['event_type']={245:'SERVER_LIST_UI_COUNT',246:'SERVER_LIST_UI_READY',247:'SERVER_LIST_HANDLER',248:'SERVER_LIST_WRITTEN'}[index]
                    if index in (245,246):
                        event['list_state']=driver.command('.printf "LIST_UI count=%x selected=%x enabled0=%x directory_count=%x\\n", @ebp, wo(@ebx+8f4), wo(@ebx+8e), dwo(5b489c)')
                    if index==247:event['payload']=driver.command('db @esi L5')
                    if index==248:event['written']=driver.command('.printf "LIST_WRITE entry0=%x\\n", dwo(@edx)')
                    driver.command(f'bc {index}')
                    if index==246 and getattr(self,'gate',None):
                        self.gate.prepare(self.events,event)
                    continue
                if index in (240,241,242,243):
                    event['event_type']={240:'LOGIN_TERMINAL_HANDLER',241:'LOGIN_TERMINAL_RETURN',242:'LOGIN_STATE_CHANGE_ENTER',243:'LOGIN_STATE_CHANGE_RETURN'}[index]
                    if index==240:
                        event['result_fields']=driver.command('db @esi L11')
                    if index in (242,243):
                        event['ui_state']=driver.command('.printf "LOGIN_UI state=%x previous=%x\\n", dwo(@ebp+178cec), dwo(@ebp+178cf0)')
                    if index==243 and getattr(self,'server_list_probe',False):
                        event['list_state']=driver.command('.printf "SERVER_LIST ui=%p directory_count=%x directory0=%p selected=%x\\n", @ebp, dwo(5b489c), dwo(5b48a0), wo(@ebp+8f4)')
                        event['entry0_status']=driver.command('db @ebp+8c L14')
                        event['directory0']=driver.command('db poi(5b48a0) L44')
                        write_json(self.run/'STATE_LOGIN_ACCEPTED.json',event)
                        driver.command('bp244 402dc0')
                    driver.command(f'bc {index}')
                    continue
                if index==244:
                    event['event_type']='SERVER_LIST_MESSAGE_CALLER'
                    event['caller_code']=driver.command(f'ub {event["ret"]:x} L30')+driver.command(f'u {event["ret"]:x} L20')
                    event['registers']=driver.command('r')
                    driver.command('bc 244')
                    continue
                if index in (235,236,237,238,239):
                    event['event_type']={235:'S2C0003_HANDLER_ENTERED',236:'S2C0003_COMPARE_1',237:'S2C0003_COMPARE_2',238:'S2C0003_STRUCT_COPIED',239:'S2C0003_CONSUMED'}[index]
                    if index==235:
                        event['flags']=driver.command('.printf "S2C3_FLAGS value=%x\\n", by(@esi+a8)')
                    driver.command(f'bc {index}')
                    if index==239:
                        event['terminal_state']=driver.command('.printf "AFTER_1D session=%p enabled=%x accumulated=%x result=%p flags0=%x flags4=%x flags8=%x flagsc=%x feedback=%x\\n", @ebp, by(@ebp+2cb8), dwo(@ebp+2cc0), dwo(@ebp), dwo(@ebp+758), dwo(@ebp+75c), dwo(@ebp+760), dwo(@ebp+764), by(@ebp+2cae)')
                        event['terminal_code']=driver.command('u 414386 L30')
                        event['state_writer']=driver.command('u 40afeb L10')
                        write_json(self.run/'STATE_AFTER_S2C_0003.json',event)
                        if not getattr(self,'terminal',False):
                            outcome='S2C0003_TRANSITION_CAPTURED';break
                        continue
                    continue
                if index in (228,229,230):
                    event['event_type']={228:'POST_SEED_HANDLER_ENTERED',229:'POST_SEED_FIELD_ACCEPTED',230:'POST_SEED_WAIT_RETURN'}[index]
                    event['registers']=driver.command('r')
                    if index==228:
                        event['field_comparison']=driver.command('.printf "POST_FIELD opcode=%x received=%x expected=%x\\n", by(@eax), by(@eax+1), by(@esp+14)')
                    if index==230 and getattr(self,'c2s_strike',False):
                        event['builder_path']=driver.command('u 413f52 L100')
                        driver.command('bp231 4124d0')
                    driver.command(f'bc {index}')
                    continue
                if index in (231,232,233,234):
                    event['event_type']={231:'C2S0002_FRAME_INPUT',232:'C2S0002_NEXT_WAIT',233:'C2S0002_BUILDER_ROOT',234:'C2S0002_INPUT_COPY'}[index]
                    event['code']=driver.command(f'ub {event["ret"]:x} L10')+driver.command(f'u {event["ret"]:x} L90')
                    event['registers']=driver.command('r')
                    if index==231:
                        if event['a1']!=173:outcome='C2S0002_UNEXPECTED_LOGICAL_LENGTH';break
                        path=self.run/'network/C2S_0002.logical.bin'
                        event['capture']=driver.command(f'.writemem "{path.as_posix()}" {event["a0"]:x} Lad')
                        event['logical_length']=173
                    if index==233:
                        event['entry_code']=driver.command('u 413e10 L26')
                    if index==234:
                        event['writers']=driver.command('u 40b010 L40')
                        event['copy_implementation']=driver.command('u 547b80 L50')
                    if index==232:
                        event['next_dispatch']=driver.command('db 4144d4 L1b')+driver.command('dd 4144b8 L7')
                        event['dispatch_end']=driver.command('u 4142d0 L90')
                        event['opcode4_length']=driver.command('u poi(401334) L2')
                        event['opcode29_length']=driver.command('u poi(401398) L2')
                        event['other_legal_lengths']={str(op):driver.command(f'u poi({0x401324+op*4:x}) L2') for op in (5,6,10,30)}
                    driver.command(f'bc {index}')
                    continue
                if index in (225,226,227):
                    event['event_type']={225:'POST_SEED_WRAPPER_RETURN',226:'POST_SEED_CALLER',227:'POST_SEED_READINESS'}[index]
                    event['registers']=driver.command('r')
                    event['code']=driver.command('u @eip L60')
                    event['stack_slots']=driver.command('dd @esp L10')
                    driver.command(f'bc {index}')
                    if index==225 and 0x400000<=event['ret']<0x707000:
                        driver.command(f'bp226 {event["ret"]:x}')
                    if index==227:
                        event['direct_caller_code']=driver.command(f'ub {event["ret"]:x} L10')+driver.command(f'u {event["ret"]:x} L60')
                        event['session_state']=driver.command('.printf "POST_WAIT session=%p enabled=%x accumulated=%x flags0=%x flags4=%x flags8=%x flagsc=%x\\n", @esi, by(@esi+2cb8), dwo(@esi+2cc0), dwo(@ecx), dwo(@ecx+4), dwo(@ecx+8), dwo(@ecx+c)')
                        event['connection_consumer']=driver.command('u 413e95 L40')
                        event['dispatch_tail']=driver.command('u 413585 L50')
                        event['length_lookup']=driver.command('u 401000 L50')
                        event['immediate_wait_consumer']=driver.command('u 4131c0 L90')
                        event['candidate_01']=driver.command('.printf "CANDIDATE_01 expected=%x length_target=%p\\n", by(@esi+754), dwo(401328)')+driver.command('u poi(401328) L2')
                        event['payload_accessors']=driver.command('u 413650 L25')
                    continue
                if index in (220,221,222,223,224):
                    event['event_type']={220:'INITIAL_WAIT_ENTERED',221:'INITIAL_HANDLER_ENTERED',222:'INITIAL_SEED_INSTALLED',223:'INITIAL_HANDSHAKE_RETURN',224:'CLIENT_CONNECTION_ROUTINE_RETURN'}[index]
                    event['state']=driver.command('.printf "HELLO_STATE obj=%p flags0=%x flags4=%x flags8=%x flagsc=%x socket=%x\\n", @ecx, dwo(@ecx), dwo(@ecx+4), dwo(@ecx+8), dwo(@ecx+c), dwo(@ecx+2558)') if index==220 else driver.command('r')
                    if index==220:
                        from server_first import RANGES,BASE
                        verified=True
                        for start,end in RANGES:
                            path=self.run/f'hello-code-{start:x}.bin'
                            driver.command(f'.writemem "{path.as_posix()}" {start:x} L{end-start:x}')
                            if not path.exists() or path.read_bytes()!=self.reference_image[start-BASE:end-BASE]:verified=False
                        event['code_verified']=verified
                        if not verified or 'flags8=0 ' not in event['state']:
                            outcome='INITIAL_CONTRACT_PRECONDITION_FAILED';break
                        self.sink.hello_gate.set()
                    if index==222:event['installed_seed']=driver.command('db @esi+2420 L10')
                    if index==223:
                        event['post_state']=driver.command('.printf "HELLO_POST flags0=%x flags4=%x flags8=%x flagsc=%x\\n", dwo(@ecx), dwo(@ecx+4), dwo(@ecx+8), dwo(@ecx+c)')
                    driver.command(f'bc {index}')
                    continue
                if index==203 and warning:
                    matched=(event['pid']==warning['pid'] and event['tid']==warning['tid'] and
                        event['pc']==warning['ret'] and event['sp']==warning['sp']+20 and event['eax']==1)
                    if getattr(self, 'owner_ui', False):
                        ui = {'closed': matched, 'source': 'MATCHED_MESSAGEBOX_RETURN',
                              'input_origin': 'NOT_INSTRUMENTED'}
                    else:
                        self.dialog.wait(timeout=5)
                        ui=json.loads((self.run/'native-dialog-result.json').read_text(encoding='utf-8'))
                    event.update(event_type='MEMORY_WARNING_RETURN',matched=matched,ui=ui)
                    if not matched or not ui.get('closed'):
                        outcome='MEMORY_WARNING_ACK_FAILED';break
                    event['step']=driver.command('t')
                    event['post_registers']=driver.command('r')
                    event['event_type']='POST_WARNING_EXECUTION'
                    result['post_warning_outcome']='STARTUP_CONTINUES'
                    continue
                if index in SITES:
                    event['event_type']=SITES[index][1]
                    if index==6 and getattr(self,'taiwan_resource_locale',False):
                        from pagefile_capacity_compat import memory
                        expected=bytes.fromhex('66833dd8df590004751066833ddadf5900027506b801000000c333c0c3')
                        if memory(driver,0x531c10,len(expected))!=expected:
                            raise ValueError('Unqualified native language selector; no locale write')
                        original=memory(driver,0x59dfd8,4)
                        event['resource_locale']=dict(before_hex=original.hex(),
                            language_import=driver.command('ln poi(570394)'),
                            scope='PROCESS_LOCAL_RESOURCE_LANGUAGE_OVERRIDE_NOT_OS_LOCALE_OR_NATIVE_DEFAULT')
                        if original not in (bytes.fromhex('04000200'),bytes.fromhex('04000100')):
                            raise ValueError('Unexpected source language; no locale write')
                        driver.command('ew 59dfd8 4 1')
                        event['resource_locale']['after_hex']=memory(driver,0x59dfd8,4).hex()
                        if event['resource_locale']['after_hex']!='04000100':
                            raise ValueError('Process-local resource language write failed')
                        result['resource_locale_override']=event['resource_locale']
                    if index in (10,11):
                        event['before_store']=self.snapshot(driver,event['event_type'])
                        driver.command('t');event['after_store']=self.snapshot(driver,'AFTER_STORE')
                        driver.command(f'bc {index}')
                    if index==7:event['path']=driver.command('da poi(@esp+4) L100')
                    if index==12:
                        event['bytes']=driver.command('db poi(5707bc) L8')
                        event['branch_step']=driver.command('t');event['after_branch']=driver.command('r')
                    if index==14:event['final_table']=self.snapshot(driver,'STRING_LOADER_RETURN')
                    if index==13:outcome='OLD_COMPAT_FAILURE';break
                    continue
                if index in returns:
                    pending=returns.pop(index)
                    api=pending['api'];matched=(event['pid']==pending['pid'] and event['tid']==pending['tid'] and
                        event['pc']==pending['ret'] and event['sp']==pending['sp']+4*(COUNTS[api]+1))
                    event.update(event_type='API_RETURN',api=api,matched=matched,entry=pending['sequence'])
                    event.update(caller_rva=pending.get('caller_rva'),return_address=pending['ret'],arguments=pending.get('arguments'))
                    if not matched:outcome='RETURN_CONTEXT_MISMATCH';break
                    if api=='send' and event['pc']==0x412506 and 4<=event['eax']<=258 and event['eax']==pending['a2']:
                        # This exact wrapper retains the codec in ESI until its following pop.
                        evidence=self.run/'crypto-private'
                        evidence.mkdir(exist_ok=True)
                        base=evidence/f'packet-{sequence:04}'
                        decoded=driver.command(f'!God2Probe.packet {pending["a1"]:x} 0n{event["eax"]} @esi "{base.as_posix()}"')
                        lines=[line.split('GOD2_PACKET ',1)[1] for line in decoded.splitlines() if 'GOD2_PACKET ' in line]
                        if lines:
                            event['packet_decode']=json.loads(lines[-1])
                            if getattr(self,'crypto_observer',None):
                                self.crypto_observer.correlate_tx(event,event['packet_decode'])
                            write_json(self.run/f'packet-decode-{sequence:04}.json',event['packet_decode'])
                            if getattr(self,'observe_ui_npc_buttons',False) and event['packet_decode'].get('opcode') in (0x37,0x85,0x86):
                                observed=result.setdefault('ui_npc_physical_packets',[])
                                observed.append(dict(sequence=sequence,opcode=event['packet_decode']['opcode'],
                                    plain_frame_hex=event['packet_decode'].get('plain_frame_hex'),
                                    client_plaintext_match=event['packet_decode'].get('client_plaintext_match')))
                                write_json(self.run/f'ui-npc-physical-{sequence:04}.json',observed[-1])
                                if (getattr(self,'ui_npc_stop',None)=='reopen' and
                                        observed[-1]['opcode']==0x37 and 'ui_npc_final_packet' in result):
                                    result['ui_npc_reopen_request']=observed[-1]
                                    write_json(self.run/'ui-npc-reopen-request.json',observed[-1])
                            from recovered_packet_pipeline import record_packet
                            event['packet_evidence']=record_packet(self.run,sequence,event['packet_decode'],
                                direction='C2S',socket=pending['a0'],caller_rva=pending.get('caller_rva'))
                            if getattr(self,'ui_npc_dialogue',False) and 'ui_npc_dialogue_open' in result:
                                expected={'cancel':0x86,'confirm':0x85,'reopen':0x85}.get(getattr(self,'ui_npc_stop',None))
                                if event['packet_decode'].get('opcode')==expected and 'ui_npc_final_packet' not in result:
                                    result['ui_npc_final_packet']=dict(sequence=sequence,opcode=expected,
                                        plain_frame_hex=event['packet_decode'].get('plain_frame_hex'),
                                        packet_evidence=event['packet_evidence'])
                                    if getattr(self,'ui_npc_stop',None) in ('confirm','cancel'):
                                        self.ui_npc_follow_until=time.monotonic()+3
                                        self.ui_npc_follow_opcode=expected
                                    elif expected==0x85:
                                        pass
                            if getattr(self,'observe_quest_transport',False) and 'quest_confirm_return' in result:
                                report=event['packet_decode']
                                if report.get('decoded') is True:
                                    plain=Path(str(base)+'.plain.bin').read_bytes()
                                    queued=bytes.fromhex(result['quest_confirm_return']['queued_hex'])
                                    if queued and plain[2:-1].startswith(queued):
                                        result['quest_confirm_transport']=dict(sequence=sequence,
                                            socket=pending['a0'],wire_len=event['eax'],
                                            logical_hex=plain[2:-1].hex(),
                                            packet_evidence=event['packet_evidence'],
                                            scope='SEND_RETURN_NOT_SERVER_AUTHORIZATION')
                    if getattr(self,'gate',None) and self.gate.active:
                        if self.gate.network_return(event,pending,driver):
                            outcome='POST_GATE_EVENT';break
                    if api=='select':
                        select_samples+=1
                        waits=result.setdefault('observed_receive_waits',{})
                        if pending['caller_rva'] not in waits and len(waits)<4:
                            waits[pending['caller_rva']]={'caller_rva':pending['caller_rva'],
                                'before':driver.command(f'ub {pending["ret"]:x} L10'),
                                'after':driver.command(f'u {pending["ret"]:x} L40'),
                                'stack':driver.command('k')}
                        if select_samples==8 and not getattr(getattr(self,'gate',None),'preserve_select_coverage',False):
                            driver.command(f'bc {100+APIS.index("select")}')
                            result['select_observation']='First 8 entry/return pairs captured; polling breakpoint removed, recv remains armed'
                    if api=='WSAStartup' and event['eax']==0:
                        result['post_warning_outcome']='WINSOCK_REACHED'
                        result['pre_network_startup']='CLEARED'
                        if self.enter_game and not self.enter_game_armed:
                            self.enter_game_armed=True
                            def enter_menu():
                                from window_snapshot import enter_game
                                action=enter_game(driver.client_pid,self.run,HOME/'artifacts/runs/network-strike-03/window-01.png')
                                self.events.append(action)
                                write_json(self.run/'enter-game-action.json',action)
                                if action.get('sent') and self.test_login:
                                    def login_menu():
                                        from window_snapshot import submit_test_login
                                        action=submit_test_login(driver.client_pid,self.run,HOME/'artifacts/runs/network-strike-enter-02/window-1789764996417130600-01.png',getattr(self,'lab_case',None))
                                        self.events.append(action)
                                        write_json(self.run/'test-login-action.json',action)
                                    driver.idle_action=login_menu;driver.idle_action_at=time.monotonic()+2
                            driver.idle_action=enter_menu;driver.idle_action_at=time.monotonic()+3
                    if api=='WSAGetLastError':event['wsa_error']=event['eax']
                    if api in CONNECT_APIS and event['eax']!=0:outcome='CONNECT_FAILED';break
                    if api=='recv' and 0<event['eax']<=min(pending['a2'],4096):
                        path=self.run/'s2c'/f'recv-{sequence:04}.bin'
                        event['capture']=driver.command(f'.writemem "{path.as_posix()}" {pending["a1"]:x} L{event["eax"]:x}')
                        if self.ceiling=='FIRST_RX':outcome='MILESTONE_CEILING';break
                    if api=='send' and 0<event['eax']<=pending['a2'] and pending.get('buffer_file'):
                        source=self.run/pending['buffer_file']
                        if source.exists():
                            target=self.run/'c2s'/f'REAL_C2S_{sequence:04}.bin';target.write_bytes(source.read_bytes()[:event['eax']]);event['accepted_buffer']=str(target.relative_to(self.run))
                        if getattr(self,'c2s_strike',False) and event['pc']==0x412506:
                            driver.command('bp232 410d20')
                        if self.network_strike and event['pc']==0x410f00 and event['eax']==19:
                            snapshot={'name':'POST_SEED_STATE_0','sequence':sequence,
                                'registers':driver.command('r'),
                                'fields':driver.command('.printf "POST_SEED obj=%p flags0=%x flags4=%x flags8=%x flagsc=%x rx_length=%x rx_cursor=%x received=%x wire_length=%x feedback=%x socket=%x\\n", @esi, dwo(@esi), dwo(@esi+4), dwo(@esi+8), dwo(@esi+c), dwo(@esi+1810), dwo(@esi+1814), dwo(@esi+2418), dwo(@esi+241c), by(@esi+2556), dwo(@esi+2558)'),
                                'seed':driver.command('db @esi+2420 L10'),
                                'tx':driver.command('db @esi+10 L13'),
                                'next_instructions':driver.command('u @eip L18')}
                            seed_number = result.get('seed_snapshot_count', 0)
                            result['seed_snapshot_count'] = seed_number + 1
                            snapshot['name'] = f'POST_SEED_STATE_{seed_number}'
                            write_json(self.run/f'POST_SEED_STATE_{seed_number}.json',snapshot)
                            if seed_number == 0:
                                driver.command('bp225 411ea5')
                                driver.command('bp227 410d20')
                        if self.ceiling=='FIRST_TX':outcome='MILESTONE_CEILING';break
                    pending=None;continue
                if index is not None and 100<=index<100+len(APIS):
                    api=APIS[index-100];event.update(event_type='API_ENTRY',api=api,caller_rva=hex(event['ret']-0x400000) if 0x400000<=event['ret']<0x707000 else None)
                    event.update(caller_va=event['ret'],return_address=event['ret'],caller_address_kind='return_address',
                        arguments={f'a{i}':event[f'a{i}'] for i in range(min(COUNTS[api],4))})
                    if COUNTS[api]>4:event['extra_arguments_raw']=driver.command(f'dd @esp+14 L{COUNTS[api]-4:x}')
                    if api in SOCKET_APIS:event.update(af=event['a0'],socket_type=event['a1'],protocol=event['a2'])
                    if api in CONNECT_APIS:
                        event['socket']=event['a0']
                        if 0<event['a2']<=128:
                            raw_path=self.run/'network'/f'sockaddr-{sequence:06}.bin'
                            event['sockaddr_capture']=driver.command(f'.writemem "{raw_path.as_posix()}" {event["a1"]:x} L{event["a2"]:x}')
                        marker=driver.command(f'.printf "APEX_DEST af=%x port=%x ip=%x\\n", wo({event["a1"]:x}), wo({event["a1"]+2:x}), dwo({event["a1"]+4:x})')
                        event['sockaddr']=marker
                        match=re.search(r'APEX_DEST af=([0-9a-f]+) port=([0-9a-f]+) ip=([0-9a-f]+)',marker)
                        if not match or int(match[1],16)!=2 or int(match[3],16)!=0x0100007f:
                            outcome='NON_LOOPBACK_DESTINATION_REFUSED';break
                        event['destination']={'ip':'127.0.0.1','port':socket.ntohs(int(match[2],16))}
                        endpoint_number = result.get('endpoint_count', 0) + 1
                        result['endpoint_count'] = endpoint_number
                        write_json(self.run/f'network/RUNTIME_SERVER_ENDPOINT_{endpoint_number:04}.json',event)
                        if getattr(self,'gate',None) and self.gate.active:
                            if hasattr(self.gate,'network_entry') and self.gate.network_entry(event,driver):
                                outcome='POST_GATE_EVENT';break
                            if not hasattr(self.gate,'network_entry'):
                                self.gate.capture('NEW_CONNECT',event)
                                outcome='POST_GATE_EVENT';break
                        if self.sink:
                            allowed_ports = self.sink.allowed_ports if isinstance(self.sink, (CppSeedServer,SharedCppServer)) and self.sink.process.poll() is None else {2592}
                            if not self.network_strike or event['destination']['port'] not in allowed_ports:
                                outcome='SECOND_CONNECT_REQUIRES_REVIEW';break
                        else:self.sink=Sink(event['destination']['port'],self.run)
                    if api=='send' and 0<event['a2']<=4096:
                        path=self.run/'c2s'/f'attempt-{sequence:04}.bin';event['buffer_file']=str(path.relative_to(self.run))
                        event['capture']=driver.command(f'.writemem "{path.as_posix()}" {event["a1"]:x} L{event["a2"]:x}')
                    gate=getattr(self,'gate',None)
                    if gate and gate.active and hasattr(gate,'network_entry') and api not in CONNECT_APIS:
                        if gate.network_entry(event,driver):
                            outcome='POST_GATE_EVENT';break
                    if api in ('WSASend','WSARecv'):
                        if getattr(self,'gate',None) and self.gate.active:
                            self.gate.capture('SCATTER_GATHER_REQUIRES_COMPLETION_OBSERVER',event)
                        outcome='SCATTER_GATHER_COMPLETION_NEXT_BLOCKER';break
                    if event['caller_rva'] is None:
                        ancestors=[p for p in returns.values() if p['pid']==event['pid'] and p['tid']==event['tid'] and p['sp']>event['sp'] and p.get('caller_rva')]
                        if ancestors:
                            ancestor=min(ancestors,key=lambda p:p['sp'])
                            event['caller_rva']=ancestor['caller_rva'];event['caller_address_kind']='observed_client_ancestor_return'
                            event['client_ancestor_entry']=ancestor['sequence']
                    slot=next((slot for slot in range(300,364) if slot not in returns),None)
                    if slot is None:outcome='RETURN_OBSERVATION_LIMIT';break
                    returns[slot]=event;driver.command(f'bp{slot} /1 {event["ret"]:x}');continue
                event['event_type']='NEXT_BLOCKER'
                event['registers']=driver.command('r');event['stack']=driver.command('k')
                if index in (201,202):
                    event['message']=driver.command(('du ' if index==202 else 'da ')+f'{event["a1"]:x} L100')
                    path=self.run/'message-buffer.bin'
                    event['message_capture']=driver.command(f'.writemem "{path.as_posix()}" {event["a1"]:x} L200')
                    if path.exists():
                        buffer=path.read_bytes()
                        event['message_text']=buffer.decode('utf-16le',errors='replace').split('\0',1)[0] if index==202 else buffer.split(b'\0',1)[0].decode('cp950',errors='replace')
                    event['known_memory_warning']=event.get('message_text')==MEMORY_WARNING
                    event['caller_rva']=hex(event['ret']-0x400000) if 0x400000<=event['ret']<0x707000 else None
                    if event['a2']:
                        title_path=self.run/f'message-title-{sequence:04}.bin'
                        event['title_capture']=driver.command(f'.writemem "{title_path.as_posix()}" {event["a2"]:x} L100')
                        if title_path.exists():
                            title=title_path.read_bytes()
                            event['message_title']=title.decode('utf-16le',errors='replace').split('\0',1)[0] if index==202 else title.split(b'\0',1)[0].decode('cp950',errors='replace')
                    if event['known_memory_warning']:
                        event['ui_action']='NOT_ATTEMPTED'
                        event['continuation_status']='REQUIRES_VERIFIED_LOCAL_UI'
                        if getattr(self, 'zero_ui_prefix', False):
                            if event.get('ret') == 0x402e0d:
                                # Wrapper: sub esp,200h; four API args plus return PC.
                                event['warning_source'] = {
                                    'wrapper': driver.command('u 402dc0 402e1c'),
                                    'caller_stack': driver.command('dd @esp+214 L4'),
                                    'caller_before': driver.command('ub poi(@esp+214) L30'),
                                    'immediate_source': driver.command('u 40f08b 40f19b'),
                                    'query_identity': driver.command('ln poi(57040c)'),
                                    'caller_values': driver.command('dd @esp+224 L14'),
                                }
                            event['continuation_status']='ACTION_BINDING_INCOMPLETE'
                            outcome='PREFIX_WARNING_ACTION_BINDING_INCOMPLETE';break
                        if warning:
                            outcome='SAME_WARNING_LOOPS';break
                        if self.mode=='MODE_COMPAT' and event.get('message_title') is not None and event['a3']==0:
                            warning=event
                            if getattr(self, 'owner_ui', False):
                                event['ui_action'] = 'WAIT_OWNER_NORMAL_UI'
                                driver.command(f'bp203 /1 {event["ret"]:x}')
                                print('OWNER_UI: dismiss the visible game memory warning, then use normal login/server selection.',
                                      file=sys.__stdout__, flush=True)
                                continue
                            request=self.run/'native-dialog-request.json'
                            write_json(request,{'pid':event['pid'],'tid':event['tid'],
                                'title':event['message_title'],'text':MEMORY_WARNING,
                                'caller_rva':event['caller_rva'],'run_id':name})
                            self.dialog=subprocess.Popen([str(HOME/'build-strike-lab/Release/god2-strike-runner.exe'),
                                '--native-dialog',str(request),str(self.run/'native-dialog-result.json')],
                                creationflags=subprocess.CREATE_NO_WINDOW)
                            event['ui_action']='NATIVE_CONTROLLER_STARTED'
                            driver.command(f'bp203 /1 {event["ret"]:x}')
                            continue
                outcome='EXIT_PROCESS' if index==200 else 'MESSAGE_BOX' if index in (201,202) else 'UNEXPECTED_STOP'
                if outcome=='UNEXPECTED_STOP' and event.get('pc')==0x459ed2:
                    from pagefile_capacity_compat import memory,number
                    owner=number(driver,'@edi')
                    result['world_table_fault']={
                        'pc':event['pc'],'owner':owner,'table_cursor':number(driver,'@ebx'),
                        'count':int.from_bytes(memory(driver,owner+0xd2aba,2),'little',signed=True),
                        'table':int.from_bytes(memory(driver,owner+0xd2abc,4),'little'),
                        'stack':driver.command('k 12'),
                        'instruction':driver.command('u 459e70 459ee4'),
                        'scope':'READ_ONLY_FAILURE_DIAGNOSTIC_NO_EXCEPTION_SUPPRESSION'}
                break
            result['result']=outcome
        finally:
            if getattr(self,'pagefile_adapter',None):
                try:self.pagefile_adapter.restore(driver)
                except Exception as error:result['pagefile_restore_error']=repr(error)
            if getattr(self,'gate',None):self.gate.finish(outcome)
            if self.dialog:
                try:self.dialog.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.dialog.terminate();self.dialog.wait(timeout=5)
            if self.sink:self.sink.close()
            result['milestones']=milestones(self.events)
            state=progression(self.events)
            result['furthest_milestone']=state['state']
            successes=[e for e in self.events if e.get('event_type')=='API_RETURN' and e.get('matched') and
                       ((e.get('api') in SOCKET_APIS and e.get('eax')!=0xffffffff) or
                        (e.get('api') in ('WSAStartup',*CONNECT_APIS) and e.get('eax')==0) or
                        (e.get('api') in ('send','recv') and 0<e.get('eax',0)<0x80000000))]
            result['last_successful_network_event']=successes[-1] if successes else None
            result['last_packet_artifact']=next((e.get('accepted_buffer') for e in reversed(self.events) if e.get('accepted_buffer')),None)
            result['next_blocker']='NO_CLIENT_BYTES_AFTER_LOOPBACK_ACCEPT' if state['CONNECTED'] and not state['FIRST_TX'] else result.get('result')
            result['regression_assertions']={key:state[key] for key in ('GRAPHICS_RETURNED','STRING_TABLE_READY','MEMORY_WARNING_PASSED')}
            result['regression_assertions']['WSASTARTUP_SUCCEEDED']=any(e.get('event_type')=='API_RETURN' and e.get('api')=='WSAStartup' and e.get('matched') and e.get('eax')==0 for e in self.events)
            if self.mode=='MODE_COMPAT' and not all(result['regression_assertions'].values()):
                result['prior_result']=result.get('result');result['result']='REGRESSION'
            result['compatibility_acceptance']='ACCEPTED' if all(result['milestones'][k] for k in ('GRAPHICS_RETURNED','TABLE_ENUMERATION_REACHED','STRING_TABLE_INITIALIZED')) else 'INTERVENTION_REJECTED' if self.mode=='MODE_COMPAT' else 'OBSERVE_ONLY'
            try:result['modules']=driver.command('lm')
            except Exception as error:result['module_error']=repr(error)
            if self.installed:
                try:result['restoration']=driver.command('!God2Compat.restore')
                except Exception as error:result['restore_error']=repr(error)
            self.result=result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tool',choices=('God2CompatHost','god2-strike-runner'))
    parser.add_argument('--mode',choices=('MODE_OBSERVE','MODE_COMPAT'))
    parser.add_argument('--ui-gate-check',action='store_true',help='Dry rendezvous prerequisite check; never launches the client')
    parser.add_argument('--ui-gate-rendezvous',action='store_true',help='Fail-closed rendezvous entry; requires a qualified live observer adapter')
    parser.add_argument('--ui-gate-max-wait',type=float,help='Optional external UI wait limit; default is unbounded')
    parser.add_argument('--post-server-select-follow',action='store_true',help='Opt-in: consume frozen six-byte C2S and observe first following API event')
    parser.add_argument('--legacy-character-list-candidate',action='store_true',
                        help='Explicit unverified loopback 07 response; requires --zero-ui-prefix and --server-list')
    parser.add_argument('--recovered-account-auth',action='store_true',
                        help='Opt in to persistent local accounts and first-login registration; requires character-list candidate mode')
    parser.add_argument('--recovered-character-create',action='store_true',
                        help='Opt in to character profile persistence and candidate list; requires recovered account authentication')
    parser.add_argument('--recovered-dual-connection',action='store_true',
                        help='Advertise independent character listener; requires recovered character persistence')
    parser.add_argument('--recovered-world-entry',action='store_true',
                        help='Opt in to historical 2A candidate and bounded initialization tail; requires dual connection')
    parser.add_argument('--run-id',default='apex-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S'))
    parser.add_argument('--timeout',type=int,default=60)
    parser.add_argument('--enter-game',action='store_true',help='One visual/PID-validated main-menu click')
    parser.add_argument('--owner-ui', action='store_true',
                        help='No automated UI or screenshots; owner operates normal client UI')
    parser.add_argument('--ui-world-movement',action='store_true',
                        help='After verified restored town entry, wait for one external UI movement and saved/native agreement')
    parser.add_argument('--ui-npc-dialogue',action='store_true',
                        help='Passive restored-town physical NPC dialogue path; never inject native game calls')
    parser.add_argument('--ui-npc-stop',choices=('open','page','cancel','confirm','reopen'),default='page',
                        help='Milestone for passive physical NPC dialogue observation')
    parser.add_argument('--observe-ui-npc-buttons',action='store_true',
                        help='Read-only original NPC dialogue button entry/return during passive town UI observation')
    parser.add_argument('--verify-restored-town-position',action='store_true',
                        help='Verify a restored town save in current-client memory without waiting for external input')
    parser.add_argument('--zero-ui-prefix', action='store_true',
                        help='Bounded prefix observation only; stop at an unbound UI action without desktop input')
    parser.add_argument('--warning-input-trace', action='store_true')
    parser.add_argument('--auto-pagefile-capacity', action='store_true')
    parser.add_argument('--test-login',action='store_true',help='One synthetic lab credential submission after --enter-game')
    parser.add_argument('--milestone-ceiling',choices=('NONE','FIRST_TX','FIRST_RX'),default='NONE')
    parser.add_argument('--network-strike',action='store_true',help='Prelisten on confirmed loopback port and send verified initial seed frame')
    parser.add_argument('--cpp-server',action='store_true',help='Use existing C++ server in recovered seed mode')
    parser.add_argument('--post-seed',action='store_true',help='Send the recovered opcode-1 post-seed contract from C++')
    parser.add_argument('--c2s-strike',action='store_true',help='Bounded C2S_0002 builder and next-wait capture')
    parser.add_argument('--lab-case',choices=('A','B'),help='Fixed local credentials, only account differs between A and B')
    parser.add_argument('--lab-peer',type=int,choices=(0,1),default=0,
                        help='Fixed public native-login identity;1 uses a distinct test account and character')
    parser.add_argument('--shared-server-manifest',type=Path,
                        help='Attach a verified owned loopback visibility server; never terminate it on exit')
    parser.add_argument('--s2c0003',action='store_true',help='Parse C2S_0002 and send the bounded opcode-29 response')
    parser.add_argument('--login-terminal',action='store_true',help='Send the bounded terminal result after opcode29')
    parser.add_argument('--server-list-probe',action='store_true',help='Capture only the empty-server-list consumer')
    parser.add_argument('--server-list',action='store_true',help='Enable one existing loopback directory entry before terminal result')
    parser.add_argument('--recover-crypto',action='store_true',help='Offline session-global constrained crypto recovery; never launches the client')
    parser.add_argument('--crypto-manifest',type=Path)
    parser.add_argument('--crypto-output',type=Path)
    parser.add_argument('--observe-login-entry', action='store_true',
                        help='Stop at the application-owned native login loop; requires zero-UI mode')
    parser.add_argument('--probe-login-command', action='store_true',
                        help='After observed native login initialization, call menu command3/flags1 and stop')
    parser.add_argument('--probe-login-panel', action='store_true',
                        help='Resume original loop after menu command to verify native login panel initialization')
    parser.add_argument('--probe-login-submit', action='store_true',
                        help='Submit public lab-case A through native controls and continue existing loopback capture')
    parser.add_argument('--probe-server-confirm', action='store_true',
                        help='After native list initialization, confirm its existing selection through original handler')
    parser.add_argument('--observe-character-create', action='store_true',
                        help='Continue an empty native character list to original creation panel initialization')
    parser.add_argument('--probe-character-create', action='store_true',
                        help='Submit public diagnostic character through native creation controls to own server')
    parser.add_argument('--isolated-database', action='store_true',
                        help='Use a fresh per-run diagnostic SQLite database, preserving existing accounts')
    parser.add_argument('--observe-created-refresh', action='store_true',
                        help='Continue native18 reply to character list refresh and selection initialization')
    parser.add_argument('--probe-character-select',action='store_true',
                        help='Confirm current native character selection and observe login-loop return')
    parser.add_argument('--observe-world-entry',action='store_true',
                        help='Continue successful native selection through original world initialization')
    parser.add_argument('--observe-world-loop',action='store_true',
                        help='Observe the original world loop after successful initialization')
    parser.add_argument('--remote-actor-probe-language',type=int,choices=(0,1),default=None,
                        help='CUSTOM-0026 isolated remote actor socket lifecycle, explicit native language bit')
    parser.add_argument('--movement-lab',action='store_true',
                        help='Use existing indoor movement config only in an isolated world-entry run')
    parser.add_argument('--town-entry-lab',action='store_true',
                        help='Fresh isolated town entry; no indoor movement probe or gameplay diagnostics')
    parser.add_argument('--town-fresh-spawn',action='store_true',
                        help='Isolated unsaved new-character town spawn at source-agreement position')
    parser.add_argument('--town-spawn-guides',action='store_true',
                        help='CUSTOM-0020 isolated town NPC spawn; requires restored town and read-only observer')
    parser.add_argument('--observe-town-npc-render',action='store_true',
                        help='Read fixed native actor render handles and projection for observed town NPCs')
    parser.add_argument('--town-guide-target',type=int,choices=(1606,1607),default=1606,
                        help='Native town NPC request target for isolated conversation probe')
    parser.add_argument('--town-map-probe',action='store_true',help='Isolated CUSTOM-0023 map response candidate, no consumption')
    parser.add_argument('--town-scene-probe',action='store_true',help='Isolated CUSTOM-0024 same-position scene61 receiver probe, not map-item gameplay')
    parser.add_argument('--town-scene-relocate',action='store_true',help='CUSTOM-0024 durable isolated town transfer110,70 to111,70')
    parser.add_argument('--town-scene-follow-move',action='store_true',help='After qualified scene receipt, native walk111,70 to112,70')
    parser.add_argument('--town-scene-indoor-probe',action='store_true',help='Read-only-save transport probe from town to qualified indoor2/15; no destination movement')
    parser.add_argument('--town-scene-indoor-transfer',action='store_true',help='Isolated durable town-to-indoor transfer; requires indoor probe and source-consensus navigation')
    parser.add_argument('--taiwan-resource-locale',action='store_true',help='Explicit process-local Taiwan resource selector override; does not change OS locale or executable')
    parser.add_argument('--town-scene-return-probe',action='store_true',help='Read-only-save indoor-to-town receiver qualification')
    parser.add_argument('--town-scene-return-commit',action='store_true',help='Persist qualified indoor return and observe town NPC projection')
    parser.add_argument('--town-return-after-battle',action='store_true',help='After isolated quest battle, invoke native map request and verify durable town return')
    parser.add_argument('--town-door-after-battle',action='store_true',help='After isolated quest battle, walk native indoor path to CUSTOM-0025 return door')
    parser.add_argument('--town-door-reconnect',action='store_true',help='Restore qualified post-battle doorway town save in a fresh client')
    parser.add_argument('--indoor-door-probe',action='store_true',help='Walk restored indoor18,12 to native HMD pair cells16,19 and16,20; no transfer response')
    parser.add_argument('--town-door-probe',action='store_true',help='Walk restored town to source grocery pair3 at86,71; no transfer response')
    parser.add_argument('--town-special-entry-probe',action='store_true',help='After grocery approach, observe native call toward special cell86,70 without relaxing server policy')
    parser.add_argument('--town-auto-door',action='store_true',help='Enable isolated CUSTOM-0025 doorway policy and verify original indoor grid/context after approach')
    parser.add_argument('--town-auto-door-roundtrips',type=int,choices=(0,1,2),default=0,help='After automatic entry, qualify one or two same-connection roundtrips')
    parser.add_argument('--town-quest-progress',action='store_true',
                        help='CUSTOM-0021 isolated acceptance persistence and native journal probe')
    parser.add_argument('--town-quest-reward-chain',action='store_true',help='Complete all three diagnostic quest stages on one connection')
    parser.add_argument('--town-quest-chain',action='store_true',
                        help='Qualify two town quest confirmations on one native connection')
    parser.add_argument('--town-east-path',action='store_true',
                        help='Probe consecutive eastward town steps instead of adjacent round trips')
    parser.add_argument('--town-detour-path',action='store_true',help='Source-qualified cardinal test route to x100')
    parser.add_argument('--town-consensus-path',action='store_true',help='CUSTOM-0019 isolated path beyond initial window to x110')
    parser.add_argument('--restore-town-database',type=Path,help='Read-only clone of qualified town checkpoint into fresh run')
    parser.add_argument('--town-battle-after-quest',action='store_true',
                        help='CUSTOM-0028: isolated completed-quest indoor save enters one durable skill battle')
    parser.add_argument('--town-completed-quest-restore',action='store_true',
                        help='Observe completed indoor quest save without replaying conversation or battle')
    parser.add_argument('--town-post-battle-position-restore',action='store_true',
                        help='Cold-restore the qualified stage-3 battle and three-step indoor19,12 save')
    parser.add_argument('--observe-quest-text-table',action='store_true')
    parser.add_argument('--diagnostic-quest-dialogue',action='store_true')
    parser.add_argument('--probe-quest-confirm',action='store_true')
    parser.add_argument('--probe-quest-close',action='store_true')
    parser.add_argument('--probe-npc-reopen',action='store_true')
    parser.add_argument('--probe-town-guide-resource',action='store_true')
    parser.add_argument('--observe-quest-transport',action='store_true')
    parser.add_argument('--observe-npc-state',action='store_true')
    parser.add_argument('--diagnostic-quest-npc',action='store_true')
    parser.add_argument('--probe-npc-request',action='store_true')
    parser.add_argument('--complete-npc-conversation',action='store_true')
    parser.add_argument('--observe-world-frames',action='store_true',
                        help='Observe three original presentation/frame returns; no visual acceptance claim')
    parser.add_argument('--probe-movement-step',action='store_true',
                        help='Guarded diagnostic original adjacent step on the isolated movement lab')
    parser.add_argument('--movement-steps',type=int,choices=range(1,101),default=1,
                        help='Bounded alternating native steps, each gated on its real ACK')
    parser.add_argument('--restore-movement-database',type=Path,
                        help='Read-only backup of verified three-step isolated DB for fresh-client restore')
    parser.add_argument('--terminal-disconnect-restore',action='store_true',
                        help='Allow one movement after a qualified committed-terminal/no-position restore')
    parser.add_argument('--diagnostic-encounter-limit',type=int,choices=(1,2),default=1,help='CUSTOM-0014: bounded encounter count')
    parser.add_argument('--observe-socket-defeat',action='store_true',help='Observe isolated HP4 lethal retaliation; no revival or native formula claim')
    parser.add_argument('--diagnostic-battle-after-movement',action='store_true',help='CUSTOM-0014: one committed movement before diagnostic entry')
    parser.add_argument('--diagnostic-battle-transition',action='store_true',
                        help='Isolated socket-fed zero-context battle initializer only, no gameplay binding')
    parser.add_argument('--observe-socket-battle-vitals',action='store_true',
                        help='Continue the diagnostic transition to original socket-fed 88 receiver return')
    parser.add_argument('--diagnostic-battle-participants',action='store_true',
                        help='Deferred isolated participants, synthetic vitals and first grant')
    parser.add_argument('--probe-socket-battle-action',action='store_true',
                        help='Invoke original basic attack after socket participant grant, diagnostic only')
    parser.add_argument('--observe-socket-retaliation',action='store_true',
                        help='Observe both diagnostic damage and retaliation HP consumers')
    parser.add_argument('--diagnostic-battle-rounds',type=int,choices=(1,2,3),default=1,
                        help='Bounded custom diagnostic rounds, not production turn policy')
    parser.add_argument('--diagnostic-battle-player-appearance',action='store_true',
                        help='Isolated historical appearance before native player identity; not production')
    parser.add_argument('--diagnostic-battle-animations',action='store_true',
                        help='Isolated native83 basic animation candidate; requires player appearance')
    parser.add_argument('--diagnostic-battle-terminal',action='store_true',
                        help='Isolated lethal test action and zero-award native outcome observation')
    parser.add_argument('--observe-socket-outcome-panel',action='store_true',
                        help='Observe original outcome-panel function entry and return, not visual acceptance')
    parser.add_argument('--observe-socket-battle-exit',action='store_true',
                        help='Observe natural battle cleanup and world-loop re-entry without input or flag writes')
    parser.add_argument('--probe-post-battle-movement',action='store_true',
                        help='After natural battle exit, invoke three original path requests and observe ACK/completion')
    parser.add_argument('--diagnostic-battle-hotbar',action='store_true',
                        help='Isolated CUSTOM-0012 hotbar file for native loader')
    parser.add_argument('--probe-socket-skill-select',action='store_true',
                        help='Call original hotbar selection; no skill cast')
    parser.add_argument('--diagnostic-battle-revival',action='store_true',
                        help='CUSTOM-0017 isolated three-actor initialization only, no cast probe')
    parser.add_argument('--probe-socket-skill-command',action='store_true',
                        help='After native selection, queue original skill command for target14')
    parser.add_argument('--diagnostic-battle-skill-settlement',action='store_true',
                        help='Isolated CUSTOM-0012 skill authorization and HP/MP settlement')
    parser.add_argument('--diagnostic-battle-mp-refusal',action='store_true',
                        help='Isolated MP7 refusal of fee8 followed by native basic retry')
    parser.add_argument('--diagnostic-battle-resources',action='store_true',
                        help='Persist CUSTOM-0012 battle HP/MP in the isolated database')
    parser.add_argument('--diagnostic-battle-experience',type=int,default=0,
                        help='Explicit CUSTOM-0012 test award, not native monster EXP')
    parser.add_argument('--diagnostic-role-progress',action='store_true',
                        help='Isolated S2C2B progress2500 sentinel, not a level formula')
    parser.add_argument('--diagnostic-progress-span',type=int,default=0,
                        help='Explicit CUSTOM-0013 test interval; derive progress from saved XP')
    parser.add_argument('--diagnostic-level-snapshot',action='store_true',
                        help='Isolated atomic level snapshot with synthetic 0/span/3span curve; no stat growth')
    parser.add_argument('--stop-after-first-checkpoint',action='store_true',
                        help='Stop isolated level-snapshot run after first skill/retaliation animations; no settlement')
    parser.add_argument('--diagnostic-resume-checkpoint',action='store_true',
                        help='Restore a qualified first or second exchange snapshot in a fresh isolated client session')
    parser.add_argument('--stop-after-second-checkpoint',action='store_true',
                        help='Capture the second completed isolated skill exchange before the final action')
    parser.add_argument('--diagnostic-world-resources',action='store_true',
                        help='Read saved resources once into world through native S2C24')
    parser.add_argument('--diagnostic-world-supply',action='store_true',
                        help='Project pre-seeded isolated slot0; not proof of live item use')
    parser.add_argument('--probe-supply-use',action='store_true',
                        help='Call original3107 use three times on isolated restored supply fixture')
    parser.add_argument('--probe-supply-exhaustion',action='store_true',
                        help='Use one saved3107 then invoke the empty slot again')
    parser.add_argument('--expect-no-world-resources',action='store_true',
                        help='Negative fixture: new character has no resource row; require no resource update')
    parser.add_argument('--diagnostic-battle-skill-seed',action='store_true',
                        help='CUSTOM-0012: isolated explicit GOD row and one learned skill before battle entry')
    args=parser.parse_args()
    if args.probe_supply_exhaustion and not args.probe_supply_use:
        parser.error('Exhaustion requires supply use probe')
    if args.observe_socket_defeat and not (args.diagnostic_battle_resources and args.diagnostic_battle_terminal and
            args.diagnostic_battle_rounds==3 and args.diagnostic_battle_skill_settlement and args.observe_socket_battle_exit and
            args.restore_movement_database and args.isolated_database and args.cpp_server and args.diagnostic_encounter_limit==1 and
            not args.diagnostic_role_progress and not args.diagnostic_level_snapshot and not args.diagnostic_world_supply and
            not args.diagnostic_battle_experience and not args.diagnostic_resume_checkpoint):
        parser.error('Defeat observation requires isolated three-round terminal skill path without awards/progression/supply/resume')
    if args.probe_supply_use and not args.diagnostic_world_supply:
        parser.error('Supply probe requires isolated world supply')
    if args.diagnostic_world_supply and not (args.diagnostic_world_resources and args.restore_movement_database and
            args.isolated_database and args.movement_lab and args.cpp_server):
        parser.error('Supply requires isolated restored world resource fixture without battle')
    if args.diagnostic_world_supply and args.diagnostic_battle_transition and not (
            args.probe_supply_use and args.observe_socket_battle_exit and args.diagnostic_battle_resources and
            args.diagnostic_battle_rounds==3 and args.diagnostic_battle_terminal and args.diagnostic_encounter_limit==1 and
            not args.diagnostic_level_snapshot and not args.diagnostic_resume_checkpoint and not args.probe_supply_exhaustion):
        parser.error('Post-battle supply requires one durable three-round terminal battle and observed exit')
    if args.diagnostic_resume_checkpoint and args.diagnostic_battle_revival and not (
            args.restore_movement_database and args.diagnostic_battle_resources and args.diagnostic_battle_rounds in (1,2)):
        parser.error('Revival restore requires copied durable one or two-round projection')
    if args.diagnostic_resume_checkpoint and not args.diagnostic_battle_revival and not (args.diagnostic_level_snapshot and args.restore_movement_database and
            args.diagnostic_battle_rounds==3 and args.diagnostic_battle_resources and not args.stop_after_first_checkpoint):
        parser.error('Resume requires copied completed-exchange level-snapshot fixture')
    if args.stop_after_second_checkpoint and (args.stop_after_first_checkpoint or args.restore_movement_database or args.diagnostic_resume_checkpoint or args.diagnostic_battle_revival or args.diagnostic_encounter_limit!=1):
        parser.error('Second checkpoint interruption requires a fresh non-revival experiment')
    if (args.stop_after_first_checkpoint or args.stop_after_second_checkpoint) and not (args.diagnostic_level_snapshot and args.diagnostic_battle_rounds==3 and
            args.diagnostic_battle_animations and args.diagnostic_battle_skill_settlement and not args.restore_movement_database):
        parser.error('Checkpoint interruption requires fresh three-round animated level-snapshot experiment')
    if args.expect_no_world_resources and (not args.diagnostic_world_resources or not args.probe_movement_step or
                                           args.restore_movement_database or args.diagnostic_battle_transition):
        parser.error('Missing resource fixture requires new-character movement without restore or battle')
    if args.diagnostic_world_resources and not (args.isolated_database and args.movement_lab and args.cpp_server):
        parser.error('World resources require isolated C++ movement server')
    if not 0<=args.diagnostic_progress_span<=0x7fffffff or (args.diagnostic_progress_span and
            (not args.diagnostic_role_progress or (not args.diagnostic_level_snapshot and args.diagnostic_battle_experience>=args.diagnostic_progress_span))):
        parser.error('Test interval requires role progress below first level transition')
    if args.diagnostic_level_snapshot and not (args.diagnostic_role_progress and args.diagnostic_progress_span and args.diagnostic_battle_player_appearance):
        parser.error('Level snapshot requires fresh player progress experiment with explicit interval')
    if args.diagnostic_role_progress and (not args.diagnostic_battle_experience or (args.restore_movement_database and not args.diagnostic_resume_checkpoint)):
        parser.error('Role progress sentinel requires fresh diagnostic award run')
    if not 0<=args.diagnostic_battle_experience<=0x7fffffff or (args.diagnostic_battle_experience and
            not (args.diagnostic_battle_resources and args.diagnostic_battle_terminal)):
        parser.error('Diagnostic EXP requires persisted terminal battle and signed display range')
    if args.diagnostic_battle_resources and not ((args.diagnostic_battle_skill_settlement or args.diagnostic_battle_revival) and args.isolated_database):
        parser.error('Battle resources require skill settlement and isolated database')
    if args.diagnostic_battle_resources and args.restore_movement_database and args.diagnostic_battle_mp_refusal:
        parser.error('Saved MP42 restore excludes the MP7 refusal fixture')
    if args.diagnostic_battle_mp_refusal and (not args.diagnostic_battle_skill_settlement or not args.diagnostic_battle_animations or args.diagnostic_battle_terminal or args.diagnostic_battle_rounds!=1):
        parser.error('MP refusal requires one animated skill round without terminal')
    if args.diagnostic_battle_hotbar and not (args.diagnostic_battle_skill_seed and args.isolated_database):
        parser.error('Hotbar fixture requires skill seed and isolated database')
    if args.diagnostic_battle_revival and (not (args.cpp_server and args.isolated_database and
            args.diagnostic_battle_skill_seed and args.diagnostic_battle_hotbar and args.diagnostic_battle_animations) or
            args.probe_socket_skill_select or args.probe_socket_battle_action or args.diagnostic_battle_skill_settlement or
            (args.restore_movement_database and not args.diagnostic_resume_checkpoint) or args.diagnostic_world_resources or
            (args.diagnostic_battle_terminal and (not args.diagnostic_resume_checkpoint or not args.diagnostic_battle_resources or args.diagnostic_battle_rounds!=1 or args.diagnostic_battle_experience)) or
            args.diagnostic_battle_rounds>2 or args.diagnostic_encounter_limit!=1 or args.diagnostic_battle_after_movement):
        parser.error('Revival bootstrap requires fresh isolated animated hotbar seed without action probes or world resources')
    if args.probe_socket_skill_select and (not args.diagnostic_battle_hotbar or args.probe_socket_battle_action):
        parser.error('Skill selection requires hotbar fixture and excludes basic action probe')
    if args.probe_socket_skill_command and not args.probe_socket_skill_select:
        parser.error('Skill command requires native skill selection probe')
    if args.diagnostic_battle_skill_settlement and (not args.probe_socket_skill_command or ((args.diagnostic_battle_terminal or args.diagnostic_battle_rounds>1) and not args.diagnostic_battle_animations)):
        parser.error('Skill settlement requires command probe and animations for repeated or terminal rounds')
    if args.diagnostic_battle_skill_seed and not args.diagnostic_battle_player_appearance:
        parser.error('Skill seed diagnostic requires isolated player appearance')
    if args.probe_post_battle_movement and not args.observe_socket_battle_exit:
        parser.error('Post-battle movement requires natural battle exit observation')
    if args.observe_socket_battle_exit and not args.observe_socket_outcome_panel:
        parser.error('Battle exit observation requires outcome panel observation')
    if args.observe_socket_outcome_panel and not args.diagnostic_battle_terminal:
        parser.error('Outcome panel observation requires terminal diagnostic')
    if args.diagnostic_battle_rounds==3 and not (args.diagnostic_battle_terminal and args.diagnostic_battle_skill_settlement and args.diagnostic_battle_animations):
        parser.error('Three rounds require animated terminal skill diagnostic')
    if args.diagnostic_battle_terminal and (not (args.probe_socket_battle_action or args.diagnostic_battle_skill_settlement or (args.diagnostic_battle_revival and args.diagnostic_resume_checkpoint)) or args.observe_socket_retaliation or args.diagnostic_battle_rounds not in (1,3)):
        parser.error('Terminal diagnostic requires one socket action without retaliation observation')
    if args.diagnostic_battle_rounds>1 and not (args.observe_socket_retaliation or args.diagnostic_battle_skill_settlement or args.diagnostic_battle_revival):
        parser.error('Multiple diagnostic rounds require retaliation observation')
    if args.observe_socket_retaliation and not args.probe_socket_battle_action:
        parser.error('Retaliation observation requires socket action probe')
    if args.probe_socket_battle_action and not args.diagnostic_battle_participants:
        parser.error('Socket action requires diagnostic participants')
    if args.diagnostic_battle_player_appearance and not args.diagnostic_battle_participants:
        parser.error('Player appearance diagnostic requires participants')
    if args.diagnostic_battle_animations and not args.diagnostic_battle_player_appearance:
        parser.error('Animation diagnostic requires player appearance')
    if args.diagnostic_battle_participants and not args.observe_socket_battle_vitals:
        parser.error('Diagnostic participants require socket vitals observation')
    if args.observe_socket_battle_vitals and not args.diagnostic_battle_transition:
        parser.error('Socket vitals observation requires diagnostic battle transition')
    if args.diagnostic_battle_after_movement and not (args.diagnostic_battle_transition and args.diagnostic_battle_participants and
            args.probe_movement_step and args.movement_steps==1 and not args.restore_movement_database):
        parser.error('Movement encounter requires one fresh pre-battle movement')
    if args.diagnostic_encounter_limit==2 and not (args.diagnostic_battle_after_movement and args.probe_post_battle_movement and
            args.diagnostic_level_snapshot and args.diagnostic_battle_rounds==3 and args.diagnostic_battle_terminal and
            args.diagnostic_battle_experience==250 and args.diagnostic_progress_span==200 and not args.stop_after_first_checkpoint):
        parser.error('Two encounters require completed movement/three-round level-snapshot fixture')
    if args.diagnostic_battle_transition and not (args.movement_lab and args.observe_world_frames and
            (not args.probe_movement_step or args.diagnostic_battle_after_movement)):
        parser.error('Diagnostic battle transition requires movement lab and world frames without movement probe')
    if args.terminal_disconnect_restore and not (args.restore_movement_database and args.movement_lab and
            args.observe_world_frames and args.probe_character_select and args.probe_movement_step and
            args.movement_steps==1 and args.diagnostic_world_resources and not args.diagnostic_battle_transition):
        parser.error('Terminal disconnect restore requires one saved world movement without battle')
    if args.restore_movement_database and not (args.movement_lab and args.observe_world_frames and args.probe_character_select and
            (not args.probe_movement_step or args.terminal_disconnect_restore)):
        parser.error('Restore requires isolated movement lab, frames and selection, without new movement probes')
    if args.observe_login_entry and not args.zero_ui_prefix:
        parser.error('--observe-login-entry requires --zero-ui-prefix')
    if args.probe_login_command and not args.observe_login_entry:
        parser.error('--probe-login-command requires --observe-login-entry')
    if args.probe_login_panel and not args.probe_login_command:
        parser.error('--probe-login-panel requires --probe-login-command')
    if args.probe_login_submit and not (args.probe_login_panel and args.cpp_server and args.network_strike and args.lab_case == 'A'):
        parser.error('--probe-login-submit requires panel probe and C++ loopback lab-case A')
    if args.lab_peer and not (args.probe_login_submit and args.probe_character_create and args.isolated_database):
        parser.error('--lab-peer1 requires isolated native login and character creation probes')
    if args.shared_server_manifest:
        if not (args.cpp_server and args.isolated_database and args.movement_lab and args.recovered_dual_connection):
            parser.error('Shared server attachment requires isolated C++ dual-connection movement mode')
        shared_document=json.loads(Path(args.shared_server_manifest).read_text())
        allowed_battle={'diagnostic_battle_transition','diagnostic_battle_participants',
            'diagnostic_battle_player_appearance','diagnostic_battle_animations','diagnostic_battle_terminal'}
        if shared_document.get('skill_battle'):
            allowed_battle.update(('diagnostic_battle_skill_seed','diagnostic_battle_hotbar','diagnostic_battle_skill_settlement'))
        if not shared_document.get('observe_battle') or args.lab_peer!=0:allowed_battle=set()
        if (args.remote_actor_probe_language is not None or args.restore_movement_database or
                args.restore_town_database or args.ui_gate_rendezvous or
                any(value is True and key not in allowed_battle and (key.startswith('diagnostic_') or key.startswith('town_'))
                    for key,value in vars(args).items())):
            parser.error('Shared server attachment cannot combine single-client diagnostic ownership modes')
    if args.probe_server_confirm and not (args.probe_login_submit and args.recovered_dual_connection):
        parser.error('--probe-server-confirm requires native login submission and own-server dual connection')
    if args.observe_character_create and not args.probe_server_confirm:
        parser.error('--observe-character-create requires --probe-server-confirm')
    if args.probe_character_create and not args.observe_character_create:
        parser.error('--probe-character-create requires --observe-character-create')
    if args.isolated_database and not args.cpp_server:
        parser.error('--isolated-database requires --cpp-server')
    if args.observe_created_refresh and not args.probe_character_create:
        parser.error('--observe-created-refresh requires --probe-character-create')
    if args.probe_character_select and not args.observe_created_refresh:
        parser.error('--probe-character-select requires --observe-created-refresh')
    if args.observe_world_entry and not args.probe_character_select:
        parser.error('--observe-world-entry requires --probe-character-select')
    if args.observe_world_loop and not args.observe_world_entry:
        parser.error('--observe-world-loop requires --observe-world-entry')
    if args.observe_world_frames and not args.observe_world_loop:
        parser.error('--observe-world-frames requires --observe-world-loop')
    if args.probe_movement_step and not (args.observe_world_frames and args.movement_lab):
        parser.error('--probe-movement-step requires world frames and isolated movement lab')
    if args.remote_actor_probe_language is not None:
        if not (args.cpp_server and args.isolated_database and args.movement_lab and args.observe_world_frames):
            parser.error('Remote actor probe requires isolated C++ movement and world frame observation')
        if (args.town_entry_lab or args.restore_movement_database or args.restore_town_database or
                args.probe_movement_step or any(value is True for key,value in vars(args).items() if key.startswith('diagnostic_'))):
            parser.error('Remote actor probe cannot combine other movement/diagnostic/restore modes')
    if args.movement_lab and not (args.cpp_server and args.isolated_database and args.recovered_world_entry):
        parser.error('--movement-lab requires isolated C++ world-entry run')
    if args.town_entry_lab and (not args.movement_lab or args.restore_movement_database or
            (args.diagnostic_battle_transition and not args.town_battle_after_quest) or
            args.diagnostic_quest_dialogue or args.diagnostic_world_resources):
        parser.error('--town-entry-lab requires fresh movement lab without indoor probes/diagnostics')
    if args.town_entry_lab and args.probe_movement_step and args.movement_steps<2:
        parser.error('Town path probe requires at least two steps and idle completion')
    if args.town_east_path and not (args.town_entry_lab and args.probe_movement_step):
        parser.error('--town-east-path requires the isolated town movement probe')
    if args.town_detour_path and (not args.town_entry_lab or not args.probe_movement_step or args.town_east_path):
        parser.error('--town-detour-path requires town movement without --town-east-path')
    if args.movement_steps>39 and not args.town_detour_path:
        parser.error('More than39 steps requires the bounded town detour probe')
    if args.town_consensus_path and not (args.town_detour_path or args.restore_town_database or args.town_fresh_spawn):
        parser.error('--town-consensus-path requires detour, restored town, or fresh town mode')
    if args.town_fresh_spawn and not (args.cpp_server and args.isolated_database and args.town_entry_lab and
            args.town_consensus_path and args.town_spawn_guides and args.town_quest_progress and
            args.observe_npc_state and args.observe_world_frames and not args.restore_town_database and
            not args.probe_movement_step and (not args.town_battle_after_quest or
            (args.town_quest_reward_chain and args.town_scene_follow_move))):
        parser.error('Fresh town spawn requires isolated C++ server, source-agreement town, NPC/frame observers, and an un-restored new character')
    if args.restore_town_database and not (args.town_entry_lab and args.town_consensus_path and
            args.observe_world_frames and args.probe_character_select and not args.town_detour_path and not args.town_east_path):
        parser.error('Town restore requires standalone source-agreement entry observation')
    if args.ui_world_movement and not (args.restore_town_database and args.town_spawn_guides and
            args.observe_npc_state and args.observe_world_frames and not args.probe_movement_step and
            not args.town_quest_progress and not args.town_map_probe and not args.town_battle_after_quest and
            not args.diagnostic_battle_transition):
        parser.error('UI movement requires passive restored-town world observation only')
    if args.ui_npc_dialogue and not (args.restore_town_database and args.town_spawn_guides and
            args.observe_npc_state and args.observe_world_frames and not args.ui_world_movement and
            not args.probe_npc_request and not args.probe_movement_step and not args.town_quest_progress and not args.town_map_probe and
            not args.town_battle_after_quest and not args.diagnostic_battle_transition):
        parser.error('UI NPC dialogue requires passive restored-town world observation only')
    if args.verify_restored_town_position and not (args.restore_town_database and args.town_spawn_guides and
            args.observe_npc_state and args.observe_world_frames and not args.ui_world_movement and
            not args.probe_npc_request and not args.probe_movement_step):
        parser.error('Restored town position verification requires passive isolated town observation')
    if args.town_battle_after_quest and not ((args.restore_town_database or args.town_fresh_spawn) and args.town_scene_indoor_transfer and
            args.town_quest_progress and args.town_spawn_guides and args.town_map_probe and args.town_scene_probe and
            args.town_scene_indoor_probe and args.diagnostic_battle_transition and
            args.diagnostic_battle_participants and args.diagnostic_battle_player_appearance and
            args.diagnostic_battle_animations and args.diagnostic_battle_skill_seed and
            args.diagnostic_battle_skill_settlement and args.diagnostic_battle_terminal and
            args.diagnostic_battle_resources and args.diagnostic_battle_rounds==1 and
            args.diagnostic_encounter_limit==1 and not args.diagnostic_battle_experience and
            not args.diagnostic_role_progress and (not args.town_scene_return_probe or (args.town_scene_return_commit and args.town_return_after_battle)) and
            not args.town_auto_door and not args.probe_movement_step):
        parser.error('Town battle requires the isolated indoor stage-3 one-round skill fixture')
    if args.town_return_after_battle and not (args.town_battle_after_quest and args.town_scene_return_probe and
                                              args.town_scene_return_commit and not args.probe_post_battle_movement):
        parser.error('Post-battle return requires isolated battle and durable map return')
    if args.town_door_after_battle and not (args.town_battle_after_quest and not args.town_return_after_battle and
                                           not args.town_scene_return_probe and not args.probe_post_battle_movement and
                                           not args.town_auto_door):
        parser.error('Post-battle doorway requires isolated battle without competing return probes')
    if args.town_door_reconnect and not (args.restore_town_database and args.town_quest_progress and
                                         args.town_spawn_guides and not args.town_battle_after_quest and
                                         not args.town_map_probe and not args.town_scene_probe and
                                         not args.town_door_after_battle):
        parser.error('Post-battle doorway reconnect requires isolated completed-town restore')
    if args.town_completed_quest_restore and not (args.restore_town_database and args.town_quest_progress and
            args.town_scene_indoor_transfer and not args.town_battle_after_quest and
            not args.diagnostic_battle_transition and not args.probe_npc_request):
        parser.error('Completed quest restore requires isolated indoor save without battle or conversation')
    if args.town_post_battle_position_restore and not args.town_completed_quest_restore:
        parser.error('Post-battle position restore requires completed quest cold reconnect')
    if args.recovered_world_entry and not args.recovered_dual_connection:
        parser.error('--recovered-world-entry requires --recovered-dual-connection')
    if args.recovered_dual_connection and not args.recovered_character_create:
        parser.error('--recovered-dual-connection requires --recovered-character-create')
    if args.recovered_character_create and not args.recovered_account_auth:
        parser.error('--recovered-character-create requires --recovered-account-auth')
    if args.recovered_account_auth and not args.legacy_character_list_candidate:
        parser.error('--recovered-account-auth requires --legacy-character-list-candidate')
    if args.legacy_character_list_candidate and not (args.zero_ui_prefix and args.server_list and args.cpp_server):
        parser.error('--legacy-character-list-candidate requires --zero-ui-prefix, --server-list and --cpp-server')
    if args.auto_pagefile_capacity and not (args.zero_ui_prefix and args.warning_input_trace and args.mode=='MODE_COMPAT'):
        parser.error('--auto-pagefile-capacity requires MODE_COMPAT, --zero-ui-prefix and --warning-input-trace')
    if args.warning_input_trace and not args.zero_ui_prefix:
        parser.error('--warning-input-trace requires --zero-ui-prefix')
    if args.zero_ui_prefix and (args.owner_ui or args.enter_game or args.test_login or
                               args.ui_gate_rendezvous):
        parser.error('--zero-ui-prefix cannot use UI actions')
    if args.recover_crypto:
        if args.crypto_manifest is None or args.crypto_output is None:
            parser.error('--recover-crypto requires --crypto-manifest and --crypto-output')
        from crypto_recovery import recover
        recover(args.crypto_manifest,args.crypto_output)
        return 0
    if args.crypto_manifest is not None or args.crypto_output is not None:
        parser.error('crypto manifest/output require --recover-crypto')
    if args.post_server_select_follow and not args.ui_gate_rendezvous:parser.error('--post-server-select-follow requires --ui-gate-rendezvous')
    if args.ui_gate_check or args.ui_gate_rendezvous:
        from ui_gate import Rendezvous,preflight
        Rendezvous(args.run_id,args.ui_gate_max_wait)
        report=preflight(HOME,CLIENT)
        if args.ui_gate_check or report['blockers']:
            print(json.dumps(report))
            return 2 if report['blockers'] else 0
        args.mode='MODE_COMPAT'
        args.network_strike=args.cpp_server=args.post_seed=args.c2s_strike=True
        args.s2c0003=args.login_terminal=args.server_list=True
        args.lab_case='A'
    if args.ui_gate_max_wait is not None and not args.ui_gate_rendezvous:parser.error('--ui-gate-max-wait requires a UI gate mode')
    if args.mode is None:parser.error('--mode is required outside UI gate modes')
    if args.network_strike:
        if args.mode!='MODE_COMPAT':raise ValueError('Network strike requires accepted MODE_COMPAT')
        args.enter_game=not args.zero_ui_prefix;args.test_login=not args.zero_ui_prefix
    if args.owner_ui:
        if not args.ui_gate_rendezvous:
            parser.error('--owner-ui requires --ui-gate-rendezvous')
        args.enter_game = args.test_login = False
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',args.run_id):raise ValueError('Unsafe run ID')
    if not 15<=args.timeout<=300:raise ValueError('Timeout must be 15..300 seconds')
    if args.test_login and not args.enter_game:raise ValueError('--test-login requires --enter-game')
    if args.cpp_server and not args.network_strike:raise ValueError('--cpp-server requires --network-strike')
    if args.post_seed and not args.cpp_server:raise ValueError('--post-seed requires --cpp-server')
    if args.c2s_strike and not args.post_seed:raise ValueError('--c2s-strike requires --post-seed')
    if args.lab_case and not args.c2s_strike:raise ValueError('--lab-case requires --c2s-strike')
    if args.s2c0003 and not args.c2s_strike:raise ValueError('--s2c0003 requires --c2s-strike')
    if args.login_terminal and not args.s2c0003:raise ValueError('--login-terminal requires --s2c0003')
    if args.server_list_probe and not args.login_terminal:raise ValueError('--server-list-probe requires --login-terminal')
    if args.server_list:
        if not args.login_terminal:raise ValueError('--server-list requires --login-terminal')
        args.server_list_probe=True
    run=HOME/'artifacts/runs'/args.run_id;run.mkdir(parents=True,exist_ok=False)
    (run/'c2s').mkdir();(run/'s2c').mkdir();(run/'network').mkdir()
    observer=Observer(run,args.mode,args.timeout,args.enter_game,args.test_login,args.milestone_ceiling,args.network_strike)
    observer.owner_ui = args.owner_ui
    observer.ui_world_movement = args.ui_world_movement
    observer.ui_npc_dialogue = args.ui_npc_dialogue
    observer.ui_npc_stop = args.ui_npc_stop
    if args.observe_ui_npc_buttons and not (args.ui_world_movement or args.ui_npc_dialogue):
        parser.error('NPC UI button observation requires passive UI world observation')
    observer.observe_ui_npc_buttons = args.observe_ui_npc_buttons or args.ui_npc_dialogue
    observer.verify_restored_town_position = args.verify_restored_town_position
    observer.zero_ui_prefix = args.zero_ui_prefix
    observer.observe_login_entry = args.observe_login_entry
    observer.probe_login_command = args.probe_login_command
    observer.probe_login_panel = args.probe_login_panel
    observer.probe_login_submit = args.probe_login_submit
    observer.probe_server_confirm = args.probe_server_confirm
    observer.observe_character_create = args.observe_character_create
    observer.probe_character_create = args.probe_character_create
    observer.observe_created_refresh = args.observe_created_refresh
    observer.probe_character_select = args.probe_character_select
    observer.observe_world_entry = args.observe_world_entry
    observer.observe_world_loop = args.observe_world_loop
    if args.observe_quest_text_table and not args.observe_world_frames:
        parser.error('--observe-quest-text-table requires --observe-world-frames')
    if args.diagnostic_quest_dialogue and not (args.cpp_server and args.isolated_database and
            args.movement_lab and args.observe_world_frames and args.observe_quest_text_table and
            not args.diagnostic_battle_transition and not args.diagnostic_world_resources):
        parser.error('Quest dialogue requires isolated observed standalone world')
    town_conversation=args.town_spawn_guides and args.probe_npc_request
    if town_conversation and not (args.observe_quest_text_table and args.complete_npc_conversation):
        parser.error('Town conversation requires text-table observation and complete conversation probe')
    observer.diagnostic_quest_dialogue = args.diagnostic_quest_dialogue or town_conversation
    if args.probe_quest_confirm and not (args.diagnostic_quest_dialogue or town_conversation):
        raise ValueError('Quest confirm requires isolated diagnostic dialogue')
    observer.probe_quest_confirm = args.probe_quest_confirm
    if args.probe_quest_close and not (args.probe_quest_confirm and args.complete_npc_conversation):
        raise ValueError('Close probe requires complete diagnostic NPC conversation')
    observer.probe_quest_close = args.probe_quest_close
    if args.probe_npc_reopen and not args.probe_quest_close:
        raise ValueError('NPC reopen probe requires initial close probe')
    observer.probe_npc_reopen=args.probe_npc_reopen
    if args.observe_quest_transport and not args.probe_quest_confirm:
        raise ValueError('Quest transport requires native confirm probe')
    observer.observe_quest_transport = args.observe_quest_transport
    if args.observe_npc_state and not args.observe_world_frames:
        raise ValueError('NPC state observation requires native world frames')
    observer.observe_npc_state = args.observe_npc_state
    if args.probe_town_guide_resource and not (args.observe_npc_state and args.observe_world_frames and args.isolated_database):
        raise ValueError('Town resource probe requires isolated world/NPC observation')
    observer.probe_town_guide_resource=args.probe_town_guide_resource
    if args.diagnostic_quest_npc and not (args.diagnostic_quest_dialogue and args.observe_npc_state):
        raise ValueError('NPC spawn diagnostic requires quest dialogue and NPC state observation')
    observer.diagnostic_quest_npc = args.diagnostic_quest_npc or town_conversation
    if args.probe_npc_request and not ((args.diagnostic_quest_npc or town_conversation) and args.probe_quest_confirm and args.observe_quest_transport):
        raise ValueError('NPC request requires isolated spawn and native-call transport observation')
    observer.probe_npc_request = args.probe_npc_request
    if args.complete_npc_conversation and not args.probe_npc_request:
        raise ValueError('Complete conversation requires native NPC request probe')
    observer.complete_npc_conversation = args.complete_npc_conversation
    observer.observe_quest_text_table = args.observe_quest_text_table
    observer.observe_world_frames = args.observe_world_frames
    observer.probe_movement_step = args.probe_movement_step
    observer.town_east_path = args.town_east_path
    observer.town_detour_path = args.town_detour_path
    observer.town_entry_lab = args.town_entry_lab
    observer.town_fresh_spawn = args.town_fresh_spawn
    if args.town_spawn_guides and not ((args.restore_town_database or args.town_fresh_spawn) and args.observe_npc_state and
                                      args.observe_world_frames and not args.probe_movement_step):
        parser.error('Town guide spawn requires restored or fresh town, NPC/frame observers and no movement probe')
    observer.town_spawn_guides = args.town_spawn_guides
    if args.observe_town_npc_render and not (args.town_spawn_guides and args.observe_npc_state and args.observe_world_frames):
        parser.error('Town NPC render observation requires isolated native NPC/frame observation')
    observer.observe_town_npc_render = args.observe_town_npc_render
    observer.town_guide_target = args.town_guide_target
    if args.town_quest_progress and not (args.town_fresh_spawn or args.town_battle_after_quest or args.town_completed_quest_restore or
            (town_conversation and not args.probe_quest_close and not args.probe_npc_reopen)):
        parser.error('Town progress probe requires complete conversation without close/reopen')
    observer.town_quest_progress = args.town_quest_progress
    if args.town_map_probe and not (args.town_quest_progress and args.town_guide_target==1606 and
                                   (not args.town_quest_chain or args.town_quest_reward_chain)):
        parser.error('Town map probe requires completed restore or full reward chain, target1606')
    if args.town_quest_reward_chain and args.town_scene_probe and not args.town_fresh_spawn:
        parser.error('Reward chain map use does not qualify a scene-transfer combination')
    observer.town_map_probe = args.town_map_probe
    if args.town_scene_probe and not (args.town_map_probe and (args.restore_town_database or args.town_fresh_spawn)):
        raise ValueError('Scene probe requires isolated restored or fresh town map probe')
    observer.town_scene_probe = args.town_scene_probe
    if args.town_scene_relocate and not args.town_scene_probe:
        raise ValueError('Town relocation requires scene probe')
    observer.town_scene_relocate = args.town_scene_relocate
    if args.town_scene_follow_move and not (args.town_scene_relocate or args.town_scene_indoor_transfer):
        raise ValueError('Post-transfer movement requires relocation')
    observer.town_scene_follow_move = args.town_scene_follow_move
    if args.town_scene_indoor_probe and (not args.town_scene_probe or args.town_scene_relocate):
        raise ValueError('Indoor probe requires scene probe without relocation')
    observer.town_scene_indoor_probe = args.town_scene_indoor_probe
    if args.town_scene_indoor_transfer and not (args.town_scene_indoor_probe and args.town_consensus_path):
        raise ValueError('Durable indoor transfer requires indoor probe and source consensus')
    observer.town_scene_indoor_transfer = args.town_scene_indoor_transfer
    observer.taiwan_resource_locale = args.taiwan_resource_locale
    if args.town_scene_return_probe and (not args.town_scene_indoor_transfer or
                                       (args.town_scene_follow_move and not args.town_scene_return_commit)):
        raise ValueError('Return probe requires dual-map restore without followup movement')
    observer.town_scene_return_probe = args.town_scene_return_probe
    if args.town_scene_return_commit and not args.town_scene_return_probe:
        raise ValueError('Durable return requires return probe')
    observer.town_scene_return_commit = args.town_scene_return_commit
    if args.indoor_door_probe and (not args.town_scene_indoor_transfer or args.town_scene_return_probe or args.town_scene_follow_move):
        raise ValueError('Door observation requires isolated indoor restore without transfer probes')
    observer.indoor_door_probe = args.indoor_door_probe
    if args.town_door_probe and (not args.restore_town_database or not args.town_consensus_path or
                                not args.town_quest_progress or not args.complete_npc_conversation or
                                args.indoor_door_probe or args.town_map_probe or args.town_scene_follow_move):
        raise ValueError('Town door probe requires completed restored town workflow without map/scene probes')
    observer.town_door_probe = args.town_door_probe
    if args.town_special_entry_probe and not args.town_door_probe:
        raise ValueError('Special entry probe requires town door approach')
    observer.town_special_entry_probe = args.town_special_entry_probe
    if args.town_auto_door and not args.town_special_entry_probe:
        raise ValueError('Automatic door qualification requires special entry approach')
    observer.town_auto_door = args.town_auto_door
    observer.town_door_after_battle = args.town_door_after_battle
    if args.town_auto_door_roundtrips and not args.town_auto_door:
        raise ValueError('Doorway roundtrips require automatic door mode')
    observer.town_auto_door_roundtrips = args.town_auto_door_roundtrips
    observer.remote_actor_probe_language = args.remote_actor_probe_language
    if args.town_quest_chain and not (args.town_quest_progress and args.town_guide_target==1606):
        parser.error('Town quest chain requires initial target1606 and progress mode')
    observer.town_quest_chain = args.town_quest_chain
    if args.town_quest_reward_chain and not args.town_quest_chain:
        parser.error('Town reward chain requires town quest chain and an explicitly empty saved slot0')
    observer.town_quest_reward_chain = args.town_quest_reward_chain
    observer.movement_steps = args.movement_steps
    observer.restore_movement_database = args.restore_movement_database
    observer.restore_town_database = args.restore_town_database
    observer.town_battle_after_quest = args.town_battle_after_quest
    observer.town_return_after_battle = args.town_return_after_battle
    observer.town_completed_quest_restore = args.town_completed_quest_restore
    observer.diagnostic_battle_transition = args.diagnostic_battle_transition
    observer.diagnostic_battle_after_movement = args.diagnostic_battle_after_movement
    observer.diagnostic_encounter_limit = args.diagnostic_encounter_limit
    observer.observe_socket_battle_vitals = args.observe_socket_battle_vitals
    observer.diagnostic_battle_participants = args.diagnostic_battle_participants
    observer.diagnostic_battle_revival = args.diagnostic_battle_revival
    observer.diagnostic_battle_player_appearance = args.diagnostic_battle_player_appearance
    observer.diagnostic_battle_animations = args.diagnostic_battle_animations
    observer.probe_socket_battle_action = args.probe_socket_battle_action
    observer.probe_socket_skill_select = args.probe_socket_skill_select
    observer.probe_socket_skill_command = args.probe_socket_skill_command
    observer.diagnostic_battle_skill_settlement = args.diagnostic_battle_skill_settlement
    observer.diagnostic_battle_mp_refusal = args.diagnostic_battle_mp_refusal
    observer.initial_battle_hp = 100
    observer.observe_socket_defeat = args.observe_socket_defeat
    observer.diagnostic_world_resources = args.diagnostic_world_resources
    observer.diagnostic_world_supply = args.diagnostic_world_supply
    observer.probe_supply_use = args.probe_supply_use
    observer.probe_supply_exhaustion = args.probe_supply_exhaustion
    observer.expect_no_world_resources = args.expect_no_world_resources
    observer.initial_battle_mp = 7 if args.diagnostic_battle_mp_refusal else 50
    observer.observe_socket_retaliation = args.observe_socket_retaliation
    observer.diagnostic_battle_rounds = args.diagnostic_battle_rounds
    observer.diagnostic_resume_checkpoint = args.diagnostic_resume_checkpoint
    if args.shared_server_manifest and shared_document.get('resume_skill_checkpoint') and args.lab_peer==0:
        if not shared_document.get('skill_battle'):raise ValueError('Shared skill resume requires skill mode')
        observer.diagnostic_resume_checkpoint=True
        observer.diagnostic_battle_rounds=2
        observer.initial_battle_hp=88;observer.initial_battle_mp=42;observer.initial_enemy_hp=96
    if args.diagnostic_resume_checkpoint and not args.diagnostic_battle_revival:
        observer.diagnostic_battle_rounds=2
        observer.initial_enemy_hp=96
    observer.diagnostic_battle_terminal = args.diagnostic_battle_terminal
    observer.diagnostic_battle_experience = args.diagnostic_battle_experience
    observer.diagnostic_role_progress = args.diagnostic_role_progress
    observer.diagnostic_progress_span = args.diagnostic_progress_span
    observer.diagnostic_level_snapshot = args.diagnostic_level_snapshot
    observer.stop_after_first_checkpoint = args.stop_after_first_checkpoint
    observer.stop_after_second_checkpoint = args.stop_after_second_checkpoint
    observer.observe_socket_outcome_panel = args.observe_socket_outcome_panel
    observer.observe_socket_battle_exit = args.observe_socket_battle_exit
    observer.probe_post_battle_movement = args.probe_post_battle_movement
    observer.warning_input_trace = args.warning_input_trace
    if args.auto_pagefile_capacity:
        from pagefile_capacity_compat import CapacityAdapter
        observer.pagefile_adapter = CapacityAdapter(CLIENT,run)
    observer.c2s_strike=args.c2s_strike
    observer.lab_case=args.lab_case
    observer.lab_peer=args.lab_peer
    observer.shared_visibility=bool(args.shared_server_manifest)
    observer.terminal=args.login_terminal
    observer.server_list_probe=args.server_list_probe
    observer.rendezvous=args.ui_gate_rendezvous
    observer.post_select_follow=args.post_server_select_follow
    observer.gate_max_wait=args.ui_gate_max_wait
    native.NativeDriver=NetworkDriver
    native.OUT=run;interactive.OUT=run
    result={};gate_lease=None
    try:
        if args.ui_gate_rendezvous:
            from ui_gate_live import RunLease
            gate_lease=RunLease(HOME/'artifacts/strike')
        if args.network_strike:
            from server_first import write_contract
            observer.reference_image,initial=write_contract(HOME,run)
            observer.sink=SharedCppServer(args.shared_server_manifest,HOME) if args.shared_server_manifest else CppSeedServer(run,args.timeout,args.post_seed,args.s2c0003,args.login_terminal,args.server_list,args.ui_gate_rendezvous,args.post_server_select_follow,args.legacy_character_list_candidate,args.recovered_account_auth,args.recovered_character_create,args.recovered_dual_connection,args.recovered_world_entry,args.isolated_database,args.movement_lab,args.restore_movement_database,args.diagnostic_battle_transition,args.diagnostic_battle_participants,args.diagnostic_battle_rounds,args.diagnostic_battle_terminal,args.diagnostic_battle_player_appearance,args.diagnostic_battle_animations,args.diagnostic_battle_skill_seed,args.diagnostic_battle_skill_settlement,args.diagnostic_battle_mp_refusal,diagnostic_battle_resources=args.diagnostic_battle_resources,diagnostic_world_resources=args.diagnostic_world_resources,diagnostic_battle_experience=args.diagnostic_battle_experience,diagnostic_role_progress=args.diagnostic_role_progress,diagnostic_progress_span=args.diagnostic_progress_span,diagnostic_level_snapshot=args.diagnostic_level_snapshot,diagnostic_resume_checkpoint=args.diagnostic_resume_checkpoint,diagnostic_battle_after_movement=args.diagnostic_battle_after_movement,diagnostic_encounter_limit=args.diagnostic_encounter_limit,diagnostic_world_supply=args.diagnostic_world_supply,diagnostic_battle_revival=args.diagnostic_battle_revival,diagnostic_quest_dialogue=args.diagnostic_quest_dialogue,diagnostic_quest_npc=args.diagnostic_quest_npc,town_entry_lab=args.town_entry_lab,town_consensus_path=args.town_consensus_path,restore_town_database=args.restore_town_database,town_fresh_spawn=args.town_fresh_spawn,town_spawn_guides=args.town_spawn_guides,town_quest_progress=args.town_quest_progress,town_map_probe=args.town_map_probe,town_scene_probe=args.town_scene_probe,town_scene_relocate=args.town_scene_relocate,town_scene_indoor_probe=args.town_scene_indoor_probe,town_scene_indoor_transfer=args.town_scene_indoor_transfer,town_scene_return_probe=args.town_scene_return_probe,town_scene_return_commit=args.town_scene_return_commit,town_door_routes=(args.town_auto_door or args.town_door_after_battle),town_battle_after_quest=args.town_battle_after_quest,town_return_after_battle=args.town_return_after_battle,town_door_after_battle=args.town_door_after_battle,town_door_reconnect=args.town_door_reconnect,town_post_battle_position_restore=args.town_post_battle_position_restore,remote_actor_probe_language=args.remote_actor_probe_language) if args.cpp_server else Sink(2592,run,initial)
            if args.town_completed_quest_restore and (observer.sink.town_guide_start_stage!=3 or
                    observer.sink.restored_town_scene!=15 or
                    observer.sink.restored_town_position!=((19,12) if args.town_post_battle_position_restore else (18,12))):
                raise ValueError('Completed quest restore requires qualified stage-3 indoor save')
        if args.diagnostic_world_supply:
            observer.expected_supply_slot=observer.sink.expected_supply_slot
        if args.diagnostic_battle_resources and args.restore_movement_database:
            observer.initial_battle_hp,observer.initial_battle_mp=observer.sink.restored_battle_resources
            if args.diagnostic_resume_checkpoint and not args.diagnostic_battle_revival:
                observer.diagnostic_battle_rounds=3-observer.sink.restored_exchanges
                observer.initial_enemy_hp=150-54*observer.sink.restored_exchanges
            if args.observe_socket_defeat and (observer.initial_battle_hp,observer.initial_battle_mp)!=(4,56):
                raise ValueError('Defeat observer requires saved HP4/MP56')
            if observer.initial_battle_hp==4 and not args.observe_socket_defeat:
                raise ValueError('HP4 battle requires explicit defeat observation')
        with (run/'stdout.log').open('x') as out,(run/'stderr.log').open('x') as err,redirect_stdout(out),redirect_stderr(err):
            from current_skill_hotbar_fixture import isolated_hotbar
            profile=(observer.sink.client_profile(CLIENT) if args.shared_server_manifest
                     else profile_context(PROFILES[2],CLIENT,run))
            parent_hotbar=bool(args.shared_server_manifest and shared_document.get('skill_battle'))
            with profile, isolated_hotbar(CLIENT,run,args.diagnostic_battle_hotbar and not parent_hotbar,revival=args.diagnostic_battle_revival):
                native.run(args.run_id,lab=observer)
        result=json.loads((run/f'{args.run_id}-result.json').read_text())
    except Exception as error:result={'result':'TOOL_ERROR','error':repr(error)}
    finally:
        if observer.sink:observer.sink.close()
        if getattr(observer,'gate',None):observer.gate.finish(result.get('result','TOOL_ERROR'))
        if gate_lease:gate_lease.close()
        if args.network_strike and observer.reference_image is not None:
            from server_first import exchange_result
            result['server_first']=exchange_result(HOME,run,observer.events,observer.sink.events if observer.sink else [],observer.reference_image)
            if args.post_seed:
                from post_seed import summarize
                result['post_seed']=summarize(HOME,run,observer.events,result['server_first'])
            if args.s2c0003:
                from c2s0002 import summarize
                result['c2s0002']=summarize(HOME,run,observer.events,result['post_seed'])
                if result['c2s0002']['CREDENTIAL_REQUEST_VERIFIED']:
                    observer.events.append({'event_type':'CREDENTIAL_REQUEST_VERIFIED','scope':'request only, not authentication success'})
                    result.setdefault('milestones',{})['LOGIN']=False
            if args.login_terminal:
                from login_terminal import summarize
                result['login_terminal']=summarize(HOME,run,observer.events,result['c2s0002'])
                if result['login_terminal']['LOGIN']:
                    observer.events.append({'event_type':'LOGIN_ACCEPTED_VERIFIED','scope':'terminal return and UI state change'})
                    result.setdefault('milestones',{})['LOGIN']=True
            if args.server_list:
                from server_list import summarize
                result['server_list']=summarize(HOME,run,observer.events,result['login_terminal'])
        result.update(mode=args.mode,run_id=args.run_id,client_disk_sha256=sha(CLIENT/'God2.exe'),
            semantic_scope='One process-local IAT pointer plus private RX tail bridge; DLL hosted in CDB, no remote thread or injected DLL',
            mode_observe_scope='No compat writes; debugger breakpoints still instrument execution',
            timeout_stop_method='DebugBreakProcess on verified child (debugger break-in thread, diagnostic only)',
            source_hashes={p.name:sha(p) for p in (Path(__file__),HOME/'tools/strike_lab/network_driver.py',HOME/'tools/strike_lab/window_snapshot.py',HOME/'tools/strike_lab/compat.cpp',HOME/'tools/strike_lab/compat_bridge.h',HOME/'tools/strike_lab/native_dialog.cpp',HOME/'tools/strike_lab/lab.py',HOME/'build-strike-lab/Release/god2-strike-runner.exe',HOME/'build-strike-lab/Release/God2Compat.dll')})
        if args.post_seed:
            result['source_hashes'].update({str(p.relative_to(HOME)):sha(p) for p in (
                HOME/'tools/strike_lab/post_seed.py',HOME/'tools/strike_lab/server_first.py',
                HOME/'src/protocol/RecoveredPostSeed.h',HOME/'src/net/Session.cpp',
                HOME/'build/Release/god2-server.exe',HOME/'config/recovered-post-seed.json')})
        if args.c2s_strike:
            result['source_hashes'].update({str(p.relative_to(HOME)):sha(p) for p in (
                HOME/'tools/strike_lab/c2s0002.py',HOME/'src/protocol/RecoveredC2S0002.h',
                HOME/'src/protocol/RecoveredZeroSeedKey.h',HOME/'config/recovered-c2s0002.json')})
        if args.login_terminal:
            result['source_hashes'].update({str(p.relative_to(HOME)):sha(p) for p in (
                HOME/'tools/strike_lab/login_terminal.py',HOME/'src/protocol/RecoveredLoginTerminal.h',
                HOME/'config/recovered-login-terminal.json')})
        if args.server_list:
            result['source_hashes'].update({str(p.relative_to(HOME)):sha(p) for p in (
                HOME/'tools/strike_lab/server_list.py',HOME/'src/protocol/RecoveredServerList.h',
                HOME/'config/recovered-server-list.json')})
        if args.auto_pagefile_capacity:
            result['semantic_scope'] += '; opt-in effective-capacity query-result view and one real OS disk API binding, restored before client arithmetic'
            for filename in ('pagefile_capacity_compat.py','warning_input_trace.py','summarize_pagefile_capacity.py'):
                result['source_hashes'][filename]=sha(HOME/'tools/strike_lab'/filename)
        if args.probe_login_command:
            result['source_hashes']['tools/strike_lab/current_login_command.py'] = sha(HOME/'tools/strike_lab/current_login_command.py')
        write_json(run/'run.json',result)
        write_json(run/'client-state.json',result.get('milestones',milestones(observer.events)))
        update_progress(run,observer.events)
        write_json(run/'modules.json',{'raw_lm':result.get('modules','')})
        for filename,network in (('compat-events.jsonl',False),('network-events.jsonl',True)):
            with (run/filename).open('x') as stream:
                for event in observer.events:
                    if ('api' in event)==network:stream.write(json.dumps(event)+'\n')
                if network and observer.sink:
                    for event in observer.sink.events:stream.write(json.dumps(event)+'\n')
        if args.auto_pagefile_capacity:
            from summarize_pagefile_capacity import summarize
            try:
                acceptance=summarize(run)
            except Exception as error:
                acceptance={'runtime_acceptance':'NOT_VERIFIED','error':repr(error)}
            write_json(run/'pagefile-acceptance.json',acceptance)
    if args.ui_gate_rendezvous:
        path=run/'ui_gate_result.json'
        print(path.read_text() if path.exists() else json.dumps({'ui_gate_ready':False,'result':result.get('result'),'error':result.get('error')}))
        return 0 if result.get('result')=='POST_GATE_EVENT' else 1
    print(json.dumps(execution_summary(result,run)))
    return 1 if result.get('result') in ('TOOL_ERROR','REGRESSION') else 0


if __name__=='__main__':raise SystemExit(main())
