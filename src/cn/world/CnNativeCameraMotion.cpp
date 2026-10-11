#include "cn/world/CnNativeCameraMotion.h"
#include <bit>
#include <cfenv>
#include <cmath>
#include <limits>

namespace god2cn {
namespace {
static_assert(sizeof(float)==4 && std::numeric_limits<float>::is_iec559);
//007F1CF0,8 rows of0x30. Exact binary32 speed bits, not rounded decimals.
constexpr std::array<std::uint32_t,7> speeds{0x40000000,0x40133333,0x402ccccd,
    0x40400000,0x404ccccd,0x40733333,0x409ccccd};
constexpr std::array<CnOutdoorCamera::Point,8> velocities{CnOutdoorCamera::Point{-60,-30},
    CnOutdoorCamera::Point{0,-60},CnOutdoorCamera::Point{60,-30},CnOutdoorCamera::Point{60,0},
    CnOutdoorCamera::Point{60,30},CnOutdoorCamera::Point{0,60},CnOutdoorCamera::Point{-60,30},CnOutdoorCamera::Point{-60,0}};
constexpr std::array<CnOutdoorCamera::Point,8> distances{CnOutdoorCamera::Point{-40,-20},
    CnOutdoorCamera::Point{0,-40},CnOutdoorCamera::Point{40,-20},CnOutdoorCamera::Point{80,0},
    CnOutdoorCamera::Point{40,20},CnOutdoorCamera::Point{0,40},CnOutdoorCamera::Point{-40,20},CnOutdoorCamera::Point{-80,0}};
bool supported(float f) {return std::isfinite(f) && (f==0 || std::fpclassify(f)!=FP_SUBNORMAL);}
// Explicit stores preserve MULSS/ADDSS/SUBSS rounding and disallow contraction
// in the supported strict build. Compiler modes must be qualified in phase2.
float mul(float a,float b) {volatile float out=a*b;return out;}
float add(float a,float b) {volatile float out=a+b;return out;}
float sub(float a,float b) {volatile float out=a-b;return out;}
std::optional<std::int32_t> narrow(std::int64_t n) {
    if(n<std::numeric_limits<std::int32_t>::min() || n>std::numeric_limits<std::int32_t>::max())return std::nullopt;
    return static_cast<std::int32_t>(n);
}
struct Axis {std::int32_t delta,remaining;float residue;bool complete;};
std::optional<Axis> advance_axis(std::int32_t remaining,float velocity,float residue,float elapsed) {
    if(!supported(velocity) || !supported(residue))return std::nullopt;
    const auto scaled=mul(velocity,elapsed);
    const auto travel=mul(scaled,std::bit_cast<float>(std::uint32_t{0x3a83126f})); //007F58B8.
    const auto value=add(travel,residue);
    // CVTTSS2SI invalid/NaN/overflow variants are not promoted into C++ casts.
    if(!supported(scaled) || !supported(travel) || !supported(value) ||
       double(value)<-2147483648.0 || double(value)>=2147483648.0)return std::nullopt;
    auto delta=static_cast<std::int32_t>(value); // Native truncation first.
    volatile float integer=static_cast<float>(delta);
    const auto fraction=sub(value,integer);
    const auto rounded=narrow(std::int64_t(delta)+(fraction>=0.5f?1:(fraction<=-0.5f?-1:0)));
    if(!rounded)return std::nullopt;
    delta=*rounded;integer=static_cast<float>(delta);
    const auto next_residue=sub(value,integer);
    if(!supported(next_residue))return std::nullopt;
    if(remaining==0)return Axis{0,0,0,true};
    const auto next=narrow(std::int64_t(remaining)-delta);
    if(!next)return std::nullopt;
    const bool complete=remaining>0?*next<=0:*next>=0;
    if(complete)return Axis{remaining,0,0,true};
    return Axis{delta,*next,next_residue,false};
}
}
std::optional<CnNativeCameraMotion::State> CnNativeCameraMotion::begin(CnOutdoorCamera::Point camera,
    std::uint8_t direction,std::uint8_t index,std::optional<float> mount) {
    if(direction>=8 || index>=7 || std::fegetround()!=FE_TONEAREST || (mount && !supported(*mount)))return std::nullopt;
    const auto base=std::bit_cast<float>(speeds[index]);
    const auto speed=mount?add(*mount,base):base;
    const auto x=mul(speed,static_cast<float>(velocities[direction].x));
    const auto y=mul(speed,static_cast<float>(velocities[direction].y));
    if(!supported(speed) || !supported(x) || !supported(y))return std::nullopt;
    // Native initializer explicitly clears both residues, reads travel from LUT.
    return State{camera,distances[direction].x,distances[direction].y,x,y,0,0};
}
std::optional<CnNativeCameraMotion::Frame> CnNativeCameraMotion::advance(const State& before,std::uint32_t actual_elapsed) {
    if(std::fegetround()!=FE_TONEAREST)return std::nullopt;
    // Native signed-int->double+{0,2^32}->binary32 yields the same exact
    // unsigned value before this explicit binary32 store in the qualified mode.
    volatile float elapsed=static_cast<float>(static_cast<double>(actual_elapsed));
    const auto x=advance_axis(before.remaining_x,before.velocity_x,before.residue_x,elapsed);
    const auto y=advance_axis(before.remaining_y,before.velocity_y,before.residue_y,elapsed);
    if(!x || !y)return std::nullopt;
    const auto camera_x=narrow(std::int64_t(before.camera.x)+x->delta);
    const auto camera_y=narrow(std::int64_t(before.camera.y)+y->delta);
    if(!camera_x || !camera_y)return std::nullopt;
    return Frame{State{{*camera_x,*camera_y},x->remaining,y->remaining,before.velocity_x,before.velocity_y,
        x->residue,y->residue},{x->delta,y->delta},x->complete && y->complete};
}
}
