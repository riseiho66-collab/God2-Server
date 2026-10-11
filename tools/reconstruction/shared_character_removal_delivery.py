"""Snapshot additive common SQL/CAS and admission coordination; files only."""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT, CN, PIN

NAME='shared-character-removal-01'
ROUND='20261007-shared-character-removal'
SOURCES=('src/db/SqliteRecoveredCharacterRepository.h','src/db/SqliteOwnedCharacterRemoval.cpp',
    'src/auth/SharedCharacterRemoval.h','src/auth/SharedCharacterRemoval.cpp',
    'docs/research/shared-character-removal-20261007.md',
    'tools/reconstruction/shared_character_removal_delivery.py')
CONTEXT=('src/db/SqliteRecoveredCharacterRepository.cpp','src/db/SqliteSupport.h',
    'src/game/RecoveredCharacter.h','src/auth/SharedWorldAdmission.h','src/auth/SharedWorldAdmission.cpp',
    'src/cn/auth/SharedCharacterDeleteIdentity.h','src/cn/auth/SharedCharacterDeleteIdentity.cpp',
    'src/cn/auth/SharedWorldSelection.h','src/cn/auth/SharedWorldSelection.cpp',
    'src/cn/protocol/CnCharacterDelete.h','src/cn/protocol/CnCharacterDeleteReply.h',
    'src/core/Application.cpp','CMakeLists.txt')


def main():
    b=ROOT/'artifacts/integration/packet-connections-20261006';out=b/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh before snapshot; preserve prior artifacts')
    if hashlib.sha256((CN.parent/'XJZ-CN/God2_opt.exe').read_bytes()).hexdigest()!=PIN:
        raise RuntimeError('Pinned CN input changed')
    files=[]
    def save(rel,data,original):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        files.append({'path':rel,'original':str(original),'bytes':len(data),
                      'sha256':hashlib.sha256(data).hexdigest()})
    def dump(rel,value):
        save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'),
             'static source accounting; not SQL/native execution')
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes(),ROOT/rel)
    for rel in CONTEXT:save('context/'+rel,(ROOT/rel).read_bytes(),ROOT/rel)
    preserved=[]
    for rel in ('src/db/SqliteRecoveredCharacterRepository.cpp','src/core/Application.cpp'):
        before=(out/'before'/rel).read_bytes();current=(ROOT/rel).read_bytes()
        if before!=current:raise RuntimeError('Frozen existing erase/auth source changed')
        preserved.append({'path':rel,'sha256':hashlib.sha256(current).hexdigest(),'byte_identical':True})
    reused=[]
    for name,rels in (
        ('shared-character-offer-invalidation-01',('findings.json',)),
        ('cn-character-delete-identity-01',('findings.json',)),
        ('cn-delete-completion-lifecycle-01',('findings.json',)),
        ('cn-character-create-operation-01',('findings.json',))):
        prior=b/name;manifest=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
        pins={row['path']:row['sha256'] for row in manifest['files']}
        for rel in rels:
            data=(prior/rel).read_bytes()
            if hashlib.sha256(data).hexdigest()!=pins[rel]:raise RuntimeError('Retained evidence changed')
            save('retained-source/'+name+'/'+rel,data,prior/rel)
        reused.append(name)
    dump('storage-source-chain.json',{'input':'copied actual common RecoveredCharacter; not native name/slot/credentials',
        'prepare':'SharedWorldAdmission prepare_character_offer_invalidation allocates before storage write',
        'sql':'foreign_keys required ->BEGIN IMMEDIATE ->full row compare ->BeforeErase actual authority/plan ->staged leaves/FK descendants ->full root CAS ->BeforeCommit authority/plan ->COMMIT',
        'gate':'plan current both before and after actual observing operation predicate; no default predicate',
        'post_commit':'immediate same-game allocation/callback/yield-free invalidation application; no stale-offer qualification',
        'cleanup':'old root-FK scope retained; unsupported references cause constraint rollback, not guessed ownership',
        'invariant_failure':'explicit throw after committed storage if prepared apply fails; not false rollback or native success',
        'limits':'No native19 handler/rule/reply/hosting or durable operation/replay source; no production SQL executed'})
    findings={'round':ROUND,'previous_goal_turn_classification':'progress: ordinary17/18 conditional C++ operation and catalog69 sealed',
        'new_common_storage_cas_writers':1,'new_storage_offer_coordination_sources':1,
        'new_cpp_headers':1,'new_cpp_implementation_files':2,'modified_cpp_headers':1,
        'preserved_existing_sources':preserved,'retained_source_artifacts':reused,
        'new_native_opcode_values':0,'new_phase_opcode_source_bindings':0,'new_native_source_owner_chains':0,
        'new_complete_bidirectional_routes':0,'native_deletion_permission_added':False,
        'native19_ingress_added':False,'native_reply_issuer_added':False,'formal_application_hosted':False,
        'durable_replay_or_recovery_added':False,'schema_or_table_change':False,
        'remaining':['Actual CN19 rule/online/guild ownership and durable operation/CAS/replay owner must invoke the shared writer using the qualified common identity and actual stored snapshot.',
          'Complete native02/1E/03 results, source19 ingress/queue/lifecycle and configured Application hosting remain open.',
          'Non-FK/history/save-policy coverage, cross-process invalidation and indirect/deferred/aggregate whole-game denominator remain open.'],
        'levels_changed':False,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False}
    dump('findings.json',findings);dump('source-manifest.json',{'files':files})
    print(json.dumps({key:findings[key] for key in ('round','new_common_storage_cas_writers',
        'new_storage_offer_coordination_sources','new_native_source_owner_chains','new_complete_bidirectional_routes')}))


if __name__=='__main__':main()
