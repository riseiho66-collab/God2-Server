"""Seal native prior-frame elapsed and post-frame clock ordering; no gameplay execution."""
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
NAME='cn-native-frame-clock-01'
ROUND='20261007-cn-native-frame-clock'
MODIFIED=['src/cn/world/SharedNativeMovementScene.h','src/cn/world/SharedNativeMovementScene.cpp']
ADDED=['src/cn/world/CnNativeFrameClock.h','src/cn/world/CnNativeFrameClock.cpp']
CONTEXT=['src/cn/world/CnNativeCameraMotion.h','src/cn/world/CnNativeCameraMotion.cpp',
    'src/cn/world/CnOutdoorCamera.h','src/cn/world/CnOutdoorCamera.cpp',
    'src/cn/world/CnOutdoorWindow.h','src/cn/world/CnOutdoorWindow.cpp',
    'src/cn/world/SharedInitialScene.h','src/cn/world/SharedInitialScene.cpp',
    'src/cn/world/SharedMovement.h','src/cn/world/SharedMovement.cpp',
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/game/SharedTaiwanMovement.h','src/game/SharedTaiwanMovement.cpp',
    'scripts/tw/native_movement.lua','scripts/cn/native_movement.lua']
SOURCES=MODIFIED+ADDED+CONTEXT+['docs/research/cn-native-frame-clock-20261007.md']
FUNCTIONS=[('004892b0',8),('0048a4d0',8),('0048aa10',8),('005395e0',16),
    ('00539150',16),('004937b0',8),('00481600',7)]

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed native frame clock source')
    ledger_path=ROOT/'packet-route-ledger.json';prior=ledger_path.read_bytes();ledger=json.loads(prior)
    cat=ROOT/'dual-client-route-catalog-26';before=(cat/'source-file-manifest.json').read_bytes()
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
        unchanged.append({'path':rel,'sha256':expected,'unchanged_from_catalog26':True})
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
        {b'0048a4d0',b'0048aa10',b'005395e0',b'00539150',b'004937b0',b'00481600'}]
    pending.append(('native/call-edges.tsv',b'\n'.join(selected)+b'\n',calls_path))
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
    imports=[{'dll':entry.dll.decode('ascii'),'name':item.name.decode('ascii'),'slot_va':f'{item.address:08x}'}
        for entry in pe.DIRECTORY_ENTRY_IMPORT for item in entry.imports if item.name==b'timeGetTime']
    clock_slot=pe.get_data(0x007ebcb4-pe.OPTIONAL_HEADER.ImageBase,4)
    if clock_slot!=bytes.fromhex('60000070'):raise ValueError('Pinned indirect clock slot differs')
    pending.append(('native/indirect-clock-slot-007ebcb4.bin',clock_slot,exe))
    # Protected/rebuilt PE does not expose this symbol in its declared imports.
    # Keep recovered naming separate from pinned call-site/slot bytes.
    clock_identity={'indirect_slot_va':'007ebcb4','pinned_raw_slot_hex':clock_slot.hex(),
        'recovered_c_symbol':'timeGetTime_exref','named_pe_import_matches':imports,
        'runtime_api_identity_confirmed':False,'raw_slot_used_as_runtime_pointer':False}
    for name in ['cn-native-camera-frame-01','cn-initial-camera-source-01']:
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
    save('prior-manifests/catalog26-source-files.json',before,cat/'source-file-manifest.json')
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    save('catalog-tool.py',(SERVER/'tools/reconstruction/dual_client_route_catalog.py').read_bytes(),SERVER/'tools/reconstruction/dual_client_route_catalog.py')
    dump(out/'source-adaptation-receipt.json',changes);dump(out/'unchanged-source-receipt.json',unchanged)
    gaps=['Actual runtime loop/observer/viewport/path/model authority and formal Application/listeners/dispatch remain open.',
        'Pre-initialization005395E0, message/render/frame counter/exit/mode/state12 and unrecovered clock-loop branches remain open.',
        'Native ring insertion, notifications/path completion/reset and server timing/permission/full5D authority remain open; sending2E precedes local ring admission.',
        'Initial camera invocation, unknown null/alias/dynamic object/frame variants, transfers/battle and TW native view remain open.',
        'All remaining gameplay paths and whole directional/state/variant/indirect/deferred denominator remain open; no full-route/runtime/native-render/deployment claim.']
    manifest={'kind':'native retained prior elapsed ->real scene motion/cache/model publication ->actual completed-loop timeGetTime observations ->qualified next clock publication',
        'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':changes,'unchanged_context':unchanged,
        'native_spans':native,'indirect_clock_identity':clock_identity,'call_edge_count':len(selected),'call_source_sha256':sha(calls_raw),'client_sha256':PIN,
        'new_source_files':2,'modified_cpp_files':2,'source_owner_chains_added':0,
        'new_phase_opcode_bindings':0,'new_unique_cn_phase_opcode_binding_values':0,'new_opcode_values':0,'new_complete_routes':0,
        'native_previous_frame_elapsed_integrated':True,'native_post_frame_clock_source_integrated':True,
        'conditional_second_clock_call_and_unsigned_wrap_preserved':True,'primary_bootstrap_idiv32_preserved':True,
        'new_clock_used_for_current_frame':False,'clock_pe_defaults_used_as_runtime':False,
        'raw_protected_pe_clock_slot_promoted_to_windows_api':False,
        'actual_scheduler_authority_implemented':False,'native_path_advance_implemented':False,
        'local_ring_admission_used_as_server_permission':False,'formal_application_hosted':False,
        'previous_goal_turn_classification':'progress: independent native frame source and catalog26 sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','asset_loaders_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN native prior elapsed/post-frame clock in existing scene owner',
        'version_scope':'cn','status':'已接上一輪時間差驅動移動/畫格後條件式取時/下一輪5至200毫秒限制；實際scheduler與正式掛載未完成',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':0,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':'none',
        'shared_storage':['same common saved position; renderer cadence separate, no gameplay DB mutation'],
        'native_form_qualifications':{'native_post_update_clock':True,'native_unsigned_time_wrap':True,
            'next_frame_elapsed_only':True,'actual_frame_scheduler':False,
            'server_movement_permission_from_client_ring':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Connect actual native ring/path completion/reset and runtime viewport owner, preserving pre-send/local-ring ordering; complete full5D authority and formal common dispatch.']+gaps
    dump(ledger_path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(snapshots),'native_functions':len(native),
        'native_call_edges':len(selected),'new_cpp_files':2,'modified_cpp_files':2,'new_partial_owner_chains':0,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
