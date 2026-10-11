#pragma once
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <map>
#include <optional>

namespace god2 {
// Static Island01 window consensus. Conflicting/unknown cells have no authority.
class RecoveredIslandEntryNavigation {
public:
    explicit RecoveredIslandEntryNavigation(const std::filesystem::path& path);
    [[nodiscard]] std::optional<std::uint8_t> consistent_cell(int x,int y) const noexcept;
    [[nodiscard]] std::size_t conflict_count() const noexcept { return conflicts_; }
private:
    std::map<std::uint64_t,std::uint16_t> cells_; // 256 marks contradictory windows.
    std::size_t conflicts_{};
};
}
