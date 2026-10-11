#pragma once
#include "protocol/RecoveredZeroSeedKey.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
struct RecoveredPostServerSelect {
    static constexpr std::size_t wire_size=6;
    static constexpr std::uint8_t logical_opcode=0xa6;
    using Wire = std::array<std::uint8_t, wire_size>;
    Wire raw{};
    // 147D0 supplies two argument low BYTEs, 147EA writes opcodeA6. B490
    // reads Main+8F4/B40 WORD inputs; these bytes are not group/server IDs.
    // Keep complete original logical data; target/phase authority is separate.
    std::array<std::uint8_t, 3> logical{};
    std::uint8_t checksum = 0;
    std::size_t consumed = wire_size;
    std::array<std::uint8_t,2> selector_bytes() const noexcept {return {logical[1],logical[2]};}
};

inline std::optional<RecoveredPostServerSelect> ParseNativePostServerSelectRequest(
    std::span<const std::uint8_t> wire) {
    // Explicit existing recovered profile ONLY: key below, feedback0,
    // uncompressed standalone A6 logical3. Dynamic seed/codec flags and mixed
    // queues remain separately qualified. 12506 is a generic send return,
    // not proof of an opcode. Historical exact fixture remains historical.
    if(wire.size()!=RecoveredPostServerSelect::wire_size || wire[0]!=wire.size() || wire[1]!=0)
        return std::nullopt;

    RecoveredPostServerSelect result{};
    std::copy(wire.begin(), wire.end(), result.raw.begin());
    std::uint8_t previous = 0;
    std::uint8_t expected=static_cast<std::uint8_t>(wire[0]+wire[1]+2*0x3c);
    for (std::size_t i = 0; i < 4; ++i) {
        const auto clear = static_cast<std::uint8_t>(
            static_cast<std::uint8_t>(wire[i + 2] + 3 - previous) ^ recovered_zero_seed_key[i]);
        if (i < result.logical.size()) {
            result.logical[i] = clear;
            expected=static_cast<std::uint8_t>(expected+clear+0x3c);
        } else {
            result.checksum = clear;
            if(clear!=expected)return std::nullopt;
        }
        previous = clear;
    }
    if(result.logical[0]!=RecoveredPostServerSelect::logical_opcode)return std::nullopt;
    return result;
}

inline std::optional<RecoveredPostServerSelect> ParsePostServerSelectRequest(
    std::span<const std::uint8_t> wire) {
    // Preserve the frozen legacy/default exact-fixture gate. General A6 input
    // is selected only with actual native list/target/phase/source suppliers.
    constexpr RecoveredPostServerSelect::Wire captured{0x06,0x00,0xa3,0xa3,0xfd,0xd5};
    if(wire.size()!=captured.size() || !std::equal(wire.begin(),wire.end(),captured.begin()))return std::nullopt;
    return ParseNativePostServerSelectRequest(wire);
}
}
