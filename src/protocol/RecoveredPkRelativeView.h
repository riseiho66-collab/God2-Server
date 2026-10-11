#pragma once
#include <array>
#include <cstdint>
#include <stdexcept>
namespace god2 {
// CUSTOM-0086 viewer projection of the native 2*14 positions. Canonical side
// remains server-owned; each viewer's own side is0 in their client records.
struct RecoveredPkRelativeView {
    static std::uint8_t position(std::uint8_t canonical,std::uint8_t viewer){
        if(canonical>=28||viewer>1)throw std::invalid_argument("Invalid PK relative position/viewer");
        return static_cast<std::uint8_t>((canonical+14u*viewer)%28u);
    }
    // This involution serves both C2S view->canonical and S2C canonical->view.
    static std::array<std::uint16_t,2> masks(std::array<std::uint16_t,2> input,std::uint8_t viewer){
        if(viewer>1||((input[0]|input[1])&0xc000))throw std::invalid_argument("Invalid PK relative masks/viewer");
        return viewer==0?input:std::array<std::uint16_t,2>{input[1],input[0]};
    }
};
}
