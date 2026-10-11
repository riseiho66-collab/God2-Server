#include "cn/assets/CnOutdoorTerrain.h"
#include "cn/assets/CnResourceBytes.h"
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2cn {
namespace {
std::uint32_t u32(std::span<const std::uint8_t> bytes, std::size_t at) {
    return std::uint32_t(bytes[at]) | (std::uint32_t(bytes[at+1]) << 8) |
        (std::uint32_t(bytes[at+2]) << 16) | (std::uint32_t(bytes[at+3]) << 24);
}
}
CnOutdoorTerrain::CnOutdoorTerrain(std::int32_t width, std::int32_t height,
    std::vector<std::uint32_t> offsets, std::vector<std::uint8_t> bytes)
    : width_(width), height_(height), offsets_(std::move(offsets)), bytes_(std::move(bytes)) {}

CnOutdoorTerrain CnOutdoorTerrain::from_v12_resource(
    std::span<const std::uint8_t> encoded, std::size_t max_plain_bytes) {
    auto bytes = decode_cn_resource(encoded, max_plain_bytes);
    constexpr std::array<std::uint8_t, 8> signature{'M','B','D',' ','v','1','.','2'};
    if (bytes.size() < 16 || !std::equal(signature.begin(), signature.end(), bytes.begin()))
        throw std::invalid_argument("CN MBD v1.2 header unavailable");
    const auto w = u32(bytes, 8), h = u32(bytes, 12);
    if (!w || !h || w > std::numeric_limits<std::int32_t>::max() ||
        h > std::numeric_limits<std::int32_t>::max())
        throw std::invalid_argument("CN MBD dimensions unavailable");
    const std::uint64_t count = std::uint64_t(w) * h;
    const std::uint64_t table_end = 16 + count * 4;
    // Native FILE offsets and products are signed32. Safe internal bounds,
    // not a recovered original-server rejection packet or gameplay limit.
    if (table_end > bytes.size() || table_end > std::numeric_limits<std::int32_t>::max())
        throw std::invalid_argument("CN MBD offset table incomplete or unrepresentable");
    std::vector<std::uint32_t> offsets;
    offsets.reserve(static_cast<std::size_t>(count));
    for (std::size_t i = 0; i < count; ++i) {
        const auto offset = u32(bytes, 16 + i * 4);
        if (offset != 0 && (offset > std::numeric_limits<std::int32_t>::max() ||
            offset > bytes.size() || bytes.size() - offset < chunk_bytes))
            throw std::invalid_argument("CN MBD referenced chunk incomplete");
        // Preserve actual offsets, including aliases; no sequential-layout
        // assumption or inferred payload records for holes in the table.
        offsets.push_back(offset);
    }
    return {static_cast<std::int32_t>(w), static_cast<std::int32_t>(h),
        std::move(offsets), std::move(bytes)};
}
CnOutdoorTerrain CnOutdoorTerrain::load_v12_file(const std::filesystem::path& path,
    std::size_t max_encoded_bytes, std::size_t max_plain_bytes) {
    return from_v12_resource(read_cn_asset_file(path, max_encoded_bytes), max_plain_bytes);
}
std::span<const std::uint8_t> CnOutdoorTerrain::chunk(ChunkCoordinate at) const noexcept {
    if (at.x < 0 || at.y < 0 || at.x >= width_ || at.y >= height_) return {};
    const auto offset = offsets_[static_cast<std::size_t>(at.y) * width_ + at.x];
    if (!offset) return {};
    return std::span<const std::uint8_t>(bytes_).subspan(offset, chunk_bytes);
}
bool CnOutdoorTerrain::has_native_neighborhood(ChunkCoordinate requested) const noexcept {
    // Widen before +/-1; do not reproduce native malformed-input overflow.
    for (std::int64_t y = std::int64_t(requested.y)-1; y <= std::int64_t(requested.y)+1; ++y)
        for (std::int64_t x = std::int64_t(requested.x)-1; x <= std::int64_t(requested.x)+1; ++x)
            if (x < 0 || y < 0 || x >= width_ || y >= height_ ||
                chunk({static_cast<std::int32_t>(x), static_cast<std::int32_t>(y)}).empty())
                return false;
    return true;
}
std::optional<CnOutdoorTerrain::ChunkCoordinate> CnOutdoorTerrain::select_native_center(
    std::int32_t world_x, std::int32_t world_y) const noexcept {
    // Native reciprocal multiply/shift implements signed truncation toward0,
    // not floor division. Division by21 also leaves room for both +/-1 loops.
    const ChunkCoordinate requested{world_x / 21, world_y / 21};
    if (has_native_neighborhood(requested)) return requested;
    // 004663A0 ignores00460510's failed-cell output; it does not sort candidates
    // by distance or use the failed-cell direction to steer this search.
    for (std::int32_t y = requested.y-1; y <= requested.y+1; ++y)
        for (std::int32_t x = requested.x-1; x <= requested.x+1; ++x)
            if (has_native_neighborhood({x, y})) return ChunkCoordinate{x, y};
    return std::nullopt;
}
std::optional<CnOutdoorTerrain::InitialNeighborhood> CnOutdoorTerrain::prepare_initial_neighborhood(
    ChunkCoordinate requested, std::int32_t mdt_width, std::int32_t mdt_height,
    std::span<const CnMapPassability::OutdoorObject> objects) const {
    if (!has_native_neighborhood(requested)) return std::nullopt;
    if (mdt_width < 3 || mdt_height < 3)
        throw std::invalid_argument("CN initial neighborhood MDT extent unavailable");
    const ChunkCoordinate center{std::min(std::max(requested.x, 1), mdt_width-2),
        std::min(std::max(requested.y, 1), mdt_height-2)};
    std::array<std::optional<ChunkCoordinate>, 9> slots;
    std::size_t slot = 0;
    for (std::int32_t y = center.y-1; y <= center.y+1; ++y)
        for (std::int32_t x = center.x-1; x <= center.x+1; ++x) {
            if (chunk({x, y}).empty())
                throw std::invalid_argument("CN clamped initial neighborhood incomplete");
            slots[slot++] = ChunkCoordinate{x, y};
        }
    // Reuses bounded MBD slot extraction and ordered native mask composition.
    // The all-present slot precondition permits an empty prior window here.
    auto grid = prepare_loaded_window(center, slots, {}, objects);
    return InitialNeighborhood{center, slots, std::move(grid)};
}
std::optional<CnOutdoorTerrain::InitialWorldPlacement> CnOutdoorTerrain::prepare_initial_at_world(
    std::int32_t world_x, std::int32_t world_y,
    std::int32_t mdt_width, std::int32_t mdt_height,
    std::span<const CnMapPassability::OutdoorObject> objects) const {
    if (world_y == std::numeric_limits<std::int32_t>::max())
        throw std::invalid_argument("CN native actor y+1 is unrepresentable");
    const auto selected = select_native_center(world_x, world_y);
    if (!selected) return std::nullopt;
    auto neighborhood = prepare_initial_neighborhood(*selected, mdt_width, mdt_height, objects);
    if (!neighborhood) return std::nullopt;
    const auto local_x = std::int64_t(world_x) - std::int64_t(neighborhood->center.x) * 21;
    const auto local_y = std::int64_t(world_y) + 1 - std::int64_t(neighborhood->center.y) * 21;
    const auto representable = [](std::int64_t value) {
        return value >= std::numeric_limits<std::int32_t>::min() &&
            value <= std::numeric_limits<std::int32_t>::max();
    };
    if (!representable(local_x) || !representable(local_y))
        throw std::invalid_argument("CN native local scene coordinates overflow");
    return InitialWorldPlacement{std::move(*neighborhood),
        static_cast<std::int32_t>(local_x), static_cast<std::int32_t>(local_y)};
}
CnMapPassability CnOutdoorTerrain::prepare_loaded_window(ChunkCoordinate center,
    const std::array<std::optional<ChunkCoordinate>, 9>& loaded_slots,
    std::span<const std::uint8_t> prior_cells,
    std::span<const CnMapPassability::OutdoorObject> ordered_objects) const {
    if (chunk(center).empty() || !loaded_slots[4] ||
        loaded_slots[4]->x != center.x || loaded_slots[4]->y != center.y)
        throw std::invalid_argument("CN outdoor center chunk state unavailable");
    const auto x = std::int64_t(center.x) * 21, y = std::int64_t(center.y) * 21;
    if (x > std::numeric_limits<std::int32_t>::max() || y > std::numeric_limits<std::int32_t>::max())
        throw std::length_error("CN outdoor origin overflow");
    std::array<std::span<const std::uint8_t>, 9> chunks;
    for (std::size_t i = 0; i < chunks.size(); ++i) {
        if (!loaded_slots[i]) continue;
        chunks[i] = chunk(*loaded_slots[i]);
        if (chunks[i].empty()) throw std::invalid_argument("CN loaded slot lacks terrain");
    }
    return CnMapPassability::compose_mode0(static_cast<std::int32_t>(x),
        static_cast<std::int32_t>(y), prior_cells, chunks, ordered_objects);
}
}
