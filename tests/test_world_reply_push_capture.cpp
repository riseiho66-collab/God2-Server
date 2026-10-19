#include "net/Session.h"
#include "protocol/RecoveredCharacterBootstrap.h"
#include "protocol/RecoveredCharacterCreateResult.h"
#include "protocol/RecoveredPostSeed.h"
#include "protocol/RecoveredSeedExchange.h"
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <functional>
#include <limits>
#include <memory>
#include <optional>
#include <span>
#include <stdexcept>
#include <type_traits>
#include <utility>
#include <variant>
#include <vector>

namespace {
using namespace god2;
using Bytes=std::vector<std::uint8_t>;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class F> bool refuses(F&& call){try{call();}catch(const std::exception&){return true;}return false;}
Bytes row(std::uint8_t value){return {0x73,value,0,0,0};}
Bytes framed(std::span<const std::uint8_t> logical){return RecoveredWorldFrame::encode(logical);}
void append(Bytes& target,std::span<const std::uint8_t> part){target.insert(target.end(),part.begin(),part.end());}

// Minimal DB-free version of test_session_state.cpp's real socket fixture.
// The explicit lab framer and synthetic admission exercise Session custody,
// not client/native gameplay, durable saves or any granted world authority.
struct Peer {
    using Handler=std::function<std::optional<Bytes>(Session&,std::span<const RecoveredWorldRecords::Record>)>;
    static constexpr std::uint64_t account=0x100000007ULL,character=0x200001234ULL;
    static constexpr std::uint16_t scene_handle=0x1234;
    static constexpr std::uint64_t common_generation=11,world_generation=21;
    asio::io_context io;
    asio::ip::tcp::acceptor acceptor{io,{asio::ip::address_v4::loopback(),0}};
    asio::ip::tcp::socket socket{io};
    std::shared_ptr<Session> session;
    const RecoveredWorldEntry::Frame entry=RecoveredWorldEntry::wire(scene_handle);
    unsigned ready_calls=0,world_calls=0,select_calls=0;

