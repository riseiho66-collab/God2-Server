#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <vector>
struct sqlite3;
namespace god2 {
// Current NPCAppearData static display only: no tail66, placement or stats.
struct NativeNpcDisplayRecord {
    std::uint16_t key{};
    std::uint32_t source_line{},decoded_offset{};
    std::string record_sha256;
    std::vector<std::uint8_t> raw_record;
    std::array<std::uint8_t,28> prefix28{};
    std::array<std::uint8_t,16> name16{};
    std::uint16_t flags{},appearance_code{},body{},face{},head{},weapon{};
};
class NativeNpcDisplayCatalog final {
public:
    static constexpr const char* dataset_sha256="b770c11e516b488adba54ab7b2bee5d1fee3eaf1c5deb3dafe2e22962ccd343c";
    explicit NativeNpcDisplayCatalog(sqlite3*);
    static const char* schema() noexcept;
    std::size_t count() const; // Empty=0; incomplete/corrupt throws.
    std::optional<NativeNpcDisplayRecord> lookup(std::uint16_t key) const;
    // One complete integrity read for a scene, rather than one per NPC.
    bool contains_all(std::span<const std::uint16_t> keys) const;
private:
    std::vector<NativeNpcDisplayRecord> read_all() const;
    sqlite3* db_;
};
}
