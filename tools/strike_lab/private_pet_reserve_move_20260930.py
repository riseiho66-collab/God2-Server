"""Owned hidden-desktop native24 reserve reorder and reconnect acceptance.

Uses the established private runner and window-local input helpers under the
owner's explicit internal-sandbox automation instruction. No foreground/desktop
switch, screenshots, packet injection or process-memory writes. Test instances
are retained synthetic operands in a disposable database clone.
"""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import struct
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]
import psutil
import private_weapon_peer_appearance_20260927 as shared
import private_owned_companions_ui as owned
import private_owned_supply_20260927 as supply
import private_daily_quest_20260927 as daily
from tools.strike_lab import run_private_owned_companions as fixture
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,drag,type_ascii

SOURCE=ROOT/'artifacts/playtests/private-pet1-mixed-20260927-02/town-diagnostic-accounts.db'
LIVE=ROOT.parent/'God2/God2.exe'
PIN='9be38ef858bc9c63b6f296cae4a8e601ddcfaf614700e725c4bec44065b53336'
RUNNER_PIN='8a4bd51dcf48753f5934fb1088d4aac10603ad8506ecc988a07d83febe878ef4'
PORT=2598


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(client):
    state=owned.native(client['handle'],client['ui']);state.pop('world_clock')
    return {'state':state,'all50':shared.exact(client['handle'],client['ui']+0x8560c,1200).hex()}


def unrelated(value):
    copy=json.loads(json.dumps(value))
    for group in ('pet_slots','pet_cache','pet1_cache'):
        for slot in ('42','43'):copy['state'][group].pop(slot)
    slots=bytearray.fromhex(copy['all50']);slots[42*24:44*24]=bytes(48)
    copy['all50']=slots.hex();return copy


def unchanged_db(value):
    out=dict(value);out['character_pet2_slots']=[r for r in out['character_pet2_slots'] if r[0]!=4 or r[1] not in (42,43)]
    return out


def check_owned(client,database):
    actual=snapshot(client);saved=owned.saved(database)
    require(owned.agrees(actual['state'],saved),'NATIVE_OWNED_PET_RECORDS_DISAGREE')
    return actual


def role_native(client):
    handle,ui=client['handle'],client['ui']
    def uint(address,count):return int.from_bytes(shared.exact(handle,address,count),'little')
    actor=uint(ui+0x86888,4);localroot=actor-0x90;world=localroot-0x1539683c
    require(uint(ui+0x86884,4)==world+0x39c,'ROLE_WORLD_RENDERER_BASE_DISAGREES')
    index=uint(localroot+0x4544,2)
    require(index<400,'ROLE_RENDERER_INDEX_OUT_OF_RANGE')
    return {'actor':actor,'renderer_index':index,
        'actor_text':shared.exact(handle,actor+0x37,16).split(b'\0',1)[0].decode('ascii'),
        'renderer_text':shared.exact(handle,world+0x39c+index*0xa7e0+0x81,17).split(b'\0',1)[0].decode('ascii'),
        'widget7_static':shared.exact(handle,0x596e54,16).split(b'\0',1)[0].decode('ascii')}


def role_row(database):
    with closing(shared.ro(database)) as db:
        row=db.execute('select hex(legacy_text),utf8_text,codepage,revision,origin,source_sha256,design_id from character_role_text where character_id=4').fetchone()
    return list(row) if row else None


def enter_role_text(client,database,log):
    text='RoleNativeProof';require(len(text)==15,'ROLE_TEST_TEXT_LENGTH')
    handle,ui=client['handle'],client['ui']
    def uint(address,count):return int.from_bytes(shared.exact(handle,address,count),'little')
    before=role_row(database);require(before is None,'ROLE_TEST_REQUIRES_UNSET_TEXT')
    hud=uint(ui+0x232db6,2);require(hud<128,'HUD_WIDGET_UNAVAILABLE')
    open_point=owned.control_point(handle,ui,hud,5);click(client['hwnd'],*open_point)
    def role_open():
        widget=uint(ui+0x232dda,2)
        if widget>=128:return None
        return widget if uint(ui+0xe2988+widget*0x2a08,4)&0x20 and uint(ui+0x5bfa4,2)==2 else None
    widget=wait_until(role_open,5,'ROLE_PANEL_INPUT_MODE_NOT_OPENED')
    close_point=owned.control_point(handle,ui,widget,0x10)
    # The panel-open path already selects text mode2 and its native caret27;
    # that caret is not a mouse hit rectangle. Type through the selected mode.
    type_ascii(client['hwnd'],'\b'*16+text);time.sleep(.5)
    offset=log.stat().st_size;click(client['hwnd'],*close_point)
    def saved():
        row=role_row(database)
        if row is None:return None
        require(row[:5]==[(text.encode()+b'\0').hex().upper(),text,950,1,'CUSTOM_DESIGNED'],'ROLE_TEXT_SAVED_ROW_MISMATCH')
        require(row[6]=='CUSTOM-0056','ROLE_TEXT_WRONG_DESIGN')
        if 'OWNED_ROLE_TEXT_SAVED' not in log.read_bytes()[offset:].decode('utf-8',errors='replace'):return None
        actual=role_native(client)
        if actual['actor_text']!=text or actual['renderer_text']!=text:return None
        return {'expected':text,'before':before,'saved':row,'native_after':actual,'native20_ui_send_observed':True,
            'ui_points':{'open':open_point,'input_mode':2,'close':close_point}}
    return wait_until(saved,8,'ROLE_TEXT_NATIVE20_SAVE_OR23_REPLY_NOT_OBSERVED')


