#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>
namespace god2 {
// Current mapped image149c1b45: producer972F0/8FAF0 queues opcode6B and
// THREE payload bytes copied in reverse formal-argument order. Native call
// sites observed here supply lane0..4; other raw lanes remain structural,
// never gameplay-authorized by this codec. This is C2S; S2C6B is21 bytes and
// enters the world/NPC pool at6AABE. No food gain, cost, pet ownership or
// S2C reply follows from the shared opcode or these producer arguments.
struct RecoveredCompanionControl6B {
    static constexpr std::uint8_t opcode=0x6b;
    static constexpr std::size_t logical_size=4;
    struct Request {
        // lane0: inventory_slot is the dragged item; selector is the live
        // panel byte from UI+85ABD, not necessarily the selected beast's
        // physical custody slot in the current server's CUSTOM-0085 model.
        std::uint8_t inventory_slot,selector,lane;
        bool operator==(const Request&)const=default;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> raw)noexcept{
        if(raw.size()!=logical_size||raw[0]!=opcode)return {};
        return Request{raw[1],raw[2],raw[3]};
    }
    static std::array<std::uint8_t,logical_size> encode(const Request& r)noexcept{
        return {opcode,r.inventory_slot,r.selector,r.lane};
    }
};
}
