#include "cn/assets/CnStandaloneMapAsset.h"
#include "cn/assets/CnAssetTokens.h"
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2cn {
CnStandaloneMapAsset::CnStandaloneMapAsset(std::int32_t w,std::int32_t h,bool palette,
    std::vector<std::uint8_t> cells):width_(w),height_(h),palnum_(palette),cells_(std::move(cells)) {}
CnStandaloneMapAsset CnStandaloneMapAsset::from_text(std::span<const std::uint8_t> bytes,
    std::size_t budget) {
    if(bytes.size()>budget)throw std::length_error("CN standalone MAP exceeds input budget");
    detail::CnAssetTokens input(bytes);
    if(input.next()!="MAP")throw std::invalid_argument("CN standalone MAP signature unavailable");
    const auto version=input.next();
    // Native compares versions lexically; later/other formats are not assumed
    // equivalent merely because their string compares above v1.0/v1.1.
    if(version!="v1.0" && version!="v1.1")
        throw std::invalid_argument("CN standalone MAP version not recovered");
    input.expect("MAPSIZE");
    const auto width=input.integer(),height=input.integer();
    if(width<=0 || height<=0)throw std::invalid_argument("CN standalone MAP dimensions unavailable");
    const auto count=std::uint64_t(width)*height;
    if(count>std::numeric_limits<std::int32_t>::max()/8 || count>budget/8 || count>input.remaining())
        throw std::length_error("CN standalone MAP cell extent unavailable");
    //00466EE0 ->0076C3BF ->__calloc_base explicitly initializes all eight
    // bytes. This is recovered allocation, never a missing-cell substitute.
    std::vector<std::uint8_t> cells(static_cast<std::size_t>(count)*8,0);
    const auto word=[&](std::size_t offset) {
        for(std::size_t i=0;i<count;++i) {
            const auto value=static_cast<std::uint16_t>(input.integer());
            cells[i*8+offset]=static_cast<std::uint8_t>(value);
            cells[i*8+offset+1]=static_cast<std::uint8_t>(value>>8);
        }
    };
    input.expect("TileNum");word(4);
    input.expect("SpriteNum");
    for(std::size_t i=0;i<count;++i)
        cells[i*8+7]=static_cast<std::uint8_t>(input.integer())&0x0f;
    input.expect("TileIdx");word(0);
    input.expect("Pass");
    for(std::size_t i=0;i<count;++i) {
        const auto value=static_cast<std::uint8_t>(input.integer());
        auto& flags=cells[i*8+7];
        // Store low2 source bits at4..5, then duplicate bit4 to bit6.
        flags=static_cast<std::uint8_t>((flags&~0x30u)|((value<<4)&0x30u));
        flags=static_cast<std::uint8_t>((flags&~0x40u)|((flags<<2)&0x40u));
    }
    input.expect("LinkIdx");word(2);
    const bool palette=version=="v1.1";
    if(palette) {
        input.expect("PalNum");
        for(std::size_t i=0;i<count;++i)
            cells[i*8+6]=static_cast<std::uint8_t>(input.integer())&0x1f;
    }
    // Native closes after its last required section; trailing text is ignored.
    // Every required numeric token must be present; failed scanf/uninitialized
    // stack behavior is an unresolved malformed variant, never default data.
    return {width,height,palette,std::move(cells)};
}
}
