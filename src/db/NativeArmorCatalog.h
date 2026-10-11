#pragma once
#include <cstdint>
#include <optional>
#include <string>
#include <vector>
struct sqlite3;
namespace god2 {
// Definitions only: 396-byte native metadata is NOT a player's 20-byte instance
// or an original armor -> final attack/defense/appearance rule.
struct NativeArmorRecord {
    std::string family;
    std::uint16_t item_id;
    std::uint32_t source_record_index,source_line,decoded_offset;
    std::string record_sha256,parsed_sha256;
    std::vector<std::uint8_t> raw_record,parsed_record;
};
class NativeArmorCatalog {
    friend class SqliteOwnedInventoryRepository;
    sqlite3* db_;
    std::vector<NativeArmorRecord> read() const;
public:
    static constexpr const char* catalog_sha256="29d1de3729c843571c3a7bc117beb12289bd7110932ec45fc5d846b627282efe";
    static std::string schema();
    explicit NativeArmorCatalog(sqlite3* db);
    bool populated() const;
    std::optional<NativeArmorRecord> lookup(std::uint16_t item) const;
    // Source-supported part only; caller must independently enforce owned
    // instance, role admission, combat rules and appearance authority.
    std::optional<std::uint8_t> equipment_slot(std::uint16_t item) const;
};
}
