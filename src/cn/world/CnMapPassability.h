#pragma once
#include <array>
#include <cstdint>
#include <span>
#include <vector>

namespace god2cn {
// Owned snapshot of already recovered native cell data. These constructors do
// not decode a map asset or establish its map ID, revision or session authority.
// Never construct it from a movement packet or fill missing cells with zero.
class CnMapPassability {
public:
    // Exact initialized snapshot: includes mode, origin, dimensions and every
    // raw cell. Geometry equality is not permission or native resource identity.
    bool operator==(const CnMapPassability&) const = default;
    enum class Mode { window0, grid2 };
    static constexpr std::int32_t window_side = 63;
    // 00470310: origin is native map+103C/+1040, NOT the window's top-left.
    // A complete, initialized window and its live map context are prerequisites.
    static CnMapPassability from_mode0_window(std::int32_t origin_x,
        std::int32_t origin_y, std::span<const std::uint8_t> cells);
    // 0045C2A0: cells are row-major, preserving the full native byte value.
    static CnMapPassability from_mode2_cells(std::int32_t width,
        std::int32_t height, std::span<const std::uint8_t> cells);
    // 0045BE20 input after frame selection in 0046B3B0. Dimensions here belong
    // to that selected mask; frame-zero base extents are passed separately.
    struct TileMask {
        std::int32_t width;
        std::int32_t height;
        std::span<const std::uint8_t> cells;
    };
    struct BlockingOverlay {
        std::int32_t native_x; // object+14 before 00475CE0
        std::int32_t native_y; // object+18 before 00475CE0
        TileMask mask;
    };
    static CnMapPassability compose_mode2(std::int32_t base_extent_width,
        std::int32_t base_extent_height, TileMask selected_base_mask,
        std::span<const BlockingOverlay> overlays);

    struct NativeMarker { std::int32_t a, b; };
    struct OutdoorObject {
        // Native object+14/+18 are already world-grid coordinates here.
        std::int32_t world_x, world_y;
        TileMask selected_mask;
        // ModelDat+2C/+30 and+34/+38; a<0 disables that marker.
        std::array<NativeMarker, 2> markers;
    };
    // 0046F630: nine LOADED native chunk slots in row-major order, each
    // 21*21*8 bytes. Empty spans mean null slots and preserve prior bytes.
    // prior_cells must be the complete initialized native window before this
    // update, or empty ONLY when all nine chunks overwrite every cell.
    // Objects must be the complete native traversal in its exact order:
    // chunk y=center-2..center+1, x=center-2..center+1, then linked-list order.
    // Missing chunk lifecycle or object evidence cannot be replaced by empty
    // arguments. The caller owns those prerequisites and the map revision.
    static CnMapPassability compose_mode0(std::int32_t origin_x,
        std::int32_t origin_y, std::span<const std::uint8_t> prior_cells,
        const std::array<std::span<const std::uint8_t>, 9>& loaded_chunks,
        std::span<const OutdoorObject> ordered_objects);

    // Outside an established grid/window is native zero. An absent map is
    // represented by absence of this object, never by an all-zero substitute.
    std::uint8_t cell_at(std::int32_t x, std::int32_t y) const noexcept;
    Mode mode() const noexcept { return mode_; }
    std::int32_t width() const noexcept { return width_; }
    std::int32_t height() const noexcept { return height_; }
    // Actual initialized grid bytes for native null-slot preservation. These
    // are the existing cache snapshot, never a generated zero-window baseline.
    std::span<const std::uint8_t> initialized_cells() const noexcept {return cells_;}
private:
    CnMapPassability(Mode mode, std::int32_t width, std::int32_t height,
        std::int32_t origin_x, std::int32_t origin_y,
        std::vector<std::uint8_t> cells);
    Mode mode_;
    std::int32_t width_, height_, origin_x_, origin_y_;
    std::vector<std::uint8_t> cells_;
};
}
