// CUSTOM-0071 actual SqliteDatabase writer/qualifier gate. Accepted helpers are
// included for observation only; the old bank fixture is never instantiated.
#define main accepted_armor_adapter_for_discard_main
#include "storage_owned_armor_bank_adapter_0067.cpp"
#undef main
#include "core/Config.h"
#include "handlers/InventoryDiscardService.h"
#include "protocol/RecoveredArmorSourceSlots.h"
#include "db/SqliteWeaponSlotRepository.h"

namespace {
using DRepo=SqliteOwnedInstanceDiscardRepository;
void discard_weapon_catalog(sqlite3* db){
    std::ifstream file(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/research/native-weapons-20260926/records.json");require(file.good(),"Qualified weapon source missing");nlohmann::json groups;file>>groups;
    require(groups.size()==2&&groups[0].size()==2&&groups[1].size()==1259,"Weapon denominator changed");sqlite_detail::Transaction transaction(db);
    for(unsigned group=0;group<2;++group)for(const auto& row:groups[group]){require(row.size()==10,"Weapon source width changed");sqlite_detail::Statement insert(db,group==0?"INSERT INTO native_weapon_sources VALUES(?,?,?,?,?,?,?,?,?,?)":"INSERT INTO native_weapon_rows VALUES(?,?,?,?,?,?,?,?,?,?)");
        for(int i=0;i<10;++i){if(group==1&&(i==6||i==8))insert.bind_blob(i+1,unhex(row[i].get<std::string>()));else if((group==0&&i==7)||(group==1&&i>=1&&i<=4))insert.bind(i+1,row[i].get<std::int64_t>());else insert.bind(i+1,row[i].get<std::string>());}insert.done();
    }transaction.commit();
}
void discard_med_catalog(sqlite3* db){
    std::ifstream file(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/research/owned-instance-trade-0069/native-med02-cache.json");require(file.good(),"Original MED02 cache missing");nlohmann::json data;file>>data;
    require(data["source"].size()==9&&data["rows"].size()==71,"MED denominator changed");sqlite_detail::Transaction transaction(db);sqlite_detail::Statement source(db,"INSERT INTO native_data_sources VALUES(?,?,?,?,?,?,?,?,?)");
    for(int i=0;i<9;++i){if(i==8)source.bind(i+1,data["source"][i].get<std::int64_t>());else source.bind(i+1,data["source"][i].get<std::string>());}source.done();
    for(const auto& row:data["rows"]){require(row.size()==11,"MED source width changed");sqlite_detail::Statement insert(db,"INSERT INTO native_med02_recovery_declarations VALUES(?,?,?,?,?,?,?,?,?,?,?)");for(int i=0;i<11;++i){if(i==5||i==6)insert.bind_blob(i+1,unhex(row[i].get<std::string>()));else if(i==0||i==4)insert.bind(i+1,row[i].get<std::string>());else insert.bind(i+1,row[i].get<std::int64_t>());}insert.done();}transaction.commit();
}
std::string discard_receipt(unsigned n){std::string result(64,'0');const auto tail=std::to_string(n);result.replace(64-tail.size(),tail.size(),tail);return result;}
struct DiscardAdapter {
    File file;SqliteDatabase current{file.path};Raw raw{nullptr,sqlite3_close_v2};std::array<std::uint64_t,2> ids{};
    DiscardAdapter(){current.initialize();current.migrate();raw=open(file.path);catalog(raw.get());discard_weapon_catalog(raw.get());discard_med_catalog(raw.get());
        sql("INSERT INTO accounts(id,username,password_hash) VALUES(1,'discard-prod0071-a','hash-a'),(2,'discard-prod0071-b','hash-b')");
        for(unsigned owner=0;owner<2;++owner){std::array<std::uint8_t,40> profile{};profile[0]=static_cast<std::uint8_t>('A'+owner);ids[owner]=current.recovered_characters().create(owner+1,profile).id;
            for(unsigned slot=0;slot<50;++slot){sqlite_detail::Statement insert(raw.get(),"INSERT INTO diagnostic_inventory_slots VALUES(?,?,0,0,1,?,'CUSTOM-0015')");insert.bind_id(1,ids[owner]);insert.bind(2,slot);insert.bind(3,SqliteArmorSlotRepository::source_sha256);insert.done();}}
        require(current.native_weapon_catalog().populated()&&current.native_armor_catalog().populated()&&current.native_supply_catalog().lookup(3107).has_value(),"Actual full1354/1259/71 qualification failed");
    }
    void sql(const std::string& text){sqlite_detail::execute(raw.get(),text);}
    DRepo& repo(){return current.instance_discards();}
    auto load(unsigned owner=0){return repo().load(owner+1,ids[owner]);}
    auto seed(unsigned owner,unsigned slot,std::uint16_t item,unsigned fill,unsigned charges=1){
        std::array<std::uint8_t,20> bytes{};bytes.fill(static_cast<std::uint8_t>(fill));bytes[0]=static_cast<std::uint8_t>(item);bytes[1]=static_cast<std::uint8_t>(item>>8);const auto armor=current.native_armor_catalog().equipment_slot(item);const auto weapon=current.native_weapon_catalog().lookup(item);
        sqlite_detail::Statement scalar(raw.get(),"UPDATE diagnostic_inventory_slots SET item_id=?,count=1,revision=7 WHERE character_id=? AND slot=?");scalar.bind(1,item);scalar.bind_id(2,ids[owner]);scalar.bind(3,slot);scalar.done();
        if(armor){bytes[2]=static_cast<std::uint8_t>(0xc0u|(item>=20000?26u:2u));sqlite_detail::Statement insert(raw.get(),"INSERT INTO character_armor_slot_metadata VALUES(?,?,?,7,'CUSTOM_TEST_NOT_NATIVE','isolated-production0071-full20',?,?,'CUSTOM-0066')");insert.bind_id(1,ids[owner]);insert.bind(2,slot);insert.bind_blob(3,bytes);insert.bind(4,SqliteArmorSlotRepository::source_sha256);insert.bind(5,SqliteArmorSlotRepository::client_sha256);insert.done();}
        else if(weapon){bytes[2]=static_cast<std::uint8_t>(0xc0u|(weapon->family=="WPN"?1u:25u));sqlite_detail::Statement insert(raw.get(),"INSERT INTO character_weapon_slot_metadata VALUES(?,?,?,7,'CUSTOM_TEST_NOT_NATIVE','isolated-production0071-full20',?,?,'CUSTOM-0046')");insert.bind_id(1,ids[owner]);insert.bind(2,slot);insert.bind_blob(3,bytes);insert.bind(4,SqliteArmorSlotRepository::source_sha256);insert.bind(5,SqliteWeaponSlotRepository::client_sha256);insert.done();}
        else {require(item==16055&&charges>=1&&charges<=10,"Invalid test typed key");bytes[2]=8;bytes[3]=static_cast<std::uint8_t>((charges<<1)|(fill&1u));sqlite_detail::Statement insert(raw.get(),"INSERT INTO character_teleport_gem_metadata VALUES(?,?,?,7,'CUSTOM_TEST_NOT_NATIVE','isolated-production0071-full20',?,'CUSTOM-0057')");insert.bind_id(1,ids[owner]);insert.bind(2,slot);insert.bind_blob(3,bytes);insert.bind(4,SqliteArmorSlotRepository::source_sha256);insert.done();}return bytes;
    }
    void absent_economy(){for(const auto* table:{"character_bank_item_slots","character_bank_armor_metadata","character_bank_foreign_metadata","character_trade_wallets"}){sqlite_detail::Statement exists(raw.get(),"SELECT 1 FROM sqlite_schema WHERE type='table' AND name=?");exists.bind(1,table);if(exists.row())require(dump(raw.get(),std::string("SELECT * FROM ")+table).empty(),"Discard allocated unrelated economic state");}}
};
void discard_fresh(){
    File file;SqliteDatabase current(file.path);rejects([&]{(void)current.instance_discards();});current.initialize();rejects([&]{(void)current.instance_discards();});current.migrate();auto raw=open(file.path);require(number(raw.get(),"SELECT version FROM schema_migrations WHERE version=47")==47,"Actual47 missing");require(number(raw.get(),"SELECT max(version) FROM schema_migrations")==default_sqlite_migrations().back().version,"Latest additive migration missing");
    for(const auto* table:{"accounts","recovered_characters","diagnostic_inventory_slots","character_owned_instance_discard_receipts","character_bank_item_slots"})require(dump(raw.get(),std::string("SELECT * FROM ")+table).empty(),"Migration47 seeded players/items/bank");const auto saved=tables(raw.get()),ddl=objects(raw.get());rejects([&]{current.instance_discards().load(1,1);});current.migrate();require(saved==tables(raw.get())&&ddl==objects(raw.get()),"Read/repeated migration mutated state");
}
void discard_actual_writer(){
    // Two owners, native four armor parts in both families plus WPN/TWP and
    // gem displayed1/10. Exact current production qualifiers, not test lookups.
    unsigned count=0;for(unsigned owner=0;owner<2;++owner)for(const auto key:{1201u,1001u,1501u,1601u,20201u,20001u,20501u,20601u,1u,19001u,16055u})for(const auto charges:key==16055?std::vector<unsigned>{1,10}:std::vector<unsigned>{1}){
        DiscardAdapter f;const auto slot=static_cast<std::uint8_t>(count%2?29:0);const auto bytes=f.seed(owner,slot,static_cast<std::uint16_t>(key),0xa5,charges);const auto retained=f.seed(owner,slot?0:29,static_cast<std::uint16_t>(key),0xb6,charges);f.seed(1-owner,4,1,0xc7);f.seed(owner,34,19001,0xd8);const auto before=f.load(owner),peer=f.load(1-owner);const DRepo::Request request{before,static_cast<std::uint16_t>(key),slot,1};const auto planned=f.repo().plan(request);unsigned prepared=0;
        const auto result=f.repo().commit(discard_receipt(1),request,[&](const auto& p){require(p==planned,"Actual plan changed during preparation");++prepared;});require(prepared==1&&result==planned&&result.removed20==bytes&&f.load(owner)==planned.after&&f.load(1-owner).bag==peer.bag,"Actual writer discarded wrong full20/other owner");require(bytes!=retained,"Test samekey instances must differ");
        sqlite_detail::Statement audit(f.raw.get(),"SELECT logical20,operation,source,quantity,instance_design_id FROM character_owned_instance_discard_receipts");require(audit.row(),"Actual destruction audit missing");const auto removed=audit.blob(0,20,20);require(std::equal(removed.begin(),removed.end(),bytes.begin())&&audit.integer(1)==39&&audit.integer(2)==slot&&audit.integer(3)==1&&!audit.text(4).empty()&&!audit.row(),"Actual destruction audit mismatch");
        const auto saved=tables(f.raw.get());rejects([&]{f.repo().commit(discard_receipt(1),request,[](const auto&){});});require(saved==tables(f.raw.get()),"Replay changed state");f.absent_economy();require(dump(f.raw.get(),"PRAGMA foreign_key_check").empty(),"Actual discard FK failure");++count;
    }require(count==24,"Actual whole typed category denominator changed");
}
void discard_actual_rollback_and_scalar(){
    DiscardAdapter f;f.seed(0,0,1,0xa1);f.seed(0,29,1,0xb2);f.seed(1,4,16055,0xc3);const auto initial=f.load();const DRepo::Request request{initial,1,0,1};
    // SQLite triggers run inside the ACTUAL SqliteDatabase transaction. The
    // specific post-receipt readback error proves this isn't a prewrite denial.
    for(const auto* body:{"UPDATE accounts SET password_hash='poison' WHERE id=2;","UPDATE diagnostic_inventory_slots SET revision=revision+1 WHERE character_id=2 AND slot=4;","UPDATE character_weapon_slot_metadata SET provenance='poison' WHERE character_id=NEW.character_id AND slot=29;"}){
        f.sql(std::string("CREATE TRIGGER discard_adapter_poison AFTER INSERT ON character_owned_instance_discard_receipts BEGIN ")+body+" END");const auto saved=tables(f.raw.get());std::string error;try{f.repo().commit(discard_receipt(2),request,[](const auto&){});}catch(const DatabaseError& e){error=e.what();}require(error=="Owned discard whole readback/other owner/currency/history conflict","Actual postwrite trigger was not detected at readback");require(saved==tables(f.raw.get()),"Actual trigger did not rollback all rows");f.sql("DROP TRIGGER discard_adapter_poison");
    }
    const auto planned=f.repo().plan(request);require(f.repo().commit(discard_receipt(2),request,[](const auto&){}).after==planned.after,"Valid actual writer blanket rejected after trigger removal");
    const auto stale=f.load();f.sql("UPDATE diagnostic_inventory_slots SET revision=revision+1 WHERE character_id=1 AND slot=44");const auto changed=tables(f.raw.get());rejects([&]{f.repo().commit(discard_receipt(3),{stale,1,29,1},[](const auto&){});});require(changed==tables(f.raw.get()),"Actual full50 stale CAS mutated rows");
    f.sql("UPDATE diagnostic_inventory_slots SET item_id=3107,count=7 WHERE character_id=1 AND slot=5");auto* scalar=dynamic_cast<SqliteRecoveredCharacterRepository*>(&f.current.recovered_characters());require(scalar,"Actual scalar adapter unavailable");InventoryDiscardService legacy(*scalar,[&](const auto& s){return f.current.native_supply_catalog().lookup(s.item_id).has_value();});const auto typed=f.load().bag;const auto first=legacy.discard(1,f.ids[0],{3107,5,3},*typed.scalar[5]);require(first.slot.count==4&&first.slot.item_id==3107,"Unchanged0061 partial MED failed");const auto second=legacy.discard(1,f.ids[0],{3107,5,4},first.slot);require(second.slot.count==0&&second.slot.item_id==0,"Unchanged0061 whole MED failed");require(f.load().bag.weapons==typed.weapons&&f.load().bag.gems==typed.gems&&f.load().bag.armor==typed.armor,"Scalar discard changed typed instances");f.absent_economy();
}
void discard_config(){
    std::ifstream file(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/releases/town-chat-welcome-20260924/server-config.json");require(file.good(),"Formal config unavailable");nlohmann::json config;file>>config;config["world"].erase("owned_instance_discard");File temp;const auto path=temp.directory/"server-config.json";const auto parse=[&]{std::ofstream out(path);out<<config.dump();out.close();return Config::load(path);};require(!parse().owned_instance_discard_enabled,"Discard not default off");config["world"]["owned_instance_discard"]={{"enabled",true}};require(parse().owned_instance_discard_enabled&&!parse().owned_weapon_transfers_enabled,"Actual default-weapon-off valid discard opt-in denied");const auto error=[&](const char* text){bool denied=false;try{parse();}catch(const std::runtime_error& e){require(e.what()==std::string(text),"Wrong discard config error");denied=true;}require(denied,"Invalid discard configuration accepted");};config["world"]["owned_instance_discard"]["enabled"]=1;error("Owned instance discard bool required");config["world"]["owned_instance_discard"]["enabled"]=true;config["world"].erase("owned_armor_bank");config["world"].erase("owned_foreign_bank");config["world"].erase("owned_mixed_bank");config["world"].erase("owned_instance_trade");config["world"]["owned_armor_transfers"]["enabled"]=false;error("Owned instance discard requires authenticated native world and complete owned bag projection");
}
}
int main(){try{discard_fresh();discard_actual_writer();discard_actual_rollback_and_scalar();discard_config();std::cout<<"PASS CUSTOM0071 actual SqliteDatabase/schema47: empty migration, full1354/1259/71 catalogs, two-owner24 typed whole discards, samekey complete20/source0/29, postreceipt unrelated account/player/tail rollback, full50 stale/replay, unchanged0061 MED partial/whole, defaultoff/dependencies/no bank grants; not live acceptance\n";return 0;}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
