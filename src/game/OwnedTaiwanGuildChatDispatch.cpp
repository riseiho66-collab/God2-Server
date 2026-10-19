#include "OwnedTaiwanGuildChatDispatch.h"
#include <stdexcept>
#include <thread>

namespace god2 {
namespace {
void guild_chat_game(std::thread::id thread){if(thread!=std::this_thread::get_id())throw std::logic_error("Owned native guild chat requires GAME");}
}
struct OwnedTaiwanGuildChatDispatch::State {
    const std::thread::id thread=std::this_thread::get_id();
    Handler handler;
    std::shared_ptr<const Invalidator> invalidator;
    bool installed=false,stopped=false;
    bool invalidating=false;
    struct Active {
        std::shared_ptr<Session> peer;
        std::uint64_t id,account,character,battle;
        SessionState phase;
        bool world_ready,valid=true;
    };
    std::shared_ptr<Active> active;
    void owner()const{guild_chat_game(thread);}
    struct Guard {
        State& state;std::shared_ptr<Active> operation;
        ~Guard(){if(state.active==operation)state.active.reset();}
    };
    bool current(const Active& occurrence)const{
        const auto& session=*occurrence.peer;
        return !stopped&&installed&&occurrence.valid&&!session.closing()&&session.id()==occurrence.id&&
            session.account_id==occurrence.account&&session.character_id==occurrence.character&&session.state()==occurrence.phase&&
            session.battle_generation()==occurrence.battle&&session.recovered_world_ready()==occurrence.world_ready&&session.native_channel_binding_current();
    }
    std::optional<SharedTaiwanWorldRecordSource::Reply> dispatch(Session& session,std::span<const RecoveredGuildChat::Request> requests){
        owner();
        if(active){invalidate();throw std::logic_error("Reentrant owned native guild chat");}
        if(stopped||!installed||!handler)throw std::logic_error("Owned native guild chat is not installed/live");
        if(requests.empty()||!session.id()||!session.account_id||!session.character_id||session.closing()||!session.native_channel_binding_current()||
            (session.state()!=SessionState::CharacterSelected&&session.state()!=SessionState::InWorld&&session.state()!=SessionState::InBattle))return {};
        const auto peer=session.shared_from_this();
        auto operation=std::make_shared<Active>(Active{peer,session.id(),session.account_id,session.character_id,session.battle_generation(),session.state(),session.recovered_world_ready()});
        active=operation;Guard guard{*this,operation};
        const auto callback=handler;
        if(!current(*operation))return {};
        auto reply=callback(session,requests);
        if(!current(*operation))return {};
        return reply;
    }
    void notify(const std::shared_ptr<const Invalidator>& callback){
        if(invalidating||!callback)return;invalidating=true;
        struct Reset {bool& flag;~Reset(){flag=false;}} reset{invalidating};(*callback)();
    }
    void release(Session& session){owner();if(active&&active->peer.get()==&session&&active->id==session.id())invalidate();}
    void invalidate(){owner();if(active)active->valid=false;const auto callback=invalidator;notify(callback);}
    void stop(){
        owner();if(stopped)return;stopped=true;if(active)active->valid=false;
        const auto callback=invalidator;handler={};invalidator.reset();notify(callback);
    }
    ~State(){if(thread!=std::this_thread::get_id())std::terminate();}
};
std::shared_ptr<OwnedTaiwanGuildChatDispatch> OwnedTaiwanGuildChatDispatch::create(){
    return std::shared_ptr<OwnedTaiwanGuildChatDispatch>(new OwnedTaiwanGuildChatDispatch(std::make_shared<State>()));
}
void OwnedTaiwanGuildChatDispatch::install(Handler handler,Invalidator invalidator){
    const auto state=state_;state->owner();if(state->installed||state->stopped||!handler)throw std::logic_error("Incomplete/late owned native guild chat handler");
    const auto callback=invalidator?std::make_shared<const Invalidator>(std::move(invalidator)):std::shared_ptr<const Invalidator>{};
    state->handler=std::move(handler);state->invalidator=callback;state->installed=true;
}
void OwnedTaiwanGuildChatDispatch::stop(){const auto state=state_;state->stop();}
OwnedTaiwanGuildChatDispatch::~OwnedTaiwanGuildChatDispatch(){state_->stop();}
OwnedTaiwanGuildChatDispatch::Binding OwnedTaiwanGuildChatDispatch::binding(){
    state_->owner();const auto thread=state_->thread;const std::weak_ptr<State> weak=state_;
    const auto lock=[thread,weak]{guild_chat_game(thread);return weak.lock();};
    Binding result;
    result.dispatch=[lock](Session& session,std::span<const RecoveredGuildChat::Request> requests)->std::optional<SharedTaiwanWorldRecordSource::Reply>{
        const auto state=lock();if(!state)throw std::logic_error("Expired owned native guild chat");return state->dispatch(session,requests);
    };
    result.release=[lock](Session& session){if(const auto state=lock())state->release(session);};
    result.invalidate_active=[lock]{if(const auto state=lock())state->invalidate();};
    return result;
}
}
