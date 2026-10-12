#pragma once
#include "db/SqliteOwnedEquipmentTransaction.h"
#include "game/SharedTaiwanWorldRecordSource.h"

namespace god2 {
class RecoveredMovementService;
// CUSTOM-0093: concrete whole-instance bag move/swap, never a grant or merge.
// Native41 can represent this subset only when both retained18B tails agree.
// Construction is game-affine; borrowed repositories outlive Application drain.
class SharedTaiwanOwnedBagMoveSource final {
public:
    static SharedTaiwanWorldRecordSource::InventoryMoveBinding create(
        std::shared_ptr<SqliteOwnedEquipmentTransaction>,AccountRepository&,
        RecoveredCharacterRepository&,std::shared_ptr<SharedWorldPresence>);
    // Separate CUSTOM-0094 opt-in; requires each changed item's genuine full25
    // material. Retention policy is not native opaque/helper qualification.
    static SharedTaiwanWorldRecordSource::InventoryMoveBinding create_with_item_material(
        std::shared_ptr<SqliteOwnedEquipmentTransaction>,AccountRepository&,
        RecoveredCharacterRepository&,std::shared_ptr<SharedWorldPresence>);
    // CUSTOM-0094 full25 only: actual legacy world-records callback and
    // private normal-entry receipt, never a fabricated common ready lease.
    // Requires both genuine complete saved banks at the exact live durable
    // pose. No initialization, grant, stale-witness rebase or scalar promotion.
    // Actual movement/common sources must outlive this game-owned binding.
    static SharedTaiwanWorldRecordSource::InventoryMoveBinding create_for_normal_entry_with_item_material(
        std::shared_ptr<SqliteOwnedEquipmentTransaction>,AccountRepository&,
        RecoveredCharacterRepository&,RecoveredMovementService&);
    // Passive transport of this actual normal-entry C24 mutation receipt and
    // its ORIGINAL already-framed response. No acquisition, initial replay,
    // native timing/final-cache authority or caller-minted source is implied.
    class MutationResult final {
    public:
        MutationResult(const MutationResult&)=delete;
        MutationResult& operator=(const MutationResult&)=delete;
        MutationResult(MutationResult&&) noexcept=default;
        MutationResult& operator=(MutationResult&&) noexcept=default;
        const SqliteOwnedEquipmentTransaction::Committed& committed() const noexcept{return committed_;}
        const std::vector<std::uint8_t>& wire() const noexcept{return wire_;}
        bool native_no_reply() const noexcept{return no_reply_;}
        std::vector<std::uint8_t> take_wire() && noexcept{return std::move(wire_);}
    private:
        friend class SharedTaiwanOwnedBagMoveSource;
        MutationResult(bool no_reply,std::vector<std::uint8_t> wire,
            SqliteOwnedEquipmentTransaction::Committed committed) noexcept
            :no_reply_(no_reply),wire_(std::move(wire)),committed_(std::move(committed)) {}
        bool no_reply_;
        std::vector<std::uint8_t> wire_;
        SqliteOwnedEquipmentTransaction::Committed committed_;
    };
    struct MutationBinding {
        std::function<std::optional<MutationResult>(Session&,const RecoveredInventoryMoveRequest::Request&)> dispatch;
        std::function<void(Session&)> release;
        std::function<void()> invalidate_active;
    };
    // Same concrete CUSTOM-0094 operation/owner; only the return carrier differs.
    // Output storage is allocated before its one joint COMMIT. Receipt/wire
    // move afterwards; no re-observation, decoding, repacking or mint callback.
    static MutationBinding create_for_normal_entry_with_item_material_and_receipt(
        std::shared_ptr<SqliteOwnedEquipmentTransaction>,AccountRepository&,
        RecoveredCharacterRepository&,RecoveredMovementService&);
};
}
