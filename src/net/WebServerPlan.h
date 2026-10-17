#pragma once
#include "net/WebClientGateway.h"

namespace god2 {
// Source hosting opt-in; ordinary Config/main remains unchanged. Native
// destinations come from Application listener objects, never this plan/browser.
struct WebServerPlan {
    enum class Role {TwAccount,TwWorld};
    struct Route {Role role;};
    WebGatewayPolicy policy;
    std::vector<Route> routes;
};
}
