#pragma once
#include "db/SqliteTradeRepository.h"
#include <functional>

namespace god2 {
// CUSTOM-0064: owned, per-character bank authority. Original shared-account
// bank scope and server ledger are unrecovered. The purse remains CUSTOM-0063.
// Caller validates the live native banking route and prepares projections before
// commit; repository authority never grants money, charges fees or interest.
class SqliteBankRepository {
public:
    static constexpr std::uint32_t bank_cap=500000000;
    struct Balance {
        std::uint32_t amount{};
        std::uint64_t revision{};
        bool operator==(const Balance&) const=default;
    };
    struct Snapshot {
        std::uint64_t account{},character{};
        SqliteTradeRepository::Wallet wallet;
        Balance bank;
        bool operator==(const Snapshot&) const=default;
    };
    enum class Operation : std::uint8_t { Deposit=61,Withdraw=62 };
    struct Request { Snapshot expected;Operation operation{};std::uint32_t amount{}; };
    explicit SqliteBankRepository(sqlite3* db):db_(db) {}
    // Explicit installation/provisioning; constructor and readers perform no DDL.
    void install_schema();
    // New bank default0. Existing balance and revision are preserved.
    // Optional pure lifecycle fence: no callbacks/SQL; invoked before writes
    // and after all persisted readback, immediately before COMMIT.
    using Current=std::function<void()>;
    Balance provision_bank(std::uint64_t account,std::uint64_t character,const Current& current={});
    std::optional<Balance> load_bank(std::uint64_t account,std::uint64_t character);
    Snapshot load(std::uint64_t account,std::uint64_t character);
    // Pure, conserved transfer; reject zero/high-bit native signed amounts,
    // insufficient funds, bank cap, purse overflow and exhausted revisions.
    static Snapshot plan(const Request& request);
    // BEGIN IMMEDIATE, ownership/pending-battle checks, CAS both revisions,
    // unique server receipt and actual persisted readback before COMMIT.
    Snapshot commit(const std::string& server_receipt,const Request& request,const Current& current={});
private:
    sqlite3* db_;
};
}
