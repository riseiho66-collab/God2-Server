"""Seal conditional ordinary17/18 ingress and actual-source boundaries, file-only."""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT, CN, PIN

NAME='cn-character-create-operation-01'
ROUND='20261007-cn-character-create-operation'
SOURCES=('src/cn/auth/SharedCharacterCreateOperation.h',
    'src/cn/auth/SharedCharacterCreateOperation.cpp',
    'src/cn/auth/SharedWorldSelection.h','src/cn/auth/SharedWorldSelection.cpp',
    'src/cn/auth/SharedLoginComposition.h','src/cn/auth/SharedLoginComposition.cpp',
    'tools/reconstruction/cn_character_create_operation_delivery.py',
    'docs/research/cn-character-create-operation-20261007.md')
CONTEXT=('src/cn/auth/SharedCreationLocationIdentity.h','src/cn/auth/SharedCreationLocationIdentity.cpp',
    'src/cn/protocol/CnCharacterCreate.h','src/cn/protocol/CnCharacterCreateStatus.h',
    'src/cn/protocol/CnCharacterLocationChoice.h','src/cn/protocol/CnCreationLocationProjection.h',
    'src/cn/auth/SharedPreWorldCloseReply.h','src/cn/net/SharedCredentialConnection.h',
    'src/cn/net/SharedCredentialConnection.cpp','src/cn/net/CnTransportSession.h',
    'src/cn/net/CnTransportSession.cpp','src/db/RecoveredCharacterRepository.h',
    'src/game/RecoveredCharacter.h','src/auth/SharedWorldAdmission.h',
    'src/auth/SharedWorldAdmission.cpp','CMakeLists.txt')


def main():
    b=ROOT/'artifacts/integration/packet-connections-20261006';out=b/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh before snapshot; preserve prior deliveries')
    native=CN.parent/'XJZ-CN/God2_opt.exe'
    if hashlib.sha256(native.read_bytes()).hexdigest()!=PIN:
        raise RuntimeError('Pinned CN input changed')
    files=[]

    def save(rel,data,original):
        path=out/rel;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(data)
        files.append({'path':rel,'original':str(original),'bytes':len(data),
                      'sha256':hashlib.sha256(data).hexdigest()})

    def dump(rel,value):
        save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'),
             'static source interpretation; not execution or acceptance')

    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes(),ROOT/rel)
    for rel in CONTEXT:save('context/'+rel,(ROOT/rel).read_bytes(),ROOT/rel)
    reused=[]
    for name,rels in (
        ('cn-character-mutation-contract-01',('findings.json','native/0043d280.bin',
            'native/0043d280.asm','native/0047e900.bin','native/0047e900.asm')),
        ('cn-create-status-resource-01',('findings.json','native/0047dcc0.bin','native/0047dcc0.asm')),
        ('cn-owned-creation-location-01',('findings.json','native/0047db70.bin','native/0047db70.asm',
            'ordinary-location-reply-consumer.json','native-creation-location-references.json')),
        ('cn-create-name-input-01',('findings.json','name-input-source-contract.json')),
        ('cn-pre-world-close-owner-01',('findings.json','source-chain.json'))):
        prior=b/name;manifest=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
        pins={row['path']:row['sha256'] for row in manifest['files']}
        for rel in rels:
            data=(prior/rel).read_bytes()
            if hashlib.sha256(data).hexdigest()!=pins[rel]:
                raise RuntimeError('Retained sealed evidence changed')
            save('retained-native/'+name+'/'+rel,data,prior/rel)
        reused.append(name)
    dump('source-chain.json',{
        'composition':'SharedLoginSources::World::creation ->compose_native_login ->SharedWorldSelection::attach',
        'start':'after actual1F queue/exact current07 offer ->ordinary17 read ->designated operation ->actual create source',
        'scope':'verified common account/lifetime-unique world session/exact retained17 pointer; serial-game exclusive phases',
        'create_success':'required complete23-byte02 status0 +actual committed new common row +actual permitted choices +current rule/operation predicate',
        'existing_identity':'pre-writer actual account row IDs retained; created ID cannot be an existing role or a client slot/name',
        'create_queue':'complete native02 ->same connection native send_batch ->scope/predicate/exact committed row recheck ->AwaitingChoice',
        'create_failure':'actual full nonzero02;31 alone selects retry branch from retained native caller, other nonzero waits for terminal owner',
        'choice':'ordinary18 +same retained17/current committed created ID/actual choices ->SharedCreationLocationIdentity ->actual choice CAS writer',
        'choice_queue':'full3-byte18 with opaque second byte retained ->current committed result +actual native slot association ->queue owner recheck ->Completed',
        'post_choice_row':'actual writer may change common row; queue checks committed result predicate/current account ownership, not stale pre-choice profile',
        'terminal':'quiescent create owner only ->existing exact-scope02controls/full03/queue/drain/same-ticket cleanup; actual terminal source required',
        'limits':'no SQL writer/rule/default/02/18/03 issuer/hosting added; no rollback of committed saved characters on queue/disconnect failure'})
    findings={'round':ROUND,'previous_goal_turn_classification':'progress: new primary name-input/resource owner evidence and catalog68 sealed',
        'new_cpp_headers':1,'new_cpp_implementation_files':1,'modified_cpp_files':4,
        'new_conditional_source_owner_chains':2,'new_phase_opcode_source_bindings':4,
        'new_distinct_phase_opcode_source_binding_values':3,'new_native_opcode_values':0,
        'native_c2s_by_phase':{'world_selection':['17','18']},
        'native_s2c_by_phase':{'world_selection':['02','18']},
        'qualified_source_branches':['ordinary17 ->complete native02','owned ordinary18 ->complete native18'],
        'retained_evidence_reused':reused,'actual_create_transaction_added':False,
        'actual_choice_transaction_added':False,'actual_native02_or18_issuer_added':False,
        'client_name_filter_promoted_to_rule':False,'formal_application_hosted':False,
        'persistent_semantic_replay_added':False,'new_complete_bidirectional_routes':0,
        'remaining':['Actual native create rules/name uniqueness/collation/slot entitlement/defaults and atomic shared create transaction must provide truthful Created output and02 bytes.',
          'Actual choice availability/routing/destination transaction/CAS/replay must provide complete18 and native-slot/common-ID mapping; UI packed references are not common map/spawn rules.',
          'Native19 transaction/02/1E, full03 supplier, configured hosting, indirect/deferred/aggregate variants and whole-game denominator remain open.'],
        'levels_changed':False,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False}
    dump('findings.json',findings);dump('source-manifest.json',{'files':files})
    print(json.dumps({key:findings[key] for key in ('round','new_cpp_headers','new_cpp_implementation_files',
        'modified_cpp_files','new_conditional_source_owner_chains','new_phase_opcode_source_bindings',
        'new_complete_bidirectional_routes')}))


if __name__=='__main__':main()
