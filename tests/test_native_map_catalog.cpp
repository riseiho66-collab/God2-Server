#include "db/NativeMapCatalog.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"

#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>

namespace {
using god2::NativeMapCatalog;
using god2::NativeMapRecord;

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

template<class F> void expect_database_error(F&& function, const char* message) {
    try { function(); } catch (const god2::DatabaseError&) { return; }
    throw std::runtime_error(message);
}

// TEST-ONLY synthetic bytes and provenance. No fixture value asserts native gameplay facts.
NativeMapRecord synthetic_record(const std::string& dataset_id = NativeMapCatalog::current_dataset_id) {
    NativeMapRecord record;
    record.source = {dataset_id, "test-only/synthetic-map-catalog.bin", std::string(64, 'a'),
                     std::string(64, 'b'), std::string(64, 'c'), "test-only-section",
                     "0x00000001", "0x00000002", 2};
    record.source_record_index = 0;
    record.source_line = 1;
    record.record_sha256 = std::string(64, 'd');
    record.raw_record = {'T', 'E', 'S', 'T', '-', 'O', 'N', 'L', 'Y', 0, 0xff, 0x80};
    record.area = 1;
    record.scene = 0;
    record.kind = 0;
    return record;
}

struct Fixture {
    struct Close { void operator()(sqlite3* db) const { sqlite3_close_v2(db); } };
    std::unique_ptr<sqlite3, Close> db;

    Fixture() {
        sqlite3* raw = nullptr;
        const int status = sqlite3_open(":memory:", &raw);
        db.reset(raw);
        require(status == SQLITE_OK, "Unable to open test-only catalog database");
        execute("PRAGMA foreign_keys=ON");
        const auto migrations = god2::default_sqlite_migrations();
        require(migrations.size() >= 4 && migrations[3].version == 4,
                "Native map catalog tests require default migration 4");
        god2::SqliteMigrationManager(db.get(), migrations).migrate();
        god2::SqliteMigrationManager(db.get(), migrations).migrate();
        for (const auto* table : {"native_data_sources", "native_map_catalog"}) {
            const auto sql = std::string("SELECT count(*) FROM ") + table;
            god2::sqlite_detail::Statement count(db.get(), sql.c_str());
            require(count.row() && count.integer(0) == 0, "Migration synthesized native catalog data");
        }
    }

