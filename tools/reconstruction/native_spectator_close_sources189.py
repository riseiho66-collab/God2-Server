"""Round189 source provenance: file copy/hash only; no native/runtime/tests."""
from pathlib import Path
import hashlib
import json
import sys

SERVER=Path(__file__).resolve().parents[2]
ROUND=SERVER/'artifacts/integration/packet-connections-20261006/native-spectator-close-record-source-01'
OUT=ROUND/'agents/native-spectator-close-sources'
OWN='tools/reconstruction/native_spectator_close_sources189.py'
CHANGED=['src/game/SharedTaiwanNativeSpectatorSource.h','src/game/SharedTaiwanNativeSpectatorSource.cpp',
    'src/cn/world/SharedNativeSpectatorSource.h','src/cn/world/SharedNativeSpectatorSource.cpp']
STABLE=CHANGED+['src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/game/SharedNativeWorldTransports.h','src/game/SharedNativeWorldTransports.cpp',
    'src/game/SharedNativeSpectatorPublication.h','src/game/SharedNativeSpectatorPublication.cpp',
    'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/cn/net/CnTransportSession.h','src/cn/net/CnTransportSession.cpp','src/cn/protocol/CnTransport.h',
    'src/protocol/RecoveredSpectator6E.h','src/cn/protocol/CnSpectator6E.h','src/protocol/RecoveredWorldFrame.h']
