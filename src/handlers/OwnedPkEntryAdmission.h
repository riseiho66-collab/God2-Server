#pragma once
#include "handlers/OwnedPkRoomState.h"
#include "cn/world/SharedActorVisibility.h"
#include "net/Session.h"
#include <array>
#include <map>
#include <memory>
#include <optional>
#include <thread>
#include <utility>

namespace god2 {
// CUSTOM-0108 concrete asynchronous admission consumer. Application hosting,
// original context/grant/skill producers and terminal recovery remain separate.
// All borrowed room/repository/source dependencies and this owner must drain
// on their actual game executor before shutdown. No client ACK is invented.
class OwnedPkEntryAdmission final:public OwnedPkInvitationService::AsyncRoomAuthority {
    struct Attempt;
    struct Lifetime {OwnedPkEntryAdmission* owner;};
public:
    static constexpr std::size_t max_retained_rooms=256; // CUSTOM-0108 admission quota.
    using Invitations=OwnedPkInvitationService;
    using Ticket=OwnedPkRoomState::Ticket;
    // Produces an actual reserved repository ticket, including private269
    // players/268 combat/267 appearance and all separately qualified records.
    // It cannot substitute caller statistics, an ID or a fabricated bool.
    using Prepare=std::function<std::optional<Ticket>(const Invitations::Pair&)>;
    using Sessions=std::function<std::shared_ptr<Session>(std::uint64_t)>;
    // CUSTOM-0115 optional output/input owner binding BEFORE either entry is
    // released. Only stores exact committed capabilities; never pumps output
    // here or waits for both written callbacks to find a fast peer's first0B.
    using Bind=std::function<bool(const Ticket&,const std::array<std::shared_ptr<Session>,2>&,
                                 const std::array<Session::NativePkEntryHold,2>&)>;
    // CUSTOM-0130 exclusive additive bind path. The real Attempt supplies its
    // privately minted departure; no caller scalar can recreate this token.
    using DepartureBind=std::function<bool(const Ticket&,const std::array<std::shared_ptr<Session>,2>&,
        const std::array<Session::NativePkEntryHold,2>&,const cn::SharedActorVisibility::TaiwanPkDeparture&)>;
    OwnedPkEntryAdmission(OwnedPkRoomState& rooms,Prepare prepare,Sessions sessions,
                          Invitations::Resolve peers,
                          std::shared_ptr<cn::SharedActorVisibility> world_visibility = {},
                          std::shared_ptr<SharedWorldPresence> world_presence = {},
                          Bind bind = {},DepartureBind departure_bind = {})
        :rooms_(rooms),prepare_(std::move(prepare)),sessions_(std::move(sessions)),
         peers_(std::move(peers)),world_visibility_(std::move(world_visibility)),
         world_presence_(std::move(world_presence)),
         bind_(std::move(bind)),
         departure_bind_(std::move(departure_bind)),
         lifetime_(std::make_shared<Lifetime>(Lifetime{this})){
        if(bool(world_visibility_)!=bool(world_presence_) ||
           (world_visibility_ && !world_visibility_->owns_presence(world_presence_)) ||
           (departure_bind_&&(!world_visibility_||bind_)))
            throw std::invalid_argument("PK departure requires exact common presence and visibility owners");
    }
    ~OwnedPkEntryAdmission(){
        stop_on_game();
    }
    OwnedPkEntryAdmission(const OwnedPkEntryAdmission&)=delete;
    OwnedPkEntryAdmission& operator=(const OwnedPkEntryAdmission&)=delete;
    std::optional<Invitations::Reservation> prepare(const Invitations::Pair& pair)override{
        check_thread();
        if(stopped_||preparing_||!prepare_||!sessions_||!peers_||attempts_.size()>=max_retained_rooms)return {};
        preparing_=true;struct End{bool& value;~End(){value=false;}}end{preparing_};
        const auto sessions=resolve_sessions(pair);
        if(!sessions||stopped_||!exact_peers(pair)||stopped_)return {};
        auto ticket=prepare_(pair);if(!ticket)return {};
        // A preparer must issue a fresh reservation, never abandon an already
        // retained ticket on behalf of a duplicate call.
        if(attempts_.contains(ticket->id()))return {};
        if(stopped_){rooms_.abandon(*ticket);return {};}
        bool stored=false;
        try {
            const auto& input=ticket->input();
            if(input.pair!=pair||!input.combat_sources||!input.entry.owned_players()||
               !input.entry.owned_appearances()||!input.entry.waiting_control()||
               !rooms_.current(*ticket)){
                rooms_.abandon(*ticket);return {};
            }
            if(world_presence_)for(const auto& appearance:*input.entry.owned_appearances())
                if(!appearance.owns_presence(world_presence_)){rooms_.abandon(*ticket);return {};}
            auto attempt=std::make_shared<Attempt>(lifetime_,*ticket,*sessions);
            if(!source_pair(*attempt)||stopped_||!exact_peers(pair)||stopped_){rooms_.abandon(*ticket);return {};}
            Invitations::Reservation reservation{ticket->id(),ticket->generation(),pair,input.entry};
            attempts_.emplace(ticket->id(),attempt);stored=true;
            return std::optional<Invitations::Reservation>(std::move(reservation));
        }catch(...){
            if(stored){const auto at=attempts_.find(ticket->id());if(at!=attempts_.end())cancel(*at->second,true);}
            else rooms_.abandon(*ticket);
            throw;
        }
    }
    bool current(const Invitations::Reservation& reservation)override{
        check_thread();
        const auto at=find(reservation);
        if(stopped_||!at||at->stage!=Stage::Reserved)return false;
        return exact_sessions(*at)&&exact_peers(at->ticket.input().pair)&&
            !stopped_&&source_pair(*at)&&rooms_.current(at->ticket)&&at->stage==Stage::Reserved&&!stopped_;
    }
    // Legacy bool commit remains false. Starting asynchronous work must never
    // satisfy the synchronous "both queues committed" contract.
    bool commit(const Invitations::Reservation&)override{return false;}
    bool begin_commit(const Invitations::Accepted& accepted,Completion complete)override{
        check_thread();
        const auto& reservation=accepted.reservation();
        const auto attempt=find(reservation);
        if(stopped_||!complete||!attempt||!current(reservation)||stopped_)return false;
        // All allocations/encodings and future delivery identities are staged
        // while both exact Sessions retain their captured qualified prebattle
        // phase (CharacterSelected or InWorld) and private sources current.
        attempt->completion=std::move(complete);attempt->stage=Stage::Preparing;
        try {
            for(std::size_t i=0;i<2;++i){
                const auto& input=attempt->ticket.input();
                const auto& peer=i==0?input.pair.challenger:input.pair.recipient;
                const auto& material=(*input.entry.owned_appearances())[i].material();
                Session::NativePkEntryRequest request{peer.account,peer.character,
                    material.lease.generation,peer.world_generation,peer.battle_generation,
                    material.entry_frame,material.entry_logical,material.accepted_tail,
                    material.config_flag,input.entry.records()[i]};
                attempt->holds[i]=attempt->sessions[i]->prepare_native_pk_entry(std::move(request),attempt);
            }
        }catch(...){cancel(*attempt,true);return false;}
        return true;
    }
    void abandon(const Invitations::Reservation& reservation)noexcept override{
        if(thread_!=std::this_thread::get_id())return;
        const auto attempt=find(reservation);if(!attempt)return;
        cancel(*attempt,true);
    }
    // CUSTOM-0125 terminal shutdown only, on the real game owner. Drain the
    // external InvitationService offers/completions BEFORE this call. Keep the
    // Admission object/map alive across synchronous source-callback reentry;
    // invalidate weak entry callbacks and cancel without invoking completions.
    // Active rooms/outboxes/locks remain recoverable; no world return/rebind.
    void stop(){check_thread();stop_on_game();}
private:
    enum class Stage {Reserved,Preparing,Active,Complete,FailedReserved,FailedActive};
    struct Attempt final:Session::NativePkEntryOwner {
        std::weak_ptr<Lifetime> lifetime;
        Ticket ticket;
        std::array<std::shared_ptr<Session>,2> sessions;
        std::array<std::optional<Session::NativePkEntryHold>,2> holds;
        // CUSTOM-0113 opt-in world departure; no automatic restoration on
        // failure or terminal result. Exact lifecycle cleanup retires markers.
        std::optional<cn::SharedActorVisibility::TaiwanPkDeparture> departure;
        std::array<bool,2> held{},submitted{};
        Stage stage=Stage::Reserved;
        Completion completion;
        Attempt(std::weak_ptr<Lifetime> life,Ticket value,std::array<std::shared_ptr<Session>,2> peers)
            :lifetime(std::move(life)),ticket(std::move(value)),sessions(std::move(peers)){}
        void native_pk_entry_held(Session& session,std::optional<Session::NativePkEntryHold> hold)override{
            const auto life=lifetime.lock();if(life&&life->owner)life->owner->held(*this,session,std::move(hold));
        }
        bool native_pk_entry_written(Session& session,const Session::NativePkEntryHold& hold,bool written)override{
            const auto life=lifetime.lock();
            return life&&life->owner&&life->owner->written(*this,session,hold,written);
        }
    };
    OwnedPkRoomState& rooms_;
    Prepare prepare_;Sessions sessions_;Invitations::Resolve peers_;
    std::shared_ptr<cn::SharedActorVisibility> world_visibility_;
    std::shared_ptr<SharedWorldPresence> world_presence_;
    Bind bind_;
    DepartureBind departure_bind_;
    std::shared_ptr<Lifetime> lifetime_;
    std::map<std::uint64_t,std::shared_ptr<Attempt>> attempts_;
    const std::thread::id thread_=std::this_thread::get_id();
    bool preparing_=false,stopped_=false;
    void stop_on_game()noexcept{
        stopped_=true;lifetime_->owner=nullptr;
        for(auto& [id,attempt]:attempts_)cancel(*attempt,false);
    }
    void check_thread()const{
        if(thread_!=std::this_thread::get_id())throw std::logic_error("PK admission game owner mismatch");
    }
    std::optional<std::array<std::shared_ptr<Session>,2>> resolve_sessions(const Invitations::Pair& pair)const{
        if(stopped_)return {};
        const auto first=sessions_(pair.challenger.session);if(stopped_||!first)return {};
        const auto second=sessions_(pair.recipient.session);if(stopped_||!second)return {};
        std::array<std::shared_ptr<Session>,2> result{first,second};
        if(result[0]==result[1]||
           !result[0]->same_native_pk_game_executor(*result[1]))return {};
        return result;
    }
    bool exact_peers(const Invitations::Pair& pair)const{
        return !stopped_&&peers_(pair.challenger.session)==std::optional{pair.challenger}&&!stopped_&&
               peers_(pair.recipient.session)==std::optional{pair.recipient}&&!stopped_;
    }
    bool exact_sessions(const Attempt& attempt)const{
        const auto peers=resolve_sessions(attempt.ticket.input().pair);
        return peers&&*peers==attempt.sessions;
    }
    static bool source_pair(const Attempt& attempt){
        const auto& input=attempt.ticket.input();
        if(!input.entry.owned_players()||!input.combat_sources||!input.entry.owned_appearances())return false;
        for(std::size_t i=0;i<2;++i){
            const auto& peer=i==0?input.pair.challenger:input.pair.recipient;
            const auto& appearance=(*input.entry.owned_appearances())[i];
            const auto& material=appearance.material();
            if((*input.entry.owned_players())[i].combat()!=(*input.combat_sources)[i]||
               (*input.combat_sources)[i].appearance()!=appearance||
               material.lease.session!=peer.session||material.lease.account!=peer.account||
               material.lease.character!=peer.character||material.battle_generation!=peer.battle_generation||
               material.equipment.position.area!=peer.position.area||material.equipment.position.scene!=peer.position.scene||
               attempt.sessions[i]->id()!=peer.session||!(*input.entry.owned_players())[i].current())return false;
        }
        // PK peer world_generation is intentionally never equated to the
        // private common presence lease generation: exact_peers resolves it.
        return true;
    }
    std::shared_ptr<Attempt> find(const Invitations::Reservation& reservation)const noexcept{
        const auto at=attempts_.find(reservation.id);if(at==attempts_.end())return {};
        const auto& attempt=at->second;
        const auto& ticket=attempt->ticket;
        if(reservation.generation!=ticket.generation()||reservation.pair!=ticket.input().pair||
           !reservation.entry||*reservation.entry!=ticket.input().entry)return {};
        return attempt;
    }
    static std::optional<std::size_t> viewer(const Attempt& attempt,const Session& session)noexcept{
        for(std::size_t i=0;i<2;++i)if(attempt.sessions[i].get()==&session)return i;
        return {};
    }
    void held(Attempt& attempt,Session& session,std::optional<Session::NativePkEntryHold> hold){
        check_thread();if(stopped_||attempt.stage!=Stage::Preparing)return;
        const auto index=viewer(attempt,session);
        if(!index||!hold||!attempt.holds[*index]||*hold!=*attempt.holds[*index]||
           !session.native_pk_entry_current(*hold)){cancel(attempt,true);return;}
        attempt.held[*index]=true;
        if(!attempt.held[0]||!attempt.held[1])return;
        try {
            if(!exact_sessions(attempt)||!exact_peers(attempt.ticket.input().pair)||stopped_||!source_pair(attempt)||
               !rooms_.current(attempt.ticket)||
               !attempt.sessions[0]->native_pk_entry_current(*attempt.holds[0])||
               !attempt.sessions[1]->native_pk_entry_current(*attempt.holds[1])||attempt.stage!=Stage::Preparing){
                cancel(attempt,true);return;
            }
            rooms_.activate(attempt.ticket);
            // activate preallocates its map node before SQL commit. From this
            // point failure retains active room/outboxes; it is not rollback.
            attempt.stage=Stage::Active;
            if(world_visibility_){
                const auto& appearances=*attempt.ticket.input().entry.owned_appearances();
                attempt.departure=world_visibility_->withdraw_taiwan_pk(
                    {appearances[0].material().lease,appearances[1].material().lease},
                    attempt.sessions,{*attempt.holds[0],*attempt.holds[1]});
                // Pending publication cleanup can synchronously complete an
                // owner or close a peer. Requalify exact held transports and
                // stage AFTER those callbacks. World-source Current is not
                // reused after durable activation acquired battle ownership.
                if(!attempt.departure ||
                   !world_visibility_->taiwan_pk_departure_current(*attempt.departure) ||
                   attempt.stage!=Stage::Active ||
                   !attempt.sessions[0]->native_pk_entry_current(*attempt.holds[0]) ||
                   !attempt.sessions[1]->native_pk_entry_current(*attempt.holds[1])){
                    cancel(attempt,true);return;
                }
            }
            if(!attempt.sessions[0]->commit_native_pk_entry(*attempt.holds[0])||
               !attempt.sessions[1]->commit_native_pk_entry(*attempt.holds[1])){
                cancel(attempt,true);return;
            }
            if(world_visibility_ &&
               (!attempt.departure ||
                !world_visibility_->taiwan_pk_departure_current(*attempt.departure) ||
                attempt.stage!=Stage::Active ||
                !attempt.sessions[0]->native_pk_entry_committed_current(*attempt.holds[0]) ||
                !attempt.sessions[1]->native_pk_entry_committed_current(*attempt.holds[1]))){
                cancel(attempt,true);return;
            }
            if(bind_||departure_bind_){
                if(attempt.stage!=Stage::Active ||
                   !attempt.sessions[0]->native_pk_entry_committed_current(*attempt.holds[0]) ||
                   !attempt.sessions[1]->native_pk_entry_committed_current(*attempt.holds[1]) ||
                   !(departure_bind_ ?
                       (attempt.departure&&departure_bind_(attempt.ticket,attempt.sessions,
                           {*attempt.holds[0],*attempt.holds[1]},*attempt.departure)) :
                       bind_(attempt.ticket,attempt.sessions,{*attempt.holds[0],*attempt.holds[1]})) ||
                   (world_visibility_ && (!attempt.departure ||
                    !world_visibility_->taiwan_pk_departure_current(*attempt.departure))) ||
                   attempt.stage!=Stage::Active ||
                   !attempt.sessions[0]->native_pk_entry_committed_current(*attempt.holds[0]) ||
                   !attempt.sessions[1]->native_pk_entry_committed_current(*attempt.holds[1])){
                    cancel(attempt,true);return;
                }
            }
            attempt.sessions[0]->release_native_pk_entry(*attempt.holds[0]);
            attempt.sessions[1]->release_native_pk_entry(*attempt.holds[1]);
        }catch(...){cancel(attempt,true);}
    }
    bool written(Attempt& attempt,Session& session,const Session::NativePkEntryHold& hold,bool ok){
        check_thread();if(stopped_)return false;const auto index=viewer(attempt,session);
        if(attempt.stage!=Stage::Active||!index||!attempt.holds[*index]||
           *attempt.holds[*index]!=hold||attempt.submitted[*index]||!ok){cancel(attempt,true);return false;}
        try {
            const auto& input=attempt.ticket.input();
            const auto& peer=*index==0?input.pair.challenger:input.pair.recipient;
            const auto& request=hold.request();
            if(session.closing()||session.state()!=SessionState::InBattle||session.account_id!=peer.account||
               session.character_id!=peer.character||session.battle_generation()!=peer.battle_generation+1||
               hold.session_id()!=peer.session||request.logical!=input.entry.records()[*index]||
               request.world_generation!=peer.world_generation||request.prebattle_generation!=peer.battle_generation)
                throw DatabaseError("PK exact entry completion identity mismatch");
            const auto pending=rooms_.pending(attempt.ticket.id());
            const auto match=std::count_if(pending.begin(),pending.end(),[&](const auto& row){
                return row.room==attempt.ticket.id()&&row.revision==1&&row.viewer==*index&&
                    row.session==peer.session&&row.world_generation==peer.world_generation&&
                    row.battle_generation==peer.battle_generation+1&&row.logical==request.logical;
            });
            if(match!=1)throw DatabaseError("PK exact initial outbox completion mismatch");
            // Explicit stronger CUSTOM0108 boundary: mark only after full
            // local socket write, not enqueue intention and never native ACK.
            rooms_.submitted(attempt.ticket.id(),1,static_cast<std::uint8_t>(*index));
            attempt.submitted[*index]=true;
            if(attempt.submitted[0]&&attempt.submitted[1]){
                attempt.stage=Stage::Complete;
                auto completion=std::move(attempt.completion);
                if(completion)completion(true);
            }
            return !stopped_;
        }catch(...){cancel(attempt,true);return false;}
    }
    void cancel(Attempt& attempt,bool notify)noexcept{
        if(attempt.stage==Stage::FailedReserved||attempt.stage==Stage::FailedActive)return;
        const bool active=attempt.stage==Stage::Active||attempt.stage==Stage::Complete;
        const auto id=attempt.ticket.id();
        attempt.stage=active?Stage::FailedActive:Stage::FailedReserved;
        auto completion=std::move(attempt.completion);
        for(std::size_t i=0;i<2;++i)try {
            if(active)attempt.sessions[i]->close();
            else if(attempt.holds[i])attempt.sessions[i]->abort_native_pk_entry(*attempt.holds[i]);
        }catch(...){try{attempt.sessions[i]->close();}catch(...) {}}
        if(!active)rooms_.abandon(attempt.ticket);
        if(notify&&completion)try{completion(false);}catch(...) {}
        // Cancelled RESERVED attempts have no active room to recover. Drop
        // their strong Sessions/source copies; late callbacks retain a private
        // failed token and cannot bind a replacement. Active/complete attempts
        // remain explicitly bounded and retained until terminal recovery.
        if(notify&&!active){
            const auto at=attempts_.find(id);
            if(at!=attempts_.end()&&at->second.get()==&attempt)attempts_.erase(at);
        }
    }
};
}
