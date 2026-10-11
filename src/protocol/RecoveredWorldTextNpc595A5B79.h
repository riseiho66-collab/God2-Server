#pragma once
#include <array>
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// WORLD S2C 59/5B -> 4C81A0, 5A -> 4CCD10, 79 chooses by logical+5 WORD.
// Read-only native receive shape. Server producer/causal request is unknown.
struct RecoveredWorldTextNpc595A5B79 {
    static constexpr std::size_t logical_size=9;
    static constexpr bool runtime_emission_enabled=false;
    enum class Effect {TextResource,NpcPoolLabel};
    struct Record {
        std::array<std::uint8_t,logical_size> logical;
        std::uint8_t opcode() const noexcept {return logical[0];}
        std::uint16_t resource_selector_raw() const noexcept {return word(7);}
        std::optional<std::uint16_t> npc_normal_message_id() const noexcept {
            if(effect()!=Effect::TextResource)return {};
            return resource_selector_raw();
        }
        std::optional<std::uint16_t> npc_boss_message_id() const noexcept {
            if(effect()!=Effect::NpcPoolLabel)return {};
            return resource_selector_raw();
        }
        std::uint16_t mode_word_raw() const noexcept {return word(5);}
        Effect effect() const noexcept {
            return opcode()==0x5a || (opcode()==0x79 && mode_word_raw()==0xffff)
                ? Effect::NpcPoolLabel : Effect::TextResource;
        }
        // Used only for a TextResource effect.
        std::uint16_t text_argument_raw() const noexcept {return word(1);}
        // Used only for an NpcPoolLabel effect; exact four-byte identity.
        std::uint32_t npc_pool_identity_raw() const noexcept {
            return std::uint32_t(logical[1])|
                   (std::uint32_t(logical[2])<<8)|
                   (std::uint32_t(logical[3])<<16)|
                   (std::uint32_t(logical[4])<<24);
        }
    private:
        std::uint16_t word(std::size_t at) const noexcept {
            return std::uint16_t(logical[at])|(
                std::uint16_t(logical[at+1])<<8);
        }
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size ||
           (bytes[0]!=0x59 && bytes[0]!=0x5a && bytes[0]!=0x5b && bytes[0]!=0x79))return {};
        Record record{};
        std::copy(bytes.begin(),bytes.end(),record.logical.begin());
        return record;
    }
};
}
