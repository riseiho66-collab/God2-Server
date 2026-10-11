"""Seal bounded mixed C2S composition and retained evidence; source accounting only."""
import json
from pathlib import Path
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import PIN
from .cn_shared_movement_owner_delivery import sha, dump

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-ready-world-dispatch-01'
ROUND='20261007-cn-ready-world-dispatch'
NEW=['src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp']
MODIFIED=['tools/reconstruction/dual_client_route_catalog.py']
CONTEXT=['src/cn/world/SharedWorldReady.h','src/cn/world/SharedWorldReady.cpp',
    'src/cn/world/SharedMovement.h','src/cn/world/SharedMovement.cpp',
    'src/cn/world/SharedDirectory.h','src/cn/world/SharedDirectory.cpp',
    'src/cn/world/SharedGenericDirectory.h','src/cn/world/SharedGenericDirectory.cpp',
    'src/cn/world/SharedSpecialDirectory.h','src/cn/world/SharedSpecialDirectory.cpp',
    'src/cn/auth/SharedWorldSelection.h','src/cn/auth/SharedWorldSelection.cpp',
    'src/cn/protocol/CnMovement.h','src/cn/protocol/CnDirectoryWire.h',
    'src/cn/protocol/CnGenericDirectoryWire.h','src/cn/protocol/CnSpecialDirectoryWire.h',
    'src/cn/protocol/CnDirectorySelection.h','src/cn/protocol/CnCharacterSummary.h',
    'src/cn/protocol/CnTransport.h','src/cn/net/SharedCredentialConnection.h',
    'src/cn/net/SharedCredentialConnection.cpp','src/game/SharedWorldPresence.h',
    'src/game/SharedWorldPresence.cpp']
SOURCES=NEW+MODIFIED+CONTEXT+['docs/research/cn-ready-world-dispatch-20261007.md',
    'tools/reconstruction/cn_ready_world_dispatch_delivery.py']
PRIOR=['cn-world-ready-owner-01','cn-shared-movement-owner-01',
    'cn-native-directory-owner-01','cn-generic-directory-owner-01',
    'cn-special-directory-owner-01','cn-summary-world-lineage-01']


