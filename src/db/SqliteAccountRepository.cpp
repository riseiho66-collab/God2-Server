#include "db/SqliteAccountRepository.h"
#include "db/SqliteSupport.h"
namespace god2 {
namespace {
Account read_account(sqlite_detail::Statement& statement) {
    return {statement.number<std::uint64_t>(0), statement.text(1), statement.text(2), statement.text(3)};
}
}
Account SqliteAccountRepository::create(const std::string& username, const std::string& password_hash) {
    if (username.empty() || password_hash.empty()) throw DatabaseError("Username and password hash must not be empty");
    sqlite_detail::Transaction transaction(db_);
    sqlite_detail::Statement statement(db_, "INSERT INTO accounts(username,password_hash) VALUES(?,?)");
    statement.bind(1, username);
    statement.bind(2, password_hash);
    statement.done();
    auto account = find_by_id(static_cast<std::uint64_t>(sqlite3_last_insert_rowid(db_)));
    if (!account) throw DatabaseError("Inserted account missing");
    transaction.commit();
    return *account;
}
std::optional<Account> SqliteAccountRepository::find_by_username(const std::string& username) {
    sqlite_detail::Statement statement(db_, "SELECT id,username,password_hash,created_at FROM accounts WHERE username=?");
    statement.bind(1, username);
    if (!statement.row()) return std::nullopt;
    return read_account(statement);
}
std::optional<Account> SqliteAccountRepository::find_by_id(std::uint64_t id) {
    sqlite_detail::Statement statement(db_, "SELECT id,username,password_hash,created_at FROM accounts WHERE id=?");
    statement.bind_id(1, id);
    if (!statement.row()) return std::nullopt;
    return read_account(statement);
}
}
