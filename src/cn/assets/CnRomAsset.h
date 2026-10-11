#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <span>
#include <vector>

namespace god2cn {
// IGSROM02 geometry/action metadata. Keeps decoded bytes; does not render,
// execute action steps or perform00417620's cross-ROM command rewriting.
class CnRomAsset {
public:
    struct ImageExtent { std::int32_t width, height; };
    struct TileGeometry { std::int32_t width, height, frame_count; };
    struct Record {
        std::array<std::uint8_t,8> tag;
        std::size_t offset, size;
    };
    struct Frame { Record pool, blocks; };
    struct Action {
        Record header;
        std::uint32_t id;
        std::vector<Record> steps;
        std::vector<Frame> frames;
    };
    static CnRomAsset from_resource(std::span<const std::uint8_t> bytes, std::size_t max_plain_bytes);
    static CnRomAsset load_file(const std::filesystem::path& path,
        std::size_t max_encoded_bytes, std::size_t max_plain_bytes);
    //0041B590: <=256 is positional; larger IDs use first matchingaction ID.
    const Action* find_action(std::uint32_t id) const noexcept;
    //00419FA0 terminal in firststep ->image;004183F0 full actionextents;
    //00475960 width0 choosesactionextent, otherwiseexplicitsize, thenceilgrid.
    std::optional<TileGeometry> tile_geometry(std::uint32_t action_id,
        std::int32_t declared_width, std::int32_t declared_height) const;
    const auto& images() const noexcept { return images_; }
    const auto& actions() const noexcept { return actions_; }
    //00418830/00419110 start ROM identity DWORD atFFFFFFFF, then each
    // ACTINDEX overwrites it with zero-extended WORD. No guessed native slot.
    std::uint32_t native_rom_identity() const noexcept {
        return act_index_?static_cast<std::uint32_t>(*act_index_):0xffffffffu;
    }
    const auto& native_act_index_word() const noexcept {return act_index_;}
    //0041B590's raw result:0..256 pass unchanged without dereferencing an
    // action; larger IDs use first matching registered action, elseFFFF.
    // This is an operand projection, not proof the returned action exists.
    std::uint16_t native_action_index_operand(std::uint16_t id) const noexcept;
    std::span<const std::uint8_t> raw_record(const Record& record) const;
private:
    CnRomAsset()=default;
    std::vector<std::uint8_t> bytes_;
    std::vector<ImageExtent> images_;
    std::vector<Action> actions_;
    std::optional<std::uint16_t> act_index_;
};
}
