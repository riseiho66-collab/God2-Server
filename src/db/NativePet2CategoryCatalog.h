#pragma once
#include "protocol/RecoveredPet2Stats.h"
#include <optional>
#include <vector>
struct sqlite3;
namespace god2 {
struct NativePet2Category {
    std::uint8_t group, index;
    std::uint32_t source_line;
    // Original CP950 bytes, excluding NUL; no Unicode/name-only species join.
    std::vector<std::uint8_t> name;
};
class NativePet2CategoryCatalog {
public:
    explicit NativePet2CategoryCatalog(sqlite3* db):db_(db) {}
    static const char* schema() noexcept;
    static constexpr const char* dataset_sha256="de6cada4b90996515a0e371eb8d503a39718b45a9103b9259c1f7f483b569772";
    std::size_t count() const;
    std::optional<NativePet2Category> lookup(RecoveredPet2Stats::CategorySelector) const;
private:
    std::vector<NativePet2Category> read_all() const;
    sqlite3* db_;
};
}
