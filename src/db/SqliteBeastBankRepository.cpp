#include "db/SqliteBeastBankRepository.h"
#include "db/SqliteSupport.h"
#include "db/SqliteWeaponSlotRepository.h"
#include "protocol/RecoveredTeleportGem.h"
#include <algorithm>
#include <bit>
#include <cstring>
#include <limits>
#include <initializer_list>
#include <memory>
#include <nlohmann/json.hpp>
#include <type_traits>

namespace god2 {
namespace {
using Repo=SqliteBeastBankRepository;
constexpr auto maximum=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
void require(bool value,const char* reason){if(!value)throw DatabaseError(reason);}
std::uint64_t advance(std::uint64_t value){require(value&&value<maximum,"PET bank revision exhausted");return value+1;}
bool hash(const std::string& value){return value.size()==64&&value.find_first_not_of("0123456789abcdef")==std::string::npos;}
std::uint16_t key(const std::array<std::uint8_t,20>& value){return static_cast<std::uint16_t>(value[0]|(std::uint16_t{value[1]}<<8));}
template<class T>const T* at(const std::vector<T>& rows,std::uint16_t slot){const auto found=std::find_if(rows.begin(),rows.end(),[&](const auto& v){return v.slot==slot;});return found==rows.end()?nullptr:&*found;}
const StoredBeastSnapshot* pet(const std::vector<StoredBeastSnapshot>& rows,std::uint16_t slot){const auto found=std::find_if(rows.begin(),rows.end(),[&](const auto& v){return v.inventory_slot==slot;});return found==rows.end()?nullptr:&*found;}
#include "../relations53/preservation.inc"
struct ReadScope {sqlite3* db;bool owns,done=false;explicit ReadScope(sqlite3* value):db(value),owns(sqlite3_get_autocommit(value)!=0){if(owns)sqlite_detail::execute(db,"BEGIN");}~ReadScope(){if(owns&&!done)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}void finish(){if(owns)sqlite_detail::execute(db,"COMMIT");done=true;}};
using Objects=std::vector<std::array<std::string,4>>;
bool feature(const std::string& name){return name=="character_bank_beast_metadata_0085"||name=="character_bank_beast_receipts_0085"||name=="beast_bank_schema_0085";}
Objects objects(sqlite3* db,bool own){sqlite_detail::Statement q(db,"SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master ORDER BY type,name");Objects out;while(q.row())if(feature(q.text(2))==own)out.push_back({q.text(0),q.text(1),q.text(2),q.text(3)});return out;}
Guard existing(sqlite3* db){auto value=guard(db,{});value.erase(":sqlite_master");for(const auto* name:{"character_bank_beast_metadata_0085","character_bank_beast_receipts_0085","beast_bank_schema_0085"}){value.erase(name);value.erase(std::string(name)+":schema");}return value;}
constexpr const char* ledger=R"SQL(
CREATE TABLE beast_bank_schema_0085(
 version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version=4),
 sql_text TEXT NOT NULL,design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0085')
);
)SQL";
struct Cell {bool vault;std::uint16_t slot;};
std::array<Cell,2> cells(const RecoveredBankItems::Request& r){
    require(r.page<3,"PET bank native UI page invalid");
    const auto vault=[&](std::uint8_t slot){require(slot>=2&&slot<50,"PET bank reserved vault cell");return static_cast<std::uint16_t>(r.page*50+slot);};
    using K=RecoveredBankItems::Kind;
    if(r.kind==K::Deposit){require(r.source<30,"PET bank source bag invalid");return {Cell{false,r.source},Cell{true,vault(r.destination)}};}
    if(r.kind==K::Withdraw){require(r.destination<30,"PET bank destination bag invalid");return {Cell{true,vault(r.source)},Cell{false,r.destination}};}
    require(r.kind==K::Move&&r.source!=r.destination,"PET bank move operation invalid");return {Cell{true,vault(r.source)},Cell{true,vault(r.destination)}};
}
auto& scalar(Repo::Snapshot& saved,Cell cell){return cell.vault?saved.base.vault[cell.slot]:saved.base.bag.scalar[cell.slot].value();}
const auto& scalar(const Repo::Snapshot& saved,Cell cell){return cell.vault?saved.base.vault[cell.slot]:saved.base.bag.scalar[cell.slot].value();}
std::optional<StoredVaultBeast> beast(const Repo::Snapshot& saved,Cell cell){
    if(cell.vault){if(const auto* v=at(saved.vault_beasts,cell.slot))return *v;}
    else if(const auto* v=pet(saved.beasts,cell.slot))return StoredVaultBeast{cell.slot,v->revision,v->bag_revision,v->inventory_metadata,v->panel,v->exploration,v->origin,v->evidence_id};
    return {};
}
void no_battle(sqlite3* db,std::uint64_t character){sqlite_detail::Statement q(db,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");q.bind_id(1,character);require(!q.row(),"PET bank pending battle");}
void shape(sqlite3* db){
    const auto exact=[&](const char* table,std::initializer_list<const char*> names){sqlite_detail::Statement q(db,("PRAGMA table_info("+quoted(table)+")").c_str());std::vector<std::string> actual,wanted;while(q.row())actual.push_back(q.text(1));for(const auto* n:names)wanted.emplace_back(n);require(actual==wanted,"PET bank affected table has unsupported columns");};
    exact("diagnostic_inventory_slots",{"character_id","slot","item_id","count","revision","source_sha256","design_id"});
    exact("character_bank_item_slots",{"character_id","slot","item_id","count","revision","source_sha256","item_design_id","design_id"});
    exact("character_armor_slot_metadata",{"character_id","slot","logical20","revision","origin","provenance","source_sha256","client_sha256","design_id"});
    exact("character_weapon_slot_metadata",{"character_id","slot","logical20","revision","origin","provenance","source_sha256","client_sha256","design_id"});
    exact("character_teleport_gem_metadata",{"character_id","slot","metadata20","revision","origin","provenance","source_sha256","design_id"});
    exact("character_bank_armor_metadata",{"character_id","slot","logical20","revision","origin","provenance","source_sha256","client_sha256","instance_design_id","storage_design_id"});
    exact("character_bank_foreign_metadata",{"character_id","slot","kind","logical20","revision","origin","provenance","source_sha256","client_sha256","instance_design_id","source_family","parsed_sha256","storage_design_id"});
}
std::string state(const Repo::Snapshot& saved){
    using J=nlohmann::json;const auto cell=[](const StoredInventorySlot& v){return J::array({v.item_id,v.count,v.revision,v.source_sha256});};
    J out=J::array({"CUSTOM-0085_BANK_FULL",saved.base.bag.account,saved.base.bag.character}),bag=J::array(),vault=J::array(),ba=J::array(),bw=J::array(),bg=J::array(),va=J::array(),vf=J::array(),bp=J::array(),vp=J::array(),selected=nullptr;
    for(const auto& v:saved.base.bag.scalar)bag.push_back(v?cell(*v):J(nullptr));for(const auto& v:saved.base.vault)vault.push_back(cell(v));
    for(const auto& v:saved.base.bag.armor)ba.push_back(J::array({v.slot,v.item_id,v.count,v.revision,v.logical20,v.origin,v.provenance,v.metadata_present}));
    const auto overlay=[](const auto& v){return J::array({v.slot,v.logical20,v.revision,v.origin,v.provenance,v.source_sha256,v.client_sha256,v.design_id});};for(const auto& v:saved.base.bag.weapons)bw.push_back(overlay(v));for(const auto& v:saved.base.bag.gems)bg.push_back(overlay(v));
    for(const auto& v:saved.base.armor)va.push_back(J::array({v.slot,v.logical20,v.revision,v.origin,v.provenance,v.source_sha256,v.client_sha256,v.instance_design_id}));
    for(const auto& v:saved.foreign)vf.push_back(J::array({v.slot,static_cast<std::uint8_t>(v.kind),v.logical20,v.revision,v.origin,v.provenance,v.source_sha256,v.client_sha256,v.instance_design_id,v.source_family,v.parsed_sha256}));
    const auto raw=[](const auto& v){J data=J::array({v.slot,v.revision,v.physical_revision,v.inventory_metadata,v.panel.bytes,nullptr,v.origin,v.evidence_id,std::string(NativeBeastSourceCatalog::source_sha256),std::string(SqliteBeastSnapshotRepository::client_sha256),"CUSTOM-0085"});if(v.exploration)data[5]=v.exploration->bytes;return data;};
    for(const auto& v:saved.beasts)bp.push_back(raw(StoredVaultBeast{v.inventory_slot,v.revision,v.bag_revision,v.inventory_metadata,v.panel,v.exploration,v.origin,v.evidence_id}));for(const auto& v:saved.vault_beasts)vp.push_back(raw(v));
    if(saved.selection)selected=J::array({saved.selection->selector,saved.selection->custody_revision,saved.selection->revision});
    for(auto* value:{&bag,&vault,&ba,&bw,&bg,&va,&vf,&bp,&vp,&selected})out.push_back(std::move(*value));return out.dump();
}
void erase_beast(sqlite3* db,std::uint64_t actor,Cell cell,const StoredVaultBeast& v){
    const auto sql=std::string("DELETE FROM ")+(cell.vault?"character_bank_beast_metadata_0085 WHERE character_id=? AND slot=?":"character_beast_snapshot_custody WHERE character_id=? AND inventory_slot=?")+" AND selector=? AND "+(cell.vault?"physical_revision":"bag_revision")+"=? AND inventory_metadata=? AND panel4c=? AND COALESCE(explorationc5,X'')=? AND revision=? AND origin=? AND evidence_id=? AND source_sha256=? AND client_sha256=? AND design_id='CUSTOM-0085'";
    sqlite_detail::Statement q(db,sql.c_str());q.bind_id(1,actor);q.bind(2,cell.slot);q.bind(3,v.panel.selector());q.bind_id(4,v.physical_revision);q.bind_blob(5,v.inventory_metadata);q.bind_blob(6,v.panel.bytes);if(v.exploration)q.bind_blob(7,v.exploration->bytes);else q.bind_blob(7,std::span<const std::uint8_t>{});q.bind_id(8,v.revision);q.bind(9,v.origin);q.bind(10,v.evidence_id);q.bind(11,std::string(NativeBeastSourceCatalog::source_sha256));q.bind(12,std::string(SqliteBeastSnapshotRepository::client_sha256));q.done();require(sqlite3_changes(db)==1,"PET bank full custody delete CAS failed");
}
void insert_beast(sqlite3* db,std::uint64_t actor,Cell cell,const StoredVaultBeast& v){
    const auto sql=std::string("INSERT INTO ")+(cell.vault?"character_bank_beast_metadata_0085":"character_beast_snapshot_custody")+" VALUES(?,?,?,?,?,?,NULLIF(?,X''),?,?,?,?,?,?)";
    sqlite_detail::Statement q(db,sql.c_str());q.bind_id(1,actor);q.bind(2,cell.slot);q.bind(3,v.panel.selector());q.bind_id(4,v.physical_revision);q.bind_blob(5,v.inventory_metadata);q.bind_blob(6,v.panel.bytes);if(v.exploration)q.bind_blob(7,v.exploration->bytes);else q.bind_blob(7,std::span<const std::uint8_t>{});q.bind_id(8,v.revision);q.bind(9,v.origin);q.bind(10,v.evidence_id);q.bind(11,std::string(NativeBeastSourceCatalog::source_sha256));q.bind(12,std::string(SqliteBeastSnapshotRepository::client_sha256));q.bind(13,std::string(SqliteBeastSnapshotRepository::design_id));q.done();require(sqlite3_changes(db)==1,"PET bank target custody insert failed");
}
}

std::string SqliteBeastBankRepository::schema(){return R"SQL(
CREATE TABLE character_bank_beast_metadata_0085(
 character_id INTEGER NOT NULL REFERENCES recovered_characters(id),
 slot INTEGER NOT NULL CHECK(typeof(slot)='integer' AND slot BETWEEN 0 AND 299 AND slot%50 BETWEEN 2 AND 49),
 selector INTEGER NOT NULL CHECK(typeof(selector)='integer' AND selector BETWEEN 0 AND 255),
 physical_revision INTEGER NOT NULL CHECK(typeof(physical_revision)='integer' AND physical_revision>0),
 inventory_metadata BLOB NOT NULL CHECK(typeof(inventory_metadata)='blob' AND length(inventory_metadata)=20),
 panel4c BLOB NOT NULL CHECK(typeof(panel4c)='blob' AND length(panel4c)=17),
 explorationc5 BLOB CHECK(explorationc5 IS NULL OR(typeof(explorationc5)='blob' AND length(explorationc5)=309)),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 origin TEXT NOT NULL CHECK(origin IN('NATIVE_OBSERVED','NATIVE_VERIFIED','CUSTOM_DESIGNED','CUSTOM_TEST_NOT_NATIVE')),
 evidence_id TEXT NOT NULL CHECK(typeof(evidence_id)='text' AND length(CAST(evidence_id AS BLOB)) BETWEEN 1 AND 512 AND instr(evidence_id,char(0))=0),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'),
 client_sha256 TEXT NOT NULL CHECK(client_sha256='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0085'),
 PRIMARY KEY(character_id,slot),UNIQUE(character_id,selector),
 FOREIGN KEY(character_id,slot) REFERENCES character_bank_item_slots(character_id,slot)
);
CREATE TABLE character_bank_beast_receipts_0085(
 receipt TEXT PRIMARY KEY NOT NULL CHECK(length(receipt)=64 AND receipt NOT GLOB '*[^0-9a-f]*'),
 account_id INTEGER NOT NULL REFERENCES accounts(id),character_id INTEGER NOT NULL REFERENCES recovered_characters(id),
 operation INTEGER NOT NULL CHECK(operation IN(99,100,101)),page INTEGER NOT NULL CHECK(page BETWEEN 0 AND 2),
 source INTEGER NOT NULL CHECK(source BETWEEN 0 AND 49),destination INTEGER NOT NULL CHECK(destination BETWEEN 0 AND 49),
 quantity INTEGER NOT NULL CHECK(quantity BETWEEN 1 AND 127),
 before_state TEXT NOT NULL,after_state TEXT NOT NULL,design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0085')
);
)SQL";}
void SqliteBeastBankRepository::require_schema(sqlite3* db){
    SqliteBeastSnapshotRepository::require_schema(db);sqlite3* expected=nullptr;sqlite_detail::check(db,sqlite3_open(":memory:",&expected));struct Close{sqlite3* db;~Close(){sqlite3_close_v2(db);}} close{expected};sqlite_detail::execute(expected,schema());sqlite_detail::execute(expected,ledger);
    require(objects(db,true)==objects(expected,true),"PET bank schema/index/trigger mismatch");sqlite_detail::Statement q(db,"SELECT version,sql_text,design_id FROM beast_bank_schema_0085");require(q.row()&&q.integer(0)==4&&q.text(1)==schema()&&q.text(2)=="CUSTOM-0085"&&!q.row(),"PET bank feature ledger mismatch");
}
void SqliteBeastBankRepository::install_schema(sqlite3* db){
    require(sqlite3_get_autocommit(db)!=0,"PET bank schema installer requires standalone transaction");SqliteBeastSnapshotRepository::require_schema(db);
    if(!objects(db,true).empty()){require_schema(db);return;}
    const auto rows=existing(db);const auto prior=objects(db,false);sqlite_detail::Transaction tx(db);sqlite_detail::execute(db,schema());sqlite_detail::execute(db,ledger);sqlite_detail::Statement q(db,"INSERT INTO beast_bank_schema_0085 VALUES(4,?,'CUSTOM-0085')");q.bind(1,schema());q.done();require_schema(db);require(existing(db)==rows&&objects(db,false)==prior,"PET bank installer changed existing rows/schema/history");sqlite_detail::Statement fk(db,"PRAGMA foreign_key_check");require(!fk.row(),"PET bank installer FK mismatch");tx.commit();
}
SqliteBeastBankRepository::SqliteBeastBankRepository(sqlite3* db,SqliteOwnedForeignBankRepository& foreign,SqliteBeastSnapshotRepository& beasts,LookupWeapon weapon,EligiblePlain plain):db_(db),foreign_(foreign),beasts_(beasts),weapon_(std::move(weapon)),plain_(std::move(plain)){require(db_&&foreign_.shares_connection(db_)&&beasts_.shares_connection(db_)&&bool(weapon_)&&bool(plain_),"PET bank requires same connection and native catalogs");}
void SqliteBeastBankRepository::validate(const Snapshot& saved) const{
    require(saved.beast_scope,"PET bank feature scope absent");std::array<bool,256> bag_ids{},vault_ids{};
    const auto valid=[&](const auto& v,const StoredInventorySlot& c){const auto view=RecoveredBeastInventoryFields::decode(v.inventory_metadata);const bool origin=v.origin=="NATIVE_OBSERVED"||v.origin=="NATIVE_VERIFIED"||v.origin=="CUSTOM_DESIGNED"||v.origin=="CUSTOM_TEST_NOT_NATIVE";
        require(view&&view->key()==c.item_id&&c.count==1&&c.source_sha256==NativeBeastSourceCatalog::source_sha256&&c.revision==v.physical_revision&&v.revision&&v.revision<=maximum&&v.physical_revision&&v.physical_revision<=maximum&&RecoveredBeastPanel::decode_snapshot(v.panel.bytes)&&v.panel.metadata_key()==c.item_id&&v.panel.kind_display_raw2()<3&&v.panel.meter_denominator_raw11()!=0&&origin&&!v.evidence_id.empty()&&v.evidence_id.size()<=512&&v.evidence_id.find('\0')==std::string::npos,"PET bank full instance/physical/source conflict");
        if(v.exploration)require(RecoveredBeastExploration::decode_snapshot(v.exploration->bytes)&&v.exploration->metadata_key()==c.item_id&&v.exploration->selector()==v.panel.selector(),"PET bank exploration snapshot conflict");};
    std::uint16_t previous=0;bool first=true;
    for(const auto& v:saved.beasts){require((v.inventory_slot<30||v.inventory_slot==37)&&(first||v.inventory_slot>previous)&&v.account==saved.base.bag.account&&v.character==saved.base.bag.character&&saved.base.bag.scalar[v.inventory_slot],"PET bank bag custody ordering/owner");first=false;previous=v.inventory_slot;const StoredVaultBeast raw{v.inventory_slot,v.revision,v.bag_revision,v.inventory_metadata,v.panel,v.exploration,v.origin,v.evidence_id};valid(raw,*saved.base.bag.scalar[v.inventory_slot]);require(!bag_ids[v.panel.selector()]&&!at(saved.base.bag.armor,v.inventory_slot)&&!at(saved.base.bag.weapons,v.inventory_slot)&&!at(saved.base.bag.gems,v.inventory_slot),"PET bank bag selector/overlay conflict");bag_ids[v.panel.selector()]=true;}
    first=true;previous=0;for(const auto& v:saved.vault_beasts){require(v.slot<300&&v.slot%50>=2&&(first||v.slot>previous),"PET bank vault domain/order");first=false;previous=v.slot;valid(v,saved.base.vault[v.slot]);require(!vault_ids[v.panel.selector()]&&!at(saved.base.armor,v.slot)&&!at(saved.foreign,v.slot),"PET bank vault selector/overlay conflict");vault_ids[v.panel.selector()]=true;}
    if(saved.selection)require(bag_ids[saved.selection->selector]&&saved.selection->revision&&saved.selection->revision<=maximum&&saved.selection->custody_revision&&saved.selection->custody_revision<=maximum,"PET bank raw selected binding invalid");
    for(std::uint16_t slot=0;slot<300;++slot)if(saved.base.vault[slot].count&&NativeBeastSourceCatalog::lookup(saved.base.vault[slot].item_id))require(at(saved.vault_beasts,slot),"PET bank vault scalar missing complete custody");
    for(std::uint8_t slot=0;slot<50;++slot)if(saved.base.bag.scalar[slot]&&saved.base.bag.scalar[slot]->count&&NativeBeastSourceCatalog::lookup(saved.base.bag.scalar[slot]->item_id))require((slot<30||slot==37)&&pet(saved.beasts,slot),"PET bank bag scalar missing complete custody");
}
SqliteBeastBankRepository::Snapshot SqliteBeastBankRepository::load(std::uint64_t account,std::uint64_t character){
    ReadScope scope(db_);require_schema(db_);shape(db_);Snapshot saved(foreign_.load(account,character));saved.beast_scope=true;saved.beasts=beasts_.load_owned(account,character);saved.selection=beasts_.load_selection_record(account,character);
    sqlite_detail::Statement q(db_,"SELECT slot,physical_revision,inventory_metadata,panel4c,explorationc5,revision,origin,evidence_id,source_sha256,client_sha256,selector,design_id,explorationc5 IS NULL FROM character_bank_beast_metadata_0085 WHERE character_id=? ORDER BY slot");q.bind_id(1,character);
    while(q.row()){StoredVaultBeast v;v.slot=q.number<std::uint16_t>(0);v.physical_revision=q.number<std::uint64_t>(1);const auto metadata=q.blob(2,20,20),panel=q.blob(3,17,17);require(metadata.size()==20,"PET vault metadata length");std::copy(metadata.begin(),metadata.end(),v.inventory_metadata.begin());const auto decoded=RecoveredBeastPanel::decode_snapshot(panel);require(decoded.has_value(),"PET vault panel format");v.panel=*decoded;if(!q.integer(12)){v.exploration=RecoveredBeastExploration::decode_snapshot(q.blob(4,309,309));require(v.exploration.has_value(),"PET vault exploration format");}v.revision=q.number<std::uint64_t>(5);v.origin=q.text(6);v.evidence_id=q.text(7);require(q.text(8)==NativeBeastSourceCatalog::source_sha256&&q.text(9)==SqliteBeastSnapshotRepository::client_sha256&&q.number<std::uint8_t>(10)==v.panel.selector()&&q.text(11)=="CUSTOM-0085","PET vault field pins/selector");saved.vault_beasts.push_back(std::move(v));}
    validate(saved);scope.finish();return saved;
}
void SqliteBeastBankRepository::verify_snapshot_in_transaction(const Snapshot& saved){require(sqlite3_get_autocommit(db_)==0,"PET bank proof must share transaction");require(load(saved.base.bag.account,saved.base.bag.character)==saved,"PET bank complete snapshot proof conflict");}
bool SqliteBeastBankRepository::receipt_exists(const std::string& receipt,bool own_only){require(hash(receipt),"PET bank malformed receipt");sqlite_detail::Statement q(db_,"SELECT 1 FROM character_bank_beast_receipts_0085 WHERE receipt=?");q.bind(1,receipt);if(q.row())return true;if(own_only)return false;sqlite_detail::Statement other(db_,"SELECT 1 FROM character_bank_mixed_receipts WHERE receipt=?");other.bind(1,receipt);return other.row()||foreign_.receipt_exists(receipt);}

SqliteBeastBankRepository::Plan SqliteBeastBankRepository::plan(const Request& request) const{
    validate(request.expected);const auto pair=cells(request.wire);const auto& before=request.expected;const auto& a=scalar(before,pair[0]);const auto& b=scalar(before,pair[1]);
    require(a.count&&request.wire.quantity==(request.wire.kind==RecoveredBankItems::Kind::Move?1:a.count),"PET bank requires whole source count/native65 marker");
    require(beast(before,pair[0])||beast(before,pair[1]),"PET bank route requires actual PET custody");
    if(request.wire.kind!=RecoveredBankItems::Kind::Move)require(!b.count,"PET bank deposit/withdraw destination must be empty");
    struct Item {StoredInventorySlot scalar;std::optional<StoredVaultArmor> armor;std::optional<StoredVaultForeign> foreign;std::optional<StoredVaultBeast> beast;};
    const auto capture=[&](Cell cell){Item item{scalar(before,cell),{},{},{}};item.beast=beast(before,cell);
        if(cell.vault){if(const auto* v=at(before.base.armor,cell.slot))item.armor=*v;if(const auto* v=at(before.foreign,cell.slot))item.foreign=*v;}
        else {
            if(const auto* v=at(before.base.bag.armor,cell.slot))item.armor=StoredVaultArmor{cell.slot,v->logical20,v->revision,v->origin,v->provenance,SqliteArmorSlotRepository::source_sha256,SqliteArmorSlotRepository::client_sha256,SqliteArmorSlotRepository::design_id};
            const auto* v=at(before.base.bag.weapons,cell.slot);const bool weapon=v!=nullptr;if(!v)v=at(before.base.bag.gems,cell.slot);
            if(v&&item.scalar.count){StoredVaultForeign raw{cell.slot,weapon?OwnedBankForeignKind::Weapon:OwnedBankForeignKind::Gem,v->logical20,v->revision,v->origin,v->provenance,v->source_sha256,v->client_sha256,v->design_id,{},{}};if(weapon){const auto definition=weapon_(item.scalar.item_id);require(definition.has_value(),"PET bank neighbour weapon definition");raw.source_family=definition->family;raw.parsed_sha256=definition->parsed_sha256;}item.foreign=std::move(raw);}
        }
        require(unsigned(bool(item.armor))+unsigned(bool(item.foreign))+unsigned(bool(item.beast))<=1,"PET bank neighbour domain collision");
        if(item.scalar.count){if(item.armor||item.foreign||item.beast)require(item.scalar.count==1,"PET bank neighbour must be whole instance");else require(plain_(item.scalar.item_id)&&item.scalar.source_sha256==NativeBeastSourceCatalog::source_sha256,"PET bank unknown neighbour cannot lose metadata");}
        if(item.beast){const auto fields=RecoveredBeastInventoryFields::decode(item.beast->inventory_metadata);require(fields&&!fields->native_exploring_label()&&!item.beast->panel.control7_alternate()&&!item.beast->panel.control8_alternate(),"PET bank inactive presentation policy rejected");}
        return item;
    };
    const auto source=capture(pair[0]),destination=capture(pair[1]);
    Plan result{before,pair[0].vault,pair[1].vault,pair[0].slot,pair[1].slot};auto& next=result.after;
    for(const auto cell:pair){
        if(cell.vault){std::erase_if(next.base.armor,[&](const auto& v){return v.slot==cell.slot;});std::erase_if(next.foreign,[&](const auto& v){return v.slot==cell.slot;});std::erase_if(next.vault_beasts,[&](const auto& v){return v.slot==cell.slot;});}
        else {if(const auto outgoing=beast(before,cell);outgoing&&next.selection&&next.selection->selector==outgoing->panel.selector())next.selection.reset();std::erase_if(next.base.bag.armor,[&](const auto& v){return v.slot==cell.slot;});std::erase_if(next.base.bag.weapons,[&](const auto& v){return v.slot==cell.slot;});std::erase_if(next.base.bag.gems,[&](const auto& v){return v.slot==cell.slot;});std::erase_if(next.beasts,[&](const auto& v){return v.inventory_slot==cell.slot;});}
    }
    const auto assign=[&](Cell cell,Item item){const auto revision=advance(scalar(before,cell).revision);scalar(next,cell)=item.scalar;scalar(next,cell).revision=revision;
        if(!item.scalar.count)return;
        if(item.armor){auto v=*item.armor;v.slot=cell.slot;v.revision=revision;if(cell.vault)next.base.armor.push_back(std::move(v));else next.base.bag.armor.push_back({static_cast<std::uint8_t>(cell.slot),key(v.logical20),1,revision,v.logical20,v.origin,v.provenance,true});}
        if(item.foreign){auto v=*item.foreign;v.slot=cell.slot;v.revision=revision;if(cell.vault)next.foreign.push_back(std::move(v));else {ArmorForeignOverlay raw{static_cast<std::uint8_t>(cell.slot),v.logical20,revision,v.origin,v.provenance,v.source_sha256,v.client_sha256,v.instance_design_id};if(v.kind==OwnedBankForeignKind::Weapon)next.base.bag.weapons.push_back(std::move(raw));else next.base.bag.gems.push_back(std::move(raw));}}
        if(item.beast){auto v=*item.beast;v.slot=cell.slot;v.physical_revision=revision;v.revision=advance(v.revision);std::array<bool,256> used{};if(cell.vault){for(const auto& own:next.vault_beasts)used[own.panel.selector()]=true;}else {for(const auto& own:next.beasts)used[own.panel.selector()]=true;}
            auto selector=v.panel.selector();if(used[selector]){unsigned free=0;while(free<used.size()&&used[free])++free;require(free<used.size(),"PET bank selector namespace full");selector=static_cast<std::uint8_t>(free);}
            // CUSTOM separate bag/vault identities, not native transfer stat math.
            v.panel.bytes[3]=selector;if(v.exploration)v.exploration->bytes[3]=selector;
            if(cell.vault)next.vault_beasts.push_back(std::move(v));else next.beasts.push_back({next.base.bag.account,next.base.bag.character,v.revision,revision,static_cast<std::uint8_t>(cell.slot),v.inventory_metadata,v.panel,v.exploration,v.origin,v.evidence_id});
        }
    };
    assign(pair[0],destination);assign(pair[1],source);
    const auto ordered=[](auto& values){std::sort(values.begin(),values.end(),[](const auto& l,const auto& r){return l.slot<r.slot;});};ordered(next.base.armor);ordered(next.foreign);ordered(next.base.bag.armor);ordered(next.base.bag.weapons);ordered(next.base.bag.gems);ordered(next.vault_beasts);std::sort(next.beasts.begin(),next.beasts.end(),[](const auto& l,const auto& r){return l.inventory_slot<r.inventory_slot;});validate(next);
    require(std::uint16_t{scalar(next,pair[0]).count}+scalar(next,pair[1]).count==std::uint16_t{a.count}+b.count,"PET bank count conservation failed");return result;
}
SqliteBeastBankRepository::Plan SqliteBeastBankRepository::commit(const std::string& receipt,const Request& request,const Prepare& prepare,const Check& check){
    static_assert(std::is_nothrow_move_constructible_v<Plan>);require(hash(receipt)&&bool(prepare)&&sqlite3_get_autocommit(db_)!=0,"PET bank writer requires fresh receipt and prepared reply");
    auto next=plan(request);const auto pair=cells(request.wire);const auto before_state=state(request.expected),after_state=state(next.after);prepare(next);
    sqlite_detail::Transaction tx(db_);verify_snapshot_in_transaction(request.expected);require(!receipt_exists(receipt),"PET bank duplicate/cross-ledger receipt");const auto actor=request.expected.base.bag.character;no_battle(db_,actor);sqlite_detail::Statement fk(db_,"PRAGMA foreign_keys");require(fk.row()&&fk.integer(0)==1,"PET bank requires foreign keys");
    Exclusions permitted;const auto allow=[&](const char* table,const std::string& predicate){auto& sql=permitted[table];sql=sql.empty()?"NOT("+predicate+")":sql+" AND NOT("+predicate+")";};const auto owner="character_id="+std::to_string(actor);
    for(const auto cell:pair){const auto where=owner+" AND slot="+std::to_string(cell.slot);for(const auto* table:cell.vault?std::initializer_list<const char*>{"character_bank_item_slots","character_bank_armor_metadata","character_bank_foreign_metadata","character_bank_beast_metadata_0085"}:std::initializer_list<const char*>{"diagnostic_inventory_slots","character_armor_slot_metadata","character_weapon_slot_metadata","character_teleport_gem_metadata"})allow(table,where);if(!cell.vault)allow("character_beast_snapshot_custody",owner+" AND inventory_slot="+std::to_string(cell.slot));}
    if(request.expected.selection!=next.after.selection)allow("character_beast_selection_0085",owner);
    permitted["character_bank_beast_receipts_0085"]="receipt<>'"+receipt+"'";const auto preserved=guard(db_,permitted);
    if(request.expected.selection!=next.after.selection){require(request.expected.selection&&!next.after.selection,"PET bank cannot create another selection");const auto& v=*request.expected.selection;sqlite_detail::Statement q(db_,"DELETE FROM character_beast_selection_0085 WHERE character_id=? AND selector=? AND custody_revision=? AND revision=? AND origin='CUSTOM_DESIGNED' AND design_id='CUSTOM-0085'");q.bind_id(1,actor);q.bind(2,v.selector);q.bind_id(3,v.custody_revision);q.bind_id(4,v.revision);q.done();require(sqlite3_changes(db_)==1,"PET bank selection retire CAS failed");}
    // Remove both occupied metadata parents before exchanging scalar identities.
    // Exact before snapshot plus preserved typed rows guards these owned cells.
    for(const auto cell:pair){
        if(const auto v=beast(request.expected,cell))erase_beast(db_,actor,cell,*v);
        for(const auto* table:cell.vault?std::initializer_list<const char*>{"character_bank_armor_metadata","character_bank_foreign_metadata"}:std::initializer_list<const char*>{"character_armor_slot_metadata","character_weapon_slot_metadata","character_teleport_gem_metadata"}){sqlite_detail::Statement q(db_,("DELETE FROM "+std::string(table)+" WHERE character_id=? AND slot=?").c_str());q.bind_id(1,actor);q.bind(2,cell.slot);q.done();}
    }
    for(const auto cell:pair){const auto& old=scalar(request.expected,cell);const auto& value=scalar(next.after,cell);const auto sql=std::string("UPDATE ")+(cell.vault?"character_bank_item_slots":"diagnostic_inventory_slots")+" SET item_id=?,count=?,revision=?,source_sha256=? WHERE character_id=? AND slot=? AND item_id=? AND count=? AND revision=? AND source_sha256=? AND "+(cell.vault?"item_design_id='CUSTOM-0015' AND design_id='CUSTOM-0065'":"design_id='CUSTOM-0015'");sqlite_detail::Statement q(db_,sql.c_str());q.bind(1,value.item_id);q.bind(2,value.count);q.bind_id(3,value.revision);q.bind(4,value.source_sha256);q.bind_id(5,actor);q.bind(6,cell.slot);q.bind(7,old.item_id);q.bind(8,old.count);q.bind_id(9,old.revision);q.bind(10,old.source_sha256);q.done();require(sqlite3_changes(db_)==1,"PET bank physical scalar CAS failed");}
    for(const auto cell:pair){
        if(const auto v=beast(next.after,cell))insert_beast(db_,actor,cell,*v);
        if(cell.vault){
            if(const auto* v=at(next.after.base.armor,cell.slot)){sqlite_detail::Statement q(db_,"INSERT INTO character_bank_armor_metadata VALUES(?,?,?,?,?,?,?,?,?,'CUSTOM-0067')");q.bind_id(1,actor);q.bind(2,cell.slot);q.bind_blob(3,v->logical20);q.bind_id(4,v->revision);q.bind(5,v->origin);q.bind(6,v->provenance);q.bind(7,v->source_sha256);q.bind(8,v->client_sha256);q.bind(9,v->instance_design_id);q.done();require(sqlite3_changes(db_)==1,"PET bank armour neighbour insert");}
            if(const auto* v=at(next.after.foreign,cell.slot)){sqlite_detail::Statement q(db_,"INSERT INTO character_bank_foreign_metadata VALUES(?,?,?,?,?,?,?,?,?,?,?,?,'CUSTOM-0068')");q.bind_id(1,actor);q.bind(2,cell.slot);q.bind(3,static_cast<std::uint8_t>(v->kind));q.bind_blob(4,v->logical20);q.bind_id(5,v->revision);q.bind(6,v->origin);q.bind(7,v->provenance);q.bind(8,v->source_sha256);q.bind(9,v->client_sha256);q.bind(10,v->instance_design_id);q.bind(11,v->source_family);q.bind(12,v->parsed_sha256);q.done();require(sqlite3_changes(db_)==1,"PET bank foreign neighbour insert");}
        }else {
            if(const auto* v=at(next.after.base.bag.armor,cell.slot)){sqlite_detail::Statement q(db_,"INSERT INTO character_armor_slot_metadata VALUES(?,?,?,?,?,?,?,?, 'CUSTOM-0066')");q.bind_id(1,actor);q.bind(2,cell.slot);q.bind_blob(3,v->logical20);q.bind_id(4,v->revision);q.bind(5,v->origin);q.bind(6,v->provenance);q.bind(7,SqliteArmorSlotRepository::source_sha256);q.bind(8,SqliteArmorSlotRepository::client_sha256);q.done();require(sqlite3_changes(db_)==1,"PET bank bag armour insert");}
            for(const bool weapon:{true,false}){const auto* v=weapon?at(next.after.base.bag.weapons,cell.slot):at(next.after.base.bag.gems,cell.slot);if(!v)continue;sqlite_detail::Statement q(db_,weapon?"INSERT INTO character_weapon_slot_metadata VALUES(?,?,?,?,?,?,?,?, 'CUSTOM-0046')":"INSERT INTO character_teleport_gem_metadata VALUES(?,?,?,?,?,?,?,'CUSTOM-0057')");q.bind_id(1,actor);q.bind(2,cell.slot);q.bind_blob(3,v->logical20);q.bind_id(4,v->revision);q.bind(5,v->origin);q.bind(6,v->provenance);q.bind(7,v->source_sha256);if(weapon)q.bind(8,v->client_sha256);q.done();require(sqlite3_changes(db_)==1,"PET bank bag foreign insert");}
        }
    }
    sqlite_detail::Statement q(db_,"INSERT INTO character_bank_beast_receipts_0085 VALUES(?,?,?,?,?,?,?,?,?,?,'CUSTOM-0085')");q.bind(1,receipt);q.bind_id(2,request.expected.base.bag.account);q.bind_id(3,actor);q.bind(4,static_cast<std::uint8_t>(request.wire.kind));q.bind(5,request.wire.page);q.bind(6,request.wire.source);q.bind(7,request.wire.destination);q.bind(8,scalar(request.expected,pair[0]).count);q.bind(9,before_state);q.bind(10,after_state);q.done();require(sqlite3_changes(db_)==1,"PET bank receipt insert failed");
    const auto verify=[&]{verify_snapshot_in_transaction(next.after);no_battle(db_,actor);sqlite_detail::Statement q(db_,"SELECT account_id,character_id,operation,page,source,destination,quantity,before_state,after_state,design_id FROM character_bank_beast_receipts_0085 WHERE receipt=?");q.bind(1,receipt);require(q.row()&&q.number<std::uint64_t>(0)==request.expected.base.bag.account&&q.number<std::uint64_t>(1)==actor&&q.number<std::uint8_t>(2)==static_cast<std::uint8_t>(request.wire.kind)&&q.number<std::uint8_t>(3)==request.wire.page&&q.number<std::uint8_t>(4)==request.wire.source&&q.number<std::uint8_t>(5)==request.wire.destination&&q.number<std::uint8_t>(6)==scalar(request.expected,pair[0]).count&&q.text(7)==before_state&&q.text(8)==after_state&&q.text(9)=="CUSTOM-0085"&&!q.row(),"PET bank full receipt readback conflict");sqlite_detail::Statement old(db_,"SELECT 1 FROM character_bank_mixed_receipts WHERE receipt=?");old.bind(1,receipt);require(!old.row()&&!foreign_.receipt_exists(receipt),"PET bank late old-ledger collision");require(guard(db_,permitted,&preserved)==preserved,"PET bank changed unrelated saves/schema/history/money/equipment");sqlite_detail::Statement fk(db_,"PRAGMA foreign_key_check");require(!fk.row(),"PET bank FK mismatch");};verify();if(check){check(next);verify();}tx.commit();return next;
}
}
