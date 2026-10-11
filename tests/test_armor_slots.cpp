#include "db/SqliteArmorSlotRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include "db/SqliteWeaponSlotRepository.h"
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>

using namespace god2;
namespace {
void require(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
template<class F>void rejects(F&& call){try{call();}catch(const DatabaseError&){return;}throw std::runtime_error("Expected armor rejection");}
std::string dump(sqlite3* db,const std::string& query){
    sqlite3_stmt* raw=nullptr;sqlite_detail::check(db,sqlite3_prepare_v2(db,query.c_str(),-1,&raw,nullptr));
    std::unique_ptr<sqlite3_stmt,decltype(&sqlite3_finalize)> guard(raw,sqlite3_finalize);std::string result;
    for(;;){const auto state=sqlite3_step(raw);if(state==SQLITE_DONE)break;require(state==SQLITE_ROW,"Dump query failed");
        for(int i=0;i<sqlite3_column_count(raw);++i){const auto type=sqlite3_column_type(raw,i);const auto* ptr=type==SQLITE_BLOB?sqlite3_column_blob(raw,i):sqlite3_column_text(raw,i);const auto size=sqlite3_column_bytes(raw,i);result+=std::to_string(type)+":"+std::to_string(size)+":";if(size)result.append(static_cast<const char*>(ptr),static_cast<std::size_t>(size));result+=';';}result+='\n';}
    return result;
}
std::optional<std::uint8_t> mapping(std::uint16_t item){
    // Synthetic mapping operands only; tests do not qualify real EQU/TEQ IDs.
    switch(item){case 60001:case 60003:return 30;case 60002:return 31;case 60004:return 32;case 60005:return 33;default:return {};}
}
struct Fixture{
    sqlite3* raw{};std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> db{nullptr,sqlite3_close_v2};std::array<std::uint64_t,2> ids{};
    Fixture(){require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Open failed");db.reset(raw);sql("PRAGMA foreign_keys=ON");auto migrations=default_sqlite_migrations();require(migrations.back().version>=42,"Armor migration boundary");while(migrations.back().version>=42)migrations.pop_back();SqliteMigrationManager(raw,std::move(migrations)).migrate();
        sql("INSERT INTO accounts(id,username,password_hash) VALUES(1,'armor-a','hash'),(2,'armor-b','hash')");SqliteRecoveredCharacterRepository characters(raw);
        for(unsigned n=0;n<2;++n){std::array<std::uint8_t,40> profile{};profile[0]=static_cast<std::uint8_t>('A'+n);ids[n]=characters.create(n+1,profile).id;
            for(unsigned i=0;i<50;++i){sqlite_detail::Statement insert(raw,"INSERT INTO diagnostic_inventory_slots(character_id,slot,item_id,count,revision,source_sha256,design_id) VALUES(?,?,0,0,1,?,'CUSTOM-0015')");insert.bind_id(1,ids[n]);insert.bind(2,i);insert.bind(3,SqliteArmorSlotRepository::source_sha256);insert.done();}}
        sql("CREATE TABLE armor_test_money(character_id INTEGER PRIMARY KEY,amount INTEGER NOT NULL);INSERT INTO armor_test_money VALUES(1,1234),(2,5678)");
    }
    void sql(const std::string& value){sqlite_detail::execute(raw,value);}
    SqliteArmorSlotRepository repo(){return {raw,mapping};}
    void install(){sql(SqliteArmorSlotRepository::schema());}
    std::string rows(){sqlite_detail::Statement tables(raw,"SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name");std::string result;while(tables.row()){const auto name=tables.text(0);require(name.find('"')==std::string::npos,"Unsafe fixture table");result+=name+'\n'+dump(raw,"SELECT * FROM \""+name+"\" ORDER BY rowid");}return result;}
    void scalar(unsigned slot,std::uint16_t item,unsigned count,std::uint64_t revision=1,unsigned owner=0){
        sqlite_detail::Statement write(raw,"UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=? WHERE character_id=? AND slot=?");write.bind(1,item);write.bind(2,count);write.bind_id(3,revision);write.bind_id(4,ids[owner]);write.bind(5,slot);write.done();require(sqlite3_changes(raw)==1,"Scalar fixture failed");
    }
    std::array<std::uint8_t,20> armor(unsigned slot,std::uint16_t item,std::uint8_t fill,std::uint64_t revision=1,unsigned owner=0){
        scalar(slot,item,1,revision,owner);std::array<std::uint8_t,20> bytes;bytes.fill(fill);bytes[0]=static_cast<std::uint8_t>(item);bytes[1]=static_cast<std::uint8_t>(item>>8);bytes[2]=static_cast<std::uint8_t>((fill&0xc0)|2);
        sqlite_detail::Statement insert(raw,"INSERT INTO character_armor_slot_metadata(character_id,slot,logical20,revision,origin,provenance,source_sha256,client_sha256,design_id) VALUES(?,?,?,?,'CUSTOM_TEST_NOT_NATIVE',?,?,?,'CUSTOM-0066')");
        insert.bind_id(1,ids[owner]);insert.bind(2,slot);insert.bind_blob(3,bytes);insert.bind_id(4,revision);insert.bind(5,std::string("isolated-armor-")+std::to_string(fill));insert.bind(6,SqliteArmorSlotRepository::source_sha256);insert.bind(7,SqliteArmorSlotRepository::client_sha256);insert.done();return bytes;
    }
    void weapon(unsigned slot,std::uint16_t item=0,std::uint64_t revision=1){
        scalar(slot,item,item?1:0,revision);std::array<std::uint8_t,20> bytes{};bytes[0]=static_cast<std::uint8_t>(item);bytes[1]=static_cast<std::uint8_t>(item>>8);bytes[19]=0x91;
        sqlite_detail::Statement insert(raw,"INSERT INTO character_weapon_slot_metadata(character_id,slot,logical20,revision,origin,provenance,source_sha256,client_sha256,design_id) VALUES(?,?,?,?,?,'isolated-old-weapon',?,'6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98','CUSTOM-0046')");
        insert.bind_id(1,ids[0]);insert.bind(2,slot);insert.bind_blob(3,bytes);insert.bind_id(4,revision);insert.bind(5,std::string(item?"CUSTOM_TEST_NOT_NATIVE":"EMPTY_SLOT_POLICY"));insert.bind(6,SqliteArmorSlotRepository::source_sha256);insert.done();
    }
};
void schema_and_moves(){
    Fixture f;auto repo=f.repo();const auto before=f.rows();const auto changes=sqlite3_total_changes(f.raw);
    rejects([&]{repo.load_snapshot(1,f.ids[0]);});require(f.rows()==before&&sqlite3_total_changes(f.raw)==changes,"Reader installed schema or created capacity");
    f.install();require(f.rows().find("character_armor_slot_metadata\n")!=std::string::npos,"Armor table absent");
    const auto a=f.armor(0,60001,0xa1,3),b=f.armor(1,60003,0xb2,9);f.armor(0,60002,0xc3,4,1);f.weapon(5);f.weapon(34,1,7);
    const auto initial=repo.load_snapshot(1,f.ids[0]),other=repo.load_snapshot(2,f.ids[1]);const auto money=dump(f.raw,"SELECT * FROM armor_test_money ORDER BY character_id");
    const auto equip=repo.move(initial,0,30,[](const auto&){});
    require(equip.source.count==0&&!equip.source.metadata_present&&equip.source.revision==4&&equip.destination.logical20==a&&equip.destination.revision==2&&equip.destination.provenance==initial.armor[0].provenance,"Equip lost complete instance/physical revision");
    require(repo.load_snapshot(1,f.ids[0])==equip.after,"Equip after snapshot mismatch");
    const auto swap=repo.move(equip.after,1,30,[](const auto&){});
    require(swap.source.logical20==a&&swap.destination.logical20==b&&swap.source.revision==10&&swap.destination.revision==3,"Same-part exchange lost20 bytes or moved revisions");
    const auto unequip=repo.move(swap.after,30,5,[](const auto&){});
    require(unequip.destination.logical20==b&&unequip.destination.revision==2&&!unequip.source.metadata_present&&!repo.load_snapshot(1,f.ids[0]).weapons.empty(),"Unequip/empty overlay retirement failed");
    require(unequip.after.weapons.size()==1&&unequip.after.weapons[0].slot==34,"Armor retired occupied foreign weapon or retained empty overlay");
    require(repo.load_snapshot(2,f.ids[1])==other&&dump(f.raw,"SELECT * FROM armor_test_money ORDER BY character_id")==money,"Armor changed another owner or money");
    const auto current=repo.load_snapshot(1,f.ids[0]);const auto unchanged=f.rows();
    rejects([&]{repo.move(initial,0,30,[](const auto&){});});require(f.rows()==unchanged,"Replay mutated rows");
    rejects([&]{repo.load_snapshot(2,f.ids[0]);});
    auto stale=current;++stale.scalar[29]->revision;rejects([&]{repo.move(stale,5,30,[](const auto&){});});
    stale=current;++stale.scalar[44]->revision;rejects([&]{repo.move(stale,5,30,[](const auto&){});});
    stale=current;stale.armor.back().logical20[19]^=1;rejects([&]{repo.move(stale,5,30,[](const auto&){});});require(f.rows()==unchanged,"Full stale snapshot mutated state");
}
void rejection_and_rollback(){
    Fixture f;f.install();f.armor(0,60001,0xab,7);f.armor(1,60002,0xcd,3);f.weapon(2,1);f.weapon(34,1);auto repo=f.repo();auto saved=repo.load_snapshot(1,f.ids[0]);
    const auto unchanged=[&](const auto& fn){const auto rows=f.rows();rejects(fn);require(f.rows()==rows,"Rejected armor operation wrote rows");};
    for(const auto dst:{0,2,31,34,42,255})unchanged([&]{repo.move(saved,0,static_cast<std::uint8_t>(dst),[](const auto&){});});
    unchanged([&]{repo.move(saved,30,0,[](const auto&){});});unchanged([&]{repo.move(saved,0,30,{});});
    auto max=saved;max.scalar[0]->revision=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());max.armor[0].revision=max.scalar[0]->revision;rejects([&]{repo.plan(max,0,30);});
    max=saved;max.scalar[30]->revision=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());rejects([&]{repo.plan(max,0,30);});
    auto boundary=saved;boundary.scalar[0]->revision=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max())-1;boundary.armor[0].revision=boundary.scalar[0]->revision;boundary.scalar[30]->revision=boundary.scalar[0]->revision;
    const auto last=repo.plan(boundary,0,30);require(last.source.revision==boundary.scalar[0]->revision+1&&last.destination.revision==last.source.revision,"Armor last valid revisions rejected");
    for(const auto sql:{
        "CREATE TRIGGER injected BEFORE DELETE ON character_armor_slot_metadata BEGIN SELECT RAISE(IGNORE); END",
        "CREATE TRIGGER injected BEFORE UPDATE ON diagnostic_inventory_slots WHEN NEW.slot=30 BEGIN SELECT RAISE(ABORT,'second scalar'); END",
        "CREATE TRIGGER injected BEFORE UPDATE ON diagnostic_inventory_slots WHEN NEW.slot=30 BEGIN SELECT RAISE(IGNORE); END",
        "CREATE TRIGGER injected BEFORE INSERT ON character_armor_slot_metadata WHEN NEW.slot=30 BEGIN SELECT RAISE(IGNORE); END",
        "CREATE TRIGGER injected AFTER INSERT ON character_armor_slot_metadata WHEN NEW.slot=30 BEGIN UPDATE diagnostic_inventory_slots SET revision=revision+1 WHERE character_id=NEW.character_id AND slot=29; END",
        "CREATE TRIGGER injected AFTER INSERT ON character_armor_slot_metadata WHEN NEW.slot=30 BEGIN UPDATE diagnostic_inventory_slots SET revision=revision+1 WHERE character_id=NEW.character_id AND slot=44; END",
        "CREATE TRIGGER injected AFTER INSERT ON character_armor_slot_metadata WHEN NEW.slot=30 BEGIN UPDATE character_weapon_slot_metadata SET provenance='corrupt-foreign' WHERE character_id=NEW.character_id AND slot=34; END"}){
        f.sql(sql);unchanged([&]{repo.move(saved,0,30,[](const auto&){});});f.sql("DROP TRIGGER injected");
    }
    {const auto rows=f.rows();try{repo.move(saved,0,30,[](const auto&){throw std::runtime_error("Projection failure");});throw std::logic_error("Expected preparation failure");}catch(const std::runtime_error& error){require(std::string(error.what())=="Projection failure","Wrong preparation failure");}require(f.rows()==rows,"Projection failure escaped rollback");}
    unchanged([&]{repo.move(saved,0,30,[&](const auto&){f.sql("UPDATE character_armor_slot_metadata SET provenance='post-prepare-corruption' WHERE slot=30");});});
    SqliteRecoveredCharacterRepository characters(f.raw);const auto resources=characters.commit_resources(1,f.ids[0],{},{52,120,2,80,0,"CUSTOM-0012"});const auto battle=characters.reserve_battle(1,f.ids[0],resources);
    unchanged([&]{repo.move(saved,0,30,[](const auto&){});});characters.settle_battle(1,f.ids[0],battle,resources,resources,true,0);
    const auto settled_resources=characters.load_resources(1,f.ids[0]).value();bool injected_battle=false;
    unchanged([&]{repo.move(saved,0,30,[&](const auto&){sqlite_detail::Statement insert(f.raw,"INSERT INTO battle_reservations(character_id,resource_revision,design_id) VALUES(?,?,'CUSTOM-0012')");insert.bind_id(1,f.ids[0]);insert.bind_id(2,settled_resources.revision);insert.done();injected_battle=true;});});
    require(injected_battle,"Post-projection pending-battle rollback was not exercised");
    // Missing explicit equipment capacity is absent and cannot be created.
    f.sql("DELETE FROM diagnostic_inventory_slots WHERE slot=30");saved=repo.load_snapshot(1,f.ids[0]);unchanged([&]{repo.move(saved,0,30,[](const auto&){});});
}
void schema_collision_and_corruption(){
    Fixture f;f.install();f.armor(0,60001,0xaa);auto repo=f.repo();const auto valid=repo.load_snapshot(1,f.ids[0]);
    const auto unchanged=[&](const auto& call){const auto rows=f.rows();rejects(call);require(f.rows()==rows,"Schema rejection changed state");};
    unchanged([&]{f.weapon(0,60001);});
    unchanged([&]{f.sql("INSERT INTO character_teleport_gem_metadata SELECT character_id,slot,logical20,revision,origin,provenance,source_sha256,'CUSTOM-0057' FROM character_armor_slot_metadata WHERE slot=0");});
    unchanged([&]{f.sql("UPDATE character_armor_slot_metadata SET slot=1 WHERE slot=0");});
    unchanged([&]{f.sql("UPDATE character_armor_slot_metadata SET logical20=zeroblob(20) WHERE slot=0");});
    unchanged([&]{f.sql("UPDATE character_armor_slot_metadata SET revision=2 WHERE slot=0");});
    unchanged([&]{f.sql("UPDATE character_armor_slot_metadata SET logical20=zeroblob(19) WHERE slot=0");});
    unchanged([&]{f.sql("UPDATE character_armor_slot_metadata SET client_sha256=printf('%064d',0) WHERE slot=0");});
    require(repo.load_snapshot(1,f.ids[0])==valid,"Schema checks lost valid instance");
    // A scalar change with no corresponding metadata is observed as corruption,
    // not repaired, recategorized or granted by the read path.
    f.sql("UPDATE diagnostic_inventory_slots SET revision=revision+1 WHERE slot=0");const auto rows=f.rows();rejects([&]{repo.load_snapshot(1,f.ids[0]);});require(f.rows()==rows,"Reader repaired corrupt instance");
}
void existing_weapon_compatibility(){
    Fixture f;f.install();f.armor(0,60001,0xa1,3);f.weapon(34,1,7);
    auto armor=f.repo();const auto before=armor.load_snapshot(1,f.ids[0]);
    SqliteWeaponSlotRepository weapons(f.raw,[](std::uint16_t item){return item==1;});
    const auto source=weapons.load(1,f.ids[0],34),destination=weapons.load(1,f.ids[0],3);
    require(source&&destination,"Existing weapon route no longer reads owned cells");
    const auto moved=weapons.move(1,f.ids[0],*source,*destination,[](const auto&){});
    const auto after=armor.load_snapshot(1,f.ids[0]);
    require(after.armor==before.armor&&after.weapons.size()==2&&moved.destination.item_id==1&&moved.destination.logical20==source->logical20,"Armor schema broke existing old-client weapon transfer");
    const auto rows=f.rows();rejects([&]{armor.move(before,0,30,[](const auto&){});});require(f.rows()==rows,"Armor ignored concurrently changed foreign overlay");
    const auto equip=armor.move(after,0,30,[](const auto&){});require(equip.after.weapons==after.weapons,"Armor equip mutated existing weapon overlays");
}
}
int main(){try{schema_and_moves();rejection_and_rollback();schema_collision_and_corruption();existing_weapon_compatibility();std::cout<<"Armor full50-slot/overlay CAS, occupied20 bytes, revisions, exclusivity, rollback, owner/money/protected-slot isolation and existing weapon compatibility passed; native mapping/live acceptance OPEN\n";}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
