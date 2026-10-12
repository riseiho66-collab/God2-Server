#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
namespace god2 {
// Current TW 4D6BA0 emits B1 + lowBYTE of its argument. Only actual
// 4F4F7B/4F4F9B selectors7/8 are qualified here; they set/clear449C bit0200.
// PetEgg action4D6940 uses the same producer for0..6/9; those variants are
// described separately by RecoveredPetEggControl and are not preferences.
// S1B is independently logical3 (4012DC), bodyWORD copied to449C (4F5041).
// The consumer's additional local449E BYTE is NOT part of this wire record.
struct TaiwanNativeClientOptions final {
    struct Control {std::uint8_t selector;};
    static constexpr std::uint8_t control_opcode=0xb1;
    static constexpr std::size_t control_size=2;
    static std::optional<Control> decode(std::span<const std::uint8_t> logical) {
        if(logical.size()!=control_size || logical[0]!=control_opcode ||
           (logical[1]!=7 && logical[1]!=8))return {};
        return Control{logical[1]};
    }
    static std::array<std::uint8_t,3> synchronize(std::uint16_t word) {
        return {0x1b,static_cast<std::uint8_t>(word),static_cast<std::uint8_t>(word>>8)};
    }
};
}
