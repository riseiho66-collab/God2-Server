#include "net/WebServerPlanConfig.h"
#include <nlohmann/json.hpp>
#include <fstream>
#include <initializer_list>
#include <limits>
#include <set>
#include <stdexcept>
#include <string_view>
#include <vector>

namespace god2 { namespace {
using J=nlohmann::json;
void need(bool value,const char* reason){if(!value)throw std::invalid_argument(reason);}
void fields(const J& object,std::initializer_list<std::string_view> names) {
    need(object.is_object()&&object.size()==names.size(),"Web configuration requires exact known fields");
    for(const auto name:names)need(object.contains(std::string(name)),"Web configuration field missing or unknown");
}
std::uint64_t number(const J& value,std::uint64_t maximum) {
    need(value.is_number_integer(),"Web configuration integer required");
    if(value.is_number_unsigned()){const auto n=value.get<std::uint64_t>();need(n<=maximum,"Web configuration integer overflow");return n;}
    const auto n=value.get<std::int64_t>();
    need(n>=0&&std::uint64_t(n)<=maximum,"Web configuration negative/overflow integer");return std::uint64_t(n);
}
std::string text(const J& value) {
    need(value.is_string(),"Web configuration string required");const auto result=value.get<std::string>();
    need(!result.empty()&&result.find('\0')==std::string::npos,"Web configuration empty/NUL string");return result;
}
}
WebServerPlan WebServerPlanConfig::from_json(const nlohmann::json& input) {
    fields(input,{"version","listen","origins","limits","timeouts_seconds","routes"});
    need(number(input.at("version"),1)==1,"Web configuration version1 required");
    const auto& listen=input.at("listen");fields(listen,{"address","port"});
    WebServerPlan result;
    // Literal parse only. No resolver, browser-controlled host or native port.
    result.policy.listen={asio::ip::make_address(text(listen.at("address"))),
        static_cast<std::uint16_t>(number(listen.at("port"),65535))};
    const auto& origins=input.at("origins");need(origins.is_array(),"Web origins array required");
    for(const auto& origin:origins)result.policy.origins.push_back(text(origin));
    const auto& limits=input.at("limits");
    fields(limits,{"max_sessions","sessions_per_address","accepts_per_second","message_bytes","queue_bytes",
        "queue_frames","frames_per_second","bytes_per_second"});
    const auto budget=[&](const char* name){return static_cast<std::size_t>(number(limits.at(name),std::numeric_limits<std::size_t>::max()));};
    auto& p=result.policy;
    p.max_sessions=budget("max_sessions");p.sessions_per_address=budget("sessions_per_address");
    p.accepts_per_second=budget("accepts_per_second");p.message_bytes=budget("message_bytes");
    p.queue_bytes=budget("queue_bytes");p.queue_frames=budget("queue_frames");
    p.frames_per_second=budget("frames_per_second");p.bytes_per_second=budget("bytes_per_second");
    const auto& timeouts=input.at("timeouts_seconds");fields(timeouts,{"handshake","idle","message","close"});
    const auto timeout=[&](const char* name){using Rep=std::chrono::seconds::rep;
        return std::chrono::seconds(static_cast<Rep>(number(timeouts.at(name),std::numeric_limits<Rep>::max())));};
    p.handshake_timeout=timeout("handshake");p.idle_timeout=timeout("idle");
    p.message_timeout=timeout("message");p.close_timeout=timeout("close");
    const auto& routes=input.at("routes");need(routes.is_array(),"Web route roles array required");
    for(const auto& role:routes) {
        const auto name=text(role);
        if(name=="tw_account")result.routes.push_back({WebServerPlan::Role::TwAccount});
        else if(name=="tw_world")result.routes.push_back({WebServerPlan::Role::TwWorld});
        else throw std::invalid_argument("Web route role invalid; native destinations and arbitrary paths are forbidden");
    }
    result.validate();return result; // Shared pure policy/role checks; never binds.
}
WebServerPlan WebServerPlanConfig::load(const std::filesystem::path& path) {
    need(!path.empty()&&path.native().find(std::filesystem::path::value_type(0))==std::filesystem::path::string_type::npos,
        "Web configuration path invalid");
    std::ifstream input(path,std::ios::binary|std::ios::ate);
    need(bool(input),"Cannot open explicit Web configuration");const auto size=input.tellg();
    need(size>0&&size<=static_cast<std::streamoff>(max_file_bytes),"Web configuration exceeds CUSTOM64KiB host-input budget");
    std::string bytes(static_cast<std::size_t>(size),'\0');input.seekg(0);
    input.read(bytes.data(),static_cast<std::streamsize>(bytes.size()));
    need(bool(input)&&input.peek()==std::char_traits<char>::eof(),"Web configuration changed during bounded read");
    std::vector<std::set<std::string>> keys;
    const auto callback=[&](int depth,J::parse_event_t event,J& parsed) {
        // CUSTOM parser-work bound, not a native JSON/gameplay depth rule.
        need(depth<=32,"Web configuration exceeds CUSTOM nesting budget");
        if(event==J::parse_event_t::object_start)keys.emplace_back();
        else if(event==J::parse_event_t::object_end){need(!keys.empty(),"Web configuration object stack invalid");keys.pop_back();}
        else if(event==J::parse_event_t::key)
            need(!keys.empty()&&keys.back().insert(parsed.get<std::string>()).second,"Web configuration duplicate key");
        return true;
    };
    return from_json(J::parse(bytes,callback));
}
}
