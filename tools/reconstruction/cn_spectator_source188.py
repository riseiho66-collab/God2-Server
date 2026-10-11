"""Round188 actual CN source provenance; file IO/hash only, no runtime/tests."""
from pathlib import Path
import hashlib
import json
import sys

SERVER=Path(__file__).resolve().parents[2]
ROUND=SERVER/'artifacts/integration/packet-connections-20261006/native-spectator-target-identity-source-01'
OUT=ROUND/'agents/cn-spectator-source'
OWN='tools/reconstruction/cn_spectator_source188.py'
ADDED=['src/cn/world/SharedNativeSpectatorSource.h','src/cn/world/SharedNativeSpectatorSource.cpp']
STABLE=ADDED+['src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/game/SharedNativeWorldTransports.h','src/game/SharedNativeWorldTransports.cpp',
    'src/game/SharedNativeSpectatorPublication.h','src/game/SharedNativeSpectatorPublication.cpp',
    'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/cn/net/CnTransportSession.h','src/cn/net/CnTransportSession.cpp','src/cn/protocol/CnTransport.h']
CONTEXT=['src/game/SharedWorldHost.h','src/game/SharedWorldHost.cpp',
    'src/game/SharedTaiwanNativeSpectatorSource.h','src/game/SharedTaiwanNativeSpectatorSource.cpp',
    'src/core/SharedTaiwanNativeWorldHostPlan.h','src/core/SharedTaiwanNativeWorldHostPlan.cpp',
    'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp',
    'src/game/SharedNativeSpectatorTargets.h','src/game/SharedNativeSpectatorTargets.cpp',
    'src/cn/protocol/CnSpectator6E.h','AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']


def sha(raw):return hashlib.sha256(raw).hexdigest()


def dump(rel,value):
    p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as stream:stream.write((json.dumps(value,indent=2)+'\n').encode())


def retain(rel,path,original=None):
    raw=path.read_bytes();p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as stream:stream.write(raw)
    return {'path':original or path.relative_to(SERVER).as_posix(),'copy':rel,'bytes':len(raw),'sha256':sha(raw)}


def findings(final):
    return {'round':188,'BATCHFINAL_received':final,'source_files_added':ADDED,'owned_cpp_additions':2,
        'native_original_inputs':0,'new_bounded_native_spans':0,'new_bounded_native_bytes':0,'new_native_relations':[],
        'retained_bounded_native_spans':0,'retained_bounded_native_bytes':0,
        'new_opcodes':0,'new_phase_bindings':0,'new_complete_routes':0,
        'receiver_contexts':14,'qualified_receiver_contexts':12,
        'unresolved_helpers':[{'va':va,'phase':None,'slot':None,'producer':None} for va in ['0047DE70','004812B0']],
        'whole_game_route_denominator':None,'whole_game_percentage':None,
        'actual_source_connections':[
            {'key':'actual_fixed_CN_ingress','scope':'Explicit create actual CN connection/full Lease/common presence/private transport registry/real WorldOwner/budgets returns ingress/invalidate/release binding. Initial pre-ready construction performs no early lookup; first actual ready6E acquires and saves original private registry Token. Permanent connection retention is weak.'},
            {'key':'independent_CN_raw_request','scope':'Uses actual independently supplied CnSpectator6E header, exact logical9/rawbody8 copy before effects, includes untouched body1..3 and full raw DWORD. Observed mode2/context0 shape is not battle permission. We read C++ header only, not its native PE evidence; no native span recounted.'},
            {'key':'full_root_UI_target_scope','scope':'Strong actual CN receiver precedes all repository observations. Current brackets full common root/saved position/exact Token/optional UI/target views; target.ui and independent native_ui must be same publication lineage. Negative/ForeignContext observations remain facts for real other-mode1 DWORD namespaces, never grants or blanket admission rejection.'},
            {'key':'real_native_phase_and_execution','scope':'Mandatory WorldOwner.current qualifies actual CN phase/battle membership/incarnation/execution ticket/namespace/rules/profile; Scope has no fabricated CN phase or battle counter. Execute called once, post checks read fresh actual scope, same Result retained throughout.'},
            {'key':'actual_logical_held_queue','scope':'Actual nonempty ordered logical records or explicit noReply decision only. Full logical vector deep-copied before queue effects; same actual Connection held publication supplies original native framing/encryption, BeforeRelease observer and AfterRelease current. No pre-encrypted double encode, same-opcode ACK, default data or retry.'},
            {'key':'exact_async_lifetime_and_poison','scope':'Active pending weak reference avoids lasting source/connection cycle; temporary pending strongly retains actual receiver through queue completion. Wrong-thread checks precede flags. Nested ingress/parent active invalidation/release terminalizes observing invocation; completion once outside source stage. Own release clears saved weak Token only, never common registry/presence/successor.'},
            {'key':'released_prefix_fact','scope':'Pending locally_released is monotonic true before completed early return, including late true after cancellation. Failed AfterRelease qualification reports input rejected while preserving released-prefix fact; never reruns execute or rewrites old completion. Volatile local fact is not durable recovery/socket/native-client receipt.'}],
        'gaps':['Real native WorldOwner phase/battle/admission/exit/operation recovery/actual reply suppliers remain OPEN.',
            'Explicit core UI/D0 issuer/target mappings do not recover all official raw DWORD namespaces or role-pool authority.',
            'Actual Main installation, native client acceptance, durable committed/released-prefix recovery and whole-game routes remain OPEN.'],
        'builds_tests_runtime_native_api_codec_db_deploy':False}


