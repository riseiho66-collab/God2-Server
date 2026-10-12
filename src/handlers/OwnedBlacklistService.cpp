#include "handlers/OwnedBlacklistService.h"
#include "db/DbTypes.h"
namespace god2 {
std::optional<SqliteOwnedBlacklistRepository::CommittedChange> OwnedBlacklistService::handle_committed(
        std::uint64_t account,std::uint64_t character,const TaiwanNativeBlacklist::Request& actual,SqliteOwnedBlacklistRepository::Current current) {
    const auto request=actual; // Own original bytes before any storage observer.
    return request.adding()?repository_.add_committed(account,character,request.name(),std::move(current)):
        repository_.remove_committed(account,character,request.row_id(),std::move(current));
}
std::optional<std::vector<std::uint8_t>> OwnedBlacklistService::handle(
        std::uint64_t account,std::uint64_t character,const TaiwanNativeBlacklist::Request& actual,SqliteOwnedBlacklistRepository::Current current) {
    auto result=handle_committed(account,character,actual,std::move(current));
    if(!result)return std::vector<std::uint8_t>{}; // Original rejected/no-mutation behavior.
    // Move the exact pre-COMMIT original projection; no allocation/re-observation.
    return std::optional<std::vector<std::uint8_t>>(std::move(result->data_->logical));
}
SqliteOwnedBlacklistRepository::Snapshot OwnedBlacklistService::observe(std::uint64_t account,std::uint64_t character,SqliteOwnedBlacklistRepository::Current current) {
    return repository_.load(account,character,std::move(current));
}
OwnedBlacklistService::Replay OwnedBlacklistService::restore(const SqliteOwnedBlacklistRepository::Snapshot& snapshot,std::uint32_t after_row,bool active_phase) {
    const auto& rows=snapshot.rows;
    Replay result{{},after_row,true};result.logical.reserve(120*21);
    unsigned count=0;
    for(const auto& row:rows) {
        if(row.active!=active_phase || row.row_id<=after_row)continue;
        if(count++==120){result.done=false;break;}
        const auto record=row.active?TaiwanNativeBlacklist::added(row.row_id,row.name):TaiwanNativeBlacklist::removed(row.row_id);
        if(!record)throw DatabaseError("Owned blacklist restoration invalid");
        result.logical.insert(result.logical.end(),record->begin(),record->end());result.last_row=row.row_id;
    }
    return result;
}
}
