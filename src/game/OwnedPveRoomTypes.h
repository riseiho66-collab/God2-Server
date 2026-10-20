#pragma once
#include "game/Battle.h"
#include "db/RecoveredCharacterRepository.h"
#include "db/SqliteRoleAuxiliaryRepository.h"
#include "db/SqliteCompanionRepository.h"
#include "db/NativeWorldEntrySnapshotRepository.h"
#include <functional>
#include <map>
#include <optional>
#include <vector>
namespace god2 {
// CUSTOM-0161: independent shared PvE/SOS ownership. No native admission,
// encounter, rewards, timing or formula is inferred from these server types.
struct OwnedPveRoomTypes {
    struct Identity {
        std::uint64_t session{},account{},character{},world_generation{},battle_generation{};
        std::uint8_t channel{};
        std::uint16_t actor_handle{};
        bool operator==(const Identity&)const=default;
    };
    struct PetInput {std::uint8_t actor_slot{};StoredPet2Slot saved;};
    struct MemberInput {
        Identity identity;
        RecoveredCharacter root;
        CharacterRoleSnapshot role;
        RoleAuxiliarySnapshot auxiliary;
        CharacterResources resources{};
        RecoveredPosition return_position;
        std::uint8_t primary_slot{};
        std::optional<PetInput> pet;
        std::uint32_t command_context{}; // Original actual entry context, never a room ID.
        std::optional<NativeWorldEntrySnapshot> row_preference;
        std::optional<StoredPet2Slot> empty_active_pet;
        std::optional<std::uint8_t> reserved_partner; // Explicit immutable CUSTOM-0162 pair; never +7.
    };
    enum class MemberStatus {Entering,Active,Withdrawn,Returned,Retired};
    enum class OutputKind {Entry,Roster,Action,Grant,Terminal,Return};
    enum class OutputStatus {Pending,Written,Failed};
    struct Assignment {
        std::uint8_t primary{};
        std::optional<std::uint8_t> pet;
        std::uint64_t revision{1};
        bool operator==(const Assignment&)const=default;
    };
    struct Member {
        MemberInput input;
        MemberStatus status{MemberStatus::Entering};
        std::uint64_t grant_epoch{1};
        bool primary_grant{},secondary_grant{},disconnected{};
        std::optional<std::array<std::uint8_t,4>> return_context;
        std::uint64_t return_sequence{};
        std::optional<Assignment> assignment;
        std::optional<MemberInput> admission_source;
        Assignment positions()const noexcept{return assignment?*assignment:Assignment{
            input.primary_slot,input.pet?std::optional{input.pet->actor_slot}:std::nullopt,1};}
        std::uint8_t primary_position()const noexcept{return positions().primary;}
        std::optional<std::uint8_t> pet_position()const noexcept{return positions().pet;}
        std::optional<std::uint8_t> partner_position()const noexcept {
            const auto other=input.reserved_partner?input.reserved_partner:
                input.pet?std::optional{input.pet->actor_slot}:std::nullopt;
            if(!other)return {};
            return primary_position()==input.primary_slot?other:std::optional{input.primary_slot};
        }
    };
    struct Output {
        std::uint64_t character{};
        OutputKind kind{};
        std::vector<std::uint8_t> logical;
    };
    struct Delivery {
        std::uint64_t sequence{};
        Identity recipient;
        OutputKind kind{};
        std::vector<std::uint8_t> logical;
        OutputStatus status{OutputStatus::Pending};
    };
    struct Snapshot {
        std::uint64_t id{},revision{},grant_epoch{1},next_sequence{1};
        std::string incarnation,source_sha256,source_record;
        BattleCheckpoint checkpoint;
        std::map<std::uint64_t,Member> members; // Full common character IDs.
        std::vector<Delivery> outbox;
        bool support_enabled{},closed{};
        struct PendingSwap {Identity identity;Assignment before;std::uint8_t actor_position{};
            bool operator==(const PendingSwap&)const=default;};
        std::optional<PendingSwap> pending_swap;
        std::uint64_t animation_sequence{}; // CUSTOM monotonically assigned native group labels0..254.
    };
    struct Encounter {
        std::vector<MemberInput> members;
        std::vector<BattleActor> enemies; // Explicit trusted encounter material, controller0 only.
        std::uint32_t seed{}; // Required issuer input; never an implicit deterministic seed.
        BattleNumericProfile numeric_profile{BattleNumericProfile::LegacyCustom};
        std::string source_sha256,source_record;
        bool support_enabled{};
    };
    struct Change {
        enum class Kind {Entry,Admission,Action,Grant,Support,Withdrawal,Terminal,RowSwap,RowSwapComplete,Pass};
        Kind kind{};
        std::uint64_t character{};
        std::optional<BattleActionResult> result;
        std::optional<std::uint8_t> actor_position;
        bool cycle_progress_observed=false; // Server-owned CUSTOM gate, never a client ACK claim.
        std::optional<Assignment> formation_before;
        std::optional<std::uint8_t> animation_group;
        std::vector<std::uint64_t> suppress_grants; // Host-owned queued commands; wire UI only, not canonical permission.
    };
    // Called outside SQL, on owned immutable after-state; prepares bytes only.
    using Project=std::function<std::vector<Output>(const Snapshot&,const Change&)>;
    // This MUST be the actual host's retained Session/entry/room pure witness.
    // No SQL/provider/callback dispatch inside the final transaction fence.
    using PureCurrent=std::function<bool()>;
};
}
