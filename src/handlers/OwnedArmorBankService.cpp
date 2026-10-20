#include "handlers/OwnedArmorBankService.h"
#include "db/DbTypes.h"
#include "protocol/RecoveredWorldFrame.h"
#include "protocol/RecoveredTeleportGem.h"
#include <algorithm>
#include <exception>

namespace god2 {
namespace {
void require(bool ok,const char* why){if(!ok)throw DatabaseError(why);}
template<class T>const T* at(const std::vector<T>& rows,std::size_t slot){const auto found=std::find_if(rows.begin(),rows.end(),[&](const auto& row){return row.slot==slot;});return found==rows.end()?nullptr:&*found;}
RecoveredInventoryProjection::Metadata scalar_metadata(const StoredInventorySlot& row){RecoveredInventoryProjection::Metadata bytes{};bytes[0]=static_cast<std::uint8_t>(row.item_id);bytes[1]=static_cast<std::uint8_t>(row.item_id>>8);return bytes;}
}
OwnedArmorBankService::OwnedArmorBankService(SqliteOwnedArmorBankRepository& repo,SqliteBankItemsRepository& plain_repo,Lookup lookup,Permit permit,Renew renew,Eligible eligible,PlainProjection plain,Receipt receipt,QualifyWeapon weapon)
    :repo_(repo),plain_repo_(plain_repo),lookup_(std::move(lookup)),permit_(std::move(permit)),renew_(std::move(renew)),eligible_(std::move(eligible)),plain_(std::move(plain)),receipt_(std::move(receipt)),weapon_(std::move(weapon)){
    require(bool(lookup_)&&bool(permit_)&&bool(renew_)&&bool(eligible_)&&bool(plain_)&&bool(receipt_)&&bool(weapon_),"Owned bank requires qualified adapters");
}
void OwnedArmorBankService::append(Batches& batches,std::span<const std::uint8_t> logical){require(!logical.empty()&&logical.size()<=RecoveredWorldFrame::max_logical_size,"Owned bank response exceeds frame");if(batches.empty()||batches.back().size()+logical.size()>RecoveredWorldFrame::max_logical_size)batches.emplace_back();batches.back().insert(batches.back().end(),logical.begin(),logical.end());}
std::array<std::uint8_t,29> OwnedArmorBankService::vault_slot(const Snapshot& saved,std::size_t slot) const{
    require(slot<300,"Owned bank vault domain");const auto& cell=saved.vault[slot];auto bytes=scalar_metadata(cell);
    if(const auto* armor=at(saved.armor,slot)){require(cell.count==1&&slot%50>=2,"Owned bank armor reserved slot");bytes=armor->logical20;}
    else require(!cell.count||(slot%50>=2&&invoke_adapter(eligible_,cell)),"Owned bank plain vault eligibility");
    const auto encoded=RecoveredBankItems::slot(static_cast<std::uint8_t>(slot/50),static_cast<std::uint8_t>(slot%50),cell.count,bytes);require(encoded.has_value(),"Owned bank full48 projection failed");return *encoded;
}
std::vector<std::uint8_t> OwnedArmorBankService::bag_slot(const Snapshot& saved,std::uint8_t slot) const{
    require(slot<30&&saved.bag.scalar[slot],"Owned bank bag row missing");const auto& scalar=*saved.bag.scalar[slot];auto bytes=scalar_metadata(scalar);bool owned=false;
    if(const auto* row=at(saved.bag.armor,slot)){require(!invoke_adapter(weapon_,scalar.item_id)&&scalar.item_id!=RecoveredTeleportGem::item_id,"Owned bank armor classification conflict");bytes=row->logical20;owned=true;}
    if(const auto* row=at(saved.bag.weapons,slot)){require(!scalar.count||(invoke_adapter(weapon_,scalar.item_id)&&scalar.item_id!=RecoveredTeleportGem::item_id),"Owned bank weapon classification invalid");bytes=row->logical20;owned=true;}
    if(const auto* row=at(saved.bag.gems,slot)){require(scalar.item_id==RecoveredTeleportGem::item_id&&!invoke_adapter(weapon_,scalar.item_id)&&RecoveredTeleportGem::displayed_charges(row->logical20).has_value(),"Owned bank gem classification/charges invalid");bytes=row->logical20;owned=true;}
    const auto encoded=RecoveredInventoryProjection::encode({slot,scalar.count,bytes});require(encoded.has_value(),"Owned bank fullbag projection failed");
    if(scalar.count&&!owned){require(!invoke_adapter(weapon_,scalar.item_id)&&scalar.item_id!=RecoveredTeleportGem::item_id,"Owned bank full instance metadata missing");const auto plain=invoke_adapter(plain_,slot,scalar);require(plain==*encoded,"Owned bank plain projection not canonical");}
    return *encoded;
}
void OwnedArmorBankService::validate_projection_snapshot(const Snapshot& saved) const{
    for(const auto& row:saved.bag.weapons){const auto& cell=saved.bag.scalar[row.slot];require(cell.has_value()&&(!cell->count||(invoke_adapter(weapon_,cell->item_id)&&cell->item_id!=RecoveredTeleportGem::item_id)),"Owned bank observed weapon category invalid");}
    for(const auto& row:saved.bag.gems){const auto& cell=saved.bag.scalar[row.slot];require(cell&&cell->item_id==RecoveredTeleportGem::item_id&&!invoke_adapter(weapon_,cell->item_id)&&RecoveredTeleportGem::displayed_charges(row.logical20).has_value(),"Owned bank observed gem charges/category invalid");}
    for(const auto& row:saved.bag.armor)require(!invoke_adapter(weapon_,row.item_id)&&row.item_id!=RecoveredTeleportGem::item_id,"Owned bank observed armor category conflict");
    for(std::uint8_t slot=0;slot<30;++slot){const auto& cell=saved.bag.scalar[slot];require(cell.has_value(),"Owned bank bag row missing");if(cell->count&&(invoke_adapter(weapon_,cell->item_id)||cell->item_id==RecoveredTeleportGem::item_id))require(at(saved.bag.weapons,slot)||at(saved.bag.gems,slot),"Owned bank observed full metadata missing");}
}
OwnedArmorBankService::Batches OwnedArmorBankService::synchronization(const Snapshot& saved,const Snapshot* before,bool bags) const{
    validate_projection_snapshot(saved);Batches batches;for(std::size_t slot=0;slot<300;++slot)if(!before||saved.vault[slot]!=before->vault[slot]||bool(at(saved.armor,slot))!=bool(at(before->armor,slot))||(at(saved.armor,slot)&&*at(saved.armor,slot)!=*at(before->armor,slot)))append(batches,vault_slot(saved,slot));
    if(bags)for(std::uint8_t slot=0;slot<30;++slot)if(!before||saved.bag.scalar[slot]!=before->bag.scalar[slot])append(batches,bag_slot(saved,slot));return batches;
}
SqliteBankItemsRepository::Snapshot OwnedArmorBankService::plain_snapshot(const Snapshot& saved){SqliteBankItemsRepository::Snapshot plain;plain.account=saved.bag.account;plain.character=saved.bag.character;plain.vault=saved.vault;for(std::size_t slot=0;slot<30;++slot){require(saved.bag.scalar[slot].has_value(),"Owned bank plain bag row missing");plain.bag[slot]=*saved.bag.scalar[slot];}return plain;}
void OwnedArmorBankService::require_live(std::uint64_t session,const RecoveredBankService::Peer& expected,std::uint16_t target,Clock::time_point now) const {
    const auto live=invoke_adapter(lookup_,session);
    require(live&&live->ready&&live->session==session&&live->session==expected.session&&
        live->account==expected.account&&live->character==expected.character&&live->area==expected.area&&live->scene==expected.scene&&
        invoke_adapter(permit_,session,target,now),"Owned bank callback changed live owner/scene/lease");
    callbacks_.require_current();
}
OwnedArmorBankService::Batches OwnedArmorBankService::open(std::uint64_t session,std::uint16_t target,Clock::time_point now) {
    auto operation=callbacks_.enter();
    try {
        const auto peer=invoke_adapter(lookup_,session);
        require(peer&&peer->ready&&peer->session==session&&peer->account&&peer->character&&invoke_adapter(permit_,session,target,now),"Owned bank opening lease rejected");
        auto saved=repo_.load(peer->account,peer->character);callbacks_.require_current();
        auto projected=synchronization(saved,nullptr,false);callbacks_.require_current();
        require(repo_.load(peer->account,peer->character)==saved,"Owned bank changed during open projection");callbacks_.require_current();
        require_live(session,*peer,target,now);
        contexts_.insert_or_assign(session,Context{target,*peer,std::move(saved)});return projected;
    } catch(...) {contexts_.erase(session);throw;}
}
OwnedArmorBankService::Result OwnedArmorBankService::handle(std::uint64_t session,std::span<const RecoveredBankItems::Request> requests,Clock::time_point now) {
    auto operation=callbacks_.enter();Result result;
    try {
        // No map iterator/reference or caller-owned request spans a callback.
        require(requests.size()==1,"Owned bank batch missing");const auto r=requests.front();
        std::optional<Context> held;
        if(const auto found=contexts_.find(session);found!=contexts_.end())held=found->second;
        const auto peer=invoke_adapter(lookup_,session);
        require(held&&peer&&peer->ready&&peer->session==session,"Owned bank context missing");
        const auto& before=held->expected;const auto opened_peer=held->peer;
        require(peer->account==before.bag.account&&peer->character==before.bag.character&&r.target==held->target,"Owned bank owner/target changed");
        require_live(session,opened_peer,r.target,now);
        require(repo_.load(peer->account,peer->character)==before,"Owned bank context stale");callbacks_.require_current();
        const auto current=[&]{callbacks_.require_current();};
        require(r.page<3,"Owned bank UI page inaccessible");const auto flat=[&](std::uint8_t slot){require(slot>=2&&slot<50,"Owned bank reserved cell");return std::size_t{r.page}*50+slot;};
        using K=RecoveredBankItems::Kind;const StoredInventorySlot* source=nullptr;bool source_armor=false,destination_armor=false;
        if(r.kind==K::Deposit){require(r.source<30,"Owned bank source bag invalid");source=&*before.bag.scalar[r.source];source_armor=at(before.bag.armor,r.source)!=nullptr;destination_armor=at(before.armor,flat(r.destination))!=nullptr;}
        else if(r.kind==K::Withdraw){const auto slot=flat(r.source);require(r.destination<30,"Owned bank destination bag invalid");source=&before.vault[slot];source_armor=at(before.armor,slot)!=nullptr;destination_armor=at(before.bag.armor,r.destination)!=nullptr;}
        else if(r.kind==K::Move){source=&before.vault[flat(r.source)];source_armor=at(before.armor,flat(r.source))!=nullptr;destination_armor=at(before.armor,flat(r.destination))!=nullptr;}
        else throw DatabaseError("Owned bank unknown operation");
        require(source->count,"Owned bank empty source");const auto receipt=invoke_adapter(receipt_);callbacks_.require_current();Batches projected;Snapshot after;
        if(source_armor){
            const SqliteOwnedArmorBankRepository::Request request{before,static_cast<SqliteBankItemsRepository::Operation>(r.kind),r.page,r.source,r.destination,r.quantity};
            auto committed=repo_.commit(receipt,request,[&](const auto& planned){callbacks_.require_current();projected=synchronization(planned.after,&before,true);callbacks_.require_current();},[&](const auto& planned){callbacks_.require_current();repo_.verify_snapshot_in_transaction(planned.after);require(!repo_.receipt_exists(receipt,SqliteOwnedArmorBankRepository::ReceiptLedger::Plain),"Owned bank cross-ledger receipt conflict");callbacks_.require_current();require_live(session,opened_peer,r.target,Clock::now());},current);after=std::move(committed.after);
        }else{
            require(!destination_armor&&invoke_adapter(eligible_,*source),"Owned bank mixed/full foreign transfer rejected");if(r.kind==K::Deposit)require(!at(before.bag.weapons,r.source)&&!at(before.bag.gems,r.source),"Owned bank foreign instance transfer rejected");if(r.kind==K::Move){const auto& target=before.vault[flat(r.destination)];require(!target.count||invoke_adapter(eligible_,target),"Owned bank MED destination unqualified");}
            const SqliteBankItemsRepository::Request request{plain_snapshot(before),static_cast<SqliteBankItemsRepository::Operation>(r.kind),r.page,r.source,r.destination,r.quantity};const auto planned=SqliteBankItemsRepository::plan(request);after=before;after.vault=planned.vault;
            for(std::uint8_t slot=0;slot<30;++slot)if(*before.bag.scalar[slot]!=planned.bag[slot]){after.bag.scalar[slot]=planned.bag[slot];std::erase_if(after.bag.weapons,[&](const auto& row){return row.slot==slot&&row.origin=="EMPTY_SLOT_POLICY";});}
            projected=synchronization(after,&before,true);
            const SqliteBankItemsRepository::CommitProof proof{[&,before,receipt]{callbacks_.require_current();repo_.verify_snapshot_in_transaction(before);require(!repo_.receipt_exists(receipt),"Owned bank duplicate cross-ledger receipt");callbacks_.require_current();},[&,after,receipt]{callbacks_.require_current();repo_.verify_snapshot_in_transaction(after);require(!repo_.receipt_exists(receipt,SqliteOwnedArmorBankRepository::ReceiptLedger::Armor),"Owned bank late cross-ledger receipt conflict");callbacks_.require_current();require_live(session,opened_peer,r.target,Clock::now());},current};
            plain_repo_.commit(receipt,request,proof);
        }
        static_assert(std::is_nothrow_move_assignable_v<Snapshot>);
        static_assert(std::is_nothrow_move_assignable_v<Batches>);
        static_assert(std::is_nothrow_move_constructible_v<Result>);
        // COMMIT has completed; callback retirement cannot report rollback.
        result.batches=std::move(projected);result.committed=true;
        if(callbacks_.invalidated()){contexts_.erase(session);result.batches.clear();return result;}
        const auto fresh=contexts_.find(session);
        if(fresh==contexts_.end())return result;
        fresh->second.expected=std::move(after); // No callback before iterator retirement.
        try {invoke_adapter(renew_,session,now);}catch(...){contexts_.erase(session);if(callbacks_.invalidated())result.batches.clear();}
        return result;
    } catch(...) {
        result.rejected=true;
        std::optional<Context> retired;
        static_assert(std::is_nothrow_move_constructible_v<Context>);
        if(const auto found=contexts_.find(session);found!=contexts_.end()){retired.emplace(std::move(found->second));contexts_.erase(found);}
        if(callbacks_.invalidated()){result.batches.clear();return result;} // No recovery on a poisoned operation.
        if(retired)try {
            const auto live=invoke_adapter(lookup_,session);const auto& expected=retired->expected;
            if(live&&live->ready&&live->session==session&&live->account==expected.bag.account&&live->character==expected.bag.character&&
               live->area==retired->peer.area&&live->scene==retired->peer.scene)
            {
                const auto saved=repo_.load(live->account,live->character);callbacks_.require_current();
                result.batches=synchronization(saved,nullptr,true);
            }
            callbacks_.require_current();
        }catch(...){result.batches.clear();}
        return result;
    }
}
}
