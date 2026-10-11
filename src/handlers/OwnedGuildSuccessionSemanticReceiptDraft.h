#pragma once
#include "handlers/CombinedGuildLifecycleRuntimeDraft.h"
namespace god2 {
// PRIVATE83 audit only. Values come from the exact pre-prefix captured plan,
// never a postcommit SQL inference. Emit only after actual execute()==true.
struct OwnedGuildSuccessionSemanticReceiptDraft {
    std::string kind;std::uint64_t session{},account{},character{},guild{},guild_revision{},target_account{},target_character{};
    unsigned opcode{},slot{},target_slot{};std::size_t members{},pending{};
    static OwnedGuildSuccessionSemanticReceiptDraft base(const OwnedGuildSuccessionServiceDraft::State& state,unsigned opcode,unsigned slot,
        const OwnedGuildSuccessionServiceDraft::Original::Identity& target,std::string kind){
        return {std::move(kind),state.recipient.session,state.recipient.account,state.recipient.character,state.leader.guild.id,state.leader.guild.revision,
            target.account_id,target.character_id,opcode,slot,static_cast<unsigned>(target.slot),state.leader.roster.size(),state.applications.size()};
    }
    static std::optional<OwnedGuildSuccessionSemanticReceiptDraft> captured(const CombinedGuildLifecycleRuntimeDraft::Captured& item){
        return std::visit([&](const auto& plan)->std::optional<OwnedGuildSuccessionSemanticReceiptDraft>{
            using T=std::decay_t<decltype(plan)>;
            if constexpr(std::is_same_v<T,std::monostate>)return {};
            else{
                if(item.logical.size()!=2 || item.original!=std::optional{plan.publication})return {};
                if constexpr(std::is_same_v<T,CombinedGuildLifecycleRuntimeDraft::Admission::Plan>){
                    if(RecoveredGuildLeadership::decode(item.logical)!=std::optional{plan.request})return {};
                    return base(plan.publication.state,item.logical[0],plan.request.slot,plan.application.applicant,
                        plan.request.action==RecoveredGuildLeadership::Action::ApproveOrAppoint?"approve_pending":"reject_pending");
                }else if constexpr(std::is_same_v<T,CombinedGuildLifecycleRuntimeDraft::Panel::Plan>){
                    if(item.logical!=std::vector<std::uint8_t>{0x73,plan.slot})return {};
                    return base(plan.publication.state,0x73,plan.slot,plan.target,"transfer");
                }else if constexpr(std::is_same_v<T,CombinedGuildLifecycleRuntimeDraft::Removal::Plan>){
                    const auto opcode=plan.action==CombinedGuildLifecycleRuntimeDraft::Removal::Action::Leave?0x73u:0x72u;
                    if(item.logical!=std::vector<std::uint8_t>{static_cast<std::uint8_t>(opcode),plan.slot})return {};
                    return base(plan.publication.state,opcode,plan.slot,plan.target,opcode==0x73?"leave":"kick");
                }else{
                    using G=CombinedGuildLifecycleRuntimeDraft::Governance;
                    const auto opcode=plan.action==G::Action::Appoint?0x71u:plan.action==G::Action::RemoveOffice?0x72u:0x75u;
                    if(item.logical!=std::vector<std::uint8_t>{static_cast<std::uint8_t>(opcode),plan.slot})return {};
                    return base(plan.publication.state,opcode,plan.slot,plan.target,plan.action==G::Action::Appoint?"appoint":plan.action==G::Action::RemoveOffice?"remove_office":"disband");
                }
            }
        },item.intent);
    }
};
}
