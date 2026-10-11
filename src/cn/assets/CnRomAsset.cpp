#include "cn/assets/CnRomAsset.h"
#include "cn/assets/CnResourceBytes.h"
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <string_view>
#include <utility>

namespace god2cn {
namespace {
std::uint16_t u16(std::span<const std::uint8_t> b,std::size_t p) {
    return static_cast<std::uint16_t>(b[p]|(std::uint16_t(b[p+1])<<8));
}
std::int32_t s16(std::span<const std::uint8_t> b,std::size_t p) {
    const auto n=u16(b,p); return n<0x8000 ? n : std::int32_t(n)-0x10000;
}
std::uint32_t u32(std::span<const std::uint8_t> b,std::size_t p) {
    return std::uint32_t(u16(b,p))|(std::uint32_t(u16(b,p+2))<<16);
}
bool tagged(const CnRomAsset::Record& r,std::string_view value) {
    return value.size()==r.tag.size() && std::equal(r.tag.begin(),r.tag.end(),value.begin());
}
}
CnRomAsset CnRomAsset::from_resource(std::span<const std::uint8_t> encoded,std::size_t budget) {
    CnRomAsset result;
    result.bytes_=decode_cn_resource(encoded,budget);
    const auto bytes=std::span<const std::uint8_t>(result.bytes_);
    if (bytes.size()<12 || !std::equal(bytes.begin(),bytes.begin()+8,"IGSROM02"))
        throw std::invalid_argument("CN ROM header unavailable");
    // Native reads the initial size word but begins sections immediately.
    std::size_t at=12;
    const auto read=[&]() {
        if (at>bytes.size() || bytes.size()-at<12) throw std::invalid_argument("CN ROM section truncated");
        Record r{};
        std::copy_n(bytes.begin()+at,8,r.tag.begin()); r.size=u32(bytes,at+8); at+=12; r.offset=at;
        if (r.size>bytes.size()-at) throw std::invalid_argument("CN ROM payload truncated");
        at+=r.size; return r;
    };
    while (at<bytes.size()) {
        const auto record=read(); const auto data=bytes.subspan(record.offset,record.size);
        if (tagged(record,"FILE_END")) break;
        if (tagged(record,"ACTINDEX")) {
            // Both native readers copy into a local WORD/DWORD-sized field.
            // Smaller/oversized payloads are unqualified, not a fabricated ID.
            if(data.size()<2 || data.size()>4)throw std::invalid_argument("CN ROM ACTINDEX payload unqualified");
            result.act_index_=u16(data,0); // Last actual section wins.
            continue;
        }
        if (tagged(record,"ACT_DATA")) {
            if (data.size()!=48) throw std::invalid_argument("CN ROM action header variant unavailable");
            const auto id=u32(data,0);
            if (id==0) continue; // native does not register zero-ID actions
            const auto steps=u32(data,16), frames=u32(data,20);
            if (steps>256 || frames>256 || result.actions_.size()>=256)
                throw std::invalid_argument("CN ROM action table exceeds native slots");
            if (std::find(data.begin()+24,data.end(),0)==data.end())
                throw std::invalid_argument("CN ROM action label lacks terminator");
            Action action{record,id,{},{}};
            for (std::uint32_t i=0;i<steps;++i) {
                auto step=read();
                if (step.size%10!=0) throw std::invalid_argument("CN ROM step record incomplete");
                action.steps.push_back(step);
            }
            for (std::uint32_t i=0;i<frames;++i) {
                const auto pool=read();
                if (pool.size!=10) throw std::invalid_argument("CN ROM frame header variant unavailable");
                const auto blocks=read();
                action.frames.push_back({pool,blocks});
            }
            result.actions_.push_back(std::move(action));
        } else if (tagged(record,"PCX_DATA") || tagged(record,"PCX_RWIF") ||
                   tagged(record,"PCA_DATA") || tagged(record,"PCA_RWIF") ||
                   tagged(record,"PCS_DATA") || tagged(record,"PCS_RWIF")) {
            if (data.size()<128) throw std::invalid_argument("CN ROM image header truncated");
            //00419B30 copies inclusive bounds into signed16 image dimensions.
            const auto w=s16(data,8)-s16(data,4)+1, h=s16(data,10)-s16(data,6)+1;
            if (w<=0 || h<=0 || w>32767 || h>32767 || result.images_.size()>=1024)
                throw std::invalid_argument("CN ROM image dimensions unavailable");
            result.images_.push_back({w,h});
        } else if (tagged(record,"TGA_DATA") || tagged(record,"TGA_RWIF")) {
            //0041A690 reads two32-bit words into overlapping imageheader
            // destinations; low16 of each becomes width andheight.
            if (data.size()<8) throw std::invalid_argument("CN ROM TGA metadata truncated");
            const auto w=s16(data,0),h=s16(data,4);
            if (w<=0 || h<=0 || result.images_.size()>=1024)
                throw std::invalid_argument("CN ROM TGA dimensions unavailable");
            result.images_.push_back({w,h});
        }
        // Palette/FLC/unknown sections remain in bytes_. They do not supply
        // geometry here. No palette rendering or animation success is claimed.
    }
    return result;
}
CnRomAsset CnRomAsset::load_file(const std::filesystem::path& path,std::size_t encoded,std::size_t plain) {
    return from_resource(read_cn_asset_file(path,encoded),plain);
}
const CnRomAsset::Action* CnRomAsset::find_action(std::uint32_t id) const noexcept {
    if (id<=256) return id<actions_.size() ? &actions_[id] : nullptr;
    for (const auto& action:actions_) if (action.id==id) return &action;
    return nullptr;
}
std::uint16_t CnRomAsset::native_action_index_operand(std::uint16_t id) const noexcept {
    if(id<=256)return id;
    for(std::size_t i=0;i<actions_.size();++i)if(actions_[i].id==id)return static_cast<std::uint16_t>(i);
    return 0xffff;
}
std::span<const std::uint8_t> CnRomAsset::raw_record(const Record& r) const {
    if (r.offset>bytes_.size() || r.size>bytes_.size()-r.offset)
        throw std::invalid_argument("CN ROM record outside owned bytes");
    return std::span<const std::uint8_t>(bytes_).subspan(r.offset,r.size);
}
std::optional<CnRomAsset::TileGeometry> CnRomAsset::tile_geometry(std::uint32_t id,
    std::int32_t width,std::int32_t height) const {
    const auto* action=find_action(id);
    if (!action || action->steps.empty()) return std::nullopt;
    const auto step=raw_record(action->steps.front());
    std::optional<std::size_t> terminal;
    for (std::size_t at=0;at<step.size();at+=10) if (step[at]==0) { terminal=at;break; }
    if (!terminal) return std::nullopt;
    const auto frame_index=step[*terminal+3];
    if (frame_index>=action->frames.size()) return std::nullopt;
    const auto selected=raw_record(action->frames[frame_index].pool);
    const auto image_index=u16(selected,6);
    if (image_index>=images_.size()) return std::nullopt;
    const auto image=images_[image_index];
    if (width==0) {
        width=0; height=0;
        for (const auto& frame:action->frames) {
            const auto pool=raw_record(frame.pool); const auto index=u16(pool,6);
            if (index>=images_.size()) return std::nullopt;
            width=std::max(width,images_[index].width-s16(pool,0));
            height=std::max(height,images_[index].height-s16(pool,2));
        }
    }
    if (width<=0 || height<=0) return std::nullopt;
    const auto frames=((std::int64_t(image.width)+width-1)/width)*
        ((std::int64_t(image.height)+height-1)/height);
    if (frames<=0 || frames>std::numeric_limits<std::int32_t>::max()) return std::nullopt;
    return TileGeometry{width,height,static_cast<std::int32_t>(frames)};
}
}
