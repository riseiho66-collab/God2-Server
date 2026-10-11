#pragma once
// PRIVATE CUSTOM-0083 proposal. No formal activation or native acceptance.
#include "db/GuildOfficerSqliteMigrations.h"
#include "db/SqliteOwnedGuildSuccessionRepositoryDraft.h"
#include <memory>
namespace god2 {
struct GuildSuccessionFlagsDraft {
    bool membership{},announcements{},officers{},succession{};
};
std::vector<Migration> owned_guild_succession_migrations_draft();
std::vector<Migration> configured_guild_succession_migrations_draft(
    const std::filesystem::path&,GuildSuccessionFlagsDraft);
void require_exact_guild_succession_migrations_draft(sqlite3*,const std::vector<Migration>&);
// Installed52 always routes owner reads through effective ownership, even when
// transfer is disabled. The legacy creator view is not an authority fallback.
class GuildSuccessionRepositoryFactoryDraft {
public:
    GuildSuccessionRepositoryFactoryDraft(sqlite3*,const std::vector<Migration>&,GuildSuccessionFlagsDraft);
    SqliteOwnedGuildSuccessionRepositoryDraft& effective_owner();
    bool uses_effective_owner() const noexcept{return bool(effective_);}
private:
    std::unique_ptr<SqliteOwnedGuildMembershipRepository> original_;
    std::unique_ptr<SqliteOwnedGuildSuccessionRepositoryDraft> effective_;
};
}
