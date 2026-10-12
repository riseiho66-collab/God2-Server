#pragma once
#include "db/NativeWorldEntrySnapshotRepository.h"
#include "db/SqliteAccountRepository.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include <functional>
#include <thread>

namespace god2 {
class SqliteNativeWorldEntrySnapshotRepository final:public NativeWorldEntrySnapshotRepository {
public:
    SqliteNativeWorldEntrySnapshotRepository(sqlite3*,const SqliteAccountRepository&,
        SqliteRecoveredCharacterRepository&);
    // Explicit fresh schema SOURCE only. No default migration or schema on read.
    static std::string schema();
    bool owns_sources(const AccountRepository&,const RecoveredCharacterRepository&) const noexcept override;
    bool owns_characters(const RecoveredCharacterRepository&) const noexcept override;
    std::optional<NativeWorldEntrySnapshot> load(std::uint64_t,std::uint64_t,std::string_view,std::string_view) override;
    using Snapshot=NativeWorldEntrySnapshot;
    enum class WriteCheck {Prepared,BeforeWrite,BeforeCommit};
    // Actual source/rules/resource/crypto/phase issuer. Synchronous, no yield,
    // pumping, SQL writes or borrowed captures. BeforeCommit sees staged next.
    // A raw blob, geometry match or always-true predicate is not an issuer.
    using Issuer=std::function<bool(const std::optional<Snapshot>&,const Snapshot&,WriteCheck)>;
    // Own BEGIN IMMEDIATE; exact expected tuple and unchanged common roots.
    // Caller supplies actual positive increasing revision, bytes and origin.
    // Does not mutate character/save, invent first material, or activate release.
    std::optional<Snapshot> replace_from_issuer(std::optional<Snapshot> expected,Snapshot next,Issuer);
private:
    friend class SqliteOwnedEquipmentTransaction;
    // Internal only: the joint owner guards this writer and owns the outer
    // transaction/current readset. No issuer, COMMIT or public receipt here.
    void validate_change(const std::optional<Snapshot>&,const Snapshot&) const;
    void stage_replace(const std::optional<Snapshot>&,const Snapshot&);
    void owner() const;
    sqlite3* db_;
    const SqliteAccountRepository& accounts_;
    SqliteRecoveredCharacterRepository& characters_;
    const std::thread::id owner_=std::this_thread::get_id();
    // Only the joint phase enables this flag; the existing public writer's
    // issuer/read behavior remains unchanged.
    bool writing_=false,reentered_=false,issuer_active_=false;
};
}
