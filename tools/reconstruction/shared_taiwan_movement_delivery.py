"""Seal TW native step geometry and TW-origin common-position/peer source."""
import json
import re
import struct
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from .archive_inputs import ArchivedInputs,SERVER
from .packet_connection_inventory import IMAGE,PIN as TW_PIN,BASE,LENGTH_TABLE,WORLD_TABLE
from .cn_wrapper_route_frontier import CN,PIN as CN_PIN
from .cn_shared_movement_owner_delivery import sha,dump

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='shared-taiwan-movement-01'
ROUND='20261007-tw-common-movement'
ADDED=['src/protocol/RecoveredNativeMovement.h','src/scripting/TaiwanMovementRules.h',
    'src/scripting/TaiwanMovementRules.cpp','src/game/SharedTaiwanMovement.h','src/game/SharedTaiwanMovement.cpp',
    'scripts/tw/native_movement.lua','docs/research/shared-taiwan-movement-20261007.md']
CONTEXT=['src/net/Session.h','src/net/Session.cpp','src/protocol/RecoveredMovement.h',
    'src/handlers/RecoveredMovementService.h','src/handlers/RecoveredMovementService.cpp',
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/cn/world/SharedActorVisibility.h','src/cn/world/SharedActorVisibility.cpp',
    'src/cn/world/SharedMovementPublication.h','src/cn/world/SharedMovementPublication.cpp',
    'src/cn/world/SharedMovement.h','src/cn/world/SharedMovement.cpp','scripts/cn/native_movement.lua',
    'src/game/SharedTaiwanWorldLifecycle.h','src/game/SharedTaiwanWorldLifecycle.cpp']
SOURCES=ADDED+CONTEXT

