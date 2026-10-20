#include "handlers/RecoveredTradeService.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include "protocol/RecoveredInventoryProjection.h"
#include "protocol/RecoveredWorldRecords.h"
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string_view>
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
    // Each callback can synchronously attempt a second public mutation. The
    // original must reject without writing either owner or reusing erased state.
    for(unsigned adapter=0;adapter<11;++adapter)for(unsigned mutation=0;mutation<3;++mutation){
        using S=RecoveredTradeService;S* original=nullptr;bool armed=false;unsigned nested=0;
        const auto hook=[&](unsigned which){if(!armed||which!=adapter||nested)return;++nested;
            if(mutation==0){const std::array<R,1> cancel{R{K::Cancel}};const auto denied=original->handle(1,cancel,now);require(denied.rejected&&!denied.committed&&denied.deliveries.empty(),"Plain nested handle escaped fence");}
            else if(mutation==1)require(original->disconnect(1).empty(),"Plain nested disconnect erased original iterator");
            else require(original->refresh(now+std::chrono::seconds(61)).empty(),"Plain nested refresh erased original iterator");
        };
        S::OwnedProjection owned;
        if(adapter==6)owned=[&](auto,auto,auto slot,const auto&,const auto& after){hook(6);return projection(slot,after);};
        S guarded(repo,[&](auto who)->std::optional<S::Peer>{hook(0);if(sqlite3_get_autocommit(raw)==0)hook(10);const auto at=peers.find(who);return at==peers.end()?std::nullopt:std::optional(at->second);},
            [&](auto character)->std::optional<S::Peer>{hook(1);for(const auto& [id,peer]:peers)if(peer.character==character)return peer;return {};},
            [&](const auto&,const auto& peer){hook(2);RecoveredTrade::Name name{};name[0]=static_cast<std::uint8_t>('A'+peer.character);return name;},
            [&](const auto& slot){hook(3);return slot.item_id==3107;},
            [&](auto slot,const auto& value){hook(4);return projection(slot,value);},
            [&]{hook(5);return std::string(64,'f');},owned,
            [&](const auto&,const auto&){hook(7);return SqliteTradeRepository::CommitProof{[&]{hook(8);},[&]{hook(9);}};});
        original=&guarded;
        const auto send=[&](unsigned who,R request){const std::array<R,1> requests{request};return guarded.handle(who,requests,now);};
        auto one_item=item;one_item.quantity=1;
        const bool opening=adapter==1||adapter==2;
        if(!opening){require(!send(1,open).rejected,"Plain fence setup open");if(adapter!=3){require(!send(1,one_item).rejected,"Plain fence setup offer");send(1,R{K::Confirm});}}
        const std::array before{repo.load(1,1),repo.load(2,2)};armed=true;
        const auto result=opening?send(1,open):(adapter==3?send(1,one_item):send(2,R{K::Confirm}));
        require(nested==1&&result.rejected&&!result.committed&&!guarded.active(1)&&!guarded.active(2)&&repo.load(1,1)==before[0]&&repo.load(2,2)==before[1],
            "Plain callback reentry committed money/items, reused revoked context or failed SQL rollback");
        require(!result.deliveries.empty(),"Retired plain trade must close UI");for(const auto& [id,bytes]:result.deliveries)require(id&&bytes==RecoveredTrade::rollback_close(),"Retired plain trade leaked old owner data");
        require(!send(1,open).rejected,"Plain operation fence did not reset after rejection");guarded.disconnect(1);
    }
    // Resolver/eligibility may invalidate the original caller vector without
    // issuing a mutation; the admitted operation owns its request bytes.
    {
        using S=RecoveredTradeService;std::vector<R> input{open};bool clear_resolve=true,clear_eligible=false,trace_armed=false;
        S guarded(repo,[&](auto id)->std::optional<S::Peer>{if(sqlite3_get_autocommit(raw)==0)trace_armed=true;const auto p=peers.find(id);return p==peers.end()?std::nullopt:std::optional(p->second);},
            [&](auto character)->std::optional<S::Peer>{if(clear_resolve){input.clear();input.shrink_to_fit();clear_resolve=false;}for(const auto& [id,peer]:peers)if(peer.character==character)return peer;return {};},
            [](const auto&,const auto&){return RecoveredTrade::Name{};},
            [&](const auto& value){if(clear_eligible){input.clear();input.shrink_to_fit();clear_eligible=false;}return value.item_id==3107;},projection,[]{return std::string(64,'e');});
        require(!guarded.handle(1,input,now).rejected&&input.empty(),"Plain resolver invalidated borrowed open span");
        auto one=item;one.quantity=1;input={one};clear_eligible=true;
        require(!guarded.handle(1,input,now).rejected&&input.empty(),"Plain eligibility invalidated borrowed offer span");
        const std::array<R,1> confirmation{R{K::Confirm}};guarded.handle(1,confirmation,now);
        struct Trace{S* service;bool* armed;unsigned fired{};bool denied{};}trace{&guarded,&trace_armed};
        sqlite3_trace_v2(raw,SQLITE_TRACE_STMT,[](unsigned,void* ctx,void*,void* text)->int{auto& value=*static_cast<Trace*>(ctx);if(std::string_view(static_cast<const char*>(text))=="COMMIT"&&*value.armed&&!value.fired){++value.fired;value.denied=value.service->disconnect(1).empty();}return 0;},&trace);
        const auto settled=guarded.handle(2,confirmation,now);sqlite3_trace_v2(raw,0,nullptr,nullptr);
        require(trace.fired==1&&trace.denied&&settled.committed&&!settled.rejected&&settled.deliveries.empty()&&!guarded.active(1),"Plain durable COMMIT was falsely refunded after trace reentry");
    }
    // Actual lookup identities must match the requested Session, even when the
    // returned account/character happens to be identical to the stored owner.
    peers[1].session=99;require(act(1,{open}).rejected&&!service.active(1),"Foreign Session admitted a plain trade");peers[1].session=1;
    std::cout<<"Trade runtime state, consent, native coalescing, cancel/disconnect/timeout/current-save recovery passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
