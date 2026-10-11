"""Static primary CN71/resource projection and immutable source accounting only."""
import csv
import json
import struct
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN,PIN,RECOVERY
from .cn_shared_movement_owner_delivery import sha,dump
from .cn_summary_world_lineage_delivery import trace

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-world-monster-display-contract-01'
ROUND='20261007-cn-world-monster-display-contract'
NEW=['src/cn/protocol/CnWorldMonster.h','src/cn/assets/CnCurrentEnemyDisplayCatalog.h',
    'src/cn/assets/CnCurrentEnemyDisplayRows.inc','src/cn/world/CnWorldMonsterDisplay.h',
    'src/cn/world/CnWorldMonsterDisplay.cpp']
CONTEXT=['src/protocol/RecoveredMonsterRecord.h','src/cn/assets/CnCurrentNpcNameCatalog.h',
    'src/cn/assets/CnCurrentNpcNameRows.inc','src/cn/world/SharedWorldGameplay.h',
    'src/cn/world/SharedWorldGameplay.cpp','src/core/Application.cpp']
SOURCES=NEW+CONTEXT+['docs/research/cn-world-monster-display-contract-20261007.md',
    'tools/reconstruction/cn_world_monster_display_contract_delivery.py']
FUNCTIONS=['0042e010','00428500','00430a50','0042f870','00428490','004828f0','004829d0',
    '00483c10','004f92a0','004f9a80','004f91c0','004fa610','0076c3bf']
ENCODED='8a72d850a34b14170c4cb0e91da9430559ea7def4e047130c533d666d67b893a'
PLAIN='16f7bb0f9cdf2965719408204800b329269c810821b96d3d81b5feca168534a3'

