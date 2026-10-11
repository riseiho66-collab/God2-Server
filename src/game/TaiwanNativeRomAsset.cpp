#include "game/TaiwanNativeRomAsset.h"
#include <algorithm>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <string_view>
#include <utility>

namespace god2 {
namespace {
struct Malformed {};
std::uint16_t u16(std::span<const std::uint8_t> b,std::size_t p) {
    return static_cast<std::uint16_t>(b[p]|(std::uint16_t(b[p+1])<<8));
}
std::uint32_t u32(std::span<const std::uint8_t> b,std::size_t p) {
    return std::uint32_t(u16(b,p))|(std::uint32_t(u16(b,p+2))<<16);
}
std::int32_t s16(std::span<const std::uint8_t> b,std::size_t p) {
    const auto n=u16(b,p);return n<0x8000?n:std::int32_t(n)-0x10000;
}
std::int32_t signed_word(std::uint32_t value) {
    const auto low=static_cast<std::uint16_t>(value);
    return low<0x8000?low:std::int32_t(low)-0x10000;
}
bool tagged(const TaiwanNativeRomAsset::Record& record,std::string_view tag) {
    return tag.size()==record.tag.size() && std::equal(record.tag.begin(),record.tag.end(),tag.begin());
}
std::vector<std::uint8_t> decoded(std::span<const std::uint8_t> source,std::size_t limit) {
    // Already recovered0516 ring codec is retained context, not new174 proof.
    if(source.size()<2 || source[0]!=5 || source[1]!=0x16) {
        if(source.empty() || source.size()>limit) throw Malformed{};
        return {source.begin(),source.end()};
    }
    if(source.size()<7) throw Malformed{};
    const auto size=u32(source,2);
    if(size==0 || size>limit) throw Malformed{};
    std::array<std::uint8_t,4096> ring;ring.fill(' ');
    std::array<bool,4096> valid{};std::fill_n(valid.begin(),0xFEE,true);
    std::size_t cursor=0xFEE,position=7;
    unsigned flags=0;
    std::vector<std::uint8_t> result;result.reserve(size);
    const auto append=[&](std::uint8_t byte) {
        if(result.size()>=size) throw Malformed{};
        result.push_back(byte);ring[cursor]=byte;valid[cursor]=true;cursor=(cursor+1)&4095;
    };
    while(position<source.size()) {
        flags>>=1;
        if(!(flags&0x100)) flags=source[position++]|0xFF00;
        if(flags&1) {
            if(position==source.size()) break;
            append(source[position++]);
        } else {
            if(source.size()-position<2) throw Malformed{};
            const auto low=source[position++],high=source[position++];
            const auto offset=std::size_t(low)|((std::size_t(high)&0xF0)<<4);
            for(std::size_t i=0;i<std::size_t(high&15)+3;++i) {
                const auto address=(offset+i)&4095;
                if(!valid[address]) throw Malformed{};
                append(ring[address]);
            }
        }
    }
    if(result.size()!=size) throw Malformed{};
    return result;
}
TaiwanNativeRomAsset::ImageExtent pcx_extent(std::span<const std::uint8_t> data,bool rows) {
    if(data.size()<128) throw Malformed{};
    // Actual0042BEB0 DWORD differences stored to low WORD, then signed loads.
    // This preserves the actual native narrowing instead of guessed PCX x/y.
    const auto width=signed_word(u32(data,8)-u32(data,4)+1);
    const auto height=signed_word(u32(data,10)-u32(data,6)+1);
    if(width<=0 || height<=0) throw Malformed{};
    const auto stride=u16(data,66);
    // Native writes each expanded row into width-sized storage. Padded rows or
    // overlong runs would overwrite that storage; source excludes that domain.
    if(stride!=width) throw Malformed{};
    std::size_t position=128;
    for(std::int32_t row=0;row<height;++row) {
        std::size_t expanded=0;
        while(expanded<stride) {
            if(position==data.size()) throw Malformed{};
            const auto token=data[position++];
            std::size_t count=1;
            if((token&0xC0)==0xC0) {
                count=token&0x3F;
                if(position==data.size()) throw Malformed{};
                ++position; // Actual repeated raw value retained in the full payload.
            }
            if(count>std::size_t(stride)-expanded) throw Malformed{};
            expanded+=count;
        }
    }
    const auto trailer=rows?std::uint64_t(height)*4:0;
    if(trailer!=data.size()-position) throw Malformed{};
    return {width,height};
}
TaiwanNativeRomAsset::ImageExtent tga_extent(std::span<const std::uint8_t> data,bool rows) {
    // Actual0042D160 reads twoDWORDs into overlapping imageheader fields;
    // only their low signed WORDs become width/height for geometry.
    if(data.size()<8) throw Malformed{};
    const auto width=s16(data,0),height=s16(data,4);
    if(width<=0 || height<=0) throw Malformed{};
    const auto pixels=std::uint64_t(width)*std::uint64_t(height)*2;
    const auto trailer=rows?std::uint64_t(height)*4:0;
    if(pixels+trailer!=data.size()-8) throw Malformed{};
    return {width,height};
}
}
struct TaiwanNativeRomAsset::Storage {
    const std::filesystem::path source;
    const std::vector<std::uint8_t> encoded,decoded;
    const std::vector<Record> records;
    const std::vector<Image> images;
    const std::vector<Action> actions;
    const std::uint32_t identity;
    Storage(std::filesystem::path path,std::vector<std::uint8_t> original,std::vector<std::uint8_t> plain,
        std::vector<Record> sections,std::vector<Image> pictures,std::vector<Action> declarations,std::uint32_t id):
        source(std::move(path)),encoded(std::move(original)),decoded(std::move(plain)),records(std::move(sections)),
        images(std::move(pictures)),actions(std::move(declarations)),identity(id) {}
};
TaiwanNativeRomAsset::TaiwanNativeRomAsset(std::shared_ptr<const Storage> retained):storage_(std::move(retained)) {}
const TaiwanNativeRomAsset::Storage& TaiwanNativeRomAsset::storage() const {
    if(!storage_) throw std::logic_error("TW ROM asset has no retained source");
    return *storage_;
}
std::optional<TaiwanNativeRomAsset> TaiwanNativeRomAsset::from_selected_resource(
    std::filesystem::path source,std::span<const std::uint8_t> encoded,std::size_t limit) {
    if(source.empty() || encoded.empty() || limit==0) return std::nullopt;
    // Full immutable originals, never aliases to a caller's mutable buffer.
    std::vector<std::uint8_t> original(encoded.begin(),encoded.end());
    std::vector<std::uint8_t> plain;
    std::vector<Record> records;
    std::vector<Image> images;
    std::vector<Action> actions;
    std::uint32_t identity=0xFFFFFFFF;
    try {
        plain=decoded(original,limit);
        const auto bytes=std::span<const std::uint8_t>(plain);
        if(bytes.size()<12 || !std::equal(bytes.begin(),bytes.begin()+8,"IGSROM02")) throw Malformed{};
        std::size_t cursor=12; // Native reads but does not use initial sizeDWORD.
        const auto read=[&]() {
            if(cursor>bytes.size() || bytes.size()-cursor<12) throw Malformed{};
            Record record{};record.header_offset=cursor;
            std::copy_n(bytes.begin()+cursor,8,record.tag.begin());
            record.size=u32(bytes,cursor+8);cursor+=12;record.offset=cursor;
            if(record.size>bytes.size()-cursor) throw Malformed{};
            cursor+=record.size;records.push_back(record);return record;
        };
        bool ended=false;
        while(cursor<bytes.size()) {
            const auto record=read();
            const auto data=bytes.subspan(record.offset,record.size);
            if(tagged(record,"FILE_END")) {
                if(record.size!=0 || cursor!=bytes.size()) throw Malformed{};
                ended=true;break;
            }
            if(tagged(record,"ACTINDEX")) {
                if(data.size()<2 || data.size()>4) throw Malformed{};
                identity=u16(data,0);continue; // Last actual ACTINDEX wins.
            }
            if(tagged(record,"ACT_DATA")) {
                if(data.size()!=48) throw Malformed{};
                const auto id=u32(data,0);
                if(id==0) continue; // Native zero-ID is not registered or nested-consumed.
                const auto steps=u32(data,16),frames=u32(data,20);
                if(steps>256 || frames>256 || actions.size()>=256 ||
                    std::find(data.begin()+24,data.end(),0)==data.end()) throw Malformed{};
                Action action{actions.size(),record,id,{},{}};
                for(std::uint32_t step=0;step<steps;++step) {
                    const auto entry=read();
                    if(entry.size%10!=0 || entry.size/10>std::numeric_limits<std::uint16_t>::max()) throw Malformed{};
                    action.steps.push_back(entry); // Native nested tags are not compared.
                }
                for(std::uint32_t frame=0;frame<frames;++frame) {
                    const auto pool=read();
                    if(pool.size!=10) throw Malformed{};
                    const auto blocks=read();action.frames.push_back({pool,blocks});
                }
                actions.push_back(std::move(action));continue;
            }
            const bool pcx=tagged(record,"PCX_DATA") || tagged(record,"PCX_RWIF") ||
                tagged(record,"PCA_DATA") || tagged(record,"PCA_RWIF") ||
                tagged(record,"PCS_DATA") || tagged(record,"PCS_RWIF");
            const bool tga=tagged(record,"TGA_DATA") || tagged(record,"TGA_RWIF");
            if(pcx || tga) {
                if(images.size()>=1024) throw Malformed{};
                const bool rows=record.tag[4]=='R';
                const auto extent=pcx?pcx_extent(data,rows):tga_extent(data,rows);
                images.push_back({images.size(),record,extent});
            }
            // Full palette/FLC/unknown payloads remain exact registered section
            // records. FLC occupies its separate native list, not image ordinals.
        }
        if(!ended) throw Malformed{};
    } catch(const Malformed&) {return std::nullopt;}
    return TaiwanNativeRomAsset(std::make_shared<const Storage>(std::move(source),std::move(original),std::move(plain),
        std::move(records),std::move(images),std::move(actions),identity));
}
std::optional<TaiwanNativeRomAsset> TaiwanNativeRomAsset::load_selected_file(
    const std::filesystem::path& path,std::size_t encoded_limit,std::size_t plain_limit) {
    if(path.empty() || encoded_limit==0 || encoded_limit>=static_cast<std::size_t>(
        std::numeric_limits<std::streamsize>::max())) return std::nullopt;
    std::ifstream file(path,std::ios::binary);
    if(!file) return std::nullopt;
    std::vector<std::uint8_t> bytes(encoded_limit+1);
    file.read(reinterpret_cast<char*>(bytes.data()),static_cast<std::streamsize>(bytes.size()));
    const auto count=file.gcount();
    if(file.bad() || count<=0 || static_cast<std::uint64_t>(count)>encoded_limit) return std::nullopt;
    bytes.resize(static_cast<std::size_t>(count));return from_selected_resource(path,bytes,plain_limit);
}
const TaiwanNativeRomAsset::Action* TaiwanNativeRomAsset::find_action(std::uint32_t operand) const noexcept {
    if(!storage_) return nullptr;
    if(operand<=256) return operand<storage_->actions.size()?&storage_->actions[operand]:nullptr;
    for(const auto& action:storage_->actions) if(action.id==operand) return &action;
    return nullptr;
}
std::span<const std::uint8_t> TaiwanNativeRomAsset::raw_record(const Record& record) const {
    const auto& held=storage();
    // Reject foreign record metadata, including forged slices into owned bytes.
    const auto found=std::find_if(held.records.begin(),held.records.end(),[&](const Record& actual) {
        return actual.header_offset==record.header_offset && actual.offset==record.offset &&
            actual.size==record.size && actual.tag==record.tag;
    });
    if(found==held.records.end()) throw std::invalid_argument("TW ROM record is not an owned section");
    return std::span<const std::uint8_t>(held.decoded).subspan(found->offset,found->size);
}
std::optional<TaiwanNativeRomAsset::TileGeometry> TaiwanNativeRomAsset::tile_geometry(
    std::uint32_t operand,std::int32_t width,std::int32_t height) const {
    const auto* action=find_action(operand);
    if(!action || action->steps.empty()) return std::nullopt;
    const auto first=raw_record(action->steps.front());
    std::optional<std::size_t> terminal;
    for(std::size_t at=0;at<first.size();at+=10) if(first[at]==0) {terminal=at;break;}
    if(!terminal) return std::nullopt;
    const auto frame_index=first[*terminal+3];
    if(frame_index>=action->frames.size()) return std::nullopt;
    const auto selected=raw_record(action->frames[frame_index].pool);
    const auto image_index=u16(selected,6);
    if(image_index>=storage_->images.size() || !storage_->images[image_index].extent) return std::nullopt;
    const auto image=*storage_->images[image_index].extent;
    if(width==0) {
        width=0;height=0;
        for(const auto& frame:action->frames) {
            const auto pool=raw_record(frame.pool);const auto index=u16(pool,6);
            if(index>=storage_->images.size() || !storage_->images[index].extent) return std::nullopt;
            width=std::max(width,storage_->images[index].extent->width-s16(pool,0));
            height=std::max(height,storage_->images[index].extent->height-s16(pool,2));
        }
    }
    if(width<=0 || height<=0) return std::nullopt;
    // Type7 has no other tile types' extra scanline. Reject overflowing native
    // DWORD additions/product rather than wrapping ceil numerator or framecount.
    const auto horizontal=std::int64_t(image.width)+width-1;
    const auto vertical=std::int64_t(image.height)+height-1;
    if(horizontal>std::numeric_limits<std::int32_t>::max() ||
        vertical>std::numeric_limits<std::int32_t>::max()) return std::nullopt;
    const auto count=(horizontal/width)*(vertical/height);
    if(count<=0 || count>std::numeric_limits<std::int32_t>::max()) return std::nullopt;
    return TileGeometry{width,height,static_cast<std::int32_t>(count)};
}
const std::filesystem::path& TaiwanNativeRomAsset::source() const {return storage().source;}
const std::vector<std::uint8_t>& TaiwanNativeRomAsset::encoded_bytes() const {return storage().encoded;}
const std::vector<std::uint8_t>& TaiwanNativeRomAsset::decoded_bytes() const {return storage().decoded;}
const std::vector<TaiwanNativeRomAsset::Record>& TaiwanNativeRomAsset::records() const {return storage().records;}
const std::vector<TaiwanNativeRomAsset::Image>& TaiwanNativeRomAsset::images() const {return storage().images;}
const std::vector<TaiwanNativeRomAsset::Action>& TaiwanNativeRomAsset::actions() const {return storage().actions;}
std::uint32_t TaiwanNativeRomAsset::native_rom_identity() const {return storage().identity;}
}
