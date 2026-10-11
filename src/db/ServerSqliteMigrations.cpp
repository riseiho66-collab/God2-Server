#include "db/ServerSqliteMigrations.h"
#include "db/SqliteSupport.h"
#include <array>
#include <memory>

namespace god2 {
std::vector<Migration> configured_sqlite_migrations(
    const std::filesystem::path& path, bool announcements_enabled) {
    if (path.empty()) throw DatabaseError("SQLite path must not be empty");
    const auto utf8 = path.u8string();
    if (utf8.find(u8'\0') != std::u8string::npos)
        throw DatabaseError("SQLite path contains NUL");
    const auto requested = [&] { return announcements_enabled ?
        owned_guild_announcement_migrations() : default_sqlite_migrations(); };
    if (!std::filesystem::exists(path)) return requested();
    sqlite3* raw = nullptr;
    const auto result = sqlite3_open_v2(reinterpret_cast<const char*>(utf8.c_str()),
        &raw, SQLITE_OPEN_READONLY | SQLITE_OPEN_FULLMUTEX, nullptr);
    std::unique_ptr<sqlite3, decltype(&sqlite3_close_v2)> connection(raw, sqlite3_close_v2);
    if (result != SQLITE_OK)
        throw DatabaseError(raw ? sqlite3_errmsg(raw) : "Unable to inspect SQLite migration history");
    sqlite_detail::check(raw, sqlite3_busy_timeout(raw, 5000));
    bool announcement_table = false;
    {
        sqlite_detail::Statement table(raw,
            "SELECT type FROM sqlite_master WHERE name='owned_guild_announcements_0078'");
        if (table.row()) {
            if (table.text(0) != "table" || table.row())
                throw DatabaseError("Ambiguous installed announcement storage");
            announcement_table = true;
        }
    }
    {
        sqlite_detail::Statement table(raw,
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'");
        if (!table.row()) {
            if (announcement_table) throw DatabaseError("Announcement storage has no migration history");
            return requested();
        }
    }
    sqlite_detail::Statement history(raw,
        "SELECT version,name,sql_text FROM schema_migrations WHERE version=50");
    if (!history.row()) {
        if (announcement_table) throw DatabaseError("Announcement storage has no migration50 contract");
        return requested();
    }
    auto migrations = owned_guild_announcement_migrations();
    const auto& installed = migrations.back();
    if (history.integer(0) != installed.version || history.text(1) != installed.name ||
        history.text(2) != installed.sql || history.row())
        throw DatabaseError("Installed announcement migration50 contract mismatch");
    if (!announcement_table) throw DatabaseError("Installed announcement migration50 storage missing");
    // Preserve additional opaque columns, but require the known repository shape.
    const std::array<const char*, 6> names{
        "guild_id", "text_utf8", "revision", "origin", "design_id", "source_sha256"};
    const std::array<const char*, 6> types{"INTEGER", "TEXT", "INTEGER", "TEXT", "TEXT", "TEXT"};
    std::array<bool, 6> found{};
    sqlite_detail::Statement columns(raw, "PRAGMA table_info(owned_guild_announcements_0078)");
    while (columns.row()) {
        for (std::size_t i = 0; i < names.size(); ++i) {
            if (columns.text(1) != names[i]) continue;
            if (found[i] || columns.text(2) != types[i] ||
                columns.integer(3) != (i == 0 ? 0 : 1) || columns.integer(5) != (i == 0 ? 1 : 0))
                throw DatabaseError("Installed announcement column contract mismatch");
            found[i] = true;
        }
    }
    for (const auto present : found)
        if (!present) throw DatabaseError("Installed announcement repository column missing");
    sqlite_detail::Statement foreign_key(raw, "PRAGMA foreign_key_list(owned_guild_announcements_0078)");
    bool owner_reference = false;
    while (foreign_key.row()) {
        if (foreign_key.text(3) == "guild_id") {
            if (owner_reference || foreign_key.text(2) != "owned_guilds" || foreign_key.text(4) != "id" ||
                foreign_key.text(5) != "NO ACTION" || foreign_key.text(6) != "NO ACTION")
                throw DatabaseError("Installed announcement owner foreign key mismatch");
            owner_reference = true;
        }
    }
    if (!owner_reference) throw DatabaseError("Installed announcement owner foreign key missing");
    // The transactional migration manager still validates the entire history,
    // consecutive numbering, all immutable SQL and unknown future migrations.
    return migrations;
}
}
