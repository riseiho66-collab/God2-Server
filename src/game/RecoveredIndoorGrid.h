#pragma once
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <span>
#include <stdexcept>
#include <vector>

namespace god2 {
struct PassGrid {
    int width = 0, height = 0;
    std::vector<std::uint8_t> cells;
};

struct Placement {
    PassGrid grid;
    int x = 0, y = 0;
};

// Isolated reconstruction of 36C30/36B60; bytes remain opaque.
class RecoveredIndoorGrid {
public:
    explicit RecoveredIndoorGrid(const PassGrid& base,
                                 std::span<const Placement> placements = {}) {
        build(base, placements);
    }

    void build(const PassGrid& base, std::span<const Placement> placements = {}) {
        validate(base);
        if (placements.size() > 1024)
            throw std::invalid_argument("Too many indoor placements");
        for (const auto& placement : placements) {
            validate(placement.grid);
            if (placement.x < -32767 || placement.x > 32767 ||
                placement.y < -32767 || placement.y > 32767)
                throw std::invalid_argument("Indoor placement coordinate exceeds bounds");
        }

        const int side = 2 * std::max(base.width, (base.height + 1) / 2) + 1;
        const int anchor = side - 1 - base.width + (base.width & 1);
        std::vector<std::uint8_t> cells(static_cast<std::size_t>(side) *
                                       static_cast<std::size_t>(side), 0);
        const auto project = [&](const PassGrid& grid, int offset_x, int offset_y,
                                 bool overlay) {
            for (int r = 0; r < grid.height; ++r) {
                for (int c = 0; c < grid.width; ++c) {
                    const int x = offset_x + c - r / 2;
                    const int y = offset_y + c + (r + 1) / 2;
                    if (x < 0 || y < 0 || x >= side || y >= side)
                        throw std::out_of_range("Indoor cell projects outside grid");
                    const auto raw = grid.cells[index(c, r, grid.width)];
                    if (!overlay || raw == 0) cells[index(x, y, side)] = raw;
                }
            }
        };
        project(base, anchor, 0, false);
        for (const auto& placement : placements) {
            // Stored grid coordinates; signed division must truncate toward zero.
            const int offset_x = anchor + placement.x - placement.y / 2;
            const int offset_y = placement.x + (placement.y + 1) / 2;
            project(placement.grid, offset_x, offset_y, true);
        }
        // Publish only a fully validated grid; failed rebuilds preserve the old one.
        cells_.swap(cells);
        side_ = side;
    }

    [[nodiscard]] int side() const noexcept { return side_; }
    [[nodiscard]] const std::vector<std::uint8_t>& cells() const noexcept { return cells_; }
    [[nodiscard]] std::uint8_t cell(int x, int y) const noexcept {
        if (x < 0 || y < 0 || x >= side_ || y >= side_) return 0;
        return cells_[index(x, y, side_)];
    }

private:
    static std::size_t index(int x, int y, int width) noexcept {
        return static_cast<std::size_t>(y) * static_cast<std::size_t>(width) +
               static_cast<std::size_t>(x);
    }
    static void validate(const PassGrid& grid) {
        if (grid.width < 1 || grid.width > 512 || grid.height < 1 || grid.height > 512)
            throw std::invalid_argument("Indoor grid dimensions must be 1..512");
        if (grid.cells.size() != static_cast<std::size_t>(grid.width) *
                                 static_cast<std::size_t>(grid.height))
            throw std::invalid_argument("Indoor grid cell count mismatch");
    }
    int side_ = 0;
    std::vector<std::uint8_t> cells_;
};
}
