#include "db/NativeSkillCatalog.h"
#include "db/SqliteDatabase.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"

#include <algorithm>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <utility>

namespace {
using god2::NativeSkillCatalog;
using god2::NativeSkillRecord;
static_assert(std::is_same_v<decltype(std::declval<const god2::SqliteDatabase&>().native_skill_catalog()),
                             const NativeSkillCatalog&>);

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

template<class F> void expect_database_error(F&& function, const char* message) {
    try { function(); } catch (const god2::DatabaseError&) { return; }
    throw std::runtime_error(message);
}

// TEST-ONLY synthetic bytes and provenance; no fixture asserts gameplay facts.
NativeSkillRecord synthetic_record(const std::string& dataset = "test-only-skill-catalog") {
    NativeSkillRecord record;
    record.source = {dataset, "test-only/synthetic.bin", std::string(64, 'a'),
                     std::string(64, 'a'), std::string(64, 'c'), "test-only-section",
                     "0x00000001", "0x00000002", 2};
    record.source_offset = 8;
    record.record_sha256 = std::string(64, 'd');
    record.raw_record.assign(110, 0xff);
    record.raw_record[0] = 1;
    record.raw_record[1] = 0;
    record.raw_record[2] = 0;
    record.definition_id = 1;
    return record;
}

struct Fixture {
    struct Close { void operator()(sqlite3* db) const { sqlite3_close_v2(db); } };
    std::unique_ptr<sqlite3, Close> db;

    Fixture() {
        sqlite3* raw = nullptr;
        const int status = sqlite3_open(":memory:", &raw);
        db.reset(raw);
        require(status == SQLITE_OK, "Unable to open test-only database");
        execute("PRAGMA foreign_keys=ON");
        const auto migrations = god2::default_sqlite_migrations();
        require(migrations.size() >= 5 && migrations[4].version == 5 &&
                migrations[4].name == "native_skill_catalog", "Missing migration 5");
        auto previous = migrations;
        previous.resize(4);
        god2::SqliteMigrationManager(db.get(), previous).migrate();
        god2::SqliteMigrationManager(db.get(), migrations).migrate();
        god2::SqliteMigrationManager(db.get(), migrations).migrate();
        god2::sqlite_detail::Statement count(db.get(), "SELECT count(*) FROM native_skill_catalog");
        require(count.row() && count.integer(0) == 0, "Migration synthesized original data");
    }

