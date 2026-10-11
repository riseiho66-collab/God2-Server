"""Hidden current-client sex-restricted weapon refusal acceptance.

Only a disposable clone is mutated. TWP metadata is a CUSTOM_TEST_NOT_NATIVE
operand, not recovered instance generation. No screenshots, desktop switching,
memory writes, source DB edits, or changes to the existing owned harnesses.
The candidate must expose a qualified rejection log marker and native message
readback is required before a run can claim complete acceptance.
"""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import sqlite3
import struct
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import psutil
import private_weapon_peer_appearance_20260927 as shared
from tools.strike_lab import run_private_owned_companions as fixture
import private_owned_companions_ui as owned
from private_inventory_memory import kernel
from private_inventory_move_ui import desktop_names, wait_until, require
from private_potion_ui import click, type_ascii, user
from private_map_item_current_ui import double_click_message


def complete_snapshot(db):
    """All owned bag/meta/appearance plus relevant role and battle tables."""
    value = {'weapons': owned.saved_weapons(db), 'appearance': owned.saved_weapon_appearance(db),
             'related': shared.db_stable(db)}
    with closing(shared.ro(db)) as connection:
        for table in ('battle_reservations', 'battle_settlements', 'battle_checkpoints'):
            value[table] = [[v.hex() if isinstance(v, bytes) else v for v in row]
                           for row in connection.execute(f'SELECT * FROM {table} ORDER BY 1')]
        value['position'] = connection.execute('SELECT * FROM recovered_positions WHERE character_id=4').fetchone()
    return value


def native_snapshot(client):
    handle, ui = client['handle'], client['ui']
    state = owned.native(handle, ui)
    return {'slots50': shared.exact(handle, ui + 0x8560c, 1200).hex(),
            'stable': {k: state[k] for k in shared.STABLE_KEYS},
            'appearance': owned.native_weapon_appearance(handle, ui),
            'map': state['world_map'], 'pending': shared.exact(handle, ui + 0x85608, 4).hex()}


def unchanged_native(before, after):
    # The middle word of each native component entry is animated, not stable.
    return all(before[k] == after[k] for k in ('slots50', 'stable', 'map')) and \
        before['appearance']['logical_hex'] == after['appearance']['logical_hex'] and \
        all({k:a[k] for k in ('handle','variant')} == {k:b[k] for k in ('handle','variant')}
            for a,b in zip(before['appearance']['live_components'], after['appearance']['live_components']))


def native_message(client, expected_text):
    """Current 484E00->47DE00 channel4, both native chat rings; no scanning.

    Rows may wrap the source text. Join chronological channel4 rows before
    removing the native /cN color commands, retaining every raw row as evidence.
    """
    handle,ui=client['handle'],client['ui']
    visible=int.from_bytes(shared.exact(handle,ui+0x39de8,4),'little')
    require(visible>0x10000,'VISIBLE_CHAT_RING_MISSING')
    rings=[]
    for name,address in (('visible',visible),('archive',ui+0x39e20)):
        raw=shared.exact(handle,address,0x67f4)
        count,oldest,next_index=struct.unpack_from('<3I',raw,0x67e8)
        require(count<=200 and oldest<200 and next_index<200,'CHAT_RING_COUNTER_OUTSIDE_NATIVE_CAPACITY')
        rows=[]
        for index in ((oldest+i)%200 for i in range(count)):
            text=raw[index*128:(index+1)*128].split(b'\0')[0]
            channel=raw[0x6400+index]
            color=struct.unpack_from('<I',raw,0x64c8+4*index)[0]
            rows.append({'index':index,'channel':channel,'color':color,'raw_hex':text.hex()})
        joined=b''.join(bytes.fromhex(row['raw_hex']) for row in rows if row['channel']==4)
        plain=re.sub(rb'/c[0-9a-fA-F]',b'',joined).decode('cp950',errors='strict')
        rings.append({'name':name,'address':hex(address),'count':count,'oldest':oldest,'next':next_index,
                      'rows':rows,'channel4_text':plain,'matched':bool(expected_text) and expected_text in plain})
    return {'normal_chat':shared.exact(handle,ui+0x39e18,1).hex(),'expected_text':expected_text,
            'matched':all(r['matched'] for r in rings),'rings':rings}


