"""Snapshot TW delete callback -> common CAS; file-only source accounting."""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT

NAME='shared-taiwan-character-removal-01'
ROUND='20261007-shared-taiwan-character-removal'
SOURCES=('src/auth/SharedTaiwanCharacterRemoval.h','src/auth/SharedTaiwanCharacterRemoval.cpp',
    'src/auth/RecoveredAccountLogin.h','docs/research/shared-taiwan-character-removal-20261007.md',
    'tools/reconstruction/shared_taiwan_character_removal_delivery.py')
CONTEXT=('src/auth/RecoveredAccountLogin.cpp','src/db/AccountRepository.h',
    'src/net/Session.h','src/net/Session.cpp','src/core/Application.cpp',
    'src/protocol/RecoveredC2S0002.h','src/protocol/RecoveredCharacterDelete.h',
    'src/game/RecoveredCharacter.h','src/auth/SharedCharacterRemoval.h',
    'src/auth/SharedCharacterRemoval.cpp','src/auth/SharedCharacterRemovalPresence.h',
    'src/auth/SharedCharacterRemovalPresence.cpp','src/auth/SharedWorldAdmission.h',
    'src/db/SqliteOwnedCharacterRemoval.cpp','src/db/SqliteRecoveredCharacterRepository.h',
    'src/db/SqliteRecoveredCharacterRepository.cpp',
    'docs/research/current-character-logout-delete-20260927.md')
PRESERVED=('src/core/Application.cpp','src/net/Session.h','src/net/Session.cpp',
    'src/auth/RecoveredAccountLogin.cpp','src/auth/SharedCharacterRemoval.cpp',
    'src/auth/SharedCharacterRemovalPresence.cpp','src/db/SqliteOwnedCharacterRemoval.cpp',
    'src/db/SqliteRecoveredCharacterRepository.cpp')

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
            'file-only source accounting, not execution/SQL/gameplay testing')
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes(),ROOT/rel)
    for rel in CONTEXT:save('context/'+rel,(ROOT/rel).read_bytes(),ROOT/rel)
    preserved=[]
    for rel in PRESERVED:
        raw=(ROOT/rel).read_bytes()
        if raw!=(out/'before'/rel).read_bytes():raise RuntimeError('Frozen/shared source body changed')
        preserved.append({'path':rel,'byte_identical':True,'sha256':hashlib.sha256(raw).hexdigest()})
    prior=base/'shared-character-removal-presence-01'
    manifest=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
    pins={r['path']:r['sha256'] for r in manifest['files']}
    for rel in ('findings.json','occupancy-source-chain.json','peer-acknowledgement.json'):
        raw=(prior/rel).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=pins[rel]:raise RuntimeError('Prior sealed source changed')
        save('retained-source/shared-character-removal-presence-01/'+rel,raw,prior/rel)
    legacy_receipt=ROOT/'artifacts/playtests/private-logout-delete-20260927-13/run-result.json'
    receipt_present=legacy_receipt.is_file()
    if receipt_present:save('historical-native-ui13/run-result.json',legacy_receipt.read_bytes(),legacy_receipt)
    dump('tw-delete-source-chain.json',{
        'ingress':'Unchanged Session character preselection TW19 parser -> actual delete_character callback',
        'auth':'actual RecoveredAccountLogin + original flag0/C8/account/password bytes; same declared account repository',
        'identity':'actual Authenticated nonselected Session + unambiguous owned slot/exact byte-name/full stored row + fresh Attempt',
        'policy':'required actual prepare(Current), copied scope/row, no credentials/default permission/native CN custom inference',
        'transaction':'SharedCharacterRemoval.commit -> full common row CAS + raw TW/CN and actual legacy occupancy before/after policy at BeforeErase/BeforeCommit -> immediate offer invalidation',
        'return':'committed truth into existing TW bool02 serializer/queue; native tail/replay/recovery/hosting remain open',
        'hosting':'Host must install callback with real complete sources before constructing TW Sessions; no frozen default Application change',
        'receipt_scope':'Legacy UI13 only, not new shared adapter/native acceptance'})
    findings={'round':ROUND,
        'previous_goal_turn_classification':'progress: catalog73 common raw occupancy source and current web ACT clock handoff sealed',
        'new_conditional_tw_source_owner_chains':1,'new_tw_phase_source_bindings':2,
        'new_distinct_tw_phase_source_binding_values':2,'new_read_only_account_source_views':1,
        'new_cpp_headers':1,'new_cpp_implementation_files':1,'modified_existing_cpp_headers':1,
        'existing_common_cas_writer_invoked_in_source':True,'tw_credentials_retained_in_operation_scope':False,
        'native_authentication_behavior_changed':False,'default_application_delete_callback_replaced':False,
        'actual_native_deletion_permission_added':False,'native_full_reply_issuer_added':False,
        'common_raw_presence_and_offer_invalidation_required':True,
        'persistent_semantic_replay_or_recovery_added':False,'preserved_existing_sources':preserved,
        'historical_ui13_receipt_present':receipt_present,'historical_ui13_qualifies_new_adapter':False,
        'new_cn_phase_source_bindings':0,'new_packet_values':0,'new_complete_bidirectional_routes':0,
        'formal_application_hosted':False,'schema_or_table_change':False,'levels_changed':False,
        'remaining':['Actual TW host must install this explicit callback using real common account/character/login/presence/admission and native guild/operation/replay policy; default frozen route is unchanged.',
            'Complete native02/03 tails/issuers and post-COMMIT queue/disconnect/crash/semantic replay recovery remain open; existing bool callback is not a new full reply issuer.',
            'CN native deletion/guild/replay, native1E exceptional continuation, common creation17/18 and all actual native hosting remain open.',
            'Cross-process occupancy/offer invalidation, all-save/history policy and whole-game phase/state/variant/indirect/deferred denominator remain open.'],
        'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False}
    dump('findings.json',findings);dump('source-manifest.json',{'files':files})
    print(json.dumps({k:findings[k] for k in ('round','new_conditional_tw_source_owner_chains',
        'new_tw_phase_source_bindings','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
