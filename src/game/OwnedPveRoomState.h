#pragma once
#include "db/SqliteOwnedPveRoomRepository.h"
#include <map>
#include <memory>
#include <thread>
namespace god2 {
// One authoritative immutable checkpoint/RNG per room. A Session only retains
// its identity/ticket; it never owns a mutable Battle copy of this room.
class OwnedPveRoomState {
public:
    using Types=OwnedPveRoomTypes;
    using Ticket=SqliteOwnedPveRoomRepository::Ticket;
    explicit OwnedPveRoomState(SqliteOwnedPveRoomRepository&);
    ~OwnedPveRoomState();
    OwnedPveRoomState(const OwnedPveRoomState&)=delete;OwnedPveRoomState& operator=(const OwnedPveRoomState&)=delete;
    Ticket create(Types::Encounter,Types::Project,Types::PureCurrent);
    void admit(const Ticket&,Types::MemberInput,Types::Project,Types::PureCurrent);
    void toggle_support(const Ticket&,Types::Identity,std::uint64_t grant_epoch,
        std::uint8_t actor_position,bool,Types::Project,Types::PureCurrent);
    void act(const Ticket&,Types::Identity,std::uint64_t grant_epoch,BattleAction,Battle::Rule,Types::Project,Types::PureCurrent);
    void act_ai(const Ticket&,BattleAction,Battle::Rule,Types::Project,Types::PureCurrent);
    void pass(const Ticket&,Types::Identity,std::uint64_t grant_epoch,std::uint8_t actor_position,
        Types::Project,Types::PureCurrent);
    void grant_round(const Ticket&,Types::Project,Types::PureCurrent,bool cycle_progress_observed=false);
    // CUSTOM withdrawal removes only this member's combat presence. Its actual
    // pre-withdraw resources are saved; HP0 combat tombstones do not kill the save.
    void withdraw(const Ticket&,Types::Identity,bool disconnected,Types::Project,Types::PureCurrent);
    void retire_disconnected(const Ticket&,std::vector<Types::Identity>,Types::Project,Types::PureCurrent);
    std::vector<Types::Delivery> pending(const Ticket&)const;
    void written(const Ticket&,std::uint64_t sequence,Types::Identity,bool success,Types::PureCurrent);
    void prepare_return(const Ticket&,Types::Identity,std::vector<std::uint8_t> logical,
        std::array<std::uint8_t,4> expected_context,Types::PureCurrent);
    void complete_return(const Ticket&,Types::Identity,std::array<std::uint8_t,4>,Types::PureCurrent);
    std::shared_ptr<const Types::Snapshot> inspect(const Ticket&)const;
    bool recovery_required(const Ticket&)const noexcept;
    void retire_closed(const Ticket&); // Durable history remains; no live actor/input/output.
    void stop()noexcept;
private:
    struct Room;
    class Operation;
    using State=Types::Snapshot;
    std::shared_ptr<Room> find(const Ticket&)const;
    void publish(Operation&,std::shared_ptr<State>,const Types::PureCurrent&);
    static Types::Member& member(State&,const Types::Identity&);
    static void require_drained(const State&);
    static void append(State&,std::vector<Types::Output>,bool every_live_member);
    static void check_current(const Types::PureCurrent&);
    void project(Operation&,State&,const Types::Change&,const Types::Project&);
    SqliteOwnedPveRoomRepository& repository_;
    std::map<std::uint64_t,std::shared_ptr<Room>> rooms_;
    std::thread::id thread_;
    bool stopped_=false;
    bool creating_=false,creation_reentered_=false;
};
}
