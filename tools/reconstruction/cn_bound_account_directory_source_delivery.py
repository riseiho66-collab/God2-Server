"""Retain actual bound CN directory source; static source/file accounting."""
import difflib
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT

NAME='cn-bound-account-directory-source-01'
ROUND='20261008-cn-bound-account-directory-source'
SOURCES=('src/cn/net/SharedListenerRegistry.h','src/cn/net/SharedListenerRegistry.cpp',
    'src/cn/auth/SharedAccountDirectorySource.h','src/cn/auth/SharedAccountDirectorySource.cpp',
    'src/cn/net/SharedCredentialServer.h','src/cn/net/SharedCredentialServer.cpp',
    'src/cn/auth/SharedLoginComposition.cpp','src/cn/auth/SharedAccountSuccess.h',
    'src/cn/auth/SharedAccountSuccess.cpp','src/cn/auth/SharedIssuedAccountSource.h',
    'src/cn/auth/SharedIssuedAccountSource.cpp',
    'docs/research/cn-bound-account-directory-source-20261008.md',
    'tools/reconstruction/cn_bound_account_directory_source_delivery.py',
    'tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
    'Actual native group/billing/load/location/configured-slot metadata and profile40/billing16/rights/revision/deadline/summaries remain unconfigured.',
    'Concrete IPv4/single endpoint per target is the qualified host form; wildcard/NAT/IPv6/public advertisement/multi-endpoint and independent account subsets remain open.',
    'Registry represents managed bind/start/stop ownership, not network health/confirmed delivery/native acceptance.',
    'All complete world/bootstrap/equipment/scene/ACT providers, TW common registry/native PC/web/WSS hosting, gameplay/numeric extension and whole-game denominator remain open.']

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Fresh before-source snapshot required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    old={r['path']:(out/r['snapshot']).read_bytes() for r in before}
    books=('docs/PACKET_CONNECTION_GOAL_20261006.md',
        'artifacts/integration/packet-connections-20261006/packet-route-ledger.json')
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{ext}' for ext in ('json','md')}
    protected=[]
    for row in before:
        rel=row['path']
        if sha(old[rel])!=row['sha256']:raise RuntimeError('Before snapshot differs')
        if rel not in set(SOURCES)|set(books)|reports:
            if (ROOT/rel).read_bytes()!=old[rel]:raise RuntimeError('Protected context differs: '+rel)
            protected.append(row)
    prior=(out/'retained-prior/cn-issued-account-source-01/manifest.json').read_bytes()
    if sha(prior)!='129b0c73cac386d6fad03a65b96957fb97e22e09e2cb991e498d5de9085bc24f' or not json.loads(prior)['sealed']:
        raise RuntimeError('Previous seal differs')
    native=(out/'retained-native/catalog-layout-findings.json').read_bytes()
    if native!=(base/'cn-account-catalog-layout-01/findings.json').read_bytes():
        raise RuntimeError('Historical native catalog evidence differs')
    dump('retained-native/origin.json',dict(
        original='artifacts/integration/packet-connections-20261006/cn-account-catalog-layout-01/findings.json',
        snapshot='retained-native/catalog-layout-findings.json',bytes=len(native),sha256=sha(native),
        existing_native_contract_reused=True,new_native_opcode_or_field_semantics=0))
    facts=dict(round=ROUND,previous_goal_turn_classification='progress: actual1D/0A source assembler/explicit key issuer/catalog116/68-file seal',
        actual_managed_listener_registries_added=1,actual_bound_native_directory_producers_added=1,
        existing_account_composition_source_bindings_strengthened=1,
        exact_directory_before_issue_publish_source_gates_added=2,
        actual_socket_bind_before_controller_factory=True,registry_invalidated_before_socket_close=True,
        new_native_field_semantics=0,new_native_primary_bytes=0,new_packet_values=0,
        new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,whole_game_route_total=None,whole_game_completed_routes=None,
        whole_game_completion_percent=None,actual_native_metadata_owner_configured=False,formal_application_hosted=False,
        profile_billing_opaque_values_invented=False,levels_changed=False,common_storage_changed=False,
        build_run=False,tests_run=False,runtime_run=False,network_bind_run=False,Cplusplus_reader_run=False,
        native_execution=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['cn_bound_account_directory_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(
        name='Actual CN bind/listen registry -> native04/05/06 directory source -> same account issue/held publication lifetime',
        version_scope='cn-account-existing-host-source-only',
        status='Actual bound address/source producer integrated; group/profile metadata and formal hosting remain unconfigured',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']=(
        'Actual pinned client group configuration/resource lineage, native billing/load/location/slots and full profile40/billing16/rights/revision/deadline/summaries. '
        'Bound registry and directory producer now implemented; no native metadata guesses or activation. '
        'Continue whole world/gameplay/numeric/TW/native PC/web/WSS/denominator; PHASE1 only.')
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN bound native account directory ('+ROUND+')\n\n'
            'Implemented actual game-owned bound listener registry: successful bind/listen/local_endpoint precedes controller factory, async accept starts only after complete controllers, managed stop invalidates snapshots before socket close. SharedAccountDirectorySource takes native group/node metadata and derives IPv4/port only from actual targets, preserving04/05/06/order/slot/raw fields. Existing whole-native catalog is qualified without rewrite. Composition always binds the same host/current/exact directory gate before issue/held publication; explicit issued-account producer can use a typed Plan. New registry1/producer1/gates2, new opcode/phase/complete owner/full0; original native catalog evidence reused with no new field claims. No source metadata guessed, formal hosting or build/test/network/native/DB/deploy; frozen transport/native codec/verifier/admission/Application/storage/fonts/conversion/levels unchanged. See research/cn-bound-account-directory-source-20261008.md; full goal remains active.\n')
    origins=[]
    for rel in sorted(set(SOURCES)|set(books)):
        data=(ROOT/rel).read_bytes();save('source/'+rel,data)
        origins.append(dict(path=rel,snapshot='source/'+rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),
                data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ('round','actual_managed_listener_registries_added',
        'actual_bound_native_directory_producers_added','exact_directory_before_issue_publish_source_gates_added','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
