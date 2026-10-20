#pragma once
#include "game/Battle.h"
#include "db/SqliteCompanionRepository.h"
#include "game/RevivalRecovery.h"
#include "net/Session.h"
#include "protocol/RecoveredBattlePose.h"
#include <chrono>
#include <unordered_map>
#include <unordered_set>

namespace god2 {
// CUSTOM-0008: explicit per-session native-command authorization bridge.
// Binding is a trusted server operation AFTER battle entry, never a C2S opcode.
// All methods run on the game executor; callbacks must not reenter or send.
class RecoveredBattleService {
public:
    struct DiagnosticRevival {
        Battle::RevivalRule rule;
        Battle::RevivalEncode encode;
        bool opening_notice{}; // CUSTOM-0017: exact observed action02+0B, no combat effect.
    };
    struct Policy {
        // client_actor/client_side match incoming C2S fields. They alone do
        // not prove current native self slot51 (also written by1C and86/5).
        // actor_position is the independently authorized Battle actor index.
        std::uint8_t client_actor, client_side, actor_position;
        std::uint32_t context;
        BattleAction basic;
        // Explicit trusted action policies keyed by both original bytes.
        // Kind1/idN must never fall back to kind0/idN's combat rule.
        std::unordered_map<std::uint16_t,BattleAction> skills;
        bool diagnostic_single_action{}; // CUSTOM-0010: one action plus local control notification.
        std::optional<BattleAction> diagnostic_retaliation;
        bool diagnostic_player_initial_control{}; // CUSTOM-0009: observed zero-mask pre-action notice.
        bool diagnostic_opening_action2{}; // Original client sends exact action02 after entry.
        bool diagnostic_manual_receipts{}; // CUSTOM-0058: existing actor masks only; no attack implied.
        bool diagnostic_timeout_action2{}; // CUSTOM-0035: isolated town no-input turn expiry.
        std::array<std::uint16_t,2> diagnostic_control_targets{1,0};
        // CUSTOM-0012: opt-in reply candidate; no turn/resource mutation on refusal.
        std::function<std::vector<std::uint8_t>(const BattleSnapshot&,const BattleAction&,
                                               const InsufficientBattleMp&)> diagnostic_mp_refusal;
        // CUSTOM-0012: exact second/terminal receipts observed in three-round lab.
        bool diagnostic_three_round_friendly_receipts{};
        // CUSTOM-0012: fresh client restored at revision3 sends enemy mask at revision5.
        bool diagnostic_first_exchange_resume{};
        bool diagnostic_second_encounter_entry{}; // CUSTOM-0014: observed initial mask1/0.
        // CUSTOM-0017: trusted authorization for kind3/id8 only, never client-enabled.
        std::optional<DiagnosticRevival> diagnostic_revival;
        // CUSTOM-0012: fresh revision5 client retains enemy mask at terminal6.
        // Native second-exchange-resume run01 packet0552; not arbitrary reconnect.
        bool diagnostic_second_exchange_resume{};
        // CUSTOM-0012: isolated candidate grant after exact initial native receipt.
        // Validated before receipt publication; never changes battle/resources.
        std::function<std::vector<std::uint8_t>()> diagnostic_initial_control_reply;
        // CUSTOM-0058: server-authorized per-skill caps and presentation. Empty
        // maps preserve existing policies; neither map grants skill ownership.
        std::unordered_map<std::uint16_t,std::uint8_t> skill_target_limits;
        std::unordered_map<std::uint16_t,Battle::Encode> skill_encoders;
        // CUSTOM-0059: native mode5 sends a side-wide 0x3FFF command. Resolve
        // living opponents from the authoritative snapshot, not packet count.
        std::unordered_set<std::uint16_t> skill_all_living_opponents;
        // Trusted server policy only; never selected by client version, C2S
        // bytes or language. Matching numeric profiles do not qualify a wire codec.
        BattleNumericProfile numeric_profile{BattleNumericProfile::LegacyCustom};
        // CUSTOM-0103: trusted actual prepared bootstrap only. No client
        // receipt, native constructor success or ordinary shared PvP implied.
        std::optional<RecoveredBattlePose::Publication> pose_publication;
        // CUSTOM-0139: real saved source for these explicitly authorized rules.
        SqliteCompanionRepository* owned_skill_repository{};
        std::unordered_set<std::uint16_t> saved_owned_skills;
        bool nonpersistent_owned_skills{}; // Explicit existing isolated diagnostic only.
    };
    static constexpr std::uint16_t skill_key(std::uint8_t kind,std::uint8_t id) noexcept {
        return static_cast<std::uint16_t>((std::uint16_t{kind}<<8)|id);
    }
    explicit RecoveredBattleService(Battle::Rule rule);
    // Persist the complete exchange atomically; throwing must leave storage unchanged.
    // Called after all encoding succeeds, before noexcept in-memory publication.
    using Commit = std::function<void(const BattleSnapshot&,const BattleSnapshot&)>;
    using CheckpointCommit = std::function<void(const BattleCheckpoint&,const BattleCheckpoint&)>;
    using OwnedCheckpointCommit = std::function<void(const BattleCheckpoint&,const BattleCheckpoint&,
        const SelectedDeitySkillReadset&)>;
    void bind(Session& session, Battle battle, Policy policy, Battle::Encode encode,Commit commit={},
        CheckpointCommit checkpoint_commit={},OwnedCheckpointCommit owned_checkpoint_commit={},
        std::optional<Session::WorldResponseWrite> owned_bootstrap_write={});
    // CUSTOM-0140: actual hosted bootstrap producer/source qualification.
    // Full saved roster is private repository data; the original callback wire
    // receipt is only local custody, never native list adoption/ACK/turn grant.
    bool qualify_owned_bootstrap(Session&,const Session::WorldResponseWrite&,
        const OwnedDeityRosterReadset&);
    std::optional<std::vector<std::uint8_t>> handle(
        Session& session, std::span<const RecoveredWorldRecords::Record> records);
    const BattleSnapshot& inspect(std::uint64_t session) const;
    bool has_authorized_skill(std::uint64_t session,std::uint16_t key) const {
        const auto found=bindings_.find(session);
        return found!=bindings_.end() && found->second.policy.skills.contains(key);
    }
    // In-process server-result boundary. Never registered in the C2S decoder.
    // Uses the same atomic checkpoint callback as command-driven combat.
    // Optional receiver view must be the actual current Session primary full
    // write. Missing view keeps conservative friendly checks; policy/pose
    // cannot substitute. It supplies no status bits, source or turn authority.
    std::vector<std::uint8_t> apply_native_deltas(Session& session,std::uint64_t revision,
        std::span<const RecoveredBattleDelta::Record> records,const Battle::NativeDeltaEncode& encode,
        std::optional<Session::BattleSelfView> view=std::nullopt);
    // Trusted diagnostic operation only; no C2S field is treated as this revision.
    void rearm_diagnostic(Session& session, std::uint64_t expected_revision);
    bool diagnostic_round_ready(const Session& session) const noexcept;
    bool diagnostic_timeout_round_ready(const Session& session) const noexcept;
    // CUSTOM-0017: trusted in-process recovery envelope, never a C2S record.
    // Durable atomic storage and fresh-client resynchronization remain separate.
    using RevivalRecovery=god2::RevivalRecovery;
    RevivalRecovery checkpoint_revival(const Session& session) const;
    void restore_revival_phase(Session& session,const RevivalRecovery& recovery);
    void expect_revival_reconnect_notice(Session& session);
    using PhaseCommit=std::function<void(const RevivalRecovery&,const RevivalRecovery&)>;
    // Trusted caller must pair this with atomic action checkpoint persistence.
    void set_revival_phase_commit(Session& session,PhaseCommit commit);
    bool release_finished_diagnostic(Session& session);
    void remove(std::uint64_t session) noexcept;
private:
    class BindingOperation;
    struct Bound {
        const Session* session;
        std::uint64_t account, character;
        Battle battle;
        Policy policy;
        Battle::Encode encode;
        Commit commit;
        CheckpointCommit checkpoint_commit;
        bool action_received{}, control_received{};
        bool initial_control_received{};
        bool opening_action2_received{};
        bool timeout_action2_received{};
        bool revival_opening_received{};
        PhaseCommit phase_commit;
        bool revival_phase_restored{};
        enum class ReconnectNotice { None, Pending, Consumed, OpeningConsumed } reconnect_notice{};
        std::uint64_t reconnect_revision{};
        // Cosmetic-only exact binding generation. Never reused as turn/skill
        // authority or persisted into a combat checkpoint.
        std::uint64_t pose_battle_generation{};
        std::weak_ptr<Session> pose_session;
        std::optional<std::chrono::steady_clock::time_point> pose_last_sent;
        std::optional<std::uint8_t> pose_last_symbol;
        OwnedCheckpointCommit owned_checkpoint_commit;
        // Shared callback lifetime fence for every operation, including the
        // original saved-skill path. Remove defers erase until the outer exit.
        bool owned_skill_operating{},owned_skill_reentered{},owned_skill_remove_pending{};
        std::optional<Session::WorldResponseWrite> owned_bootstrap_write;
        // CUSTOM-0140: separate opt-in actual bootstrap identity; not cosmetic.
        std::uint64_t owned_bootstrap_battle_generation{};
        // Captured by every actual bind, independent of cosmetic/owned bootstrap.
        std::uint64_t native_delta_battle_generation{};
    };
    void reject_owned_skill_reentry(std::uint64_t session);
    Battle::Rule rule_;
    std::unordered_map<std::uint64_t,Bound> bindings_;
};
}
