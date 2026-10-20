#include "core/WebApplicationPlan.h"
#include <chrono>
#include <stdexcept>

namespace {
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class F> bool refuses(F&& call){try{call();}catch(const std::invalid_argument&){return true;}return false;}
god2::WebServerPlan plan() {
    // Synthetic host-input fixture only. No socket, DB or native issuer.
    god2::WebServerPlan result;
    auto& p=result.policy;
    p.listen={asio::ip::make_address("127.0.0.1"),0};
    p.origins={"http://localhost"};p.max_sessions=2;p.sessions_per_address=2;
    p.accepts_per_second=2;p.message_bytes=65536;p.queue_bytes=65546;
    p.queue_frames=2;p.frames_per_second=2;p.bytes_per_second=65536;
    p.handshake_timeout=p.idle_timeout=p.message_timeout=p.close_timeout=std::chrono::seconds(1);
    result.routes={{god2::WebServerPlan::Role::TwAccount},{god2::WebServerPlan::Role::TwWorld}};
    return result;
}
}
int main() {
    // SOURCE cases only until the separately authorized concentrated phase.
    god2::Config config;
    config.protocol_mode=god2::ProtocolMode::God2LegacyCharacterListCandidate;
    config.mock_login=false;config.recovered_account_auth=true;config.recovered_dual_connection=true;
    auto web=plan();
    god2::validate_web_application_plan(config,web,false);
    god2::validate_web_application_plan(config,web,true); // Does not mint a native three-world plan.
    auto bad=config;bad.mock_login=true;
    require(refuses([&]{god2::validate_web_application_plan(bad,web,false);}),"Mock login was granted web native authority");
    bad=config;bad.recovered_account_auth=false;
    require(refuses([&]{god2::validate_web_application_plan(bad,web,false);}),"Missing native authentication was accepted");
    bad=config;bad.protocol_mode=god2::ProtocolMode::God2CharacterConnection;
    require(refuses([&]{god2::validate_web_application_plan(bad,web,false);}),"Standalone G was used as L");
    bad=config;bad.recovered_dual_connection=false;
    require(refuses([&]{god2::validate_web_application_plan(bad,web,false);}),"World route lacks actual G listener mode");
    auto account=web;account.routes.resize(1);
    god2::validate_web_application_plan(bad,account,false); // L-only is still explicitly supported.
    auto world=web;world.routes.erase(world.routes.begin());
    god2::validate_web_application_plan(config,world,false); // Existing typed single-G-only boundary.
    require(refuses([&]{god2::validate_web_application_plan(config,world,true);}),"Three G routes lack the actual L route");
    auto duplicate=web;duplicate.routes[1]=duplicate.routes[0];
    require(refuses([&]{god2::validate_web_application_plan(config,duplicate,false);}),"Duplicate role escaped pre-DB validation");
    auto policy=web;policy.policy.origins.clear();
    require(refuses([&]{god2::validate_web_application_plan(config,policy,false);}),"Invalid policy escaped pre-DB validation");
}
