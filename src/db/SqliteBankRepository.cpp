#include "db/SqliteBankRepository.h"
#include "db/SqliteSupport.h"
#include <limits>

namespace god2 {
namespace {
constexpr auto max_revision=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
void require(bool valid,const char* message) {if(!valid)throw DatabaseError(message);}
void owner(sqlite3* db,std::uint64_t account,std::uint64_t character) {
    require(account && character,"Bank owner missing");
    sqlite_detail::Statement owned(db,"SELECT 1 FROM recovered_characters WHERE id=? AND account_id=?");
    owned.bind_id(1,character);owned.bind_id(2,account);require(owned.row(),"Bank ownership rejected");
}
void valid_bank(const SqliteBankRepository::Balance& bank) {
    require(bank.amount<=SqliteBankRepository::bank_cap && bank.revision && bank.revision<=max_revision,
        "Bank balance invalid");
}
}
void SqliteBankRepository::install_schema() {
    sqlite_detail::Transaction transaction(db_);
    sqlite_detail::execute(db_,R"(
CREATE TABLE IF NOT EXISTS character_bank_balances(
 character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id) ON DELETE CASCADE,
 amount INTEGER NOT NULL CHECK(typeof(amount)='integer' AND amount BETWEEN 0 AND 500000000),
 revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>0),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0064'));
CREATE TABLE IF NOT EXISTS character_bank_receipts(
 receipt TEXT PRIMARY KEY CHECK(length(receipt)=64 AND receipt NOT GLOB '*[^0-9a-f]*'),
 account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
 character_id INTEGER NOT NULL REFERENCES recovered_characters(id) ON DELETE CASCADE,
 operation INTEGER NOT NULL CHECK(operation IN (61,62)),
 amount INTEGER NOT NULL CHECK(typeof(amount)='integer' AND amount BETWEEN 1 AND 2147483647),
 wallet_amount INTEGER NOT NULL CHECK(typeof(wallet_amount)='integer' AND wallet_amount BETWEEN 0 AND 4294967295),
 wallet_revision INTEGER NOT NULL CHECK(typeof(wallet_revision)='integer' AND wallet_revision>0),
 bank_amount INTEGER NOT NULL CHECK(typeof(bank_amount)='integer' AND bank_amount BETWEEN 0 AND 500000000),
 bank_revision INTEGER NOT NULL CHECK(typeof(bank_revision)='integer' AND bank_revision>0),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0064'));
)");
    transaction.commit();
}
SqliteBankRepository::Balance SqliteBankRepository::provision_bank(std::uint64_t account,std::uint64_t character) {
    sqlite_detail::Transaction transaction(db_);owner(db_,account,character);
    sqlite_detail::Statement insert(db_,"INSERT INTO character_bank_balances(character_id,amount,revision,design_id) "
        "VALUES(?,0,1,'CUSTOM-0064') ON CONFLICT(character_id) DO NOTHING");
    insert.bind_id(1,character);insert.done();
    const auto result=load_bank(account,character);require(result.has_value(),"Bank provision readback missing");
    transaction.commit();return *result;
}
std::optional<SqliteBankRepository::Balance> SqliteBankRepository::load_bank(std::uint64_t account,std::uint64_t character) {
    owner(db_,account,character);
    sqlite_detail::Statement read(db_,"SELECT amount,revision,design_id FROM character_bank_balances WHERE character_id=?");
    read.bind_id(1,character);if(!read.row())return {};
    require(read.text(2)=="CUSTOM-0064","Bank provenance invalid");
    Balance result{read.number<std::uint32_t>(0),read.number<std::uint64_t>(1)};valid_bank(result);return result;
}
SqliteBankRepository::Snapshot SqliteBankRepository::load(std::uint64_t account,std::uint64_t character) {
    Snapshot result{};result.account=account;result.character=character;
    const auto bank=load_bank(account,character);require(bank.has_value(),"Bank balance unavailable");result.bank=*bank;
    SqliteTradeRepository trades(db_);const auto wallet=trades.load_wallet(account,character);
    require(wallet.has_value(),"Bank purse unavailable");result.wallet=*wallet;return result;
}
SqliteBankRepository::Snapshot SqliteBankRepository::plan(const Request& request) {
    auto result=request.expected;
    require(result.account && result.account<=max_revision && result.character && result.character<=max_revision,"Bank owner invalid");
    valid_bank(result.bank);
    require(ExtendedCoinAmount::from(result.wallet.amount).has_value(),"Bank purse outside owner coin domain");
    require(result.bank.revision<max_revision && result.wallet.revision && result.wallet.revision<max_revision,"Bank revision exhausted");
    require(request.amount && request.amount<=static_cast<std::uint32_t>(std::numeric_limits<std::int32_t>::max()),"Bank native amount invalid");
    if(request.operation==Operation::Deposit) {
        require(request.amount<=result.wallet.amount,"Bank purse insufficient");
        const auto total=std::uint64_t{result.bank.amount}+request.amount;
        require(total<=bank_cap,"Bank capacity exceeded");
        const auto purse=ExtendedCoinAmount::exchange(result.wallet.amount,request.amount,0);
        require(purse.has_value(),"Bank purse debit invalid");
        result.wallet.amount=purse->value();result.bank.amount=static_cast<std::uint32_t>(total);
    } else if(request.operation==Operation::Withdraw) {
        require(request.amount<=result.bank.amount,"Bank funds insufficient");
        const auto purse=ExtendedCoinAmount::exchange(result.wallet.amount,0,request.amount);
        require(purse.has_value(),"Bank purse owner coin cap exceeded");
        result.bank.amount-=request.amount;result.wallet.amount=purse->value();
    } else throw DatabaseError("Bank operation invalid");
    ++result.wallet.revision;++result.bank.revision;return result;
}
SqliteBankRepository::Snapshot SqliteBankRepository::commit(const std::string& server_receipt,const Request& request) {
    require(server_receipt.size()==64 && server_receipt.find_first_not_of("0123456789abcdef")==std::string::npos,"Bank receipt invalid");
    const auto next=plan(request);const auto& expected=request.expected;
    sqlite_detail::Transaction transaction(db_);
    sqlite_detail::Statement duplicate(db_,"SELECT 1 FROM character_bank_receipts WHERE receipt=?");
    duplicate.bind(1,server_receipt);require(!duplicate.row(),"Bank transfer already committed");
    require(load(expected.account,expected.character)==expected,"Bank snapshot conflict");
    sqlite_detail::Statement battle(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s "
        "ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
    battle.bind_id(1,expected.character);require(!battle.row(),"Bank during pending battle");
    sqlite_detail::Statement purse(db_,"UPDATE character_trade_wallets SET amount=?,revision=? "
        "WHERE character_id=? AND amount=? AND revision=? AND design_id='CUSTOM-0063'");
    purse.bind(1,next.wallet.amount);purse.bind_id(2,next.wallet.revision);purse.bind_id(3,next.character);
    purse.bind(4,expected.wallet.amount);purse.bind_id(5,expected.wallet.revision);purse.done();
    require(sqlite3_changes(db_)==1,"Bank purse write rejected");
    sqlite_detail::Statement bank(db_,"UPDATE character_bank_balances SET amount=?,revision=? "
        "WHERE character_id=? AND amount=? AND revision=? AND design_id='CUSTOM-0064'");
    bank.bind(1,next.bank.amount);bank.bind_id(2,next.bank.revision);bank.bind_id(3,next.character);
    bank.bind(4,expected.bank.amount);bank.bind_id(5,expected.bank.revision);bank.done();
    require(sqlite3_changes(db_)==1,"Bank balance write rejected");
    sqlite_detail::Statement insert(db_,"INSERT INTO character_bank_receipts(receipt,account_id,character_id,operation,amount,"
        "wallet_amount,wallet_revision,bank_amount,bank_revision,design_id) VALUES(?,?,?,?,?,?,?,?,?,'CUSTOM-0064')");
    insert.bind(1,server_receipt);insert.bind_id(2,next.account);insert.bind_id(3,next.character);
    insert.bind(4,static_cast<std::uint8_t>(request.operation));insert.bind(5,request.amount);
    insert.bind(6,next.wallet.amount);insert.bind_id(7,next.wallet.revision);insert.bind(8,next.bank.amount);insert.bind_id(9,next.bank.revision);
    insert.done();require(sqlite3_changes(db_)==1,"Bank receipt write rejected");
    sqlite_detail::Statement recorded(db_,"SELECT account_id,character_id,operation,amount,wallet_amount,wallet_revision,"
        "bank_amount,bank_revision,design_id FROM character_bank_receipts WHERE receipt=?");
    recorded.bind(1,server_receipt);
    require(recorded.row() && recorded.number<std::uint64_t>(0)==next.account && recorded.number<std::uint64_t>(1)==next.character &&
        recorded.number<std::uint8_t>(2)==static_cast<std::uint8_t>(request.operation) && recorded.number<std::uint32_t>(3)==request.amount &&
        recorded.number<std::uint64_t>(4)==next.wallet.amount && recorded.number<std::uint64_t>(5)==next.wallet.revision &&
        recorded.number<std::uint32_t>(6)==next.bank.amount && recorded.number<std::uint64_t>(7)==next.bank.revision &&
        recorded.text(8)=="CUSTOM-0064","Bank receipt readback mismatch");
    require(load(next.account,next.character)==next,"Bank balances readback mismatch");
    transaction.commit();return next;
}
}