    void execute(const std::string& sql) { god2::sqlite_detail::execute(db.get(), sql); }
    NativeSkillCatalog reader() const { return NativeSkillCatalog(db.get()); }
    std::optional<NativeSkillRecord> lookup() const {
        return reader().lookup("test-only-skill-catalog", 0, 1);
    }
    void insert_source(const god2::NativeSkillSource& source) {
        god2::sqlite_detail::Statement insert(db.get(),
            "INSERT INTO native_data_sources VALUES(?,?,?,?,?,?,?,?,?)");
        insert.bind(1, source.dataset_id);
        insert.bind(2, source.source_path);
        insert.bind(3, source.source_sha256);
        insert.bind(4, source.decoded_sha256);
        insert.bind(5, source.native_image_sha256);
        insert.bind(6, source.source_section);
        insert.bind(7, source.loader_rva);
        insert.bind(8, source.lookup_rva);
        insert.bind(9, source.row_count);
        insert.done();
    }
    void insert_record(const NativeSkillRecord& record) {
        god2::sqlite_detail::Statement insert(db.get(),
            "INSERT INTO native_skill_catalog VALUES(?,?,?,?,?,?,?)");
        insert.bind(1, record.source.dataset_id);
        insert.bind(2, record.source_record_index);
        insert.bind(3, record.source_offset);
        insert.bind(4, record.record_sha256);
        insert.bind_blob(5, record.raw_record);
        insert.bind(6, record.kind);
        insert.bind(7, record.definition_id);
        insert.done();
    }
    void seed() {
        const auto record = synthetic_record();
        insert_source(record.source);
        insert_record(record);
    }
};

void test_ownership_and_missing() {
    std::optional<NativeSkillRecord> retained;
    const auto expected = synthetic_record();
    {
        Fixture fixture;
        require(!fixture.lookup(), "Empty catalog returned data");
        fixture.seed();
        auto other = synthetic_record("test-only-other");
        other.source.source_path = "test-only/other.bin";
        other.raw_record[2] = 0x80;
        fixture.insert_source(other.source);
        fixture.insert_record(other);
        fixture.execute("PRAGMA query_only=ON");
        retained = fixture.lookup();
        require(retained == expected, "Lookup lost bytes or provenance");
        require(fixture.reader().lookup(other.source.dataset_id, 0, 1) == other, "Incorrect source join");
        require(!fixture.reader().lookup(expected.source.dataset_id, 0, 2), "Missing id returned data");
        require(!fixture.reader().lookup(expected.source.dataset_id, 1, 1), "Missing kind returned data");
        require(!fixture.reader().lookup("missing", 0, 1), "Missing dataset returned data");
        require(!fixture.reader().lookup("' OR 1=1 --", 0, 1), "Dataset was not parameterized");
        require(sqlite3_next_stmt(fixture.db.get(), nullptr) == nullptr, "Statement leak");
        auto copy = *retained;
        copy.raw_record[3] = 0;
        copy.source.source_path.clear();
        require(*retained == expected && fixture.lookup() == expected, "Snapshot storage aliasing");
        fixture.execute("PRAGMA query_only=OFF");
        fixture.execute("DELETE FROM native_skill_catalog");
        fixture.execute("DELETE FROM native_data_sources");
        require(!fixture.lookup() && *retained == expected, "Mutation changed snapshot");
    }
    require(retained == expected, "Database closure invalidated snapshot");
}

void test_selectors_and_boundaries() {
    expect_database_error([] { NativeSkillCatalog reader(nullptr); }, "Null connection accepted");
    Fixture fixture;
    for (const auto kind : {std::numeric_limits<std::int64_t>::min(), std::int64_t{-1},
                            std::int64_t{4}, std::numeric_limits<std::int64_t>::max()})
        expect_database_error([&] { fixture.reader().lookup("test", kind, 1); }, "Invalid kind accepted");
    for (const auto id : {std::numeric_limits<std::int64_t>::min(), std::int64_t{-1}, std::int64_t{0},
                          std::int64_t{256}, std::numeric_limits<std::int64_t>::max()})
        expect_database_error([&] { fixture.reader().lookup("test", 0, id); }, "Invalid id accepted");
    for (const auto& dataset : {std::string{}, std::string("test\0only", 9)})
        expect_database_error([&] { fixture.reader().lookup(dataset, 0, 1); }, "Invalid dataset accepted");
    for (const bool maximum : {false, true}) {
        Fixture bounds;
        auto record = synthetic_record();
        record.source.row_count = maximum ? 1020 : 1;
        record.source_record_index = maximum ? 1019 : 0;
        record.kind = maximum ? 3 : 0;
        record.definition_id = maximum ? 255 : 1;
        record.source_offset = 8 + record.kind * 0x6e04 + (record.definition_id - 1) * 110;
        record.raw_record[0] = static_cast<std::uint8_t>(record.definition_id);
        record.raw_record[1] = static_cast<std::uint8_t>(record.kind);
        bounds.insert_source(record.source);
        bounds.insert_record(record);
        require(bounds.reader().lookup(record.source.dataset_id, record.kind, record.definition_id) == record,
                "Valid boundary rejected");
    }
}

void test_migration_constraints_and_corruption() {
    Fixture fixture;
    fixture.seed();
    const auto corrupt = [&](const char* table, const char* assignment, bool schema_rejects) {
        fixture.execute("SAVEPOINT test_only_corruption");
        const auto sql = std::string("UPDATE ") + table + " SET " + assignment;
        if (schema_rejects) {
            expect_database_error([&] { fixture.execute(sql); }, assignment);
            fixture.execute("PRAGMA ignore_check_constraints=ON");
        }
        fixture.execute(sql);
        expect_database_error([&] { fixture.lookup(); }, assignment);
        fixture.execute("ROLLBACK TO test_only_corruption");
        fixture.execute("RELEASE test_only_corruption");
        fixture.execute("PRAGMA ignore_check_constraints=OFF");
        require(fixture.lookup() == synthetic_record(), "Fixture restore failed");
        require(sqlite3_next_stmt(fixture.db.get(), nullptr) == nullptr, "Corruption statement leak");
    };
    for (const auto* assignment : {
            "source_record_index=-1", "source_record_index=1020", "source_record_index=1.5",
            "source_record_index='bad'", "source_record_index=X'00'", "source_offset=0",
            "source_offset=9", "source_offset=118", "source_offset=7.5", "source_offset='bad'",
            "source_offset=X'08'", "source_offset=9223372036854775807",
            "raw_record='test-only'", "raw_record=X''", "raw_record=zeroblob(109)",
            "raw_record=zeroblob(111)", "raw_record=zeroblob(110)",
            "raw_record=CAST(X'0101' || substr(raw_record,3) AS BLOB)",
            "record_sha256='bad'", "record_sha256=zeroblob(64)",
            "record_sha256=upper(record_sha256)",
            "record_sha256=replace(hex(zeroblob(32)),'0','g')"})
        corrupt("native_skill_catalog", assignment, true);
    corrupt("native_skill_catalog", "source_record_index=2", false);
    for (const auto* assignment : {
            "row_count=0", "row_count=-1", "row_count=32768", "row_count=1.5", "row_count=X'00'",
            "source_path=''", "source_section=''",
            "loader_rva=''", "lookup_rva=''", "source_sha256='bad'", "decoded_sha256='bad'",
            "native_image_sha256='bad'", "source_sha256=upper(source_sha256)"})
        corrupt("native_data_sources", assignment, true);
    // Immutable migration 4 allows these BLOBs; the strict reader must reject them.
    for (const auto* assignment : {"row_count=1021", "source_path=char(116,0,120)",
                                  "source_path=X'01'", "source_section=X'01'", "loader_rva=X'01'",
                                  "lookup_rva=X'01'", "source_sha256=zeroblob(64)",
                                  "decoded_sha256=zeroblob(64)", "native_image_sha256=zeroblob(64)",
                                  "decoded_sha256=replace(source_sha256,'a','b')"})
        corrupt("native_data_sources", assignment, false);
    expect_database_error([&] { fixture.insert_record(synthetic_record()); }, "Duplicate primary key accepted");
    auto duplicate = synthetic_record();
    duplicate.source_record_index = 1;
    expect_database_error([&] { fixture.insert_record(duplicate); }, "Duplicate lookup key accepted");
    auto orphan = synthetic_record("test-only-orphan");
    expect_database_error([&] { fixture.insert_record(orphan); }, "Orphan insert accepted");
    fixture.execute("PRAGMA foreign_keys=OFF");
    fixture.execute("DELETE FROM native_data_sources");
    expect_database_error([&] { fixture.lookup(); }, "Orphan treated as missing");
}

void test_null_types_and_duplicates() {
    Fixture fixture;
    fixture.seed();
    const auto shadow = [&](const char* table, const char* columns, const char* field, const char* expression) {
        // Views expose corrupt result types without SQLite affinity normalizing them.
        std::string projection = columns;
        const std::string column = field;
        const auto position = projection.find(column);
        require(position != std::string::npos, "Missing projection field");
        projection.replace(position, column.size(), std::string(expression) + " AS " + field);
        fixture.execute(std::string("CREATE TEMP VIEW ") + table + " AS SELECT " + projection + " FROM main." + table);
        expect_database_error([&] { fixture.lookup(); }, "Malformed projected row accepted");
        fixture.execute(std::string("DROP VIEW temp.") + table);
    };
    constexpr auto record_columns = "dataset_id,source_record_index,source_offset,record_sha256,raw_record,kind,definition_id";
    for (const auto* field : {"source_record_index", "source_offset", "record_sha256", "raw_record"})
        shadow("native_skill_catalog", record_columns, field, "NULL");
    shadow("native_skill_catalog", record_columns, "kind", "CAST(kind AS REAL)");
    shadow("native_skill_catalog", record_columns, "definition_id", "CAST(definition_id AS REAL)");
    constexpr auto source_columns = "dataset_id,source_path,source_sha256,decoded_sha256,native_image_sha256,"
                                    "source_section,loader_rva,lookup_rva,row_count";
    for (const auto* field : {"dataset_id", "source_path", "source_sha256", "decoded_sha256", "native_image_sha256",
                             "source_section", "loader_rva", "lookup_rva", "row_count"})
        shadow("native_data_sources", source_columns, field, "NULL");
    for (const auto* table : {"native_skill_catalog", "native_data_sources"}) {
        fixture.execute(std::string("CREATE TEMP VIEW ") + table + " AS SELECT * FROM main." + table +
                        " UNION ALL SELECT * FROM main." + table);
        expect_database_error([&] { fixture.lookup(); }, "Duplicate matches accepted");
        fixture.execute(std::string("DROP VIEW temp.") + table);
    }
    fixture.execute("ALTER TABLE native_skill_catalog RENAME TO test_only_unavailable");
    expect_database_error([&] { fixture.lookup(); }, "Schema failure treated as missing");
}

void test_migrated_accessor() {
    god2::SqliteDatabase database(":memory:");
    const auto& constant = database;
    expect_database_error([&] { constant.native_skill_catalog(); }, "Accessor usable before initialize");
    database.initialize();
    expect_database_error([&] { constant.native_skill_catalog(); }, "Accessor usable before migrate");
    database.migrate();
    require(!constant.native_skill_catalog().lookup(NativeSkillCatalog::current_dataset_id, 0, 1),
            "Empty accessor returned data");
    database.migrate();
    auto migrations = god2::default_sqlite_migrations();
    migrations.back().sql += "\nINVALID TEST ONLY SQL;";
    god2::SqliteDatabase failed(":memory:", migrations);
    failed.initialize();
    expect_database_error([&] { failed.migrate(); }, "Invalid migration succeeded");
    expect_database_error([&] { failed.native_skill_catalog(); }, "Failed migration exposed accessor");
}

void verify_import(const char* database_path, const char* source_path) {
    sqlite3* raw = nullptr;
    const int status = sqlite3_open_v2(database_path, &raw, SQLITE_OPEN_READONLY, nullptr);
    std::unique_ptr<sqlite3, Fixture::Close> db(raw);
    require(status == SQLITE_OK, "Cannot open imported test DB read-only");
    std::ifstream stream(source_path, std::ios::binary);
    require(stream.good(), "Cannot open current original source");
    const std::vector<std::uint8_t> source{std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>()};
    require(source.size() == 112660, "Unexpected source size");
    NativeSkillCatalog reader(db.get());
    const int counts[] = {121, 129, 87, 111};
    std::int64_t index = 0;
    for (int kind = 0; kind < 4; ++kind) {
        for (int id = 1; id <= 255; ++id) {
            const auto record = reader.lookup(NativeSkillCatalog::current_dataset_id, kind, id);
            if (id > counts[kind]) {
                require(!record, "Unpopulated definition was imported");
                continue;
            }
            require(record.has_value(), "Missing original record");
            require(record->source_record_index == index++, "Wrong source record order");
            require(record->source.row_count == 448 && record->source.source_section == "1.03" &&
                    record->source.loader_rva == "0x12d3b0" && record->source.lookup_rva == "0x11c520" &&
                    record->source.source_path == "Data2/Fight/Spg/cbspec2.bin" &&
                    record->source.source_sha256 == "7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51" &&
                    record->source.native_image_sha256 == "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763",
                    "Original provenance mismatch");
            require(std::equal(record->raw_record.begin(), record->raw_record.end(),
                                source.begin() + record->source_offset), "Original byte mismatch");
            const auto source_offset = static_cast<std::size_t>(record->source_offset);
            const auto client_threshold = static_cast<std::uint16_t>(
                source[source_offset + 0x42] | (static_cast<std::uint16_t>(source[source_offset + 0x43]) << 8));
            require(record->client_mp_threshold() == client_threshold,
                    "Client MP threshold differs from pinned source WORD+0x42");
        }
    }
    require(index == 448, "Wrong imported count");
    std::cout << "All 448 original skill records verified through read-only C++ lookup\n";
}
}

int main(int argc, char** argv) {
    try {
        if (argc == 4 && std::string(argv[1]) == "--verify-import") {
            verify_import(argv[2], argv[3]);
            return 0;
        }
        require(argc == 1, "Usage: native-skill-catalog [--verify-import TEST_DB CURRENT_CBSPEC2]");
        test_ownership_and_missing();
        test_selectors_and_boundaries();
        test_migration_constraints_and_corruption();
        test_null_types_and_duplicates();
        test_migrated_accessor();
        std::cout << "Native skill catalog C++20 checks passed (test-only synthetic data)\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
