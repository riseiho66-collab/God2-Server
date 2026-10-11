#include "handlers/RecoveredTradeService.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include "protocol/RecoveredInventoryProjection.h"
#include "protocol/RecoveredWorldRecords.h"
#include <iostream>
#include <memory>
#include <stdexcept>
using namespace god2;
void require(bool n,const char* text){if(!n)throw std::runtime_error(text);}
int main(){try {
    sqlite3* raw=nullptr;require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Open failed");
    std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> db(raw,sqlite3_close_v2);
    sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();
    sqlite_detail::execute(raw,"INSERT INTO accounts(id,username,password_hash) VALUES(1,'a','hash'),(2,'b','hash')");
    SqliteRecoveredCharacterRepository chars(raw);SqliteTradeRepository repo(raw);repo.install_schema();
    std::map<std::uint64_t,RecoveredTradeService::Peer> peers;
    const auto hash=SqliteRecoveredCharacterRepository::town_reward_item_source_sha256;
    for(unsigned n=1;n<=2;++n) {
        std::array<std::uint8_t,40> profile{};profile[0]=static_cast<std::uint8_t>('A'+n);
        const auto id=chars.create(n,profile).id;auto resources=chars.commit_resources(n,id,{},{50,120,10,80,0,"CUSTOM-0012"});
        chars.provision_town_reward_slot(n,id);chars.provision_owned_bag(n,id);
        chars.commit_inventory_resources(n,id,5,chars.load_inventory_slot(n,id,5),resources,{3107,7,0,hash},resources);
        repo.provision_wallet(n,id);peers.emplace(n,RecoveredTradeService::Peer{n,n,id,4,3,true});
    }
    sqlite_detail::execute(raw,"UPDATE character_trade_wallets SET amount=500");
    unsigned receipt=0;
    const auto projection=[](std::uint8_t index,const StoredInventorySlot& slot){
        RecoveredInventoryProjection::Metadata m{};m[0]=static_cast<std::uint8_t>(slot.item_id);m[1]=static_cast<std::uint8_t>(slot.item_id>>8);
        return *RecoveredInventoryProjection::encode({index,slot.count,m});};
    RecoveredTradeService service(repo,[&](auto session)->std::optional<RecoveredTradeService::Peer>{
        if(const auto at=peers.find(session);at!=peers.end())return at->second;return {};},
        [&](std::uint16_t id)->std::optional<RecoveredTradeService::Peer>{for(const auto& [session,peer]:peers)if(peer.character==id)return peer;return {};},
        [](const auto&,const auto& actor){RecoveredTrade::Name name{};name[0]=static_cast<std::uint8_t>('A'+actor.character);return name;},
        [](const auto& slot){return slot.item_id==3107;},projection,[&]{return std::string(63,'0')+"123456789abcdef"[receipt++];});
    using K=RecoveredTrade::Kind;using R=RecoveredTrade::Request;const auto now=RecoveredTradeService::Clock::now();
    const auto act=[&](std::uint64_t who,std::initializer_list<R> commands){
        std::vector<R> copied(commands);
        for(const auto& r:copied){const auto parsed=RecoveredWorldRecords::decode(RecoveredTrade::encode(r));require(parsed && parsed->size()==1 && std::get<R>(parsed->front())==r,"Trade typed transport missing");}
        return service.handle(who,copied,now);
    };
    R open{K::Open};open.target=2;R item{K::OfferItem};item.target=2;item.slot=5;item.quantity=3;item.item=3107;
    R other=item;other.target=1;other.quantity=2;
    R money{K::OfferMoney};money.target=2;money.money=100;money.opaque=0xa5a5;
    R other_money=money;other_money.target=1;other_money.money=20;
    const auto baseline_a=repo.load(1,1),baseline_b=repo.load(2,2);
    const auto unchanged=[&]{require(repo.load(1,1)==baseline_a && repo.load(2,2)==baseline_b,"Uncommitted offer changed durable state");};
    auto bad=open;bad.target=1;require(act(1,{bad}).rejected && !service.active(1),"Self trade admitted");unchanged();
    peers[2].scene=4;require(act(1,{open}).rejected,"Cross scene trade admitted");peers[2].scene=3;
    const auto opened=act(1,{open});require(!opened.rejected && opened.deliveries.size()==2 && opened.deliveries.at(1).size()==24,"Native two-sided open missing");
    const auto offered=act(1,{item});require(offered.deliveries.at(2)==std::vector<std::uint8_t>{0x50,3,0,0,0,0x23,0x0c,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0},"Peer item50 wrong native instance");unchanged();
    act(2,{other});require(!act(1,{money,R{K::Confirm}}).committed,"Single confirmation committed");unchanged();
    require(act(1,{item}).rejected && !service.active(1) && !service.active(2),"Confirmed offer was changed");unchanged();
    act(1,{open});act(1,{item});act(2,{other});act(1,{money,R{K::Confirm}});
    const auto settled=act(2,{other_money,R{K::Confirm}});
    require(settled.committed && !settled.rejected && !service.active(1) && !service.active(2),"Both confirmations did not settle");
    const auto saved_a=repo.load(1,1),saved_b=repo.load(2,2);
    require(saved_a.wallet.amount==420 && saved_b.wallet.amount==580 && saved_a.bag[5].count==4 && saved_a.bag[0].count==2 &&
        saved_b.bag[5].count==5 && saved_b.bag[0].count==3,"Committed exchange contents wrong");
    require(settled.deliveries.at(1)[0]==0x51 && settled.deliveries.at(1)[9]==0x53 && settled.deliveries.at(1)[12]==0x52 &&
        settled.deliveries.at(2)[0]==0x52,"Settlement close/refund confused");
    const auto stable=[&]{require(repo.load(1,1)==saved_a && repo.load(2,2)==saved_b,"Cancelled trade changed either participant");};
    act(1,{open});act(1,{item});const auto cancel=act(2,{R{K::Cancel}});require(cancel.deliveries.size()==2 && cancel.deliveries.at(1)[0]==0x4f,"Cancellation did not restore both sides");stable();
    act(1,{open});act(1,{item});require(service.refresh(now+std::chrono::seconds(61)).size()==2 && !service.active(1),"Timeout did not restore");stable();
    act(1,{open});act(1,{item});peers.erase(2);require(service.disconnect(2).size()==1 && !service.active(1),"Disconnect retained peer lease");stable();
    peers.emplace(2,RecoveredTradeService::Peer{2,2,2,4,3,true});
    act(1,{open});act(1,{item});auto changed=chars.commit_inventory_discard(1,1,5,1,saved_a.bag[5]);
    const auto restored=service.refresh(now);require(restored.size()==2 && !service.active(1),"Changed inventory left stale escrow");
    require(repo.load(1,1).bag[5]==changed,"Cancellation overwrote newer saved inventory");
    act(1,{open});auto wrong=item;wrong.target=99;require(act(1,{wrong}).rejected && !service.active(1),"Forged peer target admitted");
    act(1,{open});require(act(1,{money,money}).rejected && !service.active(1),"Duplicate money batch admitted");
    const auto two=RecoveredTrade::encode(money);auto pair=two;const auto confirm=RecoveredTrade::encode(R{K::Confirm});pair.insert(pair.end(),confirm.begin(),confirm.end());
    require(RecoveredWorldRecords::decode(pair)->size()==2,"Native coalesced money/confirm framing lost");
    for(std::size_t size=1;size<pair.size();++size)if(size!=two.size())require(!RecoveredWorldRecords::decode(std::span(pair).first(size)),"Truncated trade batch accepted");
    std::cout<<"Trade runtime state, consent, native coalescing, cancel/disconnect/timeout/current-save recovery passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
