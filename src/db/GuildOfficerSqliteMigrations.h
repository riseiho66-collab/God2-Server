#pragma once
#include "db/Migration.h"
#include <filesystem>
struct sqlite3;
namespace god2 {
// CUSTOM0082: no edits to frozen49/50 selectors. Explicit opt-in installs51;
// installed exact51 is retained when officer/announcement gameplay are disabled.
std::vector<Migration> owned_guild_officer_migrations();
std::vector<Migration> configured_guild_officer_sqlite_migrations(
    const std::filesystem::path&,bool announcements_enabled,bool officers_enabled);
// Exact entire1..51 vector + stored prefix/history + canonical physical51 DDL.
// Read-only. Unknown opaque schema extensions are denied, never repaired/deleted.
void require_exact_guild_officer_migrations(sqlite3*,const std::vector<Migration>&);
}
