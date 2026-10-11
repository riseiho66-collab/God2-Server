"""Seal native frame completion/path and distinct5D consumer; no gameplay execution."""
import json
import re
import struct
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN, PIN, RECOVERY
from .cn_shared_movement_owner_delivery import sha, dump

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-native-path-completion-01'
ROUND='20261007-cn-native-path-completion'
MODIFIED=['src/cn/world/SharedNativeMovementScene.h','src/cn/world/SharedNativeMovementScene.cpp',
    'src/cn/protocol/CnMovement.h']
ADDED=['src/cn/world/CnNativePathCompletion.h','src/cn/world/CnNativePathCompletion.cpp']
CONTEXT=['src/cn/world/CnNativeCameraMotion.h','src/cn/world/CnNativeCameraMotion.cpp',
    'src/cn/world/CnNativeFrameClock.h','src/cn/world/CnNativeFrameClock.cpp',
    'src/cn/world/CnOutdoorCamera.h','src/cn/world/CnOutdoorCamera.cpp',
    'src/cn/world/CnOutdoorWindow.h','src/cn/world/CnOutdoorWindow.cpp',
    'src/cn/world/SharedInitialScene.h','src/cn/world/SharedInitialScene.cpp',
    'src/cn/world/SharedMovement.h','src/cn/world/SharedMovement.cpp',
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/game/SharedTaiwanMovement.h','src/game/SharedTaiwanMovement.cpp',
    'scripts/tw/native_movement.lua','scripts/cn/native_movement.lua']
