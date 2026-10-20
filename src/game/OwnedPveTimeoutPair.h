#pragma once
#include "game/OwnedPveRoomTypes.h"
#include "protocol/RecoveredWorldRecords.h"
#include <array>
#include <optional>
#include <span>
#include <stdexcept>
namespace god2 {
// Matched aaf0:5129C0 can enqueue action2 for A and then B before413370.
// Each518E50 action2 rewrites its targets to the acting role's one-hot slot.
// This is a native batch grammar, NOT an original defense/pass/turn policy.
struct OwnedPveTimeoutPair {
    using Fields=RecoveredBattleCommand::BasicAttackRequest;
    using Record=RecoveredWorldRecords::Record;
    struct Batch {std::array<Fields,2> roles;std::optional<Fields> progress;};
    static std::optional<Batch> read(std::span<const Record> records) {
        std::size_t count=0;for(const auto& r:records)count+=std::holds_alternative<RecoveredBattleCommand::Action2Request>(r);
        if(count<2)return {};
        if(count!=2)throw std::invalid_argument("PvE native timeout batch exceeds its two actual roles");
        Batch batch{};std::size_t at=0;
        for(const auto& r:records) {
            if(const auto* request=std::get_if<RecoveredBattleCommand::Action2Request>(&r))batch.roles[at++]=request->fields;
            else if(const auto* control=std::get_if<RecoveredBattleCommand::ControlRequest>(&r)) {
                if(batch.progress)throw std::invalid_argument("PvE timeout batch repeats native progress");
                batch.progress=control->fields;
            }else if(!std::holds_alternative<RecoveredWorldRecords::Tick>(r)&&
                     !std::holds_alternative<RecoveredWorldRecords::TimerNotification>(r))
                throw std::invalid_argument("PvE timeout pair intersects another mutation; no prefix allowed");
        }
        for(std::size_t i=0;i<2;++i) {
            const auto& r=batch.roles[i];
            if(r.actor_position>=14||r.side_flag!=i||r.target_masks[0]!=(1u<<r.actor_position)||r.target_masks[1])
                throw std::invalid_argument("PvE timeout pair differs from original ordered self-target roles");
        }
        if(batch.roles[0].actor_position==batch.roles[1].actor_position||
           batch.roles[0].context_storage!=batch.roles[1].context_storage)
            throw std::invalid_argument("PvE timeout pair repeats a role or changes native context");
        // Unwritten byte4/tail bits remain exactly the received values.
        return batch;
    }
    static bool current(const Batch& batch,const OwnedPveRoomTypes::Member& member,
            const OwnedPveRoomTypes::Snapshot& room)noexcept {
        using T=OwnedPveRoomTypes;
        const auto primary=member.primary_position();const auto pet=member.pet_position();
        if(room.pending_swap||room.checkpoint.snapshot.state!=BattleState::Active||
           member.status!=T::MemberStatus::Active||member.disconnected||member.return_context||
           !member.primary_grant||!member.secondary_grant||!member.input.pet||!pet||
           primary>=14||*pet>=14||primary==*pet||member.grant_epoch!=room.grant_epoch||
           batch.roles[0].actor_position!=primary||batch.roles[1].actor_position!=*pet||
           batch.roles[0].context_storage!=member.input.command_context)return false;
        for(const auto slot:{primary,*pet}) {
            const auto& actor=room.checkpoint.snapshot.actors[slot];
            if(!actor||!actor->hp||actor->controller!=member.input.identity.character)return false;
        }
        return !batch.progress||(batch.progress->actor_position==primary&&batch.progress->side_flag<=1&&
            batch.progress->context_storage==member.input.command_context);
    }
};
}
