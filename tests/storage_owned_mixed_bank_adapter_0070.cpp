// NEW CUSTOM0070 real SqliteDatabase/native catalog qualification, isolated only.
#define main accepted_armor_adapter_for_mixed_main
#include "storage_owned_armor_bank_adapter_0067.cpp"
#undef main
#include "db/SqliteOwnedMixedBankRepository.h"
#include "db/SqliteWeaponSlotRepository.h"
#include "core/Config.h"
namespace {
using MRepo=SqliteOwnedMixedBankRepository;
using FRepo=SqliteOwnedForeignBankRepository;
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

void fresh_mixed(){
    File file;SqliteDatabase db(file.path);rejects([&]{(void)db.mixed_bank();});db.initialize();rejects([&]{(void)db.mixed_bank();});db.migrate();auto raw=open(file.path);
    require(number(raw.get(),"SELECT max(version) FROM schema_migrations")==default_sqlite_migrations().back().version,"Fresh current migration missing");
    for(const auto* name:{"accounts","recovered_characters","diagnostic_inventory_slots","character_bank_item_slots","character_bank_mixed_receipts"})require(dump(raw.get(),std::string("SELECT * FROM ")+name).empty(),"Mixed migration granted data/capacity");
    const auto before=tables(raw.get());rejects([&]{db.mixed_bank().load(1,1);});db.migrate();require(tables(raw.get())==before,"Read/migration46 wrote data");
}
std::array<std::uint8_t,20> mixed_bytes(std::uint16_t key,std::uint8_t type,std::uint8_t seed){std::array<std::uint8_t,20> value;value.fill(seed);value[0]=static_cast<std::uint8_t>(key);value[1]=static_cast<std::uint8_t>(key>>8);value[2]=type;if(type==8)value[3]=14;return value;}
void seed_foreign(Fixture& f,unsigned n,const std::array<std::uint8_t,20>& value,bool gem){
    sqlite_detail::Statement scalar(f.raw.get(),"UPDATE diagnostic_inventory_slots SET item_id=?,count=1,revision=11 WHERE character_id=? AND slot=?");scalar.bind(1,value[0]|(unsigned(value[1])<<8));scalar.bind_id(2,f.character);scalar.bind(3,10+n);scalar.done();
    sqlite_detail::Statement insert(f.raw.get(),gem?"INSERT INTO character_teleport_gem_metadata VALUES(?,?,?,11,'CUSTOM_TEST_NOT_NATIVE','isolated-adapter0070',?,'CUSTOM-0057')":"INSERT INTO character_weapon_slot_metadata VALUES(?,?,?,11,'CUSTOM_TEST_NOT_NATIVE','isolated-adapter0070',?,?,'CUSTOM-0046')");insert.bind_id(1,f.character);insert.bind(2,10+n);insert.bind_blob(3,value);insert.bind(4,SqliteArmorSlotRepository::source_sha256);if(!gem)insert.bind(5,SqliteWeaponSlotRepository::client_sha256);insert.done();
}
std::string unique_receipt(unsigned n){auto s=std::string(64,'0');const auto v=std::to_string(n);s.replace(64-v.size(),v.size(),v);return s;}
void actual_writer(){
    Fixture f;weapon_catalog(f.raw.get());med_catalog(f.raw.get());require(f.current->native_weapon_catalog().populated()&&f.current->native_supply_catalog().lookup(3107).has_value(),"Original1259/71 qualifier failed");
    f.commit(unique_receipt(1),f.request(Op::Deposit,0,2));f.commit(unique_receipt(2),f.request(Op::Deposit,1,3));
    const std::array foreign{mixed_bytes(1,0xc1,0x91),mixed_bytes(19001,0xd9,0x92),mixed_bytes(16055,8,0x93)};
    for(unsigned n=0;n<3;++n){seed_foreign(f,n,foreign[n],n==2);auto& repo=f.current->foreign_bank();repo.commit(unique_receipt(3+n),{repo.load(1,f.character),Op::Deposit,0,static_cast<std::uint8_t>(10+n),static_cast<std::uint8_t>(4+n),1},[](const auto&){});}
    auto& plain=f.current->bank_items();plain.commit(unique_receipt(6),{plain.load(1,f.character),Op::Deposit,0,5,7,7});
    auto& repo=f.current->mixed_bank();const auto initial=repo.load(1,f.character),peer=repo.load(2,f.peer);const auto bag=initial.base.bag;
    unsigned receipt=10,exchanges=0;
    for(unsigned a=2;a<8;++a)for(unsigned b=2;b<8;++b)if(a!=b){auto before=repo.load(1,f.character);MRepo::Request request{before,0,static_cast<std::uint8_t>(a),static_cast<std::uint8_t>(b),static_cast<std::uint8_t>(before.base.vault[a].count)};const auto plan=repo.plan(request);unsigned prepared=0;
        auto result=repo.commit(unique_receipt(receipt++),request,[&](const auto& p){require(p==plan,"Actual prepare plan differs");++prepared;});require(result==plan&&prepared==1&&repo.load(1,f.character)==plan.after,"Actual mixed writer differs from plan");require(result.after.base.bag==bag&&repo.load(2,f.peer)==peer,"Mixed swap changed protected bag/other owner");
        require(result.after.base.vault[a].item_id==before.base.vault[b].item_id&&result.after.base.vault[b].item_id==before.base.vault[a].item_id,"Occupied whole-cell swap flattened");++exchanges;
        const auto swapped=repo.load(1,f.character);const MRepo::Request reverse{swapped,0,static_cast<std::uint8_t>(a),static_cast<std::uint8_t>(b),static_cast<std::uint8_t>(swapped.base.vault[a].count)};repo.commit(unique_receipt(receipt++),reverse,[](const auto&){});
        const auto restored=repo.load(1,f.character);require(restored.base.vault[a].item_id==before.base.vault[a].item_id&&restored.base.vault[b].item_id==before.base.vault[b].item_id,"Reverse ordered swap did not restore original family pair");
    }
    require(exchanges==30,"Six-family ordered occupied swaps incomplete");
    const auto correct=repo.load(1,f.character);const MRepo::Request request{correct,0,2,49,static_cast<std::uint8_t>(correct.base.vault[2].count)};const auto plan=repo.plan(request);
    f.sql("CREATE TRIGGER mixed_adapter_poison AFTER INSERT ON character_bank_mixed_receipts BEGIN UPDATE character_bank_foreign_metadata SET provenance='late-tail-poison' WHERE character_id=NEW.character_id; END");const auto before=tables(f.raw.get());rejects([&]{repo.commit(unique_receipt(99),request,[](const auto&){});});require(tables(f.raw.get())==before,"Actual writer did not rollback full scalar/metadata/receipt after injected unrelated tail mutation");f.sql("DROP TRIGGER mixed_adapter_poison");
    require(repo.commit(unique_receipt(99),request,[](const auto&){}).after==plan.after,"Same legal plan failed after trigger removal");const auto saved=tables(f.raw.get());rejects([&]{repo.commit(unique_receipt(99),request,[](const auto&){});});require(saved==tables(f.raw.get()),"Replay changed data");
    const auto stale=repo.load(1,f.character);f.sql("UPDATE diagnostic_inventory_slots SET revision=revision+1 WHERE character_id=1 AND slot=44");const auto changed=tables(f.raw.get());rejects([&]{repo.commit(unique_receipt(100),{stale,0,49,2,static_cast<std::uint8_t>(stale.base.vault[49].count)},[](const auto&){});});require(tables(f.raw.get())==changed,"Full50 stale snapshot wrote data");
    require(number(f.raw.get(),"SELECT count(*) FROM character_bank_mixed_receipts")==61,"Actual receipt count incomplete");require(dump(f.raw.get(),"PRAGMA foreign_key_check").empty(),"Mixed writer foreign key failure");
}
void mixed_gate(){
    std::ifstream file(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/releases/town-chat-welcome-20260924/server-config.json");require(file.good(),"Formal config unavailable");nlohmann::json config;file>>config;config["world"].erase("owned_mixed_bank");File temp;const auto path=temp.directory/"server-config.json";auto parse=[&]{std::ofstream out(path);out<<config.dump();out.close();return Config::load(path);};require(!parse().owned_mixed_bank_enabled,"Mixed not default off");config["world"]["owned_mixed_bank"]={{"enabled",true}};require(parse().owned_mixed_bank_enabled,"Valid mixed gate refused");
    const auto error=[&](const char* text){bool failed=false;try{parse();}catch(const std::runtime_error& e){require(e.what()==std::string(text),"Wrong config error");failed=true;}require(failed,"Bad mixed config accepted");};config["world"]["owned_mixed_bank"]["enabled"]="true";error("Owned mixed bank bool required");config["world"]["owned_mixed_bank"]["enabled"]=true;config["world"]["owned_foreign_bank"]["enabled"]=false;error("Owned mixed bank requires authenticated native world and owned foreign bank");
}
}
int main(){try{fresh_mixed();actual_writer();mixed_gate();std::cout<<"PASS CUSTOM0070 actual SqliteDatabase schema46 empty migration, original1354/1259/71 catalogs, six-family30 occupied ordered swaps, full20/provenance conservation, full50 CAS, other owner intact, actual postwrite rollback/replay/config; not live acceptance\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
