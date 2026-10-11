#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>

namespace god2 {
// CUSTOM-0077: native8E grammar with explicitly inactive CUSTOM metadata.
// Native4EC170 copies52 bytes; native dictionaries prove status6=no base.
// This is NOT an original rent/tax/building/capacity/leader reconstruction.
struct OwnedGuildPanelHeader {
    using Logical=std::array<std::uint8_t,53>;
    static constexpr std::optional<Logical> readonly_members(std::size_t count) noexcept {
        if(!count || count>50)return {};
        Logical wire{};wire[0]=0x8e;
        wire[1+0x0d]=6; // no base; no officer or economic action is granted
        wire[1+0x13]=static_cast<std::uint8_t>(count);
        wire[1+0x17]=50; // CUSTOM projection ceiling, NOT native membership policy
        // All other fields are inactive CUSTOM displaymetadata. Time/name/portrait
        // absent; no saved guild ID/revision is mislabeled as native headeridentity.
        return wire;
    }
};
}
