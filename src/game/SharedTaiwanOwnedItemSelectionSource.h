#pragma once
#include "db/SqliteOwnedInventoryRepository.h"
#include "game/SharedWorldPresence.h"
#include "net/Session.h"
#include "protocol/RecoveredSelectionItemRequest.h"
#include <memory>
#include <thread>

namespace god2 {
// Read-only native C28(flag1) -> actual common owned whole-item selection.
// No destination, equip boolean, grant, stat, reply or item->DA is inferred.
// A typed caller supplies Request; this reader does not attest wire receipt,
// request freshness or action permission. Actual C28 dispatch remains required.
class SharedTaiwanOwnedItemSelectionSource final:
    public std::enable_shared_from_this<SharedTaiwanOwnedItemSelectionSource> {
public:
    static constexpr const char* client_pin="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    static constexpr const char* alias_profile="tw149c-item20";
    class Selection {
    public:
        const OwnedInventorySnapshot& snapshot() const noexcept{return committed_.snapshot();}
        const OwnedInventoryCell& cell() const noexcept{return snapshot().cells[cell_index_];}
        const OwnedInventoryInstance& instance() const noexcept{return *cell().instance;}
        const OwnedItemNativeAlias& alias() const noexcept{return instance().aliases[alias_index_];}
        const SharedWorldPresence::Lease& lease() const noexcept{return lease_;}
        const RecoveredPosition& saved_position() const noexcept{return position_;}
        std::uint64_t battle_generation() const noexcept{return battle_generation_;}
        const RecoveredSelectionItemRequest::Request& request() const noexcept{return request_;}
        // Optional explicit historical full-catalog observation for the actual
        // alias key. instance.definition_key remains an opaque common ID.
        const std::optional<NativeItemDefinitionObservation>& definition() const noexcept{return definition_;}
        const std::optional<NativeDeityEquipmentObservation>& deity_equipment() const noexcept{return deity_equipment_;}
    private:
        friend class SharedTaiwanOwnedItemSelectionSource;
        Selection(SqliteOwnedInventoryRepository::Committed committed,std::size_t cell,std::size_t alias,
            std::weak_ptr<Session> session,SharedWorldPresence::Lease lease,RecoveredPosition position,
            std::uint64_t battle,RecoveredSelectionItemRequest::Request request,
            std::optional<NativeItemDefinitionObservation> definition,
            std::optional<NativeDeityEquipmentObservation> deity_equipment)
            :committed_(std::move(committed)),cell_index_(cell),alias_index_(alias),session_(std::move(session)),
             lease_(lease),position_(position),battle_generation_(battle),request_(request),definition_(std::move(definition)),
             deity_equipment_(std::move(deity_equipment)) {}
        SqliteOwnedInventoryRepository::Committed committed_;
        std::size_t cell_index_,alias_index_;
        std::weak_ptr<Session> session_;
        SharedWorldPresence::Lease lease_;
        RecoveredPosition position_;
        std::uint64_t battle_generation_;
        RecoveredSelectionItemRequest::Request request_;
        std::optional<NativeItemDefinitionObservation> definition_;
        std::optional<NativeDeityEquipmentObservation> deity_equipment_;
    };
    static std::shared_ptr<SharedTaiwanOwnedItemSelectionSource> create(
        SqliteOwnedInventoryRepository&,AccountRepository&,RecoveredCharacterRepository&,
        std::shared_ptr<SharedWorldPresence>);
    static std::shared_ptr<SharedTaiwanOwnedItemSelectionSource> create_with_definitions(
        SqliteOwnedInventoryRepository&,AccountRepository&,RecoveredCharacterRepository&,
        std::shared_ptr<SharedWorldPresence>);
    // Explicit required full definition AND owner-local deity witness mode.
    // Does not enable equipment rights or infer a selected deity from D1/D2.
    static std::shared_ptr<SharedTaiwanOwnedItemSelectionSource> create_with_deity_equipment(
        SqliteOwnedInventoryRepository&,AccountRepository&,RecoveredCharacterRepository&,
        std::shared_ptr<SharedWorldPresence>);
    SharedTaiwanOwnedItemSelectionSource(const SharedTaiwanOwnedItemSelectionSource&)=delete;
    SharedTaiwanOwnedItemSelectionSource& operator=(const SharedTaiwanOwnedItemSelectionSource&)=delete;
    SharedTaiwanOwnedItemSelectionSource(SharedTaiwanOwnedItemSelectionSource&&)=delete;
    SharedTaiwanOwnedItemSelectionSource& operator=(SharedTaiwanOwnedItemSelectionSource&&)=delete;
    std::optional<Selection> select(Session&,RecoveredSelectionItemRequest::Request);
    // Current BEFORE mutation only. A later staged next must be qualified as
    // next, never compared with this old full population after intended CAS.
    bool current(Session&,const Selection&);
    // Same private selection connection/ready receipt, without comparing the
    // old inventory after an intended joint mutation. No action permission.
    bool ready_current(Session&,const Selection&);
    // Pure construction identity; no read, grant or ready-state inference.
    bool owns_presence(const std::shared_ptr<SharedWorldPresence>& common) const noexcept {return presence_==common;}
    bool owns_repository(const SqliteOwnedInventoryRepository& actual) const noexcept {return &repository_==&actual;}
private:
    SharedTaiwanOwnedItemSelectionSource(SqliteOwnedInventoryRepository&,AccountRepository&,
        RecoveredCharacterRepository&,std::shared_ptr<SharedWorldPresence>,bool definitions,bool deity_equipment=false);
    void owner() const;
    bool ready(Session&,const SharedWorldPresence::Lease&,const RecoveredPosition&,std::uint64_t) const;
    SqliteOwnedInventoryRepository& repository_;
    AccountRepository& accounts_;
    RecoveredCharacterRepository& characters_;
    std::shared_ptr<SharedWorldPresence> presence_;
    const bool definitions_;
    const bool deity_equipment_;
    const std::thread::id thread_=std::this_thread::get_id();
    bool reading_=false,reentered_=false;
};
}
