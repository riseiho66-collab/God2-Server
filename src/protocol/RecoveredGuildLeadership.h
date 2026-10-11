#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <stdexcept>

namespace god2 {
// Original149c/currentc5d8: C2S71 selected-row producer004EF320;
// C2S72 modal3 callback004EE560 ->004EF670; S2C93 ->004EE3B0.
// Evidence: native-guild-membership-0078/leader-entry-v01 (84 x86 cases).
// Direction is essential: these C2S71/72 actions are NOT S2C71/72 world
// mob/NPC records. The one-byte slot is recipient-local roster state, never
// a database identity or authorization. ApproveOrAppoint is not unconditional
// approval: native control18 can address every role and permits selfrole2/3.
// Original server approval/rank rules remain unverified; CUSTOM-0078 must
// supply authoritative ownership, pending/leader state and a fresh slot lease.
struct RecoveredGuildLeadership {
    enum class Action : std::uint8_t {
        ApproveOrAppoint=0x71,
        RejectOrRemove=0x72
    };
    static constexpr std::size_t request_size=2, role_update_size=3;
    static constexpr std::uint8_t role_update_opcode=0x93, slot_limit=50;
    struct Request {
        Action action{};
        std::uint8_t slot{};
        bool operator==(const Request&) const=default;
    };
    struct RoleUpdate {
        std::uint8_t slot{};
        std::uint8_t role{};
        bool operator==(const RoleUpdate&) const=default;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> logical) noexcept {
        if(logical.size()!=request_size || logical[1]>=slot_limit ||
           (logical[0]!=static_cast<std::uint8_t>(Action::ApproveOrAppoint) &&
            logical[0]!=static_cast<std::uint8_t>(Action::RejectOrRemove)))return {};
        return Request{static_cast<Action>(logical[0]),logical[1]};
    }
    // S2C93 updates an EXISTING native row. It neither inserts a row nor
    // establishes server-side authority; the recipient's self slot also
    // refreshes native controls. Roles0..3 are applicant/member/guardian/leader.
    static std::array<std::uint8_t,role_update_size> role_update(std::uint8_t slot,std::uint8_t role) {
        if(slot>=slot_limit || role>3)throw std::invalid_argument("Native guild93 slot/role bounds");
        return {role_update_opcode,slot,role};
    }
    static std::optional<RoleUpdate> decode_role_update(std::span<const std::uint8_t> logical) noexcept {
        if(logical.size()!=role_update_size || logical[0]!=role_update_opcode ||
           logical[1]>=slot_limit || logical[2]>3)return {};
        return RoleUpdate{logical[1],logical[2]};
    }
};
}
