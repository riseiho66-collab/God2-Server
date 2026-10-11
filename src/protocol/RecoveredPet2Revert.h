#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current mapped-image A5741/A578B -> A57FF -> 132E0. This is the
// second-generation pet panel's revert request, not a received FB snapshot.
// Current gamedata MIS02 keys400F/4010 describe talent/category revert stones.
// The texts do not establish consumption, historical values or reply opcodes.
struct RecoveredPet2Revert {
    static constexpr std::uint8_t opcode=0xd6;
    static constexpr std::size_t logical_size=4;
    struct Request {
        std::uint8_t item_slot,pet_slot,option;
        bool operator==(const Request&) const = default;
    };
    // Preserve all three bytes structurally. On inventory miss the original
    // producer queues event_flags' low byte (20/60), not a valid bag slot.
    // Authorization must reject that case separately; never clamp it to slot0.
    static std::optional<Request> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode) return std::nullopt;
        return Request{bytes[1],bytes[2],bytes[3]};
    }
    static std::array<std::uint8_t,logical_size> encode(Request request) noexcept {
        return {opcode,request.item_slot,request.pet_slot,request.option};
    }
    static std::optional<std::uint16_t> required_item_key(std::uint8_t option) noexcept {
        if(option>=1 && option<=3) return std::uint16_t{0x400f};
        if(option==4) return std::uint16_t{0x4010};
        return std::nullopt;
    }
    static bool has_qualified_operands(Request request) noexcept {
        return request.item_slot<30 && request.pet_slot>=42 && request.pet_slot<=44 &&
            required_item_key(request.option).has_value();
    }
};
}
