#include "db/NativeSkillBookCatalog.h"
#include "db/SqliteDatabase.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"

#include <memory>
#include <stdexcept>
#include <string>

namespace {
void require(bool value) { if (!value) throw std::runtime_error("Native skill book reader check failed"); }
template<class F> void rejected(F&& call) {
    try { call(); } catch (const god2::DatabaseError&) { return; }
    throw std::runtime_error("Malformed native skill book query was accepted");
}
void test() {
    rejected([] { god2::NativeSkillBookCatalog missing(nullptr); });
    sqlite3* raw = nullptr;
    require(sqlite3_open(":memory:", &raw) == SQLITE_OK);
    struct Close { void operator()(sqlite3* p) const { sqlite3_close_v2(p); } };
    std::unique_ptr<sqlite3, Close> db(raw);
    god2::sqlite_detail::execute(raw, "PRAGMA foreign_keys=ON");
    god2::SqliteMigrationManager(raw, god2::default_sqlite_migrations()).migrate();
    god2::NativeSkillBookCatalog catalog(raw);
    require(!catalog.lookup(0, 1));
    rejected([&] { catalog.lookup(4, 1); });
    rejected([&] { catalog.lookup(0, 0); });
    god2::sqlite_detail::execute(raw,
        "INSERT INTO native_data_sources VALUES("
        "'current-skill-catalog-v1','1.03',"
        "'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',"
        "'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',"
        "'149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763',"
        "'1.03','0x12d3b0','0x11c520',448)");
    god2::sqlite_detail::execute(raw,
        "INSERT INTO native_data_sources VALUES("
        "'current-skill-books-v1','Data2/Patch/Comm/gamedata.csvZ',"
        "'70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731',"
        "'75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815',"
        "'149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763',"
        "'SKB','0x59420','0xA8E10',381)");
    god2::sqlite_detail::execute(raw,
        "INSERT INTO native_skill_catalog VALUES("
        "'current-skill-catalog-v1',0,8,"
        "'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',"
        "CAST(X'0100' || zeroblob(108) AS BLOB),0,1)");
    god2::sqlite_detail::execute(raw,
        "INSERT INTO native_skill_books VALUES("
        "'current-skill-books-v1',0,8916,707624,6501,"
        "'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',"
        "X'36353031',"
        "'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',"
        "zeroblob(396))");
    god2::sqlite_detail::execute(raw,
        "INSERT INTO native_skill_book_bindings VALUES("
        "'current-skill-books-v1','current-skill-catalog-v1',0,1,6501)");
    const auto found = catalog.lookup(0, 1);
    require(found && found->item_id == 6501 && found->source_line == 8916 &&
            found->source_record_index == 0 && found->decoded_offset == 707624 &&
            found->raw_record.size() == 4 && found->parsed_record.size() == 396 &&
            found->source.row_count == 381);
    require(!catalog.lookup(0, 2));
    god2::sqlite_detail::execute(raw,
        "UPDATE native_data_sources SET source_section='BAD' WHERE dataset_id='current-skill-books-v1'");
    rejected([&] { catalog.lookup(0, 1); });
}
}
int main(int argc, char** argv) {
    try {
        test();
        if (argc == 2) {
            sqlite3* raw = nullptr;
            require(sqlite3_open_v2(argv[1], &raw, SQLITE_OPEN_READONLY, nullptr) == SQLITE_OK);
            struct Close { void operator()(sqlite3* p) const { sqlite3_close_v2(p); } };
            std::unique_ptr<sqlite3, Close> db(raw);
            god2::NativeSkillBookCatalog catalog(raw);
            const auto first = catalog.lookup(0, 1);
            const auto other = catalog.lookup(1, 1);
            require(first && first->item_id == 6501 && first->source_line == 8916);
            require(other && other->item_id == 6601 && other->source_line == 9016);
            require(!catalog.lookup(0, 68));
        } else require(argc == 1);
        return 0;
    } catch (...) { return 1; }
}
