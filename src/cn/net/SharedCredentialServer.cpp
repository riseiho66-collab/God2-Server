#include "cn/net/SharedCredentialServer.h"
#include "cn/protocol/CnAccountWire.h"
#include "cn/assets/CnSharedSkillCatalog.h"
#include "game/SharedWorldHost.h"
#include "net/ConnectionIdentity.h"
#include <chrono>
#include <map>
#include <set>
#include <stdexcept>
#include <utility>

namespace god2::cn {
struct SharedCredentialServer::State {
    SharedAccountVerifier& verifier;
    // Destroy controllers/connections before the same common host. State and
    // Application retain it on the serial game owner through normal drain.
    std::shared_ptr<god2::SharedWorldHost> common_world;
    // Retain the exact qualified native provider after controllers/connections
    // are destroyed. The shared DB reader remains Application-owned through
    // game-owner drain; catalog also retains the explicit actual store owner.
    std::shared_ptr<const CnSharedSkillCatalog> cn_native_skills;
    SharedServerPlan::Controllers controllers;
    std::shared_ptr<SharedWorldAdmission> admission;
    std::map<std::uint64_t,std::shared_ptr<SharedCredentialConnection>> connections;
    const std::size_t capacity;
    bool stopping=false,started=false;

    State(SharedAccountVerifier& v,SharedServerPlan::Controllers c,
          std::shared_ptr<SharedWorldAdmission> a,std::size_t limit,std::shared_ptr<god2::SharedWorldHost> world,
          std::shared_ptr<const CnSharedSkillCatalog> skills)
        :verifier(v),common_world(std::move(world)),cn_native_skills(std::move(skills)),
         controllers(std::move(c)),admission(std::move(a)),capacity(limit) {}
};
struct SharedCredentialServer::Listener:std::enable_shared_from_this<Listener> {
    struct Slot {
        std::shared_ptr<std::atomic_size_t> count;
        explicit Slot(std::shared_ptr<std::atomic_size_t> c):count(std::move(c)) {}
        ~Slot(){count->fetch_sub(1,std::memory_order_relaxed);}
    };
    struct Port {
        SharedServerPlan::Endpoint endpoint;
        asio::ip::tcp::acceptor acceptor;
        asio::steady_timer retry;
        Port(SharedServerPlan::Endpoint e,asio::any_io_executor strand)
            :endpoint(std::move(e)),acceptor(strand),retry(strand) {}
    };
    asio::io_context& network;
    asio::strand<asio::io_context::executor_type> strand;
    asio::any_io_executor game;
    // Network handlers never own the game state/verifier or destroy its worker
    // pool on a network thread. Even already accepted sockets recheck stop on game.
    std::weak_ptr<State> state;
    // Includes accepted sockets queued to game and live/closing transports;
    // game-map capacity alone would leave the network->game queue unbounded.
    std::shared_ptr<std::atomic_size_t> reserved=std::make_shared<std::atomic_size_t>(0);
    const std::size_t capacity;
    std::vector<std::unique_ptr<Port>> ports;
    bool started=false,stopped=false;

