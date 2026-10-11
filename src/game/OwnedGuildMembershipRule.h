#pragma once
#include <cstdint>
namespace god2 {
// CUSTOM-0078: reference-based policy, not recovered original server rules.
// No grant, debit or membership mutation occurs in rule evaluation.
struct OwnedGuildMembershipInput {
    std::uint8_t level{};
    // CUSTOM-0088 wallet input; fixed existing creation policy stays unchanged.
    std::uint64_t wallet{};
};
struct OwnedGuildMembershipPolicy {
    std::uint32_t creation_fee{};
    std::uint8_t minimum_level{},initial_capacity{};
    bool may_create{};
    bool operator==(const OwnedGuildMembershipPolicy&) const=default;
};
}
