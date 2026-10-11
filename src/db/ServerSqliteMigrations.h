#pragma once
#include "db/Migration.h"
#include <filesystem>

namespace god2 {
// CUSTOM-0078: enabling announcement gameplay explicitly installs migration50.
// Disabling gameplay retains an already installed exact50 storage contract.
// This read-only selector never creates a database or grants gameplay authority.
std::vector<Migration> configured_sqlite_migrations(
    const std::filesystem::path& path, bool announcements_enabled);
}