    Listener(asio::io_context& n,asio::any_io_executor g,const std::shared_ptr<State>& s,
             const std::vector<SharedServerPlan::Endpoint>& endpoints)
        :network(n),strand(asio::make_strand(n)),game(std::move(g)),state(s),capacity(s->capacity) {
        for(const auto& endpoint:endpoints) {
            auto port=std::make_unique<Port>(endpoint,strand);
            const asio::ip::tcp::endpoint address(asio::ip::make_address(endpoint.host),endpoint.port);
            port->acceptor.open(address.protocol());
            // No shared-port guessing or automatic destination remapping.
            port->acceptor.bind(address);
            port->acceptor.listen(asio::socket_base::max_listen_connections);
            ports.push_back(std::move(port));
        }
    }
    void start() {
        if(started || stopped)return;
        started=true;
        for(std::size_t i=0;i<ports.size();++i)accept(i);
    }
    void accept(std::size_t index) {
        if(stopped)return;
        ports[index]->acceptor.async_accept(network,asio::bind_executor(strand,
            [self=shared_from_this(),index](const asio::error_code& ec,asio::ip::tcp::socket socket) mutable {
                if(self->stopped)return;
                if(ec) {
                    auto& port=*self->ports[index];
                    port.retry.expires_after(std::chrono::milliseconds(250));
                    port.retry.async_wait([self,index](const asio::error_code& error) {
                        if(!error)self->accept(index);
                    });
                    return;
                }
                asio::error_code ignored;
                socket.set_option(asio::ip::tcp::no_delay(true),ignored);
                auto count=self->reserved->load(std::memory_order_relaxed);
                while(count<self->capacity && !self->reserved->compare_exchange_weak(
                    count,count+1,std::memory_order_relaxed)) {}
                if(count>=self->capacity){self->accept(index);return;}
                std::shared_ptr<Slot> slot;
                try {slot=std::make_shared<Slot>(self->reserved);}
                catch(...) {self->reserved->fetch_sub(1,std::memory_order_relaxed);self->accept(index);return;}
                // Work remains until game sees this socket, including during stop.
                auto work=asio::make_work_guard(self->game);
                asio::post(self->game,[weak=self->state,endpoint=self->ports[index]->endpoint,
                    socket=std::move(socket),game=self->game,work=std::move(work),slot=std::move(slot)]() mutable {
                    const auto state=weak.lock();
                    if(!state || state->stopping || state->connections.size()>=state->capacity)return;
                    std::shared_ptr<SharedCredentialConnection> connection;
                    std::uint64_t id=0;
                    try {
                        if(state->cn_native_skills && !state->cn_native_skills->current())return;
                        id=next_connection_identity();
                        const auto seed=state->controllers.seed(id,endpoint);
                        if(!seed || state->stopping ||
                           (state->cn_native_skills && !state->cn_native_skills->current()))return;
                        connection=SharedCredentialConnection::create(std::move(socket),game,*seed,
                            endpoint.role,state->controllers.account_configuration,state->verifier,
                            [weak,id,endpoint](std::shared_ptr<SharedCredentialConnection> current,
                                CredentialResult result,std::shared_ptr<const god2cn::CnAccountWire::Login> login,
                                SharedCredentialConnection::Transport::Completion done) mutable {
                                const auto owner=weak.lock();
                                if(!owner || owner->stopping){done(false);return;}
                                if(owner->cn_native_skills && !owner->cn_native_skills->current()) {
                                    done(false);return;
                                }
                                const auto found=owner->connections.find(id);
                                if(found==owner->connections.end() || found->second!=current || current->closing()) {
                                    done(false);return;
                                }
                                const auto& verified=endpoint.role==SharedServerPlan::Role::Account?
                                    owner->controllers.account:owner->controllers.world;
                                verified(id,endpoint,std::move(current),result,std::move(login),std::move(done));
                            },
                            [weak,id,slot] {
                                if(const auto owner=weak.lock())owner->connections.erase(id);
                            });
                        state->connections.emplace(id,connection);
                        connection->start();
                    } catch(...) {
                        // No exception text/login/native seed enters diagnostics.
                        if(connection)connection->close();
                        if(id)state->connections.erase(id);
                    }
                });
                self->accept(index);
            }));
    }
    void stop() {
        if(stopped)return;
        stopped=true;
        for(auto& port:ports) {
            asio::error_code ignored;
            port->acceptor.close(ignored);
            port->retry.cancel();
        }
    }
};
void SharedCredentialServer::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN listener game owner mismatch");
}
SharedCredentialServer::SharedCredentialServer(asio::io_context& network,asio::any_io_executor game,
    AccountRepository& accounts,NativeAccountSnapshotRepository& account_snapshots,
    NativeCharacterSummarySnapshotRepository& character_summaries,
    RecoveredCharacterRepository& characters,const NativeMapCatalog& maps,
    const SharedServerPlan& plan)
    :SharedCredentialServer(network,std::move(game),accounts,account_snapshots,character_summaries,
        characters,maps,plan,{}) {}
SharedCredentialServer::SharedCredentialServer(asio::io_context& network,asio::any_io_executor game,
    AccountRepository& accounts,NativeAccountSnapshotRepository& account_snapshots,
    NativeCharacterSummarySnapshotRepository& character_summaries,
    RecoveredCharacterRepository& characters,const NativeMapCatalog& maps,
    const SharedServerPlan& plan,std::shared_ptr<god2::SharedWorldHost> common_world)
    :SharedCredentialServer(network,std::move(game),accounts,account_snapshots,character_summaries,
        characters,maps,plan,std::move(common_world),nullptr) {}
SharedCredentialServer::SharedCredentialServer(asio::io_context& network,asio::any_io_executor game,
    AccountRepository& accounts,NativeAccountSnapshotRepository& account_snapshots,
    NativeCharacterSummarySnapshotRepository& character_summaries,
    RecoveredCharacterRepository& characters,const NativeMapCatalog& maps,
    const SharedServerPlan& plan,std::shared_ptr<god2::SharedWorldHost> common_world,
    const god2::NativeSkillCatalog& native_skills)
    :SharedCredentialServer(network,std::move(game),accounts,account_snapshots,character_summaries,
        characters,maps,plan,std::move(common_world),&native_skills) {}
