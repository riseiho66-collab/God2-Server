#pragma once
#include <cstdint>
#include <optional>
#include <string>
#include <vector>
struct sqlite3;
namespace god2 {
// Definitions only: 396-byte native metadata is NOT a player's 20-byte instance
// or an original weapon -> final attack/defense/appearance rule.
struct NativeWeaponRecord {
    std::string family;
    std::uint16_t item_id;
    std::uint32_t source_record_index,source_line,decoded_offset;
    std::string record_sha256,parsed_sha256;
    std::vector<std::uint8_t> raw_record,parsed_record;
};
class NativeWeaponCatalog {
    friend class SqliteOwnedInventoryRepository;
    sqlite3* db_;
    std::vector<NativeWeaponRecord> read() const;
public:
    explicit NativeWeaponCatalog(sqlite3* db);
    bool populated() const;
    std::optional<NativeWeaponRecord> lookup(std::uint16_t item) const;
};
}
