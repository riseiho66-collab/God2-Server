#pragma once
#include <array>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <vector>
namespace god2 {
// Current CityI2 source windows, not a claim about original birth coordinates.
class RecoveredKunlunNavigation {
public:
    explicit RecoveredKunlunNavigation(const std::filesystem::path& path);
    std::optional<std::uint8_t> consistent_cell(int x,int y) const noexcept;
    bool consistently_walkable(int x,int y) const noexcept;
private:
    // Fixed source extent stored on the heap: multiple cold-relogin service
    // instances must not exhaust the default Windows thread stack.
    std::vector<std::uint8_t> cells_=std::vector<std::uint8_t>(252*252,255);
    std::vector<std::uint8_t> walkable_=std::vector<std::uint8_t>(252*252,255);
};
}
