"""Read actual current-client catalogs on an owned hidden desktop.

No injection, process-memory write, screenshot, desktop switch, login or external
server is used. Only source-qualified catalog records are retained; arbitrary
process memory (including possible credentials) is never dumped to disk.
"""
import argparse
import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import psutil
from tools.strike_lab import run_private_owned_companions as fixture
from tools.strike_lab.omega_assets import decode_csvz
from tools.strike_lab.recover_quests import parse_table
from private_inventory_memory import kernel,read,Region
from private_inventory_move_ui import desktop_names,wait_until,require
from private_weapon_peer_appearance_20260927 import window_for
from private_potion_ui import click


def digest(raw):return hashlib.sha256(raw).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def exact(handle,address,size):
    value=read(handle,address,size)
    require(value is not None and len(value)==size,f'SHORT_READ_{address:x}_{size}')
    return value


def source_quests():
    raw=(fixture.LIVE_CLIENT.parent/'Data2/Patch/Comm/Mission_data.csvZ').read_bytes()
    require(digest(raw)=='659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716','QUEST_SOURCE_PIN')
    table=parse_table('missions',decode_csvz(raw))
    quests=[]
    for row in table['records']:
        fields=[bytes.fromhex(f) for f in row['raw_fields_hex']]
        if fields[0]:quests.append({'id':int(fields[0]),'name':fields[1], 'count':int(fields[2]),'texts':[]})
        else:quests[-1]['texts'].append(fields[3])
    require(len(quests)==418 and sum(len(q['texts']) for q in quests)==2014,'QUEST_SOURCE_COUNTS')
    return quests


def regions(handle):
    address=0x10000
    while address<0x80000000:
        r=Region()
        if not kernel.VirtualQueryEx(handle,address,c.byref(r),c.sizeof(r)):break
        base=int(r.BaseAddress or address);end=min(base+r.RegionSize,0x80000000)
        if end<=address:break
        if r.State==0x1000 and not r.Protect&0x101 and r.Protect&255 in (2,4,8,0x20,0x40,0x80):
            yield base,end,r.Type,r.Protect
        address=end


def quest_catalog(handle,base,quests):
    raw=read(handle,base,418*40)
    if raw is None or len(raw)!=418*40:return None
    for q in quests:
        row=raw[(q['id']-1)*40:q['id']*40]
        if struct.unpack_from('<h',row)[0]!=q['count'] or row[2:36].split(b'\0')[0]!=q['name']:return None
    rows=[];observed=0;differences=[]
    for q in quests:
        row=raw[(q['id']-1)*40:q['id']*40];pointer=struct.unpack_from('<I',row,36)[0]
        pointers=exact(handle,pointer,q['count']*4)
        texts=[]
        for i,source in enumerate(q['texts']):
            address=struct.unpack_from('<I',pointers,i*4)[0]
            # Native loader source bound379; reads stop at that allocation's NUL.
            expected=source[:379]
            content=exact(handle,address,len(expected)+1)
            require(content==expected+b'\0',f'QUEST_MEMORY_SOURCE_MISMATCH_{q["id"]}_{i}')
            if expected!=source:differences.append({'mission':q['id'],'description':i,'source_length':len(source),'memory_length':len(expected)})
            texts.append({'address':hex(address),'length':len(expected),'sha256':digest(expected)})
            observed+=1
        rows.append({'id':q['id'],'record_address':hex(base+(q['id']-1)*40),
            'record40_hex':row.hex(),'name_hex':q['name'].hex(),'count':q['count'],
            'text_pointer_array':hex(pointer),'texts':texts})
    return {'base':hex(base),'record_count':418,'text_count':observed,'records':rows,
        'native_long_text_truncations':differences,'authority':'LIVE_SOURCE_DISPLAY_CATALOG_NOT_GAMEPLAY_RULES'}


