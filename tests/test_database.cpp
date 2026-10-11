#include "db/SqliteDatabase.h"
#include "db/MySqlDatabase.h"
#include "db/DbTypes.h"
#include <filesystem>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>

namespace {
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
template<class F> void expect_database_error(F&& function, const char* message) {
    try { function(); } catch (const god2::DatabaseError&) { return; }
    throw std::runtime_error(message);
}
struct TemporaryDatabase {
    std::filesystem::path directory;
    TemporaryDatabase() {
        std::random_device random;
        for (int attempt = 0; attempt < 100; ++attempt) {
            directory = std::filesystem::temp_directory_path() /
                ("god2-db-test-" + std::to_string(random()) + "-" + std::to_string(random()));
            if (std::filesystem::create_directory(directory)) return;
        }
        throw std::runtime_error("Unable to create database test directory");
    }
    ~TemporaryDatabase() {
        std::error_code error;
        std::filesystem::remove_all(directory, error);
    }
    std::filesystem::path path() const { return directory / "test.sqlite"; }
};
}

void test_database() {
    using namespace god2;
    TemporaryDatabase temporary;
    std::uint64_t account_id = 0, character_id = 0;
    const std::string username = "user'; DROP TABLE accounts;--";
    const std::string hash("hash\0with-nul", 13);
    std::string created_at;
    {
        SqliteDatabase db(temporary.path());
        expect_database_error([&] { db.accounts(); }, "Uninitialized access must fail");
        expect_database_error([&] { db.migrate(); }, "Uninitialized migration must fail");
        db.initialize();
        db.initialize();
        expect_database_error([&] { db.characters(); }, "Unmigrated access must fail");
        db.migrate();
        db.migrate();
        auto account = db.accounts().create(username, hash);
        account_id = account.id;
        require(account.id > 0 && !account.created_at.empty(), "Account generated fields missing");
        const auto found = db.accounts().find_by_username(username);
        require(found && found->id == account.id && found->password_hash == hash, "Bound account text did not round trip");
        const auto by_id = db.accounts().find_by_id(account.id);
        require(by_id && by_id->username == username, "Account id lookup failed");
        require(!db.accounts().find_by_id(0) && !db.accounts().find_by_username("missing"), "Missing account must be optional");
        expect_database_error([&] { db.accounts().create(username, "other"); }, "Duplicate username accepted");
        expect_database_error([&] { db.accounts().create("", "hash"); }, "Empty username accepted");
        expect_database_error([&] { db.accounts().find_by_id(std::numeric_limits<std::uint64_t>::max()); }, "Oversized id accepted");
        auto second_account = db.accounts().create("second", "hash");
        Character input;
        input.name = "Hero ' quoted";
        input.account_id = account.id;
        const auto character = db.characters().create(input);
        character_id = character.id;
        created_at = character.created_at;
        require(character.id > 0 && !created_at.empty(), "Character generated fields missing");
        require(character.level == 1 && character.job == 1 && character.hp == 100 && character.mp == 50 &&
                character.map_id == 1 && character.x == 100 && character.y == 100, "Character defaults changed");
        auto changed = character;
        changed.level = 42;
        changed.job = 7;
        changed.hp = std::numeric_limits<std::uint32_t>::max();
        changed.mp = 0;
        changed.map_id = 17;
        changed.x = std::numeric_limits<std::int32_t>::min();
        changed.y = std::numeric_limits<std::int32_t>::max();
        changed.name = "Renamed";
        changed.created_at = "must not replace creation time";
        db.characters().save(changed);
        db.characters().save(changed);
        const auto saved = db.characters().find_by_id(character.id);
        require(saved && saved->level == 42 && saved->job == 7 && saved->name == "Renamed" &&
                saved->hp == changed.hp && saved->mp == 0 && saved->map_id == 17 &&
                saved->x == changed.x && saved->y == changed.y && saved->created_at == created_at,
                "Character save did not round trip");
        changed.account_id = second_account.id;
        expect_database_error([&] { db.characters().save(changed); }, "Character ownership transfer accepted");
        changed.account_id = account.id;
        changed.id = 0;
        expect_database_error([&] { db.characters().save(changed); }, "Save of missing character accepted");
        input.account_id = 0;
        expect_database_error([&] { db.characters().create(input); }, "Foreign key violation accepted");
        input.account_id = account.id;
        const auto next = db.characters().create(input);
        const auto list = db.characters().list_for_account(account.id);
        require(list.size() == 2 && list[0].id == character.id && list[1].id == next.id, "Character list ordering failed");
        require(db.characters().list_for_account(second_account.id).empty(), "Character list leaked another account");
        require(!db.characters().find_by_id(0), "Missing character must be optional");
    }
    {
        SqliteDatabase db(temporary.path());
        db.initialize();
        db.migrate();
        const auto account = db.accounts().find_by_id(account_id);
        const auto character = db.characters().find_by_id(character_id);
        require(account && account->username == username, "Account persistence failed");
        require(character && character->level == 42, "Character persistence failed");
    }
    // An earlier successful step and the failed step must both roll back.
    auto failing = default_sqlite_migrations();
    const auto probe_index=failing.size();
    const auto probe_version=failing.back().version+1;
    failing.push_back({probe_version, "rollback_probe", "CREATE TABLE rollback_probe(id INTEGER PRIMARY KEY);"});
    failing.push_back({probe_version+1, "failure", "INSERT INTO nonexistent_table VALUES(1);"});
    {
        SqliteDatabase db(temporary.path(), failing);
        db.initialize();
        expect_database_error([&] { db.migrate(); }, "Invalid migration succeeded");
        expect_database_error([&] { db.migrate(); }, "Failed migration did not allow retry");
    }
    auto corrected = default_sqlite_migrations();
    corrected.push_back(failing[probe_index]);
    {
        SqliteDatabase db(temporary.path(), corrected);
        db.initialize();
        db.migrate(); // Would fail if rollback_probe survived the failed batch.
        require(db.accounts().find_by_id(account_id).has_value(), "Migration failure lost existing data");
        db.migrate();
    }
    {
        SqliteDatabase old_server(temporary.path());
        old_server.initialize();
        expect_database_error([&] { old_server.migrate(); }, "Newer schema accepted by older server");
    }
    corrected[0].sql += "\n";
    {
        SqliteDatabase changed_history(temporary.path(), corrected);
        changed_history.initialize();
        expect_database_error([&] { changed_history.migrate(); }, "Edited migration history accepted");
    }
    {
        TemporaryDatabase fresh;
        SqliteDatabase failed(fresh.path(), failing);
        failed.initialize();
        expect_database_error([&] { failed.migrate(); }, "Fresh invalid migration succeeded");
        SqliteDatabase recovered(fresh.path());
        recovered.initialize();
        recovered.migrate();
        require(recovered.accounts().create("recovered", "hash").id > 0, "Fresh migration rollback failed");
    }
    MySqlDatabase mysql;
    expect_database_error([&] { mysql.initialize(); }, "MySQL placeholder silently succeeded");
    expect_database_error([&] { mysql.migrate(); }, "MySQL migration placeholder silently succeeded");
    expect_database_error([&] { mysql.accounts(); }, "MySQL account placeholder silently succeeded");
    expect_database_error([&] { mysql.characters(); }, "MySQL character placeholder silently succeeded");
}
