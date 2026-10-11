#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// CN582f modal3B -> 004ADB8D/004B0720 -> opcode25/body4.
// Particular saved-item caller zeroextends its WORD, making its fourth body
// byte zero. The producer does not separately initialize that byte: preserve
// every received tail; do not impose a global zero-padding contract.
struct CnSkillBookUse25 {
    static constexpr std::uint8_t opcode=0x25;
    static constexpr std::size_t logical_size=5;
    using ControlRequest=std::array<std::uint8_t,2>;
    class Request {
    public:
        std::span<const std::uint8_t> logical_bytes() const noexcept {return bytes_;}
        std::uint16_t item() const noexcept {return std::uint16_t(bytes_[1])|(std::uint16_t(bytes_[2])<<8);}
        std::uint8_t slot() const noexcept {return bytes_[3];}
        std::uint8_t opaque_tail() const noexcept {return bytes_[4];}
        bool operator==(const Request&) const=default;
    private:
        friend struct CnSkillBookUse25;
        explicit Request(std::array<std::uint8_t,logical_size> bytes):bytes_(bytes){}
        std::array<std::uint8_t,logical_size> bytes_;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode)return {};
        std::array<std::uint8_t,logical_size> owned;
        std::copy(bytes.begin(),bytes.end(),owned.begin());return Request(owned);
    }
    // Separate ready-world control from 004ADB98 -> 004B1B40(1F,0).
    // Conditional even if the preceding25 producer suppressed its send.
    // Not a learned acknowledgement or initial/bootstrap1F.
    static std::optional<ControlRequest> read_control1f(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=2 || bytes[0]!=0x1f || bytes[1]!=0)return {};
        return ControlRequest{bytes[0],bytes[1]};
    }
};
}
