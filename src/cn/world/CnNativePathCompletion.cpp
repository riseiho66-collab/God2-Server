#include "cn/world/CnNativePathCompletion.h"

namespace god2cn {
std::optional<CnNativePathCompletion::Plan> CnNativePathCompletion::prepare(const Snapshot& actual) {
    //00535D80 supplies0x3C capacity to004866A0; the path buffer ends before
    // actor camera+21C. Actual append/overflow/malformed-state variants stay open.
    if(actual.count<1 || actual.count>60 || actual.cursor<0 || actual.cursor>=actual.count ||
       actual.actual_points.size()!=static_cast<std::size_t>(actual.count))return std::nullopt;
    const auto next=actual.cursor+1;
    if(next>=actual.count-1) {
        // Native loads+34+count*8 /+38+count*8, which are point[count-1],
        // NOT point[count]. No destination extrapolation or zero coordinates.
        return Plan{next,std::nullopt,actual.actual_points.back(),0};
    }
    const auto from=actual.actual_points[static_cast<std::size_t>(next)];
    const auto to=actual.actual_points[static_cast<std::size_t>(next+1)];
    return Plan{next,Segment{from,to},from,1};
}
}
