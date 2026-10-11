#include "handlers/OwnedMixedBankService.h"
#include "db/DbTypes.h"
#include "protocol/RecoveredWorldFrame.h"
#include "protocol/RecoveredTeleportGem.h"
#include <algorithm>
#include <exception>
#include <type_traits>

namespace god2 {
namespace {
void require(bool ok,const char* why){if(!ok)throw DatabaseError(why);}
template<class T>const T* at(const std::vector<T>& rows,std::size_t slot){const auto found=std::find_if(rows.begin(),rows.end(),[&](const auto& row){return row.slot==slot;});return found==rows.end()?nullptr:&*found;}
const StoredBeastSnapshot* pet(const std::vector<StoredBeastSnapshot>& rows,std::size_t slot){const auto found=std::find_if(rows.begin(),rows.end(),[&](const auto& row){return row.inventory_slot==slot;});return found==rows.end()?nullptr:&*found;}
RecoveredInventoryProjection::Metadata scalar_metadata(const StoredInventorySlot& row){RecoveredInventoryProjection::Metadata bytes{};bytes[0]=static_cast<std::uint8_t>(row.item_id);bytes[1]=static_cast<std::uint8_t>(row.item_id>>8);return bytes;}
}
OwnedMixedBankService::OwnedMixedBankService(SqliteOwnedMixedBankRepository& repo,SqliteOwnedForeignBankRepository& foreign_repo,SqliteOwnedArmorBankRepository& armor_repo,SqliteBankItemsRepository& plain_repo,Lookup lookup,Permit permit,Renew renew,Eligible eligible,PlainProjection plain,Receipt receipt,QualifyWeapon weapon,SqliteBeastBankRepository* beasts,EligibleBeast beast_eligible)
    :repo_(repo),foreign_repo_(foreign_repo),armor_repo_(armor_repo),plain_repo_(plain_repo),lookup_(std::move(lookup)),permit_(std::move(permit)),renew_(std::move(renew)),eligible_(std::move(eligible)),plain_(std::move(plain)),receipt_(std::move(receipt)),weapon_(std::move(weapon)),beasts_(beasts),beast_eligible_(std::move(beast_eligible)){
    require(bool(lookup_)&&bool(permit_)&&bool(renew_)&&bool(eligible_)&&bool(plain_)&&bool(receipt_)&&bool(weapon_),"Owned bank requires qualified adapters");
}
OwnedMixedBankService::Snapshot OwnedMixedBankService::load_snapshot(std::uint64_t account,std::uint64_t character) const{return beasts_?beasts_->load(account,character):Snapshot(repo_.load(account,character));}
void OwnedMixedBankService::verify_snapshot(const Snapshot& saved) const{repo_.verify_snapshot_in_transaction(saved);if(beasts_)beasts_->verify_snapshot_in_transaction(saved);}
bool OwnedMixedBankService::duplicate(const std::string& receipt) const{return repo_.receipt_exists(receipt)||(beasts_&&beasts_->receipt_exists(receipt));}
void OwnedMixedBankService::append(Batches& batches,std::span<const std::uint8_t> logical){require(!logical.empty()&&logical.size()<=RecoveredWorldFrame::max_logical_size,"Owned bank response exceeds frame");if(batches.empty()||batches.back().size()+logical.size()>RecoveredWorldFrame::max_logical_size)batches.emplace_back();batches.back().insert(batches.back().end(),logical.begin(),logical.end());}
std::array<std::uint8_t,29> OwnedMixedBankService::vault_slot(const Snapshot& saved,std::size_t slot) const{
    require(slot<300,"Owned bank vault domain");const auto& cell=saved.base.vault[slot];auto bytes=scalar_metadata(cell);
    if(const auto* armor=at(saved.base.armor,slot)){require(cell.count==1&&slot%50>=2,"Owned bank armor reserved slot");bytes=armor->logical20;}
    else if(const auto* foreign=at(saved.foreign,slot)){require(cell.count==1&&slot%50>=2,"Owned bank foreign reserved slot");bytes=foreign->logical20;}
    else if(const auto* beast=at(saved.vault_beasts,slot)){require(saved.beast_scope&&cell.count==1&&slot%50>=2,"PET bank vault scope/count");bytes=beast->inventory_metadata;}
    else require(!cell.count||(slot%50>=2&&eligible_(cell)),"Owned bank plain vault eligibility");
    const auto encoded=RecoveredBankItems::slot(static_cast<std::uint8_t>(slot/50),static_cast<std::uint8_t>(slot%50),cell.count,bytes);require(encoded.has_value(),"Owned bank full48 projection failed");return *encoded;
}
std::vector<std::uint8_t> OwnedMixedBankService::bag_slot(const Snapshot& saved,std::uint8_t slot) const{
    require(slot<30&&saved.base.bag.scalar[slot],"Owned bank bag row missing");const auto& scalar=*saved.base.bag.scalar[slot];auto bytes=scalar_metadata(scalar);bool owned=false;
    if(const auto* row=at(saved.base.bag.armor,slot)){require(!weapon_(scalar.item_id)&&scalar.item_id!=RecoveredTeleportGem::item_id,"Owned bank armor classification conflict");bytes=row->logical20;owned=true;}
    if(const auto* row=at(saved.base.bag.weapons,slot)){require(!scalar.count||(weapon_(scalar.item_id)&&scalar.item_id!=RecoveredTeleportGem::item_id),"Owned bank weapon classification invalid");bytes=row->logical20;owned=true;}
    if(const auto* row=at(saved.base.bag.gems,slot)){require(scalar.item_id==RecoveredTeleportGem::item_id&&!weapon_(scalar.item_id)&&RecoveredTeleportGem::displayed_charges(row->logical20).has_value(),"Owned bank gem classification/charges invalid");bytes=row->logical20;owned=true;}
    if(const auto* row=pet(saved.beasts,slot)){require(saved.beast_scope&&scalar.count==1&&!owned,"PET bank bag scope/overlay collision");bytes=row->inventory_metadata;owned=true;}
    const auto encoded=RecoveredInventoryProjection::encode({slot,scalar.count,bytes});require(encoded.has_value(),"Owned bank fullbag projection failed");
    if(scalar.count&&!owned){require(!weapon_(scalar.item_id)&&scalar.item_id!=RecoveredTeleportGem::item_id,"Owned bank full instance metadata missing");const auto plain=plain_(slot,scalar);require(plain==*encoded,"Owned bank plain projection not canonical");}
    return *encoded;
}
void OwnedMixedBankService::validate_projection_snapshot(const Snapshot& saved) const{
    for(const auto& row:saved.base.bag.weapons){const auto& cell=saved.base.bag.scalar[row.slot];require(cell.has_value()&&(!cell->count||(weapon_(cell->item_id)&&cell->item_id!=RecoveredTeleportGem::item_id)),"Owned bank observed weapon category invalid");}
    for(const auto& row:saved.base.bag.gems){const auto& cell=saved.base.bag.scalar[row.slot];require(cell&&cell->item_id==RecoveredTeleportGem::item_id&&!weapon_(cell->item_id)&&RecoveredTeleportGem::displayed_charges(row.logical20).has_value(),"Owned bank observed gem charges/category invalid");}
    for(const auto& row:saved.base.bag.armor)require(!weapon_(row.item_id)&&row.item_id!=RecoveredTeleportGem::item_id,"Owned bank observed armor category conflict");
    for(std::uint8_t slot=0;slot<30;++slot){const auto& cell=saved.base.bag.scalar[slot];require(cell.has_value(),"Owned bank bag row missing");if(cell->count&&(weapon_(cell->item_id)||cell->item_id==RecoveredTeleportGem::item_id))require(at(saved.base.bag.weapons,slot)||at(saved.base.bag.gems,slot),"Owned bank observed full metadata missing");}
}
OwnedMixedBankService::Batches OwnedMixedBankService::synchronization(const Snapshot& saved,const Snapshot* before,bool bags) const{
    validate_projection_snapshot(saved);Batches batches;
    for(std::size_t slot=0;slot<300;++slot)if(!before||saved.base.vault[slot]!=before->base.vault[slot]||bool(at(saved.base.armor,slot))!=bool(at(before->base.armor,slot))||(at(saved.base.armor,slot)&&*at(saved.base.armor,slot)!=*at(before->base.armor,slot))||bool(at(saved.foreign,slot))!=bool(at(before->foreign,slot))||(at(saved.foreign,slot)&&*at(saved.foreign,slot)!=*at(before->foreign,slot))||bool(at(saved.vault_beasts,slot))!=bool(at(before->vault_beasts,slot))||(at(saved.vault_beasts,slot)&&*at(saved.vault_beasts,slot)!=*at(before->vault_beasts,slot)))append(batches,vault_slot(saved,slot));
    // CUSTOM0085 full ordinary synchronization closes any old presentation via
    // 4B physical0 plus the first41-clear, without changing saved selection.
    if(bags&&saved.beast_scope){const std::array<std::uint8_t,3> close{0x4b,0,0};append(batches,close);}
    if(bags)for(std::uint8_t slot=0;slot<30;++slot)if(saved.beast_scope||!before||saved.base.bag.scalar[slot]!=before->base.bag.scalar[slot])append(batches,bag_slot(saved,slot));return batches;
}

SqliteBankItemsRepository::Snapshot OwnedMixedBankService::plain_snapshot(const Snapshot& saved){SqliteBankItemsRepository::Snapshot plain;plain.account=saved.base.bag.account;plain.character=saved.base.bag.character;plain.vault=saved.base.vault;for(std::size_t slot=0;slot<30;++slot){require(saved.base.bag.scalar[slot].has_value(),"Owned bank plain bag row missing");plain.bag[slot]=*saved.base.bag.scalar[slot];}return plain;}
OwnedMixedBankService::Batches OwnedMixedBankService::open(std::uint64_t session,std::uint16_t target,Clock::time_point now){const auto peer=lookup_(session);require(peer&&peer->ready&&peer->session==session&&permit_(session,target,now),"Owned bank opening lease rejected");auto saved=load_snapshot(peer->account,peer->character);auto projected=synchronization(saved,nullptr,false);require(load_snapshot(peer->account,peer->character)==saved,"Owned bank changed during open projection");const auto live=lookup_(session);require(live&&live->ready&&live->session==peer->session&&live->account==peer->account&&live->character==peer->character&&live->area==peer->area&&live->scene==peer->scene&&permit_(session,target,Clock::now()),"Owned mixed bank opening live world/lease changed");contexts_.insert_or_assign(session,Context{target,*peer,std::move(saved)});return projected;}
OwnedMixedBankService::Result OwnedMixedBankService::handle(std::uint64_t session,std::span<const RecoveredBankItems::Request> requests,Clock::time_point now){
    Result result;try{
        const auto context=contexts_.find(session);const auto peer=lookup_(session);
        require(context!=contexts_.end()&&peer&&peer->ready&&peer->session==session&&requests.size()==1,"Owned foreign bank context/batch missing");
        const auto before=context->second.expected;const auto opened_peer=context->second.peer;const auto& r=requests.front();
        require(peer->account==before.base.bag.account&&peer->character==before.base.bag.character&&peer->area==opened_peer.area&&peer->scene==opened_peer.scene&&r.target==context->second.target&&permit_(session,r.target,now),"Owned foreign bank owner/lease changed");
        require(load_snapshot(peer->account,peer->character)==before,"Owned foreign bank context stale");require(r.page<3,"Owned foreign bank UI page inaccessible");
        const auto flat=[&](std::uint8_t slot){require(slot>=2&&slot<50,"Owned foreign bank reserved cell");return std::size_t{r.page}*50+slot;};
        using K=RecoveredBankItems::Kind;using L=SqliteOwnedForeignBankRepository::ReceiptLedger;
        const StoredInventorySlot* source=nullptr;bool source_armor=false,source_foreign=false,destination_armor=false,destination_foreign=false;
        if(r.kind==K::Deposit){require(r.source<30,"Owned foreign bank source bag invalid");source=&*before.base.bag.scalar[r.source];source_armor=at(before.base.bag.armor,r.source);source_foreign=at(before.base.bag.weapons,r.source)||at(before.base.bag.gems,r.source);destination_armor=at(before.base.armor,flat(r.destination));destination_foreign=at(before.foreign,flat(r.destination));}
        else if(r.kind==K::Withdraw){const auto slot=flat(r.source);require(r.destination<30,"Owned foreign bank destination bag invalid");source=&before.base.vault[slot];source_armor=at(before.base.armor,slot);source_foreign=at(before.foreign,slot);destination_armor=at(before.base.bag.armor,r.destination);destination_foreign=before.base.bag.scalar[r.destination]->count&&(at(before.base.bag.weapons,r.destination)||at(before.base.bag.gems,r.destination));}
        else if(r.kind==K::Move){const auto slot=flat(r.source),destination=flat(r.destination);source=&before.base.vault[slot];source_armor=at(before.base.armor,slot);source_foreign=at(before.foreign,slot);destination_armor=at(before.base.armor,destination);destination_foreign=at(before.foreign,destination);}
        else throw DatabaseError("Owned foreign bank unknown operation");
        require(source->count,"Owned foreign bank empty source");const auto receipt=receipt_();require(!duplicate(receipt),"Owned foreign bank duplicate receipt");Batches projected;Snapshot after=before;
        const auto live_check=[&]{
            require(!beasts_||!beasts_->receipt_exists(receipt,true),"PET bank late ledger collision with old writer");
            const auto live=lookup_(session);
            require(live&&live->ready&&live->session==session&&live->account==opened_peer.account&&live->character==opened_peer.character&&live->area==opened_peer.area&&live->scene==opened_peer.scene&&permit_(session,r.target,Clock::now()),"Owned mixed bank late live lease/world conflict");
        };
        const auto pair_pet=[&](bool vault,std::uint16_t slot)->std::optional<StoredVaultBeast>{
            if(vault){if(const auto* v=at(before.vault_beasts,slot))return *v;}
            else if(const auto* v=pet(before.beasts,slot))return StoredVaultBeast{slot,v->revision,v->bag_revision,v->inventory_metadata,v->panel,v->exploration,v->origin,v->evidence_id};return {};
        };
        const bool source_vault=r.kind!=K::Deposit,destination_vault=r.kind!=K::Withdraw;
        const auto source_pet=pair_pet(source_vault,source_vault?flat(r.source):r.source);
        const auto destination_pet=pair_pet(destination_vault,destination_vault?flat(r.destination):r.destination);
        if(source_pet||destination_pet){
            require(beasts_&&bool(beast_eligible_)&&(!source_pet||beast_eligible_(*source_pet,r))&&(!destination_pet||beast_eligible_(*destination_pet,r)),"PET bank Lua admission rejected");
            const SqliteBeastBankRepository::Request request{before,r};
            auto committed=beasts_->commit(receipt,request,[&](const auto& planned){after=planned.after;projected=synchronization(after,&before,true);},[&](const auto& planned){
                beasts_->verify_snapshot_in_transaction(planned.after);
                const auto live=lookup_(session);require(live&&live->ready&&live->session==session&&live->account==opened_peer.account&&live->character==opened_peer.character&&live->area==opened_peer.area&&live->scene==opened_peer.scene&&permit_(session,r.target,Clock::now()),"PET bank late live world/lease conflict");
            });after=std::move(committed.after);
        }else if(r.kind==K::Move){
            // Native65's final1 is a whole-cell marker, never an amount.
            // The repository's quantity/receipt is authoritative whole custody.
            require(r.quantity==1,"Owned mixed bank native65 marker must be1");
            const SqliteOwnedMixedBankRepository::Request request{before,r.page,r.source,r.destination,source->count};
            auto committed=repo_.commit(receipt,request,[&](const auto& planned){after=before;static_cast<SqliteBeastBankRepository::Base&>(after)=planned.after;projected=synchronization(after,&before,true);},[&](const auto& planned){verify_snapshot(after);live_check();});static_cast<SqliteBeastBankRepository::Base&>(after)=std::move(committed.after);
        }else if(source_foreign){
            require(!source_armor&&!destination_armor,"Owned foreign bank mixed armor transfer unqualified");
            const SqliteOwnedForeignBankRepository::Request request{before,static_cast<SqliteBankItemsRepository::Operation>(r.kind),r.page,r.source,r.destination,r.quantity};
            auto committed=foreign_repo_.commit(receipt,request,[&](const auto& planned){after=before;static_cast<SqliteBeastBankRepository::Base&>(after)=planned.after;projected=synchronization(after,&before,true);},[&](const auto& planned){verify_snapshot(after);require(!foreign_repo_.receipt_exists(receipt,L::Armor)&&!foreign_repo_.receipt_exists(receipt,L::Plain),"Owned foreign bank late cross-ledger receipt conflict");require(!repo_.receipt_exists(receipt,SqliteOwnedMixedBankRepository::ReceiptLedger::Mixed),"Owned mixed bank late0070 ledger collision");live_check();});static_cast<SqliteBeastBankRepository::Base&>(after)=std::move(committed.after);
        }else if(source_armor){
            require(!destination_foreign,"Owned foreign bank mixed armor transfer unqualified");
            const SqliteOwnedArmorBankRepository::Request request{before.base,static_cast<SqliteBankItemsRepository::Operation>(r.kind),r.page,r.source,r.destination,r.quantity};
            // Original armor repository retains its full base prewrite CAS.
            // Foreign metadata is immutable and proved by exact full readback
            // inside that same transaction before COMMIT (not a prewrite hook).
            auto committed=armor_repo_.commit(receipt,request,[&](const auto& planned){after=before;after.base=planned.after;projected=synchronization(after,&before,true);},[&](const auto&){verify_snapshot(after);require(!foreign_repo_.receipt_exists(receipt,L::Foreign)&&!foreign_repo_.receipt_exists(receipt,L::Plain),"Owned foreign bank armor cross-ledger receipt conflict");require(!repo_.receipt_exists(receipt,SqliteOwnedMixedBankRepository::ReceiptLedger::Mixed),"Owned mixed bank armor late0070 collision");live_check();});after.base=std::move(committed.after);
        }else{
            require(!destination_armor&&!destination_foreign&&eligible_(*source),"Owned foreign bank plain/full mixed transfer rejected");
            const SqliteBankItemsRepository::Request request{plain_snapshot(before),static_cast<SqliteBankItemsRepository::Operation>(r.kind),r.page,r.source,r.destination,r.quantity};
            const auto planned=SqliteBankItemsRepository::plan(request);after=before;after.base.vault=planned.vault;
            for(std::uint8_t slot=0;slot<30;++slot)if(*before.base.bag.scalar[slot]!=planned.bag[slot]){after.base.bag.scalar[slot]=planned.bag[slot];std::erase_if(after.base.bag.weapons,[&](const auto& row){return row.slot==slot&&row.origin=="EMPTY_SLOT_POLICY";});}
            projected=synchronization(after,&before,true);
            const SqliteBankItemsRepository::CommitProof proof{[&,before,receipt]{verify_snapshot(before);require(!duplicate(receipt),"Owned foreign bank duplicate receipt before write");},[&,after,receipt]{verify_snapshot(after);require(!foreign_repo_.receipt_exists(receipt,L::Armor)&&!foreign_repo_.receipt_exists(receipt,L::Foreign),"Owned foreign bank MED cross-ledger receipt conflict");require(!repo_.receipt_exists(receipt,SqliteOwnedMixedBankRepository::ReceiptLedger::Mixed),"Owned mixed bank MED late0070 collision");live_check();}};
            plain_repo_.commit(receipt,request,proof);
        }
        // COMMIT has completed. These state/result transfers are statically
        // noexcept; a renewal failure drops context but never reports rollback.
        static_assert(std::is_nothrow_move_assignable_v<Snapshot>);
        static_assert(std::is_nothrow_move_assignable_v<SqliteOwnedArmorBankRepository::Snapshot>);
        static_assert(std::is_nothrow_move_assignable_v<Batches>);
        static_assert(std::is_nothrow_move_constructible_v<Result>);
        context->second.expected=std::move(after);result.batches=std::move(projected);result.committed=true;try{renew_(session,now);}catch(...){contexts_.erase(session);}return result;
    }catch(const std::exception&){result.rejected=true;const auto found=contexts_.find(session);if(found!=contexts_.end()){const auto expected=found->second.expected;const auto found_peer=found->second.peer;contexts_.erase(found);try{const auto live=lookup_(session);if(live&&live->ready&&live->session==session&&live->account==expected.base.bag.account&&live->character==expected.base.bag.character&&live->area==found_peer.area&&live->scene==found_peer.scene)result.batches=synchronization(load_snapshot(live->account,live->character),nullptr,true);}catch(const std::exception&){result.batches.clear();}}return result;}
}
}
