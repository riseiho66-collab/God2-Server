#pragma once
#include "db/NativeAccountSnapshotRepository.h"
#include "db/SqliteAccountRepository.h"
#include <functional>
#include <thread>

namespace god2 {
class SqliteNativeAccountSnapshotRepository final:public NativeAccountSnapshotRepository {
public:
    SqliteNativeAccountSnapshotRepository(sqlite3*,const SqliteAccountRepository&);
    // Proposal only: no constructor/accessor/read DDL, no migration registration,
    // import, implicit writes, account changes or default native values.
    static std::string schema();
    bool owns_accounts(const AccountRepository&) const noexcept override;
    std::optional<NativeAccountSnapshot> load(std::uint64_t,std::string_view) override;
    using Snapshot=NativeAccountSnapshot;
    enum class WriteCheck {Prepared,BeforeWrite,BeforeCommit};
    // Actual issuer/source revision/policy observer. Never pass account records
    // or credentials. No SQL, writes, pumping, yields or borrowed captures.
    // BeforeCommit observes the staged next tuple, not old snapshot Current.
    using Issuer=std::function<bool(const std::optional<Snapshot>& expected,
        const Snapshot& next,WriteCheck)>;
    // Explicit own transaction, full expected tuple and unchanged full account
    // baseline. Real issuer supplies every byte/origin and increasing revision;
    // no generated initial/revision++, schema installation or login fallback.
    // Nullopt means no commit. Return owns readback before durable COMMIT.
    std::optional<Snapshot> replace_from_issuer(std::optional<Snapshot> expected,Snapshot next,Issuer);
private:
    void owner() const;
    sqlite3* db_;
    const SqliteAccountRepository& accounts_;
    const std::thread::id owner_=std::this_thread::get_id();
    bool writing_=false;
};
}
