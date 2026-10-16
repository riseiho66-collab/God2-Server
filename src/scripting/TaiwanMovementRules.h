#pragma once
#include "protocol/RecoveredNativeMovement.h"
#include "game/RecoveredPosition.h"
#include <filesystem>
#include <memory>
#include <thread>

namespace god2 {
// Pure current-native TW geometry preparation. The native cell and direction
// must come from this actual actor/scene; missing data is never a zero default.
class TaiwanMovementRules {
public:
    struct Step {RecoveredMovement::Request request;std::uint8_t direction,native_cell;};
    // CUSTOM-0150 explicit immutable installation policy; no numeric defaults.
    struct OrdinaryPolicy {
        std::uint64_t version;
        std::uint32_t step_interval_us;
        std::uint8_t burst_steps,initial_credit_steps,first_sequence;
        bool block_players,forbid_corner_cut,allow_zero;
        OrdinaryPolicy()=delete;
        // All scalar choices are required, never uninitialized defaults.
        OrdinaryPolicy(std::uint64_t actual_version,std::uint32_t interval_us,
            std::uint8_t burst,std::uint8_t initial_credit,std::uint8_t first,
            bool blocks_players,bool blocks_corners,bool permits_zero)
            :version(actual_version),step_interval_us(interval_us),burst_steps(burst),
             initial_credit_steps(initial_credit),first_sequence(first),block_players(blocks_players),
             forbid_corner_cut(blocks_corners),allow_zero(permits_zero) {}
    };
    static bool valid_ordinary_policy(const OrdinaryPolicy&) noexcept;
    bool supports_owned_ordinary() const;
    std::optional<std::uint8_t> owned_ordinary_token(const OrdinaryPolicy&,
        const RecoveredPosition&,const RecoveredMovement::Request&,std::uint8_t expected_sequence,
        bool destination_occupied,bool diagonal_sides_clear);
    explicit TaiwanMovementRules(const std::filesystem::path&);
    ~TaiwanMovementRules();
    TaiwanMovementRules(const TaiwanMovementRules&)=delete;
    TaiwanMovementRules& operator=(const TaiwanMovementRules&)=delete;
    std::optional<Step> prepare(const RecoveredMovement::Request&,const RecoveredPosition&,
        std::uint8_t previous_direction,std::uint8_t native_cell);
private:
    struct Vm;
    std::unique_ptr<Vm> vm_;
    std::thread::id thread_=std::this_thread::get_id();
};
}
