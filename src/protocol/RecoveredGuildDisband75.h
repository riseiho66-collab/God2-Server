#pragma once
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Native149c/currentc5d8: main25 ->004EF7C0 modal5 ->004EE560 case5
// ->004EF800 ->004132E0 sends C2S75 plus the selected self row's slot byte.
// Evidence: native-guild-management-0081/disband-plan-v01/report.json.
// This is C2S grammar only. No dedicated S2C75 ACK has been established.
// A native-local slot is never a database ID or founder authorization. The
// qualified current recipient uses self slot0; CUSTOM-0081 service must enforce
// founder/full-publication/single-use/world/storage authority separately.
struct RecoveredGuildDisband75 {
    static constexpr std::uint8_t opcode=0x75,slot_limit=50;
    static constexpr std::size_t request_size=2;
    struct Request {
        std::uint8_t slot{};
        bool operator==(const Request&) const=default;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> logical) noexcept {
        if(logical.size()!=request_size || logical[0]!=opcode || logical[1]>=slot_limit)return {};
        return Request{logical[1]};
    }
};
}
