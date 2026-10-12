#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// TW149c selected PetEgg action4D6940 ->4D6BA0 ->4132E0.
// B1 logical2 carries a selector only, never slot/key/full20 instance.
// This selected native action's0..6/9 are distinct from options7/8.
// No original server operation, E5/E6 reply pairing or mutation is inferred.
struct RecoveredPetEggControl {
    static constexpr std::uint8_t opcode=0xb1;
    static constexpr std::size_t logical_size=2;
    static constexpr bool runtime_emission_enabled=false, runtime_mutation_enabled=false;
    struct Request {
        std::uint8_t selector_raw;
        bool operator==(const Request&) const = default;
    };
    // Scope is the recovered PetEgg action, not every caller of the generic
    // BYTE producer. Other B1 variants remain separate recovery tasks.
    static constexpr bool qualified_selector(std::uint8_t selector) noexcept {
        return selector<=6 || selector==9;
    }
    static std::optional<Request> decode(std::span<const std::uint8_t> logical) noexcept {
        if(logical.size()!=logical_size || logical[0]!=opcode ||
           !qualified_selector(logical[1]))return {};
        return Request{logical[1]};
    }
    static std::array<std::uint8_t,logical_size> encode(Request request) noexcept {
        return {opcode,request.selector_raw};
    }
};
}
