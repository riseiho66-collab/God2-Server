#pragma once
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>

namespace god2 {
// Native definition396 +0/+4 contain source columns5/6, not the instance
// packed header. Family is the external EQU2/TEQ26 loader namespace.
// Exact source/instance consistency is admission policy; native59A60 itself
// ignores header highWORD and tooltip treats both families as armor.
struct RecoveredArmorSourceInstance {
    static std::optional<std::uint8_t> family(std::string_view source) noexcept {
        if(source=="EQU")return 2;
        if(source=="TEQ")return 26;
        return {};
    }
    static bool matches(std::uint16_t source_key,std::string_view source_family,
                        std::span<const std::uint8_t> instance) noexcept {
        const auto expected=family(source_family);
        if(!source_key||source_key>=0x7f58u||!expected||instance.size()!=20)return false;
        const auto key=static_cast<std::uint16_t>(instance[0]|(std::uint16_t{instance[1]}<<8));
        return key==source_key && (instance[2]&63u)==*expected;
    }
    // Bits22..31 are deliberately not compared with definition price/cost or
    // cleared. Their admission/transfer semantics require separate authority.
};
}
