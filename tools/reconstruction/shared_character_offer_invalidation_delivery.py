"""Capture common character-offer invalidation source; no runtime/test/DB work."""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT,CN,PIN

NAME='shared-character-offer-invalidation-01'
ROUND='20261007-shared-character-offer-invalidation'
SOURCES=('src/auth/SharedWorldAdmission.h','src/auth/SharedWorldAdmission.cpp',
    'tools/reconstruction/shared_character_offer_invalidation_delivery.py',
    'docs/research/shared-character-offer-invalidation-20261007.md')
CONTEXT=('src/cn/auth/SharedCharacterDeleteIdentity.h','src/cn/auth/SharedCharacterDeleteIdentity.cpp',
    'src/cn/auth/SharedCreationLocationIdentity.h','src/cn/auth/SharedCreationLocationIdentity.cpp',
    'src/cn/auth/SharedWorldSelection.cpp','src/cn/net/SharedCredentialConnection.cpp',
    'src/db/SqliteRecoveredCharacterRepository.cpp','src/db/Migration.cpp','src/core/Application.cpp')

def main():
    b=ROOT/'artifacts/integration/packet-connections-20261006';out=b/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh before snapshot; preserve historical artifacts')
    image=CN.parent/'XJZ-CN/God2_opt.exe'
    if hashlib.sha256(image.read_bytes()).hexdigest()!=PIN:raise RuntimeError('Pinned native CN changed')
    files=[]
    def save(rel,data,original):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        files.append({'path':rel,'original':str(original),'bytes':len(data),
            'sha256':hashlib.sha256(data).hexdigest()})
    def dump(rel,obj):save(rel,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'),'current static source accounting')
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes(),ROOT/rel)
    for rel in CONTEXT:save('context/'+rel,(ROOT/rel).read_bytes(),ROOT/rel)
    prior=b/'cn-delete-completion-lifecycle-01'
    manifest=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
    pins={r['path']:r['sha256'] for r in manifest['files']}
    retained=('findings.json','native/0047e960.bin','native/0047e960.asm',
              'native/00446bd0.bin','native/00446bd0.asm')
    for rel in retained:
        data=(prior/rel).read_bytes()
        if hashlib.sha256(data).hexdigest()!=pins[rel]:raise RuntimeError('Sealed native lifecycle changed')
        save('retained-native/'+rel,data,prior/rel)
    # Current source dependency boundaries, not executed deletion scenarios.
    dump('storage-and-lifecycle-boundaries.json',{
        'existing_taiwan_delete_source':'Application.cpp existing delete callback ->SqliteRecoveredCharacterRepository::erase_owned',
        'existing_taiwan_delete_changed':False,
        'existing_storage':'recovered_characters/positions/battle/items/etc common FK graph; root-only delete cannot replace graph/rules',
        'native19':'Current offered07 slot/name ->common ID resolver already exists; no19 ingress or actual common delete transaction added',
        'native_completion':'02status0 ->client local cached07 compaction ->0204 ->03 wait ->account0A; old native evidence reused',
        'invalidation_sequence':'prepare allocations ->actual rules/storage ->last current-plan check ->successful SQL COMMIT ->apply on same serial game owner without callbacks/yield',
        'scope':'all TW/CN grants for exact account which offered exact common character ID',
        'invalidated_source':'full offered_source absent; target membership false; stale reserve/commit rejected',
        'preserved':'world_owned ticket, unrelated accounts, unaffected character membership, raw native bytes, other native connections',
        'refresh':'real newly qualified account offer select clears invalidation and advances offer_revision',
        'durable_cross_process_transaction':'not implemented; this is in-process source support only',
        'actual_native_delete_permission_or_issuer':'not recovered by this change'})
    findings={'round':ROUND,'previous_goal_turn_classification':'progress: common created-character location identity and18-row native projection source were saved',
        'common_character_offer_invalidation_sources_added':1,'source_prepare_current_apply_stages':3,
        'protocol_scope':['tw','cn'],'existing_native_lifecycle_snapshots_reused':2,
        'native_fields_or_opcode_values_added':0,'new_phase_opcode_source_bindings':0,
        'source_owner_chains_added':0,'actual_delete_ingress_connected':False,
        'actual_common_delete_transaction_added':False,'real_native_reply_issuer_added':False,
        'new_complete_bidirectional_routes':0,'levels_changed':False,
        'remaining':['Actual native19 operation/rule/offline owner, atomic common save/dependency deletion and durable operation/replay receipt remain open; existing TW deletion is not CN native permission evidence.',
          'Required real02/1E/03 issuers, actual postcommit invalidation integration and generation-safe close/reconnect handler remain open.',
          'Native17 creation/common slot/name/storage, map/spawn/18 issuer and all whole-game indirect/deferred phase/state/variant paths remain incomplete.'],
        'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False,'database_access':False}
    dump('findings.json',findings);dump('source-manifest.json',{'files':files})
    print(json.dumps({k:findings[k] for k in ('round','common_character_offer_invalidation_sources_added',
        'source_prepare_current_apply_stages','existing_native_lifecycle_snapshots_reused','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
