"""File-only initial CN source ->actual TW/CN observers/native6F publication."""
import hashlib
import json
from pathlib import Path
import pefile
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT, PIN

NAME='dual-outward-visibility-publication-01'
ROUND='20261007-dual-outward-visibility-publication'
SOURCES=('src/cn/world/SharedActorVisibility.h','src/cn/world/SharedActorVisibility.cpp',
    'src/cn/world/SharedWorldReady.h','src/cn/world/SharedWorldReady.cpp',
    'tools/reconstruction/dual_client_route_catalog.py',
    'tools/reconstruction/dual_outward_visibility_publication_delivery.py',
    'docs/research/dual-outward-visibility-publication-20261007.md')
REMAINING=[
    'Actual complete ordered observer policy and full recipient-native actor/appearance/text/resources/data/issuer providers remain missing and unhosted; no native response causality/default is invented.',
    'TW own initial publication/character-handle qualification, normal/CF/later replacement/hide/reset and full scene/gameplay lifecycle remain incomplete.',
    'Production Application/WS hosting, semantic replay, durable committed-state/output and crash/cross-process recovery remain open; local queue release is not native receipt or atomic fanout.',
    'All TW/CN/web gameplay and numeric wire/object/display routes plus exhaustive state/variant/indirect/deferred denominator remain open; levels unchanged; comprehensive native acceptance follows full source connection.']

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh before receipt required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    unchanged=[]
    for row in json.loads((out/'before-manifest.json').read_text(encoding='utf-8')):
        data=(out/'before'/row['path']).read_bytes()
        if sha(data)!=row['sha256']:raise RuntimeError('Before receipt differs')
        if row['path'] not in SOURCES and row['path'] not in ('artifacts/integration/packet-connections-20261006/packet-route-ledger.json','docs/PACKET_CONNECTION_GOAL_20261006.md'):
            if data!=(ROOT/row['path']).read_bytes():raise RuntimeError('Preserved context differs')
            unchanged.append(row)
    # Preserve prior immutable provenance, then reread only bounded current CN
    # file ranges. No native API, transport, codec, Lua, DB or fixture execution.
    for name in ('tw-common-world-publication-01','cn-initial-visibility-publication-01'):
        prior=base/name;raw=(prior/'manifest.json').read_bytes();sealed=json.loads(raw)
        pins={r['path']:r['sha256'] for r in sealed['files']}
        if not sealed['sealed']:raise RuntimeError('Prior source is not sealed')
        save('retained-source/'+name+'/manifest.json',raw)
        for rel in ('findings.json','round-report.json'):
            data=(prior/rel).read_bytes()
            if sha(data)!=pins[rel]:raise RuntimeError('Prior source differs')
            save('retained-source/'+name+'/'+rel,data)
        if name=='tw-common-world-publication-01':
            rel='after/src/core/Application.cpp';data=(prior/rel).read_bytes()
            if sha(data)!=pins[rel] or data!=(ROOT/'src/core/Application.cpp').read_bytes():raise RuntimeError('Frozen host context differs')
            save('retained-source/'+name+'/'+rel,data)
        else:
            native=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');raw_native=native.read_bytes()
            if sha(raw_native)!=PIN:raise RuntimeError('Pinned CN primary file differs')
            pe=pefile.PE(data=raw_native,fast_load=True);view=FileView(pe,raw_native);reads=[]
            for row in sealed['files']:
                rel=row['path']
                if not rel.startswith(('native/current-cn/','native/historical-listings/')):continue
                data=(prior/rel).read_bytes()
                if sha(data)!=row['sha256']:raise RuntimeError('Prior native scoped receipt differs')
                save('retained-source/'+name+'/'+rel,data)
                if rel.startswith('native/current-cn/'):
                    va=int(Path(rel).stem,16);current=view.read(va-pe.OPTIONAL_HEADER.ImageBase,len(data))
                    if current!=data:raise RuntimeError('CN primary scope differs')
                    save('native/current-cn/'+Path(rel).name,current)
                    reads.append({'va':f'{va:08x}','bytes':len(current),'sha256':sha(current),'retained_prior_match':True})
            pe.close();dump('native/current-file-read-receipt.json',{'native_sha256':PIN,'ranges':reads,
                'new_native_fields_or_response_causality':False,'native_executed':False})
    # Unmodified legacy transport/model submission methods are retained as bytes.
    rel='src/cn/world/SharedActorVisibility.cpp';old=(out/'before'/rel).read_bytes();new=(ROOT/rel).read_bytes();preserved=[]
    for start,end in ((b'bool SharedActorVisibility::recipient_bound(',b'bool SharedActorVisibility::submit('),
        (b'bool SharedActorVisibility::submit(',b'void SharedActorVisibility::reject_output('),
        (b'void SharedActorVisibility::reject_output(',b'std::optional<SharedActorVisibility::Binding> SharedActorVisibility::show('),
        (b'bool SharedActorVisibility::advance(',b'bool SharedActorVisibility::hide(')):
        a=old[old.index(start):old.index(end,old.index(start))];b=new[new.index(start):new.index(end,new.index(start))]
        if a!=b:raise RuntimeError('Preserved model/transport body differs')
        preserved.append({'method':start.decode(),'sha256':sha(a),'exact_bytes_preserved':True})
    dump('preserved-methods.json',preserved)
    tw=ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
    facts={'round':ROUND,'cn_native_sha256_context':PIN,
        'previous_goal_turn_classification':'progress: TW common generation/held publication, packet catalog100 and web native-input receipt sealed',
        'dual_outward6F_publication_sources_added':1,'initial1C_outward_handoffs_strengthened':1,
        'pending_source_visibility_movement_lifecycle_guards_added':1,
        'new_source_owner_chains':0,'new_tw_source_owner_chains':0,'new_native_phase_source_bindings':0,
        'new_packet_values':0,'new_complete_bidirectional_routes':0,
        'whole_game_route_total':None,'whole_game_completed_routes':None,'whole_game_completion_percent':None,
        'native_response_causality_recovered':False,'configured_native_visibility_providers_installed':False,
        'formal_application_hosted':False,'TW_historical_original_present':tw.exists(),'TW_current_original_restored':False,
        'levels_changed':False,'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'existing_contexts_unchanged':unchanged,'remaining':REMAINING}
    dump('findings.json',facts)
    dump('source-relations.json',{
        'CN_entry':'complete1C ->same prepared lease/actual issuer ->activate/gameplay install/incoming6F model ->own held aggregate release ->actual ordered outward recipients ->all local queue releases ->complete gameplay remainder',
        'TW_recipient':'full supplied TW6F/5E/73 ->exact common account/character/generation ->held Session IO ->actual issuer/current lease/model node ->release ->single game completion',
        'CN_recipient':'full supplied CN6F/5E/73 ->verified admitted WORLD/account/session/exact lease ->held CN IO ->actual issuer/current lease/model node ->release ->single game completion',
        'pending':'source operation ->movement/chat/legacy model mutation guards ->exact disconnect/reset cancellation ->single failure/no committed-state rollback/no atomic fanout claim',
        'remaining':REMAINING})
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes())
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['dual_outward_visibility_publication']={k:v for k,v in facts.items() if k!='existing_contexts_unchanged'}
    ledger['dual_outward_visibility_publication']['evidence']=out.relative_to(ROOT).as_posix()
    ledger['dual_client_source_segments'].append({'name':'Initial CN source full6F to actual TW/CN observers inside recipient held publication',
        'version_scope':'tw-cn-explicit-common-initial-outward-visibility','status':'actual1C/incoming model release ->supplied complete outward set/native records ->same generation/model preallocation ->TW/CN held publication ->all local queue releases ->gameplay remainder; native suppliers/hosting/later lifecycle/recovery open',
        'source_paths':list(SOURCES),'native_c2s_by_phase':{},'native_s2c_by_phase':{},
        'source_owner_chains_added':0,'tw_source_owner_chains_added':0,'formal_application_hosted':False,
        'complete_gameplay_routes_added':0,'dual_outward6F_publication_sources_added':1,
        'initial1C_outward_handoffs_strengthened':1,'pending_source_visibility_movement_lifecycle_guards_added':1,
        'evidence':out.relative_to(ROOT).as_posix(),'remaining':REMAINING})
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Trace actual complete recipient-native actor/appearance source and its scene issuer composition to supply the initial incoming/outward sets now required by1C and both held transports. Actual native visibility policy/data/resources/text/issuer providers and production host remain open, as do TW own initial/character-handle, normal/CF/later replacement/hide/reset, semantic replay/recovery, all gameplay/numeric routes and exhaustive denominator. Levels unchanged; PHASE1 file-only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'docs/PACKET_CONNECTION_GOAL_20261006.md').open('a',encoding='utf-8') as f:f.write(
        '\n\n## Initial CN source ->TW/CN observer publication ('+ROUND+')\n\n'
        'Actual1C incoming publication release now dispatches the mandatory actual ordered outward observer set. Full version-native6F/5E/73 and real scene/source predicates feed preallocated common model nodes inside each TW/CN held publication. Exact pending source guards prevent movement/partial model use until all local queues release; generation-qualified disconnect/reset/failure cancels once and requires real recovery, not atomic fanout/rollback. Outward source1/initial1C handoff strengthened1/pending lifecycle guard1; new opcode/phase/owner/full route0. Actual visibility/appearance/resource/data/issuer providers and production hosting, TW own initial/handle/later lifecycle, replay/recovery and all gameplay/denominator remain open. Levels unchanged; no builds/tests/runtime/DB/deploy. See research/dual-outward-visibility-publication-20261007.md.\n')
    print(json.dumps({k:facts[k] for k in ('round','dual_outward6F_publication_sources_added','initial1C_outward_handoffs_strengthened','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
