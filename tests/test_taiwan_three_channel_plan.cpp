#include "core/TaiwanThreeChannelPlan.h"
#include <array>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>

namespace {
using namespace god2;
using Plan=TaiwanThreeChannelPlan;
using Handoff=SharedTaiwanCharacterListHandoff;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class F> bool refuses(F&& call){try{call();}catch(const std::invalid_argument&){return true;}return false;}
[[noreturn]] void unprovided(){throw std::runtime_error("Plan validation invoked an unprovided gameplay authority");}

// Same actual immutable, plain config.ini reader as the channel-server tests.
// No database, executor, listener or native world plan is constructed here.
struct ConfigurationFiles {
    const std::filesystem::path root=std::filesystem::temp_directory_path()/
        ("g2-three-plan491-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    ConfigurationFiles(){
        require(std::filesystem::create_directory(root),"Unique plan configuration directory unavailable");
        try{require(std::filesystem::create_directory(root/"Data3"),"Plan Data3 directory unavailable");}
        catch(...){std::error_code ignored;std::filesystem::remove_all(root,ignored);throw;}
    }
    ~ConfigurationFiles(){std::error_code ignored;std::filesystem::remove_all(root,ignored);}
    std::shared_ptr<const TaiwanNativeClientGroupConfiguration> read(std::initializer_list<unsigned> counts){
        {
            std::ofstream stream(root/"Data3"/"config.ini",std::ios::binary|std::ios::trunc);
            unsigned group=0;
            for(const auto count:counts){
                stream<<"[Synthetic"<<group++<<"]\n";
                for(unsigned slot=0;slot<count;++slot)stream<<"Channel"<<slot<<"=127.0.0.1\n";
            }
            require(bool(stream),"Complete plain plan configuration write failed");
        }
        return TaiwanNativeClientGroupConfiguration::read(root,{"127.0.0.1",0,0},4096,4096);
    }
};
struct Calls {unsigned live=0,authority=0,factory=0;};
struct Arguments {
    std::shared_ptr<const TaiwanNativeClientGroupConfiguration> configuration;
    std::uint8_t group=0,group_byte_1=0x92;
    std::array<TaiwanChannelServers::EndpointPolicy,3> endpoints{{
        {{127,0,0,1},0,0x71,{0x11,0xa1,0xb1,0xc1}},
        {{127,0,0,1},0,0x82,{0x83,0xa2,0xb2,0xc2}},
        {{127,0,0,1},0,0x93,{0xfe,0xa3,0xb3,0xc3}}
    }};
    // Exact existing configuration/handoff identity, not binary attestation
    // or callback authority. No current-build alias is accepted by the plan.
    std::string client_sha256{TaiwanNativeClientGroupConfiguration::client_sha256};
    std::size_t capacity=4;
    Handoff::Live live;
    Handoff::Authority authority;
    Plan::Factory factory;
    Arguments(std::shared_ptr<const TaiwanNativeClientGroupConfiguration> source,const std::shared_ptr<Calls>& calls)
        :configuration(std::move(source)),
         live([calls](const Handoff::Source::Issued&,const Handoff::Auth&)->bool{++calls->live;unprovided();}),
         authority([calls](Session&,const Handoff::Source::Scope&,const Handoff::Source::Issued&,
             const Handoff::Auth&,const Handoff::Auth&)->std::optional<Handoff::DestinationAuthority>{
                 ++calls->authority;unprovided();}),
         factory([calls](const Plan::Context&)->Plan::WorldPlans{++calls->factory;unprovided();}){}
    Plan make()const{return {configuration,group,group_byte_1,endpoints,client_sha256,capacity,live,authority,factory};}
};
void untouched(const std::shared_ptr<Calls>& calls){
    require(!calls->live&&!calls->authority&&!calls->factory,"Passive plan validation invoked a source/factory");
}

void actual_configuration_and_passive_validation(){
    ConfigurationFiles files;const auto calls=std::make_shared<Calls>();
    const auto configured=files.read({3});Arguments input(configured,calls);
    const auto plan=input.make();plan.validate();
    require(plan.configuration==configured&&plan.group==input.group&&plan.group_byte_1==input.group_byte_1&&
        plan.client_sha256==input.client_sha256&&plan.handoff_capacity==input.capacity,
        "Passive plan changed its explicit source/group/hash/capacity");
    for(std::size_t k=0;k<3;++k)require(plan.endpoints[k].address==input.endpoints[k].address&&
        plan.endpoints[k].port==0&&plan.endpoints[k].status==input.endpoints[k].status&&
        plan.endpoints[k].route_body==input.endpoints[k].route_body,
        "Plan rewrote pending kernel-assigned endpoint or opaque native bytes");
    // Replacing the file must not change the actual earlier immutable input.
    const auto replacement=files.read({4});
    require(configured->configured_slots(0)==std::optional<std::uint8_t>{3}&&
        replacement->configured_slots(0)==std::optional<std::uint8_t>{4},"Configuration snapshot was not immutable");
    plan.validate();
    for(const unsigned count:{0u,1u,2u,4u,10u}){
        auto bad=input;bad.configuration=files.read({count});
        require(refuses([&]{(void)bad.make();}),"Plan accepted a configured count other than exactly three");
    }
    auto absent=input;absent.configuration.reset();
    require(refuses([&]{(void)absent.make();}),"Plan accepted absent immutable configuration");
    auto selected=input;selected.configuration=files.read({2,3});selected.group=1;
    (void)selected.make();selected.group=0;
    require(refuses([&]{(void)selected.make();}),"Plan ignored the selected group's actual slot count");
    selected.group=2;
    require(refuses([&]{(void)selected.make();}),"Plan accepted an unconfigured group");
    selected.configuration=files.read({0,0,0,0,0,0,0,0,0,3,3});selected.group=9;
    (void)selected.make();selected.group=10;
    require(refuses([&]{(void)selected.make();}),"Plan accepted a physical group outside native visible0..9");
    selected.group=255;
    require(refuses([&]{(void)selected.make();}),"Plan accepted an out-of-range group byte");
    untouched(calls);
}

void missing_sources_and_hash_identity(){
    ConfigurationFiles files;const auto calls=std::make_shared<Calls>();Arguments input(files.read({3}),calls);
    auto bad=input;bad.capacity=0;
    require(refuses([&]{(void)bad.make();}),"Plan accepted zero handoff capacity");
    bad=input;bad.live={};
    require(refuses([&]{(void)bad.make();}),"Plan accepted absent actual live predicate");
    bad=input;bad.authority={};
    require(refuses([&]{(void)bad.make();}),"Plan accepted absent destination authority supplier");
    bad=input;bad.factory={};
    require(refuses([&]{(void)bad.make();}),"Plan accepted absent fresh world-plan factory");
    for(const auto& hash:std::array<std::string,3>{"",std::string(63,'a'),std::string(65,'a')}){
        bad=input;bad.client_sha256=hash;
        require(refuses([&]{(void)bad.make();}),"Plan accepted wrong SHA256 spelling length");
    }
    for(const char byte:{'A','g',' ', '\0'}){
        bad=input;bad.client_sha256[31]=byte;
        require(refuses([&]{(void)bad.make();}),"Plan accepted a non-lowercase-hex SHA256 byte");
    }
    // These spell valid SHA256 values. Old spelling-only validation passed
    // them, then actual Handoff::create rejected only after Application DB
    // initialization/migrations. No callback should run to discover mismatch.
    for(const auto& hash:std::array<std::string,2>{std::string(64,'0'),
        "aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48"}) {
        bad=input;bad.client_sha256=hash;
        require(refuses([&]{(void)bad.make();}),"Plan accepted a different valid-hex native build");
        auto changed=input.make();changed.client_sha256=hash;
        require(refuses([&]{changed.validate();}),"Plan revalidation accepted a replaced native build");
        untouched(calls);
    }
    auto revalidated=input.make();revalidated.live={};
    require(refuses([&]{revalidated.validate();}),"Revalidation accepted a removed live predicate");
    untouched(calls);
}

void endpoint_identity_and_loopback(){
    ConfigurationFiles files;const auto calls=std::make_shared<Calls>();Arguments input(files.read({3}),calls);
    // Port0 is an explicit later kernel allocation, not three aliases of port0.
    (void)input.make();
    for(std::size_t k=0;k<3;++k){
        auto bad=input;bad.endpoints[k].route_body[0]=0;
        require(refuses([&]{(void)bad.make();}),"Plan accepted a missing native route key");
        for(const std::uint8_t first:{std::uint8_t{0},std::uint8_t{10},std::uint8_t{126},std::uint8_t{128},std::uint8_t{192}}){
            bad=input;bad.endpoints[k].address={first,0,0,1};
            require(refuses([&]{(void)bad.make();}),"Plan accepted a nonloopback endpoint");
        }
    }
    auto explicit_ports=input;
    for(std::size_t k=0;k<3;++k)explicit_ports.endpoints[k].port=static_cast<std::uint16_t>(2592+k);
    (void)explicit_ports.make();
    for(std::size_t k=1;k<3;++k)for(std::size_t j=0;j<k;++j){
        auto bad=explicit_ports;bad.endpoints[k].port=bad.endpoints[j].port;
        require(refuses([&]{(void)bad.make();}),"Plan accepted aliased nonzero address/port endpoints");
    }
    // Loopback is127/8; equal ports on distinct explicit addresses do not alias.
    auto distinct_addresses=explicit_ports;
    distinct_addresses.endpoints[1].address={127,0,0,2};
    distinct_addresses.endpoints[1].port=distinct_addresses.endpoints[0].port;
    distinct_addresses.endpoints[2].address={127,42,3,4};
    (void)distinct_addresses.make();
    auto opaque=input;opaque.group_byte_1=0xff;opaque.endpoints[0].status=0;
    opaque.endpoints[1].status=0xff;opaque.endpoints[2].route_body={1,0,0,0};
    (void)opaque.make(); // No invented bounds on opaque native status/tail bytes.
    auto revalidated=input.make();revalidated.endpoints[2].address={192,168,1,1};
    require(refuses([&]{revalidated.validate();}),"Revalidation accepted a changed nonloopback endpoint");
    untouched(calls);
}

void game_owned_startup_recipe(){
    ConfigurationFiles files;const auto calls=std::make_shared<Calls>();Arguments input(files.read({3}),calls);
    Plan::StartupFactory startup=[calls](const Plan::StartupContext&)->Plan::StartupSources {
        ++calls->factory;unprovided();
    };
    Plan plan(input.configuration,input.group,input.group_byte_1,input.endpoints,input.client_sha256,input.capacity,startup);
    plan.validate();untouched(calls);
    auto mixed=plan;mixed.live=input.live;
    require(refuses([&]{mixed.validate();}),"Startup recipe mixed with direct live callback");
    mixed=plan;mixed.authority=input.authority;
    require(refuses([&]{mixed.validate();}),"Startup recipe mixed with direct authority callback");
    mixed=plan;mixed.make_world_plans=input.factory;
    require(refuses([&]{mixed.validate();}),"Startup recipe mixed with direct world factory");
    auto absent=plan;absent.startup_sources={};
    require(refuses([&]{absent.validate();}),"Removed startup factory accepted without direct sources");
    require(refuses([&]{Plan::StartupSources{}.validate();}),"Empty runtime startup accepted");
    Plan::StartupSources complete{input.live,input.authority,input.factory};complete.validate();
    complete.live={};require(refuses([&]{complete.validate();}),"Incomplete runtime authority accepted");
    complete={input.live,input.authority,input.factory};complete.authority={};
    require(refuses([&]{complete.validate();}),"Incomplete runtime destination source accepted");
    complete={input.live,input.authority,input.factory};complete.make_world_plans={};
    require(refuses([&]{complete.validate();}),"Incomplete runtime worlds accepted");
    untouched(calls); // No startup DB/executor or gameplay factory was accessed.
}
} // namespace

void test_taiwan_three_channel_plan(){
    actual_configuration_and_passive_validation();missing_sources_and_hash_identity();endpoint_identity_and_loopback();game_owned_startup_recipe();
}
