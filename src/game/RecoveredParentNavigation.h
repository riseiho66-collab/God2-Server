#pragma once
#include <filesystem>
#include <optional>
#include <vector>
#include <cstdint>

namespace god2 {
// Current Island03 source windows, original static projection only.
// CUSTOM-0053 uses these cells for separately registered parent transfers.
class RecoveredParentNavigation {
public:
    explicit RecoveredParentNavigation(const std::filesystem::path& path,std::uint16_t area=4);
    [[nodiscard]] std::optional<std::uint8_t> consistent_cell(int x,int y) const noexcept;
    // Read-only nonzero consensus; admission remains the caller's exact policy.
    [[nodiscard]] bool consistently_walkable(int x,int y) const noexcept;
private:
    int width{},height{};
    std::vector<std::uint8_t> cells_;
    std::vector<std::uint8_t> observed_masks_;
};
}
