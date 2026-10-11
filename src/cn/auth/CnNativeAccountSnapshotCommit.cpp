#include "cn/auth/CnNativeAccountSnapshotCommit.h"
#include "db/SqliteDatabase.h"
#include <algorithm>
#include <limits>
#include <utility>

namespace god2::cn {
namespace {
constexpr std::string_view client="582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8";
bool origin(std::string_view hash,std::string_view row) {
    return hash.size()==64 && std::all_of(hash.begin(),hash.end(),[](char c) {
        return (c>='0' && c<='9') || (c>='a' && c<='f');
    }) && !row.empty() && row.size()<=2048 && row.find('\0')==row.npos;
}
bool qualified_shape(const NativeAccountSnapshot& value) {
    // Actual NativeData::Scope.verified_account is uint32; SQLite revisions
    // must be positive signed64-representable. Neither bound is gameplay policy.
    return value.account && value.account<=std::numeric_limits<std::uint32_t>::max() &&
        value.revision && value.revision<=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()) &&
        value.client_sha256==client && value.metadata.size()==40 && value.billing.size()==16 &&
        origin(value.source_sha256,value.source_record);
}
}
CnNativeAccountSnapshotCommit::Plan::Plan(std::optional<Snapshot> expected,Snapshot next,Issuer issuer)
    :expected_(std::move(expected)),next_(std::move(next)),issuer_(std::move(issuer)) {}
std::optional<CnNativeAccountSnapshotCommit::Plan> CnNativeAccountSnapshotCommit::Plan::from_actual_issuer(
    std::optional<Snapshot> expected,Snapshot next,Issuer issuer) {
    if(!issuer || !qualified_shape(next) || (expected && (!qualified_shape(*expected) ||
        expected->account!=next.account || expected->client_sha256!=next.client_sha256 ||
        expected->revision>=next.revision)))return std::nullopt;
    return Plan(std::move(expected),std::move(next),std::move(issuer));
}
std::optional<CnNativeAccountSnapshotCommit::Snapshot> CnNativeAccountSnapshotCommit::commit_actual_source(
    SqliteDatabase& database,Plan plan) {
    auto& writer=database.native_account_snapshot_writer();
    if(!writer.owns_accounts(database.accounts()))
        throw DatabaseError("CN account snapshot commit requires exact shared Application account source");
    return writer.replace_from_issuer(std::move(plan.expected_),std::move(plan.next_),std::move(plan.issuer_));
}
}
