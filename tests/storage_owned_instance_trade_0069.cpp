#include "db/SqliteOwnedInstanceTradeRepository.h"
// Reuse the frozen actual1259 definition fixture, not its test entry point.
// No catalog grant, retired client data or invented weapon mapping is added.
#pragma push_macro("main")
#undef main
#define main included_foreign_bank_fixture_0068_main
#include "storage_owned_foreign_bank_0068.cpp"
#undef main
#pragma pop_macro("main")

namespace {
using TradeRepo=SqliteOwnedInstanceTradeRepository;
struct TradeFixture : Fixture {
    explicit TradeFixture(unsigned slots=50,bool file=false):Fixture(slots,file){
        SqliteTradeRepository old(db);old.install_schema();for(unsigned n=0;n<2;++n)old.provision_wallet(n+1,ids[n]);
        sql("UPDATE character_trade_wallets SET amount=CASE character_id WHEN 1 THEN 1000 ELSE 2000 END");
    }
    TradeRepo trade_repo(){return {db,armor,armor_exact,[this](auto id)->std::optional<NativeWeaponRecord>{const auto found=definitions.find(id);return found==definitions.end()?std::nullopt:std::optional(found->second);},[](auto id){return id==3107||id==3108;}};}
    void install_trade(){sql(TradeRepo::schema());}
    auto trade_load(unsigned owner=0){return trade_repo().load(owner+1,ids[owner]);}
    std::array<TradeRepo::Side,2> trade_sides(){return {{{trade_load(0),{},0},{trade_load(1),{},0}}};}
    auto trade_commit(const std::array<TradeRepo::Side,2>& sides){bool prepared=false,checked=false;const auto result=trade_repo().commit(receipt(),sides,[&](const auto&){require(sqlite3_get_autocommit(db)!=0,"Trade prepare must precede BEGIN");prepared=true;},[&](const auto& next){require(sqlite3_get_autocommit(db)==0,"Trade check outside transaction");for(unsigned n=0;n<2;++n)require(trade_load(n)==next.sides[n],"Trade checked full snapshot differs");checked=true;});require(prepared&&checked,"Trade hooks skipped");return result;}
    void empty_weapon(unsigned slot,unsigned owner=0,std::uint8_t fill=0xab){
        const auto saved=trade_load(owner);std::array<std::uint8_t,20> bytes;bytes.fill(fill);bytes[0]=bytes[1]=0;
        sqlite_detail::Statement insert(db,"INSERT INTO character_weapon_slot_metadata VALUES(?,?,?,?,'EMPTY_SLOT_POLICY','preserved-empty-tail',?,?,'CUSTOM-0046')");insert.bind_id(1,ids[owner]);insert.bind(2,slot);insert.bind_blob(3,bytes);insert.bind_id(4,saved.bag.scalar[slot]->revision);insert.bind(5,SqliteArmorSlotRepository::source_sha256);insert.bind(6,SqliteWeaponSlotRepository::client_sha256);insert.done();
    }
};
template<class T>const T& trade_overlay(const std::vector<T>& values,unsigned slot){const auto found=std::find_if(values.begin(),values.end(),[&](const auto& value){return value.slot==slot;});require(found!=values.end(),"Trade instance overlay missing");return *found;}

void trade_full_instances(){
    TradeFixture f;const auto before_schema=f.rows();f.trade_load();require(f.rows()==before_schema,"Trade load created schema/grants");rejects([&]{f.trade_repo().receipt_exists(std::string(64,'a'));});f.install_trade();
    const auto wpn=f.add(0,1,0xa1,7),twp=f.add(1,19001,0xb2,11),gem=f.add(2,16055,0xc3,13);f.add_armor(3,1001);f.add_armor(30,1201);f.add(34,2,0xe5,17);f.add(0,1,0xf6,19,1);f.add(1,16055,0xd7,23,1);f.add_armor(2,1001,1);f.scalar(4,3107,127,29);f.scalar(3,3108,50,31,1);f.scalar(44,60000,3,37);f.empty_weapon(10);f.empty_weapon(11,1);
    const auto initial=f.trade_sides();const auto vault=dump(f.db,"SELECT * FROM character_bank_item_slots ORDER BY character_id,slot");auto sides=initial;sides[0].items={{0,1},{1,1},{2,1},{3,1},{4,27}};sides[1].items={{0,1},{1,1},{2,1},{3,10}};sides[0].money=100;sides[1].money=300;
    const auto planned=f.trade_repo().plan(sides);require(planned.transfers.size()==9,"Trade transfer count differs");const auto next=f.trade_commit(sides);require(next==planned,"Trade committed plan differs");
    require(trade_overlay(next.sides[1].bag.weapons,0).logical20==wpn&&trade_overlay(next.sides[1].bag.weapons,1).logical20==twp&&trade_overlay(next.sides[1].bag.gems,2).logical20==gem,"Trade lost WPN/TWP/gem full20");
    require(trade_overlay(next.sides[1].bag.weapons,0).client_sha256==SqliteWeaponSlotRepository::client_sha256&&trade_overlay(next.sides[1].bag.weapons,1).design_id=="CUSTOM-0046"&&trade_overlay(next.sides[1].bag.gems,2).client_sha256.empty()&&trade_overlay(next.sides[1].bag.gems,2).design_id=="CUSTOM-0057","Trade normalized distinct source/client/design pins");
    const auto& armor_after=trade_overlay(next.sides[1].bag.armor,4);require(armor_after.logical20==trade_overlay(initial[0].expected.bag.armor,3).logical20&&armor_after.provenance==trade_overlay(initial[0].expected.bag.armor,3).provenance,"Trade lost armor opaque tail/provenance");
    require(next.sides[0].bag.scalar[4]->count==100&&next.sides[1].bag.scalar[5]->count==27&&next.sides[1].bag.scalar[3]->count==40,"Trade partial MED altered quantity or merged stacks");
    for(const auto& transfer:next.transfers)require(next.sides[transfer.to_side].bag.scalar[transfer.destination]->revision==initial[transfer.to_side].expected.bag.scalar[transfer.destination]->revision+1,"Trade copied source revision into destination");
    require(next.sides[0].wallet.amount==1200&&next.sides[1].wallet.amount==1800&&next.sides[0].wallet.revision==2&&next.sides[1].wallet.revision==2,"Trade money conservation/revisions failed");
    require(next.sides[0].bag.scalar[30]==initial[0].expected.bag.scalar[30]&&next.sides[0].bag.scalar[34]==initial[0].expected.bag.scalar[34]&&next.sides[0].bag.scalar[44]==initial[0].expected.bag.scalar[44]&&trade_overlay(next.sides[0].bag.weapons,34)==trade_overlay(initial[0].expected.bag.weapons,34)&&trade_overlay(next.sides[0].bag.weapons,10)==trade_overlay(initial[0].expected.bag.weapons,10)&&dump(f.db,"SELECT * FROM character_bank_item_slots ORDER BY character_id,slot")==vault,"Trade altered protected/equipment/untouched empty tail/vault");
    auto second=f.trade_sides();const auto rows=f.rows();rejects([&]{f.trade_repo().commit(std::string(62,'e')+"00",second,[](const auto&){});});require(f.rows()==rows,"Trade duplicate receipt mutated either owner");
    sqlite_detail::Statement recorded(f.db,"SELECT before_state,after_state,offers_state FROM character_owned_instance_trade_receipts");require(recorded.row(),"Trade receipt missing");auto before=nlohmann::json::parse(recorded.text(0)),after=nlohmann::json::parse(recorded.text(1)),op=nlohmann::json::parse(recorded.text(2));require(before.size()==2&&before[0][4].size()==50&&after[1][4].size()==50&&op[2].size()==9&&!recorded.row(),"Trade receipt omitted complete before/after/offer payload");
}

void trade_capacity_and_empty_retirement(){
    TradeFixture f(30,true);f.install_trade();for(unsigned owner=0;owner<2;++owner)for(unsigned slot=0;slot<30;++slot)f.scalar(slot,3107,127,slot+2,owner);
    // Full bags can trade after both source cells are emptied, including same
    // ID instances with different opaque tails and physical revisions.
    f.scalar(29,0,0,50);f.scalar(29,0,0,70,1);auto a=f.add(29,1,0xa1,51),b=f.add(29,1,0xb2,71,1);auto sides=f.trade_sides();sides[0].items={{29,1}};sides[1].items={{29,1}};const auto next=f.trade_commit(sides);require(trade_overlay(next.sides[0].bag.weapons,29).logical20==b&&trade_overlay(next.sides[1].bag.weapons,29).logical20==a&&next.sides[0].bag.scalar[29]->revision==52&&next.sides[1].bag.scalar[29]->revision==72,"Full bag reciprocal same-ID trade lost tails/physical revisions");
    for(const auto& side:next.sides)for(unsigned slot=30;slot<50;++slot)require(!side.bag.scalar[slot],"Trade fabricated protected capacity");
    sides=f.trade_sides();sides[0].items={{0,1}};const auto rows=f.rows();rejects([&]{f.trade_repo().commit(f.receipt(),sides,[](const auto&){});});require(f.rows()==rows,"Partial-full bag capacity denial wrote rows");
    TradeFixture empty(30);empty.install_trade();empty.add(0,1,0xa1,7);empty.empty_weapon(0,1);empty.empty_weapon(1,1);const auto untouched=trade_overlay(empty.trade_load(1).bag.weapons,1);auto offered=empty.trade_sides();offered[0].items={{0,1}};const auto moved=empty.trade_commit(offered);require(trade_overlay(moved.sides[1].bag.weapons,0).origin=="CUSTOM_TEST_NOT_NATIVE"&&trade_overlay(moved.sides[1].bag.weapons,1)==untouched&&moved.sides[0].bag.weapons.empty(),"Trade empty overlay retirement affected untouched row or retained moved source");
    // Unknown, unoffered legal scalar is observed and preserved, not admitted.
    empty.scalar(7,60000,2,9);const auto snapshot=empty.trade_load();require(snapshot.bag.scalar[7]->item_id==60000,"Unknown unoffered plain blocked snapshot");
}

void trade_rejections(){
    TradeFixture f;f.install_trade();f.add(0,1,0xa1,7);f.add(1,19001,0xb2,9);f.add(2,16055,0xc3,11);f.add_armor(3,1001);f.add(34,2,0xd4,13);f.scalar(4,3107,127,17);f.scalar(5,60000,2,19);f.add(0,16055,0xe5,23,1);auto repository=f.trade_repo();auto valid=f.trade_sides();valid[0].items={{0,1}};
    const auto denied=[&](const auto& sides){const auto rows=f.rows();rejects([&]{repository.commit(f.receipt(),sides,[](const auto&){});});require(f.rows()==rows,"Trade rejection changed either owner");};
    for(unsigned slot:{30,34,49,255}){auto wrong=valid;wrong[0].items={{static_cast<std::uint8_t>(slot),1}};denied(wrong);}
    auto wrong=valid;wrong[0].items={{0,1},{0,1}};denied(wrong);wrong=valid;wrong[0].items={{0,0}};denied(wrong);wrong=valid;wrong[0].items={{0,2}};denied(wrong);wrong=valid;wrong[0].items={{5,1}};denied(wrong);wrong=valid;wrong[0].items.assign(9,{4,1});denied(wrong);
    wrong=valid;wrong[1].expected=wrong[0].expected;denied(wrong);wrong=valid;wrong[0].expected.bag.account=2;denied(wrong);wrong=valid;wrong[0].money=1001;denied(wrong);wrong=valid;wrong[1].expected.wallet.amount=std::numeric_limits<std::uint32_t>::max();wrong[0].money=1;denied(wrong);wrong=valid;wrong[0].expected.bag.scalar[0]->revision=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());wrong[0].expected.bag.weapons[0].revision=wrong[0].expected.bag.scalar[0]->revision;denied(wrong);
    wrong=valid;wrong[0].expected.bag.weapons[0].logical20[2]=25;denied(wrong);wrong=valid;wrong[0].expected.bag.weapons[1].logical20[2]=1;denied(wrong);wrong=valid;wrong[0].expected.bag.gems[0].logical20[3]=0;denied(wrong);wrong=valid;wrong[0].expected.bag.gems[0].client_sha256=SqliteWeaponSlotRepository::client_sha256;denied(wrong);wrong=valid;wrong[0].expected.bag.weapons[0].client_sha256=SqliteArmorSlotRepository::client_sha256;denied(wrong);wrong=valid;wrong[0].expected.bag.armor[0].logical20[2]=1;denied(wrong);
    wrong=valid;wrong[0].expected.bag.weapons[0].logical20[19]^=1;denied(wrong);wrong=valid;++wrong[1].expected.bag.scalar[44]->revision;denied(wrong);wrong=valid;++wrong[1].expected.wallet.revision;denied(wrong);wrong=valid;wrong[0].expected.bag.armor[0].provenance="stale";denied(wrong);wrong=valid;wrong[1].expected.bag.scalar[49].reset();denied(wrong);
    rejects([&]{repository.load(2,f.ids[0]);});rejects([&]{TradeRepo invalid(f.db,armor,armor_exact,{},[](auto){return true;});});
    f.sql("INSERT INTO character_trade_receipts VALUES('"+std::string(64,'a')+"',1,2,'CUSTOM-0063')");auto rows=f.rows();rejects([&]{repository.commit(std::string(64,'a'),valid,[](const auto&){});});require(f.rows()==rows&&repository.receipt_exists(std::string(64,'a')),"Trade reused old0063 receipt");
    const auto original=f.definitions.at(19001);f.definitions.at(19001).parsed_record[0x11a]=0;rejects([&]{repository.plan(valid);});f.definitions.at(19001)=original;require(f.rows()==rows,"Definition admission failure wrote rows");
    f.sql("DELETE FROM diagnostic_inventory_slots WHERE character_id=1 AND slot=29");rows=f.rows();rejects([&]{f.trade_load();});require(f.rows()==rows,"Trade allocated missing ordinary slot");
}

