"""Read the complete scene pools and map/catalog memory after owned lab login.

Own loopback clone only, hidden desktop, VM_READ only. The received world state
is explicitly OUR_SERVER, never original-server spawn/stat authority.
"""
import argparse
from contextlib import closing
import ctypes as c
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
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).resolve().parent))
import psutil
from tools.strike_lab import run_private_owned_companions as fixture
from tools.strike_lab import current_live_memory_catalog_20260927 as catalog
from tools.strike_lab import private_weapon_peer_appearance_20260927 as peer
from tools.strike_lab import import_native_enemy_display as enemy
from tools.strike_lab import import_native_npc_display as npc
from tools.strike_lab.omega_assets import decode_csvz
from tools.strike_lab.world_atlas import parse_catalog
from tools.strike_lab import current_skill_identity as skills
from private_inventory_memory import kernel,read
from private_inventory_move_ui import require,desktop_names,wait_until
from private_potion_ui import click,type_ascii

def digest(raw):return hashlib.sha256(raw).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def exact(handle,address,size):
    raw=read(handle,address,size)
    require(raw is not None and len(raw)==size,f'SHORT_READ_{address:x}_{size}')
    return raw

def capture(handle,ui,output,expected_scene=(0,4,3)):
    role_pointer=struct.unpack('<I',exact(handle,ui+0x86888,4))[0]
    role=role_pointer-0x90;world=role-0x1539683c
    require(world>0x10000 and ui==world+0xa7f2f6c,'WORLD_ROOT_QUALIFICATION')
    require(exact(handle,role,4)==struct.pack('<I',4),'OWNED_ACTOR_REQUIRED')
    current=exact(handle,role+0x10,10)
    kind,scene,area=struct.unpack('<IIH',current)
    require((kind,area,scene)==expected_scene,'EXPECTED_OWN_SCENE')
    owner=struct.unpack('<I',exact(handle,world+0xaa36480,4))[0]
    require(owner==struct.unpack('<I',exact(handle,ui+0xcff70,4))[0] and owner>0x10000,'WORLD_STATIC_OWNER_MISMATCH')
    source=catalog.source_quests()
    # The authenticated world already publishes C through two independent
    # pointers. Follow the qualified catalog directly instead of rescanning
    # the entire (now much larger) scene heap for textual anchors.
    quest_pointer=struct.unpack('<I',exact(handle,owner+0xd2ac4,4))[0]
    quest_records=catalog.quest_catalog(handle,quest_pointer,source)
    require(quest_records is not None,'WORLD_QUEST_OWNER_QUALIFICATION')
    anchors={}
    for name,key in (('廚師梁禎',2936),('阿銀嬸',2938),('馬老伯',2939)):
        at=owner+0x121ea+94*key
        require(exact(handle,at,len(name.encode('cp950')))==name.encode('cp950'),'NPC_OWNER_ANCHOR')
        anchors[name]=[hex(at)]
    scan={'quest_catalogs':[quest_records],'source_name_hits':anchors}
    loaded=catalog.static_catalogs(handle,scan)
    loaded['capture_phase']='POST_LOGIN_WORLD'
    loaded['npc_record_regions']['nonzero_tail_records_after_login']=loaded['npc_record_regions'].pop('nonzero_tail_records_before_login')
    require(owner==int(loaded['owner'],16),'FULL_SOURCE_OWNER_MISMATCH')
    pools=[]
    for label,offset in (('npc',0x1539aed8),('monster_or_follower',0x153b8758)):
        address=world+offset;raw=exact(handle,address+0x70,256*0x1d8)
        occupied=[];empty=[]
        for slot in range(256):
            record=raw[slot*0x1d8:(slot+1)*0x1d8]
            identity=struct.unpack_from('<I',record)[0]
            if identity==0xffffffff:empty.append(slot);continue
            occupied.append({'slot':slot,'record_address':hex(address+0x70+slot*0x1d8),
                'identity':identity,'facing_word':struct.unpack_from('<H',record,8)[0],
                'sprite_handle':struct.unpack_from('<h',record,10)[0],
                'interaction_handle':struct.unpack_from('<h',record,12)[0],
                'x':struct.unpack_from('<i',record,16)[0],'y':struct.unpack_from('<i',record,20)[0],
                'projected_xy_hex':record[24:32].hex(),
                'movement_snapshot':list(struct.unpack_from('<4i',record,0x180)),
                'record_hex':record.hex(),'sha256':digest(record),
                'authority':'OUR_SERVER_SCENE_STATE_NOT_ORIGINAL_SPAWN'})
        require(len(empty)+len(occupied)==256,'POOL_COVERAGE')
        pools.append({'kind':label,'address':hex(address),'capacity':256,'stride':472,
            'bytes_read':len(raw),'whole_pool_sha256':digest(raw),'empty_slots':empty,'occupied':occupied})
    source_data=decode_csvz((fixture.LIVE_CLIENT.parent/'Data2/Patch/Comm/gamedata.csvZ').read_bytes())
    expected=parse_catalog(source_data)
    count=struct.unpack('<h',exact(handle,owner+0xd2aba,2))[0]
    pointer=struct.unpack('<I',exact(handle,owner+0xd2abc,4))[0]
    require(count==len(expected)==144 and pointer>0x10000,'FULL_MAP_CATALOG_REQUIRED')
    raw=exact(handle,pointer,count*0x1a4);maps=[]
    for i,row in enumerate(expected):
        record=raw[i*0x1a4:(i+1)*0x1a4]
        selector=struct.unpack_from('<H',record,0xf0)[0]
        packed=struct.unpack_from('<I',record,0xf4)[0]
        geometry=struct.unpack_from('<hhh',record,0xf8)
        require(selector==row['packed_selector'] and packed==row['kind']|(row['catalog_x']<<2)|(row['catalog_y']<<17),f'MAP_SOURCE_LAYOUT_{i}')
        require(geometry==(row['layer_width'],row['layer_height'],row['layers_per_row']),f'MAP_GEOMETRY_{i}')
        maps.append({'area':row['area'],'scene':row['scene'],'kind':row['kind'],
            'source_line':row['source_line'],'record_address':hex(pointer+i*0x1a4),
            'metadata_pointer':hex(struct.unpack_from('<I',record,0x1a0)[0]),
            'raw_record_hex':record.hex(),'authority':'LOADED_SOURCE_MAP_METADATA_NOT_NPC_COORDINATES'})
    require(exact(handle,role+0x10,10)==current,'SCENE_CHANGED_DURING_CAPTURE')
    checkpoint={'world':hex(world),'role':hex(role),'ui':hex(ui),'catalog_owner':hex(owner),
        'current_map':{'area':area,'scene':scene,'kind':kind},'pools':pools,
        'full_loaded_catalogs':loaded,'all_map_records':maps,
        'authority':'Actual post-login RAM; source catalogs verified; world state is OUR_SERVER only'}
    save(output/'world-capture.json',checkpoint)
    skill_source=(fixture.LIVE_CLIENT.parent/skills.SOURCE).read_bytes()
    require(digest(skill_source)==skills.SOURCE_SHA256,'SKILL_SOURCE_PIN')
    published=struct.unpack('<I',exact(handle,role+0x4504,4))[0]
    locations=list(dict.fromkeys([world+0xa7e0444,world+0x144938+0xa7e0444,published]))
    diagnostics=[];matches=[]
    for address in locations:
        if address<0x10000:continue
        body=read(handle,address,len(skill_source)-4)
        diagnostics.append({'address':hex(address),'readable':body is not None,
            'whole_body_sha256':digest(body) if body else None,'matches_source':body==skill_source[4:]})
        if body==skill_source[4:]:matches.append((address,body))
    # If the published owner is not initialized in a world-only scene, search
    # only for the exact source prefix and qualify the complete source body.
    if not matches:
        marker=skill_source[4:260]
        scanned=0
        for start,end,region_kind,protect in catalog.regions(handle):
            if region_kind!=0x20000:continue
            at=start;tail=b''
            while at<end:
                size=min(1<<20,end-at)
                require(scanned+size<=1800*(1<<20),'SKILL_SOURCE_SCAN_BOUND')
                raw=read(handle,at,size)
                if raw:
                    scanned+=len(raw);joined=tail+raw;index=joined.find(marker)
                    while index>=0:
                        address=at-len(tail)+index
                        body=read(handle,address,len(skill_source)-4)
                        if body==skill_source[4:] and not any(address==x[0] for x in matches):matches.append((address,body))
                        index=joined.find(marker,index+1)
                    tail=joined[-255:]
                at+=size
        diagnostics.append({'full_exact_source_scan_bytes':scanned,'matches':len(matches)})
    checkpoint['skill_location_diagnostics']={'published_role_pointer':hex(published),'candidates':diagnostics}
    save(output/'world-capture.json',checkpoint)
    require(len(matches)==1,'COMPLETE_SKILL_SOURCE_NOT_UNIQUE_OR_NOT_LOADED_'+str(len(matches)))
    skill_address,skill_body=matches[0]
    require(skill_address==published,'SKILL_SOURCE_NOT_ROLE_PUBLISHED_OWNER')
    definitions=skills.decode_definitions(skill_source)
    skill_rows=[]
    for key,definition in definitions.items():
        offset=definition.source_offset-4
        memory=skill_body[offset:offset+110]
        require(memory==definition.raw,f'ACTUAL_SKILL_RECORD_MISMATCH_{key}')
        skill_rows.append({'kind':key[0],'id':key[1],'address':hex(skill_address+offset),
            'record110_hex':memory.hex(),'sha256':digest(memory),
            'mp_threshold_word':struct.unpack_from('<H',memory,0x42)[0],
            'unclassified_word46':struct.unpack_from('<H',memory,0x46)[0],
            'effect_presence_words':list(struct.unpack_from('<13H',memory,0x4c)),
            'authority':'LOADED_SKILL_SOURCE; MP threshold verified; other fields not server formulas'})
    require(skill_body==skill_source[4:],'FULL_SKILL_BODY_MISMATCH')
    import pefile
    executable=(fixture.LIVE_CLIENT).read_bytes();pe=pefile.PE(data=executable)
    text_sections=[section for section in pe.sections if section.Name.rstrip(b'\0')==b'.text']
    require(len(text_sections)==1,'CURRENT_TEXT_SECTION_REQUIRED')
    section=text_sections[0]
    live_text=exact(handle,0x400000+section.VirtualAddress,section.SizeOfRawData)
    original_text=section.get_data()
    require(len(live_text)==len(original_text),'CURRENT_TEXT_SIZE_MISMATCH')
    (output/'live-text.bin').write_bytes(live_text)
    text_receipt={'rva':hex(section.VirtualAddress),'size':len(live_text),
        'live_sha256':digest(live_text),'original_sha256':digest(original_text),
        'matches_current_exe':live_text==original_text,'file':'live-text.bin',
        'scope':'Entire source-qualified current .text memory, not a process heap dump'}
    spans=[]
    # These are code/data ranges already qualified in previous original-native
    # traces. Read the running process, not only the unpacked on-disk image.
    for name,lo,hi in (('damage_projection',0x119e30,0x11aaf0),
                      ('skill_loader',0x12d3b0,0x12d43d),
                      ('skill_lookup',0x11c520,0x11c800),
                      ('skill_animation_reader',0x1297d0,0x129861),
                      ('received_battle_results',0x12c520,0x12ccc1),
                      ('hp_mp_result_application',0x128a70,0x128b0d),
                      ('skill_mp_gate',0xa9070,0xa9110)):
        live=exact(handle,0x400000+lo,hi-lo);original=pe.get_data(lo,hi-lo)
        spans.append({'name':name,'rva_start':hex(lo),'rva_end':hex(hi),
            'live_sha256':digest(live),'original_sha256':digest(original),
            'live_matches_current_exe':live==original,'live_code_hex':live.hex()})
    return {'world':hex(world),'role':hex(role),'ui':hex(ui),'catalog_owner':hex(owner),
        'current_map':{'area':area,'scene':scene,'kind':kind},'pools':pools,
        'full_loaded_catalogs':loaded,'all_map_records':maps,
        'skills':{'address':hex(skill_address),'whole_body_sha256':digest(skill_body),
            'source_sha256':skills.SOURCE_SHA256,'populated_definition_count':len(skill_rows),'records':skill_rows},
        'combat_code_spans':spans,'whole_live_text':text_receipt,
        'coverage':{'scene_entries_read':512,'npc_sources_read':len(loaded['npc_records']),
            'enemy_sources_read':len(loaded['enemy_records']),'map_records_read':len(maps),
            'npc_nonzero_tail_rows':loaded['npc_record_regions']['nonzero_tail_records_after_login'],
            'skill_records_read':len(skill_rows),'original_spawn_rows_recovered':0,
            'original_server_formulas_recovered':0},
        'authority':'Actual post-login RAM; loaded source fields verified; received world fields from our server only'}

