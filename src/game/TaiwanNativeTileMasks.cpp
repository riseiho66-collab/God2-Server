#include "game/TaiwanNativeTileMasks.h"
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2 {
namespace {
bool whitespace(std::uint8_t c) {return c==' ' || (c>='\t' && c<='\r');}
std::uint8_t lower(std::uint8_t c) {return c>='A' && c<='Z'?c+('a'-'A'):c;}
struct Malformed {};
class Cursor {
public:
    Cursor(std::span<const std::uint8_t> bytes,std::size_t position):bytes_(bytes),position_(position) {}
    std::size_t position() const {return position_;}
    std::size_t remaining() const {return bytes_.size()-position_;}
    void expect(std::string_view expected) {
        const auto begin=position_;
        skip();
        const auto token=position_;
        while(position_<bytes_.size() && !whitespace(bytes_[position_])) ++position_;
        if(position_-token!=expected.size()) throw Malformed{};
        for(std::size_t i=0;i<expected.size();++i)
            if(lower(bytes_[token+i])!=lower(static_cast<std::uint8_t>(expected[i]))) throw Malformed{};
        consumed.push_back({TaiwanNativeTileMasks::Consumption::Kind::Word,begin,token,position_,std::nullopt});
    }
    std::int32_t decimal() {
        // Actual fscanf %d skips whitespace and consumes a signed decimal
        // prefix, leaving its first non-digit for the next actual read.
        const auto begin=position_;
        skip();
        const auto token=position_;
        bool negative=false;
        if(position_<bytes_.size() && (bytes_[position_]=='+' || bytes_[position_]=='-'))
            negative=bytes_[position_++]=='-';
        const auto digits=position_;
        std::uint64_t magnitude=0;
        const std::uint64_t limit=negative?2147483648ULL:2147483647ULL;
        while(position_<bytes_.size() && bytes_[position_]>='0' && bytes_[position_]<='9') {
            const auto digit=std::uint64_t(bytes_[position_]-'0');
            if(magnitude>(limit-digit)/10) throw Malformed{};
            magnitude=magnitude*10+digit;
            ++position_;
        }
        if(position_==digits) throw Malformed{};
        const auto value=static_cast<std::int32_t>(negative?-static_cast<std::int64_t>(magnitude):
            static_cast<std::int64_t>(magnitude));
        consumed.push_back({TaiwanNativeTileMasks::Consumption::Kind::Decimal,begin,token,position_,value});
        return value;
    }
    std::size_t count() {
        const auto value=decimal();
        if(value<0 || static_cast<std::size_t>(value)>remaining()) throw Malformed{};
        return static_cast<std::size_t>(value);
    }
    std::vector<TaiwanNativeTileMasks::Consumption> consumed;
private:
    void skip() {while(position_<bytes_.size() && whitespace(bytes_[position_])) ++position_;}
    std::span<const std::uint8_t> bytes_;
    std::size_t position_;
};
}
struct TaiwanNativeTileMasks::Storage {
    const std::vector<std::uint8_t> decoded;
    const std::vector<Model> models;
    const std::vector<Consumption> consumed;
    const std::size_t begin,end;
    Storage(std::vector<std::uint8_t> bytes,std::vector<Model> records,
        std::vector<Consumption> tokens,std::size_t first,std::size_t last):
        decoded(std::move(bytes)),models(std::move(records)),consumed(std::move(tokens)),begin(first),end(last) {}
};
TaiwanNativeTileMasks::TaiwanNativeTileMasks(std::shared_ptr<const Storage> retained):storage_(std::move(retained)) {}
const TaiwanNativeTileMasks::Storage& TaiwanNativeTileMasks::storage() const {
    if(!storage_) throw std::logic_error("TW tile mask library has no retained source");
    return *storage_;
}
std::optional<TaiwanNativeTileMasks> TaiwanNativeTileMasks::read_v16_prefix(
    std::span<const std::uint8_t> decoded,std::size_t start,std::size_t tile_count,std::string_view version) {
    if(version!="v1.6" || decoded.empty() || start>=decoded.size() ||
        tile_count==0 || tile_count>static_cast<std::size_t>(std::numeric_limits<std::int32_t>::max()) ||
        std::find(decoded.begin(),decoded.end(),std::uint8_t(0))!=decoded.end()) return std::nullopt;
    // Full deep copy before any parsing. No alias to caller-owned decoded bytes
    // remains, and parsing/cursor/material all refer to the same original copy.
    std::vector<std::uint8_t> original(decoded.begin(),decoded.end());
    Cursor input(original,start);
    std::vector<Model> models;
    try {
        // VA0044D907/RVA0004D907 section, count and dispatch to0044C980.
        input.expect("ModelDat");
        const auto count=input.count();
        models.reserve(count);
        for(std::size_t index=0;index<count;++index) {
            Model model{};
            model.model=index;
            model.source_begin=input.position();
            // VA0044C9E5..0044CA78 reads precisely three %d %d %d groups.
            for(auto& layer:model.layers) {
                layer={input.decimal(),input.decimal(),input.decimal()};
                if(layer.tile_index < -1 || (layer.tile_index>=0 &&
                    static_cast<std::size_t>(layer.tile_index)>=tile_count)) throw Malformed{};
            }
            // Native dereferences body+8 before frame handling. Missing body is
            // not converted into a guessed mask or a fabricated ROM object.
            if(model.layers[0].tile_index<0) throw Malformed{};
            const auto frames=input.count();
            // VA00441560 initializes ten 0x24 slots. Zero declared frames are
            // recorded, not expanded to unresolved actual ROM frame count.
            if(frames>10) throw Malformed{};
            model.frames.reserve(frames);
            for(std::size_t frame=0;frame<frames;++frame) {
                Frame entry{};
                entry.frame=static_cast<std::uint8_t>(frame);
                entry.anchor_x=input.decimal();entry.anchor_y=input.decimal();
                model.frames.push_back(std::move(entry));
            }
            for(auto& marker:model.declared_markers) marker={input.decimal(),input.decimal()};
            input.expect("Pass"); // VA0044CC43 uses native case-insensitive comparator.
            for(auto& frame:model.frames) {
                frame.source_begin=input.position();
                frame.width=input.decimal();frame.height=input.decimal();
                // Native v1.6 reads both dimensions and runs positive-only
                // loops; zero width/height read no cell tokens. Negative and
                // wrapped allocation domains are deliberately unsupported.
                if(frame.width<0 || frame.height<0) throw Malformed{};
                const auto size=std::uint64_t(frame.width)*std::uint64_t(frame.height);
                if(size>std::numeric_limits<std::int32_t>::max() || size>input.remaining()) throw Malformed{};
                frame.bytes.reserve(static_cast<std::size_t>(size));
                for(std::uint64_t cell=0;cell<size;++cell)
                    // VA0044CD0B reads signed %d;00441798/0044179C store lowBYTE.
                    frame.bytes.push_back(static_cast<std::uint8_t>(input.decimal()));
                frame.source_end=input.position();
            }
            model.source_end=input.position();
            models.push_back(std::move(model));
        }
    } catch(const Malformed&) {return std::nullopt;}
    const auto end=input.position(); // No trailing whitespace or Model token consumed.
    return TaiwanNativeTileMasks(std::make_shared<const Storage>(std::move(original),std::move(models),
        std::move(input.consumed),start,end));
}
std::optional<TaiwanNativeGrid::Mask> TaiwanNativeTileMasks::select(std::size_t model,std::uint32_t selector) const {
    if(!storage_ || model>=storage_->models.size()) return std::nullopt;
    const auto frame=static_cast<std::uint8_t>(selector);
    const auto& frames=storage_->models[model].frames;
    if(frame>=frames.size()) return std::nullopt;
    const auto& selected=frames[frame];
    if(selected.width<=0 || selected.height<=0) return std::nullopt;
    return TaiwanNativeGrid::Mask{selected.frame,selected.width,selected.height,selected.bytes};
}
std::optional<TaiwanNativeGrid::Mask> TaiwanNativeTileMasks::frame_zero(std::size_t model) const {return select(model,0);}
const std::vector<TaiwanNativeTileMasks::Model>& TaiwanNativeTileMasks::models() const {return storage().models;}
const std::vector<std::uint8_t>& TaiwanNativeTileMasks::decoded_bytes() const {return storage().decoded;}
const std::vector<TaiwanNativeTileMasks::Consumption>& TaiwanNativeTileMasks::consumption() const {return storage().consumed;}
std::size_t TaiwanNativeTileMasks::begin_cursor() const {return storage().begin;}
std::size_t TaiwanNativeTileMasks::end_cursor() const {return storage().end;}
}
