#pragma once
#include "game/SharedTaiwanNativeMovementScene.h"
#include "game/TaiwanNativeTileMasks.h"
#include "game/TaiwanNativeRomAsset.h"
#include <array>
#include <filesystem>
#include <memory>
#include <optional>
#include <span>
#include <string>
#include <vector>

namespace god2 {
// Pinned TW HMD v1.6 source, independently recovered from00437900/00437250.
// Asset strings remain original bytes. This does not execute ROMs/scripts,
// resolve a native search path, create x86 objects or grant movement rights.
class TaiwanNativeMapAsset final {
public:
    struct Tile {std::string native_label;std::array<std::int32_t,5> fields;};
    struct Placement {
        std::int32_t model,screen_x,screen_y,native_x,native_y,selector;
        struct Object {
            std::int32_t native_1c,native_20,script_flag,native_38;
            std::optional<std::string> script;
        };
        std::optional<Object> object;
        std::size_t source_begin,source_end;
    };
    struct Extent {std::int32_t width,height;};
    struct OrderedObject {std::size_t placement;std::int32_t native_sort_key;Extent model_extent;};
    struct RomSlot {
        std::size_t ordinal;
        std::string native_reference; // Exact ROMFILE bytes, not a normalized path.
        std::uint64_t actual_resource_generation;
        TaiwanNativeRomAsset source; // Whole parsed original, immutable-owned.
    };
    class RomBound;
    // Explicit opt-in to actual ROM-bound geometry. The original explicit-only
    // methods below retain their signatures and domain; no fallback is added.
    std::optional<RomBound> bind_rom_sources(std::vector<RomSlot>) const;
    // The caller selects the actual source. No guessed map name, preferred-Z
    // path or substitution is introduced. Full encoded/decoded bytes retained.
    static std::optional<TaiwanNativeMapAsset> from_selected_resource(
        std::filesystem::path actual_source,std::span<const std::uint8_t>,std::size_t max_plain_bytes);
    static std::optional<TaiwanNativeMapAsset> load_selected_file(
        const std::filesystem::path& actual_source,std::size_t max_encoded_bytes,std::size_t max_plain_bytes);
    // Actual native00441A00 body/layer2 geometry. Only explicit positive tile
    // dimensions of qualified native type2/7 are recovered here. Missing ROM
    // or image geometry rejects; Pass mask height is never a sprite extent.
    std::optional<Extent> explicit_model_extent(std::size_t model) const;
    // Native004425F0 stable insertion by signed(screen_y+ModelDat[4]), not
    // source file order. Complete original placements remain accessible.
    std::optional<std::vector<OrderedObject>> ordered_objects() const;
    // Qualified initial file selectors:00437318/004374D0 preserve full DWORD
    // bits after object creation;00436C30 reinitialization does not change them.
    // Later animation/frame/object mutations require actual lifecycle Current.
    std::optional<TaiwanNativeGrid::Material> compose_material() const;
    std::optional<SharedTaiwanNativeMovementScene::Resources> resources(
        std::uint64_t actual_resource_generation,std::uint64_t actual_initial_scene_generation) const;
    // Direct concrete producer for the existing scene's Native/MaterialSource.
    // Actual current pose/direction, generations and ResourceCurrent mandatory.
    // Current retains the whole immutable asset and exact composed Grid storage
    // until release, qualifying grid identity and generations before/after it.
    std::optional<SharedTaiwanNativeMovementScene::Native> native_scene(
        std::uint64_t actual_resource_generation,std::uint64_t actual_initial_scene_generation,
        RecoveredPosition actual_position,std::uint8_t actual_direction,
        SharedTaiwanNativeMovementScene::ResourceCurrent) const;
    const std::filesystem::path& source() const;
    const std::vector<std::uint8_t>& encoded_bytes() const;
    const TaiwanNativeTileMasks& masks() const;
    const std::vector<std::string>& rom_references() const;
    const std::vector<Tile>& tiles() const;
    const std::vector<Placement>& placements() const;
    std::size_t consumed_cursor() const;
private:
    struct Storage;
    explicit TaiwanNativeMapAsset(std::shared_ptr<const Storage>);
    const Storage& storage() const;
    std::shared_ptr<const Storage> storage_;
};
// Concrete ROMFILE binding, not a native bank or rendering/cache success.
// Every original ordinal/name has one actual immutable source and generation.
class TaiwanNativeMapAsset::RomBound final {
public:
    std::optional<TaiwanNativeRomAsset::TileGeometry> tile_geometry(std::size_t tile) const;
    std::optional<Extent> model_extent(std::size_t model) const;
    std::optional<std::vector<OrderedObject>> ordered_objects() const;
    std::optional<TaiwanNativeGrid::Material> compose_material() const;
    std::optional<SharedTaiwanNativeMovementScene::Resources> resources(
        std::uint64_t actual_resource_generation,std::uint64_t actual_initial_scene_generation) const;
    // Current must qualify every actual ROM/source generation as well as the
    // HMD/object lifetime. This owner retains exact full binding and Grid storage
    // and checks Grid identity/generations before and after the real delegate.
    std::optional<SharedTaiwanNativeMovementScene::Native> native_scene(
        std::uint64_t actual_resource_generation,std::uint64_t actual_initial_scene_generation,
        RecoveredPosition actual_position,std::uint8_t actual_direction,
        SharedTaiwanNativeMovementScene::ResourceCurrent) const;
    const TaiwanNativeMapAsset& asset() const;
    const std::vector<RomSlot>& slots() const;
private:
    friend class TaiwanNativeMapAsset;
    struct Storage;
    explicit RomBound(std::shared_ptr<const Storage>);
    const Storage& storage() const;
    std::shared_ptr<const Storage> storage_;
};
}
