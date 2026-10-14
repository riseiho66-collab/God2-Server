#pragma once
#include "handlers/OwnedTaiwanPkLuaBasicOwner.h"
#include <chrono>

namespace god2 {
// CUSTOM-0124 concrete later-game-turn retry/cancellation owner. Owns the
// exact Lua/Publication composition and genuine bound Ticket/Session/holds.
// The supplied executor must be the actual single-thread game executor of
// BOTH bound Sessions, proved at bind. All operations and destruction stay
// there. Drain/destroy Admission first; Lua/rooms/repository/executor outlive
// this owner. No Application install, ReturnScene material or recovery is supplied.
class OwnedTaiwanPkBasicDriver final {
    struct Lifetime {OwnedTaiwanPkBasicDriver* owner;};
    struct LifecycleOwner final : OwnedPkOutboxPublication::ReturnLifecycleOwner {
        explicit LifecycleOwner(std::weak_ptr<Lifetime> value):life(std::move(value)){}
        std::weak_ptr<Lifetime> life;
        bool native_pk_return_lifecycle(const OwnedPkOutboxPublication::ReturnLifecycle& value)override{
            const auto current=life.lock();
            return current&&current->owner&&current->owner->return_lifecycle(value);
        }
    };
    using Ticket=OwnedTaiwanPkLuaBasicOwner::Ticket;
    struct Pair {
        Ticket ticket;
        std::array<std::shared_ptr<Session>,2> sessions;
        std::array<Session::NativePkEntryHold,2> holds;
        bool dirty=true,retired=false,returning=false,adopted=false;
        std::optional<OwnedPkOutboxPublication::ReturnLifecycle> lifecycle;
    };
    using Pairs=std::map<std::uint64_t,std::shared_ptr<Pair>>;
    using Index=std::map<std::uint64_t,std::uint64_t>;
public:
    using ReturnLifecycleOwner=OwnedPkOutboxPublication::ReturnLifecycleOwner;
    using Parameters=OwnedTaiwanPkLuaBasicOwner::Parameters;
    using NativeBatch=OwnedTaiwanPkLuaBasicOwner::NativeBatch;
    using ReturnSceneSource=OwnedPkOutboxPublication::ReturnSceneSource; // CUSTOM-0133
    using WorldDeparture=OwnedTaiwanPkLuaBasicOwner::WorldDeparture;
    OwnedTaiwanPkBasicDriver(asio::any_io_executor game,OwnedPkRoomState& rooms,LuaEngine& lua,
            Parameters parameters,std::array<std::uint8_t,2> order,std::chrono::milliseconds retry,
            ReturnSceneSource return_scene={},std::weak_ptr<ReturnLifecycleOwner> sibling_lifecycle={})
        :game_(std::move(game)),retry_(checked(retry)),timer_(game_),
         lifetime_(std::make_shared<Lifetime>(Lifetime{this})),
         lifecycle_owner_(std::make_shared<LifecycleOwner>(lifetime_)),
         sibling_lifecycle_(std::move(sibling_lifecycle)),
         sibling_required_(sibling_lifecycle_.owner_before(std::weak_ptr<ReturnLifecycleOwner>{})||
             std::weak_ptr<ReturnLifecycleOwner>{}.owner_before(sibling_lifecycle_)),
         owner_(rooms,lua,parameters,order,std::move(return_scene),lifecycle_owner_){}
    ~OwnedTaiwanPkBasicDriver(){lifetime_->owner=nullptr;stop_on_game();}
    OwnedTaiwanPkBasicDriver(const OwnedTaiwanPkBasicDriver&)=delete;
    OwnedTaiwanPkBasicDriver& operator=(const OwnedTaiwanPkBasicDriver&)=delete;

    bool bind(const Ticket& ticket,const std::array<std::shared_ptr<Session>,2>& sessions,
            const std::array<Session::NativePkEntryHold,2>& holds,
            std::optional<WorldDeparture> departure={}){
        check_action();
        if(pairs_.size()>=256 || pairs_.contains(ticket.id()) || !sessions[0] || !sessions[1] ||
           sessions[0]==sessions[1] || by_session_.contains(sessions[0]->id()) ||
           by_session_.contains(sessions[1]->id()) ||
           !sessions[0]->native_pk_game_executor_matches(game_) ||
           !sessions[1]->native_pk_game_executor_matches(game_))return false;
        // All map allocation BEFORE the Publication atomically publishes its
        // binding. Both owners retain the same genuine private capabilities.
        Pairs staged;staged.emplace(ticket.id(),std::make_shared<Pair>(Pair{ticket,sessions,holds}));
        Index staged_index;
        for(const auto& session:sessions)staged_index.emplace(session->id(),ticket.id());
        if(staged_index.size()!=2 || !owner_.bind(ticket,sessions,holds,std::move(departure)))return false;
        pairs_.insert(staged.extract(ticket.id()));
        while(!staged_index.empty())by_session_.insert(staged_index.extract(staged_index.begin()));
        try{arm();}catch(...){stop_on_game();throw;}
        return true; // Still no inline resolution/send or entry release.
    }

