"""Seal primary same-pool5F source extension; static work only, no tests/runtime."""
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
NAME='cn-world-monster-motion-01'
ROUND='20261007-cn-world-monster-motion'
NEW=['src/cn/protocol/CnWorldMonsterMotion.h']
MODIFIED=['src/cn/world/SharedMonsterPublication.h','src/cn/world/SharedMonsterPublication.cpp']
CONTEXT=['src/cn/protocol/CnWorldMonster.h','src/cn/protocol/CnWorldMonsterLifecycle.h',
    'src/cn/world/CnWorldMonsterDisplay.h','src/cn/world/CnWorldMonsterDisplay.cpp',
    'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp','src/core/Application.cpp']
SOURCES=NEW+MODIFIED+CONTEXT+['docs/research/cn-world-monster-motion-20261007.md',
    'tools/reconstruction/cn_world_monster_motion_delivery.py']
FUNCTIONS=['004fc6a0','004fc7a0','004fac00','00481b90','004fb5b0','0048aa10',
    '004fae10','004fc3e0','004b1fa0','004fbd90','004fbef0','0048c440']

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed')
    catalog=(out/'catalog47-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog);before=json.loads((out/'before-source-manifest.json').read_bytes());changes=[]
    for rel in MODIFIED+CONTEXT:
        b=(out/'prior-sources'/rel).read_bytes()
        if sha(b)!=before[rel]['sha256'] or sha(b)!=known[rel]['sha256']:raise ValueError('Before source differs '+rel)
        if rel in CONTEXT and b!=(SERVER/rel).read_bytes():raise ValueError('Context changed '+rel)
        if rel in MODIFIED:
            changes.append({'path':rel,'before_sha256':sha(b),'after_sha256':sha((SERVER/rel).read_bytes()),
                'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-47'})
    if NEW[0] in known:raise ValueError('New source already cataloged')
    snapshots=[]
    def save(rel,data,origin):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'bytes':len(data),'sha256':sha(data),'original':str(origin)})
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('Native PE pin differs')
    pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
    metadata=(RECOVERY/'functions.tsv').read_bytes()
    rows={r['address']:r for r in csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t')}
    save('native/selected-function-metadata.json',(json.dumps({'original_sha256':sha(metadata),
        'rows':[rows[a] for a in FUNCTIONS]},indent=2)+'\n').encode(),RECOVERY/'functions.tsv')
    def read(va,size):
        b=pe.get_data(va-base,size)
        if len(b)!=size:raise ValueError('Short native span')
        return b
    spans=[];primary={}
    for a in FUNCTIONS:
        r=rows[a];p=Path(r['file']);p=p if p.is_absolute() else RECOVERY/p
        source=p.read_bytes();lo=int(a,16);size=int(r['bytes']);code=read(lo,size)
        cfg,asm,ins=trace(md,code,lo,lo+size,{})
        save('native/'+a+'.c',source,p);save('native/'+a+'.bin',code,exe)
        save('native/'+a+'-cfg.asm',asm,'static primary CFG, not execution')
        save('native/'+a+'-cfg.json',(json.dumps(cfg,indent=2)+'\n').encode(),'bounded CFG; calls not followed, indirect/open edges retained')
        spans.append({'va':a,'reported_bytes':size,'code_sha256':sha(code),'source_sha256':sha(source),
            'cfg_instructions':cfg['decoded_cfg_instructions'],'cfg_bytes':cfg['decoded_unique_cfg_bytes'],
            'open_edges':cfg['open_edges'],'not_whole_program_closure':True})
        if a=='0048aa10':primary=ins
    expected={0x48ad07:0x4fb5b0,0x48adea:0x4b1fa0,0x48af7c:0x4fb5b0,0x48b924:0x4fbd90}
    for site,target in expected.items():
        i=primary.get(site)
        if i is None or i.mnemonic!='call' or i.op_str!=f'0x{target:x}':raise ValueError('Selected native interaction edge differs')
    evidence_sites={0x48aced:'ecx, [edi + 0x147c720]',0x48add3:'ecx, [edi + 0x147c720]',
        0x48af76:'ecx, [edi + 0x1499fa0]',0x48b908:'ecx, [edi + 0x1499fa0]'}
    for site,operand in evidence_sites.items():
        i=primary.get(site)
        if i is None or i.mnemonic!='lea' or i.op_str!=operand:raise ValueError('Primary owner operand differs')
    branch_rows=[]
    for op,lo,hi in [(0x5f,0x4919f4,0x491a0a),(0x60,0x491dc0,0x491dd6)]:
        table=read(0x4929d8+op*4,4)
        if struct.unpack('<I',table)[0]!=lo:raise ValueError('Primary WORLD switch differs')
        code=read(lo,hi-lo);cfg,asm,ins=trace(md,code,lo,hi,{})
        if any(e['address']!='00490ab1' for e in cfg['open_edges']):raise ValueError('Unexpected consumer frontier')
        prefix=f'native/world{op:02X}'
        save(prefix+'-table-entry.bin',table,exe);save(prefix+'-primary.bin',code,exe)
        save(prefix+'-cfg.asm',asm,'primary static branch decode')
        save(prefix+'-cfg.json',(json.dumps(cfg,indent=2)+'\n').encode(),'all outside branches exit actual WORLD receive loop')
        branch_rows.append({'opcode':op,'va':f'{lo:08x}','end_exclusive':f'{hi:08x}',
            'cfg_instructions':cfg['decoded_cfg_instructions'],'cfg_bytes':cfg['decoded_unique_cfg_bytes'],
            'open_edges':cfg['open_edges'],'source_binding_integrated':op==0x5f})
    phase_path=CN/'artifacts/native/20261006-cn-route-denominator-03/s2c-phase-opcodes.json'
    selected=[r for r in json.loads(phase_path.read_bytes()) if r['phase']=='world-connection-1' and r['opcode'] in [0x5f,0x60]]
    if len(selected)!=2 or any(r['length']!=21 for r in selected):raise ValueError('Phase evidence differs')
    save('native/selected-phase-opcodes.json',(json.dumps(selected,indent=2)+'\n').encode(),phase_path)
    for r in selected:
        p=CN/r['branch_source'];save(f"native/world{r['opcode']:02X}-branch.c.txt",p.read_bytes(),p)
    previous='cn-world-monster-lifecycle-01';expected=ledger['cn_account_admission_evidence'][previous]['artifact_sha256']
    for rel in ['native-monster-lifecycle-contract.json','integration-manifest.json']:
        p=ROOT/previous/rel;b=p.read_bytes()
        if sha(b)!=expected[rel]:raise ValueError('Previous immutable native evidence differs')
        save('prior-native/'+rel,b,p)
    contract={'client_sha256':PIN,'world5F':{'logical_size':21,'owner_offset':'1499FA0','callee':'004FC6A0',
        'instance':'WORD1 unsigned','state':'byte4&1F','target':'DWORD9 x=(value>>2)&7FFF,y=value>>17',
        'anchor':['WORD13 MOVZX','WORD15 MOVZX'],'timing':'WORD17 MOVZX ->signed promotion-40 ->current native clock addition',
        'opaque_preserved':['byte3','bytes5..8','bytes19..20','DWORD9 low2','byte4 high3'],
        'missing_instance':'no allocation/no update','existing_pool':'256 entries stride1D8',
        'extra_caller_parameter':1,'extra_parameter_semantics_not_inferred':True},
        'path_initialization':{'function':'004FAC00','snap_to_anchor_if_either_axis_diff_gt1':True,
            'generator':'00481B90 with00470310 actual native terrain predicate','generated_waypoint_cap':20,
            'target_not_guaranteed_reached':True,'frame_clock_or_queue_emulated':False},
        'world60':{'logical_size':21,'owner_offset':'147C720','callee':'004FC7A0','extra_parameter':3,'integrated':False},
        'click37':{'slot_picker':'0048AD07 main+147C720 ->004FB5B0',
            'dialog_qualifier':'0048ADD9 main+147C720 ->004FC3E0',
            'producer':'0048ADEA ->004B1FA0 ->00481440(37,parameter4bytes)',
            'native_time_gate':'timeGetTime delta>1000','same71_monster_pool_proven':False,
            'formal_request_route_integrated':False,'whole48AA10_case_variants_closed':False},
        'same71_selection_branches':['0048AF7C main+1499FA0 click','0048B924 main+1499FA0 level-range selection'],
        'expected_last_submitted_target_not_native_current_coordinates':True,'whole_bidirectional_route_connected':False}
    save('native-monster-motion-contract.json',(json.dumps(contract,indent=2)+'\n').encode(),'bounded primary pool/field/path/interaction source relations')
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',prior,lp)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    listed={r['path'] for r in snapshots}
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.relative_to(out).as_posix() not in listed:
            snapshots.append({'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),
                'original':'captured before source edits'})
    gaps=['Actual common monster authority/position CAS/native anchor/path/terrain/clock/queue suppliers and Application hosting remain absent.',
        '71-monster click/automatic selection C2S and battle1C entry/native identity remain unpaired;37 observed branch uses another147C720 owner and is not monster combat proof.',
        'TW/CN shared monster publication, double attacks/defenses/four attributes/five elements/HPMP/full carried skills and native gameplay rules remain incomplete.',
        'Login/world suppliers, whole48AA10 indirect cases and whole-game directional/state/variant denominator/full routes remain open.']
    manifest={'kind':'primary5F same71 owner motion ->private common monster/recipient incarnation ->actual source qualification ->original full5F transport submission',
        'client_sha256':PIN,'source_paths':SOURCES,'source_adaptations':changes,'native_spans':spans,'snapshots':snapshots,
        'primary_branches':branch_rows,'native_contract':contract,'new_cpp_files':1,'modified_cpp_files':2,
        'source_owner_chains_added':0,'new_phase_opcode_bindings':1,'new_opcode_values':0,'new_complete_routes':0,
        'formal_application_hosted':False,'actual_monster_authority_supplied':False,'expected_send_submission_not_native_observation':True,
        'previous_goal_turn_classification':'progress: catalog47 actual conditional common monster publication/78/74 private lifecycle and pool boundaries sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','native_api_executed','lua_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','frozen_tw_chat_modified','resource_decode_run']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN same71-pool native5F motion through existing common monster publication incarnation',
        'version_scope':'cn','status':'5F保留型別/真實authority資格入口/既有怪物世代與收件者transport接来源；實際路徑與production owner仍缺',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{'world-connection-1':[0x5f]},'source_paths':SOURCES,
        'source_owner_chains_added':0,'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'storage_writes':'none; real current revision and movement transition qualification required',
        'shared_storage':['existing common monster identity/incarnation/revisions; per-recipient low16 instance stays adapter identity; no tables created'],
        'native_form_qualifications':{'same71_owner':'1499FA0','logical_size':21,'anchors_unsigned':True,
            'generated_native_path_cap':20,'target_is_not_observed_current_position':True,
            'actual_monster_authority_supplied':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['world_monster_motion']={'root':out.relative_to(SERVER).as_posix(),
        'integrated_world_s2c':[0x5f],'same_owner_offset':'1499FA0','other_world60_owner':'147C720',
        'actual_native_path_or_clock_supplied':False,'complete_gameplay_routes':0}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND;plan['next']=gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'new_phase_bindings':1,
        'new_partial_owner_chains':0,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
