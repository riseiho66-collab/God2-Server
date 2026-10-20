#pragma once
#include "handlers/RecoveredMovementService.h"
#include "net/Session.h"
#include <functional>
#include <optional>
#include <thread>

namespace god2 {
// A synchronous pure observation of the actual normal-world owner/pose, not
// inventory, learning, movement, publication or entry authority. Capture a new
// observation for each operation; a historical return position is not Current.
class RecoveredNormalCompanionCurrent {
public:
    static std::optional<RecoveredNormalCompanionCurrent> capture(Session& session,
            RecoveredMovementService& movement,std::function<bool()> owner,
            std::optional<RecoveredPosition> expected={}) {
        const auto initialization=session.normal_world_initialization_on_game();
        if(!initialization||!initialization->entry_written()||!owner||!owner())return {};
        const auto position=movement.observe_world_location(session.id(),session.account_id,session.character_id);
        if(!position||(expected&&*expected!=position->position()))return {};
        RecoveredNormalCompanionCurrent result(session,movement,std::move(owner),*initialization,*position);
        if(!result.current())return {};
        return result;
    }
    bool current()const noexcept {
        try{return binding_current()&&movement_->world_location_current(position_)&&owner_();}
        catch(...){return false;}
    }
    // An ordinary committed movement may change position while retaining this
    // original binding/INIT. Its separate after-state must certify the new pose.
    bool binding_current()const noexcept {
        try {
            if(thread_!=std::this_thread::get_id())return false; // Before invoking any GAME-owned provider.
            const auto peer=session_.lock();
            return peer&&owner_&&owner_()&&peer->id()==id_&&peer->account_id==account_&&peer->character_id==character_&&
                !peer->closing()&&peer->recovered_world_ready()&&peer->state()==phase_&&peer->battle_generation()==battle_&&
                (phase_==SessionState::CharacterSelected||phase_==SessionState::InWorld)&&initialization_.entry_written()&&
                peer->normal_world_initialization_current_on_game(initialization_)&&
                movement_->world_binding_current(position_)&&owner_();
        }catch(...){return false;}
    }
    const RecoveredPosition& position()const noexcept{return position_.position();}
    const RecoveredMovementService::WorldLocationObservation& movement()const noexcept{return position_;}
private:
    RecoveredNormalCompanionCurrent(Session& session,RecoveredMovementService& movement,std::function<bool()> owner,
            Session::NormalWorldInitialization initialization,RecoveredMovementService::WorldLocationObservation position)
        :session_(session.weak_from_this()),movement_(&movement),owner_(std::move(owner)),initialization_(std::move(initialization)),
         position_(position),id_(session.id()),account_(session.account_id),character_(session.character_id),
         battle_(session.battle_generation()),phase_(session.state()){}
    std::weak_ptr<Session> session_;
    RecoveredMovementService* movement_;
    std::function<bool()> owner_;
    Session::NormalWorldInitialization initialization_;
    RecoveredMovementService::WorldLocationObservation position_;
    std::uint64_t id_,account_,character_,battle_;
    SessionState phase_;
    const std::thread::id thread_=std::this_thread::get_id();
};
}
