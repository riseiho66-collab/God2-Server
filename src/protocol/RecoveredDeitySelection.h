#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current 004962E0 -> 004132E0. 004A8690 and 004A8AA0 select an
// existing row's key; this is not proof of summon/recall or ownership.
struct RecoveredDeitySelection {
    static constexpr std::uint8_t opcode=0x67;
    static constexpr std::size_t logical_size=2;
    struct Request {
        std::uint8_t key;
        bool operator==(const Request&) const = default;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode) return std::nullopt;
        return Request{bytes[1]};
    }
    static std::array<std::uint8_t,logical_size> encode(Request request) noexcept {
        return {opcode,request.key};
    }
};
}