def worker(args):
    fixture.CLIENT=args.client.resolve()
    result={'accepted':False,'stages':[],'owned_client_pids':[],'rendered_pixels_tested':False}
    desktop=desktop_names();client=None;database=args.output/'town-diagnostic-accounts.db';log=args.output/'server.log'
    def save():shared.dump(args.output/'ui-result.json',result)
    try:
        require(desktop['current'].startswith('God2Lab-') and desktop['current']!=desktop['input'],'HIDDEN_DESKTOP_REQUIRED')
        result['desktop_before']=desktop
        client=supply.login();result['owned_client_pids'].append(client['process'].pid)
        before=daily.stable_database(database);native=check_owned(client,database)
        rows={r[1]:r for r in before['character_pet2_slots'] if r[0]==4}
        require(rows[42][3].startswith('fb') and rows[43][3].startswith('e3') and rows[44][3].startswith('fb'),'MIXED_ACTIVE_CONTROL_REQUIRED')
        require(native['state']['deity_count']>0,'SAVED_GOD_CONTROL_REQUIRED')
        result['before']={'db':before,'native':native};save()
        click(client['hwnd'],708,584);time.sleep(1)
        widget=int.from_bytes(shared.exact(client['handle'],client['ui']+0x232dc8,2),'little',signed=True)
        require(0<=widget<128,'INVENTORY_WIDGET_UNAVAILABLE')
        points={slot:owned.control_point(client['handle'],client['ui'],widget,slot) for slot in (42,43)}
        result['points']=points
        for source,destination in ((42,43),(43,42)):
            prior=daily.stable_database(database);previous={r[1]:r for r in prior['character_pet2_slots'] if r[0]==4}
            offset=log.stat().st_size;drag(client['hwnd'],points[source],points[destination])
            def observed():
                after=daily.stable_database(database);current=snapshot(client)
                result['last_observed']={'db':after,'native':current}
                lines=log.read_bytes()[offset:].decode('utf-8',errors='replace')
                if f'source={source} destination={destination} changed=true' not in lines:return None
                if not owned.agrees(current['state'],owned.saved(database)):return None
                actual={r[1]:r for r in after['character_pet2_slots'] if r[0]==4}
                for slot,donor in ((source,destination),(destination,source)):
                    expected=list(previous[donor]);expected[1]=slot;expected[4]=previous[slot][4]+1
                    raw=bytearray.fromhex(expected[3]);raw[0x27 if raw[0]==0xe3 else 3]=slot;expected[3]=raw.hex()
                    require(actual[slot]==expected,'FULL_INSTANCE_SWAP_OR_PROVENANCE_MISMATCH')
                    opposite='pet_cache' if raw[0]==0xe3 else 'pet1_cache'
                    require(current['state'][opposite][str(slot)]==bytes(72 if raw[0]==0xe3 else 52).hex(),'OLD_FAMILY_CACHE_NOT_CLEARED')
                require(unrelated(current)==unrelated(native),'UNRELATED_NATIVE_STATE_CHANGED')
                require(unchanged_db(after)==unchanged_db(before),'UNRELATED_SAVED_STATE_CHANGED')
                require(client['process'].poll() is None,'CLIENT_EXITED')
                return {'source':source,'destination':destination,'db':after,'native':current,'native24_observed':True}
            result['stages'].append(wait_until(observed,12,'RESERVE_NATIVE24_NOT_ACCEPTED'));save()
        persisted=daily.stable_database(database);final=check_owned(client,database)
        if args.role_text:
            result['role_text']=enter_role_text(client,database,log);save()
        shared.close_client(client);client=None;time.sleep(1)
        client=supply.login();result['owned_client_pids'].append(client['process'].pid)
        restored=check_owned(client,database)
        require(daily.stable_database(database)==persisted,'RECONNECT_CHANGED_SAVED_RECORDS')
        require(restored['all50']==final['all50'],'RECONNECT_INVENTORY_METADATA_CHANGED')
        for key in ('role_resources','role_auxiliary','deity_count','deity_selected_key','deity_keys','deity_vitals'):
            require(restored['state'][key]==final['state'][key],'RECONNECT_CONTROL_CHANGED_'+key)
        require(restored['state']['pet_cache']['44']==final['state']['pet_cache']['44'],'RECONNECT_ACTIVE_PET_CHANGED')
        result['reconnect']={'saved_unchanged':True,'native':restored,'inactive_opposite_caches_not_compared_across_processes':True}
        if args.role_text:
            actual=role_native(client);expected=result['role_text']['expected']
            require(role_row(database)==result['role_text']['saved'],'ROLE_TEXT_RECONNECT_CHANGED_SAVED_ROW')
            require(actual['actor_text']==expected and actual['renderer_text']==expected,'ROLE_TEXT_NATIVE23_RECONNECT_NOT_RESTORED')
            require('OWNED_ROLE_TEXT_RESTORED' in log.read_text('utf-8',errors='replace'),'ROLE_TEXT_RESTORE_LOG_MISSING')
            result['role_text']['reconnect']={'native':actual,'saved_unchanged':True,'native23_receive_observed':True}
        require(log.read_text('utf-8',errors='replace').count('OWNED_PET_RESERVE_MOVE')==2,'UNEXPECTED_RESERVE_TRANSACTION_COUNT')
        result['accepted']=True
    except Exception as error:result['error']=str(error);result['traceback']=traceback.format_exc()
    finally:
        if client:
            try:shared.close_client(client)
            except Exception as error:result['cleanup_error']=str(error)
        result['desktop_after']=desktop_names();result['desktop_unchanged']=desktop==result['desktop_after']
        result['all_clients_closed']=not any(psutil.pid_exists(pid) for pid in result['owned_client_pids'])
        result['accepted']=bool(result['accepted'] and result['desktop_unchanged'] and result['all_clients_closed'] and not result.get('cleanup_error'));save()
    return 0 if result['accepted'] else 1


