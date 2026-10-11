#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>
struct sqlite3;
namespace god2 {
struct NativeMapItemSource {
    std::uint16_t item_id{};
    std::uint32_t source_line{},decoded_offset{};
    std::string record_sha256;
    std::vector<std::uint8_t> raw_record;
    std::uint32_t category_code{};
    std::vector<std::uint8_t> resource_name;
    std::uint16_t icon_id{};
    std::vector<std::uint8_t> name_bytes,description_bytes;
    std::uint16_t effect_code{};
    // Raw source columns14..25, not packed inventory instance metadata.
    // RowDesc names columns14..24; the last column remains unnamed.
    std::array<std::uint8_t,12> source_flags{};
    bool operator==(const NativeMapItemSource&) const = default;
};
// SOURCE_DISPLAY_ONLY. Qualification of original text/flags is not ownership,
// use authorization, map selection, grant, consumption or a quest rule.
class NativeMapItemCatalog final {
public:
    static constexpr char authority[]="SOURCE_DISPLAY_ONLY";
    static constexpr char source_file[]="Data2/Patch/Comm/gamedata.csvZ";
    static constexpr char source_sha256[]="70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731";
    static constexpr char decoded_sha256[]="75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815";
    explicit NativeMapItemCatalog(sqlite3* db);
    // False only for both installed source tables empty. Missing schema or any
    // incomplete/corrupt catalog throws. Each call validates BOTH exact rows.
    bool is_imported() const;
    bool populated() const;
    bool contains(std::uint16_t item_id) const;
    std::optional<NativeMapItemSource> lookup(std::uint16_t item_id) const;
private:
    std::optional<std::array<NativeMapItemSource,2>> read() const;
    sqlite3* db_;
};
}
