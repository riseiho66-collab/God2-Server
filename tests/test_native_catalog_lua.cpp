#include "db/SqliteDatabase.h"
#include "db/SqliteSupport.h"
#include "scripting/LuaEngine.h"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <memory>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>
#include <vector>

namespace {
using god2::LuaEngine;
using god2::NativeMapCatalog;
using god2::SqliteDatabase;

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

template<class Error = std::runtime_error, class F>
void expect_error(F&& function, const std::string& text) {
    try { function(); }
    catch (const Error& error) {
        require(std::string(error.what()).find(text) != std::string::npos,
                "Exception lost its expected diagnostic");
        return;
    }
    throw std::runtime_error("Expected error: " + text);
}

struct TempDirectory {
    std::filesystem::path root;
    TempDirectory() {
        const auto seed = std::chrono::steady_clock::now().time_since_epoch().count();
        for (int i = 0; i < 100; ++i) {
            root = std::filesystem::temp_directory_path() /
                ("god2-native-catalog-lua-test-" + std::to_string(seed) + "-" + std::to_string(i));
            if (std::filesystem::create_directory(root)) return;
        }
        throw std::runtime_error("Unable to create synthetic test directory");
    }
    ~TempDirectory() { std::error_code error; std::filesystem::remove_all(root, error); }
    void write(const std::string& name, const std::string& script) const {
        std::ofstream file(root / name, std::ios::binary | std::ios::trunc);
        file << script;
        file.close();
        require(!file.fail(), "Unable to write synthetic Lua script");
    }
};

struct Connection {
    struct Close { void operator()(sqlite3* db) const { sqlite3_close_v2(db); } };
    std::unique_ptr<sqlite3, Close> db;
    explicit Connection(const std::filesystem::path& path) {
        const auto utf8 = path.u8string();
        sqlite3* raw = nullptr;
        const int status = sqlite3_open_v2(reinterpret_cast<const char*>(utf8.c_str()), &raw,
                                          SQLITE_OPEN_READWRITE, nullptr);
        db.reset(raw);
        require(status == SQLITE_OK, "Unable to open synthetic fixture connection");
        execute("PRAGMA foreign_keys=ON");
    }
    void execute(const std::string& sql) { god2::sqlite_detail::execute(db.get(), sql); }
    std::int64_t data_version() const {
        god2::sqlite_detail::Statement query(db.get(), "PRAGMA data_version");
        require(query.row(), "Missing data_version");
        return query.integer(0);
    }
};

// Synthetic raw bytes and deliberately invented, shape-valid hashes. This test
// neither reads native source files nor asserts gameplay or cryptographic facts.
void seed(Connection& connection) {
    connection.execute(R"SQL(
INSERT INTO native_data_sources VALUES(
 'current-map-catalog-v1','test-only/nonexistent-synthetic.bin',
 replace(hex(zeroblob(32)),'0','a'),replace(hex(zeroblob(32)),'0','b'),
 replace(hex(zeroblob(32)),'0','c'),'test-only-section','0x00000001','0x00000002',2);
INSERT INTO native_map_catalog VALUES(
 'current-map-catalog-v1',0,1,replace(hex(zeroblob(32)),'0','d'),X'5445535400FF80',1,0,0);
INSERT INTO native_map_catalog VALUES(
 'current-map-catalog-v1',1,9223372036854775807,replace(hex(zeroblob(32)),'0','e'),X'00',16,1023,3);
)SQL");
}

struct Fixture {
    TempDirectory files;
    std::shared_ptr<SqliteDatabase> database;
    Connection writer;
    static std::shared_ptr<SqliteDatabase> migrated(const std::filesystem::path& path) {
        auto db = std::make_shared<SqliteDatabase>(path);
        db->initialize();
        db->migrate();
        return db;
    }
    Fixture() : database(migrated(files.root / "synthetic.sqlite")),
                writer(files.root / "synthetic.sqlite") { seed(writer); }
    LuaEngine::NativeMapLookup lookup() const {
        return [db = database](std::int64_t area, std::int64_t scene) {
            return db->native_map_catalog().lookup(NativeMapCatalog::current_dataset_id, area, scene);
        };
    }
};

void command(LuaEngine& engine, const std::string& name, const std::vector<std::string>& args = {}) {
    engine.call_gm_command(name, {1, "synthetic-test-admin"}, args);
}

std::string bytes(const std::filesystem::path& path) {
    std::ifstream file(path, std::ios::binary);
    require(file.good(), "Unable to read synthetic database bytes");
    return {std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>()};
}

void test_migration_guard() {
    TempDirectory files;
    SqliteDatabase database(files.root / "guard.sqlite");
    expect_error<god2::DatabaseError>([&] { database.native_map_catalog(); }, "Migrate database");
    database.initialize();
    expect_error<god2::DatabaseError>([&] { database.native_map_catalog(); }, "Migrate database");
    database.migrate();
    const auto* reader = &database.native_map_catalog();
    require(!reader->lookup(NativeMapCatalog::current_dataset_id, 1, 0), "Migration invented catalog data");
    database.initialize();
    database.migrate();
    require(reader == &database.native_map_catalog(), "Reader lifetime changed after repeated initialization");
    Connection writer(files.root / "guard.sqlite");
    writer.execute("UPDATE schema_migrations SET name='synthetic-corruption' WHERE version=1");
    expect_error<god2::DatabaseError>([&] { database.migrate(); }, "Migration history mismatch");
    expect_error<god2::DatabaseError>([&] { database.native_map_catalog(); }, "Migrate database");
    writer.execute("UPDATE schema_migrations SET name='accounts_and_characters' WHERE version=1");
    database.migrate();
    require(reader == &database.native_map_catalog(), "Remigration replaced reader");
}

void test_lookup_validation_and_read_only_snapshots() {
    Fixture fixture;
    const auto expected = fixture.database->native_map_catalog().lookup(NativeMapCatalog::current_dataset_id, 1, 0);
    const auto before = bytes(fixture.files.root / "synthetic.sqlite");
    const auto version = fixture.writer.data_version();
    int calls = 0;
    fixture.files.write("lookup.lua", R"LUA(
local function verify(r)
    assert(type(r) == 'table' and getmetatable(r) == nil)
    assert(r.area == 1 and r.scene == 0 and r.kind == 0)
    assert(r.source_record_index == 0 and r.source_line == 1)
    assert(r.record_sha256 == string.rep('d',64))
    assert(type(r.raw_record) == 'string' and r.raw_record == 'TEST' .. string.char(0,255,128))
    local s = r.source
    assert(type(s) == 'table' and getmetatable(s) == nil)
    assert(s.dataset_id == 'current-map-catalog-v1')
    assert(s.source_path == 'test-only/nonexistent-synthetic.bin')
    assert(s.source_sha256 == string.rep('a',64) and s.decoded_sha256 == string.rep('b',64))
    assert(s.native_image_sha256 == string.rep('c',64))
    assert(s.source_section == 'test-only-section')
    assert(s.loader_rva == '0x00000001' and s.lookup_rva == '0x00000002' and s.row_count == 2)
    local n = 0; for _ in pairs(r) do n = n + 1 end; assert(n == 8)
    n = 0; for _ in pairs(s) do n = n + 1 end; assert(n == 9)
end
local retained = native_map_catalog(1,0)
register_gm_command('check',function()
    verify(retained)
    local changed = native_map_catalog(1,0)
    assert(changed ~= retained and changed.source ~= retained.source)
    changed.raw_record = 'mutation'; changed.area = 16; changed.kind = 3
    changed.source.source_path = 'mutation'; changed.source.row_count = 999
    rawset(changed,'source_line',999); changed.source = {}
    verify(retained); verify(native_map_catalog(1.0,0.0))
    assert(native_map_catalog(1,1) == nil)
    local maximum = native_map_catalog(16,1023)
    assert(maximum.area == 16 and maximum.scene == 1023 and maximum.kind == 3)
    assert(maximum.source_record_index == 1 and maximum.raw_record == string.char(0))
    assert(math.type(maximum.source_line) == 'integer' and maximum.source_line == math.maxinteger)
    assert(io == nil and os == nil and package == nil and debug == nil)
    assert(dofile == nil and loadfile == nil and load == nil)
end)
register_gm_command('invalid',function()
    for _,args in ipairs({{}, {1}, {1,0,0}, {'1',0}, {1,'0'}, {true,0}, {1,false},
        {{},0}, {1,{}}, {function() end,0}, {1,function() end},
        {0,0}, {17,0}, {-1,0}, {1,-1}, {1,1024}, {1.5,0}, {1,0.5},
        {math.huge,0}, {1,math.huge}, {-math.huge,0}, {1,-math.huge},
        {0/0,0}, {1,0/0}, {math.maxinteger,0}, {math.mininteger,0},
        {1,math.maxinteger}, {1,math.mininteger}}) do
        local ok,err = pcall(native_map_catalog,table.unpack(args))
        assert(not ok and type(err) == 'string' and err:find('native_map_catalog',1,true))
    end
    assert(not pcall(native_map_catalog,nil,0))
    assert(not pcall(native_map_catalog,1,nil))
end)
)LUA");
    LuaEngine engine(fixture.files.root, false, [lookup = fixture.lookup(), &calls](auto area, auto scene) {
        ++calls;
        return lookup(area, scene);
    });
    require(engine.initialize() && engine.load_script("lookup.lua"), "Lookup script failed");
    command(engine, "check");
    const auto valid_calls = calls;
    command(engine, "invalid");
    require(calls == valid_calls, "Invalid selector reached host callback");
    require(fixture.database->native_map_catalog().lookup(NativeMapCatalog::current_dataset_id, 1, 0) == expected,
            "Lua snapshot mutation changed database data");
    require(fixture.writer.data_version() == version && bytes(fixture.files.root / "synthetic.sqlite") == before,
            "Lua catalog access wrote to SQLite");
    bool rejected = false;
    std::thread other([&] {
        try { command(engine, "check"); }
        catch (const std::runtime_error& error) {
            rejected = std::string(error.what()).find("initialization thread") != std::string::npos;
        }
    });
    other.join();
    require(rejected && calls == valid_calls, "Cross-thread lookup reached VM or callback");
}

void test_database_errors_and_unavailable() {
    Fixture fixture;
    fixture.files.write("errors.lua", R"LUA(
register_gm_command('lookup',function() assert(native_map_catalog(1,0)) end)
register_gm_command('caught',function(_,args)
    local ok,err = pcall(native_map_catalog,1,0)
    assert(not ok and type(err) == 'string' and err:find(args[1],1,true))
end)
)LUA");
    LuaEngine engine(fixture.files.root, false, fixture.lookup());
    require(engine.initialize() && engine.load_script("errors.lua"), "Error script failed");
    fixture.writer.execute("PRAGMA ignore_check_constraints=ON");
    fixture.writer.execute("UPDATE native_map_catalog SET record_sha256='synthetic-bad-hash' WHERE area=1");
    command(engine, "caught", {"Invalid native map SHA-256 text"});
    expect_error([&] { command(engine, "lookup"); }, "Invalid native map SHA-256 text");
    fixture.writer.execute("UPDATE native_map_catalog SET record_sha256=replace(hex(zeroblob(32)),'0','d') WHERE area=1");
    fixture.writer.execute("ALTER TABLE native_map_catalog RENAME TO synthetic_unavailable");
    command(engine, "caught", {"no such table"});
    expect_error([&] { command(engine, "lookup"); }, "no such table");
    fixture.writer.execute("ALTER TABLE synthetic_unavailable RENAME TO native_map_catalog");
    command(engine, "lookup");
    for (const bool fixture_mode : {false, true}) {
        LuaEngine unavailable(fixture.files.root, fixture_mode);
        require(unavailable.initialize() && unavailable.load_script("errors.lua"), "Default engine failed");
        command(unavailable, "caught", {"native_map_catalog unavailable"});
        expect_error([&] { command(unavailable, "lookup"); }, "native_map_catalog unavailable");
        require(unavailable.reload_all(), "Unavailable binding failed reload");
        command(unavailable, "caught", {"native_map_catalog unavailable"});
    }
}

void test_reload_and_callback_ownership() {
    Fixture fixture;
    std::weak_ptr<SqliteDatabase> lifetime = fixture.database;
    const auto script = [](int sequence) {
        return "local saved = native_map_catalog(1,0)\nassert(saved.source_line == " + std::to_string(sequence) + R"LUA()
register_gm_command('saved',function(_,args)
    assert(saved.source_line == tonumber(args[1]))
    assert(saved.raw_record == 'TEST' .. string.char(0,255,128))
end)
register_gm_command('next',function(_,args)
    assert(native_map_catalog(1,0).source_line == tonumber(args[1]))
end)
)LUA";
    };
    {
        // Mutable state is intentionally inside the callable, not an external counter.
        LuaEngine::NativeMapLookup callback = [db = fixture.database, sequence = 0](auto area, auto scene) mutable {
            auto result = db->native_map_catalog().lookup(NativeMapCatalog::current_dataset_id, area, scene);
            if (result) result->source_line = ++sequence;
            return result;
        };
        LuaEngine engine(fixture.files.root, false, callback);
        callback = {};
        fixture.database.reset();
        require(!lifetime.expired(), "Engine did not retain callable dependencies");
        require(engine.initialize() && engine.initialize(), "Initialization not idempotent");
        fixture.files.write("reload.lua", script(1));
        require(engine.load_script("reload.lua"), "Initial callback failed");
        command(engine, "saved", {"1"});
        fixture.files.write("reload.lua", script(2));
        require(engine.reload_all(), "Successful reload lost callable state");
        command(engine, "saved", {"2"});
        fixture.files.write("reload.lua", script(3) + "error('synthetic staged failure')");
        require(!engine.reload_all(), "Failed reload committed");
        command(engine, "saved", {"2"});
        command(engine, "next", {"4"});
        fixture.files.write("reload.lua", "synthetic invalid lua !!!");
        require(!engine.reload_all(), "Syntax failure committed");
        command(engine, "saved", {"2"});
        command(engine, "next", {"5"});
        fixture.files.write("reload.lua", script(6));
        require(engine.reload_all(), "Callback failed after rejected reloads");
        command(engine, "saved", {"6"});
        require(!lifetime.expired(), "Reload dropped captured database ownership");
    }
    require(lifetime.expired(), "Destroyed engine retained callback or VM ownership cycle");
}

