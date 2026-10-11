"""Seal CN88 side0 batch and86/5 gate/clock primary source, static only."""
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
NAME='cn-battle-round-gate-01';ROUND='20261007-cn-battle-round-gate'
NEW=['src/cn/protocol/CnBattleRoundBatch.h','src/cn/protocol/CnBattleCommandGate.h']
MODIFIED=['src/cn/protocol/CnBattleDeferredRecord.h','src/cn/battle/CnBattleScalarProjection.h']
CONTEXT=['src/cn/protocol/CnBattleScalarUpdate.h','src/cn/protocol/CnBattleSingleObject.h','src/core/Application.cpp']
SOURCES=NEW+MODIFIED+CONTEXT+['docs/research/cn-battle-round-gate-20261007.md',
    'tools/reconstruction/cn_battle_round_gate_delivery.py']
FUNCTIONS=['00551d50','0054d450','0054cd80','00561c40','00561fd0','0054f360',
    '005504e0','00543d40','00551430','005471f0','00547785','00518f70']

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed')
    catalog=(out/'catalog50-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog);before=json.loads((out/'before-source-manifest.json').read_bytes());changes=[]
    for rel in MODIFIED+CONTEXT:
        b=(out/'prior-sources'/rel).read_bytes()
        if sha(b)!=before[rel]['sha256'] or sha(b)!=known[rel]['sha256']:raise ValueError('Before source differs '+rel)
        if rel in CONTEXT and b!=(SERVER/rel).read_bytes():raise ValueError('Frozen context changed '+rel)
        if rel in MODIFIED:changes.append({'path':rel,'before_sha256':sha(b),
            'after_sha256':sha((SERVER/rel).read_bytes()),'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-50'})
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
        if len(b)!=size:raise ValueError('Short primary span')
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
    for site,table,count in [(0x551dc8,0x552514,9),(0x551ffe,0x552538,10),(0x55212d,0x5525d0,7)]:
        b=read(table,count*4);targets=list(struct.unpack('<'+'I'*count,b));switches[site]=targets;tables[table]=targets
        save(f'native/table-{table:08x}.bin',b,exe)
    selector=read(0x552560,110);save('native/selector-00552560.bin',selector,exe)
    if tables[0x552538][selector[0x88-0x1c]]!=0x552439 or tables[0x5525d0][5]!=0x55236b:
        raise ValueError('Selected native branch differs')
    cfgs=[];primary={}
    for a in ['00551d50','0054d450','0054cd80','00561c40','00561fd0','00551430','005471f0']:
        lo=int(a,16);hi=0x552514 if a=='00551d50' else (0x547f20 if a=='005471f0' else lo+int(rows[a]['bytes']))
        code=read(lo,hi-lo);cfg,asm,ins=trace(md,code,lo,hi,switches)
        if a!='005471f0' and cfg['open_edges']:raise ValueError('Unexpected bounded CFG frontier '+a)
        if a=='005471f0' and cfg['open_edges']!=[
            {'address':'00547373','kind':'unresolved_indirect_jump'},
            {'address':'0054774d','kind':'unresolved_indirect_jump'}]:raise ValueError('Frame UI frontier differs')
        cfgs.append(cfg);primary.update(ins)
        save('native/'+a+'-envelope.bin',code,exe)
        save('native/'+a+'-cfg.asm',asm,'entry-connected primary static decode, no instruction execution')
        save('native/'+a+'-cfg.json',(json.dumps(cfg,indent=2)+'\n').encode(),'calls not followed; UI indirect edges preserved')
    for site,target in {0x552444:0x54d450,0x54d598:0x561c40,0x54d5ad:0x561fd0,0x547e6f:0x551430}.items():
        i=primary.get(site)
        if i is None or i.mnemonic!='call' or i.op_str!=f'0x{target:x}':raise ValueError('Primary call differs')
    for site,mnemonic,operand in [(0x54d4a5,'mov','dword ptr [esi + 0xa97130], 0x14'),
        (0x54cd97,'mov','eax, dword ptr [edi + 0xa97130]'),
        (0x54cd9d,'mov','dword ptr [edi + 0xa970d8], eax'),
        (0x547e53,'sub','ecx, dword ptr [esi + 0xa970d0]'),
        (0x547e59,'mul','ecx'),(0x547e63,'shr','edx, 6'),
        (0x547e69,'mov','dword ptr [esi + 0xa970d8], eax')]:
        i=primary.get(site)
        if i is None or i.mnemonic!=mnemonic or i.op_str!=operand:raise ValueError('Primary clock assignment differs')
    prev=ROOT/'cn-battle-scalar-update-01';proof=ledger['cn_account_admission_evidence']['cn-battle-scalar-update-01']['artifact_sha256']
    for rel in ['native-battle-scalar-contract.json','integration-manifest.json']:
        b=(prev/rel).read_bytes()
        if sha(b)!=proof[rel]:raise ValueError('Previous immutable native evidence differs')
        save('prior-native/'+rel,b,prev/rel)
    contract={'client_sha256':PIN,'phase':'battle-connection-2',
        'batch88':{'logical_size':121,'round_word':'DWORD1','current_pairs':'DWORD5+slot*8 and DWORD9+slot*8',
            'slots':14,'side':0,'actual_all_base_pointers_required':True,'maximum_values_written':False,
            'control_byte':118,'opaque_tail_bytes':[117,119,120],'source_reset_emulated':False},
        'gate86_5':{'logical_size':17,'flags':'byte3 bits0,1','slots':'byte4 low/high nibble',
            'display':'promotedWORD5+1 last3 digits','display_word_is_duration':False,
            'clock_start':'actual timeGetTime ->main+A970D0','duration_source':'main+A97130',
            'first88':'prior round wordFFFFFFFF retains actual prior duration','later88':'sets native duration20',
            'frame_remaining':'DWORD(duration - unsigned DWORD(now-start)/1000)',
            'native_timeout_compare':'signed negative, not zero','source_timeout_command_emitted':False},
        'primary_cfgs':cfgs,'whole_ui_producer_closure':False,'whole_bidirectional_route_connected':False}
    save('native-battle-round-gate-contract.json',(json.dumps(contract,indent=2)+'\n').encode(),'primary queue/loop/gate/frame clock state recovery')
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',prior,lp)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    listed={r['path'] for r in snapshots}
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.relative_to(out).as_posix() not in listed:
            snapshots.append({'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,
                'sha256':sha(p.read_bytes()),'original':'captured before source edits'})
    gaps=['Actual shared encounter/admission and first native duration writer, common-to-native slot incarnation and Application host remain absent.',
        '88 complete actor/effect/skill-pointer reset and86/5 actual command ownership/UI/0054FFC0 producer need recovery.',
        'Two005471F0 UI indirect cases remain open; local timing path does not close all action variants.',
        'Enemy true double attacks/defenses/attributes/elements/full skills, authoritative Lua/storage and whole-game denominator remain open.']
    manifest={'kind':'primary88 current pair batch and86/5 actual clock/display distinction ->retained deferred adapter and existing actor projection',
        'client_sha256':PIN,'source_paths':SOURCES,'source_adaptations':changes,'snapshots':snapshots,'native_contract':contract,
        'new_cpp_files':2,'modified_cpp_files':2,'new_phase_opcode_bindings':1,'new_opcode_values':1,
        'new_source_variants':['BATTLE88 current side0 batch','BATTLE86/5 command gate'],
        'source_owner_chains_added':0,'new_complete_routes':0,'formal_application_hosted':False,
        'previous_goal_turn_classification':'progress: catalog50 scalar subtype primary CFG and actual pair stores sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','native_api_executed','lua_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','frozen_tw_chat_modified','resource_decode_run']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN BATTLE88 side0 current batch and86/5 native clock/display state',
        'version_scope':'cn','status':'保留型別/局部batch stores/gate接來源；正式權威/slot與動作producer仍缺',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{'battle-connection-2':[0x88,0x86]},'source_paths':SOURCES,
        'source_owner_chains_added':0,'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'storage_writes':'none','shared_storage':['common content default; no tables created'],
        'native_form_qualifications':{'batch88_side':0,'batch88_slots':14,'gate86_subtype':5,
            'gate_display_is_duration':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['battle_round_gate']={'root':out.relative_to(SERVER).as_posix(),
        'integrated_s2c':[0x88,0x86],'gate86_subtype':5,'display_word_is_duration':False,
        'actual_native_admission_or_command_owner_supplied':False,'complete_gameplay_routes':0}
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND;ledger['dual_client_execution_plan']['next']=gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'new_phase_bindings':1,'new_variants':['88 batch','86/5 gate'],
        'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
