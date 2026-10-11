#include "db/SqliteBeastBagRepository.h"
#include "db/SqliteSupport.h"
#include "handlers/OwnedBagProjectionService.h"
#include "protocol/RecoveredInventoryProjection.h"
#include "protocol/RecoveredBeastInventoryProjection.h"
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
#include <bit>
#include <cstring>
#include <limits>
#include <initializer_list>
#include <nlohmann/json.hpp>
#include <type_traits>
namespace god2 {
namespace {
void require(bool value,const char* reason){if(!value)throw DatabaseError(reason);}
constexpr auto limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
std::uint64_t advance(std::uint64_t value){require(value&&value<limit,"Beast bag revision exhausted");return value+1;}
// Typed whole-save preservation, reused as a new source consumer. Main schema,
// all other characters, protected slots and opaque peripheral values survive.
#include "../relations53/preservation.inc"
Exclusions exclusions(std::uint64_t character,const RecoveredInventoryMoveRequest::Request& use){
    const auto actor="character_id="+std::to_string(character);
    const auto cells=" AND slot IN("+std::to_string(use.source_slot)+","+std::to_string(use.destination_slot)+")";
    Exclusions result;
    for(const auto* table:{"diagnostic_inventory_slots","character_weapon_slot_metadata","character_armor_slot_metadata","character_teleport_gem_metadata"})result[table]="NOT("+actor+cells+")";
    result["character_beast_snapshot_custody"]="NOT("+actor+" AND inventory_slot IN("+std::to_string(use.source_slot)+","+std::to_string(use.destination_slot)+"))";
    result["character_beast_selection_0085"]="NOT("+actor+")";
    return result;
}
void columns(sqlite3* db,const char* table,std::initializer_list<const char*> expected){
    const auto sql="PRAGMA table_info("+quoted(table)+")";sqlite_detail::Statement q(db,sql.c_str());
    std::vector<std::string> actual,wanted;while(q.row())actual.push_back(q.text(1));for(const auto* name:expected)wanted.emplace_back(name);
    require(actual==wanted,"Beast bag affected table has unsupported opaque columns");
}
void shape(sqlite3* db){
    columns(db,"diagnostic_inventory_slots",{"character_id","slot","item_id","count","revision","source_sha256","design_id"});
    for(const auto* table:{"character_weapon_slot_metadata","character_armor_slot_metadata"})columns(db,table,{"character_id","slot","logical20","revision","origin","provenance","source_sha256","client_sha256","design_id"});
    columns(db,"character_teleport_gem_metadata",{"character_id","slot","metadata20","revision","origin","provenance","source_sha256","design_id"});
    SqliteBeastSnapshotRepository::require_schema(db);
}
template<class T,class Slot>const T* at(const std::vector<T>& values,std::uint8_t slot,Slot key){
    const auto found=std::find_if(values.begin(),values.end(),[&](const auto& value){return key(value)==slot;});return found==values.end()?nullptr:&*found;
}
RecoveredInventoryProjection::Metadata metadata(const SqliteBeastBagRepository::Snapshot& saved,std::uint8_t slot){
    const auto* beast=at(saved.beasts,slot,[](const auto& row){return row.inventory_slot;});if(beast)return beast->inventory_metadata;
    const auto* armor=at(saved.bag.armor,slot,[](const auto& row){return row.slot;});if(armor)return armor->logical20;
    const auto* weapon=at(saved.bag.weapons,slot,[](const auto& row){return row.slot;});if(weapon)return weapon->logical20;
    const auto* gem=at(saved.bag.gems,slot,[](const auto& row){return row.slot;});if(gem)return gem->logical20;
    RecoveredInventoryProjection::Metadata bytes{};const auto& row=*saved.bag.scalar[slot];bytes[0]=static_cast<std::uint8_t>(row.item_id);bytes[1]=static_cast<std::uint8_t>(row.item_id>>8);return bytes;
}
void foreign_insert(sqlite3* db,const char* table,std::uint64_t character,const ArmorForeignOverlay& row,bool gem){
    const auto sql="INSERT INTO "+std::string(table)+(gem?
        "(character_id,slot,metadata20,revision,origin,provenance,source_sha256,design_id) VALUES(?,?,?,?,?,?,?,?)":
        "(character_id,slot,logical20,revision,origin,provenance,source_sha256,client_sha256,design_id) VALUES(?,?,?,?,?,?,?,?,?)");
    sqlite_detail::Statement q(db,sql.c_str());q.bind_id(1,character);q.bind(2,row.slot);q.bind_blob(3,row.logical20);q.bind_id(4,row.revision);q.bind(5,row.origin);q.bind(6,row.provenance);q.bind(7,row.source_sha256);if(!gem)q.bind(8,row.client_sha256);q.bind(gem?8:9,row.design_id);q.done();require(sqlite3_changes(db)==1,"Beast neighbouring overlay insertion failed");
}
void beast_insert(sqlite3* db,const StoredBeastSnapshot& row){
    sqlite_detail::Statement q(db,"INSERT INTO character_beast_snapshot_custody(character_id,inventory_slot,selector,bag_revision,inventory_metadata,panel4c,explorationc5,revision,origin,evidence_id,source_sha256,client_sha256,design_id) VALUES(?,?,?,?,?,?,NULLIF(?,X''),?,?,?,?,?,?)");
    q.bind_id(1,row.character);q.bind(2,row.inventory_slot);q.bind(3,row.panel.selector());q.bind_id(4,row.bag_revision);q.bind_blob(5,row.inventory_metadata);q.bind_blob(6,row.panel.bytes);
    if(row.exploration)q.bind_blob(7,row.exploration->bytes);else q.bind_blob(7,std::span<const std::uint8_t>{});
    q.bind_id(8,row.revision);q.bind(9,row.origin);q.bind(10,row.evidence_id);q.bind(11,std::string(NativeBeastSourceCatalog::source_sha256));q.bind(12,std::string(SqliteBeastSnapshotRepository::client_sha256));q.bind(13,std::string(SqliteBeastSnapshotRepository::design_id));q.done();require(sqlite3_changes(db)==1,"Beast relocated custody insertion failed");
}
using FeatureObjects=std::vector<std::array<std::string,4>>;
FeatureObjects discard_objects(sqlite3* db){
    sqlite_detail::Statement q(db,"SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master WHERE tbl_name IN('character_beast_discard_receipts_0085','beast_discard_schema_0085') ORDER BY type,name");
    FeatureObjects out;while(q.row())out.push_back({q.text(0),q.text(1),q.text(2),q.text(3)});return out;
}
FeatureObjects discard_peripheral_objects(sqlite3* db){
    sqlite_detail::Statement q(db,"SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master WHERE tbl_name NOT IN('character_beast_discard_receipts_0085','beast_discard_schema_0085') ORDER BY type,name");
    FeatureObjects out;while(q.row())out.push_back({q.text(0),q.text(1),q.text(2),q.text(3)});return out;
}
bool receipt_key(const std::string& value){return value.size()==64&&value.find_first_not_of("0123456789abcdef")==std::string::npos;}
bool discarded(sqlite3* db,const std::string& receipt){
    sqlite_detail::Statement q(db,"SELECT 1 FROM character_beast_discard_receipts_0085 WHERE receipt=?");q.bind(1,receipt);return q.row();
}
std::string removed_state(const StoredBeastSnapshot& row,const std::optional<SqliteBeastSnapshotRepository::SelectionRecord>& selection){
    using J=nlohmann::json;
    J value={{"account",row.account},{"character",row.character},{"inventory_slot",row.inventory_slot},
        {"bag_revision",row.bag_revision},{"custody_revision",row.revision},{"inventory_metadata",row.inventory_metadata},
        {"panel4c",row.panel.bytes},{"explorationc5",nullptr},{"origin",row.origin},{"evidence_id",row.evidence_id},
        {"source_sha256",NativeBeastSourceCatalog::source_sha256},{"client_sha256",SqliteBeastSnapshotRepository::client_sha256},
        {"instance_design_id",SqliteBeastSnapshotRepository::design_id},{"retired_selection",nullptr}};
    if(row.exploration)value["explorationc5"]=row.exploration->bytes;
    if(selection)value["retired_selection"]={{"selector",selection->selector},{"custody_revision",selection->custody_revision},
        {"revision",selection->revision},{"origin","CUSTOM_DESIGNED"},{"design_id","CUSTOM-0085"}};
    return value.dump();
}
}
std::string SqliteBeastBagRepository::discard_schema(){return R"SQL(
CREATE TABLE character_beast_discard_receipts_0085 (
 receipt TEXT PRIMARY KEY NOT NULL CHECK(typeof(receipt)='text' AND length(receipt)=64 AND receipt NOT GLOB '*[^0-9a-f]*'),
 account_id INTEGER NOT NULL CHECK(typeof(account_id)='integer' AND account_id>0),
 character_id INTEGER NOT NULL CHECK(typeof(character_id)='integer' AND character_id>0),
 operation INTEGER NOT NULL CHECK(operation=39),
 item_id INTEGER NOT NULL CHECK(typeof(item_id)='integer' AND item_id BETWEEN 1 AND 65535),
 source INTEGER NOT NULL CHECK(typeof(source)='integer' AND source BETWEEN 0 AND 29),
 quantity INTEGER NOT NULL CHECK(typeof(quantity)='integer' AND quantity=1),
 before_bag_revision INTEGER NOT NULL CHECK(typeof(before_bag_revision)='integer' AND before_bag_revision>0),
 after_bag_revision INTEGER NOT NULL CHECK(typeof(after_bag_revision)='integer' AND after_bag_revision>before_bag_revision),
 removed_state TEXT NOT NULL CHECK(typeof(removed_state)='text' AND length(removed_state)>0),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0085')
);
CREATE TABLE beast_discard_schema_0085 (
 version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version=3),
 sql_text TEXT NOT NULL,
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0085')
);
)SQL";}
void SqliteBeastBagRepository::require_discard_schema(sqlite3* db){
    SqliteBeastSnapshotRepository::require_schema(db);
    sqlite3* expected=nullptr;sqlite_detail::check(db,sqlite3_open(":memory:",&expected));
    struct Close{sqlite3* db;~Close(){sqlite3_close_v2(db);}} close{expected};
    sqlite_detail::execute(expected,discard_schema());
    require(discard_objects(db)==discard_objects(expected),"Beast discard feature schema/index/trigger mismatch");
    sqlite_detail::Statement q(db,"SELECT version,sql_text,design_id FROM beast_discard_schema_0085");
    require(q.row()&&q.integer(0)==3&&q.text(1)==discard_schema()&&q.text(2)=="CUSTOM-0085"&&!q.row(),"Beast discard immutable journal3 mismatch");
}
void SqliteBeastBagRepository::install_discard_schema(sqlite3* db){
    require(db&&sqlite3_get_autocommit(db)!=0,"Beast discard installation requires standalone transaction");
    sqlite_detail::Transaction tx(db);SqliteBeastSnapshotRepository::require_schema(db);
    if(discard_objects(db).empty()){
        const auto before=guard(db,{});const auto schema_before=discard_peripheral_objects(db);
        sqlite_detail::execute(db,discard_schema());
        sqlite_detail::Statement ledger(db,"INSERT INTO beast_discard_schema_0085 VALUES(3,?,'CUSTOM-0085')");ledger.bind(1,discard_schema());ledger.done();
        auto after=guard(db,{});after.erase(":sqlite_master");
        after.erase("beast_discard_schema_0085");after.erase("beast_discard_schema_0085:schema");
        after.erase("character_beast_discard_receipts_0085");after.erase("character_beast_discard_receipts_0085:schema");
        auto saved=before;saved.erase(":sqlite_master");require(after==saved&&discard_peripheral_objects(db)==schema_before,"Beast discard installation changed existing saved data/schema");
        sqlite_detail::Statement empty(db,"SELECT 1 FROM character_beast_discard_receipts_0085");require(!empty.row(),"Beast discard installation created a receipt");
    }
    require_discard_schema(db);tx.commit();
}
SqliteBeastBagRepository::SqliteBeastBagRepository(sqlite3* db,SqliteBeastSnapshotRepository& beasts,SqliteArmorSlotRepository& armor,OwnedBagProjectionService& projector)
    :db_(db),beasts_(beasts),armor_(armor),projector_(projector){require(db&&beasts.shares_connection(db)&&armor.shares_connection(db)&&projector.shares_connection(db),"Beast bag ports require same managed connection");}
