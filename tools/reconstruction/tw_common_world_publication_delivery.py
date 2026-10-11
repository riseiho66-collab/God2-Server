"""File-only actual TW common lease identity and held native game/IO publication."""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT,PIN

NAME='tw-common-world-publication-01'
ROUND='20261007-tw-common-world-publication'
SOURCES=('src/net/Session.h','src/net/Session.cpp','src/game/SharedTaiwanWorldLifecycle.h',
    'src/game/SharedTaiwanWorldLifecycle.cpp','tools/reconstruction/dual_client_route_catalog.py',
    'tools/reconstruction/tw_common_world_publication_delivery.py','docs/research/tw-common-world-publication-20261007.md')
REMAINING=[
    'Actual outward native TW/CN6F visibility model/issuer/fanout using both held publication entries remains open; no native policy/default/appearance/resource/data provider is supplied.',
    'Full TW initial publication/native character-handle qualification, native scene/normal/CF/later visibility lifecycle and common gameplay authorities remain incomplete.',
    'Configured Application providers/hosting, pending operation serialization/semantic replay and durable committed-state/output/crash/cross-process recovery remain open.',
    'All TW/CN/web gameplay/numeric wire/object/display and exhaustive directional phase/state/variant/indirect/deferred denominator, followed by comprehensive original-client acceptance. Levels unchanged.']

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh before receipt required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before/artifacts/integration/packet-connections-20261006/packet-route-ledger.json').read_text(encoding='utf-8'));unchanged=[]
    for row in json.loads((out/'before-manifest.json').read_text(encoding='utf-8')):
        data=(out/'before'/row['path']).read_bytes()
        if sha(data)!=row['sha256']:raise RuntimeError('Before snapshot differs')
        if row['path'] not in SOURCES and row['path'] not in ('artifacts/integration/packet-connections-20261006/packet-route-ledger.json','docs/PACKET_CONNECTION_GOAL_20261006.md'):
            if data!=(ROOT/row['path']).read_bytes():raise RuntimeError('Preserved source changed')
            unchanged.append(row)
    prior=base/'shared-taiwan-world-lifecycle-01';pins=before['cn_account_admission_evidence']['shared-taiwan-world-lifecycle-01']['artifact_sha256']
    raw=(prior/'integration-manifest.json').read_bytes()
    if sha(raw)!=pins['integration-manifest.json']:raise RuntimeError('TW common lifecycle provenance differs')
    manifest=json.loads(raw);save('retained-source/shared-taiwan-world-lifecycle-01/integration-manifest.json',raw)
    for row in manifest['snapshots']:
        if not row['path'].endswith(('SharedTaiwanWorldLifecycle.h','SharedTaiwanWorldLifecycle.cpp','Session.h','Session.cpp')):continue
        p=(prior/row['path']).resolve()
        if not p.is_relative_to(prior.resolve()):raise RuntimeError('Historical path outside artifact')
        data=p.read_bytes()
        if sha(data)!=row['sha256'] or sha(data)!=pins[row['path']]:raise RuntimeError('Historical scoped source differs')
        save('retained-source/shared-taiwan-world-lifecycle-01/'+row['path'],data)
    prior=base/'cn-initial-visibility-publication-01';raw=(prior/'manifest.json').read_bytes();sealed=json.loads(raw)
    pins={row['path']:row['sha256'] for row in sealed['files']};data=(prior/'findings.json').read_bytes()
    if not sealed['sealed'] or sha(data)!=pins['findings.json']:raise RuntimeError('Previous sealed source differs')
    save('retained-source/cn-initial-visibility-publication-01/manifest.json',raw)
    save('retained-source/cn-initial-visibility-publication-01/findings.json',data)
    # File slices only, not running a transport/codec/fixture or acceptance test.
    rel='src/net/Session.cpp';old=(out/'before'/rel).read_bytes();new=(ROOT/rel).read_bytes();preserved=[]
    for start,end in ((b'void Session::send_world_records(',b'void Session::bind_world_delivery_identity('),
        (b'void Session::send_world_records_with_acceptance(',b'void Session::close()')):
        a=old[old.index(start):old.index(end,old.index(start))];b=new[new.index(start):new.index(end,new.index(start))]
        if a!=b:raise RuntimeError('Legacy TW send method changed')
        preserved.append({'method':start.decode(),'sha256':sha(a),'exact_bytes_preserved':True})
    dump('preserved-legacy-send-methods.json',preserved)
    facts={'round':ROUND,'cn_native_sha256_context':PIN,'previous_goal_turn_classification':'progress: initial CN full6F/common model and1C source handoff, catalog99 sealed',
        'tw_common_world_publication_sources_added':1,'tw_common_world_identity_lineage_sources_added':1,
        'tw_existing_common_lifecycle_bindings_strengthened':1,'new_source_owner_chains':0,'new_tw_source_owner_chains':0,
        'new_native_phase_source_bindings':0,'new_packet_values':0,'new_complete_bidirectional_routes':0,
        'whole_game_route_total':None,'whole_game_completion_percent':None,'native_response_causality_recovered':False,
        'configured_native_visibility_providers_installed':False,'formal_application_hosted':False,
        'levels_changed':False,'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'existing_sources_unchanged':unchanged,'remaining':REMAINING}
    dump('findings.json',facts)
    dump('source-relations.json',{'identity':'actual TW common ready lease/generation ->separate immutable atomic Session identity ->exact generation cleanup revocation',
        'publication':'game current/native source bytes/budget ->IO native tail/frame/capacity/held entry ->game same actual identity/publisher ->IO exact held entry/current identity ->release ->single game local queue completion',
        'old_paths':'legacy send and PRIVATE0083 acceptance bytes preserved; original queue flags default held=false, writer only stops held/empty head',
        'open':'actual outward native6F caller/model/fanout/providers/hosting/lifecycle/semantic replay/recovery and full gameplay/denominator'})
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes())
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['tw_common_world_publication']={k:v for k,v in facts.items() if k!='existing_sources_unchanged'}
    ledger['tw_common_world_publication']['evidence']=out.relative_to(ROOT).as_posix()
    ledger['dual_client_source_segments'].append({'name':'TW actual common lease identity and held native game/IO source publication prerequisite',
        'version_scope':'tw-explicit-common-world-transport-publication','status':'actual common lifecycle ready ->same lease atomic identity ->actual source native bytes ->held native IO ->game publisher ->identity-qualified release ->single game completion; outward caller/native providers/hosting/recovery open',
        'source_paths':list(SOURCES),'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_owner_chains_added':0,
        'tw_source_owner_chains_added':0,'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'tw_common_world_publication_sources_added':1,'tw_common_world_identity_lineage_sources_added':1,
        'tw_existing_common_lifecycle_bindings_strengthened':1,'evidence':out.relative_to(ROOT).as_posix(),'remaining':REMAINING})
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Continue actual outward native6F common model publication/fanout using the CN verified world and TW actual common-lease held IO entries. TW common identity now binds/revokes its exact presence generation independently of PRIVATE0083; frozen host remains unchanged. Full native visibility policy/data/appearance/resources/issuers/providers, TW initial/character-handle and normal/CF/later lifecycle, Application hosting, semantic replay/crash/recovery and all gameplay/numeric/denominator remain open. Levels unchanged; PHASE1 file-only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'docs/PACKET_CONNECTION_GOAL_20261006.md').open('a',encoding='utf-8') as f:f.write(
        '\n\n## TW actual common-world held publication ('+ROUND+')\n\n'
        'Separate common identity binds/revokes actual TW presence account/character/generation after real ready and before cleanup, never borrowing PRIVATE0083 generation. Complete native source bytes use unchanged framing/budgets; held IO entry ->same game identity/publisher ->requalified IO release ->single game local completion. Original send/PRIVATE0083 method bytes retained; old queue held defaults false, writer stops held head only. TW publication source1/common identity source1/existing lifecycle strengthened1; new owner/phase/opcode/full route0. Actual outward6F model/fanout/caller/full native providers/hosting/initial and later lifecycle/recovery and full gameplay/denominator remain open. Levels unchanged; PHASE1 no builds/tests/runtime/SQL/deploy. See research/tw-common-world-publication-20261007.md.\n')
    print(json.dumps({k:facts[k] for k in ('round','tw_common_world_publication_sources_added','tw_common_world_identity_lineage_sources_added','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
