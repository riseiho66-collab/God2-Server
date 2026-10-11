"""File-only round176 actual CN selected-location source/caller delivery.

Retain full original inputs/source epochs. No runtime, builds, tests or native
rescans; round175 native sites remain retained evidence, not new spans/routes.
"""
from pathlib import Path
import difflib
import json
from .cn_receiver_owner_frontier169 import sha

SERVER=Path(__file__).resolve().parents[2]
ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
OUT=ROOT/'tw-native-host-composition-source-01/agents/cn-selection-source'
PRIOR=ROOT/'tw-native-resource-selection-source-01/agents/cn-location-frontier'
OWN='tools/reconstruction/cn_selected_character_location176.py'
CHANGED=['src/cn/auth/SharedSelectedCharacterLocationSource.h',
    'src/cn/auth/SharedSelectedCharacterLocationSource.cpp',
    'src/cn/auth/SharedAccountSelection.h', 'src/cn/auth/SharedLoginComposition.h',
    'src/cn/auth/SharedLoginComposition.cpp']
EXTRA=['tools/reconstruction/cn_receiver_owner_frontier169.py',
    'tools/reconstruction/cn_account_location_frontier175.py',
    'src/cn/net/SharedListenerRegistry.h','src/cn/net/SharedListenerRegistry.cpp',
    'CMakeLists.txt','src/core/Application.cpp']
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'


def dump(rel,value):
    target=OUT/rel;target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream:
        stream.write((json.dumps(value,indent=2,ensure_ascii=True)+'\n').encode())


def retain(rel,path,repository=False):
    raw=path.read_bytes();target=OUT/rel;target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream:stream.write(raw)
    return {'path':path.relative_to(SERVER).as_posix() if repository else str(path),
            'copy':rel,'bytes':len(raw),'sha256':sha(raw)}


def sources():
    before=json.loads((OUT/'before-source-origins.json').read_text(encoding='utf-8'))
    return [row['path'] for row in before]+CHANGED[:2]+EXTRA+[OWN]


def source_site(relative,needle):
    raw=(SERVER/relative).read_bytes();token=needle.encode();offset=raw.index(token)
    return {'source':relative,'byte_offset':offset,'line':raw[:offset].count(b'\n')+1,
            'actual_source_text':needle,'source_sha256':sha(raw)}


