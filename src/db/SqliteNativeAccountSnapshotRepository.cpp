#include "db/SqliteNativeAccountSnapshotRepository.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <limits>
#include <type_traits>
#include <utility>

namespace god2 {
namespace {
bool digest(std::string_view text) {
    return text.size()==64 && std::all_of(text.begin(),text.end(),[](char c) {
        return (c>='0' && c<='9') || (c>='a' && c<='f');
    });
}
bool positive(std::uint64_t value) {
    return value && value<=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
}
bool origin(std::string_view text) {
    return !text.empty() && text.size()<=2048 && text.find('\0')==text.npos;
}
// Internal CAS baseline only. Never pass or log these fields to a native issuer.
struct AccountBaseline {
    std::uint64_t id;
    std::string username,password_hash,created_at;
    bool operator==(const AccountBaseline&) const=default;
};
std::optional<AccountBaseline> account_baseline(sqlite3* db,std::uint64_t account) {
    sqlite_detail::Statement row(db,"SELECT id,username,password_hash,created_at FROM accounts WHERE id=?");
    row.bind_id(1,account);
    if(!row.row())return std::nullopt;
    AccountBaseline value{row.number<std::uint64_t>(0),row.text(1),row.text(2),row.text(3)};
    if(value.id!=account || !positive(value.id) || row.row())
        throw DatabaseError("Invalid or duplicate native snapshot account baseline");
    return value;
}
}
SqliteNativeAccountSnapshotRepository::SqliteNativeAccountSnapshotRepository(
    sqlite3* db,const SqliteAccountRepository& accounts):db_(db),accounts_(accounts) {
    if(!db || !accounts.uses_connection(db))throw DatabaseError("Native account snapshot requires same account connection");
}
bool SqliteNativeAccountSnapshotRepository::owns_accounts(const AccountRepository& accounts) const noexcept {
    return &accounts==&accounts_ && accounts_.uses_connection(db_);
}
void SqliteNativeAccountSnapshotRepository::owner() const {
    if(owner_!=std::this_thread::get_id())throw DatabaseError("Native account snapshot game owner mismatch");
}
std::optional<NativeAccountSnapshot> SqliteNativeAccountSnapshotRepository::load(
    std::uint64_t account,std::string_view profile) {
    owner();
    if(!account || account>static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()) || !digest(profile))
        throw DatabaseError("Invalid native account snapshot scope");
    // Existing account identity only. Do not read passwords/credentials or join
    // by display name. No SQL writes/BEGIN/DDL/schema installation on this path.
    sqlite_detail::Statement row(db_,
        "SELECT s.account_id,s.client_sha256,s.metadata,s.billing,s.revision,s.source_sha256,s.source_record "
        "FROM accounts a JOIN account_native_snapshots s ON s.account_id=a.id "
        "WHERE a.id=? AND s.client_sha256=?");
    row.bind_id(1,account);row.bind(2,std::string(profile));
    if(!row.row())return std::nullopt;
    NativeAccountSnapshot result;
    result.account=row.number<std::uint64_t>(0);result.client_sha256=row.text(1);
    // Operational shared opaque-storage bounds, not a recovered native length.
    const auto metadata=row.blob(2,1,4096);
    result.metadata.assign(metadata.begin(),metadata.end());
    const auto billing=row.blob(3,1,4096);
    result.billing.assign(billing.begin(),billing.end());
    result.revision=row.number<std::uint64_t>(4);result.source_sha256=row.text(5);result.source_record=row.text(6);
    if(result.account!=account || result.client_sha256!=profile || !result.revision ||
       !digest(result.client_sha256) || !digest(result.source_sha256) || result.source_record.empty() ||
       result.source_record.size()>2048 || result.source_record.find('\0')!=result.source_record.npos || row.row())
        throw DatabaseError("Invalid or duplicate native account snapshot data");
    return result;
}
std::optional<SqliteNativeAccountSnapshotRepository::Snapshot>
SqliteNativeAccountSnapshotRepository::replace_from_issuer(
    std::optional<Snapshot> expected,Snapshot next,Issuer issuer) {
    owner();
    if(writing_ || !issuer || !owns_accounts(accounts_) || !sqlite3_get_autocommit(db_))
        throw DatabaseError("Native account writer requires same owner/backend, actual issuer and own transaction");
    const auto valid=[](const Snapshot& value) {
        return positive(value.account) && positive(value.revision) && digest(value.client_sha256) &&
            digest(value.source_sha256) && origin(value.source_record) && !value.metadata.empty() &&
            value.metadata.size()<=4096 && !value.billing.empty() && value.billing.size()<=4096;
    };
    if(!valid(next) || (expected && (!valid(*expected) || expected->account!=next.account ||
        expected->client_sha256!=next.client_sha256 || expected->revision>=next.revision)))
        throw DatabaseError("Invalid native account issuer/CAS scope or supplied revision");
    struct Writing {
        bool& active;
        explicit Writing(bool& value):active(value){active=true;}
        ~Writing(){active=false;}
    } writing(writing_);
    {
        sqlite_detail::Statement keys(db_,"PRAGMA foreign_keys");
        if(!keys.row() || keys.integer(0)!=1 || keys.row())
            throw DatabaseError("Native account writer requires foreign keys");
    }
    sqlite_detail::Transaction transaction(db_);
    const auto account=account_baseline(db_,next.account);
    if(!account)throw DatabaseError("Native account issuer requires an existing account");
    const auto verify=[&](const std::optional<Snapshot>& wanted) {
        if(sqlite3_get_autocommit(db_) || !owns_accounts(accounts_) ||
           account_baseline(db_,next.account)!=account || load(next.account,next.client_sha256)!=wanted ||
           account_baseline(db_,next.account)!=account)
            throw DatabaseError("Native account snapshot fulltuple or full account conflict");
    };
    verify(expected);
    const bool prepared=issuer(expected,next,WriteCheck::Prepared);
    verify(expected);
    if(!prepared)return std::nullopt;
    verify(expected);
    const bool before_write=issuer(expected,next,WriteCheck::BeforeWrite);
    verify(expected);
    if(!before_write)return std::nullopt;
    {
        sqlite_detail::Statement write(db_,expected?
            "UPDATE account_native_snapshots SET metadata=?,billing=?,revision=?,source_sha256=?,source_record=? "
            "WHERE account_id=? AND client_sha256=? AND revision=?":
            "INSERT INTO account_native_snapshots(metadata,billing,revision,source_sha256,source_record,account_id,client_sha256) "
            "VALUES(?,?,?,?,?,?,?)");
        write.bind_blob(1,next.metadata);write.bind_blob(2,next.billing);write.bind_id(3,next.revision);
        write.bind(4,next.source_sha256);write.bind(5,next.source_record);write.bind_id(6,next.account);
        write.bind(7,next.client_sha256);
        if(expected)write.bind_id(8,expected->revision);
        write.done();if(sqlite3_changes(db_)!=1)throw DatabaseError("Native account snapshot revision CAS failed");
    }
    // Own every return byte BEFORE durable COMMIT. No callback/reload afterwards.
    auto result=load(next.account,next.client_sha256);
    if(!result || *result!=next)throw DatabaseError("Native account snapshot staged readback differs");
    verify(result);
    const bool before_commit=issuer(expected,next,WriteCheck::BeforeCommit);
    verify(result);
    if(!before_commit)return std::nullopt;
    static_assert(std::is_nothrow_move_constructible_v<std::optional<Snapshot>>);
    transaction.commit();
    return result;
}
std::string SqliteNativeAccountSnapshotRepository::schema() {
    // One common table; client-specific raw bytes are keyed by pinned build.
    // Account ownership/gameplay remain in existing common tables. No defaults.
    return R"SQL(CREATE TABLE account_native_snapshots (
 account_id INTEGER NOT NULL CHECK(typeof(account_id)='integer' AND account_id>0),
 client_sha256 TEXT NOT NULL CHECK(typeof(client_sha256)='text' AND length(client_sha256)=64 AND client_sha256 NOT GLOB '*[^0-9a-f]*'),
 metadata BLOB NOT NULL CHECK(typeof(metadata)='blob' AND length(metadata) BETWEEN 1 AND 4096),
 billing BLOB NOT NULL CHECK(typeof(billing)='blob' AND length(billing) BETWEEN 1 AND 4096),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 source_sha256 TEXT NOT NULL CHECK(typeof(source_sha256)='text' AND length(source_sha256)=64 AND source_sha256 NOT GLOB '*[^0-9a-f]*'),
 source_record TEXT NOT NULL CHECK(typeof(source_record)='text' AND length(CAST(source_record AS BLOB)) BETWEEN 1 AND 2048 AND instr(source_record,char(0))=0),
 PRIMARY KEY(account_id,client_sha256),
 FOREIGN KEY(account_id) REFERENCES accounts(id)
) WITHOUT ROWID;
)SQL";
}
}
