#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current native 97D40 ->97D66 queues 6E plus eight raw bytes. The local
// producer writes body0 mode and body4..7 nonnegative context; body1..3 are
// unwritten stack bytes. Four direct callers pass mode1, one battle caller
// passes mode2/context0. This codec neither admits spectators nor exits battle.
struct RecoveredSpectator6E {
    static constexpr std::uint8_t opcode=0x6e;
    static constexpr std::size_t logical_size=9;
    struct Request {
        std::array<std::uint8_t,8> body{};
        std::uint8_t mode() const noexcept {return body[0];}
        std::uint32_t context() const noexcept {
            return std::uint32_t{body[4]} | (std::uint32_t{body[5]}<<8) |
                   (std::uint32_t{body[6]}<<16) | (std::uint32_t{body[7]}<<24);
        }
        bool operator==(const Request&) const=default;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode)return {};
        Request request{};std::copy_n(bytes.begin()+1,8,request.body.begin());return request;
    }
    static std::array<std::uint8_t,logical_size> encode(const Request& request) noexcept {
        std::array<std::uint8_t,logical_size> bytes{};bytes[0]=opcode;
        std::copy(request.body.begin(),request.body.end(),bytes.begin()+1);return bytes;
    }
    static bool observed_producer_shape(const Request& request) noexcept {
        if(request.context()>0x7fffffff)return false;
        return request.mode()==1 || (request.mode()==2 && request.context()==0);
    }
};
}
