#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
namespace god2 {
void SqliteMigrationManager::migrate() {
    for (std::size_t i = 0; i < migrations_.size(); ++i) {
        if (migrations_[i].version != static_cast<int>(i + 1) || migrations_[i].name.empty() || migrations_[i].sql.empty())
            throw DatabaseError("Migrations must be nonempty and consecutively numbered starting at 1");
    }
    sqlite_detail::Transaction transaction(db_);
    sqlite_detail::execute(db_,
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "version INTEGER PRIMARY KEY, name TEXT NOT NULL, sql_text TEXT NOT NULL,"
        "applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now')))");
    std::size_t applied = 0;
    {
        sqlite_detail::Statement history(db_, "SELECT version,name,sql_text FROM schema_migrations ORDER BY version");
        while (history.row()) {
            if (applied >= migrations_.size()) throw DatabaseError("Database schema is newer than this server");
            const auto& migration = migrations_[applied];
            // Store and compare the entire SQL text to detect edits without checksum collisions.
            if (history.integer(0) != migration.version || history.text(1) != migration.name || history.text(2) != migration.sql)
                throw DatabaseError("Migration history mismatch; applied migrations are immutable");
            ++applied;
        }
    }
    for (; applied < migrations_.size(); ++applied) {
        const auto& migration = migrations_[applied];
        sqlite_detail::execute(db_, migration.sql);
        sqlite_detail::Statement insert(db_, "INSERT INTO schema_migrations(version,name,sql_text) VALUES(?,?,?)");
        insert.bind(1, migration.version);
        insert.bind(2, migration.name);
        insert.bind(3, migration.sql);
        insert.done();
    }
    {
        sqlite_detail::Statement foreign_keys(db_, "PRAGMA foreign_key_check");
        if (foreign_keys.row()) throw DatabaseError("Migration foreign key check failed");
        sqlite_detail::Statement integrity(db_, "PRAGMA quick_check");
        if (!integrity.row() || integrity.text(0) != "ok" || integrity.row())
            throw DatabaseError("Migration integrity check failed");
    }
    transaction.commit();
}
}
