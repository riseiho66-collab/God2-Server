"""File-only CN selection07 appearance/panel source accounting; no C++ run."""
import difflib,hashlib,json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT,PIN

NAME='cn-selection-appearance-source-01'
ROUND='20261007-cn-selection-appearance-source'
SOURCES=('src/cn/protocol/CnCharacterSummary.h','src/cn/assets/CnAppearanceResources.h',
    'src/cn/assets/CnAppearanceResources.cpp','src/cn/assets/CnAppearanceRomInputs.h',
    'src/cn/assets/CnAppearanceRomInputs.cpp',
    'tools/reconstruction/cn_selection_appearance_source_delivery.py',
    'docs/research/cn-selection-appearance-source-20261007.md')
REMAINING=[
    'Actual complete07 native flags/opaque18/inactive rows/visibility/slot mapping issuer and authoritative shared model projection remain unconfigured.',
    'Selection HeroDoll cache/UI1792CC filename bank/current handle lifetime/ACT/rendering are not the in-world NPC two-cache source and remain open.',
    'Full1D/0A/world1F/02/2A/6F sources, common TW registry, formal PC/web/WSS hosting, credential revisions/ABA/revocation and all gameplay/numeric/full denominator remain open.'
]
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Fresh before-source receipt required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    bookkeeping=('docs/PACKET_CONNECTION_GOAL_20261006.md',
        'artifacts/integration/packet-connections-20261006/packet-route-ledger.json')
    preserved=[];after=[];original={}
    for row in before:
        old=(out/row['snapshot']).read_bytes()
        if sha(old)!=row['sha256']:raise RuntimeError('Before bytes differ')
        original[row['path']]=old
        if row['path'] in bookkeeping:continue
        data=(ROOT/row['path']).read_bytes()
        if row['path'] not in SOURCES:
            if data!=old:raise RuntimeError('Frozen context differs: '+row['path'])
            preserved.append(row)
        rel='after/'+row['path'];save(rel,data)
        after.append(dict(path=row['path'],snapshot=rel,sha256=sha(data),bytes=len(data)))
        if data!=old:
            diff=''.join(difflib.unified_diff(old.decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+row['path'],tofile='after/'+row['path']))
            save('diff/'+Path(row['path']).name+'.diff',diff.encode('utf-8'))
    envelopes=json.loads((out/'native/function-envelopes.json').read_text(encoding='utf-8'))
    if envelopes['sha256']!=PIN:raise RuntimeError('Native primary differs')
    # Prior seals remain immutable; compare overlapping native ranges only.
    prior=base/'cn-summary-opaque-agent-01'
    prior_manifest=base/'cn-login-record-source-observation-01/manifest.json'
    data=prior_manifest.read_bytes()
    if sha(data)!='96fa890c5899cf04c88e0740164ee98584668a36af184f17c30714a710251fb7' or not json.loads(data)['sealed']:
        raise RuntimeError('Previous source seal differs')
    save('retained-previous/manifest.json',data)
    save('retained-native/prior-opaque-findings.json',(prior/'findings.json').read_bytes())
    lineage=dict(raw_source='UI1792D0 complete07,36-byte rows; component payload1A/row24',
        preview_act='0044315C and004431BF literal0 ->004237F0; no driver/aux/alternate operand',
        face_variant='0044318E head lookup;00443197 head byte2A;004431B1 BYTE base+face low5 when base>=2',
        palettes='00443313 selected raw high3,00443325 unselected7; palette-bank validity not established',
        ordering='004433AB calls00443640 nonzero after four preview parts; repeated display may use changed body category',
        panel_writes=['00443694 row24 low4=low1, preserve high4',
            '004436DF row20..21 preserve low3/high8, clear bits3..4, bits5..7 modulo7',
            '0044371B row22..23 low4 preserved, each six-bit field modulo10',
            '004438BE/004438C8 row16 FF sentinel ->1 locally'],
        cache='004430EA owner+d8c HeroDoll WORD1E resetFFFF;004432A5 ->00446740/UI1792CC filename bank ->004197E0',
        stage='Explicit ReceivedBeforePanel or AfterPanel, no default stage or native UI owner manufactured',
        authority='Complete raw07 retained; local display never mutates common storage/wire or issues native authority',
        native_executed=False,whole_CFG_or_indirect_closed=False)
    dump('native/consumer-lineage.json',lineage)
    facts=dict(round=ROUND,cn_native_sha256_context=PIN,
        previous_goal_turn_classification='no progress: status-only answer; resumed with native consumer dataflow and new selection resource source',
        cn_selection_resource_input_chains_added=1,cn_selection_local_panel_projections_added=1,
        native_function_envelopes_read=len(envelopes['ranges']),native_function_bytes_read=sum(i['bytes'] for i in envelopes['ranges']),
        native_opcode_newly_discovered=0,source_issuer_configured=False,formal_application_hosted=False,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,whole_game_route_total=None,whole_game_completed_routes=None,
        whole_game_completion_percent=None,levels_changed=False,common_storage_changed=False,
        build_run=False,tests_run=False,runtime_run=False,Cplusplus_resource_reader_run=False,database_access=False,deployed=False,
        preserved_contexts=preserved,remaining=REMAINING)
    dump('findings.json',facts)
    origins=[]
    for rel in SOURCES:
        data=(ROOT/rel).read_bytes();snap='source/'+rel;save(snap,data)
        origins.append(dict(path=rel,snapshot=snap,sha256=sha(data),bytes=len(data)))
    dump('source/source-origins.json',origins)
    path=base/'packet-route-ledger.json';ledger=json.loads(path.read_text(encoding='utf-8'))
    ledger['cn_selection_appearance_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(
        name='Complete CN07 active row and explicit native local display stage ->actual HeroDoll four-part selection ->original ROM input metadata',
        version_scope='cn-selection-source-only',status='New consumer/resource input source; real07 issuer and UI/cache/bank/ACT/runtime owner remain open',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual native07 shared identity/visibility/opaque/slot issuer and selection UI1792CC filename-bank lifetime/ACT owner; raw07 and post-panel projection stay distinct. Full auth/world/gameplay/numeric/PC/web/WSS suppliers and whole-game denominator remain open; PHASE1 source only.'
    path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/bookkeeping[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN07 native selection resource input source ('+ROUND+')\n\n'
            'Saved11 primary native envelopes/3865B;00443080 preview literalActType0/four HeroDoll rows, head face-base BYTE derivation, selected palette operands and separate00443640 local mutations recovered. Full raw75-byte07 plus explicit pre/post-panel stage retained; resource rows connect to original ROM-input readers without fabricated2A/6F/driver0/selection or in-world cache. Native levels and shared saves unchanged. New opcode/phase/owner/full routes0; formal07 issuer/cache-bank-ACT/rendering and all auth/world/gameplay/denominator remain open. No build/test/C++resource reader/runtime/DB/deploy. See research/cn-selection-appearance-source-20261007.md.\n')
    for rel in bookkeeping:
        data=(ROOT/rel).read_bytes();snap='after/'+rel;save(snap,data)
        after.append(dict(path=rel,snapshot=snap,sha256=sha(data),bytes=len(data)))
        diff=''.join(difflib.unified_diff(original[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='after/'+rel))
        save('diff/'+Path(rel).name+'.diff',diff.encode('utf-8'))
    dump('after-manifest.json',after)
    print(json.dumps({k:facts[k] for k in ('round','cn_selection_resource_input_chains_added','native_function_bytes_read','new_complete_bidirectional_routes')}))
if __name__=='__main__':main()
