#pragma once
#include "handlers/OwnedPkRoomState.h"
#include "net/Session.h"
#include <algorithm>
#include <array>
#include <limits>
#include <map>
#include <memory>
#include <optional>
#include <stdexcept>
#include <thread>

namespace god2 {
// CUSTOM-0115 opt-in exact Session transport for durable PK grants/results.
// Borrowed RoomState/repository and this owner MUST live and drain on their
// actual game executor. No Application default, reconnect, world return,
// native ACK, new raw template or later-round grant authority is supplied.
class OwnedPkOutboxPublication final {
    friend class OwnedTaiwanPkLuaBasicOwner;
    struct Binding;
    struct Flight;
    struct Lifetime {OwnedPkOutboxPublication* owner;};
public:
    using Ticket=OwnedPkRoomState::Ticket;
    using Repository=OwnedPkRoomState::Repository;
    explicit OwnedPkOutboxPublication(OwnedPkRoomState& rooms)
        :rooms_(rooms),lifetime_(std::make_shared<Lifetime>(Lifetime{this})){}
    ~OwnedPkOutboxPublication(){
        lifetime_->owner=nullptr;
        for(auto& [id,binding]:bindings_)fail(*binding);
    }
    OwnedPkOutboxPublication(const OwnedPkOutboxPublication&)=delete;
    OwnedPkOutboxPublication& operator=(const OwnedPkOutboxPublication&)=delete;

    // Called by Admission's optional Bind AFTER both private commits, BEFORE
    // either release. Both original capabilities are stored atomically in
    // preallocated map nodes; no callback/send/DB mutation occurs here.
    bool bind(const Ticket& ticket,const std::array<std::shared_ptr<Session>,2>& sessions,
              const std::array<Session::NativePkEntryHold,2>& holds){
        check_thread();
        if(bindings_.size()>=256 || bindings_.contains(ticket.id()) || !rooms_.owns_ticket(ticket) ||
           !sessions[0] || !sessions[1] || sessions[0]==sessions[1] ||
           !sessions[0]->same_native_pk_game_executor(*sessions[1]))return false;
        const auto& input=ticket.input();
        if(!input.entry.owned_appearances() || !input.entry.owned_players() ||
           !input.combat_sources || !input.entry.waiting_control())return false;
        for(std::size_t i=0;i<2;++i){
            const auto& p=peer(ticket,i);
            const auto& material=(*input.entry.owned_appearances())[i].material();
            const auto& request=holds[i].request();
            if(by_session_.contains(p.session) || sessions[i]->id()!=p.session ||
               holds[i].session_id()!=p.session || request.account!=p.account || request.character!=p.character ||
               request.common_generation!=material.lease.generation || request.world_generation!=p.world_generation ||
               request.prebattle_generation!=p.battle_generation ||
               holds[i].committed_battle_generation()!=p.battle_generation+1 ||
               request.normal_entry_frame!=material.entry_frame || request.normal_entry_logical!=material.entry_logical ||
               request.accepted_tail!=material.accepted_tail || request.config_flag!=material.config_flag ||
               request.logical!=input.entry.records()[i] ||
               !sessions[i]->native_pk_entry_committed_current(holds[i]))return false;
        }
        auto binding=std::make_shared<Binding>(ticket,sessions,holds);
        Bindings staged;staged.emplace(ticket.id(),binding);
        SessionIndex staged_index;
        for(std::uint8_t i=0;i<2;++i)staged_index.emplace(sessions[i]->id(),Index{ticket.id(),i});
        if(staged_index.size()!=2)return false;
        // No allocation, external callback or reentry beyond this point.
        bindings_.insert(staged.extract(ticket.id()));
        while(!staged_index.empty())by_session_.insert(staged_index.extract(staged_index.begin()));
        return true;
    }

