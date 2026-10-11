#pragma once
#include "cn/world/CnOutdoorCamera.h"

namespace god2cn {
//00539150/005393B0 native renderer movement; not server speed permission.
struct CnNativeCameraMotion {
    struct State {
        CnOutdoorCamera::Point camera;
        std::int32_t remaining_x,remaining_y; // Native+14/+18.
        float velocity_x,velocity_y,residue_x,residue_y; //+24/+28,+1C/+20.
    };
    struct Frame {
        State after; // Before00473120's conditional cache-switch rebase.
        CnOutdoorCamera::Point delta;
        bool complete; // Both native axis-completion branches, not an ack.
    };
    // Direction already qualified from00539150 geometry; speed index is the
    // actual owner+230 byte. Optional mount addition is the actual00489070
    // coefficient only when00539150's packed-state branch applies. No defaults.
    // Does not insert the ring, emit2E, grant motion or advance path indices.
    static std::optional<State> begin(CnOutdoorCamera::Point camera,
        std::uint8_t direction,std::uint8_t actual_speed_index,
        std::optional<float> actual_mount_addition);
    // Actual unsigned native+89B210 elapsed; never derived from2E count/CAS.
    // Qualified strict binary32 nearest-mode/non-subnormal/no-overflow subset.
    static std::optional<Frame> advance(const State&,std::uint32_t actual_elapsed);
};
}