SqliteBeastBagRepository::Snapshot SqliteBeastBagRepository::capture(std::uint64_t account,std::uint64_t character,const RecoveredInventoryMoveRequest::Request& use,Domain domain){
    if(domain==Domain::OrdinaryBag)require(use.source_slot<30&&use.destination_slot<30,"Beast move outside ordinary bag");
    else require((use.source_slot<30&&use.destination_slot==37)||(use.source_slot==37&&use.destination_slot<30),"Beast equipment must exchange bag and37");
    const bool owns=sqlite3_get_autocommit(db_)!=0;if(owns)sqlite_detail::execute(db_,"BEGIN");
    struct ReadEnd{sqlite3* db;bool owns,done=false;~ReadEnd(){if(owns&&!done)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}} end{db_,owns};
    shape(db_);if(domain==Domain::BeastEquipment)SqliteBeastSnapshotRepository::require_equipment_schema(db_);
    Snapshot saved;saved.request=use;saved.domain=domain;saved.bag=projector_.capture_proof(account,character).snapshot();saved.beasts=beasts_.load_owned(account,character);saved.selection=beasts_.load_selection_record(account,character);
    for(const auto slot:{use.source_slot,use.destination_slot}){
        require(saved.bag.scalar[slot].has_value(),"Beast move needs explicitly owned capacity");
        const auto& scalar=*saved.bag.scalar[slot];require(scalar.source_sha256==NativeBeastSourceCatalog::source_sha256,"Beast move mixed scalar source");
        // Canonical projection is independently qualified by the full bag port.
        const auto canonical=RecoveredBeastInventoryProjection::encode({slot,scalar.count,metadata(saved,slot)});
        require(canonical.has_value(),"Beast neighbour full projection rejected");
        if(slot<30)require(*canonical==projector_.project(account,character,slot,scalar),"Beast neighbour full projection mismatch");
        if(domain==Domain::BeastEquipment){
            const auto* beast=at(saved.beasts,slot,[](const auto& row){return row.inventory_slot;});
            require(!scalar.count||(scalar.count==1&&beast),"Beast equipment contains a foreign occupied cell");
            require(slot!=use.source_slot||beast,"Beast equipment source lacks owned custody");
            if(slot==37)require(!at(saved.bag.armor,slot,[](const auto& row){return row.slot;})&&!at(saved.bag.weapons,slot,[](const auto& row){return row.slot;})&&!at(saved.bag.gems,slot,[](const auto& row){return row.slot;}),"Beast37 has foreign overlays");
        }
    }
    require(at(saved.beasts,use.source_slot,[](const auto& row){return row.inventory_slot;})||at(saved.beasts,use.destination_slot,[](const auto& row){return row.inventory_slot;}),"Beast move contains no owned beast");
    saved.peripheral=guard(db_,exclusions(character,use));if(owns)sqlite_detail::execute(db_,"COMMIT");end.done=true;return saved;
}
SqliteBeastBagRepository::Result SqliteBeastBagRepository::move(const Snapshot& expected){
    require(sqlite3_get_autocommit(db_)!=0,"Beast move requires standalone transaction");
    sqlite_detail::Statement fk(db_,"PRAGMA foreign_keys");require(fk.row()&&fk.integer(0)==1,"Beast move requires foreign keys");
    sqlite_detail::Statement deferred(db_,"PRAGMA defer_foreign_keys");require(deferred.row()&&deferred.integer(0)==0,"Beast move cannot borrow deferred foreign keys");
    sqlite_detail::Transaction tx(db_);const auto actor=expected.bag.character;const auto a=expected.request.source_slot,b=expected.request.destination_slot;
    require(capture(expected.bag.account,actor,expected.request,expected.domain)==expected,"Beast full-frame snapshot CAS conflict");
    sqlite_detail::Statement battle(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");battle.bind_id(1,actor);require(!battle.row(),"Beast move during pending battle");
    Result result{expected,{},false};auto& next=result.after;
    const auto response=[&]{std::vector<std::uint8_t> logical;for(const auto slot:{a,b}){
        if(slot==b&&a==b&&!logical.empty())continue;
        const auto bytes=RecoveredBeastInventoryProjection::encode({slot,next.bag.scalar[slot]->count,metadata(next,slot)});require(bytes.has_value(),"Beast move response rejected");logical.insert(logical.end(),bytes->begin(),bytes->end());
    }return RecoveredWorldFrame::encode(logical);};
    if(a==b||!expected.bag.scalar[a]->count){result.wire=response();tx.commit();return result;}
    const auto destination=[](std::uint8_t slot,std::uint8_t a,std::uint8_t b){return slot==a?b:a;};
    next.bag.scalar[a]=*expected.bag.scalar[b];next.bag.scalar[b]=*expected.bag.scalar[a];
    next.bag.scalar[a]->revision=advance(expected.bag.scalar[a]->revision);next.bag.scalar[b]->revision=advance(expected.bag.scalar[b]->revision);
    const auto relocate=[&](auto& rows){for(auto& row:rows)if(row.slot==a||row.slot==b){row.slot=destination(row.slot,a,b);row.revision=next.bag.scalar[row.slot]->revision;}std::sort(rows.begin(),rows.end(),[](const auto& l,const auto& r){return l.slot<r.slot;});};
    // Existing empty weapon overlay is inactive and retired by scalar policy.
    std::erase_if(next.bag.weapons,[&](const auto& row){return (row.slot==a||row.slot==b)&&row.origin=="EMPTY_SLOT_POLICY";});
    relocate(next.bag.armor);relocate(next.bag.weapons);relocate(next.bag.gems);
    for(auto& row:next.beasts)if(row.inventory_slot==a||row.inventory_slot==b){
        const auto previous=row.revision;row.inventory_slot=destination(row.inventory_slot,a,b);row.bag_revision=next.bag.scalar[row.inventory_slot]->revision;row.revision=advance(previous);
        if(next.selection&&next.selection->selector==row.panel.selector()&&next.selection->custody_revision==previous){next.selection->custody_revision=row.revision;next.selection->revision=advance(next.selection->revision);}
    }
    std::sort(next.beasts.begin(),next.beasts.end(),[](const auto& l,const auto& r){return l.inventory_slot<r.inventory_slot;});
    result.wire=response(); // complete wire prepared before ANY write
    sqlite_detail::execute(db_,"PRAGMA defer_foreign_keys=ON"); // selected stable selector survives delete/reinsert
    for(const auto* table:{"character_weapon_slot_metadata","character_armor_slot_metadata","character_teleport_gem_metadata","character_beast_snapshot_custody"}){
        const auto column=std::string(table)=="character_beast_snapshot_custody"?"inventory_slot":"slot";
        const auto sql="DELETE FROM "+std::string(table)+" WHERE character_id=? AND "+column+" IN(?,?)";
        sqlite_detail::Statement erase(db_,sql.c_str());erase.bind_id(1,actor);erase.bind(2,a);erase.bind(3,b);erase.done();
    }
    for(const auto slot:{a,b}){
        const auto& before=*expected.bag.scalar[slot];const auto& after=*next.bag.scalar[slot];
        sqlite_detail::Statement q(db_,"UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=? WHERE character_id=? AND slot=? AND item_id=? AND count=? AND revision=? AND source_sha256=? AND design_id='CUSTOM-0015'");
        q.bind(1,after.item_id);q.bind(2,after.count);q.bind_id(3,after.revision);q.bind_id(4,actor);q.bind(5,slot);q.bind(6,before.item_id);q.bind(7,before.count);q.bind_id(8,before.revision);q.bind(9,before.source_sha256);q.done();require(sqlite3_changes(db_)==1,"Beast move scalar CAS conflict");
    }
    for(const auto& row:next.bag.armor)if(row.slot==a||row.slot==b){
        ArmorForeignOverlay overlay{row.slot,row.logical20,row.revision,row.origin,row.provenance,SqliteArmorSlotRepository::source_sha256,SqliteArmorSlotRepository::client_sha256,SqliteArmorSlotRepository::design_id};foreign_insert(db_,"character_armor_slot_metadata",actor,overlay,false);
    }
    for(const auto& row:next.bag.weapons)if(row.slot==a||row.slot==b)foreign_insert(db_,"character_weapon_slot_metadata",actor,row,false);
    for(const auto& row:next.bag.gems)if(row.slot==a||row.slot==b)foreign_insert(db_,"character_teleport_gem_metadata",actor,row,true);
    for(const auto& row:next.beasts)if(row.inventory_slot==a||row.inventory_slot==b)beast_insert(db_,row);
    if(next.selection!=expected.selection){
        require(next.selection&&expected.selection,"Beast move cannot create/delete selection");
        sqlite_detail::Statement q(db_,"UPDATE character_beast_selection_0085 SET custody_revision=?,revision=? WHERE character_id=? AND selector=? AND custody_revision=? AND revision=? AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0085'");
        q.bind_id(1,next.selection->custody_revision);q.bind_id(2,next.selection->revision);q.bind_id(3,actor);q.bind(4,expected.selection->selector);q.bind_id(5,expected.selection->custody_revision);q.bind_id(6,expected.selection->revision);q.done();require(sqlite3_changes(db_)==1,"Beast move selection CAS conflict");
    }
    require(armor_.load_snapshot(expected.bag.account,actor)==next.bag&&beasts_.load_owned(expected.bag.account,actor)==next.beasts&&beasts_.load_selection_record(expected.bag.account,actor)==next.selection,"Beast move full resulting custody mismatch");
    require(guard(db_,exclusions(actor,expected.request),&expected.peripheral)==expected.peripheral,"Beast move changed unrelated saved rows/schema");
    sqlite_detail::Statement foreign_keys(db_,"PRAGMA foreign_key_check");require(!foreign_keys.row(),"Beast move foreign key mismatch");
    tx.commit();result.changed=true;return result;
}
SqliteBeastBagRepository::Result SqliteBeastBagRepository::discard(const Snapshot& expected,
        const RecoveredInventoryDiscard::Request& use,const std::string& receipt){
    static_assert(std::is_nothrow_move_constructible_v<Result>,"Committed beast discard must return without allocation failure");
    require(expected.domain==Domain::OrdinaryBag&&use.slot<30&&use.quantity==1&&
        expected.request.source_slot==use.slot&&expected.request.destination_slot==use.slot&&receipt_key(receipt),"Beast discard source/frame/receipt domain");
    require(sqlite3_get_autocommit(db_)!=0,"Beast discard requires standalone transaction");
    require_discard_schema(db_);
    sqlite_detail::Statement fk(db_,"PRAGMA foreign_keys");require(fk.row()&&fk.integer(0)==1,"Beast discard requires foreign keys");
    sqlite_detail::Transaction tx(db_);const auto account=expected.bag.account,actor=expected.bag.character;
    require(capture(account,actor,expected.request)==expected&&!discarded(db_,receipt),"Beast discard whole saved-state CAS or duplicate receipt");
    const auto no_battle=[&]{sqlite_detail::Statement q(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");q.bind_id(1,actor);require(!q.row(),"Beast discard during pending battle");};
    no_battle();
    const auto* source=at(expected.beasts,use.slot,[](const auto& row){return row.inventory_slot;});
    require(source&&source->panel.metadata_key()==use.item&&expected.bag.scalar[use.slot]&&
        expected.bag.scalar[use.slot]->item_id==use.item&&expected.bag.scalar[use.slot]->count==1,"Beast discard requires exact owned whole PET custody");
    const auto fields=source->inventory_fields();
    require(fields&&!fields->native_exploring_label()&&!source->panel.control7_alternate()&&!source->panel.control8_alternate(),"Beast discard outside admitted custom inactive presentation domain");
    Result result{expected,{},true};auto& next=result.after;
    const auto old_revision=next.bag.scalar[use.slot]->revision;
    next.bag.scalar[use.slot]->item_id=0;next.bag.scalar[use.slot]->count=0;
    next.bag.scalar[use.slot]->revision=advance(old_revision);
    std::optional<SqliteBeastSnapshotRepository::SelectionRecord> retired;
    if(next.selection&&next.selection->selector==source->panel.selector()){retired=next.selection;next.selection.reset();}
    std::erase_if(next.beasts,[&](const auto& row){return row.inventory_slot==use.slot;});
    const auto audit=removed_state(*source,retired);
    // CUSTOM presentation pairing:4B rebinds85ABD to the affected physical
    // slot, then native41 closes the current beast UI (including old9F view).
    // The BYTE does not replace a surviving persisted logical selection.
    std::vector<std::uint8_t> logical{0x4b,use.slot,0};
    const auto clear=RecoveredInventory::clear_slot(use.slot);require(clear.has_value(),"Beast discard native41 clear rejected");
    logical.insert(logical.end(),clear->begin(),clear->end());result.wire=RecoveredWorldFrame::encode(logical);
    // Every reply and journal allocation is complete before ANY destruction.
    if(retired){
        sqlite_detail::Statement q(db_,"DELETE FROM character_beast_selection_0085 WHERE character_id=? AND selector=? AND custody_revision=? AND revision=? AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0085'");
        q.bind_id(1,actor);q.bind(2,retired->selector);q.bind_id(3,retired->custody_revision);q.bind_id(4,retired->revision);q.done();require(sqlite3_changes(db_)==1,"Beast discard selected or stale binding CAS failed");
    }
    sqlite_detail::Statement erase(db_,"DELETE FROM character_beast_snapshot_custody WHERE character_id=? AND inventory_slot=? AND selector=? AND bag_revision=? AND inventory_metadata=? AND panel4c=? AND COALESCE(explorationc5,X'')=? AND revision=? AND origin=? AND evidence_id=? AND source_sha256=? AND client_sha256=? AND design_id='CUSTOM-0085'");
    erase.bind_id(1,actor);erase.bind(2,use.slot);erase.bind(3,source->panel.selector());erase.bind_id(4,source->bag_revision);erase.bind_blob(5,source->inventory_metadata);erase.bind_blob(6,source->panel.bytes);
    if(source->exploration)erase.bind_blob(7,source->exploration->bytes);else erase.bind_blob(7,std::span<const std::uint8_t>{});
    erase.bind_id(8,source->revision);erase.bind(9,source->origin);erase.bind(10,source->evidence_id);erase.bind(11,std::string(NativeBeastSourceCatalog::source_sha256));erase.bind(12,std::string(SqliteBeastSnapshotRepository::client_sha256));erase.done();require(sqlite3_changes(db_)==1,"Beast discard full custody delete CAS failed");
    sqlite_detail::Statement scalar(db_,"UPDATE diagnostic_inventory_slots SET item_id=0,count=0,revision=? WHERE character_id=? AND slot=? AND item_id=? AND count=1 AND revision=? AND source_sha256=? AND design_id='CUSTOM-0015'");
    scalar.bind_id(1,next.bag.scalar[use.slot]->revision);scalar.bind_id(2,actor);scalar.bind(3,use.slot);scalar.bind(4,use.item);scalar.bind_id(5,old_revision);scalar.bind(6,std::string(NativeBeastSourceCatalog::source_sha256));scalar.done();require(sqlite3_changes(db_)==1,"Beast discard scalar clear CAS failed");
    sqlite_detail::Statement insert(db_,"INSERT INTO character_beast_discard_receipts_0085 VALUES(?,?,?,39,?,?,1,?,?,?,'CUSTOM-0085')");
    insert.bind(1,receipt);insert.bind_id(2,account);insert.bind_id(3,actor);insert.bind(4,use.item);insert.bind(5,use.slot);insert.bind_id(6,old_revision);insert.bind_id(7,next.bag.scalar[use.slot]->revision);insert.bind(8,audit);insert.done();require(sqlite3_changes(db_)==1,"Beast discard journal insertion failed");
    sqlite_detail::Statement journal(db_,"SELECT account_id,character_id,operation,item_id,source,quantity,before_bag_revision,after_bag_revision,removed_state,design_id FROM character_beast_discard_receipts_0085 WHERE receipt=?");journal.bind(1,receipt);
    require(journal.row()&&journal.number<std::uint64_t>(0)==account&&journal.number<std::uint64_t>(1)==actor&&journal.integer(2)==39&&journal.number<std::uint16_t>(3)==use.item&&journal.number<std::uint8_t>(4)==use.slot&&journal.integer(5)==1&&journal.number<std::uint64_t>(6)==old_revision&&journal.number<std::uint64_t>(7)==next.bag.scalar[use.slot]->revision&&journal.text(8)==audit&&journal.text(9)=="CUSTOM-0085"&&!journal.row(),"Beast discard exact journal readback conflict");
    require(projector_.capture_proof(account,actor).snapshot()==next.bag&&beasts_.load_owned(account,actor)==next.beasts&&beasts_.load_selection_record(account,actor)==next.selection,"Beast discard resulting complete bag/custody/selection mismatch");
    auto allowed=exclusions(actor,expected.request);allowed["character_beast_discard_receipts_0085"]="receipt<>'"+receipt+"'";
    require(guard(db_,allowed,&expected.peripheral)==expected.peripheral,"Beast discard changed unrelated saved values/schema/receipt history");
    no_battle();sqlite_detail::Statement foreign(db_,"PRAGMA foreign_key_check");require(!foreign.row(),"Beast discard foreign key mismatch");
    tx.commit();return result;
}
std::vector<std::uint8_t> SqliteBeastBagRepository::refresh_source(std::uint64_t account,std::uint64_t character,std::uint8_t slot){
    require(slot<30&&sqlite3_get_autocommit(db_)!=0,"Beast refusal projection requires standalone ordinary source read");
    sqlite_detail::execute(db_,"BEGIN");
    struct End{sqlite3* db;bool done=false;~End(){if(!done)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}} end{db_};
    const auto proof=projector_.capture_proof(account,character);
    require(proof.snapshot().scalar[slot].has_value(),"Beast refusal source has no owned capacity");
    const auto logical=projector_.project(account,character,slot,*proof.snapshot().scalar[slot]);
    auto wire=RecoveredWorldFrame::encode(logical);projector_.verify_proof_in_transaction(proof);
    sqlite_detail::execute(db_,"COMMIT");end.done=true;return wire;
}
}