def ready():
    if (OUT/'seal.json').exists():raise RuntimeError('Immutable capture')
    manifest=ROUND/'before-manifest.json'
    if sha(manifest.read_bytes())!='6b9ec7faf43f692cdf92df9150845f23f8179dadaf47a42725aa8556509718d6':
        raise ValueError('Exact freshbefore1341 required')
    fresh={row['path']:row for row in json.loads(manifest.read_bytes())};before=[];absent=[]
    for n,rel in enumerate(STABLE+CONTEXT+[OWN]):
        if rel not in fresh:absent.append(rel);continue
        row=fresh[rel];p=ROUND/row['snapshot'];raw=p.read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise ValueError('Before source changed '+rel)
        saved=retain(f'before/b{n:02d}{Path(rel).suffix}',p,rel)
        saved.update({'snapshot_original':str(p.resolve()),'epoch':'Full actual freshbefore1341 source, historical not current pin'})
        before.append(saved)
    dump('before-source-origins.json',before)
    dump('source-absence.json',{'absent_freshbefore1341':absent,'excluded_current_pins':CONTEXT})
    dump('source-ready-source-origins.json',[retain(f'source-ready/r{n:02d}{Path(rel).suffix}',SERVER/rel) for n,rel in enumerate(ADDED+[OWN])])
    dump('derived-inputs.json',[retain('derived/freshbefore1341.json',manifest,str(manifest.resolve()))])
    dump('findings-source-ready.json',findings(False))
    print(json.dumps({'state':'source-ready','owned_new_cpp':2,'native_original_inputs':0,'tool_sha256':sha((SERVER/OWN).read_bytes())}))


def final():
    if (OUT/'seal.json').exists():raise RuntimeError('Immutable capture')
    ready_rows=json.loads((OUT/'source-ready-source-origins.json').read_bytes())
    intermediate=json.loads((OUT/'intermediate-source-origins.json').read_bytes())
    for row in ready_rows+intermediate:
        raw=(OUT/row['copy']).read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise ValueError('Actual epoch changed '+row['copy'])
    current=[retain(f'current/c{n:02d}{Path(rel).suffix}',SERVER/rel) for n,rel in enumerate(STABLE+[OWN])]
    context=[retain(f'context-final/k{n:02d}{Path(rel).suffix}',SERVER/rel) for n,rel in enumerate(CONTEXT)]
    dump('current-source-origins.json',current);dump('context-final-source-origins.json',context)
    dump('original-inputs.json',[{**row,'path':str((SERVER/row['path']).resolve())} for row in current+context])
    dump('native-original-inputs.json',[])
    dump('source-epoch-changes.json',[{'path':rel,'first_cpp_sha256':next(row['sha256'] for row in intermediate if row['path']==rel),
        'source_ready_sha256':next(row['sha256'] for row in ready_rows if row['path']==rel),
        'final_sha256':next(row['sha256'] for row in current if row['path']==rel)} for rel in ADDED])
    dump('findings.json',findings(True))
    with (OUT/'README.txt').open('xb') as stream:stream.write(('Round188 actual CN typed6E source/real held queue.\n'
        'New C++2, native inputs/spans/relations/opcodes/phases/fullroutes0.\n'
        'No fabricated CN battle counter, no default rights/ACK, no retry of committed/released prefixes.\n'
        'Actual preexisting full before snapshots, new-source absence, first implementation, source-ready/current/finalcontext kept as separate actual epochs.\n'
        'Root8/common2/native-header3rdparty/governing docs are finalcontext, not current pins.\n'
        'Only source file/hash capture; no native/codec execution/build/test/API/DB/deployment.\n').encode())
    paths=sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file())
    with (OUT/'LIST.txt').open('xb') as stream:stream.write(('\n'.join(sorted(paths+['LIST.txt']))+'\n').encode())
    members=[{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(OUT.rglob('*')) if p.is_file()]
    seal={'round':188,'immutable':True,'members':members,'member_count':len(members),'member_bytes':sum(row['bytes'] for row in members),
        'current_source_count':len(current),'context_original_count':len(context),'all_actual_original_count':len(current+context),'native_original_count':0}
    dump('seal.json',seal)
    print(json.dumps({key:seal[key] for key in ['member_count','member_bytes','current_source_count','context_original_count','all_actual_original_count','native_original_count']}
        | {'files_including_seal':len(members)+1,'seal_sha256':sha((OUT/'seal.json').read_bytes()),'tool_sha256':sha((SERVER/OWN).read_bytes())}))


if __name__=='__main__':
    if sys.argv[1:]==['--final']:final()
    elif not sys.argv[1:]:ready()
    else:raise ValueError('Only source-ready or explicit --final capture')
