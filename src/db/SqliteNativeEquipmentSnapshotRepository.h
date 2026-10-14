#pragma once
#include "db/NativeEquipmentSnapshotRepository.h"
#include "db/SqliteAccountRepository.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include <functional>
#include <thread>
#include <memory>
#include <utility>

namespace god2 {
class SqliteNativeEquipmentSnapshotRepository final:public NativeEquipmentSnapshotRepository {
    struct Identity {};
public:
    SqliteNativeEquipmentSnapshotRepository(sqlite3*,const SqliteAccountRepository&,
        SqliteRecoveredCharacterRepository&);
    SqliteNativeEquipmentSnapshotRepository(const SqliteNativeEquipmentSnapshotRepository&)=delete;
    SqliteNativeEquipmentSnapshotRepository& operator=(const SqliteNativeEquipmentSnapshotRepository&)=delete;
    // Explicit fresh schema SOURCE only. No default migration or schema on read.
    static std::string schema();
    bool owns_sources(const AccountRepository&,const RecoveredCharacterRepository&) const noexcept override;
    bool owns_characters(const RecoveredCharacterRepository&) const noexcept override;
    std::optional<NativeEquipmentSnapshot> load(std::uint64_t,std::uint64_t,std::string_view,std::string_view) override;
    using Snapshot=NativeEquipmentSnapshot;
    enum class WriteCheck {Prepared,BeforeWrite,BeforeCommit};
    // Actual source/rules/resource/crypto/phase issuer. Synchronous, no yield,
    // pumping, SQL writes or borrowed captures. BeforeCommit sees staged next.
    // Returns the COMPLETE qualified next snapshot at every stage, exactly equal
    // to planned next. No defaults/padding/grants or bool-only Current issuer.
    using Issuer=std::function<std::optional<Snapshot>(const std::optional<Snapshot>&,const Snapshot&,WriteCheck)>;
    class Committed {
    public:
        Committed(const Committed&)=default;
        Committed& operator=(const Committed&)=default;
        // Keep both owned tokens valid; moved-from public getters cannot expose
        // a null witness, and token identity cannot be copied from a writer.
        Committed(Committed&& other) noexcept:identity_(other.identity_),snapshot_(other.snapshot_) {}
        Committed& operator=(Committed&& other) noexcept {
            identity_=other.identity_;snapshot_=other.snapshot_;return *this;
        }
        const Snapshot& snapshot() const noexcept {return *snapshot_;}
    private:
        friend class SqliteNativeEquipmentSnapshotRepository;
        friend class SqliteOwnedEquipmentTransaction;
        Committed(std::shared_ptr<const Identity> identity,std::shared_ptr<const Snapshot> snapshot) noexcept
            :identity_(std::move(identity)),snapshot_(std::move(snapshot)) {}
        std::shared_ptr<const Identity> identity_;
        std::shared_ptr<const Snapshot> snapshot_;
    };
    // Exact same writer token plus complete current storage/common-root tuple.
    // Requires autocommit: a staged savepoint may never masquerade as durable.
    bool committed_current(const Committed&);
    // Own BEGIN IMMEDIATE; exact expected tuple and unchanged common roots.
    // Caller supplies actual positive increasing revision, bytes and origin.
    // Writes delivery witness only: does not mutate canonical items/character saves,
    // acquire items, recover equip rules or activate release. Preallocate token
    // before COMMIT; only successful outer durable COMMIT returns it.
    std::optional<Committed> replace_from_issuer(std::optional<Snapshot> expected,Snapshot next,Issuer);
private:
    friend class SqliteOwnedEquipmentTransaction;
    friend class SqliteSkillBookLearningRepository;
    // Internal only: caller owns the one outer transaction and both writer
    // guards. Never returns an uncommitted public receipt or invokes a supplier.
    void validate_change(const std::optional<Snapshot>&,const Snapshot&) const;
    void stage_replace(const std::optional<Snapshot>&,const Snapshot&);
    void owner() const;
    sqlite3* db_;
    const SqliteAccountRepository& accounts_;
    SqliteRecoveredCharacterRepository& characters_;
    const std::thread::id owner_=std::this_thread::get_id();
    bool writing_=false,reentered_=false,issuer_active_=false;
    const std::shared_ptr<const Identity> identity_=std::make_shared<const Identity>();
};
}
