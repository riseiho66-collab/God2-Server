#include "handlers/OwnedInstanceTradeService.h"
#include "db/DbTypes.h"
#include <algorithm>
#include <exception>

namespace god2 {
namespace {
void require(bool ok,const char* why){if(!ok)throw DatabaseError(why);}
template<class T>const T* at(const std::vector<T>& rows,std::uint8_t slot){const auto found=std::find_if(rows.begin(),rows.end(),[&](const auto& row){return row.slot==slot;});return found==rows.end()?nullptr:&*found;}
const StoredBeastSnapshot* beast_at(const std::vector<StoredBeastSnapshot>& rows,std::uint8_t slot){const auto found=std::find_if(rows.begin(),rows.end(),[&](const auto& row){return row.inventory_slot==slot;});return found==rows.end()?nullptr:&*found;}
void retire_beast_presentation(RecoveredTradeService::Deliveries& out,std::uint64_t session,const SqliteOwnedInstanceTradeRepository::Snapshot& saved){
    if(saved.beast_scope){auto& bytes=out[session];bytes.insert(bytes.end(),{0x4b,0,0});}
    // CUSTOM0085: the next full-bag projection starts with41 slot0 clear,
    // so rebinding85ABD to0 closes the current beast UI independently of its
    // old logical selection. No persisted selection or activity is created.
}
}
OwnedInstanceTradeService::OwnedInstanceTradeService(Repo& repo,Lookup lookup,Resolve resolve,Name name,Eligible eligible,PlainProjection plain,Receipt receipt,EligibleBeast beast_eligible)
    :repo_(repo),lookup_(std::move(lookup)),resolve_(std::move(resolve)),name_(std::move(name)),eligible_(std::move(eligible)),plain_(std::move(plain)),receipt_(std::move(receipt)),beast_eligible_(std::move(beast_eligible)){
    require(bool(lookup_)&&bool(resolve_)&&bool(name_)&&bool(eligible_)&&bool(plain_)&&bool(receipt_),"Owned trade requires qualified adapters");
}
bool OwnedInstanceTradeService::compatible(const Peer& a,const Peer& b){
    return a.ready&&b.ready&&a.session&&b.session&&a.session!=b.session&&a.account&&b.account&&a.character&&b.character&&a.character!=b.character&&a.character<=0x3fff&&b.character<=0x3fff&&a.area==b.area&&a.scene==b.scene;
}
void OwnedInstanceTradeService::append(Deliveries& out,std::uint64_t session,const std::vector<std::uint8_t>& bytes){auto& target=out[session];target.insert(target.end(),bytes.begin(),bytes.end());}
OwnedInstanceTradeService::Contexts::iterator OwnedInstanceTradeService::find(std::uint64_t session){return std::find_if(contexts_.begin(),contexts_.end(),[&](const auto& value){return value.second.peers[0].session==session||value.second.peers[1].session==session;});}
bool OwnedInstanceTradeService::active(std::uint64_t session) const{return std::any_of(contexts_.begin(),contexts_.end(),[&](const auto& value){return value.second.peers[0].session==session||value.second.peers[1].session==session;});}
bool OwnedInstanceTradeService::lease_current(const Context& context) const{
    const auto a=lookup_(context.peers[0].session),b=lookup_(context.peers[1].session);
    if(!a||!b||!compatible(*a,*b))return false;
    for(unsigned n=0;n<2;++n){const auto& live=n==0?*a:*b;const auto& saved=context.peers[n];
        if(live.session!=saved.session||live.account!=saved.account||live.character!=saved.character||live.area!=saved.area||live.scene!=saved.scene)return false;}
    return true;
}
bool OwnedInstanceTradeService::current(const Context& context) const{
    if(!lease_current(context))return false;
    for(unsigned n=0;n<2;++n)if(repo_.load(context.peers[n].account,context.peers[n].character)!=context.sides[n].expected)return false;
    return true;
}
bool OwnedInstanceTradeService::whole(const Repo::Snapshot& saved,std::uint8_t slot){
    require(slot<30&&saved.bag.scalar[slot],"Owned trade ordinary scalar absent");
    return saved.bag.scalar[slot]->count&&(at(saved.bag.armor,slot)||at(saved.bag.weapons,slot)||at(saved.bag.gems,slot)||beast_at(saved.beasts,slot));
}
RecoveredInventoryProjection::Metadata OwnedInstanceTradeService::metadata(const Repo::Snapshot& saved,std::uint8_t slot){
    require(slot<30&&saved.bag.scalar[slot],"Owned trade projection ordinary scalar absent");
    const auto& scalar=*saved.bag.scalar[slot];RecoveredInventoryProjection::Metadata bytes{};
    const auto* armor=at(saved.bag.armor,slot);const auto* weapon=at(saved.bag.weapons,slot);const auto* gem=at(saved.bag.gems,slot);
    const auto* beast=beast_at(saved.beasts,slot);
    require(unsigned(bool(armor))+unsigned(bool(weapon))+unsigned(bool(gem))+unsigned(bool(beast))<=1,"Owned trade metadata domain collision");
    if(armor)bytes=armor->logical20;else if(weapon)bytes=weapon->logical20;else if(gem)bytes=gem->logical20;else if(beast)bytes=beast->inventory_metadata;
    else {bytes[0]=static_cast<std::uint8_t>(scalar.item_id);bytes[1]=static_cast<std::uint8_t>(scalar.item_id>>8);}
    require(static_cast<std::uint16_t>(bytes[0]|(std::uint16_t{bytes[1]}<<8))==scalar.item_id,"Owned trade metadata key mismatch");
    if((armor||gem||beast)||(weapon&&scalar.count))require(scalar.count==1,"Owned trade instance not whole");
    return bytes;
}
std::vector<std::uint8_t> OwnedInstanceTradeService::project(const Repo::Snapshot& saved,std::uint8_t slot) const{
    require(slot<30&&saved.bag.scalar[slot],"Owned trade projection ordinary scalar absent");
    if(!saved.bag.scalar[slot]->count){const auto clear=RecoveredInventory::clear_slot(slot);require(clear.has_value(),"Owned trade canonical empty clear failed");return {clear->begin(),clear->end()};}
    const auto bytes=metadata(saved,slot);const auto& scalar=*saved.bag.scalar[slot];
    const auto encoded=RecoveredInventoryProjection::encode({slot,scalar.count,bytes});require(encoded.has_value(),"Owned trade bag projection failed");
    if(!at(saved.bag.armor,slot)&&!at(saved.bag.weapons,slot)&&!at(saved.bag.gems,slot)&&!beast_at(saved.beasts,slot))require(plain_(slot,scalar)==*encoded,"Owned trade plain projection must be canonical");
    return *encoded;
}
OwnedInstanceTradeService::Deliveries OwnedInstanceTradeService::restore(const Context& context) const{
    Deliveries out;
    for(const auto& peer:context.peers){const auto live=lookup_(peer.session);if(!live||!live->ready||live->session!=peer.session||live->account!=peer.account||live->character!=peer.character)continue;
        const auto saved=repo_.load(peer.account,peer.character);append(out,peer.session,RecoveredTrade::rollback_close());
        retire_beast_presentation(out,peer.session,saved);
        for(std::uint8_t slot=0;slot<30;++slot)append(out,peer.session,project(saved,slot));
        append(out,peer.session,RecoveredTrade::wallet(saved.wallet.amount));}
    return out;
}
OwnedInstanceTradeService::Deliveries OwnedInstanceTradeService::disconnect(std::uint64_t session){const auto found=find(session);if(found==contexts_.end())return {};const auto context=found->second;contexts_.erase(found);return restore(context);}
OwnedInstanceTradeService::Deliveries OwnedInstanceTradeService::refresh(Clock::time_point now){
    Deliveries out;for(auto found=contexts_.begin();found!=contexts_.end();){bool valid=false;try{valid=now<found->second.expires&&current(found->second);}catch(const std::exception&){valid=false;}
        if(valid){++found;continue;}const auto context=found->second;found=contexts_.erase(found);const auto restored=restore(context);for(const auto& [session,bytes]:restored)append(out,session,bytes);}
    return out;
}
OwnedInstanceTradeService::Result OwnedInstanceTradeService::handle(std::uint64_t session,std::span<const RecoveredTrade::Request> requests,Clock::time_point now){
    Result result;
    const auto reject=[&](){result.rejected=true;
        try{
            if(active(session))result.deliveries=disconnect(session);
            else if(const auto peer=lookup_(session);peer&&peer->ready&&peer->session==session){const auto saved=repo_.load(peer->account,peer->character);append(result.deliveries,session,RecoveredTrade::rollback_close());retire_beast_presentation(result.deliveries,session,saved);for(std::uint8_t slot=0;slot<30;++slot)append(result.deliveries,session,project(saved,slot));append(result.deliveries,session,RecoveredTrade::wallet(saved.wallet.amount));}
        }catch(const std::exception&){result.deliveries.clear();}
        return result;};
    using K=RecoveredTrade::Kind;
    if(requests.empty()||requests.size()>2||(requests.size()==2&&(requests[0].kind!=K::OfferMoney||requests[1].kind!=K::Confirm)))return reject();
    try{
        auto found=find(session);
        if(requests.front().kind==K::Open){require(!active(session),"Owned trade participant busy");const auto own=lookup_(session),peer=resolve_(requests.front().target);require(own&&peer&&own->session==session&&peer->character==requests.front().target&&compatible(*own,*peer)&&!active(peer->session),"Owned trade peer unavailable");
            Context context{{*own,*peer},{},{},{},now+std::chrono::seconds(60)};
            for(unsigned n=0;n<2;++n){context.sides[n].expected=repo_.load(context.peers[n].account,context.peers[n].character);for(std::uint8_t slot=0;slot<30;++slot)project(context.sides[n].expected,slot);}
            for(unsigned n=0;n<2;++n){append(result.deliveries,context.peers[n].session,RecoveredTrade::open(static_cast<std::uint16_t>(context.peers[1-n].character),name_(context.peers[n],context.peers[1-n])));append(result.deliveries,context.peers[n].session,RecoveredTrade::wallet(context.sides[n].expected.wallet.amount));}
            require(lease_current(context),"Owned trade peer changed during opening preparation");contexts_.emplace(session,std::move(context));return result;}
        require(found!=contexts_.end(),"Owned trade context absent");auto next=found->second;require(now<next.expires&&current(next),"Owned trade lease/snapshot expired");const unsigned own=next.peers[0].session==session?0:1,peer=1-own;
        for(const auto& request:requests){
            if(request.kind==K::Cancel){require(request.control==0,"Unknown owned trade cancel control");result.deliveries=restore(next);contexts_.erase(found);return result;}
            require(!next.confirmed[own],"Confirmed owned trade cannot change");
            if(request.kind==K::OfferItem){require(request.target==next.peers[peer].character&&request.slot<30&&request.quantity&&next.sides[own].items.size()<8,"Owned trade offer target/slot/cap invalid");const auto& saved=next.sides[own].expected;require(saved.bag.scalar[request.slot].has_value(),"Owned trade offered scalar absent");const auto& scalar=*saved.bag.scalar[request.slot];
                require(scalar.item_id==request.item&&request.quantity<=scalar.count&&std::none_of(next.sides[own].items.begin(),next.sides[own].items.end(),[&](const auto& item){return item.slot==request.slot;}),"Owned trade offer key/quantity/duplicate invalid");
                require(whole(saved,request.slot)?request.quantity==1:eligible_(scalar),"Owned trade offer whole-instance/plain eligibility invalid");
                if(const auto* beast=beast_at(saved.beasts,request.slot))require(bool(beast_eligible_)&&beast_eligible_(*beast),"PET trade Lua eligibility rejected");
                const auto index=static_cast<std::uint8_t>(next.sides[own].items.size());next.sides[own].items.push_back({request.slot,request.quantity});RecoveredTrade::Item item{};item[0]=request.quantity;item[1]=index;const auto bytes=metadata(saved,request.slot);std::copy(bytes.begin(),bytes.end(),item.begin()+4);const auto encoded=RecoveredTrade::peer_item(item);require(encoded.has_value(),"Owned trade peer50 offer index invalid");append(result.deliveries,next.peers[peer].session,*encoded);
            }else if(request.kind==K::OfferMoney){require(!next.money_submitted[own]&&request.target==next.peers[peer].character&&request.money<=next.sides[own].expected.wallet.amount,"Owned trade money target/balance/repetition invalid");next.sides[own].money=request.money;next.money_submitted[own]=true;append(result.deliveries,next.peers[peer].session,RecoveredTrade::peer_money(request.money));
            }else if(request.kind==K::Confirm){require(request.control==0,"Unknown owned trade confirm control");next.confirmed[own]=true;append(result.deliveries,next.peers[peer].session,RecoveredTrade::peer_confirmation(1));}
            else throw DatabaseError("Invalid owned trade state operation");
        }
        next.expires=now+std::chrono::seconds(60);
        if(next.confirmed[0]&&next.confirmed[1]){
            const auto receipt=receipt_();
            repo_.commit(receipt,next.sides,[&](const Repo::Plan& planned){
                // Prepare both complete replies from the immutable Plan before
                // BEGIN. No postwrite reads or metadata reconstruction here.
                for(unsigned n=0;n<2;++n){append(result.deliveries,next.peers[n].session,RecoveredTrade::close_without_refund());retire_beast_presentation(result.deliveries,next.peers[n].session,planned.sides[n]);for(std::uint8_t slot=0;slot<30;++slot)append(result.deliveries,next.peers[n].session,project(planned.sides[n],slot));append(result.deliveries,next.peers[n].session,RecoveredTrade::wallet(planned.sides[n].wallet.amount));}
                require(lease_current(next)&&Clock::now()<next.expires,"Owned trade lease changed during preparation");
            },[&](const Repo::Plan&){require(lease_current(next)&&Clock::now()<next.expires,"Owned trade late live lease changed");});
            contexts_.erase(found);result.committed=true;
        }else found->second=std::move(next);
        return result;
    }catch(const std::exception&){result.deliveries.clear();return reject();}
}
}
