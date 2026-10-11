#pragma once
#include "net/WebClientGateway.h"
#include <optional>

namespace god2 {
// Source hosting opt-in; ordinary Config/main remains unchanged. Native
// destinations come from Application listener objects, never this plan/browser.
struct WebServerPlan {
    enum class Role {TwAccount,TwWorld,CnAccount,CnWorld};
    struct CnTarget {std::uint16_t group,server;};
    struct Route {Role role;std::optional<CnTarget> target;};
    WebGatewayPolicy policy;
    std::vector<Route> routes;
};
}
