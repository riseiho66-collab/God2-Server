#pragma once
#include "db/AccountRepository.h"
struct sqlite3;
namespace god2 {
class SqliteAccountRepository final : public AccountRepository {
public:
    explicit SqliteAccountRepository(sqlite3* db) : db_(db) {}
    Account create(const std::string& username, const std::string& password_hash) override;
    std::optional<Account> find_by_username(const std::string& username) override;
    std::optional<Account> find_by_id(std::uint64_t id) override;
    // Backend identity only; does not open/read/write/authenticate an account.
    bool uses_connection(const sqlite3* connection) const noexcept {return db_==connection;}
private:
    sqlite3* db_;
};
}
