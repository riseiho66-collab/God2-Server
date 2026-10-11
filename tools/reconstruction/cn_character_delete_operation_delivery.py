"""Retain native evidence and snapshot the conditional19/common-CAS source; files only."""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT, CN, PIN

NAME='cn-character-delete-operation-01'
ROUND='20261007-cn-character-delete-operation'
SOURCES=('src/cn/auth/SharedCharacterDeleteOperation.h','src/cn/auth/SharedCharacterDeleteOperation.cpp',
    'src/cn/auth/SharedWorldSelection.h','src/cn/auth/SharedWorldSelection.cpp',
    'src/cn/auth/SharedLoginComposition.h','src/cn/auth/SharedLoginComposition.cpp',
    'docs/research/cn-character-delete-operation-20261007.md',
    'tools/reconstruction/cn_character_delete_operation_delivery.py')
CONTEXT=('src/cn/auth/SharedCharacterDeleteIdentity.h','src/cn/auth/SharedCharacterDeleteIdentity.cpp',
    'src/cn/protocol/CnCharacterDelete.h','src/cn/protocol/CnCharacterDeleteReply.h',
    'src/cn/protocol/CnWorldSelectionStatus.h','src/cn/auth/SharedPreWorldCloseReply.h',
    'src/cn/net/SharedCredentialConnection.h','src/auth/SharedCharacterRemoval.h',
    'src/auth/SharedCharacterRemoval.cpp','src/db/SqliteOwnedCharacterRemoval.cpp',
    'src/db/SqliteRecoveredCharacterRepository.h','src/db/SqliteRecoveredCharacterRepository.cpp',
    'src/auth/SharedWorldAdmission.h','src/auth/SharedWorldAdmission.cpp','src/core/Application.cpp',
    'src/game/RecoveredCharacter.h','CMakeLists.txt')


def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh before snapshot; preserve prior evidence')
    if hashlib.sha256((CN.parent/'XJZ-CN/God2_opt.exe').read_bytes()).hexdigest()!=PIN:
        raise RuntimeError('Pinned CN source changed')
    files=[]
    def save(rel,data,original):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        files.append({'path':rel,'original':str(original),'bytes':len(data),
                      'sha256':hashlib.sha256(data).hexdigest()})
    def dump(rel,value):
        save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'),
             'static source accounting; no SQL/native execution')
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes(),ROOT/rel)
    for rel in CONTEXT:save('context/'+rel,(ROOT/rel).read_bytes(),ROOT/rel)
    preserved=[]
    for rel in ('src/db/SqliteRecoveredCharacterRepository.cpp','src/core/Application.cpp'):
        raw=(ROOT/rel).read_bytes()
        if raw!=(out/'before'/rel).read_bytes():raise RuntimeError('Frozen existing source changed')
        preserved.append({'path':rel,'sha256':hashlib.sha256(raw).hexdigest(),'byte_identical':True})
    reused=[]
    for name,rels in (
        ('cn-delete-completion-lifecycle-01',('findings.json','native-delete-lifecycle.json',
          'native-return-branches.json',*[f'native/{va}.{ext}' for va in ('0047e960','00446bd0','00480b10') for ext in ('c','asm','bin')])),
        ('cn-character-delete-identity-01',('findings.json',)),
        ('shared-character-removal-01',('findings.json','storage-source-chain.json')),
        ('cn-pre-world-close-owner-01',('findings.json',))):
        prior=base/name;manifest=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
        pins={r['path']:r['sha256'] for r in manifest['files']}
        for rel in rels:
            data=(prior/rel).read_bytes()
            if hashlib.sha256(data).hexdigest()!=pins[rel]:raise RuntimeError('Retained evidence changed')
            save('retained-source/'+name+'/'+rel,data,prior/rel)
        reused.append(name)
    dump('operation-source-chain.json',{
        'ingress':'world Selection19 ->exact native07/common-ID identity + credential alias ->wipe raw/parsed credentials',
        'source':'explicit same common SQLite backend + complete02 actual decision before write; no invented rules',
        'scope':'new server-created attempt pointer + verified account/world-session/common-character/native-slot; retained/designated before supplier',
        'success':'SharedCharacterRemoval::commit ->prepared TW/CN invalidation ->BEGIN IMMEDIATE/full snapshot CAS ->actual BeforeErase/BeforeCommit ->COMMIT ->immediate invalidation',
        'queue':'current exact ticket/attempt + absent common ID + actual BeforeQueue/AfterQueue; invalidated07 is not reused',
        'nonzero':'actual full02 with unchanged common row/current native offer, no SQL; release only after whole reply queue completion',
        'terminal':'successful owner remains until actual03 source/drain after0204; busy owner cannot yield terminal',
        'missing':'native permission/rules/reply issuer/durable receipts/hosting/1E continuation; local queue is not native acceptance'})
    findings={'round':ROUND,'native_sha256':PIN,
        'previous_goal_turn_classification':'progress: shared common CAS removal writer and storage/offer coordinator sealed in catalog70; level acknowledgement is a scope confirmation only',
        'new_conditional_source_owner_chains':1,'new_phase_opcode_source_bindings':2,
        'new_distinct_phase_opcode_source_binding_values':1,
        'native_c2s_by_phase':{'world_selection':['19']},'native_s2c_by_phase':{'world_selection':['02']},
        'new_cpp_headers':1,'new_cpp_implementation_files':1,'modified_existing_cpp_files':4,
        'new_native_opcode_values':0,'new_common_storage_writers':0,'prior_common_cas_writer_invoked_in_source':True,
        'native19_conditional_ingress_added':True,'native_deletion_permission_added':False,
        'actual_native_reply_issuer_added':False,'native1e_completed':False,'formal_application_hosted':False,
        'durable_replay_or_recovery_added':False,'schema_or_table_change':False,
        'preserved_existing_sources':preserved,'retained_source_artifacts':reused,
        'new_complete_bidirectional_routes':0,'levels_changed':False,
        'whole_game_route_total':None,'whole_game_completion_percent':None,
        'remaining':['Actual native19 permission/online/guild/operation/CAS/replay owner and full native02/03 issuer must be supplied before configured hosting.',
          'Native1E post-API continuation, all failure/recovery variants and durable crash/replay receipts remain open.',
          'All-save/history/non-FK deletion policy, cross-process offer invalidation and whole-game phase/state/variant/indirect denominator remain open.'],
        'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False}
    dump('findings.json',findings);dump('source-manifest.json',{'files':files})
    print(json.dumps({k:findings[k] for k in ('round','new_conditional_source_owner_chains',
        'new_phase_opcode_source_bindings','prior_common_cas_writer_invoked_in_source','new_complete_bidirectional_routes')}))


if __name__=='__main__':main()
