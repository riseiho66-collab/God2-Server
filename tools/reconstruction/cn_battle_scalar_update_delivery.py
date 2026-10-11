"""Seal primary CN86/0,1,6 native pair stores into retained deferred adapter."""
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
NAME='cn-battle-scalar-update-01'
ROUND='20261007-cn-battle-scalar-update'
NEW=['src/cn/protocol/CnBattleScalarUpdate.h','src/cn/battle/CnBattleScalarProjection.h']
MODIFIED=['src/cn/protocol/CnBattleDeferredRecord.h']
CONTEXT=['src/cn/protocol/CnBattleSingleObject.h','src/core/Application.cpp','src/protocol/RecoveredBattleVitals.h']
SOURCES=NEW+MODIFIED+CONTEXT+['docs/research/cn-battle-scalar-update-20261007.md',
    'tools/reconstruction/cn_battle_scalar_update_delivery.py']
FUNCTIONS=['00551d50','00551dcf','0055b910','0055b740','0055ba40','00518f70','0055e220',
    '00454090','00453ee0','004540d0','004db090','00519640','005597b0']

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed')
    catalog=(out/'catalog49-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog);before=json.loads((out/'before-source-manifest.json').read_bytes());changes=[]
    for rel in MODIFIED+CONTEXT:
        b=(out/'prior-sources'/rel).read_bytes()
        if sha(b)!=before[rel]['sha256'] or (rel in known and sha(b)!=known[rel]['sha256']):
            raise ValueError('Before source differs '+rel)
        if rel in CONTEXT and b!=(SERVER/rel).read_bytes():raise ValueError('Frozen context changed '+rel)
        if rel in MODIFIED:
            changes.append({'path':rel,'before_sha256':sha(b),'after_sha256':sha((SERVER/rel).read_bytes()),
                'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-49'})
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
    expected=[0x552134,0x552263,0x552385,0x552318,0x552378,0x55236b,0x552134]
    if tables[0x5525d0]!=expected:raise ValueError('Subtype table differs')
    selector=read(0x552560,110);save('native/selector-00552560.bin',selector,exe)
    if tables[0x552538][selector[0x86-0x1c]]!=0x552117:raise ValueError('Outer86 target differs')
    primary={};cfgs=[]
    for a in ['00551d50','0055b910','0055b740','0055ba40','00518f70','0055e220','00454090','00453ee0','005597b0']:
        lo=int(a,16);hi=0x552514 if a=='00551d50' else lo+int(rows[a]['bytes'])
        code=read(lo,hi-lo);cfg,asm,ins=trace(md,code,lo,hi,switches)
        if cfg['open_edges']:raise ValueError('Recovered bounded CFG still open '+a)
        cfgs.append(cfg);primary.update(ins)
        save('native/'+a+'-envelope.bin',code,exe)
        save('native/'+a+'-cfg.asm',asm,'entry-connected static primary decode; no execution')
        save('native/'+a+'-cfg.json',(json.dumps(cfg,indent=2)+'\n').encode(),'bounded closed local CFG; calls not followed')
    for site,target in {0x552189:0x55b910,0x5522b7:0x55ba40,0x552259:0x55b740,
        0x55222c:0x518f70,0x55b992:0x454090,0x55b9b1:0x453ee0}.items():
        i=primary.get(site)
        if i is None or i.mnemonic!='call' or i.op_str!=f'0x{target:x}':raise ValueError('Primary call differs')
    for site,operand in {0x55b970:'dword ptr [edi + 0xde8], eax',0x55b979:'dword ptr [edi + 0xdf0], eax',
        0x55baa0:'dword ptr [edi + 0xdec], eax',0x55baa9:'dword ptr [edi + 0xdf4], eax',
        0x55b83a:'dword ptr [esi + 0xde8], eax',0x55b843:'dword ptr [esi + 0xdf0], eax'}.items():
        i=primary.get(site)
        if i is None or i.mnemonic!='mov' or i.op_str!=operand:raise ValueError('Primary destination store differs')
    prev=ROOT/'cn-battle-deferred-consumer-01';proof=ledger['cn_account_admission_evidence']['cn-battle-deferred-consumer-01']['artifact_sha256']
    for rel in ['native-battle-deferred-contract.json','integration-manifest.json']:
        b=(prev/rel).read_bytes()
        if sha(b)!=proof[rel]:raise ValueError('Previous immutable native evidence differs')
        save('prior-native/'+rel,b,prev/rel)
    contract={'client_sha256':PIN,'phase':'battle-connection-2','opcode':0x86,'logical_size':17,
        'scalar_source_kinds':[0,1,6],'all_subtype_targets':[f'{x:08x}' for x in expected],
        'position':'byte2 /14 side, %14 slot','maximum':'DWORD5 unsigned','current':'DWORD9 unsigned',
        'opaque_retained':['WORD3','bytes13..16'],'actual_battle_owner':'main+149DF8',
        'side0':{'kind0':['actor+DE8','actor+DF0'],'kind1':['actor+DEC','actor+DF4'],
            'kind6':'no base actor scalar writes; selected self ->00518F70/6 ->real secondary-owner+2C/+30'},
        'side1':{'kind0_or6':['actor+DE8','actor+DF0'],'kind1':'no actor writes in this path',
            'extra_gate':'actual native object WORD+1A unsigned<1000'},
        'actor_stores_full32_unclamped':True,'render_current_separately_clamped':True,
        'cn_scalar_meaning_names':'raw pair A/B; TW HP/MP labels kept separately scoped',
        'true_enemy_base_stats_or_carried_skills_recovered':False,'primary_cfgs':cfgs,
        'calls_followed':False,'whole_bidirectional_route_connected':False}
    save('native-battle-scalar-contract.json',(json.dumps(contract,indent=2)+'\n').encode(),'primary nested dispatch/argument/destination store recovery')
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',prior,lp)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    listed={r['path'] for r in snapshots}
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.relative_to(out).as_posix() not in listed:
            snapshots.append({'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,
                'sha256':sha(p.read_bytes()),'original':'captured before source edits'})
    gaps=['Actual shared battle admission/encounter authority, common-to-native slot incarnation and formal Application host remain absent.',
        '86/6 side0 actual self/secondary owner and kinds2..5 downstream rules remain unintegrated; local CFG closure is not whole gameplay closure.',
        'CN scalar semantic/native value origins, true enemy attacks/defenses/attributes/elements and full carried skills remain incomplete.',
        '88 batch/5 command gate/entry requirements, TW/CN actual Lua/storage suppliers and whole-game denominator remain open.']
    manifest={'kind':'primary86 nested subtype closure ->retained queue-record adapter ->native scalar pair field stores',
        'client_sha256':PIN,'source_paths':SOURCES,'source_adaptations':changes,'snapshots':snapshots,'native_contract':contract,
        'new_cpp_files':2,'modified_cpp_files':1,'new_phase_opcode_bindings':1,'new_opcode_values':1,
        'new_source_subtype_values':[0,1,6],'source_owner_chains_added':0,'new_complete_routes':0,
        'formal_application_hosted':False,'actual_battle_authority_supplied':False,
        'previous_goal_turn_classification':'progress: catalog49 primary deferred queue and1C prefix field source sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','native_api_executed','lua_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','frozen_tw_chat_modified','resource_decode_run']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN BATTLE86/0,1,6 retained scalar fields through existing deferred adapter',
        'version_scope':'cn','status':'原生subtype與DWORD stores接來源；實際權威/slot世代/正式host仍缺',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{'battle-connection-2':[0x86]},'source_paths':SOURCES,
        'source_owner_chains_added':0,'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'storage_writes':'none','shared_storage':['common content default; no tables created'],
        'native_form_qualifications':{'logical_size':17,'subtypes':[0,1,6],
            'actual_battle_authority_supplied':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['battle_scalar_update']={'root':out.relative_to(SERVER).as_posix(),
        'integrated_s2c':[0x86],'subtypes':[0,1,6],'local_nested_cfg_closed':True,
        'common_world_monster_identity_join_proven':False,'complete_gameplay_routes':0}
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next']=gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'new_source_phase_bindings':1,'new_source_subtypes':[0,1,6],
        'local_cfgs_closed':len(cfgs),'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
