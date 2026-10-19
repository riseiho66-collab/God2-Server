#include "net/TcpServer.h"
#include "net/SessionManager.h"
#include "net/ConnectionIdentity.h"
#include "net/NativeTaiwanChannelBinding.h"
#include <spdlog/spdlog.h>
#include <chrono>
#include <atomic>
#include <stdexcept>
#include <utility>

namespace god2 {
struct TcpServer::StopObservation::Data {
    enum class State {Pending,Complete,Aborted};
    std::atomic<State> state{State::Pending};
    std::atomic<bool> callback_failed{false};
    void mark_aborted() noexcept {
        auto pending=State::Pending;
        state.compare_exchange_strong(pending,State::Aborted,std::memory_order_acq_rel);
    }
};
bool TcpServer::StopObservation::complete() const noexcept {
    return data_&&data_->state.load(std::memory_order_acquire)==Data::State::Complete;
}
bool TcpServer::StopObservation::succeeded() const noexcept {
    return complete()&&!data_->callback_failed.load(std::memory_order_acquire);
}
bool TcpServer::StopObservation::aborted() const noexcept {
    return data_&&data_->state.load(std::memory_order_acquire)==Data::State::Aborted;
}
struct TcpServer::Impl : std::enable_shared_from_this<TcpServer::Impl> {
    asio::io_context& network;
    asio::strand<asio::io_context::executor_type> strand;
    asio::any_io_executor game;
    asio::ip::tcp::acceptor acceptor;
    asio::steady_timer retry;
    SessionManager sessions;
    Session::PacketHandler on_packet;
    Session::DisconnectHandler on_disconnect;
    Session::RecoveredLoginHandler recovered_login;
    Session::RecoveredCharacterHandlers character_handlers;
    std::vector<std::uint8_t> character_routes;
    std::shared_ptr<const NativeTaiwanChannelBinding> channel_binding;
    const bool packet_dump;
    const ProtocolMode mode;
    std::uint16_t bound_port = 0;
    asio::ip::tcp::endpoint bound_endpoint;
    bool started = false;
    bool stopped = false;
    bool accept_pending=false,retry_pending=false,observed=false,marker_posted=false;
    const std::shared_ptr<StopObservation::Data> stop_state=std::make_shared<StopObservation::Data>();