def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed')
    catalog=(out/'catalog37-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog);before=json.loads((out/'before-source-manifest.json').read_bytes())
    adaptations=[];unchanged=[]
    for rel in MODIFIED:
        b=(out/'prior-sources'/rel).read_bytes();row=before[rel]
        if sha(b)!=row['sha256'] or len(b)!=row['bytes'] or sha(b)!=known[rel]['sha256']:
            raise ValueError('Before source differs')
        adaptations.append({'path':rel,'before_sha256':sha(b),'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-37'})
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
    native_receipts=[]
    for name in PRIOR:
        rel='integration-manifest.json';path=ROOT/name/rel;b=path.read_bytes()
        if sha(b)!=ledger['cn_account_admission_evidence'][name]['artifact_sha256'][rel]:
            raise ValueError('Prior native receipt differs '+name)
        receipt=json.loads(b)
        if receipt.get('client_sha256')!=PIN:raise ValueError('Prior pinned client differs '+name)
        native_receipts.append({'artifact':name,'receipt_sha256':sha(b),'client_sha256':PIN,
            'prior_native_contract_reused_without_reanalysis':True})
        save('prior-manifests/'+name+'.json',b,path)
    path=ROOT/'cn-ready-bootstrap-order-agent-01/worker-control-contract.json'
    b=path.read_bytes()
    expected=ledger['cn_account_admission_evidence']['cn-ready-bootstrap-order-agent-01']['artifact_sha256']
    if sha(b)!=expected['worker-control-contract.json']:raise ValueError('Worker control contract differs')
    save('native/worker-control-contract.json',b,path)
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',prior,lp)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    gaps=['Actual Application world-preparation supplier does not yet use this composition factory.',
        'Real native login/world suppliers and ongoing30/36 controls/semantics/replies remain missing.',
        'Directory/movement actual common authorities, native rules, data and CN NPC resource mappings remain incomplete.',
        'Dispatcher is bounded to six C2S opcode values; D1(27/28), other94/B0/A4, scene1C/transfer and all other gameplay variants remain open.',
        'Whole-game state/variant/direction denominator and completed route count remain unknown.']
    facts={'client_sha256':PIN,'phase':'world-connection-1-ready','initial_ready_owner_unchanged':True,
        'exact_same_connection_presence_visibility_generation_lease':True,
        'controllers_attach_only_after_real_ready':True,'all_records_preflighted_before_effects':True,
        'record_order_preserved':True,'inline_or_deferred_completion_serialization':True,
        'mode0_generic_special_only':True,'requires_actual_retained_suppliers':True,
        'ongoing_control_callback_independent_from_bootstrap':True,'unknown_or_truncated_records_rejected_not_discarded':True,
        'uses_s2c_lengths_for_c2s_split':False,'aggregate_atomic_gameplay_transaction':False,
        'dispatcher_scope':[{'opcode':'2E','bytes':7,'target':'SharedMovement'},
            {'opcode':'94','bytes':9,'target':'SharedDirectory three selectors both modes or SharedGenericDirectory22 selectors mode0'},
            {'opcode':'A4','bytes':3,'target':'SharedDirectory three selectors FF/01'},
            {'opcode':'D1','bytes':3,'target':'SharedSpecialDirectory25/26 mode0'},
            {'opcode':'30','bytes':2,'target':'required actual ongoing controls; literal payload00'},
            {'opcode':'36','bytes':9,'target':'required actual ongoing controls; full opaque payload8'}],
        'new_opcode_values':0,'new_unique_phase_opcode_values':0,'new_complete_routes':0,
        'native_response_causality_or_rules_newly_recovered':False,'actual_application_hosted':False,
        'actual_common_authority_implemented':False,'source_only_not_runtime_acceptance':True}
    save('ready-world-dispatch-source-relations.json',(json.dumps(facts,ensure_ascii=False,indent=2)+'\n').encode(),
        'bounded source composition; retained pinned native contracts')
    listed={r['path'] for r in snapshots}
    for path in sorted(out.rglob('*')):
        if path.is_file() and path.relative_to(out).as_posix() not in listed:
            snapshots.append({'path':path.relative_to(out).as_posix(),'sha256':sha(path.read_bytes()),
                'bytes':path.stat().st_size,'original':'captured before source edits'})
    manifest={'kind':'same prepared common actor ->unchanged native readiness ->ordered bounded mixed C2S dispatch ->retained actual common owner controllers',
        'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':adaptations,'unchanged_context':unchanged,
        'retained_native_receipts':native_receipts,'client_sha256':PIN,
        'new_cpp_files':2,'modified_cpp_files':0,'modified_catalog_tools':1,
        'source_owner_chains_added':1,'new_phase_opcode_bindings':6,'new_opcode_values':0,
        'new_unique_phase_opcode_values':0,'new_complete_routes':0,
        'formal_application_hosted':False,'actual_common_backend_implemented':False,
        'previous_goal_turn_classification':'progress: catalog37 bounded D1(25/26) fullF9 common-lease owner sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','asset_loaders_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN initial ready to bounded mixed world C2S common-owner composition',
        'version_scope':'cn','status':'已串同一準備lease的原入場owner及六opcode混合順序分派；實際權威供應與Application世界掛載未完成',
        'native_c2s_by_phase':{'world':['2E','94','A4','D1','30','36']},'native_s2c_by_phase':{},
        'source_paths':SOURCES,'source_owner_chains_added':1,'formal_application_hosted':False,
        'complete_gameplay_routes_added':0,'storage_writes':'delegated to existing qualified owners only; no new writes or tables',
        'shared_storage':['same common presence/visibility actor lease; existing position CAS remains in movement owner'],
        'native_form_qualifications':{'bounded_c2s_opcodes':6,'whole_opcode_variants_complete':False,
            'new_native_response_causality_recovered':False,'requires_real_suppliers':True},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['ready_world_dispatch']={'root':out.relative_to(SERVER).as_posix(),
        'facts':'ready-world-dispatch-source-relations.json','scoped_c2s_opcodes':['2E','94','A4','D1','30','36'],
        'new_opcode_values':0,'complete_gameplay_routes':0,'all_variants_complete':False}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Connect actual Application native world-preparation suppliers to bounded ready-world factory; recover remaining gameplay variants and real common directory/control authorities.']+gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'new_cpp_files':2,
        'new_partial_compositions':1,'new_overlapping_phase_source_bindings':6,'new_unique_phase_opcode_values':0,
        'new_complete_routes':0,'tests_run':False}))


if __name__=='__main__':main()
