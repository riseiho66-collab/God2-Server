#include "net/TaiwanChannelServers.h"
#include "db/RecoveredCharacterRepository.h"
#include "protocol/RecoveredSeedExchange.h"
#include "protocol/RecoveredPostSeed.h"
#include "protocol/RecoveredTaiwanServerAdvertisement.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <exception>
#include <filesystem>
#include <fstream>
#include <optional>
#include <set>
#include <stdexcept>
#include <thread>
#include <vector>

namespace {
using namespace god2;
using Servers=TaiwanChannelServers;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class Exception,class F> bool refuses(F&& call){try{call();}catch(const Exception&){return true;}return false;}
[[noreturn]] void unused(){throw std::runtime_error("Synthetic topology fixture reached an unprovided gameplay authority");}
// No database or invented saved roots: the seed-only socket exercise must not
// enter any character, item, entry, movement or durable storage operation.
struct Repository final:RecoveredCharacterRepository {
    std::optional<CharacterRoleSnapshot> load_role(std::uint64_t,std::uint64_t) override{unused();}
    RoleResourceCommit commit_role_resources(std::uint64_t,std::uint64_t,const std::optional<CharacterRoleSnapshot>&,
        const CharacterResources&,CharacterRoleSnapshot,CharacterResources) override{unused();}
    std::optional<CharacterExperience> load_experience(std::uint64_t,std::uint64_t) override{unused();}
    BattleSettlement settle_battle(std::uint64_t,std::uint64_t,std::uint64_t,const CharacterResources&,
        CharacterResources,bool,std::uint64_t,const std::optional<BattleProgressionCommit>&) override{unused();}
    std::uint64_t reserve_battle(std::uint64_t,std::uint64_t,const CharacterResources&) override{unused();}
    std::optional<CharacterResources> load_resources(std::uint64_t,std::uint64_t) override{unused();}
    CharacterResources commit_resources(std::uint64_t,std::uint64_t,const std::optional<CharacterResources>&,
        CharacterResources) override{unused();}
    RecoveredCharacter create(std::uint64_t,const std::array<std::uint8_t,40>&) override{unused();}
    std::vector<RecoveredCharacter> list_for_account(std::uint64_t) override{unused();}
    std::optional<RecoveredPosition> load_position(std::uint64_t,std::uint64_t) override{unused();}
    RecoveredPosition commit_position(std::uint64_t,std::uint64_t,const std::optional<RecoveredPosition>&,
        std::uint16_t,std::uint16_t,std::uint16_t,std::uint16_t) override{unused();}
};
struct ConfigurationFiles {
    const std::filesystem::path root=std::filesystem::temp_directory_path()/
        ("g2-channel487-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    ConfigurationFiles(){require(std::filesystem::create_directory(root),"Unique channel configuration directory unavailable");std::filesystem::create_directory(root/"Data3");}
    ~ConfigurationFiles(){std::error_code ignored;std::filesystem::remove_all(root,ignored);}
    std::shared_ptr<const TaiwanNativeClientGroupConfiguration> read(unsigned slots){
        {
            std::ofstream stream(root/"Data3"/"config.ini",std::ios::binary|std::ios::trunc);
            stream<<"[Synthetic]\n";for(unsigned k=0;k<slots;++k)stream<<"Channel"<<k<<"=127.0.0.1\n";
            require(bool(stream),"Synthetic complete plain configuration write failed");
        }
        return TaiwanNativeClientGroupConfiguration::read(root,{"127.0.0.1",0,0},4096,4096);
    }
};
std::array<Servers::EndpointPolicy,3> policies(){return {{
    {{127,0,0,1},0,0x71,{0x11,0xa1,0xb1,0xc1}},
    {{127,0,0,1},0,0x82,{0x83,0xa2,0xb2,0xc2}},
    {{127,0,0,1},0,0x93,{0xfe,0xa3,0xb3,0xc3}}
}};}
struct Fixture {
    // Repositories/worlds outlive both executors and all borrowed callbacks.
    // GAME also outlives NET; pump them serially on the actual owning thread.
    Repository repository;
    SharedTaiwanChannelWorlds worlds{repository};
    asio::io_context game,network,client;
    ConfigurationFiles files;
    const std::shared_ptr<const TaiwanNativeClientGroupConfiguration> configuration=files.read(3);
    const std::thread::id owner=std::this_thread::get_id();
    std::array<unsigned,3> factory_calls{},disconnects{};
    std::array<std::shared_ptr<Session>,3> held{};
    std::array<std::unique_ptr<asio::ip::tcp::socket>,3> peers{};
    std::exception_ptr callback_failure;
    std::unique_ptr<Servers> servers;
    std::size_t pump(){
        network.restart();game.restart();
        const auto a=network.poll(),b=game.poll();network.restart();return a+b+network.poll();
    }
    void drain(){for(unsigned k=0;k<256;++k)if(!pump())break;}
    void checked(){if(callback_failure)std::rethrow_exception(callback_failure);}
    Servers::Sources sources(std::uint8_t k,const std::shared_ptr<SharedWorldHost>& world){
        require(std::this_thread::get_id()==owner&&k<3&&world==worlds.world(k),"Source factory was not on the selected actual GAME world");
        ++factory_calls[k];Servers::Sources out;
        out.packet=[](std::shared_ptr<Session>,Packet){unused();};
        // Borrow this fixture, never retain an affine world in a NET-owned
        // callback. Gameplay callbacks below deliberately supply no authority.
        out.disconnected=[this,k](std::shared_ptr<Session> session){
            try{
                require(std::this_thread::get_id()==owner&&session->state()==SessionState::Disconnected&&
                    session->native_channel_bound()&&session->native_channel_binding_current()&&
                    session->native_channel_ordinal()==std::optional{k},"Accepted channel Session lost GAME metadata");
                for(std::uint8_t j=0;j<3;++j)
                    require(session->native_channel_allows_presence(worlds.world(j)->presence())==(j==k)&&
                        session->native_channel_allows_destination(0,j)==(j==k),"Accepted Session borrowed a different world/destination");
                require(!session->native_channel_allows_destination(1,k),"Accepted Session borrowed another group");
            }catch(...){if(!callback_failure)callback_failure=std::current_exception();}
            held[k]=std::move(session);++disconnects[k];
        };
        out.authenticate=[](const RecoveredC2S0002::Parsed&)->std::uint64_t{unused();};
        auto& h=out.characters;
        h.native_list=[](Session&)->Session::NativeCharacterList{unused();};
        h.native_list_current=[](Session&,const Session::NativeCharacterList&)->bool{unused();};
        h.native_list_complete=[](Session&,const Session::NativeCharacterList&,bool)->bool{unused();};
        h.native_select=[](Session&,const RecoveredPostCreateSelect::Selection&,std::optional<std::uint64_t>)->std::uint64_t{unused();};
        h.create=[](std::uint64_t,const RecoveredCharacterCreate&)->std::uint64_t{unused();};
        h.world_entry=[](std::uint64_t,std::uint64_t,std::uint64_t)->RecoveredWorldEntry::Frame{unused();};
        h.world_ready=[](Session&){unused();};
        h.world_records=[](Session&,std::span<const RecoveredWorldRecords::Record>)->std::optional<std::vector<std::uint8_t>>{unused();};
        h.common_world_lifecycle_factory=[](Session&)->std::shared_ptr<const Session::CommonWorldLifecycle>{unused();};
        h.common_world_cleanup_owner=[](Session&,std::function<void()>)->std::function<void()>{unused();};
        h.common_world_lifecycle_abandon=[](Session&){}; // No factory slot was created by this seed-only exercise.
        h.common_world_publication_owner=[](Session&,Session::CommonWorldPublication)->Session::CommonWorldPublication{unused();};
        return out;
    }
    Servers::SourceFactory factory(){return [this](std::uint8_t k,const auto& world){return sources(k,world);};}
    void expect(asio::ip::tcp::socket& socket,std::span<const std::uint8_t> expected){
        std::vector<std::uint8_t> actual(expected.size());std::size_t at=0;
        const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(3);
        while(at<actual.size()&&std::chrono::steady_clock::now()<deadline){
            pump();checked();asio::error_code error;
            at+=socket.read_some(asio::buffer(actual.data()+at,actual.size()-at),error);
            require(!error||error==asio::error::would_block||error==asio::error::try_again,"Accepted Session closed before seed reply");
        }
        require(at==actual.size()&&std::equal(actual.begin(),actual.end(),expected.begin()),"Actual three-listener seed reply changed/timed out");
    }
    ~Fixture(){
        for(auto& peer:peers)if(peer){asio::error_code ignored;peer->close(ignored);}
        if(servers)servers->stop();drain();servers.reset();drain();
        held={};drain();
    }
};

void actual_three_listener_bindings(){
    Fixture f;const auto policy=policies();
    f.servers=std::make_unique<Servers>(f.network,f.game.get_executor(),f.worlds,f.configuration,0,0x92,policy,4,false,f.factory());
    const auto advertisement=RecoveredTaiwanServerAdvertisement::parse(f.servers->advertisement());
    require(advertisement&&advertisement->rows[0]&&advertisement->rows[0]->raw==std::array<std::uint8_t,4>{0,0x92,7,0},"Bound topology did not advertise exactly three available slots");
    std::set<std::uint16_t> ports;
    for(std::uint8_t k=0;k<3;++k){
        const auto endpoint=f.servers->endpoint(k);ports.insert(endpoint.port());
        require(endpoint.address()==asio::ip::make_address("127.0.0.1")&&endpoint.port()&&f.factory_calls[k]==1,"Listener did not bind actual independent endpoint/source");
        std::array<std::uint8_t,75> list{};list[0]=7;list[1]=1;list[3+19]=5;list[3+32]=policy[k].route_body[0];
        const auto destination=advertisement->primary_destination({0,k,3},5,list);
        require(destination&&destination->port()==endpoint.port()&&destination->address()==endpoint.address().to_v4().to_bytes()&&
            destination->endpoint_body[1]==policy[k].status&&destination->route_body==policy[k].route_body&&
            destination->endpoint_index==k&&destination->route_index==0,"Advertisement did not use actual bound destination/full opaque routing bytes");
    }
    require(ports.size()==3&&refuses<std::out_of_range>([&]{(void)f.servers->endpoint(3);}),"Three listeners aliased ports or exposed a fourth channel");
    f.servers->start();f.servers->start(); // Idempotent start, no duplicate source construction.
    for(std::uint8_t k=0;k<3;++k){
        f.peers[k]=std::make_unique<asio::ip::tcp::socket>(f.client);auto& peer=*f.peers[k];
        peer.connect(f.servers->endpoint(k));peer.non_blocking(true);f.expect(peer,RecoveredSeedExchange::hello());
        peer.non_blocking(false);asio::write(peer,asio::buffer(RecoveredSeedExchange::response));peer.non_blocking(true);
        f.expect(peer,RecoveredPostSeed::frame(0xf6));asio::error_code ignored;peer.close(ignored);
    }
    const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(3);
    while(std::chrono::steady_clock::now()<deadline&&std::any_of(f.disconnects.begin(),f.disconnects.end(),[](auto n){return n!=1;})){f.pump();f.checked();}
    f.checked();std::set<std::uint64_t> identities;
    for(std::uint8_t k=0;k<3;++k){require(f.disconnects[k]==1&&f.held[k],"Actual accepted Session was not captured on GAME disconnect");identities.insert(f.held[k]->id());}
    require(identities.size()==3&&!identities.contains(0),"Separate listeners reused a connection identity");
    unsigned thread_refusals=0;
    std::thread foreign([&]{
        thread_refusals+=refuses<std::logic_error>([&]{(void)f.servers->endpoint(0);});
        thread_refusals+=refuses<std::logic_error>([&]{(void)f.servers->advertisement();});
        thread_refusals+=refuses<std::logic_error>([&]{(void)f.held[0]->native_channel_allows_destination(0,0);});
        thread_refusals+=refuses<std::logic_error>([&]{(void)f.held[0]->native_channel_binding_current();});
    });foreign.join();require(thread_refusals==4,"Bound listener/source Game-owner checks were bypassed");
    const auto observations=f.servers->stop_observed(); // Revocation is synchronous, before NET drain.
    const auto repeated=f.servers->stop_observed();
    for(const auto& observation:observations)
        require(!observation.complete()&&!observation.succeeded()&&!observation.aborted(),"Triple stop completed before actual executor acknowledgments");
    for(std::uint8_t k=0;k<3;++k)
        require(f.held[k]->native_channel_bound()&&f.held[k]->native_channel_ordinal()==std::optional{k}&&
            !f.held[k]->native_channel_binding_current()&&
            !f.held[k]->native_channel_allows_presence(f.worlds.world(k)->presence())&&
            !f.held[k]->native_channel_allows_destination(0,k),"Stop rewrote metadata or left retained accepted binding live");
    require(refuses<std::logic_error>([&]{(void)f.servers->advertisement();})&&
        refuses<std::logic_error>([&]{f.servers->start();}),"Stopped topology advertised or restarted");
    // NET accept cancellation may finish now, but each pure final GAME marker
    // is still paused. A receipt is not merely synchronous socket retirement.
    for(unsigned k=0;k<64;++k){f.network.restart();f.network.poll();}
    for(const auto& observation:observations)require(!observation.complete(),"Triple stop bypassed final GAME marker");
    const auto stop_deadline=std::chrono::steady_clock::now()+std::chrono::seconds(3);
    while(std::chrono::steady_clock::now()<stop_deadline&&
        std::any_of(observations.begin(),observations.end(),[](const auto& value){return !value.complete();})){f.pump();f.checked();}
    for(std::size_t k=0;k<observations.size();++k)
        require(observations[k].complete()&&observations[k].succeeded()&&!observations[k].aborted()&&
            repeated[k].complete()&&repeated[k].succeeded(),"One actual channel/repeated stop observation did not acknowledge clean drain");
    f.drain();
}

void observed_stop_waits_for_actual_game_callbacks(bool throwing){
    Fixture f;
    struct CallbackState {
        explicit CallbackState(std::thread::id actual_owner):owner(actual_owner){}
        const std::thread::id owner;
        unsigned abandon_calls=0,disconnect_calls=0;
        bool correct_owner=true,reentrant_pending=false;
        std::vector<char> callback_order;
        std::shared_ptr<Session> held;
        std::optional<TcpServer::StopObservation> reentrant;
        std::weak_ptr<TcpServer> listener;
    };
    const auto state=std::make_shared<CallbackState>(f.owner);
    // These aliases are assertion-only. Every asynchronous callback owns pure
    // state and a weak listener, never references these aliases, f or locals.
    auto& abandon_calls=state->abandon_calls;auto& disconnect_calls=state->disconnect_calls;
    auto& correct_owner=state->correct_owner;auto& reentrant_pending=state->reentrant_pending;
    auto& callback_order=state->callback_order;auto& held=state->held;auto& reentrant=state->reentrant;
    auto source=f.sources(0,f.worlds.world(0));
    source.characters.common_world_lifecycle_abandon=[state,throwing](Session&){
        ++state->abandon_calls;state->callback_order.push_back('a');state->correct_owner&=std::this_thread::get_id()==state->owner;
        if(throwing)throw std::runtime_error("Expected synthetic abandon failure");
    };
    source.disconnected=[state,throwing](std::shared_ptr<Session> session){
        ++state->disconnect_calls;state->callback_order.push_back('d');state->held=std::move(session);
        state->correct_owner&=std::this_thread::get_id()==state->owner&&state->held->state()==SessionState::Disconnected;
        // Early assertion/construction failures can unwind the listener before
        // Fixture drains GAME. Its callbacks still own state, but never touch a
        // destroyed server; normal execution below requires the real receipt.
        if(const auto listener=state->listener.lock()){
            state->reentrant=listener->stop_observed();
            state->reentrant_pending=!state->reentrant->complete()&&!state->reentrant->succeeded()&&!state->reentrant->aborted();
        }
        if(throwing)throw std::runtime_error("Expected synthetic disconnect failure");
    };
    // Real listener/Session and real private disconnect completion; no auth,
    // native entry hooks, fabricated save receipt or DB operation is provided.
    auto server=std::make_shared<TcpServer>(f.network,f.game.get_executor(),"127.0.0.1",0,4,false,
        std::move(source.packet),std::move(source.disconnected),ProtocolMode::God2CharacterConnection,
        std::move(source.authenticate),std::move(source.characters));state->listener=server;server->start();
    f.peers[0]=std::make_unique<asio::ip::tcp::socket>(f.client);auto& peer=*f.peers[0];
    peer.connect(server->bound_endpoint());peer.non_blocking(true);f.expect(peer,RecoveredSeedExchange::hello());
    peer.non_blocking(false);asio::write(peer,asio::buffer(RecoveredSeedExchange::response));peer.non_blocking(true);
    f.expect(peer,RecoveredPostSeed::frame(0xf6));
    const auto stopped=server->stop_observed(),copy=stopped;
    const auto repeated=server->stop_observed();
    require(!stopped.complete()&&!stopped.succeeded()&&!stopped.aborted(),"Stop observation completed before executing stop");
    // Keep GAME paused while NET processes stop, pending accept/read cancellation
    // and actual Session close. Disconnect callback ownership has not run yet.
    for(unsigned k=0;k<128;++k){f.network.restart();f.network.poll();}
    require(abandon_calls==0&&disconnect_calls==0&&!stopped.complete()&&!copy.complete(),"NET retirement bypassed paused GAME callbacks");
    const auto callback_deadline=std::chrono::steady_clock::now()+std::chrono::seconds(3);
    while(!disconnect_calls&&std::chrono::steady_clock::now()<callback_deadline){f.game.restart();f.game.poll();}
    require(abandon_calls==1&&disconnect_calls==1&&correct_owner&&callback_order==std::vector<char>{'a','d'}&&
        held&&reentrant&&reentrant_pending&&!stopped.complete()&&!repeated.complete(),
        "Abandon/disconnect were skipped, reordered, repeated or reported complete inside GAME callback");
    // GAME has returned, but exact SessionManager removal still needs NET and
    // its resulting final GAME marker. A failing callback must still join both.
    for(unsigned k=0;k<128;++k){f.network.restart();f.network.poll();}
    require(!stopped.complete()&&!stopped.aborted(),"NET acknowledgment bypassed the final GAME marker");
    const auto marker_deadline=std::chrono::steady_clock::now()+std::chrono::seconds(3);
    while(!stopped.complete()&&!stopped.aborted()&&std::chrono::steady_clock::now()<marker_deadline){f.game.restart();f.game.poll();}
    require(stopped.complete()&&!stopped.aborted()&&stopped.succeeded()==!throwing&&copy.complete()&&
        repeated.complete()&&reentrant->complete()&&reentrant->succeeded()==!throwing&&
        abandon_calls==1&&disconnect_calls==1,"Final stop lost callback failure or did not complete exact repeated observations");
    // Observation does not promise Session destruction; this copy stays owned
    // after completion. Clean means callbacks returned, never durable-save proof.
    require(held->state()==SessionState::Disconnected,"Completed observation required destruction of retained Session");
    server.reset();f.drain();held.reset();f.drain();
}
void unstarted_observed_stop_is_repeatable(){
    Fixture f;
    auto server=std::make_unique<TcpServer>(f.network,f.game.get_executor(),"127.0.0.1",0,4,false,
        Session::PacketHandler{},Session::DisconnectHandler{});
    const auto first=server->stop_observed(),second=server->stop_observed();
    require(!first.complete()&&!first.succeeded()&&!first.aborted(),"Unstarted listener fabricated synchronous completion");
    for(unsigned k=0;k<32;++k){f.network.restart();f.network.poll();}
    require(!first.complete()&&!second.complete(),"Unstarted stop bypassed final GAME marker");
    f.game.restart();f.game.poll();
    require(first.complete()&&first.succeeded()&&!first.aborted()&&second.complete()&&second.succeeded(),"Unstarted/repeated stop could not acknowledge cleanly");
    const auto later=server->stop_observed();require(later.complete()&&later.succeeded(),"Repeated stop did not observe same completed receipt");
    server.reset();f.drain();require(first.complete()&&first.succeeded(),"Copied stop observation depended on listener lifetime");
}

struct PortReservation {
    asio::ip::tcp::acceptor socket;
    explicit PortReservation(asio::io_context& io,std::uint16_t port=0):socket(io){
        socket.open(asio::ip::tcp::v4());
#ifdef _WIN32
        const int exclusive=1;
        require(::setsockopt(socket.native_handle(),SOL_SOCKET,SO_EXCLUSIVEADDRUSE,reinterpret_cast<const char*>(&exclusive),sizeof(exclusive))==0,
            "Exclusive fixture port reservation unavailable");
#endif
        socket.bind({asio::ip::address_v4::loopback(),port});socket.listen();
    }
    std::uint16_t port()const{return socket.local_endpoint().port();}
};
void invalid_sources_and_atomic_bind_rollback(){
    Fixture f;const auto policy=policies();
    const auto make=[&](auto config,const auto& input,std::size_t capacity,Servers::SourceFactory factory){
        return std::make_unique<Servers>(f.network,f.game.get_executor(),f.worlds,std::move(config),0,0x92,input,capacity,false,std::move(factory));
    };
    for(const unsigned count:{2u,4u})require(refuses<std::invalid_argument>([&]{(void)make(f.files.read(count),policy,4,f.factory());}),"Wrong configured slot count accepted");
    require(refuses<std::invalid_argument>([&]{(void)make(nullptr,policy,4,f.factory());})&&
        refuses<std::invalid_argument>([&]{(void)make(f.configuration,policy,0,f.factory());})&&
        refuses<std::invalid_argument>([&]{(void)make(f.configuration,policy,4,{});}),"Missing configuration/capacity/factory accepted");
    auto bad=policy;bad[2].route_body[0]=0;
    require(refuses<std::invalid_argument>([&]{(void)make(f.configuration,bad,4,f.factory());}),"Missing route key accepted");
    bad=policy;bad[1].address={192,168,1,1};
    require(refuses<std::invalid_argument>([&]{(void)make(f.configuration,bad,4,f.factory());}),"Nonloopback topology accepted");
    bad=policy;bad[0].port=bad[1].port=2593;
    require(refuses<std::invalid_argument>([&]{(void)make(f.configuration,bad,4,f.factory());}),"Aliased configured endpoints accepted");
    const auto incomplete=[&](std::uint8_t k,const auto& world){auto source=f.sources(k,world);if(k==2)source.characters.common_world_publication_owner={};return source;};
    require(refuses<std::invalid_argument>([&]{(void)make(f.configuration,policy,4,incomplete);}),"Incomplete actual source facade accepted");
    const auto throwing=[&](std::uint8_t k,const auto& world){if(k==2)throw std::runtime_error("Synthetic third source failure");return f.sources(k,world);};
    require(refuses<std::runtime_error>([&]{(void)make(f.configuration,policy,4,throwing);}),"Third source failure was swallowed");
    PortReservation first(f.client),second(f.client),third(f.client);
    const auto p0=first.port(),p1=second.port();bad=policy;bad[0].port=p0;bad[1].port=p1;bad[2].port=third.port();
    first.socket.close();second.socket.close();
    require(refuses<asio::system_error>([&]{(void)make(f.configuration,bad,4,f.factory());}),"Occupied third port did not reject partial topology");
    // Check before pumping either executor: rollback must close successful
    // first/second binds synchronously, not rely on deferred stop handlers.
    PortReservation recovered_first(f.client,p0),recovered_second(f.client,p1);
    f.drain();
}
void legacy_unbound_session_remains_unbound(){
    Fixture f;asio::ip::tcp::acceptor acceptor(f.network,{asio::ip::address_v4::loopback(),0});
    asio::ip::tcp::socket peer(f.client);peer.connect(acceptor.local_endpoint());
    auto accepted=acceptor.accept();
    auto session=std::make_shared<Session>(std::move(accepted),f.game.get_executor(),0x500000001ULL,false,
        Session::PacketHandler{},Session::DisconnectHandler{});
    require(!session->native_channel_bound()&&!session->native_channel_ordinal()&&session->native_channel_binding_current()&&
        session->native_channel_allows_presence(f.worlds.world(2)->presence())&&session->native_channel_allows_destination(9,9),
        "Legacy unbound Session acquired channel restrictions/metadata");
    session->close();peer.close();f.drain();session.reset();f.drain();
}
} // namespace

void test_taiwan_channel_servers(){
    actual_three_listener_bindings();invalid_sources_and_atomic_bind_rollback();legacy_unbound_session_remains_unbound();
    observed_stop_waits_for_actual_game_callbacks(false);observed_stop_waits_for_actual_game_callbacks(true);
    unstarted_observed_stop_is_repeatable();
}
