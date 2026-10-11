#pragma once
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace god2 {
// Current-native WORLD FD -> 858B0 subtype12 -> 85BBE. This is the
// presentation state upstream of C2S E4 UI gates, not a proven E4 response.
// Only the minimum consumed prefix is known; preserve every trailing byte.
struct RecoveredFDE4Panel {
    static constexpr std::uint8_t opcode=0xfd,subtype=12;
    static constexpr std::size_t minimum_logical_size=26;
    static constexpr bool runtime_emission_enabled=false;
    struct Record {
        std::vector<std::uint8_t> logical;
        std::span<const std::uint8_t,18> displayed_prefix() const noexcept {
            return std::span<const std::uint8_t>(logical).subspan<4,18>();
        }
        // 956B0 reads UI+26108+2*index and resolves this WORD through
        // the native item-definition lookup 459A60. No award is implied.
        std::optional<std::uint16_t> displayed_item_key(std::size_t index) const noexcept {
            if(index>=9)return std::nullopt;
            const auto offset=4+2*index;
            return std::uint16_t(logical[offset])|
                   (std::uint16_t(logical[offset+1])<<8);
        }
        std::uint8_t presentation_mode_raw() const noexcept {return logical[22];}
        std::uint8_t option_mask_raw() const noexcept {return logical[23];}
        std::uint8_t operation1_button_raw() const noexcept {return logical[24];}
        std::uint8_t operation2_button_raw() const noexcept {return logical[25];}
        bool option_flags_refreshed() const noexcept {return presentation_mode_raw()!=0;}
        bool incoming_offer_has_any_option() const noexcept {
            return option_flags_refreshed() && option_mask_raw()!=0;
        }
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) {
        if(bytes.size()<minimum_logical_size || bytes.size()>0xffff ||
           bytes[0]!=opcode || bytes[3]!=subtype ||
           (std::size_t{bytes[1]}|(std::size_t{bytes[2]}<<8))!=bytes.size())return std::nullopt;
        return Record{std::vector<std::uint8_t>(bytes.begin(),bytes.end())};
    }
};
}
