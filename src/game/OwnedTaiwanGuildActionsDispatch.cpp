#include "game/OwnedTaiwanGuildActionsDispatch.h"
#include <exception>
#include <stdexcept>
#include <thread>
namespace god2 {
struct OwnedTaiwanGuildActionsDispatch::State {
    using Capture=Binding::Capture;
    using Reply=SharedTaiwanWorldRecordSource::Reply;
    using Record=SharedTaiwanWorldRecordSource::Record;
    struct Captured final:Binding::Batch {
        std::weak_ptr<State> issuer;
        std::weak_ptr<Session> peer;
        std::uint64_t id,account,character,battle;
        SessionState phase;
        std::vector<std::size_t> indices;
        Capture source;
        std::size_t next=0;
        bool valid=true,finished=false;
        Captured(Session& s,std::span<const std::size_t> selected):peer(s.weak_from_this()),
            id(s.id()),account(s.account_id),character(s.character_id),battle(s.battle_generation()),
            phase(s.state()),indices(selected.begin(),selected.end()){}
    };
    const std::thread::id thread=std::this_thread::get_id();
    std::shared_ptr<const Binding> source;
    std::shared_ptr<Captured> active;
    bool operating=false,stopped=false,invalidating=false,interrupted=false;
    void owner()const{if(thread!=std::this_thread::get_id())throw std::logic_error("Guild action GAME owner mismatch");}
    void poison(){
        owner();if(active)active->valid=false;if(invalidating)return;
        const auto callbacks=source;if(!callbacks)return;
        invalidating=true;struct Reset{bool& b;~Reset(){b=false;}} reset{invalidating};
        callbacks->invalidate_active();
    }
    struct Operation {
        State& state;
        explicit Operation(State& s):state(s){s.owner();if(s.operating){s.interrupted=true;s.poison();throw std::logic_error("Reentered guild action source");}s.operating=true;s.interrupted=false;}
        ~Operation(){state.operating=false;}
    };
    std::shared_ptr<const Binding> callbacks()const{
        owner();if(stopped||!source)throw std::logic_error("Guild action source absent/retired");return source;
    }
    bool current(Session& s,const std::shared_ptr<Captured>& b)const{
        return b&&!interrupted&&active==b&&b->valid&&!b->finished&&b->issuer.lock().get()==this&&b->peer.lock().get()==&s&&
            s.id()==b->id&&s.account_id==b->account&&s.character_id==b->character&&s.battle_generation()==b->battle&&
            s.state()==b->phase&&s.recovered_world_ready()&&!s.closing()&&s.native_channel_binding_current();
    }
    bool handles(Session& s,const Record& record){
        Operation operation(*this);const auto cb=callbacks();
        if(active){poison();throw std::logic_error("Guild action classification inside active batch");}
        const auto id=s.id(),a=s.account_id,c=s.character_id,b=s.battle_generation();const auto p=s.state();
        const auto actual=cb->handles(s,record);
        if(stopped||interrupted||s.id()!=id||s.account_id!=a||s.character_id!=c||s.battle_generation()!=b||s.state()!=p)
            throw std::logic_error("Guild action selector changed source");
        return actual;
    }
    Capture capture(Session& s,std::span<const Record> records,std::span<const std::size_t> indices,
            const std::shared_ptr<State>& self){
        Operation operation(*this);const auto cb=callbacks();
        if(active){poison();throw std::logic_error("Guild action batch already active");}
        if(records.empty()||indices.empty()||!s.id()||!s.account_id||!s.character_id||s.closing()||
            !s.recovered_world_ready()||!s.native_channel_binding_current())throw std::logic_error("Guild action original owner unavailable");
        std::size_t previous=0;bool first=true;
        for(const auto index:indices){if(index>=records.size()||(!first&&index<=previous))throw std::logic_error("Guild action original indices invalid");first=false;previous=index;}
        auto batch=std::make_shared<Captured>(s,indices);batch->issuer=self;active=batch;
        try{
            batch->source=cb->capture(s,records,indices);
            if(!batch->source||!current(s,batch))throw std::logic_error("Guild action full capture rejected");
            return batch;
        }catch(...){
            const auto failure=std::current_exception();batch->valid=false;
            try{poison();}catch(...){}
            if(batch->source)try{cb->finish_batch(s,batch->source,false);}catch(...){}
            batch->finished=true;if(active==batch)active.reset();std::rethrow_exception(failure);
        }
    }
    std::optional<Reply> dispatch(Session& s,const Capture& supplied,std::size_t index,std::size_t offset){
        Operation operation(*this);const auto cb=callbacks();const auto batch=std::dynamic_pointer_cast<Captured>(supplied);
        if(!batch||batch->issuer.lock().get()!=this||batch->peer.lock().get()!=&s||active!=batch)
            throw std::logic_error("Foreign/stale guild action batch cannot affect successor");
        if(!current(s,batch)||batch->next>=batch->indices.size()||batch->indices[batch->next]!=index){
            poison();throw std::logic_error("Guild action foreign/stale/replayed original index");
        }
        ++batch->next; // Consume before callbacks, SQL or output.
        try{
            auto result=cb->dispatch(s,batch->source,index,offset);
            if(!result||!current(s,batch))throw std::logic_error("Guild action source changed during execution");
            return result;
        }catch(...){const auto failure=std::current_exception();try{poison();}catch(...){}std::rethrow_exception(failure);}
    }
    void finish(Session& s,const Capture& supplied,bool accepted){
        Operation operation(*this);const auto cb=callbacks();const auto batch=std::dynamic_pointer_cast<Captured>(supplied);
        if(!batch||batch->issuer.lock().get()!=this||batch->peer.lock().get()!=&s)throw std::logic_error("Foreign guild action completion");
        if(batch->finished){if(!accepted)cb->finish_batch(s,batch->source,false);return;}
        const bool good=accepted&&current(s,batch)&&batch->next==batch->indices.size();
        batch->finished=true;if(!good)batch->valid=false;
        try{cb->finish_batch(s,batch->source,good);
            if(good&&(interrupted||stopped||!batch->valid||s.id()!=batch->id||s.account_id!=batch->account||s.character_id!=batch->character||
                s.state()!=batch->phase||s.battle_generation()!=batch->battle||s.closing()||!s.recovered_world_ready()||!s.native_channel_binding_current()))
                throw std::logic_error("Guild action completion reentered/changed source");
        }
        catch(...){
            const auto failure=std::current_exception();batch->valid=false;try{poison();}catch(...){}
            try{cb->finish_batch(s,batch->source,false);}catch(...){}if(active==batch)active.reset();std::rethrow_exception(failure);
        }
        if(active==batch)active.reset();
        if(accepted&&!good)throw std::logic_error("Guild action batch was not completely handled");
    }
    void release(Session& s){
        Operation operation(*this);const auto cb=callbacks();
        if(active&&active->id==s.id()&&active->peer.lock().get()!=&s)
            throw std::logic_error("Guild action release pointer mismatch");
        if(active&&active->peer.lock().get()==&s){const auto batch=active;batch->valid=false;
            std::exception_ptr failure;try{poison();}catch(...){failure=std::current_exception();}
            if(batch->source)try{cb->finish_batch(s,batch->source,false);}catch(...){if(!failure)failure=std::current_exception();}
            batch->finished=true;active.reset();try{cb->release(s);}catch(...){if(!failure)failure=std::current_exception();}
            if(failure)std::rethrow_exception(failure);return;
        }
        cb->release(s);
    }
    void stop(){
        owner();if(stopped)return;stopped=true;const auto cb=source;const auto batch=active;
        if(batch){batch->valid=false;try{poison();}catch(...){}
            if(cb&&batch->source)if(const auto peer=batch->peer.lock())try{cb->finish_batch(*peer,batch->source,false);}catch(...){}
            batch->finished=true;active.reset();}
        source.reset();
    }
    ~State(){if(thread!=std::this_thread::get_id())std::terminate();}
};
std::shared_ptr<OwnedTaiwanGuildActionsDispatch> OwnedTaiwanGuildActionsDispatch::create(){
    return std::shared_ptr<OwnedTaiwanGuildActionsDispatch>(new OwnedTaiwanGuildActionsDispatch(std::make_shared<State>()));
}
void OwnedTaiwanGuildActionsDispatch::install(Binding binding){
    const auto s=state_;s->owner();if(s->source||s->stopped||!binding.handles||!binding.capture||!binding.dispatch||
        !binding.finish_batch||!binding.release||!binding.invalidate_active)throw std::invalid_argument("Incomplete/replaced guild action source");
    s->source=std::make_shared<const Binding>(std::move(binding));
}
OwnedTaiwanGuildActionsDispatch::Binding OwnedTaiwanGuildActionsDispatch::binding(){
    const auto s=state_;s->owner();const auto thread=s->thread;const std::weak_ptr<State> weak=s;
    const auto lock=[weak,thread]{if(thread!=std::this_thread::get_id())throw std::logic_error("Guild action weak facade GAME mismatch");return weak.lock();};
    Binding result;
    result.handles=[lock](Session& p,const auto& r){const auto s=lock();if(!s)throw std::logic_error("Expired guild action selector");return s->handles(p,r);};
    result.capture=[lock](Session& p,auto r,auto i)->Binding::Capture{const auto s=lock();if(!s)throw std::logic_error("Expired guild action capture");return s->capture(p,r,i,s);};
    result.dispatch=[lock](Session& p,const auto& b,auto i,auto o)->std::optional<SharedTaiwanWorldRecordSource::Reply>{const auto s=lock();if(!s)throw std::logic_error("Expired guild action dispatch");return s->dispatch(p,b,i,o);};
    result.finish_batch=[lock](Session& p,const auto& b,bool a){const auto s=lock();if(!s)throw std::logic_error("Expired guild action completion");s->finish(p,b,a);};
    result.release=[lock](Session& p){if(const auto s=lock())if(!s->stopped)s->release(p);};
    result.invalidate_active=[lock]{if(const auto s=lock())s->poison();};
    return result;
}
void OwnedTaiwanGuildActionsDispatch::stop(){state_->stop();}
OwnedTaiwanGuildActionsDispatch::~OwnedTaiwanGuildActionsDispatch(){state_->stop();}
}
