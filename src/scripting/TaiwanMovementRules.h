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