    Impl(asio::io_context& network_, asio::any_io_executor game_,
         const std::string& host, std::uint16_t port, std::size_t max_sessions,
         bool dump, Session::PacketHandler packet, Session::DisconnectHandler disconnect,ProtocolMode mode_,
         Session::RecoveredLoginHandler login,Session::RecoveredCharacterHandlers characters,
         std::vector<std::uint8_t> routes)
        : network(network_), strand(asio::make_strand(network_)),
          game(asio::make_strand(std::move(game_))), acceptor(strand), retry(strand),
          sessions(max_sessions), on_packet(std::move(packet)),
          on_disconnect(std::move(disconnect)), recovered_login(std::move(login)), character_handlers(std::move(characters)), character_routes(std::move(routes)), packet_dump(dump),mode(mode_) {
        if(is_recovered(mode) && !asio::ip::make_address(host).is_loopback())
            throw std::invalid_argument("Recovered lab mode requires loopback");
        if (max_sessions == 0) throw std::invalid_argument("max_sessions must be positive");
        asio::ip::tcp::resolver resolver(network);
        const auto endpoints = resolver.resolve(host, std::to_string(port),
                                                asio::ip::tcp::resolver::passive);
        asio::error_code last_error = asio::error::host_not_found;
        for (const auto& resolved : endpoints) {
            asio::error_code ec;
            acceptor.open(resolved.endpoint().protocol(), ec);
            if (!ec) acceptor.set_option(asio::socket_base::reuse_address(true), ec);
            if (!ec) acceptor.bind(resolved.endpoint(), ec);
            if (!ec) acceptor.listen(asio::socket_base::max_listen_connections, ec);
            if (!ec) { bound_endpoint=acceptor.local_endpoint();bound_port = bound_endpoint.port(); return; }
            last_error = ec;
            acceptor.close(ec);
        }
        throw asio::system_error(last_error);
    }
    void start() {
        if (started || stopped) return;
        started = true;
        accept();
    }
    void abort() noexcept {
        // Infrastructure failure is terminal but never a clean-drain receipt.
        stop_state->mark_aborted();
        stopped=true;
        if(channel_binding)channel_binding->retire();
        asio::error_code ignored;acceptor.close(ignored);
        try{retry.cancel();}catch(...){}
        try{sessions.close_all();}catch(...){}
    }
    void maybe_complete() {
        if(!observed||!stopped||accept_pending||retry_pending||sessions.size()||marker_posted||
           stop_state->state.load()!=StopObservation::Data::State::Pending)return;
        marker_posted=true;
        try {
            // This marker carries only pure state/executors, no GAME owners.
            // Retain both run loops until it acknowledges the final NET job.
            auto network_work=asio::make_work_guard(network);
            auto game_work=asio::make_work_guard(game);
            asio::post(game,[state=stop_state,network_work=std::move(network_work),game_work=std::move(game_work)]() mutable {
                auto pending=StopObservation::Data::State::Pending;
                state->state.compare_exchange_strong(pending,StopObservation::Data::State::Complete,std::memory_order_acq_rel);
                network_work.reset();game_work.reset();
            });
        }catch(...){abort();}
    }
    void wait_retry() {
        retry.expires_after(std::chrono::milliseconds(250));
        retry_pending=true;
        try {
            retry.async_wait([self=shared_from_this()](const asio::error_code& error) {
                self->retry_pending=false;
                if(!error&&!self->stopped)self->accept();
                else if(error&&!self->stopped)self->abort();
                self->maybe_complete();
            });
        }catch(...){retry_pending=false;abort();}
    }
    void accept() {
        if (stopped) return;
        // A plain network executor here avoids nesting every session beneath
        // the acceptor strand, which would serialize all socket traffic.
        accept_pending=true;
        try {acceptor.async_accept(network, asio::bind_executor(strand,
            [self = shared_from_this()](const asio::error_code& ec, asio::ip::tcp::socket socket) {
                self->accept_pending=false;
                if (self->stopped) {
                    asio::error_code ignored;socket.close(ignored);
                    self->maybe_complete();return;
                }
                if (ec) {
                    try{self->wait_retry();}catch(...){self->abort();}
                    return;
                }
                bool registered=false;
                try {
                    asio::error_code ignored;
                    socket.set_option(asio::ip::tcp::no_delay(true), ignored);
                    auto weak = std::weak_ptr<Impl>(self);
                    auto session = std::make_shared<Session>(std::move(socket), self->game,
                        next_connection_identity(), self->packet_dump, self->on_packet,
                        self->on_disconnect,self->mode,self->recovered_login,self->character_handlers,self->character_routes,self->channel_binding,
                        [weak](std::shared_ptr<Session> session,bool clean) {
                            // GAME has finished all actual disconnect callbacks.
                            // NET must acknowledge exact removal before the final
                            // GAME marker may publish completion.
                            if (auto server = weak.lock()) {
                                try {
                                    asio::post(server->strand, [server,session=std::move(session),clean] {
                                        if(!clean)server->stop_state->callback_failed.store(true,std::memory_order_release);
                                        if(!server->sessions.remove(session)){server->abort();return;}
                                        server->maybe_complete();
                                    });
                                }catch(...){
                                    // Called on GAME: only atomics here, never
                                    // touch the acceptor strand from this catch.
                                    server->stop_state->mark_aborted();
                                    throw;
                                }
                            }
                        });
                    registered=self->sessions.add(session);
                    if(registered)session->start();
                    // A rejected session has never entered the application and
                    // is destroyed here without a disconnect notification.
                } catch (const std::exception& e) {
                    try{
                        auto log = spdlog::get("network");
                        if (!log) log = spdlog::default_logger();
                        if (log) log->error("accept session failed: {}", e.what());
                    }catch(...){}
                    // A never-registered constructor refusal keeps the prior
                    // accept policy. A registered start failure cannot be
                    // dropped from custody or counted as a clean disconnect.
                    if(registered){self->abort();return;}
                } catch(...) {
                    self->abort();return;
                }
                self->accept();
            }));}catch(...){accept_pending=false;abort();}
    }
    void stop() {
        if (stopped) {maybe_complete();return;}
        stopped = true;
        asio::error_code ignored;
        acceptor.close(ignored);
        try{retry.cancel();sessions.close_all();}catch(...){abort();return;}
        maybe_complete();
    }
};

TcpServer::TcpServer(asio::io_context& network, asio::any_io_executor game_executor,
                     const std::string& host, std::uint16_t port,
                     std::size_t max_sessions, bool packet_dump,
                     Session::PacketHandler on_packet, Session::DisconnectHandler on_disconnect,ProtocolMode mode,
                     Session::RecoveredLoginHandler recovered_login,Session::RecoveredCharacterHandlers characters,
                     std::vector<std::uint8_t> character_routes)
    : impl_(std::make_shared<Impl>(network, std::move(game_executor), host, port, max_sessions,
                                  packet_dump, std::move(on_packet), std::move(on_disconnect),mode,std::move(recovered_login),std::move(characters),std::move(character_routes))) {}
TcpServer::~TcpServer() { stop(); }
void TcpServer::start() {
    asio::post(impl_->strand, [impl = impl_] { impl->start(); });
}
void TcpServer::stop() {
    if(impl_->channel_binding)impl_->channel_binding->retire();
    asio::post(impl_->strand, [impl = impl_] { impl->stop(); });
}
TcpServer::StopObservation TcpServer::stop_observed() {
    if(impl_->channel_binding)impl_->channel_binding->retire();
    if(impl_->stop_state->state.load(std::memory_order_acquire)!=StopObservation::Data::State::Pending)
        return StopObservation(impl_->stop_state);
    try{asio::post(impl_->strand,[impl=impl_]{impl->observed=true;impl->stop();});}
    catch(...){impl_->stop_state->mark_aborted();throw;}
    return StopObservation(impl_->stop_state);
}
std::uint16_t TcpServer::port() const noexcept { return impl_->bound_port; }
asio::ip::tcp::endpoint TcpServer::bound_endpoint() const noexcept {return impl_->bound_endpoint;}
void TcpServer::bind_native_channel(std::shared_ptr<SharedWorldPresence> presence,std::uint8_t group,std::uint8_t channel) {
    if(impl_->started||impl_->stopped||impl_->channel_binding||impl_->mode!=ProtocolMode::God2CharacterConnection)
        throw std::logic_error("Native channel must bind once before listener start");
    impl_->channel_binding=std::shared_ptr<const NativeTaiwanChannelBinding>(
        new NativeTaiwanChannelBinding(std::move(presence),group,channel,impl_->bound_endpoint));
}
void TcpServer::discard_unstarted() {
    if(impl_->started)throw std::logic_error("Cannot discard a started listener synchronously");
    if(impl_->channel_binding)impl_->channel_binding->retire();
    impl_->stop();
}
} // namespace god2
