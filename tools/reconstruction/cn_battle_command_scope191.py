"""Round191 exact source epochs; file/hash/copy only, no native/runtime/tests."""
from pathlib import Path
import hashlib
import json
import sys

SERVER=Path(__file__).resolve().parents[2]
ROUND=SERVER/'artifacts/integration/packet-connections-20261006/cn-native-battle-command-group-source-01'
OUT=ROUND/'agents/cn-battle-command-scope'
OWN='tools/reconstruction/cn_battle_command_scope191.py'
CHANGED=['src/cn/world/SharedNativeBattleCommandSource.h','src/cn/world/SharedNativeBattleCommandSource.cpp']
STABLE=CHANGED+['src/game/SharedNativeWorldTransports.h','src/game/SharedNativeWorldTransports.cpp',
    'src/cn/protocol/CnBattleCommand35.h','src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/cn/net/CnTransportSession.h','src/cn/net/CnTransportSession.cpp','src/cn/protocol/CnTransport.h']
CONTEXT=['src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp',
    'src/cn/world/SharedNativeBattleCommandGroups.h','src/cn/world/SharedNativeBattleCommandGroups.cpp',
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
    return {'round':191,'BATCHFINAL_received':final,'owned_cpp_modified':2,'source_files_modified':CHANGED,
        'native_original_inputs':0,'new_bounded_native_spans':0,'new_bounded_native_bytes':0,'new_native_relations':[],
        'retained_bounded_native_spans':0,'retained_bounded_native_bytes':0,
        'new_opcodes':0,'new_phase_bindings':0,'new_complete_routes':0,
        'receiver_contexts':14,'qualified_receiver_contexts':12,
        'unresolved_helpers':[{'va':va,'phase':None,'slot':None,'producer':None} for va in ['0047DE70','004812B0']],
        'whole_game_route_denominator':None,'whole_game_percentage':None,
        'actual_source_connections':[
            {'key':'actual_original_token_scope','scope':'Scope.native_token copies exact original Pending Token along with full actual Lease/common character/saved position. same_scope adds private registry same_registration around pure WorldOwner Current. Token supplies endpoint incarnation only, never battle grant, clock, core actor mapping or context82.'},
            {'key':'opaque_actual_operation_evidence','scope':'OperationEvidence virtual destructor and optional shared_ptr<const OperationEvidence> Result.evidence retain real owner-supplied immutable proof through unchanged defined Current stages: explicit no_reply keeps BeforeExecute/AfterExecute/BeforeQueue; held replies additionally use BeforeRelease/AfterRelease. Reply remains explicit; Result(Reply) compatibility retained with null evidence. Source never interprets/creates a fake proof or default success.'},
            {'key':'exact_once_real_owner_release','scope':'WorldOwner.release_binding(full Lease,original Token) noexcept defaults empty for existing owners. Source terminalizes before callback, marks once guard and clears only own saved registration before external hook. No token means no fabricated hook argument. Real owner must retire only this exact bound pending operation/group; no source common/transport/successor release.'},
            {'key':'deferred_cancel_outside_actual_stage','scope':'Source.release during Current/Execute/submitting terminalizes invocation but defers real cancellation; unchanged post endpoint qualification fails and final finish(false) invokes same hook outside Stage. Hook recursion sees consumed capability/once guard, no repeated cancel. finish(false), external release and invalid later ingress with original registration use same once path before original done; no in-stage outer continuation.'},
            {'key':'preserved_native_request_and_queue','scope':'Original exact17/raw request/unknown kind and fields, actual strong receiver before repository visits, lazy original token, once Execute, logical deep-copy/posted held approval/inlinefalse deferral/late true localprefix/once continuation remain. No speculative grant cache, semantic duplicate policy, cost, native ACK, durable receipt or new runtime activation.'}],
        'gaps':['Actual native battle/actor/context82/grant86/incarnation/skill/item/target/settlement/reply suppliers remain OPEN.',
            'Group owner implementation is separate caller context. Source token/evidence/cancel support alone recovers no battle authority or complete gameplay route.',
            'Main selection/durable committed-released prefix recovery/native-client acceptance/whole-game route inventory remain OPEN.'],
        'builds_tests_runtime_native_api_codec_db_deploy':False}

def ready():
    if (OUT/'seal.json').exists():raise RuntimeError('Immutable capture')
    manifest=ROUND/'before-manifest.json'
    if sha(manifest.read_bytes())!='c404b8c0d8a12061cb79fbe0a30c256e921826478880dcf8f6d15a96ddf6e6b3':
        raise ValueError('Exact freshbefore1365 required')
    dump('source-ready-source-origins.json',[retain(f'source-ready/r{n:02d}{Path(rel).suffix}',SERVER/rel) for n,rel in enumerate(CHANGED+[OWN])])
    dump('derived-inputs.json',[retain('derived/freshbefore1365.json',manifest,str(manifest.resolve()))])
    dump('findings-source-ready.json',findings(False))
    print(json.dumps({'state':'source-ready','owned_cpp_modified':2,'native_original_inputs':0,'tool_sha256':sha((SERVER/OWN).read_bytes())}))

def final():
    if (OUT/'seal.json').exists():raise RuntimeError('Immutable capture')
    epochs=[]
    for rel in ['before-source-origins.json','intermediate-source-origins.json','source-ready-source-origins.json']:
        epochs+=json.loads((OUT/rel).read_bytes())
    for row in epochs:
        raw=(OUT/row['copy']).read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise ValueError('Actual epoch changed '+row['copy'])
    current=[retain(f'current/c{n:02d}{Path(rel).suffix}',SERVER/rel) for n,rel in enumerate(STABLE+[OWN])]
    context=[retain(f'context-final/k{n:02d}{Path(rel).suffix}',SERVER/rel) for n,rel in enumerate(CONTEXT)]
    dump('current-source-origins.json',[dict(row,path=str((SERVER/row['path']).resolve())) for row in current])
    dump('final-context-source-origins.json',context)
    dump('original-inputs.json',[dict(row,path=str((SERVER/row['path']).resolve())) for row in current+context])
    dump('native-original-inputs.json',[]);dump('sites.json',[])
    dump('findings.json',findings(True));dump('gaps.json',findings(True)['gaps'])
    dump('actual-read-epochs.json',{'before_fullsource':17,'new_owned_tool_absence':1,'initial_implementation':2,
        'source_ready':3,'current_stable':len(current),'final_context':len(context),
        'historical_copies_are_not_current_pins':True,'native_original_inputs':0,'missing_owned_transient_epochs':[],
        'scope':'Only actual observed parent/peer epochs recorded; no claim to reconstruct unobserved transient versions.'})
    members=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file():
            raw=p.read_bytes();members.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
    dump('LIST.json',members)
    list_raw=(OUT/'LIST.json').read_bytes();members.append({'path':'LIST.json','bytes':len(list_raw),'sha256':sha(list_raw)})
    dump('seal.json',{'round':191,'scope':'Complete immutable source-only agent artifact','members':members,
        'member_count':len(members),'member_bytes':sum(row['bytes'] for row in members),
        'native_original_input_count':0,'current_source_count':len(current),'final_context_count':len(context)})
    print(json.dumps({'state':'sealed','seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),
        'total_files_with_seal':len(members)+1,'member_bytes':sum(row['bytes'] for row in members),
        'current':len(current),'context':len(context),'actual_original_inputs':len(current)+len(context),
        'native_original_inputs':0,'tool_sha256':sha((SERVER/OWN).read_bytes())}))

if __name__=='__main__':
    {'ready':ready,'final':final}[sys.argv[1]]()
