#include "game/SharedTaiwanNativeSpectatorSource.h"
#include "protocol/RecoveredWorldFrame.h"
#include <exception>
#include <map>
#include <stdexcept>
#include <thread>
#include <utility>
#include <variant>

namespace god2 {
namespace {
using Source=SharedTaiwanNativeSpectatorSource;
using Input=std::variant<Source::Request,Source::CloseRequest>;
struct Slot {
    const Source::Lease lease;
    const std::weak_ptr<Session> session;
    const SharedNativeWorldTransports::Token token;
    bool live=true;
    Slot(const Source::Lease& identity,const std::shared_ptr<Session>& connection,
        const SharedNativeWorldTransports::Token& registered):lease(identity),session(connection),token(registered) {}
};
bool same_root(const RecoveredCharacter& a,const RecoveredCharacter& b) {
    return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot && a.profile==b.profile &&
        a.created_at==b.created_at && a.name_codepage==b.name_codepage && a.streamer_privilege==b.streamer_privilege;
}
bool same_scope(const Source::Scope& a,const Source::Scope& b) {
    return a.lease==b.lease && same_root(a.character,b.character) && a.saved_position==b.saved_position &&
        a.phase==b.phase && a.battle_generation==b.battle_generation;
}
bool native_phase(SessionState phase) {return phase==SessionState::InWorld || phase==SessionState::InBattle;}
struct Owner {
    const std::thread::id thread=std::this_thread::get_id();
    const std::shared_ptr<SharedWorldPresence> presence;
    const std::shared_ptr<SharedNativeWorldTransports> transports;
    const std::shared_ptr<Source::WorldOwner> world;
    const std::shared_ptr<Source::CloseOwner> close;
    const std::shared_ptr<SharedNativeSpectatorPublication> publication;
    const std::shared_ptr<SharedNativeSpectatorTargets> targets;
    const Source::Budgets budgets;
    const std::size_t capacity;
    std::map<std::uint64_t,std::shared_ptr<Slot>> slots;
    std::shared_ptr<Slot> active;
    bool operating=false,reentered=false;
    Owner(std::shared_ptr<SharedWorldPresence> p,std::shared_ptr<SharedNativeWorldTransports> t,
        std::shared_ptr<Source::WorldOwner> w,Source::Budgets b,std::size_t c,
        std::shared_ptr<SharedNativeSpectatorPublication> ui,std::shared_ptr<SharedNativeSpectatorTargets> namespace_source,
        std::shared_ptr<Source::CloseOwner> close_owner)
        :presence(std::move(p)),transports(std::move(t)),world(std::move(w)),close(std::move(close_owner)),
         publication(std::move(ui)),targets(std::move(namespace_source)),budgets(b),capacity(c) {}
    ~Owner() {
        if(thread!=std::this_thread::get_id())std::terminate();
        operating=true;reentered=true;
        for(auto& item:slots)item.second->live=false;
        slots.clear();active.reset(); // No common lease/token/native cleanup.
    }
    void owner() const {
        if(thread!=std::this_thread::get_id())throw std::logic_error("TW spectator source game owner mismatch");
    }
    void poison() {
        owner();if(!operating)return;
        reentered=true;if(active)active->live=false;
    }
    struct Operation {
        Owner& state;
        explicit Operation(Owner& s):state(s) {
            state.owner();if(state.operating) {
                state.poison();throw std::logic_error("TW spectator source reentry rejected");
            }
            state.operating=true;state.reentered=false;
        }
        ~Operation(){state.active.reset();state.operating=false;}
    };
    bool endpoint(Session& session,const std::shared_ptr<Slot>& slot) const {
        if(reentered || !slot || !slot->live || slot->session.lock().get()!=&session || session.closing() ||
           session.id()!=slot->lease.session || session.account_id!=slot->lease.account ||
           session.character_id!=slot->lease.character || !session.recovered_world_ready() || !native_phase(session.state()) ||
           !session.common_world_delivery_current(slot->lease.account,slot->lease.character,slot->lease.generation) ||
           session.common_world_entry_current(slot->lease.account,slot->lease.character,slot->lease.generation))return false;
        const auto found=slots.find(slot->lease.session);
        return found!=slots.end() && found->second==slot && transports->registry_current(slot->token);
    }
    std::optional<SharedWorldPresence::ReadyCharacter> root(Session& session,const std::shared_ptr<Slot>& slot) const {
        if(!endpoint(session,slot))return std::nullopt;
        const auto rows=presence->ready_characters();if(!rows || !endpoint(session,slot))return std::nullopt;
        std::optional<SharedWorldPresence::ReadyCharacter> actual;
        for(const auto& row:*rows)if(row.lease==slot->lease) {
            if(actual || row.character.id!=slot->lease.character || row.character.account_id!=slot->lease.account)return std::nullopt;
            actual=row;
        }
        return actual;
    }
    std::optional<Source::Scope> snapshot(Session& session,const std::shared_ptr<Slot>& slot,const Input& request) const {
        if(!endpoint(session,slot))return std::nullopt;
        const auto phase=session.state();const auto generation=session.battle_generation();
        if(!transports->current(slot->token) || !endpoint(session,slot))return std::nullopt;
        const auto first=root(session,slot);if(!first)return std::nullopt;
        const auto six=std::get_if<Source::Request>(&request);
        // The saved registry token identifies this actual recipient, including
        // endpoint incarnation. Never select UI history through a name/low ID.
        std::optional<SharedNativeSpectatorPublication::Observation> ui;
        if(publication) {
            ui=publication->observe(slot->token);
            if(ui->lease()!=slot->lease || !transports->same_registration(ui->token(),slot->token) ||
               !publication->current(*ui) || !endpoint(session,slot))return std::nullopt;
        }
        std::optional<SharedNativeSpectatorTargets::Observation> target;
        if(targets && six) {
            target=targets->resolve(slot->token,six->context()); // Full DWORD, never mask/cast to WORD.
            if(!ui || !target->ui() || !transports->same_registration(target->token(),slot->token) ||
               !publication->same(*ui,*target->ui()) || !targets->current(*target) || !endpoint(session,slot))return std::nullopt;
        }
        if(!transports->current(slot->token) || !endpoint(session,slot))return std::nullopt;
        const auto last=root(session,slot);
        if(!last || !same_root(first->character,last->character) || first->position!=last->position ||
           !endpoint(session,slot) || session.state()!=phase || session.battle_generation()!=generation)return std::nullopt;
        if(publication) {
            const auto after_ui=publication->observe(slot->token);
            if(!publication->same(*ui,after_ui) || !publication->current(after_ui) || !endpoint(session,slot))return std::nullopt;
            if(targets && six) {
                const auto after_target=targets->resolve(slot->token,six->context());
                if(!targets->same(*target,after_target) || !targets->current(after_target) ||
                   !after_target.ui() || !publication->same(after_ui,*after_target.ui()) || !endpoint(session,slot))return std::nullopt;
                target=after_target;
            }
            // Actual current observers may visit the repository. Re-read root
            // after them, then use only pure UI/endpoint registry checks.
            const auto final=root(session,slot);
            if(!final || !same_root(last->character,final->character) || last->position!=final->position ||
               !publication->registry_current(after_ui) || (target && !targets->registry_current(*target)) || !endpoint(session,slot) ||
               session.state()!=phase || session.battle_generation()!=generation)return std::nullopt;
            ui=after_ui;
        }
        return Source::Scope{slot->lease,last->character,last->position,phase,generation,std::move(ui),std::move(target)};
    }
    std::optional<Source::Scope> qualified(Session& session,const std::shared_ptr<Slot>& slot,
        Source::Check check,const Input& request,const Source::Result* result) {
        const auto before=snapshot(session,slot,request);if(!before)return std::nullopt;
        if(result && (before->phase!=result->expected_post_phase ||
           before->battle_generation!=result->expected_post_battle_generation))return std::nullopt;
        const auto six=std::get_if<Source::Request>(&request);
        const bool actual_current=six?world->current(session,check,*before,*six,result):
            (close && close->current(session,check,*before,std::get<Source::CloseRequest>(request),result));
        if(!actual_current || !endpoint(session,slot))return std::nullopt;
        const auto after=snapshot(session,slot,request);
        if(!after || !same_scope(*before,*after) || bool(before->native_ui)!=bool(after->native_ui) ||
           bool(before->native_target)!=bool(after->native_target))return std::nullopt;
        if(before->native_ui && (!publication || !publication->same(*before->native_ui,*after->native_ui)))return std::nullopt;
        if(before->native_target && (!targets || !targets->same(*before->native_target,*after->native_target)))return std::nullopt;
        return after;
    }
    bool wire(const Source::Reply& reply) const {
        const auto& output=reply.bytes();
        if(reply.native_no_reply())return output.empty(); // Explicit actual handler decision.
        if(output.empty() || output.size()>budgets.max_output_bytes)return false;
        for(std::size_t at=0;at<output.size();) {
            if(output.size()-at<2)return false;
            const auto size=std::size_t{output[at]}+256u*output[at+1];
            if(size<4 || size>RecoveredWorldFrame::max_logical_size+3 || size>output.size()-at)return false;
            at+=size;
        }
        // Structure only. Real WorldOwner qualifies same cipher/profile/output;
        // existing Session later validates full envelope/checksum. Never decode.
        return true;
    }
    std::optional<Source::Reply> dispatch(Session& session,const Input& input) {
        Operation operation(*this);
        const auto request=input; // Copy all actual request bytes before callbacks.
        if(const auto six=std::get_if<Source::Request>(&request)) {
            if(!RecoveredSpectator6E::observed_producer_shape(*six))return std::nullopt;
        }else {
            const auto& raw=std::get<Source::CloseRequest>(request);
            if(!close || !publication || (raw.opcode!=0xa3 && raw.opcode!=0xcb))return std::nullopt;
        }
        const auto connection=session.shared_from_this(); // Strong before any repo observer.
        if(connection.get()!=&session || session.closing() || !native_phase(session.state()) ||
           !session.recovered_world_ready())return std::nullopt;
        std::shared_ptr<Slot> slot;
        if(const auto found=slots.find(session.id());found!=slots.end()) {
            slot=found->second;
            if(slot->session.lock()!=connection || slot->lease.account!=session.account_id ||
               slot->lease.character!=session.character_id)return std::nullopt; // No foreign/successor poison.
            active=slot;if(!endpoint(session,slot))return std::nullopt;
        }
        try {
            const auto lease=presence->ready_lease(session.id(),session.account_id,session.character_id);
            if(!lease || reentered || (slot && slot->lease!=*lease))return std::nullopt;
            if(!slot) {
                const auto registered=transports->lookup(*lease);
                if(!registered || reentered || slots.size()>=capacity)return std::nullopt;
                const auto tw=std::get_if<std::shared_ptr<Session>>(&registered->transport());
                if(!tw || *tw!=connection || !transports->registry_current(*registered))return std::nullopt;
                slot=std::make_shared<Slot>(*lease,connection,registered->token());
                if(!slots.emplace(lease->session,slot).second)return std::nullopt;
                active=slot;
            }
            const auto before=qualified(session,slot,Source::Check::BeforeExecute,request,nullptr);
            if(!before)throw std::runtime_error("TW spectator actual pre-execution authority failed");
            // Exactly once: no loop/retry/default result. Real execute owns the
            // committed prefix, admission/exit membership and native reply.
            const auto six=std::get_if<Source::Request>(&request);
            auto result=six?world->execute(session,*before,*six):
                close->execute(session,*before,std::get<Source::CloseRequest>(request));
            if(!result || !native_phase(result->expected_post_phase) || !endpoint(session,slot) || !wire(result->reply))
                throw std::runtime_error("TW spectator actual execution/result failed");
            if(!qualified(session,slot,Source::Check::AfterExecute,request,&*result) ||
               !qualified(session,slot,Source::Check::BeforeReturn,request,&*result) || !endpoint(session,slot))
                throw std::runtime_error("TW spectator actual post-execution source failed");
            return std::move(result->reply);
        }catch(...) {
            if(slot)slot->live=false; // Only this retained exact own slot, never common successor cleanup.
            throw;
        }
    }
    void release(Session& session) {
        Operation operation(*this);
        const auto found=slots.find(session.id());if(found==slots.end())return;
        const auto slot=found->second;
        if(slot->session.lock().get()!=&session)return;
        slots.erase(found);slot->live=false; // Erase before destruction, own bookkeeping only.
    }
};
}
SharedTaiwanNativeSpectatorSource::Binding SharedTaiwanNativeSpectatorSource::create(
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<SharedNativeWorldTransports> transports,
    std::shared_ptr<WorldOwner> world,Budgets budgets,std::size_t capacity,
    std::shared_ptr<SharedNativeSpectatorPublication> publication,std::shared_ptr<SharedNativeSpectatorTargets> targets,
    std::shared_ptr<CloseOwner> close) {
    if(!presence || !transports || !transports->owns_presence(presence) || !world || !capacity || budgets.max_output_bytes<4 ||
       (close && !publication) || (publication && !publication->owns_source(presence,transports)) ||
       (targets && (!publication || !targets->owns_source(presence,transports,publication))))
        throw std::invalid_argument("TW spectator source requires actual same-presence transport/handler/budgets/capacity");
    auto owner=std::make_shared<Owner>(std::move(presence),std::move(transports),std::move(world),budgets,capacity,std::move(publication),std::move(targets),std::move(close));
    Binding binding{
        [owner](Session& session,const Request& request){return owner->dispatch(session,request);},
        [owner](Session& session){owner->release(session);},
        [owner]{owner->poison();},{}
    };
    if(owner->close)binding.close_dispatch=[owner](Session& session,const CloseRequest& request){return owner->dispatch(session,request);};
    return binding;
}
}
