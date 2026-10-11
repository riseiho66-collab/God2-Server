#pragma once
#include <string>
#include <vector>
namespace god2 {
struct Migration {
    int version;
    std::string name;
    std::string sql;
};
class MigrationManager {
public:
    virtual ~MigrationManager() = default;
    virtual void migrate() = 0;
};
std::vector<Migration> default_sqlite_migrations();
// CUSTOM-0078: explicit disposable candidate; not the production default.
std::vector<Migration> owned_guild_announcement_migrations();
}