SOURCES=MODIFIED+ADDED+CONTEXT+['docs/research/cn-native-path-completion-20261007.md']
FUNCTIONS=[('005395e0',16),('00539150',16),('00535d80',16),('005375c0',16),
    ('005368f0',16),('0048fcc0',8),('00539bf0',16)]

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed native path completion source')
    ledger_path=ROOT/'packet-route-ledger.json';prior=ledger_path.read_bytes();ledger=json.loads(prior)
    cat=ROOT/'dual-client-route-catalog-27';before=(cat/'source-file-manifest.json').read_bytes()
    if sha(before)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior source catalog manifest changed')
    previous=json.loads(before);captured=json.loads((out/'before-source-manifest.json').read_bytes())
    snapshots=[];changes=[];unchanged=[];pending=[]
    for rel in MODIFIED:
        raw=(out/'prior-sources'/rel).read_bytes();expected=previous[rel]['sha256']
        if sha(raw)!=expected or captured[rel]!=previous[rel]:raise ValueError('Before source changed: '+rel)
        snapshots.append({'path':'prior-sources/'+rel,'sha256':sha(raw),'bytes':len(raw),'original':str(SERVER/rel)})
        changes.append({'path':rel,'before_sha256':expected,'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':cat.relative_to(SERVER).as_posix()})
    for rel in CONTEXT:
        expected=previous[rel]['sha256']
        if sha((SERVER/rel).read_bytes())!=expected:raise ValueError('Context changed: '+rel)
        unchanged.append({'path':rel,'sha256':expected,'unchanged_from_catalog27':True})
    exe=CN.parent/'XJZ-CN/God2_opt.exe';pe_raw=exe.read_bytes()
    if sha(pe_raw)!=PIN:raise ValueError('Pinned CN PE changed')
    pe=pefile.PE(data=pe_raw,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32);native=[]
    for address,part in FUNCTIONS:
        path=RECOVERY/f'part_{part:04d}'/(address+'_FUN_'+address+'.c');source=path.read_bytes()
        match=re.search(rb'Address: 0x([0-9a-fA-F]+).*Size: (\d+) bytes',source)
        if not match or int(match.group(1),16)!=int(address,16):raise ValueError('Native extent differs')
        size=int(match.group(2));code=pe.get_data(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size)
        ins=list(md.disasm(code,int(address,16)))
        if len(code)!=size or sum(i.size for i in ins)!=size:raise ValueError('Incomplete native span')
        asm=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in ins)+'\n').encode()
        for ext,data,origin in [('.c',source,path),('.bin',code,exe),('.asm',asm,'pinned CN disassembly')]:
            pending.append(('native/functions/'+address+ext,data,origin))
        native.append({'address':address,'bytes':size,'native_sha256':sha(code),'source_sha256':sha(source),
            'decoded_bytes':sum(i.size for i in ins),'source_original':str(path)})
    calls_path=RECOVERY/'calls.tsv';calls_raw=calls_path.read_bytes()
    selected=[line for line in calls_raw.splitlines() if line.split(b'\t')[0] in
        {b'005395e0',b'00539150',b'00535d80',b'005375c0',b'005368f0',b'0048fcc0',b'00539bf0'}]
    pending.append(('native/call-edges.tsv',b'\n'.join(selected)+b'\n',calls_path))
    for name in ['cn-native-frame-clock-01','cn-native-camera-frame-01']:
        path=ROOT/name/'integration-manifest.json';raw=path.read_bytes()
        if sha(raw)!=ledger['cn_account_admission_evidence'][name]['artifact_sha256']['integration-manifest.json']:
            raise ValueError('Prior evidence changed')
        old={r['address']:r for r in json.loads(raw).get('native_spans',[])}
        for row in native:
            if row['address'] in old:
                for key in ['native_sha256','source_sha256']:
                    if row[key]!=old[row['address']][key]:raise ValueError('Prior native bytes differ')
        pending.append(('prior-manifests/'+name+'.json',raw,path))
    def save(rel,data,origin):
        path=out/rel;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'sha256':sha(data),'bytes':len(data),'original':str(origin)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel,data,origin in pending:save(rel,data,origin)
    save('prior-ledger.json',prior,ledger_path)
    save('prior-manifests/catalog27-source-files.json',before,cat/'source-file-manifest.json')
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    save('catalog-tool.py',(SERVER/'tools/reconstruction/dual_client_route_catalog.py').read_bytes(),SERVER/'tools/reconstruction/dual_client_route_catalog.py')
    dump(out/'source-adaptation-receipt.json',changes);dump(out/'unchanged-source-receipt.json',unchanged)
    gaps=['Actual deferred notification/current path/segment admission/reset/model/viewport/scheduler owners and formal Application/listeners/dispatch remain open.',
        'Native path planning has qualified source; actual pathfinder/append/overcapacity/wrapped/count0/mode/state variants remain open.',
        'Native5D server value contract/timing/permission remains open; byte-unconditional queue pop and empty(0,0) presentation are separate from animation completion.',
        'Initial camera invocation, unknown null/alias/dynamic object/frame variants, transfers/battle and TW native view remain open.',
        'All remaining gameplay paths and whole directional/state/variant/indirect/deferred denominator remain open; no full-route/runtime/native-render/deployment claim.']
    manifest={'kind':'actual both-axis frame completion ->deferred notification/current bounded native path ->next segment OR final state/target publication ->post-frame clock; distinct5D queue consumer qualified',
        'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':changes,'unchanged_context':unchanged,
        'native_spans':native,'call_edge_count':len(selected),'call_source_sha256':sha(calls_raw),'client_sha256':PIN,
        'new_source_files':2,'modified_cpp_files':3,'source_owner_chains_added':0,
        'new_phase_opcode_bindings':0,'new_unique_cn_phase_opcode_binding_values':0,'new_opcode_values':0,'new_complete_routes':0,
        'native_completed_path_planning_source_integrated':True,'deferred_path_before_clock_order_integrated':True,
        'native_count_capacity60_and_last_point_address_qualified':True,'actual_deferred_path_runtime_implemented':False,
        'animation_completion_promoted_to_server_ack':False,'native5d_empty_coordinates_qualified':True,
        'native5d_value_contract_complete':False,'native_overcapacity_or_malformed_path_qualified':False,
        'formal_application_hosted':False,'previous_goal_turn_classification':'progress: prior elapsed/post-frame clock source and catalog27 sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','asset_loaders_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN native path completion in existing independent frame owner',
        'version_scope':'cn','status':'已接動畫完成/延後通知後路徑快照/下一段或最終目標發布/後續時計順序；5D佇列consumer分開記錄，實際runtime與正式掛載未完成',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':0,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':'none',
        'shared_storage':['common position unchanged; native renderer/path targets remain distinct from authoritative saved position'],
        'native_form_qualifications':{'native_bounded_completion_plan':True,'deferred_path_clock_order':True,
            'server_ack_inferred_from_animation':False,'native5d_empty_queue_local_zero':True,
            'whole_opcode_variants_complete':False},'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Recover actual pending-ring/reset/deferred notification/runtime viewport ownership, preserving5D and animation distinctions; complete real permission/full5D/formal common dispatch.']+gaps
    dump(ledger_path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(snapshots),'native_functions':len(native),
        'native_call_edges':len(selected),'new_cpp_files':2,'modified_cpp_files':3,'new_partial_owner_chains':0,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