void test_snapshot_survives_database_close() {
    Fixture fixture;
    fixture.files.write("snapshot.lua", R"LUA(
local saved = native_map_catalog(1,0)
register_gm_command('saved',function()
    assert(saved.raw_record == 'TEST' .. string.char(0,255,128))
    assert(saved.source.source_path == 'test-only/nonexistent-synthetic.bin')
    assert(saved.record_sha256 == string.rep('d',64))
end)
register_gm_command('lookup',function() native_map_catalog(1,0) end)
)LUA");
    LuaEngine engine(fixture.files.root, false,
        [weak = std::weak_ptr<SqliteDatabase>(fixture.database)](auto area, auto scene) {
            const auto db = weak.lock();
            if (!db) throw god2::DatabaseError("synthetic source closed");
            return db->native_map_catalog().lookup(NativeMapCatalog::current_dataset_id, area, scene);
        });
    require(engine.initialize() && engine.load_script("snapshot.lua"), "Snapshot script failed");
    fixture.writer.execute("DELETE FROM native_map_catalog");
    fixture.writer.execute("DELETE FROM native_data_sources");
    command(engine, "saved");
    fixture.database.reset();
    fixture.writer.db.reset();
    command(engine, "saved");
    expect_error([&] { command(engine, "lookup"); }, "synthetic source closed");
    require(!engine.reload_all(), "Closed source error ignored during reload");
    command(engine, "saved");
}
}

int main() {
    try {
        test_migration_guard();
        test_lookup_validation_and_read_only_snapshots();
        test_database_errors_and_unavailable();
        test_reload_and_callback_ownership();
        test_snapshot_survives_database_close();
        std::cout << "Native catalog Lua checks passed (test-only synthetic data)\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
