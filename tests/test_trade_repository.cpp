#include "db/SqliteTradeRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <iostream>
#include <memory>
#include <stdexcept>
using namespace god2;
void require(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
template<class F>void rejects(F&& f){try{f();}catch(const DatabaseError&){return;}throw std::runtime_error("Expected trade rejection");}
int main(){try {
    sqlite3* raw=nullptr;require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Open failed");
    std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> db(raw,sqlite3_close_v2);
    sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();
    sqlite_detail::execute(raw,"INSERT INTO accounts(id,username,password_hash) VALUES(1,'a','hash'),(2,'b','hash'),(3,'c','hash')");
    SqliteRecoveredCharacterRepository chars(raw);SqliteTradeRepository trades(raw);trades.install_schema();
    std::array<std::uint64_t,3> ids{};
    const auto hash=SqliteRecoveredCharacterRepository::town_reward_item_source_sha256;
    for(unsigned n=0;n<3;++n) {
        std::array<std::uint8_t,40> profile{};profile[0]=static_cast<std::uint8_t>('A'+n);ids[n]=chars.create(n+1,profile).id;
        auto resources=chars.commit_resources(n+1,ids[n],{},{50,120,10,80,0,"CUSTOM-0012"});
        chars.provision_town_reward_slot(n+1,ids[n]);chars.provision_owned_bag(n+1,ids[n]);
        if(n<2)chars.commit_inventory_resources(n+1,ids[n],5,chars.load_inventory_slot(n+1,ids[n],5),resources,{static_cast<std::uint16_t>(3107+n),7,0,hash},resources);
        trades.provision_wallet(n+1,ids[n]);
    }
    // Explicit test-only funding, never part of provision or a production grant.
    sqlite_detail::execute(raw,"UPDATE character_trade_wallets SET amount=CASE character_id WHEN 1 THEN 100 ELSE 50 END");
    using Side=SqliteTradeRepository::Side;
    const auto a=trades.load(1,ids[0]),b=trades.load(2,ids[1]),unrelated=trades.load(3,ids[2]);
    require(trades.provision_wallet(1,ids[0])==a.wallet,"Provision reset existing balance");
    rejects([&]{trades.load(2,ids[0]);});
    const std::array<Side,2> proposal{{{a,{{5,3}},30},{b,{{5,7}},10}}};
    const auto expected=SqliteTradeRepository::plan(proposal);
    require(expected.sides[0].wallet.amount==80 && expected.sides[1].wallet.amount==70,"Money not conserved");
    require(expected.sides[0].bag[5].count==4 && expected.sides[0].bag[0].item_id==3108 && expected.sides[0].bag[0].count==7 &&
        expected.sides[1].bag[5].count==0 && expected.sides[1].bag[0].item_id==3107 && expected.sides[1].bag[0].count==3,"Item plan incorrect");
    const auto unchanged=[&]{require(trades.load(1,ids[0])==a && trades.load(2,ids[1])==b && trades.load(3,ids[2])==unrelated,"Rejected trade changed saved values");};
    for(unsigned mode=0;mode<6;++mode) {
        auto bad=proposal;
        switch(mode) {
        case 0:bad[0].money=101;break;
        case 1:bad[0].items={{5,1},{5,1}};break;
        case 2:bad[0].items={{30,1}};break;
        case 3:bad[0].items={{5,8}};break;
        case 4:bad[0].expected.account=2;break;
        case 5:++bad[1].expected.bag[6].revision;break;
        }
        rejects([&]{trades.commit(std::string(64,'a'),bad);});unchanged();
    }
    // Midway failures: all first-player updates must roll back when the second
    // write or readback fails. A receipt trigger cannot silently corrupt either.
    for(const auto sql:{
        "CREATE TRIGGER fail BEFORE UPDATE ON character_trade_wallets WHEN NEW.character_id=2 BEGIN SELECT RAISE(ABORT,'injected'); END",
        "CREATE TRIGGER fail AFTER INSERT ON character_trade_receipts BEGIN UPDATE character_trade_wallets SET amount=999 WHERE character_id=1; END",
        "CREATE TRIGGER fail AFTER INSERT ON character_trade_receipts BEGIN DELETE FROM character_trade_receipts WHERE receipt=NEW.receipt; END"}) {
        sqlite_detail::execute(raw,sql);rejects([&]{trades.commit(std::string(64,'b'),proposal);});unchanged();
        sqlite_detail::Statement receipts(raw,"SELECT count(*) FROM character_trade_receipts");require(receipts.row() && receipts.integer(0)==0,"Failure left receipt");
        sqlite_detail::execute(raw,"DROP TRIGGER fail");
    }
    auto overflow=proposal;overflow[0].expected.wallet.amount=0xffffffff;overflow[0].money=0;
    rejects([&]{SqliteTradeRepository::plan(overflow);});
    auto full=proposal;for(auto& slot:full[0].expected.bag){slot.item_id=3107;slot.count=7;}
    rejects([&]{SqliteTradeRepository::plan(full);});
    auto exhausted=proposal;exhausted[0].expected.bag[5].revision=0x7fffffffffffffff;
    rejects([&]{SqliteTradeRepository::plan(exhausted);});
    auto boundary=proposal;boundary[0].expected.bag[5].revision=0x7ffffffffffffffe;
    require(SqliteTradeRepository::plan(boundary).sides[0].bag[5].revision==0x7fffffffffffffff,"Last valid slot revision rejected");
    const auto committed=trades.commit(std::string(64,'c'),proposal);
    require(committed.sides==expected.sides && trades.load(1,ids[0])==expected.sides[0] && trades.load(2,ids[1])==expected.sides[1],"Settlement/readback mismatch");
    require(trades.load(3,ids[2])==unrelated,"Unrelated character changed");
    rejects([&]{trades.commit(std::string(64,'c'),proposal);});
    const std::array<Side,2> repeated{{{committed.sides[0],{},0},{committed.sides[1],{},0}}};
    rejects([&]{trades.commit(std::string(64,'c'),repeated);});
    require(trades.load(1,ids[0])==committed.sides[0] && trades.load(2,ids[1])==committed.sides[1],"Receipt replay changed either player");
    auto resources=*chars.load_resources(2,ids[1]);chars.reserve_battle(2,ids[1],resources);
    rejects([&]{trades.commit(std::string(64,'d'),repeated);});
    require(trades.load(1,ids[0])==committed.sides[0] && trades.load(2,ids[1])==committed.sides[1],"Battle guard changed trade snapshots");
    std::cout<<"Trade owned atomic settlement, CAS, conservation, receipt replay and rollback passed; runtime UI OPEN\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
