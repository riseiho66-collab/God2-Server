#include "db/SqliteTradeRepository.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <limits>
#include <set>
#include <type_traits>

namespace god2 {
namespace {
constexpr auto max_revision=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
void require(bool valid,const char* message) {if(!valid)throw DatabaseError(message);}
void owner(sqlite3* db,std::uint64_t account,std::uint64_t character) {
    require(account && character,"Trade owner missing");
    sqlite_detail::Statement owned(db,"SELECT 1 FROM recovered_characters WHERE id=? AND account_id=?");
    owned.bind_id(1,character);owned.bind_id(2,account);require(owned.row(),"Trade ownership rejected");
}
void valid_slot(const StoredInventorySlot& slot) {
    require(slot.count<=127 && (slot.count==0)==(slot.item_id==0) && slot.revision && slot.revision<=max_revision &&
        slot.source_sha256.size()==64 && slot.source_sha256.find_first_not_of("0123456789abcdef")==std::string::npos,
        "Trade bag snapshot invalid");
}
}
void SqliteTradeRepository::install_schema() {
    sqlite_detail::Transaction transaction(db_);
    sqlite_detail::execute(db_,R"(
CREATE TABLE IF NOT EXISTS character_trade_wallets(
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) ON DELETE CASCADE,
 amount INTEGER NOT NULL CHECK(typeof(amount)='integer' AND amount BETWEEN 0 AND 4294967295),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0063'));
CREATE TABLE IF NOT EXISTS character_trade_receipts(
 receipt TEXT PRIMARY KEY CHECK(length(receipt)=64 AND receipt NOT GLOB '*[^0-9a-f]*'),
 first_character INTEGER NOT NULL REFERENCES recovered_characters(id) ON DELETE CASCADE,
 second_character INTEGER NOT NULL REFERENCES recovered_characters(id) ON DELETE CASCADE,
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0063'),
 CHECK(first_character<>second_character));
)");
    transaction.commit();
}
SqliteTradeRepository::Wallet SqliteTradeRepository::provision_wallet(std::uint64_t account,std::uint64_t character) {
    sqlite_detail::Transaction transaction(db_);owner(db_,account,character);
    sqlite_detail::Statement insert(db_,"INSERT INTO character_trade_wallets(character_id,amount,revision,design_id) "
        "VALUES(?,0,1,'CUSTOM-0063') ON CONFLICT(character_id) DO NOTHING");
    insert.bind_id(1,character);insert.done();
    sqlite_detail::Statement read(db_,"SELECT amount,revision,design_id FROM character_trade_wallets WHERE character_id=?");
    read.bind_id(1,character);require(read.row() && read.text(2)=="CUSTOM-0063","Trade wallet invalid");
    Wallet result{read.number<std::uint64_t>(0),read.number<std::uint64_t>(1)};
    require(ExtendedCoinAmount::from(result.amount).has_value() && result.revision && result.revision<=max_revision,"Trade wallet amount/revision invalid");
    transaction.commit();return result;
}
std::optional<SqliteTradeRepository::Wallet> SqliteTradeRepository::load_wallet(std::uint64_t account,std::uint64_t character) {
    owner(db_,account,character);
    sqlite_detail::Statement wallet(db_,"SELECT amount,revision,design_id FROM character_trade_wallets WHERE character_id=?");
    wallet.bind_id(1,character);if(!wallet.row())return {};
    require(wallet.text(2)=="CUSTOM-0063","Trade wallet invalid");
    Wallet result{wallet.number<std::uint64_t>(0),wallet.number<std::uint64_t>(1)};
    require(ExtendedCoinAmount::from(result.amount).has_value() && result.revision && result.revision<=max_revision,"Trade wallet amount/revision invalid");return result;
}
SqliteTradeRepository::Snapshot SqliteTradeRepository::load(std::uint64_t account,std::uint64_t character) {
    Snapshot result{};result.account=account;result.character=character;
    const auto wallet=load_wallet(account,character);require(wallet.has_value(),"Trade wallet unavailable");result.wallet=*wallet;
    SqliteRecoveredCharacterRepository inventory(db_);
    for(std::uint8_t slot=0;slot<30;++slot) {
        const auto saved=inventory.load_inventory_slot(account,character,slot);require(saved.has_value(),"Trade bag capacity unallocated");
        valid_slot(*saved);result.bag[slot]=*saved;
    }
    return result;
}
SqliteTradeRepository::Settlement SqliteTradeRepository::plan(const std::array<Side,2>& sides) {
    require(sides[0].expected.character && sides[1].expected.character &&
        sides[0].expected.character!=sides[1].expected.character,"Trade participants invalid");
    Settlement result{{sides[0].expected,sides[1].expected}};
    std::array<std::vector<StoredInventorySlot>,2> outgoing;
    for(const auto& side:sides)
        require(ExtendedCoinAmount::from(side.expected.wallet.amount).has_value() &&
            ExtendedCoinAmount::from(side.money).has_value() && side.money<=side.expected.wallet.amount,
            "Trade wallet/offer outside owner coin domain");
    for(std::size_t n=0;n<2;++n) {
        const auto& source=sides[n];auto& next=result.sides[n];
        require(source.expected.account && source.items.size()<=8,"Trade offer invalid");
        require(next.wallet.revision && next.wallet.revision<max_revision && source.money<=next.wallet.amount,"Trade wallet insufficient");
        for(const auto& slot:next.bag)valid_slot(slot);
        std::set<std::uint8_t> used;
        for(const auto& offer:source.items) {
            require(offer.slot<30 && used.insert(offer.slot).second,"Duplicate or reserved trade source slot");
            auto& slot=next.bag[offer.slot];require(offer.quantity && offer.quantity<=slot.count,"Trade quantity invalid");
            auto transferred=slot;transferred.count=offer.quantity;outgoing[n].push_back(std::move(transferred));
            slot.count=static_cast<std::uint8_t>(slot.count-offer.quantity);if(!slot.count)slot.item_id=0;
        }
        const auto amount=ExtendedCoinAmount::exchange(next.wallet.amount,source.money,sides[1-n].money);
        require(amount.has_value(),"Trade owner coin cap/insufficient balance");next.wallet.amount=amount->value();
    }
    for(std::size_t n=0;n<2;++n) {
        auto& next=result.sides[n];
        for(const auto& transferred:outgoing[1-n]) {
            const auto empty=std::find_if(next.bag.begin(),next.bag.end(),[](const auto& slot){return !slot.count;});
            require(empty!=next.bag.end(),"Trade destination capacity insufficient");
            const auto revision=empty->revision;*empty=transferred;empty->revision=revision;
        }
        for(std::size_t slot=0;slot<30;++slot)if(next.bag[slot]!=sides[n].expected.bag[slot]) {
            require(next.bag[slot].revision<max_revision,"Trade bag revision exhausted");++next.bag[slot].revision;
        }
        if(next.wallet.amount!=sides[n].expected.wallet.amount)++next.wallet.revision;
    }
    require(result.sides[0].wallet.amount+result.sides[1].wallet.amount==
        sides[0].expected.wallet.amount+sides[1].expected.wallet.amount,"Trade coin conservation failed");
    return result;
}
SqliteTradeRepository::CommitProof SqliteTradeRepository::prepare_proof(const std::array<Snapshot,2>& before,const Settlement& after,const PrepareProof& override_factory) const {
    const auto& factory=override_factory?override_factory:proof_;if(!factory)return {};
    auto proof=factory(before,after);require(bool(proof.before_write)&&bool(proof.after_write),"Trade requires paired transaction proof checks");return proof;
}
SqliteTradeRepository::Settlement SqliteTradeRepository::commit(const std::string& receipt,const std::array<Side,2>& sides,const std::optional<CommitProof>& prepared) {
    require(receipt.size()==64 && receipt.find_first_not_of("0123456789abcdef")==std::string::npos,"Trade receipt invalid");
    static_assert(std::is_nothrow_move_constructible_v<Settlement>,"Committed settlement must return without allocation or exceptions");
    auto result=plan(sides);
    const auto proof=prepared?*prepared:prepare_proof({sides[0].expected,sides[1].expected},result);
    require(bool(proof.before_write)==bool(proof.after_write),"Trade transaction proof incomplete");
    sqlite_detail::Transaction transaction(db_);
    if(proof.before_write)proof.before_write();
    sqlite_detail::Statement duplicate(db_,"SELECT 1 FROM character_trade_receipts WHERE receipt=?");
    duplicate.bind(1,receipt);require(!duplicate.row(),"Trade settlement already committed");
    for(std::size_t n=0;n<2;++n) {
        const auto& expected=sides[n].expected;require(load(expected.account,expected.character)==expected,"Trade snapshot conflict");
        sqlite_detail::Statement battle(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s "
            "ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
        battle.bind_id(1,expected.character);require(!battle.row(),"Trade during pending battle");
    }
    for(std::size_t n=0;n<2;++n) {
        const auto& expected=sides[n].expected;const auto& next=result.sides[n];
        for(std::uint8_t slot=0;slot<30;++slot)if(next.bag[slot]!=expected.bag[slot]) {
            sqlite_detail::Statement update(db_,"UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=?,source_sha256=? "
                "WHERE character_id=? AND slot=? AND revision=?");
            update.bind(1,next.bag[slot].item_id);update.bind(2,next.bag[slot].count);update.bind_id(3,next.bag[slot].revision);
            update.bind(4,next.bag[slot].source_sha256);update.bind_id(5,next.character);update.bind(6,slot);
            update.bind_id(7,expected.bag[slot].revision);update.done();require(sqlite3_changes(db_)==1,"Trade bag write rejected");
        }
        if(next.wallet!=expected.wallet) {
            sqlite_detail::Statement update(db_,"UPDATE character_trade_wallets SET amount=?,revision=? WHERE character_id=? AND revision=? AND amount=? AND design_id='CUSTOM-0063'");
            update.bind(1,next.wallet.amount);update.bind_id(2,next.wallet.revision);update.bind_id(3,next.character);
            update.bind_id(4,expected.wallet.revision);update.bind(5,expected.wallet.amount);update.done();require(sqlite3_changes(db_)==1,"Trade wallet write rejected");
        }
    }
    sqlite_detail::Statement insert(db_,"INSERT INTO character_trade_receipts(receipt,first_character,second_character,design_id) VALUES(?,?,?,'CUSTOM-0063')");
    insert.bind(1,receipt);insert.bind_id(2,result.sides[0].character);insert.bind_id(3,result.sides[1].character);insert.done();
    require(sqlite3_changes(db_)==1,"Trade receipt write rejected");
    const auto verify=[&]{sqlite_detail::Statement recorded(db_,"SELECT first_character,second_character,design_id FROM character_trade_receipts WHERE receipt=?");
    recorded.bind(1,receipt);require(recorded.row() && recorded.number<std::uint64_t>(0)==result.sides[0].character &&
        recorded.number<std::uint64_t>(1)==result.sides[1].character && recorded.text(2)=="CUSTOM-0063","Trade receipt readback mismatch");
    for(const auto& next:result.sides)require(load(next.account,next.character)==next,"Trade readback mismatch");
    };verify();if(proof.after_write){proof.after_write();verify();}
    if(proof.current){const auto changes=sqlite3_total_changes64(db_);const bool valid=proof.current();require(valid&&sqlite3_get_autocommit(db_)==0&&sqlite3_total_changes64(db_)==changes,"Trade final pure current retired or mutated transaction");}
    transaction.commit();return result;
}
}
