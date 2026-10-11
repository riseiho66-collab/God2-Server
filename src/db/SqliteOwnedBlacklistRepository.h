#pragma once
#include <sqlite3.h>
#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <string_view>
#include <vector>
namespace god2 {
class SqliteOwnedBlacklistRepository final {
public:
    // CUSTOM-0096: max10 active /4096 lifetime captured CP950 names.
    // IDs0 and FFFFFFFF are reserved; row IDs1..FFFFFFFE are global committed
    // contact-row DWORDs, not common IDs. Future contact authorities must share
    // this allocator or qualify a disjoint namespace before coexistence.
    struct Row {
        std::uint32_t row_id;
        std::uint64_t account,character,target_character;
        std::string name;
        bool active;
        bool operator==(const Row&) const=default;
    };
    explicit SqliteOwnedBlacklistRepository(sqlite3* db):db_(db) {}
    SqliteOwnedBlacklistRepository(const SqliteOwnedBlacklistRepository&)=delete;
    SqliteOwnedBlacklistRepository& operator=(const SqliteOwnedBlacklistRepository&)=delete;
    static void install_schema(sqlite3*);
    using Current=std::function<bool()>; // Actual pure Session/feature current; no SQL writes or transaction operations.
    struct Snapshot {bool supported;std::vector<Row> rows;bool operator==(const Snapshot&) const=default;};
    Snapshot load(std::uint64_t account,std::uint64_t character,Current);
    std::optional<Row> add(std::uint64_t account,std::uint64_t character,std::string_view name,Current);
    std::optional<Row> remove(std::uint64_t account,std::uint64_t character,std::uint32_t row_id,Current);
private:
    struct Operation;
    struct Root;
    sqlite3* db_;
    bool active_=false,reentered_=false;
    void qualify(bool installed);
    Root owner(std::uint64_t account,std::uint64_t character);
    std::vector<Row> rows(std::uint64_t account,std::uint64_t character);
};
}
