#pragma once
#include "EffectiveGuildRemovalServiceDraft.h"
#include "EffectiveGuildGovernanceServiceDraft.h"
#include "OwnedGuildSuccessionWorldHostDraft.h"
#include "handlers/EffectiveGuildAnnouncementServiceDraft.h"
#include <variant>
#include "protocol/RecoveredGuildDisband75.h"
namespace god2 {
// PRIVATE trusted executor composition. One captured publication, all wire
// validation before any prefix; mandatory peer readiness before EACH SQL entry.
class CombinedGuildLifecycleRuntimeDraft {
public:
    using Panel=OwnedGuildSuccessionServiceDraft;
    using Host=OwnedGuildSuccessionWorldHostDraft;
    using Admission=EffectiveGuildAdmissionServiceDraft;
    using Removal=EffectiveGuildRemovalServiceDraft;
    using Governance=EffectiveGuildGovernanceServiceDraft;
    using Announcement=EffectiveGuildAnnouncementServiceDraft;
    using Indexed=founder_transfer_contract_draft::IndexedLogical;
    using Intent=std::variant<std::monostate,Panel::Plan,Admission::Plan,Removal::Plan,Governance::Plan>;
    struct Captured {std::size_t index{};std::vector<std::uint8_t> logical;std::optional<Panel::Publication> original;Intent intent;};
    struct Batch {bool structurally_valid{};std::optional<Panel::Publication> original;std::vector<Captured> actions;};
    CombinedGuildLifecycleRuntimeDraft(Panel& panel,Host& host,Admission& admission,Removal& removal,Governance& governance,Announcement& announcement):panel_(panel),host_(host),admission_(admission),removal_(removal),governance_(governance),announcement_(announcement){}
    Batch capture_before_any_prefix(std::uint64_t session,std::span<const Indexed> records) const {
        std::size_t previous=0;bool first=true;
        for(const auto& item:records){
            if(!first && item.index<=previous)return {};first=false;previous=item.index;
            if(item.logical.size()!=2)return {};
            if(item.logical[0]==0x73){if(!RecoveredGuildLeave::decode(item.logical))return {};}
            else if(item.logical[0]==0x75){if(!RecoveredGuildDisband75::decode(item.logical))return {};}
            else if(item.logical[0]==0x71 || item.logical[0]==0x72){if(!RecoveredGuildLeadership::decode(item.logical))return {};}
            else return {};
        }
        const auto original=panel_.publication(session);Batch out{true,original,{}};
        for(const auto& item:records){Captured captured{item.index,item.logical,original,{}};
            if(original){
                const auto slot=item.logical[1];
                if(item.logical[0]==0x73){
                    if(slot==0){if(auto leave=removal_.prepare_before_prefix(*original,item.logical))captured.intent=*leave;}
                    else if(auto transfer=panel_.prepare(*original,slot))captured.intent=*transfer;
                }else if(item.logical[0]==0x75){if(auto disband=governance_.prepare_before_prefix(*original,item.logical))captured.intent=*disband;
                }else{
                    const auto wire=RecoveredGuildLeadership::decode(item.logical);
                    if(auto pending=admission_.prepare_before_prefix(*original,*wire))captured.intent=*pending;
                    else if(auto office=governance_.prepare_before_prefix(*original,item.logical))captured.intent=*office;
                    else if(item.logical[0]==0x72)if(auto kick=removal_.prepare_before_prefix(*original,item.logical))captured.intent=*kick;
                }
            }
            out.actions.push_back(std::move(captured));
        }
        return out;
    }
    bool execute(const Captured& item){
        const bool accepted=std::visit([&](const auto& plan)->bool{
            using T=std::decay_t<decltype(plan)>;
            if constexpr(std::is_same_v<T,std::monostate>)return false;
            else{
                if(item.original!=std::optional{plan.publication})return false;
                // Pure trusted peer/executor guard precedes service/SQL access.
                if(!host_.preflight(plan.publication.state.audience))return false;
                if constexpr(std::is_same_v<T,Panel::Plan>){
                    if(item.logical!=std::vector<std::uint8_t>{0x73,plan.slot})return false;
                    return panel_.execute(plan);
                }else if constexpr(std::is_same_v<T,Admission::Plan>){
                    if(RecoveredGuildLeadership::decode(item.logical)!=std::optional{plan.request})return false;
                    return admission_.execute(plan);
                }else if constexpr(std::is_same_v<T,Removal::Plan>){
                    const std::vector<std::uint8_t> expected{plan.action==Removal::Action::Leave?std::uint8_t{0x73}:std::uint8_t{0x72},plan.slot};
                    return item.logical==expected && removal_.execute(plan);
                }else{const std::vector<std::uint8_t> expected{plan.action==Governance::Action::Appoint?std::uint8_t{0x71}:plan.action==Governance::Action::RemoveOffice?std::uint8_t{0x72}:std::uint8_t{0x75},plan.slot};return item.logical==expected && governance_.execute(plan);
                }
            }
        },item.intent);
        // Every attempted valid captured row consumes ONLY its original grant.
        // Recovered peer readiness cannot revive a denied suffix in this batch.
        if(item.original){panel_.invalidate_exact(*item.original);announcement_.invalidate_exact_publication(*item.original);}
        return accepted;
    }
    static std::optional<Announcement::Repository::Snapshot> execute_announcement(
        Panel& panel,Host& host,Announcement& service,const Announcement::Action& action,
        const Announcement::Wire::Request& request,Announcement::Time now){
        if(!host.preflight(action.panel.state.audience)){panel.invalidate_exact(action.panel);service.invalidate_exact_publication(action.panel);return {};}
        const auto result=service.execute(action,request,now);panel.invalidate_exact(action.panel);service.invalidate_exact_publication(action.panel);return result;
    }
private:Panel& panel_;Host& host_;Admission& admission_;Removal& removal_;Governance& governance_;Announcement& announcement_;
};
}
