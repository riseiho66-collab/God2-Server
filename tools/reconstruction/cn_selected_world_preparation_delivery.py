"""Retain selected-world preparation source provenance; no runtime or tests."""
import json
from pathlib import Path
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import PIN
from .cn_shared_movement_owner_delivery import sha, dump

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-selected-world-preparation-01'
ROUND='20261007-cn-selected-world-preparation'
NEW=['src/cn/world/SharedWorldPreparation.h','src/cn/world/SharedWorldPreparation.cpp']
MODIFIED=['src/cn/auth/SharedWorldSelection.h','src/cn/auth/SharedWorldSelection.cpp',
    'src/game/SharedWorldPresence.h','src/cn/world/SharedWorldReady.h','src/cn/world/SharedWorldReady.cpp',
    'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp',
    'tools/reconstruction/dual_client_route_catalog.py']
CONTEXT=['src/cn/world/SharedInitialScene.h','src/cn/world/SharedInitialScene.cpp',
    'src/cn/world/SharedNativeMovementScene.h','src/cn/world/SharedNativeMovementScene.cpp',
    'src/cn/world/SharedSceneIdentity.h','src/cn/world/SharedSceneIdentity.inc',
    'src/cn/world/SharedActorVisibility.h','src/cn/world/SharedActorVisibility.cpp',
    'src/cn/protocol/CnWorldEntry.h','src/cn/protocol/CnWorldSelectionStatus.h',
    'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/cn/assets/CnSceneAssets.h','src/cn/assets/CnSceneAssets.cpp',
    'src/db/RecoveredCharacterRepository.h','src/db/NativeMapCatalog.h',
    'src/game/SharedWorldPresence.cpp','src/cn/auth/SharedLoginComposition.h','src/cn/auth/SharedLoginComposition.cpp']
SOURCES=NEW+MODIFIED+CONTEXT+['docs/research/cn-selected-world-preparation-20261007.md',
    'tools/reconstruction/cn_selected_world_preparation_delivery.py']
PRIOR=['cn-world-selection-owner-01','cn-world-ready-owner-01','cn-initial-scene-provider-01',
    'cn-live-movement-scene-owner-01','cn-shared-listener-host-01','cn-ready-world-dispatch-01']