def main():
    out=ROOT/NAME
    if out.exists():raise RuntimeError('Preserve sealed TW common movement delivery')
    ledger_path=ROOT/'packet-route-ledger.json';prior=ledger_path.read_bytes();ledger=json.loads(prior)
    cat=ROOT/'dual-client-route-catalog-22';before=(cat/'source-file-manifest.json').read_bytes()
    if sha(before)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog manifest changed')
    previous=json.loads(before);unchanged=[];pending=[]
    release=SERVER/'artifacts/releases/owned-guild-disband-20261005-01'
    release_manifest_raw=(release/'manifest.json').read_bytes();release_manifest=json.loads(release_manifest_raw)
    pending.append(('prior-manifests/frozen-tw-source-release.json',release_manifest_raw,release/'manifest.json'))
    for rel in CONTEXT:
        if rel in previous:
            expected=previous[rel]['sha256'];baseline=cat.relative_to(SERVER).as_posix()
        else:
            historical=release_manifest['source_snapshot_map'][rel]
            expected=release_manifest['artifacts'][historical];saved=(release/historical).read_bytes()
            if sha(saved)!=expected:raise ValueError('Historical TW source receipt differs')
            pending.append(('prior-sources/'+rel,saved,release/historical));baseline=(release/historical).relative_to(SERVER).as_posix()
        if sha((SERVER/rel).read_bytes())!=expected:raise ValueError('Frozen/context source changed: '+rel)
        unchanged.append({'path':rel,'sha256':expected,'unchanged_from_exact_prior_source':True,'baseline':baseline})
    reader=ArchivedInputs()
    try:tw=reader.read(IMAGE)
    finally:reader.close()
    if sha(tw)!=TW_PIN:raise ValueError('Pinned TW mapped image changed')
    md=Cs(CS_ARCH_X86,CS_MODE_32);native=[]
    for opcode,length,target in [(0x5d,2,0x692fa),(0x5e,13,0x69a60)]:
        leaf=struct.unpack_from('<I',tw,LENGTH_TABLE+4*opcode)[0]-BASE
        actual=struct.unpack_from('<I',tw,WORLD_TABLE+4*opcode)[0]-BASE
        if actual!=target or tw[leaf:leaf+6]!=b'\xb8'+struct.pack('<I',length)+b'\xc3':
            raise ValueError('TW native length/dispatch changed')
        code=tw[leaf:leaf+6];pending.append((f'native/tw/{opcode:02x}-length.bin',code,IMAGE))
        native.append({'name':f'{opcode:02x}-length','rva':f'{leaf:08x}','bytes':6,'sha256':sha(code)})
    for name,start,end in [('2e-producer',0x15790,0x157c5),('ordinary-direction',0x102700,0x1027b2),
        ('native-direction-cell-probe',0x102f20,0x102fe1),('ring-write40',0x1036b0,0x1036fb),
        ('5d-world-consumer',0x692fa,0x69345),('5e-world-consumer',0x69a60,0x69b35)]:
        code=tw[start:end];ins=list(md.disasm(code,BASE+start))
        if sum(i.size for i in ins)!=len(code):raise ValueError('TW slice boundary differs: '+name)
        asm=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in ins)+'\n').encode()
        pending.extend([('native/tw/'+name+'.bin',code,IMAGE),('native/tw/'+name+'.asm',asm,'pinned TW disassembly')])
        native.append({'name':name,'rva':f'{start:08x}','bytes':len(code),'sha256':sha(code)})
    table=tw[0x102fe4:0x103004];cases=list(struct.unpack('<8I',table))
    if any(not 0x502f46<=x<=0x502fa8 for x in cases):raise ValueError('TW direction table leaves actual probe')
    pending.append(('native/tw/native-direction-probe-table.bin',table,IMAGE))
    native.append({'name':'native-direction-probe-table','rva':'00102fe4','bytes':32,'sha256':sha(table),
        'kind':'eight native case addresses/data, not disassembled instructions','case_vas':[f'{x:08x}' for x in cases]})
    old=ROOT/'cn-shared-movement-owner-01';evidence_path=old/'native/20261006-cn-movement-01/movement-evidence.json'
    raw_evidence=evidence_path.read_bytes()
    if sha(raw_evidence)!=ledger['cn_account_admission_evidence']['cn-shared-movement-owner-01']['artifact_sha256'][evidence_path.relative_to(old).as_posix()]:
        raise ValueError('Prior CN movement native evidence changed')
    evidence=json.loads(raw_evidence);row=next(r for r in evidence['functions'] if r['va']=='00539150')
    source=Path(row['source']).read_bytes();match=re.search(rb'Size: (\d+) bytes',source)
    if not match or sha(source)!=row['source_sha256']:raise ValueError('CN direction C differs')
    exe=CN.parent/'XJZ-CN/God2_opt.exe';pe_raw=exe.read_bytes()
    if sha(pe_raw)!=CN_PIN:raise ValueError('CN native pin changed')
    pe=pefile.PE(data=pe_raw,fast_load=True);size=int(match.group(1));code=pe.get_data(0x539150-pe.OPTIONAL_HEADER.ImageBase,size)
    if sha(code)!=row['code_sha256'] or len(code)!=size:raise ValueError('CN direction native span differs')
    ins=list(md.disasm(code,0x539150));asm=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in ins)+'\n').encode()
    for ext,data,origin in [('.c',source,row['source']),('.bin',code,exe),('.asm',asm,'pinned CN disassembly')]:
        pending.append(('native/cn/00539150'+ext,data,origin))
    pending.append(('native/cn/prior-movement-evidence.json',raw_evidence,evidence_path))
    gaps=['Real dual Application/listeners/dispatcher, common scene/actor owner and actual per-TW-session attachment remain open.',
        'Native map/resource/frame/window lifecycle, timing/pending/reset/index/permission and complete native5D byte authority remain required.',
        'Common publication is state-preserving adjacent11-bit position/native visible low12 identity only; dynamic state/large coordinate/handle variants stay open.',
        '61/reset/transfer/recovery/battle/path/speed and every remaining game route/whole phase-state-variant denominator stay open.',
        'Session response queue submission and peer send API calls do not prove client receipt/rendered acceptance or deployment.']
    out.mkdir();snapshots=[]
    def save(rel,data,origin):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'sha256':sha(data),'bytes':len(data),'original':str(origin)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel,data,origin in pending:save(rel,data,origin)
    save('prior-ledger.json',prior,ledger_path)
    save('prior-manifests/catalog22-source-files.json',before,cat/'source-file-manifest.json')
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    dump(out/'unchanged-source-receipt.json',unchanged)
    manifest={'kind':'TW native2E/current scene/Lua geometry/real permission ->one shared saved-position CAS ->actual actor/cache ->all TW/CN native5E observer submissions ->complete supplied TW5D/actual Session queue',
        'source_paths':SOURCES,'snapshots':snapshots,'unchanged_context':unchanged,'tw_native_spans':native,
        'native_pins':{'tw':TW_PIN,'cn':CN_PIN},'cn_direction_span':{'va':'00539150','bytes':size,'sha256':sha(code),'source_sha256':sha(source)},
        'new_source_files':5,'new_lua_files':1,'modified_cpp_files':0,'source_owner_chains_added':0,'tw_source_owner_chains_added':1,
        'new_tw_phase_opcode_bindings':3,'new_cn_phase_opcode_bindings':0,'new_opcode_values':0,'new_complete_routes':0,
        'actual_session_movement_callback_signature_connected':True,'formal_application_hosted':False,
        'full_native_5d_supplier_required':True,'request_index_echo_invented':False,'tw_frozen_movement_source_changed':False,
        'cn_native_lua_changed':False,'one_common_position_commit_per_request':True,
        'previous_goal_turn_classification':'progress: actual TW Session/common world lifecycle extension sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','asset_loaders_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'TW native ordinary2E/common stored movement and TW/CN peer5E/full5D response source',
        'version_scope':'tw','status':'台服2E已接原生方向Lua/實際場景與權限/共用位置CAS/全部登記觀察者雙版5E/完整5D回應；world owner及正式掛載未接',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'tw_native_c2s_by_phase':{'world':['2E']},
        'tw_native_s2c_by_phase':{'world':['5D','5E']},'source_paths':SOURCES,
        'source_owner_chains_added':0,'tw_source_owner_chains_added':1,'formal_application_hosted':False,
        'complete_gameplay_routes_added':0,'storage_writes':'source uses one existing common position CAS per authorized request; no phase1 DB access',
        'shared_storage':['existing common character ownership and saved position/revision; transient observer registry'],
        'native_form_qualifications':{'tw_native_direction_and_cell_probe':True,'ring_index_without_initial_policy':True,
            'opaque_tail_preserved_without_authority':True,'full_native_ack_mandatory':True,
            'all_private_observer_generations_used':True,'native_render_acceptance':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'version_scope':'tw','root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Connect actual common native scene/resource owner and pending/timing/full5D authority; bind dual entry/movement dispatch without activating frozen legacy replacements.']+gaps
    dump(ledger_path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(snapshots),'tw_native_spans':len(native),
        'cn_direction_function_bytes':size,'new_cpp_files':5,'new_lua_files':1,'new_tw_partial_owner_chains':1,
        'new_tw_phase_bindings':3,'new_cn_phase_bindings':0,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
