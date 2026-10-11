#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current mapped client image: four guarded calls to 961A0(68,1) in
// C3750..C39C3 may queue exactly 68 00; the wrapper can also divert locally.
// S2C 3F opens a map panel and S2C 68 updates another UI row, but neither is
// established as this request's original reply. CUSTOM-0087 separately pairs
// an owned regional-map control with native 3F display, without claiming the
// original server's 68 response contract. This codec alone grants no action.
struct RecoveredMapPanelControl68 {
    static constexpr std::uint8_t opcode=0x68;
    static constexpr std::size_t logical_size=2;
    struct Request {
        bool operator==(const Request&) const=default;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode || bytes[1]!=0)return {};
        return Request{};
    }
    static constexpr std::array<std::uint8_t,logical_size> encode(Request) noexcept {
        return {opcode,0};
    }
};
}
