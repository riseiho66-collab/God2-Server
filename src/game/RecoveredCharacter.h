#pragma once
#include <array>
#include <cstdint>
#include <string>

namespace god2 {
struct RecoveredCharacter {
    std::uint64_t id = 0;
    std::uint64_t account_id = 0;
    std::uint8_t slot = 0;
    std::array<std::uint8_t, 40> profile{};
    std::string created_at;
    std::uint16_t name_codepage=950; // 0 until a newly created character first completes world entry.
    // CUSTOM-0054: 0 normal, 1 YouTube, 2 Facebook, 3 TikTok. Server-owned appearance only.
    std::uint8_t streamer_privilege=0;
};
}
