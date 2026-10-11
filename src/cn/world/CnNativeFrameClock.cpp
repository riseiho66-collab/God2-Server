#include "cn/world/CnNativeFrameClock.h"
#include <bit>

namespace god2cn {
std::optional<CnNativeFrameClock::State> CnNativeFrameClock::initialize(std::uint32_t tick,std::int32_t rate) {
    if(!rate)return std::nullopt; // Native division fault is not a zero default.
    const auto quotient=static_cast<std::int32_t>(std::int64_t{1000}/rate);
    return State{tick,tick,std::bit_cast<std::uint32_t>(quotient)};
}
std::optional<CnNativeFrameClock::Next> CnNativeFrameClock::after_native_update(const Observation& observed) {
    if(observed.native_update_return!=3 || !observed.native_loop_enabled)return std::nullopt;
    const bool reset=observed.first_time_get_time<observed.before.frame_base_tick;
    if(reset!=observed.second_time_get_time.has_value())return std::nullopt;
    const auto tick=reset?*observed.second_time_get_time:observed.first_time_get_time;
    //0048A7AF..0048A7D5 resets BASE and frame counters, never previous_tick
    // before subtracting. Unsigned DWORD subtraction keeps actual wrap behavior.
    const std::uint32_t elapsed=tick-observed.before.previous_tick;
    const auto bounded=elapsed<5?std::uint32_t{5}:(elapsed>200?std::uint32_t{200}:elapsed);
    return Next{State{reset?tick:observed.before.frame_base_tick,tick,bounded},tick,reset};
}
}