def prepare(args):
    # This validated preparation imports pinned WPN/TWP definitions, creates
    # 31 explicit owned cells, and seeds the existing synthetic role/appearance.
    # It writes only the new output directory. Its source helpers are unchanged.
    shared.prepare(args)
    database = args.output / 'town-diagnostic-accounts.db'
    logical20 = bytes.fromhex(args.restricted_metadata_hex)
    require(len(logical20) == 20 and int.from_bytes(logical20[:2], 'little') == args.restricted_item,
            'RESTRICTED_INSTANCE_WIDTH_OR_KEY')
    require(logical20[2] & 63 == 25, 'RESTRICTED_TWP_CLASS_REQUIRED')
    with closing(sqlite3.connect(database)) as db:
        # Keep exactly two test instances: one legal WPN and one restricted TWP.
        db.execute('DELETE FROM character_weapon_slot_metadata WHERE character_id=4 AND slot=1')
        db.execute('UPDATE diagnostic_inventory_slots SET item_id=0,count=0 WHERE character_id=4 AND slot=1')
        row = db.execute('SELECT source_line,record_sha256,raw_record,parsed_record FROM native_weapon_rows '
                         "WHERE family='TWP' AND item_id=?", (args.restricted_item,)).fetchone()
        require(row is not None and len(row[3]) == 396, 'PINNED_TWP_SOURCE_MISSING')
        source_text = row[3][0x2e:].split(b'\0')[0].decode('cp950')
        source_name = row[3][8:0x2e].split(b'\0')[0].decode('cp950')
        expected = {19071:'限男性角色裝備',19072:'限女性角色裝備'}[args.restricted_item]
        require(source_text == expected, 'TWP_SOURCE_RESTRICTION_CHANGED')
        # Slot2 is separate from the proven WPN1/2 fallback fixtures in0/1.
        db.execute('UPDATE diagnostic_inventory_slots SET item_id=?,count=1 WHERE character_id=4 AND slot=2',
                   (args.restricted_item,))
        db.execute('INSERT INTO character_weapon_slot_metadata '
            '(character_id,slot,logical20,revision,origin,provenance,source_sha256,client_sha256,design_id) '
            "VALUES(4,2,?,1,'CUSTOM_TEST_NOT_NATIVE',?,?,?,'CUSTOM-0046')",
            (logical20, 'hidden-weapon-rejection-20260927/synthetic-TWP/CUSTOM-0046',
             fixture.WEAPON_SOURCE_SHA, fixture.CURRENT_CLIENT_SHA))
        profile = db.execute('SELECT profile FROM recovered_characters WHERE id=4').fetchone()[0]
        db.commit()
        require(db.execute('SELECT item_id,count,revision FROM diagnostic_inventory_slots WHERE character_id=4 AND slot=2').fetchone()
                == (args.restricted_item,1,1), 'RESTRICTED_SCALAR_READBACK')
        require(db.execute('SELECT logical20 FROM character_weapon_slot_metadata WHERE character_id=4 AND slot=2').fetchone()[0]
                == logical20, 'RESTRICTED_METADATA_READBACK')
    config_path = args.output / 'server-config.json'
    config = json.loads(config_path.read_text('utf-8'))
    config['development']['diagnostic_town']['player_visibility'] = False
    shared.dump(config_path, config)
    shared.dump(args.output/'rejection-fixture.json', {
        'item_id':args.restricted_item, 'slot':2, 'logical20':logical20.hex(),
        'instance_origin':'CUSTOM_TEST_NOT_NATIVE', 'design_id':'CUSTOM-0046',
        'definition_source_sha256':fixture.WEAPON_SOURCE_SHA, 'source_line':row[0],
        'source_record_sha256':row[1], 'source_record_hex':row[2].hex(), 'source_restriction_text':source_text,
        'source_name':source_name,'expected_message':source_name+' 無法使用或裝備。',
        'profile_hex':profile.hex(), 'profile_sha256':hashlib.sha256(profile).hexdigest(),
        'scope':'Source restriction text is native; instance fields and fallback appearance are synthetic; no generation/formula claim'})


