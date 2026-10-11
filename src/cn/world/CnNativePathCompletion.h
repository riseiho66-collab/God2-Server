#pragma once
#include <cstdint>
#include <optional>
#include <vector>

namespace god2cn {
//005395E0 AFTER005393B0 returns1 and AFTER the actual deferred005385F0.
// Client renderer path progression, not an acknowledged server movement.
struct CnNativePathCompletion {
    struct Point {std::int32_t x,y;};
    struct Snapshot {
        std::int32_t cursor; // Actual native+34.
        std::int32_t count;  // Actual native+38, not inferred from target/distance.
        std::vector<Point> actual_points; // Exactly count actual+3C/+40 pairs.
    };
    struct Segment {Point from,to;};
    struct Plan {
        std::int32_t cursor_after_increment;
        // No next segment: native sets actor target to final point and state0,
        // publishes00537800/0047FE20, returns0. Otherwise00539150 executes
        // BEFORE changing actor target; failed start enters actual reset branch.
        std::optional<Segment> next_segment;
        Point target_on_success;
        std::int32_t native_return; //005395E0 return, never a server5D byte.
    };
    // Actual004866A0 capacity60 and representable in-buffer native states only.
    // Zero/oversized counts or missing points are unresolved, not fake paths.
    static std::optional<Plan> prepare(const Snapshot& after_actual_deferred_notification);
};
}
