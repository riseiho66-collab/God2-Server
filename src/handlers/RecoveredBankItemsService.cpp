#include "handlers/RecoveredBankItemsService.h"
#include "db/DbTypes.h"
#include "protocol/RecoveredWorldFrame.h"
#include <type_traits>
namespace god2 {
namespace {void require(bool yes,const char* reason){if(!yes)throw DatabaseError(reason);}}
void RecoveredBankItemsService::append(Batches& batches,std::span<const std::uint8_t> logical) {
    require(!logical.empty() && logical.size()<=RecoveredWorldFrame::max_logical_size,"Bank item projection exceeds frame");
    if(batches.empty() || batches.back().size()+logical.size()>RecoveredWorldFrame::max_logical_size)batches.emplace_back();
    batches.back().insert(batches.back().end(),logical.begin(),logical.end());
}
std::array<std::uint8_t,29> RecoveredBankItemsService::bank_slot(std::size_t flat,const StoredInventorySlot& slot) const {
    require(flat<300 && (!slot.count || (flat%50>=2 && eligible_(slot))),"Unqualified scalar bank slot");
    callbacks_.require_current();
    RecoveredInventoryProjection::Metadata metadata{};
    metadata[0]=static_cast<std::uint8_t>(slot.item_id);metadata[1]=static_cast<std::uint8_t>(slot.item_id>>8);
    const auto out=RecoveredBankItems::slot(static_cast<std::uint8_t>(flat/50),static_cast<std::uint8_t>(flat%50),slot.count,metadata);
    require(out.has_value(),"Native bank slot serialization rejected");return *out;
}
RecoveredBankItemsService::Batches RecoveredBankItemsService::synchronization(
    const SqliteBankItemsRepository::Snapshot& saved,const SqliteBankItemsRepository::Snapshot* before,bool bags) const {
    Batches out;
    // Bank native48 absolute replacement restores all metadata, including
    // locally swapped cells. Do not infer fields from cached client records.
    for(std::size_t flat=0;flat<300;++flat)if(!before || saved.vault[flat]!=before->vault[flat])append(out,bank_slot(flat,saved.vault[flat]));
    if(bags)for(std::uint8_t slot=0;slot<30;++slot)if(!before || saved.bag[slot]!=before->bag[slot]) {
        append(out,owned_projection_?owned_projection_(saved.account,saved.character,slot,before?before->bag[slot]:saved.bag[slot],saved.bag[slot]):projection_(slot,saved.bag[slot]));
        callbacks_.require_current();
    }
    return out;
}
RecoveredBankItemsService::Batches RecoveredBankItemsService::open(std::uint64_t session,std::uint16_t target,Clock::time_point now) {
    auto operation=callbacks_.enter();
    try {
        const auto peer=lookup_(session);callbacks_.require_current();
        require(peer && peer->ready && peer->session==session && session && peer->account && peer->character,
            "Bank item opening has no current owner");
        const bool permitted=permit_(session,target,now);callbacks_.require_current();
        require(permitted,"Bank item opening has no qualified lease");
        repo_.provision_empty(peer->account,peer->character,[&]{callbacks_.require_current();});
        callbacks_.require_current();
        auto saved=repo_.load(peer->account,peer->character);callbacks_.require_current();
        auto projected=synchronization(saved,nullptr,false);
        require(repo_.load(peer->account,peer->character)==saved,"Bank item opening snapshot changed");callbacks_.require_current();
        const bool still_permitted=permit_(session,target,now);callbacks_.require_current();
        require(still_permitted,"Bank item opening lease revoked");
        const auto live=lookup_(session);callbacks_.require_current();
        require(live && live->ready && live->session==session && live->account==peer->account &&
            live->character==peer->character && live->area==peer->area && live->scene==peer->scene,
            "Bank item opening owner changed");
        contexts_.insert_or_assign(session,Context{target,*peer,std::move(saved)});return projected;
    }catch(...) {contexts_.erase(session);throw;}
}
RecoveredBankItemsService::Result RecoveredBankItemsService::handle(std::uint64_t session,
    std::span<const RecoveredBankItems::Request> requests,Clock::time_point now) {
    auto operation=callbacks_.enter();
    Result result;
    try {
        const auto at=contexts_.find(session);
        require(at!=contexts_.end() && requests.size()==1,"Bank item lease/batch missing");
        // Both copies precede lookup/permit/projection. No borrowed iterator,
        // request span or slot can be destroyed by a synchronous adapter.
        const auto context=at->second;const auto r=requests.front();
        const auto peer=lookup_(session);callbacks_.require_current();
        require(peer && peer->ready && peer->session==session && session &&
            peer->account==context.expected.account && peer->character==context.expected.character &&
            peer->area==context.peer.area && peer->scene==context.peer.scene &&
            r.target==context.target,"Bank item owner changed");
        const bool permitted=permit_(session,r.target,now);callbacks_.require_current();
        require(permitted,"Bank item access/expiry changed");
        require(repo_.load(peer->account,peer->character)==context.expected,"Bank item snapshot changed");
        callbacks_.require_current();
        // Native next-page control wraps at2 or3 pages depending on232F64.
        require(r.page<3,"Bank item page not reachable by native UI");
        const auto flat=[&](std::uint8_t slot){require(slot>=2 && slot<50,"Special/reserved bank item slot");return std::size_t{r.page}*50+slot;};
        const StoredInventorySlot* source=nullptr;
        using K=RecoveredBankItems::Kind;
        if(r.kind==K::Deposit){require(r.source<30,"Bank deposit bag slot invalid");source=&context.expected.bag[r.source];flat(r.destination);}
        else if(r.kind==K::Withdraw){source=&context.expected.vault[flat(r.source)];require(r.destination<30,"Bank withdraw bag slot invalid");}
        else if(r.kind==K::Move){
            source=&context.expected.vault[flat(r.source)];
            const auto& destination=context.expected.vault[flat(r.destination)];
            require(!destination.count || eligible_(destination),"Bank swap destination category unqualified");
            callbacks_.require_current();
        }
        else throw DatabaseError("Unknown bank item operation");
        require(source->count && eligible_(*source),"Bank item source category unqualified");
        callbacks_.require_current();
        const SqliteBankItemsRepository::Request proposal{context.expected,
            static_cast<SqliteBankItemsRepository::Operation>(static_cast<std::uint8_t>(r.kind)),r.page,r.source,r.destination,r.quantity};
        const auto next=SqliteBankItemsRepository::plan(proposal);
        const auto prepared=repo_.prepare_proof(context.expected,next,proof_);callbacks_.require_current();
        require(!owned_projection_||(bool(prepared.before_write)&&bool(prepared.after_write)),"Owned bank projection requires transaction proof");
        auto projected=synchronization(next,&context.expected,true);
        const auto owner_current=[&] {
            callbacks_.require_current();const auto live=lookup_(session);callbacks_.require_current();
            require(live && live->ready && live->session==session && live->account==peer->account &&
                live->character==peer->character && live->area==peer->area && live->scene==peer->scene,
                "Bank item commit owner changed");
            const bool access=permit_(session,r.target,now);callbacks_.require_current();
            require(access,"Bank item commit lease revoked");
        };
        const SqliteBankItemsRepository::CommitProof proof{
            [&,check=prepared.before_write]{owner_current();if(check)check();callbacks_.require_current();},
            [&,check=prepared.after_write]{if(check)check();owner_current();},
            [&,check=prepared.current]{callbacks_.require_current();if(check)check();callbacks_.require_current();}};
        const auto receipt=receipt_();callbacks_.require_current();
        auto committed=repo_.commit(receipt,proposal,proof);
        // COMMIT is the durable boundary. Renewal failure must not describe a
        // persisted transfer as rejected or invite a stale-snapshot retry.
        static_assert(std::is_nothrow_move_assignable_v<SqliteBankItemsRepository::Snapshot>);
        static_assert(std::is_nothrow_move_constructible_v<Result>);
        result.batches=std::move(projected);result.committed=true;
        if(callbacks_.invalidated()){contexts_.erase(session);result.batches.clear();return result;}
        if(const auto live=contexts_.find(session);live!=contexts_.end())live->second.expected=std::move(committed);
        try {renew_(session,now);if(callbacks_.invalidated()){contexts_.erase(session);result.batches.clear();}}
        catch(...){contexts_.erase(session);if(callbacks_.invalidated())result.batches.clear();}
        return result;
    }catch(const DatabaseError&) {
        result.rejected=true;
        if(callbacks_.invalidated()){contexts_.erase(session);return result;}
        // Rejection synchronization never reopens or renews a lease. Copy and
        // retire before callbacks, and suppress output after any revocation.
        const auto at=contexts_.find(session);
        if(at!=contexts_.end()) {
            static_assert(std::is_nothrow_move_constructible_v<Context>);
            const auto context=std::move(at->second);contexts_.erase(at);
            try {
                const auto live=lookup_(session);callbacks_.require_current();
                if(live && live->ready && live->session==session && live->account==context.expected.account && live->character==context.expected.character &&
                    live->area==context.peer.area && live->scene==context.peer.scene) {
                    const auto saved=repo_.load(live->account,live->character);callbacks_.require_current();
                    result.batches=synchronization(saved,nullptr,true);
                }
            }catch(...){result.batches.clear();}
        }
        return result;
    }catch(...){contexts_.erase(session);throw;}
}
}
