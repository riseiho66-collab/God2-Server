#include "db/SqliteOwnedMixedBankRepository.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <limits>
#include <map>
#include <memory>
#include <nlohmann/json.hpp>
#include <type_traits>
#include <utility>

namespace god2 {
namespace {
constexpr auto max_revision=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
void require(bool yes,const char* why){if(!yes)throw DatabaseError(why);}
bool hash(const std::string& value){return value.size()==64&&value.find_first_not_of("0123456789abcdef")==std::string::npos;}
template<class T>const T* row(const std::vector<T>& values,std::uint16_t slot){const auto found=std::find_if(values.begin(),values.end(),[&](const auto& value){return value.slot==slot;});return found==values.end()?nullptr:&*found;}
template<class T>void replace(std::vector<T>& values,std::uint16_t slot,std::optional<T> value,std::uint64_t revision){std::erase_if(values,[&](const auto& item){return item.slot==slot;});if(value){value->slot=slot;value->revision=revision;values.push_back(std::move(*value));}std::sort(values.begin(),values.end(),[](const auto& a,const auto& b){return a.slot<b.slot;});}
// Observe the unmodified owners, money and preexisting receipt history on the
// actual writer connection too. This also rejects an unrelated SQL trigger
// silently changing another player's instance or currency.
std::string immutable_rows(sqlite3* db,std::uint64_t character,const std::string& receipt){
    using J=nlohmann::json;J result=J::array();
    for(const auto* table:{"diagnostic_inventory_slots","character_armor_slot_metadata","character_weapon_slot_metadata","character_teleport_gem_metadata","character_bank_item_slots","character_bank_armor_metadata","character_bank_foreign_metadata","character_bank_balances","character_trade_wallets","character_bank_item_receipts","character_bank_armor_receipts","character_bank_foreign_receipts","character_bank_mixed_receipts"}){
        sqlite_detail::Statement exists(db,"SELECT 1 FROM sqlite_schema WHERE type='table' AND name=?");exists.bind(1,std::string(table));if(!exists.row()){result.push_back(J::array({table,nullptr}));continue;}
        const std::string name=table;const bool history=name.ends_with("receipts"),money=name=="character_bank_balances"||name=="character_trade_wallets";
        const auto sql="SELECT * FROM "+name+(history?(name=="character_bank_mixed_receipts"?" WHERE receipt<>?":""):money?"":" WHERE character_id<>?")+" ORDER BY rowid";
        sqlite3_stmt* raw=nullptr;sqlite_detail::check(db,sqlite3_prepare_v2(db,sql.c_str(),-1,&raw,nullptr));std::unique_ptr<sqlite3_stmt,decltype(&sqlite3_finalize)> owned(raw,sqlite3_finalize);
        if(!history&&!money)sqlite_detail::check(db,sqlite3_bind_int64(raw,1,static_cast<sqlite3_int64>(character)));
        if(name=="character_bank_mixed_receipts")sqlite_detail::check(db,sqlite3_bind_text(raw,1,receipt.data(),static_cast<int>(receipt.size()),SQLITE_TRANSIENT));
        J rows=J::array();int rc=SQLITE_OK;while((rc=sqlite3_step(raw))==SQLITE_ROW){J values=J::array();for(int i=0;i<sqlite3_column_count(raw);++i){const auto type=sqlite3_column_type(raw,i);J value;
            if(type==SQLITE_INTEGER)value=sqlite3_column_int64(raw,i);else if(type==SQLITE_FLOAT)value=sqlite3_column_double(raw,i);else if(type==SQLITE_NULL)value=nullptr;
            else {const auto size=sqlite3_column_bytes(raw,i);const auto* bytes=static_cast<const std::uint8_t*>(type==SQLITE_BLOB?sqlite3_column_blob(raw,i):static_cast<const void*>(sqlite3_column_text(raw,i)));std::vector<std::uint8_t> data;if(size)data.assign(bytes,bytes+size);value=std::move(data);}
            values.push_back(J::array({type,value}));}rows.push_back(std::move(values));}
        require(rc==SQLITE_DONE,"Mixed bank immutable-row observation failed");result.push_back(J::array({name,rows}));
    }return result.dump();
}
std::string state(const SqliteOwnedMixedBankRepository::Snapshot& saved){
    using J=nlohmann::json;const auto scalar=[](const StoredInventorySlot& value){return J::array({value.item_id,value.count,value.revision,value.source_sha256});};J out=J::array({saved.base.bag.account,saved.base.bag.character}),bag=J::array(),vault=J::array(),armorbag=J::array(),armorvault=J::array(),weapons=J::array(),gems=J::array(),foreign=J::array();
    for(const auto& item:saved.base.bag.scalar)bag.push_back(item?scalar(*item):J(nullptr));for(const auto& item:saved.base.vault)vault.push_back(scalar(item));
    for(const auto& item:saved.base.bag.armor)armorbag.push_back(J::array({item.slot,item.item_id,item.count,item.revision,item.logical20,item.origin,item.provenance,item.metadata_present}));
    for(const auto& item:saved.base.armor)armorvault.push_back(J::array({item.slot,item.logical20,item.revision,item.origin,item.provenance,item.source_sha256,item.client_sha256,item.instance_design_id}));
    const auto overlay=[](const auto& item){return J::array({item.slot,item.logical20,item.revision,item.origin,item.provenance,item.source_sha256,item.client_sha256,item.design_id});};for(const auto& item:saved.base.bag.weapons)weapons.push_back(overlay(item));for(const auto& item:saved.base.bag.gems)gems.push_back(overlay(item));
    for(const auto& item:saved.foreign)foreign.push_back(J::array({item.slot,static_cast<std::uint8_t>(item.kind),item.logical20,item.revision,item.origin,item.provenance,item.source_sha256,item.client_sha256,item.instance_design_id,item.source_family,item.parsed_sha256}));
    out.push_back(bag);out.push_back(vault);out.push_back(armorbag);out.push_back(armorvault);out.push_back(weapons);out.push_back(gems);out.push_back(foreign);return out.dump();
}
}
std::string SqliteOwnedMixedBankRepository::schema(){return R"SQL(
CREATE TABLE character_bank_mixed_receipts(
 receipt TEXT PRIMARY KEY CHECK(length(receipt)=64 AND receipt NOT GLOB '*[^0-9a-f]*'),
 account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
 character_id INTEGER NOT NULL REFERENCES recovered_characters(id) ON DELETE CASCADE,
 operation INTEGER NOT NULL CHECK(operation=101),page INTEGER NOT NULL CHECK(page BETWEEN 0 AND 2),
 source INTEGER NOT NULL CHECK(source BETWEEN 2 AND 49),destination INTEGER NOT NULL CHECK(destination BETWEEN 2 AND 49 AND destination<>source),
 quantity INTEGER NOT NULL CHECK(typeof(quantity)='integer' AND quantity BETWEEN 1 AND 127),
 before_state TEXT NOT NULL CHECK(typeof(before_state)='text' AND length(before_state)>0),
 after_state TEXT NOT NULL CHECK(typeof(after_state)='text' AND length(after_state)>0),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0070')
);
)SQL";}
SqliteOwnedMixedBankRepository::SqliteOwnedMixedBankRepository(sqlite3* db,SqliteOwnedForeignBankRepository& foreign,EligiblePlain plain):db_(db),foreign_(foreign),plain_(std::move(plain)){
    require(db_&&bool(plain_),"Mixed bank requires shared connection and strict plain qualifier");
}
SqliteOwnedMixedBankRepository::Snapshot SqliteOwnedMixedBankRepository::load(std::uint64_t account,std::uint64_t character){return foreign_.load(account,character);}
SqliteOwnedMixedBankRepository::Plan SqliteOwnedMixedBankRepository::plan(const Request& request) const{
    require(request.page<3&&request.source>=2&&request.source<50&&request.destination>=2&&request.destination<50&&request.source!=request.destination,"Mixed bank move domain rejected");
    require(foreign_.load(request.expected.base.bag.account,request.expected.base.bag.character)==request.expected,"Mixed bank qualified complete before snapshot conflict");
    const auto source=static_cast<std::uint16_t>(request.page*50+request.source),destination=static_cast<std::uint16_t>(request.page*50+request.destination);
    const auto& a=request.expected.base.vault[source];const auto& b=request.expected.base.vault[destination];
    require(a.count&&request.quantity==a.count&&a.count<=127&&a.revision<max_revision&&b.revision<max_revision,"Mixed bank requires whole source and valid physical revisions");
    const auto qualified=[&](std::uint16_t slot){const auto& cell=request.expected.base.vault[slot];const auto* armor=row(request.expected.base.armor,slot);const auto* foreign=row(request.expected.foreign,slot);
        require(!(armor&&foreign),"Mixed bank overlay collision");
        if(!cell.count){require(!armor&&!foreign,"Mixed bank empty cell has occupied metadata");return;}
        if(armor||foreign)require(cell.count==1,"Mixed bank instance not whole");
        else require(plain_(cell.item_id)&&cell.source_sha256==SqliteArmorSlotRepository::source_sha256,"Mixed bank plain cell not strict original MED02");
    };qualified(source);qualified(destination);
    std::optional<StoredVaultArmor> a_armor,b_armor;std::optional<StoredVaultForeign> a_foreign,b_foreign;
    if(const auto* value=row(request.expected.base.armor,source))a_armor=*value;if(const auto* value=row(request.expected.base.armor,destination))b_armor=*value;
    if(const auto* value=row(request.expected.foreign,source))a_foreign=*value;if(const auto* value=row(request.expected.foreign,destination))b_foreign=*value;
    Plan next{request.expected,source,destination};auto& from=next.after.base.vault[source];auto& to=next.after.base.vault[destination];
    to=a;to.revision=b.revision+1;if(b.count){from=b;from.revision=a.revision+1;}else{from.item_id=0;from.count=0;from.revision=a.revision+1;}
    replace(next.after.base.armor,source,b_armor,from.revision);replace(next.after.base.armor,destination,a_armor,to.revision);
    replace(next.after.foreign,source,b_foreign,from.revision);replace(next.after.foreign,destination,a_foreign,to.revision);
    const auto counts=[](const Snapshot& saved){std::map<std::uint16_t,std::uint32_t> result;for(const auto& cell:saved.base.vault)if(cell.count)result[cell.item_id]+=cell.count;return result;};
    require(counts(next.after)==counts(request.expected),"Mixed bank whole quantity conservation failed");return next;
}
bool SqliteOwnedMixedBankRepository::receipt_exists(const std::string& receipt,ReceiptLedger ledger){
    require(hash(receipt),"Mixed bank invalid receipt");
    using L=SqliteOwnedForeignBankRepository::ReceiptLedger;
    if(ledger==ReceiptLedger::Foreign)return foreign_.receipt_exists(receipt,L::Foreign);
    if(ledger==ReceiptLedger::Armor)return foreign_.receipt_exists(receipt,L::Armor);
    if(ledger==ReceiptLedger::Plain)return foreign_.receipt_exists(receipt,L::Plain);
    sqlite_detail::Statement read(db_,"SELECT 1 FROM character_bank_mixed_receipts WHERE receipt=?");read.bind(1,receipt);return read.row()||(ledger==ReceiptLedger::Any&&foreign_.receipt_exists(receipt));
}
void SqliteOwnedMixedBankRepository::verify_snapshot_in_transaction(const Snapshot& expected){
    require(sqlite3_get_autocommit(db_)==0,"Mixed bank proof requires mutation transaction");foreign_.verify_snapshot_in_transaction(expected);
}
SqliteOwnedMixedBankRepository::Plan SqliteOwnedMixedBankRepository::commit(const std::string& receipt,const Request& request,const Prepare& prepare,const Check& check,const std::function<void()>& current){
    static_assert(std::is_nothrow_move_constructible_v<Plan>,"Committed mixed plan must return without allocation exceptions");
    require(hash(receipt)&&bool(prepare)&&sqlite3_get_autocommit(db_)!=0,"Mixed bank preparation/receipt/transaction invalid");auto next=plan(request);const auto before=state(request.expected),after=state(next.after),immutable=immutable_rows(db_,request.expected.base.bag.character,receipt);prepare(next);
    sqlite_detail::Transaction transaction(db_);verify_snapshot_in_transaction(request.expected);require(!receipt_exists(receipt),"Mixed bank duplicate receipt");require(immutable_rows(db_,request.expected.base.bag.character,receipt)==immutable,"Mixed bank immutable prewrite conflict");
    const auto character=request.expected.base.bag.character;
    if(current)current(); // Pure lifecycle check after before-read observers.
    // Both occupied overlays are removed before either scalar is exchanged,
    // so the frozen reverse collision triggers remain authoritative.
    for(const auto slot:{next.source,next.destination}){
        if(const auto* value=row(request.expected.base.armor,slot)){
            sqlite_detail::Statement erase(db_,"DELETE FROM character_bank_armor_metadata WHERE character_id=? AND slot=? AND logical20=? AND revision=? AND origin=? AND provenance=? AND source_sha256=? AND client_sha256=? AND instance_design_id=? AND storage_design_id='CUSTOM-0067'");erase.bind_id(1,character);erase.bind(2,slot);erase.bind_blob(3,value->logical20);erase.bind_id(4,value->revision);erase.bind(5,value->origin);erase.bind(6,value->provenance);erase.bind(7,value->source_sha256);erase.bind(8,value->client_sha256);erase.bind(9,value->instance_design_id);erase.done();require(sqlite3_changes(db_)==1,"Mixed bank armor delete CAS failed");
        }
        if(const auto* value=row(request.expected.foreign,slot)){
            sqlite_detail::Statement erase(db_,"DELETE FROM character_bank_foreign_metadata WHERE character_id=? AND slot=? AND kind=? AND logical20=? AND revision=? AND origin=? AND provenance=? AND source_sha256=? AND client_sha256=? AND instance_design_id=? AND source_family=? AND parsed_sha256=? AND storage_design_id='CUSTOM-0068'");erase.bind_id(1,character);erase.bind(2,slot);erase.bind(3,static_cast<std::uint8_t>(value->kind));erase.bind_blob(4,value->logical20);erase.bind_id(5,value->revision);erase.bind(6,value->origin);erase.bind(7,value->provenance);erase.bind(8,value->source_sha256);erase.bind(9,value->client_sha256);erase.bind(10,value->instance_design_id);erase.bind(11,value->source_family);erase.bind(12,value->parsed_sha256);erase.done();require(sqlite3_changes(db_)==1,"Mixed bank foreign delete CAS failed");
        }
    }
    for(const auto slot:{next.source,next.destination}){
        const auto& old=request.expected.base.vault[slot];const auto& value=next.after.base.vault[slot];sqlite_detail::Statement write(db_,"UPDATE character_bank_item_slots SET item_id=?,count=?,revision=?,source_sha256=? WHERE character_id=? AND slot=? AND item_id=? AND count=? AND revision=? AND source_sha256=? AND item_design_id='CUSTOM-0015' AND design_id='CUSTOM-0065'");write.bind(1,value.item_id);write.bind(2,value.count);write.bind_id(3,value.revision);write.bind(4,value.source_sha256);write.bind_id(5,character);write.bind(6,slot);write.bind(7,old.item_id);write.bind(8,old.count);write.bind_id(9,old.revision);write.bind(10,old.source_sha256);write.done();require(sqlite3_changes(db_)==1,"Mixed bank scalar CAS write failed");
    }
    for(const auto slot:{next.source,next.destination}){
        if(const auto* value=row(next.after.base.armor,slot)){
            sqlite_detail::Statement insert(db_,"INSERT INTO character_bank_armor_metadata VALUES(?,?,?,?,?,?,?,?,?,'CUSTOM-0067')");insert.bind_id(1,character);insert.bind(2,slot);insert.bind_blob(3,value->logical20);insert.bind_id(4,value->revision);insert.bind(5,value->origin);insert.bind(6,value->provenance);insert.bind(7,value->source_sha256);insert.bind(8,value->client_sha256);insert.bind(9,value->instance_design_id);insert.done();require(sqlite3_changes(db_)==1,"Mixed bank armor install failed");
        }
        if(const auto* value=row(next.after.foreign,slot)){
            sqlite_detail::Statement insert(db_,"INSERT INTO character_bank_foreign_metadata VALUES(?,?,?,?,?,?,?,?,?,?,?,?,'CUSTOM-0068')");insert.bind_id(1,character);insert.bind(2,slot);insert.bind(3,static_cast<std::uint8_t>(value->kind));insert.bind_blob(4,value->logical20);insert.bind_id(5,value->revision);insert.bind(6,value->origin);insert.bind(7,value->provenance);insert.bind(8,value->source_sha256);insert.bind(9,value->client_sha256);insert.bind(10,value->instance_design_id);insert.bind(11,value->source_family);insert.bind(12,value->parsed_sha256);insert.done();require(sqlite3_changes(db_)==1,"Mixed bank foreign install failed");
        }
    }
    sqlite_detail::Statement insert(db_,"INSERT INTO character_bank_mixed_receipts VALUES(?,?,?,101,?,?,?,?,?,?,'CUSTOM-0070')");insert.bind(1,receipt);insert.bind_id(2,request.expected.base.bag.account);insert.bind_id(3,character);insert.bind(4,request.page);insert.bind(5,request.source);insert.bind(6,request.destination);insert.bind(7,request.quantity);insert.bind(8,before);insert.bind(9,after);insert.done();require(sqlite3_changes(db_)==1,"Mixed bank receipt insert failed");
    const auto verify=[&]{
        sqlite_detail::Statement read(db_,"SELECT account_id,character_id,operation,page,source,destination,quantity,before_state,after_state,design_id FROM character_bank_mixed_receipts WHERE receipt=?");read.bind(1,receipt);require(read.row()&&read.number<std::uint64_t>(0)==request.expected.base.bag.account&&read.number<std::uint64_t>(1)==character&&read.number<std::uint8_t>(2)==101&&read.number<std::uint8_t>(3)==request.page&&read.number<std::uint8_t>(4)==request.source&&read.number<std::uint8_t>(5)==request.destination&&read.number<std::uint8_t>(6)==request.quantity&&read.text(7)==before&&read.text(8)==after&&read.text(9)==design_id&&!read.row(),"Mixed bank exact receipt readback conflict");
        verify_snapshot_in_transaction(next.after);require(!foreign_.receipt_exists(receipt),"Mixed bank late old-ledger receipt conflict");require(immutable_rows(db_,character,receipt)==immutable,"Mixed bank other-owner/money/receipt history readback conflict");
    };verify();if(check){check(next);verify();}if(current)current();transaction.commit();return next;
}
}
