"""Seal common Application/CN listener/login composition source, without runtime/tests."""
import json
from pathlib import Path
import pefile
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN, PIN
from .cn_shared_movement_owner_delivery import sha, dump

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-shared-listener-host-01'
ROUND='20261007-cn-shared-listener-host'
ADDED=['src/net/ConnectionIdentity.h','src/net/ConnectionIdentity.cpp',
    'src/cn/net/SharedCredentialServer.h','src/cn/net/SharedCredentialServer.cpp',
    'src/cn/auth/SharedLoginComposition.h','src/cn/auth/SharedLoginComposition.cpp']
MODIFIED=['src/core/Application.h','src/core/Application.cpp','src/net/TcpServer.cpp',
    'src/cn/auth/SharedWorldSelection.h','src/cn/auth/SharedWorldSelection.cpp',
    'tools/reconstruction/dual_client_route_catalog.py']
CONTEXT=['src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/cn/net/CnTransportSession.h','src/cn/net/CnTransportSession.cpp',
    'src/cn/auth/SharedCredentialStage.h','src/cn/auth/SharedCredentialStage.cpp',
    'src/cn/auth/SharedAccountVerifier.h','src/cn/auth/SharedAccountVerifier.cpp',
    'src/cn/auth/SharedAccountSuccess.h','src/cn/auth/SharedAccountSuccess.cpp',
    'src/cn/auth/SharedAccountSelection.h','src/cn/auth/SharedAccountSelection.cpp',
    'src/auth/SharedWorldAdmission.h','src/auth/SharedWorldAdmission.cpp',
    'src/db/NativeMapCatalog.h','src/db/SqliteDatabase.h','src/net/IoContextPool.h',
    'src/net/IoContextPool.cpp','src/core/Config.h','src/net/TcpServer.h',
    'src/main.cpp','CMakeLists.txt']
SOURCES=ADDED+MODIFIED+CONTEXT+['docs/research/cn-shared-listener-host-20261007.md',
    'tools/reconstruction/cn_shared_listener_host_delivery.py']
