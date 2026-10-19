#include "core/ApplicationGameSources.h"
#include "core/ApplicationGameFrame.h"
#include <asio.hpp>
#include <array>
#include <atomic>
#include <cstdint>
#include <exception>
#include <optional>
#include <stdexcept>
#include <thread>
#include <utility>

namespace {
using namespace god2;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
[[noreturn]] void unavailable(){throw std::runtime_error("Synthetic export fixture has no authentication/native authority");}
struct HostAbort final {};
struct State {
    const std::thread::id owner=std::this_thread::get_id();
    std::thread::id network_thread;
    std::array<std::atomic<unsigned>,3> captures{};
    std::array<unsigned,3> original_captures{},packets{},disconnects{},starts{},retires{},revokes{},destroyed{},unpublished{},refused{};
    std::array<std::uint8_t,3> observed{};
    std::array<bool,3> alive{},retired{},revoked{},host_copies{},tail{};
    bool invalid=false,net_joined=false,game_drained=false;
    std::exception_ptr network_failure,game_failure;
};
// Counts actual std::function capture copies, including queued NET/GAME jobs.
// Copy/destruction on NET touches only this pure atomic witness, not a probe.
struct Capture {
    State* state;std::uint8_t channel;
    Capture(State& source,std::uint8_t k):state(&source),channel(k){++state->captures[channel];}
    Capture(const Capture& other):state(other.state),channel(other.channel){if(state)++state->captures[channel];}
    Capture(Capture&& other) noexcept:state(std::exchange(other.state,nullptr)),channel(other.channel){}
    ~Capture(){if(state)--state->captures[channel];}
};
struct Probe {
    State& state;const std::uint8_t channel;ApplicationGameSources** published;
    std::uint8_t byte;
    Probe(State& source,std::uint8_t k,ApplicationGameSources** output):state(source),channel(k),published(output),byte(static_cast<std::uint8_t>(0x10+k)){state.alive[k]=true;}
    ~Probe(){
        state.invalid|=std::this_thread::get_id()!=state.owner||state.captures[channel].load()!=0||*published!=nullptr;
        ++state.destroyed[channel];state.alive[channel]=false;
    }
};
ApplicationGameFrame build_world_sources(State& state,std::uint8_t k,ApplicationGameSources** published){
    Probe probe(state,k,published);
    struct TransportHolders {Session::PacketHandler packet;Session::DisconnectHandler disconnected;} transport;
    ApplicationGameSources source;
    source.packet=[&probe,&state,k,witness=Capture(state,k)](std::shared_ptr<Session>,Packet packet){
        state.invalid|=std::this_thread::get_id()!=state.owner;
        if(!state.alive[k]){state.invalid=true;return;}
        if(state.retired[k]||state.revoked[k]){++state.refused[k];return;}
        state.invalid|=!state.alive[k]||!state.net_joined||state.starts[k]!=1||packet.payload.size()!=1;
        if(packet.payload.size()==1){probe.byte=static_cast<std::uint8_t>(probe.byte+packet.payload[0]);state.observed[k]=probe.byte;}
        ++state.packets[k];
    };
    source.disconnected=[&probe,&state,k,witness=Capture(state,k)](std::shared_ptr<Session>){
        state.invalid|=std::this_thread::get_id()!=state.owner;
        if(!state.alive[k]){state.invalid=true;return;}
        if(state.retired[k]||state.revoked[k]){++state.refused[k];return;}
        state.invalid|=!state.alive[k]||state.packets[k]!=1;
        probe.byte^=0x80;state.observed[k]=probe.byte;++state.disconnects[k];
    };
    // These fields prove complete passive export/copy shape only. They throw
    // if invoked: no successful auth, character list, selection or entry exists.
    source.authenticate=[](const RecoveredC2S0002::Parsed&)->std::uint64_t{unavailable();};
    source.account.native_list=[](Session&)->Session::NativeCharacterList{unavailable();};
    source.character.emplace();
    source.character->native_select=[](Session&,const RecoveredPostCreateSelect::Selection&,std::optional<std::uint64_t>)->std::uint64_t{unavailable();};
    source.start=[&probe,&state,k,witness=Capture(state,k)]{
        if(!state.alive[k]){state.invalid=true;return;}
        state.invalid|=std::this_thread::get_id()!=state.owner||!state.alive[k]||state.starts[k]!=0;
        ++state.starts[k];probe.byte=static_cast<std::uint8_t>(probe.byte+0x10);
    };
    source.retire=[&probe,&state,k,witness=Capture(state,k)]{
        if(!state.alive[k]){state.invalid=true;return;}
        state.invalid|=std::this_thread::get_id()!=state.owner||!state.alive[k]||state.retired[k];
        state.retired[k]=true;++state.retires[k];probe.byte=static_cast<std::uint8_t>(probe.byte+0x20);state.observed[k]=probe.byte;
    };
    source.revoke_transport=[&transport,&state,k,witness=Capture(state,k)]{
        if(!state.alive[k]){state.invalid=true;return;}
        state.invalid|=std::this_thread::get_id()!=state.owner||!state.alive[k]||!state.retired[k]||state.revoked[k];
        state.revoked[k]=true;++state.revokes[k];transport.packet={};transport.disconnected={};
    };
    state.original_captures[k]=state.captures[k].load();
    transport.packet=source.packet;transport.disconnected=source.disconnected;
    struct Unpublish {
        ApplicationGameSources** pointer;State& state;std::uint8_t channel;
        ~Unpublish(){*pointer=nullptr;++state.unpublished[channel];}
    } unpublish{published,state,k};
    *published=&source;
    co_await ApplicationGameFrame::Hold{};
    *published=nullptr;
    state.tail[k]=state.net_joined&&state.game_drained&&!state.host_copies[k]&&state.retired[k]&&state.revoked[k]&&
        state.captures[k].load()==state.original_captures[k];
}
struct HostCopies {
    State& state;
    std::array<std::optional<ApplicationGameSources>,3> sources;
    HostCopies(State& source,const std::array<ApplicationGameSources*,3>& published):state(source){
        for(std::uint8_t k=0;k<3;++k){sources[k].emplace(*published[k]);state.host_copies[k]=true;}
    }
    ~HostCopies(){for(std::uint8_t k=0;k<3;++k){sources[k].reset();state.host_copies[k]=false;}}
};
struct RetireBeforeHostCopies {
    const std::array<ApplicationGameSources*,3>& published;State& state;
    ~RetireBeforeHostCopies(){for(std::uint8_t k=0;k<3;++k){
        auto* source=published[k];if(!source||!state.alive[k]){state.invalid=true;continue;}
        source->retire();source->revoke_transport();
    }}
};
struct DrainBeforeFrames {
    asio::io_context& network;asio::io_context& game;State& state;
    std::thread worker;bool joined=false,drained=false;
    static void run(asio::io_context& context,std::exception_ptr& failure) noexcept{
        for(;;)try{context.restart();context.run();return;}catch(...){if(!failure)failure=std::current_exception();}
    }
    void finish(){
        if(!joined){if(worker.joinable())worker.join();else run(network,state.network_failure);joined=true;state.net_joined=true;}
        if(!drained){run(game,state.game_failure);drained=true;state.game_drained=true;}
    }
    ~DrainBeforeFrames(){finish();}
};

void three_independent_world_exports(bool abort_host){
    State state;std::array<ApplicationGameSources*,3> published{};bool caught_abort=false;
    try{
        asio::io_context game,network;
        std::array<std::optional<ApplicationGameFrame>,3> frames;
        // Declared after every frame owner, before host copies: queued copies
        // drain on unwind while all three independent lexical cohorts still live.
        DrainBeforeFrames drain{network,game,state};
        for(std::uint8_t k=0;k<3;++k){
            frames[k].emplace(build_world_sources(state,k,&published[k]));frames[k]->require_held();
            require(published[k]&&state.alive[k]&&!state.destroyed[k],"Independent frame did not publish its own held source");
            for(std::uint8_t j=0;j<k;++j)require(published[k]!=published[j],"Three worlds shared one lexical export object");
        }
        {
            HostCopies host(state,published);
            RetireBeforeHostCopies retire{published,state};
            for(std::uint8_t k=0;k<3;++k){
                auto& source=*host.sources[k];
                require(source.packet&&source.disconnected&&source.authenticate&&source.account.native_list&&
                    source.character&&source.character->native_select&&source.start&&source.retire&&source.revoke_transport,
                    "Host copy dropped account/optional character or lifecycle exports");
                source.start();
                for(std::uint8_t j=0;j<3;++j)require(state.starts[j]==(j<=k?1u:0u),"Starting one source modified another world's phase");
                asio::post(network,[&,k,packet=source.packet,disconnected=source.disconnected]{
                    state.network_thread=std::this_thread::get_id();
                    asio::post(game,[k,packet=std::move(packet),disconnected=std::move(disconnected)]{
                        // Null Session is intentional: these SYNTHETIC callbacks
                        // dispatch byte probes, never Session/native authority.
                        packet({},Packet{0xf001,{static_cast<std::uint8_t>(k+1)}});disconnected({});
                    });
                });
            }
            drain.worker=std::thread([&]{DrainBeforeFrames::run(network,state.network_failure);});
            if(abort_host)throw HostAbort{};
            drain.finish();
            if(state.network_failure)std::rethrow_exception(state.network_failure);
            if(state.game_failure)std::rethrow_exception(state.game_failure);
            require(state.network_thread!=state.owner&&network.stopped()&&game.stopped(),"One host did not naturally join NET and drain GAME");
            for(std::uint8_t k=0;k<3;++k)
                require(state.packets[k]==1&&state.disconnects[k]==1&&state.observed[k]==0xa1+2*k&&state.alive[k],
                    "Queued export callback updated the wrong held world bytes");
        }
        for(std::uint8_t k=0;k<3;++k){
            require(!state.host_copies[k]&&state.retired[k]&&state.revoked[k]&&state.retires[k]==1&&state.revokes[k]==1&&
                state.captures[k].load()==state.original_captures[k],"Listener/queued copies or transport holders survived host retirement");
            frames[k]->require_held();frames[k]->finish_after_drain();
            require(!published[k]&&state.tail[k]&&state.destroyed[k]==1,"Frame resumed before host copies died or failed to unpublish");
            for(std::uint8_t j=static_cast<std::uint8_t>(k+1);j<3;++j)
                require(published[j]&&state.alive[j]&&!state.destroyed[j],"Finishing one cohort retired another world's sources");
        }
    }catch(const HostAbort&){caught_abort=true;}
    if(state.network_failure)std::rethrow_exception(state.network_failure);
    if(state.game_failure)std::rethrow_exception(state.game_failure);
    require(caught_abort==abort_host&&!state.invalid&&state.net_joined&&state.game_drained,"Host lifetime error was swallowed or callbacks escaped GAME");
    for(std::uint8_t k=0;k<3;++k)
        require(!published[k]&&!state.alive[k]&&state.destroyed[k]==1&&state.unpublished[k]==1&&
            !state.host_copies[k]&&state.captures[k].load()==0&&state.starts[k]==1&&state.retires[k]==1&&state.revokes[k]==1&&
            state.observed[k]==(abort_host?0x40+k:0xc1+2*k)&&
            state.tail[k]==!abort_host&&(abort_host?(state.packets[k]==0&&state.disconnects[k]==0&&state.refused[k]==2):state.refused[k]==0),
            "Normal/abort path retained a raw export, escaped callback copy or wrong-world lifetime");
}
} // namespace

void test_application_game_sources(){three_independent_world_exports(false);three_independent_world_exports(true);}