CONTEXT=['src/protocol/RecoveredWorldRecords.h','src/game/SharedTaiwanNativeRecordHandlerSource.cpp',
    'src/game/SharedTaiwanWorldRecordSource.h','src/game/SharedTaiwanWorldRecordSource.cpp',
    'src/net/Session.h','src/net/Session.cpp','src/core/Application.cpp',
    'src/core/SharedTaiwanNativeWorldHostPlan.h','src/core/SharedTaiwanNativeWorldHostPlan.cpp',
    'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp',
    'src/game/SharedNativeSpectatorTargets.h','src/game/SharedNativeSpectatorTargets.cpp',
    'src/protocol/RecoveredSpectatorClose.h','src/cn/protocol/CnSpectatorClose.h',
    'AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def dump(rel,value):
    p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as stream:stream.write((json.dumps(value,indent=2)+'\n').encode())

def retain(rel,path,original=None):
    raw=path.read_bytes();p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as stream:stream.write(raw)
    return {'path':original or path.relative_to(SERVER).as_posix(),'copy':rel,'bytes':len(raw),'sha256':sha(raw)}

def findings(final):
    return {'round':189,'BATCHFINAL_received':final,'owned_cpp_modified':4,'source_files_modified':CHANGED,
        'native_original_inputs':0,'new_bounded_native_spans':0,'new_bounded_native_bytes':0,'new_native_relations':[],
        'retained_bounded_native_spans':0,'retained_bounded_native_bytes':0,
        'new_opcodes':0,'new_phase_bindings':0,'new_complete_routes':0,
        'receiver_contexts':14,'qualified_receiver_contexts':12,
        'unresolved_helpers':[{'va':va,'phase':None,'slot':None,'producer':None} for va in ['0047DE70','004812B0']],
        'whole_game_route_denominator':None,'whole_game_percentage':None,
        'actual_source_connections':[
            {'key':'independent_optin_close_owner','scope':'TW and CN keep mandatory original WorldOwner and append optional independent CloseOwner to create. CloseOwner selection requires actual same-source publication. Binding old field order remains, trailing close_dispatch/close_ingress is empty if not selected; no implicit6E capability enables close.'},
            {'key':'preserved_actual_close_bytes','scope':'Exact independent close header Request keeps opcode and opaque byte. TW typed source admits only A3/CB; CN close ingress decodes exact logical2. The peer headers describe actual pointer-high-byte provenance; this worker reads headers only, not PE evidence. No opaque normalization, invented nonce, epoch, encoder, ACK or native span recount.'},
            {'key':'full_ready_recipient_and_UI','scope':'Same actual full ready Lease/original private registry Token/full common root/saved position bracket actual publication observations. TW retains true Session phase/battle generation; CN invents no corresponding field. Strong actual receiver precedes repository observation. Selected UI negative states remain facts, not rights.'},
            {'key':'no_synthetic_close_target','scope':'Internal variant retains exact6E or Close request. Both first and repeated target resolver visits require actual6E alternative; Close Scope target remains nullopt even if target source selected. No context0/D0 lookup or zero-cast shared namespace is synthesized.'},
            {'key':'separate_actual_authority_once','scope':'Pure pre/post Current and single Execute dispatch to original WorldOwner for6E or independent CloseOwner for close. Actual native window/phase/rights/membership/request/reply qualification is mandatory CloseOwner responsibility; no automatic retirement/leave-battle decision or default result. Fresh actual post Scope allows an actual authorized UI status/phase transition.'},
            {'key':'preserved_ordered_reply_lifetime','scope':'TW returns original actual encrypted Reply or explicit native noReply through mixed order. CN keeps original logical deep-copy/held queue/BeforeRelease/AfterRelease lifecycle, monotonic locally_released including late true after cancellation, once original continuation and no prefix retry. Source reentry, parent invalidation, exact own cleanup and weak permanent connection remain; no shared successor cleanup.'}],
        'gaps':['Actual CloseOwner native window/phase/rights/operation/reply suppliers and existing6E WorldOwner remain OPEN.',
            'The source does not invoke retirement_for_ui/retire_for_ui; a real independently qualified CloseOwner must capture actual UI lineage before real core close and decide cleanup.',
            'Real Main installation, durable committed/released-prefix recovery, complete original gameplay routes and native-client acceptance remain OPEN.'],
        'builds_tests_runtime_native_api_codec_db_deploy':False}

def ready():
    if (OUT/'seal.json').exists():raise RuntimeError('Immutable capture')
    manifest=ROUND/'before-manifest.json'
    if sha(manifest.read_bytes())!='1c7a98ae5abd06ccdfac7d83e41370d6524df074295a6afb20a318d3a779a309':
        raise ValueError('Exact freshbefore1351 required')
    fresh={row['path']:row for row in json.loads(manifest.read_bytes())};before=[];absent=[]
    for n,rel in enumerate(STABLE[len(CHANGED):]+CONTEXT+[OWN]):
        if rel not in fresh:absent.append(rel);continue
        row=fresh[rel];p=ROUND/row['snapshot'];raw=p.read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise ValueError('Historical source changed '+rel)
        saved=retain(f'before-context/b{n:02d}{Path(rel).suffix}',p,rel)
        saved.update({'snapshot_original':str(p.resolve()),'epoch':'Full actual freshbefore1351, historical not current'})
        before.append(saved)
    dump('before-context-source-origins.json',before)
    dump('context-source-absence.json',{'absent_freshbefore1351':absent,'excluded_current_pins':CONTEXT})
    dump('source-ready-source-origins.json',[retain(f'source-ready/r{n:02d}{Path(rel).suffix}',SERVER/rel) for n,rel in enumerate(CHANGED+[OWN])])
    dump('derived-inputs.json',[retain('derived/freshbefore1351.json',manifest,str(manifest.resolve()))])
    dump('findings-source-ready.json',findings(False))
    print(json.dumps({'state':'source-ready','owned_cpp_modified':4,'native_original_inputs':0,'tool_sha256':sha((SERVER/OWN).read_bytes())}))

def final():
    if (OUT/'seal.json').exists():raise RuntimeError('Immutable capture')
    epochs=[]
    for rel in ['before-source-origins.json','before-context-source-origins.json','intermediate-source-origins.json','source-ready-source-origins.json']:
        epochs+=json.loads((OUT/rel).read_bytes())
    for row in epochs:
        raw=(OUT/row['copy']).read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise ValueError('Actual epoch changed '+row['copy'])
    current=[retain(f'current/c{n:02d}{Path(rel).suffix}',SERVER/rel) for n,rel in enumerate(STABLE+[OWN])]
    context=[retain(f'context-final/k{n:02d}{Path(rel).suffix}',SERVER/rel) for n,rel in enumerate(CONTEXT)]
    dump('current-source-origins.json',current);dump('final-context-source-origins.json',context)
    dump('original-inputs.json',[dict(row,path=str((SERVER/row['path']).resolve())) for row in current+context])
    dump('native-original-inputs.json',[])
    dump('findings.json',findings(True));dump('sites.json',[])
    dump('gaps.json',findings(True)['gaps'])
    dump('actual-read-epochs.json',{'before':4,'before_context':len(json.loads((OUT/'before-context-source-origins.json').read_bytes())),
        'initial_implementation':4,'source_ready':5,'current_stable':len(current),'final_context':len(context),
        'historical_copies_are_not_current_pins':True,'native_original_inputs':0,'missing_transient_epochs':[]})
    members=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file():
            raw=p.read_bytes();members.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
    dump('LIST.json',members)
    list_raw=(OUT/'LIST.json').read_bytes();members.append({'path':'LIST.json','bytes':len(list_raw),'sha256':sha(list_raw)})
    dump('seal.json',{'round':189,'scope':'Complete immutable source-only agent artifact','members':members,
        'member_count':len(members),'member_bytes':sum(row['bytes'] for row in members),
        'native_original_input_count':0,'current_source_count':len(current),'final_context_count':len(context)})
    print(json.dumps({'state':'sealed','seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),
        'total_files_with_seal':len(members)+1,'member_bytes':sum(row['bytes'] for row in members),
        'current':len(current),'context':len(context),'actual_original_inputs':len(current)+len(context),
        'native_original_inputs':0,'tool_sha256':sha((SERVER/OWN).read_bytes())}))

if __name__=='__main__':
    {'ready':ready,'final':final}[sys.argv[1]]()
