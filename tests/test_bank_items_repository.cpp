#include "db/SqliteBankItemsRepository.h"
#include "db/SqliteBankRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <stdexcept>
using namespace god2;
namespace {
void require(bool ok,const char* reason) {if(!ok)throw std::runtime_error(reason);}
template<class F>void rejects(F&& f) {
    try {f();}catch(const DatabaseError&) {return;}
    throw std::runtime_error("Expected bank items rejection");
}
std::string dump(sqlite3* db,const std::string& sql) {
    sqlite3_stmt* raw=nullptr;sqlite_detail::check(db,sqlite3_prepare_v2(db,sql.c_str(),-1,&raw,nullptr));
    std::unique_ptr<sqlite3_stmt,decltype(&sqlite3_finalize)> statement(raw,sqlite3_finalize);
    std::string result;
    for(;;) {
        const auto step=sqlite3_step(raw);if(step==SQLITE_DONE)break;
        require(step==SQLITE_ROW,"Raw state query failed");
        for(int c=0;c<sqlite3_column_count(raw);++c) {
            const auto type=sqlite3_column_type(raw,c);
            const auto* bytes=type==SQLITE_BLOB?sqlite3_column_blob(raw,c):sqlite3_column_text(raw,c);
            const auto size=sqlite3_column_bytes(raw,c);
            result+=std::to_string(type)+":"+std::to_string(size)+":";
            if(size)result.append(static_cast<const char*>(bytes),static_cast<std::size_t>(size));
            result+=';';
        }
        result+='\n';
    }
    return result;
}
std::string original_schema(sqlite3* db) {
    return dump(db,"SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE tbl_name NOT LIKE 'character_bank_item_%' ORDER BY type,name");
}
std::string untouched_saves(sqlite3* db,std::uint64_t character) {
    sqlite_detail::Statement tables(db,"SELECT name FROM sqlite_schema WHERE type='table' "
        "AND name NOT LIKE 'character_bank_item_%' ORDER BY name");
    std::string result;
    while(tables.row()) {
        const auto name=tables.text(0);require(name.find('"')==std::string::npos,"Unsafe test table name");
        auto query="SELECT * FROM \""+name+"\"";
        if(name=="diagnostic_inventory_slots")query+=" WHERE character_id<>"+std::to_string(character)+" OR slot>=30";
        result+=name+'\n'+dump(db,query+" ORDER BY rowid");
    }
    return result;
}
std::int64_t receipts(sqlite3* db) {
    sqlite_detail::Statement read(db,"SELECT count(*) FROM character_bank_item_receipts");
    require(read.row(),"Missing receipt count");return read.integer(0);
}
using Snapshot=SqliteBankItemsRepository::Snapshot;
using Totals=std::map<std::pair<std::uint16_t,std::string>,std::uint64_t>;
Totals totals(const Snapshot& snapshot) {
    Totals result;
    const auto add=[&](const auto& cells) {for(const auto& value:cells)if(value.count)result[{value.item_id,value.source_sha256}]+=value.count;};
    add(snapshot.bag);add(snapshot.vault);return result;
}
}
int main() {try {
    sqlite3* raw=nullptr;require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Open failed");
    std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> db(raw,sqlite3_close_v2);
    sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");auto historical=default_sqlite_migrations();while(historical.back().version>42)historical.pop_back();SqliteMigrationManager(raw,std::move(historical)).migrate();
    sqlite_detail::execute(raw,"INSERT INTO accounts(id,username,password_hash) VALUES(1,'a','hash'),(2,'b','hash')");
    SqliteRecoveredCharacterRepository characters(raw);SqliteTradeRepository trades(raw);trades.install_schema();
    SqliteBankRepository money(raw);money.install_schema();
    std::array<std::uint64_t,2> ids{};
    for(unsigned n=0;n<2;++n) {
        std::array<std::uint8_t,40> profile{};profile[0]=static_cast<std::uint8_t>('A'+n);
        ids[n]=characters.create(n+1,profile).id;
        characters.commit_resources(n+1,ids[n],{},{50,120,10,80,0,"CUSTOM-0012"});
        characters.provision_town_reward_slot(n+1,ids[n]);characters.provision_owned_bag(n+1,ids[n]);
        trades.provision_wallet(n+1,ids[n]);money.provision_bank(n+1,ids[n]);
    }
    // Explicit isolated fixture funding only, never a production grant.
    const std::string item_source=SqliteRecoveredCharacterRepository::town_reward_item_source_sha256;
    const auto resources=*characters.load_resources(1,ids[0]);
    characters.commit_inventory_resources(1,ids[0],5,characters.load_inventory_slot(1,ids[0],5),resources,{3107,7,0,item_source},resources);
    sqlite_detail::execute(raw,"UPDATE character_trade_wallets SET amount=123");
    sqlite_detail::execute(raw,"UPDATE character_bank_balances SET amount=456");
    const auto schema=original_schema(raw),saves=untouched_saves(raw,ids[0]);
    const auto total_changes=sqlite3_total_changes(raw);
    SqliteBankItemsRepository items(raw);
    rejects([&]{items.load(1,ids[0]);});
    require(sqlite3_total_changes(raw)==total_changes && original_schema(raw)==schema,"Constructor/load wrote schema or rows");
    sqlite_detail::Statement absent(raw,"SELECT count(*) FROM sqlite_schema WHERE name LIKE 'character_bank_item_%'");
    require(absent.row() && absent.integer(0)==0,"Reader installed schema");
    items.install_schema();items.install_schema();
    require(original_schema(raw)==schema && untouched_saves(raw,ids[0])==saves,"Install changed original schema/history/saves");
    const auto load_changes=sqlite3_total_changes(raw);rejects([&]{items.load(1,ids[0]);});
    require(sqlite3_total_changes(raw)==load_changes,"Reader auto-provisioned vault");
    rejects([&]{items.provision_empty(2,ids[0]);});
    require(items.provision_empty(1,ids[0])==300 && items.provision_empty(2,ids[1])==300,"Incomplete new vault allocation");
    auto initial=items.load(1,ids[0]);const auto unrelated=items.load(2,ids[1]);
    for(const auto& value:initial.vault)require(value==StoredInventorySlot{0,0,1,SqliteBankItemsRepository::empty_source_sha256},"New vault granted items");
    require(items.provision_empty(1,ids[0])==0 && items.load(1,ids[0])==initial,"Provision replaced saved cells");
    // A damaged partial vault is never silently supplemented by provision/load.
    sqlite_detail::Statement remove(raw,"DELETE FROM character_bank_item_slots WHERE character_id=? AND slot=299");
    remove.bind_id(1,ids[0]);remove.done();const auto partial_changes=sqlite3_total_changes(raw);
    rejects([&]{items.provision_empty(1,ids[0]);});rejects([&]{items.load(1,ids[0]);});
    require(sqlite3_total_changes(raw)==partial_changes,"Partial vault was repaired implicitly");
    sqlite_detail::Statement restore(raw,"INSERT INTO character_bank_item_slots "
        "(character_id,slot,item_id,count,revision,source_sha256,item_design_id,design_id) "
        "VALUES(?,299,0,0,1,?,'CUSTOM-0015','CUSTOM-0065')");
    restore.bind_id(1,ids[0]);restore.bind(2,std::string(SqliteBankItemsRepository::empty_source_sha256));restore.done();
    require(items.load(1,ids[0])==initial,"Explicit test-only missing-cell restoration failed");
    using Operation=SqliteBankItemsRepository::Operation;using Request=SqliteBankItemsRepository::Request;
    const Request deposit{initial,Operation::Deposit,5,5,49,3};
    const auto planned=SqliteBankItemsRepository::plan(deposit);
    require(planned.bag[5]==StoredInventorySlot{3107,4,initial.bag[5].revision+1,item_source} &&
        planned.vault[299]==StoredInventorySlot{3107,3,2,item_source} && totals(planned)==totals(initial),"Partial deposit/provenance/conservation failed");
    const auto unchanged=[&] {
        require(items.load(1,ids[0])==initial && items.load(2,ids[1])==unrelated && receipts(raw)==0,"Rejection changed items/receipt/other player");
        require(untouched_saves(raw,ids[0])==saves,"Item transfer changed money or unrelated saved rows");
    };
    for(unsigned mode=0;mode<16;++mode) {
        auto bad=deposit;
        switch(mode) {
        case 0:bad.quantity=0;break;
        case 1:bad.quantity=128;break;
        case 2:bad.quantity=255;break;
        case 3:bad.quantity=8;break;
        case 4:bad.page=6;break;
        case 5:bad.source=30;break;
        case 6:bad.destination=50;break;
        case 7:bad.expected.account=2;break;
        case 8:++bad.expected.bag[29].revision;break;
        case 9:++bad.expected.vault[298].revision;break;
        case 10:++bad.expected.bag[5].revision;break;
        case 11:bad.expected.bag[5].source_sha256=std::string(64,'a');break;
        case 12:bad.source=4;break;
        case 13:bad.operation=static_cast<Operation>(0x66);break;
        case 14:bad.operation=Operation::Withdraw;break;
        case 15:bad.expected.vault[299]={3107,1,1,item_source};break;
        }
        rejects([&]{items.commit(std::string(64,'a'),bad);});unchanged();
    }
    for(const auto receipt:{std::string{},std::string(63,'a'),std::string(64,'A'),std::string(64,'g')}) {
        rejects([&]{items.commit(receipt,deposit);});unchanged();
    }
    // Source is written first. Every destination/receipt/readback fault must
    // roll back both physical cells and even changes to untouched vault cells.
    for(const auto sql:{
        "CREATE TRIGGER fail BEFORE UPDATE ON character_bank_item_slots BEGIN SELECT RAISE(ABORT,'injected second update'); END",
        "CREATE TRIGGER fail BEFORE UPDATE ON character_bank_item_slots BEGIN SELECT RAISE(IGNORE); END",
        "CREATE TRIGGER fail AFTER UPDATE ON diagnostic_inventory_slots BEGIN UPDATE character_bank_item_slots SET revision=revision+1 WHERE character_id=NEW.character_id AND slot=299; END",
        "CREATE TRIGGER fail BEFORE INSERT ON character_bank_item_receipts BEGIN SELECT RAISE(IGNORE); END",
        "CREATE TRIGGER fail AFTER INSERT ON character_bank_item_receipts BEGIN DELETE FROM character_bank_item_receipts WHERE receipt=NEW.receipt; END",
        "CREATE TRIGGER fail AFTER INSERT ON character_bank_item_receipts BEGIN UPDATE character_bank_item_receipts SET after_state='corrupt' WHERE receipt=NEW.receipt; END",
        "CREATE TRIGGER fail AFTER INSERT ON character_bank_item_receipts BEGIN UPDATE character_bank_item_slots SET count=2 WHERE character_id=NEW.character_id AND slot=299; END",
        "CREATE TRIGGER fail AFTER INSERT ON character_bank_item_receipts BEGIN UPDATE diagnostic_inventory_slots SET count=2 WHERE character_id=NEW.character_id AND slot=5; END",
        "CREATE TRIGGER fail AFTER INSERT ON character_bank_item_receipts BEGIN UPDATE character_bank_item_slots SET revision=revision+1 WHERE character_id=NEW.character_id AND slot=298; END"}) {
        sqlite_detail::execute(raw,sql);rejects([&]{items.commit(std::string(64,'b'),deposit);});unchanged();
        sqlite_detail::execute(raw,"DROP TRIGGER fail");
    }
    constexpr auto max_revision=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
    for(unsigned mode=0;mode<5;++mode) {
        auto bad=deposit;
        switch(mode) {
        case 0:bad.expected.bag[5].revision=max_revision;break;
        case 1:bad.expected.vault[299].revision=max_revision;break;
        case 2:bad.expected.bag[29].revision=0;break;
        case 3:bad.expected.vault[298].count=128;bad.expected.vault[298].item_id=3107;break;
        case 4:bad.expected.vault[298].source_sha256="bad";break;
        }
        rejects([&]{SqliteBankItemsRepository::plan(bad);});
    }
    auto boundary=deposit;boundary.expected.bag[5].revision=max_revision-1;boundary.expected.vault[299].revision=max_revision-1;
    const auto last=SqliteBankItemsRepository::plan(boundary);
    require(last.bag[5].revision==max_revision && last.vault[299].revision==max_revision,"Last valid physical revisions rejected");
    const auto committed=items.commit(std::string(64,'c'),deposit);
    require(committed==planned && items.load(1,ids[0])==planned,"Deposit readback differed from plan");
    require(items.provision_empty(1,ids[0])==0 && items.load(1,ids[0])==committed,"Reprovision reset occupied bank");
    rejects([&]{items.commit(std::string(64,'c'),deposit);});rejects([&]{items.commit(std::string(64,'d'),deposit);});
    const Request withdraw{committed,Operation::Withdraw,5,49,6,2};
    rejects([&]{items.commit(std::string(64,'c'),withdraw);});
    auto occupied=withdraw;occupied.destination=5;rejects([&]{items.commit(std::string(64,'d'),occupied);});
    auto bank_range=withdraw;bank_range.source=50;rejects([&]{SqliteBankItemsRepository::plan(bank_range);});
    bank_range=withdraw;bank_range.destination=30;rejects([&]{SqliteBankItemsRepository::plan(bank_range);});
    require(items.load(1,ids[0])==committed && receipts(raw)==1,"Replay/stale/occupied withdrawal changed items");
    const auto withdrawn=items.commit(std::string(64,'d'),withdraw);
    require(withdrawn.bag[6]==StoredInventorySlot{3107,2,initial.bag[6].revision+1,item_source} && withdrawn.vault[299].count==1 &&
        withdrawn.vault[299].revision==3 && totals(withdrawn)==totals(initial),"Partial withdrawal failed");
    const Request whole{withdrawn,Operation::Deposit,5,5,48,4};
    const auto whole_deposit=items.commit(std::string(64,'e'),whole);
    require(!whole_deposit.bag[5].item_id && !whole_deposit.bag[5].count && whole_deposit.bag[5].source_sha256==item_source &&
        whole_deposit.bag[5].revision==withdrawn.bag[5].revision+1 && whole_deposit.vault[298].count==4,"Whole deposit failed");
    const Request move{whole_deposit,Operation::Move,5,48,47,1};
    for(unsigned mode=0;mode<4;++mode) {
        auto bad=move;
        switch(mode) {
        case 0:bad.destination=48;break;
        case 1:bad.quantity=2;break;
        case 2:bad.source=50;break;
        case 3:bad.destination=50;break;
        }
        rejects([&]{SqliteBankItemsRepository::plan(bad);});
    }
    const auto moved=items.commit(std::string(64,'f'),move);
    require(!moved.vault[298].count && !moved.vault[298].item_id && moved.vault[298].revision==whole_deposit.vault[298].revision+1 &&
        moved.vault[297]==StoredInventorySlot{3107,4,2,item_source} && moved.bag==whole_deposit.bag && totals(moved)==totals(initial),"65 whole-cell move/provenance/conservation failed");
    const auto emptied=items.commit(std::string(64,'0'),{moved,Operation::Withdraw,5,47,5,4});
    require(!emptied.vault[297].count && !emptied.vault[297].item_id && emptied.vault[297].revision==3 && emptied.bag[5].count==4 &&
        totals(emptied)==totals(initial),"Whole withdrawal failed");
    require(items.load(2,ids[1])==unrelated && untouched_saves(raw,ids[0])==saves && original_schema(raw)==schema,
        "Successful item transfer changed unrelated player/saves/money/schema/history");
    // Explicit isolated vault fixtures exercise native65 whole-cell exchanges.
    // Unequal revisions belong to the physical slots, never to travelling items.
    const auto seed_vault=[&](std::uint16_t index,const StoredInventorySlot& value) {
        sqlite_detail::Statement write(raw,"UPDATE character_bank_item_slots SET item_id=?,count=?,revision=?,source_sha256=? WHERE character_id=? AND slot=?");
        write.bind(1,value.item_id);write.bind(2,value.count);write.bind_id(3,value.revision);write.bind(4,value.source_sha256);
        write.bind_id(5,ids[0]);write.bind(6,index);write.done();require(sqlite3_changes(raw)==1,"Vault fixture seeding failed");
    };
    const std::string source_a(64,'a'),source_b(64,'b');
    seed_vault(2,{3107,127,7,source_a});seed_vault(3,{3108,11,19,source_b});
    const auto before_swap=items.load(1,ids[0]);
    const Request swap{before_swap,Operation::Move,0,2,3,1};
    const auto expected_swap=SqliteBankItemsRepository::plan(swap);
    require(expected_swap.vault[2]==StoredInventorySlot{3108,11,8,source_b} &&
        expected_swap.vault[3]==StoredInventorySlot{3107,127,20,source_a} &&
        expected_swap.bag==before_swap.bag && totals(expected_swap)==totals(before_swap),
        "Occupied65 must exchange complete items/provenance while preserving physical revisions");
    const auto swap_receipts=receipts(raw);
    const auto swap_unchanged=[&] {
        require(items.load(1,ids[0])==before_swap && receipts(raw)==swap_receipts && items.load(2,ids[1])==unrelated,
            "Rejected occupied65 changed either item, receipt or other player");
        require(untouched_saves(raw,ids[0])==saves && original_schema(raw)==schema,"Occupied65 changed money/saves/schema/history");
    };
    for(unsigned mode=0;mode<6;++mode) {
        auto stale=swap;
        switch(mode) {
        case 0:stale.expected.account=2;break;
        case 1:++stale.expected.vault[2].revision;break;
        case 2:++stale.expected.vault[3].revision;break;
        case 3:++stale.expected.vault[299].revision;break;
        case 4:stale.expected.vault[2].source_sha256=source_b;break;
        case 5:stale.expected.vault[3].count=10;break;
        }
        rejects([&]{items.commit(std::string(64,'2'),stale);});swap_unchanged();
    }
    // Reject the second physical write or damage the receipt/readback after
    // both writes. The first write must not escape the atomic transaction.
    for(const auto sql:{
        "CREATE TRIGGER fail BEFORE UPDATE ON character_bank_item_slots WHEN NEW.slot=3 BEGIN SELECT RAISE(ABORT,'injected swap destination'); END",
        "CREATE TRIGGER fail BEFORE UPDATE ON character_bank_item_slots WHEN NEW.slot=3 BEGIN SELECT RAISE(IGNORE); END",
        "CREATE TRIGGER fail BEFORE INSERT ON character_bank_item_receipts BEGIN SELECT RAISE(ABORT,'injected swap receipt'); END",
        "CREATE TRIGGER fail BEFORE INSERT ON character_bank_item_receipts BEGIN SELECT RAISE(IGNORE); END",
        "CREATE TRIGGER fail AFTER INSERT ON character_bank_item_receipts BEGIN DELETE FROM character_bank_item_receipts WHERE receipt=NEW.receipt; END",
        "CREATE TRIGGER fail AFTER INSERT ON character_bank_item_receipts BEGIN UPDATE character_bank_item_receipts SET after_state='corrupt' WHERE receipt=NEW.receipt; END",
        "CREATE TRIGGER fail AFTER INSERT ON character_bank_item_receipts BEGIN UPDATE character_bank_item_slots SET revision=revision+1 WHERE character_id=NEW.character_id AND slot=299; END"}) {
        sqlite_detail::execute(raw,sql);rejects([&]{items.commit(std::string(64,'2'),swap);});swap_unchanged();
        sqlite_detail::execute(raw,"DROP TRIGGER fail");
    }
    auto swap_boundary=swap;swap_boundary.expected.vault[2].revision=max_revision-1;swap_boundary.expected.vault[3].revision=max_revision-1;
    const auto swap_last=SqliteBankItemsRepository::plan(swap_boundary);
    require(swap_last.vault[2].revision==max_revision && swap_last.vault[3].revision==max_revision &&
        swap_last.vault[2].count==11 && swap_last.vault[3].count==127,"Occupied65 last physical revision/count127 boundary failed");
    for(const auto index:{2,3}) {
        auto exhausted=swap;exhausted.expected.vault[index].revision=max_revision;
        rejects([&]{SqliteBankItemsRepository::plan(exhausted);});
    }
    const auto swapped=items.commit(std::string(64,'2'),swap);
    require(swapped==expected_swap && items.load(1,ids[0])==expected_swap && receipts(raw)==swap_receipts+1,
        "Occupied65 complete committed readback failed");
    rejects([&]{items.commit(std::string(64,'2'),{swapped,Operation::Move,0,2,3,1});});
    rejects([&]{items.commit(std::string(64,'3'),swap);});
    require(items.load(1,ids[0])==swapped && receipts(raw)==swap_receipts+1,"Occupied65 duplicate/stale replay mutated state");
    sqlite_detail::Statement swap_receipt(raw,"SELECT operation,page,source,destination,quantity,before_state,after_state FROM character_bank_item_receipts WHERE receipt=?");
    swap_receipt.bind(1,std::string(64,'2'));
    require(swap_receipt.row() && swap_receipt.integer(0)==101 && swap_receipt.integer(1)==0 && swap_receipt.integer(2)==2 &&
        swap_receipt.integer(3)==3 && swap_receipt.integer(4)==1 &&
        swap_receipt.text(5)=="1:2:3107:127:7:"+source_a+":CUSTOM-0015;1:3:3108:11:19:"+source_b+":CUSTOM-0015;" &&
        swap_receipt.text(6)=="1:2:3108:11:8:"+source_b+":CUSTOM-0015;1:3:3107:127:20:"+source_a+":CUSTOM-0015;",
        "Occupied65 receipt lost marker, physical revisions or full item provenance");
    // Same ID/provenance is still a swap, not stack merging, even at127.
    seed_vault(4,{3107,127,3,item_source});seed_vault(5,{3107,2,8,item_source});
    const auto same_id_before=items.load(1,ids[0]);
    const auto same_id_after=items.commit(std::string(64,'3'),{same_id_before,Operation::Move,0,4,5,1});
    require(same_id_after.vault[4]==StoredInventorySlot{3107,2,4,item_source} &&
        same_id_after.vault[5]==StoredInventorySlot{3107,127,9,item_source} && totals(same_id_after)==totals(same_id_before),
        "Occupied65 merged same-ID stacks instead of exchanging whole cells");
    require(items.load(2,ids[1])==unrelated && untouched_saves(raw,ids[0])==saves && original_schema(raw)==schema,
        "Successful occupied65 changed other player, money, unrelated saves or schema/history");
    rejects([&]{sqlite_detail::execute(raw,"UPDATE character_bank_item_slots SET design_id='CUSTOM-0000'");});
    rejects([&]{sqlite_detail::execute(raw,"UPDATE character_bank_item_slots SET item_design_id='CUSTOM-0000'");});
    sqlite_detail::Statement provenance(raw,"SELECT count(*) FROM character_bank_item_slots WHERE design_id='CUSTOM-0065' AND item_design_id='CUSTOM-0015'");
    require(provenance.row() && provenance.integer(0)==600,"Bank item provenance missing");
    const auto active_resources=*characters.load_resources(1,ids[0]);characters.reserve_battle(1,ids[0],active_resources);
    const auto pending_saves=untouched_saves(raw,ids[0]);const auto pending_items=items.load(1,ids[0]);const auto before_receipts=receipts(raw);
    rejects([&]{items.commit(std::string(64,'1'),{pending_items,Operation::Deposit,0,5,6,1});});
    rejects([&]{items.commit(std::string(64,'4'),{pending_items,Operation::Move,0,2,3,1});});
    require(items.load(1,ids[0])==pending_items && receipts(raw)==before_receipts && untouched_saves(raw,ids[0])==pending_saves,
        "Pending battle rejection changed items/receipt/saves");
    std::cout<<"Bank items owned330-slot CAS, scalar conservation, whole/partial transfers, native65 whole-cell move/swap, provenance, boundaries, replay, rollback and money isolation passed; live acceptance OPEN\n";
}catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}}
