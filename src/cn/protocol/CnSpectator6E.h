#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Independent CN 582f native evidence: 004B2010 queues opcode6E plus eight
// body bytes through00481440. It writes mode at0 and nonnegative DWORD at4;
// bytes1..3 remain the original unwritten local-stack bytes. The five retained
// direct-call candidates supply four mode1 contexts and mode2/context0.
// Only004A28DC is proven D0-WORD-derived UI selection. Other contexts are
// native DWORD operands; neither target namespace nor server rights is known.
// S2C6E logical5 is a distinct direction and does not establish an ACK.
struct CnSpectator6E {
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
        Request request{};
        std::copy_n(bytes.begin()+1,8,request.body.begin());
        return request;
    }
    // Observed caller/producer domain only. Opaque bytes1..3 stay unrestricted;
    // this predicate supplies no source identity, phase, currentness or rights.
    static bool observed_producer_shape(const Request& request) noexcept {
        if(request.context()>0x7fffffff)return false;
        return request.mode()==1 || (request.mode()==2 && request.context()==0);
    }
};
}