    void execute(const std::string& sql) { god2::sqlite_detail::execute(db.get(), sql); }
    NativeMapCatalog reader() const { return NativeMapCatalog(db.get()); }
    std::optional<NativeMapRecord> lookup() const {
        return reader().lookup(NativeMapCatalog::current_dataset_id, 1, 0);
    }
    void insert_source(const god2::NativeMapSource& source) {
        god2::sqlite_detail::Statement insert(db.get(),
            "INSERT INTO native_data_sources(dataset_id,source_path,source_sha256,decoded_sha256,"
            "native_image_sha256,source_section,loader_rva,lookup_rva,row_count) VALUES(?,?,?,?,?,?,?,?,?)");
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
    void insert_record(const NativeMapRecord& record) {
        god2::sqlite_detail::Statement insert(db.get(),
            "INSERT INTO native_map_catalog(dataset_id,source_record_index,source_line,record_sha256,"
            "raw_record,area,scene,kind) VALUES(?,?,?,?,?,?,?,?)");
        insert.bind(1, record.source.dataset_id);
        insert.bind(2, record.source_record_index);
        insert.bind(3, record.source_line);
        insert.bind(4, record.record_sha256);
        insert.bind_blob(5, record.raw_record);
        insert.bind(6, record.area);
        insert.bind(7, record.scene);
        insert.bind(8, record.kind);
        insert.done();
    }
    void seed() {
        auto record = synthetic_record();
        insert_source(record.source);
        insert_record(record);
        record.source_record_index = 1;
        record.source_line = 2;
        record.area = 16;
        record.scene = 1023;
        record.kind = 3;
        insert_record(record);
    }
};

void test_lookup_ownership_and_missing() {
    std::optional<NativeMapRecord> retained;
    const auto expected = synthetic_record();
    {
        Fixture fixture;
        require(!fixture.lookup(), "Empty migrated catalog returned data");
        fixture.seed();
        fixture.execute("PRAGMA query_only=ON");
        retained = fixture.lookup();
        require(retained && *retained == expected, "Lookup lost raw bytes or source provenance");
        auto maximum = expected;
        maximum.source_record_index = 1;
        maximum.source_line = 2;
        maximum.area = 16;
        maximum.scene = 1023;
        maximum.kind = 3;
        require(fixture.reader().lookup(maximum.source.dataset_id, 16, 1023) == maximum,
                "Maximum selector/kind failed");
        require(!fixture.reader().lookup(expected.source.dataset_id, 1, 1), "Missing scene returned data");
        require(!fixture.reader().lookup(expected.source.dataset_id, 2, 0), "Missing area returned data");
        require(!fixture.reader().lookup("test-only-missing-dataset", 1, 0), "Missing dataset returned data");
        require(!fixture.reader().lookup("' OR 1=1 --", 1, 0), "Dataset selector was not parameterized");
        require(sqlite3_next_stmt(fixture.db.get(), nullptr) == nullptr, "Lookup leaked a statement");
        fixture.execute("PRAGMA query_only=OFF");
        auto copy = *retained;
        copy.raw_record[0] = 0;
        copy.source.source_path.clear();
        require(*retained == expected && fixture.lookup() == expected, "Returned data did not own its storage");
        fixture.execute("DELETE FROM native_map_catalog");
        fixture.execute("DELETE FROM native_data_sources");
        require(!fixture.lookup() && *retained == expected, "Database mutation changed an owned result");
    }
    require(retained && *retained == expected, "Database closure invalidated returned bytes/provenance");
}

void test_invalid_selectors() {
    expect_database_error([] { NativeMapCatalog reader(nullptr); }, "Null connection accepted");
    Fixture fixture;
    for (const auto value : {std::numeric_limits<std::int64_t>::min(), std::int64_t{-1},
                             std::int64_t{0}, std::int64_t{17},
                             std::numeric_limits<std::int64_t>::max()}) {
        expect_database_error([&] { fixture.reader().lookup(NativeMapCatalog::current_dataset_id, value, 0); },
                              "Invalid area treated as a missing key");
    }
    for (const auto value : {std::numeric_limits<std::int64_t>::min(), std::int64_t{-1},
                             std::int64_t{1024}, std::numeric_limits<std::int64_t>::max()}) {
        expect_database_error([&] { fixture.reader().lookup(NativeMapCatalog::current_dataset_id, 1, value); },
                              "Invalid scene treated as a missing key");
    }
    for (const auto& dataset : {std::string{}, std::string("test\0only", 9)}) {
        expect_database_error([&] { fixture.reader().lookup(dataset, 1, 0); }, "Invalid dataset accepted");
    }
}

void test_storage_boundaries() {
    for (const bool maximum : {false, true}) {
        Fixture fixture;
        auto record = synthetic_record();
        record.source.row_count = maximum ? 32767 : 1;
        record.source_record_index = maximum ? 32766 : 0;
        record.source_line = maximum ? std::numeric_limits<std::int64_t>::max() : 1;
        record.raw_record.assign(maximum ? 4095 : 1, 'T');
        fixture.insert_source(record.source);
        fixture.insert_record(record);
        require(fixture.lookup() == record, "Valid storage boundary rejected or narrowed");
    }
}

void test_source_join_and_orphans() {
    Fixture fixture;
    fixture.seed();
    auto other = synthetic_record("test-only-other-dataset");
    other.source.source_path = "test-only/other.bin";
    other.source.source_sha256 = std::string(64, 'e');
    other.raw_record = {0xff, 0, 0x7f};
    fixture.insert_source(other.source);
    fixture.insert_record(other);
    require(fixture.lookup() == synthetic_record(), "Joined another dataset's source");
    require(fixture.reader().lookup(other.source.dataset_id, 1, 0) == other,
            "Dataset-specific lookup lost its source or bytes");
    fixture.execute("PRAGMA foreign_keys=OFF");
    fixture.execute("DELETE FROM native_data_sources WHERE dataset_id='current-map-catalog-v1'");
    expect_database_error([&] { fixture.lookup(); }, "Orphaned catalog record treated as missing");
    require(fixture.reader().lookup(other.source.dataset_id, 1, 0) == other,
            "Orphan rejection affected another dataset");
    require(sqlite3_next_stmt(fixture.db.get(), nullptr) == nullptr, "Corruption path leaked a statement");
}

void test_corrupt_record_and_source() {
    Fixture fixture;
    fixture.seed();
    fixture.execute("PRAGMA ignore_check_constraints=ON");
    const auto corrupt = [&](const char* table, const char* assignment) {
        fixture.execute("SAVEPOINT test_only_corruption");
        fixture.execute(std::string("UPDATE ") + table + " SET " + assignment +
                        (std::string(table) == "native_map_catalog" ? " WHERE source_record_index=0" : ""));
        expect_database_error([&] { fixture.lookup(); }, assignment);
        fixture.execute("ROLLBACK TO test_only_corruption");
        fixture.execute("RELEASE test_only_corruption");
        require(fixture.lookup() == synthetic_record(), "Corruption recovery did not restore fixture");
    };
    for (const auto* assignment : {
            "source_record_index=-1", "source_record_index=2", "source_record_index=32767", "source_record_index=1.5", "source_record_index='bad'",
            "source_record_index=X'00'", "source_line=0", "source_line=-1", "source_line=1.5",
            "source_line='bad'", "source_line=X'00'", "kind=-1", "kind=4", "kind=1.5", "kind='bad'",
            "kind=X'00'", "kind=9223372036854775807", "raw_record='test-only'", "raw_record=1",
            "raw_record=X''", "raw_record=zeroblob(4096)", "record_sha256='bad'", "record_sha256=zeroblob(64)",
            "record_sha256=upper(record_sha256)",
            "record_sha256=replace(hex(zeroblob(32)),'0','g')"})
        corrupt("native_map_catalog", assignment);
    for (const auto* assignment : {
            "row_count=0", "row_count=-1", "row_count=32768", "row_count=1.5", "row_count='bad'", "row_count=X'01'",
            "row_count=9223372036854775808", "source_path=''", "source_path=X'01'",
            "source_path=char(116,0,120)", "source_section=''", "source_section=X'01'",
            "loader_rva=''", "loader_rva=X'01'", "lookup_rva=''", "lookup_rva=X'01'",
            "source_sha256='bad'", "source_sha256=zeroblob(64)", "decoded_sha256='bad'",
            "decoded_sha256=zeroblob(64)", "native_image_sha256='bad'",
            "native_image_sha256=zeroblob(64)",
            "source_sha256=upper(source_sha256)", "decoded_sha256=upper(decoded_sha256)",
            "native_image_sha256=upper(native_image_sha256)",
            "source_sha256=replace(hex(zeroblob(32)),'0','g')",
            "decoded_sha256=replace(hex(zeroblob(32)),'0','g')",
            "native_image_sha256=replace(hex(zeroblob(32)),'0','g')"})
        corrupt("native_data_sources", assignment);
}

void test_null_types_and_duplicates() {
    Fixture fixture;
    fixture.seed();
    const auto shadow = [&](const char* table, const char* columns, const char* field, const char* expression) {
        // A temporary view exposes malformed read results without weakening the real migration.
        // SQLite affinity would otherwise normalize exact REAL selectors back to INTEGER.
        std::string projection = columns;
        const std::string column = field;
        const auto position = projection.find(column);
        require(position != std::string::npos, "Missing corruption projection field");
        projection.replace(position, column.size(), std::string(expression) + " AS " + field);
        fixture.execute(std::string("CREATE TEMP VIEW ") + table + " AS SELECT " + projection + " FROM main." + table);
        expect_database_error([&] { fixture.lookup(); }, "Malformed projected row accepted");
        fixture.execute(std::string("DROP VIEW temp.") + table);
    };
    constexpr auto record_columns = "dataset_id,source_record_index,source_line,record_sha256,raw_record,area,scene,kind";
    for (const auto* field : {"source_record_index", "source_line", "record_sha256", "raw_record", "kind"})
        shadow("native_map_catalog", record_columns, field, "NULL");
    shadow("native_map_catalog", record_columns, "area", "CAST(area AS REAL)");
    shadow("native_map_catalog", record_columns, "scene", "CAST(scene AS REAL)");
    constexpr auto source_columns = "dataset_id,source_path,source_sha256,decoded_sha256,native_image_sha256,"
                                    "source_section,loader_rva,lookup_rva,row_count";
    for (const auto* field : {"dataset_id", "source_path", "source_sha256", "decoded_sha256", "native_image_sha256",
                             "source_section", "loader_rva", "lookup_rva", "row_count"})
        shadow("native_data_sources", source_columns, field, "NULL");
    for (const auto* table : {"native_map_catalog", "native_data_sources"}) {
        fixture.execute(std::string("CREATE TEMP VIEW ") + table + " AS SELECT * FROM main." + table +
                        " UNION ALL SELECT * FROM main." + table);
        expect_database_error([&] { fixture.lookup(); }, "Duplicate matched rows were silently accepted");
        fixture.execute(std::string("DROP VIEW temp.") + table);
    }
    fixture.execute("ALTER TABLE native_map_catalog RENAME TO test_only_unavailable_catalog");
    expect_database_error([&] { fixture.lookup(); }, "SQLite schema failure treated as a missing key");
}
}

int main() {
    try {
        test_lookup_ownership_and_missing();
        test_invalid_selectors();
        test_storage_boundaries();
        test_source_join_and_orphans();
        test_corrupt_record_and_source();
        test_null_types_and_duplicates();
        std::cout << "Native map catalog C++20 checks passed (test-only synthetic data)\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
