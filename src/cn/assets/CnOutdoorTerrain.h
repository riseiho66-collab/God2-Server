#pragma once
#include "cn/world/CnMapPassability.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <span>
#include <vector>

namespace god2cn {
// Native MBD terrain only. MDT/MDL/ROM objects and live slot lifecycle are
// separate prerequisites; this asset alone cannot authorize movement.
class CnOutdoorTerrain {
public:
    static constexpr std::size_t chunk_bytes = 21 * 21 * 8;
    struct ChunkCoordinate { std::int32_t x, y; };
    struct InitialNeighborhood {
        ChunkCoordinate center;
        std::array<std::optional<ChunkCoordinate>, 9> loaded_slots;
        CnMapPassability grid;
    };
    struct InitialWorldPlacement {
        InitialNeighborhood neighborhood;
        // Native0046C780 outputs for camera/map projection, not actor movement.
        std::int32_t local_x, local_y_plus_one;
    };
    static CnOutdoorTerrain from_v12_resource(std::span<const std::uint8_t> bytes,
        std::size_t max_plain_bytes);
    // Explicit chosen MBD/MBDZ input. Does not run the client's file-cache
    // refresh, timestamp selection, disk decompression or legacy conversion.
    static CnOutdoorTerrain load_v12_file(const std::filesystem::path& path,
        std::size_t max_encoded_bytes, std::size_t max_plain_bytes);
    std::int32_t chunks_wide() const noexcept { return width_; }
    std::int32_t chunks_high() const noexcept { return height_; }
    // Empty means out-of-range or native offset zero, not an all-zero chunk.
    std::span<const std::uint8_t> chunk(ChunkCoordinate at) const noexcept;
    // 00460490: all nine offsets around the requested center must exist.
    bool has_native_neighborhood(ChunkCoordinate requested) const noexcept;
    // 004663A0: signed division by21, candidate first; if unavailable, visit
    // centers in row-major order y-1..y+1, x-1..x+1 and take first full3x3.
    // This selects a loading center; never changes the actor's world position.
    std::optional<ChunkCoordinate> select_native_center(
        std::int32_t world_x, std::int32_t world_y) const noexcept;
    // Initial0046C830 branch after00470920: prior center(-1,-1), no cached
    // slots. Gate on MBD neighborhood, then clamp using MDT+1468/+146C sizes,
    // then load all nine. Never substitute MBD sizes for missing MDT evidence.
    // Caller must supply the complete ordered objects for the resulting center.
    // nullopt is native branch inapplicability, not a movement rejection reply.
    std::optional<InitialNeighborhood> prepare_initial_neighborhood(
        ChunkCoordinate requested, std::int32_t mdt_width, std::int32_t mdt_height,
        std::span<const CnMapPassability::OutdoorObject> ordered_objects) const;
    // 00537D40 gives0046C780(actor.x,actor.y+1);0046C780 subtracts1 before
    // selecting a center. Therefore world_y here is the unmodified actor y.
    // Complete ordered object data must belong to the resulting clamped center.
    std::optional<InitialWorldPlacement> prepare_initial_at_world(
        std::int32_t world_x, std::int32_t world_y,
        std::int32_t mdt_width, std::int32_t mdt_height,
        std::span<const CnMapPassability::OutdoorObject> ordered_objects) const;
    // Slots are explicit native loaded-state coordinates, NOT an inferred
    // 3x3 neighborhood. A present slot must have its actual terrain bytes.
    CnMapPassability prepare_loaded_window(ChunkCoordinate center,
        const std::array<std::optional<ChunkCoordinate>, 9>& loaded_slots,
        std::span<const std::uint8_t> prior_cells,
        std::span<const CnMapPassability::OutdoorObject> ordered_objects) const;
private:
    CnOutdoorTerrain(std::int32_t width, std::int32_t height,
        std::vector<std::uint32_t> offsets, std::vector<std::uint8_t> bytes);
    std::int32_t width_, height_;
    std::vector<std::uint32_t> offsets_;
    std::vector<std::uint8_t> bytes_;
};
}
