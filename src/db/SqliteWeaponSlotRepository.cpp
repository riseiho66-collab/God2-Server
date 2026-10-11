#include "db/SqliteWeaponSlotRepository.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <limits>
#include <utility>
namespace god2 {
namespace {
void require(bool value,const char* message){if(!value)throw DatabaseError(message);}
bool domain(std::uint8_t slot){return slot<30||slot==34;}
struct ReadScope {
 sqlite3* db;bool owns,finished=false;
 explicit ReadScope(sqlite3* value):db(value),owns(sqlite3_get_autocommit(value)!=0){if(owns)sqlite_detail::execute(db,"BEGIN");}
 ~ReadScope(){if(owns&&!finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
 void finish(){if(owns)sqlite_detail::execute(db,"COMMIT");finished=true;}
};
}
SqliteWeaponSlotRepository::SqliteWeaponSlotRepository(sqlite3* db,QualifyWeapon qualify):db_(db),qualify_(std::move(qualify)){
 require(db_&&bool(qualify_),"Weapon repository requires database and source qualifier");
}
void SqliteWeaponSlotRepository::owner(std::uint64_t account,std::uint64_t character){
 require(account&&character,"Invalid weapon owner");
 sqlite_detail::Statement q(db_,"SELECT 1 FROM recovered_characters WHERE account_id=? AND id=?");
 q.bind_id(1,account);q.bind_id(2,character);require(q.row(),"Weapon character ownership rejected");
}
std::optional<StoredWeaponSlot> SqliteWeaponSlotRepository::read(std::uint64_t character,std::uint8_t slot){
 require(domain(slot),"Weapon slot outside qualified domain");
 sqlite_detail::Statement q(db_,"SELECT item_id,count,revision,source_sha256,design_id FROM diagnostic_inventory_slots WHERE character_id=? AND slot=?");
 q.bind_id(1,character);q.bind(2,slot);
 sqlite_detail::Statement m(db_,"SELECT logical20,revision,origin,provenance,source_sha256,client_sha256,design_id FROM character_weapon_slot_metadata WHERE character_id=? AND slot=?");
 m.bind_id(1,character);m.bind(2,slot);
 const bool scalar=q.row(),metadata=m.row();
 if(!scalar){require(!metadata,"Orphan weapon metadata");return {};}
 StoredWeaponSlot out;out.slot=slot;out.item_id=q.number<std::uint16_t>(0);out.count=q.number<std::uint8_t>(1);out.revision=q.number<std::uint64_t>(2);out.metadata_present=metadata;
 require(out.revision>0&&out.count<=127&&q.text(4)=="CUSTOM-0015"&&((out.count==0)==(out.item_id==0)),"Malformed weapon scalar occupancy");
 const bool qualified=out.count&&qualify_(out.item_id);
 if(!metadata&&out.count){require(!qualified,"Occupied weapon has no instance metadata");return {};}
 require(q.text(3)==source_sha256,"Weapon scalar source identity mismatch");
 if(!metadata){out.origin="EMPTY_SLOT_POLICY";out.provenance="CUSTOM-0046/implicit-empty-scalar";return out;}
 const auto bytes=m.blob(0,20,20);std::copy(bytes.begin(),bytes.end(),out.logical20.begin());
 require(m.number<std::uint64_t>(1)==out.revision,"Weapon scalar/metadata revision mismatch");
 out.origin=m.text(2);out.provenance=m.text(3);
 require(m.text(4)==source_sha256&&m.text(5)==client_sha256&&m.text(6)=="CUSTOM-0046","Weapon metadata source identity mismatch");
 require(!out.provenance.empty()&&out.provenance.size()<=512&&out.provenance.find('\0')==std::string::npos,"Weapon provenance invalid");
 const auto key=std::uint16_t(out.logical20[0]|(std::uint16_t(out.logical20[1])<<8));
 require(key==out.item_id,"Weapon metadata key disagrees with scalar");
 if(out.count)require(out.count==1&&qualified&&(out.origin=="NATIVE_CAPTURE_VERIFIED"||out.origin=="CUSTOM_TEST_NOT_NATIVE"),"Unqualified occupied weapon metadata");
 else require(out.origin=="EMPTY_SLOT_POLICY","Empty weapon metadata has occupied origin");
 return out;
}
std::optional<StoredWeaponSlot> SqliteWeaponSlotRepository::load(std::uint64_t account,std::uint64_t character,std::uint8_t slot){
 ReadScope scope(db_);owner(account,character);auto result=read(character,slot);scope.finish();return result;
}
std::vector<StoredWeaponSlot> SqliteWeaponSlotRepository::load_saved(std::uint64_t account,std::uint64_t character){
 ReadScope scope(db_);owner(account,character);
 sqlite_detail::Statement orphans(db_,"SELECT 1 FROM character_weapon_slot_metadata m LEFT JOIN diagnostic_inventory_slots d ON d.character_id=m.character_id AND d.slot=m.slot WHERE m.character_id=? AND (d.character_id IS NULL OR NOT(m.slot BETWEEN 0 AND 29 OR m.slot=34)) LIMIT 1");
 orphans.bind_id(1,character);require(!orphans.row(),"Orphan/out-of-domain saved weapon metadata");
 sqlite_detail::Statement rows(db_,"SELECT slot FROM diagnostic_inventory_slots WHERE character_id=? AND (slot BETWEEN 0 AND 29 OR slot=34) ORDER BY slot");rows.bind_id(1,character);
 std::vector<StoredWeaponSlot> result;
 while(rows.row()){auto row=read(character,rows.number<std::uint8_t>(0));if(row)result.push_back(std::move(*row));}
 scope.finish();return result;
}
void SqliteWeaponSlotRepository::write(std::uint64_t character,const StoredWeaponSlot& before,const StoredWeaponSlot& after){
 sqlite_detail::Statement scalar(db_,"UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=? WHERE character_id=? AND slot=? AND revision=? AND item_id=? AND count=? AND source_sha256=? AND design_id='CUSTOM-0015'");
 scalar.bind(1,after.item_id);scalar.bind(2,after.count);scalar.bind_id(3,after.revision);scalar.bind_id(4,character);scalar.bind(5,before.slot);scalar.bind_id(6,before.revision);scalar.bind(7,before.item_id);scalar.bind(8,before.count);scalar.bind(9,source_sha256);scalar.done();
 require(sqlite3_changes(db_)==1,"Weapon scalar CAS failed");
 bool update_metadata=before.metadata_present;
 // Migration may retire EMPTY_SLOT_POLICY metadata when another scalar use
 // advances the cell. The transaction's captured tails still define after-state.
 if(update_metadata&&!before.count){sqlite_detail::Statement present(db_,"SELECT 1 FROM character_weapon_slot_metadata WHERE character_id=? AND slot=?");present.bind_id(1,character);present.bind(2,before.slot);update_metadata=present.row();}
 sqlite_detail::Statement meta(db_,update_metadata?
  "UPDATE character_weapon_slot_metadata SET logical20=?,revision=?,origin=?,provenance=?,source_sha256=?,client_sha256=?,design_id='CUSTOM-0046' WHERE character_id=? AND slot=? AND revision=?":
  "INSERT INTO character_weapon_slot_metadata(logical20,revision,origin,provenance,source_sha256,client_sha256,character_id,slot,design_id) VALUES(?,?,?,?,?,?,?,?,'CUSTOM-0046')");
 meta.bind_blob(1,after.logical20);meta.bind_id(2,after.revision);meta.bind(3,after.origin);meta.bind(4,after.provenance);meta.bind(5,source_sha256);meta.bind(6,client_sha256);meta.bind_id(7,character);meta.bind(8,before.slot);if(update_metadata)meta.bind_id(9,before.revision);meta.done();
 require(sqlite3_changes(db_)==1,"Weapon metadata CAS failed");
}
WeaponSlotMove SqliteWeaponSlotRepository::move(std::uint64_t account,std::uint64_t character,
 const StoredWeaponSlot& source,const StoredWeaponSlot& destination,const Prepare& prepare){
 require(domain(source.slot)&&domain(destination.slot)&&source.slot!=destination.slot&&bool(prepare),"Invalid weapon transfer/preparation");
 sqlite_detail::Transaction tx(db_);owner(account,character);
 require(read(character,source.slot)==std::optional{source}&&read(character,destination.slot)==std::optional{destination},"Weapon transfer version conflict");
 sqlite_detail::Statement pending(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");pending.bind_id(1,character);require(!pending.row(),"Weapon change during pending battle");
 const auto limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
 require(source.count==1&&source.item_id&&source.metadata_present&&source.revision<limit&&destination.revision<limit,"Invalid weapon transfer state");
 WeaponSlotMove result{destination,source};
 if(!destination.count){result.source=source;result.source.item_id=0;result.source.count=0;result.source.logical20[0]=result.source.logical20[1]=0;result.source.origin="EMPTY_SLOT_POLICY";result.source.provenance="CUSTOM-0046/clear-previous-instance";}
 result.source.slot=source.slot;result.source.revision=source.revision+1;result.source.metadata_present=true;
 result.destination.slot=destination.slot;result.destination.revision=destination.revision+1;result.destination.metadata_present=true;
 write(character,source,result.source);write(character,destination,result.destination);
 const auto verify=[&]{require(read(character,source.slot)==std::optional{result.source}&&read(character,destination.slot)==std::optional{result.destination},"Weapon transfer readback mismatch");};
 verify();prepare(result);verify();tx.commit();return result;
}
}
