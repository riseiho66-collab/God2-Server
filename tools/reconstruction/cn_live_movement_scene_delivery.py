"""Seal actual CN initial->live scene/cache/actor owner source without runtime."""
import json
import re
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN,PIN
from .cn_shared_movement_owner_delivery import sha,dump

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-live-movement-scene-owner-01'
ROUND='20261007-cn-live-movement-scene'
MODIFIED=['src/cn/world/SharedInitialScene.h','src/cn/world/SharedInitialScene.cpp',
    'src/cn/world/CnMapPassability.h','src/cn/world/CnOutdoorWindow.h','src/cn/world/CnOutdoorWindow.cpp']
ADDED=['src/cn/world/SharedNativeMovementScene.h','src/cn/world/SharedNativeMovementScene.cpp']
CONTEXT=['src/cn/world/SharedMovement.h','src/cn/world/SharedMovement.cpp',
    'src/cn/assets/CnSceneAssets.h','src/cn/assets/CnSceneAssets.cpp',
    'src/cn/world/CnOutdoorCamera.h','src/cn/world/CnOutdoorCamera.cpp',
    'src/cn/protocol/CnWorldEntry.h','src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/cn/world/SharedMovementPublication.h','src/cn/world/SharedMovementPublication.cpp',
    'src/game/SharedTaiwanMovement.h','src/game/SharedTaiwanMovement.cpp','scripts/tw/native_movement.lua','scripts/cn/native_movement.lua']