    explicit Peer(Handler handle){
        socket.connect(acceptor.local_endpoint());auto accepted=acceptor.accept();
        Session::RecoveredCharacterHandlers h;
        h.list=[](std::uint64_t){return std::array<std::uint8_t,78>{};};
        h.create=[](std::uint64_t,const RecoveredCharacterCreate&)->std::uint64_t{
            throw std::runtime_error("Capture fixture provides no character creation");
        };
        h.select_created=[](std::uint64_t,std::uint64_t,std::uint8_t)->std::uint64_t{
            throw std::runtime_error("Capture fixture provides no created-character selection");
        };
        h.select_existing=[this](std::uint64_t owner,std::uint8_t token){
            require(owner==account&&token==0,"Capture fixture selection changed full owner/token");
            ++select_calls;return character;
        };
        h.world_entry=[this](std::uint64_t,std::uint64_t owner,std::uint64_t selected){
            require(owner==account&&selected==character,"Capture fixture entry narrowed full identity");return entry;
        };
        h.world_ready=[this](Session& actual){
            require(actual.account_id==account&&actual.character_id==character,"Capture fixture readiness lost full identity");++ready_calls;
        };
        h.world_records=[this,handle=std::move(handle)](Session& actual,auto input){
            require(ready_calls==1&&actual.account_id==account&&actual.character_id==character,
                "Capture callback preceded actual authenticated readiness");
            ++world_calls;return handle(actual,input);
        };
        auto lifecycle=std::make_shared<Session::CommonWorldLifecycle>();
        lifecycle->prepared=[this](Session& actual,const auto& frame){
            return actual.account_id==account&&actual.character_id==character&&frame==entry;
        };
        lifecycle->prepared_actor=[this](Session&,const auto& frame)->std::optional<std::uint16_t>{
            return frame==entry?std::optional<std::uint16_t>{scene_handle}:std::nullopt;
        };
        lifecycle->ready_async=[](Session& actual,auto complete){
            actual.set_state(SessionState::InWorld);
            actual.bind_common_world_delivery_identity(account,character,common_generation);
            actual.bind_world_delivery_identity({account,character,world_generation,actual.battle_generation()});
            complete(true);
        };
        lifecycle->cancel=[](Session&){};h.common_world_lifecycle=std::move(lifecycle);
        session=std::make_shared<Session>(std::move(accepted),io.get_executor(),0x300000002ULL,false,
            Session::PacketHandler{},Session::DisconnectHandler{},ProtocolMode::God2CharacterConnection,
            [](const RecoveredC2S0002::Parsed& request){
                require(request.logical[0]==0,"Capture fixture login opcode changed");return account;
            },std::move(h));
        socket.non_blocking(true);session->start();
    }
    ~Peer(){
        asio::error_code ignored;socket.close(ignored);session->close();
        io.restart();io.run_for(std::chrono::milliseconds(20));
    }
    void pump(){io.restart();io.run_for(std::chrono::milliseconds(5));}
    void send(std::span<const std::uint8_t> bytes){
        socket.non_blocking(false);asio::write(socket,asio::buffer(bytes.data(),bytes.size()));socket.non_blocking(true);
    }
    void expect(std::span<const std::uint8_t> expected){
        Bytes actual(expected.size());std::size_t at=0;
        const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(2);
        while(at<actual.size()&&std::chrono::steady_clock::now()<deadline){
            pump();asio::error_code error;at+=socket.read_some(asio::buffer(actual.data()+at,actual.size()-at),error);
            require(!error||error==asio::error::would_block||error==asio::error::try_again,"Capture output closed before final reply");
        }
        require(at==actual.size()&&std::equal(actual.begin(),actual.end(),expected.begin()),"Captured final FIFO bytes changed");
    }
    void silent(){
        for(unsigned i=0;i<10;++i){
            pump();std::array<std::uint8_t,256> bytes{};asio::error_code error;
            const auto count=socket.read_some(asio::buffer(bytes),error);
            require(!count&&(error==asio::error::would_block||error==asio::error::try_again),"Capture leaked a side write or closed unexpectedly");
        }
    }
    void closed_without_output(){
        const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(2);
        while(session->state()!=SessionState::Disconnected&&std::chrono::steady_clock::now()<deadline)pump();
        require(session->state()==SessionState::Disconnected,"Invalid captured output did not fail closed");
        std::array<std::uint8_t,256> bytes{};asio::error_code error;
        const auto count=socket.read_some(asio::buffer(bytes),error);
        require(!count&&(error==asio::error::eof||error==asio::error::connection_reset),"Failed capture leaked bytes before closing");
    }
    void ready(){
        expect(RecoveredSeedExchange::hello());send(RecoveredSeedExchange::response);expect(RecoveredPostSeed::frame(0xf6));
        RecoveredC2S0002::Payload credentials{};credentials[167]=0xc8;send(RecoveredC2S0002::encode(credentials));
        expect(RecoveredCharacterBootstrap::candidate());
        std::array<std::uint8_t,38> selected{};selected[0]=0x1a;selected[34]=4;send(framed(selected));
        expect(RecoveredCharacterCreateResult::committed_success());expect(entry);
        require(select_calls==1&&session->account_id==account&&session->character_id==character,"Capture fixture selection lost high64 identity");
        send(framed(std::array<std::uint8_t,9>{0x1f,0,0x23,0,0x1c,
            static_cast<std::uint8_t>(scene_handle),static_cast<std::uint8_t>(scene_handle>>8),1,0}));
        silent();require(ready_calls==1&&session->recovered_world_ready()&&session->state()==SessionState::InWorld,
            "Capture fixture did not traverse original2A/tail readiness");
    }
    void invoke(){send(framed(std::array<std::uint8_t,2>{0x30,0}));}
};

Session::WorldReplyPushWire profile(unsigned& calls){
    return [&calls](Session& actual,std::span<const std::uint8_t> logical)->std::optional<Bytes>{
        require(actual.account_id==Peer::account&&actual.character_id==Peer::character,"Explicit capture framer lost full64 source");
        ++calls;return framed(logical);
    };
}
void accepted(Session& actual,const Bytes& logical,std::function<void(bool)> callback){
    // The real Application sender re-observes/rebinds this same delivery tuple
    // before a push. A fresh holder with equal values is not a new generation.
    actual.bind_world_delivery_identity({Peer::account,Peer::character,Peer::world_generation,actual.battle_generation()});
    actual.send_world_records_with_acceptance(logical,Peer::account,Peer::character,Peer::world_generation,
        actual.battle_generation(),std::move(callback));
}

struct Acknowledgements {
    unsigned yes=0,no=0;bool inside=false,early=false;
    std::vector<char> order;
    std::function<void(bool)> callback(char tag,bool throwing=false){
        return [this,tag,throwing](bool value){
            early|=inside;value?++yes:++no;order.push_back(tag);
            if(throwing)throw std::runtime_error("Expected fixture acknowledgement exception");
        };
    }
};
struct CallbackExtent {
    bool& active;
    explicit CallbackExtent(bool& value):active(value){active=true;}
    ~CallbackExtent(){active=false;}
};

void final_fifo_and_original_callback_order(){
    unsigned encodings=0,callbacks=0;Acknowledgements ack;
    Peer other([](Session&,auto)->std::optional<Bytes>{throw std::runtime_error("Other peer received unprovided input");});
    other.ready();
    const auto prefix=framed(row(11)),first=framed(row(12)),second=framed(row(13)),
        third=framed(row(14)),suffix=framed(row(15)),next=framed(row(16));
    Peer peer([&](Session& actual,auto input)->std::optional<Bytes>{
        require(input.size()==1&&std::holds_alternative<RecoveredWorldRecords::Tick>(input.front()),"Capture changed original input occurrence");
        if(++callbacks==2)return next;
        require(callbacks==1,"Original callback was replayed");
        CallbackExtent extent(ack.inside);auto capture=actual.capture_world_reply_pushes(profile(encodings));
        actual.send_world_records(row(12));
        accepted(actual,row(13),ack.callback('a',true));
        accepted(actual,row(14),ack.callback('b'));
        other.session->send_world_records(row(90)); // Real other Session keeps its original sender.
        auto middle=capture.finish(prefix.size());
        Bytes expected=first;append(expected,second);append(expected,third);
        require(middle==expected&&encodings==3&&!ack.yes&&!ack.no,"Capture acknowledged or rewrote pushes inside original callback");
        Bytes final=prefix;append(final,middle);append(final,suffix);return final;
    });
    peer.ready();peer.invoke();peer.invoke();
    Bytes expected=prefix;append(expected,first);append(expected,second);append(expected,third);append(expected,suffix);append(expected,next);
    peer.expect(expected);peer.silent();other.expect(framed(row(90)));other.silent();
    require(callbacks==2&&peer.world_calls==2&&encodings==3&&ack.yes==2&&!ack.no&&!ack.early&&
        ack.order==std::vector<char>{'a','b'},"Final FIFO acceptance was early, duplicated, skipped or reordered after a throwing callback");
    peer.session->close();peer.pump();
    require(ack.yes==2&&!ack.no,"Later Session close reacknowledged settled captured pushes");
}

void empty_scope_and_relative_base(){
    unsigned encodings=0;Acknowledgements ack;const auto prefix=framed(row(21)),middle=framed(row(22)),suffix=framed(row(23));
    Peer peer([&](Session& actual,auto)->std::optional<Bytes>{
        CallbackExtent extent(ack.inside);
        {auto empty=actual.capture_world_reply_pushes(profile(encodings));require(empty.finish(0).empty(),"Empty capture invented output");}
        Bytes result=prefix;
        {
            auto offset=actual.callback_reply_output_offset(prefix.size());
            auto capture=actual.capture_world_reply_pushes(profile(encodings));
            accepted(actual,row(22),ack.callback('a'));
            append(result,capture.finish(0));
        }
        append(result,suffix);require(!ack.yes&&!ack.no,"Relative capture acknowledged before returning final bytes");return result;
    });
    peer.ready();peer.invoke();Bytes expected=prefix;append(expected,middle);append(expected,suffix);
    peer.expect(expected);peer.silent();require(encodings==1&&ack.yes==1&&!ack.no&&!ack.early,"Empty/base-offset capture changed framing or acceptance");
}

void finished_old_scope_cannot_poison_successor(){
    unsigned encodings=0,callbacks=0;Acknowledgements ack;
    std::unique_ptr<Session::WorldReplyPushCapture> old_scope;
    Peer peer([&](Session& actual,auto)->std::optional<Bytes>{
        CallbackExtent extent(ack.inside);
        if(++callbacks==1){
            // C++20 guaranteed elision constructs the nonmove RAII object in
            // its final allocation. It was minted in the actual TLS callback.
            old_scope.reset(new Session::WorldReplyPushCapture(actual.capture_world_reply_pushes(profile(encodings))));
            accepted(actual,row(24),ack.callback('a'));return old_scope->finish(0);
        }
        require(callbacks==2&&old_scope&&ack.yes==1&&!ack.no,"Successor did not follow the first actual FIFO acknowledgement");
        auto current=actual.capture_world_reply_pushes(profile(encodings));
        accepted(actual,row(25),ack.callback('b'));
        old_scope->invalidate();old_scope.reset();
        return current.finish(0);
    });
    peer.ready();peer.invoke();peer.expect(framed(row(24)));peer.silent();
    require(old_scope&&ack.yes==1&&!ack.no,"Finished first scope lost its settled handle");
    peer.invoke();peer.expect(framed(row(25)));peer.silent();
    require(callbacks==2&&encodings==2&&!old_scope&&ack.yes==2&&!ack.no&&!ack.early&&
        ack.order==std::vector<char>{'a','b'},"Stale finished scope poisoned or reacknowledged a successor capture");
}

enum class Failure {Drop,Invalidate,Nested,ProfileThrow,ProfileReentry,ProfileNull,ProfileLength,
    WrongOffset,OverflowOffset,AlteredFinal,Account,Character,ExpectedAccount,ExpectedCharacter,Delivery,AfterFinishAccount,Observed,FrameBudget};

void refused_capture(Failure failure){
    unsigned encodings=0;bool caught=false;Acknowledgements ack;
    const auto frame_limit=Session::common_world_publication_capacity();
    require(frame_limit&&frame_limit<=4096,"Unbounded fixture producer budget");
    Peer peer([&](Session& actual,auto)->std::optional<Bytes>{
        try{
            auto encoder=[&](Session& source,std::span<const std::uint8_t> logical)->std::optional<Bytes>{
                require(&source==&actual,"Capture framer borrowed another Session");++encodings;
                if(encodings==2){
                    if(failure==Failure::ProfileThrow)throw std::runtime_error("Expected explicit framer failure");
                    if(failure==Failure::ProfileReentry)source.send_world_records(row(99));
                    if(failure==Failure::ProfileNull)return {};
                    if(failure==Failure::ProfileLength){auto bytes=framed(logical);bytes.push_back(0);return bytes;}
                }
                return framed(logical);
            };
            auto capture=actual.capture_world_reply_pushes(encoder);
            accepted(actual,row(31),ack.callback('a',true));
            if(failure==Failure::ExpectedAccount||failure==Failure::ExpectedCharacter)
                actual.send_world_records_with_acceptance(row(32),
                    Peer::account^(failure==Failure::ExpectedAccount?std::uint64_t{1}<<32:0),
                    Peer::character^(failure==Failure::ExpectedCharacter?std::uint64_t{1}<<32:0),
                    Peer::world_generation,actual.battle_generation(),ack.callback('b'));
            if(failure==Failure::Drop)return Bytes{};
            if(failure==Failure::Invalidate)capture.invalidate();
            if(failure==Failure::Nested){auto nested=actual.capture_world_reply_pushes(encoder);(void)nested;}
            if(failure==Failure::Observed)(void)actual.send_world_records_observed(row(32));
            if(failure==Failure::ProfileThrow||failure==Failure::ProfileReentry||failure==Failure::ProfileNull||failure==Failure::ProfileLength)
                actual.send_world_records(row(32));
            if(failure==Failure::Account)actual.account_id^=std::uint64_t{1}<<32;
            if(failure==Failure::Character)actual.character_id^=std::uint64_t{1}<<32;
            if(failure==Failure::Delivery)actual.bind_world_delivery_identity({Peer::account,Peer::character,Peer::world_generation+1,actual.battle_generation()});
            if(failure==Failure::FrameBudget){
                for(std::size_t i=0;i<frame_limit;++i)actual.send_world_records(row(32));
            }
            const auto offset=failure==Failure::OverflowOffset?std::numeric_limits<std::size_t>::max():
                failure==Failure::WrongOffset?std::size_t{1}:std::size_t{0};
            auto result=capture.finish(offset);
            if(failure==Failure::AlteredFinal)result=framed(row(33)); // Valid envelope, wrong exact captured slice.
            if(failure==Failure::AfterFinishAccount)actual.account_id^=std::uint64_t{1}<<32;
            return result;
        }catch(const std::exception&){caught=true;return Bytes{};}
    });
    peer.ready();peer.invoke();peer.closed_without_output();
    const bool wrong_expected=failure==Failure::ExpectedAccount||failure==Failure::ExpectedCharacter;
    const unsigned refusals=wrong_expected?2u:1u;
    require(peer.world_calls==1&&!ack.yes&&ack.no==refusals&&ack.order==(wrong_expected?std::vector<char>{'a','b'}:std::vector<char>{'a'}),
        "Failed capture leaked/duplicated a producer acknowledgement or replayed the callback");
    const bool final_only=failure==Failure::Drop||failure==Failure::WrongOffset||failure==Failure::AlteredFinal||failure==Failure::AfterFinishAccount;
    require(final_only||caught,"Invalid live capture was not refused synchronously");
    if(failure==Failure::ProfileThrow||failure==Failure::ProfileReentry||failure==Failure::ProfileNull||failure==Failure::ProfileLength)
        require(encodings==2,"Framer failure retried, reentered its callback or skipped the actual second source push");
    if(wrong_expected)require(encodings==1,"Wrong full64 expected tuple reached the framer");
    peer.pump();require(ack.no==refusals,"Failure cleanup repeated the throwing refusal callback");
}

void qualified_capture_retains_source_cancellation(){
    // Future socket cases for the actual qualified API's active-capture branch.
    // Explicit fixture framing remains test-only, never native qualification.
    for(unsigned mode=0;mode<4;++mode){
        unsigned encodings=0,async_profiles=0,yes=0,no=0;
        const auto live=std::make_shared<std::atomic_bool>(true);
        Peer peer([&](Session& actual,auto)->std::optional<Bytes>{
            auto capture=actual.capture_world_reply_pushes([&](Session&,auto logical)->std::optional<Bytes>{
                ++encodings;if(mode==1)live->store(false);return framed(logical);
            });
            const auto init=actual.normal_world_initialization();
            require(init.has_value(),"Qualified fixture requires actual private input initialization");
            actual.send_qualified_world_records_with_acceptance(*init,row(41),
                [&](Session&,auto logical)->std::optional<Bytes>{++async_profiles;return framed(logical);},
                {Peer::account,Peer::character,Peer::world_generation,actual.battle_generation()},
                [&](bool accepted){accepted?++yes:++no;if(mode==3&&accepted)live->store(false);},live);
            try{
                auto result=capture.finish(0);
                if(mode==2)live->store(false); // Retained after the capture handle finished.
                return result;
            }catch(const std::exception&){return Bytes{};}
        });
        peer.ready();peer.invoke();
        if(mode==0){peer.expect(framed(row(41)));peer.silent();}
        else peer.closed_without_output();
        require(encodings==1&&async_profiles==0,"Qualified captured push must use only its original-run profile");
        require((mode==0||mode==3)?(yes==1&&no==0):(yes==0&&no==1),
            "Captured cancellation must preserve once-only FIFO acceptance stage");
        peer.pump();
        require(yes+no==1,"Later failure repeated qualified captured acknowledgment");
    }
}

void outside_callback_is_not_authority(){
    unsigned encodings=0;
    Peer peer([](Session&,auto)->std::optional<Bytes>{return Bytes{};});peer.ready();
    require(refuses([&]{auto capture=peer.session->capture_world_reply_pushes(profile(encodings));(void)capture;}),
        "Ready Session outside actual world callback minted a push capture");
    require(!encodings,"Rejected outside-TLS capture invoked the explicit framer");peer.silent();
}

} // namespace

void test_world_reply_push_capture(){
    static_assert(!std::is_copy_constructible_v<Session::WorldReplyPushCapture>);
    static_assert(!std::is_move_constructible_v<Session::WorldReplyPushCapture>);
    static_assert(!std::is_copy_assignable_v<Session::WorldReplyPushCapture>);
    static_assert(!std::is_move_assignable_v<Session::WorldReplyPushCapture>);
    final_fifo_and_original_callback_order();empty_scope_and_relative_base();finished_old_scope_cannot_poison_successor();qualified_capture_retains_source_cancellation();outside_callback_is_not_authority();
    for(const auto failure:{Failure::Drop,Failure::Invalidate,Failure::Nested,Failure::ProfileThrow,Failure::ProfileReentry,
        Failure::ProfileNull,Failure::ProfileLength,Failure::WrongOffset,Failure::OverflowOffset,Failure::AlteredFinal,
        Failure::Account,Failure::Character,Failure::ExpectedAccount,Failure::ExpectedCharacter,Failure::Delivery,
        Failure::AfterFinishAccount,Failure::Observed,Failure::FrameBudget})
        refused_capture(failure);
}
