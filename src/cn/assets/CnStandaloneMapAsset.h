#pragma once
#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

namespace god2cn {
//004657E0 text MAP reader. Independent plain .map input, not MBD/MBDZ.
// Full native eight-byte cells, including Pass bit6 used by0046F630.
class CnStandaloneMapAsset {
public:
    static CnStandaloneMapAsset from_text(std::span<const std::uint8_t>,std::size_t max_bytes);
    std::int32_t width() const noexcept {return width_;}
    std::int32_t height() const noexcept {return height_;}
    bool has_palnum() const noexcept {return palnum_;}
    std::span<const std::uint8_t> cells() const noexcept {return cells_;}
private:
    CnStandaloneMapAsset(std::int32_t,std::int32_t,bool,std::vector<std::uint8_t>);
    std::int32_t width_,height_;
    bool palnum_;
    std::vector<std::uint8_t> cells_;
};
}
