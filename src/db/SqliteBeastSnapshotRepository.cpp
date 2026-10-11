#include "db/SqliteBeastSnapshotRepository.h"
#include "db/SqliteSupport.h"
#include "protocol/RecoveredWorldFrame.h"
#include "protocol/RecoveredInventoryProjection.h"
#include "protocol/RecoveredBeastInventoryProjection.h"
#include <algorithm>
#include <bit>
#include <cstring>
#include <map>
#include <limits>
namespace god2 {
namespace {
void require(bool yes,const char* error){if(!yes)throw DatabaseError(error);}
struct ReadScope {
    sqlite3* db;bool owns,finished=false;
    explicit ReadScope(sqlite3* value):db(value),owns(sqlite3_get_autocommit(db)!=0){if(owns)sqlite_detail::execute(db,"BEGIN");}
    ~ReadScope(){if(owns&&!finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){if(owns)sqlite_detail::execute(db,"COMMIT");finished=true;}
};
}
SqliteBeastSnapshotRepository::SqliteBeastSnapshotRepository(sqlite3* db):db_(db){require(db_!=nullptr,"Null beast custody database");require_schema(db_);}
const char* SqliteBeastSnapshotRepository::schema() noexcept{return R"SQL(
CREATE TABLE character_beast_snapshot_custody (
 character_id INTEGER NOT NULL REFERENCES recovered_characters(id),
 inventory_slot INTEGER NOT NULL CHECK(typeof(inventory_slot)='integer' AND inventory_slot BETWEEN 0 AND 29),
 selector INTEGER NOT NULL CHECK(typeof(selector)='integer' AND selector BETWEEN 0 AND 255),
 bag_revision INTEGER NOT NULL CHECK(typeof(bag_revision)='integer' AND bag_revision BETWEEN 1 AND 9223372036854775807),
 inventory_metadata BLOB NOT NULL CHECK(typeof(inventory_metadata)='blob' AND length(inventory_metadata)=20),
 panel4c BLOB NOT NULL CHECK(typeof(panel4c)='blob' AND length(panel4c)=17 AND substr(panel4c,1,1)=X'4C'),
 explorationc5 BLOB CHECK(explorationc5 IS NULL OR (typeof(explorationc5)='blob' AND length(explorationc5)=309 AND substr(explorationc5,1,1)=X'C5')),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision BETWEEN 1 AND 9223372036854775807),
 origin TEXT NOT NULL CHECK(origin IN ('NATIVE_OBSERVED','NATIVE_VERIFIED','CUSTOM_DESIGNED','CUSTOM_TEST_NOT_NATIVE')),
 evidence_id TEXT NOT NULL CHECK(length(evidence_id) BETWEEN 1 AND 512 AND instr(evidence_id,char(0))=0),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'),
 client_sha256 TEXT NOT NULL CHECK(client_sha256='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0085'),
 PRIMARY KEY(character_id,inventory_slot),UNIQUE(character_id,selector),
 FOREIGN KEY(character_id,inventory_slot) REFERENCES diagnostic_inventory_slots(character_id,slot)
);
)SQL";}
const char* SqliteBeastSnapshotRepository::selection_schema() noexcept{return R"SQL(
CREATE TABLE character_beast_selection_0085 (
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id),
 selector INTEGER NOT NULL CHECK(typeof(selector)='integer' AND selector BETWEEN 0 AND 255),
 custody_revision INTEGER NOT NULL CHECK(typeof(custody_revision)='integer' AND custody_revision BETWEEN 1 AND 9223372036854775807),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision BETWEEN 1 AND 9223372036854775807),
 origin TEXT NOT NULL CHECK(origin='CUSTOM_DESIGNED'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0085'),
 FOREIGN KEY(character_id,selector) REFERENCES character_beast_snapshot_custody(character_id,selector)
);
CREATE TABLE beast_selection_schema_0085 (
 version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version=1),
 sql_text TEXT NOT NULL,
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0085')
);
)SQL";}
std::string SqliteBeastSnapshotRepository::equipment_schema(){
    std::string result=schema();
    const std::string old="inventory_slot BETWEEN 0 AND 29";
    result.replace(result.find(old),old.size(),"(inventory_slot BETWEEN 0 AND 29 OR inventory_slot=37)");
    return result;
}
namespace {
// New feature migration consumer; no change to relations53 preservation code.
#include "../relations53/preservation.inc"
constexpr const char* equipment_feature_schema=R"SQL(
CREATE TABLE beast_equipment_schema_0085 (
 version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version=2),
 sql_text TEXT NOT NULL,
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0085')
);
)SQL";
constexpr const char* beast_feature_schema=R"SQL(
CREATE TABLE beast_custody_schema_0085 (
 version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version=1),
 sql_text TEXT NOT NULL,
 client_sha256 TEXT NOT NULL CHECK(client_sha256='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0085')
);
)SQL";
using Objects=std::vector<std::array<std::string,4>>;
Objects beast_objects(sqlite3* db){
    sqlite_detail::Statement q(db,"SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master WHERE tbl_name IN('character_beast_snapshot_custody','beast_custody_schema_0085') ORDER BY type,name");
    Objects result;while(q.row())result.push_back({q.text(0),q.text(1),q.text(2),q.text(3)});return result;
}
Objects selection_objects(sqlite3* db){
    sqlite_detail::Statement q(db,"SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master WHERE tbl_name IN('character_beast_selection_0085','beast_selection_schema_0085') ORDER BY type,name");
    Objects result;while(q.row())result.push_back({q.text(0),q.text(1),q.text(2),q.text(3)});return result;
}
Objects equipment_objects(sqlite3* db){
    sqlite_detail::Statement q(db,"SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master WHERE tbl_name='beast_equipment_schema_0085' ORDER BY type,name");
    Objects result;while(q.row())result.push_back({q.text(0),q.text(1),q.text(2),q.text(3)});return result;
}
Objects peripheral_objects(sqlite3* db){
    sqlite_detail::Statement q(db,"SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master WHERE tbl_name NOT IN('character_beast_snapshot_custody','beast_equipment_schema_0085') ORDER BY type,name");
    Objects result;while(q.row())result.push_back({q.text(0),q.text(1),q.text(2),q.text(3)});return result;
}
Guard migration_rows(sqlite3* db){
    auto rows=guard(db,{});rows.erase(":sqlite_master");rows.erase("character_beast_snapshot_custody:schema");
    rows.erase("beast_equipment_schema_0085");rows.erase("beast_equipment_schema_0085:schema");return rows;
}
}
void SqliteBeastSnapshotRepository::require_schema(sqlite3* db){
    require(db!=nullptr,"Null beast feature database");
    sqlite3* expected=nullptr;sqlite_detail::check(db,sqlite3_open(":memory:",&expected));
    struct Close{sqlite3* db;~Close(){sqlite3_close_v2(db);}} close{expected};
    const bool equipment=!equipment_objects(db).empty();
    sqlite_detail::execute(expected,beast_feature_schema);sqlite_detail::execute(expected,equipment?equipment_schema():schema());
    require(beast_objects(db)==beast_objects(expected),"Beast feature schema/index/trigger mismatch");
    sqlite_detail::Statement row(db,"SELECT version,sql_text,client_sha256,design_id FROM beast_custody_schema_0085");
    require(row.row()&&row.integer(0)==1&&row.text(1)==schema()&&row.text(2)==client_sha256&&row.text(3)==design_id&&!row.row(),"Beast feature immutable version mismatch");
    sqlite_detail::execute(expected,selection_schema());
    require(selection_objects(db)==selection_objects(expected),"Beast selection schema/index/trigger mismatch");
    sqlite_detail::Statement selection(db,"SELECT version,sql_text,design_id FROM beast_selection_schema_0085");
    require(selection.row()&&selection.integer(0)==1&&selection.text(1)==selection_schema()&&selection.text(2)==design_id&&!selection.row(),"Beast selection immutable version mismatch");
    if(equipment){
        sqlite_detail::execute(expected,equipment_feature_schema);
        require(equipment_objects(db)==equipment_objects(expected),"Beast equipment feature schema mismatch");
        sqlite_detail::Statement ledger(db,"SELECT version,sql_text,design_id FROM beast_equipment_schema_0085");
        require(ledger.row()&&ledger.integer(0)==2&&ledger.text(1)==equipment_schema()&&ledger.text(2)==design_id&&!ledger.row(),"Beast equipment v2 ledger mismatch");
    }
}
void SqliteBeastSnapshotRepository::require_equipment_schema(sqlite3* db){
    require_schema(db);require(!equipment_objects(db).empty(),"Beast equipment v2 feature not installed");
}
void SqliteBeastSnapshotRepository::install_schema(sqlite3* db){
    require(db&&sqlite3_get_autocommit(db)!=0,"Beast feature installation requires standalone transaction");
    sqlite_detail::Transaction tx(db);
    const auto existing=beast_objects(db);
    if(existing.empty()){
        // Called only after the managed base migration. Independent feature
        // ledger leaves immutable1..53 history and guild validators untouched.
        sqlite_detail::Statement base(db,"SELECT count(*) FROM schema_migrations");
        require(base.row()&&base.integer(0)>0,"Beast feature requires migrated base database");
        sqlite_detail::execute(db,beast_feature_schema);sqlite_detail::execute(db,schema());
        sqlite_detail::Statement version(db,"INSERT INTO beast_custody_schema_0085 VALUES(1,?,?,?)");
        version.bind(1,std::string(schema()));version.bind(2,std::string(client_sha256));version.bind(3,std::string(design_id));version.done();
    }
    // Selection has its own append-only feature ledger. Preserve custody v1.
    if(selection_objects(db).empty()){
        sqlite_detail::execute(db,selection_schema());
        sqlite_detail::Statement version(db,"INSERT INTO beast_selection_schema_0085 VALUES(1,?,?)");
        version.bind(1,std::string(selection_schema()));version.bind(2,std::string(design_id));version.done();
    }
    // Partially installed or altered objects fail; never silently adopt them.
    require_schema(db);
    if(equipment_objects(db).empty()){
        sqlite_detail::Statement fk(db,"PRAGMA foreign_keys");require(fk.row()&&fk.integer(0)==1,"Beast equipment migration requires foreign keys");
        sqlite_detail::Statement deferred(db,"PRAGMA defer_foreign_keys");require(deferred.row()&&deferred.integer(0)==0,"Beast equipment migration cannot borrow deferral");
        const auto before=migration_rows(db);const auto objects=peripheral_objects(db);
        // Recreate the parent under its original name. Never rename the live
        // parent (which could rewrite child FK targets), disable foreign keys
        // or overwrite v1 custody/selection ledger rows. Typed whole-save
        // equality below catches external cascade/trigger effects and rolls back.
        sqlite_detail::execute(db,"PRAGMA defer_foreign_keys=ON");
        sqlite_detail::execute(db,"CREATE TEMP TABLE beast_custody_v2_copy_0085 AS SELECT * FROM main.character_beast_snapshot_custody");
        sqlite_detail::execute(db,"DROP TABLE main.character_beast_snapshot_custody");
        sqlite_detail::execute(db,equipment_schema());
        sqlite_detail::execute(db,"INSERT INTO main.character_beast_snapshot_custody SELECT * FROM temp.beast_custody_v2_copy_0085");
        sqlite_detail::execute(db,"DROP TABLE temp.beast_custody_v2_copy_0085");
        sqlite_detail::execute(db,equipment_feature_schema);
        sqlite_detail::Statement ledger(db,"INSERT INTO beast_equipment_schema_0085 VALUES(2,?,?)");ledger.bind(1,equipment_schema());ledger.bind(2,std::string(design_id));ledger.done();
        require_schema(db);
        require(migration_rows(db)==before&&peripheral_objects(db)==objects,"Beast equipment migration changed saved values or unrelated schema");
        sqlite_detail::Statement foreign(db,"PRAGMA foreign_key_check");require(!foreign.row(),"Beast equipment migration foreign key mismatch");
    }
    tx.commit();
}
std::optional<std::vector<std::uint8_t>> SqliteBeastSnapshotRepository::open_owned_panel(
    std::uint64_t account,std::uint64_t character,std::uint8_t slot,std::uint16_t key){
    require(sqlite3_get_autocommit(db_)!=0,"Beast selection requires standalone transaction");
    sqlite_detail::Transaction tx(db_);require_schema(db_);owner(account,character);no_pending_battle(character);
    const auto saved=read(account,character,slot);
    if(!saved||saved->panel.metadata_key()!=key){tx.commit();return {};}
    // CUSTOM-0085 pairing: native25 producer and native4B/4C consumers are
    // independently recovered, not an observed original-server exchange.
    // 4B BYTE2 is unconsumed by the qualified receiver; custom policy uses0.
    std::vector<std::uint8_t> logical{0x4b,saved->panel.selector(),0};
    logical.insert(logical.end(),saved->panel.bytes.begin(),saved->panel.bytes.end());
    auto wire=RecoveredWorldFrame::encode(logical);
    // No original selection persistence semantics are inferred. Exact current
    // custody becomes the custom selected instance; unchanged requests are
    // idempotent. An earlier stale selection is retained until explicit25.
    sqlite_detail::Statement before(db_,"SELECT selector,custody_revision,revision,origin,design_id FROM character_beast_selection_0085 WHERE character_id=?");before.bind_id(1,character);
    const bool exists=before.row();std::uint64_t revision=0;
    if(exists){
        revision=before.number<std::uint64_t>(2);require(revision&&before.text(3)=="CUSTOM_DESIGNED"&&before.text(4)==design_id,"Beast selected provenance/revision mismatch");
        if(before.number<std::uint8_t>(0)==saved->panel.selector()&&before.number<std::uint64_t>(1)==saved->revision){tx.commit();return wire;}
    }
    require(revision<static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),"Beast selection revision exhausted");
    sqlite_detail::Statement write(db_,exists?
        "UPDATE character_beast_selection_0085 SET selector=?,custody_revision=?,revision=?,origin='CUSTOM_DESIGNED',design_id='CUSTOM-0085' WHERE character_id=? AND revision=?":
        "INSERT INTO character_beast_selection_0085(selector,custody_revision,revision,character_id,origin,design_id) VALUES(?,?,?,?,'CUSTOM_DESIGNED','CUSTOM-0085')");
    write.bind(1,saved->panel.selector());write.bind_id(2,saved->revision);write.bind_id(3,revision+1);write.bind_id(4,character);if(exists)write.bind_id(5,revision);write.done();
    require(sqlite3_changes(db_)==1,"Beast selection CAS conflict");
    const auto after=selected(account,character);require(after&&after->instance==*saved&&after->revision==revision+1,"Beast selection postwrite conflict");
    tx.commit();return wire;
}
std::optional<SqliteBeastSnapshotRepository::Selected> SqliteBeastSnapshotRepository::selected(std::uint64_t account,std::uint64_t character){
    sqlite_detail::Statement q(db_,"SELECT s.selector,s.custody_revision,s.revision,s.origin,s.design_id,c.inventory_slot FROM character_beast_selection_0085 s LEFT JOIN character_beast_snapshot_custody c ON c.character_id=s.character_id AND c.selector=s.selector WHERE s.character_id=?");q.bind_id(1,character);
    if(!q.row())return {};
    require(q.text(3)=="CUSTOM_DESIGNED"&&q.text(4)==design_id,"Selected beast origin mismatch");
    const auto saved=read(account,character,q.number<std::uint8_t>(5));
    const auto revision=q.number<std::uint64_t>(2);require(revision&&saved&&saved->panel.selector()==q.number<std::uint8_t>(0),"Selected beast instance missing");
    // Custody replacement retires selection authority until another explicit25;
    // preserve the stale row as data, never rewrite it on a read/reconnect.
    if(saved->revision!=q.number<std::uint64_t>(1))return {};
    return Selected{*saved,revision};
}
std::optional<SqliteBeastSnapshotRepository::Selected> SqliteBeastSnapshotRepository::load_selected(std::uint64_t account,std::uint64_t character){
    ReadScope scope(db_);require_schema(db_);owner(account,character);auto value=selected(account,character);scope.finish();return value;
}
std::optional<SqliteBeastSnapshotRepository::SelectionRecord> SqliteBeastSnapshotRepository::load_selection_record(std::uint64_t account,std::uint64_t character){
    ReadScope scope(db_);require_schema(db_);owner(account,character);
    sqlite_detail::Statement q(db_,"SELECT selector,custody_revision,revision,origin,design_id FROM character_beast_selection_0085 WHERE character_id=?");q.bind_id(1,character);
    std::optional<SelectionRecord> result;
    if(q.row()){
        require(q.text(3)=="CUSTOM_DESIGNED"&&q.text(4)==design_id,"Beast selection lease provenance mismatch");
        result=SelectionRecord{q.number<std::uint8_t>(0),q.number<std::uint64_t>(1),q.number<std::uint64_t>(2)};
        require(result->custody_revision&&result->revision,"Beast selection lease revision missing");
    }
    scope.finish();return result;
}
SqliteBeastSnapshotRepository::Projection SqliteBeastSnapshotRepository::restore(std::uint64_t account,std::uint64_t character){
    // Read-only display restoration may coexist with durable battle recovery;
    // new selection mutations still require no_pending_battle separately.
    ReadScope scope(db_);require_schema(db_);owner(account,character);
    Projection result;result.instances=load_owned(account,character);result.selected=selected(account,character);
    for(const auto& saved:result.instances){
        const auto bytes=RecoveredBeastInventoryProjection::encode({saved.inventory_slot,1,saved.inventory_metadata});
        require(bytes.has_value(),"Beast full bag projection rejected");result.logical.insert(result.logical.end(),bytes->begin(),bytes->end());
    }
    // Reconnect restores selected4C without unsolicited4B panel opening or
    // explorationC5. Modal/activity/timer recovery remains separate work.
    if(result.selected)result.logical.insert(result.logical.end(),result.selected->instance.panel.bytes.begin(),result.selected->instance.panel.bytes.end());
    scope.finish();return result;
}
void SqliteBeastSnapshotRepository::owner(std::uint64_t account,std::uint64_t character){
    require(account&&character,"Invalid beast owner");sqlite_detail::Statement row(db_,"SELECT 1 FROM recovered_characters WHERE account_id=? AND id=?");
    row.bind_id(1,account);row.bind_id(2,character);require(row.row(),"Beast ownership rejected");
}
void SqliteBeastSnapshotRepository::no_pending_battle(std::uint64_t character){
    sqlite_detail::Statement row(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
    row.bind_id(1,character);require(!row.row(),"Beast custody change during pending battle");
}
void SqliteBeastSnapshotRepository::validate(const StoredBeastSnapshot& value){
    const auto limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
    require(value.account&&value.character&&RecoveredBeastInventoryProjection::domain(value.inventory_slot)&&value.bag_revision&&value.bag_revision<=limit&&value.revision&&value.revision<=limit,"Beast custody identity/revision domain");
    if(value.inventory_slot==37)require(!equipment_objects(db_).empty(),"Beast37 custody requires installed v2 feature");
    require(value.origin=="NATIVE_OBSERVED"||value.origin=="NATIVE_VERIFIED"||value.origin=="CUSTOM_DESIGNED"||value.origin=="CUSTOM_TEST_NOT_NATIVE","Beast snapshot origin unqualified");
    require(!value.evidence_id.empty()&&value.evidence_id.size()<=512&&value.evidence_id.find('\0')==std::string::npos,"Beast snapshot evidence invalid");
    const auto panel=RecoveredBeastPanel::decode_snapshot(value.panel.bytes);
    require(panel.has_value()&&NativeBeastSourceCatalog::lookup(panel->metadata_key()),"Beast snapshot key/source unqualified");
    // Mechanical display admission only: three initialized label pointers and
    // the native division denominator. Not a fatigue/growth/eligibility rule.
    require(panel->kind_display_raw2()<3&&panel->meter_denominator_raw11()!=0,"Beast selected display state unqualified");
    const auto fields=value.inventory_fields();
    require(fields.has_value()&&fields->key()==panel->metadata_key(),"Beast instance metadata key/type/source mismatch");
    const auto key=fields->key();
    // Both classic and packed-date branches retain their original full20
    // bytes. Do not impose EXP caps or cross-field equality from tooltip text.
    sqlite_detail::Statement scalar(db_,"SELECT item_id,count,revision,source_sha256,design_id FROM diagnostic_inventory_slots WHERE character_id=? AND slot=?");
    scalar.bind_id(1,value.character);scalar.bind(2,value.inventory_slot);
    require(scalar.row()&&scalar.number<std::uint16_t>(0)==key&&scalar.number<std::uint8_t>(1)==1&&scalar.number<std::uint64_t>(2)==value.bag_revision&&scalar.text(3)==NativeBeastSourceCatalog::source_sha256&&scalar.text(4)=="CUSTOM-0015","Beast custody lacks exact existing owned scalar");
    for(const auto* table:{"character_weapon_slot_metadata","character_armor_slot_metadata","character_teleport_gem_metadata"}){
        sqlite_detail::Statement exists(db_,"SELECT 1 FROM sqlite_master WHERE type='table' AND name=?");exists.bind(1,std::string(table));
        if(exists.row()){
            const auto sql="SELECT 1 FROM "+std::string(table)+" WHERE character_id=? AND slot=?";
            sqlite_detail::Statement overlay(db_,sql.c_str());overlay.bind_id(1,value.character);overlay.bind(2,value.inventory_slot);
            require(!overlay.row(),"Beast custody collides with another full instance overlay");
        }
    }
    if(value.exploration){
        const auto exploration=RecoveredBeastExploration::decode_snapshot(value.exploration->bytes);
        require(exploration&&exploration->metadata_key()==key&&exploration->selector()==panel->selector(),"Beast exploration context belongs to another instance");
    }
}
std::optional<StoredBeastSnapshot> SqliteBeastSnapshotRepository::read(std::uint64_t account,std::uint64_t character,std::uint8_t slot){
    require(RecoveredBeastInventoryProjection::domain(slot),"Beast custody slot outside bag/equipment37 domain");
    sqlite_detail::Statement row(db_,"SELECT selector,bag_revision,inventory_metadata,panel4c,explorationc5,revision,origin,evidence_id,source_sha256,client_sha256,design_id,explorationc5 IS NULL FROM character_beast_snapshot_custody WHERE character_id=? AND inventory_slot=?");
    row.bind_id(1,character);row.bind(2,slot);if(!row.row())return {};
    StoredBeastSnapshot value;value.account=account;value.character=character;value.inventory_slot=slot;value.bag_revision=row.number<std::uint64_t>(1);
    const auto metadata=row.blob(2,20,20);std::copy(metadata.begin(),metadata.end(),value.inventory_metadata.begin());
    const auto panel=RecoveredBeastPanel::decode_snapshot(row.blob(3,17,17));require(panel.has_value(),"Saved beast panel malformed");value.panel=*panel;
    if(!row.integer(11)){const auto explore=RecoveredBeastExploration::decode_snapshot(row.blob(4,309,309));require(explore.has_value(),"Saved beast exploration malformed");value.exploration=*explore;}
    value.revision=row.number<std::uint64_t>(5);value.origin=row.text(6);value.evidence_id=row.text(7);
    require(row.number<std::uint8_t>(0)==panel->selector()&&row.text(8)==NativeBeastSourceCatalog::source_sha256&&row.text(9)==client_sha256&&row.text(10)==design_id,"Beast custody namespace/build mismatch");
    validate(value);return value;
}
std::optional<StoredBeastSnapshot> SqliteBeastSnapshotRepository::load(std::uint64_t account,std::uint64_t character,std::uint8_t slot){
    ReadScope scope(db_);require_schema(db_);owner(account,character);auto value=read(account,character,slot);scope.finish();return value;
}
std::vector<StoredBeastSnapshot> SqliteBeastSnapshotRepository::load_owned(std::uint64_t account,std::uint64_t character){
    ReadScope scope(db_);require_schema(db_);owner(account,character);sqlite_detail::Statement rows(db_,"SELECT inventory_slot FROM character_beast_snapshot_custody WHERE character_id=? ORDER BY inventory_slot");rows.bind_id(1,character);
    std::vector<StoredBeastSnapshot> values;while(rows.row()){const auto value=read(account,character,rows.number<std::uint8_t>(0));require(value.has_value(),"Beast custody vanished during snapshot read");values.push_back(*value);}scope.finish();return values;
}
StoredBeastSnapshot SqliteBeastSnapshotRepository::store_existing_owned(const StoredBeastSnapshot& supplied,const std::optional<StoredBeastSnapshot>& expected){
    // Standalone server import, never borrow an unrelated gameplay transaction.
    require(sqlite3_get_autocommit(db_)!=0,"Beast trusted custody import requires standalone transaction");
    sqlite_detail::Transaction tx(db_);require_schema(db_);owner(supplied.account,supplied.character);no_pending_battle(supplied.character);
    const auto current=read(supplied.account,supplied.character,supplied.inventory_slot);require(current==expected,"Beast custody full expected snapshot changed");
    auto next=supplied;const auto revision=current?current->revision:0;
    require(revision<static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),"Beast custody revision exhausted");next.revision=revision+1;validate(next);
    // Prepare exact native logical records before COMMIT. This is ordinary
    // runtime serialization, not execution or acceptance of a client packet.
    (void)RecoveredWorldFrame::encode(next.panel.bytes);if(next.exploration)(void)RecoveredWorldFrame::encode(next.exploration->bytes);
    const char* sql=current?
        "UPDATE character_beast_snapshot_custody SET selector=?,bag_revision=?,inventory_metadata=?,panel4c=?,explorationc5=NULLIF(?,X''),revision=?,origin=?,evidence_id=?,source_sha256=?,client_sha256=?,design_id=? WHERE character_id=? AND inventory_slot=? AND revision=?":
        "INSERT INTO character_beast_snapshot_custody(selector,bag_revision,inventory_metadata,panel4c,explorationc5,revision,origin,evidence_id,source_sha256,client_sha256,design_id,character_id,inventory_slot) VALUES(?,?,?,?,NULLIF(?,X''),?,?,?,?,?,?,?,?)";
    sqlite_detail::Statement write(db_,sql);write.bind(1,next.panel.selector());write.bind_id(2,next.bag_revision);write.bind_blob(3,next.inventory_metadata);write.bind_blob(4,next.panel.bytes);
    // Keep NULL distinct from a forged zero-filled exploration payload.
    if(next.exploration)write.bind_blob(5,next.exploration->bytes);else write.bind_blob(5,std::span<const std::uint8_t>{});
    write.bind_id(6,next.revision);write.bind(7,next.origin);write.bind(8,next.evidence_id);write.bind(9,std::string(NativeBeastSourceCatalog::source_sha256));write.bind(10,std::string(client_sha256));write.bind(11,std::string(design_id));write.bind_id(12,next.character);write.bind(13,next.inventory_slot);if(current)write.bind_id(14,current->revision);write.done();
    require(sqlite3_changes(db_)==1,"Beast custody write conflict");tx.commit();return next;
}
}
