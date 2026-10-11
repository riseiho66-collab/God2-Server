#pragma once
#include "cn/world/CnMapPassability.h"
#include "cn/assets/CnRomAsset.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <span>
#include <string>
#include <vector>

namespace god2cn {
namespace detail { class CnAssetTokens; }
// Static HMD v1.6 content recovered from 0045C350/00477A80/00476F90/0045CB50.
// Asset labels remain byte strings. They are not chat text or OS-locale paths.
// ROM images/scripts are references only; reading this class executes neither.
class CnHouseMapAsset {
public:
    struct TileModel {
        std::string native_label;
        std::array<std::int32_t,5> native_fields;
    };
    struct ModelLayer { std::int32_t tile_index, offset_x, offset_y; };
    struct MaskFrame {
        std::int32_t native_anchor_x, native_anchor_y;
        std::int32_t width, height;
        std::vector<std::uint8_t> cells;
    };
    struct ModelData {
        std::array<ModelLayer,3> layers;
        // Raw file pairs;0046B8B0 duplicate suppression is not applied here.
        std::array<std::array<std::int32_t,2>,4> declared_markers;
        std::vector<MaskFrame> declared_frames;
    };
    struct ModelExtent { std::int32_t width, height; };
    struct Placement {
        std::int32_t model_index, screen_x, screen_y, native_x, native_y;
        std::int32_t packed_selector;
        // First placement (base) has no following object-only fields.
        struct ObjectFields {
            std::int32_t native_1c, native_20, script_flag, native_38;
            std::optional<std::string> script_reference;
        };
        std::optional<ObjectFields> object;
    };
    static CnHouseMapAsset from_v16_resource(std::span<const std::uint8_t> bytes,
        std::size_t max_plain_bytes);
    // Caller resolves the native scene asset; no search into TW or automatic
    // substitute file selection. Windows filesystem::path retains UTF-16.
    static CnHouseMapAsset load_v16_file(const std::filesystem::path& path,
        std::size_t max_encoded_bytes, std::size_t max_plain_bytes);
    // Explicit file placements and declared mask frames only. No inferred
    // masks for animation frames whose data depend on unresolved ROM loaders.
    CnMapPassability compose_initial_passability() const;
    // 00475410/00475960 retain explicit positive tile width/height. After
    // layer offsets,0046A730 derives ModelDat+0/+4 from body and layer2.
    // Null means geometry needs native image/ROM resolution (or unsupported
    // metadata), never a substitute zero height. This does not prove ROM load
    // success or resolve frame count, animation, or default masks.
    std::vector<std::optional<ModelExtent>> declared_model_extents() const;
    // Slots must correspond to this asset's ROMFILE order. Null slots and
    // standalone-image tile types remain unresolved; no declared fallback.
    std::vector<std::optional<ModelExtent>> rom_model_extents(
        std::span<const CnRomAsset* const> slots) const;
    const auto& rom_references() const noexcept { return roms_; }
    const auto& tile_models() const noexcept { return tiles_; }
    const auto& model_data() const noexcept { return models_; }
    const auto& placements() const noexcept { return placements_; }
private:
    friend class CnOutdoorModelAsset;
    // Shared native00477A80/00476F90 prefix. The caller checks its distinct
    // HMD or MDL header and consumes that family's placement format.
    static void read_v16_models(detail::CnAssetTokens& input, CnHouseMapAsset& asset);
    std::vector<std::optional<ModelExtent>> model_extents(
        std::span<const std::optional<ModelExtent>> tile_extents) const;
    CnHouseMapAsset()=default;
    std::vector<std::string> roms_;
    std::vector<TileModel> tiles_;
    std::vector<ModelData> models_;
    std::vector<Placement> placements_;
};
}
