#include "db/SqliteNativeCharacterSummarySnapshotRepository.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <limits>
#include <tuple>
#include <utility>

namespace god2 {
SqliteNativeCharacterSummarySnapshotRepository::RemovalObservation
SqliteNativeCharacterSummarySnapshotRepository::read_removal_observation(std::uint64_t account) {
    owner();
    if(writing_ || !owns_sources(accounts_,characters_) || !sqlite3_get_autocommit(db_))
        throw DatabaseError("Summary removal observation requires same backend, owner and own transaction");
    struct Lease {bool& active;~Lease(){active=false;}} lease{writing_};writing_=true;
    sqlite_detail::Transaction transaction(db_);
    RemovalObservation observed{load_for_account(account),characters_.list_for_account(account)};
    transaction.commit();return observed;
}
std::vector<SqliteNativeCharacterSummarySnapshotRepository::Snapshot>
SqliteNativeCharacterSummarySnapshotRepository::load_for_account(std::uint64_t account) {
    owner();
    if(!account || account>static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()) ||
       sqlite3_get_autocommit(db_))throw DatabaseError("Summary inventory requires actual account and owner transaction");
    {
        sqlite_detail::Statement root(db_,"SELECT id FROM accounts WHERE id=?");root.bind_id(1,account);
        if(!root.row() || root.number<std::uint64_t>(0)!=account || root.row())
            throw DatabaseError("Summary inventory account missing or ambiguous");
    }
    std::vector<std::tuple<std::uint16_t,std::uint16_t,std::string>> scopes;
    {
        sqlite_detail::Statement query(db_,"SELECT group_id,server_id,client_sha256 FROM account_native_character_summaries "
            "WHERE account_id=? ORDER BY group_id,server_id,client_sha256");query.bind_id(1,account);
        while(query.row()) {
            auto scope=std::tuple{query.number<std::uint16_t>(0),query.number<std::uint16_t>(1),query.text(2)};
            if(!scopes.empty() && scope<=scopes.back())throw DatabaseError("Summary inventory duplicate scope");
            scopes.push_back(std::move(scope));
        }
    }
    std::vector<Snapshot> result;result.reserve(scopes.size());std::uint64_t mapped=0;
    for(const auto& [group,server,profile]:scopes) {
        auto value=load(account,group,server,profile);
        if(!value)throw DatabaseError("Summary inventory header disappeared");
        if(value->rows.size()>std::numeric_limits<std::uint64_t>::max()-mapped)
            throw DatabaseError("Summary inventory mapping count overflow");
        mapped+=value->rows.size();result.push_back(std::move(*value));
    }
    // Always read the child table, including an actually empty header set.
    // A missing schema or orphan outside listed scopes must not look absent.
    sqlite_detail::Statement children(db_,"SELECT COUNT(*) FROM account_native_character_summary_rows WHERE account_id=?");
    children.bind_id(1,account);
    if(!children.row() || children.number<std::uint64_t>(0)!=mapped || children.row())
        throw DatabaseError("Summary inventory child cardinality or orphan conflict");
    return result;
}
void SqliteNativeCharacterSummarySnapshotRepository::check_removal_inventory(
    std::uint64_t account,std::uint64_t character,std::span<const Snapshot> expected) {
    owner();
    if(!writing_ || sqlite3_get_autocommit(db_) || !character)
        throw DatabaseError("Summary removal requires its common owner transaction/lease");
    const auto actual=load_for_account(account);
    if(actual.size()!=expected.size() || !std::equal(actual.begin(),actual.end(),expected.begin()))
        throw DatabaseError("Summary removal full account tuple conflict");
    // The schema's character FK alone does not prove account ownership. Never
    // let descendant cleanup silently repair another account's malformed row.
    sqlite_detail::Statement foreign(db_,"SELECT account_id FROM account_native_character_summary_rows "
        "WHERE character_id=? AND account_id<>? LIMIT 1");
    foreign.bind_id(1,character);foreign.bind_id(2,account);
    if(foreign.row())throw DatabaseError("Summary removal has foreign account character reference");
}
void SqliteNativeCharacterSummarySnapshotRepository::invalidate_for_removal(
    std::uint64_t account,std::uint64_t character,std::span<const Snapshot> expected) {
    check_removal_inventory(account,character,expected);
    {
        sqlite_detail::Statement remove(db_,"DELETE FROM account_native_character_summaries WHERE account_id=?");
        remove.bind_id(1,account);remove.done();
        if(expected.size()>static_cast<std::size_t>(std::numeric_limits<int>::max()) ||
           sqlite3_changes(db_)!=static_cast<int>(expected.size()))throw DatabaseError("Summary removal header cardinality conflict");
    }
    // Successful FK cascade is checked independently of header changes().
    // No new empty/raw07/row_count/revision is generated in this transaction.
    if(!load_for_account(account).empty())throw DatabaseError("Summary removal invalidation incomplete");
}
}