def main():
    if not (OUT/'before-source-origins.json').is_file() or (OUT/'findings.json').exists():
        raise RuntimeError('Require fresh176 before; preserve existing evidence')
    native=[]
    for i,row in enumerate(json.loads((PRIOR/'native-original-inputs.json').read_text(encoding='utf-8'))):
        path=Path(row['path']);raw=path.read_bytes()
        if sha(raw)!=row['sha256'] or len(raw)!=row['bytes']:
            raise ValueError('Actual full original differs from retained175 pin: '+str(path))
        native.append(retain('native-original-inputs/input-'+f'{i:02d}'+path.suffix,path))
    dump('native-original-inputs.json',native)
    dump('before-additional-source-origins.json',
        [retain('before-additional/source-'+f'{i:02d}.bin',SERVER/rel,True) for i,rel in enumerate(EXTRA)])
    prior=[PRIOR/'findings.json',PRIOR/'seal.json',PRIOR/'native/new-sites.json',
           PRIOR/'native/retained-caller-catalog-sites.json',PRIOR/'native/selected-original-metadata.json',
           PRIOR/'native/selected-original-calls.json',PRIOR/'README.md']
    dump('derived-retained-inputs.json',[retain('retained175/'+f'{i:02d}-'+p.name,p)
                                       for i,p in enumerate(prior)])
    cpp='src/cn/auth/SharedSelectedCharacterLocationSource.cpp'
    composition='src/cn/auth/SharedLoginComposition.cpp'
    bindings=[
        {'id':'actual-directory-qualified-login-caller',
         'scope':'Verified account callback binds optional actual selected-location source AFTER from_catalog and BEFORE native directory binding/AccountSuccess.attach. Existing absent-config behavior retained.',
         'sources':[source_site(composition,'auto directory=SharedAccountDirectorySource::from_catalog'),
                    source_site(composition,'supplied->summaries=SharedSelectedCharacterLocationSource::bind'),
                    source_site(composition,'supplied->native.bind_directory_source'),
                    source_site(composition,'(void)SharedAccountSuccess::attach')]},
        {'id':'exact-selected-account-character-row-proof',
         'scope':'One actual selected ordinal/common character ID comes from mandatory State1A source and is matched to exact original07 ordered IDs and same-account full roots; no default/all-row grant.',
         'sources':[source_site(cpp,'auto selected=state->prepare(input);'),
                    source_site(cpp,'value->character_ids_[row]!=selected->selected_.character'),
                    source_site(cpp,'root.id==selected->selected_.character && root.account_id==scope.account')]},
        {'id':'retained-original07-and-separate-native-local-projection',
         'scope':'Only a COPY receives four exact first-nonzero06 bytes at wire07 3+row*0x24+0x20. The returned NativeSummary record/IDs/roots remain original; proof retains both complete75B records.',
         'sources':[source_site(cpp,'auto local=value->record_;'),
                    source_site(cpp,'std::copy(location->original.raw.begin(),location->original.raw.end(),local.begin()+start);'),
                    source_site(cpp,'auto proof=std::make_shared<const Proof>')],
         'character_row_offsets':['0x20','0x21','WORD+0x22'],
         'native_payload_offsets':['0x22','0x23','WORD+0x24'],
         'actual_native_state':'0x1A', 'native_creation_state_not_reused':'0x18',
         'raw_gameplay_semantics':None,'original07_rewritten':False},
        {'id':'original-issuer-directory-and-location-rights-current-chain',
         'scope':'Each original Prepared/BeforePublish/QueueAccepted/NameSubmission stage runs original issuer before/after mandatory real location/state1A/right observer with retained same directory and whole source data.',
         'sources':[source_site(cpp,'value->current_=[state,proof,original=std::move(original)]'),
                    source_site(cpp,'return observe([&]{return original(actual,check);}) &&'),
                    source_site(cpp,'proof->state1a.current_(actual,proof->state1a.revision_,check,observation)')]},
        {'id':'permanent-bound-source-reentrancy-poison',
         'scope':'Wrong-thread requests check first without touching flags. Nested summary/current permanently set terminal; every external callback checks before/after. Escaping exceptions poison through RAII. Shared bound state invalidates old proofs and cannot reset next operation.',
         'sources':[source_site(cpp,'if(state->busy) {state->terminal=true;return std::nullopt;}'),
                    source_site(cpp,'if(state->owner!=std::this_thread::get_id())return false;'),
                    source_site(cpp,'if(state->busy) {state->terminal=true;return false;}'),
                    source_site(cpp,'~Preparing(){if(std::uncaught_exceptions()>exceptions)terminal=true;busy=false;}')]}]
    dump('source/new-source-bindings.json',bindings)
    dump('source-ready-source-origins.json',[retain('source-ready/source-'+f'{i:02d}.bin',SERVER/rel,True)
                                           for i,rel in enumerate(sources())])
    diffs=[]
    for i,rel in enumerate(CHANGED):
        original=OUT/'before'/rel
        old=original.read_text(encoding='utf-8').splitlines(keepends=True) if original.exists() else []
        current=(SERVER/rel).read_text(encoding='utf-8').splitlines(keepends=True)
        text=''.join(difflib.unified_diff(old,current,fromfile='before/'+rel,tofile='current/'+rel))
        path=OUT/('diff/source-'+f'{i:02d}.diff');path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(text.encode())
        diffs.append({'source':rel,'copy':path.relative_to(OUT).as_posix(),'sha256':sha(path.read_bytes())})
    dump('source/owned-diffs.json',diffs)
    dump('source/review-revisions.json',[
        {'epoch':'initial','files':'intermediate-source-origins.json','review':'Actual caller/immutable75B/local projection and scope/row/common ID retained.'},
        {'epoch':'pre-poison','files':'intermediate-pre-poison-source-origins.json','review':'Proof copies passed explicitly, startup config preparation required, bind allocation/lifetime failures delivered to existing completion.'},
        {'epoch':'final','files':'source-ready-source-origins.json','review':'Root found caught nested rejection could revive outer proof; fixed permanent terminal poison shared by all retained proofs plus callback pre/post checks and escaping exception RAII. No compilation/runtime/tests.'}])
    findings={'round':176,'version_scope':'cn','native_sha256':PIN,
        'new_bounded_native_spans':0,'new_bounded_native_bytes':0,'new_native_relations':[],
        'retained175_native_spans_not_recounted':5,'retained175_native_relations_not_recounted':5,
        'new_source_bindings':bindings,'new_qualified_selected_location_source_bridges':1,
        'actual_login_composition_callers_added':1,'cpp_source_files_changed':5,'new_cpp_files':2,
        'owned_cpp_sources':CHANGED,'native_original_count':len(native),
        'explicit_config_domain':'Only active actual selected row/commonID with real current native state0x1A/location/rights/source proof. Empty account or ordinary not-yet-selected07 is not inferred; absent explicit config keeps existing path.',
        'complete_native07_issuer_recovered':False,'active_production_config':False,
        'original07_rewritten':False,'local_projection_only':True,'location_gameplay_meaning':None,
        'terminal_scope':'entire bound selected-location source and all retained proofs; no reset/retry',
        'receiver_contexts':14,'qualified_receiver_contexts':12,
        'unresolved_helpers':[{'address':a,'phase':None,'slot':None,'producer_pair':None}
                              for a in ('0047de70','004812b0')],
        'new_phase_opcode_bindings':0,'new_formal_source_owner_chains':0,
        'new_complete_bidirectional_routes':0,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'native_run':False,'emulation_run':False,
        'database_access':False,'deployed':False}
    dump('findings.json',findings)
    dump('stage-accounting.json',{'direction':'existing-account07-source-to-qualified-local-selection-observer',
        'actual_cpp_bridge':1,'actual_login_caller':1,'new_native_spans':0,'new_native_relations':0,
        'old175_spans_or_relations_recounted':0,'new_opcode_inventory':0,'complete_routes_added':0})
    dump('gaps.json',[
        'Actual Prepare/Current native state1A/source revision/rights issuer must configure this explicit domain. No fabricated proof, row, default visibility or all-account source is provided.',
        'Local projected75B is observed only. Original75B remains selection/admission/sent07; no original server07 producer or authoritative map/scene/coordinate meaning is recovered.',
        'Empty account and not-yet-selected ordinary07 do not fit the explicit active selected-row domain. Keep config absent until real peer proof exists; never default row0 or create a successful empty07.',
        'Permanent reentrancy/escaping-exception poison makes the whole bound source terminal, including prior proofs. A fresh actually qualified account bind is required; no operation reset reactivates it.',
        'This adds a real C++ source-to-login caller composition but does not complete world providers, original admission rights, native phase/opcode variants or full-game routes.',
        'Unknown47DE70/4812B0 phases remain null. No155formatter/capacity chain, locale candidates, global CFG/helper rescans or runtime verification were performed.'])
    print(json.dumps({'artifact':str(OUT),'changed_cpp':len(CHANGED),'new_cpp':2,
        'source_bindings':len(bindings),'full_native_originals':len(native),'current_sources':len(sources()),
        'new_native_spans':0,'new_routes':0}))


