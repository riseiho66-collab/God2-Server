#include "db/SqliteOwnedInstanceDiscardRepository.h"
#include "db/SqliteSupport.h"
#include "db/SqliteWeaponSlotRepository.h"
#include "protocol/RecoveredArmorInstance.h"
#include "protocol/RecoveredTeleportGem.h"
#include <algorithm>
#include <limits>
#include <memory>
#include <nlohmann/json.hpp>
#include <type_traits>
#include <utility>

namespace god2 {
namespace {
constexpr auto max_revision=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
void require(bool ok,const char* why){if(!ok)throw DatabaseError(why);}
bool hash(const std::string& value){return value.size()==64&&value.find_first_not_of("0123456789abcdef")==std::string::npos;}
bool evidence(const std::string& value){return !value.empty()&&value.size()<=512&&value.find('\0')==std::string::npos;}
bool origin(const std::string& value){return value=="NATIVE_CAPTURE_VERIFIED"||value=="CUSTOM_TEST_NOT_NATIVE";}
std::uint16_t key(const std::array<std::uint8_t,20>& bytes){return static_cast<std::uint16_t>(bytes[0]|(std::uint16_t{bytes[1]}<<8));}
template<class T>const T* row(const std::vector<T>& values,std::uint8_t slot){const auto found=std::find_if(values.begin(),values.end(),[&](const auto& value){return value.slot==slot;});return found==values.end()?nullptr:&*found;}
struct ReadScope {
    sqlite3* db;bool owns,done=false;
    explicit ReadScope(sqlite3* value):db(value),owns(sqlite3_get_autocommit(value)!=0){if(owns)sqlite_detail::execute(db,"BEGIN");}
    ~ReadScope(){if(owns&&!done)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){if(owns)sqlite_detail::execute(db,"COMMIT");done=true;}
};
using Repo=SqliteOwnedInstanceDiscardRepository;using J=nlohmann::json;
// Retain SQLite types and exact TEXT/BLOB bytes, including embedded NULs.
// No absent table/row becomes provisioned capacity. Older new-design receipts
// are separately checked; the newly inserted audit is the only allowed addition.
std::string typed_rows(sqlite3* db,const std::string& sql,const std::optional<std::uint64_t> owner={}){
    sqlite3_stmt* raw=nullptr;sqlite_detail::check(db,sqlite3_prepare_v2(db,sql.c_str(),-1,&raw,nullptr));std::unique_ptr<sqlite3_stmt,decltype(&sqlite3_finalize)> owned(raw,sqlite3_finalize);
    if(owner)sqlite_detail::check(db,sqlite3_bind_int64(raw,1,static_cast<sqlite3_int64>(*owner)));
    J rows=J::array();int rc=SQLITE_OK;while((rc=sqlite3_step(raw))==SQLITE_ROW){J values=J::array();for(int i=0;i<sqlite3_column_count(raw);++i){const auto type=sqlite3_column_type(raw,i);J value;
        if(type==SQLITE_INTEGER)value=sqlite3_column_int64(raw,i);else if(type==SQLITE_FLOAT)value=sqlite3_column_double(raw,i);else if(type==SQLITE_NULL)value=nullptr;
        else{const auto length=sqlite3_column_bytes(raw,i);const auto* bytes=static_cast<const std::uint8_t*>(type==SQLITE_BLOB?sqlite3_column_blob(raw,i):static_cast<const void*>(sqlite3_column_text(raw,i)));std::vector<std::uint8_t> data;if(length)data.assign(bytes,bytes+length);value=std::move(data);}values.push_back(J::array({type,value}));}rows.push_back(std::move(values));}
    require(rc==SQLITE_DONE,"Owned discard immutable typed observation failed");return rows.dump();
}
std::string peripheral(sqlite3* db,std::uint64_t character){
    sqlite_detail::Statement names(db,"SELECT name FROM sqlite_schema WHERE type='table' AND (name GLOB 'character_*' OR name GLOB 'diagnostic_*' OR name GLOB 'recovered_*' OR name GLOB 'battle_*' OR name='characters' OR name='accounts') AND name<>'character_owned_instance_discard_receipts' ORDER BY name");J result=J::array();
    while(names.row()){const auto name=names.text(0);require(name.find('"')==std::string::npos,"Owned discard peripheral table name invalid");const bool bag=name=="diagnostic_inventory_slots"||name=="character_armor_slot_metadata"||name=="character_weapon_slot_metadata"||name=="character_teleport_gem_metadata";
        result.push_back(J::array({name,typed_rows(db,"SELECT * FROM \""+name+"\""+(bag?" WHERE character_id<>?":"")+" ORDER BY rowid",bag?std::optional(character):std::nullopt)}));
    }return result.dump();
}
std::string history(sqlite3* db,const std::string& receipt){
    // Exclude only the new receipt key, not the whole owner or ledger.
    require(hash(receipt),"Owned discard malformed history exclusion");return typed_rows(db,"SELECT * FROM character_owned_instance_discard_receipts WHERE receipt<>'"+receipt+"' ORDER BY rowid");
}
std::string state(const Repo::Snapshot& saved){
    const auto& bag=saved.bag;J scalar=J::array(),armor=J::array(),weapons=J::array(),gems=J::array();
    for(const auto& value:bag.scalar)scalar.push_back(value?J::array({value->item_id,value->count,value->revision,value->source_sha256}):J(nullptr));
    for(const auto& value:bag.armor)armor.push_back(J::array({value.slot,value.item_id,value.count,value.revision,value.logical20,value.origin,value.provenance,value.metadata_present,SqliteArmorSlotRepository::source_sha256,SqliteArmorSlotRepository::client_sha256,SqliteArmorSlotRepository::design_id}));
    const auto foreign=[](const auto& value){return J::array({value.slot,value.logical20,value.revision,value.origin,value.provenance,value.source_sha256,value.client_sha256,value.design_id});};
    for(const auto& value:bag.weapons)weapons.push_back(foreign(value));for(const auto& value:bag.gems)gems.push_back(foreign(value));
    return J::array({bag.account,bag.character,scalar,armor,weapons,gems,saved.peripheral}).dump();
}
void erase_armor(sqlite3* db,std::uint64_t character,const StoredArmorSlot& value){
    sqlite_detail::Statement erase(db,"DELETE FROM character_armor_slot_metadata WHERE character_id=? AND slot=? AND logical20=? AND revision=? AND origin=? AND provenance=? AND source_sha256=? AND client_sha256=? AND design_id='CUSTOM-0066'");erase.bind_id(1,character);erase.bind(2,value.slot);erase.bind_blob(3,value.logical20);erase.bind_id(4,value.revision);erase.bind(5,value.origin);erase.bind(6,value.provenance);erase.bind(7,SqliteArmorSlotRepository::source_sha256);erase.bind(8,SqliteArmorSlotRepository::client_sha256);erase.done();require(sqlite3_changes(db)==1,"Owned discard armor delete CAS failed");
}
void erase_foreign(sqlite3* db,std::uint64_t character,const ArmorForeignOverlay& value,bool weapon){
    sqlite_detail::Statement erase(db,weapon?"DELETE FROM character_weapon_slot_metadata WHERE character_id=? AND slot=? AND logical20=? AND revision=? AND origin=? AND provenance=? AND source_sha256=? AND client_sha256=? AND design_id='CUSTOM-0046'":"DELETE FROM character_teleport_gem_metadata WHERE character_id=? AND slot=? AND metadata20=? AND revision=? AND origin=? AND provenance=? AND source_sha256=? AND design_id='CUSTOM-0057'");erase.bind_id(1,character);erase.bind(2,value.slot);erase.bind_blob(3,value.logical20);erase.bind_id(4,value.revision);erase.bind(5,value.origin);erase.bind(6,value.provenance);erase.bind(7,value.source_sha256);if(weapon)erase.bind(8,value.client_sha256);erase.done();require(sqlite3_changes(db)==1,"Owned discard foreign delete CAS failed");
}
}
std::string SqliteOwnedInstanceDiscardRepository::schema(){return R"SQL(
CREATE TABLE character_owned_instance_discard_receipts(
 receipt TEXT PRIMARY KEY CHECK(length(receipt)=64 AND receipt NOT GLOB '*[^0-9a-f]*'),
 account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
 character_id INTEGER NOT NULL REFERENCES recovered_characters(id) ON DELETE CASCADE,
 operation INTEGER NOT NULL CHECK(operation=39),
 item_id INTEGER NOT NULL CHECK(typeof(item_id)='integer' AND item_id BETWEEN 1 AND 65535),
 source INTEGER NOT NULL CHECK(typeof(source)='integer' AND source BETWEEN 0 AND 29),
 quantity INTEGER NOT NULL CHECK(typeof(quantity)='integer' AND quantity=1),
 kind INTEGER NOT NULL CHECK(typeof(kind)='integer' AND kind BETWEEN 1 AND 3),
 logical20 BLOB NOT NULL CHECK(typeof(logical20)='blob' AND length(logical20)=20),
 origin TEXT NOT NULL CHECK(origin IN ('NATIVE_CAPTURE_VERIFIED','CUSTOM_TEST_NOT_NATIVE')),
 provenance TEXT NOT NULL CHECK(typeof(provenance)='text' AND length(CAST(provenance AS BLOB)) BETWEEN 1 AND 512 AND instr(provenance,char(0))=0),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'),
 client_sha256 TEXT NOT NULL,
 instance_design_id TEXT NOT NULL,
 before_state TEXT NOT NULL CHECK(typeof(before_state)='text' AND length(before_state)>0),
 after_state TEXT NOT NULL CHECK(typeof(after_state)='text' AND length(after_state)>0),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0071'),
 CHECK((kind=1 AND client_sha256='c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575' AND instance_design_id='CUSTOM-0066') OR
       (kind=2 AND client_sha256='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98' AND instance_design_id='CUSTOM-0046') OR
       (kind=3 AND client_sha256='' AND instance_design_id='CUSTOM-0057'))
);
)SQL";}
SqliteOwnedInstanceDiscardRepository::SqliteOwnedInstanceDiscardRepository(sqlite3* db,SqliteArmorSlotRepository& reader,QualifyArmor armor,QualifyInstance instance,LookupWeapon weapon):db_(db),armor_reader_(reader),armor_(std::move(armor)),armor_instance_(std::move(instance)),weapon_(std::move(weapon)){
    require(db_&&bool(armor_)&&bool(armor_instance_)&&bool(weapon_),"Owned discard requires complete native qualifiers");
}
void SqliteOwnedInstanceDiscardRepository::validate(const ArmorSnapshot& bag) const{
    require(bag.account&&bag.account<=max_revision&&bag.character&&bag.character<=max_revision,"Owned discard owner invalid");
    for(std::size_t slot=0;slot<50;++slot){const auto& value=bag.scalar[slot];if(value)require(value->revision&&value->revision<=max_revision&&value->count<=127&&((value->item_id==0)==(value->count==0))&&hash(value->source_sha256),"Owned discard scalar invalid");}
    std::uint8_t previous=0;bool first=true;
    for(const auto& value:bag.armor){
        require(value.slot<34&&(first||value.slot>previous),"Owned discard armor domain/order conflict");first=false;previous=value.slot;const auto& scalar=bag.scalar[value.slot];const auto part=armor_(value.item_id);
        require(scalar&&scalar->item_id==value.item_id&&scalar->count==1&&scalar->revision==value.revision&&scalar->source_sha256==SqliteArmorSlotRepository::source_sha256&&value.count==1&&value.metadata_present&&key(value.logical20)==value.item_id&&part&&*part>=30&&*part<=33&&(value.slot<30||value.slot==*part)&&!weapon_(value.item_id)&&value.item_id!=RecoveredTeleportGem::item_id&&RecoveredArmorInstance::armor_family(value.logical20)&&armor_instance_(value.item_id,value.logical20)&&origin(value.origin)&&evidence(value.provenance)&&!row(bag.weapons,value.slot)&&!row(bag.gems,value.slot),"Owned discard armor family/source/instance conflict");
    }
    const auto foreign=[&](const auto& values,bool weapon){
        std::uint8_t last=0;bool initial=true;
        for(const auto& value:values){
            require((weapon?(value.slot<30||value.slot==34):value.slot<30)&&(initial||value.slot>last),"Owned discard foreign domain/order conflict");initial=false;last=value.slot;
            const auto& scalar=bag.scalar[value.slot];require(scalar&&scalar->revision==value.revision&&scalar->item_id==key(value.logical20)&&scalar->source_sha256==value.source_sha256&&value.source_sha256==SqliteArmorSlotRepository::source_sha256&&evidence(value.provenance)&&!row(bag.armor,value.slot)&&!(weapon?row(bag.gems,value.slot):row(bag.weapons,value.slot)),"Owned discard foreign owner/scalar/overlay conflict");
            if(weapon)require(value.client_sha256==SqliteWeaponSlotRepository::client_sha256&&value.design_id=="CUSTOM-0046","Owned discard weapon pins conflict");
            else require(value.client_sha256.empty()&&value.design_id=="CUSTOM-0057","Owned discard gem pins conflict");
            if(!scalar->count){require(weapon&&value.origin=="EMPTY_SLOT_POLICY","Owned discard invalid empty overlay");continue;}
            require(scalar->count==1&&origin(value.origin)&&!armor_(scalar->item_id),"Owned discard foreign not whole/category conflict");
            const auto definition=weapon_(scalar->item_id);
            if(weapon)require(scalar->item_id!=RecoveredTeleportGem::item_id&&definition&&definition->item_id==scalar->item_id&&(definition->family=="WPN"||definition->family=="TWP")&&definition->parsed_record.size()==396&&(definition->parsed_record[0x11a]&4)!=0&&hash(definition->parsed_sha256)&&(value.logical20[2]&0x3fu)==(definition->family=="WPN"?1u:25u),"Owned discard weapon source definition/type conflict");
            else require(!definition&&scalar->item_id==RecoveredTeleportGem::item_id&&RecoveredTeleportGem::displayed_charges(value.logical20).has_value(),"Owned discard gem key/type/charges conflict");
        }
    };foreign(bag.weapons,true);foreign(bag.gems,false);
    for(std::uint8_t slot=0;slot<50;++slot){const auto& scalar=bag.scalar[slot];if(!scalar||!scalar->count)continue;
        const auto part=armor_(scalar->item_id);const bool weapon=weapon_(scalar->item_id).has_value(),gem=scalar->item_id==RecoveredTeleportGem::item_id;
        require(unsigned(part.has_value())+unsigned(weapon)+unsigned(gem)<=1,"Owned discard catalog category conflict");
        if(part&&slot<34)require(row(bag.armor,slot),"Owned discard armor missing complete metadata");
        if(weapon&&(slot<30||slot==34))require(row(bag.weapons,slot),"Owned discard weapon missing complete metadata");
        if(gem&&slot<30)require(row(bag.gems,slot),"Owned discard gem missing complete metadata");
    }
}
SqliteOwnedInstanceDiscardRepository::Snapshot SqliteOwnedInstanceDiscardRepository::load(std::uint64_t account,std::uint64_t character){
    ReadScope scope(db_);Snapshot saved;saved.bag=armor_reader_.load_snapshot(account,character);
    // Compare the borrowed observation against a native-qualified reader on
    // this exact writer connection; a reader of an identical separate fixture
    // cannot mask a later writer-only trigger or ownership mutation.
    require(SqliteArmorSlotRepository(db_,armor_,armor_instance_).load_snapshot(account,character)==saved.bag,"Owned discard borrowed/writer snapshot conflict");
    validate(saved.bag);saved.peripheral=peripheral(db_,character);scope.finish();return saved;
}
SqliteOwnedInstanceDiscardRepository::Plan SqliteOwnedInstanceDiscardRepository::plan(const Request& request) const{
    validate(request.expected.bag);require(request.source<30&&request.item&&request.quantity==1,"Owned discard source/key/quantity rejected");
    const auto& scalar=request.expected.bag.scalar[request.source];require(scalar&&scalar->count==1&&scalar->item_id==request.item&&scalar->revision<max_revision&&scalar->source_sha256==SqliteArmorSlotRepository::source_sha256,"Owned discard requires exact qualified whole source");
    Plan next;next.after=request.expected;next.slot=request.source;
    if(const auto* value=row(request.expected.bag.armor,request.source)){next.kind=Kind::Armor;next.removed20=value->logical20;next.origin=value->origin;next.provenance=value->provenance;next.source_sha256=SqliteArmorSlotRepository::source_sha256;next.client_sha256=SqliteArmorSlotRepository::client_sha256;next.instance_design_id=SqliteArmorSlotRepository::design_id;}
    else {const auto* foreign_value=row(request.expected.bag.weapons,request.source);next.kind=Kind::Weapon;if(!foreign_value){foreign_value=row(request.expected.bag.gems,request.source);next.kind=Kind::Gem;}require(foreign_value,"Owned discard selected instance metadata missing");next.removed20=foreign_value->logical20;next.origin=foreign_value->origin;next.provenance=foreign_value->provenance;next.source_sha256=foreign_value->source_sha256;next.client_sha256=foreign_value->client_sha256;next.instance_design_id=foreign_value->design_id;}
    auto& bag=next.after.bag;std::erase_if(bag.armor,[&](const auto& value){return value.slot==request.source;});std::erase_if(bag.weapons,[&](const auto& value){return value.slot==request.source;});std::erase_if(bag.gems,[&](const auto& value){return value.slot==request.source;});
    auto& cleared=*bag.scalar[request.source];cleared.item_id=0;cleared.count=0;++cleared.revision;validate(bag);return next;
}
bool SqliteOwnedInstanceDiscardRepository::receipt_exists(const std::string& receipt){require(hash(receipt),"Owned discard receipt malformed");sqlite_detail::Statement read(db_,"SELECT 1 FROM character_owned_instance_discard_receipts WHERE receipt=?");read.bind(1,receipt);return read.row();}
void SqliteOwnedInstanceDiscardRepository::no_battle(std::uint64_t character){sqlite_detail::Statement read(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");read.bind_id(1,character);require(!read.row(),"Owned discard pending battle");}
SqliteOwnedInstanceDiscardRepository::Plan SqliteOwnedInstanceDiscardRepository::commit(const std::string& receipt,const Request& request,const Prepare& prepare,const Check& check){
    static_assert(std::is_nothrow_move_constructible_v<Plan>,"Committed discard plan must return without allocation exceptions");
    require(hash(receipt)&&bool(prepare)&&sqlite3_get_autocommit(db_)!=0,"Owned discard receipt/preparation/transaction invalid");auto next=plan(request);require(!receipt_exists(receipt),"Owned discard duplicate receipt");
    // Snapshot.load deliberately excludes this destruction ledger. Capture
    // its exact existing typed rows now, before preparation; subsequent BEGIN/
    // readback/Check guards protect this commit interval, not load-to-commit
    // history changes. Do not recursively embed old audits inside new audits.
    const auto before=state(request.expected),after=state(next.after),old_history=history(db_,receipt);prepare(next);
    sqlite_detail::Transaction transaction(db_);const auto account=request.expected.bag.account,character=request.expected.bag.character;
    require(load(account,character)==request.expected&&!receipt_exists(receipt)&&history(db_,receipt)==old_history,"Owned discard complete before CAS/history conflict");no_battle(character);
    if(next.kind==Kind::Armor)erase_armor(db_,character,*row(request.expected.bag.armor,request.source));
    else if(next.kind==Kind::Weapon)erase_foreign(db_,character,*row(request.expected.bag.weapons,request.source),true);
    else erase_foreign(db_,character,*row(request.expected.bag.gems,request.source),false);
    const auto& old=*request.expected.bag.scalar[request.source];const auto& cleared=*next.after.bag.scalar[request.source];
    sqlite_detail::Statement write(db_,"UPDATE diagnostic_inventory_slots SET item_id=0,count=0,revision=? WHERE character_id=? AND slot=? AND item_id=? AND count=1 AND revision=? AND source_sha256=? AND design_id='CUSTOM-0015'");write.bind_id(1,cleared.revision);write.bind_id(2,character);write.bind(3,request.source);write.bind(4,old.item_id);write.bind_id(5,old.revision);write.bind(6,old.source_sha256);write.done();require(sqlite3_changes(db_)==1,"Owned discard scalar clear CAS failed");
    sqlite_detail::Statement insert(db_,"INSERT INTO character_owned_instance_discard_receipts VALUES(?,?,?,39,?,?,1,?,?,?,?,?,?,?,?,?,'CUSTOM-0071')");
    insert.bind(1,receipt);insert.bind_id(2,account);insert.bind_id(3,character);insert.bind(4,request.item);insert.bind(5,request.source);insert.bind(6,static_cast<std::uint8_t>(next.kind));insert.bind_blob(7,next.removed20);insert.bind(8,next.origin);insert.bind(9,next.provenance);insert.bind(10,next.source_sha256);insert.bind(11,next.client_sha256);insert.bind(12,next.instance_design_id);insert.bind(13,before);insert.bind(14,after);insert.done();require(sqlite3_changes(db_)==1,"Owned discard receipt insert failed");
    const auto verify=[&]{
        sqlite_detail::Statement read(db_,"SELECT account_id,character_id,operation,item_id,source,quantity,kind,logical20,origin,provenance,source_sha256,client_sha256,instance_design_id,before_state,after_state,design_id FROM character_owned_instance_discard_receipts WHERE receipt=?");read.bind(1,receipt);
        require(read.row()&&read.number<std::uint64_t>(0)==account&&read.number<std::uint64_t>(1)==character&&read.number<std::uint8_t>(2)==39&&read.number<std::uint16_t>(3)==request.item&&read.number<std::uint8_t>(4)==request.source&&read.number<std::uint8_t>(5)==1&&read.number<std::uint8_t>(6)==static_cast<std::uint8_t>(next.kind),"Owned discard receipt owner/operation readback conflict");
        const auto bytes=read.blob(7,20,20);require(std::equal(bytes.begin(),bytes.end(),next.removed20.begin())&&read.text(8)==next.origin&&read.text(9)==next.provenance&&read.text(10)==next.source_sha256&&read.text(11)==next.client_sha256&&read.text(12)==next.instance_design_id&&read.text(13)==before&&read.text(14)==after&&read.text(15)==design_id&&!read.row(),"Owned discard full20/provenance/exact receipt readback conflict");
        require(load(account,character)==next.after&&history(db_,receipt)==old_history,"Owned discard whole readback/other owner/currency/history conflict");no_battle(character);
    };verify();if(check){check(next);verify();}transaction.commit();return next;
}
}
