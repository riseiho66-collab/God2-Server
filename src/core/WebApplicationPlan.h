#pragma once
#include "core/Config.h"
#include "net/WebServerPlan.h"
#include <stdexcept>

namespace god2 {
// Pure startup compatibility only. No DB, listener, selection or authority is
// created here; a real three-world native plan still supplies every issuer.
inline void validate_web_application_plan(const Config& config,const WebServerPlan& web,
        bool three_channels) {
    web.validate();
    if(!config.recovered_account_auth||config.mock_login||!is_credential_mode(config.protocol_mode)||
       config.protocol_mode==ProtocolMode::God2CharacterConnection)
        throw std::invalid_argument("WEB TW requires hosted native authentication and role");
    bool account=false,world=false;
    for(const auto& route:web.routes) {
        account|=route.role==WebServerPlan::Role::TwAccount;
        world|=route.role==WebServerPlan::Role::TwWorld;
    }
    if(world&&!config.recovered_dual_connection)
        throw std::invalid_argument("WEB TW world requires its actual dual-connection listener");
    if(three_channels&&world&&!account)
        throw std::invalid_argument("Three-channel WEB world routes require the actual L route");
}
}
