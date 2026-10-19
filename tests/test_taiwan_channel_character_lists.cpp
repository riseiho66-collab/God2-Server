#include "game/TaiwanChannelCharacterLists.h"
#include "protocol/RecoveredServerRoutes.h"
#include "protocol/RecoveredSeedExchange.h"
#include "protocol/RecoveredPostSeed.h"
#include "protocol/RecoveredLoginTerminal.h"
#include "protocol/RecoveredWorldFrame.h"
#include <chrono>
#include <algorithm>
#include <array>
#include <map>
#include <stdexcept>
#include <thread>
#include <utility>
#include <vector>

namespace {
using namespace god2;using Router=TaiwanChannelCharacterLists;using Delivery=Session::NativeCharacterList;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class E,class F> bool refuses(F&& f){try{f();}catch(const E&){return true;}return false;}
constexpr std::uint64_t account=0x100000007ULL;
auto list_frame(){std::array<std::uint8_t,75> logical{};logical[0]=7;const auto wire=RecoveredWorldFrame::encode(logical);
    std::array<std::uint8_t,78> result{};std::copy(wire.begin(),wire.end(),result.begin());return result;}
// Public delivery construction and fixed synthetic login are TEST routing
// material, never original auth/entitlement. Actual Session alone mints private
// A6, written-advertisement, socket Written and canonical completion pointers.
struct Issuers:std::enable_shared_from_this<Issuers> {
    std::array<unsigned,3> lists{},currents{},false_completions{},commits{},disconnects{},selections{};
    std::array<Delivery,3> last{};
    std::array<std::map<const Session*,Delivery>,3> pending;
    std::function<void(Session&)> current_hook,complete_hook;
    bool reject_current=false,throw_false=false,throw_disconnect=false;
    std::uint64_t sequence=0;
    Router::Binding nested;
    std::array<Router::Source,3> sources(){
        std::array<Router::Source,3> out;const auto self=shared_from_this();
        for(std::uint8_t k=0;k<3;++k){
            out[k].native_list=[self,k](Session& session){
                ++self->lists[k];auto delivery=std::make_shared<const Session::NativeCharacterListDelivery>(
                    Session::NativeCharacterListDelivery{session.id(),session.account_id,++self->sequence,list_frame(),session.recovered_server_selection()});
                self->pending[k][&session]=delivery;self->last[k]=delivery;return delivery;
            };
            out[k].native_list_current=[self,k](Session& session,const Delivery& delivery){
                ++self->currents[k];if(auto hook=std::exchange(self->current_hook,{}))hook(session);
                const auto found=self->pending[k].find(&session);
                return !self->reject_current&&!session.closing()&&found!=self->pending[k].end()&&found->second==delivery;
            };
            out[k].native_list_complete=[self,k](Session& session,const Delivery& delivery,bool written){
                const auto found=self->pending[k].find(&session);
                const bool exact=found!=self->pending[k].end()&&found->second==delivery;
                if(exact)self->pending[k].erase(found);
                if(!written){++self->false_completions[k];if(self->throw_false)throw std::runtime_error("Expected synthetic false cleanup failure");return false;}
                if(auto hook=std::exchange(self->complete_hook,{}))hook(session);
                const bool accepted=exact&&!session.closing()&&session.recovered_native_character_list_written()==delivery;
                if(accepted)++self->commits[k];return accepted;
            };
            out[k].on_disconnect=[self,k](std::shared_ptr<Session> session){
                ++self->disconnects[k];self->pending[k].erase(session.get());
                if(self->throw_disconnect&&k==0)throw std::runtime_error("Expected first cleanup failure");
            };
            out[k].native_select=[self,k](Session&,const RecoveredPostCreateSelect::Selection&,std::optional<std::uint64_t>)->std::uint64_t{
                ++self->selections[k];return 0; // Always denies; tests grant no native selection rights.
            };
        }return out;
    }
};
struct Peer {
    asio::io_context io;asio::ip::tcp::acceptor acceptor{io,{asio::ip::address_v4::loopback(),0}};
    asio::ip::tcp::socket client{io};std::shared_ptr<Session> session;std::vector<std::uint8_t> advertised;
    Peer(const Router::Binding& binding,std::uint64_t id,std::uint16_t mask=7){
        const std::array<RecoveredServerRoutes::ChannelEndpoint,3> endpoints{{
            {{127,0,0,1},2593,1,{0x11,1,2,3}},{{127,0,0,1},2594,2,{0x12,4,5,6}},{{127,0,0,1},2595,3,{0x13,7,8,9}}}};
        const auto ad=RecoveredServerRoutes::wire_three_channels({2,0x92,static_cast<std::uint8_t>(mask),static_cast<std::uint8_t>(mask>>8)},endpoints);
        advertised.assign(ad.begin(),ad.end());client.connect(acceptor.local_endpoint());auto socket=acceptor.accept();
        Session::RecoveredCharacterHandlers h;h.native_list=binding.list;h.native_list_current=binding.current;
        h.native_list_complete=binding.complete;h.native_select=binding.select;
        h.create=[](std::uint64_t,const RecoveredCharacterCreate&)->std::uint64_t{throw std::runtime_error("No synthetic creation rights");};
        session=std::make_shared<Session>(std::move(socket),io.get_executor(),id,false,Session::PacketHandler{},binding.disconnected,
            ProtocolMode::God2LegacyCharacterListCandidate,[](const RecoveredC2S0002::Parsed&){return account;},std::move(h),advertised);
        client.non_blocking(true);session->start();
    }
    void one(){io.restart();io.poll_one();}
    template<class Predicate>void until(Predicate predicate){const auto end=std::chrono::steady_clock::now()+std::chrono::seconds(3);
        while(!predicate()&&std::chrono::steady_clock::now()<end)one();require(predicate(),"Bounded actual Session transition did not complete");}
    void send(std::span<const std::uint8_t> wire){client.non_blocking(false);asio::write(client,asio::buffer(wire.data(),wire.size()));client.non_blocking(true);}
    void expect(std::span<const std::uint8_t> expected){
        std::vector<std::uint8_t> actual(expected.size());std::size_t at=0;
        until([&]{if(at==actual.size())return true;asio::error_code error;at+=client.read_some(asio::buffer(actual.data()+at,actual.size()-at),error);
            require(!error||error==asio::error::would_block||error==asio::error::try_again,"Actual account socket closed before expected response");return at==actual.size();});
        require(std::equal(actual.begin(),actual.end(),expected.begin()),"Actual account socket bytes changed");
    }
    void authenticate(){
        expect(RecoveredSeedExchange::hello());send(RecoveredSeedExchange::response);expect(RecoveredPostSeed::frame());
        RecoveredC2S0002::Payload body{};body[0]=4;body[167]=0xc8;const auto wire=RecoveredC2S0002::encode(body);
        const auto parsed=RecoveredC2S0002::parse(wire);require(bool(parsed),"Synthetic complete login frame unavailable");
        send(wire);expect(*RecoveredC2S0002::response(*parsed));expect(advertised);expect(RecoveredLoginTerminal::success());
    }
    void choose(std::uint8_t channel,std::uint8_t group=2){send(RecoveredWorldFrame::encode(std::array<std::uint8_t,3>{0xa6,group,channel}));}
    void written(){expect(list_frame());until([&]{return bool(session->recovered_native_character_list());});}
    void close(){session->close();until([&]{return session->state()==SessionState::Disconnected;});
        for(unsigned k=0;k<64;++k)one();}
    ~Peer(){asio::error_code ignored;client.close(ignored);session->close();for(unsigned k=0;k<128;++k)one();}
};
void routing_written_identity_and_select(){
    auto issuers=std::make_shared<Issuers>();auto owner=Router::create(issuers->sources(),2,4);const auto binding=owner->binding();issuers->nested=binding;
    for(std::uint8_t k=0;k<3;++k){
        Peer peer(binding,0x100000100ULL+k);peer.authenticate();peer.choose(k);peer.written();const auto delivery=issuers->last[k];
        require(delivery&&delivery==peer.session->recovered_native_character_list_written()&&issuers->lists[k]==1&&issuers->commits[k]==1,
            "Actual A6/Written list routed to another issuer");
        auto copy=std::make_shared<const Session::NativeCharacterListDelivery>(*delivery);
        require(!binding.current(*peer.session,copy)&&!binding.complete(*peer.session,copy,false)&&
            !binding.complete(*peer.session,delivery,true),"Copied delivery or repeated completion borrowed retained issuer");
        Peer impostor(binding,peer.session->id());
        require(!binding.current(*impostor.session,delivery)&&!binding.complete(*impostor.session,delivery,false)&&
            refuses<std::invalid_argument>([&]{binding.disconnected(impostor.session);}),"Same-ID foreign Session evicted actual list routing");
        require(refuses<std::invalid_argument>([&]{binding.select(*peer.session,RecoveredPostCreateSelect::Selection{},{});})&&
            issuers->selections[k]==1,"Denied native selection did not use exact completed-list issuer");
        peer.close();
        for(std::uint8_t j=0;j<3;++j)require(issuers->disconnects[j]>=k+1,"One failing/foreign issuer skipped actual disconnect cleanup");
    }
}
void failures_reentry_and_pending_capacity(){
    {
        auto issuers=std::make_shared<Issuers>();auto owner=Router::create(issuers->sources(),2,1);const auto binding=owner->binding();
        Peer first(binding,0x200000101ULL);first.authenticate();first.choose(1);first.until([&]{return bool(issuers->last[1]);});
        const auto delivery=issuers->last[1];require(!first.session->recovered_native_character_list_written(),"Fixture missed pre-Written cut");
        Peer second(binding,0x200000102ULL);second.authenticate();second.choose(2);second.until([&]{return second.session->closing();});
        require(issuers->lists[2]==0,"Pending capacity exhaustion invoked another issuer");
        require(!binding.complete(*first.session,delivery,true)&&issuers->commits[1]==0&&issuers->false_completions[1]==1&&
            issuers->false_completions[0]==0&&issuers->false_completions[2]==0,"Pre-Written completion did not clean exact failed issuer");
        first.close();second.close();
    }
    for(bool during_complete:{false,true}){
        auto issuers=std::make_shared<Issuers>();auto owner=Router::create(issuers->sources(),2,2);const auto binding=owner->binding();
        unsigned nested_refusals=0;
        auto reenter=[&](Session& session){nested_refusals+=refuses<std::logic_error>([&]{(void)binding.list(session);});};
        if(during_complete)issuers->complete_hook=reenter;else issuers->current_hook=reenter;
        Peer peer(binding,0x300000100ULL+during_complete);peer.authenticate();peer.choose(2);peer.until([&]{return peer.session->closing();});peer.close();
        require(nested_refusals==1&&issuers->commits[2]==0&&issuers->false_completions[2]==1&&issuers->pending[2].empty(),
            "Caught callback reentry committed or retained a stale list");
    }
    {
        auto issuers=std::make_shared<Issuers>();auto owner=Router::create(issuers->sources(),2,2);const auto binding=owner->binding();
        Peer peer(binding,0x600000100ULL);peer.authenticate();peer.choose(1);peer.until([&]{return bool(issuers->last[1]);});
        const auto delivery=issuers->last[1];peer.session->account_id^=std::uint64_t{1}<<32;
        require(!binding.current(*peer.session,delivery)&&issuers->commits[1]==0&&issuers->false_completions[1]==1&&
            issuers->false_completions[0]==0&&issuers->false_completions[2]==0,"Changed full account identity borrowed a pending issuer");
        peer.close();
    }
    {
        auto issuers=std::make_shared<Issuers>();auto owner=Router::create(issuers->sources(),2,2);const auto binding=owner->binding();
        Peer peer(binding,0x400000100ULL);peer.authenticate();peer.choose(0);peer.until([&]{return bool(issuers->last[0]);});
        issuers->throw_false=true;issuers->throw_disconnect=true;
        require(refuses<std::runtime_error>([&]{binding.disconnected(peer.session);}),"Disconnect failure was swallowed");
        require(issuers->false_completions[0]==1&&issuers->disconnects==std::array<unsigned,3>{1,1,1},"Throwing pending/first issuer skipped remaining cleanup");
        issuers->throw_false=false;issuers->throw_disconnect=false;peer.close();
    }
}
void selectors_owner_bounds_and_weak_facades(){
    auto issuers=std::make_shared<Issuers>();auto sources=issuers->sources();
    require(refuses<std::invalid_argument>([&]{(void)Router::create(sources,10,2);})&&
        refuses<std::invalid_argument>([&]{(void)Router::create(sources,2,0);}),"Router accepted invalid UI group/capacity");
    auto incomplete=sources;incomplete[1].native_select={};require(refuses<std::invalid_argument>([&]{(void)Router::create(incomplete,2,2);}),"Router accepted incomplete native issuer");
    auto owner=Router::create(sources,2,3);const auto binding=owner->binding();
    Peer masked(binding,0x500000100ULL,1);masked.authenticate();masked.choose(1);masked.until([&]{return masked.session->closing();});
    require(issuers->lists==std::array<unsigned,3>{},"Unavailable advertised slot defaulted to another issuer");
    Peer wrong(binding,0x500000101ULL);wrong.authenticate();wrong.choose(0,3);wrong.until([&]{return wrong.session->closing();});
    require(issuers->lists==std::array<unsigned,3>{},"Wrong group defaulted to channel0");
    unsigned foreign_refusals=0;std::thread foreign([&]{
        foreign_refusals+=refuses<std::logic_error>([&]{(void)owner->binding();});
        foreign_refusals+=refuses<std::logic_error>([&]{(void)binding.current(*wrong.session,{});});
    });foreign.join();require(foreign_refusals==2,"Router facade bypassed GAME owner checks");
    owner.reset();
    bool expired_foreign_refused=false;std::thread expired_foreign([&]{
        expired_foreign_refused=refuses<std::logic_error>([&]{(void)binding.current(*wrong.session,{});});
    });expired_foreign.join();require(expired_foreign_refused,"Retired facade skipped pure GAME check before weak owner access");
    require(refuses<std::logic_error>([&]{(void)binding.list(*wrong.session);})&&!binding.current(*wrong.session,{})&&
        !binding.complete(*wrong.session,{},false),"NET facade retained retired GAME sources");
}
} // namespace

void test_taiwan_channel_character_lists(){routing_written_identity_and_select();failures_reentry_and_pending_capacity();selectors_owner_bounds_and_weak_facades();}
