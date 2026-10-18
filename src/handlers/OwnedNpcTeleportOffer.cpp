#include "handlers/OwnedNpcTeleportOffer.h"
#include <algorithm>
#include <limits>
#include <utility>

namespace god2 {
namespace {
using Service=OwnedNpcTeleportOffer;
using Reason=Service::Reason;
bool text(const std::string& value,std::size_t limit) noexcept {
    return !value.empty() && value.size()<=limit && value.find('\0')==std::string::npos;
}
bool same_source(const Service::Npc& a,const Service::Npc& b) noexcept {
    return a.instance==b.instance && a.catalog_key==b.catalog_key && a.area==b.area &&
        a.scene==b.scene && a.kind==b.kind && a.x==b.x && a.y==b.y;
}
}
struct OwnedNpcTeleportOffer::Operation {
    OwnedNpcTeleportOffer& service;
    bool entered;
    explicit Operation(OwnedNpcTeleportOffer& owner):service(owner),entered(!owner.busy_) {
        if(entered){owner.busy_=true;owner.reentered_=false;}
        else owner.reentered_=true;
    }
    ~Operation(){if(entered)service.busy_=false;}
};
OwnedNpcTeleportOffer::OwnedNpcTeleportOffer(std::shared_ptr<const Authority> authority)
    :authority_(std::move(authority)) {}

const char* OwnedNpcTeleportOffer::reason_name(Reason value) noexcept {
    switch(value) {
#define GOD2_NPC_REASON(x) case Reason::x:return #x
        GOD2_NPC_REASON(Ok);GOD2_NPC_REASON(NoDefinition);GOD2_NPC_REASON(DisabledDefinition);
        GOD2_NPC_REASON(IncompleteDefinition);GOD2_NPC_REASON(InvalidDefinition);
        GOD2_NPC_REASON(DuplicateDefinition);GOD2_NPC_REASON(DuplicateNpcBinding);
        GOD2_NPC_REASON(AuthorityUnavailable);GOD2_NPC_REASON(MenuProjectionUnavailable);
        GOD2_NPC_REASON(Reentered);GOD2_NPC_REASON(NoOffer);
        GOD2_NPC_REASON(WrongOwner);GOD2_NPC_REASON(WrongNpc);GOD2_NPC_REASON(NotReady);
        GOD2_NPC_REASON(InBattle);GOD2_NPC_REASON(TransferPending);GOD2_NPC_REASON(PositionChanged);
        GOD2_NPC_REASON(WorldChanged);GOD2_NPC_REASON(NpcChanged);GOD2_NPC_REASON(PolicyChanged);
        GOD2_NPC_REASON(PolicyDenied);GOD2_NPC_REASON(Expired);GOD2_NPC_REASON(ClockRollback);
        GOD2_NPC_REASON(WrongMenu);GOD2_NPC_REASON(WrongContext);GOD2_NPC_REASON(ChoiceNotOffered);
        GOD2_NPC_REASON(AlreadyPrepared);GOD2_NPC_REASON(TokenExhausted);
        GOD2_NPC_REASON(ClockOverflow);GOD2_NPC_REASON(Cancelled);
        GOD2_NPC_REASON(Invalidated);
#undef GOD2_NPC_REASON
    }
    return "Unknown";
}
OwnedNpcTeleportOffer::Reason OwnedNpcTeleportOffer::definition_status(const Definition& d) noexcept {
    if(!d.enabled)return Reason::DisabledDefinition;
    if(!text(d.id,128) || !d.revision || !d.policy_revision || !text(d.source_evidence,512) ||
       !text(d.condition_evidence,512) || !text(d.cost_evidence,512) ||
       d.cost_policy==CostPolicy::Unqualified || d.choices.empty())return Reason::IncompleteDefinition;
    if(d.cost_policy!=CostPolicy::ExplicitNoCost && d.cost_policy!=CostPolicy::QualifiedResources)
        return Reason::InvalidDefinition;
    if(d.source.instance>static_cast<std::uint32_t>(std::numeric_limits<std::int32_t>::max()) || d.source.instance==0xffff ||
       !d.source.catalog_key || d.source.generation || d.source.area>63 || d.source.scene>1023 ||
       d.source.kind>3 || d.source.x>=0x4000 || d.source.y>0x7fff ||
       d.lifetime<=std::chrono::seconds::zero() || d.lifetime>std::chrono::hours(24) ||
       d.interaction_range>63 || d.choices.size()>8)return Reason::InvalidDefinition;
    for(std::size_t i=0;i<d.choices.size();++i) {
        if(!text(d.choices[i].route_id,128))return Reason::IncompleteDefinition;
        for(std::size_t j=0;j<i;++j)
            if(d.choices[j].wire_value==d.choices[i].wire_value)return Reason::InvalidDefinition;
    }
    if(const auto* menu=std::get_if<DialogueMenu>(&d.menu)) {
        if(menu->mode<1 || menu->mode>4 || !menu->text_key || menu->reply_control>0x7fff)
            return Reason::InvalidDefinition;
        if(menu->mode==4) {
            if(!menu->option_count || menu->option_count>8)return Reason::InvalidDefinition;
            for(const auto& choice:d.choices)if(choice.wire_value>=menu->option_count)return Reason::InvalidDefinition;
        } else if(d.choices.size()!=1 || menu->option_count || d.choices[0].wire_value!=menu->reply_control)
            return Reason::InvalidDefinition;
    } else {
        const auto& city_menu=std::get<RecoveredTeleport::Menu>(d.menu);
        const auto count=city_menu.count_flags&0x7fu;
        if(!RecoveredTeleport::valid(city_menu) || !city_menu.message_id ||
           !count || count!=d.choices.size())return Reason::InvalidDefinition;
        for(std::size_t i=0;i<count;++i) {
            if(!city_menu.destinations[i].id)return Reason::InvalidDefinition;
            if(d.cost_policy==CostPolicy::ExplicitNoCost && city_menu.destinations[i].displayed_cost)
                return Reason::InvalidDefinition;
            for(std::size_t j=0;j<i;++j)if(city_menu.destinations[j].id==city_menu.destinations[i].id)return Reason::InvalidDefinition;
            if(std::none_of(d.choices.begin(),d.choices.end(),[&](const Choice& c){return c.wire_value==city_menu.destinations[i].id;}))
                return Reason::InvalidDefinition;
        }
    }
    return Reason::Ok;
}
OwnedNpcTeleportOffer::Reason OwnedNpcTeleportOffer::install(std::vector<Definition> rows) {
    Operation operation(*this);if(!operation.entered)return Reason::Reentered;
    if(rows.size()>4096)return Reason::InvalidDefinition; // Bounded host configuration, not a native limit.
    std::map<std::string,Definition> next;
    for(auto& row:rows) {
        if(!text(row.id,128))return Reason::InvalidDefinition;
        const auto status=definition_status(row);
        if(row.enabled && status!=Reason::Ok)return status;
        if(next.contains(row.id))return Reason::DuplicateDefinition;
        if(row.enabled)for(const auto& [id,other]:next) {
            (void)id;
            if(other.enabled && other.source.instance==row.source.instance &&
               other.source.area==row.source.area && other.source.scene==row.source.scene)
                return Reason::DuplicateNpcBinding;
        }
        const auto id=row.id;next.emplace(id,std::move(row));
    }
    definitions_.swap(next);offers_.clear();return Reason::Ok;
}
OwnedNpcTeleportOffer::Reason OwnedNpcTeleportOffer::eligible(
    const Identity& owner,const Definition& definition,const Observation& actual) noexcept {
    if(!owner.session || !owner.account || !owner.character || actual.owner!=owner)return Reason::WrongOwner;
    if(!actual.ready || !actual.position || !actual.position->revision || !actual.world_generation ||
       !actual.actor_identity)return Reason::NotReady;
    if(actual.in_battle)return Reason::InBattle;
    if(actual.transfer_pending)return Reason::TransferPending;
    if(!actual.npc.generation || !same_source(actual.npc,definition.source))return Reason::WrongNpc;
    const auto& p=*actual.position;
    if(p.area!=definition.source.area || p.scene!=definition.source.scene)return Reason::WorldChanged;
    const auto dx=int(p.x)-int(actual.npc.x),dy=int(p.y)-int(actual.npc.y);
    const auto range=int(definition.interaction_range);
    if(dx < -range || dx>range || dy < -range || dy>range)return Reason::WrongNpc;
    if(actual.policy.policy_revision!=definition.policy_revision || !actual.policy.readset_revision)
        return Reason::PolicyChanged;
    if(!actual.policy.conditions_satisfied || !actual.policy.costs_satisfied)return Reason::PolicyDenied;
    return Reason::Ok;
}
OwnedNpcTeleportOffer::Result<OwnedNpcTeleportOffer::Observation> OwnedNpcTeleportOffer::current(
    const Identity& owner,const Definition& definition) {
    if(!authority_)return {Reason::AuthorityUnavailable,{}};
    std::optional<Observation> value;
    try {value=authority_->observe(owner,definition);} catch(...) {return {Reason::AuthorityUnavailable,{}};}
    if(reentered_)return {Reason::Reentered,{}};
    if(!value)return {Reason::AuthorityUnavailable,{}};
    const auto reason=eligible(owner,definition,*value);
    if(reason!=Reason::Ok)return {reason,{}};
    return {Reason::Ok,std::move(value)};
}
bool OwnedNpcTeleportOffer::claims(std::uint64_t session,
    std::span<const RecoveredWorldRecords::Record> records,Time now) const {
    if(busy_ || !authority_)return false;
    const auto found=offers_.find(session);
    const Offer* offer=found!=offers_.end() && now>=found->second.opened && now<found->second.expires?&found->second:nullptr;
    for(const auto& record:records) {
        if(!offer)continue;
        if(const auto* close=std::get_if<RecoveredQuestClose::Request>(&record))
            if(offer->baseline.close_source_low_word && close->source_low_word==*offer->baseline.close_source_low_word)return true;
        if(const auto* reply=std::get_if<RecoveredQuestAction::Request>(&record)) {
            const auto* menu=std::get_if<DialogueMenu>(&offer->menu);
            if(menu && reply->request_word==menu->request && reply->context_byte==menu->context)return true;
        }
        if(const auto* selection=std::get_if<RecoveredTeleport::Selection>(&record)) {
            const auto* menu=std::get_if<RecoveredTeleport::Menu>(&offer->menu);
            if(menu && selection->context==menu->context &&
               selection->opcode==(RecoveredTeleport::special_context(menu->context)?0xa9:0x99))return true;
        }
    }
    return false;
}
bool OwnedNpcTeleportOffer::claims(const Identity& owner,
    std::span<const RecoveredWorldRecords::Record> records,Time now) {
    const auto issued=offers_.find(owner.session);
    if(issued!=offers_.end() && issued->second.owner==owner && claims(owner.session,records,now))return true;
    Operation operation(*this);if(!operation.entered || !authority_)return false;
    for(const auto& record:records)if(const auto* npc=std::get_if<RecoveredNpcInteraction::Request>(&record))
        for(const auto& [id,definition]:definitions_) {
            (void)id;
            if(!definition.enabled || definition.source.instance!=npc->raw_target)continue;
            const auto actual=current(owner,definition);
            // An actual matching NPC can own the explicit insufficient-cost
            // denial. Missing/foreign source or authority never steals37.
            if(actual || actual.reason==Reason::PolicyDenied)return true;
        }
    return false;
}
OwnedNpcTeleportOffer::Result<OwnedNpcTeleportOffer::Issued> OwnedNpcTeleportOffer::open(
    const Identity& owner,const RecoveredNpcInteraction::Request& request,Time now) {
    Operation operation(*this);if(!operation.entered)return {Reason::Reentered,{}};
    const auto existing=offers_.find(owner.session);
    if(existing!=offers_.end() && existing->second.owner!=owner)return {Reason::WrongOwner,{}};
    Reason unavailable=Reason::NoDefinition;
    for(const auto& [id,definition]:definitions_) {
        (void)id;
        if(definition.source.instance!=request.raw_target)continue;
        const auto status=definition_status(definition);
        if(status!=Reason::Ok){unavailable=status;continue;}
        const auto actual=current(owner,definition);
        if(!actual){
            unavailable=actual.reason;
            const auto old=offers_.find(owner.session);
            if(old!=offers_.end() && old->second.owner==owner && actual.reason!=Reason::WrongOwner)
                offers_.erase(old);
            continue;
        }
        // A qualified new37 supersedes this owner's prior conversation even
        // when constructing its replacement menu fails. Do not leave an old85
        // or Prepared usable after the client has selected a new interaction.
        const auto prior=offers_.find(owner.session);
        if(prior!=offers_.end() && prior->second.owner==owner)offers_.erase(prior);
        if(next_token_==std::numeric_limits<std::uint64_t>::max())return {Reason::TokenExhausted,{}};
        const auto duration=std::chrono::duration_cast<Clock::duration>(definition.lifetime);
        if(now>Time::max()-duration)return {Reason::ClockOverflow,{}};
        // Only publish a new offer after the complete menu is qualified.
        Issued issued{next_token_+1,definition.id,definition.menu,{}};
        if(auto* menu=std::get_if<DialogueMenu>(&issued.menu)) {
            menu->request=static_cast<std::uint16_t>(next_dialogue_request_);
            next_dialogue_request_=(next_dialogue_request_+1u)&0xffffu;
            std::optional<MenuProjection> projection;
            try {projection=authority_->project_dialogue(definition,*menu,*actual.value);}
            catch(...) {return {Reason::MenuProjectionUnavailable,{}};}
            if(reentered_)return {Reason::Reentered,{}};
            if(!projection || !text(projection->source_evidence,512))return {Reason::MenuProjectionUnavailable,{}};
            const auto& logical=projection->logical;
            const auto word=[&](std::size_t at){return std::uint16_t(logical[at]|(std::uint16_t(logical[at+1])<<8));};
            if(logical.size()<27 || logical.size()>283 || logical[0]!=0x7a ||
               std::size_t(word(1))!=logical.size() || logical[3]!=menu->mode || logical[4]!=menu->context ||
               word(5)!=menu->request || word(7)!=menu->text_key || word(9)!=menu->reply_control)
                return {Reason::MenuProjectionUnavailable,{}};
            issued.logical_menu=std::move(projection->logical);
        } else {
            auto& city_menu=std::get<RecoveredTeleport::Menu>(issued.menu);
            if(!RecoveredTeleport::special_context(city_menu.context)) {
                while(RecoveredTeleport::special_context(static_cast<std::uint16_t>(next_city_context_)) ||
                      next_city_context_==16055u)next_city_context_=(next_city_context_+1u)&0xffffu;
                city_menu.context=static_cast<std::uint16_t>(next_city_context_);
                next_city_context_=(next_city_context_+1u)&0xffffu;
            }
            const auto logical=RecoveredTeleport::encode(city_menu);
            if(!logical)return {Reason::MenuProjectionUnavailable,{}};
            issued.logical_menu.assign(logical->begin(),logical->end());
        }
        Offer offer{owner,*actual.value,definition,issued.menu,now,now+duration,next_token_+1,{}};
        offers_.insert_or_assign(owner.session,std::move(offer));++next_token_;
        return {Reason::Ok,std::move(issued)};
    }
    return {unavailable,{}};
}
OwnedNpcTeleportOffer::Reason OwnedNpcTeleportOffer::check(const Identity& owner,Time now) {
    const auto it=offers_.find(owner.session);
    if(it==offers_.end())return Reason::NoOffer;
    if(it->second.owner!=owner)return Reason::WrongOwner; // A foreign owner cannot revoke this offer.
    auto reason=Reason::Ok;
    if(now<it->second.opened)reason=Reason::ClockRollback;
    else if(now>=it->second.expires)reason=Reason::Expired;
    else {
        const auto actual=current(owner,it->second.definition);
        if(!actual)reason=actual.reason;
        else if(actual.value->world_generation!=it->second.baseline.world_generation ||
                actual.value->actor_identity!=it->second.baseline.actor_identity ||
                actual.value->close_source_low_word!=it->second.baseline.close_source_low_word)reason=Reason::WorldChanged;
        else if(actual.value->position!=it->second.baseline.position)reason=Reason::PositionChanged;
        else if(actual.value->npc!=it->second.baseline.npc)reason=Reason::NpcChanged;
        else if(actual.value->policy!=it->second.baseline.policy)reason=Reason::PolicyChanged;
    }
    if(reason!=Reason::Ok)offers_.erase(it);
    return reason;
}
OwnedNpcTeleportOffer::Result<OwnedNpcTeleportOffer::Prepared> OwnedNpcTeleportOffer::prepare(
    const Identity& owner,std::uint16_t selected) {
    auto& offer=offers_.at(owner.session);
    if(offer.prepared)return {Reason::AlreadyPrepared,{}};
    const auto found=std::find_if(offer.definition.choices.begin(),offer.definition.choices.end(),
        [selected](const Choice& choice){return choice.wire_value==selected;});
    if(found==offer.definition.choices.end())return {Reason::ChoiceNotOffered,{}};
    Prepared result{offer.token,offer.definition.id,found->route_id,*offer.baseline.position,offer.baseline.npc,
        offer.definition.revision,offer.definition.policy_revision,offer.baseline.world_generation,
        offer.baseline.npc.generation,offer.baseline.policy.readset_revision,
        offer.definition.cost_policy,offer.definition.cost_evidence};
    offer.prepared=result;return {Reason::Ok,std::move(result)};
}
OwnedNpcTeleportOffer::Result<OwnedNpcTeleportOffer::Prepared> OwnedNpcTeleportOffer::select_dialogue(
    const Identity& owner,const RecoveredQuestAction::Request& request,Time now) {
    Operation operation(*this);if(!operation.entered)return {Reason::Reentered,{}};
    const auto reason=check(owner,now);if(reason!=Reason::Ok)return {reason,{}};
    const auto* menu=std::get_if<DialogueMenu>(&offers_.at(owner.session).menu);
    if(!menu)return {Reason::WrongMenu,{}};
    if(request.request_word!=menu->request || request.context_byte!=menu->context)return {Reason::WrongContext,{}};
    return prepare(owner,request.reply_word); // opaque_tail has no authority.
}
OwnedNpcTeleportOffer::Result<OwnedNpcTeleportOffer::Prepared> OwnedNpcTeleportOffer::select_city(
    const Identity& owner,const RecoveredTeleport::Selection& request,Time now) {
    Operation operation(*this);if(!operation.entered)return {Reason::Reentered,{}};
    const auto reason=check(owner,now);if(reason!=Reason::Ok)return {reason,{}};
    const auto* menu=std::get_if<RecoveredTeleport::Menu>(&offers_.at(owner.session).menu);
    if(!menu)return {Reason::WrongMenu,{}};
    if(request.context!=menu->context ||
       request.opcode!=(RecoveredTeleport::special_context(menu->context)?0xa9:0x99))return {Reason::WrongContext,{}};
    return prepare(owner,request.destination);
}
OwnedNpcTeleportOffer::Result<OwnedNpcTeleportOffer::CostPolicy> OwnedNpcTeleportOffer::revalidate(
    const Identity& owner,const Prepared& prepared,Time now) {
    Operation operation(*this);if(!operation.entered)return {Reason::Reentered,{}};
    const auto reason=check(owner,now);if(reason!=Reason::Ok)return {reason,{}};
    const auto& offer=offers_.at(owner.session);
    if(!offer.prepared || *offer.prepared!=prepared)return {Reason::WrongContext,{}};
    return {Reason::Ok,offer.definition.cost_policy};
}
OwnedNpcTeleportOffer::Reason OwnedNpcTeleportOffer::cancel(
    const Identity& owner,const RecoveredQuestClose::Request& request,Time now) {
    Operation operation(*this);if(!operation.entered)return Reason::Reentered;
    const auto reason=check(owner,now);if(reason!=Reason::Ok)return reason;
    const auto& source=offers_.at(owner.session).baseline.close_source_low_word;
    if(!source)return Reason::AuthorityUnavailable;
    if(request.source_low_word!=*source)return Reason::WrongContext;
    offers_.erase(owner.session);return Reason::Cancelled; // high WORD is opaque.
}
OwnedNpcTeleportOffer::Reason OwnedNpcTeleportOffer::observe(const Identity& owner,Time now) {
    Operation operation(*this);if(!operation.entered)return Reason::Reentered;
    return check(owner,now);
}
bool OwnedNpcTeleportOffer::committed(std::uint64_t session,std::uint64_t token) {
    Operation operation(*this);if(!operation.entered)return false;
    const auto it=offers_.find(session);
    if(it==offers_.end() || !it->second.prepared || it->second.token!=token)return false;
    offers_.erase(it);return true;
}
void OwnedNpcTeleportOffer::forget(std::uint64_t session) {
    Operation operation(*this);if(operation.entered)offers_.erase(session);
}
bool OwnedNpcTeleportOffer::has_offer(std::uint64_t session) const noexcept {return offers_.contains(session);}
}
