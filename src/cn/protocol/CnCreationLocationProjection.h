#pragma once
#include <array>
#include <cstdint>
#include <optional>

namespace god2cn {
// 00445B40, pinned CN PE word at008865CC+48*(choice-1), and ProgramMsg
// IDs00886578..0088659B. Native field projection, NOT destination availability,
// common map IDs, spawn coordinates or permission. No TW profile conversion.
class CnCreationLocationProjection {
public:
    struct Reference {
        std::uint8_t one_based_choice;
        std::uint16_t program_message_id,packed_word;
        std::uint8_t endpoint_routing_key,scene_selector;
        std::uint16_t location_index;
    };
    static std::optional<Reference> from_choice(std::uint8_t choice) noexcept {
        if(!choice || choice>words_.size())return std::nullopt;
        const auto word=words_[choice-1];
        return Reference{choice,static_cast<std::uint16_t>(301+choice-1),word,
            static_cast<std::uint8_t>(word&15),static_cast<std::uint8_t>((word>>4)&3),
            static_cast<std::uint16_t>(word>>6)};
    }
private:
    // Complete18 retained table words; repeated packed values do not imply
    // identical permissions or merge different native choices.
    inline static constexpr std::array<std::uint16_t,18> words_={
        0x0041,0x0e81,0x0045,0x0086,0x1242,0x0442,0x0482,0x0902,0x1582,
        0x0004,0x0004,0x0004,0x0004,0x0004,0x0003,0x0003,0x0003,0x0003};
};
}
