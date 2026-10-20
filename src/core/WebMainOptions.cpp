#include "core/WebMainOptions.h"
#include "core/Config.h"
#include "net/WebServerPlan.h"
#include <charconv>
#include <ostream>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>
#ifdef _WIN32
#include <windows.h>
#include <shellapi.h>
#endif
namespace god2 { namespace {
template<class Text>bool option(const Text& value,std::string_view expected) noexcept {
    if(value.size()!=expected.size())return false;
    for(std::size_t i=0;i<value.size();++i)
        if(value[i]!=static_cast<typename Text::value_type>(expected[i]))return false;
    return true;
}
template<class Text>bool takes_value(const Text& value) noexcept {
    return option(value,"--config")||option(value,"--web-config")||option(value,"--run-for")||
        option(value,"--tw-client-root")||option(value,"--manifest")||option(value,"--output")||
        option(value,"--account-id")||option(value,"--character-id");
}
template<class Args>bool requested(const Args& args) {
    for(std::size_t i=1;i<args.size();++i) {
        if(option(args[i],"--web-config"))return true;
        // An existing option's filename is data, even if it spells a flag.
        if(takes_value(args[i])&&i+1<args.size())++i;
    }
    return false;
}
std::string ascii(const WebMainOptions::Argument& value) {
    std::string out;out.reserve(value.size());
    for(const auto c:value){if(c<0||c>127)return {};out.push_back(static_cast<char>(c));}
    return out;
}
std::vector<WebMainOptions::Argument> native_arguments(int argc,char** argv) {
#ifdef _WIN32
    int count=0;struct End {LPWSTR* data=nullptr;~End(){if(data)LocalFree(data);}} end;
    end.data=CommandLineToArgvW(GetCommandLineW(),&count);
    if(!end.data||count!=argc)throw std::invalid_argument("Cannot retain actual Windows Web arguments");
    return {end.data,end.data+count};
#else
    return {argv,argv+argc};
#endif
}
}
std::optional<WebMainOptions> WebMainOptions::parse(std::span<const Argument> args) {
    if(args.empty())throw std::invalid_argument("Web arguments require the program name");
    if(!requested(args))return std::nullopt;
    WebMainOptions result;std::set<std::string> seen;
    for(std::size_t i=1;i<args.size();++i) {
        const auto name=ascii(args[i]);
        if(name.empty()||name.find('\0')!=std::string::npos||!seen.insert(name).second)
            throw std::invalid_argument("Invalid or duplicate Web option");
        if(name=="--help"){result.help=true;continue;}
        if(name!="--config"&&name!="--web-config"&&name!="--run-for")
            throw std::invalid_argument("Web hosting is exclusive with migration, schema, import, capacity and unknown options");
        if(++i>=args.size()||args[i].empty()||
           (args[i].size()>=2&&args[i][0]=='-'&&args[i][1]=='-')||
           args[i].find(Argument::value_type(0))!=Argument::npos)
            throw std::invalid_argument("Web option requires an explicit value");
        if(name=="--run-for") {
            const auto value=ascii(args[i]);
            const auto parsed=std::from_chars(value.data(),value.data()+value.size(),result.run_for_seconds);
            if(value.empty()||parsed.ec!=std::errc{}||parsed.ptr!=value.data()+value.size())
                throw std::invalid_argument("Web --run-for requires an unsigned integer number of seconds");
        }else if(name=="--config")result.config_path=std::filesystem::path(args[i]);
        else result.web_config_path=std::filesystem::path(args[i]);
    }
    if(result.web_config_path.empty())throw std::invalid_argument("Web hosting requires --web-config path");
    return result;
}
std::optional<WebMainOptions> WebMainOptions::parse_if_requested(int argc,char** argv) {
    if(argc<1||!argv)throw std::invalid_argument("Invalid Web process arguments");
    std::vector<std::string_view> raw;raw.reserve(static_cast<std::size_t>(argc));
    for(int i=0;i<argc;++i){if(!argv[i])throw std::invalid_argument("Invalid Web process argument");raw.emplace_back(argv[i]);}
    if(!requested(raw))return std::nullopt; // Ordinary native Main remains unchanged.
    const auto args=native_arguments(argc,argv);return parse(args);
}
void WebMainOptions::write_help(std::ostream& out) {
    out<<"--web-config <explicit Web JSON> [--config config/server.json] [--run-for seconds] [--help]\n"
        "  Opt-in loopback WebSocket host over Application-owned native Account/single-G listeners.\n"
        "  Requires explicit origins, all budgets/timeouts and fixed TW route roles; no native destinations or guessed ports.\n"
        "  Exclusive with migration/schema/import/capacity modes. Help reads no files.\n"
        "  Normal startup DB initialization/migrations remain the existing Application behavior.\n"
        "  No three-world provider is manufactured; source hosting is not client/runtime acceptance.\n";
}
void validate_web_main_host(const Config& config,const WebServerPlan& plan) {
    plan.validate();
    if(!config.recovered_account_auth||!is_credential_mode(config.protocol_mode)||
       config.protocol_mode==ProtocolMode::God2CharacterConnection||config.mock_login)
        throw std::invalid_argument("Main Web host requires actual native Account authentication");
    for(const auto& route:plan.routes)if(route.role==WebServerPlan::Role::TwWorld&&!config.recovered_dual_connection)
        throw std::invalid_argument("Main Web world role requires the actual single-G listener");
}
}
