"""Snapshot actual common/legacy occupancy sources and conditional19 gates; files only."""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT

NAME='shared-character-removal-presence-01'
ROUND='20261007-shared-character-removal-presence'
SOURCES=('src/auth/SharedCharacterRemovalPresence.h','src/auth/SharedCharacterRemovalPresence.cpp',
    'src/auth/SharedCharacterRemoval.h','src/auth/SharedCharacterRemoval.cpp',
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/handlers/RecoveredMovementService.h','src/cn/auth/SharedCharacterDeleteOperation.h',
    'src/cn/auth/SharedCharacterDeleteOperation.cpp','src/cn/auth/SharedLoginComposition.h',
    'src/cn/auth/SharedLoginComposition.cpp','src/cn/world/SharedWorldPreparation.h',
    'docs/research/shared-character-removal-presence-20261007.md',
    'tools/reconstruction/shared_character_removal_presence_delivery.py')
CONTEXT=('src/game/World.h','src/game/World.cpp','src/handlers/RecoveredMovementService.cpp',
    'src/core/Application.cpp','src/auth/SharedCharacterRemoval.h','src/auth/SharedCharacterRemoval.cpp',
    'src/db/SqliteOwnedCharacterRemoval.cpp','src/db/SqliteRecoveredCharacterRepository.cpp',
    'src/cn/world/SharedWorldPreparation.cpp','src/game/SharedTaiwanWorldLifecycle.h',
    'src/game/SharedTaiwanWorldLifecycle.cpp','src/db/SqliteOwnedGuildMembershipRepository.h',
    'src/db/SqliteOwnedGuildSuccessionRepositoryDraft.h','CMakeLists.txt')
PRESERVED=('src/core/Application.cpp','src/handlers/RecoveredMovementService.cpp',
           'src/game/World.cpp','src/db/SqliteRecoveredCharacterRepository.cpp')


def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Fresh before snapshot required; preserve prior evidence')
    files=[]
    def save(rel,data,original):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        files.append({'path':rel,'original':str(original),'bytes':len(data),
                      'sha256':hashlib.sha256(data).hexdigest()})
    def dump(rel,obj):
        save(rel,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'),
             'static source accounting; no gameplay or SQL execution')
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes(),ROOT/rel)
    for rel in CONTEXT:save('context/'+rel,(ROOT/rel).read_bytes(),ROOT/rel)
    preserved=[]
    for rel in PRESERVED:
        raw=(ROOT/rel).read_bytes()
        if raw!=(out/'before'/rel).read_bytes():raise RuntimeError('Existing frozen/source body changed')
        preserved.append({'path':rel,'sha256':hashlib.sha256(raw).hexdigest(),'byte_identical':True})
    for name,rels in (
        ('cn-character-delete-operation-01',('findings.json','operation-source-chain.json')),
        ('shared-character-removal-01',('findings.json','storage-source-chain.json')),
        ('cn-delete-exception-frontier-01',('findings.json','ui-seh-source-chain.json'))):
        prior=base/name;manifest=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
        pins={r['path']:r['sha256'] for r in manifest['files']}
        for rel in rels:
            data=(prior/rel).read_bytes()
            if hashlib.sha256(data).hexdigest()!=pins[rel]:raise RuntimeError('Retained evidence changed')
            save('retained-source/'+name+'/'+rel,data,prior/rel)
    writer_rel='src/db/SqliteOwnedCharacterRemoval.cpp'
    prior_writer=(base/'shared-character-removal-01/source'/writer_rel).read_bytes()
    if (ROOT/writer_rel).read_bytes()!=prior_writer:raise RuntimeError('Prior common SQL writer changed')
    preserved.append({'path':writer_rel,'sha256':hashlib.sha256(prior_writer).hexdigest(),
                      'byte_identical_to_prior_sealed_source':True})
    dump('occupancy-source-chain.json',{
        'common':'SharedWorldPresence.prepare retains raw entry beforeactivate;character_reserved reads every entry without SQL ownership/readiness filtering',
        'legacy_world':'actual World.character_online checks its existing player IDs',
        'legacy_movement':'actual RecoveredMovementService.character_active includes prepared/transfer ownership; explicit disabled configuration is separate from empty active map',
        'binding':'same common repository, actual preparation registry getter and composition pointer comparison; host must bind actual TW/CN and legacy instances',
        'sql':'BeforeErase/BeforeCommit occupancy checked before+after required actual Decision; root staged absent does not hide raw registry',
        'queue':'successful committed02 occupancy checked before+after BeforeQueue/AfterQueue Decision alongside ticket/ID state',
        'nonzero':'does not remove, does not require idle actor and cannot turn absence into permission',
        'missing':'native permission/guild/replay/issuers/hosting, cross-process occupancy and crash receipts; no native invented rules or activation'})
    findings={'round':ROUND,'previous_goal_turn_classification':'progress: catalog72 primary EH/CRT/TLS/code-patch frontier and peer handoff sealed',
        'new_concrete_common_occupancy_observers':1,'existing_conditional19_chains_strengthened':1,
        'new_read_only_registry_binding_views':3,'new_cpp_headers':1,'new_cpp_implementation_files':1,
        'modified_existing_cpp_files':10,'prepared_and_active_raw_common_entries_observed':True,
        'actual_legacy_sources_mandatory':True,'native_authority_still_mandatory':True,
        'common_guild_custom_policy_imported_as_cn_native':False,'preserved_existing_sources':preserved,
        'new_source_owner_chains':0,'new_native_phase_source_bindings':0,'new_packet_values':0,
        'new_complete_bidirectional_routes':0,'actual_native_reply_issuer_added':False,
        'native_deletion_permission_added':False,'durable_replay_or_recovery_added':False,
        'schema_or_table_change':False,'formal_application_hosted':False,'levels_changed':False,
        'remaining':['Actual configured host must use the same common preparation registry for TW/CN and bind actual legacy objects; pointer/source views alone do not prove hosting.',
          'Frozen TW deletion is not automatically routed through this common coordinator; its explicit adapter/hosting connection must exclude CN reservations before global cross-version deletion safety is claimed.',
          'Native19 permission/guild ownership and operation/replay receipt, complete02/03 issuer, native1E exceptional continuation and durable recovery remain open.',
          'Cross-process exclusion/all-save deletion policy and whole-game phase/state/variant/indirect/deferred denominator remain open.'],
        'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False}
    dump('findings.json',findings);dump('source-manifest.json',{'files':files})
    print(json.dumps({k:findings[k] for k in ('round','new_concrete_common_occupancy_observers',
        'existing_conditional19_chains_strengthened','new_source_owner_chains','new_complete_bidirectional_routes')}))


if __name__=='__main__':main()