def scan(handle,quests):
    marker=quests[233]['name']
    require(quests[233]['id']==234 and marker=='[新手任務]果力名產'.encode('cp950'),'SOURCE_ANCHOR')
    anchors=[];catalogs=[];seen=set();scanned=0;region_count=0
    needle_names={name:name.encode('cp950') for name in ('廚師梁禎','阿銀嬸','馬老伯','大灰狐','果村蝸牛','巨水蛭')}
    name_hits={name:[] for name in needle_names}
    for start,end,kind,protect in regions(handle):
        region_count+=1;at=start;tail=b''
        while at<end:
            size=min(1<<20,end-at)
            require(scanned+size<=800*(1<<20),'READ_SCAN_LIMIT')
            raw=read(handle,at,size)
            if raw:
                scanned+=len(raw);combined=tail+raw;origin=at-len(tail)
                offset=combined.find(marker)
                while offset>=0:
                    candidate=origin+offset-2-233*40
                    if candidate>0x10000 and candidate not in seen:
                        seen.add(candidate)
                        value=quest_catalog(handle,candidate,quests)
                        if value:catalogs.append(value)
                    anchors.append(hex(origin+offset));offset=combined.find(marker,offset+1)
                for name,needle in needle_names.items():
                    offset=combined.find(needle)
                    while offset>=0:
                        hit=origin+offset
                        if len(name_hits[name])<64 and hex(hit) not in name_hits[name]:name_hits[name].append(hex(hit))
                        offset=combined.find(needle,offset+1)
                tail=combined[-128:]
            at+=size
    return {'bytes_read':scanned,'readable_regions':region_count,'quest_anchor_hits':anchors,
        'quest_catalogs':catalogs,'source_name_hits':name_hits,'name_hits_authority':'STRING_CANDIDATES_ONLY_NOT_SPAWNS_OR_STATS'}


