"""Save CN literal catalog/deadline publication source; file-only accounting."""
import difflib,hashlib,json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT
NAME='cn-account-catalog-source-observation-01'
ROUND='20261008-cn-account-catalog-source-observation'
SOURCES=('src/cn/auth/SharedAccountSuccess.h','src/cn/auth/SharedAccountSuccess.cpp',
    'docs/research/cn-account-catalog-source-observation-20261008.md',
    'tools/reconstruction/cn_account_catalog_source_observation_delivery.py',
    'tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
    'Actual seed/key/full1D/0A/opaque/entitlement/catalog/deadline issuer and native07/world1F/02/2A/6F/equipment/scene/ACT sources remain unconfigured.',
    'Credential monotonic revision/ABA/external writes/revocation/cross-process authority and TW common registry/native PC/web/WSS hosting remain open.',
    'Full shared gameplay/numeric extensions and whole-game direction/state/variant/indirect/deferred denominator remain open.']
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh source snapshot required')
    def save(rel,b):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(b)
    def dump(rel,v):save(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    old={r['path']:(out/r['snapshot']).read_bytes() for r in before}
    books=('docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json')
    protected=[]
    for r in before:
        if sha(old[r['path']])!=r['sha256']:raise RuntimeError('Before snapshot differs')
        if r['path'] not in set(SOURCES)|set(books):
            if (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Frozen context differs')
            protected.append(r)
    prior=(out/'retained-prior/cn-same-opcode-consumer-source-01/manifest.json').read_bytes()
    if sha(prior)!='3b80e376c0c82d900d3070a3acab8668294f28b027719b3f1852fa1268523334' or not json.loads(prior)['sealed']:
        raise RuntimeError('Previous source seal differs')
    encoding=json.loads((out/'report-recovery/original-observation.json').read_text(encoding='utf-8'))
    corrected=out/'report-recovery/20261008-cn-same-opcode-consumer-source.corrected.md'
    corrected_text=corrected.read_text(encoding='utf-8')
    # Encoding/source accounting only, never native or gameplay validation.
    encoding['corrected_sha256']=sha(corrected.read_bytes())
    encoding['corrected_cjk_characters']=sum(0x4e00<=ord(c)<=0x9fff for c in corrected_text)
    encoding['corrected_counts_come_from_unchanged_round113']=True
    dump('report-recovery/correction-receipt.json',encoding)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress: original three WORLD consumer sources/catalog113/79-file seal',
        existing_cn_account_success_source_bindings_strengthened=1,literal_directory_deadline_observation_boundaries_added=2,
        prepared_missing_directory_deadline_explicit=True,exact_retained_directory_publication_sources_added=1,
        prior_utf8_markdown_correction_saved=True,report_encoding_correction=encoding,
        new_native_metadata_or_function_bytes=0,new_packet_values=0,new_native_phase_source_bindings=0,
        new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        source_issuer_configured=False,formal_application_hosted=False,levels_changed=False,common_storage_changed=False,
        build_run=False,tests_run=False,runtime_run=False,Cplusplus_reader_run=False,database_access=False,deployed=False,
        preserved_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['cn_account_catalog_source_observation']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name='Existing CN account success native Current ->literal04/05/06 and actual grant deadline before issue/held publication',
        version_scope='cn-account-existing-publication-source-only',status='Existing source handoff strengthened; actual native issuer/listener remains unconfigured',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual configured account native issuer/seed/billing/entitlement/catalog/deadline and complete world source providers remain required. Exact observation is not provider or native success. Continue entry source/provenance, all gameplay/numeric/PC/web/WSS/denominator; PHASE1 only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN literal directory/deadline source observation ('+ROUND+')\n\n'
            'Strengthened actual existing account-success handoff: BeforeIssue/BeforePublish Current sees exact ordered04/05/06 records and actual issued grant deadline, retained once before moving output records into the held aggregate. Prepared explicitly has directory/deadline absent. No obsolete source check after output release; credential wipe/grant cleanup preserved. Native codecs/wire/TW/Application/admission/transport/DB/frozen contexts unchanged; actual provider/hosting/full routes0. Prior damaged shell-written中文 Markdown and original79-file seal retained; separately named apply_patch UTF8 correction restores presentation only. New opcode/phase/owner/full0; no build/test/runtime/DB/deploy; all gameplay/numeric/denominator remain open. See research/cn-account-catalog-source-observation-20261008.md.\n')
    origins=[]
    for rel in sorted(set(SOURCES)|set(books)):
        data=(ROOT/rel).read_bytes();save('source/'+rel,data);origins.append(dict(path=rel,snapshot='source/'+rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ('round','literal_directory_deadline_observation_boundaries_added','existing_cn_account_success_source_bindings_strengthened','new_complete_bidirectional_routes')}))
if __name__=='__main__':main()
