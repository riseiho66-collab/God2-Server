#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current-native senders queue C2 plus eight raw body bytes. Mode1 comes from
// a separate UI-flag gate; modes2..6 use the F5-populated panel. Several
// branches leave body bytes unwritten. Parsing grants no gameplay operation.
struct RecoveredC2Control {
    static constexpr std::uint8_t opcode=0xc2;
    static constexpr std::size_t logical_size=9;
    struct Request {
        std::array<std::uint8_t,8> body{};
        std::uint16_t mode() const noexcept {
            return static_cast<std::uint16_t>(body[0] | (std::uint16_t{body[1]}<<8));
        }
        std::uint16_t field4() const noexcept {
            return static_cast<std::uint16_t>(body[4] | (std::uint16_t{body[5]}<<8));
        }
        std::uint16_t field6() const noexcept {
            return static_cast<std::uint16_t>(body[6] | (std::uint16_t{body[7]}<<8));
        }
        bool known_mode() const noexcept {return mode()>=1 && mode()<=6;}
        bool operator==(const Request&) const=default;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode)return {};
        Request out{};
        std::copy_n(bytes.begin()+1,out.body.size(),out.body.begin());
        return out;
    }
    static std::array<std::uint8_t,logical_size> encode(const Request& request) noexcept {
        std::array<std::uint8_t,logical_size> bytes{};
        bytes[0]=opcode;
        std::copy(request.body.begin(),request.body.end(),bytes.begin()+1);
        return bytes;
    }
};
}
