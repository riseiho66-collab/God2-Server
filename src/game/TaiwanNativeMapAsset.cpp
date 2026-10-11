#include "game/TaiwanNativeMapAsset.h"
#include <algorithm>
#include <array>
#include <bitset>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2 {
namespace {
struct Malformed {};
bool space(std::uint8_t c) {return c==' ' || (c>='\t' && c<='\r');}
std::uint8_t lower(std::uint8_t c) {return c>='A' && c<='Z'?c+('a'-'A'):c;}
class Cursor {
public:
    Cursor(std::span<const std::uint8_t> bytes,std::size_t start=0):bytes_(bytes),position_(start) {}
    std::size_t position() const {return position_;}
    std::string word() {
        skip();const auto first=position_;
        while(position_<bytes_.size() && !space(bytes_[position_])) ++position_;
        if(first==position_) throw Malformed{};
        return {reinterpret_cast<const char*>(bytes_.data()+first),position_-first};
    }
    void expect(std::string_view text) {
        const auto found=word();
        if(found.size()!=text.size()) throw Malformed{};
        for(std::size_t i=0;i<text.size();++i)
            if(lower(static_cast<std::uint8_t>(found[i]))!=lower(static_cast<std::uint8_t>(text[i]))) throw Malformed{};
    }
    std::int32_t decimal() {
        skip();bool negative=false;
        if(position_<bytes_.size() && (bytes_[position_]=='+' || bytes_[position_]=='-')) negative=bytes_[position_++]=='-';
        const auto first=position_;
        std::uint64_t value=0,limit=negative?2147483648ULL:2147483647ULL;
        while(position_<bytes_.size() && bytes_[position_]>='0' && bytes_[position_]<='9') {
            const auto digit=std::uint64_t(bytes_[position_]-'0');
            if(value>(limit-digit)/10) throw Malformed{};
            value=value*10+digit;++position_;
        }
        if(first==position_) throw Malformed{};
        return static_cast<std::int32_t>(negative?-static_cast<std::int64_t>(value):static_cast<std::int64_t>(value));
    }
    std::size_t count() {
        const auto value=decimal();
        if(value<0 || static_cast<std::size_t>(value)>bytes_.size()-position_) throw Malformed{};
        return static_cast<std::size_t>(value);
    }
    bool finish() {skip();return position_==bytes_.size();}
private:
    void skip() {while(position_<bytes_.size() && space(bytes_[position_])) ++position_;}
    std::span<const std::uint8_t> bytes_;
    std::size_t position_;
};
std::optional<std::vector<std::uint8_t>> decode(std::span<const std::uint8_t> raw,std::size_t budget) {
    // TW00402530 selects an actual0516 source;00401D20 decodes it to a stream.
    // Explicit already-selected plain sources are retained without path guesses.
    if(raw.size()<2 || raw[0]!=5 || raw[1]!=0x16) {
        if(raw.size()>budget) return std::nullopt;
        return std::vector<std::uint8_t>(raw.begin(),raw.end());
    }
    if(raw.size()<7) return std::nullopt;
    const auto expected=std::uint32_t(raw[2])|(std::uint32_t(raw[3])<<8)|
        (std::uint32_t(raw[4])<<16)|(std::uint32_t(raw[5])<<24);
    if(expected>budget) return std::nullopt;
    std::array<std::uint8_t,4096> ring{};
    std::bitset<4096> initialized;
    for(std::size_t i=0;i<0xfee;++i) {ring[i]=0x20;initialized.set(i);}
    std::size_t cursor=0xfee,offset=7;
    std::uint32_t flags=0;
    std::vector<std::uint8_t> plain;plain.reserve(expected);
    const auto append=[&](std::uint8_t value) {
        if(plain.size()>=expected) throw Malformed{};
        plain.push_back(value);ring[cursor]=value;initialized.set(cursor);cursor=(cursor+1)&0xfff;
    };
    try {
        while(offset<raw.size()) {
            flags>>=1;
            if((flags&0x100)==0) {
                flags=raw[offset++]|0xff00;
                if(offset==raw.size()) break;
            }
            const auto first=raw[offset++];
            if(flags&1) {append(first);continue;}
            if(offset==raw.size()) break;
            const auto second=raw[offset++];
            const std::size_t position=first|((second&0xf0)<<4),length=(second&0xf)+3;
            for(std::size_t i=0;i<length;++i) {
                const auto source=(position+i)&0xfff;
                if(!initialized.test(source)) throw Malformed{};
                append(ring[source]);
            }
        }
    }catch(const Malformed&) {return std::nullopt;}
    if(plain.size()!=expected) return std::nullopt;
    return plain;
}
std::optional<std::int32_t> narrow(std::int64_t value) {
    if(value<std::numeric_limits<std::int32_t>::min() || value>std::numeric_limits<std::int32_t>::max()) return std::nullopt;
    return static_cast<std::int32_t>(value);
}
}
struct TaiwanNativeMapAsset::Storage {
    const std::filesystem::path source;
    const std::vector<std::uint8_t> encoded;
    const TaiwanNativeTileMasks masks;
    const std::vector<std::string> roms;
    const std::vector<Tile> tiles;
    const std::vector<Placement> placements;
    const std::size_t cursor;
    Storage(std::filesystem::path path,std::vector<std::uint8_t> raw,TaiwanNativeTileMasks library,
        std::vector<std::string> references,std::vector<Tile> native_tiles,std::vector<Placement> records,std::size_t end):
        source(std::move(path)),encoded(std::move(raw)),masks(std::move(library)),roms(std::move(references)),
        tiles(std::move(native_tiles)),placements(std::move(records)),cursor(end) {}
};
TaiwanNativeMapAsset::TaiwanNativeMapAsset(std::shared_ptr<const Storage> retained):storage_(std::move(retained)) {}
const TaiwanNativeMapAsset::Storage& TaiwanNativeMapAsset::storage() const {
    if(!storage_) throw std::logic_error("TW map asset has no retained actual source");
    return *storage_;
}
std::optional<TaiwanNativeMapAsset> TaiwanNativeMapAsset::from_selected_resource(
    std::filesystem::path source,std::span<const std::uint8_t> encoded,std::size_t budget) {
    if(source.empty() || encoded.empty()) return std::nullopt;
    std::vector<std::uint8_t> original(encoded.begin(),encoded.end());
    auto plain=decode(original,budget);
    if(!plain || std::find(plain->begin(),plain->end(),std::uint8_t(0))!=plain->end()) return std::nullopt;
    Cursor input(*plain);
    try {
        // Actual00437900 reads header/version. Other native historical layouts
        // are not promoted into this recovered exact v1.6 branch.
        if(input.word()!="HMD") return std::nullopt;
        const auto version=input.word();
        if(version!="v1.6") return std::nullopt;
        input.expect("ROMFILE");
        const auto rom_count=input.count();
        std::vector<std::string> roms;roms.reserve(rom_count);
        for(std::size_t i=0;i<rom_count;++i) roms.push_back(input.word());
        input.expect("TileModel");
        const auto tile_count=input.count();
        std::vector<Tile> tiles;tiles.reserve(tile_count);
        for(std::size_t i=0;i<tile_count;++i) {
            Tile tile{};tile.native_label=input.word();
            for(auto& field:tile.fields) field=input.decimal();
            tiles.push_back(std::move(tile));
        }
        auto masks=TaiwanNativeTileMasks::read_v16_prefix(*plain,input.position(),tile_count,version);
        if(!masks) return std::nullopt;
        Cursor placements_input(masks->decoded_bytes(),masks->end_cursor());
        placements_input.expect("Model");
        const auto count=placements_input.count();
        if(count==0) return std::nullopt; // No guessed base/default empty world.
        std::vector<Placement> placements;placements.reserve(count);
        for(std::size_t i=0;i<count;++i) {
            Placement placement{};placement.source_begin=placements_input.position();
            placement.model=placements_input.decimal();placement.screen_x=placements_input.decimal();
            placement.screen_y=placements_input.decimal();placement.native_x=placements_input.decimal();
            placement.native_y=placements_input.decimal();placement.selector=placements_input.decimal();
            if(placement.model<0 || static_cast<std::size_t>(placement.model)>=masks->models().size()) return std::nullopt;
            if(i) {
                Placement::Object object{};
                object.native_1c=placements_input.decimal();object.native_20=placements_input.decimal();
                object.script_flag=placements_input.decimal();
                if(object.script_flag==1) object.script=placements_input.word();
                object.native_38=placements_input.decimal();placement.object=std::move(object);
            }
            placement.source_end=placements_input.position();placements.push_back(std::move(placement));
        }
        if(!placements_input.finish()) return std::nullopt;
        const auto cursor=placements_input.position();
        return TaiwanNativeMapAsset(std::make_shared<const Storage>(std::move(source),std::move(original),
            std::move(*masks),std::move(roms),std::move(tiles),std::move(placements),cursor));
    }catch(const Malformed&) {return std::nullopt;}
}
std::optional<TaiwanNativeMapAsset> TaiwanNativeMapAsset::load_selected_file(
    const std::filesystem::path& source,std::size_t encoded_budget,std::size_t plain_budget) {
    if(source.empty()) return std::nullopt;
    std::ifstream input(source,std::ios::binary|std::ios::ate);
    if(!input) return std::nullopt;
    const std::streamoff length=input.tellg();
    if(length<0 || static_cast<std::uintmax_t>(length)>encoded_budget ||
       static_cast<std::uintmax_t>(length)>static_cast<std::uintmax_t>(std::numeric_limits<std::streamsize>::max())) return std::nullopt;
    std::vector<std::uint8_t> bytes(static_cast<std::size_t>(length));input.seekg(0);
    if(!bytes.empty() && !input.read(reinterpret_cast<char*>(bytes.data()),static_cast<std::streamsize>(bytes.size()))) return std::nullopt;
    if(input.peek()!=std::char_traits<char>::eof() || input.bad()) return std::nullopt;
    return from_selected_resource(source,bytes,plain_budget);
}
std::optional<TaiwanNativeMapAsset::Extent> TaiwanNativeMapAsset::explicit_model_extent(std::size_t model) const {
    if(!storage_ || model>=storage_->masks.models().size()) return std::nullopt;
    const auto& layers=storage_->masks.models()[model].layers;
    const auto tile=[&](const TaiwanNativeTileMasks::Layer& layer)->std::optional<Extent> {
        if(layer.tile_index<0 || static_cast<std::size_t>(layer.tile_index)>=storage_->tiles.size()) return std::nullopt;
        const auto& f=storage_->tiles[layer.tile_index].fields;
        const auto type=static_cast<std::uint32_t>(f[0])&0xf;
        //0044C420 dispatch to0044A6F0/0044A800; explicit positive width/height
        // avoid the unresolved image/ROM geometry branch. Type3 is not claimed.
        if((type!=2 && type!=7) || f[1]<=0 || f[2]<=0) return std::nullopt;
        return Extent{f[1],f[2]};
    };
    const auto body=tile(layers[0]);
    if(!body) return std::nullopt;
    const auto body_w=narrow(std::int64_t(body->width)+layers[0].offset_x);
    const auto body_h=narrow(std::int64_t(body->height)+layers[0].offset_y);
    if(!body_w || !body_h) return std::nullopt;
    auto width=body_w,height=body_h;
    if(layers[2].tile_index!=-1) {
        const auto other=tile(layers[2]);
        if(!other) return std::nullopt;
        const auto other_w=narrow(std::int64_t(other->width)+layers[2].offset_x);
        const auto other_h=narrow(std::int64_t(other->height)+layers[2].offset_y);
        if(!other_w || !other_h) return std::nullopt;
        width=narrow(std::int64_t(std::max(*body_w,*other_w))-std::min(layers[0].offset_x,layers[2].offset_x));
        height=narrow(std::int64_t(std::max(*body_h,*other_h))-std::min(layers[0].offset_y,layers[2].offset_y));
    }
    if(!width || !height || *width<=0 || *height<=0) return std::nullopt;
    return Extent{*width,*height};
}
std::optional<std::vector<TaiwanNativeMapAsset::OrderedObject>> TaiwanNativeMapAsset::ordered_objects() const {
    if(!storage_ || storage_->placements.empty()) return std::nullopt;
    std::vector<OrderedObject> ordered;ordered.reserve(storage_->placements.size()-1);
    for(std::size_t i=1;i<storage_->placements.size();++i) {
        const auto& placement=storage_->placements[i];
        const auto extent=explicit_model_extent(static_cast<std::size_t>(placement.model));
        if(!extent) return std::nullopt;
        const auto key=narrow(std::int64_t(placement.screen_y)+extent->height);
        if(!key) return std::nullopt;
        ordered.push_back({i,*key,*extent});
    }
    std::stable_sort(ordered.begin(),ordered.end(),[](const auto& a,const auto& b){return a.native_sort_key<b.native_sort_key;});
    return ordered;
}
std::optional<TaiwanNativeGrid::Material> TaiwanNativeMapAsset::compose_material() const {
    if(!storage_ || storage_->placements.empty()) return std::nullopt;
    const auto& base=storage_->placements.front();
    auto zero=storage_->masks.frame_zero(static_cast<std::size_t>(base.model));
    auto selected=storage_->masks.select(static_cast<std::size_t>(base.model),static_cast<std::uint32_t>(base.selector));
    auto order=ordered_objects();
    if(!zero || !selected || !order) return std::nullopt;
    TaiwanNativeGrid::Material material{std::move(*zero),std::move(*selected),static_cast<std::uint32_t>(base.selector),{}};
    material.actual_ordered_overlays.reserve(order->size());
    for(const auto& object:*order) {
        const auto& placement=storage_->placements[object.placement];
        auto mask=storage_->masks.select(static_cast<std::size_t>(placement.model),static_cast<std::uint32_t>(placement.selector));
        if(!mask) return std::nullopt;
        material.actual_ordered_overlays.push_back({placement.native_x,placement.native_y,
            static_cast<std::uint32_t>(placement.selector),std::move(*mask)});
    }
    return material;
}
std::optional<SharedTaiwanNativeMovementScene::Resources> TaiwanNativeMapAsset::resources(
    std::uint64_t resource_generation,std::uint64_t initial_scene_generation) const {
    auto material=compose_material();
    if(!material) return std::nullopt;
    return SharedTaiwanNativeMovementScene::Resources::compose_mode2(std::move(*material),resource_generation,initial_scene_generation);
}
std::optional<SharedTaiwanNativeMovementScene::Native> TaiwanNativeMapAsset::native_scene(
    std::uint64_t resource_generation,std::uint64_t initial_scene_generation,RecoveredPosition position,
    std::uint8_t direction,SharedTaiwanNativeMovementScene::ResourceCurrent current) const {
    if(!storage_ || !current || direction>7) return std::nullopt;
    auto images=resources(resource_generation,initial_scene_generation);
    if(!images) return std::nullopt;
    const auto retained=storage_; // Whole original input and model/placement identities retained strongly.
    const auto expected=*images->composed_grid; // Shares private immutable deep-owned Grid storage only.
    return SharedTaiwanNativeMovementScene::Native(std::move(*images),position,direction,
        [retained,expected,resource_generation,initial_scene_generation,current=std::move(current)]
        (auto check,const auto& scope,const auto& images) {
            const auto matches=[&] {
                return images.composed_grid && images.complete() &&
                    images.cell_source()==SharedTaiwanNativeMovementScene::CellSource::ComposedMode2 &&
                    images.actual_resource_generation==resource_generation &&
                    images.actual_initial_scene_generation==initial_scene_generation &&
                    std::addressof(images.composed_grid->material())==std::addressof(expected.material()) &&
                    std::addressof(images.composed_grid->bytes())==std::addressof(expected.bytes());
            };
            // Public Native inputs cannot substitute an unrelated complete grid,
            // even with matching generations. No recomposition inside Current.
            return retained && matches() && current(check,scope,images) && matches();
        });
}
const std::filesystem::path& TaiwanNativeMapAsset::source() const {return storage().source;}
const std::vector<std::uint8_t>& TaiwanNativeMapAsset::encoded_bytes() const {return storage().encoded;}
const TaiwanNativeTileMasks& TaiwanNativeMapAsset::masks() const {return storage().masks;}
const std::vector<std::string>& TaiwanNativeMapAsset::rom_references() const {return storage().roms;}
const std::vector<TaiwanNativeMapAsset::Tile>& TaiwanNativeMapAsset::tiles() const {return storage().tiles;}
const std::vector<TaiwanNativeMapAsset::Placement>& TaiwanNativeMapAsset::placements() const {return storage().placements;}
std::size_t TaiwanNativeMapAsset::consumed_cursor() const {return storage().cursor;}
struct TaiwanNativeMapAsset::RomBound::Storage {
    const TaiwanNativeMapAsset asset;
    const std::vector<RomSlot> slots;
    Storage(TaiwanNativeMapAsset retained,std::vector<RomSlot> inputs):asset(std::move(retained)),slots(std::move(inputs)) {}
};
TaiwanNativeMapAsset::RomBound::RomBound(std::shared_ptr<const Storage> retained):storage_(std::move(retained)) {}
const TaiwanNativeMapAsset::RomBound::Storage& TaiwanNativeMapAsset::RomBound::storage() const {
    if(!storage_) throw std::logic_error("TW ROM-bound map has no retained actual sources");
    return *storage_;
}
std::optional<TaiwanNativeMapAsset::RomBound> TaiwanNativeMapAsset::bind_rom_sources(std::vector<RomSlot> inputs) const {
    if(!storage_ || inputs.size()!=storage_->roms.size() || inputs.size()>128) return std::nullopt;
    // Copy even moved input vectors: caller aliases to slot elements must not
    // remain aliases to this immutable binding. ROM handles own const Storage.
    std::vector<RomSlot> slots=inputs;
    try {
        for(std::size_t i=0;i<slots.size();++i) {
            const auto& slot=slots[i];
            if(slot.ordinal!=i || slot.native_reference!=storage_->roms[i] || !slot.actual_resource_generation ||
               slot.source.source().empty() || slot.source.encoded_bytes().empty()) return std::nullopt;
        }
    }catch(const std::logic_error&) {return std::nullopt;} // Empty/moved-from parsed source is not a slot.
    return RomBound(std::make_shared<const RomBound::Storage>(*this,std::move(slots)));
}
std::optional<TaiwanNativeRomAsset::TileGeometry> TaiwanNativeMapAsset::RomBound::tile_geometry(std::size_t tile) const {
    if(!storage_ || tile>=storage_->asset.tiles().size()) return std::nullopt;
    const auto& f=storage_->asset.tiles()[tile].fields;
    // Actual v1.6 type7 F3 is the ROMFILE ordinal. Full F4 DWORD reaches
    //0042D050/0042AF40: unsigned<=256 positional, else first matching DWORD ID.
    // Do not substitute ACTINDEX for ordinal or truncate action to WORD.
    if((static_cast<std::uint32_t>(f[0])&0xf)!=7 || f[1]<0 || f[3]<0 ||
       static_cast<std::size_t>(f[3])>=storage_->slots.size()) return std::nullopt;
    const auto& slot=storage_->slots[static_cast<std::size_t>(f[3])];
    return slot.source.tile_geometry(static_cast<std::uint32_t>(f[4]),f[1],f[2]);
}
std::optional<TaiwanNativeMapAsset::Extent> TaiwanNativeMapAsset::RomBound::model_extent(std::size_t model) const {
    if(!storage_ || model>=storage_->asset.masks().models().size()) return std::nullopt;
    const auto& layers=storage_->asset.masks().models()[model].layers;
    const auto tile=[&](const TaiwanNativeTileMasks::Layer& layer)->std::optional<Extent> {
        if(layer.tile_index<0 || static_cast<std::size_t>(layer.tile_index)>=storage_->asset.tiles().size()) return std::nullopt;
        const auto& f=storage_->asset.tiles()[layer.tile_index].fields;
        const auto type=static_cast<std::uint32_t>(f[0])&0xf;
        if(type==2 && f[1]>0 && f[2]>0) return Extent{f[1],f[2]};
        if(type!=7) return std::nullopt;
        const auto geometry=tile_geometry(static_cast<std::size_t>(layer.tile_index));
        if(!geometry) return std::nullopt;
        return Extent{geometry->width,geometry->height};
    };
    const auto body=tile(layers[0]);
    if(!body) return std::nullopt;
    const auto body_w=narrow(std::int64_t(body->width)+layers[0].offset_x);
    const auto body_h=narrow(std::int64_t(body->height)+layers[0].offset_y);
    if(!body_w || !body_h) return std::nullopt;
    auto width=body_w,height=body_h;
    if(layers[2].tile_index!=-1) {
        const auto other=tile(layers[2]);
        if(!other) return std::nullopt;
        const auto other_w=narrow(std::int64_t(other->width)+layers[2].offset_x);
        const auto other_h=narrow(std::int64_t(other->height)+layers[2].offset_y);
        if(!other_w || !other_h) return std::nullopt;
        width=narrow(std::int64_t(std::max(*body_w,*other_w))-std::min(layers[0].offset_x,layers[2].offset_x));
        height=narrow(std::int64_t(std::max(*body_h,*other_h))-std::min(layers[0].offset_y,layers[2].offset_y));
    }
    if(!width || !height || *width<=0 || *height<=0) return std::nullopt;
    return Extent{*width,*height};
}
std::optional<std::vector<TaiwanNativeMapAsset::OrderedObject>> TaiwanNativeMapAsset::RomBound::ordered_objects() const {
    if(!storage_ || storage_->asset.placements().empty()) return std::nullopt;
    const auto& placements=storage_->asset.placements();
    std::vector<OrderedObject> ordered;ordered.reserve(placements.size()-1);
    for(std::size_t i=1;i<placements.size();++i) {
        const auto& placement=placements[i];
        const auto extent=model_extent(static_cast<std::size_t>(placement.model));
        if(!extent) return std::nullopt;
        const auto key=narrow(std::int64_t(placement.screen_y)+extent->height);
        if(!key) return std::nullopt;
        ordered.push_back({i,*key,*extent});
    }
    std::stable_sort(ordered.begin(),ordered.end(),[](const auto& a,const auto& b){return a.native_sort_key<b.native_sort_key;});
    return ordered;
}
std::optional<TaiwanNativeGrid::Material> TaiwanNativeMapAsset::RomBound::compose_material() const {
    if(!storage_ || storage_->asset.placements().empty()) return std::nullopt;
    const auto& placements=storage_->asset.placements();
    const auto& masks=storage_->asset.masks();const auto& base=placements.front();
    // Qualify the actual base's native body/layer2 geometry too; its sprite
    // extent remains separate from the declared frame0 grid loop dimensions.
    if(!model_extent(static_cast<std::size_t>(base.model))) return std::nullopt;
    auto zero=masks.frame_zero(static_cast<std::size_t>(base.model));
    auto selected=masks.select(static_cast<std::size_t>(base.model),static_cast<std::uint32_t>(base.selector));
    auto order=ordered_objects();
    if(!zero || !selected || !order) return std::nullopt;
    TaiwanNativeGrid::Material material{std::move(*zero),std::move(*selected),static_cast<std::uint32_t>(base.selector),{}};
    material.actual_ordered_overlays.reserve(order->size());
    for(const auto& object:*order) {
        const auto& placement=placements[object.placement];
        auto mask=masks.select(static_cast<std::size_t>(placement.model),static_cast<std::uint32_t>(placement.selector));
        if(!mask) return std::nullopt;
        material.actual_ordered_overlays.push_back({placement.native_x,placement.native_y,
            static_cast<std::uint32_t>(placement.selector),std::move(*mask)});
    }
    return material;
}
std::optional<SharedTaiwanNativeMovementScene::Resources> TaiwanNativeMapAsset::RomBound::resources(
    std::uint64_t resource_generation,std::uint64_t initial_scene_generation) const {
    auto material=compose_material();
    if(!material) return std::nullopt;
    return SharedTaiwanNativeMovementScene::Resources::compose_mode2(std::move(*material),resource_generation,initial_scene_generation);
}
std::optional<SharedTaiwanNativeMovementScene::Native> TaiwanNativeMapAsset::RomBound::native_scene(
    std::uint64_t resource_generation,std::uint64_t initial_scene_generation,RecoveredPosition position,
    std::uint8_t direction,SharedTaiwanNativeMovementScene::ResourceCurrent current) const {
    if(!storage_ || !current || direction>7) return std::nullopt;
    auto images=resources(resource_generation,initial_scene_generation);
    if(!images) return std::nullopt;
    const auto retained=storage_; // Whole exact HMD, ordinal/name slots and original ROM inputs retained.
    const auto expected=*images->composed_grid;
    return SharedTaiwanNativeMovementScene::Native(std::move(*images),position,direction,
        [retained,expected,resource_generation,initial_scene_generation,current=std::move(current)]
        (auto check,const auto& scope,const auto& images) {
            const auto matches=[&] {
                return images.composed_grid && images.complete() &&
                    images.cell_source()==SharedTaiwanNativeMovementScene::CellSource::ComposedMode2 &&
                    images.actual_resource_generation==resource_generation &&
                    images.actual_initial_scene_generation==initial_scene_generation &&
                    std::addressof(images.composed_grid->material())==std::addressof(expected.material()) &&
                    std::addressof(images.composed_grid->bytes())==std::addressof(expected.bytes());
            };
            return retained && matches() && current(check,scope,images) && matches();
        });
}
const TaiwanNativeMapAsset& TaiwanNativeMapAsset::RomBound::asset() const {return storage().asset;}
const std::vector<TaiwanNativeMapAsset::RomSlot>& TaiwanNativeMapAsset::RomBound::slots() const {return storage().slots;}
}
