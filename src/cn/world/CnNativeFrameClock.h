#pragma once
#include <cstdint>
#include <optional>

namespace god2cn {
//0048A4D0 uses the PREVIOUS saved+89B210 for0048AA10/005395E0.
// New timeGetTime samples update the NEXT elapsed only after native update.
// Renderer cadence, not server move permission or a substitute server clock.
struct CnNativeFrameClock {
    struct State {
        std::uint32_t frame_base_tick; // Native+89B1FC.
        std::uint32_t previous_tick;   // Native+89B214.
        std::uint32_t stored_elapsed;  // Native+89B210, used by this frame.
        bool operator==(const State&) const=default;
    };
    struct Observation {
        State before; // Actual retained loop state, no guessed bootstrap.
        std::int32_t native_update_return; //0048AA10; normal continuation3.
        std::int32_t native_loop_enabled; // Actual DAT00886060, not permission.
        std::uint32_t first_time_get_time;
        // Actual second call ONLY when first<frame_base, not a guessed wrap delta.
        std::optional<std::uint32_t> second_time_get_time;
    };
    struct Next {
        State after;
        std::uint32_t current_tick; // Native+89B200.
        bool reset_frame_counters; // Native+89B204/+89B208 on clock rollover.
    };
    // Exact signed IDIV32(1000,actualDAT008964CC) stored as unsigned bits.
    // Initial frame call005395E0 precedes this bootstrap; not modeled here.
    static std::optional<State> initialize(std::uint32_t actual_time_get_time,
        std::int32_t actual_native_frame_rate);
    // Timing slice only; native counters/render/message/exit paths remain owners.
    static std::optional<Next> after_native_update(const Observation&);
};
}
