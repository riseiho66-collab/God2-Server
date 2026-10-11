#include "cn/auth/CnNativeCharacterSummaryCommit.h"
#include "cn/auth/SharedCommonCharacterSummarySource.h"
#include "cn/protocol/CnCharacterSummary.h"
#include "db/SqliteDatabase.h"
#include <algorithm>
#include <set>
#include <utility>

namespace god2::cn {
namespace {
constexpr std::string_view client="582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8";
bool origin(std::string_view hash,std::string_view row) {
    return hash.size()==64 && std::all_of(hash.begin(),hash.end(),[](char c) {
        return (c>='0' && c<='9') || (c>='a' && c<='f');
    }) && !row.empty() && row.size()<=2048 && row.find('\0')==row.npos;
}
bool qualified_shape(const NativeCharacterSummarySnapshot& value) {
    const auto record=god2cn::CnCharacterSummary::read(value.record);
    if(!value.account || !value.revision || value.client_sha256!=client || value.group>=64 || value.server>=10 ||
       !origin(value.source_sha256,value.source_record) || !record || value.rows.size()!=record->count())return false;
    std::set<std::uint64_t> ids;
    std::set<std::uint8_t> slots;
    for(unsigned ordinal=0;ordinal<value.rows.size();++ordinal) {
        const auto& row=value.rows[ordinal];const auto native=record->character(ordinal);
        if(!row.character || !ids.insert(row.character).second || !slots.insert(native->native_slot()).second)return false;
        if(row.name_source==NativeCharacterSummarySnapshot::NameSource::NativePromptMarker) {
            if(!native->native_name_prompt_marker())return false;
        }else if(row.name_source!=NativeCharacterSummarySnapshot::NameSource::CommonIdentity)return false;
        if(row.role && (!origin(row.role->source_sha256,row.role->source_record) ||
            !SharedCommonCharacterSummarySource::RoleLevel::from_native22(row.role->record,row.role->revision)))return false;
    }
    return true;
}
}
CnNativeCharacterSummaryCommit::Plan::Plan(std::optional<Snapshot> expected,Snapshot next,Issuer issuer)
    :expected_(std::move(expected)),next_(std::move(next)),issuer_(std::move(issuer)) {}
std::optional<CnNativeCharacterSummaryCommit::Plan> CnNativeCharacterSummaryCommit::Plan::from_actual_issuer(
    std::optional<Snapshot> expected,Snapshot next,Issuer issuer) {
    if(!issuer || !qualified_shape(next) || (expected && (!qualified_shape(*expected) ||
        expected->account!=next.account || expected->group!=next.group || expected->server!=next.server ||
        expected->client_sha256!=next.client_sha256 || expected->revision>=next.revision)))return std::nullopt;
    return Plan(std::move(expected),std::move(next),std::move(issuer));
}
std::optional<CnNativeCharacterSummaryCommit::Snapshot> CnNativeCharacterSummaryCommit::commit_actual_source(
    SqliteDatabase& database,Plan plan) {
    auto& writer=database.native_character_summary_writer();
    if(!writer.owns_sources(database.accounts(),database.recovered_characters()))
        throw DatabaseError("CN summary commit requires exact shared Application sources");
    return writer.replace_from_issuer(std::move(plan.expected_),std::move(plan.next_),std::move(plan.issuer_));
}
}
