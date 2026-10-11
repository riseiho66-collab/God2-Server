#include "handlers/OwnedBlacklistService.h"
#include "db/DbTypes.h"
namespace god2 {
std::optional<std::vector<std::uint8_t>> OwnedBlacklistService::handle(
        std::uint64_t account,std::uint64_t character,const TaiwanNativeBlacklist::Request& actual,SqliteOwnedBlacklistRepository::Current current) {
    const auto request=actual; // Own original bytes before any storage observer.
    const auto row=request.adding()?repository_.add(account,character,request.name(),current):
        repository_.remove(account,character,request.row_id(),current);
    if(!row)return std::vector<std::uint8_t>{}; // Explicit rejected/no mutation; no invented native error record.
    // Repository returns only AFTER its outer COMMIT. A delivery allocation/
    // failure cannot roll back/retry that durable prefix or pretend peer ACK.
    const auto reply=request.adding()?TaiwanNativeBlacklist::added(row->row_id,row->name):
        TaiwanNativeBlacklist::removed(row->row_id);
    if(!reply)throw DatabaseError("Committed owned blacklist projection invalid");
    return reply;
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
