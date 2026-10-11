#include "handlers/RecoveredBankItemsService.h"
#include "db/DbTypes.h"
#include "protocol/RecoveredWorldFrame.h"
namespace god2 {
namespace {void require(bool yes,const char* reason){if(!yes)throw DatabaseError(reason);}}
void RecoveredBankItemsService::append(Batches& batches,std::span<const std::uint8_t> logical) {
    require(!logical.empty() && logical.size()<=RecoveredWorldFrame::max_logical_size,"Bank item projection exceeds frame");
    if(batches.empty() || batches.back().size()+logical.size()>RecoveredWorldFrame::max_logical_size)batches.emplace_back();
    batches.back().insert(batches.back().end(),logical.begin(),logical.end());
}
std::array<std::uint8_t,29> RecoveredBankItemsService::bank_slot(std::size_t flat,const StoredInventorySlot& slot) const {
    require(flat<300 && (!slot.count || (flat%50>=2 && eligible_(slot))),"Unqualified scalar bank slot");
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
    if(bags)for(std::uint8_t slot=0;slot<30;++slot)if(!before || saved.bag[slot]!=before->bag[slot])append(out,owned_projection_?owned_projection_(saved.account,saved.character,slot,before?before->bag[slot]:saved.bag[slot],saved.bag[slot]):projection_(slot,saved.bag[slot]));
    return out;
}
RecoveredBankItemsService::Batches RecoveredBankItemsService::open(std::uint64_t session,std::uint16_t target,Clock::time_point now) {
    const auto peer=lookup_(session);
    require(peer && peer->ready && permit_(session,target,now),"Bank item opening has no qualified lease");
    repo_.provision_empty(peer->account,peer->character);
    auto saved=repo_.load(peer->account,peer->character);
    auto projected=synchronization(saved,nullptr,false);
    contexts_.insert_or_assign(session,Context{target,std::move(saved)});return projected;
}
RecoveredBankItemsService::Result RecoveredBankItemsService::handle(std::uint64_t session,
    std::span<const RecoveredBankItems::Request> requests,Clock::time_point now) {
    Result result;
    try {
        const auto at=contexts_.find(session);const auto peer=lookup_(session);
        require(at!=contexts_.end() && peer && peer->ready && requests.size()==1,"Bank item lease/batch missing");
        const auto& context=at->second;const auto& r=requests.front();
        require(peer->account==context.expected.account && peer->character==context.expected.character &&
            r.target==context.target && permit_(session,r.target,now),"Bank item owner/access/expiry changed");
        require(repo_.load(peer->account,peer->character)==context.expected,"Bank item snapshot changed");
        // Native next-page control wraps at2 or3 pages depending on232F64.
        // Six allocated cache pages are not six independently unlocked pages.
        require(r.page<3,"Bank item page not reachable by native UI");
        const auto flat=[&](std::uint8_t slot){require(slot>=2 && slot<50,"Special/reserved bank item slot");return std::size_t{r.page}*50+slot;};
        const StoredInventorySlot* source=nullptr;
        using K=RecoveredBankItems::Kind;
        if(r.kind==K::Deposit){require(r.source<30,"Bank deposit bag slot invalid");source=&context.expected.bag[r.source];flat(r.destination);}
        else if(r.kind==K::Withdraw){source=&context.expected.vault[flat(r.source)];require(r.destination<30,"Bank withdraw bag slot invalid");}
        else if(r.kind==K::Move){
            source=&context.expected.vault[flat(r.source)];
            const auto& destination=context.expected.vault[flat(r.destination)];
            // Native65 exchanges complete cells. Both occupied cells must be
            // independently qualified; an eligible source cannot launder an
            // unsupported destination into another physical slot.
            require(!destination.count || eligible_(destination),"Bank swap destination category unqualified");
        }
        else throw DatabaseError("Unknown bank item operation");
        require(source->count && eligible_(*source),"Bank item source category unqualified");
        const SqliteBankItemsRepository::Request proposal{context.expected,
            static_cast<SqliteBankItemsRepository::Operation>(static_cast<std::uint8_t>(r.kind)),r.page,r.source,r.destination,r.quantity};
        const auto next=SqliteBankItemsRepository::plan(proposal);
        const auto proof=repo_.prepare_proof(context.expected,next,proof_);
        require(!owned_projection_||(bool(proof.before_write)&&bool(proof.after_write)),"Owned bank projection requires transaction proof");
        auto projected=synchronization(next,&context.expected,true);
        // Allocate/hash/render all response data before changing either cell.
        auto committed=repo_.commit(receipt_(),proposal,proof);
        at->second.expected=std::move(committed);renew_(session,now);
        result.batches=std::move(projected);result.committed=true;return result;
    }catch(const DatabaseError&) {
        result.rejected=true;
        // Existing authenticated ready peers get saved absolute cells, even
        // after their local65 whole-cell swap. This grants no bank lease.
        const auto at=contexts_.find(session);
        if(at!=contexts_.end()) {
            const auto context=at->second;contexts_.erase(at);
            if(const auto live=lookup_(session);live && live->ready && live->account==context.expected.account && live->character==context.expected.character)
                result.batches=synchronization(repo_.load(live->account,live->character),nullptr,true);
        }
        return result;
    }
}
}
