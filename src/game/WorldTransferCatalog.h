#pragma once
#include <array>
#include <cstdint>
#include <filesystem>
#include <map>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace god2 {
// CUSTOM-0155: immutable, source-pinned static world policy. This is not an
// actual native scene-resource lifecycle, actor occupancy or native5D issuer.
class WorldTransferCatalog final {
public:
    struct SceneKey {std::uint16_t area,scene;bool operator==(const SceneKey&) const = default;};
    struct Point {SceneKey scene;std::uint16_t x,y;};
    enum class Trigger {DisplacedPoint,DirectedStep,NpcOffer};
    struct Scene {SceneKey key;std::uint16_t kind,width,height;std::string grid_sha256;};
    struct Route {
        std::string id;Trigger trigger;Point source,destination;std::uint8_t approach_mask;
    };
    explicit WorldTransferCatalog(const std::filesystem::path&);
    [[nodiscard]] const Scene* scene(SceneKey) const noexcept;
    [[nodiscard]] std::optional<std::uint8_t> observed_mask(Point) const noexcept;
    [[nodiscard]] bool available(Point) const noexcept;
    [[nodiscard]] const Route* route(std::string_view id) const noexcept;
    // approach_mask bits: before relative to trigger, NW,N,NE,W,E,SW,S,SE.
    [[nodiscard]] const Route* route_for_step(SceneKey,std::uint16_t before_x,std::uint16_t before_y,
        std::uint16_t x,std::uint16_t y) const noexcept;
    [[nodiscard]] std::span<const Route> routes() const noexcept {return routes_;}
    [[nodiscard]] std::span<const Scene> scenes() const noexcept {return scene_definitions_;}
private:
    struct Grid {Scene definition;std::vector<std::uint8_t> masks;};
    std::map<std::pair<std::uint16_t,std::uint16_t>,Grid> scenes_;
    std::vector<Route> routes_;
    std::vector<Scene> scene_definitions_;
    std::map<std::string,std::size_t,std::less<>> route_ids_;
    std::map<std::array<std::uint16_t,4>,std::size_t> point_routes_;
    std::map<std::array<std::uint16_t,4>,std::uint8_t> exceptions_;
};
}
