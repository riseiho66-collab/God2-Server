#include "db/SqliteTeleportGemRepository.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <limits>

namespace god2 {
namespace {
void require(bool value,const char* message){if(!value)throw DatabaseError(message);}
std::uint64_t advance(std::uint64_t value){
    require(value && value<static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),"Teleport gem revision exhausted");
    return value+1;
}
void provenance(const std::string& origin,const std::string& evidence){
    require(origin=="NATIVE_CAPTURE_VERIFIED" || origin=="CUSTOM_TEST_NOT_NATIVE","Teleport gem origin rejected");
    require(!evidence.empty() && evidence.size()<=512 && evidence.find('\0')==std::string::npos,"Teleport gem evidence rejected");
}
struct ReadScope {
    sqlite3* db;bool owns,finished=false;
    explicit ReadScope(sqlite3* value):db(value),owns(sqlite3_get_autocommit(value)!=0){if(owns)sqlite_detail::execute(db,"BEGIN");}
    ~ReadScope(){if(owns&&!finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){if(owns)sqlite_detail::execute(db,"COMMIT");finished=true;}
};
}

SqliteTeleportGemRepository::SqliteTeleportGemRepository(sqlite3* db):db_(db){require(db_,"Null teleport gem database");}
std::string SqliteTeleportGemRepository::schema(){return R"SQL(
-- CUSTOM-0057: no scalar item/charge grants; full owned instance evidence only.
CREATE TABLE character_teleport_gem_metadata (
 character_id INTEGER NOT NULL,
 slot INTEGER NOT NULL CHECK(typeof(slot)='integer' AND slot BETWEEN 0 AND 29),
 metadata20 BLOB NOT NULL CHECK(typeof(metadata20)='blob' AND length(metadata20)=20),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 origin TEXT NOT NULL CHECK(origin IN ('NATIVE_CAPTURE_VERIFIED','CUSTOM_TEST_NOT_NATIVE')),
 provenance TEXT NOT NULL CHECK(typeof(provenance)='text' AND length(CAST(provenance AS BLOB)) BETWEEN 1 AND 512 AND instr(provenance,char(0))=0),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0057'),
 PRIMARY KEY(character_id,slot),
 FOREIGN KEY(character_id,slot) REFERENCES diagnostic_inventory_slots(character_id,slot) ON DELETE CASCADE
);
)SQL";}
void SqliteTeleportGemRepository::owner(std::uint64_t account,std::uint64_t character){
    require(account && character,"Invalid teleport gem owner");
    sqlite_detail::Statement query(db_,"SELECT 1 FROM recovered_characters WHERE account_id=? AND id=?");
    query.bind_id(1,account);query.bind_id(2,character);require(query.row(),"Teleport gem ownership rejected");
}
void SqliteTeleportGemRepository::no_pending_battle(std::uint64_t character){
    sqlite_detail::Statement query(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
    query.bind_id(1,character);require(!query.row(),"Teleport gem change during pending battle");
}
void SqliteTeleportGemRepository::no_weapon_overlay(std::uint64_t character,std::uint8_t slot){
    sqlite_detail::Statement query(db_,"SELECT 1 FROM character_weapon_slot_metadata WHERE character_id=? AND slot=?");
    query.bind_id(1,character);query.bind(2,slot);require(!query.row(),"Teleport gem conflicts with weapon metadata");
}
std::optional<StoredTeleportGemSlot> SqliteTeleportGemRepository::read(std::uint64_t character,std::uint8_t slot){
    require(slot<30,"Teleport gem slot outside bag");
    no_weapon_overlay(character,slot);
    sqlite_detail::Statement scalar(db_,"SELECT item_id,count,revision,source_sha256,design_id FROM diagnostic_inventory_slots WHERE character_id=? AND slot=?");
    scalar.bind_id(1,character);scalar.bind(2,slot);
    sqlite_detail::Statement meta(db_,"SELECT metadata20,revision,origin,provenance,source_sha256,design_id FROM character_teleport_gem_metadata WHERE character_id=? AND slot=?");
    meta.bind_id(1,character);meta.bind(2,slot);
    const bool has_scalar=scalar.row(),has_meta=meta.row();
    if(!has_scalar){require(!has_meta,"Orphan teleport gem metadata");return {};}
    StoredTeleportGemSlot row;row.slot=slot;row.item_id=scalar.number<std::uint16_t>(0);
    row.count=scalar.number<std::uint8_t>(1);row.revision=scalar.number<std::uint64_t>(2);
    require(row.revision && row.count<=127 && ((row.count==0)==(row.item_id==0)) && scalar.text(4)=="CUSTOM-0015","Malformed teleport gem scalar");
    if(row.count && row.item_id!=RecoveredTeleportGem::item_id){require(!has_meta,"Teleport metadata overlays another item");return {};}
    require(scalar.text(3)==source_sha256,"Teleport gem scalar source mismatch");
    if(!row.count){require(!has_meta,"Empty scalar retains teleport gem metadata");return row;}
    require(row.count==1 && has_meta,"Teleport gem requires one full owned instance");
    const auto bytes=meta.blob(0,20,20);std::copy(bytes.begin(),bytes.end(),row.metadata20.begin());
    require(meta.number<std::uint64_t>(1)==row.revision,"Teleport gem metadata/scalar revision mismatch");
    require(meta.text(4)==source_sha256 && meta.text(5)=="CUSTOM-0057","Teleport gem metadata source mismatch");
    require(RecoveredTeleportGem::displayed_charges(row.metadata20).has_value(),"Teleport gem key/type/charges rejected");
    row.metadata_present=true;row.origin=meta.text(2);row.provenance=meta.text(3);provenance(row.origin,row.provenance);return row;
}
std::optional<StoredTeleportGemSlot> SqliteTeleportGemRepository::load(std::uint64_t account,std::uint64_t character,std::uint8_t slot){
    ReadScope scope(db_);owner(account,character);auto result=read(character,slot);scope.finish();return result;
}
std::vector<StoredTeleportGemSlot> SqliteTeleportGemRepository::load_saved(std::uint64_t account,std::uint64_t character){
    ReadScope scope(db_);owner(account,character);
    // A historical scalar is not a full instance. Keep its unknown charge
    // untouched and let interactive load(slot) reject it explicitly; adding
    // migration40 must not make that old character unable to enter the world.
    sqlite_detail::Statement rows(db_,"SELECT slot FROM character_teleport_gem_metadata WHERE character_id=? ORDER BY slot");
    rows.bind_id(1,character);std::vector<StoredTeleportGemSlot> result;
    while(rows.row()){
        auto row=read(character,rows.number<std::uint8_t>(0));require(row.has_value() && row->metadata_present,"Saved teleport gem is incomplete");
        result.push_back(std::move(*row));
    }
    scope.finish();return result;
}
StoredTeleportGemSlot SqliteTeleportGemRepository::save_existing(std::uint64_t account,std::uint64_t character,std::uint8_t slot,
    const StoredInventorySlot& expected,const RecoveredTeleportGem::Metadata& metadata,
    const std::string& origin,const std::string& evidence){
    require(slot<30 && expected.item_id==RecoveredTeleportGem::item_id && expected.count==1 && expected.revision &&
            expected.source_sha256==source_sha256 && RecoveredTeleportGem::displayed_charges(metadata).has_value(),"Invalid teleport gem attachment");
    provenance(origin,evidence);sqlite_detail::Transaction tx(db_);owner(account,character);no_pending_battle(character);no_weapon_overlay(character,slot);
    sqlite_detail::Statement scalar(db_,"SELECT 1 FROM diagnostic_inventory_slots WHERE character_id=? AND slot=? AND item_id=16055 AND count=1 AND revision=? AND source_sha256=? AND design_id='CUSTOM-0015'");
    scalar.bind_id(1,character);scalar.bind(2,slot);scalar.bind_id(3,expected.revision);scalar.bind(4,source_sha256);
    require(scalar.row(),"Teleport gem attachment scalar CAS failed");
    sqlite_detail::Statement insert(db_,"INSERT INTO character_teleport_gem_metadata(character_id,slot,metadata20,revision,origin,provenance,source_sha256,design_id) VALUES(?,?,?,?,?,?,?,'CUSTOM-0057')");
    insert.bind_id(1,character);insert.bind(2,slot);insert.bind_blob(3,metadata);insert.bind_id(4,expected.revision);
    insert.bind(5,origin);insert.bind(6,evidence);insert.bind(7,source_sha256);insert.done();
    StoredTeleportGemSlot result{slot,expected.item_id,expected.count,expected.revision,metadata,true,origin,evidence};
    require(sqlite3_changes(db_)==1 && read(character,slot)==std::optional(result),"Teleport gem attachment readback mismatch");
    tx.commit();return result;
}
RecoveredPosition SqliteTeleportGemRepository::position(std::uint64_t character){
    sqlite_detail::Statement query(db_,"SELECT area,scene,x,y,revision FROM recovered_positions WHERE character_id=?");
    query.bind_id(1,character);require(query.row(),"Teleport gem requires a saved source position");
    return {query.number<std::uint16_t>(0),query.number<std::uint16_t>(1),query.number<std::uint16_t>(2),query.number<std::uint16_t>(3),query.number<std::uint64_t>(4)};
}
void SqliteTeleportGemRepository::write(std::uint64_t character,const StoredTeleportGemSlot& before,const StoredTeleportGemSlot& after){
    if(before.metadata_present){
        sqlite_detail::Statement erase(db_,"DELETE FROM character_teleport_gem_metadata WHERE character_id=? AND slot=? AND revision=?");
        erase.bind_id(1,character);erase.bind(2,before.slot);erase.bind_id(3,before.revision);erase.done();
        require(sqlite3_changes(db_)==1,"Teleport gem metadata CAS failed");
    }
    sqlite_detail::Statement scalar(db_,"UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=? WHERE character_id=? AND slot=? AND revision=? AND item_id=? AND count=? AND source_sha256=? AND design_id='CUSTOM-0015'");
    scalar.bind(1,after.item_id);scalar.bind(2,after.count);scalar.bind_id(3,after.revision);scalar.bind_id(4,character);
    scalar.bind(5,before.slot);scalar.bind_id(6,before.revision);scalar.bind(7,before.item_id);scalar.bind(8,before.count);scalar.bind(9,source_sha256);scalar.done();
    require(sqlite3_changes(db_)==1,"Teleport gem scalar CAS failed");
    if(after.metadata_present){
        sqlite_detail::Statement insert(db_,"INSERT INTO character_teleport_gem_metadata(character_id,slot,metadata20,revision,origin,provenance,source_sha256,design_id) VALUES(?,?,?,?,?,?,?,'CUSTOM-0057')");
        insert.bind_id(1,character);insert.bind(2,after.slot);insert.bind_blob(3,after.metadata20);insert.bind_id(4,after.revision);
        insert.bind(5,after.origin);insert.bind(6,after.provenance);insert.bind(7,source_sha256);insert.done();
        require(sqlite3_changes(db_)==1,"Teleport gem metadata write failed");
    }
}
TeleportGemTransfer SqliteTeleportGemRepository::prepare_transfer(std::uint64_t account,std::uint64_t character,
    const StoredTeleportGemSlot& expected,const RecoveredPosition& expected_position,const PrepareTransfer& prepare){
    require(bool(prepare) && expected_position.area==2 && expected_position.scene==0,"Teleport gem transfer source/callback rejected");
    sqlite_detail::Transaction tx(db_);owner(account,character);no_pending_battle(character);
    require(read(character,expected.slot)==std::optional(expected) && expected.metadata_present && expected.count==1,
            "Teleport gem transfer instance CAS failed");
    require(position(character)==expected_position,"Teleport gem source position CAS failed");
    const auto charges=RecoveredTeleportGem::displayed_charges(expected.metadata20);
    require(charges.has_value(),"Teleport gem charge unavailable");
    TeleportGemTransfer result{expected,expected,expected_position,{2,4,56,75,advance(expected_position.revision)}};
    result.after.revision=advance(expected.revision);
    if(*charges==1){
        result.after.item_id=0;result.after.count=0;result.after.metadata20={};result.after.metadata_present=false;
        result.after.origin.clear();result.after.provenance.clear();
    } else result.after.metadata20=*RecoveredTeleportGem::with_charges(expected.metadata20,static_cast<std::uint8_t>(*charges-1));
    write(character,expected,result.after);
    sqlite_detail::Statement update(db_,"UPDATE recovered_positions SET area=2,scene=4,x=56,y=75,revision=? WHERE character_id=? AND area=? AND scene=? AND x=? AND y=? AND revision=?");
    update.bind_id(1,result.position_after.revision);update.bind_id(2,character);update.bind(3,expected_position.area);update.bind(4,expected_position.scene);
    update.bind(5,expected_position.x);update.bind(6,expected_position.y);update.bind_id(7,expected_position.revision);update.done();
    require(sqlite3_changes(db_)==1,"Teleport gem position write CAS failed");
    const auto verify=[&]{owner(account,character);no_pending_battle(character);
        require(read(character,expected.slot)==std::optional(result.after) && position(character)==result.position_after,"Teleport gem transfer readback mismatch");};
    verify();prepare(result);verify();tx.commit();return result;
}
TeleportGemMove SqliteTeleportGemRepository::move_whole(std::uint64_t account,std::uint64_t character,
    const StoredTeleportGemSlot& source,const StoredTeleportGemSlot& destination,const PrepareMove& prepare){
    require(source.slot<30 && destination.slot<30 && source.slot!=destination.slot && source.count==1 &&
            source.metadata_present && bool(prepare),"Teleport gem move operands rejected");
    sqlite_detail::Transaction tx(db_);owner(account,character);no_pending_battle(character);
    require(read(character,source.slot)==std::optional(source) && read(character,destination.slot)==std::optional(destination),
            "Teleport gem move instance CAS failed");
    TeleportGemMove result{destination,source};
    result.source.slot=source.slot;result.destination.slot=destination.slot;
    result.source.revision=advance(source.revision);result.destination.revision=advance(destination.revision);
    write(character,source,result.source);write(character,destination,result.destination);
    const auto verify=[&]{owner(account,character);no_pending_battle(character);
        require(read(character,source.slot)==std::optional(result.source) && read(character,destination.slot)==std::optional(result.destination),"Teleport gem move readback mismatch");};
    verify();prepare(result);verify();tx.commit();return result;
}
}
