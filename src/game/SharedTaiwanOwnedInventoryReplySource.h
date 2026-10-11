#pragma once
#include "db/SqliteOwnedEquipmentTransaction.h"
#include "game/SharedTaiwanOwnedItemSelectionSource.h"
#include "protocol/RecoveredTaiwanInventoryItemRecord.h"
#include "protocol/RecoveredInventory.h"
#include <variant>

namespace god2 {
// Pre-COMMIT complete real before/next custody + native material -> explicit
// ordered inventory component -> this exact joint durable receipt. No default
// record order/count/opaque, equip rule, native final-cache proof or full reply.
class SharedTaiwanOwnedInventoryReplySource final {
public:
    ~SharedTaiwanOwnedInventoryReplySource();
    SharedTaiwanOwnedInventoryReplySource(const SharedTaiwanOwnedInventoryReplySource&)=delete;
    SharedTaiwanOwnedInventoryReplySource& operator=(const SharedTaiwanOwnedInventoryReplySource&)=delete;
    SharedTaiwanOwnedInventoryReplySource(SharedTaiwanOwnedInventoryReplySource&&)=delete;
    SharedTaiwanOwnedInventoryReplySource& operator=(SharedTaiwanOwnedInventoryReplySource&&)=delete;
    using Operation=std::variant<RecoveredTaiwanInventoryItemRecord::Fields,RecoveredInventory::SlotUpdate>;
    struct Budgets {std::size_t max_records,max_logical_bytes;};
    class Component final {
    public:
        const std::vector<std::uint8_t>& wire() const noexcept {return wire_;}
    private:
        friend class SharedTaiwanOwnedInventoryReplySource;
        explicit Component(std::vector<std::uint8_t> wire) noexcept:wire_(std::move(wire)) {}
        std::vector<std::uint8_t> wire_;
    };
    // Must run before real mutation; actual same reader.current qualifies old
    // Selection before allocating/encoding. It never manufactures an issuer.
    // Retain the result only in that synchronous real Action; all receipt APIs
    // are game-only. The source's bytes are allocated before the future COMMIT.
    static std::shared_ptr<SharedTaiwanOwnedInventoryReplySource> prepare(
        std::shared_ptr<SqliteOwnedEquipmentTransaction>,std::shared_ptr<SharedTaiwanOwnedItemSelectionSource>,
        Session&,const Session::NativeWorldSelectionInput&,const SharedTaiwanOwnedItemSelectionSource::Selection&,
        SqliteOwnedEquipmentTransaction::Before,SqliteOwnedEquipmentTransaction::State,
        std::vector<Operation>,Budgets);
    // One use, exact actual Session/input/current joint receipt; no reply
    // encoding/allocation, supplier, rebuild or retry after COMMIT. Actual
    // current storage/presence observers still run and may allocate or throw.
    // Real Action must compose remaining pending/stat/self/DA and ordered
    // publication separately. Component is deliberately not a complete Reply.
    std::optional<Component> take(Session&,const SqliteOwnedEquipmentTransaction::Committed&);
    void invalidate();
private:
    SharedTaiwanOwnedInventoryReplySource(std::shared_ptr<SqliteOwnedEquipmentTransaction>,
        std::shared_ptr<SharedTaiwanOwnedItemSelectionSource>,
        Session&,const Session::NativeWorldSelectionInput&,const SharedTaiwanOwnedItemSelectionSource::Selection&,
        SqliteOwnedEquipmentTransaction::State,std::vector<std::uint8_t>);
    void owner() const;
    bool local(Session&) const;
    const std::shared_ptr<SqliteOwnedEquipmentTransaction> transaction_;
    const std::shared_ptr<SharedTaiwanOwnedItemSelectionSource> reader_;
    const SharedTaiwanOwnedItemSelectionSource::Selection selection_;
    const std::weak_ptr<Session> connection_;
    const Session::NativeWorldSelectionInput input_;
    const SharedWorldPresence::Lease lease_;
    const std::uint64_t battle_;
    const SqliteOwnedEquipmentTransaction::State after_;
    std::vector<std::uint8_t> wire_;
    const std::thread::id thread_=std::this_thread::get_id();
    bool consumed_=false,invalidated_=false;
};
}
