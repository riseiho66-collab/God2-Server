// Actual SqliteDatabase with complete original armor/weapon/MED02 catalogs.
#define main accepted_armor_adapter_for_trade_main
#include "storage_owned_armor_bank_adapter_0067.cpp"
#undef main
#include "db/SqliteOwnedInstanceTradeRepository.h"
#include "db/SqliteWeaponSlotRepository.h"
#include "core/Config.h"
namespace {
using TRepo=SqliteOwnedInstanceTradeRepository;
void weapon_catalog(sqlite3* db){
    std::ifstream file(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/research/native-weapons-20260926/records.json");require(file.good(),"Qualified full weapon source missing");nlohmann::json groups;file>>groups;
    require(groups.size()==2&&groups[0].size()==2&&groups[1].size()==1259,"Full weapon source denominator changed");sqlite_detail::Transaction transaction(db);
    for(unsigned group=0;group<2;++group)for(const auto& row:groups[group]){require(row.size()==10,"Weapon source width changed");sqlite_detail::Statement insert(db,group==0?"INSERT INTO native_weapon_sources VALUES(?,?,?,?,?,?,?,?,?,?)":"INSERT INTO native_weapon_rows VALUES(?,?,?,?,?,?,?,?,?,?)");
        for(int i=0;i<10;++i){if(group==1&&(i==6||i==8))insert.bind_blob(i+1,unhex(row[i].get<std::string>()));else if((group==0&&i==7)||(group==1&&i>=1&&i<=4))insert.bind(i+1,row[i].get<std::int64_t>());else insert.bind(i+1,row[i].get<std::string>());}insert.done();
    }transaction.commit();
}
void med_catalog(sqlite3* db){
    std::ifstream file(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/research/owned-instance-trade-0069/native-med02-cache.json");require(file.good(),"Original71 MED02 cache missing");nlohmann::json data;file>>data;
    require(data["source"].size()==9&&data["rows"].size()==71,"MED02 source width/count changed");sqlite_detail::Transaction transaction(db);
    sqlite_detail::Statement source(db,"INSERT INTO native_data_sources VALUES(?,?,?,?,?,?,?,?,?)");
    for(int i=0;i<9;++i){if(i==8)source.bind(i+1,data["source"][i].get<std::int64_t>());else source.bind(i+1,data["source"][i].get<std::string>());}source.done();
    for(const auto& row:data["rows"]){require(row.size()==11,"MED02 declaration width changed");sqlite_detail::Statement insert(db,"INSERT INTO native_med02_recovery_declarations VALUES(?,?,?,?,?,?,?,?,?,?,?)");
        for(int i=0;i<11;++i){if(i==5||i==6)insert.bind_blob(i+1,unhex(row[i].get<std::string>()));else if(i==0||i==4)insert.bind(i+1,row[i].get<std::string>());else insert.bind(i+1,row[i].get<std::int64_t>());}insert.done();}
    transaction.commit();
}
void migration45(){
    File file;SqliteDatabase database(file.path);rejects([&]{(void)database.instance_trades();});database.initialize();rejects([&]{(void)database.instance_trades();});database.migrate();auto raw=open(file.path);
    require(number(raw.get(),"SELECT max(version) FROM schema_migrations")==default_sqlite_migrations().back().version,"Current schema tail absent; migration45 receipt still required");
    for(const auto* table:{"accounts","recovered_characters","diagnostic_inventory_slots","character_owned_instance_trade_receipts"})require(dump(raw.get(),std::string("SELECT * FROM ")+table).empty(),"Fresh migration granted rows");
    const auto before=tables(raw.get());rejects([&]{(void)database.instance_trades().load(1,1);});require(tables(raw.get())==before,"Unallocated read wrote data");database.migrate();require(tables(raw.get())==before,"Migration45 not idempotent");
}
std::array<std::uint8_t,20> trade_bytes(std::uint16_t key,std::uint8_t type,std::uint8_t seed){
    std::array<std::uint8_t,20> value;value.fill(seed);value[0]=static_cast<std::uint8_t>(key);value[1]=static_cast<std::uint8_t>(key>>8);value[2]=type;if(type==8)value[3]=14;return value;
}
void trade_instance(Fixture& f,std::uint64_t owner,std::uint8_t slot,const std::array<std::uint8_t,20>& value,bool gem=false){
    sqlite_detail::Statement scalar(f.raw.get(),"UPDATE diagnostic_inventory_slots SET item_id=?,count=1,revision=11 WHERE character_id=? AND slot=?");scalar.bind(1,value[0]|(unsigned(value[1])<<8));scalar.bind_id(2,owner);scalar.bind(3,slot);scalar.done();
    sqlite_detail::Statement insert(f.raw.get(),gem?"INSERT INTO character_teleport_gem_metadata VALUES(?,?,?,11,'CUSTOM_TEST_NOT_NATIVE','isolated-adapter0069',?,'CUSTOM-0057')":"INSERT INTO character_weapon_slot_metadata VALUES(?,?,?,11,'CUSTOM_TEST_NOT_NATIVE','isolated-adapter0069',?,?,'CUSTOM-0046')");
    insert.bind_id(1,owner);insert.bind(2,slot);insert.bind_blob(3,value);insert.bind(4,SqliteArmorSlotRepository::source_sha256);if(!gem)insert.bind(5,SqliteWeaponSlotRepository::client_sha256);insert.done();
}
void production_trade(){
    Fixture f;weapon_catalog(f.raw.get());med_catalog(f.raw.get());require(f.current->native_supply_catalog().lookup(3107).has_value(),"Full71 MED catalog unqualified");require(f.current->native_weapon_catalog().populated(),"Full1259 WPN/TWP catalog invalid");
    f.current->trades().install_schema();f.current->trades().provision_wallet(1,f.character);f.current->trades().provision_wallet(2,f.peer);f.sql("UPDATE character_trade_wallets SET amount=character_id*1000,revision=3");
    const auto w=trade_bytes(1,0xc1,0x91),t=trade_bytes(19001,0xd9,0x92),g=trade_bytes(16055,8,0x93),other=trade_bytes(1,0xc1,0xa4);
    trade_instance(f,f.character,10,w);trade_instance(f,f.character,11,t);trade_instance(f,f.character,12,g,true);trade_instance(f,f.peer,9,other);trade_instance(f,f.character,34,w);trade_instance(f,f.peer,34,other);
    f.sql("UPDATE diagnostic_inventory_slots SET item_id=3107,count=8,revision=7 WHERE character_id=2 AND slot=5");
    auto& repo=f.current->instance_trades();const std::array<TRepo::Side,2> sides{{{repo.load(1,f.character),{{0,1},{1,1},{10,1},{11,1},{12,1},{5,3}},100},{repo.load(2,f.peer),{{9,1},{5,4}},50}}};
    const auto plan=repo.plan(sides);require(plan.transfers.size()==8,"Actual transfer mapping incomplete");
    // Actual receipt-trigger corruption of a protected equipped instance must
    // roll back both players, metadata, money and the complete new receipt.
    f.sql("CREATE TRIGGER adapter_trade_poison AFTER INSERT ON character_owned_instance_trade_receipts BEGIN UPDATE character_weapon_slot_metadata SET logical20=CAST(substr(logical20,1,19)||X'7F' AS BLOB) WHERE character_id=NEW.second_character AND slot=34; END");
    const auto before=tables(f.raw.get());rejects([&]{repo.commit(std::string(64,'e'),sides,[](const auto&){});});require(tables(f.raw.get())==before,"Real production trade writer failed to roll back both full owners");f.sql("DROP TRIGGER adapter_trade_poison");
    unsigned prepared=0;const auto committed=repo.commit(std::string(64,'e'),sides,[&](const auto& value){require(value==plan,"Prepared plan changed");++prepared;});require(committed==plan&&prepared==1,"Actual production trade differs from plan");
    for(unsigned n=0;n<2;++n)require(repo.load(n+1,n?f.peer:f.character)==plan.sides[n],"Production stored full snapshot differs");
    require(plan.sides[0].wallet.amount+plan.sides[1].wallet.amount==3000,"Trade money not conserved");require(plan.sides[0].bag.weapons[0].logical20==other,"Same-ID metadata moved from wrong owner");
    require(plan.sides[1].bag.armor.size()==2&&plan.sides[1].bag.gems[0].logical20==g,"Armor/gem transfer incomplete");
    const auto saved=tables(f.raw.get());rejects([&]{repo.commit(std::string(64,'e'),sides,[](const auto&){});});require(tables(f.raw.get())==saved,"Replay changed both owners");
    require(number(f.raw.get(),"SELECT count(*) FROM character_trade_receipts")==0,"New route wrote accepted scalar ledger");require(dump(f.raw.get(),"PRAGMA foreign_key_check").empty(),"New trade FK failure");
}
void config_trade_gate(){
    std::ifstream file(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/releases/town-chat-welcome-20260924/server-config.json");require(file.good(),"Accepted config missing");nlohmann::json config;file>>config;config["world"].erase("owned_mixed_bank");config["world"].erase("owned_instance_discard");config["world"].erase("owned_instance_trade");File temp;const auto path=temp.directory/"server-config.json";
    auto parse=[&]{std::ofstream out(path);out<<config.dump();out.close();return Config::load(path);};require(!parse().owned_instance_trade_enabled,"New trade not default off");config["world"]["owned_instance_trade"]={{"enabled",true}};require(parse().owned_instance_trade_enabled,"Valid instance trade opt-in rejected");
    const auto error=[&](const std::string& expected){bool failed=false;try{(void)parse();}catch(const std::runtime_error& e){require(e.what()==expected,"Unexpected trade config rejection");failed=true;}require(failed,"Invalid trade config accepted");};
    config["world"]["owned_instance_trade"]["enabled"]="true";error("Owned instance trade bool required");config["world"]["owned_instance_trade"]["enabled"]=true;config["world"]["owned_armor_bank"]["enabled"]=false;config["world"]["owned_foreign_bank"]["enabled"]=false;config["world"]["owned_armor_transfers"]["enabled"]=false;error("Owned instance trade requires authenticated native world and owned armor transport");
}
}
int main(){try{migration45();production_trade();config_trade_gate();std::cout<<"PASS CUSTOM0069 true SqliteDatabase original catalogs1354/1259/71, full20 mixed dual-owner transfer, actual writer contamination rollback, replay, schema45 no grants/config; not live acceptance\n";return 0;}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
