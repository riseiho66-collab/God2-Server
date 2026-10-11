#pragma once
#include "NeighboringGuild53AdmissionRepositoryDraft.h"
#include "Panel53Draft.h"
#include "handlers/OwnedGuildMembershipName.h"
#include "game/OwnedGuildMembershipRule.h"
#include "protocol/RecoveredTrade.h"
#include <variant>
namespace god2 {
// PRIVATE CUSTOM0083: native8D ->6F Create0/Join1; exact qualified CUSTOM0078 Lua policy.
class GuildJoinConversation53Service {
public:
    using Repository=NeighboringGuild53AdmissionRepositoryDraft;using Panel=Panel53Draft;
    using Conversation=OwnedGuildMembershipConversation;using Wire=RecoveredGuildMembership;using Time=Conversation::Time;
    // Opaque trusted server interaction fingerprint. Native selected_actor_hint never supplies it.
    struct Interaction {Panel::Owner owner;std::uint64_t service_id{},service_revision{},interaction_revision{};bool operator==(const Interaction&)const=default;};
    struct CreationLease {Repository::Original::Wallet wallet;OwnedGuildMembershipInput input;OwnedGuildMembershipPolicy policy;bool operator==(const CreationLease& o)const{return wallet==o.wallet && input.level==o.input.level && input.wallet==o.input.wallet && policy==o.policy;}};
    struct Opening {Interaction interaction;Repository::Original::Identity actor;CharacterResources resources;Wire::Prompt prompt;Time opened,expires;std::optional<CreationLease> creation;bool operator==(const Opening&)const=default;};
    struct Plan {Opening original;Wire::Request request;std::optional<Repository::Succession::EffectiveLeader> target;std::vector<Repository::Original::Application> applications;Panel::Audience audience;std::string name;std::optional<Repository::CreationSnapshot> catalog;bool operator==(const Plan&)const=default;};
    using Resolve=std::function<std::optional<Interaction>(std::uint64_t)>;
    using ActorReady=std::function<bool(const Panel::Owner&)>;
    using Capture=std::function<std::optional<Panel::Audience>(const Repository::Succession::EffectiveLeader&,const std::vector<Repository::Original::Application>&,const Repository::Original::Identity&)>;
    using Preflight=std::function<bool(const Panel::Audience&)>;
    using ReadWallet=std::function<std::optional<Repository::Original::Wallet>(std::uint64_t,std::uint64_t)>;
    using Rule=std::function<OwnedGuildMembershipPolicy(const OwnedGuildMembershipInput&)>;
    using CaptureCreate=std::function<std::optional<Panel::Audience>(const Repository::Original::Identity&)>;
    using Result=std::variant<Repository::Original::Application,Repository::Created53>;
    using Current=std::function<bool(const Panel::Audience&)>; // Pure world only; safe after SQL writes.
    GuildJoinConversation53Service(Repository& repository,Repository::Original& original,Repository::Succession& effective,SqliteRecoveredCharacterRepository& profiles,
        Resolve resolve,ActorReady actor_ready,Capture capture,Preflight preflight,Current current,ReadWallet wallet={},Rule rule={},CaptureCreate capture_create={}):repository_(repository),original_(original),effective_(effective),profiles_(profiles),
        resolve_(std::move(resolve)),actor_ready_(std::move(actor_ready)),capture_(std::move(capture)),preflight_(std::move(preflight)),current_(std::move(current)),conversations_(OwnedGuildMembershipName::valid),wallet_(std::move(wallet)),rule_(std::move(rule)),capture_create_(std::move(capture_create)){}
    std::optional<Opening> prepare_join(std::uint64_t session,Time now){return prepare_operation(session,Wire::Operation::Join,now);}
    std::optional<Opening> prepare_create(std::uint64_t session,Time now){return prepare_operation(session,Wire::Operation::Create,now);}
    std::optional<Opening> prepare_operation(std::uint64_t session,Wire::Operation operation,Time now){
        try{if(!resolve_ || !actor_ready_ || !capture_ || !preflight_ || !current_ || now>Time::max()-Conversation::lifetime)return {};
            const auto interaction=resolve_(session);if(!interaction || interaction->owner.session!=session || !valid(*interaction) || !actor_ready_(interaction->owner))return {};
            const auto actor=original_.nonmember(interaction->owner.account,interaction->owner.character);if(original_.pending(actor.account_id,actor.character_id))return {};
            const auto resource=profiles_.load_resources(actor.account_id,actor.character_id);if(!resource)return {};
            std::optional<CreationLease> creation;
            if(operation==Wire::Operation::Create){if(!wallet_ || !rule_ || !capture_create_ || !actor.role)return {};const auto wallet=wallet_(actor.account_id,actor.character_id);const auto role=RecoveredRoleLevel::parse(actor.role->logical);if(!wallet || !role || !role->level())return {};
                // The neighboring53 host also returns legacy27 after SQL.
                // An extended shared balance cannot enter this legacy lease.
                if(!RecoveredTrade::wallet_amount_representable(wallet->amount))return {};
                const OwnedGuildMembershipInput input{role->level(),wallet->amount};const auto policy=rule_(input);if(!policy.may_create)return {};creation=CreationLease{*wallet,input,policy};}
            if(resolve_(session)!=interaction)return {};const auto prompt=conversations_.open(interaction->owner,operation,now,true);if(!prompt)return {};
            Opening opening{*interaction,actor,*resource,*prompt,now,now+Conversation::lifetime,creation};prepared_.insert_or_assign(session,opening);return opening;
        }catch(...){return {};}
    }
    // Trusted host calls only after EXACT8D logical response is accepted into current world tail.
    bool published(const Opening& opening,Time now){
        const auto session=opening.interaction.owner.session;
        try{const auto at=prepared_.find(session);if(at==prepared_.end() || at->second!=opening || !opening_current(opening,now) || !actor_ready_ || !actor_ready_(opening.interaction.owner))return false;
            if(prepared_.find(session)==prepared_.end() || prepared_.at(session)!=opening || !opening_current(opening,now))return false;
            prepared_.erase(session);published_.insert_or_assign(session,opening);return true;
        }catch(...){return false;}
    }
    std::optional<Opening> opening(std::uint64_t session)const{const auto at=published_.find(session);return at==published_.end()?std::nullopt:std::optional{at->second};}
    std::optional<Plan> capture_before_prefix(const Opening& opening,const Wire::Request& request,Time now)const{
        try{const auto session=opening.interaction.owner.session;if(this->opening(session)!=std::optional{opening} || !bound(opening,request) || !opening_current(opening,now) || !actor_ready_ || !actor_ready_(opening.interaction.owner))return {};
            const auto field=Wire::canonical(request);if(!field || !OwnedGuildMembershipName::valid(*field,opening.interaction.owner.name_codepage))return {};
            const auto name=OwnedGuildMembershipName::decode(*field,opening.interaction.owner.name_codepage);
            if(opening.creation){const auto audience=capture_create_(opening.actor);if(!audience || !complete_create(*audience,opening.actor,opening.resources) || !preflight_(*audience))return {};const auto catalog=repository_.creation_snapshot();
                if(this->opening(session)!=std::optional{opening} || !opening_current(opening,now) || !current_(*audience))return {};return Plan{opening,request,{}, {},*audience,name,catalog};}
            const auto selected=effective_.find_by_name(name);if(!selected)return {};
            const auto target=effective_.effective_snapshot(selected->id);const auto apps=effective_.applications(selected->id);
            const auto audience=capture_(target,apps,opening.actor);if(!audience || !complete(*audience,opening.actor,opening.resources,target,apps) || !preflight_(*audience))return {};
            if(this->opening(session)!=std::optional{opening} || !opening_current(opening,now) || effective_.effective_snapshot(selected->id)!=target || effective_.applications(selected->id)!=apps || !current_(*audience))return {};
            return Plan{opening,request,target,apps,*audience,name,{}};
        }catch(...){return {};}
    }
    std::optional<Result> execute(const Plan& plan,Time now){
        const auto session=plan.original.interaction.owner.session;
        try{if(opening(session)!=std::optional{plan.original})return {};
            // Mandatory projection/world preflight BEFORE any repository transaction.
            const auto field=Wire::canonical(plan.request);
            const auto name=field?OwnedGuildMembershipName::decode(*field,plan.original.interaction.owner.name_codepage):std::string{};
            bool exact=bound(plan.original,plan.request) && name==plan.name && opening_current(plan.original,now);
            if(plan.original.creation)exact=exact && !plan.target && plan.applications.empty() && plan.catalog && repository_.creation_snapshot()==*plan.catalog && complete_create(plan.audience,plan.original.actor,plan.original.resources);
            else {const auto selected=effective_.find_by_name(name);exact=exact && plan.target && !plan.catalog && selected && *selected==plan.target->guild && effective_.effective_snapshot(plan.target->guild.id)==*plan.target && effective_.applications(plan.target->guild.id)==plan.applications && complete(plan.audience,plan.original.actor,plan.original.resources,*plan.target,plan.applications);}
            if(!exact || !actor_ready_ || !actor_ready_(plan.original.interaction.owner) || !preflight_ || !preflight_(plan.audience) || !current_ || !current_(plan.audience)){
                reject_exact(plan.original,plan.request);return {};}
            if(opening(session)!=std::optional{plan.original})return {};
            const auto accepted=conversations_.consume(plan.original.interaction.owner,plan.request,now,true);
            if(!accepted){reject_exact(plan.original,plan.request);return {};}
            published_.erase(session);consumed_.insert_or_assign(session,plan);
            const auto proof=[&](bool after){const auto at=consumed_.find(session);if(at==consumed_.end() || at->second!=plan || !resolve_ || resolve_(session)!=std::optional{plan.original.interaction} ||
                    !current_ || !current_(plan.audience) ||
                    consumed_.find(session)==consumed_.end() || consumed_.at(session)!=plan || resolve_(session)!=std::optional{plan.original.interaction})throw DatabaseError("Join immutable original conversation/world/resources lease changed");};
            const Repository::Original::Proof paired{[&]{proof(false);},[&]{proof(true);}};
            if(plan.original.creation){const auto& creation=*plan.original.creation;const Repository::Original::Policy policy{creation.policy.creation_fee,creation.policy.minimum_level,creation.policy.initial_capacity};
                const auto& owner=plan.original.interaction.owner;
                const RelationsRepositoryDraft::Authority authority{owner.session,owner.account,owner.character,owner.world_generation,owner.position_revision,owner.battle_generation,
                    plan.original.interaction.interaction_revision,owner.name_codepage,plan.original.actor.slot,false};
                const auto result=repository_.create53(plan.original.actor,creation.wallet,plan.name,policy,*plan.catalog,paired,authority);consumed_.erase(session);return Result{result};}
            const auto result=repository_.apply(plan.original.actor,*plan.target,plan.applications,paired);consumed_.erase(session);return Result{result};
        }catch(...){const auto at=consumed_.find(session);if(at!=consumed_.end() && at->second==plan)consumed_.erase(at);reject_exact(plan.original,plan.request);return {};}
    }
    // A matching bound rejected attempt consumes ONLY this original opening, never a newer nonce.
    void reject_exact(const Opening& opening,const Wire::Request& request){const auto session=opening.interaction.owner.session;
        const auto at=published_.find(session);if(at!=published_.end() && at->second==opening && bound(opening,request)){published_.erase(at);conversations_.invalidate(session);}}
    void invalidate(std::uint64_t session){prepared_.erase(session);published_.erase(session);conversations_.invalidate(session);}
private:
    static bool valid(const Interaction& value){const auto& o=value.owner;return value.service_id && value.service_revision && value.interaction_revision && o.session && o.account && o.character && o.world_generation && o.position_revision && (o.name_codepage==950 || o.name_codepage==936);}
    static bool bound(const Opening& opening,const Wire::Request& request){return static_cast<std::uint8_t>(request.operation)==opening.prompt[3] && request.context==static_cast<std::uint16_t>(opening.prompt[1]|(std::uint16_t{opening.prompt[2]}<<8));}
    bool opening_current(const Opening& opening,Time now)const{return now>=opening.opened && now<opening.expires && resolve_ && resolve_(opening.interaction.owner.session)==std::optional{opening.interaction} &&
        original_.nonmember(opening.actor.account_id,opening.actor.character_id)==opening.actor && !original_.pending(opening.actor.account_id,opening.actor.character_id) && profiles_.load_resources(opening.actor.account_id,opening.actor.character_id)==std::optional{opening.resources} && creation_proof(opening,false);}
    bool creation_proof(const Opening& opening,bool after)const{if(!opening.creation)return true;const auto& creation=*opening.creation;if(!wallet_ || !rule_ || rule_(creation.input)!=creation.policy)return false;
        const Repository::Original::Wallet expected{after?creation.wallet.amount-creation.policy.creation_fee:creation.wallet.amount,creation.wallet.revision+(after?1:0)};return wallet_(opening.actor.account_id,opening.actor.character_id)==std::optional{expected};}
    static bool complete_create(const Panel::Audience& audience,const Repository::Original::Identity& actor,const CharacterResources& resource){if(audience.resources.size()!=1 || !audience.resources.contains(actor.character_id) || audience.resources.at(actor.character_id)!=resource)return false;
        std::uint64_t previous=0;bool found=false;for(const auto& owner:audience.connected){if(owner.session<=previous || owner.character!=actor.character_id || owner.account!=actor.account_id)return false;previous=owner.session;found=true;}return found;}
    static bool complete(const Panel::Audience& audience,const Repository::Original::Identity& actor,const CharacterResources& resource,
        const Repository::Succession::EffectiveLeader& target,const std::vector<Repository::Original::Application>& apps){
        std::map<std::uint64_t,std::uint64_t> identities;for(const auto& row:target.roster)if(!identities.emplace(row.character_id,row.account_id).second)return false;
        for(const auto& app:apps)if(!identities.emplace(app.applicant.character_id,app.applicant.account_id).second)return false;
        if(!identities.emplace(actor.character_id,actor.account_id).second || audience.resources.size()!=identities.size())return false;
        const auto at=audience.resources.find(actor.character_id);if(at==audience.resources.end() || at->second!=resource)return false;
        for(const auto& [character,account]:identities)if(!audience.resources.contains(character))return false;
        std::uint64_t previous=0;bool found=false;for(const auto& owner:audience.connected){const auto who=identities.find(owner.character);if(owner.session<=previous || who==identities.end() || who->second!=owner.account)return false;previous=owner.session;if(owner.account==actor.account_id && owner.character==actor.character_id)found=true;}
        return found;
    }
    bool resources_current(const Panel::Audience& audience,const std::optional<Repository::Succession::EffectiveLeader>& target,const std::vector<Repository::Original::Application>& apps,const Repository::Original::Identity& actor)const{
        const auto match=[&](const auto& row){return profiles_.load_resources(row.account_id,row.character_id)==std::optional{audience.resources.at(row.character_id)};};
        if(!match(actor))return false;if(target)for(const auto& row:target->roster)if(!match(row))return false;for(const auto& app:apps)if(!match(app.applicant))return false;return true;
    }
    Repository& repository_;Repository::Original& original_;Repository::Succession& effective_;SqliteRecoveredCharacterRepository& profiles_;
    Resolve resolve_;ActorReady actor_ready_;Capture capture_;Preflight preflight_;Current current_;Conversation conversations_;
    ReadWallet wallet_;Rule rule_;CaptureCreate capture_create_;
    std::map<std::uint64_t,Opening> prepared_,published_;std::map<std::uint64_t,Plan> consumed_;
};
class GuildJoinConversation53Runtime {
public:
    using Service=GuildJoinConversation53Service;using Indexed=founder_transfer_contract_draft::IndexedLogical;
    struct Captured{std::size_t index{};Service::Wire::Request request;std::optional<Service::Opening> original;std::optional<Service::Plan> plan;};
    struct Batch{bool structurally_valid{};std::vector<Captured> actions;};
    explicit GuildJoinConversation53Runtime(Service& service):service_(service){}
    Batch capture_before_any_prefix(std::uint64_t session,std::span<const Indexed> records,Service::Time now)const{
        std::vector<Service::Wire::Request> decoded;std::size_t previous=0;bool first=true;
        for(const auto& item:records){if(!first && item.index<=previous)return {};first=false;previous=item.index;const auto wire=Service::Wire::decode(item.logical);if(!wire)return {};decoded.push_back(*wire);}
        const auto original=service_.opening(session);Batch out{true,{}};
        for(std::size_t i=0;i<records.size();++i)out.actions.push_back({records[i].index,decoded[i],original,original?service_.capture_before_prefix(*original,decoded[i],now):std::nullopt});return out;
    }
    std::optional<Service::Result> execute(const Captured& item,Service::Time now){if(item.plan && item.original==std::optional{item.plan->original} && item.request==item.plan->request)return service_.execute(*item.plan,now);
        if(item.original)service_.reject_exact(*item.original,item.request);return {};}
private:Service& service_;
};
using GuildMembershipConversation53Service=GuildJoinConversation53Service;
using GuildMembershipConversation53Runtime=GuildJoinConversation53Runtime;
}
