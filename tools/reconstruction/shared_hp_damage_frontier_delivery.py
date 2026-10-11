"""Retain three disjoint HP/damage source investigations; no gameplay execution."""
import difflib
import hashlib
import json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT

NAME='shared-hp-damage-connection-frontier-01'
ROUND='20261008-shared-hp-damage-connection-frontier'
WRITTEN=['docs/research/shared-hp-damage-connection-frontier-20261008.md',
         'tools/reconstruction/shared_hp_damage_frontier_delivery.py',
         'tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',
       'artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
REMAINING=[
 'HP/damage actual shared actors/rules/exact Lua/checkpoint/resource loader/CAS/SQL and recovery need a synchronous separately versioned numeric64 connection; this round is bounded research, not implemented widening.',
 'Actual native role/entry maxima and signed-short/DWORD projections require qualified extended authority and TW/CN/web consumer/object/display profiles; never narrow authoritative values to satisfy old native fields.',
 'PK terminal character resource/role policy, both owner locks and exact replay/outbox recovery remain open; whole resource guild leases must be preserved.',
 'Original native DWORD math and CUSTOM formula/1m gates remain original scoped sources, not wide math or CN native authority; EXP/HP/damage gameplay maxima remain undecided.',
 'Actual deletion/summary issuer/schema/data/Main/durable recovery/general worldoffer, account40+16, world reservation/bootstrap/presence remain open.',
 'Native WORLD68 next407E93->40B4B0/current re-read index, conditional receiver phase/nonalias and interrupted title partial remain open; interrupted native research not retried.',
 'Coin wallet CHECK/additive migration, stack99, full TW/CN/PC/web hosting/WSS/denominator/complete source routes and later comprehensive tests/repairs/release remain open.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Fresh before required; preserve prior deliveries')
    def save(rel,raw):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(raw)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=919:raise RuntimeError('Expected919 before sources')
    old={row['path']:(out/row['snapshot']).read_bytes() for row in before}
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{ext}' for ext in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before receipt differs')
        if row['path'] not in set(WRITTEN+BOOKS)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    for name,pin in [('shared-experience-award64-source-01','c7f3de3d335066f7206097fe46c4fd99bd9c2fed44c92d9dcc892b33637bc3dc'),
                     ('endpoint-catalog156','5500e02db66d28a0ef0a95b4d79999dbc85b54fd6294a0198ccb36f97134be69')]:
        raw=(out/'retained-prior'/name/'manifest.json').read_bytes()
        if sha(raw)!=pin or not json.loads(raw)['sealed']:raise RuntimeError('Prior156 seal differs')
    source_paths=set(WRITTEN);agents=[];source_records=[]
    def record_origins(folder):
        origin='normalized-source-origin.json' if (folder/'normalized-source-origin.json').exists() else 'source-origin.json'
        value=json.loads((folder/origin).read_text(encoding='utf-8-sig'))
        rows=value if isinstance(value,list) else value.get('source_files',value.get('files',value.get('sources',[])))
        if not rows:raise RuntimeError('Missing actual source origins: '+str(folder))
        for row in rows:
            rel=row.get('relative_path',row.get('path',row.get('original_path')))
            if not rel:raise RuntimeError('Missing source path')
            path=Path(rel) if Path(rel).is_absolute() else ROOT/rel
            raw=path.read_bytes()
            pin=row.get('original_sha256',row.get('sha256'))
            length=row.get('original_bytes',row.get('bytes'))
            if sha(raw)!=pin or len(raw)!=length:raise RuntimeError('Current source differs: '+str(path))
            # A range copy may have its own hash; it is not a whole-file receipt.
            if row.get('copy'):
                copy=(folder/row['copy']).read_bytes()
                if sha(copy)!=row['sha256'] or len(copy)!=row['bytes']:raise RuntimeError('Retained copy differs')
            try:repo_path=path.relative_to(ROOT).as_posix()
            except ValueError:repo_path=None
            if repo_path:source_paths.add(repo_path)
            source_records.append(dict(folder=folder.relative_to(out).as_posix(),source=row,repo_path=repo_path))
        return value
    for name in ['resource-storage','battle-calculation','per-recipient-projection']:
        folder=out/'agents'/name
        raw=(folder/'findings.json').read_bytes();seal=json.loads((folder/'seal.json').read_text(encoding='utf-8-sig'))
        if seal.get('sealed') is False or seal.get('complete') is False:raise RuntimeError('Incomplete agent')
        sealed_files=seal.get('files',seal.get('entries',[]))
        if not sealed_files:raise RuntimeError('Missing agent seal files')
        for row in sealed_files:
            content=(folder/row['path']).read_bytes()
            if len(content)!=row['bytes'] or sha(content)!=row['sha256']:raise RuntimeError('Agent seal differs: '+name)
        origins=record_origins(folder)
        files=[dict(path=p.relative_to(folder).as_posix(),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
               for p in sorted(folder.rglob('*')) if p.is_file()]
        agents.append(dict(agent=name,findings=json.loads(raw),findings_sha256=sha(raw),files=files,
                           source_origin=origins,formal_source_modified_by_agent=False))
    root=out/'source/root-dependencies';record_origins(root)
    root_findings=json.loads((root/'findings.json').read_text(encoding='utf-8'))
    dump('parallel-agent-deliveries.json',agents)
    dump('source/reviewed-source-records.json',source_records)
    relations=dict(source_only=True,implemented_HP_damage_widening=False,
        resource_storage=agents[0]['findings'],battle_calculation=agents[1]['findings'],
        battle_calculation_required_changes=json.loads((out/'agents/battle-calculation/necessary-64bit-calculation-changes.json').read_text(encoding='utf-8')),
        legacy_math_preservation_conditions=json.loads((out/'agents/battle-calculation/legacy-math-preservation-conditions.json').read_text(encoding='utf-8')),
        per_recipient_projection=agents[2]['findings'],root_PK_and_guild_dependencies=root_findings,
        prior_experience64_source_preserved=True,coin_cap_applied_to_HP_damage=False,
        HP_damage_gameplay_maximum_selected=False,levels_changed=False,
        original_native_DWORD_math_preserved=True,separate_versioned_extended_profile_required=True,
        interrupted_title_research_retried=False,complete_route=False,formal_application_hosted=False)
    dump('source/hp-damage-connection-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:156 actual experience award64 settlement/storage/progression and bounded native owner evidence; numerical64 full routes remain OPEN',
        user_requested_delegation=True,delegated_parallel_agents=3,completed_parallel_agents=3,
        source_investigation_topics=['resource-storage-CAS-migration','battle-Lua-checkpoint-calculation','per-recipient-native-projection-and-web-hosting'],
        root_additional_dependency_maps=2,reviewed_source_record_count=len(source_records),
        gameplay_source_modified=False,new_HP_damage64_storage_or_calculation_connections=0,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        original_native_wire_layout_changed=False,actual_issuer_selected=False,actual_native_data_imported=False,
        schema_registered_or_installed=False,formal_application_hosted=False,levels_changed=False,
        build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,
        Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    sources=sorted(source_paths)
    path=ROOT/BOOKS[1];ledger=json.loads(path.read_text(encoding='utf-8'))
    if any(row['name']==NAME for row in ledger['dual_client_source_segments']):raise RuntimeError('Preserve existing segment')
    ledger['shared_HP_damage_connection_frontier']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
        version_scope='shared-HP-damage64-actual-source-dependencies-bounded-three-worker-research-only',
        status='Bounded actual storage/CAS, Battle/Lua/checkpoint and per-recipient source dependencies captured; no implemented HP/damage widening or new phase/routes',
        source_paths=sources,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next_source_frontier']='Connect synchronous shared HP/damage64 domain/actual Battle/Lua/checkpoint/resource CAS/reversible additive migration with qualified extended role/entry and recipient TW/CN/web consumer/display; retain original native math/replay and whole guild/PK owner leases. Prior native WORLD68 and full M1-M3/hosting gaps remain OPEN. PHASE1.'
    path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as stream:
        stream.write('\n\n## Three-worker HP/damage connection dependencies ('+ROUND+')\n\n'
            'Owner requested delegation: three disjoint workers delivered actual resource load/CAS/writer/schema/role maxima, Battle/Lua/checkpoint calculations and per-recipient native projections/web source evidence. '
            'Root additionally captured PK legacy entry/readset/checkpoint/outbox and guild whole-resource lease dependencies. Source hashes, copies and reading ranges retained; bounded inventories are not all writers/consumers. '
            'This round is new research, not implemented HP/damage widening or native packet/phase/route completion. Preserve exact original DWORD math and version1 replay; separately version wide storage/checkpoint/role/entry/recipient profiles and additive migration, exact Lua integer arithmetic. '
            'No coin cap applied to HP/damage; gameplay maxima remain undecided; native levels/frozen functionality unchanged. '
            'Prior EXP64 source and all history preserved; interrupted title native work not retried. New complete routes0, percent null; no game-source mutation/build/test/native/API/C++/SQLDB/deploy. Full goal active.\n')
    origins=[]
    for rel in sorted(set(sources+BOOKS)):
        raw=(ROOT/rel).read_bytes();save('source/current/'+rel,raw)
        origins.append(dict(path=rel,bytes=len(raw),sha256=sha(raw),changed_this_round=rel not in old or old[rel]!=raw))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='current/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps(dict(round=ROUND,completed_agents=3,source_record_count=len(source_records),source_paths=len(sources),
                          protected_files=len(protected),new_complete_bidirectional_routes=0)))

if __name__=='__main__':main()
