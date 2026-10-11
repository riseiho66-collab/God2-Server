#pragma once
#include "SharedGuildCoordinator53Draft.h"
#include <array>

namespace god2 {
// Source-phase protocol bootstrap. An ordered enqueue receipt is an EXPECTED
// native cache state, not a client memory observation or acceptance evidence.
// Based on retained native91/92 composition: valid count0..50, terminated row
// names, matching current self profile, ordered delivery and no roster writer
// interleaving. Reset closes the native guild UI; fresh Help grants separately.
class GuildRelationCacheBootstrap53:public std::enable_shared_from_this<GuildRelationCacheBootstrap53> {
public:
    using Common=SharedGuildCoordinator53Draft;using Owner=Common::Owner;
    struct Self {Owner owner;std::string name;std::uint8_t level{},profession{};bool operator==(const Self&)const=default;};
    using Read=std::function<std::optional<Self>(const Owner&)>;
    using Complete=std::function<void(const Owner&)>;
    GuildRelationCacheBootstrap53(Read read,Common::Send send,Complete complete)
        :read_(std::move(read)),send_(std::move(send)),complete_(std::move(complete)){}
    std::optional<Common::Baseline> baseline(const Owner& owner){
        if(!read_||!send_)return {};
        const auto hold=shared_from_this();const auto self=read_(owner);if(!self||self->owner!=owner)return {};
        const auto at=states_.find(owner.session);
        if(at!=states_.end()){
            if(at->second.completed&&Common::Panel::same_native_namespace(at->second.self.owner,owner)&&
                at->second.self.name==self->name){
                Common::Baseline value{owner,{},false};value.origin=Common::Baseline::Origin::OrderedNativeReset;return value;
            }
            if(!at->second.completed&&at->second.self==*self)return {};
        }
        if(serial_==UINT64_MAX)return {};
        State state;state.self=*self;state.attempt=++serial_;
        // Every byte slot is retired on each pass because native92 swaps the
        // last row into a removed position and duplicate slots may occur.
        for(unsigned pass=0;pass<50;++pass)for(unsigned slot=0;slot<256;++slot){
            const auto index=(pass*256+slot)/1280;
            state.chunks[index].push_back(0x92);state.chunks[index].push_back(static_cast<std::uint8_t>(slot));
        }
        state.chunks[10]=RecoveredGuildRoster::member(0,0,self->level,self->profession,1,self->name);
        state.chunks[10].insert(state.chunks[10].end(),{0x92,0});
        const auto attempt=state.attempt;states_.insert_or_assign(owner.session,std::move(state));dispatch(owner.session,attempt);return {};
    }
    void revoke(std::uint64_t session){states_.erase(session);}
private:
    struct State {Self self;std::array<std::vector<std::uint8_t>,11> chunks;std::uint64_t attempt{};std::size_t next{};bool pending{},completed{};};
    bool exact(std::uint64_t session,std::uint64_t attempt)const{
        const auto at=states_.find(session);if(at==states_.end()||at->second.attempt!=attempt)return false;
        const auto captured=at->second.self;const auto current=read_(captured.owner);
        const auto after=states_.find(session);return after!=states_.end()&&after->second.attempt==attempt&&after->second.self==captured&&current==std::optional{captured};
    }
    void stop(std::uint64_t session,std::uint64_t attempt){const auto at=states_.find(session);if(at!=states_.end()&&at->second.attempt==attempt)states_.erase(at);}
    void dispatch(std::uint64_t session,std::uint64_t attempt){
        const auto hold=shared_from_this();
        try{
            if(!exact(session,attempt)){stop(session,attempt);return;}
            auto& state=states_.at(session);if(state.pending||state.completed)return;
            const auto index=state.next;const auto owner=state.self.owner;const auto logical=state.chunks[index];state.pending=true;
            const auto weak=weak_from_this();send_(owner,logical,[weak,session,attempt,index](bool accepted){
                if(const auto self=weak.lock())self->ack(session,attempt,index,accepted);
            });
        }catch(...){stop(session,attempt);}
    }
    void ack(std::uint64_t session,std::uint64_t attempt,std::size_t index,bool accepted){
        try{
            const auto at=states_.find(session);if(at==states_.end()||at->second.attempt!=attempt)return;
            if(!accepted||!at->second.pending||at->second.next!=index||!exact(session,attempt)){stop(session,attempt);return;}
            auto& state=states_.at(session);state.pending=false;++state.next;
            if(state.next<state.chunks.size()){dispatch(session,attempt);return;}
            state.completed=true;const auto owner=state.self.owner;if(complete_)complete_(owner);
        }catch(...){stop(session,attempt);}
    }
    Read read_;Common::Send send_;Complete complete_;std::map<std::uint64_t,State> states_;std::uint64_t serial_{};
};
}
