#pragma once
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Qualified C2S02 forms emitted through00480B10 by the pre-world UI owner.
// This is NOT the23-byte S2C02 status layout or an in-world gameplay opcode.
// 00440CA0 calls(2,0,1) when account transport is absent and world is live;
// 00448475 calls(2,4,1) after deletion's actual EAX0/list compaction.
// 0043D414 calls(2,3,1) after ordinary create's nonzero/non31 status.
// Control0 also occurs on ordinary-create success/reconnect and multiple UI
// abort/reset branches; its value alone does not mean account recovery.
// The wrapper sends one byte, waits for S2C03 when requested, then clears
// its own transport flags. No authority, official server rule or03 generator
// is inferred; other callers/control values require their own qualification.
struct CnPreWorldCloseControl {
    enum class Form:std::uint8_t {Native0=0,OrdinaryCreateFailure=3,AfterCharacterDeletion=4};
    Form form;
    static std::optional<CnPreWorldCloseControl> read(std::span<const std::uint8_t> record) {
        if(record.size()!=2 || record[0]!=0x02)return std::nullopt;
        if(record[1]!=0 && record[1]!=3 && record[1]!=4)return std::nullopt;
        return CnPreWorldCloseControl{static_cast<Form>(record[1])};
    }
};
}
