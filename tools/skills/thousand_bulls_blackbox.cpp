// CUSTOM-0059. Standalone TCP fixture, NOT full Application/database/native UI acceptance.
// RecoveredSessionPeer is bounded from tests/test_session_state.cpp. Real Session
// seed/login/select/world framing is used with synthetic account admission.
#include "protocol/OpcodeDispatcher.h"
#include "net/Session.h"
#include "handlers/RecoveredWorldService.h"
#include "handlers/RecoveredVisibility.h"
#include "handlers/RecoveredPlayerPresence.h"
#include "protocol/DiagnosticRemoteActor.h"
#include "handlers/RecoveredBattleService.h"
#include "scripting/LuaEngine.h"
#include "protocol/RecoveredSeedExchange.h"
#include "protocol/RecoveredPostSeed.h"
#include "protocol/RecoveredCharacterBootstrap.h"
#include "protocol/RecoveredCharacterCreateResult.h"
#include "protocol/RecoveredWorldStateCandidate.h"
#include <algorithm>
#include <chrono>
#include <stdexcept>
#include <string>
#include <fstream>
#include <charconv>
#include <nlohmann/json.hpp>
#include "game/ThousandBulls.h"
#include "protocol/ThousandBullsReply.h"
#include <iostream>

namespace {
using namespace god2;
void require(bool value,const char* message) { if(!value) throw std::runtime_error(message); }

// Synthetic peer and handlers exercise the real Session socket/state machine.
// Test identities/coordinates are not recovered character attributes.
struct RecoveredSessionPeer {
    using WorldHandler=std::function<std::optional<std::vector<std::uint8_t>>(
        Session&,std::span<const RecoveredWorldRecords::Record>)>;
    asio::io_context io;
    asio::ip::tcp::acceptor acceptor{io,{asio::ip::address_v4::loopback(),0}};
    asio::ip::tcp::socket peer{io};
    std::shared_ptr<Session> session;
    unsigned ready_calls=0,movement_calls=0,selection_calls=0,world_calls=0;
    std::vector<std::uint8_t> last_wire;
    static constexpr std::uint64_t account=7,character=0x1234;
    std::uint64_t selected_character=character;
    RecoveredWorldEntry::Frame world_frame;

