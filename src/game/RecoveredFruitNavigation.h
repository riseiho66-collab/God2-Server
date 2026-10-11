#pragma once
#include <array>
#include <cstdint>
#include <filesystem>
#include <string_view>

namespace god2 {
// Current fruit-village static cell consensus. No dynamic actor occupancy,
// encounter, NPC spawn or quest-event authority is implied by a passable cell.
class RecoveredFruitNavigation {
public:
    static constexpr int width=189, height=189;
    static constexpr std::string_view source_sha256=
        "a07db1f68dab7294c41d0813da85c134f7c3b454bef352e337d40157c843f55d";
    static RecoveredFruitNavigation load(const std::filesystem::path& path);
    explicit RecoveredFruitNavigation(const std::filesystem::path& path)
        : RecoveredFruitNavigation(load(path)) {}
    // 1/2 are qualified pass values. Blocked, unknown, conflicting and outside
    // cells all return0; callers cannot accidentally accept a marker as truthy.
    std::uint8_t consistent_cell(int x,int y) const noexcept;
private:
    RecoveredFruitNavigation() = default;
    std::array<std::uint8_t,width*height> cells_{};
};
}
