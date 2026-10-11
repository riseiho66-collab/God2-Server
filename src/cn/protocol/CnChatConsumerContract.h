#pragma once
#include <cstddef>
#include <cstdint>
#include <optional>

namespace god2cn {
// Pinned CN0049A020 ->004A7270 local destination [ebp-104,ebp-4),
// size100 hex, cleared then appended WITHOUT a length check. This bound
// includes the native client prefix and terminator, not just transport length.
// A capacity bound is not a recovered server chat rule or complete sink proof.
struct CnChatConsumerContract {
    static constexpr std::size_t display_buffer_bytes=256;
    static constexpr std::size_t channel_prefix_bytes=3; //00899978 slots: "1Ax\0".
    static constexpr std::size_t channel18_prefix_bytes=8; //007F2CF8 CP936 literal.
    static std::optional<std::size_t> world_plain_text_budget(std::uint8_t channel) {
        switch(channel) {
        case 0:case 1:case 2:case 3:case 5:case 6:case 8:case 9:
            return display_buffer_bytes-channel_prefix_bytes-1;
        case 13:return display_buffer_bytes-1; // Cleared buffer; no label prefix.
        case 18:return display_buffer_bytes-channel18_prefix_bytes-1;
        // Template10/11/16, timestamp12, globals14/15 and defaults require
        // their own actual formatter/destination contract. Never treat the
        // transport's2545 text budget as their native storage capacity.
        default:return std::nullopt;
        }
    }
};
}
