#pragma once
#include "cn/protocol/CnCharacterSummary.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// World-login S2C1F: exact125 bytes, separate from Account07 and BeginPlay2A.
// Normal00444EC0 receives124 bytes into a temporary stack buffer and does not
// use it for1A;00444FE0 selects from07. Transfer0044D240 uses the07-selected
// row ordinal to read1F payload38+40*row. It does not compare the two slots,
// reorder1F by slot, or obtain a playable count from1F. Preserve all raw bytes.
// Evidence: cn-world-list-consumers-agent-01; upstream read-only view retained
// separately in the integration delivery. No serializer or guessed metadata.
class CnWorldCharacterList {
public:
    struct TransferSelection {
        std::uint8_t summary_slot;
        std::uint8_t world_list_slot;
        std::uint8_t emitted_enter_slot;
    };
    static std::optional<CnWorldCharacterList> read(std::span<const std::uint8_t> record) {
        if(record.size()!=125 || record[0]!=0x1f)return std::nullopt;
        CnWorldCharacterList result;
        std::copy(record.begin()+1,record.end(),result.payload_.begin());return result;
    }
    std::optional<TransferSelection> transfer_selection(
        const CnCharacterSummary& summary,std::size_t summary_row) const {
        if(summary_row>=summary.count())return std::nullopt;
        const auto row=summary.character(static_cast<unsigned>(summary_row));
        if(!row)return std::nullopt;
        const auto raw_slot=payload_[38+40*summary_row];
        return TransferSelection{row->native_slot(),raw_slot,
            static_cast<std::uint8_t>(raw_slot<4?raw_slot:0)};
    }
    // Bounds come from the separate07, never this buffer's capacity. The
    // invalid-slot->0 native producer projection above is not authorization
    // to redirect an incoming request or identify a common character ID.
private:
    CnWorldCharacterList()=default;
    std::array<std::uint8_t,124> payload_{};
};
}
