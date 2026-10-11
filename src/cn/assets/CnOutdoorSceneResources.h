#pragma once
#include "cn/assets/CnOutdoorMapAsset.h"
#include "cn/assets/CnStandaloneMapAsset.h"
#include <memory>
#include <string_view>

namespace god2cn {
class CnSceneAssets;
// Immutable decoded native CN inputs retained by their actual scene loader.
// No disk reread, TW resource fallback, frame animation or version conversion.
class CnOutdoorSceneResources {
public:
    std::optional<CnOutdoorTerrain::InitialWorldPlacement> initial_at_world(
        std::int32_t actor_x,std::int32_t actor_y) const;
    //0046C830/00470C90: when MBD is present, its requested-neighborhood gate
    // precedes MDT clamping. Flag0 standalone profiles skip that MBD gate.
    std::optional<CnOutdoorTerrain::ChunkCoordinate> qualified_center(
        CnOutdoorTerrain::ChunkCoordinate requested) const;
    bool chunk_available(CnOutdoorTerrain::ChunkCoordinate) const noexcept;
    bool has_retained_mbd() const noexcept {return terrain_.has_value();}
    // Shared ASCII axis/delimiter parser; no resource/owner authorization.
    static std::optional<std::string> native_map_mdt_reference(std::string_view,
        CnOutdoorTerrain::ChunkCoordinate);
    const std::string& native_mdt_reference() const noexcept {return native_mdt_reference_;}
    //00470C90 removes the five axis/x bytes before appending.mdt, compares
    // current resource via native ASCII case-insensitive subset. Other base
    // resources require an actual replacement, never reuse this profile.
    bool owns_native_map_reference(std::string_view,CnOutdoorTerrain::ChunkCoordinate) const;
    // Complete loaded slots and native MDL declared selectors/object order.
    // Runtime mask/frame changes and partial/failed slots are separate paths.
    CnMapPassability complete_declared_frame_window(CnOutdoorTerrain::ChunkCoordinate center,
        const std::array<std::optional<CnOutdoorTerrain::ChunkCoordinate>,9>& loaded) const;
    // Flag0 MDT profile: each slot must be an actual plain MAP v1.0/v1.1
    //21x21 payload. Full9 only; no MBD gate, synthetic offsets or zero chunks.
    CnMapPassability complete_standalone_frame_window(CnOutdoorTerrain::ChunkCoordinate center,
        const std::array<std::optional<CnStandaloneMapAsset>,9>& loaded) const;
    //0046F630 null slots preserve their exact prior memory cells; center null
    // skips model traversal. Prior must be the actual initialized63x63 window.
    CnMapPassability compose_standalone_frame_window(CnOutdoorTerrain::ChunkCoordinate center,
        const std::array<std::optional<CnStandaloneMapAsset>,9>& loaded,
        std::span<const std::uint8_t> prior_cells) const;
private:
    friend class CnSceneAssets;
    CnOutdoorSceneResources(CnOutdoorMapAsset,CnOutdoorModelAsset,
        std::vector<CnRomAsset>,std::optional<CnOutdoorTerrain>,std::string native_mdt_reference);
    CnOutdoorMapAsset map_;
    CnOutdoorModelAsset models_;
    std::vector<CnRomAsset> roms_;
    std::optional<CnOutdoorTerrain> terrain_; // Absent for native00462980 flag0.
    std::vector<std::optional<std::int32_t>> model_heights_;
    std::string native_mdt_reference_; // Plain identity even when selected bytes are MDTZ.
};
}
