#pragma once
#include "db/SqliteOwnedEquipmentTransaction.h"
#include "game/SharedTaiwanOwnedItemSelectionSource.h"
#include "protocol/RecoveredTaiwanInventoryItemRecord.h"
#include "protocol/RecoveredInventory.h"
#include <memory>
#include <variant>

namespace god2 {
// Pre-COMMIT complete real before/next custody + native material -> explicit
// ordered inventory component -> this exact joint durable receipt. No default
// record order/count/opaque, equip rule, native final-cache proof or full reply.
class SharedTaiwanOwnedInventoryReplySource final:
    public std::enable_shared_from_this<SharedTaiwanOwnedInventoryReplySource> {
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
    // CUSTOM-0092: the explicit existing-entry consumer keeps the complete
    // private three-store receipt. It never substitutes material-only Current.
    // Source/receipt copies share the source's one consumption and invalidation.
    // Borrowed repositories must outlive every Component and copied source.
    class EntryComponent final {
    public:
        const std::vector<std::uint8_t>& wire() const noexcept {return wire_;}
        const SqliteOwnedEquipmentTransaction::EntryCommitted& committed() const noexcept {return committed_;}
        // Synchronous game-owner observation during the same actual C28 Action.
        // The occurrence's retirement invalidates it; this is not queue/ACK
        // qualification or permission to send/retry after the Action returns.
        bool current(Session&) const;
    private:
        friend class SharedTaiwanOwnedInventoryReplySource;
        EntryComponent(std::vector<std::uint8_t> wire,
            std::shared_ptr<SharedTaiwanOwnedInventoryReplySource> source,
            SqliteOwnedEquipmentTransaction::EntryCommitted committed) noexcept
            :wire_(std::move(wire)),source_(std::move(source)),committed_(std::move(committed)) {}
        std::vector<std::uint8_t> wire_;
        std::shared_ptr<SharedTaiwanOwnedInventoryReplySource> source_;
        SqliteOwnedEquipmentTransaction::EntryCommitted committed_;
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
    // Same preallocated inventory projection, qualified against the complete
    // actual three-store COMMIT. Preparation above still observes two before
    // populations; the real three-store issuer owns the complete entry CAS.
    // No encoding, allocation of a new source, reminting or fallback after
    // COMMIT. Pass committed() to the existing entry-aware DA factory to keep
    // the same receipt; the caller still owns full ordered reply/publication.
    std::optional<EntryComponent> take(Session&,const SqliteOwnedEquipmentTransaction::EntryCommitted&);
    void invalidate();
private:
    SharedTaiwanOwnedInventoryReplySource(std::shared_ptr<SqliteOwnedEquipmentTransaction>,
        std::shared_ptr<SharedTaiwanOwnedItemSelectionSource>,
        Session&,const Session::NativeWorldSelectionInput&,const SharedTaiwanOwnedItemSelectionSource::Selection&,
        SqliteOwnedEquipmentTransaction::State,std::vector<std::uint8_t>);
    void owner() const;
    bool local(Session&) const;
    bool entry_current(Session&,const SqliteOwnedEquipmentTransaction::EntryCommitted&);
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
    bool observing_entry_=false;
};
}
