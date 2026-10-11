#include "handlers/RecoveredTradeService.h"
#include "db/DbTypes.h"
#include <algorithm>

namespace god2 {
namespace {
void require(bool valid,const char* reason){if(!valid)throw DatabaseError(reason);}
}
bool RecoveredTradeService::compatible(const Peer& a,const Peer& b) {
    return a.ready && b.ready && a.session && b.session && a.session!=b.session &&
        a.account && b.account && a.character && b.character && a.character!=b.character &&
        a.character<=0x3fff && b.character<=0x3fff && a.area==b.area && a.scene==b.scene;
}
std::vector<std::uint8_t> RecoveredTradeService::project(std::uint64_t account,std::uint64_t character,std::uint8_t slot,const StoredInventorySlot& before,const StoredInventorySlot& after) const {
    return owned_projection_?owned_projection_(account,character,slot,before,after):projection_(slot,after);
}
void RecoveredTradeService::append(Deliveries& out,std::uint64_t session,const std::vector<std::uint8_t>& b) {
    auto& bytes=out[session];bytes.insert(bytes.end(),b.begin(),b.end());
}
RecoveredTradeService::Contexts::iterator RecoveredTradeService::find(std::uint64_t session) {
    return std::find_if(contexts_.begin(),contexts_.end(),[&](const auto& value){
        return value.second.peers[0].session==session || value.second.peers[1].session==session;});
}
bool RecoveredTradeService::active(std::uint64_t session) const {
    return std::any_of(contexts_.begin(),contexts_.end(),[&](const auto& value){
        return value.second.peers[0].session==session || value.second.peers[1].session==session;});
}
bool RecoveredTradeService::current(const Context& c) const {
    const auto a=lookup_(c.peers[0].session),b=lookup_(c.peers[1].session);
    if(!a || !b || !compatible(*a,*b))return false;
    for(unsigned n=0;n<2;++n) {
        const auto& live=n==0?*a:*b;const auto& saved=c.peers[n];
        if(live.account!=saved.account || live.character!=saved.character || live.area!=saved.area || live.scene!=saved.scene ||
            repo_.load(saved.account,saved.character)!=c.sides[n].expected)return false;
    }
    return true;
}
RecoveredTradeService::Deliveries RecoveredTradeService::restore(const Context& c) const {
    Deliveries out;
    for(const auto& peer:c.peers) {
        const auto live=lookup_(peer.session);
        if(!live || !live->ready || live->account!=peer.account || live->character!=peer.character)continue;
        const auto saved=repo_.load(peer.account,peer.character);
        // Native4F refunds only local money. Absolute slots and purse afterwards
        // restore committed state, including unrelated authorized save changes.
        append(out,peer.session,RecoveredTrade::rollback_close());
        for(std::uint8_t slot=0;slot<30;++slot)append(out,peer.session,project(peer.account,peer.character,slot,saved.bag[slot],saved.bag[slot]));
        append(out,peer.session,RecoveredTrade::wallet(saved.wallet.amount));
    }
    return out;
}
RecoveredTradeService::Deliveries RecoveredTradeService::disconnect(std::uint64_t session) {
    const auto at=find(session);if(at==contexts_.end())return {};
    // Drop the ephemeral context even if an unrepresentable current slot blocks
    // restoration. The next login still projects canonical storage.
    const auto context=at->second;contexts_.erase(at);return restore(context);
}
RecoveredTradeService::Deliveries RecoveredTradeService::refresh(Clock::time_point now) {
    Deliveries out;
    for(auto at=contexts_.begin();at!=contexts_.end();) {
        bool valid=false;try{valid=now<at->second.expires && current(at->second);}catch(const DatabaseError&){valid=false;}
        if(valid){++at;continue;}
        const auto context=at->second;at=contexts_.erase(at);
        const auto restored=restore(context);for(const auto& [id,bytes]:restored)append(out,id,bytes);
    }
    return out;
}
RecoveredTradeService::Result RecoveredTradeService::handle(std::uint64_t session,
    std::span<const RecoveredTrade::Request> requests,Clock::time_point now) {
    Result result;
    const auto reject=[&]() {
        result.rejected=true;
        try {
        if(active(session))result.deliveries=disconnect(session);
        else if(const auto peer=lookup_(session);peer && peer->ready) {
            const auto saved=repo_.load(peer->account,peer->character);
            append(result.deliveries,session,RecoveredTrade::rollback_close());
            for(std::uint8_t slot=0;slot<30;++slot)append(result.deliveries,session,project(peer->account,peer->character,slot,saved.bag[slot],saved.bag[slot]));
            append(result.deliveries,session,RecoveredTrade::wallet(saved.wallet.amount));
        }
        }catch(const LegacyCoinProjectionError&){result.deliveries.clear();}
        return result;
    };
    using K=RecoveredTrade::Kind;
    if(requests.empty() || requests.size()>2 || (requests.size()==2 &&
        (requests[0].kind!=K::OfferMoney || requests[1].kind!=K::Confirm)))return reject();
    try {
        auto at=find(session);
        if(requests.front().kind==K::Open) {
            require(!active(session),"Trade participant busy");
            const auto own=lookup_(session),peer=resolve_(requests.front().target);
            require(own && peer && compatible(*own,*peer) && !active(peer->session),"Trade peer unavailable");
            Context context{{*own,*peer},{},{},{},now+std::chrono::seconds(60)};
            for(unsigned n=0;n<2;++n) {
                context.sides[n].expected=repo_.load(context.peers[n].account,context.peers[n].character);
                for(std::uint8_t slot=0;slot<30;++slot)project(context.peers[n].account,context.peers[n].character,slot,context.sides[n].expected.bag[slot],context.sides[n].expected.bag[slot]);
            }
            // Prepare both native name projections before publishing context.
            for(unsigned n=0;n<2;++n) {
                append(result.deliveries,context.peers[n].session,RecoveredTrade::open(
                    static_cast<std::uint16_t>(context.peers[1-n].character),name_(context.peers[n],context.peers[1-n])));
                append(result.deliveries,context.peers[n].session,RecoveredTrade::wallet(context.sides[n].expected.wallet.amount));
            }
            contexts_.emplace(session,std::move(context));return result;
        }
        require(at!=contexts_.end(),"Trade context absent");
        auto next=at->second;
        require(now<next.expires && current(next),"Trade lease/snapshot expired");
        const unsigned own=next.peers[0].session==session?0:1,peer=1-own;
        for(const auto& r:requests) {
            if(r.kind==K::Cancel) {
                require(r.control==0,"Unknown trade cancel control");
                result.deliveries=restore(next);contexts_.erase(at);return result;
            }
            require(!next.confirmed[own],"Confirmed trade cannot change");
            if(r.kind==K::OfferItem) {
                require(r.target==next.peers[peer].character && r.slot<30 && r.quantity && next.sides[own].items.size()<8,
                    "Trade item target/slot/cap invalid");
                const auto& source=next.sides[own].expected.bag[r.slot];
                require(source.item_id==r.item && r.quantity<=source.count && eligible_(source) &&
                    std::none_of(next.sides[own].items.begin(),next.sides[own].items.end(),[&](const auto& item){return item.slot==r.slot;}),
                    "Trade item ownership/quantity/eligibility invalid");
                const auto index=static_cast<std::uint8_t>(next.sides[own].items.size());
                next.sides[own].items.push_back({r.slot,r.quantity});
                RecoveredTrade::Item item{};item[0]=r.quantity;item[1]=index;
                item[4]=static_cast<std::uint8_t>(source.item_id);item[5]=static_cast<std::uint8_t>(source.item_id>>8);
                append(result.deliveries,next.peers[peer].session,*RecoveredTrade::peer_item(item));
            } else if(r.kind==K::OfferMoney) {
                require(!next.money_submitted[own] && r.target==next.peers[peer].character && r.money<=next.sides[own].expected.wallet.amount,
                    "Trade money target/balance/repetition invalid");
                next.sides[own].money=r.money;next.money_submitted[own]=true;
                append(result.deliveries,next.peers[peer].session,RecoveredTrade::peer_money(r.money));
            } else if(r.kind==K::Confirm) {
                require(r.control==0,"Unknown trade confirm control");next.confirmed[own]=true;
                append(result.deliveries,next.peers[peer].session,RecoveredTrade::peer_confirmation(1));
            } else throw DatabaseError("Invalid trade state operation");
        }
        next.expires=now+std::chrono::seconds(60);
        if(next.confirmed[0] && next.confirmed[1]) {
            const auto planned=SqliteTradeRepository::plan(next.sides);
            const auto proof=repo_.prepare_proof({next.sides[0].expected,next.sides[1].expected},planned,proof_);
            require(!owned_projection_||(bool(proof.before_write)&&bool(proof.after_write)),"Owned trade projection requires transaction proof");
            // Serialize both complete authoritative replies before any write.
            for(unsigned n=0;n<2;++n) {
                append(result.deliveries,next.peers[n].session,RecoveredTrade::close_without_refund());
                for(std::uint8_t slot=0;slot<30;++slot)append(result.deliveries,next.peers[n].session,project(next.peers[n].account,next.peers[n].character,slot,next.sides[n].expected.bag[slot],planned.sides[n].bag[slot]));
                append(result.deliveries,next.peers[n].session,RecoveredTrade::wallet(planned.sides[n].wallet.amount));
            }
            const auto receipt=receipt_();repo_.commit(receipt,next.sides,proof);
            contexts_.erase(at);result.committed=true;
        } else at->second=std::move(next);
        return result;
    }catch(const DatabaseError&) {
        result.deliveries.clear();return reject();
    }catch(const LegacyCoinProjectionError&) {
        // Prepared legacy replies cannot represent the exact shared balance.
        // No settlement may be committed and no truncated refund is sent.
        result.deliveries.clear();return reject();
    }
}
}
