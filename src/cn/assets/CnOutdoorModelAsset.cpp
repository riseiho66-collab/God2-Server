#include "cn/assets/CnOutdoorModelAsset.h"
#include "cn/assets/CnAssetTokens.h"
#include "cn/assets/CnResourceBytes.h"
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2cn {
CnOutdoorModelAsset CnOutdoorModelAsset::from_v16_resource(
    std::span<const std::uint8_t> bytes, std::size_t max_plain_bytes) {
    const auto plain=decode_cn_resource(bytes,max_plain_bytes);
    detail::CnAssetTokens input(plain);
    if (input.next()!="MDL" || input.next()!="v1.6")
        throw std::invalid_argument("CN MDL version or header unavailable");
    CnOutdoorModelAsset asset;
    CnHouseMapAsset::read_v16_models(input,asset.library_);
    input.expect("Model");
    // 004651D0 repeats (chunkx,chunky,count) until EOF, not one global count.
    while (!input.empty()) {
        const auto chunk_x=input.integer(), chunk_y=input.integer();
        const auto count=input.count();
        for (std::size_t i=0; i<count; ++i) {
            Placement p{};
            p.chunk_x=chunk_x; p.chunk_y=chunk_y;
            p.model_index=input.integer(); p.screen_x=input.integer(); p.screen_y=input.integer();
            p.world_x=input.integer(); p.world_y=input.integer(); p.packed_selector=input.integer();
            if (p.model_index<0 || static_cast<std::size_t>(p.model_index)>=asset.library_.model_data().size())
                throw std::invalid_argument("CN MDL model reference unavailable");
            // v1.6 stores world coordinates directly. Only v1.1/v1.2 add
            // chunk*21 in004651D0; those layouts are not handled here.
            p.object.native_1c=input.integer(); p.object.native_20=input.integer();
            p.object.script_flag=input.integer();
            if (p.object.script_flag==1) p.object.script_reference=std::string(input.next());
            p.object.native_38=input.integer();
            asset.placements_.push_back(std::move(p));
        }
    }
    return asset;
}
CnOutdoorModelAsset CnOutdoorModelAsset::load_v16_file(const std::filesystem::path& path,
    std::size_t max_encoded_bytes, std::size_t max_plain_bytes) {
    return from_v16_resource(read_cn_asset_file(path,max_encoded_bytes),max_plain_bytes);
}
std::vector<CnMapPassability::OutdoorObject> CnOutdoorModelAsset::ordered_objects(
    CnOutdoorTerrain::ChunkCoordinate center, std::int32_t mdt_width, std::int32_t mdt_height,
    std::span<const std::optional<std::int32_t>> heights) const {
    if (mdt_width<=0 || mdt_height<=0 || heights.size()!=library_.model_data().size())
        throw std::invalid_argument("CN MDL map/model geometry unavailable");
    // Invalid source groups are not silently dropped as an empty chunk. Native
    //00439A10 bounds them using MDT dimensions before linking placements.
    for (const auto& p:placements_)
        if (p.chunk_x<0 || p.chunk_y<0 || p.chunk_x>=mdt_width || p.chunk_y>=mdt_height)
            throw std::invalid_argument("CN MDL placement group outside MDT extent");
    std::vector<CnMapPassability::OutdoorObject> result;
    for (std::int64_t y=std::int64_t(center.y)-2; y<std::int64_t(center.y)+2; ++y) {
        for (std::int64_t x=std::int64_t(center.x)-2; x<std::int64_t(center.x)+2; ++x) {
            std::vector<std::pair<std::int32_t,const Placement*>> ordered;
            for (const auto& p:placements_) {
                if (p.chunk_x!=x || p.chunk_y!=y) continue;
                const auto& height=heights[static_cast<std::size_t>(p.model_index)];
                if (!height) throw std::invalid_argument("CN MDL native model height unresolved");
                const auto key=std::int64_t(p.screen_y)+*height;
                if (key<std::numeric_limits<std::int32_t>::min() || key>std::numeric_limits<std::int32_t>::max())
                    throw std::invalid_argument("CN MDL native insertion key overflow");
                ordered.emplace_back(static_cast<std::int32_t>(key),&p);
            }
            // 0046A640 inserts before the first strictly greater key, so ties
            // retain file insertion order, including repeated chunk groups.
            std::stable_sort(ordered.begin(),ordered.end(),[](const auto& a,const auto& b) { return a.first<b.first; });
            for (const auto& entry:ordered) {
                const auto& p=*entry.second;
                const auto& model=library_.model_data()[static_cast<std::size_t>(p.model_index)];
                const auto selected=static_cast<std::uint8_t>(p.packed_selector);
                if (selected>=model.declared_frames.size())
                    throw std::invalid_argument("CN MDL selected mask needs unresolved ROM frame");
                const auto& frame=model.declared_frames[selected];
                std::array<std::array<std::int32_t,2>,4> markers;
                markers.fill({-1,-1}); // 00469CD0 ModelDat marker initialization
                for (std::size_t i=0; i<markers.size(); ++i) {
                    const auto candidate=model.declared_markers[i];
                    if (candidate[0]==-1 || std::find(markers.begin(),markers.end(),candidate)==markers.end())
                        markers[i]=candidate; // 0046B8B0, duplicate retains prior slot
                }
                CnMapPassability::OutdoorObject object{};
                object.world_x=p.world_x; object.world_y=p.world_y;
                object.selected_mask={frame.width,frame.height,frame.cells};
                object.markers[0]={markers[0][0],markers[0][1]};
                object.markers[1]={markers[1][0],markers[1][1]};
                result.push_back(object);
            }
        }
    }
    return result;
}
std::optional<CnOutdoorTerrain::InitialWorldPlacement> CnOutdoorModelAsset::prepare_initial_at_world(
    const CnOutdoorTerrain& terrain,std::int32_t world_x,std::int32_t world_y,
    std::int32_t mdt_width,std::int32_t mdt_height,
    std::span<const std::optional<std::int32_t>> heights) const {
    const auto selected=terrain.select_native_center(world_x,world_y);
    if (!selected) return std::nullopt;
    if (mdt_width<3 || mdt_height<3) throw std::invalid_argument("CN MDL initial MDT extent unavailable");
    const CnOutdoorTerrain::ChunkCoordinate center{std::min(std::max(selected->x,1),mdt_width-2),
        std::min(std::max(selected->y,1),mdt_height-2)};
    const auto objects=ordered_objects(center,mdt_width,mdt_height,heights);
    return terrain.prepare_initial_at_world(world_x,world_y,mdt_width,mdt_height,objects);
}
std::optional<CnOutdoorTerrain::InitialWorldPlacement> CnOutdoorModelAsset::prepare_initial_with_declared_geometry(
    const CnOutdoorTerrain& terrain,std::int32_t world_x,std::int32_t world_y,
    std::int32_t mdt_width,std::int32_t mdt_height) const {
    const auto extents=library_.declared_model_extents();
    std::vector<std::optional<std::int32_t>> heights;
    heights.reserve(extents.size());
    for (const auto& extent:extents)
        heights.push_back(extent ? std::optional<std::int32_t>(extent->height) : std::nullopt);
    return prepare_initial_at_world(terrain,world_x,world_y,mdt_width,mdt_height,heights);
}
std::optional<CnOutdoorTerrain::InitialWorldPlacement> CnOutdoorModelAsset::prepare_initial_with_rom_geometry(
    const CnOutdoorTerrain& terrain,std::int32_t world_x,std::int32_t world_y,
    std::int32_t mdt_width,std::int32_t mdt_height,std::span<const CnRomAsset* const> rom_slots) const {
    const auto heights=native_model_heights(rom_slots);
    return prepare_initial_at_world(terrain,world_x,world_y,mdt_width,mdt_height,heights);
}
std::vector<std::optional<std::int32_t>> CnOutdoorModelAsset::native_model_heights(
    std::span<const CnRomAsset* const> rom_slots) const {
    const auto extents=library_.rom_model_extents(rom_slots);
    std::vector<std::optional<std::int32_t>> heights;
    heights.reserve(extents.size());
    for (const auto& extent:extents)
        heights.push_back(extent ? std::optional<std::int32_t>(extent->height) : std::nullopt);
    return heights;
}
}
