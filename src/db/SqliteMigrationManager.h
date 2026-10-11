#pragma once
#include "db/Migration.h"
struct sqlite3;
namespace god2 {
class SqliteMigrationManager final : public MigrationManager {
public:
    SqliteMigrationManager(sqlite3* db, const std::vector<Migration>& migrations)
        : db_(db), migrations_(migrations) {}
    void migrate() override;
private:
    sqlite3* db_;
    std::vector<Migration> migrations_;
};
}
