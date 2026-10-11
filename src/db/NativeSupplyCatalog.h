#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

struct sqlite3;

namespace god2 {

// Current MED02 tooltip declarations only. Consumption and caps are separate
// CUSTOM-0016 gameplay policy, not inferred from this catalog.
struct NativeSupplyDeclaration {
    std::uint16_t item_id{};
    std::uint32_t declared_hp{};
    std::uint32_t declared_mp{};
    std::int64_t source_record_index{};
    std::int64_t source_line{};
    std::string record_sha256;
    std::vector<std::uint8_t> raw_record;
    std::vector<std::uint8_t> tooltip_bytes;
    bool operator==(const NativeSupplyDeclaration&) const = default;
};

class NativeSupplyCatalog final {
public:
    static constexpr char current_dataset_id[] = "current-med02-recovery-v1";
    static constexpr char current_source_sha256[] =
        "70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731";
    static constexpr char current_catalog_sha256[] =
        "ebb3882ce833ac8bd45f5b6c341a67ff17039ea3fd30ab31a715d2d6985c4d9b";
    explicit NativeSupplyCatalog(sqlite3* db);
    // False only if BOTH source and its rows are absent. Every read validates
    // the complete pinned source plus71 declarations in one SQLite snapshot.
    // Present/incomplete/orphan/corrupt data throws; never fall back on error.
    bool is_imported() const;
    std::optional<NativeSupplyDeclaration> lookup(std::uint16_t item_id) const;
private:
    std::vector<NativeSupplyDeclaration> read() const;
    sqlite3* db_;
};

}
