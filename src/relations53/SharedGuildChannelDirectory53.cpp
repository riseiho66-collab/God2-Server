#include "SharedGuildChannelDirectory53.h"
#include <algorithm>
#include <map>
#include <stdexcept>
#include <thread>

namespace god2 {
namespace {
void game_thread(std::thread::id owner){if(owner!=std::this_thread::get_id())throw std::logic_error("Common53 directory requires GAME");}
}
struct SharedGuildChannelDirectory53::State {
    const std::thread::id thread=std::this_thread::get_id();
    std::array<std::optional<Source>,3> sources;
    bool sealed=false,retired=false;
    std::uint64_t epoch=1;
    struct Row {Host::Live live;std::shared_ptr<Session> peer;std::uint8_t channel;SessionState phase;bool closing;};
    using Rows=std::map<std::uint64_t,Row>;
    void owner() const {game_thread(thread);}
    bool current(std::uint64_t revision) const {return sealed&&!retired&&epoch==revision;}
    std::array<Source,3> copy() const {
        owner();if(!sealed||retired)throw std::logic_error("Common53 directory unavailable");
        return {*sources[0],*sources[1],*sources[2]};
    }
    static bool scalars_current(const Rows& rows){
        for(const auto& [id,row]:rows)if(row.peer->id()!=id||row.peer->account_id!=row.live.account||row.peer->character_id!=row.live.character||
            row.peer->state()!=row.phase||row.peer->closing()!=row.closing)return false;
        return true;
    }
    Rows inspect(const std::array<Source,3>& local,std::uint64_t revision) const {
        Rows rows;std::set<std::uint64_t> characters;
        for(std::uint8_t k=0;k<3;++k){
            const auto live=local[k].enumerate();if(!current(revision))throw std::logic_error("Common53 source retired during enumeration");
            for(const auto& item:live){
                auto peer=local[k].session(item.session);
                if(!current(revision)||!item.session||!peer||peer->id()!=item.session||peer->account_id!=item.account||peer->character_id!=item.character||
                   !rows.emplace(item.session,Row{item,peer,k,peer->state(),peer->closing()}).second||
                   (item.character&&!characters.insert(item.character).second))throw std::logic_error("Common53 duplicate/mismatched live identity");
            }
        }
        // A hidden or foreign same-ID pointer may not resolve through another
        // source, even if that supplier omitted it from its enumeration.
        for(const auto& [id,row]:rows)for(std::uint8_t k=0;k<3;++k){
            const auto peer=local[k].session(id);
            if(!current(revision)||(k==row.channel?peer!=row.peer:static_cast<bool>(peer)))throw std::logic_error("Common53 ambiguous session issuer");
        }
        if(!scalars_current(rows))throw std::logic_error("Common53 source changed an already captured peer");
        return rows;
    }
    bool unchanged(const std::array<Source,3>& local,std::uint64_t revision,const Rows& before) const {
        if(!current(revision))return false;
        const auto after=inspect(local,revision);if(before.size()!=after.size())return false;
        for(const auto& [id,a]:before){const auto at=after.find(id);if(at==after.end())return false;const auto& b=at->second;
            if(a.peer!=b.peer||a.channel!=b.channel||a.phase!=b.phase||a.closing!=b.closing||a.live.account!=b.live.account||
               a.live.character!=b.live.character||a.live.permitted_state!=b.live.permitted_state)return false;}
        return current(revision);
    }
    std::optional<std::pair<Row,Owner>> resolve(const std::array<Source,3>& local,std::uint64_t revision,const Rows& rows,std::uint64_t id) const {
        const auto at=rows.find(id);if(at==rows.end()||!at->second.live.permitted_state||at->second.closing)return {};
        const auto& row=at->second;const auto value=local[row.channel].owner(id);
        if(!current(revision)||!value||value->session!=id||value->account!=row.live.account||value->character!=row.live.character||
           !value->account||!value->character||!value->world_generation||!value->position_revision||
           (value->name_codepage!=950&&value->name_codepage!=936)||
           // The actual accepted entry tail can still be CharacterSelected.
           // Local owner/readiness policy decides whether a battle is eligible.
           (row.phase!=SessionState::CharacterSelected&&row.phase!=SessionState::InWorld&&row.phase!=SessionState::InBattle))return {};
        if(!unchanged(local,revision,rows)||local[row.channel].owner(id)!=value||!current(revision)||!scalars_current(rows))return {};
        return std::pair{row,*value};
    }
    bool exact(const std::array<Source,3>& local,std::uint64_t revision,const Rows& rows,const Row& row,const Owner& value) const {
        if(!unchanged(local,revision,rows))return false;
        const auto now=resolve(local,revision,rows,value.session);
        return now&&now->first.peer==row.peer&&now->first.channel==row.channel&&now->second==value;
    }
    std::optional<Owner> find(std::uint64_t id){
        const auto local=copy();const auto revision=epoch;const auto rows=inspect(local,revision);const auto found=resolve(local,revision,rows,id);
        return found?std::optional{found->second}:std::nullopt;
    }
    std::vector<Host::Live> enumerate(){
        const auto local=copy();const auto revision=epoch;const auto rows=inspect(local,revision);
        if(!unchanged(local,revision,rows))throw std::logic_error("Common53 enumeration changed");
        std::vector<Host::Live> result;for(const auto& [id,row]:rows)result.push_back(row.live);return result;
    }
    bool ready(const Owner& value,bool recipient){
        const auto local=copy();const auto revision=epoch;const auto rows=inspect(local,revision);const auto found=resolve(local,revision,rows,value.session);
        if(!found||found->second!=value)return false;const auto& row=found->first;
        const bool accepted=recipient?local[row.channel].recipient_ready(value):local[row.channel].peer_ready(value);
        return accepted&&exact(local,revision,rows,row,value);
    }
    bool closed(const Owner& value){
        const auto local=copy();const auto revision=epoch;const auto rows=inspect(local,revision);
        if(!value.session||!value.account||!value.character||!value.world_generation||!value.position_revision||
           (value.name_codepage!=950&&value.name_codepage!=936)||rows.contains(value.session))return false;
        for(const auto& source:local)if(source.session(value.session)||!current(revision))return false;
        unsigned claims=0;for(const auto& source:local){claims+=source.closed(value)?1u:0u;if(!current(revision))return false;}
        if(!unchanged(local,revision,rows))return false;
        for(const auto& source:local)if(source.session(value.session)||!current(revision))return false;
        return claims==1;
    }
    std::set<std::uint32_t> online(){
        const auto local=copy();const auto revision=epoch;const auto rows=inspect(local,revision);std::set<std::uint32_t> result;
        for(const auto& source:local){const auto part=source.online();if(!current(revision))throw std::logic_error("Common53 online source retired");result.insert(part.begin(),part.end());}
        if(!unchanged(local,revision,rows))throw std::logic_error("Common53 online source changed");return result;
    }
    void sync_name(const Owner& value){
        const auto local=copy();const auto revision=epoch;const auto rows=inspect(local,revision);const auto found=resolve(local,revision,rows,value.session);
        if(!found||found->second!=value)throw std::logic_error("Common53 name owner changed");
        local[found->first.channel].sync_name(value);
        if(!exact(local,revision,rows,found->first,value))throw std::logic_error("Common53 name source changed");
    }
    std::optional<Common::Baseline> baseline(const Owner& value){
        const auto local=copy();const auto revision=epoch;const auto rows=inspect(local,revision);const auto found=resolve(local,revision,rows,value.session);
        if(!found||found->second!=value)return {};
        auto result=local[found->first.channel].baseline(value);
        if(!exact(local,revision,rows,found->first,value)||(result&&result->recipient!=value))return {};return result;
    }
    void send(const Owner& value,std::vector<std::uint8_t> bytes,std::function<void(bool)> ack,std::weak_ptr<State> weak){
        const auto local=copy();const auto revision=epoch;const auto rows=inspect(local,revision);const auto found=resolve(local,revision,rows,value.session);
        if(!found||found->second!=value){if(ack)ack(false);return;}
        // All captures are owned values. Nested synchronous ACK/sync is allowed;
        // there is deliberately no global busy bit. Never retain a frame callback
        // in the ACK: only weak directory state plus exact identity evidence.
        struct Gate {bool done=false,dispatching=true;std::optional<bool> deferred;std::function<void(bool)> ack;};
        auto gate=std::make_shared<Gate>();gate->ack=std::move(ack);const auto row=found->first;const auto thread_id=thread;
        auto complete=[weak,gate,revision,value,peer=std::weak_ptr<Session>(row.peer),channel=row.channel,thread_id](bool accepted){
            game_thread(thread_id);if(gate->done)return;if(gate->dispatching){if(!gate->deferred)gate->deferred=accepted;return;}gate->done=true;bool good=false;
            if(accepted)if(const auto state=weak.lock())try{
                if(state->current(revision)){const auto sources=state->copy();const auto now=state->inspect(sources,revision);const auto current=state->resolve(sources,revision,now,value.session);
                    good=current&&current->first.peer==peer.lock()&&current->first.channel==channel&&current->second==value;}
            }catch(...){good=false;}
            if(gate->ack)gate->ack(good);
        };
        try{local[row.channel].send(value,std::move(bytes),complete);}catch(...){gate->dispatching=false;complete(false);throw;}
        gate->dispatching=false;
        try{if(!exact(local,revision,rows,row,value)){complete(false);return;}}
        catch(...){complete(false);throw;}
        if(gate->deferred)complete(*gate->deferred);
    }
    void retire(){owner();if(retired)return;retired=true;++epoch;for(auto& source:sources)source.reset();}
    ~State(){if(thread!=std::this_thread::get_id())std::terminate();}
};
std::shared_ptr<SharedGuildChannelDirectory53> SharedGuildChannelDirectory53::create(std::size_t expected){
    if(expected!=3)throw std::invalid_argument("Common53 requires exactly three channels");
    return std::shared_ptr<SharedGuildChannelDirectory53>(new SharedGuildChannelDirectory53(std::make_shared<State>()));
}
void SharedGuildChannelDirectory53::install(std::uint8_t k,Source source){
    state_->owner();if(k>=3||state_->sealed||state_->retired||state_->sources[k]||!source.session||!source.enumerate||!source.owner||!source.peer_ready||
        !source.recipient_ready||!source.closed||!source.send||!source.baseline||!source.online||!source.sync_name)throw std::invalid_argument("Incomplete/late Common53 channel source");
    state_->sources[k]=std::move(source);++state_->epoch;
}
void SharedGuildChannelDirectory53::seal(){state_->owner();if(state_->retired||state_->sealed||!state_->sources[0]||!state_->sources[1]||!state_->sources[2])throw std::logic_error("Incomplete/already sealed Common53 directory");state_->sealed=true;++state_->epoch;}
void SharedGuildChannelDirectory53::retire(){state_->retire();}
SharedGuildChannelDirectory53::~SharedGuildChannelDirectory53(){state_->retire();}
SharedGuildChannelDirectory53::Binding SharedGuildChannelDirectory53::binding(){
    state_->owner();const auto thread=state_->thread;const std::weak_ptr<State> weak=state_;
    const auto lock=[weak,thread]{game_thread(thread);return weak.lock();};
    Binding result;
    result.enumerate=[lock]{const auto state=lock();if(!state)throw std::logic_error("Expired Common53 directory");return state->enumerate();};
    result.owner=[lock](auto id)->std::optional<Owner>{const auto state=lock();if(!state)return {};try{return state->find(id);}catch(...){return {};}};
    result.peer_ready=[lock](const Owner& value){const auto state=lock();if(!state)return false;try{return state->ready(value,false);}catch(...){return false;}};
    result.recipient_ready=[lock](const Owner& value){const auto state=lock();if(!state)return false;try{return state->ready(value,true);}catch(...){return false;}};
    result.closed=[lock](const Owner& value){const auto state=lock();if(!state)return false;try{return state->closed(value);}catch(...){return false;}};
    result.send=[lock,weak](const Owner& value,auto bytes,auto ack){
        const auto state=lock();if(!state){if(ack)ack(false);return;}
        auto once=std::make_shared<bool>(false);
        const auto settle=[once,ack=std::move(ack)](bool good){if(*once)return;*once=true;if(ack)ack(good);};
        try{state->send(value,std::move(bytes),settle,weak);}catch(...){settle(false);throw;}
    };
    result.baseline=[lock](const Owner& value)->std::optional<Common::Baseline>{const auto state=lock();if(!state)return {};try{return state->baseline(value);}catch(...){return {};}};
    result.online=[lock]{const auto state=lock();if(!state)throw std::logic_error("Expired Common53 directory");return state->online();};
    result.sync_name=[lock](const Owner& value){const auto state=lock();if(!state)throw std::logic_error("Expired Common53 directory");state->sync_name(value);};
    return result;
}
}