    std::optional<NativeBatch> dispatch_native_basic(Session& session,
            std::span<const RecoveredWorldRecords::Record> records){
        check_action();
        const auto indexed=by_session_.find(session.id());if(indexed==by_session_.end())return {};
        const auto pair=pairs_.at(indexed->second);
        try{
            require_session(*pair,session);
            const auto accepted=owner_.dispatch_native_basic(session,records);
            if(!accepted)throw DatabaseError("PK driver lost its privately bound input owner");
            if(!pair->retired&&!pair->returning&&!pair->adopted)pair->dirty=true;
            arm(); // The timer is the only resolution visit.
            return accepted;
        }catch(...){retire(*pair);throw;}
    }

    void disconnected(Session& session){
        check_thread();
        const auto indexed=by_session_.find(session.id());if(indexed==by_session_.end())return;
        const auto pair=pairs_.at(indexed->second);
        if(pair->sessions[0].get()!=&session && pair->sessions[1].get()!=&session)
            throw DatabaseError("PK disconnect requires the exact retained Session instance");
        if(visiting_){stop_on_game();return;}
        retire(*pair); // Idempotent also after stop/peer failure.
    }
    void stop(){check_thread();stop_on_game();}
private:
    const asio::any_io_executor game_;
    const std::chrono::milliseconds retry_;
    asio::steady_timer timer_;
    const std::thread::id thread_=std::this_thread::get_id();
    std::shared_ptr<Lifetime> lifetime_;
    std::shared_ptr<LifecycleOwner> lifecycle_owner_;
    std::weak_ptr<ReturnLifecycleOwner> sibling_lifecycle_;
    const bool sibling_required_;
    OwnedTaiwanPkLuaBasicOwner owner_;
    Pairs pairs_;
    Index by_session_;
    bool armed_=false,visiting_=false,stopped_=false,lifecycle_busy_=false;

    bool return_lifecycle(const OwnedPkOutboxPublication::ReturnLifecycle& value)noexcept{
        if(thread_!=std::this_thread::get_id())return false;
        if(lifecycle_busy_){stop_on_game();return false;}
        if(stopped_||!owner_.return_lifecycle_current(value))return false;
        const auto at=pairs_.find(value.ticket().id());
        if(at==pairs_.end())return false;
        const auto pair=at->second; // Own it across the sibling and exact erase.
        const auto exact=[&]()noexcept{
            const auto current=pairs_.find(pair->ticket.id());
            if(stopped_||pair->retired||pair->adopted||current==pairs_.end()||current->second!=pair||
               !pair->ticket.same_incarnation(value.ticket())||pair->holds!=value.holds())return false;
            for(std::size_t i=0;i<2;++i){
                const auto indexed=by_session_.find(pair->sessions[i]->id());
                if(value.session(i)!=pair->sessions[i]||indexed==by_session_.end()||
                   indexed->second!=pair->ticket.id())return false;
            }
            return true;
        };
        if(!exact())return false;
        using Phase=OwnedPkOutboxPublication::ReturnLifecyclePhase;
        const auto phase=value.phase();
        if(phase!=Phase::Returning&&phase!=Phase::Adopted)return false;
        if(phase==Phase::Adopted&&(!pair->returning||!pair->lifecycle||*pair->lifecycle!=value))return false;
        if(phase==Phase::Returning&&pair->lifecycle&&*pair->lifecycle!=value)return false;
        lifecycle_busy_=true;
        struct End {bool& busy;~End(){busy=false;}}end{lifecycle_busy_};
        try{
            if(phase==Phase::Returning){
                pair->lifecycle.emplace(value);pair->returning=true;pair->dirty=false;
            }
            // Sibling is a pure exact Admission join/retirement, not a new grant.
            const auto sibling=sibling_lifecycle_.lock();
            if(sibling_required_&&!sibling){retire(*pair);return false;}
            if(sibling&&!sibling->native_pk_return_lifecycle(value)){retire(*pair);return false;}
            if(value.phase()!=phase||!owner_.return_lifecycle_current(value)||!exact()){retire(*pair);return false;}
            if(phase==Phase::Returning)return true;
            // No observer/allocation follows the adopted flag. Outstanding
            // local shared Pair references cannot close the returned Sessions.
            pair->adopted=true;pair->dirty=false;
            for(const auto& session:pair->sessions){
                const auto indexed=by_session_.find(session->id());
                if(indexed!=by_session_.end()&&indexed->second==pair->ticket.id())by_session_.erase(indexed);
            }
            pairs_.erase(pair->ticket.id());
            return true;
        }catch(...){retire(*pair);return false;}
    }

