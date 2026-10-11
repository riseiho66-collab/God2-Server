#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Actual TW D0 length-table7 -> world case00469DF4 ->00478CC0.
// The callee uses body0 as unsigned slot, ignores body1, and zeroextends
// WORD body2/body4 into two UI target arrays. FFFF stays0000FFFF, never
// FFFFFFFF. Target namespace/issuer and update/reset lifecycle are not proved.
// Native does not check slot1..50; a future server qualification must not be
// described as native rejection of slot0 or51..255. This view cannot emit D0.
struct RecoveredSpectatorTargetsD0 {
    static constexpr std::uint8_t opcode=0xd0;
    static constexpr std::size_t logical_size=7;
    struct Record {
        std::array<std::uint8_t,6> body;
        std::uint8_t slot() const noexcept {return body[0];}
        std::uint8_t opaque() const noexcept {return body[1];}
        std::uint16_t first_target() const noexcept {
            return std::uint16_t(std::uint16_t{body[2]} | (std::uint16_t{body[3]}<<8));
        }
        std::uint16_t second_target() const noexcept {
            return std::uint16_t(std::uint16_t{body[4]} | (std::uint16_t{body[5]}<<8));
        }
        bool operator==(const Record&) const=default;
    };
    static std::optional<Record> read(std::span<const std::uint8_t> logical) noexcept {
        if(logical.size()!=logical_size || logical[0]!=opcode)return std::nullopt;
        Record record;std::copy_n(logical.begin()+1,record.body.size(),record.body.begin());return record;
    }
};
}