def worker(args):
    result = {'accepted':False, 'authority':'CUSTOM_TEST_NOT_NATIVE', 'stages':[],
              'actual_god_preservation_tested':False, 'rendered_pixels_tested':False}
    client = None
    desktop = desktop_names()
    database = args.output/'town-diagnostic-accounts.db'
    log = args.output/'server.log'
    if not args.expected_text:
        args.expected_text=json.loads((args.output/'rejection-fixture.json').read_text('utf-8'))['expected_message']
    def checkpoint(): shared.dump(args.output/'ui-result.json',result)
    try:
        require(desktop['current'].startswith('God2Lab-') and desktop['current'] != desktop['input'], 'HIDDEN_DESKTOP_REQUIRED')
        result['desktop_before'] = desktop
        process = subprocess.Popen([str(fixture.CLIENT),'127.0.0.1','127.0.0.1','6001','1'],cwd=fixture.CLIENT.parent,
            creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        client = {'process':process}; result['owned_client_pid'] = process.pid; checkpoint()
        hwnd = wait_until(lambda:shared.window_for(process.pid),35,'OWNED_CLIENT_WINDOW_MISSING')
        client['hwnd'] = hwnd
        time.sleep(2); click(hwnd,512,464); time.sleep(3)
        click(hwnd,437,232); type_ascii(hwnd,'codexslow')
        click(hwnd,437,263); type_ascii(hwnd,'labtest2345'); click(hwnd,452,304); time.sleep(4)
        click(hwnd,330,145); click(hwnd,452,413); time.sleep(4)
        click(hwnd,330,150); click(hwnd,452,376); time.sleep(4)
        click(hwnd,452,370); time.sleep(8)
        require(process.poll() is None,'OWNED_CLIENT_EXITED')
        client['handle'] = kernel.OpenProcess(0x1010,False,process.pid)
        require(client['handle'],'READONLY_PROCESS_OPEN_FAILED')
        client['ui'] = shared.find_ui(client['handle'],4)
        click(hwnd,708,584); time.sleep(2)
        handle,ui=client['handle'],client['ui']
        widget=int.from_bytes(shared.exact(handle,ui+0x232dc8,2),'little',signed=True)
        saved_before=complete_snapshot(database); native_before=native_snapshot(client)
        require(native_before['stable']['deity_count']==0,'NO_GOD_FIXTURE_REQUIRED')
        require(owned.weapon_slots_agree(owned.native_weapon_slots(handle,ui),saved_before['weapons']),'INITIAL_BAG_MISMATCH')
        require(native_before['map']=={'kind':0,'area':4,'scene':3},'KUNLUN_REQUIRED')
        result['before']={'db':saved_before,'native':native_before}; checkpoint()
        log_offset=log.stat().st_size
        message_before=native_message(client,args.expected_text)
        require(not message_before['matched'],'REFUSAL_TEXT_ALREADY_PRESENT_BEFORE_ATTEMPT')
        result['message_before']=message_before
        double_click_message(hwnd,*owned.control_point(handle,ui,widget,2))
        def refused():
            text=log.read_bytes()[log_offset:].decode('utf-8',errors='replace')
            lines=[line for line in text.splitlines() if args.rejection_marker in line and
                   f'item={args.restricted_item}' in line and 'character_id=4' in line]
            if not lines: return None
            after=complete_snapshot(database); current=native_snapshot(client)
            require(after==saved_before,'REJECTED_REQUEST_MUTATED_DATABASE')
            require(unchanged_native(native_before,current),'REJECTED_REQUEST_MUTATED_NATIVE_STATE')
            message=native_message(client,args.expected_text)
            result['last_rejection_observation']={'log_lines':lines,'message':message,'db':after,'native':current}
            if not message['matched'] or message==message_before: return None
            require(message['normal_chat']=='00','REJECTION_MESSAGE_NOT_IN_NORMAL_CHAT')
            new_rows=[]
            for previous,ring in zip(message_before['rings'],message['rings']):
                # This bounded TWP19071 message is one native row (qualified
                # full-consumer oracle). Check the actual newly written cell.
                require(ring['next']==(previous['next']+1)%200,'REJECTION_CHAT_APPEND_COUNT')
                rows=[row for row in ring['rows'] if row['index']==previous['next']]
                require(len(rows)==1 and rows[0]['channel']==4 and rows[0]['color']==0xff80ff,
                        'REJECTION_NEW_ROW_COLOR_CHANNEL_MISMATCH')
                plain=re.sub(rb'/c[0-9a-fA-F]',b'',bytes.fromhex(rows[0]['raw_hex'])).decode('cp950')
                require(args.expected_text in plain,'REJECTION_NEW_ROW_TEXT_MISMATCH')
                new_rows.append({'ring':ring['name'],**rows[0]})
            message['new_rows']=new_rows
            return {'log_lines':lines,'message':message,'all_owned_and_battle_rows_unchanged':True,
                    'all50_native_slots_stats_appearance_unchanged':True,'native':current}
        result['rejection']=wait_until(refused,12,'QUALIFIED_NATIVE_REJECTION_NOT_OBSERVED'); checkpoint()
        # A legal native28 immediately afterward must still work; then unequip.
        for step,source in enumerate((0,34),1):
            prior=owned.saved_weapons(database)
            destination=34 if source==0 else 0
            double_click_message(hwnd,*owned.control_point(handle,ui,widget,source))
            def changed():
                after=owned.saved_weapons(database)
                if not owned.weapon_after_state(prior,after,source,destination): return None
                if not owned.weapon_slots_agree(owned.native_weapon_slots(handle,ui),after): return None
                stable=owned.native(handle,ui)
                require({k:stable[k] for k in shared.STABLE_KEYS}==native_before['stable'],'LEGAL_FALLBACK_CHANGED_STATS')
                require(after['2']==saved_before['weapons']['2'],'LEGAL_FALLBACK_CHANGED_RESTRICTED_SLOT')
                appearance=owned.saved_weapon_appearance(database)
                visible=owned.native_weapon_appearance(handle,ui)
                if appearance['revision']!=step+1 or visible['logical_hex']!=appearance['logical_hex']:return None
                owned.check_weapon_appearance(appearance,visible,saved_before['appearance'],native_before['appearance'],
                    1 if source==0 else 0,step+1)
                return {'source':source,'destination':destination,'db':after,'native_slots':owned.native_weapon_slots(handle,ui),
                        'appearance':appearance,'native_appearance':visible}
            result['stages'].append(wait_until(changed,12,f'LEGAL_FALLBACK_{step}_FAILED')); checkpoint()
        final=complete_snapshot(database)
        for key in ('related','battle_reservations','battle_settlements','battle_checkpoints','position'):
            require(final[key]==saved_before[key],f'FINAL_UNRELATED_STATE_{key}')
        result['final_db']=final; result['accepted']=True
    except Exception as error:
        result['error']=f'{type(error).__name__}: {error}'; result['traceback']=traceback.format_exc()
    finally:
        if client:
            try: shared.close_client(client)
            except Exception as error: result['cleanup_error']=str(error)
        result['desktop_after']=desktop_names()
        result['all_owned_clients_closed']=client is None or client['process'].poll() is not None
        result['accepted']=bool(result['accepted'] and result['desktop_after']==desktop and result['all_owned_clients_closed'] and not result.get('cleanup_error'))
        checkpoint()
    return 0 if result['accepted'] else 1


def owner(args):
    args.output=args.output.resolve(); args.server_candidate=args.server_candidate.resolve()
    paths={'source_db':fixture.SOURCE_DB,'live_client':fixture.LIVE_CLIENT,'private_client':fixture.CLIENT}
    result={'accepted':False,'before':{key:fixture.sha(path) for key,path in paths.items()},
            'server_sha256':fixture.sha(args.server_candidate)}
    server=runner=None
    try:
        with socket.socket() as probe:
            require(probe.connect_ex(('127.0.0.1',2598))!=0,'PRIVATE_PORT_ALREADY_IN_USE')
        prepare(args)
        if args.prepare_only:
            result['prepared_only']=True
        else:
            env=os.environ.copy(); env['GOD2_LOG_FILE_ONLY']='1'; env.pop('GOD2_PRIVATE_SIDECAR_COMMAND',None)
            with (args.output/'stdout.log').open('wb') as log, (args.output/'runner.log').open('wb') as runner_log:
                server=subprocess.Popen([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--run-for','160'],
                    cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                result['server_pid']=server.pid
                def listening():
                    require(server.poll() is None,'SERVER_EXITED')
                    with socket.socket() as probe:return probe.connect_ex(('127.0.0.1',2598))==0
                wait_until(listening,10,'SERVER_NOT_LISTENING')
                command=[str(fixture.RUNNER),sys.executable,'-X','utf8','-B',str(Path(__file__).resolve()),'--worker',
                    '--output',str(args.output),'--restricted-item',str(args.restricted_item),
                    '--rejection-marker',args.rejection_marker]
                if args.expected_text:command.extend(['--expected-text',args.expected_text])
                runner=subprocess.Popen(command,cwd=ROOT,env=env,stdout=runner_log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                result['runner_pid']=runner.pid; result['runner_exit']=runner.wait(timeout=130)
                result['ui']=json.loads((args.output/'ui-result.json').read_text('utf-8'))
                result['accepted']=result['runner_exit']==0 and result['ui']['accepted']
    except Exception as error: result['error']=f'{type(error).__name__}: {error}'
    finally:
        for process in (runner,server):
            if process is not None and process.poll() is None:
                children=psutil.Process(process.pid).children(recursive=True)
                for child in reversed(children):
                    try:child.terminate()
                    except psutil.NoSuchProcess:pass
                process.terminate(); process.wait(timeout=5)
                _,alive=psutil.wait_procs(children,timeout=5)
                for child in alive:child.kill(); child.wait(timeout=5)
        result['source_files_unchanged']={key:fixture.sha(path)==result['before'][key] for key,path in paths.items()}
        result['accepted']=bool(result['accepted'] and all(result['source_files_unchanged'].values()))
        if args.output.exists():shared.dump(args.output/'run-result.json',result)
    print(json.dumps({'accepted':result['accepted'],'prepared_only':result.get('prepared_only',False),'error':result.get('error')}))
    return 0 if (result['accepted'] or result.get('prepared_only')) and all(result['source_files_unchanged'].values()) else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--server-candidate',type=Path)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--restricted-item',type=int,choices=(19071,19072),default=19071)
    parser.add_argument('--restricted-metadata-hex',default=(struct.pack('<HH',19071,25)+bytes(16)).hex())
    parser.add_argument('--rejection-marker',default='OWNED_WEAPON_SOURCE_SEX_REJECTED')
    parser.add_argument('--expected-text',default='')
    args=parser.parse_args()
    if args.worker:return worker(args)
    if args.server_candidate is None:parser.error('--server-candidate required')
    return owner(args)


if __name__=='__main__':raise SystemExit(main())
