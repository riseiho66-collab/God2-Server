#pragma once
#include "db/SqliteOwnedPkRoomRepository.h"
#include "handlers/RecoveredPkCommandSelection.h"
#include "protocol/RecoveredPkActionProjection.h"
#include <map>
#include <type_traits>
namespace god2 {
// CUSTOM-0086 concrete single-game-executor shared PK state. Each room owns
// exactly ONE Battle; two Sessions must never create two mutable copies.
// Still an INCOMPLETE backend: a RoomAuthority adapter must own live profile
// refresh, two Session bindings, turn/skill policy, outbox transport receipts,
// terminal WORLD re-entry and reconnect before Application can install it.
class OwnedPkRoomState {
public:
    using Repository=SqliteOwnedPkRoomRepository;
    using Ticket=Repository::Ticket;
    using Replies=Repository::Replies;
    // Pure two-viewer encoding only, not sends, storage or client authority.
    using Project=std::function<Replies(const BattleSnapshot&,const BattleActionResult&)>;
    explicit OwnedPkRoomState(Repository& repository):repository_(repository){}
    OwnedPkRoomState(const OwnedPkRoomState&)=delete;
    OwnedPkRoomState& operator=(const OwnedPkRoomState&)=delete;
    Ticket prepare(Repository::Input input){return repository_.prepare(std::move(input));}
    bool current(const Ticket& ticket){return repository_.current(ticket);}
    void abandon(const Ticket& ticket)noexcept{repository_.abandon(ticket);}
    // Only server-side activation. Both entries become DURABLE outbox rows;
    // this does not change Session states or claim their queues accepted them.
    void activate(const Ticket& ticket){
        if(rooms_.contains(ticket.id()))throw DatabaseError("PK room already active in this executor");
        // CUSTOM-0114 same issuer claim also covers retained recovery. A
        // different RoomState cannot own another mutable Battle concurrently.
        auto claim=repository_.claim_runtime(ticket);
        auto battle=Battle::restore(repository_.initial(ticket));
        // Allocate the future map node BEFORE the durable transaction. A DB
        // exception leaves no published in-memory room; after COMMIT map node
        // transfer and Battle moves do not allocate or call user callbacks.
        Rooms staged;
        staged.emplace(ticket.id(),Room{ticket,std::move(battle),std::move(claim)});
        auto node=staged.extract(ticket.id());
        repository_.activate(ticket);
        rooms_.insert(std::move(node));
    }
    // CUSTOM-0114 restore the latest durable active/retained-finished room
    // only while its genuine Ticket and original repository issuer survive.
    // No seed restart, Session binding, sends, grant reset, saved settlement,
    // lock release or private source rehydration across process restart.
    void restore_retained(const Ticket& ticket){
        if(rooms_.contains(ticket.id()))throw DatabaseError("PK room already active in this executor");
        auto claim=repository_.claim_runtime(ticket);
        const auto retained=repository_.recover_retained(ticket);
        auto battle=Battle::restore(retained.checkpoint());
        Rooms staged;
        staged.emplace(ticket.id(),Room{retained.ticket(),std::move(battle),std::move(claim)});
        auto node=staged.extract(ticket.id());
        // All fallible allocation/restoration precedes the final full durable
        // fence. Publishing the preallocated node neither sends nor writes DB.
        if(!repository_.retained_recovery_current(retained))
            throw DatabaseError("PK retained recovery changed before executor binding");
        rooms_.insert(std::move(node));
    }
    std::optional<BattleSnapshot> inspect(std::uint64_t room)const{
        const auto at=rooms_.find(room);if(at==rooms_.end())return {};
        return at->second.battle.inspect();
    }
    // Policies are supplied by the authoritative adapter. This method does
    // not accept native35/context/selection bytes as a BattleAction directly.
    // Resource deltas are battle-local; saved character rows stay unchanged.
    // Legacy trusted primitive is refused by the repository for collection
    // rooms; it cannot bypass persisted input/grant phases. Use submit_native
    // until the atomic two-intent resolver has been implemented.
    void act(std::uint64_t room,std::uint64_t controller,std::uint64_t revision,
             const BattleAction& action,const Battle::Rule& rule,const Project& project,
             const std::optional<NativeSkillRecord>& definition={}){
        auto at=rooms_.find(room);if(at==rooms_.end()||!project)throw DatabaseError("PK active room unavailable");
        auto& current=at->second;
        if(controller!=current.ticket.input().pair.challenger.character&&
           controller!=current.ticket.input().pair.recipient.character)
            throw DatabaseError("PK controller is not either owned participant");
        const auto before=current.battle.checkpoint();
        auto staged=current.battle;
        Replies replies;
        (void)staged.act(controller,revision,action,rule,[&](const auto& state,const auto& result){
            replies=project(state,result);return replies[0];
        });
        const auto after=staged.checkpoint();
        repository_.advance(current.ticket,before,after,replies,definition);
        static_assert(std::is_nothrow_move_assignable_v<Battle>);
        current.battle=std::move(staged);
    }
    struct NativeCaller {
        std::uint64_t session,account,character,world_generation,battle_generation;
        bool in_battle;
    };
    // Stage one owned native command without damage or result presentation.
    // The permit values are server-owned, NEVER decoded from native bytes.
    // One player's input cannot mutate shared HP/MP before BOTH inputs exist.
    // Still not wired to Application; no completed35/gameplay claim.
    void submit_native(std::uint64_t room,const NativeCaller& caller,
                       std::uint64_t server_battle_revision,std::uint64_t server_grant_epoch,
                       const std::string& current_profile_readset_sha256,
                       const RecoveredPkCommandSelection::Policy& policy,
                       std::span<const RecoveredWorldRecords::Record> records){
        auto& current=find(room);const auto viewer=owned_viewer(current,caller,current_profile_readset_sha256);
        const auto phase=repository_.round(current.ticket);
        if(server_battle_revision!=current.battle.inspect().revision||phase.battle_revision()!=server_battle_revision||
           phase.grant_epoch()!=server_grant_epoch||policy.client_actor!=0||policy.client_side!=0||
           policy.context!=current.ticket.input().entry.command_contexts()[viewer])
            throw DatabaseError("PK native command has no matching server-owned grant/profile header");
        const auto selection=RecoveredPkCommandSelection::select(current.battle.inspect(),viewer,policy,records);
        if(!selection)throw DatabaseError("PK native selection is outside the owned attack policy");
        auto definition=selection->skill_key?repository_.scalar_definition_document(*selection->skill_key):std::string{};
        repository_.submit_intent(current.ticket,phase,viewer,
            OwnedPkRound::Intent{selection->action,selection->skill_key,std::move(definition)});
        // Atomic paired resolver/order/second-action cancellation/results are
        // the next source gap; no first-arrival action is executed here.
    }
    void control_native(std::uint64_t room,const NativeCaller& caller,std::uint64_t server_phase_revision,
                        const std::string& current_profile_readset_sha256,
                        const RecoveredBattleCommand::ControlRequest& request){
        auto& current=find(room);const auto viewer=owned_viewer(current,caller,current_profile_readset_sha256);
        const auto phase=repository_.round(current.ticket);
        if(phase.revision()!=server_phase_revision||phase.battle_revision()!=current.battle.inspect().revision)
            throw DatabaseError("PK native notification has a stale server phase permit");
        repository_.control(current.ticket,phase,viewer,request);
    }
    OwnedPkRound round(std::uint64_t room){return repository_.round(find(room).ticket);}
    // Typed grant epoch is separate from checkpoint/outbox revision; exact-live
    // enqueue callback MUST call grant_submitted, not ordinary submitted.
    std::vector<Repository::GrantDelivery> pending_grants(std::uint64_t room){
        return repository_.pending_grants(find(room).ticket);
    }
    void grant_submitted(std::uint64_t room,std::uint64_t epoch,std::uint8_t viewer){
        repository_.grant_submitted(find(room).ticket,epoch,viewer);
    }
    // CUSTOM-0086 order/skip-on-terminal policy is supplied by the eventual
    // server/Lua authority. No C2S byte, arrival order, or client animation
    // counter chooses the order. Templates are FRESH, by canonical actor.
    struct Resolution {
        std::array<std::uint8_t,2> order;
        std::array<RecoveredPkActionProjection::Templates,2> templates_by_actor;
        OwnedPkRound::Masks next_control_masks;
    };
    void resolve_collected(std::uint64_t room,const Resolution& source,const Battle::Rule& rule){
        if(!rule||!((source.order==std::array<std::uint8_t,2>{0,1})||
                     (source.order==std::array<std::uint8_t,2>{1,0})))
            throw DatabaseError("PK paired order requires explicit server policy");
        auto& current=find(room);
        const auto before=current.battle.checkpoint();
        const auto prior=repository_.round(current.ticket);
        if(prior.phase()!=OwnedPkRound::Phase::Ready||prior.battle_revision()!=before.snapshot.revision||
           !OwnedPkRound::masks_valid(source.next_control_masks))
            throw DatabaseError("PK two owned commands are not ready for paired settlement");
        auto staged=current.battle;
        Replies replies;
        std::size_t executed=0;
        for(const auto viewer:source.order){
            // Both intents were selected against the same original checkpoint.
            // A lethal first action ends this CUSTOM round before the peer can
            // act. The missing original simultaneous/initiative rule remains
            // explicit provenance, rather than allowing a dead actor to attack.
            if(!staged.active())break;
            const auto& intent=*prior.intents()[viewer];
            const auto& peer=viewer==0?current.ticket.input().pair.challenger:
                                  current.ticket.input().pair.recipient;
            const auto& templates=source.templates_by_actor[viewer];
            (void)staged.act(peer.character,staged.inspect().revision,intent.action,rule,
                [&](const BattleSnapshot& state,const BattleActionResult& result){
                    const bool final_bulk=state.state==BattleState::Finished||executed==1;
                    const auto projected=RecoveredPkActionProjection::logical(state,result,templates,
                        intent.skill_key,final_bulk);
                    for(std::size_t i=0;i<2;++i)
                        replies[i].insert(replies[i].end(),projected[i].begin(),projected[i].end());
                    return projected[0];
                });
            ++executed;
        }
        if(!executed)throw DatabaseError("PK resolution applied no owned action");
        const auto after=staged.checkpoint();
        auto following=prior;
        if(!following.results_issued(after.snapshot.revision,source.next_control_masks,
                                      after.snapshot.state==BattleState::Finished))
            throw DatabaseError("PK paired result phase could not advance");
        repository_.settle(current.ticket,before,after,prior,following,replies);
        static_assert(std::is_nothrow_move_assignable_v<Battle>);
        current.battle=std::move(staged);
    }
    std::vector<Repository::Delivery> pending(std::uint64_t room){
        return repository_.pending(find(room).ticket);
    }
    void submitted(std::uint64_t room,std::uint64_t revision,std::uint8_t viewer){
        repository_.submitted(find(room).ticket,revision,viewer);
    }
    // Finished rooms/owner locks are retained. No generic clear(), loss of a
    // peer, simulated89 or re-login is an authorized settlement/recovery.
private:
    struct Room {Ticket ticket;Battle battle;Repository::RuntimeClaim claim;};
    using Rooms=std::map<std::uint64_t,Room>;
    Repository& repository_;
    Rooms rooms_;
    static std::uint8_t owned_viewer(const Room& current,const NativeCaller& caller,const std::string& profile){
        const auto& input=current.ticket.input();
        if(!caller.in_battle||profile!=input.profile_readset_sha256)
            throw DatabaseError("PK native caller/profile no longer owns the room");
        for(std::uint8_t i=0;i<2;++i){
            const auto& p=i==0?input.pair.challenger:input.pair.recipient;
            if(p.session==caller.session&&p.account==caller.account&&p.character==caller.character&&
               p.world_generation==caller.world_generation&&p.battle_generation+1==caller.battle_generation)return i;
        }
        throw DatabaseError("PK native caller identity/generations do not match either owner");
    }
    Room& find(std::uint64_t room){
        const auto at=rooms_.find(room);if(at==rooms_.end())throw DatabaseError("PK room not bound in this executor");
        return at->second;
    }
};
}
