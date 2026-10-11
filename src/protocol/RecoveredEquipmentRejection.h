#pragma once
#include <array>
#include <cstdint>
#include <stdexcept>
namespace god2 {
// Current S2C02: native length23,484E00/484AE0 SystemMessage27(mode1).
// Generic inability to equip/use; no success acknowledgement or pending clear.
struct RecoveredEquipmentRejection {
    using Bytes=std::array<std::uint8_t,23>;
    static constexpr Bytes logical(std::uint64_t owned_item) {
        if(!owned_item || owned_item>0xffff)throw std::invalid_argument("Equipment rejection needs owned item WORD");
        // Name16, variant and opaque default0 are a verified bounded fixture
        // choice; they are not quantities or server-owned state mutations.
        return {0x02,27,0,static_cast<std::uint8_t>(owned_item),static_cast<std::uint8_t>(owned_item>>8)};
    }
};
}