void trade_real_trigger_rollbacks(){
    TradeFixture f;f.install_trade();f.add(0,1,0xa1,7);f.add(1,19001,0xb2,11);f.add(2,16055,0xc3,13);f.add_armor(3,1001);f.add(34,2,0xe5,17);f.add(0,16055,0xd4,19,1);f.add_armor(30,1201,1);f.empty_weapon(10);auto sides=f.trade_sides();sides[0].items={{0,1},{1,1},{2,1},{3,1}};sides[1].items={{0,1}};sides[0].money=10;sides[1].money=20;
    auto repo=f.trade_repo();unsigned index=0;
    for(const auto* sql:{
        "CREATE TRIGGER injected BEFORE DELETE ON character_weapon_slot_metadata BEGIN SELECT RAISE(IGNORE); END",
        "CREATE TRIGGER injected BEFORE UPDATE ON diagnostic_inventory_slots WHEN NEW.character_id=2 BEGIN SELECT RAISE(ABORT,'second owner'); END",
        "CREATE TRIGGER injected BEFORE UPDATE ON character_trade_wallets WHEN NEW.character_id=2 BEGIN SELECT RAISE(IGNORE); END",
        "CREATE TRIGGER injected BEFORE INSERT ON character_weapon_slot_metadata BEGIN SELECT RAISE(IGNORE); END",
        "CREATE TRIGGER injected BEFORE INSERT ON character_armor_slot_metadata BEGIN SELECT RAISE(IGNORE); END",
        "CREATE TRIGGER injected BEFORE INSERT ON character_teleport_gem_metadata BEGIN SELECT RAISE(IGNORE); END",
        "CREATE TRIGGER injected BEFORE INSERT ON character_owned_instance_trade_receipts BEGIN SELECT RAISE(IGNORE); END",
        "CREATE TRIGGER injected AFTER INSERT ON character_owned_instance_trade_receipts BEGIN UPDATE character_weapon_slot_metadata SET logical20=CAST(substr(logical20,1,19)||X'7F' AS BLOB) WHERE character_id=2 AND slot=0; END",
        "CREATE TRIGGER injected AFTER INSERT ON character_owned_instance_trade_receipts BEGIN UPDATE character_weapon_slot_metadata SET provenance='late-equipped' WHERE slot=34; END",
        "CREATE TRIGGER injected AFTER INSERT ON character_owned_instance_trade_receipts BEGIN UPDATE character_armor_slot_metadata SET provenance='late-equipped-armor' WHERE slot=30; END",
        "CREATE TRIGGER injected AFTER INSERT ON character_owned_instance_trade_receipts BEGIN UPDATE character_teleport_gem_metadata SET provenance='late-gem'; END",
        "CREATE TRIGGER injected AFTER INSERT ON character_owned_instance_trade_receipts BEGIN UPDATE character_weapon_slot_metadata SET provenance='late-empty-tail' WHERE slot=10; END",
        "CREATE TRIGGER injected AFTER INSERT ON character_owned_instance_trade_receipts BEGIN UPDATE diagnostic_inventory_slots SET revision=revision+1 WHERE character_id=2 AND slot=44; END",
        "CREATE TRIGGER injected AFTER INSERT ON character_owned_instance_trade_receipts BEGIN DELETE FROM diagnostic_inventory_slots WHERE character_id=2 AND slot=49; END",
        "CREATE TRIGGER injected AFTER INSERT ON character_owned_instance_trade_receipts BEGIN UPDATE character_trade_wallets SET amount=amount+1 WHERE character_id=2; END",
        "CREATE TRIGGER injected AFTER INSERT ON character_owned_instance_trade_receipts BEGIN UPDATE character_owned_instance_trade_receipts SET offers_state='late-offer'; END",
        "CREATE TRIGGER injected AFTER INSERT ON character_owned_instance_trade_receipts BEGIN INSERT INTO character_trade_receipts VALUES(NEW.receipt,NEW.first_character,NEW.second_character,'CUSTOM-0063'); END",
        "CREATE TRIGGER injected AFTER INSERT ON character_owned_instance_trade_receipts BEGIN UPDATE recovered_characters SET account_id=2,slot=1 WHERE id=1; END"
    }){
        f.sql(sql);const auto before=f.rows();bool executed=false;sqlite3_trace_v2(f.db,SQLITE_TRACE_STMT,[](unsigned,void* context,void*,void* statement)->int{if(statement&&std::strstr(static_cast<const char*>(statement),"TRIGGER injected"))*static_cast<bool*>(context)=true;return 0;},&executed);
        rejects([&]{repo.commit(std::string(64,'f'),sides,[](const auto&){});});sqlite3_trace_v2(f.db,0,nullptr,nullptr);require(executed,("Trade trigger not executed index"+std::to_string(index)).c_str());require(f.rows()==before,("Trade trigger rollback lost either owner index"+std::to_string(index)).c_str());f.sql("DROP TRIGGER injected");++index;
    }
    const auto rows=f.rows();try{repo.commit(std::string(64,'f'),sides,[](const auto&){throw std::runtime_error("Trade prepare failed");});throw std::logic_error("Prepare succeeded");}catch(const std::runtime_error& error){require(std::string(error.what())=="Trade prepare failed","Wrong prepare error");}require(f.rows()==rows,"Trade prepare failure wrote rows");
    bool checked=false;rejects([&]{repo.commit(std::string(64,'f'),sides,[](const auto&){},[&](const auto&){checked=true;f.sql("UPDATE character_weapon_slot_metadata SET provenance='check-contamination' WHERE slot=34");});});require(checked&&f.rows()==rows,"Trade Check contamination committed");
    // Preparation is deliberately outside BEGIN. A legitimate intervening
    // revision remains saved, but the stale trade must not settle either side.
    bool prepared=false;rejects([&]{repo.commit(std::string(64,'f'),sides,[&](const auto&){prepared=true;f.sql("UPDATE character_trade_wallets SET revision=revision+1 WHERE character_id=2");});});require(prepared&&f.trade_load(0)==sides[0].expected&&f.trade_load(1).wallet.revision==sides[1].expected.wallet.revision+1&&dump(f.db,"SELECT * FROM character_owned_instance_trade_receipts").empty(),"Trade pre-BEGIN stale CAS erased concurrent change or partially settled");
    auto refreshed=f.trade_sides();refreshed[0].items=sides[0].items;refreshed[1].items=sides[1].items;refreshed[0].money=10;refreshed[1].money=20;
    SqliteRecoveredCharacterRepository characters(f.db);const auto resources=characters.commit_resources(2,f.ids[1],{},{52,120,2,80,0,"CUSTOM-0012"});f.sql("CREATE TRIGGER injected AFTER INSERT ON character_owned_instance_trade_receipts BEGIN INSERT INTO battle_reservations(character_id,resource_revision,design_id) VALUES(NEW.second_character,"+std::to_string(resources.revision)+",'CUSTOM-0012'); END");const auto before=f.rows();bool executed=false;sqlite3_trace_v2(f.db,SQLITE_TRACE_STMT,[](unsigned,void* context,void*,void* statement)->int{if(statement&&std::strstr(static_cast<const char*>(statement),"TRIGGER injected"))*static_cast<bool*>(context)=true;return 0;},&executed);rejects([&]{repo.commit(std::string(64,'f'),refreshed,[](const auto&){});});sqlite3_trace_v2(f.db,0,nullptr,nullptr);require(executed&&f.rows()==before,"Late peer battle trigger did not exercise full rollback");f.sql("DROP TRIGGER injected");characters.reserve_battle(2,f.ids[1],resources);const auto pending=f.rows();rejects([&]{repo.commit(std::string(64,'f'),refreshed,[](const auto&){});});require(f.rows()==pending,"Pending peer battle trade wrote rows");
}

void trade_cascade(){
    TradeFixture f(30,true);f.install_trade();f.add(0,1,0xa1,7);f.add(0,16055,0xb2,11,1);auto sides=f.trade_sides();sides[0].items={{0,1}};f.trade_commit(sides);const auto peer=f.trade_load(1);const std::array<std::uint8_t,1> name{'A'};require(SqliteRecoveredCharacterRepository(f.db).erase_owned(1,f.ids[0],name),"New trade receipt blocked existing character deletion");require(f.trade_load(1)==peer&&dump(f.db,"SELECT * FROM character_owned_instance_trade_receipts").empty(),"Trade cascade deleted peer instances/wallet or retained blocking receipt");
}
}
int main(){try{trade_full_instances();trade_capacity_and_empty_retirement();trade_rejections();trade_real_trigger_rollbacks();trade_cascade();std::cout<<"PASS CUSTOM0069 whole owned trade foundation: native WPN/TWP catalog, armor/weapon/gem20 and partial MED, two-owner full50+wallet CAS, physical revisions, fullbag reciprocal capacity, empty-tail retirement, exact receipts/old0063 replay, 19 actual trigger rollback cases incl late peerbattle, prepare/check/stale/owner/equipment/provenance/money/cascade, no live integration\n";return 0;}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
