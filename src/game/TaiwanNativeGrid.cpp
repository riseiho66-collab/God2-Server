#include "game/TaiwanNativeGrid.h"
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2 {
namespace {
std::optional<std::int32_t> narrow(std::int64_t value) {
    if(value<std::numeric_limits<std::int32_t>::min() ||
        value>std::numeric_limits<std::int32_t>::max()) return std::nullopt;
    return static_cast<std::int32_t>(value);
}
std::optional<std::int32_t> half(std::int32_t value) {
    // CDQ; SUB EAX,EDX; SAR EAX,1, preserving each nonwrapped intermediate.
    const auto adjusted=narrow(std::int64_t(value)+(value<0?1:0));
    if(!adjusted) return std::nullopt;
    return value/2;
}
}
struct TaiwanNativeGrid::Storage {
    const Material material;
    const std::int32_t side;
    const Placement placement;
    const std::vector<std::uint8_t> cells;
    Storage(Material retained,std::int32_t dimension,Placement origin,std::vector<std::uint8_t> matrix):
        material(std::move(retained)),side(dimension),placement(origin),cells(std::move(matrix)) {}
};
TaiwanNativeGrid::TaiwanNativeGrid(Material material,std::int32_t side,Placement placement,
    std::vector<std::uint8_t> cells):storage_(std::make_shared<const Storage>(
        std::move(material),side,placement,std::move(cells))) {}
bool TaiwanNativeGrid::full(const Mask& mask) noexcept {
    if(mask.width<=0 || mask.height<=0) return false;
    const auto count=std::uint64_t(mask.width)*std::uint64_t(mask.height);
    return count<=std::numeric_limits<std::uint32_t>::max() && count==mask.bytes.size();
}
std::uint8_t TaiwanNativeGrid::sample(const Mask& mask,std::int32_t x,std::int32_t y) noexcept {
    // VA004416B0 / RVA000416B0: a complete known mask has native AL1 outside
    // its signed dimensions. This is getter fallback, never movement permission.
    if(x<0 || y<0 || x>=mask.width || y>=mask.height) return 1;
    return mask.bytes[static_cast<std::size_t>(std::uint64_t(y)*std::uint64_t(mask.width)+
        std::uint64_t(x))];
}
std::optional<TaiwanNativeGrid::Point> TaiwanNativeGrid::native_to_pixels(
    std::int32_t x,std::int32_t y,std::int32_t width) {
    // 49B30 takes x,y,outX,outY,width; the caller also pushes a sixth unused
    // height. 41FC0 merely writes the resulting initialization fields.
    const auto sum=narrow(std::int64_t(x)+y);
    if(!sum) return std::nullopt;
    const auto five=narrow(std::int64_t(*sum)*5);
    if(!five) return std::nullopt;
    const auto pixel_x=narrow(std::int64_t(*five)*8);
    const auto next=narrow(std::int64_t(width)+1);
    if(!pixel_x || !next) return std::nullopt;
    const auto rounded=half(*next);
    if(!rounded) return std::nullopt;
    const auto doubled=narrow(std::int64_t(*rounded)*2);
    if(!doubled) return std::nullopt;
    const auto minus_x=narrow(std::int64_t(*doubled)-x);
    if(!minus_x) return std::nullopt;
    const auto shifted=narrow(std::int64_t(*minus_x)+y-2);
    if(!shifted) return std::nullopt;
    const auto five_y=narrow(std::int64_t(*shifted)*5);
    if(!five_y) return std::nullopt;
    const auto pixel_y=narrow(std::int64_t(*five_y)*4);
    if(!pixel_y) return std::nullopt;
    return Point{*pixel_x,*pixel_y};
}
std::optional<TaiwanNativeGrid::Point> TaiwanNativeGrid::native_to_grid(
    std::int32_t x,std::int32_t y) {
    const auto lower=half(y);
    const auto next=narrow(std::int64_t(y)+1);
    if(!lower || !next) return std::nullopt;
    const auto upper=half(*next);
    if(!upper) return std::nullopt;
    const auto out_x=narrow(std::int64_t(x)-*lower);
    const auto out_y=narrow(std::int64_t(x)+*upper);
    if(!out_x || !out_y) return std::nullopt;
    return Point{*out_x,*out_y};
}
std::optional<TaiwanNativeGrid> TaiwanNativeGrid::compose(Material input) {
    // Copy even when the caller moved vectors: pre-existing aliases to those
    // vector elements must not be aliases to the retained immutable snapshot.
    Material material=input;
    // Existing171 initializer VA00436C30 / RVA00036C30 is context. Its frame0
    // extent determines the loops; selected frame determines the actual sample.
    if(material.frame_zero.frame!=0 || !full(material.frame_zero) ||
        !full(material.selected_base) || material.selected_base.frame!=
            static_cast<std::uint8_t>(material.actual_base_selector)) return std::nullopt;
    if(material.selected_base.frame==0 &&
        (material.selected_base.width!=material.frame_zero.width ||
         material.selected_base.height!=material.frame_zero.height ||
         material.selected_base.bytes!=material.frame_zero.bytes)) return std::nullopt;
    for(const auto& overlay:material.actual_ordered_overlays)
        if(!full(overlay.selected) || overlay.selected.frame!=
            static_cast<std::uint8_t>(overlay.actual_selector)) return std::nullopt;
    const auto width=material.frame_zero.width,height=material.frame_zero.height;
    const auto ceiling=height/2+(height&1);
    const auto side=narrow(std::int64_t(std::max(width,ceiling))*2+1);
    if(!side) return std::nullopt;
    const auto count=std::uint64_t(*side)*std::uint64_t(*side);
    if(count>std::numeric_limits<std::uint32_t>::max() ||
        count>std::numeric_limits<std::size_t>::max()) return std::nullopt;
    const auto origin=narrow(std::int64_t(width&1)-width+*side-1);
    if(!origin) return std::nullopt;
    const auto pixels=native_to_pixels(*origin,0,*side);
    if(!pixels) return std::nullopt;
    // Full native cleared matrix, including cells never reached by either loop.
    std::vector<std::uint8_t> cells(static_cast<std::size_t>(count),0);
    for(std::int32_t row=0;row<height;++row) {
        const auto down=row/2,up=row/2+(row&1);
        for(std::int32_t col=0;col<width;++col) {
            const auto gx=narrow(std::int64_t(*origin)-down+col);
            const auto gy=narrow(std::int64_t(up)+col);
            if(!gx || !gy) return std::nullopt;
            // Native assert at36D8F followed by continue36DA6; no raw sample.
            if(*gx<0 || *gy<0 || *gx>=*side || *gy>=*side) continue;
            const auto offset=std::uint64_t(*gy)*std::uint64_t(*side)+std::uint64_t(*gx);
            cells[static_cast<std::size_t>(offset)]=sample(material.selected_base,col,row);
        }
    }
    for(const auto& overlay:material.actual_ordered_overlays) {
        const auto local=native_to_grid(overlay.actual_x,overlay.actual_y);
        if(!local) return std::nullopt;
        const auto ox=narrow(std::int64_t(local->x)+*origin);
        if(!ox) return std::nullopt;
        for(std::int32_t row=0;row<overlay.selected.height;++row) {
            const auto down=row/2,up=row/2+(row&1);
            const auto row_x=narrow(std::int64_t(*ox)-down);
            const auto row_y=narrow(std::int64_t(local->y)+up);
            if(!row_x || !row_y) return std::nullopt;
            for(std::int32_t col=0;col<overlay.selected.width;++col) {
                const auto gx=narrow(std::int64_t(*row_x)+col);
                const auto gy=narrow(std::int64_t(*row_y)+col);
                if(!gx || !gy) return std::nullopt;
                // Native assert at36EC7 then continue36EDE preserves cleared/base.
                if(*gx<0 || *gy<0 || *gx>=*side || *gy>=*side) continue;
                if(sample(overlay.selected,col,row)!=0) continue;
                const auto offset=std::uint64_t(*gy)*std::uint64_t(*side)+std::uint64_t(*gx);
                cells[static_cast<std::size_t>(offset)]=0;
            }
        }
    }
    return TaiwanNativeGrid(std::move(material),*side,Placement{*origin,*pixels},std::move(cells));
}
bool TaiwanNativeGrid::complete() const noexcept {
    return storage_ && storage_->side>0 &&
        std::uint64_t(storage_->side)*std::uint64_t(storage_->side)==storage_->cells.size();
}
std::optional<std::uint8_t> TaiwanNativeGrid::read(std::int32_t x,std::int32_t y) const noexcept {
    if(!complete() || x<0 || y<0 || x>=storage_->side || y>=storage_->side) return std::nullopt;
    return storage_->cells[static_cast<std::size_t>(std::uint64_t(y)*
        std::uint64_t(storage_->side)+std::uint64_t(x))];
}
const TaiwanNativeGrid::Storage& TaiwanNativeGrid::storage() const {
    if(!storage_) throw std::logic_error("TW native grid handle has no retained material");
    return *storage_;
}
std::int32_t TaiwanNativeGrid::side() const {return storage().side;}
const std::vector<std::uint8_t>& TaiwanNativeGrid::bytes() const {return storage().cells;}
const TaiwanNativeGrid::Material& TaiwanNativeGrid::material() const {return storage().material;}
const TaiwanNativeGrid::Placement& TaiwanNativeGrid::placement() const {return storage().placement;}
}
