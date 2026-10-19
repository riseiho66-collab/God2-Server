#include "game/OwnedTaiwanGuildChatDispatch.h"
#include "protocol/RecoveredWorldFrame.h"
#include <array>
#include <stdexcept>
#include <thread>

namespace {
using namespace god2;
using Dispatch=OwnedTaiwanGuildChatDispatch;
using Reply=SharedTaiwanWorldRecordSource::Reply;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class F> bool refuses(F&& callback){try{callback();}catch(const std::exception&){return true;}return false;}
// Actual Session objects carry only explicit synthetic public scalar state.
// No private input, initialization, readiness or guild membership is minted.
// These future tests check the late-installed callback's custody, not gameplay.
struct Fixture {
    asio::io_context game;
    std::shared_ptr<Session> peer=make(0x100000007ULL);
    std::shared_ptr<Session> impostor=make(peer->id());
    std::shared_ptr<Dispatch> owner=Dispatch::create();
    Dispatch::Binding binding=owner->binding();
    std::array<RecoveredGuildChat::Request,2> requests{RecoveredGuildChat::Request{{3,0xa5,1,2},"first"},RecoveredGuildChat::Request{{0x83,0x5a,3,4},"second"}};
    std::shared_ptr<Session> make(std::uint64_t id){
        auto session=std::make_shared<Session>(asio::ip::tcp::socket(game),game.get_executor(),id,false,Session::PacketHandler{},Session::DisconnectHandler{});
        session->account_id=0x200000007ULL;session->character_id=41;session->set_state(SessionState::InWorld);return session;
    }
    ~Fixture(){if(owner)owner->stop();}
};
void installation_and_exact_reply(){
    Fixture f;unsigned calls=0;
    require(refuses([&]{(void)f.binding.dispatch(*f.peer,f.requests);}),"Uninstalled holder cannot claim a native decision");
    require(refuses([&]{f.owner->install({});}),"Incomplete callback refused without installation");
    std::vector<std::uint8_t> expected;
    for(const auto& message:f.requests){auto wire=RecoveredWorldFrame::encode(RecoveredGuildChat::display(41,false,message.legacy_text));expected.insert(expected.end(),wire.begin(),wire.end());}
    f.owner->install([&](Session& session,std::span<const RecoveredGuildChat::Request> messages)->std::optional<Reply>{
        ++calls;require(&session==f.peer.get()&&messages.size()==2&&messages[0]==f.requests[0]&&messages[1]==f.requests[1],"Original exact Session and request order reaches supplied callback");return Reply::wire(expected);
    });
    const auto reply=f.binding.dispatch(*f.peer,f.requests);require(reply&&!reply->native_no_reply()&&reply->bytes()==expected&&calls==1,"Actual supplied encrypted envelopes return unchanged, never directly sent");
    require(refuses([&]{f.owner->install([](auto&,auto)->std::optional<Reply>{return Reply::no_reply();});}),"Installation is one-time");
    require(!f.binding.dispatch(*f.peer,{}).has_value()&&calls==1,"Empty request is not successful output");
    f.peer->account_id=0;require(!f.binding.dispatch(*f.peer,f.requests)&&calls==1,"Missing full owner identity never reaches callback");
    f.peer->account_id=0x200000007ULL;f.owner->stop();f.owner->stop();
    require(refuses([&]{(void)f.binding.dispatch(*f.peer,f.requests);})&&calls==1,"Stopped holder cannot run captured handler");
    require(refuses([&]{f.owner->install([](auto&,auto)->std::optional<Reply>{return Reply::no_reply();});}),"Stopped holder cannot be revived");
}
void native_decisions_and_exception_cleanup(){
    Fixture f;unsigned calls=0;
    f.owner->install([&](Session&,auto)->std::optional<Reply>{++calls;if(calls==1)return Reply::no_reply();if(calls==2)return {};if(calls==3)throw std::runtime_error("Synthetic source exception");return Reply::no_reply();});
    const auto silent=f.binding.dispatch(*f.peer,f.requests);require(silent&&silent->native_no_reply()&&silent->bytes().empty(),"Only actual callback supplies native no-reply decision");
    require(!f.binding.dispatch(*f.peer,f.requests),"Actual null refusal passes through");
    require(refuses([&]{(void)f.binding.dispatch(*f.peer,f.requests);}),"Callback exception does not become success");
    require(f.binding.dispatch(*f.peer,f.requests).has_value()&&calls==4,"Throwing callback retires active occurrence without wedging later dispatch");
}
void pointer_release_and_caught_reentry(){
    Fixture f;unsigned mode=0;bool nested_refused=false;
    f.owner->install([&](Session& session,auto)->std::optional<Reply>{
        if(mode==0)f.binding.release(*f.impostor);
        if(mode==1)f.binding.release(session);
        if(mode==2)f.binding.invalidate_active();
        if(mode==3)nested_refused=refuses([&]{(void)f.binding.dispatch(session,f.requests);});
        return Reply::no_reply();
    });
    require(f.binding.dispatch(*f.peer,f.requests).has_value(),"Same scalar ID on another actual pointer cannot release active occurrence");
    mode=1;require(!f.binding.dispatch(*f.peer,f.requests),"Exact actual Session release invalidates continuation");
    mode=2;require(!f.binding.dispatch(*f.peer,f.requests),"Outer source invalidation reaches active handler");
    mode=3;require(!f.binding.dispatch(*f.peer,f.requests)&&nested_refused,"Caught nested dispatch invalidates original callback result");
    mode=0;f.binding.release(*f.peer);f.binding.invalidate_active();
    require(f.binding.dispatch(*f.peer,f.requests).has_value(),"No persistent pending grant or stale release survives completion");
}
void identity_and_lifecycle_fences(){
    Fixture f;unsigned mode=0;
    f.owner->install([&](Session& session,auto)->std::optional<Reply>{
        if(mode==0)session.account_id+=0x100000000ULL;
        if(mode==1)session.character_id+=0x100000000ULL;
        if(mode==2)session.set_state(SessionState::InBattle);
        if(mode==3){session.set_state(SessionState::InWorld);session.set_state(SessionState::InBattle);}
        if(mode==4)f.owner->stop();
        return Reply::no_reply();
    });
    require(!f.binding.dispatch(*f.peer,f.requests),"Account high32 mismatch invalidates returned result");f.peer->account_id=0x200000007ULL;
    mode=1;require(!f.binding.dispatch(*f.peer,f.requests),"Character high32 mismatch invalidates returned result");f.peer->character_id=41;
    mode=2;require(!f.binding.dispatch(*f.peer,f.requests),"Phase boundary invalidates returned result");
    mode=3;require(!f.binding.dispatch(*f.peer,f.requests),"Battle out-and-back generation invalidates result despite equal final phase");
    mode=4;require(!f.binding.dispatch(*f.peer,f.requests),"Stop inside active callback revokes copied continuation");
    Fixture selected;selected.peer->set_state(SessionState::CharacterSelected);selected.owner->install([](auto&,auto)->std::optional<Reply>{return Reply::no_reply();});
    require(selected.binding.dispatch(*selected.peer,selected.requests).has_value(),"Original native entry tail may remain CharacterSelected");
    Fixture closed;closed.owner->install([](Session& session,auto)->std::optional<Reply>{session.close();return Reply::no_reply();});
    require(!closed.binding.dispatch(*closed.peer,closed.requests),"Synchronous closing latch invalidates active continuation");
}
void synchronous_invalidation_propagation(){
    Fixture f;
    struct Observation {unsigned mode=0,notifications=0;bool observed_before_return=false,nested_refused=false;};
    const auto observation=std::make_shared<Observation>();const auto binding=f.binding;
    f.owner->install([observation,binding,impostor=f.impostor,requests=f.requests](Session& session,auto)->std::optional<Reply>{
        const auto before=observation->notifications;
        if(observation->mode==0)binding.release(*impostor);
        if(observation->mode==1)binding.release(session);
        if(observation->mode==2)binding.invalidate_active();
        if(observation->mode==3)observation->nested_refused=refuses([&]{(void)binding.dispatch(session,requests);});
        observation->observed_before_return=observation->notifications==before+1;return Reply::no_reply();
    },[observation,binding]{++observation->notifications;binding.invalidate_active();});
    require(f.binding.dispatch(*f.peer,f.requests).has_value()&&observation->notifications==0,"Impostor release cannot propagate cancellation into another actual sender");
    observation->mode=1;require(!f.binding.dispatch(*f.peer,f.requests)&&observation->notifications==1&&observation->observed_before_return,"Exact release propagates synchronously before handler continues");
    observation->mode=2;require(!f.binding.dispatch(*f.peer,f.requests)&&observation->notifications==2&&observation->observed_before_return,"Outer invalidation propagates with recursive observer fenced");
    observation->mode=3;require(!f.binding.dispatch(*f.peer,f.requests)&&observation->notifications==3&&observation->nested_refused&&observation->observed_before_return,"Caught nested dispatch notifies downstream before original handler returns");
    f.owner->stop();require(observation->notifications==4,"Stop notifies downstream after latching retirement");f.owner->stop();f.binding.invalidate_active();require(observation->notifications==4,"Stop clears stored invalidator and is idempotent");
}
void weak_facades_and_affine_capture_retirement(){
    Fixture f;
    struct Observation {std::thread::id game=std::this_thread::get_id();bool destroyed=false,wrong=false;};
    struct Capture {
        std::shared_ptr<Observation> observation;
        explicit Capture(std::shared_ptr<Observation> value):observation(std::move(value)){}
        ~Capture(){observation->destroyed=true;observation->wrong=std::this_thread::get_id()!=observation->game;}
    };
    const auto observation=std::make_shared<Observation>();auto capture=std::make_shared<Capture>(observation);std::weak_ptr<Capture> weak=capture;
    f.owner->install([capture](auto&,auto)->std::optional<Reply>{return Reply::no_reply();});capture.reset();
    bool foreign_dispatch=false,foreign_release=false,foreign_invalidate=false;
    std::thread worker([&]{foreign_dispatch=refuses([&]{(void)f.binding.dispatch(*f.peer,f.requests);});foreign_release=refuses([&]{f.binding.release(*f.peer);});foreign_invalidate=refuses([&]{f.binding.invalidate_active();});});worker.join();
    require(foreign_dispatch&&foreign_release&&foreign_invalidate&&!observation->destroyed&&!weak.expired(),"Wrong-thread weak facade checks before acquiring/copying GAME source");
    f.owner->stop();require(observation->destroyed&&!observation->wrong&&weak.expired(),"GAME stop releases affine source capture even while facade copies remain");
    f.owner.reset();f.binding.release(*f.peer);f.binding.invalidate_active();
    require(refuses([&]{(void)f.binding.dispatch(*f.peer,f.requests);}),"Expired weak dispatch cannot manufacture native no-reply success");
    bool expired_foreign=false;std::thread expired([&]{expired_foreign=refuses([&]{f.binding.invalidate_active();});});expired.join();require(expired_foreign,"Expired facade still enforces GAME before weak lock");
}
}
void test_owned_taiwan_guild_chat_dispatch(){installation_and_exact_reply();native_decisions_and_exception_cleanup();pointer_release_and_caught_reentry();identity_and_lifecycle_fences();synchronous_invalidation_propagation();weak_facades_and_affine_capture_retirement();}
