#include "db/SqliteOwnedArmorBankRepository.h"
#include "db/SqliteSupport.h"
#include "db/SqliteWeaponSlotRepository.h"
#include "protocol/RecoveredArmorInstance.h"
#include <algorithm>
#include <limits>
#include <nlohmann/json.hpp>
#include <utility>

namespace god2 {
namespace {
constexpr auto limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
void require(bool ok,const char* message){if(!ok)throw DatabaseError(message);}
bool hash(const std::string& value){return value.size()==64&&value.find_first_not_of("0123456789abcdef")==std::string::npos;}
std::uint16_t key(const std::array<std::uint8_t,20>& value){return static_cast<std::uint16_t>(value[0]|(std::uint16_t{value[1]}<<8));}
bool evidence(const std::string& value){return !value.empty()&&value.size()<=512&&value.find('\0')==std::string::npos;}
void scalar(const StoredInventorySlot& value){require(value.revision&&value.revision<=limit&&value.count<=127&&((value.count==0)==(value.item_id==0))&&hash(value.source_sha256),"Owned armor bank scalar malformed");}
template<class T>const T* row(const std::vector<T>& values,std::uint16_t slot){const auto found=std::find_if(values.begin(),values.end(),[&](const auto& value){return value.slot==slot;});return found==values.end()?nullptr:&*found;}
struct Cell {bool vault;std::uint16_t slot;};
std::array<Cell,2> cells(const SqliteOwnedArmorBankRepository::Request& request){
    using O=SqliteOwnedArmorBankRepository::Operation;require(request.page<6&&request.quantity==1,"Owned armor bank whole-instance marker required");
    const auto base=static_cast<std::uint16_t>(request.page*50);
    if(request.operation==O::Deposit){require(request.source<30&&request.destination<50,"Owned armor deposit domain rejected");return {Cell{false,request.source},Cell{true,static_cast<std::uint16_t>(base+request.destination)}};}
    if(request.operation==O::Withdraw){require(request.source<50&&request.destination<30,"Owned armor withdrawal domain rejected");return {Cell{true,static_cast<std::uint16_t>(base+request.source)},Cell{false,request.destination}};}
    require(request.operation==O::Move&&request.source<50&&request.destination<50&&request.source!=request.destination,"Owned armor bank move domain rejected");
    return {Cell{true,static_cast<std::uint16_t>(base+request.source)},Cell{true,static_cast<std::uint16_t>(base+request.destination)}};
}
const StoredInventorySlot& at(const SqliteOwnedArmorBankRepository::Snapshot& saved,Cell cell){return cell.vault?saved.vault[cell.slot]:saved.bag.scalar[cell.slot].value();}
StoredInventorySlot& at(SqliteOwnedArmorBankRepository::Snapshot& saved,Cell cell){return cell.vault?saved.vault[cell.slot]:saved.bag.scalar[cell.slot].value();}
std::optional<StoredVaultArmor> instance(const SqliteOwnedArmorBankRepository::Snapshot& saved,Cell cell){
    if(cell.vault){if(const auto* value=row(saved.armor,cell.slot))return *value;return {};}
    if(const auto* value=row(saved.bag.armor,cell.slot))return StoredVaultArmor{cell.slot,value->logical20,value->revision,value->origin,value->provenance,SqliteArmorSlotRepository::source_sha256,SqliteArmorSlotRepository::client_sha256,SqliteArmorSlotRepository::design_id};
    return {};
}
void put(SqliteOwnedArmorBankRepository::Snapshot& saved,Cell cell,std::optional<StoredVaultArmor> value){
    if(cell.vault){std::erase_if(saved.armor,[&](const auto& item){return item.slot==cell.slot;});if(value)saved.armor.push_back(*value);std::sort(saved.armor.begin(),saved.armor.end(),[](const auto& a,const auto& b){return a.slot<b.slot;});}
    else {
        std::erase_if(saved.bag.armor,[&](const auto& item){return item.slot==cell.slot;});
        if(value)saved.bag.armor.push_back(StoredArmorSlot{static_cast<std::uint8_t>(cell.slot),key(value->logical20),1,value->revision,value->logical20,value->origin,value->provenance,true});
        std::sort(saved.bag.armor.begin(),saved.bag.armor.end(),[](const auto& a,const auto& b){return a.slot<b.slot;});
        // Exactly the existing scalar-update empty weapon retirement policy.
        std::erase_if(saved.bag.weapons,[&](const auto& item){return item.slot==cell.slot&&item.origin=="EMPTY_SLOT_POLICY";});
    }
}
void no_battle(sqlite3* db,std::uint64_t character){sqlite_detail::Statement read(db,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");read.bind_id(1,character);require(!read.row(),"Owned armor bank during pending battle");}
struct ReadScope {
    sqlite3* db;bool owns,done=false;
    explicit ReadScope(sqlite3* value):db(value),owns(sqlite3_get_autocommit(value)!=0){if(owns)sqlite_detail::execute(db,"BEGIN");}
    ~ReadScope(){if(owns&&!done)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){if(owns)sqlite_detail::execute(db,"COMMIT");done=true;}
};
std::string state(const SqliteOwnedArmorBankRepository::Snapshot& saved){
    using nlohmann::json;json result=json::array({saved.bag.account,saved.bag.character});
    const auto scalar=[](const StoredInventorySlot& value){return json::array({value.item_id,value.count,value.revision,value.source_sha256});};
    json bag=json::array(),vault=json::array(),armor=json::array(),bagarmor=json::array(),weapon=json::array(),gem=json::array();
    for(const auto& value:saved.bag.scalar)bag.push_back(value?scalar(*value):json(nullptr));for(const auto& value:saved.vault)vault.push_back(scalar(value));
    for(const auto& value:saved.armor)armor.push_back(json::array({value.slot,value.logical20,value.revision,value.origin,value.provenance,value.source_sha256,value.client_sha256,value.instance_design_id}));
    for(const auto& value:saved.bag.armor)bagarmor.push_back(json::array({value.slot,value.item_id,value.count,value.revision,value.logical20,value.origin,value.provenance,value.metadata_present}));
    const auto foreign=[](const auto& value){return json::array({value.slot,value.logical20,value.revision,value.origin,value.provenance,value.source_sha256,value.client_sha256,value.design_id});};
    for(const auto& value:saved.bag.weapons)weapon.push_back(foreign(value));for(const auto& value:saved.bag.gems)gem.push_back(foreign(value));
    result.push_back(bag);result.push_back(vault);result.push_back(bagarmor);result.push_back(weapon);result.push_back(gem);result.push_back(armor);return result.dump();
}
}
std::string SqliteOwnedArmorBankRepository::schema(){return R"SQL(
CREATE TABLE character_bank_armor_metadata(
 character_id INTEGER NOT NULL,slot INTEGER NOT NULL CHECK(typeof(slot)='integer' AND slot BETWEEN 0 AND 299),
 logical20 BLOB NOT NULL CHECK(typeof(logical20)='blob' AND length(logical20)=20),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 origin TEXT NOT NULL CHECK(origin IN ('NATIVE_CAPTURE_VERIFIED','CUSTOM_TEST_NOT_NATIVE')),
 provenance TEXT NOT NULL CHECK(typeof(provenance)='text' AND length(CAST(provenance AS BLOB)) BETWEEN 1 AND 512 AND instr(provenance,char(0))=0),
 source_sha256 TEXT NOT NULL CHECK(source_sha256='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'),
 client_sha256 TEXT NOT NULL CHECK(client_sha256='c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575'),
 instance_design_id TEXT NOT NULL CHECK(instance_design_id='CUSTOM-0066'),
 storage_design_id TEXT NOT NULL CHECK(storage_design_id='CUSTOM-0067'),
 PRIMARY KEY(character_id,slot),FOREIGN KEY(character_id,slot) REFERENCES character_bank_item_slots(character_id,slot) ON DELETE CASCADE
);
CREATE TRIGGER bank_armor_insert_guard BEFORE INSERT ON character_bank_armor_metadata BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM character_bank_item_slots WHERE character_id=NEW.character_id AND slot=NEW.slot AND count=1 AND revision=NEW.revision AND source_sha256=NEW.source_sha256 AND design_id='CUSTOM-0065' AND item_design_id='CUSTOM-0015' AND hex(substr(NEW.logical20,1,2))=printf('%02X%02X',item_id&255,(item_id>>8)&255)) THEN RAISE(ABORT,'Vault armor scalar mismatch') END;
END;
CREATE TRIGGER bank_armor_update_guard BEFORE UPDATE ON character_bank_armor_metadata BEGIN
 SELECT CASE WHEN NEW.character_id<>OLD.character_id OR NEW.slot<>OLD.slot OR NOT EXISTS(SELECT 1 FROM character_bank_item_slots WHERE character_id=NEW.character_id AND slot=NEW.slot AND count=1 AND revision=NEW.revision AND source_sha256=NEW.source_sha256 AND design_id='CUSTOM-0065' AND item_design_id='CUSTOM-0015' AND hex(substr(NEW.logical20,1,2))=printf('%02X%02X',item_id&255,(item_id>>8)&255)) THEN RAISE(ABORT,'Vault armor scalar mismatch') END;
END;
CREATE TABLE character_bank_armor_receipts(
 receipt TEXT PRIMARY KEY CHECK(length(receipt)=64 AND receipt NOT GLOB '*[^0-9a-f]*'),
 account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,character_id INTEGER NOT NULL REFERENCES recovered_characters(id) ON DELETE CASCADE,
 operation INTEGER NOT NULL CHECK(operation IN (99,100,101)),page INTEGER NOT NULL CHECK(page BETWEEN 0 AND 5),
 source INTEGER NOT NULL CHECK(source BETWEEN 0 AND 49),destination INTEGER NOT NULL CHECK(destination BETWEEN 0 AND 49),
 quantity INTEGER NOT NULL CHECK(quantity=1),before_state TEXT NOT NULL CHECK(length(before_state)>0),after_state TEXT NOT NULL CHECK(length(after_state)>0),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0067')
);
)SQL";}
SqliteOwnedArmorBankRepository::SqliteOwnedArmorBankRepository(sqlite3* db,QualifyArmor qualify,QualifyInstance instance):db_(db),qualify_(std::move(qualify)),instance_(std::move(instance)){
    require(db_&&bool(qualify_)&&bool(instance_),"Owned armor bank needs source and complete-instance qualifiers");
}
void SqliteOwnedArmorBankRepository::validate(const Snapshot& saved) const {
    require(saved.bag.account&&saved.bag.account<=limit&&saved.bag.character&&saved.bag.character<=limit,"Owned armor bank owner missing");
    // Existing repository validates all bag scalar/armor/foreign metadata.
    // Admission of manually supplied snapshots is completed by actual full CAS.
    for(std::size_t slot=0;slot<saved.bag.scalar.size();++slot){const auto& value=saved.bag.scalar[slot];require(slot>=30||value.has_value(),"Owned armor bank complete30 bag capacity missing");if(value)scalar(*value);}
    for(const auto& value:saved.vault)scalar(value);
    const auto qualified=[&](const auto& bytes){const auto part=qualify_(key(bytes));return part&&*part>=30&&*part<=33&&RecoveredArmorInstance::armor_family(bytes)&&instance_(key(bytes),bytes);};
    std::uint16_t previous=0;bool first=true;
    for(const auto& value:saved.armor){
        require(value.slot<300&&(first||value.slot>previous),"Vault armor slot ordering invalid");first=false;previous=value.slot;const auto& cell=saved.vault[value.slot];
        require(cell.count==1&&cell.item_id==key(value.logical20)&&cell.revision==value.revision&&cell.source_sha256==value.source_sha256&&
            value.source_sha256==SqliteArmorSlotRepository::source_sha256&&value.client_sha256==SqliteArmorSlotRepository::client_sha256&&value.instance_design_id==SqliteArmorSlotRepository::design_id&&
            (value.origin=="NATIVE_CAPTURE_VERIFIED"||value.origin=="CUSTOM_TEST_NOT_NATIVE")&&evidence(value.provenance)&&qualified(value.logical20),"Vault armor full-instance qualification failed");
    }
    for(std::uint16_t slot=0;slot<300;++slot)if(saved.vault[slot].count&&qualify_(saved.vault[slot].item_id))require(row(saved.armor,slot)!=nullptr,"Vault armor complete metadata missing");
    previous=0;first=true;
    for(const auto& value:saved.bag.armor){
        require(value.slot<34&&(first||value.slot>previous),"Bag armor snapshot ordering invalid");first=false;previous=value.slot;
        const auto& cell=saved.bag.scalar[value.slot];const auto part=qualify_(value.item_id);
        require(cell&&cell->count==1&&value.count==1&&value.metadata_present&&key(value.logical20)==value.item_id&&cell->item_id==value.item_id&&cell->revision==value.revision&&cell->source_sha256==SqliteArmorSlotRepository::source_sha256&&qualified(value.logical20)&&
            (value.slot<30||(part&&value.slot==*part))&&(value.origin=="NATIVE_CAPTURE_VERIFIED"||value.origin=="CUSTOM_TEST_NOT_NATIVE")&&evidence(value.provenance)&&!row(saved.bag.weapons,value.slot)&&!row(saved.bag.gems,value.slot),"Bag armor snapshot qualification failed");
    }
    for(std::uint8_t slot=0;slot<34;++slot)if(const auto& cell=saved.bag.scalar[slot];cell&&cell->count&&qualify_(cell->item_id))require(row(saved.bag.armor,slot)!=nullptr,"Bag armor complete metadata missing");
    const auto foreign=[&](const auto& values,bool weapon){
        std::uint8_t last=0;bool first=true;
        for(const auto& value:values){
            require((weapon?(value.slot<30||value.slot==34):value.slot<30)&&(first||value.slot>last),"Observed foreign overlay ordering invalid");first=false;last=value.slot;
            const auto& cell=saved.bag.scalar[value.slot];require(cell&&cell->revision==value.revision&&cell->item_id==key(value.logical20)&&cell->source_sha256==value.source_sha256&&value.source_sha256==SqliteArmorSlotRepository::source_sha256&&evidence(value.provenance),"Observed foreign overlay scalar mismatch");
            if(weapon)require(value.client_sha256==SqliteWeaponSlotRepository::client_sha256&&value.design_id=="CUSTOM-0046"&&(cell->count?cell->count==1&&(value.origin=="NATIVE_CAPTURE_VERIFIED"||value.origin=="CUSTOM_TEST_NOT_NATIVE"):value.origin=="EMPTY_SLOT_POLICY"),"Observed weapon overlay pins invalid");
            else require(cell->count==1&&value.client_sha256.empty()&&value.design_id=="CUSTOM-0057"&&(value.origin=="NATIVE_CAPTURE_VERIFIED"||value.origin=="CUSTOM_TEST_NOT_NATIVE"),"Observed gem overlay pins invalid");
            require(!row(saved.bag.armor,value.slot)&&!(weapon?row(saved.bag.gems,value.slot):row(saved.bag.weapons,value.slot)),"Observed foreign overlay collision");
        }
    };foreign(saved.bag.weapons,true);foreign(saved.bag.gems,false);
}
SqliteOwnedArmorBankRepository::Snapshot SqliteOwnedArmorBankRepository::load(std::uint64_t account,std::uint64_t character){
    ReadScope scope(db_);Snapshot saved;SqliteArmorSlotRepository bags(db_,qualify_,instance_);saved.bag=bags.load_snapshot(account,character);
    const auto scalar=SqliteBankItemsRepository(db_).load(account,character);saved.vault=scalar.vault;
    sqlite_detail::Statement read(db_,"SELECT slot,logical20,revision,origin,provenance,source_sha256,client_sha256,instance_design_id,storage_design_id FROM character_bank_armor_metadata WHERE character_id=? ORDER BY slot");read.bind_id(1,character);
    while(read.row()){
        StoredVaultArmor value;value.slot=read.number<std::uint16_t>(0);const auto bytes=read.blob(1,20,20);std::copy(bytes.begin(),bytes.end(),value.logical20.begin());value.revision=read.number<std::uint64_t>(2);
        value.origin=read.text(3);value.provenance=read.text(4);value.source_sha256=read.text(5);value.client_sha256=read.text(6);value.instance_design_id=read.text(7);require(read.text(8)==design_id,"Vault armor custody design invalid");saved.armor.push_back(std::move(value));
    }validate(saved);scope.finish();return saved;
}
SqliteOwnedArmorBankRepository::Plan SqliteOwnedArmorBankRepository::plan(const Request& request) const {
    validate(request.expected);const auto pair=cells(request);const auto from=instance(request.expected,pair[0]),to=instance(request.expected,pair[1]);
    const auto& source=at(request.expected,pair[0]);const auto& destination=at(request.expected,pair[1]);
    require(from&&source.count==1,"Owned armor bank requires complete qualified armor source");
    require(source.revision<limit&&destination.revision<limit,"Owned armor bank physical revision overflow");
    if(request.operation!=Operation::Move)require(destination.count==0&&!to,"Owned armor bank deposit/withdraw requires empty target");
    else require(!destination.count||(to&&destination.count==1),"Owned armor bank swap target is not qualified whole armor");
    if(!pair[1].vault){require(!row(request.expected.bag.gems,pair[1].slot),"Owned armor bank empty destination has gem overlay");if(const auto* other=row(request.expected.bag.weapons,pair[1].slot))require(other->origin=="EMPTY_SLOT_POLICY","Owned armor bank destination has occupied foreign overlay");}
    Plan next{request.expected,pair[0].vault,pair[1].vault,pair[0].slot,pair[1].slot};
    auto& a=at(next.after,pair[0]);auto& b=at(next.after,pair[1]);
    b=source;b.revision=destination.revision+1;
    if(to){a=destination;a.revision=source.revision+1;}
    else{a.item_id=0;a.count=0;++a.revision;}
    auto outgoing=from;outgoing->slot=pair[1].slot;outgoing->revision=b.revision;auto incoming=to;if(incoming){incoming->slot=pair[0].slot;incoming->revision=a.revision;}
    put(next.after,pair[0],incoming);put(next.after,pair[1],outgoing);validate(next.after);return next;
}
bool SqliteOwnedArmorBankRepository::receipt_exists(const std::string& receipt,ReceiptLedger ledger){
    require(hash(receipt),"Owned armor bank receipt invalid");ReadScope scope(db_);const char* query=ledger==ReceiptLedger::Any?"SELECT 1 FROM character_bank_armor_receipts WHERE receipt=? UNION ALL SELECT 1 FROM character_bank_item_receipts WHERE receipt=?":ledger==ReceiptLedger::Armor?"SELECT 1 FROM character_bank_armor_receipts WHERE receipt=?":"SELECT 1 FROM character_bank_item_receipts WHERE receipt=?";sqlite_detail::Statement read(db_,query);read.bind(1,receipt);if(ledger==ReceiptLedger::Any)read.bind(2,receipt);const bool exists=read.row();scope.finish();return exists;
}
void SqliteOwnedArmorBankRepository::verify_snapshot_in_transaction(const Snapshot& expected){
    require(sqlite3_get_autocommit(db_)==0,"Owned armor bank proof requires shared mutation transaction");require(load(expected.bag.account,expected.bag.character)==expected,"Owned armor bank full snapshot proof conflict");no_battle(db_,expected.bag.character);
}
SqliteOwnedArmorBankRepository::Plan SqliteOwnedArmorBankRepository::commit(const std::string& receipt,const Request& request,const Prepare& prepare,const Check& check,const std::function<void()>& current){
    require(hash(receipt)&&bool(prepare),"Owned armor bank receipt/preparation invalid");require(sqlite3_get_autocommit(db_)!=0,"Owned armor bank must own mutation transaction");
    auto next=plan(request);const auto pair=cells(request);const auto before=state(request.expected),after=state(next.after);
    prepare(next); // Serialization/projection can fail before any database write.
    sqlite_detail::Transaction transaction(db_);
    require(load(request.expected.bag.account,request.expected.bag.character)==request.expected,"Owned armor bank complete before snapshot conflict");no_battle(db_,request.expected.bag.character);
    sqlite_detail::Statement duplicate(db_,"SELECT 1 FROM character_bank_armor_receipts WHERE receipt=? UNION ALL SELECT 1 FROM character_bank_item_receipts WHERE receipt=?");duplicate.bind(1,receipt);duplicate.bind(2,receipt);require(!duplicate.row(),"Owned armor bank duplicate receipt");
    if(current)current(); // Pure lifecycle check after before-read observers.
    for(const auto cell:pair)if(const auto value=instance(request.expected,cell)){
        sqlite_detail::Statement erase(db_,cell.vault?
            "DELETE FROM character_bank_armor_metadata WHERE character_id=? AND slot=? AND logical20=? AND revision=? AND origin=? AND provenance=? AND source_sha256=? AND client_sha256=? AND instance_design_id='CUSTOM-0066' AND storage_design_id='CUSTOM-0067'":
            "DELETE FROM character_armor_slot_metadata WHERE character_id=? AND slot=? AND logical20=? AND revision=? AND origin=? AND provenance=? AND source_sha256=? AND client_sha256=? AND design_id='CUSTOM-0066'");
        erase.bind_id(1,request.expected.bag.character);erase.bind(2,cell.slot);erase.bind_blob(3,value->logical20);erase.bind_id(4,value->revision);erase.bind(5,value->origin);erase.bind(6,value->provenance);erase.bind(7,value->source_sha256);erase.bind(8,value->client_sha256);erase.done();require(sqlite3_changes(db_)==1,"Owned armor bank metadata CAS removal failed");
    }
    for(const auto cell:pair){
        const auto& old=at(request.expected,cell);const auto& value=at(next.after,cell);
        sqlite_detail::Statement write(db_,cell.vault?
            "UPDATE character_bank_item_slots SET item_id=?,count=?,revision=?,source_sha256=? WHERE character_id=? AND slot=? AND item_id=? AND count=? AND revision=? AND source_sha256=? AND item_design_id='CUSTOM-0015' AND design_id='CUSTOM-0065'":
            "UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=?,source_sha256=? WHERE character_id=? AND slot=? AND item_id=? AND count=? AND revision=? AND source_sha256=? AND design_id='CUSTOM-0015'");
        write.bind(1,value.item_id);write.bind(2,value.count);write.bind_id(3,value.revision);write.bind(4,value.source_sha256);write.bind_id(5,request.expected.bag.character);write.bind(6,cell.slot);write.bind(7,old.item_id);write.bind(8,old.count);write.bind_id(9,old.revision);write.bind(10,old.source_sha256);write.done();require(sqlite3_changes(db_)==1,"Owned armor bank scalar CAS write failed");
        if(const auto metadata=instance(next.after,cell)){
            sqlite_detail::Statement insert(db_,cell.vault?
                "INSERT INTO character_bank_armor_metadata VALUES(?,?,?,?,?,?,?,?, 'CUSTOM-0066','CUSTOM-0067')":
                "INSERT INTO character_armor_slot_metadata VALUES(?,?,?,?,?,?,?,?,'CUSTOM-0066')");
            insert.bind_id(1,request.expected.bag.character);insert.bind(2,cell.slot);insert.bind_blob(3,metadata->logical20);insert.bind_id(4,metadata->revision);insert.bind(5,metadata->origin);insert.bind(6,metadata->provenance);insert.bind(7,metadata->source_sha256);insert.bind(8,metadata->client_sha256);insert.done();require(sqlite3_changes(db_)==1,"Owned armor bank metadata installation failed");
        }
    }
    sqlite_detail::Statement insert(db_,"INSERT INTO character_bank_armor_receipts VALUES(?,?,?,?,?,?,?,?,?,?,'CUSTOM-0067')");
    insert.bind(1,receipt);insert.bind_id(2,request.expected.bag.account);insert.bind_id(3,request.expected.bag.character);insert.bind(4,static_cast<std::uint8_t>(request.operation));insert.bind(5,request.page);insert.bind(6,request.source);insert.bind(7,request.destination);insert.bind(8,request.quantity);insert.bind(9,before);insert.bind(10,after);insert.done();require(sqlite3_changes(db_)==1,"Owned armor bank receipt write failed");
    const auto verify=[&]{
        sqlite_detail::Statement read(db_,"SELECT account_id,character_id,operation,page,source,destination,quantity,before_state,after_state,design_id FROM character_bank_armor_receipts WHERE receipt=?");read.bind(1,receipt);
        require(read.row()&&read.number<std::uint64_t>(0)==request.expected.bag.account&&read.number<std::uint64_t>(1)==request.expected.bag.character&&read.number<std::uint8_t>(2)==static_cast<std::uint8_t>(request.operation)&&read.number<std::uint8_t>(3)==request.page&&read.number<std::uint8_t>(4)==request.source&&read.number<std::uint8_t>(5)==request.destination&&read.number<std::uint8_t>(6)==1&&read.text(7)==before&&read.text(8)==after&&read.text(9)==design_id&&!read.row(),"Owned armor bank receipt readback failed");
        require(load(request.expected.bag.account,request.expected.bag.character)==next.after,"Owned armor bank full actual readback failed");no_battle(db_,request.expected.bag.character);
    };
    verify();if(check){check(next);verify();}if(current)current();transaction.commit();return next;
}
}
