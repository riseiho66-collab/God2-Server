#include "core/WebMainOptions.h"
#include "core/Config.h"
#include "net/WebServerPlanConfig.h"
#include <nlohmann/json.hpp>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <limits>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

// SOURCE regression only: no Application, listener, native authentication,
// database, migration or server is started by this standalone fixture.
namespace {
using god2::WebMainOptions;
using god2::WebServerPlanConfig;
using J=nlohmann::json;
using A=WebMainOptions::Argument;
namespace fs=std::filesystem;
void need(bool value){if(!value)throw std::runtime_error("web_main_options source regression");}
template<class F>void rejects(F&& operation) {
    bool rejected=false;try{operation();}catch(const std::exception&){rejected=true;}
    need(rejected);
}
A arg(std::string_view text) {A result;for(const auto c:text)result.push_back(static_cast<A::value_type>(c));return result;}
std::vector<A> args(std::initializer_list<std::string_view> values) {
    std::vector<A> result;for(const auto text:values)result.push_back(arg(text));return result;
}
J supplied_plan() {
    // Explicit synthetic host policy; these values are not native rules or
    // evidence that the application owns an Account/G listener at any port.
    return {{"version",1},{"listen",{{"address","127.0.0.1"},{"port",0}}},
        {"origins",J::array({"http://localhost:8080"})},
        {"limits",{{"max_sessions",4},{"sessions_per_address",2},{"accepts_per_second",10},
            {"message_bytes",65536},{"queue_bytes",65546},{"queue_frames",16},
            {"frames_per_second",100},{"bytes_per_second",1048576}}},
        {"timeouts_seconds",{{"handshake",5},{"idle",60},{"message",5},{"close",2}}},
        {"routes",J::array({"tw_account","tw_world"})}};
}
class Fixture {
public:
    Fixture() {
        const auto temp=fs::canonical(fs::temp_directory_path());std::random_device random;
        for(unsigned attempt=0;attempt<100;++attempt) {
            const auto candidate=temp/("god2-web-options-"+std::to_string(random())+"-"+
                std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
            if(fs::create_directory(candidate)){root_=candidate;return;}
        }
        throw std::runtime_error("cannot create Web options fixture");
    }
    ~Fixture(){std::error_code ignored;fs::remove_all(root_,ignored);}
    Fixture(const Fixture&)=delete;Fixture& operator=(const Fixture&)=delete;
    fs::path file()const{return root_/fs::path(u8"明確網頁設定.json");}
    fs::path absent()const{return root_/"absent.json";}
    void write(const std::string& bytes)const {
        std::ofstream out(file(),std::ios::binary|std::ios::trunc);
        if(!out)throw std::runtime_error("cannot open Web options fixture");
        out.write(bytes.data(),static_cast<std::streamsize>(bytes.size()));out.close();
        if(!out)throw std::runtime_error("cannot write Web options fixture");
    }
private:fs::path root_;
};
void command_line_cases() {
    need(!WebMainOptions::parse(args({"server","--help"})));
    need(!WebMainOptions::parse(args({"server","--config","--web-config"})));
    need(!WebMainOptions::parse(args({"server","--manifest","--web-config"})));
    need(!WebMainOptions::parse(args({"server","--run-for","--web-config"})));
    char program[]="server",help_flag[]="--help";char* native_no_optin[]={program,help_flag};
    need(!WebMainOptions::parse_if_requested(2,native_no_optin)); // No Windows argv acquisition.
    rejects([]{WebMainOptions::parse(std::span<const A>{});});
    const auto ordinary=args({"server","--web-config","web.json","--config","server.json","--run-for","0"});
    const auto parsed=WebMainOptions::parse(ordinary);
    need(parsed&&parsed->web_config_path==fs::path("web.json")&&
        parsed->config_path==fs::path("server.json")&&parsed->run_for_seconds==0&&!parsed->help);
    auto unicode=ordinary;unicode[2]=fs::path(u8"資料夾/網頁.json").native();
    unicode[4]=fs::path(u8"資料夾/服務端.json").native();
    const auto retained=WebMainOptions::parse(unicode);
    need(retained&&retained->web_config_path.native()==unicode[2]&&retained->config_path.native()==unicode[4]);
    const auto help=WebMainOptions::parse(args({"server","--help","--web-config","does-not-exist.json"}));
    need(help&&help->help); // Pure parse; nonexistent paths were not opened.
    std::ostringstream out;WebMainOptions::write_help(out);need(out.str().find("--web-config")!=std::string::npos);
    for(const auto flag:{"--migrate-only","--native-delivery-schema","--owned-equipment-schema",
        "--owned-blacklist-schema","--import-tw-installed-skills","--provision-owned-bank-capacity",
        "--export-owned-bank-capacity","--unknown","--manifest","--output","--tw-client-root"}) {
        // Give offline value flags actual data so the opt-in token is not
        // itself consumed as that flag's filename during mode classification.
        rejects([&]{WebMainOptions::parse(args({"server",flag,"operator-value","--web-config","web.json"}));});
        rejects([&]{WebMainOptions::parse(args({"server","--web-config","web.json",flag,"operator-value"}));});
    }
    for(const auto flag:{"--config","--web-config","--run-for","--help"}) {
        auto duplicate=args({"server","--web-config","web.json",flag});
        if(std::string_view(flag)!="--help")duplicate.push_back(arg("1"));
        if(std::string_view(flag)!="--web-config") {
            duplicate.push_back(arg(flag));if(std::string_view(flag)!="--help")duplicate.push_back(arg("1"));
        }
        rejects([&]{WebMainOptions::parse(duplicate);});
    }
    for(const auto value:{"","-1","+1","1.5","1x","4294967296","18446744073709551616"})
        rejects([&]{WebMainOptions::parse(args({"server","--web-config","web.json","--run-for",value}));});
    const auto positive=WebMainOptions::parse(args({"server","--web-config","web.json","--run-for","10"}));
    need(positive&&positive->run_for_seconds==10);
    rejects([]{WebMainOptions::parse(args({"server","--web-config"}));});
    rejects([]{WebMainOptions::parse(args({"server","--web-config",""}));});
    rejects([]{WebMainOptions::parse(args({"server","--web-config","--help"}));});
    auto nul=ordinary;nul[2].push_back(0);nul[2]+=arg("tail");
    rejects([&]{WebMainOptions::parse(nul);});
}
void plan_cases() {
    const auto valid=supplied_plan();const auto plan=WebServerPlanConfig::from_json(valid);
    need(plan.policy.listen.address().is_loopback()&&plan.policy.listen.port()==0&&plan.routes.size()==2);
    auto ipv6=valid;ipv6["listen"]["address"]="::1";ipv6["listen"]["port"]=65535;
    need(WebServerPlanConfig::from_json(ipv6).policy.listen.port()==65535);
    for(const auto key:{"version","listen","origins","limits","timeouts_seconds","routes"}) {
        auto missing=valid;missing.erase(key);rejects([&]{WebServerPlanConfig::from_json(missing);});
    }
    auto unknown=valid;unknown["native_endpoint"]="127.0.0.1:1";
    rejects([&]{WebServerPlanConfig::from_json(unknown);});
    for(const auto object:{"listen","limits","timeouts_seconds"}) {
        auto bad=valid;bad[object]["unknown"]=1;rejects([&]{WebServerPlanConfig::from_json(bad);});
        bad=valid;bad[object].erase(bad[object].begin());rejects([&]{WebServerPlanConfig::from_json(bad);});
    }
    for(const J bad:{J(),J(true),J(1.0),J(-1),J("1"),J(std::numeric_limits<std::uint64_t>::max())}) {
        auto changed=valid;changed["listen"]["port"]=bad;rejects([&]{WebServerPlanConfig::from_json(changed);});
        changed=valid;changed["version"]=bad;rejects([&]{WebServerPlanConfig::from_json(changed);});
        changed=valid;changed["timeouts_seconds"]["handshake"]=bad;
        rejects([&]{WebServerPlanConfig::from_json(changed);});
    }
    for(const auto address:{"localhost","0.0.0.0","192.0.2.1","::"}) {
        auto changed=valid;changed["listen"]["address"]=address;
        rejects([&]{WebServerPlanConfig::from_json(changed);});
    }
    for(const auto role:{"/tw/native","http://localhost:1","cn_world","tw_world/0"}) {
        auto changed=valid;changed["routes"]=J::array({role});rejects([&]{WebServerPlanConfig::from_json(changed);});
    }
    for(const J roles:{J::array(),J::array({"tw_world","tw_world"}),J::array({1}),J("tw_account")}) {
        auto changed=valid;changed["routes"]=roles;rejects([&]{WebServerPlanConfig::from_json(changed);});
    }
    for(const auto key:{"max_sessions","sessions_per_address","accepts_per_second","message_bytes",
        "queue_bytes","queue_frames","frames_per_second","bytes_per_second"}) {
        for(const J value:{J(0),J(true),J(-1),J(1.5),J("1")}) {
            auto changed=valid;changed["limits"][key]=value;rejects([&]{WebServerPlanConfig::from_json(changed);});
        }
    }
    for(const auto key:{"handshake","idle","message","close"}) {
        auto changed=valid;changed["timeouts_seconds"][key]=0;rejects([&]{WebServerPlanConfig::from_json(changed);});
    }
    for(const J origins:{J::array(),J::array({"*"}),J::array({"http://localhost:8080","http://localhost:8080"}),
        J::array({"http://localhost\r\nx"}),J::array({nullptr}),J("http://localhost:8080")}) {
        auto changed=valid;changed["origins"]=origins;rejects([&]{WebServerPlanConfig::from_json(changed);});
    }
    auto changed=valid;changed["limits"]["message_bytes"]=16*1024*1024+1;
    rejects([&]{WebServerPlanConfig::from_json(changed);});
    changed=valid;changed["limits"]["queue_bytes"]=65545;
    rejects([&]{WebServerPlanConfig::from_json(changed);});
    changed=valid;changed["origins"][0]=std::string("http://localhost\0tail",21);
    rejects([&]{WebServerPlanConfig::from_json(changed);});
    changed=valid;changed["listen"]["port"]=65536;
    rejects([&]{WebServerPlanConfig::from_json(changed);});
    changed=valid;changed["timeouts_seconds"]["idle"]=std::numeric_limits<std::int64_t>::max();
    rejects([&]{WebServerPlanConfig::from_json(changed);}); // Shared steady-clock representability.
    god2::Config config;config.protocol_mode=god2::ProtocolMode::God2LegacyCharacterListCandidate;
    config.recovered_account_auth=true;config.recovered_dual_connection=true;config.mock_login=false;
    god2::validate_web_main_host(config,plan);
    config.recovered_dual_connection=false;rejects([&]{god2::validate_web_main_host(config,plan);});
    changed=valid;changed["routes"]=J::array({"tw_account"});
    const auto account=WebServerPlanConfig::from_json(changed);god2::validate_web_main_host(config,account);
    config.mock_login=true;rejects([&]{god2::validate_web_main_host(config,account);});config.mock_login=false;
    config.recovered_account_auth=false;rejects([&]{god2::validate_web_main_host(config,account);});
    config.recovered_account_auth=true;
    for(const auto mode:{god2::ProtocolMode::Fixture,god2::ProtocolMode::God2CharacterConnection}) {
        config.protocol_mode=mode;rejects([&]{god2::validate_web_main_host(config,account);});
    }
}
void bounded_file_cases() {
    const auto valid=supplied_plan().dump();Fixture fixture;fixture.write(valid);
    need(WebServerPlanConfig::load(fixture.file()).routes.size()==2);
    rejects([&]{WebServerPlanConfig::load(fixture.absent());});
    rejects([]{WebServerPlanConfig::load({});});
    auto nul=fixture.file().native();nul.push_back(0);nul+=arg("tail");
    rejects([&]{WebServerPlanConfig::load(fs::path(nul));});
    fixture.write("");rejects([&]{WebServerPlanConfig::load(fixture.file());});
    fixture.write(valid+std::string(WebServerPlanConfig::max_file_bytes+1-valid.size(),' '));
    rejects([&]{WebServerPlanConfig::load(fixture.file());});
    // Raw file path is necessary: an already parsed json object cannot retain
    // duplicate keys. Both root and nested duplicates must reject during load.
    fixture.write("{\"version\":1,"+valid.substr(1));
    rejects([&]{WebServerPlanConfig::load(fixture.file());});
    auto nested=valid;const auto at=nested.find("\"port\":0");need(at!=std::string::npos);
    nested.replace(at,8,"\"port\":0,\"port\":0");fixture.write(nested);
    rejects([&]{WebServerPlanConfig::load(fixture.file());});
    fixture.write("{}");rejects([&]{WebServerPlanConfig::load(fixture.file());});
    fixture.write(valid+" trailing");rejects([&]{WebServerPlanConfig::load(fixture.file());});
    fixture.write(std::string(40,'[')+"0"+std::string(40,']'));
    rejects([&]{WebServerPlanConfig::load(fixture.file());}); // CUSTOM parsing depth, before schema checks.
    fixture.write(valid+std::string(WebServerPlanConfig::max_file_bytes-valid.size(),' '));
    need(WebServerPlanConfig::load(fixture.file()).routes.size()==2); // Exact CUSTOM bound.
}
}
int main(){command_line_cases();plan_cases();bounded_file_cases();}
