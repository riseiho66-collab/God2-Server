#pragma once
#include "handlers/OwnedGuildRosterService.h"
#include "protocol/OwnedGuildPanelHeader.h"
#include "protocol/RecoveredNpcInteraction.h"
#include "protocol/RecoveredGuildLeave.h"
#include "protocol/RecoveredWorldFrame.h"

namespace god2 {
// CUSTOM-0077: member panel extends the frozen0076 roster projection. Its only
// mutation is authenticated self-leave; no leader/officer/economy action.
// Native4B1660 control4 is "new player help", not an original cave entry.
// CUSTOM entry binds this currently unimplemented fixed service to the owned
// readonly panel. Its label mismatch is explicit; no native NPC is fabricated.
// A target number, client name or UI disabled bit grants no membership.
class OwnedGuildPanelService {
public:
    struct Plan {
        OwnedGuildRosterService::Plan roster;
        std::vector<std::uint8_t> logical;
    };
    using Leave=std::function<void(std::uint64_t,std::uint64_t,const StoredGuildMembership&)>;
    explicit OwnedGuildPanelService(OwnedGuildRosterService& roster,Leave leave={}):
        roster_(roster),leave_(std::move(leave)){}
    static constexpr bool custom_help_entry(const RecoveredNpcInteraction::Request& request) noexcept {
        return request.raw_target==0x087b; // exact native4B1660->496750 constant
    }
    std::optional<Plan> prepare(std::uint64_t session) const {
        auto projection=roster_.prepare(session);
        if(!projection || !projection->next.roster)return {};
        auto header=OwnedGuildPanelHeader::readonly_members(projection->next.roster->members.size());
        if(!header)return {};
        Plan plan{std::move(*projection),{}};
        plan.logical=plan.roster.logical;
        plan.logical.insert(plan.logical.end(),header->begin(),header->end());
        if(!current(plan))return {};
        return plan;
    }
    bool current(const Plan& plan) const {return roster_.current(plan.roster);}
    void published(const Plan& plan) {roster_.published(plan.roster);}
    std::optional<Plan> prepare_leave(std::uint64_t session,const RecoveredGuildLeave::Request& request) const {
        try {
            // Only self slot0 is supported. A complete, already published
            // current cache must still agree with authenticated owner state.
            // Transactional storage rechecks the full membership lease.
            if(request.slot!=0 || !leave_ || !roster_.panel_ready(session))return {};
            return prepare(session);
        }catch(const std::exception&){return {};}
    }
    bool leave(const Plan& plan,const RecoveredGuildLeave::Request& request) const {
        try {
            if(request.slot!=0 || !leave_ || !plan.roster.next.roster || !current(plan))return false;
            const auto& state=plan.roster.next;
            leave_(state.peer.account,state.peer.character,state.roster->membership);
            return true;
        }catch(const std::exception&){return false;}
    }
    bool leave(std::uint64_t session,const RecoveredGuildLeave::Request& request) const {
        const auto plan=prepare_leave(session,request);return plan && leave(*plan,request);
    }
    // A new73 mutation splits only its own batch into ordered old-route
    // prefixes. Validate ALL returned complete envelopes before queueing the
    // unchanged logical responses, so an invalid prefix cannot publish partly.
    static std::optional<std::vector<std::vector<std::uint8_t>>> prefix_replies(
        std::span<const std::uint8_t> wire) {
        std::vector<std::vector<std::uint8_t>> result;
        for(std::size_t offset=0;offset<wire.size();) {
            if(wire.size()-offset<2)return {};
            const auto length=static_cast<std::size_t>(wire[offset])+256u*wire[offset+1];
            if(length<4 || length>wire.size()-offset)return {};
            auto logical=RecoveredWorldFrame::decode(wire.subspan(offset,length));
            if(!logical)return {};
            result.push_back(std::move(*logical));offset+=length;
        }
        return result;
    }
private:
    OwnedGuildRosterService& roster_;
    Leave leave_;
};
}
