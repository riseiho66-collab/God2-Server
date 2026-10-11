#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <vector>
struct sqlite3;
namespace god2 {
// Explicit server-owned scene records. A consumer address never supplies rows.
// Importers must establish complete map/record evidence before native admission.
struct StoredWorldDisplay {
    std::uint16_t area{},scene{};
    std::array<std::uint8_t,21> logical{};
    std::string origin,provenance;
    bool operator==(const StoredWorldDisplay&) const=default;
};
struct StoredMonsterLevel {
    std::uint16_t area{},scene{},identity{},level{};
    std::string origin,provenance;
    bool operator==(const StoredMonsterLevel&) const=default;
};
class SqliteWorldDisplayRepository {
public:
    explicit SqliteWorldDisplayRepository(sqlite3* db):db_(db){}
    static const char* schema() noexcept;
    static const char* level_schema() noexcept;
    // Immutable insert: conflicting instance records are rejected, never replaced.
    void insert(const StoredWorldDisplay& record);
    void insert_level(const StoredMonsterLevel& record);
    std::vector<StoredMonsterLevel> load_levels(std::uint16_t area,std::uint16_t scene,bool isolated_test=false) const;
    std::vector<StoredWorldDisplay> load(std::uint16_t area,std::uint16_t scene,bool isolated_test=false) const;
private:
    sqlite3* db_;
};
}
