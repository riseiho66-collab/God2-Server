#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <stdexcept>

namespace god2 {
struct RecoveredWorldClock {
    static constexpr std::uint8_t opcode=0x1a;
    static constexpr std::size_t logical_size=4;
    using Bytes=std::array<std::uint8_t,logical_size>;
    struct Fields {
        // Unsigned native input bytes, not normalized clock components.
        std::uint8_t base_hours{},base_minutes{},base_seconds{};
        bool operator==(const Fields&) const = default;
    };
    // RVA 6B022 -> C35F0; native length selector1264 returns exactly four.
    // Writer C360B/C3615/C3623 accepts each complete unsigned BYTE domain.
    static constexpr Bytes encode(std::uint64_t hours,std::uint64_t minutes,std::uint64_t seconds) {
        if(hours>255 || minutes>255 || seconds>255)
            throw std::invalid_argument("World clock field exceeds unsigned byte");
        return {opcode,static_cast<std::uint8_t>(hours),static_cast<std::uint8_t>(minutes),
                       static_cast<std::uint8_t>(seconds)};
    }
    static constexpr Bytes encode(Fields value) noexcept {
        return {opcode,value.base_hours,value.base_minutes,value.base_seconds};
    }
    static constexpr std::optional<Fields> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode) return std::nullopt;
        return Fields{bytes[1],bytes[2],bytes[3]};
    }
    // Native C3634 value written at source+44B0 (character+4540).
    // C35FF separately stores timeGetTime at source+44AC (character+453C).
    // This is only the initial base: elapsed x87 conversion/wrap remains in
    // the actual client, not approximated as an unrestricted server delta.
    static constexpr std::uint32_t native_base_seconds(Fields value) noexcept {
        return 6u*(3600u*value.base_hours+60u*value.base_minutes+value.base_seconds);
    }
    // CUSTOM-0042: shared UTC Unix epoch-zero calendar anchor. The sixfold
    // native clock multiplier is recovered; this anchor is server policy.
    // Four real hours project one game day. No timezone/DST, daily quest,
    // weather, reset, or reward authority is implied. Remainder first avoids
    // signed overflow even at INT64_MIN/MAX; do not multiply epoch by six.
    static constexpr Bytes logical_from_unix_seconds(std::int64_t epoch) noexcept {
        auto phase=epoch%14400;
        if(phase<0) phase+=14400;
        return encode(Fields{static_cast<std::uint8_t>(phase/3600),
            static_cast<std::uint8_t>((phase/60)%60),static_cast<std::uint8_t>(phase%60)});
    }
};
}
