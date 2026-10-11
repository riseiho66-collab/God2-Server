#pragma once
#include "db/SqliteOwnedInventoryRepository.h"
#include "db/SqliteNativeEquipmentSnapshotRepository.h"
#include <functional>

namespace god2 {
// CUSTOM-0092 storage coordination, not recovered equip/unequip rules. A real
// source must supply BOTH complete next populations. No mapping from item key,
// category/icon/raw20 to DA, no padding of unknown cache bytes or item grants.
// Borrowed same-Application writers must outlive this game-owned object/drain.
class SqliteOwnedEquipmentTransaction final {
    struct Identity {};
public:
    struct Before {
        std::optional<OwnedInventorySnapshot> inventory;
        std::optional<NativeEquipmentSnapshot> equipment;
    };
    struct State {
        OwnedInventorySnapshot inventory;
        NativeEquipmentSnapshot equipment;
        bool operator==(const State&) const=default;
    };
    enum class Check {Prepared,BeforeWrite,BeforeCommit};
    // Full genuine definition/acquisition/custody/equip/native-presentation
    // issuer, including actual Session/lease/input freshness and rules. Sync,
    // no yields, sends, SQL writes/transaction operations or reader reentry.
    // BeforeCommit observes BOTH staged next populations. Exact State required.
    using Issuer=std::function<std::optional<State>(const Before&,const State&,Check)>;
    class Committed {
    public:
        Committed(const Committed&)=default;
        Committed& operator=(const Committed&)=default;
        Committed(Committed&& v) noexcept
            :identity_(v.identity_),inventory_(v.inventory_),equipment_(v.equipment_) {}
        Committed& operator=(Committed&& v) noexcept {
            identity_=v.identity_;inventory_=v.inventory_;equipment_=v.equipment_;return *this;
        }
        const SqliteOwnedInventoryRepository::Committed& inventory() const noexcept{return inventory_;}
        const SqliteNativeEquipmentSnapshotRepository::Committed& equipment() const noexcept{return equipment_;}
    private:
        friend class SqliteOwnedEquipmentTransaction;
        Committed(std::shared_ptr<const Identity> identity,SqliteOwnedInventoryRepository::Committed inventory,
            SqliteNativeEquipmentSnapshotRepository::Committed equipment) noexcept
            :identity_(std::move(identity)),inventory_(std::move(inventory)),equipment_(std::move(equipment)) {}
        std::shared_ptr<const Identity> identity_;
        SqliteOwnedInventoryRepository::Committed inventory_;
        SqliteNativeEquipmentSnapshotRepository::Committed equipment_;
    };
    SqliteOwnedEquipmentTransaction(SqliteOwnedInventoryRepository&,SqliteNativeEquipmentSnapshotRepository&);
    SqliteOwnedEquipmentTransaction(const SqliteOwnedEquipmentTransaction&)=delete;
    SqliteOwnedEquipmentTransaction& operator=(const SqliteOwnedEquipmentTransaction&)=delete;
    bool owns_sources(const AccountRepository&,const RecoveredCharacterRepository&) const noexcept;
    bool owns_writers(const SqliteOwnedInventoryRepository&,const SqliteNativeEquipmentSnapshotRepository&) const noexcept;
    SqliteNativeEquipmentSnapshotRepository& equipment_writer() const noexcept{return equipment_;}
    SqliteOwnedInventoryRepository& inventory_writer() const noexcept{return inventory_;}
    const RecoveredCharacterRepository& characters_repository() const noexcept{return inventory_.characters_;}
    // Own one IMMEDIATE transaction, full expected CAS for both stores. Every
    // failure rolls back both; no borrowed transaction/savepoint/public staged
    // tokens. Allocate the joint immutable receipt BEFORE the only COMMIT.
    std::optional<Committed> replace_from_issuer(Before,State,Issuer);
    // CUSTOM-0095 ordinary SAME-MAP persistence policy: retain every complete
    // inventory/native byte and identity, advance only saved x/y+position
    // revision and native witness revision/provenance. Not native after-state
    // capture, a grant, geometry/rules qualification or a movement reply issuer.
    // The actual scene/rules owner is checked twice while storage is still OLD,
    // at Prepared and immediately BeforeWrite; synchronous/no SQL writes,
    // transaction operations, sends, pumping, yields or reader/writer reentry.
    // Once staged, only concrete closed reads run, never an old-position Current.
    using MovementCurrent=std::function<bool()>;
    std::optional<Committed> move_position_from_current(Before expected,std::uint16_t actor_handle,
        std::uint16_t x,std::uint16_t y,MovementCurrent);
    // Single consistent read scope over BOTH current tuples and actual common
    // root/position/battle state. Never compose two independently current reads.
    bool committed_current(const Committed&);
    // Preparation-time exact full old tuple, in one actual consistent read
    // scope. Equality proves current material, never action/equip permission.
    bool before_current(const Before&);
    // Actual same-connection complete old tuple in one owned read scope.
    // Missing material stays absent; this never allocates slots or grants items.
    std::optional<Before> observe_before(std::uint64_t account,std::uint64_t character);
    // CUSTOM-0112: mint private receipts for ONE consistent complete durable
    // tuple, then requalify it. This is a read, not a new write, item/equip
    // grant, original native issuer or proof of historical writer invocation.
    std::optional<Committed> observe_committed(std::uint64_t account,std::uint64_t character);
private:
    void owner() const;
    bool common_current(const RecoveredCharacter&,const RecoveredPosition&);
    bool stored_current(const Before&,const State&);
    SqliteOwnedInventoryRepository& inventory_;
    SqliteNativeEquipmentSnapshotRepository& equipment_;
    const std::shared_ptr<const Identity> identity_=std::make_shared<const Identity>();
};
}
