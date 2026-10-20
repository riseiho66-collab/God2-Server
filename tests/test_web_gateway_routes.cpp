#include "net/WebClientGateway.h"
#include "net/WebServerPlan.h"
#include <nlohmann/json.hpp>
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using namespace god2;
using Route=WebNativeRoute;
using Json=nlohmann::json;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class F> void refuses(F&& call,const char* message) {
    bool rejected=false;try{call();}catch(const std::invalid_argument&){rejected=true;}
    require(rejected,message);
}
asio::ip::tcp::endpoint endpoint(std::uint16_t port) {
    return {asio::ip::address_v4::loopback(),port};
}
WebGatewayPolicy policy() {
    WebGatewayPolicy p;
    p.listen=endpoint(0); // Bound-port allocation is a later host operation.
    p.origins={"http://127.0.0.1:8080","https://game.example"};
    p.max_sessions=12;p.sessions_per_address=4;p.accepts_per_second=8;
    p.message_bytes=4096;p.queue_bytes=65546;p.queue_frames=4;
    p.frames_per_second=32;p.bytes_per_second=16384;
    p.handshake_timeout=std::chrono::seconds(5);p.idle_timeout=std::chrono::seconds(30);
    p.message_timeout=std::chrono::seconds(4);p.close_timeout=std::chrono::seconds(2);
    return p;
}
std::vector<Route> triple() {
    // Distinct opaque bound ports; channel numbers are metadata, not ports.
    return {{"/tw/native",endpoint(45173)},
        {"/tw/native-game/0",endpoint(53421),std::uint8_t{7},std::uint8_t{0}},
        {"/tw/native-game/1",endpoint(49731),std::uint8_t{7},std::uint8_t{1}},
        {"/tw/native-game/2",endpoint(61243),std::uint8_t{7},std::uint8_t{2}}};
}
void explicit_policy_and_pre_db_plan() {
    validate_web_gateway_policy(policy());
    refuses([]{validate_web_gateway_policy({});},"Zero/default transport policy accepted");
    auto bad=policy();bad.listen.address(asio::ip::address_v4::any());
    refuses([&]{validate_web_gateway_policy(bad);},"Nonloopback web listener accepted");
    for(const auto field:{&WebGatewayPolicy::max_sessions,&WebGatewayPolicy::sessions_per_address,
            &WebGatewayPolicy::accepts_per_second,&WebGatewayPolicy::message_bytes,
            &WebGatewayPolicy::queue_frames,&WebGatewayPolicy::frames_per_second,&WebGatewayPolicy::bytes_per_second}) {
        bad=policy();bad.*field=0;
        refuses([&]{validate_web_gateway_policy(bad);},"Missing explicit transport budget accepted");
    }
    bad=policy();bad.queue_bytes=65545;
    refuses([&]{validate_web_gateway_policy(bad);},"Native read reservation exceeds queue budget");
    bad=policy();bad.message_bytes=16*1024*1024+1;
    refuses([&]{validate_web_gateway_policy(bad);},"Unbounded incoming message accepted");
    for(const auto timeout:{&WebGatewayPolicy::handshake_timeout,&WebGatewayPolicy::idle_timeout,
            &WebGatewayPolicy::message_timeout,&WebGatewayPolicy::close_timeout}) {
        bad=policy();bad.*timeout=std::chrono::seconds(0);
        refuses([&]{validate_web_gateway_policy(bad);},"Missing explicit timeout accepted");
        bad=policy();bad.*timeout=std::chrono::seconds::max();
        refuses([&]{validate_web_gateway_policy(bad);},"Seconds-to-steady-clock overflow accepted");
    }
    for(const auto& origin:std::vector<std::string>{"null","*","ftp://example","https://game.example\r\nX: y",
            std::string("https://game.example\0evil",25)}) {
        bad=policy();bad.origins={origin};
        refuses([&]{validate_web_gateway_policy(bad);},"Invalid Origin policy accepted");
    }
    bad=policy();bad.origins.push_back(bad.origins.front());
    refuses([&]{validate_web_gateway_policy(bad);},"Duplicate Origin policy accepted");
    WebServerPlan plan{policy(),{{WebServerPlan::Role::TwAccount},{WebServerPlan::Role::TwWorld}}};
    plan.validate();
    plan.routes.clear();refuses([&]{plan.validate();},"Empty host role list accepted");
    plan.routes={{WebServerPlan::Role::TwWorld},{WebServerPlan::Role::TwWorld}};
    refuses([&]{plan.validate();},"Repeated host world role accepted");
    plan.routes={{static_cast<WebServerPlan::Role>(200)}};
    refuses([&]{plan.validate();},"Unknown host role accepted");
}
void legacy_shapes_and_manifest_consumer() {
    const std::vector<Route> routes{{"/tw/native",endpoint(54321)},{"/tw/native-game",endpoint(54322)}};
    validate_web_native_routes(routes);
    const auto body=web_native_routes_manifest(routes);
    const auto doc=Json::parse(body);
    require(body.size()<=4096&&doc.size()==3&&doc.at("version")==1,"Manifest schema or fixed size changed");
    require(doc.at("account").size()==1&&doc.at("account").at("path")=="/tw/native","Account path inferred incorrectly");
    const auto& games=doc.at("games");require(games.size()==1,"Legacy G map expanded into imaginary channels");
    require(games[0].size()==3&&games[0].at("path")=="/tw/native-game"&&
        games[0].at("native_address")=="127.0.0.1"&&games[0].at("native_port")==54322,
        "Manifest changed its supplied actual endpoint or invented metadata");
    const std::vector<Route> world_only{routes[1]};
    require(Json::parse(web_native_routes_manifest(world_only)).at("account").is_null(),
        "Typed legacy G-only route invented an account listener");
    const std::vector<Route> account_only{routes[0]};
    require(Json::parse(web_native_routes_manifest(account_only)).at("games").empty(),
        "Account-only transport invented a G listener");
    // Internal typed endpoints remain observations of held listeners; limiting
    // the browser's path never reinterprets an explicit LAN bind as loopback.
    const std::vector<Route> lan{{"/tw/native-game",{asio::ip::make_address("192.0.2.1"),54322}}};
    require(Json::parse(web_native_routes_manifest(lan)).at("games")[0].at("native_address")=="192.0.2.1",
        "Typed legacy native endpoint domain changed");
}
void complete_three_bound_endpoints_are_public_metadata() {
    auto routes=triple();std::reverse(routes.begin(),routes.end());
    validate_web_native_routes(routes);
    const auto doc=Json::parse(web_native_routes_manifest(routes));
    const auto& games=doc.at("games");require(games.size()==3,"Three actual G routes missing");
    const std::uint16_t ports[]{53421,49731,61243};
    for(std::size_t i=0;i<3;++i) {
        const auto& game=games[i];
        require(game.size()==5&&game.at("path")=="/tw/native-game/"+std::to_string(i)&&
            game.at("native_port")==ports[i]&&game.at("native_address")=="127.0.0.1"&&
            game.at("group")==7&&game.at("subgroup")==i,"Channel manifest lost exact bound endpoint/namespace");
    }
    require(doc.at("account").size()==1,"Account metadata exposed extra authority or payload");
}
void partial_or_ambiguous_three_channel_maps_refuse() {
    auto bad=triple();bad.pop_back();
    refuses([&]{validate_web_native_routes(bad);},"Partial channel topology accepted");
    bad=triple();bad.erase(bad.begin());
    refuses([&]{validate_web_native_routes(bad);},"Channels without actual account path accepted");
    bad=triple();bad[2].endpoint=bad[1].endpoint;
    refuses([&]{validate_web_native_routes(bad);},"Two channel paths aliased one native endpoint");
    bad=triple();bad[0].endpoint=bad[1].endpoint;
    refuses([&]{validate_web_native_routes(bad);},"Account and G aliased one native endpoint");
    bad=triple();bad[1].path="/tw/native-game";
    refuses([&]{validate_web_native_routes(bad);},"Mixed legacy/indexed G topology accepted");
    bad=triple();bad[2].group=8;
    refuses([&]{validate_web_native_routes(bad);},"Channels from different native groups accepted");
    bad=triple();bad[2].subgroup=0;
    refuses([&]{validate_web_native_routes(bad);},"Path/subgroup mismatch accepted");
    bad=triple();bad[1].group.reset();
    refuses([&]{validate_web_native_routes(bad);},"Missing actual channel group accepted");
    bad=triple();bad[1].subgroup.reset();
    refuses([&]{validate_web_native_routes(bad);},"Missing actual channel subgroup accepted");
    bad=triple();for(auto& route:bad)if(route.group)route.group=10;
    refuses([&]{validate_web_native_routes(bad);},"Native group outside0..9 accepted");
}
void no_browser_selected_destination_or_path_alias() {
    for(const auto& path:std::vector<std::string>{"/tw/native?host=127.0.0.1:80","/tw/native-game/3",
            "/tw/native-game/00","/tw/native-game/%30","/tw/native-game/0/","/tw/native-routes",
            "https://example/native","/tw/native-game?port=12345"}) {
        std::vector<Route> bad{{path,endpoint(54321)}};
        refuses([&]{validate_web_native_routes(bad);},"Unregistered/query/decoded route accepted");
        refuses([&]{(void)web_native_routes_manifest(bad);},"Manifest serialized an unregistered destination");
    }
    std::vector<Route> bad{{"/tw/native",endpoint(0)}};
    refuses([&]{validate_web_native_routes(bad);},"Configured port0 substituted for actual bound port");
    bad={{"/tw/native",{asio::ip::address_v4::any(),54321}}};
    refuses([&]{validate_web_native_routes(bad);},"Unassigned native destination accepted");
    bad={{"/tw/native",endpoint(54321)},{"/tw/native",endpoint(54322)}};
    refuses([&]{validate_web_native_routes(bad);},"Repeated path selected first/last destination");
    bad={{"/tw/native-game",endpoint(54321),std::uint8_t{0},std::uint8_t{0}}};
    refuses([&]{validate_web_native_routes(bad);},"Legacy path invented native group metadata");
}
}
int main() {
    explicit_policy_and_pre_db_plan();
    legacy_shapes_and_manifest_consumer();
    complete_three_bound_endpoints_are_public_metadata();
    partial_or_ambiguous_three_channel_maps_refuse();
    no_browser_selected_destination_or_path_alias();
}
