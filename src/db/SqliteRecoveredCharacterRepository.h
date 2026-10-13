#pragma once
#include "db/RecoveredCharacterRepository.h"
#include "db/NativeCharacterSummarySnapshotRepository.h"
#include "game/CharacterResources.h"
#include "game/BattleCheckpointCodec.h"
#include "game/RevivalRecovery.h"
#include "protocol/RecoveredQuestSync.h"
#include <utility>
#include <functional>
#include <vector>
struct sqlite3;

namespace god2 {
class SqliteNativeCharacterSummarySnapshotRepository;
class SqliteCompanionRepository;
class SelectedDeitySkillReadset;
// CUSTOM-0139: borrowed actual saved observation, consumed in the same DB txn.
// It grants neither native CN casting nor a skill absent from the saved row.
struct OwnedSkillCheckpointAuthority {
    SqliteCompanionRepository& repository;
    const SelectedDeitySkillReadset& readset;
};
// CUSTOM-0021: completion requires a matching CUSTOM-0022 reward receipt.
struct StoredTownGuideProgress {
    std::uint32_t stage{}, journal_description{};
    std::uint64_t revision{};
    bool operator==(const StoredTownGuideProgress&) const = default;
};
// CUSTOM-0018: display projection only, never quest completion/reward authority.
struct StoredQuestJournal {
    RecoveredQuestSync::JournalValues slots{};
    std::uint64_t revision{};
    std::string source_sha256;
    bool operator==(const StoredQuestJournal&) const = default;
};
struct StoredBattleCheckpoint {
    BattleCheckpoint checkpoint;
    std::uint64_t resource_revision;
    std::string policy_id;
    std::optional<RevivalRecovery> revival;
    bool operator==(const StoredBattleCheckpoint&) const = default;
};
// CUSTOM-0015: explicit isolated occupancy, not evidence that other slots are empty.
struct StoredInventorySlot {
    std::uint16_t item_id;
    std::uint8_t count;
    std::uint64_t revision;
    std::string source_sha256;
    bool operator==(const StoredInventorySlot&) const = default;
};
struct InventoryResourceCommit {
    StoredInventorySlot slot;
    CharacterResources resources;
};
struct InventoryMoveCommit {
    StoredInventorySlot source;
    StoredInventorySlot destination;
};
struct TownGuideRewardCommit {
    StoredTownGuideProgress progress;
    StoredInventorySlot slot;
};
class SqliteRecoveredCharacterRepository final : public RecoveredCharacterRepository {
public:
    void bind_name_encoding(std::uint64_t account,std::uint64_t character,bool simplified);
    explicit SqliteRecoveredCharacterRepository(sqlite3* db) : db_(db) {}
    // Backend identity only; no SQL, state change or character authority.
    bool uses_connection(const sqlite3* connection) const noexcept {return db_==connection;}
    static constexpr const char* town_guide_source_sha256 =
        "1ff497204b5cf77cbbccffdf1836d7aeee30e46980ac1e85d8d0a08a0a4bcda7";
    std::optional<StoredTownGuideProgress> load_town_guide_progress(std::uint64_t account,std::uint64_t character);
    StoredTownGuideProgress commit_town_guide_progress(std::uint64_t account,std::uint64_t character,
        const std::optional<StoredTownGuideProgress>& expected,std::uint32_t next_stage);
    static constexpr const char* town_reward_item_source_sha256 =
        "70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731";
    // CUSTOM-0031: explicit empty slot for isolated town-guide play, never an item grant.
    // Returns true only when the owned slot was inserted.
    bool provision_town_reward_slot(std::uint64_t account,std::uint64_t character);
    // CUSTOM-0037 explicit allocation, never inference that an absent slot is empty.
    // Requires the pre-existing owned town slot0; preserves all existing rows.
    std::size_t provision_owned_bag(std::uint64_t account,std::uint64_t character);
    // CUSTOM-0037 whole-slot transfer/swap, no stack merge or equipment semantics. Both
    // expected snapshots must exist. Each physical slot retains its own revision.
    // CUSTOM-0089 caps this qualified scalar mutation at99 on both snapshots;
    //no clipping/migration of saved rows, slot-count expansion or instance merge.
    InventoryMoveCommit commit_inventory_move(std::uint64_t account,std::uint64_t character,
        std::uint8_t source,std::uint8_t destination,const StoredInventorySlot& expected_source,
        const StoredInventorySlot& expected_destination);
    // CUSTOM-0061: discard only an explicit owner-bound scalar bag snapshot.
    StoredInventorySlot commit_inventory_discard(std::uint64_t account,std::uint64_t character,
        std::uint8_t slot,std::uint8_t quantity,const StoredInventorySlot& expected);
    // CUSTOM-0022: exactly one map, only into an explicitly owned empty slot.
    TownGuideRewardCommit complete_town_guide(std::uint64_t account,std::uint64_t character,
        const StoredTownGuideProgress& expected,std::uint8_t slot,const StoredInventorySlot& expected_slot);
    // Pinned display catalog only; an absent/incomplete import is an error.
    std::array<std::uint16_t,418> load_quest_description_counts();
    static constexpr const char* quest_source_sha256 =
        "659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716";
    std::optional<StoredQuestJournal> load_quest_journal(std::uint64_t account,std::uint64_t character);
    StoredQuestJournal commit_quest_journal(std::uint64_t account,std::uint64_t character,
        const std::optional<StoredQuestJournal>& expected,StoredQuestJournal next,
        std::span<const std::uint16_t> description_counts);
    std::optional<StoredInventorySlot> load_inventory_slot(std::uint64_t account,std::uint64_t character,std::uint8_t slot);
    // CUSTOM-0015/0016: only explicitly saved consumable slots0..29.
    std::vector<std::pair<std::uint8_t,StoredInventorySlot>> load_saved_supply_slots(
        std::uint64_t account,std::uint64_t character);
    InventoryResourceCommit commit_inventory_resources(std::uint64_t account,std::uint64_t character,std::uint8_t slot,
        const std::optional<StoredInventorySlot>& expected_slot,const CharacterResources& expected_resources,
        StoredInventorySlot next_slot,CharacterResources next_resources);
    // Consistent owned lookup, not an exclusive session lease or authorization to replay.
    std::optional<StoredBattleCheckpoint> load_pending_checkpoint(std::uint64_t account,std::uint64_t character);
    // Owner-qualified admission precheck. Atomic mutation methods still
    // recheck reservations within their write transaction.
    bool owned_pending_battle(std::uint64_t account,std::uint64_t character);
    // CUSTOM-0028 admits one completed-quest encounter per owned character.
    bool has_settled_diagnostic_battle(std::uint64_t account,std::uint64_t character);
    BattleSettlement settle_checkpoint(std::uint64_t account,std::uint64_t character,
        const StoredBattleCheckpoint& expected_checkpoint,const CharacterResources& expected_resources,
        const BattleCheckpoint& terminal,CharacterResources resources,bool won,std::uint64_t experience,
        const std::optional<BattleProgressionCommit>& progression={},
        const OwnedSkillCheckpointAuthority* owned_skill=nullptr);
    std::optional<StoredBattleCheckpoint> load_checkpoint(std::uint64_t account,std::uint64_t character,std::uint64_t battle);
    StoredBattleCheckpoint commit_checkpoint(std::uint64_t account,std::uint64_t character,
        const std::optional<StoredBattleCheckpoint>& expected,const CharacterResources& expected_resources,
        BattleCheckpoint next,CharacterResources resources,const std::string& policy_id,
        const std::optional<RevivalRecovery>& revival={},
        const OwnedSkillCheckpointAuthority* owned_skill=nullptr);
    // CUSTOM-0017: receipt/rearm only; resources and battle revision stay unchanged.
    StoredBattleCheckpoint commit_revival_phase(std::uint64_t account,std::uint64_t character,
        const StoredBattleCheckpoint& expected,const CharacterResources& resources,const RevivalRecovery& next);
    std::optional<CharacterRoleSnapshot> load_role(std::uint64_t account,std::uint64_t character) override;
    RoleResourceCommit commit_role_resources(std::uint64_t account,std::uint64_t character,
        const std::optional<CharacterRoleSnapshot>& expected_role,const CharacterResources& expected_resources,
        CharacterRoleSnapshot next_role,CharacterResources next_resources) override;
    std::optional<CharacterExperience> load_experience(std::uint64_t account,
        std::uint64_t character) override;
    BattleSettlement settle_battle(std::uint64_t account,std::uint64_t character,
        std::uint64_t battle,const CharacterResources& expected,CharacterResources next,
        bool won,std::uint64_t experience,const std::optional<BattleProgressionCommit>& progression={}) override;
    std::uint64_t reserve_battle(std::uint64_t account,std::uint64_t character,
        const CharacterResources& expected) override;
    std::optional<CharacterResources> load_resources(std::uint64_t account,std::uint64_t character) override;
    CharacterResources commit_resources(std::uint64_t account,std::uint64_t character,
        const std::optional<CharacterResources>& expected,CharacterResources next) override;
    // CUSTOM-0139: additive typed variants for existing noncheckpoint storage.
    CharacterResources commit_owned_skill_resources(std::uint64_t account,std::uint64_t character,
        const CharacterResources& expected,CharacterResources next,const OwnedSkillCheckpointAuthority&);
    BattleSettlement settle_owned_skill_battle(std::uint64_t account,std::uint64_t character,
        std::uint64_t battle,const CharacterResources& expected,CharacterResources next,bool won,std::uint64_t experience,
        const std::optional<BattleProgressionCommit>&,const OwnedSkillCheckpointAuthority&);
    RecoveredCharacter create(std::uint64_t account_id,
                              const std::array<std::uint8_t, 40>& profile) override;
    struct NewOwnedCharacter {
        // Explicit common storage shape from the actual qualified rule source.
        // Never infer these bytes/slot/codepage/style from a native CN17 record.
        std::uint8_t slot;
        std::array<std::uint8_t,40> profile;
        std::uint16_t name_codepage;
        std::uint8_t streamer_privilege;
    };
    enum class CreationPhase {BeforeInsert,BeforeCommit};
    // Observe actual operation/rules without writes/yield/nested transaction.
    // BeforeCommit sees the staged new row, not the old account row set.
    using CurrentCreation=std::function<bool(CreationPhase)>;
    std::optional<RecoveredCharacter> create_owned_snapshot(std::uint64_t account,
        std::span<const RecoveredCharacter> expected,NewOwnedCharacter,CurrentCreation);
    struct OwnedNameCandidate {
        // Actual qualified common storage bytes/codepage, not incoming CN D3,
        // a display conversion, name join or new character identity.
        std::array<std::uint8_t,16> common_name_bytes;
        std::uint16_t name_codepage;
    };
    enum class NameReplacementPhase {BeforeReplace,BeforeCommit};
    // Actual operation/rule/name-equivalence/visibility/lease/replay owner.
    // Observe only: no writes/yields/event pumping/nested transaction.
    // BeforeCommit observes staged updated name and full account roots.
    using CurrentNameReplacement=std::function<bool(NameReplacementPhase)>;
    // Additive full account-root CAS. Changes only the first16 profile bytes,
    // name_bytes and explicit name codepage; keeps ID/slot/creation time/style,
    // remaining24 profile bytes (including levels) and all saved descendants.
    // Not installed as a native D3 handler; replies/offer refresh/recovery open.
    std::optional<RecoveredCharacter> replace_owned_name_snapshot(std::uint64_t account,
        std::vector<RecoveredCharacter> expected,std::uint64_t character,
        OwnedNameCandidate,CurrentNameReplacement);
    struct InitialOwnedPosition {
        // Actual qualified common spawn source; no default coordinate or
        // conversion from the native creation-choice packed word.
        std::uint16_t area,scene,x,y;
    };
    enum class CreationPositionPhase {BeforeInsert,BeforeCommit};
    using CurrentCreationPosition=std::function<bool(CreationPositionPhase)>;
    // Initial position only: requires exact current root and position absent.
    // Repeated/stale choice never updates an existing position or movement save.
    std::optional<RecoveredPosition> insert_owned_creation_position(
        const RecoveredCharacter&,InitialOwnedPosition,CurrentCreationPosition);
    std::vector<RecoveredCharacter> list_for_account(std::uint64_t account_id) override;
    // Caller checks active sessions on the serial game executor. This transaction
    // rechecks owner and name and removes only this character's saved descendants.
    bool erase_owned(std::uint64_t account,std::uint64_t character,
                     std::span<const std::uint8_t> expected_name);
    enum class RemovalPhase {BeforeErase,BeforeCommit};
    // Additive common-storage CAS; no incoming native name/slot/credential and
    // no native deletion permission. Required caller predicate checks the real
    // operation/rules/online leases and prepared offer invalidation. It observes
    // only: no writes, callbacks that yield, event pumping or nested transactions.
    // BeforeCommit runs after staged deletion, so it must not demand that the
    // deleted row still exists. False/throw rolls back all staged saved rows.
    using CurrentRemoval=std::function<bool(RemovalPhase)>;
    bool erase_owned_snapshot(RecoveredCharacter,CurrentRemoval);
    // Explicit source for an actual issuer authorizing account-wide delivery
    // snapshot invalidation. Complete expected scope tuples, not only rows
    // containing this character. No synthetic refreshed07 or native reply.
    // Legacy erase/handlers do not select this overload automatically.
    using CurrentNativeSummaryRemoval=std::function<bool(RemovalPhase,
        std::span<const NativeCharacterSummarySnapshot> complete_expected_summaries,
        std::span<const RecoveredCharacter> complete_original_roots)>;
    bool erase_owned_snapshot_with_native_summaries(RecoveredCharacter,
        SqliteNativeCharacterSummarySnapshotRepository&,
        std::vector<NativeCharacterSummarySnapshot> complete_expected_summaries,
        CurrentNativeSummaryRemoval);
    std::optional<RecoveredPosition> load_position(std::uint64_t account_id,
                                                  std::uint64_t character_id) override;
    RecoveredPosition commit_position(std::uint64_t account_id, std::uint64_t character_id,
                                      const std::optional<RecoveredPosition>& expected,
                                      std::uint16_t area, std::uint16_t scene,
                                      std::uint16_t x, std::uint16_t y) override;
private:
    bool erase_owned_snapshot_impl(RecoveredCharacter,CurrentRemoval,
        SqliteNativeCharacterSummarySnapshotRepository*,
        std::vector<NativeCharacterSummarySnapshot>,CurrentNativeSummaryRemoval);
    BattleSettlement settle_battle_impl(std::uint64_t account,std::uint64_t character,std::uint64_t battle,
        const CharacterResources& expected,CharacterResources next,bool won,std::uint64_t experience,
        const std::optional<BattleProgressionCommit>& progression,
        const StoredBattleCheckpoint* checkpoint=nullptr,const BattleCheckpoint* terminal=nullptr,
        const OwnedSkillCheckpointAuthority* owned_skill=nullptr);
    void require_owned_skill_current(std::uint64_t account,std::uint64_t character,
        const OwnedSkillCheckpointAuthority*);
    RoleResourceCommit commit_role_resources_in_transaction(std::uint64_t account,std::uint64_t character,
        const std::optional<CharacterRoleSnapshot>& expected_role,const CharacterResources& expected_resources,
        CharacterRoleSnapshot next_role,CharacterResources next_resources);
    CharacterResources commit_resources_in_transaction(std::uint64_t account,std::uint64_t character,
        const std::optional<CharacterResources>& expected,CharacterResources next);
    sqlite3* db_;
};
}
