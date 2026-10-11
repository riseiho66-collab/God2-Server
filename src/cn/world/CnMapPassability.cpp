#include "cn/world/CnMapPassability.h"
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2cn {
namespace {
std::size_t area(std::int32_t width, std::int32_t height) {
    if (width <= 0 || height <= 0)
        throw std::invalid_argument("CN native map dimensions unavailable");
    const auto count = static_cast<std::uint64_t>(width) * static_cast<std::uint64_t>(height);
    // Keep recovered signed 32-bit native indexing representable. This is an
    // internal preparation boundary, not an original-server rejection rule.
    if (count > static_cast<std::uint64_t>(std::numeric_limits<std::int32_t>::max()) ||
        count > std::vector<std::uint8_t>().max_size())
        throw std::length_error("CN native map cell extent is not representable");
    return static_cast<std::size_t>(count);
}
void require_mask(CnMapPassability::TileMask mask) {
    if (mask.cells.size() != area(mask.width, mask.height))
        throw std::invalid_argument("CN native tile mask is incomplete");
}
}
CnMapPassability::CnMapPassability(Mode mode, std::int32_t width, std::int32_t height,
    std::int32_t origin_x, std::int32_t origin_y, std::vector<std::uint8_t> cells)
    : mode_(mode), width_(width), height_(height), origin_x_(origin_x),
      origin_y_(origin_y), cells_(std::move(cells)) {}

CnMapPassability CnMapPassability::from_mode0_window(std::int32_t origin_x,
    std::int32_t origin_y, std::span<const std::uint8_t> cells) {
    if (cells.size() != area(window_side, window_side))
        throw std::invalid_argument("CN native mode0 window is incomplete");
    return {Mode::window0, window_side, window_side, origin_x, origin_y,
        std::vector<std::uint8_t>(cells.begin(), cells.end())};
}
CnMapPassability CnMapPassability::from_mode2_cells(std::int32_t width,
    std::int32_t height, std::span<const std::uint8_t> cells) {
    if (cells.size() != area(width, height))
        throw std::invalid_argument("CN native mode2 grid is incomplete");
    return {Mode::grid2, width, height, 0, 0,
        std::vector<std::uint8_t>(cells.begin(), cells.end())};
}
std::uint8_t CnMapPassability::cell_at(std::int32_t x, std::int32_t y) const noexcept {
    std::int64_t local_x = x, local_y = y;
    if (mode_ == Mode::window0) {
        local_x = local_x - origin_x_ + 21;
        local_y = local_y - origin_y_ + 21;
    }
    if (local_x < 0 || local_y < 0 || local_x >= width_ || local_y >= height_) return 0;
    return cells_[static_cast<std::size_t>(local_y) * static_cast<std::size_t>(width_) +
        static_cast<std::size_t>(local_x)];
}
CnMapPassability CnMapPassability::compose_mode2(std::int32_t base_width,
    std::int32_t base_height, TileMask base, std::span<const BlockingOverlay> overlays) {
    // Native dimensions come from frame0; lookup may select a different frame.
    // Do not reproduce 0046B3B0's assert-and-return-1 for absent/short masks.
    (void)area(base_width, base_height);
    require_mask(base);
    if (base.width < base_width || base.height < base_height)
        throw std::invalid_argument("CN native base mask does not cover its extents");
    for (const auto& overlay : overlays) require_mask(overlay.mask);
    const std::int64_t side64 = 2 * std::max<std::int64_t>(base_width,
        (static_cast<std::int64_t>(base_height) + 1) / 2) + 1;
    if (side64 > std::numeric_limits<std::int32_t>::max())
        throw std::length_error("CN native mode2 dimensions overflow");
    const auto side = static_cast<std::int32_t>(side64);
    // Here zero is the explicit native 0045BE20 memset prior to composition,
    // not a substitute for missing assets. All supplied masks are complete.
    std::vector<std::uint8_t> cells(area(side, side), 0);
    const std::int64_t origin_x = side64 - base_width + (base_width & 1) - 1;
    for (std::int32_t row = 0; row < base_height; ++row) {
        for (std::int32_t col = 0; col < base_width; ++col) {
            const std::int64_t x = origin_x - row / 2 + col;
            const std::int64_t y = (static_cast<std::int64_t>(row) + 1) / 2 + col;
            // 0045BE20 skips out-of-grid writes after its assertion callback.
            if (x >= 0 && y >= 0 && x < side && y < side)
                cells[static_cast<std::size_t>(y * side + x)] =
                    base.cells[static_cast<std::size_t>(row) * base.width + col];
        }
    }
    for (const auto& overlay : overlays) {
        // Signed division truncates toward zero, as in native 00475CE0.
        const std::int64_t overlay_x = origin_x + overlay.native_x -
            static_cast<std::int64_t>(overlay.native_y) / 2;
        const std::int64_t overlay_y = overlay.native_x +
            (static_cast<std::int64_t>(overlay.native_y) + 1) / 2;
        for (std::int32_t row = 0; row < overlay.mask.height; ++row) {
            for (std::int32_t col = 0; col < overlay.mask.width; ++col) {
                const std::int64_t x = overlay_x - row / 2 + col;
                const std::int64_t y = overlay_y + (static_cast<std::int64_t>(row) + 1) / 2 + col;
                if (x < 0 || y < 0 || x >= side || y >= side) continue;
                if (overlay.mask.cells[static_cast<std::size_t>(row) * overlay.mask.width + col] == 0)
                    cells[static_cast<std::size_t>(y * side + x)] = 0;
            }
        }
    }
    return {Mode::grid2, side, side, 0, 0, std::move(cells)};
}
CnMapPassability CnMapPassability::compose_mode0(std::int32_t origin_x,
    std::int32_t origin_y, std::span<const std::uint8_t> prior,
    const std::array<std::span<const std::uint8_t>, 9>& chunks,
    std::span<const OutdoorObject> objects) {
    for (const auto chunk : chunks)
        if (!chunk.empty() && chunk.size() != 21 * 21 * 8)
            throw std::invalid_argument("CN loaded outdoor chunk incomplete");
    const auto count = area(window_side, window_side);
    if (prior.empty()) {
        if (std::any_of(chunks.begin(), chunks.end(), [](auto chunk) { return chunk.empty(); }))
            throw std::invalid_argument("CN initial outdoor window lacks full terrain coverage");
    } else if (prior.size() != count) {
        throw std::invalid_argument("CN prior outdoor window unavailable");
    }
    for (const auto& object : objects) require_mask(object.selected_mask);
    // With no prior snapshot, all bytes below are overwritten by nine complete
    // chunks before observation. Allocation value-initialization is not a
    // claim that native00470920 clears its passability memory (it does not).
    std::vector<std::uint8_t> cells = prior.empty() ? std::vector<std::uint8_t>(count) :
        std::vector<std::uint8_t>(prior.begin(), prior.end());
    for (std::size_t slot = 0; slot < chunks.size(); ++slot) {
        if (chunks[slot].empty()) continue; // native null-slot leaves prior cells
        const auto left = (slot % 3) * 21, top = (slot / 3) * 21;
        for (std::size_t y = 0; y < 21; ++y)
            for (std::size_t x = 0; x < 21; ++x)
                cells[(top + y) * 63 + left + x] =
                    (chunks[slot][(y * 21 + x) * 8 + 7] >> 6) & 1;
    }
    const auto write = [&](std::int64_t x, std::int64_t y, std::uint8_t value) {
        if (x >= 0 && y >= 0 && x < 63 && y < 63)
            cells[static_cast<std::size_t>(y * 63 + x)] = value;
    };
    // Per-object mask then its two markers, exactly in native traversal order.
    // Sorting objects or applying all markers last would change overlapping cells.
    for (const auto& object : objects) {
        const auto local_x = std::int64_t(object.world_x) - origin_x + 21;
        const auto local_y = std::int64_t(object.world_y) - origin_y + 21;
        const auto mask = object.selected_mask;
        for (std::int32_t row = 0; row < mask.height; ++row)
            for (std::int32_t col = 0; col < mask.width; ++col)
                if (mask.cells[static_cast<std::size_t>(row) * mask.width + col] == 0)
                    write(local_x - row / 2 + col,
                        local_y + (std::int64_t(row) + 1) / 2 + col, 0);
        for (const auto marker : object.markers)
            if (marker.a >= 0)
                write(local_x + marker.a - std::int64_t(marker.b) / 2,
                    local_y + marker.a + (std::int64_t(marker.b) + 1) / 2, 2);
    }
    return {Mode::window0, window_side, window_side, origin_x, origin_y, std::move(cells)};
}
}
