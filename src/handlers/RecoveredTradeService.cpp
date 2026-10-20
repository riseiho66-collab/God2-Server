#include "handlers/RecoveredTradeService.h"
#include "db/DbTypes.h"
#include <algorithm>
#include <type_traits>

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
bool RecoveredTradeService::lease_current(const Context& c) const {
    if(operation_invalid_)return false;
    const auto a=lookup_(c.peers[0].session);if(operation_invalid_)return false;
    const auto b=lookup_(c.peers[1].session);
    if(operation_invalid_ || !a || !b || !compatible(*a,*b))return false;
    for(unsigned n=0;n<2;++n) {
        const auto& live=n==0?*a:*b;const auto& saved=c.peers[n];
        if(live.session!=saved.session || live.account!=saved.account || live.character!=saved.character ||
            live.area!=saved.area || live.scene!=saved.scene)return false;
    }
    return !operation_invalid_ && Clock::now()<c.expires;
}
bool RecoveredTradeService::current(const Context& c) const {
    if(!lease_current(c))return false;
    for(unsigned n=0;n<2;++n)if(repo_.load(c.peers[n].account,c.peers[n].character)!=c.sides[n].expected)return false;
    return !operation_invalid_ && Clock::now()<c.expires;
}
RecoveredTradeService::Deliveries RecoveredTradeService::close_only(const Context& c) {
    Deliveries out;for(const auto& peer:c.peers)if(peer.session)append(out,peer.session,RecoveredTrade::rollback_close());return out;
}
RecoveredTradeService::Deliveries RecoveredTradeService::restore(const Context& c) const {
    if(operation_invalid_)return close_only(c);
    Deliveries out;
    for(const auto& peer:c.peers) {
        if(!peer.session)continue;
        const auto live=lookup_(peer.session);if(operation_invalid_)return close_only(c);
        if(!live || !live->ready || live->session!=peer.session || live->account!=peer.account || live->character!=peer.character)continue;
        const auto saved=repo_.load(peer.account,peer.character);if(operation_invalid_)return close_only(c);
        append(out,peer.session,RecoveredTrade::rollback_close());
        for(std::uint8_t slot=0;slot<30;++slot){const auto bytes=project(peer.account,peer.character,slot,saved.bag[slot],saved.bag[slot]);if(operation_invalid_)return close_only(c);append(out,peer.session,bytes);}
        append(out,peer.session,RecoveredTrade::wallet(saved.wallet.amount));
        const auto current=lookup_(peer.session);if(operation_invalid_)return close_only(c);
        if(!current || !current->ready || current->session!=peer.session || current->account!=peer.account || current->character!=peer.character)out.erase(peer.session);
    }
    return out;
}
RecoveredTradeService::Deliveries RecoveredTradeService::disconnect(std::uint64_t session) {
    Operation operation(*this);if(!operation)return {};return disconnect_impl(session);
}
RecoveredTradeService::Deliveries RecoveredTradeService::disconnect_impl(std::uint64_t session) {
    const auto at=find(session);if(at==contexts_.end())return {};
    // Drop the ephemeral context even if an unrepresentable current slot blocks
    // restoration. The next login still projects canonical storage.
    static_assert(std::is_nothrow_move_constructible_v<Context>);
    auto context=std::move(at->second);contexts_.erase(at);return restore(context);
}
RecoveredTradeService::Deliveries RecoveredTradeService::refresh(Clock::time_point now) {
    Operation operation(*this);if(!operation)return {};
    Deliveries out;
    for(auto at=contexts_.begin();at!=contexts_.end();) {
        bool valid=false;try{valid=now<at->second.expires && current(at->second);}catch(...){valid=false;}
        if(valid){++at;continue;}
        static_assert(std::is_nothrow_move_constructible_v<Context>);
        auto context=std::move(at->second);at=contexts_.erase(at);
        const auto restored=restore(context);for(const auto& [id,bytes]:restored)append(out,id,bytes);
        if(operation_invalid_)break;
    }
    if(operation_invalid_)for(auto& [id,bytes]:out)bytes=RecoveredTrade::rollback_close();
    return out;
}
RecoveredTradeService::Result RecoveredTradeService::handle(std::uint64_t session,
    std::span<const RecoveredTrade::Request> requests,Clock::time_point now) {
    Result result;
    Operation operation(*this);if(!operation){result.rejected=true;return result;}
    const auto reject=[&]() {
        result.rejected=true;
        try {
        if(active(session))result.deliveries=disconnect_impl(session);
        else if(operation_invalid_)append(result.deliveries,session,RecoveredTrade::rollback_close());
        else if(const auto peer=lookup_(session);operation_invalid_)append(result.deliveries,session,RecoveredTrade::rollback_close());
        else if(peer && peer->ready && peer->session==session){Context context{};context.peers[0]=*peer;result.deliveries=restore(context);}
        }catch(...){result.deliveries.clear();}
        return result;
    };
    using K=RecoveredTrade::Kind;
    if(requests.empty() || requests.size()>2 || (requests.size()==2 &&
        (requests[0].kind!=K::OfferMoney || requests[1].kind!=K::Confirm)))return reject();
    try {
        const std::vector<RecoveredTrade::Request> owned_requests(requests.begin(),requests.end());
        requests=std::span<const RecoveredTrade::Request>(owned_requests);
        auto at=find(session);
        if(requests.front().kind==K::Open) {
            require(!active(session),"Trade participant busy");
            const auto own=lookup_(session),peer=resolve_(requests.front().target);
            require(own && peer && own->session==session && peer->character==requests.front().target &&
                compatible(*own,*peer) && !active(peer->session),"Trade peer unavailable");
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
            require(lease_current(context),"Trade opening retired original peers/operation");
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
        require(lease_current(next),"Trade adapter retired original operation/peers");
        next.expires=now+std::chrono::seconds(60);
        if(next.confirmed[0] && next.confirmed[1]) {
            const auto planned=SqliteTradeRepository::plan(next.sides);
            auto proof=repo_.prepare_proof({next.sides[0].expected,next.sides[1].expected},planned,proof_);
            require(!owned_projection_||(bool(proof.before_write)&&bool(proof.after_write)),"Owned trade projection requires transaction proof");
            // Serialize both complete authoritative replies before any write.
            for(unsigned n=0;n<2;++n) {
                append(result.deliveries,next.peers[n].session,RecoveredTrade::close_without_refund());
                for(std::uint8_t slot=0;slot<30;++slot)append(result.deliveries,next.peers[n].session,project(next.peers[n].account,next.peers[n].character,slot,next.sides[n].expected.bag[slot],planned.sides[n].bag[slot]));
                append(result.deliveries,next.peers[n].session,RecoveredTrade::wallet(planned.sides[n].wallet.amount));
            }
            const auto receipt=receipt_();
            require(lease_current(next),"Trade receipt/projection retired original operation/peers");
            // Retain the original full-owner proofs and add the same pure live
            // operation fence on BOTH sides of SQL writes. Never compare the
            // old saved bag against a deliberately staged next bag here.
            proof.before_write=[&,original=std::move(proof.before_write)]{
                require(lease_current(next),"Trade prewrite operation/lease retired");
                if(original)original();
                require(lease_current(next),"Trade prewrite proof retired operation/lease");
            };
            proof.after_write=[&,original=std::move(proof.after_write)]{
                require(lease_current(next),"Trade postwrite operation/lease retired");
                if(original)original();
                require(lease_current(next),"Trade postwrite proof retired operation/lease");
            };
            proof.current=[&,original=std::move(proof.current)]{
                if(operation_invalid_||Clock::now()>=next.expires)return false;
                const bool current=!original||original();
                return current&&!operation_invalid_&&Clock::now()<next.expires;
            };
            repo_.commit(receipt,next.sides,proof);
            contexts_.erase(at);result.committed=true;
            if(operation_invalid_)result.deliveries.clear(); // Durable COMMIT is never relabelled as rollback.
        } else at->second=std::move(next);
        return result;
    }catch(const DatabaseError&) {
        result.deliveries.clear();return reject();
    }catch(const LegacyCoinProjectionError&) {
        // Prepared legacy replies cannot represent the exact shared balance.
        // No settlement may be committed and no truncated refund is sent.
        result.deliveries.clear();return reject();
    }catch(...) {
        result.deliveries.clear();return reject();
    }
}
}
