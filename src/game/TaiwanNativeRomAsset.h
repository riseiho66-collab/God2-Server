#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <optional>
#include <span>
#include <vector>

namespace god2 {
// Independently recovered TW IGSROM02 sections and static type7 geometry.
// No native ROMFILE slot/path/ACTINDEX correspondence is inferred. Palette,
// rendering, action execution and cross-ROM command rewriting remain opaque.
class TaiwanNativeRomAsset final {
public:
    struct Record {
        std::array<std::uint8_t,8> tag;
        std::size_t header_offset,offset,size;
    };
    struct ImageExtent {std::int32_t width,height;};
    struct Image {
        std::size_t ordinal;
        Record record;
        std::optional<ImageExtent> extent;
    };
    struct Frame {Record pool,blocks;};
    struct Action {
        std::size_t ordinal;
        Record header;
        std::uint32_t id;
        std::vector<Record> steps;
        std::vector<Frame> frames;
    };
    struct TileGeometry {std::int32_t width,height,frame_count;};
    static std::optional<TaiwanNativeRomAsset> from_selected_resource(
        std::filesystem::path actual_source,std::span<const std::uint8_t> encoded,std::size_t max_plain_bytes);
    static std::optional<TaiwanNativeRomAsset> load_selected_file(
        const std::filesystem::path& actual_source,std::size_t max_encoded_bytes,std::size_t max_plain_bytes);
    // Actual0042AF40: unsigned DWORD <=256 is positional, larger operand is
    // first matching DWORD action ID. Missing is never silently action zero.
    const Action* find_action(std::uint32_t full_action_operand) const noexcept;
    // Actual0044A800: width0 obtains0042B4C0 full-action extent; otherwise
    // uses declared dimensions. Both require0042D050's real first-step
    // command0 terminal, frame/image identity and positive signed16 image.
    std::optional<TileGeometry> tile_geometry(std::uint32_t full_action_operand,
        std::int32_t declared_width,std::int32_t declared_height) const;
    std::span<const std::uint8_t> raw_record(const Record&) const;
    const std::filesystem::path& source() const;
    const std::vector<std::uint8_t>& encoded_bytes() const;
    const std::vector<std::uint8_t>& decoded_bytes() const;
    const std::vector<Record>& records() const;
    const std::vector<Image>& images() const;
    const std::vector<Action>& actions() const;
    // Original native identity, not a ROMFILE ordinal or manager slot.
    // Missing ACTINDEX preserves actual reader initializerFFFFFFFF.
    std::uint32_t native_rom_identity() const;
private:
    struct Storage;
    explicit TaiwanNativeRomAsset(std::shared_ptr<const Storage>);
    const Storage& storage() const;
    std::shared_ptr<const Storage> storage_;
};
}
