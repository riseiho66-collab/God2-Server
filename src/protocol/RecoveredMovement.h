#pragma once
#include "protocol/RecoveredWorldFrame.h"
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <utility>
#include <vector>

namespace god2 {
struct RecoveredMovement {
    struct Request {
        std::uint16_t x,y;
        std::uint8_t sequence,opaque_tail;
    };
    using Frame=std::array<std::uint8_t,10>;
    using AckFrame=std::array<std::uint8_t,5>;
    static constexpr std::size_t max_logical_size=RecoveredWorldFrame::max_logical_size;
    struct WorldBatch {
        std::vector<Request> movements;
        std::size_t ticks=0;
    };

    // original15790 queues opcode 0x2e and six body bytes. The final body
    // byte is an uninitialized stack tail, not padding or a mount state.
    // Coordinate and ring-index policy are external; preserve every sequence byte.
    static std::optional<std::vector<Request>> parse_batch(std::span<const std::uint8_t> wire) {
        auto batch=parse_world_batch(wire);
        if(!batch || batch->ticks!=0) return std::nullopt;
        return std::move(batch->movements);
    }

    // Current 11750 queues 30 00 before flushing the same queue as movement.
    // Accept only that exact sideband; it neither advances the movement ring
    // nor proves a corresponding server reply or gameplay mutation.
    static std::optional<WorldBatch> parse_world_batch(std::span<const std::uint8_t> wire) {
        const auto logical=RecoveredWorldFrame::decode(wire);
        if(!logical) return std::nullopt;
        const auto& decoded=*logical;
        const auto logical_size=decoded.size();
        WorldBatch result;
        for(std::size_t i=0;i<logical_size;) {
            if(decoded[i]==0x30) {
                if(logical_size-i<2 || decoded[i+1]!=0) return std::nullopt;
                ++result.ticks;
                i+=2;
            } else if(decoded[i]==0x2e) {
                if(logical_size-i<7) return std::nullopt;
                result.movements.push_back(Request{
                    static_cast<std::uint16_t>(decoded[i+1]+256u*decoded[i+2]),
                    static_cast<std::uint16_t>(decoded[i+3]+256u*decoded[i+4]),
                    decoded[i+5],decoded[i+6]});
                i+=7;
            } else return std::nullopt;
        }
        return result;
    }

    // Exact one-record convenience API; stream framing belongs to the caller.
    static std::optional<Request> parse(std::span<const std::uint8_t> wire) {
        if(wire.size()!=10) return std::nullopt;
        const auto requests=parse_batch(wire);
        if(!requests) return std::nullopt;
        return requests->front();
    }

    // Diagnostic fixture encoder only, not a production client movement builder.
    // Callers supply the opaque byte explicitly; never read uninitialized storage.
    static Frame encode(const Request& request) noexcept {
        return seal(Frame{10,0,0x2e,
            static_cast<std::uint8_t>(request.x),static_cast<std::uint8_t>(request.x>>8),
            static_cast<std::uint8_t>(request.y),static_cast<std::uint8_t>(request.y>>8),
            request.sequence,request.opaque_tail,0});
    }

    // Diagnostic fixture only: echo is a historical CUSTOM server policy.
    // Native5D stores an arbitrary BYTE, then pops the front pending point;
    // client write-cursor provenance does not prove original server echo.
    static AckFrame ack(std::uint8_t sequence) noexcept {
        return seal(AckFrame{5,0,0x5d,sequence,0});
    }
private:
    template<std::size_t N>
    static std::array<std::uint8_t,N> seal(std::array<std::uint8_t,N> frame) noexcept {
        std::uint8_t checksum=0;
        for(std::size_t i=0;i+1<N;++i)
            checksum=static_cast<std::uint8_t>(checksum+frame[i]+0x3c);
        frame.back()=checksum;
        std::uint8_t previous=0;
        for(std::size_t i=2;i<N;++i) {
            const auto plain=frame[i];
            frame[i]=static_cast<std::uint8_t>((plain^recovered_zero_seed_key[i-2])+previous-3);
            previous=plain;
        }
        return frame;
    }
};
}
