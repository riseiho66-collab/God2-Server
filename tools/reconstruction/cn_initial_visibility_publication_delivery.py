"""Bounded file-only initial CN recipient full6F/common model/ready publication."""
import hashlib
import json
from pathlib import Path
import pefile
from .cn_wrapper_route_frontier import ROOT,PIN
from .cn_pe_import_directory import FileView

NAME='cn-initial-visibility-publication-01'
ROUND='20261007-cn-initial-visibility-publication'
SOURCES=('src/cn/world/SharedActorVisibility.h','src/cn/world/SharedActorVisibility.cpp',
    'src/cn/world/SharedWorldReady.h','src/cn/world/SharedWorldReady.cpp',
    'tools/reconstruction/dual_client_route_catalog.py','tools/reconstruction/cn_initial_visibility_publication_delivery.py',
    'docs/research/cn-initial-visibility-publication-20261007.md')
REMAINING=[
    'Full actual initial visibility policy/ordered complete actor set/native appearance/resources/data/issuer and no-output causality providers remain missing; the private model token cannot certify those native rules.',
    'Joining actor outward TW/CN fanout, later replacement/hide/reset/movement visibility publication and recovery, ongoing controls, normal/CF lifecycle and actual common gameplay authorities remain open.',
    'Configured Application providers/hosting, durable semantic operation/replay/committed-state/publication/crash/cross-process recovery remain open.',
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
        if sha(data)!=row['sha256']:raise RuntimeError('Before source differs')
        if row['path'] not in SOURCES and row['path'] not in ('artifacts/integration/packet-connections-20261006/packet-route-ledger.json','docs/PACKET_CONNECTION_GOAL_20261006.md'):
            if data!=(ROOT/row['path']).read_bytes():raise RuntimeError('Preserved source changed')
            unchanged.append(row)
    prior=base/'shared-actor-visibility-01';pins=before['cn_account_admission_evidence']['shared-actor-visibility-01']['artifact_sha256']
    raw=(prior/'integration-manifest.json').read_bytes()
    if sha(raw)!=pins['integration-manifest.json']:raise RuntimeError('Visibility provenance changed')
    manifest=json.loads(raw);save('retained-source/shared-actor-visibility-01/integration-manifest.json',raw)
    for row in manifest['snapshots']:
        if not row['path'].endswith(('SharedActorVisibility.h','SharedActorVisibility.cpp','CnRemoteActor.h','CnRemoteActorMove.h')):continue
        p=(prior/row['path']).resolve()
        if not p.is_relative_to(prior.resolve()):raise RuntimeError('Historical path outside original artifact')
        data=p.read_bytes()
        if sha(data)!=row['sha256'] or sha(data)!=pins[row['path']]:raise RuntimeError('Historical scoped source differs')
        save('retained-source/shared-actor-visibility-01/'+row['path'],data)
    native_path=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');raw=native_path.read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Current CN PE pin differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);primary=[]
    for row in manifest['native_spans']:
        if row['version']!='cn' or row['address'] not in ('0052f170','0052f5a0','00532410','0052fd40'):continue
        data=view.read(int(row['address'],16)-pe.OPTIONAL_HEADER.ImageBase,row['bytes'])
        if sha(data)!=row['native_sha256']:raise RuntimeError('Current CN consumer span differs')
        save('native/current-cn/'+row['address']+'.bin',data)
        rel='native/cn/functions/'+row['address']+'.asm';asm=(prior/rel).read_bytes()
        if sha(asm)!=pins[rel]:raise RuntimeError('Historical consumer listing differs')
        save('native/historical-listings/'+row['address']+'.asm',asm)
        primary.append({'address':row['address'],'bytes':len(data),'sha256':sha(data),'current_CN_primary_compared':True,'historical_listing_sha256':sha(asm),'new_native_fields_or_rules':0})
    dump('native/current-file-read-receipt.json',{'path':str(native_path),'sha256':PIN,'ranges':primary,'native_executed':False})
    prior=base/'cn-entered-world-publication-01';raw=(prior/'manifest.json').read_bytes();sealed=json.loads(raw)
    pins={r['path']:r['sha256'] for r in sealed['files']};data=(prior/'findings.json').read_bytes()
    if not sealed['sealed'] or sha(data)!=pins['findings.json']:raise RuntimeError('Previous sealed1C source differs')
    save('retained-source/cn-entered-world-publication-01/manifest.json',raw)
    save('retained-source/cn-entered-world-publication-01/findings.json',data)
    facts={'round':ROUND,'native_sha256':PIN,'previous_goal_turn_classification':'progress: actual initial1C presence/gameplay before native IO plus bounded peer driver ACK and catalog98 sealed',
        'initial_visibility_publication_sources_added':1,'existing_initial6F_model_bindings_strengthened':1,
        'existing_initial1C_visibility_result_handoffs_strengthened':1,'new_source_owner_chains':0,
        'new_native_phase_source_bindings':0,'new_packet_values':0,'new_complete_bidirectional_routes':0,
        'whole_game_route_total':None,'whole_game_completion_percent':None,'native_response_causality_recovered':False,
        'configured_native_visibility_providers_installed':False,'formal_application_hosted':False,
        'levels_changed':False,'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'existing_sources_unchanged':unchanged,'remaining':REMAINING}
    dump('findings.json',facts)
    dump('source-relations.json',{'input':'actual scene complete ordered incoming set/full CN81-byte6F/5E/73 with same inactive recipient/private visibility owner',
        'preparation':'exact ready common source leases/positions/handles/native state ->preallocated nodes/full bytes ->private single-use publication token',
        'wire':'every declared complete6F matches an ordered nonoverlapping source aggregate slice; no rebuilding/split/default or full sequence completeness inference',
        'publication':'same1C pending/current actor snapshots around issuer ->held world IO ->activate common presence/install gameplay ->active token qualification/node merge ->InWorld ->release full source replies',
        'lifecycle':'stored private bindings feed actual movement/chat; same-incarnation close erases incoming models; outgoing cross-peer/later lifecycle/durable recovery open'})
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes())
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['cn_initial_visibility_publication']={k:v for k,v in facts.items() if k!='existing_sources_unchanged'}
    ledger['cn_initial_visibility_publication']['evidence']=out.relative_to(ROOT).as_posix()
    ledger['dual_client_source_segments'].append({'name':'CN actual initial incoming6F data/slices/private common model published inside1C held IO',
        'version_scope':'cn-initial-recipient-visibility-publication','status':'actual full actor set ->same common/private recipient source preparation ->full6F aggregate slices ->held1C IO ->active recipient/gameplay ->node merge ->InWorld/release; native policy/data/providers/outward/later lifecycle/hosting/recovery open',
        'source_paths':list(SOURCES),'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_owner_chains_added':0,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'initial_visibility_publication_sources_added':1,
        'existing_initial6F_model_bindings_strengthened':1,'existing_initial1C_visibility_result_handoffs_strengthened':1,
        'evidence':out.relative_to(ROOT).as_posix(),'remaining':REMAINING})
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Continue actual joining actor outward native TW/CN visibility and later replacement/hide/reset/movement fanout publication/current ownership, full native scene visibility/data/resources/issuer/rule providers and Application hosting. Initial incoming CN6F models now bind exact actual aggregate slices and preallocated common nodes in held1C publication. Durable semantic replay/crash/committed-state recovery, all gameplay/numeric and full directional phase/state/variant/indirect/deferred denominator remain open. Levels unchanged; PHASE1 file-only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'docs/PACKET_CONNECTION_GOAL_20261006.md').open('a',encoding='utf-8') as f:f.write(
        '\n\n## CN actual initial incoming visibility ('+ROUND+')\n\n'
        'Actual scene issuer must prepare an explicit ordered common actor set/full native6F/5E/73 for the inactive CN recipient. Private same-owner/generation/connection/position token preallocates nodes; each complete81-byte6F matches its actual aggregate slice. Held1C IO qualifies all current sources around issuer, activates recipient/installs gameplay, merges model nodes then publishes InWorld/releases bytes. Existing6F model binding strengthened1/1C result handoff strengthened1, initial publication source1; new owner/phase/opcode/full route0. Full native visibility policy/appearance/data/resources/providers/hosting, outward TW/CN fanout/later lifecycle/durable recovery and full gameplay/denominator remain open. Four CN primary consumer/reset/removal ranges retained, no new fields/rules or native execution. Previous peer driver unchanged; levels unchanged; PHASE1 no build/tests/runtime/SQL/deploy. See research/cn-initial-visibility-publication-20261007.md.\n')
    print(json.dumps({k:facts[k] for k in ('round','initial_visibility_publication_sources_added','existing_initial6F_model_bindings_strengthened','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
