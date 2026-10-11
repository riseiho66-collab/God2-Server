"""Round190 actual source originals; file copy/hash only, no native/runtime/tests."""
from pathlib import Path
import hashlib
import json
import sys

SERVER=Path(__file__).resolve().parents[2]
ROUND=SERVER/'artifacts/integration/packet-connections-20261006/cn-native-battle-command-source-01'
OUT=ROUND/'agents/cn-battle-command-source'
OWN='tools/reconstruction/cn_battle_command_source190.py'
ADDED=['src/cn/world/SharedNativeBattleCommandSource.h','src/cn/world/SharedNativeBattleCommandSource.cpp']
STABLE=ADDED+['src/cn/world/SharedNativeSpectatorSource.h','src/cn/world/SharedNativeSpectatorSource.cpp',
    'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/game/SharedNativeWorldTransports.h','src/game/SharedNativeWorldTransports.cpp',
    'src/cn/net/CnTransportSession.h','src/cn/net/CnTransportSession.cpp','src/cn/protocol/CnTransport.h']
CONTEXT=['src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp',
    'src/cn/protocol/CnBattleCommand35.h','AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def dump(rel,value):
    p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as stream:stream.write((json.dumps(value,indent=2)+'\n').encode())

def retain(rel,path,original=None):
    raw=path.read_bytes();p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as stream:stream.write(raw)
    return {'path':original or path.relative_to(SERVER).as_posix(),'copy':rel,'bytes':len(raw),'sha256':sha(raw)}

def findings(final):
    return {'round':190,'BATCHFINAL_received':final,'owned_cpp_added':2,'source_files_added':ADDED,
        'native_original_inputs':0,'new_bounded_native_spans':0,'new_bounded_native_bytes':0,'new_native_relations':[],
        'retained_bounded_native_spans':0,'retained_bounded_native_bytes':0,
        'new_opcodes':0,'new_phase_bindings':0,'new_complete_routes':0,
        'receiver_contexts':14,'qualified_receiver_contexts':12,
        'unresolved_helpers':[{'va':va,'phase':None,'slot':None,'producer':None} for va in ['0047DE70','004812B0']],
        'whole_game_route_denominator':None,'whole_game_percentage':None,
        'actual_source_connections':[
            {'key':'actual_selected_CN35_binding','scope':'create(actual Connection/full ready Lease/common presence/private transport registry/real WorldOwner/budgets) returns ingress/invalidate/release. Construction before ready performs no lookup; first actual ready request lazily acquires exact original private Token. No optional source means no automatic35 selection by source metadata.'},
            {'key':'entire_independent_native_request','scope':'Reads actual independent CnBattleCommand35 header only, not PE. Uses decode exactlogical17/opcode35 and owned Request copy. Entire raw logical17, actor position/command kind/source/padding/target field/context/operand retained. Unknown kinds unrestricted by source; no client position-to-commonID, padding/operand zero-fill, synthetic nonce or uniform target-mask rule.'},
            {'key':'full_source_scope','scope':'Actual receiver strong before every repository/Current visit. Original Token/current registry incarnation/full Lease/full actual common character/saved position bracket pure real WorldOwner Current before and after. Scope creates no battle clock/context/grant/cache/actor incarnation, UI target or TW state field.'},
            {'key':'real_battle_authority_and_once_execute','scope':'Required pure WorldOwner Current must qualify actual native battle/actor ownership/82 context/86 grant/incarnation/primary-secondary commands/target-formation/learned skill/MP/range/held item slot-count/semantic duplicate/settlement/reply profile. Execute once, same actual Result retained through five checks; source supplies no substitute rights/rules/cost/default success.'},
            {'key':'actual_ordered_native_reply','scope':'Only explicit real nonempty ordered logical records or explicit real no_reply. Full logical vector deep-copy precedes native held queue. Same actual Connection send_world_batch_with_publication performs original framing/encryption and posted game approval. Current at BeforeRelease and AfterRelease; wrapper inline false completion deferred until source Stage ends. No pre-encrypted double framing or guessed ACK.'},
            {'key':'exact_lifetime_and_prefix','scope':'Permanent receiver weak, active pending weak, temporary Pending strong through original completion; wrong-thread check first. Parent active invalidation/reentry/release monotonic terminalizes operation. Locally released true retained before completed early return even late after cancellation, without resetting done/retrying execute/rolling back prefix. Own release resets only own saved token, never common/registry successor. Local volatile queue fact is not durable native-client receipt.'}],
        'gaps':['Real battle/actor/context82/grant86/incarnation/skill/item/target/settlement/reply WorldOwner suppliers remain OPEN.',
            'Native client local permission fields and raw grammar do not establish server authority or complete any battle gameplay route.',
            'Main selection/real battle data suppliers/durable committed-released prefix recovery/native-client acceptance/whole-game route inventory remain OPEN.'],
        'builds_tests_runtime_native_api_codec_db_deploy':False}

def ready():
    if (OUT/'seal.json').exists():raise RuntimeError('Immutable capture')
    manifest=ROUND/'before-manifest.json'
    if sha(manifest.read_bytes())!='97d1f9fb3eb9d6fabb94c88078c014942448a6fbcf690bd759a5b5ca5284aaa3':
        raise ValueError('Exact freshbefore1358 required')
    dump('source-ready-source-origins.json',[retain(f'source-ready/r{n:02d}{Path(rel).suffix}',SERVER/rel) for n,rel in enumerate(ADDED+[OWN])])
    dump('source-ready-context-origins.json',[retain(f'context-source-ready/k{n:02d}{Path(rel).suffix}',SERVER/rel) for n,rel in enumerate(CONTEXT[:3])])
    dump('derived-inputs.json',[retain('derived/freshbefore1358.json',manifest,str(manifest.resolve()))])
    dump('findings-source-ready.json',findings(False))
    print(json.dumps({'state':'source-ready','owned_cpp_added':2,'native_original_inputs':0,'tool_sha256':sha((SERVER/OWN).read_bytes())}))

def final():
    if (OUT/'seal.json').exists():raise RuntimeError('Immutable capture')
    epochs=[]
    for rel in ['before-source-origins.json','intermediate-source-origins.json','source-ready-source-origins.json','source-ready-context-origins.json']:
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
    dump('actual-read-epochs.json',{'before_context':16,'new_owned_absence':3,'initial_implementation':2,
        'source_ready':3,'early_caller_header_context':3,'current_stable':len(current),'final_context':len(context),
        'historical_copies_are_not_current_pins':True,'native_original_inputs':0,'missing_owned_transient_epochs':[],
        'scope':'Only actual observed parent/peer epochs saved; no claim to reconstruct every unobserved transient.'})
    members=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file():
            raw=p.read_bytes();members.append({'path':p.relative_to(OUT).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
    dump('LIST.json',members)
    list_raw=(OUT/'LIST.json').read_bytes();members.append({'path':'LIST.json','bytes':len(list_raw),'sha256':sha(list_raw)})
    dump('seal.json',{'round':190,'scope':'Complete immutable source-only agent artifact','members':members,
        'member_count':len(members),'member_bytes':sum(row['bytes'] for row in members),
        'native_original_input_count':0,'current_source_count':len(current),'final_context_count':len(context)})
    print(json.dumps({'state':'sealed','seal_sha256':sha((OUT/'seal.json').read_bytes()),'members':len(members),
        'total_files_with_seal':len(members)+1,'member_bytes':sum(row['bytes'] for row in members),
        'current':len(current),'context':len(context),'actual_original_inputs':len(current)+len(context),
        'native_original_inputs':0,'tool_sha256':sha((SERVER/OWN).read_bytes())}))

if __name__=='__main__':
    {'ready':ready,'final':final}[sys.argv[1]]()
