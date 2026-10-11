"""Static selection filename-cache source receipts, never C++/native tests."""
import difflib,hashlib,json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT,PIN
NAME='cn-selection-filename-cache-source-01'
ROUND='20261007-cn-selection-filename-cache-source'
SOURCES=('src/cn/assets/CnSelectionFilenameCacheSnapshot.h',
    'src/cn/assets/CnSelectionFilenameCacheSnapshot.cpp',
    'tools/reconstruction/cn_selection_filename_cache_source_delivery.py',
    'docs/research/cn-selection-filename-cache-source-20261007.md')
REMAINING=[
    'Actual selection UI/pool/buffer/filename/native row cache/ROM bank/ACT/history/lifetime provider remains unconfigured; an operand is not successful loaded metadata or rendering.',
    'Full native07 flags/opaque/inactive/visibility/slot issuer,1D/0A/world1F/02/2A/6F providers, common TW registry and formal PC/web/WSS hosting remain open.',
    'Credential monotonic revision/ABA/external-write/cross-process/revocation, all numeric/items/trade/quests/combat/skills/monsters/pets/guilds/recovery and full route denominator remain open.'
]
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    b=ROOT/'artifacts/integration/packet-connections-20261006';o=b/NAME
    if not (o/'before-manifest.json').exists() or (o/'findings.json').exists():raise RuntimeError('Fresh snapshot required')
    def save(rel,data):
        p=o/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,v):save(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((o/'before-manifest.json').read_text(encoding='utf-8'))
    books=('docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json')
    preserved=[];after=[];original={}
    for row in before:
        old=(o/row['snapshot']).read_bytes()
        if sha(old)!=row['sha256']:raise RuntimeError('Before bytes differ')
        original[row['path']]=old
        if row['path'] in books:continue
        data=(ROOT/row['path']).read_bytes()
        if data!=old:raise RuntimeError('Preserved context differs: '+row['path'])
        preserved.append(row);rel='after/'+row['path'];save(rel,data)
        after.append(dict(path=row['path'],snapshot=rel,sha256=sha(data),bytes=len(data)))
    prior=b/'cn-selection-appearance-source-01/manifest.json';data=prior.read_bytes()
    if sha(data)!='bd69c36a07b1c5c04e5ba7dddad9cd6ced34bd5c03117baa907efae31739c244' or not json.loads(data)['sealed']:
        raise RuntimeError('Previous source seal differs')
    save('retained-previous/manifest.json',data)
    native=json.loads((o/'native/function-envelopes.json').read_text(encoding='utf-8'))
    if native['sha256']!=PIN:raise RuntimeError('Native identity differs')
    correction=json.loads((o/'native/boundary-decode-correction.json').read_text(encoding='utf-8'))
    allocator=json.loads((o/'allocator-addendum/function-envelopes.json').read_text(encoding='utf-8'))
    comparator=json.loads((o/'comparator-addendum/function-envelopes.json').read_text(encoding='utf-8'))
    additional=allocator['ranges']+comparator['ranges']
    relations=dict(initializer='00445040 UI1792CC pool410B, physical256 pointers; initial22 calloc100h,1 through76C3BF/790027/HeapAlloc flag8; count404/preload40C0; separate UI16174 ROM manager',
        preload='UI2866C count/28674 stride108;4452B7 calls446740 per actual flow;4452F8 saves allocatorcheckpoint0;445313 saves currentcount aspreload',
        refresh='443080/4405F0 restore allocatorcheckpoint0+ownpreloadcount, clear HeroDoll cachedWORDFFFF; not all ROMs reset',
        hit='4467A9 native full-name stricmp; first match among currentprefix; no newload or countincrement',
        miss='4467ED ->4197E0(currentcount); negative staysFFFFFFFF/countunchanged; nonnegative copies originalname then44688B increments',
        capacity='Nativeassert is not early-return proof; this source returns CapacityUnqualified without loading or overflow behavior',
        caches_distinct=['selection filename ordinal','HeroDoll cachedWORD','512 manager ROM slots','NPC two-cache contexts','ROM ACTINDEX/action references'],
        source_reader='Actual UI/pool/buffers/CRT compare flag009FA544=0/revision/Current; original full bytes with ASCII-only case fold; no pointer access, native execution, defaults or loaded-bank claims',
        boundary_correction=correction,actual_issuer_configured=False,whole_native_CFG_or_unwind_closed=False)
    dump('native/source-relations.json',relations)
    facts=dict(round=ROUND,cn_native_sha256_context=PIN,
        previous_goal_turn_classification='progress: complete07 selection resources/local panel projection and catalog110/113-file seal saved',
        cn_selection_filename_cache_source_readers_added=1,cn_selection_filename_operand_projections_added=1,
        cn_selection_preload_count_operand_sources_added=1,cn_original_CRT_fastpath_source_qualifications_added=1,
        native_function_envelopes_read=len(native['ranges'])+len(additional),
        native_function_metadata_bytes_read=sum(i['bytes'] for i in native['ranges']+additional),
        original_loader_additive_bytes=62,native_function_unique_bytes_read=sum(i['bytes'] for i in native['ranges']+additional)+62,
        initial_selection_filename_allocations_observed=22,physical_filename_pointer_slots=256,
        constructor_counts_are_current_runtime_defaults=False,source_issuer_configured=False,formal_application_hosted=False,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,whole_game_route_total=None,whole_game_completed_routes=None,
        whole_game_completion_percent=None,levels_changed=False,common_storage_changed=False,
        build_run=False,tests_run=False,runtime_run=False,Cplusplus_reader_run=False,database_access=False,deployed=False,
        preserved_contexts=preserved,remaining=REMAINING)
    dump('findings.json',facts)
    origins=[]
    for rel in SOURCES:
        data=(ROOT/rel).read_bytes();snap='source/'+rel;save(snap,data)
        origins.append(dict(path=rel,snapshot=snap,sha256=sha(data),bytes=len(data)))
    dump('source/source-origins.json',origins)
    p=b/'packet-route-ledger.json';l=json.loads(p.read_text(encoding='utf-8'))
    l['cn_selection_filename_cache_source']=dict(facts,evidence=o.relative_to(ROOT).as_posix())
    l['dual_client_source_segments'].append(dict(name='Native selection UI/filename pool/buffers/actualCRTfastpath/current revision ->full byte first-match/actual slot operand and saved preload-count source',
        version_scope='cn-selection-source-only',status='Actual-owner readonly source added; no installed cache/bank/ACT provider or native success',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,
        formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=o.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=l['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual selection filename/bank/row-cache/ACT source lifetime and original07 part dependencies; constructor22/preload operands are not current providers. Full actual account/world issuer/PC/web/WSS hosting, all gameplay/numeric/security/denominator remain open; PHASE1 source only.'
    p.write_text(json.dumps(l,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN selection filename cache source ('+ROUND+')\n\n'
            'Saved20 metadata ranges7204B plus retained loader62B additive window. Actual445040 initial22 calloc filename allocations/256 pointer table/separate UI16174 ROM bank, real flow preload/checkpoint0, selected prefix/full-name first match, negative load/no countincrement and success-only filename insertion recovered. Added readonly actual UI/pool/buffers/CRTflag009FA544=0/revision/Current source, slot operand query and preload-count operand; no constructor/default/loaded bank/native success. Standalone tail ASM starts midinstruction and is retained unqualified; corrected identical contiguous655B ends419A6C ret8. Initial malloc/uninitialized interpretation is retained provisional and corrected by caller/tailthunk/callocbody/qualified HeapAlloc import. New opcode/phase/owner/full0; levels/commonstate/frozen sources unchanged; no build/test/runtime/C++reader/DB/deploy. See research/cn-selection-filename-cache-source-20261007.md.\n')
    for rel in books:
        data=(ROOT/rel).read_bytes();snap='after/'+rel;save(snap,data)
        after.append(dict(path=rel,snapshot=snap,sha256=sha(data),bytes=len(data)))
        save('diff/'+Path(rel).name+'.diff',''.join(difflib.unified_diff(original[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='after/'+rel)).encode('utf-8'))
    dump('after-manifest.json',after)
    print(json.dumps({k:facts[k] for k in ('round','cn_selection_filename_cache_source_readers_added','native_function_unique_bytes_read','new_complete_bidirectional_routes')}))
if __name__=='__main__':main()
