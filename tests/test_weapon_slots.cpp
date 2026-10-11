#include "db/SqliteWeaponSlotRepository.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteDatabase.h"
#include "db/SqliteSupport.h"
#include "db/SqlitePlayerAppearanceRepository.h"
#include "handlers/RecoveredOwnedPlayerAppearance.h"
#include <algorithm>
#include <filesystem>
#include <iostream>
#include <memory>
#include <random>
#include <stdexcept>
#include <limits>
namespace {
using god2::SqliteWeaponSlotRepository;
using god2::StoredWeaponSlot;
void require(bool value,const char* text){if(!value)throw std::runtime_error(text);}
template<class F>void rejects(F f){try{f();}catch(const std::exception&){return;}throw std::runtime_error("Expected weapon rejection");}
struct Close{void operator()(sqlite3* db)const{sqlite3_close_v2(db);}};
struct Fixture {
 std::unique_ptr<sqlite3,Close> db;std::uint64_t character{};
 explicit Fixture(const std::string& path=":memory:",bool initialize=true){sqlite3* raw=nullptr;require(sqlite3_open(path.c_str(),&raw)==SQLITE_OK,"Open weapon fixture");db.reset(raw);sql("PRAGMA foreign_keys=ON");if(!initialize){character=1;return;}
  god2::SqliteMigrationManager(raw,god2::default_sqlite_migrations()).migrate();sql("INSERT INTO accounts(id,username,password_hash) VALUES(1,'weapon-owner','test'),(2,'other','test')");
  std::array<std::uint8_t,40> profile{};profile[0]='W';character=god2::SqliteRecoveredCharacterRepository(raw).create(1,profile).id;
 }
 void sql(const char* text){god2::sqlite_detail::execute(db.get(),text);}
 // Current WPN IDs1/2, but these20-byte instances are explicitly synthetic.
 SqliteWeaponSlotRepository repo(){return SqliteWeaponSlotRepository(db.get(),[](std::uint16_t id){return id==1||id==2;});}
 StoredWeaponSlot get(std::uint8_t slot){auto r=repo().load(1,character,slot);require(r.has_value(),"Missing expected weapon cell");return *r;}
 void scalar(std::uint8_t slot,std::uint16_t item=0,std::uint8_t count=0){god2::sqlite_detail::Statement q(db.get(),"INSERT INTO diagnostic_inventory_slots VALUES(?,?,?,?,1,?,'CUSTOM-0015')");q.bind_id(1,character);q.bind(2,slot);q.bind(3,item);q.bind(4,count);q.bind(5,SqliteWeaponSlotRepository::source_sha256);q.done();}
 void weapon(std::uint8_t slot,std::uint16_t key,std::uint8_t tail){scalar(slot,key,1);std::array<std::uint8_t,20> bytes{};bytes.fill(tail);bytes[0]=static_cast<std::uint8_t>(key);bytes[1]=static_cast<std::uint8_t>(key>>8);
  god2::sqlite_detail::Statement q(db.get(),"INSERT INTO character_weapon_slot_metadata VALUES(?,?,?,1,'CUSTOM_TEST_NOT_NATIVE',?,?,?,'CUSTOM-0046')");q.bind_id(1,character);q.bind(2,slot);q.bind_blob(3,bytes);q.bind(4,std::string("isolated-weapon-slot-test-")+std::to_string(key));q.bind(5,SqliteWeaponSlotRepository::source_sha256);q.bind(6,SqliteWeaponSlotRepository::client_sha256);q.done();
 }
 std::string snapshot(){std::string out;for(const char* query:{
  "SELECT CAST(character_id AS TEXT),CAST(slot AS TEXT),CAST(item_id AS TEXT),CAST(count AS TEXT),CAST(revision AS TEXT),source_sha256,design_id FROM diagnostic_inventory_slots ORDER BY character_id,slot",
  "SELECT CAST(character_id AS TEXT),CAST(slot AS TEXT),hex(logical20),CAST(revision AS TEXT),origin,provenance,source_sha256,client_sha256,design_id FROM character_weapon_slot_metadata ORDER BY character_id,slot"}){
   god2::sqlite_detail::Statement q(db.get(),query);const int columns=out.empty()?7:9; // table delimiter below makes second choice stable
   while(q.row())for(int i=0;i<columns;++i){auto s=q.text(i);out+=std::to_string(s.size())+":"+s;}out+='|';
  }return out;}
 template<class F>void unchanged_rejection(F call){auto before=snapshot();rejects(call);require(snapshot()==before,"Rejected weapon operation changed DB");}
};
auto prepared=[](const god2::WeaponSlotMove&){};
void moves_and_preservation(){Fixture f;f.weapon(0,1,0xa7);f.weapon(1,2,0xc9);f.scalar(5);f.scalar(34);f.scalar(6,5569,1);f.scalar(7,6001,12);auto r=f.repo();
 require(!r.load(1,f.character,6)&&!r.load(1,f.character,7),"Scalar consumable projected as weapon");auto saved=r.load_saved(1,f.character);require(saved.size()==4,"Mixed bag projection should include only known weapons/empties");
 auto a=f.get(0),b=f.get(1),empty=f.get(34);require(!empty.metadata_present&&empty.logical20==std::array<std::uint8_t,20>{}&&empty.origin=="EMPTY_SLOT_POLICY","Missing empty metadata baseline");
 int encoded=0;auto equip=r.move(1,f.character,a,empty,[&](const auto& next){++encoded;require(sqlite3_get_autocommit(f.db.get())==0,"Encoder must run before commit");require(next.destination.logical20==a.logical20,"Encoder lost metadata");});
 require(encoded==1&&equip.destination.slot==34&&equip.destination.revision==2&&equip.source.revision==2,"Equip revision/slot");
 require(equip.source.logical20[0]==0&&equip.source.logical20[1]==0&&std::equal(a.logical20.begin()+2,a.logical20.end(),equip.source.logical20.begin()+2),"Clear must retain original18tails");
 require(equip.source.origin=="EMPTY_SLOT_POLICY"&&equip.destination.provenance==a.provenance&&equip.destination.origin==a.origin,"Equip provenance");
 auto swap=r.move(1,f.character,b,equip.destination,prepared);require(swap.source.logical20==a.logical20&&swap.destination.logical20==b.logical20&&swap.source.provenance==a.provenance&&swap.destination.provenance==b.provenance,"Swap changed owned instances");
 auto unequip=r.move(1,f.character,swap.destination,equip.source,prepared);require(unequip.destination.logical20==b.logical20&&unequip.destination.slot==0&&unequip.source.origin=="EMPTY_SLOT_POLICY","Unequip to existing empty overlay");
 auto again=r.move(1,f.character,unequip.destination,unequip.source,prepared);require(again.destination.logical20==b.logical20&&again.source.logical20[2]==b.logical20[2],"Empty retirement trigger lost instance tails");
 f.unchanged_rejection([&]{r.move(1,f.character,a,empty,prepared);});
 // Scalar usage by existing nonweapon routes retires only inactive empty overlay.
 f.sql("UPDATE diagnostic_inventory_slots SET item_id=5569,count=1,revision=revision+1 WHERE slot=0");require(!r.load(1,f.character,0),"Reused empty overlay interfered with scalar map");require(f.get(34).item_id==2,"Empty retirement deleted occupied metadata");
}
void rejection_boundaries(){Fixture f;f.weapon(0,1,0x81);f.scalar(34);auto r=f.repo();auto a=f.get(0),b=f.get(34);
 f.scalar(5,5569,1);auto scalar_only=b;scalar_only.slot=5;scalar_only.item_id=5569;scalar_only.count=1;
 f.unchanged_rejection([&]{r.move(1,f.character,scalar_only,b,prepared);});f.unchanged_rejection([&]{r.move(1,f.character,a,scalar_only,prepared);});
 f.unchanged_rejection([&]{r.load(2,f.character,0);});f.unchanged_rejection([&]{r.load_saved(2,f.character);});f.unchanged_rejection([&]{r.move(2,f.character,a,b,prepared);});
 require(!r.load(1,f.character,29),"Missing capacity invented cell");auto missing=b;missing.slot=29;f.unchanged_rejection([&]{r.move(1,f.character,a,missing,prepared);});
 for(auto slot:{30,33,35,49,255})f.unchanged_rejection([&]{r.load(1,f.character,static_cast<std::uint8_t>(slot));});
 auto stale=a;++stale.revision;f.unchanged_rejection([&]{r.move(1,f.character,stale,b,prepared);});stale=a;stale.logical20[19]^=1;f.unchanged_rejection([&]{r.move(1,f.character,stale,b,prepared);});
 f.unchanged_rejection([&]{r.move(1,f.character,a,a,prepared);});f.unchanged_rejection([&]{r.move(1,f.character,b,a,prepared);});f.unchanged_rejection([&]{r.move(1,f.character,a,b,{});});
 f.unchanged_rejection([&]{r.move(1,f.character,a,b,[](const auto&){throw std::runtime_error("Encoding rejected candidate");});});
 f.sql("CREATE TRIGGER reject_weapon BEFORE INSERT ON character_weapon_slot_metadata WHEN NEW.slot=34 BEGIN SELECT RAISE(ABORT,'metadata failure'); END");f.unchanged_rejection([&]{r.move(1,f.character,a,b,prepared);});f.sql("DROP TRIGGER reject_weapon");
 f.sql("CREATE TRIGGER reject_scalar BEFORE UPDATE ON diagnostic_inventory_slots WHEN NEW.slot=34 BEGIN SELECT RAISE(ABORT,'scalar failure'); END");f.unchanged_rejection([&]{r.move(1,f.character,a,b,prepared);});f.sql("DROP TRIGGER reject_scalar");
 f.unchanged_rejection([&]{r.move(1,f.character,a,b,[&](const auto&){f.sql("UPDATE character_weapon_slot_metadata SET provenance='encoder-mutation' WHERE slot=34");});});
 // Existing gameplay battle reservation API establishes a genuine pending row.
 god2::SqliteRecoveredCharacterRepository character(f.db.get());auto resources=character.commit_resources(1,f.character,{}, {52,120,2,80,0,"CUSTOM-0012"});
 auto battle=character.reserve_battle(1,f.character,resources);f.unchanged_rejection([&]{r.move(1,f.character,a,b,prepared);});character.settle_battle(1,f.character,battle,resources,resources,true,0);
 r.move(1,f.character,a,b,prepared);
}
void corrupt_and_partial(){Fixture f;f.weapon(0,1,0x8f);f.scalar(34);auto r=f.repo();
 for(const char* sql:{"DELETE FROM character_weapon_slot_metadata WHERE slot=0",
  "UPDATE character_weapon_slot_metadata SET revision=2 WHERE slot=0",
  "UPDATE character_weapon_slot_metadata SET logical20=zeroblob(20) WHERE slot=0",
  "UPDATE character_weapon_slot_metadata SET logical20=zeroblob(19) WHERE slot=0",
  "UPDATE character_weapon_slot_metadata SET logical20=CAST(logical20 AS TEXT) WHERE slot=0",
  "UPDATE character_weapon_slot_metadata SET client_sha256=printf('%064d',0) WHERE slot=0",
  "UPDATE character_weapon_slot_metadata SET source_sha256=printf('%064d',0) WHERE slot=0",
  "UPDATE character_weapon_slot_metadata SET provenance=CAST(X'610062' AS TEXT) WHERE slot=0",
  "UPDATE character_weapon_slot_metadata SET origin='EMPTY_SLOT_POLICY' WHERE slot=0",
  "UPDATE diagnostic_inventory_slots SET count=2 WHERE slot=0",
  "UPDATE diagnostic_inventory_slots SET item_id=5569 WHERE slot=0",
  "DELETE FROM diagnostic_inventory_slots WHERE slot=0"}){
   f.sql("PRAGMA foreign_keys=OFF;PRAGMA ignore_check_constraints=ON;BEGIN");f.sql(sql);f.unchanged_rejection([&]{r.load(1,f.character,0);});f.unchanged_rejection([&]{r.load_saved(1,f.character);});f.sql("ROLLBACK;PRAGMA foreign_keys=ON");require(f.get(0).item_id==1,"Corruption rollback");
 }
 f.sql("UPDATE diagnostic_inventory_slots SET revision=9223372036854775807 WHERE slot=0;UPDATE character_weapon_slot_metadata SET revision=9223372036854775807 WHERE slot=0");auto a=f.get(0),b=f.get(34);f.unchanged_rejection([&]{r.move(1,f.character,a,b,prepared);});
}
void reopen(){struct Temp{std::filesystem::path root;Temp(){std::random_device rd;for(int i=0;i<100;++i){root=std::filesystem::temp_directory_path()/("god2-weapon-slots-"+std::to_string(rd()));if(std::filesystem::create_directory(root))return;}throw std::runtime_error("Create temp fixture");}~Temp(){std::error_code ec;std::filesystem::remove_all(root,ec);}} temp;
 const auto file=(temp.root/"fixture.sqlite").string();std::vector<StoredWeaponSlot> expected;
 {Fixture f(file);f.weapon(0,1,0xfe);f.weapon(1,2,0xb5);f.scalar(34);auto r=f.repo();r.move(1,f.character,f.get(0),f.get(34),prepared);r.move(1,f.character,f.get(1),f.get(34),prepared);expected=r.load_saved(1,f.character);}
 {Fixture f(file,false);require(f.repo().load_saved(1,f.character)==expected,"Reopen lost weapon after-state");}
}
void coupled_appearance_rollback(){
 Fixture f;f.weapon(0,1,0xa7);f.scalar(34);auto weapon=f.repo();
 god2::SqlitePlayerAppearanceRepository appearance(f.db.get());
 god2::RecoveredPlayerAppearanceUpdate::Fields fields{static_cast<std::uint16_t>(f.character),0,7,9,{1,0,1,0,1,0,0x81,0}};
 auto before=appearance.save(1,f.character,{},fields,"CUSTOM_TEST_NOT_NATIVE","isolated-coupled-appearance/CUSTOM-0047");
 const auto inventory_before=f.snapshot();auto next=fields;next.components[6]=1;next.components[7]=1;
 rejects([&]{weapon.move(1,f.character,f.get(0),f.get(34),[&](const auto&){
  appearance.save(1,f.character,before.revision,next,before.origin,before.provenance);
  throw std::runtime_error("outer encoder failed after nested appearance save");
 });});
 require(f.snapshot()==inventory_before && appearance.load(1,f.character)==before,"Outer failure did not roll back inventory and appearance together");
 weapon.move(1,f.character,f.get(0),f.get(34),[&](const auto&){appearance.save(1,f.character,before.revision,next,before.origin,before.provenance);});
 require(f.get(34).item_id==1 && appearance.load(1,f.character)->revision==2 && appearance.load(1,f.character)->fields==next,"Coupled inventory/appearance commit failed");
 const auto inventory_after=f.snapshot();rejects([&]{weapon.move(1,f.character,f.get(34),f.get(0),[&](const auto&){appearance.save(1,f.character,before.revision,fields,before.origin,before.provenance);});});
 require(f.snapshot()==inventory_after && appearance.load(1,f.character)->fields==next,"Appearance CAS failure committed weapon change");
}
}
int main(){try{moves_and_preservation();rejection_boundaries();corrupt_and_partial();reopen();coupled_appearance_rollback();std::cout<<"PASS weapon slots: preserve/CAS/owner/corruption/rollback/prepare/pending/reopen/coupled-appearance\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