def prepare(args):
    require(sha(LIVE)==PIN,'CURRENT_CLIENT_PIN_CHANGED')
    require(sha(fixture.RUNNER)==RUNNER_PIN,'HIDDEN_RUNNER_CHANGED')
    args.output.mkdir(parents=True,exist_ok=False)
    require(not args.client.exists() and args.client.parent.resolve()==LIVE.parent.resolve() and args.client.resolve()!=LIVE.resolve(),'NEW_PRIVATE_CLIENT_REQUIRED')
    original=LIVE.read_bytes();site=bytes.fromhex('68 20 0a 00 00 68 9c 47 5b 00')
    require(original.count(site)==1,'PORT_SITE_NOT_UNIQUE')
    at=original.index(site)+1;changed=bytearray(original);changed[at:at+4]=struct.pack('<I',PORT)
    require(sum(a!=b for a,b in zip(original,changed))<=4,'NONPORT_CLIENT_CHANGE')
    with args.client.open('xb') as output:output.write(changed)
    shared.dump(args.output/'client-copy.json',{'source':str(LIVE),'source_sha256':PIN,'copy':str(args.client),
        'copy_sha256':sha(args.client),'port':PORT,'port_file_offset':at,'changed_offsets':[i for i,(a,b) in enumerate(zip(original,changed)) if a!=b]})
    database=args.output/'town-diagnostic-accounts.db'
    with closing(shared.ro(SOURCE)) as source,closing(sqlite3.connect(database)) as target:source.backup(target)
    config=json.loads(SOURCE.with_name('server-config.json').read_text('utf-8'))
    config['database']['path']=str(database);config['logging']['file']=str(args.output/'server.log')
    config['server'].update(host='127.0.0.1',port=PORT,character_port=0)
    config['development']['diagnostic_town']['player_visibility']=False
    cfg=args.output/'server-config.json';shared.dump(cfg,config)
    env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1';env.pop('GOD2_PRIVATE_SIDECAR_COMMAND',None)
    with (args.output/'migration.log').open('wb') as output:
        subprocess.run([str(args.server_candidate),'--config',str(cfg),'--migrate-only'],cwd=ROOT,env=env,
            stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,check=True,timeout=30)
    with closing(sqlite3.connect(database)) as db:
        db.execute('delete from character_deity_selection where character_id=4')
        db.execute('delete from character_deities where character_id=4 and row_key=100')
        db.execute('insert into character_deity_selection values(4,101,1)')
        meta,stats,source,authority,evidence=db.execute('select metadata,stats,source_sha256,authority,evidence_id from character_pet2_slots where character_id=4 and slot=42').fetchone()
        raw=bytearray(stats);require(raw[0]==0xfb and len(meta)==20,'ACTIVE_CONTROL_SOURCE');raw[3]=44
        db.execute('update character_pet2_slots set metadata=?,stats=?,revision=1,source_sha256=?,authority=?,evidence_id=? where character_id=4 and slot=44',
            (meta,bytes(raw),source,authority,evidence+'-reserve-active-control'))
        db.commit();require(db.execute('pragma quick_check').fetchone()==('ok',),'CLONE_INTEGRITY')
    shared.dump(args.output/'fixture.json',{'source_database':str(SOURCE),'source_sha256':sha(SOURCE),
        'authority':'CUSTOM_TEST_NOT_NATIVE','active44':'Explicit synthetic preserved control copied from qualified fixture FB',
        'saved':daily.stable_database(database)})


