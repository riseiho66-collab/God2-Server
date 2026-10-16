#pragma once
#include "protocol/RecoveredNativeMovement.h"
#include "game/RecoveredPosition.h"
#include "game/OwnedOrdinaryMovementPolicy.h"
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
    using OrdinaryPolicy=OwnedOrdinaryMovementPolicy;
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