def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed')
    catalog=(out/'catalog38-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog);before=json.loads((out/'before-source-manifest.json').read_bytes())
    adaptations=[];unchanged=[]
    for rel in MODIFIED:
        b=(out/'prior-sources'/rel).read_bytes();row=before[rel]
        if sha(b)!=row['sha256'] or len(b)!=row['bytes'] or sha(b)!=known[rel]['sha256']:
            raise ValueError('Before source differs '+rel)
        adaptations.append({'path':rel,'before_sha256':sha(b),'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-38'})
    for rel in CONTEXT:
        b=(SERVER/rel).read_bytes()
        if rel in known and sha(b)!=known[rel]['sha256']:raise ValueError('Context changed '+rel)
        unchanged.append({'path':rel,'sha256':sha(b),'previously_cataloged':rel in known})
    for rel in NEW:
        if rel in known:raise ValueError('New source already cataloged')
    snapshots=[]
    def save(rel,data,origin):
        path=out/rel;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'sha256':sha(data),'bytes':len(data),'original':str(origin)})
    receipts=[]
    for name in PRIOR:
        path=ROOT/name/'integration-manifest.json';b=path.read_bytes()
        if sha(b)!=ledger['cn_account_admission_evidence'][name]['artifact_sha256']['integration-manifest.json']:
            raise ValueError('Prior receipt differs '+name)
        if json.loads(b).get('client_sha256')!=PIN:raise ValueError('Pinned client differs '+name)
        save('prior-manifests/'+name+'.json',b,path)
        receipts.append({'artifact':name,'sha256':sha(b),'client_sha256':PIN,'prior_native_contracts_reused':True})
    path=ROOT/'cn-ready-world-dispatch-01/source-accounting-addendum.json';b=path.read_bytes()
    if sha(b)!=ledger['cn_account_admission_evidence']['cn-ready-world-dispatch-01']['artifact_sha256'][path.name]:
        raise ValueError('Prior accounting addendum differs')
    save('prior-manifests/cn-ready-world-source-accounting-addendum.json',b,path)
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',prior,lp)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    gaps=['Real native actor allocator and complete scene-qualified02/2A/native login/world data suppliers remain missing.',
        'Actual bootstrap/entered/periodic controls and common gameplay timing/permission/directory/resource authorities remain incomplete.',
        'Transfer retained/reload lifecycle and its actual movement owner must be supplied; required qualifier is not a completed transfer route.',
        'Application production world supplier must provide this Selected continuation and full native account/world suppliers; no plan is enabled.',
        'All remaining native directional/state/variant paths and whole-game denominator remain open.']
    facts={'client_sha256':PIN,'source_chain':'pending owned choice ->same common saved position ->required actual reservation ->common generation lease ->native initial scene or qualified transfer ->existing ready/mixed ingress ->supplied02-before2A',
        'same_selection_character_repository_map_catalog_presence_visibility_required':True,
        'position_write_or_default_spawn_added':False,'actor_handle_allocated_from_common_id':False,
        'normal_initial_scene_source_connected':True,'normal_native_movement_scene_adoption_deferred_until_ready':True,
        'exactly_one_eager_or_deferred_movement_source':True,'prepared_movement_owner_retained_before_child_attachment':True,
        'transfer_qualifier_required_without_normal_initial_snapshot':True,'transfer_actual_lifecycle_implemented':False,
        'failure_close_destructor_reservation_release_once':True,'complete_supplied_02_2A_bytes_preserved':True,
        'actual_allocator_or_native_reply_supplier_implemented':False,'native_contracts_newly_recovered':False,
        'new_opcode_values':0,'new_phase_opcode_bindings':0,'new_complete_routes':0,'production_plan_enabled':False}
    save('selected-world-preparation-source-relations.json',(json.dumps(facts,ensure_ascii=False,indent=2)+'\n').encode(),
        'static conditional source composition; existing native contracts')
    listed={r['path'] for r in snapshots}
    for path in sorted(out.rglob('*')):
        if path.is_file() and path.relative_to(out).as_posix() not in listed:
            snapshots.append({'path':path.relative_to(out).as_posix(),'sha256':sha(path.read_bytes()),
                'bytes':path.stat().st_size,'original':'captured before source edits'})
    manifest={'kind':'actual pending Selected choice/common storage/native scene/live movement/ready-world conditional source composition',
        'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':adaptations,'unchanged_context':unchanged,
        'retained_native_receipts':receipts,'client_sha256':PIN,'new_cpp_files':2,'modified_cpp_files':7,
        'modified_catalog_tools':1,'source_owner_chains_added':1,'new_phase_opcode_bindings':0,
        'new_opcode_values':0,'new_complete_routes':0,'formal_application_hosted':False,
        'actual_common_backend_implemented':False,'actual_native_supplier_implemented':False,
        'previous_goal_turn_classification':'progress: catalog38 ready-world bounded mixed source composition plus retained source-label correction',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','asset_loaders_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN actual Selected common world preparation and deferred native movement scene composition',
        'version_scope':'cn','status':'已串同一共用存檔/角色lease/原生場景/Selected入場來源，補ready後建立實際移動場景；原生值、配置與權威供應未完成',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,
        'source_owner_chains_added':1,'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'storage_writes':'none added; reads actual common saved position and reserves generation-qualified presence when later enabled',
        'shared_storage':['same actual selection RecoveredCharacterRepository','same actual selection NativeMapCatalog','same SharedWorldPresence/SharedActorVisibility'],
        'native_form_qualifications':{'full_native_data_required':True,'actual_common_allocator_supplied':False,
            'normal_concrete_native_movement_adoption_after_ready':True,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['selected_world_preparation']={'root':out.relative_to(SERVER).as_posix(),
        'facts':'selected-world-preparation-source-relations.json','new_opcode_values':0,'complete_gameplay_routes':0,'all_variants_complete':False}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Recover/implement actual native full account/world data and scene allocator/authorities for the now composed Selected and ready-world source; continue missing native gameplay variants.']+gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'new_cpp_files':2,'modified_cpp_files':7,
        'new_partial_compositions':1,'new_phase_source_bindings':0,'new_complete_routes':0,'tests_run':False}))


if __name__=='__main__':main()
