#pragma once
#include "db/NativeCharacterSummarySnapshotRepository.h"
#include "db/SqliteAccountRepository.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include <functional>
#include <span>
#include <thread>

namespace god2 {
class SqliteNativeCharacterSummarySnapshotRepository final:public NativeCharacterSummarySnapshotRepository {
public:
    SqliteNativeCharacterSummarySnapshotRepository(sqlite3*,const SqliteAccountRepository&,
        SqliteRecoveredCharacterRepository&);
    // Source proposal only. No constructor/accessor/load DDL or writes, no
    // default migration, installation/import or synthesized native data.
    static std::string schema();
    bool owns_sources(const AccountRepository&,const RecoveredCharacterRepository&) const noexcept override;
    bool owns_characters(const RecoveredCharacterRepository& value) const noexcept {return owns_sources(accounts_,value);}
    std::optional<NativeCharacterSummarySnapshot> load(std::uint64_t,std::uint16_t,std::uint16_t,std::string_view) override;
    using Snapshot=NativeCharacterSummarySnapshot;
    enum class WriteCheck {Prepared,BeforeWrite,BeforeCommit};
    // Real issuer/rules/source-revision/visibility/operation observer. No SQL
    // writes, event pumping, yields, borrowed captures or fallback true.
    // BeforeCommit observes the STAGED next tuple, never old snapshot Current.
    using Issuer=std::function<bool(const std::optional<Snapshot>& expected,const Snapshot& next,
        WriteCheck,std::span<const RecoveredCharacter> complete_account_roots)>;
    // Own atomic transaction, exact expected fulltuple CAS, unchanged complete
    // common roots. Candidate revision/origin/data all supplied by real issuer;
    // no initial1/revision++/native values generated. Missing schema is error.
    // Nullopt means no commit, not a native response. No release activation.
    std::optional<Snapshot> replace_from_issuer(std::optional<Snapshot> expected,Snapshot next,Issuer);
    // Complete account/build/destination inventory, canonical scope order.
    // Multi-SELECT requires the caller's actual owner transaction throughout;
    // no implicit BEGIN, missing-schema=>empty, schema install or guessed rows.
    std::vector<Snapshot> load_for_account(std::uint64_t account);
    struct RemovalObservation {
        std::vector<Snapshot> summaries;
        std::vector<RecoveredCharacter> roots;
    };
    // Explicit own-server preparation read: same owner/connection, own
    // BEGIN IMMEDIATE for one consistent observation, no persisted mutation,
    // schema install or permission. Both vectors owned before read COMMIT.
    // This COMMIT is not character removal or a native success receipt.
    RemovalObservation read_removal_observation(std::uint64_t account);
private:
    friend class SqliteRecoveredCharacterRepository;
    // Only the explicit common removal source may stage this in its own
    // transaction. Its writing_ lease covers all callbacks/root cleanup.
    void check_removal_inventory(std::uint64_t account,std::uint64_t character,
        std::span<const Snapshot> expected);
    void invalidate_for_removal(std::uint64_t account,std::uint64_t character,
        std::span<const Snapshot> expected);
    void owner() const;
    sqlite3* db_;
    const SqliteAccountRepository& accounts_;
    SqliteRecoveredCharacterRepository& characters_;
    const std::thread::id owner_=std::this_thread::get_id();
    bool writing_=false;
    bool reentered_=false;
};
}