    // Fast first0B needs only THIS viewer's source-accepted Written proof.
    // The peer may still be completing its own entry. No supplied room ID or
    // scalar Session identity can mint this binding.
    std::optional<std::uint64_t> room_for(const Session& session)const noexcept{
        if(!on_thread() || session.native_battle_skill_publication_pending())return {};
        const auto indexed=by_session_.find(session.id());if(indexed==by_session_.end())return {};
        const auto at=bindings_.find(indexed->second.room);if(at==bindings_.end())return {};
        const auto& binding=*at->second;const auto viewer=indexed->second.viewer;
        if(viewer>1 || binding.sessions[viewer].get()!=&session || !written_current(binding,viewer))return {};
        return binding.ticket.id();
    }
    // Actual C2S owners can use these seams with their separately current
    // server-owned profile/skill policy. The Session/private hold derives all
    // identity and phase permits; native bytes never choose a room or epoch.
    void control_native(Session& session,const std::string& current_profile,
                        const RecoveredBattleCommand::ControlRequest& request){
        check_thread();const auto binding=caller_binding(session);
        reject_resolver_reentry(*binding);
        const auto viewer=by_session_.at(session.id()).viewer;
        const auto phase=rooms_.round(binding->ticket.id());
        rooms_.control_native(binding->ticket.id(),caller(*binding,viewer),phase.revision(),current_profile,request);
    }
    void submit_native(Session& session,const std::string& current_profile,
                       const RecoveredPkCommandSelection::Policy& policy,
                       std::span<const RecoveredWorldRecords::Record> records){
        check_thread();const auto binding=caller_binding(session);
        reject_resolver_reentry(*binding);
        const auto viewer=by_session_.at(session.id()).viewer;
        const auto phase=rooms_.round(binding->ticket.id());
        rooms_.submit_native(binding->ticket.id(),caller(*binding,viewer),phase.battle_revision(),
                             phase.grant_epoch(),current_profile,policy,records);
    }

    // CUSTOM-0118 one complete native frame, never a TCP-read prefix. Only
    // immutable server coefficients are supplied; native input cannot supply
    // a Policy header, source, MP cost, skill map, room or grant epoch.
    struct BasicParameters {
        std::uint32_t power_percent,defense_percent;
        std::uint32_t critical_chance_bp,critical_multiplier_percent;
    };
    enum class NativeBatch {Idle,ControlStored,BasicStored};
    // CUSTOM-0119 actual private runtime room supplies a freshly checked
    // durable frozen profile. No external digest authority or stat refresh.
    std::optional<NativeBatch> dispatch_native_basic(Session& session,
            const std::optional<BasicParameters>& server_basic,
            std::span<const RecoveredWorldRecords::Record> records){
        check_thread();
        if(!by_session_.contains(session.id()))return {};
        const auto binding=caller_binding(session);
        reject_resolver_reentry(*binding);
        const auto basic=server_basic;
        const auto profile=rooms_.current_owned_profile(binding->ticket.id());
        return dispatch_native_basic(session,profile,basic,records);
    }
    std::optional<NativeBatch> dispatch_native_basic(Session& session,const std::string& current_profile,
            const std::optional<BasicParameters>& server_basic,
            std::span<const RecoveredWorldRecords::Record> records){
        check_thread();
        const std::string profile=current_profile;
        const auto basic=server_basic; // No caller alias survives a later observer.
        const auto indexed=by_session_.find(session.id());
        if(indexed==by_session_.end())return {}; // Unbound: existing owner handles it.
        // An indexed but pending/failed/wrong Session MUST reject, not fall
        // through a diagnostic handler as if it had never owned a PK room.
        const auto binding=caller_binding(session);
        reject_resolver_reentry(*binding);
        if(profile!=binding->ticket.input().profile_readset_sha256)
            throw DatabaseError("PK frame lacks the separately current server profile binding");
        const RecoveredBattleCommand::ControlRequest* control=nullptr;
        const RecoveredBattleCommand::BasicAttackRequest* attack=nullptr;
        if(records.empty())throw DatabaseError("PK empty input is not an owned native frame");
        for(const auto& record:records){
            if(std::holds_alternative<RecoveredWorldRecords::Tick>(record))continue;
            if(const auto* value=std::get_if<RecoveredBattleCommand::ControlRequest>(&record)){
                if(control||attack)throw DatabaseError("PK frame mixes or repeats owned operations");
                control=value;
            }else if(const auto* value=std::get_if<RecoveredBattleCommand::BasicAttackRequest>(&record)){
                if(attack||control)throw DatabaseError("PK frame mixes or repeats owned operations");
                attack=value;
            }else throw DatabaseError("PK basic frame contains an unsupported operation");
        }
        // Entire span classified BEFORE any durable phase/intent mutation.
        // Ticks provide no grant, resolution, pump or remote receipt authority.
        if(!control&&!attack)return NativeBatch::Idle;
        const auto viewer=indexed->second.viewer;
        const auto phase=rooms_.round(binding->ticket.id());
        if(control){
            rooms_.control_native(binding->ticket.id(),caller(*binding,viewer),phase.revision(),profile,*control);
            return NativeBatch::ControlStored;
        }
        if(!basic||basic->power_percent>10000||basic->defense_percent>100||
           basic->critical_chance_bp>10000||basic->critical_multiplier_percent<100||
           basic->critical_multiplier_percent>1000)
            throw DatabaseError("PK basic frame requires explicit bounded server coefficients");
        RecoveredPkCommandSelection::Policy policy{0,0,
            binding->ticket.input().entry.command_contexts()[viewer],
            BattleAction{0,{},false,basic->power_percent,basic->defense_percent,0,
                basic->critical_chance_bp,basic->critical_multiplier_percent},{}};
        rooms_.submit_native(binding->ticket.id(),caller(*binding,viewer),phase.battle_revision(),
                             phase.grant_epoch(),profile,policy,records);
        return NativeBatch::BasicStored; // No implicit resolver or inline send.
    }

