#pragma once
#include <cstdint>
#include <filesystem>
#include <map>
#include <optional>
#include <vector>

namespace god2 {
// CUSTOM-0154: one whole-file-pinned TW cross-MDL navigation/endpoint bundle.
// Asset geometry qualifies endpoints, not official server activation policy.
class RecoveredCrossMapNavigation {
public:
    struct Route {
        std::uint16_t area,source_scene,source_x,source_y,target_scene,target_x,target_y;
        bool operator==(const Route&) const = default;
    };
    explicit RecoveredCrossMapNavigation(const std::filesystem::path&);
    static constexpr bool supported_scene(std::uint16_t area,std::uint16_t scene) noexcept {
        return area==2 && (scene==2 || scene==32 || scene==43 || scene==108);
    }
    [[nodiscard]] std::optional<std::uint16_t> kind(std::uint16_t area,std::uint16_t scene) const noexcept;
    [[nodiscard]] std::optional<std::uint8_t> cell(std::uint16_t area,std::uint16_t scene,int x,int y) const noexcept;
    [[nodiscard]] bool consistently_walkable(std::uint16_t area,std::uint16_t scene,int x,int y) const noexcept;
    [[nodiscard]] bool contains(const Route&) const noexcept;
    [[nodiscard]] const std::vector<Route>& routes() const noexcept {return routes_;}
private:
    struct Scene {std::uint16_t kind;int width,height;std::vector<std::uint8_t> cells,observed_masks;};
    std::map<std::pair<std::uint16_t,std::uint16_t>,Scene> scenes_;
    std::vector<Route> routes_;
};
}
