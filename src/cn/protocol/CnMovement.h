#pragma once
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
struct CnMovement {
    struct Point {std::uint16_t x;std::uint16_t y;};
    struct Step {
        Point destination;
        std::uint8_t client_ring_index;
        std::uint8_t opaque_stack_byte;
    };
    static std::optional<Step> parse_step(std::span<const std::uint8_t> record) {
        // 005375C0/005395E0 ->00539150 ->004937B0 ->00481600.
        // The producer writes two u16 coordinates and one ring index, then
        // queues6 bytes. Payload5 is uninitialized, not a direction or flag.
        if(record.size()!=7 || record[0]!=0x2e || record[5]>=40)return std::nullopt;
        return Step{{static_cast<std::uint16_t>(record[1]|(std::uint16_t(record[2])<<8)),
                     static_cast<std::uint16_t>(record[3]|(std::uint16_t(record[4])<<8))},
                    record[5],record[6]};
    }
    struct AckConsumer {std::uint8_t debug_value;};
    static std::optional<AckConsumer> read_step_ack(std::span<const std::uint8_t> record) {
        // World case5D stores this byte atclient+231, then attempts a queue
        // pop regardless of this byte.005368F0 advances/decrements only when
        // read!=write; popped low16 coordinates sign-extend. Empty queue leaves
        // caller-initialized(0,0), still passed to00493E70. This is separate
        // from both-axis animation/path completion. Its complete server
        // value contract is unresolved; do not invent an echo serializer.
        if(record.size()!=2 || record[0]!=0x5d)return std::nullopt;
        return AckConsumer{record[1]};
    }
};
}
