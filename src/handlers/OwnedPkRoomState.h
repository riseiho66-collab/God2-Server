#pragma once
#include "db/SqliteOwnedPkRoomRepository.h"
#include "handlers/RecoveredPkCommandSelection.h"
#include "protocol/RecoveredPkActionProjection.h"
#include "game/OwnedTaiwanPkBasicResultSource.h"
#include "game/OwnedTaiwanPkTerminalSource.h"
#include <map>
#include <type_traits>
namespace god2 {
// CUSTOM-0086 concrete single-game-executor shared PK state. Each room owns
// exactly ONE Battle; two Sessions must never create two mutable copies.
// Still an INCOMPLETE backend: a RoomAuthority adapter must own live profile
// refresh, two Session bindings, turn/skill policy, outbox transport receipts,
// terminal WORLD re-entry and reconnect before Application can install it.
class OwnedPkRoomState {
    // Per-room, single-executor fence. A staged Battle is a different object,
    // so Battle's own callback fence cannot protect the containing Room.
    struct CallbackState {bool operating=false,invalidated=false,recovery=false;};
    class Operation {
    public:
        explicit Operation(CallbackState& value):state_(value){
            if(state_.operating){state_.invalidated=true;throw DatabaseError("PK Room callback reentry rejected");}
            if(state_.recovery)throw DatabaseError("PK Room requires durable recovery");
            state_.operating=true;state_.invalidated=false;
        }
        ~Operation(){
            // An unexpected callback during persistence may follow a COMMIT.
            // Retain the claim/history, but never retry an old mutable model.
            if(persisting_&&state_.invalidated)state_.recovery=true;
            state_.operating=false;
        }
        Operation(const Operation&)=delete;
        Operation& operator=(const Operation&)=delete;
        void current()const{if(state_.invalidated)throw DatabaseError("PK Room callback invalidated its operation");}
        void persist(){current();persisting_=true;}
    private:
        CallbackState& state_;
        bool persisting_=false;
    };
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
    // CUSTOM-0115 identity only. The private live Room must own this original
    // Ticket; an equal room/readset from another issuer is insufficient.
    bool owns_ticket(const Ticket& ticket)const noexcept{
        const auto at=rooms_.find(ticket.id());
        return at!=rooms_.end()&&!at->second.callbacks.recovery&&at->second.ticket.same_incarnation(ticket);
    }
    void abandon(const Ticket& ticket)noexcept{
        const auto at=rooms_.find(ticket.id());
        if(at!=rooms_.end()&&at->second.callbacks.operating){at->second.callbacks.invalidated=true;return;}
        repository_.abandon(ticket);
    }
    // Only server-side activation. Both entries become DURABLE outbox rows;
    // this does not change Session states or claim their queues accepted them.
    void activate(const Ticket& ticket){
        reject_existing_activation(ticket.id());
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
        reject_existing_activation(ticket.id());
        auto claim=repository_.claim_runtime(ticket);
        const auto retained=repository_.recover_retained(ticket);
        if(retained.released_finished())
            throw DatabaseError("PK released Finished history cannot restore a mutable room");
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
        const auto at=rooms_.find(room);if(at==rooms_.end()||at->second.callbacks.recovery)return {};
        return at->second.battle.inspect();
    }
    // CUSTOM-0119 derives the expected complete checkpoint including RNG
    // from this actual runtime-claimed Battle. No supplied digest/checkpoint
    // can mint this current durable frozen-profile binding.
    std::string current_owned_profile(std::uint64_t room){
        const auto& current=find(room);
        return repository_.require_active_owned_profile(current.ticket,current.battle.checkpoint());
    }
    // Policies are supplied by the authoritative adapter. This method does
    // not accept native35/context/selection bytes as a BattleAction directly.
    // Resource deltas are battle-local; saved character rows stay unchanged.
    // Legacy trusted primitive is refused by the repository for collection
    // rooms; it cannot bypass persisted input/grant phases. Use submit_native
    // and the atomic paired resolver below for collection rooms.
    void act(std::uint64_t room,std::uint64_t controller,std::uint64_t revision,
             const BattleAction& supplied_action,const Battle::Rule& supplied_rule,const Project& supplied_project,
             const std::optional<NativeSkillRecord>& supplied_definition={}){
        auto& current=find(room);Operation operation(current.callbacks);
        const auto action=supplied_action;const auto rule=supplied_rule;const auto project=supplied_project;
        const auto definition=supplied_definition;operation.current();
        if(!rule||!project)throw DatabaseError("PK active room unavailable");
        if(controller!=current.ticket.input().pair.challenger.character&&
           controller!=current.ticket.input().pair.recipient.character)
            throw DatabaseError("PK controller is not either owned participant");
        const auto before=current.battle.checkpoint();
        auto staged=current.battle;
        Replies replies;
        const Battle::Rule checked_rule=[&](const auto& input){
            operation.current();const auto result=rule(input);operation.current();return result;
        };
        (void)staged.act(controller,revision,action,checked_rule,[&](const auto& state,const auto& result){
            operation.current();replies=project(state,result);operation.current();return replies[0];
        });
        const auto after=staged.checkpoint();
        operation.persist();
        repository_.advance(current.ticket,before,after,replies,definition);
        operation.current();
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
    void submit_native(std::uint64_t room,const NativeCaller& supplied_caller,
                       std::uint64_t server_battle_revision,std::uint64_t server_grant_epoch,
                       const std::string& supplied_profile,
                       const RecoveredPkCommandSelection::Policy& supplied_policy,
                       std::span<const RecoveredWorldRecords::Record> supplied_records){
        auto& current=find(room);Operation operation(current.callbacks);
        const auto caller=supplied_caller;const auto profile=supplied_profile;const auto policy=supplied_policy;
        const std::vector<RecoveredWorldRecords::Record> records(supplied_records.begin(),supplied_records.end());
        operation.current();const auto viewer=owned_viewer(current,caller,profile);
        const auto phase=repository_.round(current.ticket);
        if(server_battle_revision!=current.battle.inspect().revision||phase.battle_revision()!=server_battle_revision||
           phase.grant_epoch()!=server_grant_epoch||policy.client_actor!=0||policy.client_side!=0||
           policy.context!=current.ticket.input().entry.command_contexts()[viewer])
            throw DatabaseError("PK native command has no matching server-owned grant/profile header");
        const auto selection=RecoveredPkCommandSelection::select(current.battle.inspect(),viewer,policy,records);
        if(!selection)throw DatabaseError("PK native selection is outside the owned attack policy");
        auto definition=selection->skill_key?repository_.scalar_definition_document(*selection->skill_key):std::string{};
        operation.persist();
        repository_.submit_intent(current.ticket,phase,viewer,
            OwnedPkRound::Intent{selection->action,selection->skill_key,std::move(definition)});
        operation.current();
        // The paired resolver below consumes the persisted pair. Its actual
        // authority/order/Rule hosting remain open; no first-arrival action
        // is executed here.
    }
    void control_native(std::uint64_t room,const NativeCaller& supplied_caller,std::uint64_t server_phase_revision,
                        const std::string& supplied_profile,
                        const RecoveredBattleCommand::ControlRequest& supplied_request){
        auto& current=find(room);Operation operation(current.callbacks);
        const auto caller=supplied_caller;const auto profile=supplied_profile;const auto request=supplied_request;
        operation.current();const auto viewer=owned_viewer(current,caller,profile);
        const auto phase=repository_.round(current.ticket);
        if(phase.revision()!=server_phase_revision||phase.battle_revision()!=current.battle.inspect().revision)
            throw DatabaseError("PK native notification has a stale server phase permit");
        operation.persist();repository_.control(current.ticket,phase,viewer,request);operation.current();
    }
    OwnedPkRound round(std::uint64_t room){return repository_.round(find(room).ticket);}
    // Typed grant epoch is separate from checkpoint/outbox revision; exact-live
    // enqueue callback MUST call grant_submitted, not ordinary submitted.
    std::vector<Repository::GrantDelivery> pending_grants(std::uint64_t room){
        const auto& current=find(room);
        return repository_.pending_grants(current.ticket,current.battle.checkpoint());
    }
    void grant_submitted(std::uint64_t room,std::uint64_t epoch,std::uint8_t viewer){
        auto& current=find(room);Operation operation(current.callbacks);
        operation.persist();repository_.grant_submitted(current.ticket,epoch,viewer);operation.current();
    }
    // CUSTOM-0086 order/skip-on-terminal policy is supplied by the eventual
    // server/Lua authority. No C2S byte, arrival order, or client animation
    // counter chooses the order. Templates are FRESH, by canonical actor.
    struct Resolution {
        std::array<std::uint8_t,2> order;
        std::array<RecoveredPkActionProjection::Templates,2> templates_by_actor;
        OwnedPkRound::Masks next_control_masks;
    };
    // CUSTOM-0117 real room-owned fresh BASIC1 result source. Order, next
    // native control masks and pure gameplay Rule remain authoritative inputs;
    // none is inferred from initial masks, arrival order or client counters.
    // No caller-supplied templates/checkpoint/round can mint this private source.
    void resolve_collected_basic(std::uint64_t room,const std::array<std::uint8_t,2>& supplied_order,
                                 const OwnedPkRound::Masks& supplied_masks,const Battle::Rule& supplied_rule){
        auto& current=find(room);Operation operation(current.callbacks);
        const auto order=supplied_order;const auto next_control_masks=supplied_masks;const auto rule=supplied_rule;
        operation.current();
        const auto prior=repository_.round(current.ticket);
        Resolution source{order,OwnedTaiwanPkBasicResultSource::prepare(
            current.ticket,current.battle.inspect(),prior,order),next_control_masks};
        operation.current();resolve_collected_impl(room,source,rule,prior.document(),operation);
    }
    // CUSTOM-0122 explicit result-notification mode. No caller next-mask
    // guess: the actual staged post-Battle roster supplies notification bounds.
    void resolve_collected_basic_notifications(std::uint64_t room,
            const std::array<std::uint8_t,2>& supplied_order,const Battle::Rule& supplied_rule){
        auto& current=find(room);Operation operation(current.callbacks);
        const auto order=supplied_order;const auto rule=supplied_rule;operation.current();
        const auto prior=repository_.round(current.ticket);
        Resolution source{order,OwnedTaiwanPkBasicResultSource::prepare(
            current.ticket,current.battle.inspect(),prior,order),{}};
        operation.current();resolve_collected_impl(room,source,rule,prior.document(),operation,true);
    }
    void resolve_collected(std::uint64_t room,const Resolution& supplied_source,const Battle::Rule& supplied_rule){
        auto& current=find(room);Operation operation(current.callbacks);
        const auto source=supplied_source;const auto rule=supplied_rule;operation.current();
        resolve_collected_impl(room,source,rule,{},operation);
    }
private:
    void resolve_collected_impl(std::uint64_t room,const Resolution& source,const Battle::Rule& rule,
                                const std::optional<std::string>& expected_round,Operation& operation,bool notifications=false){
        if(!rule||!((source.order==std::array<std::uint8_t,2>{0,1})||
                     (source.order==std::array<std::uint8_t,2>{1,0})))
            throw DatabaseError("PK paired order requires explicit server policy");
        auto& current=find(room);
        const auto before=current.battle.checkpoint();
        const auto prior=repository_.round(current.ticket);
        if((expected_round&&prior.document()!=*expected_round)||
           prior.phase()!=OwnedPkRound::Phase::Ready||prior.battle_revision()!=before.snapshot.revision||
           !OwnedPkRound::masks_valid(source.next_control_masks))
            throw DatabaseError("PK two owned commands are not ready for paired settlement");
        auto staged=current.battle;
        const Battle::Rule checked_rule=[&](const auto& input){
            operation.current();const auto result=rule(input);operation.current();return result;
        };
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
            (void)staged.act(peer.character,staged.inspect().revision,intent.action,checked_rule,
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
        const bool advanced=notifications?following.results_issued_notification(after.snapshot):
            following.results_issued(after.snapshot.revision,source.next_control_masks,
                                      after.snapshot.state==BattleState::Finished);
        if(!advanced)
            throw DatabaseError("PK paired result phase could not advance");
        if(notifications&&after.snapshot.state==BattleState::Finished){
            if(!following.issue_terminal_notification())
                throw DatabaseError("PK terminal notification phase could not advance");
            const auto terminal=OwnedTaiwanPkTerminalSource::prepare(current.ticket,after.snapshot,following);
            // Native FIFO holds88/89 behind the current83 group and stops its
            // consume visit at88. Append89 after final88 in the SAME durable
            // pair, not an invented Battle revision/independent receipt stage.
            for(auto& reply:replies)reply.insert(reply.end(),terminal.begin(),terminal.end());
        }
        operation.persist();repository_.settle(current.ticket,before,after,prior,following,replies);operation.current();
        static_assert(std::is_nothrow_move_assignable_v<Battle>);
        current.battle=std::move(staged);
    }
public:
    bool terminal_notification_current(std::uint64_t room,std::span<const std::uint8_t> bytes){
        auto& current=find(room);const auto phase=repository_.round(current.ticket);
        if(!phase.terminal_notification())return false;
        const auto expected=OwnedTaiwanPkTerminalSource::prepare(current.ticket,current.battle.inspect(),phase);
        return RecoveredTaiwanPkTerminalNotification::matches_retained_result_sequence(bytes)&&
            std::equal(expected.begin(),expected.end(),bytes.end()-expected.size());
    }
    std::vector<Repository::Delivery> pending(std::uint64_t room){
        return repository_.pending(find(room).ticket);
    }
    void submitted(std::uint64_t room,std::uint64_t revision,std::uint8_t viewer){
        auto& current=find(room);Operation operation(current.callbacks);
        operation.persist();repository_.submitted(current.ticket,revision,viewer);operation.current();
    }
    // Finished rooms/owner locks are retained. No generic clear(), loss of a
    // peer, simulated89 or re-login is an authorized settlement/recovery.
private:
    friend class OwnedPkOutboxPublication;
    // CUSTOM-0127 only the exact Publication's two live fullwrite observations
    // consume this seam. It supplies this actual runtime-owned checkpoint;
    // native input/public submitted flags cannot request a resource save.
    void commit_terminal_resources(std::uint64_t room,const Replies& actually_written){
        auto& current=find(room);Operation operation(current.callbacks);
        const auto written=actually_written;operation.persist();
        repository_.commit_terminal_resources(current.ticket,current.battle.checkpoint(),written);operation.current();
    }
    // CUSTOM-0132 stronger paired preparation guard, distinct from own early
    // terminal context. Runtime claim supplies checkpoint; existing save only.
    std::uint64_t require_terminal_resources_saved(std::uint64_t room,const Replies& actually_written){
        const auto& current=find(room);const auto actual=current.battle.checkpoint();
        repository_.require_terminal_resources_saved(current.ticket,actual,actually_written);
        return actual.snapshot.revision;
    }
    // CUSTOM-0128 private, read-only terminal input guard. Never resurrect an
    // old world-entry receipt or derive a runtime checkpoint from native1C.
    std::uint64_t require_terminal_context(std::uint64_t room,std::uint8_t viewer,
            const std::array<std::uint8_t,4>& payload,const std::vector<std::uint8_t>& actually_written){
        const auto& current=find(room);const auto actual=current.battle.checkpoint();
        repository_.require_terminal_context(current.ticket,actual,viewer,payload,actually_written);
        return actual.snapshot.revision;
    }
    // CUSTOM-0133 only the actual Publication whole-written/finalisation path
    // may use these private seams. RoomState supplies its own live claim and
    // Battle; source observers never construct them from native/scalar input.
    Repository::FinishedReturnReleasePlan prepare_finished_return_release(std::uint64_t room,
            const Replies& actually_written,const std::array<std::array<std::uint8_t,4>,2>& payloads){
        auto& current=find(room);Operation operation(current.callbacks);
        const auto written=actually_written;const auto inputs=payloads;operation.current();
        auto plan=repository_.prepare_finished_return_release(current.ticket,current.claim,
            current.battle.checkpoint(),written,inputs);
        operation.current();return plan;
    }
    Repository::FinishedReturnReleaseReceipt commit_finished_return_release(std::uint64_t room,
            const Repository::FinishedReturnReleasePlan& plan,
            const std::function<void(sqlite3*)>& final_stored_fence){
        auto& current=find(room);Operation operation(current.callbacks);
        const auto retained_plan=plan;const auto fence=final_stored_fence;operation.current();
        if(!fence)throw DatabaseError("PK finished return requires its stored observer");
        const auto checked_fence=[&](sqlite3* db){operation.current();fence(db);operation.current();};
        operation.persist();
        auto receipt=repository_.commit_finished_return_release(current.ticket,current.claim,
            current.battle.checkpoint(),retained_plan,checked_fence);
        operation.current();
        current.finished_return.emplace(receipt); // Exact existing Room stamp; shared pointer copy only.
        return receipt;
    }
    void require_finished_return_release(std::uint64_t room,const Repository::FinishedReturnReleaseReceipt& receipt){
        const auto& current=find(room);
        repository_.require_finished_return_release(current.ticket,current.claim,current.battle.checkpoint(),receipt);
    }
    bool retire_finished_return_release(std::uint64_t room,const Repository::FinishedReturnReleaseReceipt& receipt)noexcept{
        const auto at=rooms_.find(room);
        if(at==rooms_.end())return false;
        if(at->second.callbacks.operating){at->second.callbacks.invalidated=true;return false;}
        if(at->second.callbacks.recovery||!at->second.finished_return||*at->second.finished_return!=receipt||
           !repository_.finished_return_release_runtime_current(at->second.ticket,at->second.claim,
                at->second.battle.inspect(),receipt))return false;
        // This exact Room's Finished Battle has no later legal mutation: every
        // old active/Finished permit rejects the release ledger. Its complete
        // checkpoint/RNG was bound before COMMIT; do not re-encode or run SQL.
        rooms_.erase(at);return true;
    }
    struct Room {Ticket ticket;Battle battle;Repository::RuntimeClaim claim;
        std::optional<Repository::FinishedReturnReleaseReceipt> finished_return{};
        CallbackState callbacks{};};
    using Rooms=std::map<std::uint64_t,Room>;
    Repository& repository_;
    Rooms rooms_;
    void reject_existing_activation(std::uint64_t room){
        const auto at=rooms_.find(room);if(at==rooms_.end())return;
        if(at->second.callbacks.operating)at->second.callbacks.invalidated=true;
        throw DatabaseError("PK room already active in this executor");
    }
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
        const auto at=rooms_.find(room);if(at==rooms_.end()||at->second.callbacks.recovery)
            throw DatabaseError("PK room not bound or requires durable recovery");
        return at->second;
    }
};
}
