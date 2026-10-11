#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <stdexcept>

namespace god2 {
// Current PE SHA6bf75ef8...: size selector RVA1252 returns15; dispatcher
// RVA69369 -> local RVA103D30 or remote RVAFC990/RVA69523. See
// docs/research/current-weapon-appearance-20260926.md (49 bounded native cases).
// Wire projection only: no item-to-HeroDoll mapping, ownership, spawn, stat,
// transform eligibility, or complete renderer acceptance is implied.
struct RecoveredPlayerAppearanceUpdate {
    static constexpr std::uint8_t opcode=0xda;
    static constexpr std::size_t logical_size=15;
    using Bytes=std::array<std::uint8_t,logical_size>;
    using Components=std::array<std::uint8_t,8>;
    struct Fields {
        // Native compares the complete actor WORD. Do not apply a3FFF mask.
        std::uint16_t actor_identity{},transform_key{};
        // Semantic names are unproven; these occupy logical offsets5 and6.
        std::uint8_t raw_scalar5{},raw_scalar6{};
        // Four packed two-byte components, including all variant bits.
        // Preserve all eight bytes, not just the weapon-position component.
        Components components{};
        bool operator==(const Fields&) const = default;
    };
    static constexpr Bytes encode(const Fields& value) noexcept {
        Bytes bytes{opcode,static_cast<std::uint8_t>(value.actor_identity),
            static_cast<std::uint8_t>(value.actor_identity>>8),
            static_cast<std::uint8_t>(value.transform_key),
            static_cast<std::uint8_t>(value.transform_key>>8),value.raw_scalar5,value.raw_scalar6};
        for(std::size_t i=0;i<value.components.size();++i)bytes[7+i]=value.components[i];
        return bytes;
    }
    // Accept wide caller values before narrowing. Nonzero transform keys are
    // preserved, not certified as resource-backed or safe to emit at runtime.
    static constexpr Bytes encode(std::uint64_t actor,std::uint64_t transform,
        std::uint64_t scalar5,std::uint64_t scalar6,std::span<const std::uint8_t> components) {
        if(actor>0xffff || transform>0xffff || scalar5>0xff || scalar6>0xff || components.size()!=8)
            throw std::invalid_argument("Player appearance field width rejected");
        Fields value{static_cast<std::uint16_t>(actor),static_cast<std::uint16_t>(transform),
            static_cast<std::uint8_t>(scalar5),static_cast<std::uint8_t>(scalar6),{}};
        for(std::size_t i=0;i<value.components.size();++i)value.components[i]=components[i];
        return encode(value);
    }
    static constexpr std::optional<Fields> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode)return std::nullopt;
        Fields value{static_cast<std::uint16_t>(bytes[1]|(std::uint16_t{bytes[2]}<<8)),
            static_cast<std::uint16_t>(bytes[3]|(std::uint16_t{bytes[4]}<<8)),bytes[5],bytes[6],{}};
        for(std::size_t i=0;i<value.components.size();++i)value.components[i]=bytes[7+i];
        return value;
    }
};
}
