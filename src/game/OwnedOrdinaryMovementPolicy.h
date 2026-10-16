#pragma once
#include <cstdint>

namespace god2 {
// CUSTOM-0150 value-only configuration; no runtime defaults or native claim.
struct OwnedOrdinaryMovementPolicy {
    std::uint64_t version;
    std::uint32_t step_interval_us;
    std::uint8_t burst_steps,initial_credit_steps,first_sequence;
    bool block_players,forbid_corner_cut,allow_zero;
    OwnedOrdinaryMovementPolicy()=delete;
    OwnedOrdinaryMovementPolicy(std::uint64_t actual_version,std::uint32_t interval_us,
        std::uint8_t burst,std::uint8_t initial_credit,std::uint8_t first,
        bool blocks_players,bool blocks_corners,bool permits_zero)
        :version(actual_version),step_interval_us(interval_us),burst_steps(burst),
         initial_credit_steps(initial_credit),first_sequence(first),block_players(blocks_players),
         forbid_corner_cut(blocks_corners),allow_zero(permits_zero) {}
    bool operator==(const OwnedOrdinaryMovementPolicy&) const=default;
    bool valid() const noexcept {
        return version>0 && step_interval_us>=1 && step_interval_us<=60000000 &&
            burst_steps>=1 && burst_steps<=39 && initial_credit_steps>=1 &&
            initial_credit_steps<=burst_steps && first_sequence<40;
    }
};
}