def owner(args):
    args.output=args.output.resolve();args.client=args.client.resolve();args.server_candidate=args.server_candidate.resolve()
    sources={'source_database':SOURCE,'live_client':LIVE,'source_config':SOURCE.with_name('server-config.json')}
    result={'accepted':False,'before':{k:sha(v) for k,v in sources.items()},'candidate_sha256':sha(args.server_candidate)}
    server=runner=None
    try:
        with socket.socket() as probe:require(probe.connect_ex(('127.0.0.1',PORT))!=0,'PRIVATE_PORT_ALREADY_IN_USE')
        prepare(args);result['client_copy_sha256']=sha(args.client)
        env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1';env.pop('GOD2_PRIVATE_SIDECAR_COMMAND',None)
        with (args.output/'stdout.log').open('wb') as stdout,(args.output/'runner.log').open('wb') as runnerlog:
            server=subprocess.Popen([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--run-for','180'],cwd=ROOT,
                env=env,stdout=stdout,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            result['server_pid']=server.pid
            def listening():
                require(server.poll() is None,'SERVER_EXITED')
                with socket.socket() as probe:return probe.connect_ex(('127.0.0.1',PORT))==0
            wait_until(listening,10,'SERVER_DID_NOT_LISTEN')
            command=[str(fixture.RUNNER),sys.executable,'-X','utf8','-B',str(Path(__file__).resolve()),'--worker','--output',str(args.output),'--client',str(args.client)]
            if args.role_text:command.append('--role-text')
            runner=subprocess.Popen(command,cwd=ROOT,env=env,stdout=runnerlog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            result['runner_pid']=runner.pid;result['runner_exit']=runner.wait(timeout=160)
            result['ui']=json.loads((args.output/'ui-result.json').read_text('utf-8'))
            result['accepted']=runner.returncode==0 and result['ui']['accepted']
    except Exception as error:result['error']=str(error);result['traceback']=traceback.format_exc()
    finally:
        for process in (runner,server):
            if process is not None and process.poll() is None:
                children=psutil.Process(process.pid).children(recursive=True)
                for child in reversed(children):
                    try:child.terminate()
                    except psutil.NoSuchProcess:pass
                process.terminate();process.wait(timeout=5);_,alive=psutil.wait_procs(children,timeout=5)
                for child in alive:child.kill();child.wait(timeout=5)
        result['after']={k:sha(v) for k,v in sources.items()}
        result['source_files_unchanged']=result['before']==result['after']
        result['candidate_unchanged']=sha(args.server_candidate)==result['candidate_sha256']
        result['copy_unchanged']=args.client.exists() and sha(args.client)==result.get('client_copy_sha256')
        result['all_owned_processes_closed']=(runner is None or runner.poll() is not None) and (server is None or server.poll() is not None)
        result['accepted']=bool(result['accepted'] and result['source_files_unchanged'] and result['candidate_unchanged'] and result['copy_unchanged'] and result['all_owned_processes_closed'])
        if args.output.exists():shared.dump(args.output/'run-result.json',result)
    print(json.dumps({k:result.get(k) for k in ('accepted','error','candidate_sha256','source_files_unchanged','all_owned_processes_closed')}))
    return 0 if result['accepted'] else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--client',type=Path,required=True);parser.add_argument('--server-candidate',type=Path)
    parser.add_argument('--role-text',action='store_true',help='Also accept native role20 input and23 restoration through owned hidden UI')
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS);args=parser.parse_args()
    if args.worker:return worker(args)
    if args.server_candidate is None:parser.error('--server-candidate required')
    return owner(args)


if __name__=='__main__':raise SystemExit(main())
