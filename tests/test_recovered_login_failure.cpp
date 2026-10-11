#include "net/Session.h"
#include "protocol/RecoveredLoginFailure.h"
#include "protocol/RecoveredSeedExchange.h"
#include "protocol/RecoveredPostSeed.h"
#include "protocol/RecoveredC2S0002.h"
#include <array>
#include <chrono>
#include <stdexcept>

void check(bool internal_error,bool asynchronous) {
    using namespace god2;
    using namespace std::chrono;
    constexpr std::array<std::uint8_t,5> native_wrong_password{5,0,0x1b,0x1e,0x16};
    if(RecoveredLoginFailure::password_mismatch()!=native_wrong_password)
        throw std::runtime_error("Native login rejection frame changed");
    asio::io_context io;
    asio::ip::tcp::acceptor acceptor(io,{asio::ip::address_v4::loopback(),0});
    asio::ip::tcp::socket peer(io);
    peer.connect(acceptor.local_endpoint());
    auto socket=acceptor.accept();
    Session::RecoveredCharacterHandlers handlers;
    if(asynchronous) handlers.authenticate_async=[&io,internal_error](const auto&,auto complete) {
        asio::post(io,[internal_error,complete] {
            complete(0,internal_error?std::make_exception_ptr(std::runtime_error("database unavailable")):std::exception_ptr{});
        });
    };
    auto session=std::make_shared<Session>(std::move(socket),io.get_executor(),1,false,
        Session::PacketHandler{},Session::DisconnectHandler{},
        ProtocolMode::God2LegacyCharacterListCandidate,
        [internal_error](const RecoveredC2S0002::Parsed&) -> std::uint64_t { if(internal_error) throw std::runtime_error("database unavailable"); return 0; },handlers);
    peer.non_blocking(true);
    session->start();
    auto receive=[&](auto expected) {
        std::size_t total=0;
        std::array<std::uint8_t,176> incoming{};
        const auto until=steady_clock::now()+seconds(2);
        while(total<expected.size() && steady_clock::now()<until) {
            io.restart();io.run_for(milliseconds(5));
            asio::error_code ec;
            total+=peer.read_some(asio::buffer(incoming.data()+total,expected.size()-total),ec);
            if(ec && ec!=asio::error::would_block && ec!=asio::error::try_again)
                throw std::runtime_error("Socket closed before login rejection");
        }
        if(total!=expected.size() || !std::equal(expected.begin(),expected.end(),incoming.begin()))
            throw std::runtime_error("Login rejection was delayed or encoded incorrectly");
    };
    receive(RecoveredSeedExchange::hello());
    peer.non_blocking(false);
    asio::write(peer,asio::buffer(RecoveredSeedExchange::response));
    peer.non_blocking(true);
    receive(RecoveredPostSeed::frame());
    RecoveredC2S0002::Payload credentials{};
    credentials[0]=4;credentials[1]='a';credentials[25]='b';credentials[167]=0xc8;
    const auto request=RecoveredC2S0002::encode(credentials);
    peer.non_blocking(false);
    asio::write(peer,asio::buffer(request));
    peer.non_blocking(true);
    receive(internal_error ? RecoveredLoginFailure::server_error() : native_wrong_password);
    const auto until=steady_clock::now()+seconds(2);
    while(session->state()!=SessionState::Disconnected && steady_clock::now()<until) {
        io.restart();io.run_for(milliseconds(5));
    }
    if(session->state()!=SessionState::Disconnected)
        throw std::runtime_error("Failed login did not close after delivering native rejection");
}
int main() { for(bool async:{false,true}) {check(false,async);check(true,async);}return 0; }
