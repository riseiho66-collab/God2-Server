#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Independent CN world0049119F -> complete004A3EC0, native length D07.
// Body0 unsigned slot; body1 unconsumed; body2/body4 WORDs zeroextend into
// two UI DWORD arrays. FFFF is0000FFFF, not theFFFFFFFF initializer sentinel.
// No native slot bound or target-common identity is established by this view.
// CN battle's default consumption is not a new D0 publication consumer.
struct CnSpectatorTargetsD0 {
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
