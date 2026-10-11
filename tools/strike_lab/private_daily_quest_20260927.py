"""Isolated native daily-list UI acceptance, never quest/reward authority.

Availability/count/status bytes are explicit CUSTOM fixture operands. The
native FD subtype2 buffer has forty entries: source catalog85 is not capacity85.
Client interaction is confined to an owned hidden desktop; no screenshots,
desktop switches, injections, or process-memory writes are used.
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

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import psutil
import private_weapon_peer_appearance_20260927 as shared
from tools.strike_lab import run_private_owned_companions as fixture
import private_owned_companions_ui as owned
from private_inventory_memory import kernel
from private_inventory_move_ui import desktop_names,wait_until,require
from private_potion_ui import click,type_ascii

DAILY_SHA='4a347d56706946d7004b2bd2118500ffc60844628fa461862b2f6d5320a90e54'


def validate_issued(raw):
    """Validate before any fixture import or client launch, including capacity."""
    require(len(raw)==172 and raw[:4]==bytes((0xfd,172,0,2)),'DAILY_FIXED_FRAME_MISMATCH')
    count=raw[164]
    require(0<count<=40,'DAILY_NATIVE_CAPACITY_EXCEEDED_OR_EMPTY_FIXTURE')
    rows=[list(raw[4+i*4:8+i*4]) for i in range(count)]
    require(len({tuple(row[:2]) for row in rows})==count,'DAILY_DUPLICATE_SOURCE_BINDING')
    return rows


def panel_state(client):
    handle,ui=client['handle'],client['ui']
    panel=int.from_bytes(shared.exact(handle,ui+0x232ebc,4),'little')
    require(panel>0x10000 and shared.exact(handle,panel+0xdc,4)==struct.pack('<I',ui),'DAILY_PANEL_OWNER_MISMATCH')
    page,pages,count=struct.unpack('<IIH',shared.exact(handle,panel+0x20f28,10))
    require(count<=40,'DAILY_NATIVE_PANEL_BOUNDS')
    rows=shared.exact(handle,panel+0x20f32,160)
    widget=int.from_bytes(shared.exact(handle,ui+0x232e00,2),'little',signed=True)
    require(0<=widget<128,'DAILY_WIDGET_ID_INVALID')
    node=ui+0xe2170+0x818+widget*0x2a08
    flags,renderer=struct.unpack('<H2xh',shared.exact(handle,node,6))
    if flags&0x28:require(pages>=1 and 0<=page<pages,'DAILY_NATIVE_PAGE_BOUNDS')
    require(0<=renderer<4096,'DAILY_RENDERER_HANDLE_INVALID')
    footer=shared.exact(handle,panel+0x20fd4,12)
    return {'panel':hex(panel),'widget':widget,'node':hex(node),'flags':flags,'renderer':renderer,
            'open':bool(flags&0x28),'page':page,'pages':pages,'count':count,
            'rows':[list(rows[i*4:i*4+4]) for i in range(count)],'all40_hex':rows.hex(),
            'footer':{'low_item':int.from_bytes(footer[:2],'little'),'low_mode':footer[2],
                      'value':int.from_bytes(footer[4:8],'little'),
                      'high_item':int.from_bytes(footer[8:10],'little'),'high_mode':footer[10]},
            'request_buffer':shared.exact(handle,panel+0x20fe4,8).hex()}


def check_panel(state,logical,page=0,opened=True):
    rows=validate_issued(logical)
    require(state['open']==opened,'DAILY_OPEN_STATE_MISMATCH')
    require(state['rows']==rows and state['count']==len(rows),'DAILY_ISSUED_ROWS_MISMATCH')
    require(state['page']==page and state['pages']==max(1,(len(rows)+7)//8),'DAILY_PAGING_MISMATCH')
    require(state['footer']=={'low_item':int.from_bytes(logical[166:168],'little'),
        'low_mode':logical[165]&15,'value':int.from_bytes(logical[168:170],'little'),
        'high_item':int.from_bytes(logical[170:172],'little'),'high_mode':logical[165]>>4},'DAILY_FOOTER_MISMATCH')


def text_cell(client,state,column,row):
    """Read the actual 506390->41E2B0->426700->426140 display text cell."""
    require(0<=column<4 and 0<=row<8,'DAILY_TEXT_CELL_BOUNDS')
    handle,ui=client['handle'],client['ui']
    graphics=int.from_bytes(shared.exact(handle,ui+0xcff60,4),'little')
    require(graphics>0x10000,'DAILY_GRAPHICS_POINTER_MISSING')
    node=graphics+0x10+state['renderer']*0x290
    sprite=int.from_bytes(shared.exact(handle,node+0xac+column*2,2),'little')
    require(sprite<5000,'DAILY_GRID_SPRITE_MISSING')
    pool=int.from_bytes(shared.exact(handle,graphics+4,4),'little')
    index=int.from_bytes(shared.exact(handle,pool+0x1264+sprite*200+row*2,2),'little',signed=True)
    require(index>=0,'DAILY_TEXT_ENTRY_UNBOUND')
    address=pool+0xf66e4+index*0x8c
    raw=shared.exact(handle,address,0x8c)
    string=raw[0xc:].split(b'\0')[0]
    return {'column':column,'row':row,'sprite':sprite,'text_index':index,'address':hex(address),
            'record_hex':raw.hex(),'text_hex':string.hex(),'text':string.decode('cp950',errors='replace')}


def source_texts(client,state,sources):
    cells=[[text_cell(client,state,col,row) for col in range(4)] for row in range(8)]
    first=state['page']*8
    for row in range(8):
        if first+row<len(sources):
            name=bytes.fromhex(sources[first+row]['name_hex'])
            require(name and name in bytes.fromhex(cells[row][1]['text_hex']),'DAILY_RENDERED_SOURCE_NAME_MISMATCH')
        else:
            require(all(not cell['text_hex'] for cell in cells[row]),'DAILY_PAGE_RETAINED_OLD_ROW_TEXT')
    return cells


def stable_native(client):
    value=owned.native(client['handle'],client['ui'])
    return {'state':{key:value[key] for key in (*shared.STABLE_KEYS,'quest_journal','world_map')},
            'all50_slots':shared.exact(client['handle'],client['ui']+0x8560c,1200).hex(),
            'appearance':owned.native_weapon_appearance(client['handle'],client['ui'])['logical_hex']}


def stable_database(database):
    """Gameplay persistence must not change merely because a list is clicked."""
    tables=('recovered_positions','character_resources','character_role_snapshots',
        'character_role_auxiliary_snapshots','character_experience','character_quest_journals',
        'character_deities','character_deity_selection','character_pet2_slots',
        'diagnostic_inventory_slots','character_weapon_slot_metadata',
        'character_player_appearance_snapshots','battle_reservations','battle_settlements','battle_checkpoints')
    with closing(shared.ro(database)) as connection:
        present={r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        result={}
        for table in tables:
            if table not in present:continue
            rows=connection.execute(f'SELECT * FROM {table} ORDER BY 1').fetchall()
            result[table]=[[value.hex() if isinstance(value,bytes) else value for value in row] for row in rows]
        return result


def expected_selection(row,side,tail):
    require(side in (1,2),'DAILY_SELECTION_SIDE')
    npc=row['start_npc'] if side==1 else row['end_npc']
    require(0<=row['index']<=255 and 0<=row['branch']<=255 and 0<=npc<=65535,'DAILY_SOURCE_BINDING_WIDTH')
    return bytes((0xd8,1,row['index'],row['branch'],0xff,npc&255,npc>>8,side,tail))


def login():
    process=subprocess.Popen([str(fixture.CLIENT),'127.0.0.1','127.0.0.1','6001','1'],cwd=fixture.CLIENT.parent,
        creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    client={'process':process}
    try:
        hwnd=wait_until(lambda:shared.window_for(process.pid),35,'OWNED_CLIENT_WINDOW_MISSING')
        client['hwnd']=hwnd
        time.sleep(2);click(hwnd,512,464);time.sleep(3)
        click(hwnd,437,232);type_ascii(hwnd,'codexslow');click(hwnd,437,263);type_ascii(hwnd,'labtest2345')
        click(hwnd,452,304);time.sleep(4);click(hwnd,330,145);click(hwnd,452,413);time.sleep(4)
        click(hwnd,330,150);click(hwnd,452,376);time.sleep(4);click(hwnd,452,370);time.sleep(8)
        require(process.poll() is None,'OWNED_CLIENT_EXITED')
        client['handle']=kernel.OpenProcess(0x1010,False,process.pid)
        require(client['handle'],'READONLY_PROCESS_OPEN_FAILED')
        client['ui']=shared.find_ui(client['handle'],4)
        return client
    except BaseException:
        shared.close_client(client)
        raise


def open_daily(client):
    """Native HUD8 -> action category0 -> action12 -> D7 00."""
    handle,ui,hwnd=client['handle'],client['ui'],client['hwnd']
    def widget(offset):
        index=int.from_bytes(shared.exact(handle,ui+offset,2),'little',signed=True)
        require(0<=index<128,'DAILY_MENU_WIDGET_INVALID')
        return index
    menu=widget(0x232e4e)
    node=ui+0xe2988+menu*0x2a08
    if not shared.exact(handle,node,1)[0]&0x28:
        click(hwnd,*owned.control_point(handle,ui,widget(0x232db6),8))
    wait_until(lambda:shared.exact(handle,node,1)[0]&0x28,5,'NATIVE_ACTION_MENU_NOT_OPEN')
    click(hwnd,*owned.control_point(handle,ui,menu,0x16))
    wait_until(lambda:shared.exact(handle,ui+0xa3cf4,2)==struct.pack('<H',0x16),3,'NATIVE_ACTION_CATEGORY_NOT_ZERO')
    point=owned.control_point(handle,ui,menu,0x27)
    click(hwnd,*point)
    return {'hud_widget':widget(0x232db6),'menu_widget':menu,'menu_control':0x27,'point':point,
            'native_path':'4820A0/4B1660 ctrl8 -> 4A65B0 -> 4A6D90 ctrl27 release20 -> 4A6760(0,12) -> D700'}


def owned_list(database):
    with closing(shared.ro(database)) as db:
        row=db.execute('SELECT logical,revision,origin,provenance,client_sha256,design_id FROM character_daily_quest_lists WHERE character_id=4').fetchone()
    require(row is not None,'OWNED_DAILY_LIST_MISSING')
    return [v.hex() if isinstance(v,bytes) else v for v in row]


def prepare(args):
    args.output.mkdir(parents=True,exist_ok=False)
    require(fixture.sha(fixture.LIVE_CLIENT)==fixture.CURRENT_CLIENT_SHA,'CURRENT_CLIENT_PIN')
    original=fixture.LIVE_CLIENT.read_bytes();private=fixture.CLIENT.read_bytes()
    site=original.index(bytes.fromhex('68 20 0a 00 00 68 9c 47 5b 00'))
    expected=bytearray(original);expected[site+1:site+5]=struct.pack('<I',2598)
    require(private==expected,'PRIVATE_CLIENT_NOT_EXACT_PORT_COPY')
    database=args.output/'town-diagnostic-accounts.db'
    with closing(shared.ro(fixture.SOURCE_DB)) as source,closing(sqlite3.connect(database)) as target:source.backup(target)
    config=json.loads(fixture.CONFIG.read_text('utf-8'))
    config['database']['path']=str(database);config['logging']['file']=str(args.output/'server.log')
    config['server']['host']='127.0.0.1';config['server']['port']=2598
    dev=config['development']
    for key,value in list(dev.items()):
        if key.startswith('diagnostic_') and isinstance(value,bool):dev[key]=False
    dev['diagnostic_town'].update(spawn_guides=True,quest_progress=False,map_probe=False,player_visibility=False,
        battle_after_quest=False,door_after_battle=False,native_npc_placements_only=True)
    dev['native_monster_placements_only']=True
    config['world']={'new_character_birthplace':{'area':4,'scene':3,'kind':0,'x':126,'y':126,
        'navigation':str(ROOT/'artifacts/world-atlas/kunlun-4-3.json'),'coordinate_authority':'CUSTOM-0040'},
        'clock':{'enabled':True,'sync_seconds':5},'owned_daily_quest_views':{'enabled':True}}
    shared.dump(args.output/'server-config.json',config)
    env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1'
    with (args.output/'migration.log').open('wb') as log:
        subprocess.run([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--migrate-only'],
            cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,check=True,timeout=20)
    from tools.strike_lab import import_native_quests,import_native_quest_sources,import_native_daily_quest_parsed
    with closing(sqlite3.connect(database)) as db:
        imports={'descriptions':import_native_quests.import_catalog(db,fixture.LIVE_CLIENT.parent),
                 'source':import_native_quest_sources.import_catalog(db,fixture.LIVE_CLIENT.parent),
                 'typed_daily':import_native_daily_quest_parsed.import_catalog(db,fixture.LIVE_CLIENT.parent)}
        selected=db.execute('SELECT ordinal,source_line,pair_index,pair_branch,logical,source_record_sha256 '
            'FROM native_daily_quest_parsed ORDER BY ordinal LIMIT 9').fetchall()
        require(len(selected)==9,'DAILY_FIXTURE_SOURCE_COUNT')
        logical=bytearray(172);logical[:4]=bytes((0xfd,172,0,2));logical[164]=9
        sources=[]
        for i,(ordinal,line,index,branch,parsed,source_hash) in enumerate(selected):
            require(len(parsed)==316 and parsed[:2]==bytes((index,branch)),'DAILY_TYPED_SOURCE_BINDING')
            logical[4+4*i:8+4*i]=bytes((index,branch,0,0x41 if i<8 else 0))
            sources.append({'ordinal':ordinal,'source_line':line,'index':index,'branch':branch,
                'name_hex':parsed[20:50].split(b'\0')[0].hex(),'start_npc':int.from_bytes(parsed[2:4],'little'),
                'end_npc':int.from_bytes(parsed[4:6],'little'),'source_record_sha256':source_hash,
                'parsed316_hex':parsed.hex(),'availability_origin':'CUSTOM_TEST_NOT_NATIVE'})
        validate_issued(logical)
        db.execute('INSERT INTO character_daily_quest_lists '
            '(character_id,logical,revision,origin,provenance,client_sha256,design_id) '
            "VALUES(4,?,1,'CUSTOM_TEST_NOT_NATIVE','hidden-daily-panel-20260927/source-display-only',?,'CUSTOM-0049')",
            (bytes(logical),fixture.CURRENT_CLIENT_SHA))
        db.execute('DELETE FROM recovered_positions WHERE character_id=4')
        db.execute('INSERT INTO character_resources VALUES(4,52,120,26,80,1,?)',('CUSTOM-0012',))
        role=bytearray(25);role[0]=0x22;role[1]=1
        struct.pack_into('<4H',role,5,10,10,10,10);struct.pack_into('<II',role,17,120,80)
        db.execute('INSERT INTO character_role_snapshots VALUES(4,?,1,?)',(bytes(role),'CUSTOM-0013'))
        for table in ('character_deity_selection','character_deities','character_pet2_slots'):
            db.execute(f'DELETE FROM {table} WHERE character_id=4')
        db.commit()
        require(db.execute('PRAGMA quick_check').fetchone()==('ok',),'DAILY_CLONE_INTEGRITY')
        require(db.execute('SELECT logical FROM character_daily_quest_lists WHERE character_id=4').fetchone()[0]==bytes(logical),'DAILY_OWNED_LIST_READBACK')
    shared.dump(args.output/'fixture.json',{'logical_hex':logical.hex(),'sources':sources,'imports':imports,
        'source_sha256':DAILY_SHA,'availability_origin':'CUSTOM_TEST_NOT_NATIVE','design_id':'CUSTOM-0049',
        'executable_quest_rules':False,'no_rewards_no_teleports_no_item_consumption':True})


def worker(args):
    result={'accepted':False,'stages':[],'availability_origin':'CUSTOM_TEST_NOT_NATIVE',
            'executable_quest_rules':False,'rendered_pixels_tested':False,'actual_god_preservation_tested':False}
    client=None;desktop=desktop_names();database=args.output/'town-diagnostic-accounts.db';log=args.output/'server.log'
    manifest=json.loads((args.output/'fixture.json').read_text('utf-8'))
    logical=bytes.fromhex(manifest['logical_hex']);validate_issued(logical);sources=manifest['sources']
    def checkpoint():shared.dump(args.output/'ui-result.json',result)
    def marker_count():return log.read_text('utf-8',errors='replace').count(args.selection_marker)
    try:
        require(desktop['current'].startswith('God2Lab-') and desktop['current']!=desktop['input'],'HIDDEN_DESKTOP_REQUIRED')
        result['desktop_before']=desktop
        client=login();result['owned_client_pid']=client['process'].pid;result['ui']=hex(client['ui']);checkpoint()
        before_db=stable_database(database);before_native=stable_native(client);before_list=owned_list(database)
        require(before_native['state']['world_map']=={'kind':0,'area':4,'scene':3},'DAILY_KUNLUN_FIXTURE_REQUIRED')
        require(before_native['state']['deity_count']==0,'DAILY_NO_GOD_FIXTURE_REQUIRED')
        slots=bytes.fromhex(before_native['all50_slots'])
        require(all(int.from_bytes(slots[i*24+4:i*24+6],'little')!=0x18ca for i in range(30)),'DAILY_CONFIRMATION_ITEM_OUTSIDE_SCOPE')
        result['before']={'native':before_native,'database':before_db,'owned_list':before_list,'panel':panel_state(client)}
        def invariant():
            require(stable_database(database)==before_db,'DAILY_UI_MUTATED_GAMEPLAY_DATABASE')
            require(stable_native(client)==before_native,'DAILY_UI_MUTATED_NATIVE_GAMEPLAY_STATE')
            require(owned_list(database)==before_list,'DAILY_UI_MUTATED_OWNED_ISSUED_LIST')
        def ready(page):
            state=panel_state(client)
            if not state['open'] or state['count']!=9 or state['page']!=page:return None
            check_panel(state,logical,page)
            return {'panel':state,'source_text_cells':source_texts(client,state,sources)}
        for cycle in range(2):
            opening=open_daily(client)
            opened=wait_until(lambda:ready(0),12,'OWNED_D7_FD_PANEL_NOT_OPEN')
            initial_count=marker_count()
            state=opened['panel'];widget=state['widget']
            click(client['hwnd'],*owned.control_point(client['handle'],client['ui'],widget,0x2b))
            page_two=wait_until(lambda:ready(1),5,'DAILY_NEXT_PAGE_FAILED')
            click(client['hwnd'],*owned.control_point(client['handle'],client['ui'],widget,0x1a))
            time.sleep(.75)
            require(marker_count()==initial_count,'DISABLED_DAILY_ROW_SENT_SELECTION')
            require(panel_state(client)['request_buffer']==page_two['panel']['request_buffer'],'DISABLED_DAILY_ROW_CHANGED_REQUEST_BUFFER')
            click(client['hwnd'],*owned.control_point(client['handle'],client['ui'],widget,0x2a))
            wait_until(lambda:ready(0),5,'DAILY_PREVIOUS_PAGE_FAILED')
            require(marker_count()==initial_count,'DAILY_PAGING_SENT_SELECTION')
            requests=[]
            for side,control in ((1,0x1a),(2,0x22)):
                before=panel_state(client)
                tail=bytes.fromhex(before['request_buffer'])[-1]
                expected=expected_selection(sources[0],side,tail)
                offset=log.stat().st_size
                click(client['hwnd'],*owned.control_point(client['handle'],client['ui'],widget,control))
                def observed():
                    state=panel_state(client)
                    text=log.read_bytes()[offset:].decode('utf-8',errors='replace')
                    lines=[line for line in text.splitlines() if args.selection_marker in line and 'character_id=4' in line]
                    result['last_selection_observation']={'expected_hex':expected.hex(),'panel':state,'log_lines':lines}
                    if state['request_buffer']!=expected[1:].hex() or not lines:return None
                    fields={'index':sources[0]['index'],'branch':sources[0]['branch'],'ticket_slot':255,
                        'npc':sources[0]['start_npc'] if side==1 else sources[0]['end_npc'],'side':side,'opaque_tail':tail}
                    require(any(all(re.search(r'\b'+key+'='+str(value)+r'\b',line) for key,value in fields.items()) for line in lines),
                        'SERVER_DAILY_SELECTION_FIELDS_MISMATCH')
                    invariant()
                    return {'control':control,'expected_logical_hex':expected.hex(),'native_buffer':state['request_buffer'],'server_log':lines}
                requests.append(wait_until(observed,10,'NATIVE_D8_SOURCE_SELECTION_NOT_OBSERVED'))
            click(client['hwnd'],*owned.control_point(client['handle'],client['ui'],widget,0x19))
            closed=wait_until(lambda:panel_state(client) if not panel_state(client)['open'] else None,5,'DAILY_CLOSE_FAILED')
            invariant()
            result['stages'].append({'cycle':cycle+1,'opening':opening,'opened':opened,'page_two':page_two,
                'disabled_row_did_not_send':True,'requests':requests,'closed':closed,'gameplay_state_unchanged':True});checkpoint()
        result['after']={'native':stable_native(client),'database':stable_database(database),'owned_list':owned_list(database)}
        result['native_state_diff']={} if result['after']['native']==before_native else {'changed':True}
        result['database_diff']={} if result['after']['database']==before_db else {'changed':True}
        result['log_counts']={marker:log.read_text('utf-8',errors='replace').count(marker) for marker in
            ('OWNED_DAILY_LIST_OPEN',args.selection_marker,'OWNED_DAILY_CLAIM_INTENT_UNRESOLVED')}
        require(result['log_counts']['OWNED_DAILY_LIST_OPEN']==2 and result['log_counts'][args.selection_marker]==4,'DAILY_LOG_COUNTS_MISMATCH')
        result['accepted']=True
    except Exception as error:
        result['error']=f'{type(error).__name__}: {error}';result['traceback']=traceback.format_exc()
    finally:
        if client:
            try:shared.close_client(client)
            except Exception as error:result['cleanup_error']=str(error)
        result['desktop_after']=desktop_names();result['all_owned_clients_closed']=client is None or client['process'].poll() is not None
        result['desktop_unchanged']=desktop==result['desktop_after']
        result['accepted']=bool(result['accepted'] and desktop==result['desktop_after'] and result['all_owned_clients_closed'] and not result.get('cleanup_error'))
        checkpoint()
    return 0 if result['accepted'] else 1


def owner(args):
    args.output=args.output.resolve();args.server_candidate=args.server_candidate.resolve()
    paths={'source_db':fixture.SOURCE_DB,'live_client':fixture.LIVE_CLIENT,'private_client':fixture.CLIENT,
        'formal_config':ROOT/'artifacts/releases/town-chat-welcome-20260924/server-config.json'}
    result={'accepted':False,'before':{key:fixture.sha(path) for key,path in paths.items()},
        'server_sha256':fixture.sha(args.server_candidate)}
    result['actual_server_sha256']=result['server_sha256']
    server=runner=None
    try:
        with socket.socket() as probe:require(probe.connect_ex(('127.0.0.1',2598))!=0,'PRIVATE_PORT_ALREADY_IN_USE')
        prepare(args)
        if args.prepare_only:result['prepared_only']=True
        else:
            env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1';env.pop('GOD2_PRIVATE_SIDECAR_COMMAND',None)
            with (args.output/'stdout.log').open('wb') as log,(args.output/'runner.log').open('wb') as runner_log:
                server=subprocess.Popen([str(args.server_candidate),'--config',str(args.output/'server-config.json'),'--run-for','170'],
                    cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                result['server_pid']=server.pid
                def listening():
                    require(server.poll() is None,'SERVER_EXITED')
                    with socket.socket() as probe:return probe.connect_ex(('127.0.0.1',2598))==0
                wait_until(listening,10,'SERVER_NOT_LISTENING')
                command=[str(fixture.RUNNER),sys.executable,'-X','utf8','-B',str(Path(__file__).resolve()),
                    '--worker','--output',str(args.output),'--selection-marker',args.selection_marker]
                runner=subprocess.Popen(command,cwd=ROOT,env=env,stdout=runner_log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                result['runner_pid']=runner.pid;result['runner_exit']=runner.wait(timeout=145)
                result['ui']=json.loads((args.output/'ui-result.json').read_text('utf-8'))
                result['accepted']=result['runner_exit']==0 and result['ui']['accepted']
                result['all_clients_closed']=result['ui']['all_owned_clients_closed']
                result['desktop_unchanged']=result['ui']['desktop_unchanged']
    except Exception as error:result['error']=f'{type(error).__name__}: {error}'
    finally:
        for process in (runner,server):
            if process is not None and process.poll() is None:
                children=psutil.Process(process.pid).children(recursive=True)
                for child in reversed(children):
                    try:child.terminate()
                    except psutil.NoSuchProcess:pass
                process.terminate();process.wait(timeout=5)
                _,alive=psutil.wait_procs(children,timeout=5)
                for child in alive:child.kill();child.wait(timeout=5)
        result['after']={key:fixture.sha(path) for key,path in paths.items()}
        result['source_files_unchanged']={key:result['after'][key]==result['before'][key] for key in paths}
        result['server_sha256_after']=fixture.sha(args.server_candidate)
        result['candidate_unchanged']=result['server_sha256_after']==result['server_sha256']
        result['owned_server_closed']=server is None or server.poll() is not None
        result['owned_runner_closed']=runner is None or runner.poll() is not None
        result['accepted']=bool(result['accepted'] and all(result['source_files_unchanged'].values()))
        result['accepted']=bool(result['accepted'] and result['candidate_unchanged'] and result['owned_server_closed'] and result['owned_runner_closed'])
        if args.output.exists():shared.dump(args.output/'run-result.json',result)
    print(json.dumps({'accepted':result['accepted'],'prepared_only':result.get('prepared_only',False),'error':result.get('error')}))
    return 0 if (result['accepted'] or result.get('prepared_only')) and all(result['source_files_unchanged'].values()) else 1


def capacity_self_test():
    for count in (1,8,9,40):
        data=bytearray(172);data[:4]=bytes((0xfd,172,0,2));data[164]=count
        for i in range(count):data[4+4*i:8+4*i]=bytes((i,0,0,0x41))
        require(len(validate_issued(bytes(data)))==count,'CAPACITY_VALID_CASE')
    for count in (0,41,85,255):
        data=bytearray(172);data[:4]=bytes((0xfd,172,0,2));data[164]=count
        try:validate_issued(bytes(data))
        except RuntimeError:pass
        else:raise RuntimeError('UNSAFE_CAPACITY_ACCEPTED')
    return {'status':'PASS','valid':[1,8,9,40],'rejected':[0,41,85,255]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--server-candidate',type=Path)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--selection-marker',default='OWNED_DAILY_NPC_INTENT_UNRESOLVED')
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.self_test:print(json.dumps(capacity_self_test()));return 0
    if args.output is None:parser.error('--output required')
    if args.worker:return worker(args)
    if args.server_candidate is None:parser.error('--server-candidate required')
    return owner(args)


if __name__=='__main__':raise SystemExit(main())
