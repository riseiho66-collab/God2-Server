#pragma once
#include "game/OwnedPveRoomState.h"
#include "net/Session.h"
#include <memory>
#include <span>
#include <thread>
namespace god2 {
// CUSTOM-0161 actual GAME/network owner. Session's private binding is the entry
// capability; DB/provider templates never construct one. One Sources instance
// is retained unchanged for the entire room, including its late admissions.
class OwnedPveRoomHost final:public Session::OwnedPveOutputOwner,
    public std::enable_shared_from_this<OwnedPveRoomHost> {
public:
    using Types=OwnedPveRoomTypes;
    using Binding=Session::OwnedPveBinding;
    using Ticket=OwnedPveRoomState::Ticket;
    struct Sources {
        enum class ControlDecision {ObserveOnly,Pass};
        // Encounter.members MUST be empty: actual prepared Session sources
        // below supply every complete root/readset/actor slot. The optional
        // current snapshot belongs to the same room; nullptr means creation.
        Types::Encounter encounter;
        std::function<Types::MemberInput(const std::shared_ptr<Session>&,
            const Binding&,std::shared_ptr<const Types::Snapshot>)> member;
        Types::Project project;
        Battle::Rule rule;
        // Whole trusted action parameters; client supplies only source/targets
        // after this host verifies current owner, epoch and native context.
        std::function<BattleAction(const Types::Snapshot&,const Types::Member&,
            const RecoveredBattleCommand::BasicAttackRequest&)> action;
        // CUSTOM opening/timeout policy is explicit, never inferred from C35
        // action2/0B. ObserveOnly cannot change a turn or simulate a native ACK.
        std::function<ControlDecision(const Types::Snapshot&,const Types::Member&,
            bool action2,const RecoveredBattleCommand::BasicAttackRequest&)> control;
        // Explicit CUSTOM AI policy. Called once for each CURRENT living enemy
        // per round; nullopt is an explicit no-action, not a synthetic ACK.
        std::function<std::optional<BattleAction>(const Types::Snapshot&,
            std::uint8_t enemy_position)> ai;
        // Fresh WORLD source after the actual original context callback. Must
        // not replay entry bytes. Persistence and actual Written are separate.
        std::function<std::vector<std::uint8_t>(const std::shared_ptr<Session>&,
            const Binding&,const Types::MemberInput&,
            const RecoveredWorldRecords::ContextNotification&)> return_world;
        // Optional actual application handoff, after BOTH durable individual
        // return and private Session WORLD renewal succeed. Never called early.
        std::function<void(const std::shared_ptr<Session>&,const Binding&,
            const Types::MemberInput&,const SqliteOwnedPveRoomRepository::ReturnContinuation&)> returned;
        // Actual application continuation readset; pure, no SQL/provider calls.
        std::function<bool(Session&,const Binding&)> member_continuation_current;
        std::function<void(const std::shared_ptr<Session>&,const Binding&,const Types::MemberInput&)> entered;
        std::function<void(const std::shared_ptr<Session>&,const Binding&)> cancelled;
    };
    explicit OwnedPveRoomHost(SqliteOwnedPveRoomRepository&);
    ~OwnedPveRoomHost();
    // Called by real committed normal WORLD movement encounter provider only.
    // Never accepts a diagnostic/per-Session mutable Battle binding.
    Ticket create(std::vector<std::shared_ptr<Session>>,std::shared_ptr<const Sources>);
    // Actual WORLD C6A. Both DWORDs resolve to exact retained native handles;
    // no common-character-ID fallback or watcher/party routing.
    void support(std::shared_ptr<Session>,RecoveredSosSupportRequest::Request);
    bool bound(const Session&)const noexcept;
    bool pending(const Session&)const noexcept;
    // Returns false only when no PvE binding exists. A bound batch is fully
    // classified before any mutation; one native mutation plus opaque ticks
    // per batch is accepted. Unsupported/multiple mutations throw, no prefix.
    bool handle(Session&,std::span<const RecoveredWorldRecords::Record>);
    void disconnected(Session&);
    void retire_dispatch()noexcept;
    void stop()noexcept;
    void owned_pve_written(Session&,const Binding&,std::uint64_t,bool)override;
private:
    struct Peer;struct Room;class Operation;
    std::shared_ptr<Room> room_for(const Session&)const;
    Types::PureCurrent current(const std::shared_ptr<Room>&,
        std::optional<std::uint64_t> allow_retired={})const;
    void drain(const std::shared_ptr<Room>&);
    void advance(const std::shared_ptr<Room>&);
    void animation_started(const std::shared_ptr<Room>&,std::uint64_t before_sequence);
    Types::Project projection(const std::shared_ptr<Room>&)const;
    void admit_prepared(const std::shared_ptr<Room>&,const std::shared_ptr<Peer>&,RecoveredSosSupportRequest::Request);
    void cancel_pending(const std::shared_ptr<Room>&)noexcept;
    void cancel_prepared(const std::shared_ptr<Room>&,const std::shared_ptr<Peer>&)noexcept;
    bool process(const std::shared_ptr<Room>&,Session&,
        std::span<const RecoveredWorldRecords::Record>,bool allow_queue);
    void fail(const std::shared_ptr<Room>&)noexcept;
    void cleanup(const std::shared_ptr<Room>&,std::uint64_t triggering_session);
    OwnedPveRoomState state_;
    std::map<std::uint64_t,std::shared_ptr<Room>> rooms_;
    std::map<std::uint64_t,std::weak_ptr<Room>> sessions_;
    std::map<std::uint64_t,std::weak_ptr<Room>> pending_sessions_;
    std::thread::id thread_;
    bool accepting_=true,stopped_=false,creating_=false,creation_poisoned_=false;
};
}
