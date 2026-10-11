#include "cn/assets/CnOutdoorSceneResources.h"
#include "cn/world/CnOutdoorCamera.h"
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2cn {
CnOutdoorSceneResources::CnOutdoorSceneResources(CnOutdoorMapAsset map,CnOutdoorModelAsset models,
    std::vector<CnRomAsset> roms,std::optional<CnOutdoorTerrain> terrain,std::string reference)
    :map_(std::move(map)),models_(std::move(models)),roms_(std::move(roms)),terrain_(std::move(terrain)),
     native_mdt_reference_(std::move(reference)) {
    std::vector<const CnRomAsset*> slots;
    slots.reserve(roms_.size());
    for(const auto& rom:roms_)slots.push_back(&rom);
    model_heights_=models_.native_model_heights(slots);
}
std::optional<std::string> CnOutdoorSceneResources::native_map_mdt_reference(std::string_view reference,
    CnOutdoorTerrain::ChunkCoordinate requested) {
    if(reference.size()<9 || !reference.ends_with(".map"))return std::nullopt;
    const auto dot=reference.size()-4;
    if(dot<5 || reference[dot-3]!='x')return std::nullopt;
    const auto x=CnOutdoorCamera::decode_ascii_axis(reference.substr(dot-5,2));
    const auto y=CnOutdoorCamera::decode_ascii_axis(reference.substr(dot-2,2));
    if(!x || !y || *x!=requested.x || *y!=requested.y)return std::nullopt;
    std::string mdt(reference.substr(0,dot-5));mdt.append(".mdt");
    for(const unsigned char c:mdt)if(c<0x20 || c>=0x7f)return std::nullopt;
    return mdt;
}
bool CnOutdoorSceneResources::owns_native_map_reference(std::string_view reference,
    CnOutdoorTerrain::ChunkCoordinate requested) const {
    const auto parsed=native_map_mdt_reference(reference,requested);
    if(!parsed)return false;
    const auto& mdt=*parsed;
    if(mdt.size()!=native_mdt_reference_.size())return false;
    const auto fold=[](unsigned char c) {return c>='A' && c<='Z' ? c-'A'+'a' : c;};
    for(std::size_t i=0;i<mdt.size();++i) {
        const auto a=static_cast<unsigned char>(mdt[i]),b=static_cast<unsigned char>(native_mdt_reference_[i]);
        if(a<0x20 || a>=0x7f || b<0x20 || b>=0x7f || fold(a)!=fold(b))return false;
    }
    return true; // No separator/locale/Unicode normalization or filesystem fallback.
}
std::optional<CnOutdoorTerrain::InitialWorldPlacement> CnOutdoorSceneResources::initial_at_world(
    std::int32_t x,std::int32_t y) const {
    if(!terrain_)throw std::invalid_argument("CN initial placement requires flag1 retained MBD");
    return models_.prepare_initial_at_world(*terrain_,x,y,map_.chunks_wide(),map_.chunks_high(),model_heights_);
}
std::optional<CnOutdoorTerrain::ChunkCoordinate> CnOutdoorSceneResources::qualified_center(
    CnOutdoorTerrain::ChunkCoordinate requested) const {
    if(requested.x==-1 || requested.y==-1)return std::nullopt;
    if(terrain_ && !terrain_->has_native_neighborhood(requested))return std::nullopt;
    if(map_.chunks_wide()<3 || map_.chunks_high()<3)
        throw std::invalid_argument("CN live neighborhood MDT extent unavailable");
    return CnOutdoorTerrain::ChunkCoordinate{
        std::min(std::max(requested.x,1),map_.chunks_wide()-2),
        std::min(std::max(requested.y,1),map_.chunks_high()-2)};
}
bool CnOutdoorSceneResources::chunk_available(CnOutdoorTerrain::ChunkCoordinate at) const noexcept {
    return terrain_ && !terrain_->chunk(at).empty();
}
CnMapPassability CnOutdoorSceneResources::complete_declared_frame_window(
    CnOutdoorTerrain::ChunkCoordinate center,
    const std::array<std::optional<CnOutdoorTerrain::ChunkCoordinate>,9>& loaded) const {
    if(center.x<1 || center.y<1 || center.x>map_.chunks_wide()-2 || center.y>map_.chunks_high()-2)
        throw std::invalid_argument("CN complete window center outside MDT clamp");
    for(std::size_t i=0;i<loaded.size();++i) {
        const CnOutdoorTerrain::ChunkCoordinate expected{
            center.x+static_cast<std::int32_t>(i%3)-1,
            center.y+static_cast<std::int32_t>(i/3)-1};
        if(!loaded[i] || loaded[i]->x!=expected.x || loaded[i]->y!=expected.y ||
           !chunk_available(*loaded[i]))throw std::invalid_argument("CN complete cache slot is unavailable or stale");
    }
    const auto objects=models_.ordered_objects(center,map_.chunks_wide(),map_.chunks_high(),model_heights_);
    // All nine chunks overwrite3969 cells before ordered masks/markers. Empty
    // prior is only permitted by that full coverage, never a zero-grid fallback.
    if(!terrain_)throw std::invalid_argument("CN MBD compositor requires retained MBD");
    return terrain_->prepare_loaded_window(center,loaded,{},objects);
}
CnMapPassability CnOutdoorSceneResources::complete_standalone_frame_window(
    CnOutdoorTerrain::ChunkCoordinate center,
    const std::array<std::optional<CnStandaloneMapAsset>,9>& loaded) const {
    return compose_standalone_frame_window(center,loaded,{});
}
CnMapPassability CnOutdoorSceneResources::compose_standalone_frame_window(
    CnOutdoorTerrain::ChunkCoordinate center,
    const std::array<std::optional<CnStandaloneMapAsset>,9>& loaded,
    std::span<const std::uint8_t> prior) const {
    if(terrain_)throw std::invalid_argument("CN standalone compositor requires flag0 resource");
    if(center.x<1 || center.y<1 || center.x>map_.chunks_wide()-2 || center.y>map_.chunks_high()-2)
        throw std::invalid_argument("CN standalone center outside MDT clamp");
    std::array<std::span<const std::uint8_t>,9> chunks;
    for(std::size_t i=0;i<loaded.size();++i) {
        if(!loaded[i])continue; // Native null slot does not overwrite any cell.
        if(loaded[i]->width()!=21 || loaded[i]->height()!=21)
            throw std::invalid_argument("CN standalone cache slot incomplete or size variant unrecovered");
        chunks[i]=loaded[i]->cells();
    }
    std::vector<CnMapPassability::OutdoorObject> objects;
    //0046F6BE..0046F6DE require center slot AND resource before overlays.
    // Absence here is the explicit native skip, not missing model-data fallback.
    if(loaded[4])objects=models_.ordered_objects(center,map_.chunks_wide(),map_.chunks_high(),model_heights_);
    const auto x=std::int64_t(center.x)*21,y=std::int64_t(center.y)*21;
    if(x>std::numeric_limits<std::int32_t>::max() || y>std::numeric_limits<std::int32_t>::max())
        throw std::length_error("CN standalone window origin overflow");
    return CnMapPassability::compose_mode0(static_cast<std::int32_t>(x),static_cast<std::int32_t>(y),prior,chunks,objects);
}
}
