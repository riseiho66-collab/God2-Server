#include "db/SqliteBankRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <vector>
using namespace god2;
namespace {
void require(bool ok,const char* message) {if(!ok)throw std::runtime_error(message);}
template<class F>void rejects(F&& f) {
    try {f();}catch(const DatabaseError&) {return;}
    throw std::runtime_error("Expected bank rejection");
}
// Preserve each column's SQLite type and exact bytes, including profile blobs.
std::string dump(sqlite3* db,const std::string& sql) {
    sqlite3_stmt* raw=nullptr;sqlite_detail::check(db,sqlite3_prepare_v2(db,sql.c_str(),-1,&raw,nullptr));
    std::unique_ptr<sqlite3_stmt,decltype(&sqlite3_finalize)> statement(raw,sqlite3_finalize);
    std::string result;
    for(;;) {
        const auto step=sqlite3_step(raw);if(step==SQLITE_DONE)break;
        require(step==SQLITE_ROW,"Raw saved-state query failed");
        for(int c=0;c<sqlite3_column_count(raw);++c) {
            const auto type=sqlite3_column_type(raw,c);
            const auto* bytes=type==SQLITE_BLOB ? sqlite3_column_blob(raw,c) : sqlite3_column_text(raw,c);
            const auto size=sqlite3_column_bytes(raw,c);
            result+=std::to_string(type)+":"+std::to_string(size)+":";
            if(size)result.append(static_cast<const char*>(bytes),static_cast<std::size_t>(size));
            result+=';';
        }
        result+='\n';
    }
    return result;
}
std::string schema(sqlite3* db) {
    return dump(db,"SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT LIKE 'character_bank_%' "
        "AND tbl_name NOT LIKE 'character_bank_%' ORDER BY type,name");
}
std::string saves(sqlite3* db) {
    sqlite_detail::Statement tables(db,"SELECT name FROM sqlite_schema WHERE type='table' "
        "AND name NOT LIKE 'character_bank_%' AND name<>'character_trade_wallets' ORDER BY name");
    std::string result;
    while(tables.row()) {
        const auto name=tables.text(0);require(name.find('"')==std::string::npos,"Unsafe test table name");
        result+=name+'\n'+dump(db,"SELECT * FROM \""+name+"\" ORDER BY rowid");
    }
    return result;
}
std::int64_t receipt_count(sqlite3* db) {
    sqlite_detail::Statement read(db,"SELECT count(*) FROM character_bank_receipts");
    require(read.row(),"Missing receipt count");return read.integer(0);
}
}
int main() {try {
    sqlite3* raw=nullptr;require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Open failed");
    std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> db(raw,sqlite3_close_v2);
    sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();
    sqlite_detail::execute(raw,"INSERT INTO accounts(id,username,password_hash) VALUES(1,'a','hash'),(2,'b','hash'),(3,'c','hash')");
    SqliteRecoveredCharacterRepository chars(raw);SqliteTradeRepository trades(raw);trades.install_schema();
    std::array<std::uint64_t,4> ids{};
    for(unsigned n=0;n<4;++n) {
        const auto account=n==3 ? 1 : n+1;
        std::array<std::uint8_t,40> profile{};profile[0]=static_cast<std::uint8_t>('A'+n);
        ids[n]=chars.create(account,profile).id;
        chars.commit_resources(account,ids[n],{},{50,120,10,80,0,"CUSTOM-0012"});
        chars.provision_town_reward_slot(account,ids[n]);
        chars.provision_owned_bag(account,ids[n]);trades.provision_wallet(account,ids[n]);
    }
    const auto original_schema=schema(raw),original_saves=saves(raw);
    const auto initial_changes=sqlite3_total_changes(raw);
    SqliteBankRepository banks(raw);
    rejects([&]{banks.load_bank(1,ids[0]);});
    require(schema(raw)==original_schema && sqlite3_total_changes(raw)==initial_changes,"Constructor/reader mutated database");
    sqlite_detail::Statement absent(raw,"SELECT count(*) FROM sqlite_schema WHERE name LIKE 'character_bank_%'");
    require(absent.row() && absent.integer(0)==0,"Reader installed bank schema");
    banks.install_schema();banks.install_schema();
    require(schema(raw)==original_schema && saves(raw)==original_saves,"Installation changed existing schema/history/saves");
    const auto before_load=sqlite3_total_changes(raw);
    require(!banks.load_bank(1,ids[0]),"Read provisioned absent bank");
    rejects([&]{banks.load(1,ids[0]);});
    require(sqlite3_total_changes(raw)==before_load,"Absent load wrote data");
    for(unsigned n=0;n<4;++n) {
        const auto account=n==3 ? 1 : n+1;
        require(banks.provision_bank(account,ids[n])==SqliteBankRepository::Balance{0,1},"New bank default not zero");
    }
    rejects([&]{banks.provision_bank(2,ids[0]);});rejects([&]{banks.load(2,ids[0]);});
    // Explicit test-only funding, deliberately absent from production API.
    sqlite_detail::Statement fund(raw,"UPDATE character_trade_wallets SET amount=100 WHERE character_id=?");
    fund.bind_id(1,ids[0]);fund.done();
    const auto initial=banks.load(1,ids[0]);
    const std::array unrelated{banks.load(2,ids[1]),banks.load(3,ids[2]),banks.load(1,ids[3])};
    using Operation=SqliteBankRepository::Operation;using Request=SqliteBankRepository::Request;
    const Request deposit{initial,Operation::Deposit,30};
    const auto planned=SqliteBankRepository::plan(deposit);
    require(planned.wallet.amount==70 && planned.bank.amount==30 && planned.wallet.revision==2 && planned.bank.revision==2,
        "Deposit conservation/revisions failed");
    require(banks.provision_bank(1,ids[0])==initial.bank,"Provision reset bank");
    const auto unchanged=[&] {
        require(banks.load(1,ids[0])==initial,"Rejected transfer changed purse/bank");
        require(receipt_count(raw)==0,"Rejected transfer left receipt");
        require(saves(raw)==original_saves,"Transfer altered unrelated saved rows");
    };
    for(unsigned mode=0;mode<12;++mode) {
        auto bad=deposit;
        switch(mode) {
        case 0:bad.amount=0;break;
        case 1:bad.amount=0x80000000;break;
        case 2:bad.amount=0xffffffff;break;
        case 3:bad.amount=101;break;
        case 4:bad.operation=Operation::Withdraw;bad.amount=1;break;
        case 5:bad.expected.account=2;break;
        case 6:++bad.expected.wallet.revision;break;
        case 7:++bad.expected.bank.revision;break;
        case 8:++bad.expected.wallet.amount;break;
        case 9:++bad.expected.bank.amount;break;
        case 10:bad.operation=static_cast<Operation>(60);break;
        case 11:bad.expected.character=0;break;
        }
        rejects([&]{banks.commit(std::string(64,'a'),bad);});unchanged();
    }
    for(const auto receipt:{std::string{},std::string(63,'a'),std::string(64,'A'),std::string(64,'g')}) {
        rejects([&]{banks.commit(receipt,deposit);});unchanged();
    }
    // CAS and readback must reject trigger failures/corruption even after the
    // purse has been written. Everything, including receipt, rolls back.
    for(const auto sql:{
        "CREATE TRIGGER fail BEFORE UPDATE ON character_bank_balances BEGIN SELECT RAISE(ABORT,'injected second write'); END",
        "CREATE TRIGGER fail BEFORE UPDATE ON character_bank_balances BEGIN SELECT RAISE(IGNORE); END",
        "CREATE TRIGGER fail AFTER UPDATE ON character_trade_wallets BEGIN UPDATE character_bank_balances SET revision=revision+1 WHERE character_id=NEW.character_id; END",
        "CREATE TRIGGER fail AFTER INSERT ON character_bank_receipts BEGIN UPDATE character_trade_wallets SET amount=999 WHERE character_id=NEW.character_id; END",
        "CREATE TRIGGER fail AFTER INSERT ON character_bank_receipts BEGIN UPDATE character_bank_balances SET amount=999 WHERE character_id=NEW.character_id; END",
        "CREATE TRIGGER fail AFTER INSERT ON character_bank_receipts BEGIN DELETE FROM character_bank_receipts WHERE receipt=NEW.receipt; END",
        "CREATE TRIGGER fail AFTER INSERT ON character_bank_receipts BEGIN UPDATE character_bank_receipts SET operation=62 WHERE receipt=NEW.receipt; END"}) {
        sqlite_detail::execute(raw,sql);rejects([&]{banks.commit(std::string(64,'b'),deposit);});unchanged();
        sqlite_detail::execute(raw,"DROP TRIGGER fail");
    }
    constexpr auto max_revision=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
    for(unsigned mode=0;mode<7;++mode) {
        auto bad=deposit;
        switch(mode) {
        case 0:bad.expected.bank.amount=SqliteBankRepository::bank_cap;break;
        case 1:bad.expected.bank.amount=SqliteBankRepository::bank_cap+1;break;
        case 2:bad.expected.bank.revision=max_revision;break;
        case 3:bad.expected.wallet.revision=max_revision;break;
        case 4:bad.expected.wallet.revision=0;break;
        case 5:bad.expected.bank.revision=0;break;
        case 6:bad.operation=Operation::Withdraw;bad.expected.bank.amount=30;bad.expected.wallet.amount=0xffffffff;break;
        }
        rejects([&]{SqliteBankRepository::plan(bad);});
    }
    auto edge=deposit;edge.expected.bank.amount=SqliteBankRepository::bank_cap-30;
    edge.expected.wallet.revision=max_revision-1;edge.expected.bank.revision=max_revision-1;
    const auto capped=SqliteBankRepository::plan(edge);
    require(capped.bank.amount==SqliteBankRepository::bank_cap && capped.bank.revision==max_revision &&
        capped.wallet.revision==max_revision,"Last valid cap/revisions rejected");
    edge.operation=Operation::Withdraw;edge.expected.bank.amount=30;edge.expected.wallet.amount=0xffffffff-30;
    require(SqliteBankRepository::plan(edge).wallet.amount==0xffffffff,"Last valid uint32 purse rejected");
    // Persistent provenance/amount constraints and readers cannot accept a
    // foreign design ID even if a corrupted schema bypasses CHECK constraints.
    rejects([&]{sqlite_detail::execute(raw,"UPDATE character_bank_balances SET design_id='CUSTOM-0000'");});
    rejects([&]{sqlite_detail::execute(raw,"UPDATE character_bank_balances SET amount=500000001");});
    sqlite_detail::execute(raw,"PRAGMA ignore_check_constraints=ON");
    sqlite_detail::execute(raw,"BEGIN IMMEDIATE");
    sqlite_detail::execute(raw,"UPDATE character_bank_balances SET design_id='CUSTOM-0000'");
    rejects([&]{banks.load_bank(1,ids[0]);});
    sqlite_detail::execute(raw,"ROLLBACK");sqlite_detail::execute(raw,"PRAGMA ignore_check_constraints=OFF");
    unchanged();
    const auto committed=banks.commit(std::string(64,'c'),deposit);
    require(committed==planned && banks.load(1,ids[0])==planned,"Committed deposit/readback mismatch");
    require(banks.provision_bank(1,ids[0])==planned.bank,"Provision reset funded bank/revision");
    rejects([&]{banks.commit(std::string(64,'c'),deposit);});
    rejects([&]{banks.commit(std::string(64,'d'),deposit);});
    const Request withdraw{committed,Operation::Withdraw,20};
    rejects([&]{banks.commit(std::string(64,'c'),withdraw);});
    auto excessive=withdraw;excessive.amount=31;rejects([&]{banks.commit(std::string(64,'d'),excessive);});
    require(banks.load(1,ids[0])==committed && receipt_count(raw)==1,"Replay/stale/insufficient changed bank");
    const auto withdrawn=banks.commit(std::string(64,'d'),withdraw);
    require(withdrawn.wallet.amount==90 && withdrawn.bank.amount==10 && withdrawn.wallet.revision==3 && withdrawn.bank.revision==3 &&
        std::uint64_t{withdrawn.wallet.amount}+withdrawn.bank.amount==100,"Withdrawal failed conservation");
    sqlite_detail::Statement provenance(raw,"SELECT count(*) FROM character_bank_balances WHERE design_id='CUSTOM-0064'");
    require(provenance.row() && provenance.integer(0)==4,"Bank row provenance missing");
    sqlite_detail::Statement receipts(raw,"SELECT count(*) FROM character_bank_receipts WHERE design_id='CUSTOM-0064' AND account_id=1");
    require(receipts.row() && receipts.integer(0)==2,"Receipt provenance/readback missing");
    require(schema(raw)==original_schema && saves(raw)==original_saves,"Bank changed existing schema/migrations/player saves");
    const auto resources=*chars.load_resources(1,ids[0]);chars.reserve_battle(1,ids[0],resources);
    const auto pending=dump(raw,"SELECT * FROM battle_reservations ORDER BY id");
    const auto pending_saves=saves(raw);
    rejects([&]{banks.commit(std::string(64,'e'),{withdrawn,Operation::Deposit,1});});
    require(banks.load(1,ids[0])==withdrawn && receipt_count(raw)==2 && dump(raw,"SELECT * FROM battle_reservations ORDER BY id")==pending,
        "Pending battle rejection mutated bank/battle");
    require(banks.load(2,ids[1])==unrelated[0] && banks.load(3,ids[2])==unrelated[1] && banks.load(1,ids[3])==unrelated[2],
        "Unrelated player or same-account character bank changed");
    require(schema(raw)==original_schema && saves(raw)==pending_saves,"Pending battle bank rejection changed existing schema/migrations/player saves");
    std::cout<<"Bank owned atomic deposit/withdraw, conservation, boundaries, CAS, pending battle, provenance, receipt replay and rollback passed; live acceptance OPEN\n";
}catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}}
