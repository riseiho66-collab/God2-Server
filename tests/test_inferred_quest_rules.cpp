#include "game/InferredQuestRules.h"
#include <iostream>
#include <stdexcept>
#include <string>

namespace q=god2::InferredQuestRules;
namespace {
q::Result isolated_accept(const q::Rule& r,const q::Snapshot& s,q::Owner owner) {
    return q::plan_accept(r,s,owner,q::Evaluation::IsolatedSyntheticTest);
}
q::Result isolated_submit(const q::Rule& r,const q::Snapshot& s,q::Owner owner) {
    return q::plan_submit(r,s,owner,q::Evaluation::IsolatedSyntheticTest);
}
bool isolated_revalidate(const q::Rule& r,const q::Snapshot& s,const q::Plan& p) {
    return q::revalidate(r,s,p,q::Evaluation::IsolatedSyntheticTest);
}
unsigned checks{};
void require(bool value,const char* message) {
    ++checks;if(!value)throw std::runtime_error(message);
}
template<class T> q::Fact<T> fact(T value) {
    return {std::move(value),{q::Origin::SyntheticTest,"synthetic unit fixture; no original value"}};
}
q::Instance instance(std::uint16_t id,std::uint8_t tail) {
    q::Instance value{};value[0]=static_cast<std::uint8_t>(id);value[1]=static_cast<std::uint8_t>(id>>8);
    for(std::size_t i=2;i<value.size();++i)value[i]=static_cast<std::uint8_t>(tail+i);
    return value;
}
q::Rule rule() {
    q::Rule r;
    r.authority={"CUSTOM-0051","synthetic tests only"};r.id=fact<q::QuestId>(900001);r.revision=3;
    r.level=fact(q::LevelRange{8,40});r.completed_prerequisites=fact(std::vector<q::QuestId>{900000});
    r.repeat=fact(q::Repeat::Once);r.collect_objective_complete=fact(true);
    r.requirements=fact(std::vector<q::Requirement>{
        {fact<std::uint16_t>(60001),fact<std::uint32_t>(5),fact(true),fact(q::Match{})}});
    r.rewards.currency=fact<std::uint64_t>(17);r.rewards.experience=fact<std::uint64_t>(0);r.rewards.reputation=fact<std::uint64_t>(0);
    r.rewards.stacks=fact(std::vector<q::RewardStack>{{fact(instance(60002,0xb0)),fact<std::uint32_t>(2)}});
    return r;
}
q::Snapshot snapshot() {
    q::Snapshot s;s.owner={71,4};s.quest_history_complete=true;s.mutation_admitted=true;
    s.role=q::Role{10,100,500,6,9};
    s.quests.emplace(900000,q::Progress{q::Phase::Completed,8,1,"CUSTOM-0051",1});
    for(auto& row:s.bag)row=q::Slot{0,0,7,std::nullopt,"owned synthetic empty"};
    s.bag[2]=q::Slot{60001,3,11,std::nullopt,"owned synthetic source A"};
    s.bag[9]=q::Slot{60001,4,21,std::nullopt,"owned synthetic source B"};
    s.bag[15]=q::Slot{60001,50,5,instance(60001,0x10),"protected full instance"};
    return s;
}
q::Snapshot accepted(const q::Rule& r,const q::Snapshot& s) {
    const auto p=isolated_accept(r,s,s.owner);require(bool(p),"accept fixture");return p.plan->after;
}
void error(q::Error expected,const q::Result& got) {
    require(!got && !got.plan && got.error==expected,"wrong rejection/no partial plan");
}
}
int main() {
    try {
        auto r=rule();auto s=snapshot();const auto original=s;
        error(q::Error::UnqualifiedRule,q::plan_accept(r,s,s.owner));
        const auto acceptance=isolated_accept(r,s,s.owner);
        require(bool(acceptance),"accept");require(s==original,"pure accept");
        const auto& a=*acceptance.plan;
        require(a.after.quests.at(900001).phase==q::Phase::Accepted,"accepted phase");
        require(a.after.bag==s.bag && a.after.role==s.role,"accept grants nothing");
        require(a.exact_rewards==q::Rewards{},"accept emits no reward payload");
        require(isolated_revalidate(r,s,a),"accept revalidate");
        error(q::Error::NotAccepted,isolated_submit(r,s,s.owner));
        s=a.after;const auto before=s;
        error(q::Error::AlreadyAccepted,isolated_accept(r,s,s.owner));
        const auto submit=isolated_submit(r,s,s.owner);require(bool(submit),"submit");
        const auto& p=*submit.plan;require(s==before,"pure submit");
        require(p.exact_rewards==r.rewards,"exact reward provenance and bytes");
        require(p.after.quests.at(900001).phase==q::Phase::Completed &&
                p.after.quests.at(900001).revision==2 && p.after.quests.at(900001).completions==1,"completion once");
        require(p.after.bag[2]->item==0 && p.after.bag[2]->count==0 && p.after.bag[2]->revision==12,"first stack debit");
        require(p.after.bag[9]->count==2 && p.after.bag[9]->revision==22,"second stack partial debit");
        require(p.after.bag[0]->instance==std::optional{instance(60002,0xb0)} &&
                p.after.bag[0]->count==2 && p.after.bag[0]->revision==8,"lowest explicit empty exact reward");
        require(p.after.bag[15]==s.bag[15],"scalar matcher preserves full instance overlay");
        require(p.after.role->currency==117 && p.after.role->experience==500 &&
                p.after.role->revision==10 && p.after.role->level==10,"exact balances; no invented growth");
        error(q::Error::AlreadyCompleted,isolated_submit(r,p.after,p.after.owner));
        error(q::Error::AlreadyCompleted,isolated_accept(r,p.after,p.after.owner));
        require(isolated_revalidate(r,s,p),"submit revalidate");
        require(!q::revalidate(r,s,p),"default mode refuses synthetic plan");
        // Every part of the read set is protected, including untouched rows.
        {auto changed=s;++changed.bag[29]->revision;require(!isolated_revalidate(r,changed,p),"untouched-row CAS");}
        {auto changed=s;++changed.role->revision;require(!isolated_revalidate(r,changed,p),"role CAS");}
        {auto changed=s;++changed.quests.at(900000).revision;require(!isolated_revalidate(r,changed,p),"prerequisite CAS");}
        {auto changed=s;++changed.quests.at(900001).revision;require(!isolated_revalidate(r,changed,p),"quest CAS");}
        {auto changed=s;++changed.owner.account;require(!isolated_revalidate(r,changed,p),"owner CAS");}
        {auto changed=p;++changed.after.role->currency;require(!isolated_revalidate(r,s,changed),"tampered reward plan");}
        {auto changed=r;++*changed.rewards.currency.value;require(!isolated_revalidate(changed,s,p),"changed reward rule");}
        {auto changed=r;++changed.revision;error(q::Error::RuleChanged,isolated_submit(changed,s,s.owner));}
        {auto changed=s;changed.quests.at(900001).design_id="CUSTOM-9998";error(q::Error::RuleChanged,isolated_submit(r,changed,changed.owner));}
        error(q::Error::WrongOwner,isolated_submit(r,s,{72,4}));
        error(q::Error::WrongOwner,isolated_submit(r,s,{71,5}));
        {auto changed=s;changed.quest_history_complete=false;error(q::Error::IncompleteSnapshot,isolated_submit(r,changed,changed.owner));}
        {auto changed=s;changed.role.reset();error(q::Error::IncompleteSnapshot,isolated_submit(r,changed,changed.owner));}
        {auto changed=s;changed.mutation_admitted=false;error(q::Error::MutationNotAdmitted,isolated_submit(r,changed,changed.owner));}
        {auto changed=s;changed.role->level=7;error(q::Error::Level,isolated_submit(r,changed,changed.owner));}
        {auto changed=s;changed.role->level=41;error(q::Error::Level,isolated_submit(r,changed,changed.owner));}
        {auto changed=s;changed.quests.erase(900000);error(q::Error::Prerequisite,isolated_submit(r,changed,changed.owner));}
        {auto changed=s;changed.quests.at(900000).phase=q::Phase::Accepted;changed.quests.at(900000).completions=0;
         error(q::Error::Prerequisite,isolated_submit(r,changed,changed.owner));}
        {auto changed=s;changed.bag[29].reset();error(q::Error::MissingBagRows,isolated_submit(r,changed,changed.owner));}
        {auto changed=s;changed.bag[9]->count=1;error(q::Error::InsufficientItems,isolated_submit(r,changed,changed.owner));}
        {auto changed=s;changed.bag[9]->count=0;error(q::Error::InvalidSnapshot,isolated_submit(r,changed,changed.owner));}
        {auto changed=s;changed.bag[9]->revision=0;error(q::Error::InvalidSnapshot,isolated_submit(r,changed,changed.owner));}
        {auto changed=s;changed.bag[9]->count=128;error(q::Error::InvalidSnapshot,isolated_submit(r,changed,changed.owner));}
        {auto changed=s;changed.bag[15]->instance=instance(60000,0);error(q::Error::InvalidSnapshot,isolated_submit(r,changed,changed.owner));}
        {auto changed=r;changed.level.evidence.origin=static_cast<q::Origin>(255);
         error(q::Error::UnqualifiedRule,isolated_submit(changed,s,s.owner));}
        // Unknown must not become explicit zero/no-op/completed.
        {auto changed=r;changed.collect_objective_complete=fact(false);error(q::Error::UnqualifiedRule,isolated_submit(changed,s,s.owner));}
        {auto changed=r;changed.rewards.experience.value.reset();error(q::Error::UnqualifiedRule,isolated_submit(changed,s,s.owner));}
        {auto changed=r;changed.rewards.stacks.value.reset();error(q::Error::UnqualifiedRule,isolated_submit(changed,s,s.owner));}
        {auto changed=r;changed.requirements.value->at(0).consume.value.reset();error(q::Error::UnqualifiedRule,isolated_submit(changed,s,s.owner));}
        {auto changed=r;changed.level.evidence.origin=q::Origin::Unknown;error(q::Error::UnqualifiedRule,isolated_submit(changed,s,s.owner));}
        {auto changed=r;changed.completed_prerequisites.evidence.reference.clear();error(q::Error::UnqualifiedRule,isolated_submit(changed,s,s.owner));}
        {auto changed=r;changed.authority.design_id="NATIVE";error(q::Error::UnqualifiedRule,isolated_submit(changed,s,s.owner));}
        {auto changed=r;changed.rewards.stacks.value->at(0).instance.value.reset();error(q::Error::UnqualifiedRule,isolated_submit(changed,s,s.owner));}
        {auto changed=r;changed.requirements.value->push_back(changed.requirements.value->at(0));error(q::Error::InvalidRule,isolated_submit(changed,s,s.owner));}
        {auto changed=r;changed.completed_prerequisites.value->push_back(*changed.id.value);error(q::Error::InvalidRule,isolated_submit(changed,s,s.owner));}
        {auto changed=r;changed.requirements.value->at(0).quantity=fact<std::uint32_t>(0);error(q::Error::InvalidRule,isolated_submit(changed,s,s.owner));}
        {auto changed=r;changed.rewards.stacks.value->at(0).count=fact<std::uint32_t>(128);error(q::Error::InvalidRule,isolated_submit(changed,s,s.owner));}
        // Exact instance matching preserves all opaque bytes and does not fall
        // back to a template key when a server-owned instance differs.
        {auto exact=r;auto& req=exact.requirements.value->at(0);
         req.match=fact(q::Match{q::MatchKind::ExactInstance,instance(60001,0x10)});
         req.quantity=fact<std::uint32_t>(49);auto got=isolated_submit(exact,s,s.owner);require(bool(got),"exact instance accepted");
         require(got.plan->after.bag[15]->count==1 && got.plan->after.bag[15]->instance==s.bag[15]->instance,"opaque retained on partial debit");
         require(got.plan->after.bag[2]==s.bag[2] && got.plan->after.bag[9]==s.bag[9],"exact selector skips scalars");
         req.match.value->instance[19]^=1;error(q::Error::InsufficientItems,isolated_submit(exact,s,s.owner));}
        {auto possess=r;possess.requirements.value->at(0).consume=fact(false);
         auto got=isolated_submit(possess,s,s.owner);require(bool(got),"explicit possession-only objective");
         require(got.plan->after.bag[2]==s.bag[2] && got.plan->after.bag[9]==s.bag[9],"possession does not debit");}
        // Plan cannot partially consume when reward capacity is unavailable.
        {auto full=s;for(auto& row:full.bag)row=q::Slot{61000,1,7,instance(61000,0x20),"owned fixture"};
         full.bag[2]=q::Slot{60001,6,11,std::nullopt,"owned scalar"};const auto saved=full;
         error(q::Error::RewardCapacity,isolated_submit(r,full,full.owner));require(full==saved,"full-bag failure is pure");
         full.bag[2]->count=5;auto got=isolated_submit(r,full,full.owner);require(bool(got),"freed material slot accepts reward");
         require(got.plan->after.bag[2]->instance==std::optional{instance(60002,0xb0)} &&
                 got.plan->after.bag[2]->revision==12,"one revision for debit-and-reward same slot");}
        {auto changed=s;changed.role->currency=q::max_revision-16;error(q::Error::Overflow,isolated_submit(r,changed,changed.owner));}
        {auto changed=s;changed.role->revision=q::max_revision;error(q::Error::Overflow,isolated_submit(r,changed,changed.owner));}
        {auto changed=s;changed.bag[2]->revision=q::max_revision;error(q::Error::Overflow,isolated_submit(r,changed,changed.owner));}
        {auto changed=s;changed.quests.at(900001).revision=q::max_revision;error(q::Error::Overflow,isolated_submit(r,changed,changed.owner));}
        {auto zero=r;zero.rewards.currency=fact<std::uint64_t>(0);zero.rewards.stacks=fact(std::vector<q::RewardStack>{});
         auto got=isolated_submit(zero,s,s.owner);require(bool(got),"explicit zero rewards");
         require(got.plan->after.role==s.role,"zero reward preserves resource revision");}
        // Four synthetic collection recipes exercising reputation-only payout;
        // their IDs, materials and counts are not claimed to be original quests.
        for(std::uint32_t index=0;index<4;++index) {
            auto reputation=r;reputation.id=fact<q::QuestId>(910001+index);
            reputation.rewards.currency=fact<std::uint64_t>(0);
            reputation.rewards.experience=fact<std::uint64_t>(0);
            reputation.rewards.reputation=fact<std::uint64_t>(1);
            reputation.rewards.stacks=fact(std::vector<q::RewardStack>{});
            auto state=accepted(reputation,snapshot());
            auto got=isolated_submit(reputation,state,state.owner);require(bool(got),"reputation-only submit");
            require(got.plan->after.role->reputation==7 && got.plan->after.role->revision==10 &&
                    got.plan->after.role->currency==100 && got.plan->after.role->experience==500,"exact reputation reward");
            require(got.plan->after.bag[0]==state.bag[0],"no invented item reward");
            require(*got.plan->exact_rewards.reputation.value==1,"reputation payload retained");
            auto overflow=state;overflow.role->reputation=q::max_revision;
            error(q::Error::Overflow,isolated_submit(reputation,overflow,overflow.owner));
            reputation.rewards.reputation.value.reset();
            error(q::Error::UnqualifiedRule,isolated_submit(reputation,state,state.owner));
        }
        std::cout<<"inferred quest rules: "<<checks<<" checks PASS (synthetic only)\n";
        return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