def static_catalogs(handle,scan_result):
    # Derive C from three independent source NPC IDs. Never accept a coincidental
    # single string or follow an arbitrary scanned integer as a pointer.
    roots=[]
    for name,key in (('廚師梁禎',2936),('阿銀嬸',2938),('馬老伯',2939)):
        roots.append({int(hit,16)-0x121ea-94*key for hit in scan_result['source_name_hits'][name]})
    common=set.intersection(*roots)
    require(len(common)==1,'NPC_CATALOG_OWNER_NOT_UNIQUE')
    owner=common.pop();require(0x10000<owner<0x7fffffff,'CATALOG_OWNER_RANGE')
    count,pointer=struct.unpack('<II',exact(handle,owner+0xd2ac0,8))
    require(count==418 and hex(pointer) in {q['base'] for q in scan_result['quest_catalogs']},'CATALOG_QUEST_OWNER_MISMATCH')
    highwater=struct.unpack('<h',exact(handle,owner+0x121e8,2))[0]
    require(2939<=highwater<=8191,'NPC_CATALOG_HIGHWATER_RANGE')
    source=(fixture.LIVE_CLIENT.parent/'Data2/Patch/Comm/gamedata.csvZ').read_bytes()
    require(digest(source)=='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731','GAME_SOURCE_PIN')
    lines=decode_csvz(source).splitlines();start=next(i for i,r in enumerate(lines) if r.startswith(b'NPCAppearData,'))
    source_count=int(lines[start].split(b',')[1]);require(source_count==4043,'NPC_SOURCE_COUNT')
    records=[];names=[]
    for line in range(start+1,start+1+source_count):
        fields=lines[line].split(b',');key=int(fields[0]);require(0<key<=highwater,'NPC_KEY_OUTSIDE_LOADED_TABLE')
        raw=exact(handle,owner+0x121ea+94*key,94)
        memory_name=raw[:16].split(b'\0')[0]
        # Preserve any observed fixed-width name truncation separately.
        require(fields[1].startswith(memory_name) and (bool(memory_name) or not fields[1]),
            f'NPC_SOURCE_NAME_MISMATCH_{key}_{fields[1].hex()}_{memory_name.hex()}')
        if memory_name!=fields[1]:names.append({'key':key,'source_name_hex':fields[1].hex(),'memory_name_hex':memory_name.hex()})
        records.append({'key':key,'source_line':line+1,'address':hex(owner+0x121ea+94*key),
            'record94_hex':raw.hex(),'source_record_sha256':digest(lines[line]),
            'flags_word':struct.unpack_from('<H',raw,16)[0],'appearance_code':struct.unpack_from('<H',raw,18)[0]})
    mission_max=struct.unpack('<H',exact(handle,owner+0xb2c48,2))[0]
    mission_messages=struct.unpack('<I',exact(handle,owner+0xb2c4c,4))[0]
    require(8904<=mission_max<=32767 and mission_messages>0x10000,'NPC_MISSION_POINTER_BOUNDS')
    bundle=json.loads((ROOT/'artifacts/research/inferred-quest-sources-20260927/source-bundle.json').read_text('utf-8'))
    dialogue=[]
    for quest in bundle['quests']:
        for role,value in quest['dialogue_candidates'].items():
            key=value['text_id'];expected=bytes.fromhex(value['raw_hex']).split(b',',1)[1]
            ptr=struct.unpack('<I',exact(handle,mission_messages+4*(key-1),4))[0]
            actual=exact(handle,ptr,len(expected)+1)
            require(actual==expected+b'\0',f'NPC_MISSION_SOURCE_MISMATCH_{key}')
            dialogue.append({'mission_id':quest['mission_id'],'inferred_dialogue_role':role,'text_id':key,
                'address':hex(ptr),'text_hex':expected.hex(),'sha256':digest(expected),
                'authority':'LIVE_SOURCE_TEXT; state-to-text join remains inferred'})
    from tools.strike_lab.current_monster_inventory import pinned_catalog
    enemy=pinned_catalog(fixture.LIVE_CLIENT.parent);arena=struct.unpack('<I',exact(handle,owner+0xd2e24,4))[0]
    require(0x10000<arena<0x7fffffff,'ENEMY_ARENA_POINTER')
    raw_enemy=exact(handle,arena,26*len(enemy['records']));enemy_records=[]
    for source_row in enemy['records']:
        index=source_row['source_record_index'];raw=raw_enemy[26*index:26*(index+1)]
        source_name=bytes.fromhex(source_row['name_bytes_hex']);actual=raw[2:18].split(b'\0')[0]
        require(source_name.startswith(actual) and (bool(actual) or not source_name),
            f'ENEMY_SOURCE_NAME_MISMATCH_{index}_{source_name.hex()}_{raw.hex()}')
        enemy_records.append({'source_record_index':index,'address':hex(arena+26*index),
            'area':source_row['area'],'scene':source_row['scene'],'ordinal':source_row['ordinal'],
            'lookup_visible':source_row['lookup_visible'],'source_line':source_row['source_line'],
            'record26_hex':raw.hex(),'name_hex':actual.hex(),'source_record_sha256':source_row['record_sha256']})
    groups=[]
    for area in range(17):
        n,descriptor=struct.unpack('<II',exact(handle,owner+0xd2d9c+8*area,8))
        require(n<=1024,'ENEMY_DESCRIPTOR_COUNT_RANGE')
        if not n:continue
        for i in range(n):
            scene,count,record=struct.unpack('<III',exact(handle,descriptor+i*12,12))
            expected=enemy['groups'].get((area,scene))
            require(expected is not None and count==len(expected),'ENEMY_GROUP_SOURCE_COUNT_MISMATCH')
            require(record==arena+26*enemy['group_offsets'][area,scene],'ENEMY_GROUP_RECORD_POINTER_MISMATCH')
            groups.append({'area':area,'scene':scene,'count':count,'descriptor_address':hex(descriptor+12*i),'record_pointer':hex(record)})
    require(len(groups)==96,'ENEMY_VISIBLE_GROUP_COUNT_MISMATCH')
    return {'owner':hex(owner),'npc_highwater':highwater,'npc_source_count':source_count,
        'npc_records':records,'npc_name_truncations':names,
        'npc_record_regions':{'static_prefix':28,'server_mutable_tail':66,
            'nonzero_tail_records_before_login':sum(any(bytes.fromhex(r['record94_hex'])[28:]) for r in records),
            'tail_authority':'F8 server cache or unspecified initial bytes, never local original stats/spawn authority'},
        'npc_mission_messages':{'max_key':mission_max,'pointer_array':hex(mission_messages),'qualified_dialogue':dialogue},
        'enemy_arena':hex(arena),
        'enemy_records':enemy_records,'enemy_groups':groups,
        'authority':'ACTUAL_LOADED_DISPLAY_CATALOG; not NPC placements, monster stats, spawn or quest rules'}


