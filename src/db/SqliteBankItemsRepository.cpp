#include "db/SqliteBankItemsRepository.h"
#include "db/SqliteSupport.h"
#include <limits>
#include <utility>

namespace god2 {
namespace {
constexpr auto max_revision=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
void require(bool valid,const char* reason) {if(!valid)throw DatabaseError(reason);}
struct ReadScope {
    sqlite3* db;bool owns,finished=false;
    explicit ReadScope(sqlite3* value):db(value),owns(sqlite3_get_autocommit(value)!=0){if(owns)sqlite_detail::execute(db,"BEGIN");}
    ~ReadScope(){if(owns&&!finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){if(owns)sqlite_detail::execute(db,"COMMIT");finished=true;}
};
void owner(sqlite3* db,std::uint64_t account,std::uint64_t character) {
    require(account && character,"Bank items owner missing");
    sqlite_detail::Statement read(db,"SELECT 1 FROM recovered_characters WHERE id=? AND account_id=?");
    read.bind_id(1,character);read.bind_id(2,account);require(read.row(),"Bank items ownership rejected");
}
void no_battle(sqlite3* db,std::uint64_t character) {
    sqlite_detail::Statement read(db,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s "
        "ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
    read.bind_id(1,character);require(!read.row(),"Bank items during pending battle");
}
void valid(const StoredInventorySlot& slot) {
    require(slot.count<=127 && (slot.count==0)==(slot.item_id==0) && slot.revision && slot.revision<=max_revision &&
        slot.source_sha256.size()==64 && slot.source_sha256.find_first_not_of("0123456789abcdef")==std::string::npos,
        "Bank item slot invalid");
}
template<std::size_t N>std::array<StoredInventorySlot,N> read_slots(sqlite3* db,std::uint64_t character,bool vault) {
    std::array<StoredInventorySlot,N> result{};
    sqlite_detail::Statement read(db,vault?
        "SELECT slot,item_id,count,revision,source_sha256,design_id,item_design_id FROM character_bank_item_slots WHERE character_id=? ORDER BY slot":
        "SELECT slot,item_id,count,revision,source_sha256,design_id,design_id FROM diagnostic_inventory_slots WHERE character_id=? AND slot<30 ORDER BY slot");
    read.bind_id(1,character);std::size_t index=0;
    while(read.row()) {
        require(index<N && read.number<std::uint16_t>(0)==index,"Bank item capacity incomplete or invalid");
        require(read.text(5)==(vault?"CUSTOM-0065":"CUSTOM-0015") && read.text(6)=="CUSTOM-0015","Bank item provenance invalid");
        auto& slot=result[index++];slot={read.number<std::uint16_t>(1),read.number<std::uint8_t>(2),read.number<std::uint64_t>(3),read.text(4)};
        valid(slot);
    }
    require(index==N,"Bank item capacity unallocated");return result;
}
struct Cell {bool vault{};std::size_t index{};};
std::array<Cell,2> cells(const SqliteBankItemsRepository::Request& request) {
    using O=SqliteBankItemsRepository::Operation;
    require(request.page<6 && request.quantity && request.quantity<=127,"Bank item page/quantity invalid");
    const auto offset=std::size_t{request.page}*50;
    if(request.operation==O::Deposit) {
        require(request.source<30 && request.destination<50,"Bank deposit slot invalid");
        return {Cell{false,request.source},Cell{true,offset+request.destination}};
    }
    if(request.operation==O::Withdraw) {
        require(request.source<50 && request.destination<30,"Bank withdrawal slot invalid");
        return {Cell{true,offset+request.source},Cell{false,request.destination}};
    }
    require(request.operation==O::Move && request.source<50 && request.destination<50 &&
        request.source!=request.destination && request.quantity==1,"Bank move invalid");
    return {Cell{true,offset+request.source},Cell{true,offset+request.destination}};
}
StoredInventorySlot& slot(SqliteBankItemsRepository::Snapshot& snapshot,const Cell& cell) {
    return cell.vault?snapshot.vault[cell.index]:snapshot.bag[cell.index];
}
const StoredInventorySlot& slot(const SqliteBankItemsRepository::Snapshot& snapshot,const Cell& cell) {
    return cell.vault?snapshot.vault[cell.index]:snapshot.bag[cell.index];
}
std::string recorded_state(const SqliteBankItemsRepository::Snapshot& snapshot,const std::array<Cell,2>& changed) {
    std::string result;
    for(const auto& cell:changed) {
        const auto& value=slot(snapshot,cell);
        result+=std::to_string(cell.vault)+":"+std::to_string(cell.index)+":"+std::to_string(value.item_id)+":"+
            std::to_string(value.count)+":"+std::to_string(value.revision)+":"+value.source_sha256+":CUSTOM-0015;";
    }
    return result;
}
}
void SqliteBankItemsRepository::install_schema() {
    sqlite_detail::Transaction transaction(db_);
    sqlite_detail::execute(db_,R"(
CREATE TABLE IF NOT EXISTS character_bank_item_slots(
 character_id INTEGER NOT NULL REFERENCES recovered_characters(id) ON DELETE CASCADE,
 slot INTEGER NOT NULL CHECK(typeof(slot)='integer' AND slot BETWEEN 0 AND 299),
 item_id INTEGER NOT NULL CHECK(typeof(item_id)='integer' AND item_id BETWEEN 0 AND 65535),
 count INTEGER NOT NULL CHECK(typeof(count)='integer' AND count BETWEEN 0 AND 127),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64 AND source_sha256 NOT GLOB '*[^0-9a-f]*'),
 item_design_id TEXT NOT NULL CHECK(item_design_id='CUSTOM-0015'),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0065'),
 CHECK((count=0 AND item_id=0) OR (count>0 AND item_id>0)),
 PRIMARY KEY(character_id,slot));
CREATE TABLE IF NOT EXISTS character_bank_item_receipts(
 receipt TEXT PRIMARY KEY CHECK(length(receipt)=64 AND receipt NOT GLOB '*[^0-9a-f]*'),
 account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
 character_id INTEGER NOT NULL REFERENCES recovered_characters(id) ON DELETE CASCADE,
 operation INTEGER NOT NULL CHECK(operation IN (99,100,101)),
 page INTEGER NOT NULL CHECK(page BETWEEN 0 AND 5),
 source INTEGER NOT NULL CHECK(source BETWEEN 0 AND 49),
 destination INTEGER NOT NULL CHECK(destination BETWEEN 0 AND 49),
 quantity INTEGER NOT NULL CHECK(quantity BETWEEN 1 AND 127),
 before_state TEXT NOT NULL CHECK(length(before_state)>0),
 after_state TEXT NOT NULL CHECK(length(after_state)>0),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0065'));
)");transaction.commit();
}
std::size_t SqliteBankItemsRepository::provision_empty(std::uint64_t account,std::uint64_t character) {
    sqlite_detail::Transaction transaction(db_);owner(db_,account,character);
    sqlite_detail::Statement count(db_,"SELECT count(*) FROM character_bank_item_slots WHERE character_id=?");
    count.bind_id(1,character);require(count.row(),"Bank item allocation query missing");
    if(count.integer(0)) {
        read_slots<vault_size>(db_,character,true);transaction.commit();return 0;
    }
    no_battle(db_,character);
    for(std::size_t index=0;index<vault_size;++index) {
        sqlite_detail::Statement insert(db_,"INSERT INTO character_bank_item_slots "
            "(character_id,slot,item_id,count,revision,source_sha256,item_design_id,design_id) "
            "VALUES(?,?,0,0,1,?,'CUSTOM-0015','CUSTOM-0065')");
        insert.bind_id(1,character);insert.bind(2,static_cast<std::int64_t>(index));insert.bind(3,std::string(empty_source_sha256));
        insert.done();require(sqlite3_changes(db_)==1,"Bank empty item write rejected");
    }
    const auto actual=read_slots<vault_size>(db_,character,true);
    for(const auto& value:actual)require(value==BankSlot{0,0,1,empty_source_sha256},"Bank empty item readback mismatch");
    transaction.commit();return vault_size;
}
SqliteBankItemsRepository::Snapshot SqliteBankItemsRepository::load(std::uint64_t account,std::uint64_t character) {
    ReadScope scope(db_);
    owner(db_,account,character);
    Snapshot snapshot{account,character,read_slots<bag_size>(db_,character,false),read_slots<vault_size>(db_,character,true)};
    scope.finish();return snapshot;
}
SqliteBankItemsRepository::Snapshot SqliteBankItemsRepository::plan(const Request& request) {
    require(request.expected.account && request.expected.account<=max_revision && request.expected.character &&
        request.expected.character<=max_revision,"Bank item owner invalid");
    for(const auto& value:request.expected.bag)valid(value);
    for(const auto& value:request.expected.vault)valid(value);
    const auto changed=cells(request);auto next=request.expected;
    auto& from=slot(next,changed[0]);auto& to=slot(next,changed[1]);
    require(from.count && (request.operation==Operation::Move || !to.count) &&
        from.revision<max_revision && to.revision<max_revision,
        "Bank item source/destination/revision invalid");
    if(request.operation==Operation::Move && to.count) {
        const auto source_revision=from.revision,destination_revision=to.revision;
        auto source=from;from=to;to=std::move(source);
        from.revision=source_revision+1;to.revision=destination_revision+1;
        return next;
    }
    const auto quantity=request.operation==Operation::Move?from.count:request.quantity;
    require(quantity<=from.count,"Bank item source quantity insufficient");
    const auto destination_revision=to.revision;
    to=from;to.count=quantity;to.revision=destination_revision+1;
    from.count=static_cast<std::uint8_t>(from.count-quantity);if(!from.count)from.item_id=0;
    ++from.revision;return next;
}
SqliteBankItemsRepository::CommitProof SqliteBankItemsRepository::prepare_proof(const Snapshot& before,const Snapshot& after,const PrepareProof& override_factory) const {
    const auto& factory=override_factory?override_factory:proof_;if(!factory)return {};
    auto proof=factory(before,after);require(bool(proof.before_write)&&bool(proof.after_write),"Bank items require paired transaction proof checks");return proof;
}
SqliteBankItemsRepository::Snapshot SqliteBankItemsRepository::commit(const std::string& server_receipt,const Request& request,const std::optional<CommitProof>& prepared) {
    require(server_receipt.size()==64 && server_receipt.find_first_not_of("0123456789abcdef")==std::string::npos,"Bank item receipt invalid");
    auto next=plan(request);const auto changed=cells(request);
    const auto before=recorded_state(request.expected,changed),after=recorded_state(next,changed);
    const auto proof=prepared?*prepared:prepare_proof(request.expected,next);require(bool(proof.before_write)==bool(proof.after_write),"Bank item transaction proof incomplete");
    sqlite_detail::Transaction transaction(db_);
    if(proof.before_write)proof.before_write();
    sqlite_detail::Statement duplicate(db_,"SELECT 1 FROM character_bank_item_receipts WHERE receipt=?");
    duplicate.bind(1,server_receipt);require(!duplicate.row(),"Bank item transfer already committed");
    require(load(next.account,next.character)==request.expected,"Bank item snapshot conflict");no_battle(db_,next.character);
    for(const auto& cell:changed) {
        const auto& expected=slot(request.expected,cell);const auto& value=slot(next,cell);
        sqlite_detail::Statement write(db_,cell.vault?
            "UPDATE character_bank_item_slots SET item_id=?,count=?,revision=?,source_sha256=? WHERE character_id=? AND slot=? "
            "AND revision=? AND item_id=? AND count=? AND source_sha256=? AND design_id='CUSTOM-0065' AND item_design_id='CUSTOM-0015'":
            "UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=?,source_sha256=? WHERE character_id=? AND slot=? "
            "AND revision=? AND item_id=? AND count=? AND source_sha256=? AND design_id='CUSTOM-0015'");
        write.bind(1,value.item_id);write.bind(2,value.count);write.bind_id(3,value.revision);write.bind(4,value.source_sha256);
        write.bind_id(5,next.character);write.bind(6,static_cast<std::int64_t>(cell.index));write.bind_id(7,expected.revision);
        write.bind(8,expected.item_id);write.bind(9,expected.count);write.bind(10,expected.source_sha256);write.done();
        require(sqlite3_changes(db_)==1,"Bank item slot write rejected");
    }
    sqlite_detail::Statement insert(db_,"INSERT INTO character_bank_item_receipts "
        "(receipt,account_id,character_id,operation,page,source,destination,quantity,before_state,after_state,design_id) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,'CUSTOM-0065')");
    insert.bind(1,server_receipt);insert.bind_id(2,next.account);insert.bind_id(3,next.character);
    insert.bind(4,static_cast<std::uint8_t>(request.operation));insert.bind(5,request.page);insert.bind(6,request.source);
    insert.bind(7,request.destination);insert.bind(8,request.quantity);insert.bind(9,before);insert.bind(10,after);
    insert.done();require(sqlite3_changes(db_)==1,"Bank item receipt write rejected");
    const auto verify=[&]{sqlite_detail::Statement read(db_,"SELECT account_id,character_id,operation,page,source,destination,quantity,before_state,after_state,design_id "
        "FROM character_bank_item_receipts WHERE receipt=?");read.bind(1,server_receipt);
    require(read.row() && read.number<std::uint64_t>(0)==next.account && read.number<std::uint64_t>(1)==next.character &&
        read.number<std::uint8_t>(2)==static_cast<std::uint8_t>(request.operation) && read.number<std::uint8_t>(3)==request.page &&
        read.number<std::uint8_t>(4)==request.source && read.number<std::uint8_t>(5)==request.destination &&
        read.number<std::uint8_t>(6)==request.quantity && read.text(7)==before && read.text(8)==after && read.text(9)=="CUSTOM-0065",
        "Bank item receipt readback mismatch");
    require(load(next.account,next.character)==next,"Bank item complete readback mismatch");};verify();if(proof.after_write){proof.after_write();verify();}transaction.commit();return next;
}
}