    explicit RecoveredSessionPeer(bool movement,WorldHandler world={},
        std::uint64_t selected=character,std::uint64_t session_id=2):selected_character(selected),
        world_frame(RecoveredWorldEntry::wire(selected)) {
        peer.connect(acceptor.local_endpoint());
        auto socket=acceptor.accept();
        Session::RecoveredCharacterHandlers handlers;
        handlers.list=[](std::uint64_t) { return std::array<std::uint8_t,78>{}; };
        handlers.create=[this](std::uint64_t owner,const RecoveredCharacterCreate& request) {
            require(owner==account && request.payload[0]=='T',"Create lost account/profile");
            return selected_character;
        };
        handlers.select_existing=[this](std::uint64_t owner,std::uint8_t token) {
            require(owner==account && token==0,"Selection lost account/token");
            ++selection_calls;return selected_character;
        };
        handlers.select_created=[this](std::uint64_t owner,std::uint64_t id,std::uint8_t token) {
            require(owner==account && id==selected_character && token==0,"Created selection lost ownership");
            ++selection_calls;return selected_character;
        };
        handlers.created_slot=[this](std::uint64_t owner,std::uint64_t id) -> std::uint8_t {
            require(owner==account && id==selected_character,"Slot lookup lost committed ownership");
            return 0;
        };
        handlers.world_entry=[this](std::uint64_t,std::uint64_t owner,std::uint64_t id) {
            require(owner==account && id==selected_character,"World entry lost ownership");
            return world_frame;
        };
        if(movement || world) {
            handlers.world_ready=[this](Session& s) {
                require(s.account_id==account && s.character_id==selected_character,"World-ready lost binding");
                ++ready_calls;
            };
        }
        if(movement) {
            handlers.movement=[this](Session& s,std::span<const RecoveredMovement::Request> requests) {
                require(ready_calls==1 && s.character_id==selected_character,"Movement preceded world-ready");
                require(requests.size()==1 && requests[0].x==18 && requests[0].y==14 &&
                        requests[0].sequence==3,"Movement request changed");
                ++movement_calls;
                const auto ack=RecoveredMovement::ack(requests[0].sequence);
                return std::vector<std::uint8_t>(ack.begin(),ack.end());
            };
        }
        if(world) {
            handlers.world_records=[this,world=std::move(world)](
                    Session& s,std::span<const RecoveredWorldRecords::Record> records) {
                require(ready_calls==1 && s.account_id==account && s.character_id==selected_character,
                        "World records preceded authenticated character/world binding");
                ++world_calls;
                return world(s,records);
            };
        }
        session=std::make_shared<Session>(std::move(socket),io.get_executor(),session_id,false,
            Session::PacketHandler{},Session::DisconnectHandler{},ProtocolMode::God2CharacterConnection,
            [](const RecoveredC2S0002::Parsed& request) {
                require(request.logical[0]==0,"Character connection login opcode changed");
                return account;
            },std::move(handlers));
        peer.non_blocking(true);
        session->start();
    }
    ~RecoveredSessionPeer() {
        asio::error_code ignored;
        peer.close(ignored);
        session->close();
        io.restart();io.run_for(std::chrono::milliseconds(20));
    }
    void pump() { io.restart();io.run_for(std::chrono::milliseconds(5)); }
    void send(std::span<const std::uint8_t> bytes) {
        // These bounded test frames fit the loopback send buffer.
        peer.non_blocking(false);
        asio::write(peer,asio::buffer(bytes.data(),bytes.size()));
        peer.non_blocking(true);
    }
    void expect(std::span<const std::uint8_t> expected) {
        std::vector<std::uint8_t> actual(expected.size());
        std::size_t received=0;
        const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(2);
        while(received<actual.size() && std::chrono::steady_clock::now()<deadline) {
            pump();
            asio::error_code error;
            received+=peer.read_some(asio::buffer(actual.data()+received,actual.size()-received),error);
            require(!error || error==asio::error::would_block || error==asio::error::try_again,
                    "Session closed before expected reply");
        }
        require(received==expected.size() && std::equal(actual.begin(),actual.end(),expected.begin()),
                "Recovered session deterministic reply changed");
        last_wire=actual;
    }
    void silent() {
        // Pump both executors before checking: queued writes must get a chance to run.
        for(unsigned i=0;i<10;++i) {
            pump();
            std::array<std::uint8_t,256> bytes{};
            asio::error_code error;
            const auto count=peer.read_some(asio::buffer(bytes),error);
            require(count==0 && (error==asio::error::would_block || error==asio::error::try_again),
                    "Recovered session injected unsolicited bytes or closed");
        }
    }
    void closed() {
        const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(2);
        while(session->state()!=SessionState::Disconnected && std::chrono::steady_clock::now()<deadline) pump();
        require(session->state()==SessionState::Disconnected,"Invalid/repeated tail did not fail closed");
        std::array<std::uint8_t,256> bytes{};
        asio::error_code error;
        const auto count=peer.read_some(asio::buffer(bytes),error);
        require(count==0 && (error==asio::error::eof || error==asio::error::connection_reset),
                "Rejected tail emitted unsolicited bytes");
    }
    void authenticate(bool created) {
        expect(RecoveredSeedExchange::hello());
        send(RecoveredSeedExchange::response);
        expect(RecoveredPostSeed::frame(0xf6));
        RecoveredC2S0002::Payload credentials{};credentials[167]=0xc8;
        send(RecoveredC2S0002::encode(credentials));
        expect(RecoveredCharacterBootstrap::candidate());
        require(session->state()==SessionState::Authenticated,"Recovered login disabled");
        if(created) {
            std::array<std::uint8_t,45> request{};
            request[0]=0x1b;request[1]='T';request[41]=4;
            send(RecoveredWorldFrame::encode(request));
            expect(RecoveredCharacterCreateResult::committed_success());
        }
    }
    void select(bool created) {
        authenticate(created);
        std::array<std::uint8_t,38> request{};request[0]=0x1a;request[34]=4;
        auto selection=RecoveredWorldFrame::encode(request);
        if(created) {
            auto prefix=RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x18,1});
            prefix.insert(prefix.end(),selection.begin(),selection.end());
            selection=std::move(prefix);
        }
        send(selection);
        expect(RecoveredCharacterCreateResult::committed_success());
        expect(world_frame);
        require(session->state()==SessionState::CharacterSelected && selection_calls==1 &&
                session->account_id==account && session->character_id==selected_character,"Selection binding changed");
        silent();
    }
    static std::vector<std::uint8_t> tail(std::uint16_t id=character) {
        return RecoveredWorldFrame::encode(std::array<std::uint8_t,9>{0x1f,0,0x23,0,0x1c,
            static_cast<std::uint8_t>(id),static_cast<std::uint8_t>(id>>8),1,0});
    }
};