def worker(args):
    before=desktop_names();require(before['current']!=before['input'],'HIDDEN_DESKTOP_REQUIRED')
    require(fixture.sha(fixture.LIVE_CLIENT)==fixture.CURRENT_CLIENT_SHA,'LIVE_CLIENT_PIN')
    require(fixture.sha(fixture.CLIENT)=='9ff8b9c99271e2e528270ce6475f231c338a09daf463c300fe39b62f66258c4f','LAB_CLIENT_PIN')
    result={'accepted':False,'desktop_before':before,'memory_access':'QUERY_LIMITED_INFORMATION|VM_READ',
        'process_memory_writes':0,'screenshots':0,'logins':0,'external_connections':0}
    process=None;handle=None
    try:
        process=subprocess.Popen([str(fixture.CLIENT),'127.0.0.1','127.0.0.1','6001','1'],cwd=fixture.CLIENT.parent,
            creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        result['client_pid']=process.pid
        hwnd=wait_until(lambda:window_for(process.pid),35,'GAME_WINDOW_MISSING')
        time.sleep(3)
        handle=kernel.OpenProcess(0x1010,False,process.pid);require(handle,'READONLY_PROCESS_OPEN')
        result['image_path']=psutil.Process(process.pid).exe()
        # Raw table loading is observed before and after the native agreement.
        quests=source_quests()
        result['before_agreement']=scan(handle,quests)
        click(hwnd,512,464);time.sleep(4)
        result['after_agreement']=scan(handle,quests)
        result['loaded_static_catalogs']=static_catalogs(handle,result['after_agreement'])
        result['accepted']=bool(result['before_agreement']['quest_catalogs'] or result['after_agreement']['quest_catalogs'])
    except Exception as error:result.update(error=str(error),traceback=traceback.format_exc())
    finally:
        if handle:kernel.CloseHandle(handle)
        if process and process.poll() is None:process.terminate();process.wait(timeout=10)
        result['owned_client_closed']=process is None or process.poll() is not None
        result['desktop_after']=desktop_names();result['desktop_unchanged']=before==result['desktop_after']
        result['accepted']=bool(result['accepted'] and result['desktop_unchanged'] and result['owned_client_closed'])
        save(args.output/'memory-result.json',result)
    return 0 if result['accepted'] else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--worker',action='store_true');args=parser.parse_args()
    if args.worker:return worker(args)
    args.output.mkdir(parents=True,exist_ok=False)
    paths={'client':fixture.LIVE_CLIENT,'lab_client':fixture.CLIENT,
        'formal_config':ROOT/'artifacts/releases/town-chat-welcome-20260924/server-config.json'}
    before={k:fixture.sha(v) for k,v in paths.items()}
    env=os.environ.copy();env['GOD2_PRIVATE_SIDECAR_WAIT_MS']='180000'
    command=[str(fixture.RUNNER),sys.executable,'-X','utf8','-B',str(Path(__file__).resolve()),'--worker','--output',str(args.output.resolve())]
    with (args.output/'runner.log').open('wb') as log:
        child=subprocess.Popen(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        try:code=child.wait(timeout=180)
        except subprocess.TimeoutExpired:
            descendants=psutil.Process(child.pid).children(recursive=True)
            for p in reversed(descendants):
                try:p.terminate()
                except psutil.NoSuchProcess:pass
            child.terminate();child.wait(timeout=10);raise
    result=json.loads((args.output/'memory-result.json').read_text('utf-8'))
    result['files_unchanged']={k:fixture.sha(v)==before[k] for k,v in paths.items()}
    result['accepted']=result['accepted'] and code==0 and all(result['files_unchanged'].values())
    save(args.output/'memory-result.json',result)
    print(json.dumps({'accepted':result['accepted'],'error':result.get('error'),'quest_tables_before':len(result.get('before_agreement',{}).get('quest_catalogs',[])),
        'quest_tables_after':len(result.get('after_agreement',{}).get('quest_catalogs',[])),'files_unchanged':result['files_unchanged']}))
    return 0 if result['accepted'] else 1


if __name__=='__main__':raise SystemExit(main())
