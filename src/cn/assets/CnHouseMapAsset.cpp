#include "cn/assets/CnHouseMapAsset.h"
#include "cn/assets/CnResourceBytes.h"
#include "cn/assets/CnAssetTokens.h"
#include <algorithm>
#include <charconv>
#include <limits>
#include <stdexcept>
#include <string_view>
#include <utility>

namespace god2cn {

CnHouseMapAsset CnHouseMapAsset::from_v16_resource(std::span<const std::uint8_t> bytes,
    std::size_t max_plain_bytes) {
    const auto plain=decode_cn_resource(bytes,max_plain_bytes);
    detail::CnAssetTokens input(plain);
    if (input.next()!="HMD") throw std::invalid_argument("CN resource is not HMD");
    // Native version comparisons have distinct layouts. Do not silently use
    // v1.6 for v1.0..v1.5 or another asset family such as MDL/MDT/MBD.
    if (input.next()!="v1.6") throw std::invalid_argument("CN HMD version not recovered by this reader");
    CnHouseMapAsset asset;
    read_v16_models(input,asset);
    input.expect("Model");
    const auto placement_count=input.count();
    if (placement_count==0) throw std::invalid_argument("CN HMD base placement unavailable");
    for (std::size_t i=0; i<placement_count; ++i) {
        Placement placement{input.integer(),input.integer(),input.integer(),
            input.integer(),input.integer(),input.integer(),std::nullopt};
        if (placement.model_index<0 || static_cast<std::size_t>(placement.model_index)>=asset.models_.size())
            throw std::invalid_argument("CN HMD model reference unavailable");
        if (i!=0) {
            Placement::ObjectFields object{input.integer(),input.integer(),input.integer(),0,std::nullopt};
            if (object.script_flag==1) object.script_reference=std::string(input.next());
            object.native_38=input.integer();
            placement.object=std::move(object);
        }
        asset.placements_.push_back(std::move(placement));
    }
    input.finish();
    return asset;
}
void CnHouseMapAsset::read_v16_models(detail::CnAssetTokens& input, CnHouseMapAsset& asset) {
    input.expect("ROMFILE");
    const auto rom_count=input.count();
    for (std::size_t i=0; i<rom_count; ++i) asset.roms_.emplace_back(input.next());
    input.expect("TileModel");
    const auto tile_count=input.count();
    for (std::size_t i=0; i<tile_count; ++i) {
        TileModel tile;
        tile.native_label=input.next();
        for (auto& field:tile.native_fields) field=input.integer();
        asset.tiles_.push_back(std::move(tile));
    }
    input.expect("ModelDat");
    const auto model_count=input.count();
    for (std::size_t i=0; i<model_count; ++i) {
        ModelData model;
        for (auto& layer:model.layers) {
            layer={input.integer(),input.integer(),input.integer()};
            if (layer.tile_index < -1 || (layer.tile_index>=0 &&
                static_cast<std::size_t>(layer.tile_index)>=asset.tiles_.size()))
                throw std::invalid_argument("CN HMD tile reference unavailable");
        }
        if (model.layers[0].tile_index<0) throw std::invalid_argument("CN HMD body tile unavailable");
        const auto frame_count=input.count();
        // 00469CD0 initializes ten 0x24-byte mask slots in the 0x1C0 object.
        // Do not emulate out-of-object native writes for malformed resources.
        if (frame_count==0 || frame_count>10) throw std::invalid_argument("CN HMD mask frame extent unavailable");
        for (std::size_t f=0; f<frame_count; ++f) {
            MaskFrame frame{};
            frame.native_anchor_x=input.integer();
            frame.native_anchor_y=input.integer();
            model.declared_frames.push_back(std::move(frame));
        }
        for (auto& marker:model.declared_markers) marker={input.integer(),input.integer()};
        input.expect("Pass");
        for (auto& frame:model.declared_frames) {
            frame.width=input.integer(); frame.height=input.integer();
            if (frame.width<=0 || frame.height<=0) throw std::invalid_argument("CN HMD mask dimensions unavailable");
            const auto size=static_cast<std::uint64_t>(frame.width)*static_cast<std::uint64_t>(frame.height);
            if (size>input.remaining() || size>std::numeric_limits<std::int32_t>::max())
                throw std::invalid_argument("CN HMD mask data incomplete");
            frame.cells.reserve(static_cast<std::size_t>(size));
            for (std::uint64_t cell=0; cell<size; ++cell)
                // 00477432 reads int;0046BB40 stores its low byte, not bool.
                frame.cells.push_back(static_cast<std::uint8_t>(input.integer()));
        }
        asset.models_.push_back(std::move(model));
    }
}
CnHouseMapAsset CnHouseMapAsset::load_v16_file(const std::filesystem::path& path,
    std::size_t max_encoded_bytes, std::size_t max_plain_bytes) {
    const auto bytes=read_cn_asset_file(path,max_encoded_bytes);
    return from_v16_resource(bytes,max_plain_bytes);
}
CnMapPassability CnHouseMapAsset::compose_initial_passability() const {
    if (placements_.empty()) throw std::logic_error("CN HMD base placement unavailable");
    const auto select=[&](const Placement& placement) -> const MaskFrame& {
        const auto& model=models_.at(static_cast<std::size_t>(placement.model_index));
        const auto index=static_cast<std::uint8_t>(placement.packed_selector);
        if (index>=model.declared_frames.size())
            throw std::invalid_argument("CN HMD selected frame requires unresolved ROM-derived mask");
        return model.declared_frames[index];
    };
    const auto mask=[](const MaskFrame& frame) {
        return CnMapPassability::TileMask{frame.width,frame.height,frame.cells};
    };
    const auto& base_placement=placements_.front();
    const auto& base=select(base_placement);
    const auto& extent=models_.at(static_cast<std::size_t>(base_placement.model_index)).declared_frames.at(0);
    std::vector<CnMapPassability::BlockingOverlay> overlays;
    for (std::size_t i=1; i<placements_.size(); ++i) {
        const auto& placement=placements_[i];
        overlays.push_back({placement.native_x,placement.native_y,mask(select(placement))});
    }
    return CnMapPassability::compose_mode2(extent.width,extent.height,mask(base),overlays);
}
std::vector<std::optional<CnHouseMapAsset::ModelExtent>> CnHouseMapAsset::declared_model_extents() const {
    std::vector<std::optional<ModelExtent>> extents;
    extents.reserve(tiles_.size());
    for (const auto& tile:tiles_) {
        const auto& fields=tile.native_fields;
        const auto type=static_cast<std::uint32_t>(fields[0])&0xf;
        if ((type!=2 && type!=3 && type!=7) || fields[1]<=0 || fields[2]<=0) {
            extents.push_back(std::nullopt); continue;
        }
        // 00477D70 fields1/2 ->00475360 ->00475410 width/height, or
        // ->004758A0 ->00475960 explicit width/height branch. Width0 must
        // resolve image/ROM dimensions and is intentionally left unavailable.
        extents.push_back(ModelExtent{fields[1],fields[2]});
    }
    return model_extents(extents);
}
std::vector<std::optional<CnHouseMapAsset::ModelExtent>> CnHouseMapAsset::rom_model_extents(
    std::span<const CnRomAsset* const> slots) const {
    if (slots.size()!=roms_.size() || slots.size()>128)
        throw std::invalid_argument("CN ROMFILE slot binding unavailable");
    std::vector<std::optional<ModelExtent>> extents;
    extents.reserve(tiles_.size());
    for (const auto& tile:tiles_) {
        const auto& f=tile.native_fields;
        //00477D70 v1.6 type7 passes ROM/action fields to004758A0.
        // Type2 forces standalone-image selection; type3 has another loader.
        if ((static_cast<std::uint32_t>(f[0])&0xf)!=7 || f[3]<0 || f[4]<0 ||
            static_cast<std::size_t>(f[3])>=slots.size() || !slots[f[3]]) {
            extents.push_back(std::nullopt); continue;
        }
        const auto geometry=slots[f[3]]->tile_geometry(static_cast<std::uint32_t>(f[4]),f[1],f[2]);
        extents.push_back(geometry ? std::optional<ModelExtent>(ModelExtent{geometry->width,geometry->height}) : std::nullopt);
    }
    return model_extents(extents);
}
std::vector<std::optional<CnHouseMapAsset::ModelExtent>> CnHouseMapAsset::model_extents(
    std::span<const std::optional<ModelExtent>> extents) const {
    if (extents.size()!=tiles_.size()) throw std::invalid_argument("CN tile geometry table mismatch");
    const auto tile_extent=[&](const ModelLayer& layer) -> std::optional<ModelExtent> {
        if (layer.tile_index<0 || static_cast<std::size_t>(layer.tile_index)>=extents.size()) return std::nullopt;
        return extents[static_cast<std::size_t>(layer.tile_index)];
    };
    std::vector<std::optional<ModelExtent>> result;
    result.reserve(models_.size());
    for (const auto& model:models_) {
        const auto& body_layer=model.layers[0];
        const auto body=tile_extent(body_layer);
        if (!body) { result.push_back(std::nullopt); continue; }
        std::int64_t width=std::int64_t(body->width)+body_layer.offset_x;
        std::int64_t height=std::int64_t(body->height)+body_layer.offset_y;
        const auto& other_layer=model.layers[2];
        if (other_layer.tile_index!=-1) {
            const auto other=tile_extent(other_layer);
            if (!other) { result.push_back(std::nullopt); continue; }
            width=std::max(width,std::int64_t(other->width)+other_layer.offset_x)-
                std::min(body_layer.offset_x,other_layer.offset_x);
            height=std::max(height,std::int64_t(other->height)+other_layer.offset_y)-
                std::min(body_layer.offset_y,other_layer.offset_y);
        }
        // The native formulas do not include layer1 in bounds. Do not replace
        // this with a generic bounding box over all three layers.
        if (width<=0 || height<=0 || width>std::numeric_limits<std::int32_t>::max() ||
            height>std::numeric_limits<std::int32_t>::max()) {
            result.push_back(std::nullopt);
            continue;
        }
        result.push_back(ModelExtent{static_cast<std::int32_t>(width),static_cast<std::int32_t>(height)});
    }
    return result;
}
}