std::array<std::uint8_t,17> bull_command(unsigned side,unsigned mask=0x3fff,bool friendly=false,unsigned action=3){
    std::array<std::uint8_t,17> b{};b[0]=0x35;b[2]=static_cast<std::uint8_t>(action);b[3]=static_cast<std::uint8_t>(side);
    const unsigned target_side=friendly?side:1-side;
    b[5+2*target_side]=static_cast<std::uint8_t>(mask);b[6+2*target_side]=static_cast<std::uint8_t>(mask>>8);
    if(action==3)b[13]=150;return b;
}
std::vector<std::uint8_t> expected_reply(unsigned side,unsigned count,unsigned mp,unsigned hp,unsigned loss,unsigned cycle,bool sparse=false){
    // Independent wire oracle. Do not invoke production skill encoder here.
    std::vector<std::uint8_t> out;
    if(!side){std::array<std::uint8_t,17> b{};b[0]=0x86;b[1]=1;b[5]=44;b[6]=1;
        for(unsigned i=0;i<4;++i)b[9+i]=static_cast<std::uint8_t>(mp>>(i*8));out.insert(out.end(),b.begin(),b.end());}
    for(unsigned n=0;n<count;++n){std::array<std::uint8_t,15>b{};b[0]=0x83;b[1]=3;b[2]=static_cast<std::uint8_t>(side*14);
        const auto offset=5+2*(1-side),mask=1u<<(sparse?13:n); b[offset]=static_cast<std::uint8_t>(mask);b[offset+1]=static_cast<std::uint8_t>(mask>>8);
        const auto delta=static_cast<std::uint16_t>(-static_cast<int>(loss));b[9]=static_cast<std::uint8_t>(delta);b[10]=static_cast<std::uint8_t>(delta>>8);b[11]=150;b[14]=hp?28:0;
        out.insert(out.end(),b.begin(),b.end());}
    std::array<std::uint8_t,121>b{};b[0]=0x88;b[1]=static_cast<std::uint8_t>(cycle);
    for(unsigned slot=0;slot<14;++slot){const unsigned h=side?((sparse?slot==13:slot<count)?hp:0):(slot==0?100:0),m=side?0:(slot==0?mp:0);
        for(unsigned i=0;i<4;++i){b[5+slot*8+i]=static_cast<std::uint8_t>(h>>(i*8));b[9+slot*8+i]=static_cast<std::uint8_t>(m>>(i*8));}}
    out.insert(out.end(),b.begin(),b.end());return RecoveredWorldFrame::encode(out);
}
void run_case(unsigned side,unsigned count,const std::string& scenario,nlohmann::json& results){
    LuaEngine lua(std::filesystem::path(GOD2_SOURCE_DIR)/"scripts",false);require(lua.initialize(),"Lua init");
    unsigned formulas=0,casts=0,rearms=0;RecoveredBattleService battles([&](const auto& in){++formulas;return lua.combat_damage(in);});
    RecoveredWorldService world({},[&](Session& s,auto records){auto reply=battles.handle(s,records);
        if(reply && battles.diagnostic_round_ready(s)){battles.rearm_diagnostic(s,battles.inspect(s.id()).revision);++rearms;}return reply;});
    RecoveredSessionPeer peer(false,[&](Session&s,auto records){return world.handle(s,records);});
    peer.select(false);peer.send(RecoveredSessionPeer::tail());peer.silent();
    peer.session->set_state(SessionState::InBattle); // Explicit trusted fixture admission, not a C2S protocol.
    const auto source=static_cast<std::uint8_t>(side*14),target=static_cast<std::uint8_t>((1-side)*14);
    const bool sparse=scenario=="lethal_sparse";
    const unsigned initial_mp=scenario=="low_mp"?99:300,initial_hp=(scenario=="lethal"||sparse)?1:2000;
    nlohmann::json received=nlohmann::json::array();
    std::vector<BattleActor> actors{{source,RecoveredSessionPeer::character,100,100,initial_mp,300,31,999,5,5}};
    for(unsigned i=0;i<count;++i)actors.push_back({static_cast<std::uint8_t>(target+(sparse?13:i)),0,initial_hp,initial_hp,0,0,10,10,13,1});
    if(sparse)actors.push_back({target,0,1,1,0,0,10,10,13,1});
    BattleAction basic{source,{},false,100,100,0,0,150};RecoveredBattleService::Policy policy{0,static_cast<std::uint8_t>(side),source,0,basic,{}};
    policy.diagnostic_single_action=true;policy.diagnostic_control_targets=side?std::array<std::uint16_t,2>{0,1}:std::array<std::uint16_t,2>{1,0};
    auto encode=[&](const auto& state,const auto& result){++casts;return thousand_bulls_reply(state,result,casts);};
    ThousandBulls::authorize(policy,basic,encode);auto initial_battle=Battle(97,actors,123).checkpoint();
    if(sparse)initial_battle.snapshot.actors[target]->hp=0;
    battles.bind(*peer.session,Battle::restore(initial_battle),policy,encode);
    auto valid=RecoveredWorldFrame::encode(bull_command(side));const auto initial=battles.inspect(peer.session->id());
    if(scenario=="friendly"||scenario=="subset"||scenario=="low_mp"){
        auto request=RecoveredWorldFrame::encode(bull_command(side,scenario=="subset"?1:0x3fff,scenario=="friendly"));
        peer.send(request);peer.closed();require(battles.inspect(peer.session->id())==initial && !casts && !formulas,"Rejected TCP request mutated resources/formula");
    }else{
        peer.send(std::span(valid).first(valid.size()-1));peer.silent();require(battles.inspect(peer.session->id())==initial && !casts,"Fragmented request committed early");
        peer.send(std::span(valid).last(1));const auto loss=std::min(297u,initial_hp);peer.expect(expected_reply(side,count,200,initial_hp-loss,loss,1,sparse));received.push_back(peer.last_wire);peer.silent();
        require(casts==1 && formulas==count,"Formula called more than once per target");
        require(battles.inspect(peer.session->id()).actors[source]->mp==initial_mp-100,"MP debit not once");
        const auto phases=ThousandBulls::presentation_losses(loss);unsigned shown=initial_hp;for(auto p:phases)shown-=p;
        for(unsigned i=0;i<count;++i)require(battles.inspect(peer.session->id()).actors[target+(sparse?13:i)]->hp==shown,"Wire phases diverged from authoritative HP");
        const auto after=battles.inspect(peer.session->id());
        if(scenario=="repeat"||scenario=="lethal"||sparse){
            peer.send(valid);peer.closed();require(battles.inspect(peer.session->id())==after && casts==1,"Repeat/terminal request committed again");
        }else{
            auto receipt=bull_command(side,1,true,0x0b);peer.send(RecoveredWorldFrame::encode(receipt));peer.silent();
            require(rearms==1 && battles.inspect(peer.session->id())==after,"Receipt must rearm without damage/MP");
            peer.send(valid);peer.expect(expected_reply(side,count,100,initial_hp-594,297,2));received.push_back(peer.last_wire);peer.silent();
            require(casts==2 && formulas==2*count && battles.inspect(peer.session->id()).actors[source]->mp==100,"Second cast failed/repeated cost");
            for(unsigned i=0;i<count;++i)require(battles.inspect(peer.session->id()).actors[target+(sparse?13:i)]->hp==initial_hp-594,"Second cast HP wrong");
        }
    }
    results.push_back({{"side",side},{"targets",count},{"scenario",scenario},{"status","PASS"},{"formula_calls",formulas},{"casts",casts},{"rearms",rearms},{"wire_frames",received},{"initial_target_hp",initial_hp},{"initial_source_mp",initial_mp},{"target_slot_start",target},{"sparse_target_bit",sparse?13:-1}});
    battles.remove(peer.session->id());
}
}
int main(int argc,char**argv){try{
    nlohmann::json results=nlohmann::json::array();
    for(unsigned side=0;side<2;++side){for(unsigned count:{1u,2u,14u})run_case(side,count,"two_rounds",results);
        for(const auto* scenario:{"friendly","subset","repeat","low_mp","lethal"})run_case(side,14,scenario,results);run_case(side,1,"lethal_sparse",results);}
    nlohmann::json report={{"scope","real loopback TCP Session/world/battle fixture; synthetic auth and battle admission; no DB/native UI/full Application claim"},{"cases",results},{"status","PASS"}};
    if(argc>1){std::ofstream out(argv[1]);require(out.good(),"Report open failed");out<<report.dump(2)<<'\n';}
    std::cout<<report.dump(2)<<'\n';return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