def recover_resource(raw):
    # Parse already decoded bytes. No decompressor/native loader/client runs.
    lines=raw.splitlines();offsets=[];position=0
    for line in raw.splitlines(keepends=True):offsets.append(position);position+=len(line)
    start=next(i for i,l in enumerate(lines) if l.startswith(b'EnyName,'))
    if lines[start]!=b'EnyName,7935' or lines[start+1]!=b'EnyNameTotal,8076':
        raise ValueError('Pinned resource header differs')
    i=start+2;rows=[];blocks=[];active={}
    while lines[i].startswith(b'EnyNameIsland_Area,'):
        _,area,count=lines[i].split(b',');category=int(area);groups=[];block_line=i+1;i+=1
        for _ in range(int(count)):
            _,group,count=lines[i].split(b',');group=int(group);count=int(count);group_rows=[];i+=1
            for ordinal in range(1,count+1):
                fields=lines[i].split(b',')
                if len(fields) not in [6,10] or b'\0' in fields[1]:raise ValueError('Unqualified resource fields')
                color,kind,model,pose=map(int,fields[2:6])
                native=bytearray(26) #0042E010 calloc; native padding is zero here.
                native[0]=((color<<4)&0xf0)|(kind&1)|((pose<<1)&0xe)
                native[1]=model&0xff
                name=fields[1][:15];native[2:2+len(name)]=name;native[17]=0
                if model in [5001,5002,5003] and kind&1:
                    for field,letter,at in [(6,b'h',22),(7,b'f',20),(8,b'b',18),(9,b'w',24)]:
                        token=fields[field]
                        if len(token)!=5 or token[1:2]!=letter or not token[0:1].isdigit() or not token[2:].isdigit():
                            raise ValueError('Unqualified component resource token')
                        native[at]=((model-5001)&15)|((token[2]<<4)&0xf0)
                        native[at+1]=((token[0]<<5)&0xe0)|(int(token[3:])&31)
                elif kind&1:raise ValueError('Unknown composite base style')
                row={'source_index':len(rows),'source_line':i+1,'source_offset':offsets[i],
                    'category':category,'group':group,'ordinal':ordinal,
                    'ignored_source_row_label_hex':fields[0].hex(),'raw_row_hex':lines[i].hex(),
                    'raw_row_sha256':sha(lines[i]),'native_record_hex':native.hex(),
                    'native_header':native[0],'native_model_selector':native[1],
                    'composite':bool(kind&1),'source_name_bytes':len(fields[1]),'active':False}
                rows.append(row);group_rows.append(row);i+=1
            groups.append({'group':group,'count':count,'rows':group_rows})
        if category in active:
            previous=active[category]
            previous['superseded_by_source_line']=block_line
        block={'category':category,'source_line':block_line,'groups':groups,'superseded_by_source_line':None}
        blocks.append(block);active[category]=block
    if len(rows)!=8076 or lines[i]!=b'SpecialEnyInfo,1' or lines[i+1]!=b'1,IGS_SPECIAL,0,0,149,1':
        raise ValueError('Current resource extent/special record differs')
    lookup={}
    for category,block in active.items():
        if category>=17:raise ValueError('Invalid category extent')
        for group in block['groups']:
            for row in group['rows']:
                key=(category<<23)|(row['group']<<13)|row['ordinal']
                if key not in lookup:lookup[key]=row;row['active']=True
    if len(lookup)!=8052:raise ValueError('Current native lookup accounting differs')
    source='// CN8A72/16F7 native0042E010 calloc26-byte rows.\n'
    source+='// Active last category blocks; first sufficient matching group; labels are not common IDs.\n'
    for key,row in sorted(lookup.items()):
        b=bytes.fromhex(row['native_record_hex'])
        source+='{'+str(key)+','+str(row['source_index'])+','+str(row['source_line'])+',{{'+','.join(f'0x{x:02x}' for x in b)+'}}},\n'
    summary={'ordered_source_rows':len(rows),'active_lookup_rows':len(lookup),
        'superseded_rows':sum(not r['active'] for r in rows),'category_blocks':len(blocks),
        'active_categories':len(active),'source_composite_rows':sum(r['composite'] for r in rows),
        'active_composite_rows':sum(r['composite'] for r in lookup.values()),
        'source_names_over15bytes':sum(r['source_name_bytes']>15 for r in rows),
        'special_record_line':i+2,'special_row_hex':lines[i+1].hex(),
        'special_native_known_mask_hex':(b'\xff'*6+b'\0'*20).hex(),
        'special_native_known_values_hex':(bytes([2,149,0,0,0,0])+b'\0'*20).hex(),
        'special_untouched_bytes_not_asserted_zero':True,
        'row_count_header7935_not_loop_limit':True,'loop_limit_eny_name_total':8076,
        'duplicate_category7_replaces_prior24rows':True,
        'category_group_keys_not_proved_map_or_common_monster_ids':True}
    compact_blocks=[{k:v for k,v in block.items() if k!='groups'}|
        {'groups':[{'group':g['group'],'count':g['count']} for g in block['groups']]} for block in blocks]
    return source.encode(),rows,compact_blocks,summary

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed')
    catalog=(out/'catalog45-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog);before=json.loads((out/'before-source-manifest.json').read_bytes())
    for rel in CONTEXT:
        b=(out/'prior-sources'/rel).read_bytes()
        if b!=(SERVER/rel).read_bytes() or sha(b)!=before[rel]['sha256']:
            raise ValueError('Context/frozen source differs '+rel)
        if rel in known and sha(b)!=known[rel]['sha256']:raise ValueError('Catalog context differs '+rel)
    for rel in NEW:
        if rel in known:raise ValueError('New source already cataloged')
    snapshots=[]
    def save(rel,data,origin):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'bytes':len(data),'sha256':sha(data),'original':str(origin)})
    plain_path=ROOT/'cn-current-npc-name-source-01/inputs/current-gamedata.csv'
    expected=ledger['cn_account_admission_evidence']['cn-current-npc-name-source-01']['artifact_sha256']
    raw=plain_path.read_bytes()
    if sha(raw)!=PLAIN or sha(raw)!=expected['inputs/current-gamedata.csv']:raise ValueError('Plain resource pin differs')
    encoded_path=CN.parent/'XJZ-CN/Data2/Patch/Comm/gamedata.csvZ';encoded=encoded_path.read_bytes()
    if sha(encoded)!=ENCODED:raise ValueError('Current encoded resource pin differs')
    generated,resource_rows,blocks,resource_summary=recover_resource(raw)
    p=SERVER/NEW[2]
    with p.open('xb') as stream:stream.write(generated)
    save('resource/ordered-display-rows.json',(json.dumps(resource_rows,indent=2)+'\n').encode(),plain_path)
    save('resource/category-group-load-order.json',(json.dumps(blocks,indent=2)+'\n').encode(),plain_path)
    save('resource/recovery-summary.json',(json.dumps(resource_summary,indent=2)+'\n').encode(),'static source projection')
    save('resource/encoded-resource-reference.json',(json.dumps({'original':str(encoded_path),'sha256':sha(encoded),
        'bytes':len(encoded),'decoded_reference':str(plain_path),'decoded_sha256':sha(raw),
        'decoded_bytes':len(raw),'decode_rerun':False},indent=2)+'\n').encode(),'existing catalog41 immutable resource reference')
    # Only bounded EnyName/SpecialEnyInfo section bytes are copied; no whole historical/resource tree recovery.
    selected_lines=raw.splitlines(keepends=True)
    first=next(i for i,l in enumerate(selected_lines) if l.startswith(b'EnyName,'))
    last=resource_summary['special_record_line']
    save('resource/EnyName-SpecialEnyInfo-section.csv',b''.join(selected_lines[first:last]),plain_path)
    exe=CN.parent/'XJZ-CN/God2_opt.exe';binary=exe.read_bytes()
    if sha(binary)!=PIN:raise ValueError('Native PE pin differs')
    pe=pefile.PE(data=binary,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
    metadata=(RECOVERY/'functions.tsv').read_bytes()
    functions={r['address']:r for r in csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t')}
    save('native/selected-function-metadata.json',(json.dumps({'original_sha256':sha(metadata),
        'rows':[functions[a] for a in FUNCTIONS]},indent=2)+'\n').encode(),RECOVERY/'functions.tsv')
    spans=[]
    for a in FUNCTIONS:
        r=functions[a];p=Path(r['file']);p=p if p.is_absolute() else RECOVERY/p
        source=p.read_bytes();lo=int(a,16);size=int(r['bytes']);code=pe.get_data(lo-base,size)
        if len(code)!=size:raise ValueError('Short PE span')
        cfg,asm,ins=trace(md,code,lo,lo+size,{})
        save('native/'+a+'.c',source,p);save('native/'+a+'.bin',code,exe)
        save('native/'+a+'-cfg.asm',asm,'primary static CFG decoding, not execution')
        save('native/'+a+'-cfg.json',(json.dumps(cfg,indent=2)+'\n').encode(),'static bounded CFG; calls not followed')
        spans.append({'va':a,'reported_bytes':size,'code_sha256':sha(code),'source_sha256':sha(source),
            'cfg_instructions':cfg['decoded_cfg_instructions'],'cfg_bytes':cfg['decoded_unique_cfg_bytes'],
            'open_edges':cfg['open_edges'],'not_whole_program_closure':True})
    branch_table=pe.get_data(0x4929d8+0x71*4-base,4)
    if struct.unpack('<I',branch_table)[0]!=0x491752:raise ValueError('Primary WORLD71 switch differs')
    save('native/world71-table-entry.bin',branch_table,exe)
    lo=0x491752;hi=0x4919cb;code=pe.get_data(lo-base,hi-lo);cfg,asm,ins=trace(md,code,lo,hi,{})
    if any(e['address']!='00490aab' for e in cfg['open_edges']):raise ValueError('Unexpected consumer frontier')
    save('native/world71-primary.bin',code,exe);save('native/world71-cfg.asm',asm,'primary static branch decoding')
    save('native/world71-cfg.json',(json.dumps(cfg,indent=2)+'\n').encode(),'all outside branches exit to actual world receive loop00490AAB')
    spans.append({'va':'00491752','end_exclusive':'004919cb','cfg_instructions':cfg['decoded_cfg_instructions'],
        'cfg_bytes':cfg['decoded_unique_cfg_bytes'],'open_edges':cfg['open_edges'],'packet_origin':'EDI then body=EDI+1'})
    save('native/component-sscanf-format.bin',pe.get_data(0x7ed65c-base,3),exe)
    phase_path=CN/'artifacts/native/20261006-cn-route-denominator-03/s2c-phase-opcodes.json'
    selected=[r for r in json.loads(phase_path.read_bytes()) if r['phase']=='world-connection-1' and r['opcode']==0x71]
    if len(selected)!=1 or selected[0]['length']!=21:raise ValueError('Native phase evidence differs')
    save('native/world71-phase-source.json',(json.dumps(selected,indent=2)+'\n').encode(),phase_path)
    p=CN/selected[0]['branch_source'];save('native/world71-branch.c.txt',p.read_bytes(),p)
    contract={'client_sha256':PIN,'logical_size':21,'native_instance_bits':16,'scene_high_bit':'8000',
        'catalog_key':{'category':'WORD5 low6; native<17','group':'WORD5>>6','ordinal':'WORD19>>3; nonzero'},
        'direction':'DWORD1>>29','state':'byte4&1F','coordinates':'DWORD9 x=(value>>2)&7FFF,y=value>>17',
        'resource_override':'byte3 nonzero invokes00430A50; outside count returns base but still changes pose',
        'resource_pose':'WORD19 low3; single constructor zero->0,nonzero->minus1',
        'opaque_preserved':['WORD7','bytes13..18','DWORD9 low2'],
        'override_empty_name_merge':'base HIGH nibble, override LOW nibble, base16-byte name',
        'single_model':'004829D0 auxiliary ->004828F0 model; model<200; selector3D rewrites consumed byte3',
        'composite_model':'00483C10(5,1,body/face/head/weapon WORDs,4 handles); all signed handles>=0',
        'pool':{'entries':256,'stride':'1D8','owner_offset':'70','existing_id_appearance_replaced':False,
            'existing_id_updates':['coordinates/current target caches','direction if changed','low5 state/title','scene high-bit hiding'],
            'fresh_id':'first FFFFFFFF slot; separate single/composite initialization; full pool logs/no new actor'},
        'actual_receiver_resources_supplied':False,'pool_constructor_emulated':False,'native_execution_observed':False,
        'battle_or_request_causality_proven':False,'no_stats_claim':'No double attacks/defenses/4 attributes/elements/skill list recovered from these bounded consumers; unread bytes remain opaque, not global absence.'}
    save('native-monster-display-contract.json',(json.dumps(contract,indent=2)+'\n').encode(),'primary bounded native consumer/source projection')
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',prior,lp)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    listed={r['path'] for r in snapshots}
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.relative_to(out).as_posix() not in listed:
            snapshots.append({'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,
                'sha256':sha(p.read_bytes()),'original':'captured before source additions'})
    gaps=['Actual per-recipient model/resource-cache suppliers/revisions, pool ownership/lifetimes/removal/reuse/reset and publication/Application remain absent.',
        'C2S world interaction/encounter ->common monster authority/spawn/position/state/storage ->TW/CN display and battle entry remain unconnected.',
        'Double attacks/defenses, four attributes, five elements, HP/MP and carried full skill repertoire need separate exact server/native sources; appearance keys are not stat/common entity IDs.',
        'TW/CN name encoding/render qualification, account/world suppliers, remaining systems and whole-game directional/state/variant denominator remain open.']
    manifest={'kind':'primary WORLD71/EnyName loader ->current active display source ->qualified native input preparation',
        'client_sha256':PIN,'source_paths':SOURCES,'source_adaptations':[],'native_spans':spans,'snapshots':snapshots,
        'resource_summary':resource_summary,'native_contract':contract,'new_cpp_source_files':5,
        'source_owner_chains_added':0,'new_phase_opcode_bindings':1,'new_opcode_values':0,'new_complete_routes':0,
        'formal_application_hosted':False,'monster_authority_implemented':False,'static_resource_parse_and_byte_projection_run':True,
        'previous_goal_turn_classification':'progress: catalog45 primary native actor text projection integrated, receiver providers still missing',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','native_loader_executed','native_api_executed','lua_executed',
            'deployed','production_database_read_or_modified','client_modified','font_modified','frozen_tw_chat_modified','resource_decode_rerun']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN native WORLD71 current monster display resource projection',
        'version_scope':'cn','status':'71單/四部件模型與當前資源載入順序接來源；實際怪物權威/模型供應/發布未完成',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{'world-connection-1':[0x71]},'source_paths':SOURCES,
        'source_owner_chains_added':0,'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'storage_writes':'none; no monster stats or entity IDs inferred, no tables created',
        'shared_storage':['common monster/gameplay tables remain default; catalog keys stay adapter presentation only'],
        'native_form_qualifications':{'logical_size':21,'active_catalog_rows':8052,'resource_success_preparation_source':True,
            'actual_resources_supplied':False,'whole_opcode_variants_complete':False,'combat_stats_recovered':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['world_monster_display']={'root':out.relative_to(SERVER).as_posix(),
        'world_s2c':0x71,'source_ordered_rows':8076,'active_display_rows':8052,'native_instance_bits':16,
        'actual_monster_authority_supplied':False,'complete_gameplay_routes':0}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND;plan['next']=gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'source_rows':8076,'active_rows':8052,'snapshots':len(snapshots),
        'new_phase_bindings':1,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
