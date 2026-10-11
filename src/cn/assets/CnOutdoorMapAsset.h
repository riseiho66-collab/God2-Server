#pragma once
#include "cn/assets/CnOutdoorModelAsset.h"
#include <array>
#include <string>

namespace god2cn {
// MDT v1.2 declarations from00462980. Material/tile fields remain raw native
// data; this reader does not claim rendering, animation or tile construction.
class CnOutdoorMapAsset {
public:
    struct Material {
        std::string declaration, name;
        std::array<std::int32_t,3> color;
        char native_flag;
    };
    struct Tile {
        enum class Kind { link, link2, replace, t1x1, t2x2 } kind;
        std::string first_material, second_material, image_reference;
        // link/link2: five native integers; replace/T*: first integer only.
        std::array<std::int32_t,5> fields{};
        std::vector<std::int32_t> animation_fields;
        // Negative ROM slot invokes a separate name lookup/standalone path.
        // It must not be silently resolved from another map's ROM registry.
        std::int32_t rom_slot=-1, action_id=-1;
    };
    static CnOutdoorMapAsset from_v12_resource(std::span<const std::uint8_t> bytes,
        std::size_t max_plain_bytes);
    static CnOutdoorMapAsset load_v12_file(const std::filesystem::path& path,
        std::size_t max_encoded_bytes,std::size_t max_plain_bytes);
    std::int32_t chunks_wide() const noexcept { return width_; }
    std::int32_t chunks_high() const noexcept { return height_; }
    std::int32_t native_dtime() const noexcept { return dtime_; }
    const auto& rom_references() const noexcept { return roms_; }
    const auto& materials() const noexcept { return materials_; }
    const auto& tiles() const noexcept { return tiles_; }
    // MDT dimensions drive clamping; MBD dimensions drive offset availability.
    // Slots belong to the MDL ROMFILE registry, not this MDT RomFile registry.
    std::optional<CnOutdoorTerrain::InitialWorldPlacement> prepare_initial_at_world(
        const CnOutdoorTerrain& terrain,const CnOutdoorModelAsset& models,
        std::span<const CnRomAsset* const> model_rom_slots,
        std::int32_t world_x,std::int32_t world_y) const;
private:
    CnOutdoorMapAsset()=default;
    std::int32_t width_=0,height_=0,dtime_=0;
    std::vector<std::string> roms_;
    std::vector<Material> materials_;
    std::vector<Tile> tiles_;
};
}