def worker(args):
    before=desktop_names();require(before['current'].startswith('God2Lab-') and before['current']!=before['input'],'HIDDEN_DESKTOP_REQUIRED')
    value={'accepted':False,'desktop_before':before,'memory_access':'VM_READ|QUERY_LIMITED_INFORMATION',
        'process_memory_writes':0,'screenshots':0,'external_connections':0,'server_authority':'OUR_SERVER_NOT_ORIGINAL'}
    client=None
    try:
        process=subprocess.Popen([str(fixture.CLIENT),'127.0.0.1','127.0.0.1','6001','1'],cwd=fixture.CLIENT.parent,
            creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        client={'process':process};value['owned_client_pid']=process.pid
        hwnd=wait_until(lambda:peer.window_for(process.pid),35,'CLIENT_WINDOW_MISSING');client['hwnd']=hwnd
        time.sleep(2);click(hwnd,512,464);time.sleep(3)
        click(hwnd,437,232);type_ascii(hwnd,'codexslow')
        click(hwnd,437,263);type_ascii(hwnd,'labtest2345')
        click(hwnd,452,304);time.sleep(4)
        click(hwnd,330,145);click(hwnd,452,413);time.sleep(4)
        click(hwnd,330,150);click(hwnd,452,376);time.sleep(4)
        click(hwnd,452,370);time.sleep(8)
        require(process.poll() is None,'CLIENT_EXITED')
        handle=kernel.OpenProcess(0x1010,False,process.pid);require(handle,'READ_ONLY_MEMORY_OPEN_FAILED');client['handle']=handle
        ui=peer.find_ui(handle,4)
        value['capture']=capture(handle,ui,args.output);value['accepted']=True
    except Exception as error:value.update(error=str(error),traceback=traceback.format_exc())
    finally:
        if client:peer.close_client(client)
        value['desktop_after']=desktop_names();value['desktop_unchanged']=before==value['desktop_after']
        value['owned_client_closed']=client is None or client['process'].poll() is not None
        value['accepted']=bool(value['accepted'] and value['desktop_unchanged'] and value['owned_client_closed'])
        save(args.output/'memory-result.json',value)
    return 0 if value['accepted'] else 1

def owner(args):
    here=args.output.resolve();here.mkdir(parents=True,exist_ok=False)
    binary=globals().get('candidate_server',ROOT/'build-town-visibility/Release/god2-server.exe')
    formal=ROOT/'artifacts/releases/town-chat-welcome-20260924/server-config.json'
    paths={'client':fixture.LIVE_CLIENT,'lab_client':fixture.CLIENT,'fixture_database':fixture.SOURCE_DB,'formal_config':formal,'server':binary}
    hashes={key:fixture.sha(path) for key,path in paths.items()}
    require(hashes['client']==fixture.CURRENT_CLIENT_SHA,'CLIENT_PIN')
    require(hashes['lab_client']=='9ff8b9c99271e2e528270ce6475f231c338a09daf463c300fe39b62f66258c4f','EXACT_PORT_ONLY_COPY_PIN')
    value={'accepted':False,'before':hashes};server=runner=None
    try:
        with socket.socket() as probe:require(probe.connect_ex(('127.0.0.1',2598))!=0,'PRIVATE_PORT_OCCUPIED')
        database=here/'town-diagnostic-accounts.db'
        with closing(sqlite3.connect(fixture.SOURCE_DB.resolve().as_uri()+'?mode=ro',uri=True)) as source,closing(sqlite3.connect(database)) as target:source.backup(target)
        cfg=json.loads(formal.read_text('utf-8'));cfg['database']['path']=str(database);cfg['logging']['file']=str(here/'server.log')
        cfg['server']['port']=2598;cfg['server']['character_port']=0
        dev=cfg['development']
        for key,value_in in list(dev.items()):
            if key.startswith('diagnostic_') and isinstance(value_in,bool):dev[key]=False
        dev['diagnostic_town'].update(spawn_guides=True,native_npc_placements_only=True,
            quest_progress=False,map_probe=False,battle_after_quest=False,door_after_battle=False)
        dev['native_monster_placements_only']=True
        cfg['world']={'new_character_birthplace':{'area':4,'scene':3,'kind':0,'x':126,'y':126,
            'navigation':str(ROOT/'artifacts/world-atlas/kunlun-4-3.json'),'coordinate_authority':'CUSTOM-0040'}}
        configure=globals().get('configure_isolated_fixture')
        if configure:configure(cfg)
        save(here/'server-config.json',cfg)
        subprocess.run([str(binary),'--config',str(here/'server-config.json'),'--migrate-only'],cwd=ROOT,
            check=True,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30)
        with closing(sqlite3.connect(database)) as db:
            enemy.import_catalog(db,fixture.LIVE_CLIENT.parent);npc.install(db,fixture.LIVE_CLIENT.parent)
            db.execute('DELETE FROM recovered_positions WHERE character_id=4')
            prepare=globals().get('prepare_isolated_clone')
            if prepare:prepare(db)
            db.commit()
        env=os.environ.copy();env['GOD2_LOG_FILE_ONLY']='1';env.pop('GOD2_PRIVATE_SIDECAR_COMMAND',None)
        with (here/'stdout.log').open('wb') as log,(here/'runner.log').open('wb') as runner_log:
            server=subprocess.Popen([str(binary),'--config',str(here/'server-config.json'),'--run-for','180'],cwd=ROOT,
                env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            def listening():
                require(server.poll() is None,'PRIVATE_SERVER_EXITED')
                with socket.socket() as probe:return probe.connect_ex(('127.0.0.1',2598))==0
            wait_until(listening,10,'PRIVATE_SERVER_NOT_LISTENING')
            runner=subprocess.Popen([str(fixture.RUNNER),sys.executable,'-X','utf8','-B',str(Path(__file__).resolve()),
                '--worker','--output',str(here)],cwd=ROOT,env=env,stdout=runner_log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            value['runner_exit']=runner.wait(timeout=160)
            value['worker']=json.loads((here/'memory-result.json').read_text('utf-8'))
            value['accepted']=value['runner_exit']==0 and value['worker']['accepted']
    except Exception as error:value.update(error=str(error),traceback=traceback.format_exc())
    finally:
        for process in (runner,server):
            if process is not None and process.poll() is None:
                descendants=psutil.Process(process.pid).children(recursive=True)
                for child in reversed(descendants):
                    try:child.terminate()
                    except psutil.NoSuchProcess:pass
                process.terminate();process.wait(timeout=5)
                _,alive=psutil.wait_procs(descendants,timeout=5)
                for child in alive:child.kill();child.wait(timeout=5)
        value['source_files_unchanged']={key:fixture.sha(path)==hashes[key] for key,path in paths.items()}
        value['accepted']=bool(value['accepted'] and all(value['source_files_unchanged'].values()))
        save(here/'run-result.json',value)
    print(json.dumps({'accepted':value['accepted'],'error':value.get('error'),
        'worker_error':value.get('worker',{}).get('error'),'output':str(here)}))
    return 0 if value['accepted'] else 1

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--worker',action='store_true')
    args=p.parse_args();return worker(args) if args.worker else owner(args)
if __name__=='__main__':raise SystemExit(main())