    // CUSTOM-0118 explicit owner resolution joins the privately bound pair to
    // CUSTOM-0117 fresh basic results. Actual Lua Rule/order/next masks remain
    // supplied, never initial-mask/target/arrival-order guesses. No auto-pump.
    void resolve_collected_basic(Session& session,const std::array<std::uint8_t,2>& server_order,
            const OwnedPkRound::Masks& next_control_masks,const Battle::Rule& supplied_rule){
        resolve_collected_basic_impl(session,server_order,next_control_masks,supplied_rule);
    }
    // CUSTOM-0122 actual room-owned post-result notification policy. This
    // explicit seam keeps the same private transport/pure Rule/reentry fences.
    void resolve_collected_basic_notifications(Session& session,
            const std::array<std::uint8_t,2>& server_order,const Battle::Rule& supplied_rule){
        resolve_collected_basic_impl(session,server_order,std::nullopt,supplied_rule);
    }
private:
    // CUSTOM-0123 consumed only by the concrete Lua owner that OWNS this
    // publication. CUSTOM-0124 also consumes it on a later scheduled game
    // visit, never inline from input/write callbacks. A pending token is a
    // retry condition, not an ACK/strand-idle proof. Actual Session staging
    // waits for the ordinary response enqueue and guards old input prefixes.
    enum class BasicAdvance {AwaitingTransport,Idle,OutputVisited,Resolved};
    std::optional<BasicAdvance> advance_basic_notifications_at_idle(Session& session,
            const std::array<std::uint8_t,2>& order,const Battle::Rule& rule){
        check_thread();
        const auto indexed=by_session_.find(session.id());
        if(indexed==by_session_.end())return {};
        const auto at=bindings_.find(indexed->second.room);
        if(at==bindings_.end())throw DatabaseError("PK idle owner lost its private binding");
        const auto binding=at->second;
        reject_resolver_reentry(*binding);
        if(indexed->second.viewer>1 || binding->failed ||
           binding->sessions[indexed->second.viewer].get()!=&session ||
           !rooms_.owns_ticket(binding->ticket) ||
           binding->sessions[0]->closing() || binding->sessions[1]->closing()){
            fail(*binding);
            throw DatabaseError("PK idle owner requires its exact retained Session pair");
        }
        try{
            for(std::uint8_t viewer=0;viewer<2;++viewer)
                if(!binding->sessions[viewer]->native_pk_entry_binding_current(binding->holds[viewer]))
                    throw DatabaseError("PK idle owner retained a revoked private entry identity");
            if(!resolution_transport_current(*binding))return BasicAdvance::AwaitingTransport;
            const auto phase=rooms_.round(binding->ticket.id()).phase();
            if(phase==OwnedPkRound::Phase::Ready){
                // The resolver reobserves current private profile/phase/checkpoint
                // and fences the synchronous Lua call before any settlement.
                resolve_collected_basic_notifications(session,order,rule);
                publish_pending(binding->ticket.id());
                return BasicAdvance::Resolved;
            }
            if(phase==OwnedPkRound::Phase::Grants || phase==OwnedPkRound::Phase::ResultsControl ||
               phase==OwnedPkRound::Phase::Terminal){
                publish_pending(binding->ticket.id());
                // No rows means no flight/pending token was installed. Stop
                // scheduled retries until the next real input dirties it.
                return resolution_transport_current(*binding)?BasicAdvance::Idle:BasicAdvance::OutputVisited;
            }
            // Initial outbox revision1 belongs to Admission's entry writer. A
            // one-sided control or collected attack never triggers resolution.
            return BasicAdvance::Idle;
        }catch(...){fail(*binding);throw;}
    }
    void resolve_collected_basic_impl(Session& session,const std::array<std::uint8_t,2>& server_order,
            const std::optional<OwnedPkRound::Masks>& next_control_masks,const Battle::Rule& supplied_rule){
        check_thread();
        const auto order=server_order;const auto masks=next_control_masks;
        const auto rule=supplied_rule;
        const auto binding=caller_binding(session);
        reject_resolver_reentry(*binding);
        if(!rule||!resolution_transport_current(*binding))
            throw DatabaseError("PK resolver requires both private Written peers with cleared publication");
        const auto profile=rooms_.current_owned_profile(binding->ticket.id());
        const auto before=rooms_.inspect(binding->ticket.id());
        const auto phase=rooms_.round(binding->ticket.id()).document();
        if(!before)throw DatabaseError("PK resolver lost its actual shared Battle");
        binding->resolving=true;binding->resolver_reentered=false;
        struct End {Binding& value;~End(){value.resolving=false;}}end{*binding};
        try{
            const auto source_current=[&]{
                return !binding->resolver_reentered&&resolution_transport_current(*binding)&&
                    rooms_.inspect(binding->ticket.id())==before&&
                    rooms_.round(binding->ticket.id()).document()==phase&&
                    rooms_.current_owned_profile(binding->ticket.id())==profile;
            };
            const Battle::Rule checked_rule=[&](const CombatRuleInput& input){
                if(!source_current())throw DatabaseError("PK resolver authority changed before pure Rule");
                const auto result=rule(input);
                if(!source_current())throw DatabaseError("PK resolver authority changed during pure Rule");
                return result;
            };
            if(masks)rooms_.resolve_collected_basic(binding->ticket.id(),order,*masks,checked_rule);
            else rooms_.resolve_collected_basic_notifications(binding->ticket.id(),order,checked_rule);
        }catch(...){fail(*binding);throw;}
    }

public:
    // Explicit game-owner pump only. Entry callbacks and output completion
    // never auto-pump: Session's pending token clears later on its strand.
    // Await a later owner dispatch if a private Written proof/pending clear is
    // not ready. Never interpret that bounded handoff window as an ACK.
    void publish_pending(std::uint64_t room){
        check_thread();const auto at=bindings_.find(room);
        if(at==bindings_.end())throw DatabaseError("PK output room is not privately bound");
        const auto binding=at->second;
        reject_resolver_reentry(*binding);
        if(binding->failed)throw DatabaseError("PK output owner retained after failure");
        if(binding->pumping)return;
        binding->pumping=true;
        struct End {bool& flag;~End(){flag=false;}}end{binding->pumping};
        try {
            if(!rooms_.owns_ticket(binding->ticket))throw DatabaseError("PK output room incarnation changed");
            if(binding->sessions[0]->closing() || binding->sessions[1]->closing())
                throw DatabaseError("PK output peer closed; durable recovery required");
            const auto rows=rooms_.pending(room);
            const auto grants=rooms_.pending_grants(room);
            for(std::uint8_t viewer=0;viewer<2;++viewer){
                if(binding->failed)break;
                auto& session=*binding->sessions[viewer];
                if(binding->flights[viewer] || session.native_battle_skill_publication_pending())continue;
                if(!session.native_pk_entry_written_current(binding->holds[viewer])){
                    if(session.closing())throw DatabaseError("PK entry peer closed before output publication");
                    continue;
                }
                const auto row=std::find_if(rows.begin(),rows.end(),[&](const auto& value){return value.viewer==viewer;});
                const auto grant=std::find_if(grants.begin(),grants.end(),[&](const auto& value){return value.viewer==viewer;});
                if(row!=rows.end() && grant!=grants.end())throw DatabaseError("PK result and grant phases overlap");
                if(row==rows.end() && grant==grants.end())continue;
                // Revision1 belongs exclusively to the admission entry writer.
                if(row!=rows.end() && row->revision<=1)throw DatabaseError("PK entry outbox cannot use result writer");
                if(sequence_==std::numeric_limits<std::uint64_t>::max())throw DatabaseError("PK output sequence exhausted");
                const bool is_grant=grant!=grants.end();
                const auto& bytes=is_grant?grant->logical:row->logical;
                const auto& p=peer(binding->ticket,viewer);
                auto delivery=std::make_shared<const Session::NativeBattleSkillDelivery>(
                    Session::NativeBattleSkillDelivery{p.session,p.account,p.character,
                        binding->holds[viewer].request().common_generation,p.battle_generation+1,++sequence_,bytes});
                auto flight=std::make_shared<Flight>(lifetime_,binding,viewer,is_grant,
                    is_grant?grant->epoch:row->revision,std::move(delivery));
                // Stage before ANY sender callback or asynchronous handoff.
                binding->flights[viewer]=flight;
                if(!row_current(*binding,*flight))throw DatabaseError("PK output row changed before enqueue");
                session.send_native_pk_output(binding->holds[viewer],flight->delivery,flight);
            }
        }catch(...){fail(*binding);throw;}
    }
private:
    struct Flight final:Session::NativeBattleSkillPublicationOwner {
        std::weak_ptr<Lifetime> lifetime;
        std::weak_ptr<Binding> binding;
        std::uint8_t viewer;
        bool grant;
        std::uint64_t key;
        Session::NativeBattleSkill delivery;
        bool before_seen=false,complete_seen=false;
        Flight(std::weak_ptr<Lifetime> life,std::weak_ptr<Binding> owner,std::uint8_t side,
               bool is_grant,std::uint64_t value,Session::NativeBattleSkill bytes)
            :lifetime(std::move(life)),binding(std::move(owner)),viewer(side),grant(is_grant),key(value),delivery(std::move(bytes)){}
        bool before_native_battle_write(Session& session,const Session::NativeBattleSkill& value)override{
            const auto life=lifetime.lock();
            return life&&life->owner&&life->owner->before(*this,session,value);
        }
        bool complete_native_battle_write(Session& session,const Session::NativeBattleSkill& value,bool written)override{
            const auto life=lifetime.lock();
            return life&&life->owner&&life->owner->complete(*this,session,value,written);
        }
    };
    struct Binding {
        Ticket ticket;
        std::array<std::shared_ptr<Session>,2> sessions;
        std::array<Session::NativePkEntryHold,2> holds;
        std::array<std::shared_ptr<Flight>,2> flights;
        // CUSTOM-0127 actual immutable deliveries accepted by fullwrite in
        // THIS original binding. Durable submitted flags never mint these.
        std::array<Session::NativeBattleSkill,2> terminal_written;
        std::array<std::uint64_t,2> terminal_written_revision{};
        bool failed=false,pumping=false,resolving=false,resolver_reentered=false;
        Binding(Ticket value,std::array<std::shared_ptr<Session>,2> peers,
                std::array<Session::NativePkEntryHold,2> entries)
            :ticket(std::move(value)),sessions(std::move(peers)),holds(std::move(entries)){}
    };
    struct Index {std::uint64_t room;std::uint8_t viewer;};
    using Bindings=std::map<std::uint64_t,std::shared_ptr<Binding>>;
    using SessionIndex=std::map<std::uint64_t,Index>;
    OwnedPkRoomState& rooms_;
    std::shared_ptr<Lifetime> lifetime_;
    Bindings bindings_;
    SessionIndex by_session_;
    const std::thread::id thread_=std::this_thread::get_id();
    std::uint64_t sequence_=0; // Transport correlation, NOT a grant/round permit.
    bool on_thread()const noexcept{return thread_==std::this_thread::get_id();}
    void check_thread()const{if(!on_thread())throw std::logic_error("PK output game owner mismatch");}
    static const OwnedPkInvitationService::Peer& peer(const Ticket& ticket,std::size_t viewer)noexcept{
        return viewer==0?ticket.input().pair.challenger:ticket.input().pair.recipient;
    }
    bool written_current(const Binding& binding,std::uint8_t viewer)const noexcept{
        return !binding.failed && rooms_.owns_ticket(binding.ticket) &&
            !binding.sessions[0]->closing() && !binding.sessions[1]->closing() &&
            binding.sessions[viewer]->native_pk_entry_written_current(binding.holds[viewer]);
    }
    std::shared_ptr<Binding> caller_binding(const Session& session)const{
        const auto room=room_for(session);
        if(!room)throw DatabaseError("PK input lacks this Session's accepted private entry");
        return bindings_.at(*room);
    }
    static void reject_resolver_reentry(Binding& binding){
        if(binding.resolving){
            binding.resolver_reentered=true;
            throw DatabaseError("PK pure resolver reentered its input/output owner");
        }
    }
    bool resolution_transport_current(const Binding& binding)const noexcept{
        return written_current(binding,0)&&written_current(binding,1)&&
            !binding.flights[0]&&!binding.flights[1]&&!binding.pumping&&
            !binding.sessions[0]->native_battle_skill_publication_pending()&&
            !binding.sessions[1]->native_battle_skill_publication_pending();
    }
    static OwnedPkRoomState::NativeCaller caller(const Binding& binding,std::uint8_t viewer){
        const auto& p=peer(binding.ticket,viewer);
        return {p.session,p.account,p.character,p.world_generation,p.battle_generation+1,true};
    }
    bool row_current(const Binding& binding,const Flight& flight){
        if(!written_current(binding,flight.viewer))return false;
        const auto checkpoint=rooms_.inspect(binding.ticket.id());
        if(!checkpoint)return false;
        const auto phase=rooms_.round(binding.ticket.id());
        if(!flight.grant&&phase.terminal_notification()&&
           !rooms_.terminal_notification_current(binding.ticket.id(),flight.delivery->logical))return false;
        if(phase.battle_revision()!=checkpoint->revision ||
           (flight.grant?phase.grant_epoch()!=flight.key:checkpoint->revision!=flight.key))return false;
        const auto& p=peer(binding.ticket,flight.viewer);
        const auto match=[&](const auto& row){
            return row.room==binding.ticket.id() && row.viewer==flight.viewer && row.session==p.session &&
                row.world_generation==p.world_generation && row.battle_generation==p.battle_generation+1 &&
                row.logical==flight.delivery->logical;
        };
        if(flight.grant){
            const auto rows=rooms_.pending_grants(binding.ticket.id());
            return std::count_if(rows.begin(),rows.end(),[&](const auto& row){return row.epoch==flight.key&&match(row);})==1;
        }
        const auto rows=rooms_.pending(binding.ticket.id());
        return std::count_if(rows.begin(),rows.end(),[&](const auto& row){return row.revision==flight.key&&match(row);})==1;
    }
    bool exact_flight(const Binding& binding,const Flight& flight,const Session& session,
                      const Session::NativeBattleSkill& value)const noexcept{
        const auto at=bindings_.find(binding.ticket.id());
        return at!=bindings_.end() && at->second.get()==&binding && flight.viewer<2 &&
            binding.flights[flight.viewer].get()==&flight && binding.sessions[flight.viewer].get()==&session &&
            value==flight.delivery && written_current(binding,flight.viewer);
    }
    bool before(Flight& flight,Session& session,const Session::NativeBattleSkill& value){
        if(!on_thread())return false;
        const auto binding=flight.binding.lock();if(!binding)return false;
        try {
            if(flight.before_seen || flight.complete_seen || !exact_flight(*binding,flight,session,value) ||
               !row_current(*binding,flight)){fail(*binding);return false;}
            flight.before_seen=true;return true;
        }catch(...){fail(*binding);return false;}
    }
    bool complete(Flight& flight,Session& session,const Session::NativeBattleSkill& value,bool written){
        if(!on_thread())return false;
        const auto binding=flight.binding.lock();if(!binding)return false;
        try {
            if(flight.complete_seen || !flight.before_seen || !written ||
               !exact_flight(*binding,flight,session,value) || session.native_battle_skill_written()!=value ||
               !row_current(*binding,flight)){fail(*binding);return false;}
            flight.complete_seen=true;
            // ONLY actual exact full local async_write crosses this boundary.
            // Typed epoch and checkpoint revision can never acknowledge each other.
            if(flight.grant)rooms_.grant_submitted(binding->ticket.id(),flight.key,flight.viewer);
            else {
                rooms_.submitted(binding->ticket.id(),flight.key,flight.viewer);
                if(rooms_.terminal_notification_current(binding->ticket.id(),value->logical)){
                    binding->terminal_written[flight.viewer]=value;
                    binding->terminal_written_revision[flight.viewer]=flight.key;
                    if(binding->terminal_written[0]&&binding->terminal_written[1]){
                        for(std::uint8_t viewer=0;viewer<2;++viewer)
                            if(binding->terminal_written_revision[viewer]!=flight.key||
                               !written_current(*binding,viewer)||
                               binding->sessions[viewer]->native_battle_skill_written()!=binding->terminal_written[viewer])
                                throw DatabaseError("PK terminal resource save lost its exact two fullwrite observations");
                        // Current callback still owns a pending token. Do not
                        // require pending-clear or auto-pump/re-enter Session.
                        rooms_.commit_terminal_resources(binding->ticket.id(),
                            {binding->terminal_written[0]->logical,binding->terminal_written[1]->logical});
                    }
                }
            }
            binding->flights[flight.viewer].reset();
            return true; // No auto-pump while Session's pending token is alive.
        }catch(...){fail(*binding);return false;}
    }
    static void fail(Binding& binding)noexcept{
        if(binding.failed)return;
        binding.failed=true;
        for(const auto& session:binding.sessions)try{session->close();}catch(...){}
        // Active room, locks, rows and submitted flags stay retained. No
        // abandon, implicit resource retry, resend/reset or synthetic world
        // return. A prior explicit terminal resource COMMIT stays durable.
    }
};
}
