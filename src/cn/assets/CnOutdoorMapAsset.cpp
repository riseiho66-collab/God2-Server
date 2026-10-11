#include "cn/assets/CnOutdoorMapAsset.h"
#include "cn/assets/CnAssetTokens.h"
#include "cn/assets/CnResourceBytes.h"
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2cn {
namespace {
std::string lower_ascii(std::string_view value) {
    std::string out(value);
    for (auto& c:out) if (c>='A' && c<='Z') c=static_cast<char>(c+('a'-'A'));
    return out;
}
void optional_rom_reference(detail::CnAssetTokens& input,CnOutdoorMapAsset::Tile& tile) {
    const auto line=input.line_remainder();
    detail::CnAssetTokens tail(std::span<const std::uint8_t>(
        reinterpret_cast<const std::uint8_t*>(line.data()),line.size()));
    if (!tail.empty()) tile.rom_slot=tail.integer();
    if (!tail.empty()) tile.action_id=tail.integer();
    tail.finish();
}
}
CnOutdoorMapAsset CnOutdoorMapAsset::from_v12_resource(std::span<const std::uint8_t> bytes,
    std::size_t budget) {
    const auto plain=decode_cn_resource(bytes,budget);
    detail::CnAssetTokens input(plain);
    if (input.next()!="MDT" || input.next()!="v1.2")
        throw std::invalid_argument("CN MDT version unavailable");
    CnOutdoorMapAsset result;
    input.expect("DTime"); result.dtime_=input.integer();
    input.expect("MAPNUM"); result.width_=input.integer(); result.height_=input.integer();
    if (result.width_<=0 || result.height_<=0 ||
        std::int64_t(result.width_)*result.height_>std::numeric_limits<std::int32_t>::max()/4)
        throw std::invalid_argument("CN MDT chunk extent unavailable");
    input.expect("RomFile");
    const auto rom_count=input.count();
    if (rom_count>128) throw std::invalid_argument("CN MDT ROM count exceeds native slots");
    for (std::size_t i=0;i<rom_count;++i) result.roms_.emplace_back(input.next());
    input.expect("MAT");
    const auto material_count=input.count();
    if (material_count>64) throw std::invalid_argument("CN MDT material count exceeds native slots");
    for (std::size_t i=0;i<material_count;++i) {
        Material material{};
        material.declaration=input.next(); material.name=input.next();
        for (auto& value:material.color) value=input.integer();
        const auto flag=input.next();
        if (flag.size()!=1) throw std::invalid_argument("CN MDT material flag unavailable");
        material.native_flag=flag.front();
        result.materials_.push_back(std::move(material));
    }
    input.expect("TILE");
    const auto tile_count=input.count();
    for (std::size_t i=0;i<tile_count;++i) {
        Tile tile{};
        const auto kind=lower_ascii(input.next());
        if (kind=="link" || kind=="link2") {
            tile.kind=kind=="link" ? Tile::Kind::link : Tile::Kind::link2;
            tile.first_material=input.next(); tile.second_material=input.next();
            tile.image_reference=input.next();
            for (auto& field:tile.fields) field=input.integer();
            //00462980 asserts this flag is N before reading the following
            // integer list. Other variants require their native contract.
            if (input.next()!="N") throw std::invalid_argument("CN MDT link flag variant unavailable");
            const auto count=input.count();
            for (std::size_t n=0;n<count;++n) tile.animation_fields.push_back(input.integer());
        } else if (kind=="replace") {
            tile.kind=Tile::Kind::replace;
            tile.first_material=input.next(); tile.fields[0]=input.integer();
            tile.image_reference=input.next();
        } else if (kind=="t1x1" || kind=="t2x2") {
            tile.kind=kind=="t1x1" ? Tile::Kind::t1x1 : Tile::Kind::t2x2;
            tile.image_reference=input.next(); tile.fields[0]=input.integer();
        } else {
            throw std::invalid_argument("CN MDT tile declaration unavailable");
        }
        optional_rom_reference(input,tile);
        result.tiles_.push_back(std::move(tile));
    }
    input.finish();
    return result;
}
CnOutdoorMapAsset CnOutdoorMapAsset::load_v12_file(const std::filesystem::path& path,
    std::size_t encoded,std::size_t plain) {
    return from_v12_resource(read_cn_asset_file(path,encoded),plain);
}
std::optional<CnOutdoorTerrain::InitialWorldPlacement> CnOutdoorMapAsset::prepare_initial_at_world(
    const CnOutdoorTerrain& terrain,const CnOutdoorModelAsset& models,
    std::span<const CnRomAsset* const> slots,std::int32_t x,std::int32_t y) const {
    return models.prepare_initial_with_rom_geometry(terrain,x,y,width_,height_,slots);
}
}
