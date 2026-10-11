"""Add native75-only projection qualification without changing frozen readers."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(value):
    return hashlib.sha256(value).hexdigest()


def main():
    path = ROOT / 'src/core/Application.cpp'
    old = path.read_bytes()
    assert sha(old) == '70d9070aef764cbcba272b26e764a88865277ff46e6d938c56824ad14423ca7b'
    anchor = b'                                std::vector<std::optional<OwnedGuildDisbandService::ActionPlan>> leases(records.size());'
    addition = b'''                                // CUSTOM-0081 projection preflight is OUTSIDE SQL proofs.
                                // Frozen native2D/92 readers require readable role/resources;
                                // world readiness alone cannot guarantee a name-cache clear.
                                // Check before capture and again after any recursive prefix.
                                // The paired transaction proof remains world-only and works
                                // after governance/member/application rows are removed.
                                const auto projection_ready=[&](const OwnedGuildLeaderPanelService::State& state) {
                                    try {
                                        const auto ready=[&](const SqliteOwnedGuildMembershipRepository::Identity& identity) {
                                            for(const auto& [id,weak]:native_chat_sessions)if(const auto peer=weak.lock()) {
                                                if(peer->character_id!=identity.character_id)continue;
                                                const auto actor=private_chat_peer(id);
                                                if(peer->account_id!=identity.account_id || !actor || !actor->ready ||
                                                   actor->session!=id || actor->account!=identity.account_id ||
                                                   actor->character!=identity.character_id)return false;
                                            }
                                            return true;
                                        };
                                        for(const auto& member:state.leader.roster)if(!ready(member))return false;
                                        for(const auto& application:state.applications)if(!ready(application.applicant))return false;
                                        return true;
                                    }catch(...){return false;}
                                };
'''
    assert old.count(anchor) == 1
    patched = old.replace(anchor, addition + anchor, 1)
    capture = b'                                        leases[index]=guild_disband->prepare_action(session.id(),action->slot);\n'
    qualification = b'                                        if(leases[index] && !projection_ready(leases[index]->panel))leases[index].reset();\n'
    assert patched.count(capture) == 1
    patched = patched.replace(capture, capture + qualification, 1)
    execute = b'                                    const bool committed=guild_disband && leases[index] && guild_disband->execute(*leases[index]);'
    execute_new = b'                                    const bool committed=guild_disband && leases[index] &&\n                                        projection_ready(leases[index]->panel) && guild_disband->execute(*leases[index]);'
    assert patched.count(execute) == 1
    patched = patched.replace(execute, execute_new, 1)
    restored = patched.replace(addition, b'', 1).replace(qualification, b'', 1).replace(execute_new, execute, 1)
    assert restored == old
    out = ROOT / 'artifacts/research/native-guild-management-0081/projection-fix-v01'
    out.mkdir(exist_ok=False)
    (out / 'Application.cpp.before').write_bytes(old)
    path.write_bytes(patched)
    (out / 'source-proof.json').write_text(json.dumps({
        'before_sha256': sha(old), 'after_sha256': sha(patched),
        'exact_restore_of_all_prior_source_bytes': True,
        'frozen_readers_changed': False, 'world_only_SQL_proof_changed': False,
        'projection_preflight_outside_transaction': True,
        'readiness_checked_before_prefix_and_before_execute': True,
        'scope': 'CUSTOM-0081 candidate native75 branch only',
        'TCP_verification_pending': True, 'formal_binary_changed': False,
    }, indent=2) + '\n', encoding='utf-8')
    print(sha(patched))


if __name__ == '__main__':
    main()
