#pragma once
#include "cn/assets/CnHouseMapAsset.h"
#include "cn/assets/CnOutdoorTerrain.h"

namespace god2cn {
// MDL v1.6 shares only the model-definition prefix with HMD. Its grouped
// placements have no base object and every record has object-only fields.
class CnOutdoorModelAsset {
public:
    struct Placement {
        std::int32_t chunk_x, chunk_y;
        std::int32_t model_index, screen_x, screen_y, world_x, world_y, packed_selector;
        CnHouseMapAsset::Placement::ObjectFields object;
    };
    static CnOutdoorModelAsset from_v16_resource(std::span<const std::uint8_t> bytes,
        std::size_t max_plain_bytes);
    static CnOutdoorModelAsset load_v16_file(const std::filesystem::path& path,
        std::size_t max_encoded_bytes, std::size_t max_plain_bytes);
    // ModelDat+4 heights must come from the native ROM/tile/layer pipeline.
    // optional permits unrelated unresolved models, never a guessed sort key.
    // Returned masks borrow this asset's storage; keep it alive and unchanged.
    std::vector<CnMapPassability::OutdoorObject> ordered_objects(
        CnOutdoorTerrain::ChunkCoordinate center, std::int32_t mdt_width, std::int32_t mdt_height,
        std::span<const std::optional<std::int32_t>> native_model_heights) const;
    std::optional<CnOutdoorTerrain::InitialWorldPlacement> prepare_initial_at_world(
        const CnOutdoorTerrain& terrain, std::int32_t world_x, std::int32_t world_y,
        std::int32_t mdt_width, std::int32_t mdt_height,
        std::span<const std::optional<std::int32_t>> native_model_heights) const;
    // Use geometry derivable from declared positive tile sizes. Referenced
    // models requiring image/ROM dimensions remain explicit missing data.
    std::optional<CnOutdoorTerrain::InitialWorldPlacement> prepare_initial_with_declared_geometry(
        const CnOutdoorTerrain& terrain, std::int32_t world_x, std::int32_t world_y,
        std::int32_t mdt_width, std::int32_t mdt_height) const;
    auto declared_model_extents() const { return library_.declared_model_extents(); }
    // ROM metadata -> native model bounds -> stable object order -> window.
    // Explicit slot binding is required; standalone images/default masks and
    // the scene file resolver are separate unfinished dependencies.
    std::optional<CnOutdoorTerrain::InitialWorldPlacement> prepare_initial_with_rom_geometry(
        const CnOutdoorTerrain& terrain, std::int32_t world_x, std::int32_t world_y,
        std::int32_t mdt_width, std::int32_t mdt_height,
        std::span<const CnRomAsset* const> rom_slots) const;
    const auto& placements() const noexcept { return placements_; }
    const auto& model_data() const noexcept { return library_.model_data(); }
    const auto& tile_models() const noexcept { return library_.tile_models(); }
    const auto& rom_references() const noexcept { return library_.rom_references(); }
    // Actual ROM/tile/layer-derived sort heights, retained by a loaded scene.
    std::vector<std::optional<std::int32_t>> native_model_heights(
        std::span<const CnRomAsset* const> rom_slots) const;
private:
    CnOutdoorModelAsset()=default;
    CnHouseMapAsset library_;
    std::vector<Placement> placements_;
};
}
