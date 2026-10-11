#include "cn/world/CnOutdoorCamera.h"
#include <algorithm>
#include <limits>
#include <vector>

namespace god2cn {
namespace {
std::optional<std::int32_t> narrow(std::int64_t n) {
    if(n<std::numeric_limits<std::int32_t>::min() || n>std::numeric_limits<std::int32_t>::max())return std::nullopt;
    return static_cast<std::int32_t>(n);
}
std::optional<CnOutdoorCamera::Point> mode0_grid(CnOutdoorCamera::Point camera) {
    const auto sx=narrow(std::int64_t(camera.x)+0xd20),sy=narrow(std::int64_t(camera.y)+0x348);
    if(!sx || !sy)return std::nullopt;
    const auto rx=*sx%80,ry=*sy%40; // Native signed truncating quotient/remainder.
    unsigned region;
    // Pinned SSE constants +0.5,-0.5,20,0. All residue values and half-integer
    // expressions are exactly representable; scaled comparisons preserve ties.
    if(rx<=40) {
        if(ry<=20)region=2*ry+rx-40<0 ? 0 : 2;
        else region=2*ry-rx-40>0 ? 3 : 2;
    } else {
        if(ry<=20)region=2*ry-rx+40>=0 ? 2 : 1;
        else region=2*ry+rx-120>0 ? 4 : 2;
    }
    constexpr std::array<std::int32_t,5> x_offset{0,1,0,-1,0}; //007F0FB8
    constexpr std::array<std::int32_t,5> y_offset{-1,0,0,0,1}; //007F0FCC
    //00475BE0 dimensions21/21, followed by00472380 subtract21/63.
    const auto x=narrow(std::int64_t(x_offset[region])+*sx/80-*sy/40-11);
    const auto y=narrow(std::int64_t(y_offset[region])+*sx/80+*sy/40-73);
    if(!x || !y)return std::nullopt;
    return CnOutdoorCamera::Point{*x,*y};
}
}
std::optional<CnOutdoorCamera::Point> CnOutdoorCamera::initial_mode0_before_cache_switch(
    const CnOutdoorTerrain::InitialWorldPlacement& placement) {
    //00470C10 passes x+21,y+21,63,63;004751C0 uses the first63
    // to form even64. Its sixth stack argument is not read in this image.
    // X=(x+21+y+21)*40-1680-400; Y=(64-(x+21)+(y+21)-2)*20-840-300.
    // Qualified mathematical domain only: native wrapped intermediate values
    // are not promoted. Retain the native operation order when narrowing.
    const auto x=narrow(std::int64_t(placement.local_x)+21);
    const auto y=narrow(std::int64_t(placement.local_y_plus_one)+21);
    if(!x || !y)return std::nullopt;
    const auto sum=narrow(std::int64_t(*x)+*y);
    const auto y_minus_two=narrow(std::int64_t(*y)-2);
    const auto minus_x=narrow(64-std::int64_t(*x));
    if(!sum || !y_minus_two || !minus_x)return std::nullopt;
    const auto vertical=narrow(std::int64_t(*minus_x)+*y_minus_two);
    if(!vertical)return std::nullopt;
    const auto px=narrow(std::int64_t(*sum)*40),py=narrow(std::int64_t(*vertical)*20);
    if(!px || !py)return std::nullopt;
    const auto map_x=narrow(std::int64_t(*px)-1680),map_y=narrow(std::int64_t(*py)-840);
    if(!map_x || !map_y)return std::nullopt;
    const auto camera_x=narrow(std::int64_t(*map_x)-400),camera_y=narrow(std::int64_t(*map_y)-300);
    if(!camera_x || !camera_y)return std::nullopt;
    return Point{*camera_x,*camera_y};
}
std::optional<CnOutdoorCamera::Projection> CnOutdoorCamera::project_mode0(const View& view) {
    if(view.viewport_width<0 || view.viewport_height<0 || view.tile_width<=0 || view.tile_height<=0)return std::nullopt;
    const auto grid=mode0_grid(view.camera);
    if(!grid)return std::nullopt;
    const auto width=view.viewport_width/view.tile_width;
    const auto height=narrow(std::int64_t(view.viewport_height)/view.tile_height+1);
    if(!height)return std::nullopt;
    const auto left=narrow(std::int64_t(grid->x)-*height);
    const auto down=narrow(std::int64_t(grid->y)+*height);
    const auto right=narrow(std::int64_t(grid->x)+width);
    const auto upper=narrow(std::int64_t(grid->y)+width);
    if(!left || !down || !right || !upper)return std::nullopt;
    const auto lower_right=narrow(std::int64_t(*left)+width);
    const auto lower_down=narrow(std::int64_t(*down)+width);
    if(!lower_right || !lower_down)return std::nullopt;
    const Point shift{grid->x< -19 || *left< -19 ? -1 : (*right<40 && *lower_right<40 ? 0 : 1),
        grid->y< -19 || *upper< -19 ? -1 : (*down<40 && *lower_down<40 ? 0 : 1)};
    Projection result{*grid,shift,{}}; // Native explicitly clears all nine flags.
    const std::array<Point,4> corners{*grid,Point{*left,*down},Point{*right,*upper},Point{*lower_right,*lower_down}};
    std::vector<std::size_t> unique;
    for(const auto point:corners) {
        const auto x=narrow(std::int64_t(point.x)+21),y=narrow(std::int64_t(point.y)+21);
        if(!x || !y)return std::nullopt;
        const auto col=*x/21,row=*y/21;
        // Native tests unsigned values; negatives are outside, not clamped.
        if(col<0 || col>=3 || row<0 || row>=3)continue;
        const auto slot=static_cast<std::size_t>(col+row*3);
        result.visible_slots[slot]=true;
        if(std::find(unique.begin(),unique.end(),slot)==unique.end())unique.push_back(slot);
    }
    const auto bridge=[&](std::size_t a,std::size_t b) {
        if(a%3!=b%3 && a/3!=b/3) {
            result.visible_slots[a%3+(b/3)*3]=true;
            result.visible_slots[b%3+(a/3)*3]=true;
        }
    };
    // Preserve native unique-corner conditions exactly, not a bounding box.
    if(unique.size()>1)bridge(unique[0],unique[1]);
    if(unique.size()==3) {bridge(unique[0],unique[2]);bridge(unique[2],unique[1]);}
    return result;
}
std::optional<std::int32_t> CnOutdoorCamera::decode_ascii_axis(std::string_view value) {
    if(value.size()!=2 || value[1]<'0' || value[1]>'9')return std::nullopt;
    auto first=static_cast<unsigned char>(value[0]);
    if(first>='a' && first<='z')first=static_cast<unsigned char>(first-'a'+'A');
    if(first<'A' || first>'Z')return std::nullopt;
    return (first-'A')*10+(value[1]-'0');
}
std::optional<std::string> CnOutdoorCamera::map_reference(std::string_view prefix,
    CnOutdoorTerrain::ChunkCoordinate center) {
    if(prefix.empty() || prefix.find('\0')!=std::string_view::npos ||
       center.x<0 || center.y<0 || center.x>259 || center.y>259)return std::nullopt;
    std::string result(prefix); // Qualified native owner's raw prefix; no conversion.
    const auto append=[&](std::int32_t n) {
        result.push_back(static_cast<char>('A'+n/10));result.push_back(static_cast<char>('0'+n%10));
    };
    append(center.x);result.push_back('x');append(center.y);result.append(".map");
    return result;
}
std::optional<CnOutdoorCamera::Point> CnOutdoorCamera::success_camera(Point original,Point shift) {
    if(shift.x< -1 || shift.x>1 || shift.y< -1 || shift.y>1)return std::nullopt;
    constexpr std::array<Point,9> offsets{Point{-1680,0},Point{-840,-420},Point{0,-840},
        Point{-840,420},Point{0,0},Point{840,-420},Point{0,840},Point{840,420},Point{1680,0}};
    const auto offset=offsets[static_cast<std::size_t>(shift.x+shift.y*3+4)];
    const auto x=narrow(std::int64_t(original.x)-offset.x),y=narrow(std::int64_t(original.y)-offset.y);
    if(!x || !y)return std::nullopt;
    return Point{*x,*y};
}
}
