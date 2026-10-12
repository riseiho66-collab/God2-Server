#include "db/SqliteOwnedInventoryRepository.h"
#include "db/SqliteNativeWorldEntrySnapshotRepository.h"
#include "db/SqliteSupport.h"
#include "db/NativeWeaponCatalog.h"
#include "db/NativeArmorCatalog.h"
#include "game/OwnedStackQuantity.h"
#include <algorithm>
#include <limits>
#include <map>
#include <set>
#include <tuple>

namespace god2 {
namespace {
bool positive(std::uint64_t n) {return n && n<=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());}
bool text(std::string_view s,std::size_t max) {return !s.empty() && s.size()<=max && s.find('\0')==s.npos;}
bool digest(std::string_view s) {
    return s.size()==64 && std::all_of(s.begin(),s.end(),[](char c){return (c>='0'&&c<='9')||(c>='a'&&c<='f');});
}
struct ReadScope {
    sqlite3* db;bool own,finished=false;
    explicit ReadScope(sqlite3* p):db(p),own(sqlite3_get_autocommit(p)!=0) {if(own)sqlite_detail::execute(db,"BEGIN");}
    ~ReadScope(){if(own&&!finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){if(own)sqlite_detail::execute(db,"COMMIT");finished=true;}
};
using Location=std::pair<std::string,std::uint32_t>;
Location location(const OwnedInventoryCell& c) {return {c.location_kind,c.location_index};}
bool same_identity(const OwnedInventoryInstance& a,const OwnedInventoryInstance& b) {
    return a.id==b.id && a.definition_key==b.definition_key && a.stackable==b.stackable &&
        a.acquisition_sha256==b.acquisition_sha256 && a.acquisition_record==b.acquisition_record;
}
bool valid(const OwnedInventorySnapshot& v) {
    if(!positive(v.root.account_id)||!positive(v.root.id)||v.root.slot>=2||!text(v.root.created_at,2048)||
       (v.root.name_codepage!=0&&v.root.name_codepage!=936&&v.root.name_codepage!=950)||
       v.root.streamer_privilege>3||!positive(v.revision)||!digest(v.source_sha256)||
       !text(v.source_record,2048)||v.cells.size()>4096)return false;
    std::optional<Location> previous;std::set<std::uint64_t> ids;
    std::set<std::tuple<std::string,std::string,std::uint8_t>> native_slots;
    for(const auto& cell:v.cells) {
        if(!text(cell.location_kind,64)||(previous && *previous>=location(cell)))return false;
        previous=location(cell);if(!cell.instance)continue;
        const auto& item=*cell.instance;
        // CUSTOM-0089: qualify the full common64 quantity directly, before
        // any native BYTE projection. Occupied/unstackable rules stay separate.
        const auto quantity=OwnedStackQuantity::from(item.quantity);
        if(!positive(item.id)||!ids.insert(item.id).second||!positive(item.definition_key)||
           !positive(item.revision)||!quantity||!quantity->value()||(!item.stackable&&quantity->value()!=1)||
           !digest(item.acquisition_sha256)||!text(item.acquisition_record,2048)||item.aliases.size()>16)return false;
        std::optional<std::pair<std::string,std::string>> prior_alias;
        for(const auto& a:item.aliases) {
            const auto key=std::pair{a.client_sha256,a.profile};
            if(!digest(a.client_sha256)||!text(a.profile,64)||!digest(a.source_sha256)||
               !text(a.source_record,2048)||a.revision!=item.revision||a.record.empty()||a.record.size()>4096||
               (prior_alias && *prior_alias>=key)||
               !native_slots.emplace(a.client_sha256,a.profile,a.native_slot).second)return false;
            prior_alias=key;
        }
    }
    return true;
}
}
SqliteOwnedInventoryRepository::SqliteOwnedInventoryRepository(sqlite3* db,const SqliteAccountRepository& a,
    SqliteRecoveredCharacterRepository& c):db_(db),accounts_(a),characters_(c) {
    if(!db||!a.uses_connection(db)||!c.uses_connection(db))throw DatabaseError("Owned inventory requires exact common connection");
}
void SqliteOwnedInventoryRepository::owner() const {
    if(thread_!=std::this_thread::get_id())throw DatabaseError("Owned inventory game owner mismatch");
}
bool SqliteOwnedInventoryRepository::owns_sources(const AccountRepository& a,const RecoveredCharacterRepository& c) const noexcept {
    return &a==&accounts_ && &c==&characters_ && accounts_.uses_connection(db_) && characters_.uses_connection(db_);
}
void SqliteOwnedInventoryRepository::namespaces() const {
    sqlite_detail::Statement q(db_,"SELECT 1 FROM temp.sqlite_master WHERE name IN ('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases') OR tbl_name IN ('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases')");
    if(q.row())throw DatabaseError("Owned inventory TEMP shadow rejected");
}
bool SqliteOwnedInventoryRepository::root_current(const RecoveredCharacter& root) {
    namespaces();const auto roots=characters_.list_for_account(root.account_id);std::size_t found=0;
    for(const auto& r:roots)if(r.id==root.id) {if(!Snapshot::same_root(r,root))return false;++found;}
    sqlite_detail::Statement q(db_,"SELECT 1 FROM main.battle_reservations r LEFT JOIN main.battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
    q.bind_id(1,root.id);return found==1&&!q.row();
}
std::optional<SqliteOwnedInventoryRepository::Snapshot> SqliteOwnedInventoryRepository::load(std::uint64_t account,std::uint64_t character) {
    owner();if(issuer_active_){reentered_=true;throw DatabaseError("Owned inventory issuer reentered reader");}
    if(!positive(account)||!positive(character))throw DatabaseError("Invalid owned inventory owner");
    ReadScope scope(db_);namespaces();
    sqlite_detail::Statement h(db_,"SELECT h.account_id,h.character_id,h.root_slot,h.root_profile,h.root_created_at,h.root_name_codepage,h.root_streamer_privilege,h.revision,h.source_sha256,h.source_record FROM main.owned_inventory_headers h JOIN main.accounts a ON a.id=h.account_id JOIN main.recovered_characters c ON c.id=h.character_id AND c.account_id=h.account_id WHERE h.account_id=? AND h.character_id=?");
    h.bind_id(1,account);h.bind_id(2,character);
    if(!h.row()){scope.finish();return std::nullopt;}
    Snapshot v;v.root.account_id=h.number<std::uint64_t>(0);v.root.id=h.number<std::uint64_t>(1);v.root.slot=h.number<std::uint8_t>(2);
    const auto profile=h.blob(3,40,40);std::copy(profile.begin(),profile.end(),v.root.profile.begin());
    v.root.created_at=h.text(4);v.root.name_codepage=h.number<std::uint16_t>(5);v.root.streamer_privilege=h.number<std::uint8_t>(6);
    v.revision=h.number<std::uint64_t>(7);v.source_sha256=h.text(8);v.source_record=h.text(9);
    if(h.row())throw DatabaseError("Ambiguous owned inventory header");
    sqlite_detail::Statement cells(db_,"SELECT c.location_kind,c.location_index,COALESCE(c.instance_id,0),c.quantity,c.instance_revision,i.definition_key,i.stackable,i.acquisition_sha256,i.acquisition_record FROM main.owned_inventory_cells c LEFT JOIN main.owned_item_instances i ON i.id=c.instance_id WHERE c.account_id=? AND c.character_id=? ORDER BY c.location_kind COLLATE BINARY,c.location_index");
    cells.bind_id(1,account);cells.bind_id(2,character);
    while(cells.row()) {
        if(v.cells.size()>=4096)throw DatabaseError("Owned inventory population exceeds bounded storage");
        OwnedInventoryCell cell;cell.location_kind=cells.text(0);cell.location_index=cells.number<std::uint32_t>(1);
        const auto id=cells.number<std::uint64_t>(2),quantity=cells.number<std::uint64_t>(3),revision=cells.number<std::uint64_t>(4);
        if(id) {
            OwnedInventoryInstance item;item.id=id;item.quantity=quantity;item.revision=revision;
            item.definition_key=cells.number<std::uint64_t>(5);const auto stackable=cells.number<std::uint8_t>(6);
            if(stackable>1)throw DatabaseError("Invalid owned inventory stackability witness");item.stackable=stackable!=0;
            item.acquisition_sha256=cells.text(7);item.acquisition_record=cells.text(8);
            sqlite_detail::Statement aliases(db_,"SELECT client_sha256,profile,source_sha256,source_record,native_key,native_slot,revision,record FROM main.owned_item_native_aliases WHERE instance_id=? ORDER BY client_sha256 COLLATE BINARY,profile COLLATE BINARY");
            aliases.bind_id(1,id);
            while(aliases.row()) {
                if(item.aliases.size()>=16)throw DatabaseError("Owned inventory aliases exceed bounded storage");
                OwnedItemNativeAlias a;a.client_sha256=aliases.text(0);a.profile=aliases.text(1);a.source_sha256=aliases.text(2);a.source_record=aliases.text(3);
                a.native_key=aliases.number<std::uint16_t>(4);a.native_slot=aliases.number<std::uint8_t>(5);a.revision=aliases.number<std::uint64_t>(6);
                const auto bytes=aliases.blob(7,1,4096);a.record.assign(bytes.begin(),bytes.end());item.aliases.push_back(std::move(a));
            }
            cell.instance=std::move(item);
        }else if(quantity||revision)throw DatabaseError("Empty owned inventory cell carries quantity or revision");
        v.cells.push_back(std::move(cell));
    }
    if(!valid(v)||v.root.account_id!=account||v.root.id!=character)throw DatabaseError("Invalid owned inventory full population");
    scope.finish();return v;
}
void SqliteOwnedInventoryRepository::validate_change(const std::optional<Snapshot>& expected,const Snapshot& next) const {
    if(!valid(next)||(expected&&(!valid(*expected)||expected->root.account_id!=next.root.account_id||
       expected->root.id!=next.root.id||expected->revision>=next.revision)))
        throw DatabaseError("Invalid owned inventory full change");
    std::map<std::uint64_t,std::pair<Location,const OwnedInventoryInstance*>> before;
    if(expected)for(const auto& cell:expected->cells)if(cell.instance)before.emplace(cell.instance->id,std::pair{location(cell),&*cell.instance});
    for(const auto& cell:next.cells)if(cell.instance) {
        const auto& item=*cell.instance;const auto prior=before.find(item.id);
        if(prior!=before.end() && (!same_identity(*prior->second.second,item)||item.revision<prior->second.second->revision||
            ((location(cell)!=prior->second.first||item!=*prior->second.second)&&item.revision<=prior->second.second->revision)))
            throw DatabaseError("Owned inventory identity changed or revision failed to advance");
    }
}
void SqliteOwnedInventoryRepository::stage_replace(const std::optional<Snapshot>& expected,const Snapshot& next) {
    owner();if(!writing_||issuer_active_||reentered_||sqlite3_get_autocommit(db_))
        throw DatabaseError("Owned inventory stage needs its guarded outer transaction");
    validate_change(expected,next);
    std::map<std::uint64_t,std::pair<Location,const OwnedInventoryInstance*>> before;
    if(expected)for(const auto& cell:expected->cells)if(cell.instance)before.emplace(cell.instance->id,std::pair{location(cell),&*cell.instance});
    for(const auto& cell:next.cells)if(cell.instance && !before.contains(cell.instance->id)) {
        const auto& i=*cell.instance;
        // Permanent unique registry prevents duplicate minting, stealing from
        // another owner, receipt replay and resurrection of retired identities.
        sqlite_detail::Statement mint(db_,"INSERT INTO main.owned_item_instances(id,definition_key,stackable,acquisition_sha256,acquisition_record) VALUES(?,?,?,?,?)");
        mint.bind_id(1,i.id);mint.bind_id(2,i.definition_key);mint.bind(3,i.stackable?1:0);mint.bind(4,i.acquisition_sha256);mint.bind(5,i.acquisition_record);mint.done();
        if(sqlite3_changes(db_)!=1)throw DatabaseError("Owned inventory identity insertion failed");
    }
    if(expected) {
        for(const auto& [id,ignored]:before) {sqlite_detail::Statement a(db_,"DELETE FROM main.owned_item_native_aliases WHERE instance_id=?");a.bind_id(1,id);a.done();}
        sqlite_detail::Statement c(db_,"DELETE FROM main.owned_inventory_cells WHERE account_id=? AND character_id=?");
        c.bind_id(1,next.root.account_id);c.bind_id(2,next.root.id);c.done();
        if(static_cast<std::size_t>(sqlite3_changes(db_))!=expected->cells.size())throw DatabaseError("Owned inventory complete cell replacement drift");
    }
    sqlite_detail::Statement h(db_,expected?
        "UPDATE main.owned_inventory_headers SET root_slot=?,root_profile=?,root_created_at=?,root_name_codepage=?,root_streamer_privilege=?,revision=?,source_sha256=?,source_record=? WHERE account_id=? AND character_id=? AND revision=?":
        "INSERT INTO main.owned_inventory_headers(root_slot,root_profile,root_created_at,root_name_codepage,root_streamer_privilege,revision,source_sha256,source_record,account_id,character_id) VALUES(?,?,?,?,?,?,?,?,?,?)");
    h.bind(1,next.root.slot);h.bind_blob(2,next.root.profile);h.bind(3,next.root.created_at);h.bind(4,next.root.name_codepage);h.bind(5,next.root.streamer_privilege);
    h.bind_id(6,next.revision);h.bind(7,next.source_sha256);h.bind(8,next.source_record);h.bind_id(9,next.root.account_id);h.bind_id(10,next.root.id);if(expected)h.bind_id(11,expected->revision);
    h.done();if(sqlite3_changes(db_)!=1)throw DatabaseError("Owned inventory header CAS failed");
    for(const auto& cell:next.cells) {
        sqlite_detail::Statement c(db_,"INSERT INTO main.owned_inventory_cells(account_id,character_id,location_kind,location_index,instance_id,quantity,instance_revision) VALUES(?,?,?,?,NULLIF(?,0),?,?)");
        c.bind_id(1,next.root.account_id);c.bind_id(2,next.root.id);c.bind(3,cell.location_kind);c.bind(4,cell.location_index);
        c.bind_id(5,cell.instance?cell.instance->id:0);c.bind_id(6,cell.instance?cell.instance->quantity:0);c.bind_id(7,cell.instance?cell.instance->revision:0);c.done();
        if(cell.instance)for(const auto& a:cell.instance->aliases) {
            sqlite_detail::Statement q(db_,"INSERT INTO main.owned_item_native_aliases(instance_id,client_sha256,profile,source_sha256,source_record,native_key,native_slot,revision,record) VALUES(?,?,?,?,?,?,?,?,?)");
            q.bind_id(1,cell.instance->id);q.bind(2,a.client_sha256);q.bind(3,a.profile);q.bind(4,a.source_sha256);q.bind(5,a.source_record);q.bind(6,a.native_key);q.bind(7,a.native_slot);q.bind_id(8,a.revision);q.bind_blob(9,a.record);q.done();
        }
    }
}
std::optional<SqliteOwnedInventoryRepository::Committed> SqliteOwnedInventoryRepository::replace_from_issuer(
    std::optional<Snapshot> expected,Snapshot next,Issuer issuer) {
    owner();if(writing_){reentered_=true;throw DatabaseError("Owned inventory writer reentered");}
    if(!issuer||!sqlite3_get_autocommit(db_)||!owns_sources(accounts_,characters_))
        throw DatabaseError("Owned inventory needs full valid CAS and own transaction");
    validate_change(expected,next);
    writing_=true;reentered_=false;
    struct End {bool& busy;bool& reentry;~End(){busy=false;reentry=false;}} end{writing_,reentered_};
    {sqlite_detail::Statement fk(db_,"PRAGMA foreign_keys");if(!fk.row()||fk.integer(0)!=1||fk.row())throw DatabaseError("Owned inventory requires foreign keys");}
    sqlite_detail::Transaction tx(db_);
    const auto check=[&](const std::optional<Snapshot>& wanted) {
        if(reentered_||sqlite3_get_autocommit(db_)||!root_current(next.root)||load(next.root.account_id,next.root.id)!=wanted||
           !root_current(next.root)||reentered_)throw DatabaseError("Owned inventory source changed");
    };
    const auto issue=[&](Check phase) {
        const auto changes=sqlite3_total_changes64(db_);
        issuer_active_=true;struct Leave {bool& active;~Leave(){active=false;}} leave{issuer_active_};
        const auto supplied=issuer(expected,next,phase);
        if(reentered_||sqlite3_get_autocommit(db_)||sqlite3_total_changes64(db_)!=changes)
            throw DatabaseError("Owned inventory issuer changed transaction or wrote storage");
        return supplied&&*supplied==next;
    };
    check(expected);if(!issue(Check::Prepared))return std::nullopt;check(expected);
    if(!issue(Check::BeforeWrite))return std::nullopt;check(expected);
    stage_replace(expected,next);
    check(std::optional{next});if(!issue(Check::BeforeCommit))return std::nullopt;check(std::optional{next});
    std::optional<Committed> result{Committed(identity_,std::make_shared<const Snapshot>(next))};
    tx.commit();return result; // No post-COMMIT issuer, reload, retry or allocation.
}
std::optional<SqliteOwnedInventoryRepository::Committed> SqliteOwnedInventoryRepository::observe_committed(
    std::uint64_t account,std::uint64_t character) {
    owner();if(writing_){reentered_=true;return std::nullopt;}
    if(!sqlite3_get_autocommit(db_))throw DatabaseError("Owned inventory durable observation rejects borrowed transaction");
    ReadScope scope(db_);auto snapshot=load(account,character);
    if(!snapshot||!root_current(snapshot->root))return std::nullopt;
    std::optional<Committed> result{Committed(identity_,std::make_shared<const Snapshot>(std::move(*snapshot)))};
    scope.finish();return result;
}
bool SqliteOwnedInventoryRepository::committed_current(const Committed& token) {
    owner();if(writing_){reentered_=true;return false;}
    if(token.identity_!=identity_||!token.snapshot_||!sqlite3_get_autocommit(db_))return false;
    ReadScope scope(db_);const auto& wanted=*token.snapshot_;
    const bool same=load(wanted.root.account_id,wanted.root.id)==std::optional{wanted}&&root_current(wanted.root);
    scope.finish();return same;
}
std::optional<NativeItemDefinitionObservation> SqliteOwnedInventoryRepository::observe_native_definition(std::uint16_t key) {
    owner();
    if(writing_||issuer_active_){reentered_=true;return std::nullopt;}
    if(!key||key>=0x7f58)return std::nullopt;
    if(!sqlite3_get_autocommit(db_))throw DatabaseError("Native definition observation rejects borrowed transaction");
    writing_=true;reentered_=false;
    struct End {bool& writing;bool& reentered;~End(){writing=reentered=false;}} end{writing_,reentered_};
    ReadScope scope(db_);namespaces();
    sqlite_detail::Statement shadow(db_,"SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ('native_weapon_sources','native_weapon_rows','native_armor_sources','native_armor_rows') OR tbl_name COLLATE NOCASE IN ('native_weapon_sources','native_weapon_rows','native_armor_sources','native_armor_rows')");
    if(shadow.row())throw DatabaseError("Native definition TEMP shadow rejected");
    // The older catalogs use unqualified names. Require real main tables so
    // an attached schema cannot supply a missing formal source under that name.
    sqlite_detail::Statement tables(db_,"SELECT count(*) FROM main.sqlite_master WHERE type='table' AND name COLLATE NOCASE IN ('native_weapon_sources','native_weapon_rows','native_armor_sources','native_armor_rows')");
    if(!tables.row()||tables.integer(0)!=4||tables.row())throw DatabaseError("Native definition requires both actual main catalogs");
    const auto weapons=NativeWeaponCatalog(db_).read();
    const auto armors=NativeArmorCatalog(db_).read();
    if(weapons.empty()||armors.empty())return std::nullopt;
    std::optional<NativeItemDefinitionObservation> result;
    const auto keep=[&](const auto& source,const char* catalog) {
        if(source.item_id!=key)return;
        if(result||source.parsed_record.size()!=396||source.raw_record.empty())
            throw DatabaseError("Native definition missing or ambiguous qualified full row");
        NativeItemDefinitionObservation::Row row{source.family,source.item_id,source.source_record_index,
            source.source_line,source.decoded_offset,source.record_sha256,source.parsed_sha256,catalog,source.raw_record,{}};
        std::copy(source.parsed_record.begin(),source.parsed_record.end(),row.metadata.begin());
        result=NativeItemDefinitionObservation(std::move(row));
    };
    for(const auto& row:weapons)keep(row,"1a6e35c37950d5edada081b184c6b7f6d1f101929d4ccf46004747c8740cde26");
    for(const auto& row:armors)keep(row,NativeArmorCatalog::catalog_sha256);
    if(reentered_||sqlite3_get_autocommit(db_))throw DatabaseError("Native definition read scope changed or reentered");
    scope.finish();return result;
}
std::optional<NativeDeityEquipmentObservation> SqliteOwnedInventoryRepository::observe_native_deity_equipment(
    std::uint64_t account,std::uint64_t character) {
    owner();
    if(writing_||issuer_active_){reentered_=true;return std::nullopt;}
    if(!positive(account)||!positive(character))return std::nullopt;
    if(!sqlite3_get_autocommit(db_))throw DatabaseError("Native deity observation rejects borrowed transaction");
    writing_=true;reentered_=false;
    struct End {bool& writing;bool& reentered;~End(){writing=reentered=false;}} end{writing_,reentered_};
    ReadScope scope(db_);namespaces();
    sqlite_detail::Statement shadow(db_,"SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ('character_native_world_entries','accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements') OR tbl_name COLLATE NOCASE IN ('character_native_world_entries','accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements')");
    if(shadow.row())throw DatabaseError("Native deity TEMP shadow rejected");
    sqlite_detail::Statement table(db_,"SELECT count(*) FROM main.sqlite_master WHERE type='table' AND name COLLATE NOCASE IN ('character_native_world_entries','accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements')");
    if(!table.row()||table.integer(0)!=6||table.row())throw DatabaseError("Native deity requires actual main witness/common tables");
    auto saved=SqliteNativeWorldEntrySnapshotRepository(db_,accounts_,characters_).load(
        account,character,NativeDeityEquipmentObservation::client_pin,NativeDeityEquipmentObservation::kind);
    if(!saved)return std::nullopt;
    const auto records=RecoveredTaiwanDeityEquipmentState::Pair::parse_storage(saved->record);
    if(!records)throw DatabaseError("Native deity requires both complete D1/D2 records");
    if(!root_current(saved->root)||characters_.load_position(account,character)!=std::optional{saved->position})
        return std::nullopt;
    if(reentered_||sqlite3_get_autocommit(db_))throw DatabaseError("Native deity read scope changed or reentered");
    std::optional<NativeDeityEquipmentObservation> result{
        NativeDeityEquipmentObservation(std::move(*saved),*records)};
    scope.finish();return result;
}
std::string SqliteOwnedInventoryRepository::schema() {
    return R"SQL(CREATE TABLE main.owned_inventory_headers (
 account_id INTEGER NOT NULL CHECK(typeof(account_id)='integer' AND account_id>0),
 character_id INTEGER PRIMARY KEY CHECK(typeof(character_id)='integer' AND character_id>0),
 root_slot INTEGER NOT NULL CHECK(typeof(root_slot)='integer' AND root_slot BETWEEN 0 AND 1),
 root_profile BLOB NOT NULL CHECK(typeof(root_profile)='blob' AND length(root_profile)=40),
 root_created_at TEXT NOT NULL CHECK(typeof(root_created_at)='text' AND length(CAST(root_created_at AS BLOB)) BETWEEN 1 AND 2048 AND instr(root_created_at,char(0))=0),
 root_name_codepage INTEGER NOT NULL CHECK(typeof(root_name_codepage)='integer' AND root_name_codepage IN (0,936,950)),
 root_streamer_privilege INTEGER NOT NULL CHECK(typeof(root_streamer_privilege)='integer' AND root_streamer_privilege BETWEEN 0 AND 3),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 source_sha256 TEXT NOT NULL CHECK(typeof(source_sha256)='text' AND length(source_sha256)=64 AND source_sha256 NOT GLOB '*[^0-9a-f]*'),
 source_record TEXT NOT NULL CHECK(typeof(source_record)='text' AND length(CAST(source_record AS BLOB)) BETWEEN 1 AND 2048 AND instr(source_record,char(0))=0),
 UNIQUE(account_id,character_id), FOREIGN KEY(account_id) REFERENCES accounts(id), FOREIGN KEY(character_id) REFERENCES recovered_characters(id) ON DELETE CASCADE
);
CREATE TABLE main.owned_item_instances (
 id INTEGER PRIMARY KEY CHECK(typeof(id)='integer' AND id>0),
 definition_key INTEGER NOT NULL CHECK(typeof(definition_key)='integer' AND definition_key>0),
 stackable INTEGER NOT NULL CHECK(typeof(stackable)='integer' AND stackable IN (0,1)),
 acquisition_sha256 TEXT NOT NULL CHECK(typeof(acquisition_sha256)='text' AND length(acquisition_sha256)=64 AND acquisition_sha256 NOT GLOB '*[^0-9a-f]*'),
 acquisition_record TEXT NOT NULL CHECK(typeof(acquisition_record)='text' AND length(CAST(acquisition_record AS BLOB)) BETWEEN 1 AND 2048 AND instr(acquisition_record,char(0))=0),
 UNIQUE(acquisition_sha256,acquisition_record)
);
CREATE TABLE main.owned_inventory_cells (
 account_id INTEGER NOT NULL CHECK(typeof(account_id)='integer' AND account_id>0),
 character_id INTEGER NOT NULL CHECK(typeof(character_id)='integer' AND character_id>0),
 location_kind TEXT NOT NULL CHECK(typeof(location_kind)='text' AND length(CAST(location_kind AS BLOB)) BETWEEN 1 AND 64 AND instr(location_kind,char(0))=0),
 location_index INTEGER NOT NULL CHECK(typeof(location_index)='integer' AND location_index BETWEEN 0 AND 4294967295),
 instance_id INTEGER UNIQUE REFERENCES owned_item_instances(id),
 quantity INTEGER NOT NULL CHECK(typeof(quantity)='integer' AND quantity BETWEEN 0 AND 99),
 instance_revision INTEGER NOT NULL CHECK(typeof(instance_revision)='integer' AND instance_revision>=0),
 CHECK((instance_id IS NULL AND quantity=0 AND instance_revision=0) OR (typeof(instance_id)='integer' AND instance_id>0 AND quantity>0 AND instance_revision>0)),
 PRIMARY KEY(character_id,location_kind,location_index), FOREIGN KEY(account_id,character_id) REFERENCES owned_inventory_headers(account_id,character_id) ON DELETE CASCADE
) WITHOUT ROWID;
CREATE TABLE main.owned_item_native_aliases (
 instance_id INTEGER NOT NULL REFERENCES owned_inventory_cells(instance_id) ON DELETE CASCADE,
 client_sha256 TEXT NOT NULL CHECK(typeof(client_sha256)='text' AND length(client_sha256)=64 AND client_sha256 NOT GLOB '*[^0-9a-f]*'),
 profile TEXT NOT NULL CHECK(typeof(profile)='text' AND length(CAST(profile AS BLOB)) BETWEEN 1 AND 64 AND instr(profile,char(0))=0),
 source_sha256 TEXT NOT NULL CHECK(typeof(source_sha256)='text' AND length(source_sha256)=64 AND source_sha256 NOT GLOB '*[^0-9a-f]*'),
 source_record TEXT NOT NULL CHECK(typeof(source_record)='text' AND length(CAST(source_record AS BLOB)) BETWEEN 1 AND 2048 AND instr(source_record,char(0))=0),
 native_key INTEGER NOT NULL CHECK(typeof(native_key)='integer' AND native_key BETWEEN 0 AND 65535),
 native_slot INTEGER NOT NULL CHECK(typeof(native_slot)='integer' AND native_slot BETWEEN 0 AND 255),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 record BLOB NOT NULL CHECK(typeof(record)='blob' AND length(record) BETWEEN 1 AND 4096),
 PRIMARY KEY(instance_id,client_sha256,profile)
) WITHOUT ROWID;
)SQL";
}
}
