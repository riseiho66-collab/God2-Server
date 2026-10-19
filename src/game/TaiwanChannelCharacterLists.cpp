#include "game/TaiwanChannelCharacterLists.h"
#include "protocol/RecoveredTaiwanServerAdvertisement.h"
#include <exception>
#include <map>
#include <stdexcept>
#include <thread>

namespace god2 {
namespace {
void require_channel_list_game(std::thread::id expected){
    if(expected!=std::this_thread::get_id())throw std::logic_error("Channel list facade requires its actual GAME owner");
}
}
struct TaiwanChannelCharacterLists::State {
    using Delivery=Session::NativeCharacterList;
    struct Pending {
        std::weak_ptr<Session> session;
        const Session* pointer;
        std::uint64_t id,account;
        std::shared_ptr<const Session::RecoveredServerSelection> selection;
        std::uint8_t issuer;
        Delivery delivery;
        bool cleanup_attempted=false,completed=false,failed=false;
    };
    const std::thread::id thread=std::this_thread::get_id();
    const std::array<Source,3> sources;
    const std::uint8_t group;
    const std::size_t capacity;
    // Completed/failed records remain until exact disconnect: neither a copied
    // delivery nor a different Session reusing a scalar ID can choose its issuer.
    std::map<std::uint64_t,std::shared_ptr<Pending>> pending;
    bool busy=false,reentered=false;
    std::weak_ptr<Session> active;
    State(std::array<Source,3> input,std::uint8_t g,std::size_t c):sources(std::move(input)),group(g),capacity(c){}
    ~State(){if(thread!=std::this_thread::get_id())std::terminate();}
    void owner() const {if(thread!=std::this_thread::get_id())throw std::logic_error("Channel list requires its actual GAME owner");}
    void poison() noexcept {
        reentered=true;
        // Existing native issuer post-observer Current checks closing(). Make a
        // caught nested router call visible before that issuer can activate a
        // ticket; returning false after an already committed callback is too late.
        try{if(const auto session=active.lock())session->close();}catch(...){}
    }
    struct Operation {
        State& state;
        Operation(State& value,const std::shared_ptr<Session>& session):state(value){
            state.owner();if(state.busy){state.poison();throw std::logic_error("Channel list callback reentered");}
            state.busy=true;state.reentered=false;state.active=session;
        }
        ~Operation(){state.active.reset();state.busy=false;}
    };
    bool registered(const std::shared_ptr<Pending>& entry) const {
        const auto found=pending.find(entry->id);return found!=pending.end()&&found->second==entry;
    }
    bool identity(Session& session,const std::shared_ptr<Pending>& entry) const {
        return entry->pointer==&session&&entry->session.lock().get()==&session&&session.id()==entry->id;
    }
    bool live(Session& session,const std::shared_ptr<Pending>& entry) const {
        return !reentered&&!entry->failed&&registered(entry)&&identity(session,entry)&&!session.closing()&&
            session.state()==SessionState::Authenticated&&session.account_id==entry->account&&!session.character_id&&
            session.recovered_server_selection()==entry->selection&&session.native_channel_binding_current()&&
            session.native_channel_allows_destination(group,entry->issuer);
    }
    void erase(const std::shared_ptr<Pending>& entry){
        const auto found=pending.find(entry->id);if(found!=pending.end()&&found->second==entry)pending.erase(found);
    }
    bool shaped(const std::shared_ptr<Pending>& entry,const Delivery& delivery) const {
        return delivery&&delivery->session==entry->id&&delivery->account==entry->account&&delivery->sequence&&
            delivery->selection==entry->selection;
    }
    void cleanup(Session& session,const std::shared_ptr<Pending>& entry){
        if(!entry->delivery||entry->cleanup_attempted)return;
        entry->cleanup_attempted=true; // Exact issuer attempt, once even if it throws/reenters.
        sources[entry->issuer].native_list_complete(session,entry->delivery,false);
    }
    void reject(Session& session,const std::shared_ptr<Pending>& entry,std::exception_ptr error={}){
        entry->failed=true;
        try{session.close();}catch(...){if(!error)error=std::current_exception();}
        try{cleanup(session,entry);}catch(...){if(!error)error=std::current_exception();}
        if(error)std::rethrow_exception(error);
    }
    Delivery list(Session& session){
        const auto peer=session.weak_from_this().lock();Operation operation(*this,peer);
        if(!peer||peer.get()!=&session||pending.contains(session.id())||pending.size()>=capacity)
            throw std::invalid_argument("Channel list actual Session/pending capacity is unavailable");
        const auto selection=session.recovered_server_selection();
        if(!selection||!selection->advertisement||selection->session!=session.id()||selection->account!=session.account_id||
           !session.account_id||session.character_id||session.state()!=SessionState::Authenticated||session.closing()||
           selection->advertisement->session!=session.id()||!session.native_channel_binding_current())
            throw std::invalid_argument("Channel list lacks actual current authenticated L selection");
        const auto selector=selection->request.selector_bytes();
        const auto advertisement=RecoveredTaiwanServerAdvertisement::parse(selection->advertisement->wire);
        if(selector[0]!=group||selector[1]>=sources.size()||!advertisement||!advertisement->rows[group]||
           !(advertisement->rows[group]->mask()&(1u<<selector[1])))
            throw std::invalid_argument("Channel list selection is outside the actual written advertisement");
        auto entry=std::make_shared<Pending>(Pending{peer,&session,session.id(),session.account_id,selection,selector[1],{}});
        if(reentered||!pending.emplace(entry->id,entry).second||!live(session,entry)){
            erase(entry);throw std::invalid_argument("Channel list changed during preparation");
        }
        try{
            entry->delivery=sources[entry->issuer].native_list(session);
            if(!shaped(entry,entry->delivery)||!live(session,entry)||
               !sources[entry->issuer].native_list_current(session,entry->delivery)||!live(session,entry))
                throw std::invalid_argument("Selected channel issuer did not retain its exact native list");
            return entry->delivery;
        }catch(...){reject(session,entry,std::current_exception());throw;}
    }
    std::shared_ptr<Pending> find(Session& session,const Delivery& delivery) const {
        const auto found=pending.find(session.id());
        return found!=pending.end()&&identity(session,found->second)&&found->second->delivery==delivery?found->second:nullptr;
    }
    bool current(Session& session,const Delivery& delivery){
        Operation operation(*this,session.weak_from_this().lock());const auto entry=find(session,delivery);if(!entry||entry->completed||entry->failed)return false;
        try{
            if(live(session,entry)&&shaped(entry,delivery)&&sources[entry->issuer].native_list_current(session,delivery)&&live(session,entry))return true;
        }catch(...){reject(session,entry,std::current_exception());throw;}
        reject(session,entry);return false;
    }
    bool complete(Session& session,const Delivery& delivery,bool written){
        Operation operation(*this,session.weak_from_this().lock());const auto entry=find(session,delivery);if(!entry||entry->completed)return false;
        if(!written){entry->failed=true;cleanup(session,entry);return false;}
        if(entry->failed)return false;
        try{
            if(!live(session,entry)||!shaped(entry,delivery)||session.recovered_native_character_list_written()!=delivery||
               !sources[entry->issuer].native_list_current(session,delivery)||!live(session,entry)){
                reject(session,entry);return false;
            }
            const bool accepted=sources[entry->issuer].native_list_complete(session,delivery,true);
            if(!accepted||!live(session,entry)){reject(session,entry);return false;}
            entry->completed=true;entry->cleanup_attempted=true;return true;
        }catch(...){reject(session,entry,std::current_exception());throw;}
    }
    std::uint64_t select(Session& session,const RecoveredPostCreateSelect::Selection& input,std::optional<std::uint64_t> created){
        Operation operation(*this,session.weak_from_this().lock());
        const auto delivery=session.recovered_native_character_list_written();const auto entry=find(session,delivery);
        if(!entry||!entry->completed||!live(session,entry)||session.recovered_native_character_list()!=delivery)
            throw std::invalid_argument("Channel selection lacks this exact completed native issuer record");
        try{
            const auto result=sources[entry->issuer].native_select(session,input,created);
            if(!result||!live(session,entry)||session.recovered_native_character_list()!=delivery||
               session.recovered_native_character_list_written()!=delivery)
                throw std::invalid_argument("Channel native selection source changed");
            return result;
        }catch(...){reject(session,entry,std::current_exception());throw;}
    }
    void disconnected(const std::shared_ptr<Session>& session){
        Operation operation(*this,session);if(!session)return;
        std::exception_ptr error;
        const auto found=pending.find(session->id());
        if(found!=pending.end()&&!identity(*session,found->second))
            throw std::invalid_argument("Channel disconnect does not own the registered actual Session");
        if(found!=pending.end()&&identity(*session,found->second)){
            const auto entry=found->second;erase(entry);
            try{cleanup(*session,entry);}catch(...){error=std::current_exception();}
        }
        // L authentication/list state can have touched several actual gameplay
        // exports. Never choose disconnect cleanup from latest A6 or stop after
        // one failing issuer. Callbacks receive this exact shared Session only.
        for(const auto& source:sources)try{source.on_disconnect(session);}catch(...){if(!error)error=std::current_exception();}
        if(error)std::rethrow_exception(error);
    }
};
std::shared_ptr<TaiwanChannelCharacterLists> TaiwanChannelCharacterLists::create(std::array<Source,3> sources,
        std::uint8_t group,std::size_t capacity){
    if(group>=10||!capacity)throw std::invalid_argument("Channel list group/capacity is unavailable");
    for(const auto& source:sources)if(!source.native_list||!source.native_list_current||!source.native_list_complete||!source.on_disconnect||!source.native_select)
        throw std::invalid_argument("Channel list requires three complete actual issuer facades");
    return std::shared_ptr<TaiwanChannelCharacterLists>(new TaiwanChannelCharacterLists(std::make_shared<State>(std::move(sources),group,capacity)));
}
TaiwanChannelCharacterLists::~TaiwanChannelCharacterLists(){if(state_->thread!=std::this_thread::get_id())std::terminate();}
TaiwanChannelCharacterLists::Binding TaiwanChannelCharacterLists::binding(){
    state_->owner();const auto weak=std::weak_ptr<State>(state_);const auto thread=state_->thread;Binding out;
    // Check the copied pure thread value BEFORE locking. A forbidden NET call
    // must never acquire/release the last affine source owner on that thread.
    out.list=[weak,thread](Session& session){require_channel_list_game(thread);const auto state=weak.lock();if(!state)throw std::logic_error("Channel list owner retired");return state->list(session);};
    out.current=[weak,thread](Session& session,const Session::NativeCharacterList& list){require_channel_list_game(thread);const auto state=weak.lock();return state&&state->current(session,list);};
    out.complete=[weak,thread](Session& session,const Session::NativeCharacterList& list,bool written){require_channel_list_game(thread);const auto state=weak.lock();return state&&state->complete(session,list,written);};
    out.disconnected=[weak,thread](std::shared_ptr<Session> session){require_channel_list_game(thread);if(const auto state=weak.lock())state->disconnected(session);};
    out.select=[weak,thread](Session& session,const RecoveredPostCreateSelect::Selection& input,std::optional<std::uint64_t> created){
        require_channel_list_game(thread);const auto state=weak.lock();if(!state)throw std::logic_error("Channel list owner retired");return state->select(session,input,created);
    };
    return out;
}
}
