"""Seal bounded primary battle queue and1C prefix recovery, static work only."""
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
NAME='cn-battle-deferred-consumer-01'
ROUND='20261007-cn-battle-deferred-consumer'
CONTEXT=['src/cn/world/SharedMonsterPublication.h','src/cn/world/SharedMonsterPublication.cpp',
    'src/cn/protocol/CnWorldMonster.h','src/core/Application.cpp']
NEW=['src/cn/protocol/CnBattleDeferredRecord.h','src/cn/protocol/CnBattleSingleObject.h']
SOURCES=NEW+CONTEXT+['docs/research/cn-battle-deferred-consumer-20261007.md',
    'tools/reconstruction/cn_battle_deferred_consumer_delivery.py']
FUNCTIONS=['005485f0','00551d50','00551dcf','0054d5e0','00555450','00555540','00555560',
    '00555620','0055e220','00481170','00567b50','00559fb0','0055ae50','00553a50']
OPCODES=[0x1c,0x38,*range(0x83,0x8a)]
LENGTHS=[45,2,15,15,2,17,3,121,57]

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed')
    catalog=(out/'catalog48-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog)
    for rel in CONTEXT:
        b=(out/'prior-sources'/rel).read_bytes()
        if sha(b)!=known[rel]['sha256'] or b!=(SERVER/rel).read_bytes():raise ValueError('Frozen context changed '+rel)
    if any(rel in known for rel in NEW):raise ValueError('New source already cataloged')
    snapshots=[]
    def save(rel,data,origin):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'bytes':len(data),'sha256':sha(data),'original':str(origin)})
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('Pinned PE differs')
    pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
    def read(va,size):
        b=pe.get_data(va-base,size)
        if len(b)!=size:raise ValueError('Short native span')
        return b
    metadata=(RECOVERY/'functions.tsv').read_bytes()
    rows={r['address']:r for r in csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t')}
    save('native/selected-function-metadata.json',(json.dumps({'original_sha256':sha(metadata),
        'rows':[rows[a] for a in FUNCTIONS]},indent=2)+'\n').encode(),RECOVERY/'functions.tsv')
    for a in FUNCTIONS:
        r=rows[a];p=Path(r['file']);p=p if p.is_absolute() else RECOVERY/p
        save('native/'+a+'.c',p.read_bytes(),p)
        save('native/'+a+'-declared.bin',read(int(a,16),int(r['bytes'])),exe)
    switches={};tables={}
    for site,table,count in [(0x548670,0x548c9c,63),(0x551dc8,0x552514,9),
        (0x551ffe,0x552538,10),(0x54d767,0x54ded8,4)]:
        b=read(table,count*4);targets=list(struct.unpack('<'+'I'*count,b))
        switches[site]=targets;tables[table]=targets
        save(f'native/table-{table:08x}.bin',b,exe)
    recv_sel=read(0x548d98,252);consume_sel=read(0x552560,110)
    save('native/selector-00548d98.bin',recv_sel,exe)
    save('native/selector-00552560.bin',consume_sel,exe)
    relations=[]
    expected=[0x552005,0x55240d,0x55202d,0x552080,0x5520f3,0x552117,0x5523f6,0x552439,0x55247a]
    for op,length,target in zip(OPCODES,LENGTHS,expected):
        receive=tables[0x548c9c][recv_sel[op]];consume=tables[0x552538][consume_sel[op-0x1c]]
        if receive!=(0x54889a if op==0x89 else 0x548882) or consume!=target:
            raise ValueError('Primary selected table entry differs')
        relations.append({'phase':'battle-connection-2','opcode':op,'logical_size':length,
            'receive_target':f'{receive:08x}','deferred_consumer_target':f'{consume:08x}',
            'receive_yield':op==0x89,'whole_consumer_variants_complete':False})
    primary={};cfgs=[]
    envelopes=[(0x5485f0,0x548c9c),(0x551d50,0x552514),(0x54d5e0,0x54ded8),
        (0x555450,0x555450+175),(0x555540,0x555540+17),(0x555560,0x555560+183),
        (0x55e220,0x55e220+128)]
    for lo,hi in envelopes:
        code=read(lo,hi-lo);cfg,asm,ins=trace(md,code,lo,hi,switches)
        primary.update(ins);cfgs.append(cfg)
        save(f'native/{lo:08x}-envelope.bin',code,exe)
        save(f'native/{lo:08x}-cfg.asm',asm,'static entry-connected primary decode; no instruction execution')
        save(f'native/{lo:08x}-cfg.json',(json.dumps(cfg,indent=2)+'\n').encode(),'calls not followed; open edges retained')
    for site,target in {0x548893:0x555450,0x5488ab:0x555450,0x551fa9:0x555540,
        0x551fe1:0x555560,0x552008:0x54d5e0}.items():
        i=primary.get(site)
        if i is None or i.mnemonic!='call' or i.op_str!=f'0x{target:x}':raise ValueError('Primary call differs')
    for site,operand in {0x54888d:'ecx, [edi + 0xa97980]',0x5488a5:'ecx, [edi + 0xa97980]',
        0x551fdb:'ecx, [esi + 0xa97980]',0x54d635:'ecx, [ebx + 0x149df8]'}.items():
        i=primary.get(site)
        if i is None or i.mnemonic!='lea' or i.op_str!=operand:raise ValueError('Primary owner differs')
    phasepath=CN/'artifacts/native/20261006-cn-route-denominator-03/s2c-phase-opcodes.json'
    selected=[r for r in json.loads(phasepath.read_bytes()) if r['phase']=='battle-connection-2' and r['opcode'] in OPCODES]
    if sorted((r['opcode'],r['length']) for r in selected)!=sorted(zip(OPCODES,LENGTHS)):
        raise ValueError('Prior phase lengths differ')
    save('native/selected-phase-opcodes.json',(json.dumps(selected,indent=2)+'\n').encode(),phasepath)
    contract={'client_sha256':PIN,'queue_owner':'main+A97980','copy_buffer':'main+A97180',
        'battle_object_owner':'main+149DF8','not_world71_owner':'main+1499FA0',
        'queued_relationships':relations,'single_object':{'logical_size':45,'consumer':'0054D5E0',
            'packed_position':'byte1 /14 side, %14 position','level':'byte2','identity':'WORD3',
            'role_word':'WORD5','selector':'WORD7','role_dependent_presentation_union':'bytes9..40',
            'trailing':'DWORD41 ->1 if bit0 else original','existing_native_prefix_copy_bytes':56,
            'source_projection_scope':'before native role/resource/allocation branch only',
            'enemy_attack_defense_attributes_elements_hpmp_or_carried_skills_identified':False},
        'primary_cfgs':cfgs,'calls_followed':False,'whole_bidirectional_route_connected':False}
    save('native-battle-deferred-contract.json',(json.dumps(contract,indent=2)+'\n').encode(),'bounded primary receiver/queue/consumer relations')
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',prior,lp)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    listed={r['path'] for r in snapshots}
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.relative_to(out).as_posix() not in listed:
            snapshots.append({'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,
                'sha256':sha(p.read_bytes()),'original':'captured before source edits'})
    gaps=['Battle admission/encounter authority, actual common-to-native slot/incarnation and Application battle host remain absent.',
        '1C role/resource/allocation variants and86 nested subtypes need downstream qualification; retained records/prefix are not complete battle routes.',
        'True enemy double attack/defense, four attributes, five elements, HPMP and carried skills are not identified in this presentation union.',
        'TW/CN authoritative gameplay/Lua/storage suppliers, indirect paths and whole-game denominator remain incomplete.']
    manifest={'kind':'primary BATTLE shared queue cases ->deferred1C consumer ->retained native record and bounded object-prefix source',
        'client_sha256':PIN,'source_paths':SOURCES,'snapshots':snapshots,'native_contract':contract,
        'new_cpp_files':2,'modified_cpp_files':0,'new_phase_opcode_bindings':1,'new_opcode_values':1,
        'new_primary_deferred_relationships':9,'source_owner_chains_added':0,'new_complete_routes':0,
        'formal_application_hosted':False,'actual_battle_authority_supplied':False,
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','native_api_executed','lua_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','frozen_tw_chat_modified','resource_decode_run']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN BATTLE1C retained object fields and pre-resource native prefix; deferred queue relations',
        'version_scope':'cn','status':'靜態保留型別與局部投影；佇列到consumer已恢復，正式戰鬥owner與完整路徑尚缺',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{'battle-connection-2':[0x1c]},'source_paths':SOURCES,
        'source_owner_chains_added':0,'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'storage_writes':'none','shared_storage':['common content default; no tables created'],
        'native_form_qualifications':{'logical_size':45,'only_prefix_before_resource_branch':True,
            'actual_battle_authority_supplied':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['battle_deferred_single_object']={'root':out.relative_to(SERVER).as_posix(),
        'queued_s2c':OPCODES,'source_field_binding_s2c':[0x1c],'battle_object_owner':'149DF8',
        'common_world_monster_identity_join_proven':False,'complete_gameplay_routes':0}
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next']=gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'source_field_bindings_added':1,'deferred_relations':9,
        'new_complete_routes':0,'tests_run':False,'cfg_open_edges':[(c['entry'],c['open_edges']) for c in cfgs]}))

if __name__=='__main__':main()
