#pragma once
#include <array>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <vector>

namespace god2 {
// Pinned static town data. Does not authorize movement or infer cache timing.
class RecoveredTownNavigation {
public:
    explicit RecoveredTownNavigation(const std::filesystem::path& path);
    [[nodiscard]] std::optional<std::uint8_t> cell(int center_x,int center_y,int x,int y) const noexcept;
    struct Center { int x,y; bool operator==(const Center&) const = default; };
    [[nodiscard]] bool available_center(int x,int y) const noexcept;
    // Original 41350 input coordinates; caller-specific y-1 is NOT applied here.
    [[nodiscard]] std::optional<Center> select_center(int x,int y) const noexcept;
    // Source agreement, not a replacement for client streaming or occupancy.
    [[nodiscard]] std::optional<std::uint8_t> consistent_cell(int x,int y) const noexcept;
    // Native46FF0/102BF0 uses nonzero bytes for a straight path. This separate
    // predicate never changes byte-consensus semantics or admits zero/unknown.
    [[nodiscard]] bool consistently_walkable(int x,int y) const noexcept;
    static constexpr int area=2, scene=4, kind=0;
private:
    std::vector<std::uint8_t> cells_;
    std::array<bool,81> block_present_{};
    std::array<std::uint8_t,189*189> consistent_{};
};
}
