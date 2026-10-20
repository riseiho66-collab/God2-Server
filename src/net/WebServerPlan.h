#pragma once
#include "net/WebClientGateway.h"
#include <stdexcept>

namespace god2 {
// Source hosting opt-in; ordinary Config/main remains unchanged. Native
// destinations come from Application listener objects, never this plan/browser.
struct WebServerPlan {
    enum class Role {TwAccount,TwWorld};
    struct Route {Role role;};
    WebGatewayPolicy policy;
    std::vector<Route> routes;
    // Pure pre-DB input validation shared by Main's explicit loader and App.
    // TwWorld expands to the actual held single-G or all three G listeners.
    void validate() const {
        validate_web_gateway_policy(policy);
        if(routes.empty()||routes.size()>2)
            throw std::invalid_argument("Web server plan requires explicit unique roles");
        bool account=false,world=false;
        for(const auto& route:routes) {
            if(route.role==Role::TwAccount) {
                if(account)throw std::invalid_argument("Web account role repeated");
                account=true;
            } else if(route.role==Role::TwWorld) {
                if(world)throw std::invalid_argument("Web world role repeated");
                world=true;
            } else throw std::invalid_argument("Web server role invalid");
        }
    }
};
}
