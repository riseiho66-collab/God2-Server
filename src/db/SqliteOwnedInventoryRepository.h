#pragma once
#include "db/OwnedInventoryRepository.h"
#include "db/NativeItemDefinitionObservation.h"
#include "db/NativeDeityEquipmentObservation.h"
#include "db/SqliteAccountRepository.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include <functional>
#include <memory>
#include <thread>
#include <utility>

namespace god2 {
// CUSTOM-0092 shared server storage, not native inventory/equipment rules.
// No migration, import, grant or callback is selected by ordinary Main.
class SqliteOwnedInventoryRepository final:public OwnedInventoryRepository {
    struct Identity {};
public:
    using Snapshot=OwnedInventorySnapshot;
    SqliteOwnedInventoryRepository(sqlite3*,const SqliteAccountRepository&,SqliteRecoveredCharacterRepository&);
    SqliteOwnedInventoryRepository(const SqliteOwnedInventoryRepository&)=delete;
    SqliteOwnedInventoryRepository& operator=(const SqliteOwnedInventoryRepository&)=delete;
    static std::string schema();
    bool owns_sources(const AccountRepository&,const RecoveredCharacterRepository&) const noexcept override;
    std::optional<Snapshot> load(std::uint64_t,std::uint64_t) override;
    enum class Check {Prepared,BeforeWrite,BeforeCommit};
    // Genuine source/definition/custody/rule owner returns COMPLETE next at
    // each boundary, not bool Current. Must be synchronous, no SQL writes,
    // transaction operations, callbacks into this writer, pump, yield or send.
    // BeforeCommit sees the actual staged next population. Grant entitlement,
    // slot eligibility and native alias meaning are still this owner's job.
    using Issuer=std::function<std::optional<Snapshot>(const std::optional<Snapshot>&,const Snapshot&,Check)>;
    class Committed {
    public:
        Committed(const Committed&)=default;
        Committed& operator=(const Committed&)=default;
        Committed(Committed&& v) noexcept:identity_(v.identity_),snapshot_(v.snapshot_) {}
        Committed& operator=(Committed&& v) noexcept {identity_=v.identity_;snapshot_=v.snapshot_;return *this;}
        const Snapshot& snapshot() const noexcept{return *snapshot_;}
    private:
        friend class SqliteOwnedInventoryRepository;
        friend class SqliteOwnedEquipmentTransaction;
        Committed(std::shared_ptr<const Identity> identity,std::shared_ptr<const Snapshot> snapshot) noexcept
            :identity_(std::move(identity)),snapshot_(std::move(snapshot)) {}
        std::shared_ptr<const Identity> identity_;
        std::shared_ptr<const Snapshot> snapshot_;
    };
    // Exact whole owner population CAS. All new IDs/acquisition receipts must
    // be globally unused; retired identities remain in a permanent registry.
    // No cross-owner transfer, merge/split algorithm or implicit resurrection.
    // Those require their own actual source-qualified multi-owner transaction.
    std::optional<Committed> replace_from_issuer(std::optional<Snapshot>,Snapshot,Issuer);
    // Fresh durable read observation of existing owned storage, not a new
    // transaction receipt or a grant. Requires autocommit and current root.
    std::optional<Committed> observe_committed(std::uint64_t account,std::uint64_t character);
    bool committed_current(const Committed&);
    // Own one read transaction on this exact common connection, qualify BOTH
    // full historical catalogs and one unique key. No grant or common-ID
    // conversion. Empty/incomplete/ambiguous definitions never choose a family.
    std::optional<NativeItemDefinitionObservation> observe_native_definition(std::uint16_t native_key);
    // Reuse the existing versioned raw witness table, exact separate kind42;
    // no schema mutation, implicit import, D1 generation or deity-row inference.
    std::optional<NativeDeityEquipmentObservation> observe_native_deity_equipment(
        std::uint64_t account,std::uint64_t character);
private:
    friend class SqliteOwnedEquipmentTransaction;
    // Internal only: caller owns the one outer transaction and both writer
    // guards. Never returns an uncommitted public receipt or invokes a supplier.
    void validate_change(const std::optional<Snapshot>&,const Snapshot&) const;
    void stage_replace(const std::optional<Snapshot>&,const Snapshot&);
    void owner() const;
    void namespaces() const;
    bool root_current(const RecoveredCharacter&);
    sqlite3* db_;
    const SqliteAccountRepository& accounts_;
    SqliteRecoveredCharacterRepository& characters_;
    const std::thread::id thread_=std::this_thread::get_id();
    bool writing_=false,reentered_=false,issuer_active_=false;
    const std::shared_ptr<const Identity> identity_=std::make_shared<const Identity>();
};
}