def capture():
    if not (OUT/'findings.json').is_file() or (OUT/'seal.json').exists():raise RuntimeError('No unsealed delivery')
    rows=[retain('current/source-'+f'{i:02d}.bin',SERVER/rel,True) for i,rel in enumerate(sources())]
    dump('current-source-origins.json',rows)
    full=json.loads((OUT/'native-original-inputs.json').read_text(encoding='utf-8'))
    full += [{**row,'path':str(SERVER/row['path'])} for row in rows]
    dump('original-inputs.json',full)
    listing=sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file())
    with (OUT/'LIST.txt').open('xb') as stream:stream.write(('\n'.join(listing+['LIST.txt'])+'\n').encode())
    members=[{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
             for p in sorted(OUT.rglob('*')) if p.is_file()]
    dump('seal.json',{'kind':'immutable round176 actual CN selected-location source/caller bridge',
        'files':members,'source_original_count':len(rows),'native_input_sha256':PIN,
        'complete_routes_added':0,'build_run':False,'tests_run':False,'native_run':False,'database_access':False})
    print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),
        'current_source_originals':len(rows),'full_actual_original_inputs':len(full),
        'tool_sha256':sha((SERVER/OWN).read_bytes()),
        'cpp_sha256':{rel:sha((SERVER/rel).read_bytes()) for rel in CHANGED}}))


if __name__=='__main__':
    import sys
    if sys.argv[1:]==['--capture-after-batchfinal']:capture()
    elif not sys.argv[1:]:main()
    else:raise SystemExit('Only file-only source retention or BATCHFINAL capture is supported')