SOURCES=MODIFIED+ADDED+CONTEXT+['docs/research/cn-live-movement-scene-owner-20261007.md']
FUNCTIONS=[('00492e70',8),('00539150',16),('00537d40',16),('0045be20',5),
    ('0046c830',6),('0046d460',6),('0046f630',6),('0046ce10',6),('00473120',6),('00470c90',6)]

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed live-scene delivery')
    ledger_path=ROOT/'packet-route-ledger.json';prior=ledger_path.read_bytes();ledger=json.loads(prior)
    cat=ROOT/'dual-client-route-catalog-23';before=(cat/'source-file-manifest.json').read_bytes()
    if sha(before)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior source catalog manifest changed')
    previous=json.loads(before);captured=json.loads((out/'before-source-manifest.json').read_bytes())
    changes=[];unchanged=[];snapshots=[]
    for rel in MODIFIED:
        raw=(out/'prior-sources'/rel).read_bytes();expected=previous[rel]['sha256']
        if sha(raw)!=expected or captured[rel]!=previous[rel]:raise ValueError('Before source changed: '+rel)
        snapshots.append({'path':'prior-sources/'+rel,'sha256':sha(raw),'bytes':len(raw),'original':str(SERVER/rel)})
        changes.append({'path':rel,'before_sha256':expected,'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':cat.relative_to(SERVER).as_posix()})
    for rel in CONTEXT:
        expected=previous[rel]['sha256']
        if sha((SERVER/rel).read_bytes())!=expected:raise ValueError('Prior/context source changed: '+rel)
        unchanged.append({'path':rel,'sha256':expected,'unchanged_from_catalog23':True})
    exe=CN.parent/'XJZ-CN/God2_opt.exe';pe_raw=exe.read_bytes()
    if sha(pe_raw)!=PIN:raise ValueError('Pinned CN native PE changed')
    pe=pefile.PE(data=pe_raw,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32)
    recovery=CN.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
    native=[];pending=[]
    for address,part in FUNCTIONS:
        path=recovery/f'part_{part:04d}'/(address+'_FUN_'+address+'.c');source=path.read_bytes()
        match=re.search(rb'Address: 0x([0-9a-fA-F]+).*Size: (\d+) bytes',source)
        if not match or int(match.group(1),16)!=int(address,16):raise ValueError('Native function extent differs')
        size=int(match.group(2));code=pe.get_data(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size)
        if len(code)!=size:raise ValueError('Incomplete native span')
        ins=list(md.disasm(code,int(address,16)));asm=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in ins)+'\n').encode()
        for ext,data,origin in [('.c',source,path),('.bin',code,exe),('.asm',asm,'pinned CN disassembly')]:
            pending.append(('native/functions/'+address+ext,data,origin))
        native.append({'address':address,'bytes':size,'native_sha256':sha(code),'source_sha256':sha(source),
            'decoded_bytes':sum(i.size for i in ins),'source_original':str(path)})
    for name in ['cn-camera-map-resource-owner-01','cn-standalone-null-slot-01','shared-taiwan-movement-01']:
        p=ROOT/name/'integration-manifest.json';raw=p.read_bytes()
        if sha(raw)!=ledger['cn_account_admission_evidence'][name]['artifact_sha256']['integration-manifest.json']:
            raise ValueError('Prior evidence manifest changed')
        old=json.loads(raw);old_native={x['address']:x for x in old.get('native_spans',[])}
        for row in native:
            if row['address'] in old_native:
                original=old_native[row['address']]
                if original['native_sha256']!=row['native_sha256'] or original['source_sha256']!=row['source_sha256']:
                    raise ValueError('Historical native span differs')
        pending.append(('prior-manifests/'+name+'.json',raw,p))
    def save(rel,data,origin):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'sha256':sha(data),'bytes':len(data),'original':str(origin)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel,data,origin in pending:save(rel,data,origin)
    save('prior-ledger.json',prior,ledger_path)
    save('prior-manifests/catalog23-source-files.json',before,cat/'source-file-manifest.json')
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    dump(out/'source-adaptation-receipt.json',changes);dump(out/'unchanged-source-receipt.json',unchanged)
    gaps=['Actual native movement Authority for timing/pending/reset/permission/full5D, viewport/camera supplier and formal Application/listeners/dispatch hosting remain open.',
        'Actual renderer model/animation/frame/object changes, native runtime handles/type7 and live profile replacement/invalidation remain open; declared-frame subset only.',
        'Mode1/3,61/CF/transfer/battle/recovery and unresolved resource/null/alias/path/coordinate variants remain open.',
        'TW native scene supplier remains separate and unhosted; CN grid is not automatically TW native evidence.',
        'Position/cache/model publication is ordered, not one ACID transaction; post-CAS failure retains saved state and needs fresh native entry.',
        'Every remaining gameplay path and whole directional/phase/state/variant/indirect/deferred denominator remains open; no native receipt/render/deployment claim.']
    manifest={'kind':'actual same initial CN native profile/ready lease ->concrete live scene/actor/direction/cache owner ->pre-CAS camera/resource preparation ->actual saved-position-qualified cache/camera/actor publication ->future movement snapshots',
        'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':changes,'unchanged_context':unchanged,'native_spans':native,
        'client_sha256':PIN,'new_source_files':2,'modified_cpp_files':5,'source_owner_chains_added':1,
        'new_phase_opcode_bindings':0,'new_unique_cn_phase_opcode_binding_values':0,'new_opcode_values':0,'new_complete_routes':0,
        'concrete_shared_movement_world_owner':True,'exact_initial_assets_instance_and_one_use_claim':True,
        'actual_native_permission_and_reply_authority_implemented':False,'formal_application_hosted':False,
        'native_camera_not_derived_from_packet':True,'camera_cache_prepared_before_common_position_cas':True,
        'native_viewport_camera_source_still_required':True,'declared_frame_profile_subset_only':True,
        'cn_grid_promoted_as_tw_evidence':False,'position_cache_acid_transaction_claimed':False,
        'previous_goal_turn_classification':'progress: TW ordinary native movement/common position/dual-native peer source sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','asset_loaders_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN actual live native movement scene/actor/cache publication owner',
        'version_scope':'cn','status':'已接同一初始原生資源實例/共用ready租約/持續場景格網/移動前camera資源準備/提交後cache與角色發布；權限回覆及正式掛載未完成',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,
        'source_owner_chains_added':1,'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'storage_writes':'none added; existing shared position CAS supplies before/after; no phase1 production DB execution',
        'shared_storage':['common character identity/ownership/position; transient native actor/camera/cache retained separately'],
        'native_form_qualifications':{'same_initial_assets_instance':True,'native_initial_direction':True,
            'live_scene_after_first_move':True,'pre_cas_native_camera_cache_preparation':True,'one_use_pending_publication':True,
            'mutation_callback_reentry_blocked':True,'native_render_acceptance':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Recover actual native timing/pending/reset/full5D and viewport/camera source, bind this live scene owner and TW own native view into formal common dispatch.']+gaps
    dump(ledger_path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(snapshots),'cn_native_functions':len(native),
        'new_cpp_files':2,'modified_cpp_files':5,'new_cn_partial_owner_chains':1,'new_phase_bindings':0,
        'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