    static std::chrono::milliseconds checked(std::chrono::milliseconds value){
        if(value.count()<1 || value>std::chrono::seconds(1))
            throw std::invalid_argument("PK driver requires explicit retry cadence1..1000ms");
        return value; // CUSTOM transport policy, not native battle/count clock.
    }
    void check_thread()const{
        if(thread_!=std::this_thread::get_id())throw std::logic_error("PK driver game executor mismatch");
    }
    void check_action(){
        check_thread();
        if(visiting_){
            // Close immediately so the Publication's pure Rule before/after
            // fences also observe a caught reentry before any shared settle.
            stop_on_game();throw DatabaseError("PK scheduled resolver reentered its driver");
        }
        if(stopped_)throw DatabaseError("PK driver stopped; durable recovery required");
    }
    static void require_session(const Pair& pair,const Session& session){
        if(pair.retired || pair.returning || pair.adopted ||
           (pair.sessions[0].get()!=&session && pair.sessions[1].get()!=&session))
            throw DatabaseError("PK driver requires the exact retained Session instance");
    }
    static void retire(Pair& pair)noexcept{
        if(pair.adopted)return;
        pair.retired=true;pair.dirty=false;
        for(const auto& session:pair.sessions)try{session->close();}catch(...){}
        // Keep Ticket/holds/room/checkpoint/outboxes/locks; no abandon/resend,
        // implicit wallet/save settlement, fresh WORLD return or DB deletion.
    }
    void stop_on_game()noexcept{
        stopped_=true;armed_=false;
        try{timer_.cancel();}catch(...){}
        for(auto& [room,pair]:pairs_)retire(*pair);
    }
    void arm(){
        if(stopped_ || armed_ || !std::any_of(pairs_.begin(),pairs_.end(),
            [](const auto& value){return value.second->dirty&&!value.second->retired&&
                !value.second->returning&&!value.second->adopted;}))return;
        try{
            timer_.expires_after(retry_);armed_=true;
            timer_.async_wait([weak=std::weak_ptr<Lifetime>(lifetime_)](const asio::error_code& error){
                const auto life=weak.lock();
                if(life&&life->owner)life->owner->visit(error);
            });
        }catch(...){armed_=false;stop_on_game();throw;}
    }
    void visit(const asio::error_code& error)noexcept{
        try{
            check_thread();armed_=false;
            if(stopped_)return;
            if(error){stop_on_game();return;}
            visiting_=true;
            struct End {bool& flag;~End(){flag=false;}}end{visiting_};
            auto cursor=pairs_.begin();
            while(cursor!=pairs_.end()){
                const auto room=cursor->first;const auto pair=cursor->second;
                // No iterator/reference survives an owner callback. Adoption
                // can erase this exact node while the local shared Pair lives.
                if(stopped_)break;
                if(!pair->retired&&!pair->returning&&!pair->adopted&&pair->dirty){
                    try{
                        for(std::size_t i=0;i<2;++i)
                            if(!pair->sessions[i]->native_pk_entry_binding_current(pair->holds[i]))
                                throw DatabaseError("PK driver retained a revoked entry binding");
                        const auto advanced=owner_.advance_from_scheduled_turn(*pair->sessions[0]);
                        if(!advanced)throw DatabaseError("PK driver lost its private output owner");
                        if(!pair->retired&&!pair->returning&&!pair->adopted)
                            pair->dirty=*advanced!=OwnedTaiwanPkLuaBasicOwner::Advance::Idle;
                    }catch(...){retire(*pair);}
                }
                cursor=pairs_.upper_bound(room);
            }
            arm();
        }catch(...){stop_on_game();}
        // A scheduled visit is not a strand-idle/readiness attestation. Real
        // Session staging waits ACK enqueue and checks prefixes again before
        // write. Later rejection retains an already durable result for recovery.
    }
};
}