PRIOR=['cn-account-success-owner-01','cn-world-selection-owner-01',
    'shared-world-admission-owner-01','cn-world-entry-projections-01']

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed delivery')
    ledger_path=ROOT/'packet-route-ledger.json';prior=ledger_path.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed during source work')
    before=(out/'catalog29-source-files.json').read_bytes()
    if sha(before)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog29 digest differs')
    known=json.loads(before)
    captured=json.loads((out/'before-source-manifest.json').read_bytes())
    captured.update(json.loads((out/'additional-before-source-manifest.json').read_bytes()))
    changes=[];unchanged=[];pending=[]
    for rel in MODIFIED:
        row=captured[rel];raw=(out/'prior-sources'/rel).read_bytes()
        if sha(raw)!=row['sha256'] or len(raw)!=row['bytes']:raise ValueError('Before source changed '+rel)
        if rel in known and sha(raw)!=known[rel]['sha256']:raise ValueError('Catalog source changed '+rel)
        changes.append({'path':rel,'before_sha256':sha(raw),'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-29',
            'previously_cataloged':rel in known})
    for rel in CONTEXT:
        raw=(SERVER/rel).read_bytes()
        if rel in known and sha(raw)!=known[rel]['sha256']:raise ValueError('Context changed '+rel)
        unchanged.append({'path':rel,'sha256':sha(raw),'previously_cataloged':rel in known})
    exe=CN.parent/'XJZ-CN/God2_opt.exe';pe_raw=exe.read_bytes()
    if sha(pe_raw)!=PIN:raise ValueError('Pinned CN input changed')
    pe=pefile.PE(data=pe_raw,fast_load=True);native={}
    for name in PRIOR:
        path=ROOT/name/'integration-manifest.json';raw=path.read_bytes()
        if sha(raw)!=ledger['cn_account_admission_evidence'][name]['artifact_sha256']['integration-manifest.json']:
            raise ValueError('Prior evidence changed '+name)
        pending.append(('prior-manifests/'+name+'.json',raw,path))
        for row in json.loads(raw).get('native_spans',[]):
            address=int(row['address'],16);code=pe.get_data(address-pe.OPTIONAL_HEADER.ImageBase,row['bytes'])
            if len(code)!=row['bytes'] or sha(code)!=row['native_sha256']:raise ValueError('Native input changed '+row['address'])
            if row['address'] in native and native[row['address']]['native_sha256']!=row['native_sha256']:
                raise ValueError('Conflicting pinned evidence')
            native[row['address']]=row
    snapshots=[]
    def save(rel,data,origin):
        path=out/rel;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'sha256':sha(data),'bytes':len(data),'original':str(origin)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel,data,origin in pending:save(rel,data,origin)
    save('prior-ledger.json',prior,ledger_path)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md','docs/GOAL_ACCEPTANCE.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    for path in sorted(out.rglob('*')):
        if path.is_file() and path.relative_to(out).as_posix() not in {r['path'] for r in snapshots}:
            snapshots.append({'path':path.relative_to(out).as_posix(),'sha256':sha(path.read_bytes()),
                'bytes':path.stat().st_size,'original':'captured before source adaptation'})
    gaps=['Qualified native seed/1D/0A/billing/07/1F and source/grant/alias lineage are mandatory; no default suppliers or production plan are installed.',
        'Actual Selected shared actor/scene/full02/2A/bootstrap/readiness/later gameplay and TW common registry enrollment remain open.',
        'Conditional Application listener/login composition is connected in source only; builds/runtime/socket lifecycle/native acceptance remain deferred.',
        'Concrete IPv4 directory mapping only; wildcard/NAT/IPv6 advertisement and alternate directory forms remain unqualified.',
        'Credential revision/revocation/cross-process key persistence and all native state/variant/indirect/deferred/gameplay denominator gaps remain open.']
    manifest={'kind':'actual shared Application repositories ->conditional CN owned listeners ->verified raw UI ->actual account/world success controller composition',
        'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':changes,'unchanged_context':unchanged,
        'native_spans':list(native.values()),'native_spans_newly_recovered':0,'client_sha256':PIN,
        'new_source_files':6,'modified_cpp_files':5,'modified_catalog_tools':1,
        'source_owner_chains_added':0,'new_phase_opcode_bindings':0,'new_opcode_values':0,'new_complete_routes':0,
        'conditional_application_listener_source_connected':True,'existing_success_controllers_composed':True,
        'same_application_account_character_map_repositories':True,'same_game_owner':True,
        'shared_nonwrapping_connection_identity':True,'pending_accept_and_live_connection_budget':True,
        'full_native_value_suppliers_implemented':False,'production_plan_installed':False,
        'formal_application_hosted':False,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'remaining':gaps,**{k:False for k in ['build_run','tests_run','runtime_run','lua_executed',
            'asset_loaders_executed','deployed','production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN shared Application listener and actual login controller composition',
        'version_scope':'tw-cn','status':'已接條件式Application監聽/共用認證資料與連線ID/原生成功controller組合；完整原生值及正式啟用未完成',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':0,
        'formal_application_hosted':False,'conditional_application_source_hosted':True,'complete_gameplay_routes_added':0,
        'storage_writes':'none during phase1; future controllers use same actual Application repositories',
        'shared_storage':['existing AccountRepository','existing RecoveredCharacterRepository','existing read-only NativeMapCatalog'],
        'native_form_qualifications':{'existing_full_native_success_controllers_composed':True,
            'native_values_supplied':False,'production_plan_installed':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Recover/implement full native1D/billing and07/1F/common-ID suppliers and actual Selected world authority for the now connected conditional source host.']+gaps
    dump(ledger_path,ledger)
    print(json.dumps({'artifact':str(out),'new_cpp_sources':6,'modified_cpp_sources':5,'snapshots':len(snapshots),
        'conditional_application_source_hosted':True,'production_plan_installed':False,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
