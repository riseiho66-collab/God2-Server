"""Retain explicit CN own-server seed source; static file accounting only."""
import difflib
import hashlib
import json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT

NAME='cn-transport-seed-source-01'
ROUND='20261008-cn-transport-seed-source'
SOURCES=(
    'src/cn/net/OperationalTransportSeed.h','src/cn/net/OperationalTransportSeed.cpp',
    'src/cn/net/SharedCredentialServer.h','src/cn/auth/SharedLoginComposition.h',
    'src/cn/auth/SharedLoginComposition.cpp',
    'docs/research/cn-transport-seed-source-20261008.md',
    'tools/reconstruction/cn_transport_seed_source_delivery.py',
    'tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
    'Operational seed source implemented but not configured/hosted; official server RNG policy not recovered. This is not1D check_key or admission/entitlement authority.',
    'Actual full1D/0A/entitlement/catalog/deadline and native07/world1F/02/2A/6F/equipment/scene/ACT providers remain required.',
    'TW shared registry/native PC/web/WSS hosting, credential revision/ABA/revocation and all gameplay/numeric extensions remain open.',
    'Whole-game direction/phase/state/variant/indirect/deferred denominator remains unknown; comprehensive tests deferred until all sources connected.']

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Fresh source snapshot required')
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
    prior=(out/'retained-prior/cn-account-catalog-source-observation-01/manifest.json').read_bytes()
    if sha(prior)!='553bf3c7c92364ea14e49e1ce06d98cf9dfbe7c17a20b2d0f9efcd428dfe8faf' or not json.loads(prior)['sealed']:
        raise RuntimeError('Previous seal differs')
    native=json.loads((out/'native/capture.json').read_text(encoding='utf-8'))
    for row in native['functions']:
        if sha((out/'native'/(row['va']+'.bin')).read_bytes())!=row['sha256']:
            raise RuntimeError('Retained primary envelope differs')
        if sha((out/'native'/(row['va']+'.c')).read_bytes())!=row['source_sha256']:
            raise RuntimeError('Retained metadata navigation source differs')
    if sha((out/'native/00895790-table256.bin').read_bytes())!=native['table_sha256']:
        raise RuntimeError('Retained primary table differs')
    facts=dict(
        round=ROUND,previous_goal_turn_classification='no progress: status-only read/report; current worktree revalidated and concrete native/source work resumed',
        own_server_operational_seed_suppliers_implemented=1,
        existing_native_login_seed_composition_bindings_strengthened=1,
        native_primary_function_envelopes_retained=5,
        native_primary_metadata_bytes_retained=native['metadata_envelope_bytes'],
        native_primary_table_bytes_retained=native['table_bytes'],
        native_primary_unique_bytes_retained=native['metadata_envelope_bytes']+native['table_bytes'],
        input_sha256=native['input_sha256'],original_server_rng_policy_recovered=False,
        transport_seed_is_admission_key=False,explicit_opt_in_required=True,
        runtime_seed_source_selected=False,formal_application_hosted=False,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,
        new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        levels_changed=False,shared_storage_changed=False,
        build_run=False,tests_run=False,runtime_run=False,rng_run=False,
        Cplusplus_reader_run=False,native_execution=False,database_access=False,deployed=False,
        protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    ledger_path=base/'packet-route-ledger.json';ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
    ledger['cn_transport_seed_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(
        name='Explicit own-server Windows CNG16-byte seed -> actual CN login composition -> existing accepted socket transport',
        version_scope='cn-transport-operational-source-only',
        status='Real opt-in source implementation; no formal hosting or native RNG recovery; account/world data remain mandatory',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},
        source_owner_chains_added=0,tw_source_owner_chains_added=0,
        formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next_source_frontier']=(
        'Actual account1D/0A/entitlement/catalog/deadline providers and full world source chain. '
        'Explicit own-server seed supplier now implemented, not configured, never official RNG evidence. '
        'Continue all shared gameplay/numeric/PC/web/WSS/denominator; PHASE1 source-only.')
    ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN explicit operational transport seed ('+ROUND+')\n\n'
            'Retained pinned CN five function envelopes1703B plus actual key table256B; native intake copies16 literal bytes then derives key/challenge. Official server RNG distribution remains unknown. Added explicitly selected own-server WindowsSystemCngV1 source using BCryptGenRandom success only, same actual endpoint/game owner/one-shot connection identity, no cached/fixed/default/random fallback. Existing login composition chooses exactly one supplied callback or explicit policy; account/world suppliers remain required. Existing listener/codec/PasswordHash/Application/main/CMake/frozen contexts unchanged. Source selected/hosted/full routes0; no build/test/RNG/runtime/DB/deploy; all native login/world/gameplay/numeric/denominator work retained. See research/cn-transport-seed-source-20261008.md.\n')
    origins=[]
    for rel in sorted(set(SOURCES)|set(books)):
        data=(ROOT/rel).read_bytes();save('source/'+rel,data)
        origins.append(dict(path=rel,snapshot='source/'+rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),
                data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ('round','own_server_operational_seed_suppliers_implemented',
        'existing_native_login_seed_composition_bindings_strengthened','native_primary_unique_bytes_retained','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
