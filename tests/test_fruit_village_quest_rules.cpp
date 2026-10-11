#include "game/FruitVillageQuestRules.h"
#include <iostream>
#include <stdexcept>
namespace f=god2::FruitVillageQuestRules;
namespace q=god2::InferredQuestRules;
namespace {
unsigned checks{};
void require(bool value,const char* message) {++checks;if(!value)throw std::runtime_error(message);}
q::Snapshot snapshot(const f::Descriptor& d) {
    q::Snapshot s;s.owner={71,4};s.quest_history_complete=true;s.mutation_admitted=true;
    s.role=q::Role{d.minimum_level,100,500,6,9};
    for(auto& slot:s.bag)slot=q::Slot{0,0,1,std::nullopt,"isolated owned fixture"};
    s.bag[2]=q::Slot{d.item,d.quantity-1,1,std::nullopt,"isolated collected source key"};
    s.bag[9]=q::Slot{d.item,2,1,std::nullopt,"isolated collected source key"};
    return s;
}
}
int main()try {
    const std::array<f::Descriptor,4> expected{{
        {234,2936,5098,5,3,400,1,108,110,8885,8886,8887,8888,8889,1487,8074},
        {236,2937,5091,5,10,3000,1,113,69,8890,8891,8892,8893,8894,1491,8067},
        {237,2938,5098,10,5,1500,1,69,72,8900,8901,8902,8903,8904,1493,8074},
        {238,2939,3464,20,8,2000,1,68,116,8895,8896,8897,8898,8899,1495,6801}
    }};
    require(f::descriptors.size()==4 && f::area==13 && f::scene==12 && f::kind==0,"source scope");
    for(const auto& d:expected) {
        const auto* got=f::find(d.mission_id);require(got!=nullptr,"known descriptor");
        require(got->npc_catalog==d.npc_catalog && got->source_x==d.source_x && got->source_y==d.source_y,"source NPC coordinate hints");
        require(got->idle_before==d.idle_before && got->offer==d.offer && got->incomplete==d.incomplete && got->completion==d.completion && got->idle_after==d.idle_after,"dialogue semantic join IDs");
        const auto optional=f::rule(d.mission_id);require(optional.has_value(),"known rule");const auto& r=*optional;
        require(q::validate_rule(r)==q::Error::None,"complete non-synthetic rule");
        require(r.authority.design_id=="CUSTOM-0051" && r.revision==1,"explicit custom policy");
        require(r.id.value==d.mission_id && r.id.evidence.origin==q::Origin::NativeVerified,"native journal ID");
        const auto& req=r.requirements.value->at(0);
        require(req.item.value==d.item && req.quantity.value==d.quantity,"source-backed recipe");
        require(req.item.evidence.origin==q::Origin::NativeVerified && req.quantity.evidence.origin==q::Origin::NativeVerified,"only source facts native");
        require(r.level.value==q::LevelRange{d.minimum_level,255} && r.level.evidence.origin==q::Origin::CustomInferred,"historical minimum and inferred maximum");
        require(r.rewards.experience.value==d.experience && r.rewards.reputation.value==d.reputation,"historical rewards");
        require(r.rewards.experience.evidence.origin==q::Origin::CustomInferred && r.rewards.reputation.evidence.origin==q::Origin::CustomInferred && r.rewards.experience.evidence.reference.find(f::wiki)!=std::string::npos,"external rewards never native");
        require(r.repeat.evidence.origin==q::Origin::CustomInferred && r.completed_prerequisites.value->empty() && r.completed_prerequisites.evidence.origin==q::Origin::CustomInferred,"repeat/prerequisites explicit inference");
        require(r.rewards.currency.value==0 && r.rewards.stacks.value->empty() && r.rewards.currency.evidence.origin==q::Origin::CustomInferred && r.rewards.stacks.evidence.origin==q::Origin::CustomInferred,"absence of source rewards not false native zeros");
        auto s=snapshot(d);auto accepted=q::plan_accept(r,s,s.owner);require(bool(accepted),"actual recipe accepts");
        auto submitted=q::plan_submit(r,accepted.plan->after,s.owner);require(bool(submitted),"actual recipe consumes across slots");
        const auto& after=submitted.plan->after;
        require(after.bag[2]->count==0 && after.bag[9]->count==1,"exact quantity consumed");
        require(after.role->experience==500+d.experience && after.role->reputation==7 && after.role->currency==100,"exact reward applied");
        require(q::plan_submit(r,after,s.owner).error==q::Error::AlreadyCompleted,"once-only replay");
        auto insufficient=accepted.plan->after;insufficient.bag[9]->item=0;insufficient.bag[9]->count=0;
        require(q::plan_submit(r,insufficient,s.owner).error==q::Error::InsufficientItems,"short collection rejects");
        auto low=s;low.role->level=d.minimum_level-1;
        require(q::plan_accept(r,low,s.owner).error==q::Error::Level,"historical minimum enforced");
        auto unknown=r;unknown.requirements.value->at(0).item.evidence.origin=q::Origin::Unknown;
        require(q::validate_rule(unknown)==q::Error::UnqualifiedRule,"unknown source rejected");
    }
    for(const auto id:{0u,235u,239u,65535u,0xffffffffu})require(!f::find(id) && !f::rule(id),"unknown ID cannot manufacture source-qualified rule");
    std::cout<<"PASS "<<checks<<" fruit village quest checks\n";return 0;
}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}