SharedCredentialServer::SharedCredentialServer(asio::io_context& network,asio::any_io_executor game,
    AccountRepository& accounts,NativeAccountSnapshotRepository& account_snapshots,
    NativeCharacterSummarySnapshotRepository& character_summaries,
    RecoveredCharacterRepository& characters,const NativeMapCatalog& maps,
    const SharedServerPlan& plan,std::shared_ptr<god2::SharedWorldHost> common_world,
    const god2::NativeSkillCatalog* native_skills) {
    if(common_world && !common_world->owns_repository(characters))
        throw std::invalid_argument("CN common world host requires the same character/presence/visibility owner");
    if(!account_snapshots.owns_accounts(accounts))
        throw std::invalid_argument("CN account snapshot source requires the same account backend");
    if(!character_summaries.owns_sources(accounts,characters))
        throw std::invalid_argument("CN character summary source requires the same account and character backend");
    if(!plan.controllers || plan.endpoints.size()<2 || !plan.max_sessions ||
       !plan.live_grants || !plan.issued_keys || !plan.authentication_workers || !plan.authentication_capacity)
        throw std::invalid_argument("CN host requires explicit budgets, endpoints and native controllers");
    std::size_t account_count=0,world_count=0;
    std::set<std::pair<asio::ip::address,std::uint16_t>> sockets;
    std::set<std::pair<std::uint16_t,std::uint16_t>> targets;
    for(const auto& endpoint:plan.endpoints) {
        const auto address=asio::ip::make_address(endpoint.host);
        if(!endpoint.port || !sockets.emplace(address,endpoint.port).second)
            throw std::invalid_argument("CN duplicate/unbound endpoint");
        if(endpoint.role==SharedServerPlan::Role::Account) {
            if(endpoint.target)throw std::invalid_argument("CN account listener has a world target");
            ++account_count;
        } else if(endpoint.role==SharedServerPlan::Role::World) {
            if(!endpoint.target || endpoint.target->group>=64 || endpoint.target->server>=10 ||
               !targets.emplace(endpoint.target->group,endpoint.target->server).second)
                throw std::invalid_argument("CN world listener lacks unique catalog destination");
            ++world_count;
        } else throw std::invalid_argument("CN unqualified listener role");
    }
    if(account_count!=1 || !world_count)throw std::invalid_argument("CN host requires one account and actual world endpoints");
    std::shared_ptr<const CnSharedSkillCatalog> qualified_skills;
    if(plan.native_skill_definitions) {
        if(!native_skills || !plan.native_skill_store_lifetime || !plan.native_skill_store_current)
            throw std::invalid_argument("CN skill definitions require the actual shared SQLite reader");
        qualified_skills=CnSharedSkillCatalog::bind_actual_shared_store(*native_skills,plan.native_skill_definitions,
            plan.native_skill_store_lifetime,plan.native_skill_store_current);
        if(!qualified_skills)
            throw std::invalid_argument("CN actual shared skill definitions missing or conflicting");
    } else if(plan.native_skill_store_lifetime || plan.native_skill_store_current) {
        throw std::invalid_argument("CN skill store qualification supplied without native definitions");
    }
    auto admission=std::make_shared<SharedWorldAdmission>(plan.live_grants,plan.issued_keys);
    verifier_=std::make_unique<SharedAccountVerifier>(accounts,game,plan.authentication_workers,plan.authentication_capacity);
    state_=std::make_shared<State>(*verifier_,SharedServerPlan::Controllers{},admission,plan.max_sessions,
        std::move(common_world),std::move(qualified_skills));
    // Bind/listen before invoking the native-source factory, but do not start
    // accepting until every controller exists. Constructor failure closes all
    // partially prepared listeners via member ownership on this game thread.
    listener_=std::make_shared<Listener>(network,game,state_,plan.endpoints);
    std::vector<BoundEndpoint> bound;
    for(const auto& port:listener_->ports)
        bound.push_back({port->endpoint.role,port->endpoint.target,port->acceptor.local_endpoint()});
    registry_=std::shared_ptr<SharedListenerRegistry>(new SharedListenerRegistry(std::move(bound)));
    auto controllers=plan.controllers({accounts,account_snapshots,character_summaries,characters,maps,admission,game,plan.endpoints,registry_,state_->common_world,native_skills,state_->cn_native_skills});
    if(state_->cn_native_skills && !state_->cn_native_skills->current())
        throw std::invalid_argument("CN native skill source retired during controller construction");
    if(!controllers.seed || !controllers.account || !controllers.world || !controllers.account_configuration ||
       !controllers.account_configuration->network_version() ||
       *controllers.account_configuration->network_version()!=god2cn::CnAccountWire::native_config_version)
        throw std::invalid_argument("CN native seed/account/world controllers missing");
    state_->controllers=std::move(controllers);
}
SharedCredentialServer::~SharedCredentialServer() {
    if(thread_!=std::this_thread::get_id())std::terminate();
    stop();
    state_.reset(); // Controller and connection destruction stays on game owner.
}
void SharedCredentialServer::start() {
    owner();
    if(state_->started || state_->stopping)return;
    if(state_->cn_native_skills && !state_->cn_native_skills->current())
        throw std::invalid_argument("CN native skill source retired before listener start");
    asio::post(listener_->strand,[listener=listener_] {listener->start();});
    state_->started=true;
    registry_->start();
}
std::vector<SharedCredentialServer::BoundEndpoint> SharedCredentialServer::bound_endpoints() const {
    owner();return registry_->bound_endpoints();
}
void SharedCredentialServer::stop() {
    owner();
    if(state_->stopping)return;
    state_->stopping=true;
    registry_->stop(); // Invalidate publication BEFORE asynchronous socket close.
    for(const auto& [id,connection]:state_->connections)connection->close();
    asio::post(listener_->strand,[listener=listener_] {listener->stop();});
}
}
