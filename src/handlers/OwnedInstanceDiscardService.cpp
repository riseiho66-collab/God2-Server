#include "handlers/OwnedInstanceDiscardService.h"
#include "db/DbTypes.h"
#include "protocol/RecoveredInventoryProjection.h"
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
#include <type_traits>

namespace god2 {
namespace {
void require(bool condition,const char* why){if(!condition)throw DatabaseError(why);}
template<class T>const T* at(const std::vector<T>& rows,std::uint8_t slot){const auto found=std::find_if(rows.begin(),rows.end(),[&](const auto& row){return row.slot==slot;});return found==rows.end()?nullptr:&*found;}
}
OwnedInstanceDiscardService::OwnedInstanceDiscardService(SqliteOwnedInstanceDiscardRepository& repo,Lookup lookup,Permit permit,Receipt receipt,PlainProjection plain,BeforeCommit invalidate_bank,PrepareExtra extra)
    :repo_(repo),lookup_(std::move(lookup)),permit_(std::move(permit)),receipt_(std::move(receipt)),plain_(std::move(plain)),invalidate_bank_(std::move(invalidate_bank)),extra_(std::move(extra)){
    require(bool(lookup_)&&bool(permit_)&&bool(receipt_)&&bool(plain_),"Owned discard requires qualified live adapters");
}
std::optional<RecoveredInventoryDiscard::Request> OwnedInstanceDiscardService::request(std::span<const RecoveredWorldRecords::Record> records){
    std::optional<RecoveredInventoryDiscard::Request> result;
    for(const auto& record:records){
        if(const auto* discard=std::get_if<RecoveredInventoryDiscard::Request>(&record)){if(result)return {};result=*discard;}
        else if(!std::holds_alternative<RecoveredWorldRecords::Tick>(record))return {};
    }
    return result;
}
bool OwnedInstanceDiscardService::same_owner_world(const Peer& a,const Peer& b){
    return a.ready&&b.ready&&a.session==b.session&&a.account==b.account&&a.character==b.character&&a.area==b.area&&a.scene==b.scene;
}
std::vector<std::uint8_t> OwnedInstanceDiscardService::project_source(const Snapshot& saved,std::uint8_t slot) const{
    require(slot<30&&saved.bag.scalar[slot],"Owned discard projection needs an existing ordinary cell");
    const auto& scalar=*saved.bag.scalar[slot];
    if(!scalar.count){const auto clear=RecoveredInventory::clear_slot(slot);require(clear.has_value(),"Owned discard clear rejected");return {clear->begin(),clear->end()};}
    const auto* armor=at(saved.bag.armor,slot);const auto* weapon=at(saved.bag.weapons,slot);const auto* gem=at(saved.bag.gems,slot);
    require(unsigned(armor!=nullptr)+unsigned(weapon!=nullptr)+unsigned(gem!=nullptr)<=1,"Owned discard projection overlay collision");
    RecoveredInventoryProjection::Metadata bytes{};
    if(armor)bytes=armor->logical20;else if(weapon)bytes=weapon->logical20;else if(gem)bytes=gem->logical20;
    else {
        bytes[0]=static_cast<std::uint8_t>(scalar.item_id);bytes[1]=static_cast<std::uint8_t>(scalar.item_id>>8);
        const auto canonical=RecoveredInventoryProjection::encode({slot,scalar.count,bytes});
        require(canonical.has_value(),"Owned discard plain refusal projection failed");
        auto logical=plain_(slot,scalar);require(logical==*canonical,"Owned discard plain refusal is not qualified canonical encoding");return logical;
    }
    require(scalar.count==1&&static_cast<std::uint16_t>(bytes[0]|(std::uint16_t{bytes[1]}<<8))==scalar.item_id,"Owned discard full20 refusal key/count mismatch");
    const auto logical=RecoveredInventoryProjection::encode({slot,scalar.count,bytes});require(logical.has_value(),"Owned discard complete20 refusal projection failed");return *logical;
}
OwnedInstanceDiscardService::Result OwnedInstanceDiscardService::handle(std::uint64_t session,std::span<const RecoveredWorldRecords::Record> records,Clock::time_point now){
    static_assert(std::is_nothrow_move_constructible_v<Result>);
    static_assert(std::is_nothrow_move_constructible_v<SqliteOwnedInstanceDiscardRepository::Plan>);
    Result result;std::optional<Peer> owner;const auto parsed=request(records);
    if(!parsed){result.rejected=true;return result;}
    const auto r=*parsed;
    try{
        require(r.slot<30,"Owned discard equipped/special source rejected");
        owner=lookup_(session);require(owner&&owner->ready&&owner->session==session&&owner->account&&owner->character&&permit_(session,r.slot,now),"Owned discard owner/live lease rejected");
        const auto before=repo_.load(owner->account,owner->character);
        const SqliteOwnedInstanceDiscardRepository::Request operation{before,r.item,r.slot,r.quantity};
        const auto check_live=[&](Clock::time_point when){const auto live=lookup_(session);require(live&&same_owner_world(*owner,*live)&&permit_(session,r.slot,when),"Owned discard late owner/world/lease rejected");};
        check_live(now);
        // Every reply allocation and optional preparation occurs before BEGIN.
        // After COMMIT only noexcept moves/flags may execute; a committed
        // destruction must never be mislabeled as a rolled-back rejection.
        repo_.commit(receipt_(),operation,[&](const auto& planned){
            require(planned.slot==r.slot&&planned.after.bag.scalar[r.slot]&&!planned.after.bag.scalar[r.slot]->count&&!planned.after.bag.scalar[r.slot]->item_id,"Owned discard prepared plan is not selected clear");
            const auto clear=RecoveredInventory::clear_slot(r.slot);require(clear.has_value(),"Owned discard native41 clear failed");
            result.wire=RecoveredWorldFrame::encode(*clear);if(extra_)extra_(planned);check_live(now);
            // Existing bank leases are invalidated only after the complete
            // typed plan and reply qualify, before BEGIN or any destruction.
            if(invalidate_bank_)invalidate_bank_(session);check_live(now);
        },[&](const auto&){check_live(Clock::now());});
        result.committed=true;return result;
    }catch(...){
        result.wire.clear();result.rejected=true;
        // Restoration is authoritative and only for the same eligible idle
        // world owner. Invalid/unqualified evidence produces no forged bytes.
        try{
            if(owner&&owner->session==session&&r.slot<30){const auto live=lookup_(session);if(live&&live->session==session&&same_owner_world(*owner,*live)&&permit_(session,r.slot,Clock::now())){
                const auto saved=repo_.load(live->account,live->character);auto logical=project_source(saved,r.slot);
                require(repo_.load(live->account,live->character)==saved,"Owned discard refusal source changed during encoding");
                const auto still=lookup_(session);require(still&&same_owner_world(*owner,*still)&&permit_(session,r.slot,Clock::now()),"Owned discard refusal world changed");
                result.wire=RecoveredWorldFrame::encode(logical);
            }}
        }catch(...){result.wire.clear();}
        return result;
    }
}
}
