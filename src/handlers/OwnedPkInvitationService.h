#pragma once
#include "protocol/RecoveredPk69.h"
#include "protocol/RecoveredPkEntryProjection.h"
#include "protocol/RecoveredWorldRecords.h"
#include "game/RecoveredPosition.h"
#include "game/TaiwanWorldEntryIdentity.h"
#include <chrono>
#include <functional>
#include <limits>
#include <map>
#include <memory>
#include <thread>
#include <utility>
namespace god2 {
// CUSTOM-0086 serial-executor invitation state and room admission boundary.
// This service NEVER binds two independent diagnostic battles as a PK room.
// Transient offers are session-scoped; no account/save/HP/skill writer here.
class OwnedPkInvitationService {
public:
    using Clock=std::chrono::steady_clock;
    // Source identity receipt, never a caller-selected actor scalar. Private
    // INIT incarnation and the complete ready common lease qualify this map;
    // saved character ownership remains full64 throughout the room lifecycle.
    class NativeIdentity {
    public:
        static std::optional<NativeIdentity> observe(const std::shared_ptr<Session>& session,
                Session::NormalWorldInitialization initialization,
                const std::shared_ptr<SharedWorldPresence>& presence,const SharedWorldPresence::Lease& supplied_lease){
            const auto lease=supplied_lease;
            if(!session||!presence||!session->normal_world_initialization_current_on_game(initialization)||
               !initialization.entry_written()||!initialization.qualified_scene_identity())return {};
            const auto phase=session->state();const auto battle=session->battle_generation();
            const auto entry=RecoveredWorldEntryView::read(initialization.entry_frame());
            if(session->closing()||(phase!=SessionState::CharacterSelected&&phase!=SessionState::InWorld)||
               session->id()!=lease.session||session->account_id!=lease.account||session->character_id!=lease.character||
               !lease.session||!lease.account||!lease.character||!lease.generation||
               !qualified_taiwan_scene_handle(lease.actor_handle)||!entry||initialization.config_flag()>1||
               entry->actor_handle!=lease.actor_handle||entry->area!=lease.position.area||entry->scene!=lease.position.scene||
               entry->x!=lease.position.x||entry->y!=lease.position.y||
               initialization.entry_logical()!=std::vector<std::uint8_t>(entry->logical.begin(),entry->logical.end()))return {};
            NativeIdentity result(session,std::move(initialization),presence,lease,battle,phase);
            if(!result.current())return {};return result;
        }
        std::uint16_t actor_handle()const noexcept{return lease_.actor_handle;}
        bool owns_presence(const std::shared_ptr<SharedWorldPresence>& value)const noexcept{
            return !presence_.owner_before(value)&&!value.owner_before(presence_);
        }
        bool matches_initialization(const Session::NormalWorldInitialization& value)const noexcept{
            return initialization_.same_initialization(value);
        }
        bool matches_peer(std::uint64_t session,std::uint64_t account,std::uint64_t character,
                std::uint64_t battle)const noexcept{
            return lease_.session==session&&lease_.account==account&&lease_.character==character&&battle_==battle;
        }
        bool retained_matches(const SharedWorldPresence::Lease& lease,const RecoveredWorldEntry::Frame& frame,
                const std::vector<std::uint8_t>& logical,const std::vector<std::uint8_t>& tail,
                std::uint8_t flag,std::uint64_t battle)const noexcept{
            return lease_==lease&&battle_==battle&&initialization_.entry_frame()==frame&&
                initialization_.entry_logical()==logical&&initialization_.accepted_tail()==tail&&
                initialization_.config_flag()==flag;
        }
        bool retained_matches_appearance(const OwnedTaiwanPkAppearanceSource::Observation& source)const noexcept{
            const auto presence=presence_.lock();const auto& m=source.material();
            return presence&&source.owns_presence(presence)&&source.owns_initialization(initialization_)&&
                retained_matches(m.lease,m.entry_frame,m.entry_logical,m.accepted_tail,m.config_flag,m.battle_generation);
        }
        bool current()const{
            // Only the original game owner may consult live Session/registry.
            if(thread_!=std::this_thread::get_id())return false;
            const auto session=session_.lock();const auto presence=presence_.lock();
            if(!session||!presence||!session->normal_world_initialization_current_on_game(initialization_)||
               !initialization_.entry_written()||session->closing()||session->state()!=phase_||
               !matches_peer(session->id(),session->account_id,session->character_id,session->battle_generation()))return false;
            return presence->ready_lease(lease_.session,lease_.account,lease_.character)==std::optional{lease_}&&
                session->normal_world_initialization_current_on_game(initialization_)&&!session->closing()&&
                session->state()==phase_&&matches_peer(session->id(),session->account_id,session->character_id,
                    session->battle_generation())&&presence->retained_ready_current(lease_);
        }
        bool operator==(const NativeIdentity& other)const noexcept{
            return lease_==other.lease_&&battle_==other.battle_&&phase_==other.phase_&&thread_==other.thread_&&
                initialization_.same_initialization(other.initialization_)&&
                !session_.owner_before(other.session_)&&!other.session_.owner_before(session_)&&
                !presence_.owner_before(other.presence_)&&!other.presence_.owner_before(presence_);
        }
    private:
        NativeIdentity(std::weak_ptr<Session> session,Session::NormalWorldInitialization initialization,
                std::weak_ptr<SharedWorldPresence> presence,SharedWorldPresence::Lease lease,
                std::uint64_t battle,SessionState phase)
            :session_(std::move(session)),initialization_(std::move(initialization)),presence_(std::move(presence)),
             lease_(std::move(lease)),battle_(battle),phase_(phase){}
        std::weak_ptr<Session> session_;
        Session::NormalWorldInitialization initialization_;
        std::weak_ptr<SharedWorldPresence> presence_;
        SharedWorldPresence::Lease lease_;
        std::uint64_t battle_;
        SessionState phase_;
        std::thread::id thread_=std::this_thread::get_id();
    };
    struct Peer {
        std::uint64_t session{},account{},character{},world_generation{},battle_generation{};
        RecoveredPosition position;
        bool ready{},blocked{};
        std::optional<NativeIdentity> native_identity{};
        std::optional<std::uint32_t> native_actor()const noexcept{
            if(native_identity){
                if(!native_identity->matches_peer(session,account,character,battle_generation))return {};
                return native_identity->actor_handle();
            }
            if(!character||character>UINT32_MAX)return {};
            return static_cast<std::uint32_t>(character); // Historical selected-character profile only.
        }
        bool operator==(const Peer&)const=default;
    };
    struct Pair {Peer challenger,recipient;bool operator==(const Pair&)const=default;};
    struct Reservation {
        std::uint64_t id{},generation{};
        Pair pair;
        std::optional<RecoveredPkEntryProjection::Prepared> entry;
        bool operator==(const Reservation&)const=default;
    };
    // Minted only after the exact pending native69 Accept and current rule /
    // pair / reservation checks. An async adapter cannot invent this token.
    class Accepted {
    public:
        const Reservation& reservation()const noexcept{return reservation_;}
    private:
        friend class OwnedPkInvitationService;
        explicit Accepted(Reservation reservation):reservation_(std::move(reservation)){}
        Reservation reservation_;
    };
    // Future shared room implementation must own profiles, actor/skill source,
    // both saved readsets, relative-side entry projections and atomic commit.
    // prepare/current never send or mutate saves/session states. prepare must
    // issue a never-reused (id,generation), including across process restarts.
    // Those opaque ASCII contexts return through native84620/970A0; no native
    // timestamp/nonce meaning is claimed. commit must
    // either create ONE common authoritative room and queue both native entry
    // streams, or fail without mutation. noexcept abandon releases reservations.
    // Merely reserving an ID is not a successful commit.
    class RoomAuthority {
    public:
        virtual ~RoomAuthority()=default;
        virtual std::optional<Reservation> prepare(const Pair&)=0;
        virtual bool current(const Reservation&)=0;
        virtual bool commit(const Reservation&)=0;
        virtual void abandon(const Reservation&)noexcept=0;
    };
    class AsyncRoomAuthority:public RoomAuthority {
    public:
        // Explicit opt-in. True means preparation STARTED, never committed or
        // delivered. Completion runs once on the same game executor. Failure
        // before activation abandons RESERVED; after activation closes peers
        // and retains durable room/outboxes/owner locks for recovery.
        using Completion=std::function<void(bool)>;
        virtual bool begin_commit(const Accepted&,Completion)=0;
    };
    using Resolve=std::function<std::optional<Peer>(std::uint64_t)>;
    using Target=std::function<std::optional<Peer>(std::uint32_t)>;
    using Rule=std::function<bool(const Pair&)>;
    // True means transport submission was requested, not enqueue acceptance
    // or a native-client ACK. The exact69 answer independently proves context.
    using Publish=std::function<bool(const Peer&,const RecoveredPk69::Bytes&)>;
    using Authority=std::function<RoomAuthority*()>;
    enum class Outcome {Denied,RoomUnavailable,Invited,Rejected,Busy,Accepted,AdmissionPending};
    OwnedPkInvitationService(Resolve resolve,Target target,Rule rule,Publish publish,Authority rooms)
        :resolve_(std::move(resolve)),target_(std::move(target)),rule_(std::move(rule)),
         publish_(std::move(publish)),rooms_(std::move(rooms)),lifetime_(std::make_shared<Lifetime>(Lifetime{this})){}
    ~OwnedPkInvitationService(){stop();}
    // Terminal game-owner drain before the borrowed RoomAuthority stops.
    // Reentrant abandon/completion cannot publish a new offer or re-drain it.
    void stop()noexcept{
        if(stopped_)return;
        stopped_=true;lifetime_->owner=nullptr;
        while(!offers_.empty())retire(offers_.begin());
    }
    OwnedPkInvitationService(const OwnedPkInvitationService&)=delete;
    OwnedPkInvitationService& operator=(const OwnedPkInvitationService&)=delete;
    static bool handles(std::span<const RecoveredWorldRecords::Record> records){
        return std::any_of(records.begin(),records.end(),[](const auto&r){return std::holds_alternative<RecoveredPk69::Request>(r);});
    }
    static std::optional<RecoveredPk69::Request> request(std::span<const RecoveredWorldRecords::Record> records){
        std::optional<RecoveredPk69::Request> result;
        for(const auto&r:records){
            if(const auto* pk=std::get_if<RecoveredPk69::Request>(&r)){if(result)return {};result=*pk;}
            else if(!std::holds_alternative<RecoveredWorldRecords::Tick>(r))return {};
        }
        return result;
    }
    Outcome handle(std::uint64_t sender,const RecoveredPk69::Request&r,Clock::time_point now){
        if(stopped_)return Outcome::Denied;
        expire(now);
        if(stopped_)return Outcome::Denied;
        if(r.control!=RecoveredPk69::Control::Invite)return answer(sender,r,now);
        if(!RecoveredPk69::right_click(r)||!resolve_||!target_||!rule_||!publish_||!rooms_)return Outcome::Denied;
        const auto source=resolve_(sender),destination=target_(r.second);
        if(!source||!destination||source->native_actor()!=std::optional{r.first}||
           destination->native_actor()!=std::optional{r.second})return Outcome::Denied;
        Pair pair{*source,*destination};
        if(!eligible(pair)||occupied(source->session)||occupied(destination->session)||!rule_(pair))return Outcome::Denied;
        auto* authority=rooms_();if(!authority)return Outcome::RoomUnavailable;
        auto reservation=authority->prepare(pair);
        if(!reservation)return Outcome::RoomUnavailable;
        if(!reservation->id||!reservation->generation||reservation->pair!=pair||!reservation->entry||
           reservation->entry->characters()!=std::array<std::uint64_t,2>{pair.challenger.character,pair.recipient.character}||
           !current(pair)||!authority->current(*reservation)){
            authority->abandon(*reservation);return Outcome::Denied;
        }
        // Install before publication so an immediate native Busy reply has a
        // context. No reentrant callbacks are allowed on this game executor.
        auto invitation=r;
        invitation.first_text=opaque_context(reservation->id);
        invitation.second_text=opaque_context(reservation->generation);
        Pending pending{pair,invitation,*reservation,authority,now+std::chrono::seconds(60)};
        try {
            const auto [it,inserted]=offers_.emplace(destination->session,pending);
            if(!inserted){authority->abandon(*reservation);return Outcome::Denied;}
            if(!publish_(*destination,RecoveredPk69::invitation(invitation))){retire(it);return Outcome::Denied;}
        } catch(...) {
            const auto it=offers_.find(destination->session);
            if(it!=offers_.end()&&it->second.reservation==*reservation)retire(it);
            else authority->abandon(*reservation);
            throw;
        }
        return Outcome::Invited;
    }
    // Invoke on logout, fresh WORLD admission or movement/scene transition.
    // No fabricated close/timeout ACK: this native UI closes locally.
    void invalidate(std::uint64_t session)noexcept{
        if(stopped_)return;
        for(auto it=offers_.begin();it!=offers_.end();){
            if(it->second.pair.challenger.session==session||it->second.pair.recipient.session==session){
                auto old=it++;retire(old);
                if(stopped_)return; // abandon may have terminally drained the remaining map.
            }
            else ++it;
        }
    }
    void expire(Clock::time_point now){
        if(stopped_)return;
        for(auto it=offers_.begin();it!=offers_.end();){
            bool valid=false;
            try {
                valid=now<it->second.deadline&&rooms_&&rooms_()==it->second.authority;
                // Once handed off, the adapter owns the InWorld -> InBattle
                // transition. Demanding the old WORLD receipt here would
                // cancel a correctly activated but not-yet-written entry.
                if(valid&&!it->second.admission)
                    valid=current(it->second.pair)&&it->second.authority->current(it->second.reservation);
            }
            catch(...){valid=false;}
            if(stopped_)return;
            if(!valid){auto old=it++;retire(old);if(stopped_)return;}else ++it;
        }
    }
private:
    struct Admission {bool retired=false,completed=false;};
    struct Lifetime {OwnedPkInvitationService* owner;};
    struct Pending {Pair pair;RecoveredPk69::Request invitation;Reservation reservation;RoomAuthority* authority;Clock::time_point deadline;std::shared_ptr<Admission> admission{};};
    using Offers=std::map<std::uint64_t,Pending>;
    Resolve resolve_;Target target_;Rule rule_;Publish publish_;Authority rooms_;
    Offers offers_;
    std::shared_ptr<Lifetime> lifetime_;
    bool stopped_=false; // LAST member; absence of stop preserves normal operation.
    static RecoveredPk69::Text opaque_context(std::uint64_t n){
        // UINT64 base36 fits13 chars plus NUL in native16. These are custom
        // replay identities, never guessed player names or stat values.
        constexpr char digits[]="0123456789abcdefghijklmnopqrstuvwxyz";
        RecoveredPk69::Text text{};std::size_t count=0;
        do{text[count++]=static_cast<std::uint8_t>(digits[n%36]);n/=36;}while(n);
        std::reverse(text.begin(),text.begin()+count);return text;
    }
    static bool eligible(const Pair&p){
        const auto&a=p.challenger;const auto&b=p.recipient;
        return a.session&&b.session&&a.session!=b.session&&a.account&&b.account&&
            a.character&&b.character&&a.character!=b.character&&a.native_actor()&&b.native_actor()&&
            a.native_actor()!=b.native_actor()&&
            a.world_generation&&b.world_generation&&a.ready&&b.ready&&!a.blocked&&!b.blocked&&
            a.position.area==b.position.area&&a.position.scene==b.position.scene;
    }
    bool current(const Pair&p)const {
        if(!eligible(p)||!resolve_)return false;
        return resolve_(p.challenger.session)==std::optional{p.challenger}&&resolve_(p.recipient.session)==std::optional{p.recipient};
    }
    bool occupied(std::uint64_t session)const{
        for(const auto&[id,p]:offers_)if(p.pair.challenger.session==session||p.pair.recipient.session==session)return true;
        return false;
    }
    void retire(Offers::iterator it)noexcept {
        if(it->second.admission)it->second.admission->retired=true;
        // Remove before invoking the adapter: a synchronous cancellation
        // completion must not erase a new offer or invalidate this iterator.
        auto pending=std::move(it->second);offers_.erase(it);
        pending.authority->abandon(pending.reservation);
    }
    Outcome answer(std::uint64_t sender,const RecoveredPk69::Request&r,Clock::time_point now){
        const auto it=offers_.find(sender);if(it==offers_.end())return Outcome::Denied;
        const auto& pending=it->second;
        if(pending.admission)return Outcome::Denied;
        if(now>=pending.deadline||r!=RecoveredPk69::expected_reply(pending.invitation,r.control)||
           !current(pending.pair)||!rooms_||rooms_()!=pending.authority||!pending.authority->current(pending.reservation))return Outcome::Denied;
        if(r.control==RecoveredPk69::Control::Reject){retire(it);return Outcome::Rejected;}
        if(r.control==RecoveredPk69::Control::Busy){retire(it);return Outcome::Busy;}
        if(r.control!=RecoveredPk69::Control::Accept||!rule_||!rule_(pending.pair)||!current(pending.pair))return Outcome::Denied;
        if(auto* async=dynamic_cast<AsyncRoomAuthority*>(pending.authority)){
            // Allocate/copy before handing over. Holds are never requested
            // during Invite/prepare, so the recipient can still send Accept.
            const Accepted accepted(pending.reservation);
            const auto attempt=std::make_shared<Admission>();
            it->second.admission=attempt;
            // Transport admission deadline, not a recovered native turn time.
            it->second.deadline=now+std::chrono::seconds(15);
            const auto thread=std::this_thread::get_id();
            const auto finish=[weak=std::weak_ptr<Lifetime>(lifetime_),
                               token=std::weak_ptr<Admission>(attempt),sender,thread](bool ok){
                if(std::this_thread::get_id()!=thread)return;
                const auto life=weak.lock();const auto admission=token.lock();
                if(!life||!life->owner||!admission||admission->retired||admission->completed)return;
                auto& service=*life->owner;
                const auto at=service.offers_.find(sender);
                if(at==service.offers_.end()||at->second.admission!=admission)return;
                admission->completed=true;
                if(ok)service.offers_.erase(at);else service.retire(at);
            };
            bool started=false;
            try {started=async->begin_commit(accepted,finish);}
            catch(...){finish(false);throw;}
            if(!started){finish(false);return Outcome::RoomUnavailable;}
            return Outcome::AdmissionPending;
        }
        // The authority must consume the exact reservation transactionally;
        // never set InBattle or emit82 here before that common commit succeeds.
        if(!pending.authority->commit(pending.reservation)){retire(it);return Outcome::RoomUnavailable;}
        offers_.erase(it);return Outcome::Accepted;
    }
};
}
