#include "game/OwnedTaiwanInitialActorSceneSource.h"
#include "game/SharedNativeActorNameSource.h"
#include "protocol/RecoveredTaiwanServerRecords.h"
#include <algorithm>
#include <array>
#include <set>
#include <span>
#include <stdexcept>
#include <thread>
#include <type_traits>
#include <utility>

namespace god2 {
namespace {
using Entered=SharedTaiwanWorldEntered;
using Visibility=cn::SharedActorVisibility;
using Profiles=TaiwanCustomFullActorProfile;
using Input=Profiles::SavedInput;
using Lease=SharedWorldPresence::Lease;
using Role=OwnedTaiwanPkReturnRoleTextSource::Observation;
template<class A,class B> bool same_owner(const std::shared_ptr<A>& a,const std::shared_ptr<B>& b) noexcept {
    return a.get()==b.get()&&!a.owner_before(b)&&!b.owner_before(a);
}
bool same_scope(const Entered::Scope& a,const Entered::Scope& b) noexcept {
    return a.lease==b.lease&&a.entry.wire==b.entry.wire&&a.entry.logical==b.entry.logical&&
        a.entry.actor_handle==b.entry.actor_handle&&a.entry.area==b.entry.area&&a.entry.scene==b.entry.scene&&
        a.entry.x==b.entry.x&&a.entry.y==b.entry.y&&a.entry.kind==b.entry.kind&&
        a.tail_language==b.tail_language&&a.population==b.population&&
        same_owner(a.actor_input,b.actor_input)&&same_owner(a.actor_endpoints,b.actor_endpoints);
}
Profiles::Check profile_check(Entered::Check check) noexcept {
    return check==Entered::Check::AfterSupply?Profiles::Check::Prepare:Profiles::Check::Retained;
}
static_assert(std::is_nothrow_move_constructible_v<Entered::Native>);
}
struct OwnedTaiwanInitialActorSceneSource::Owner {
    const std::shared_ptr<SharedWorldPresence> presence;
    const std::shared_ptr<Profiles> profiles;
    const OwnedTaiwanPkReturnSceneSource::MaterialSources material;
    const Entered::Source genuine;
    const std::thread::id thread=std::this_thread::get_id();
    bool supplying=false,poisoned=false;
    Owner(std::shared_ptr<SharedWorldPresence> p,std::shared_ptr<Profiles> f,
            OwnedTaiwanPkReturnSceneSource::MaterialSources m,Entered::Source source)
        :presence(std::move(p)),profiles(std::move(f)),material(std::move(m)),genuine(std::move(source)){}
};
struct OwnedTaiwanInitialActorSceneSource::State {
    struct Actor {
        const std::size_t row;
        const Lease source,recipient;
        const Profiles::Equipment equipment;
        const Profiles::ResourceInput resources;
        const Profiles::StatusInput status;
        const Role role;
        const RecoveredRemoteActor::LogicalRecord spawn;
        const RecoveredRemoteActorMove::LogicalRecord movement;
        const RecoveredRemoteActorRemove::LogicalRecord removal;
        const TaiwanActorStatusPublication::ActorUnit unit;
        Actor(std::size_t index,const Profiles::Profile& profile,TaiwanActorStatusPublication::ActorUnit publication)
            :row(index),source(profile.source()),recipient(profile.recipient()),equipment(profile.equipment()),resources(profile.resources()),
             status(profile.status()),role(profile.role_text()),spawn(RecoveredRemoteActor::encode_logical(profile.spawn())),
             movement(RecoveredRemoteActorMove::encode_logical(profile.movement())),
             removal(RecoveredRemoteActorRemove::encode_logical(profile.removal())),unit(std::move(publication)){}
    };
    struct FrozenOutward {
        const std::vector<Actor> actors;
        const std::vector<Role> roles;
        const std::vector<Profiles::Equipment> equipment;
        FrozenOutward(std::vector<Actor> a,std::vector<Role> r,std::vector<Profiles::Equipment> e)
            :actors(std::move(a)),roles(std::move(r)),equipment(std::move(e)){}
    };
    const std::shared_ptr<Owner> owner;
    const Entered::Scope scope;
    const std::weak_ptr<Session> connection;
    // Original material is never mutated to callbacks capturing this State.
    std::shared_ptr<const Entered::Native> original;
    std::vector<Actor> actors;
    std::vector<Role> roles;
    std::vector<Profiles::Equipment> equipment;
    bool cancelled=false,cleaned=false,running=false,installed=false;
    bool released=false,outward_started=false;
    std::shared_ptr<const FrozenOutward> outward;
    State(std::shared_ptr<Owner> actual,Entered::Scope input,Session& session)
        :owner(std::move(actual)),scope(std::move(input)),connection(session.weak_from_this()){}
    ~State() {
        if(owner->thread!=std::this_thread::get_id())std::terminate();
        try {cleanup();}catch(...) {}
    }
    void cleanup(Entered::Native* unpublished=nullptr) {
        if(owner->thread!=std::this_thread::get_id())std::terminate();
        cancelled=true; // Revoke BEFORE the exact real cleanup and any reentry.
        if(cleaned)return;cleaned=true;
        if(original&&original->cleanup)original->cleanup(scope);
        else if(unpublished&&unpublished->cleanup)unpublished->cleanup(scope);
    }
    bool actor_current(const Actor& actor) const noexcept {
        try {
        const auto& status=actor.status;
        if(actor.row>=scope.actor_input->readset().materials().size()||
           scope.actor_input->readset().materials()[actor.row].actor.lease!=actor.source||
           !scope.actor_input->source()->profile_equipment_matches(actor.equipment,scope.actor_input->readset(),actor.row)||
           !status.owned_status_source||!status.owned_status||
           status.domain!=Profiles::StatusInput::Domain::OrdinaryExplicitClear||status.unsupported_domains||
           status.epoch!=status.owned_status->revision()||status.actor_override!=status.owned_status->actor_override()||
           !same_owner(status.dependency_owner,status.owned_status_source)||
           !status.owned_status_source->matches_inputs(*status.owned_status,scope.actor_input,actor.row,actor.equipment,actor.recipient)||
           !status.owned_status_source->retained(*status.owned_status)||
           !status.profile_scope_source||!status.profile_scope||
           !status.profile_scope_source->matches_inputs(*status.profile_scope,scope.actor_input,actor.row,actor.equipment,actor.recipient)||
           !status.profile_scope_source->retained(*status.profile_scope)||
           !actor.resources.arguments_source||!actor.resources.arguments||
           !actor.resources.arguments_source->matches_inputs(*actor.resources.arguments,scope.actor_input,actor.row,actor.equipment)||
           actor.unit.source()!=actor.source||actor.unit.recipient()!=actor.recipient||!actor.unit.retained())return false;
        return true;
        }catch(...){return false;}
    }
    bool pure_body() const noexcept {
        try {
            if(owner->thread!=std::this_thread::get_id()||owner->poisoned||cancelled||
               !scope.actor_input||!scope.population||!scope.actor_input->initial_population()||
               *scope.actor_input->initial_population()!=*scope.population||
               scope.population->joining().lease!=scope.lease||
               !scope.actor_input->population_current(owner->presence)||!owner->profiles->owns_presence(owner->presence)||
               !scope.actor_endpoints||
               !scope.actor_endpoints->matches_input(scope.actor_input)||!scope.actor_endpoints->retained())return false;
            const auto session=connection.lock();
            if(!session||session->closing()||session->id()!=scope.lease.session||session->account_id!=scope.lease.account||
               session->character_id!=scope.lease.character||session->recovered_client_language()!=scope.tail_language)return false;
            for(const auto& actor:actors)if(!actor_current(actor))return false;
            if(outward)for(const auto& actor:outward->actors)if(!actor_current(actor))return false;
            return !cancelled&&!owner->poisoned;
        }catch(...){return false;}
    }
    bool pure() const noexcept {
        // pure_body's temporary strong Session is dropped before this final cut.
        const bool okay=pure_body();
        return okay&&!cancelled&&!owner->poisoned&&scope.actor_input->population_current(owner->presence)&&
            scope.actor_endpoints->retained()&&!cancelled&&!owner->poisoned;
    }
    bool genuine_current(Entered::Check check) const {
        const auto material=original;
        // Supplied callers never promised the additive deferred Check values.
        // Preserve their original BeforeOutward/OutwardPublish contract.
        if(material&&material->outward_decision==Entered::OutwardDecision::Supplied){
            if(check==Entered::Check::BeforeDeferredOutward)check=Entered::Check::BeforeOutward;
            if(check==Entered::Check::AfterDeferredOutward)check=Entered::Check::OutwardPublish;
        }
        return material&&material->current&&pure()&&material->current(check,scope)&&pure();
    }
    bool verify(const Actor& actor,Profiles::Check check) const {
        // Profiles contain strong endpoint Sessions. Keep them TEMPORARY:
        // State->Profile->joining Session->SceneOwner->State would be a cycle.
        auto source=scope.actor_endpoints->source(actor.source);if(!source||!pure())return false;
        auto receiver=scope.actor_endpoints->receiver(actor.recipient);if(!receiver||!pure())return false;
        auto resources=actor.resources;auto status=actor.status;
        if(!pure())return false; // Callback-copy allocations can cancel.
        auto profile=owner->profiles->observe(scope.actor_input,actor.row,actor.equipment,std::move(*source),actor.recipient,
            std::move(*receiver),std::move(resources),std::move(status));
        if(!profile||!pure()||!owner->profiles->current(*profile,check)||!pure())return false;
        return profile->source()==actor.source&&profile->recipient()==actor.recipient&&profile->equipment()==actor.equipment&&
            profile->role_text()==actor.role&&profile->resources().epoch==actor.resources.epoch&&
            profile->resources().arguments==actor.resources.arguments&&
            same_owner(profile->resources().dependency_owner,actor.resources.dependency_owner)&&
            profile->status().owned_status==actor.status.owned_status&&
            profile->status().profile_scope==actor.status.profile_scope&&
            profile->status().epoch==actor.status.epoch&&profile->actor_override()==actor.status.actor_override&&
            RecoveredRemoteActor::encode_logical(profile->spawn())==actor.spawn&&
            RecoveredRemoteActorMove::encode_logical(profile->movement())==actor.movement&&
            RecoveredRemoteActorRemove::encode_logical(profile->removal())==actor.removal;
    }
    bool live(Entered::Check check) const {
        if(!genuine_current(check))return false;
        for(const auto& actor:actors)if(!verify(actor,profile_check(check))||!pure())return false;
        if(outward)for(const auto& actor:outward->actors)if(!verify(actor,profile_check(check))||!pure())return false;
        if(!genuine_current(check))return false;
        // Every temporary Profile/Session/provider copy is gone. Qualify ALL
        // frozen roles/equipment together after every actual live observer.
        return pure()&&scope.actor_input->source()->current_with_role_text(scope.actor_input->readset(),
            scope.actor_input->role_text_source(),outward?outward->roles:roles,{},outward?outward->equipment:equipment)&&pure();
    }
    bool outward_ready() const noexcept {
        bool okay=false;
        {
            const auto actual=connection.lock();
            okay=installed&&released&&scope.population&&scope.population->activated()&&actual&&
                actual->state()==SessionState::InWorld&&actual->common_world_delivery_current(
                    scope.lease.account,scope.lease.character,scope.lease.generation);
        } // Last temporary strong joining owner drops before the pure fence.
        return okay&&pure();
    }
    // Qualify genuine audience metadata BEFORE authoring any TW replacement.
    // CN material remains the genuine source's complete native responsibility.
    bool audience(const std::vector<Visibility::OutwardRecipient>& selected) const {
        if(selected.size()>256||!outward_ready())return false;
        std::set<std::uint64_t> sessions;
        for(const auto& item:selected){
            const auto& recipient=item.lease;
            if(item.actor_status||recipient.session==scope.lease.session||recipient.character==scope.lease.character||
               !sessions.insert(recipient.session).second||!owner->presence->ready(recipient)||!pure())return false;
            const auto position=owner->presence->saved_position(recipient);
            if(!position||position->area!=scope.lease.position.area||position->scene!=scope.lease.position.scene||!pure())return false;
            const bool bound=std::visit([&](const auto& native){
                const auto actual=native.connection.lock();if(!actual)return false;
                if(native.spawn.identity()!=scope.lease.actor_handle||native.movement.identity()!=scope.lease.actor_handle||
                   native.removal.identity()!=scope.lease.actor_handle||native.spawn.x()!=scope.lease.position.x||
                   native.spawn.y()!=scope.lease.position.y||native.movement.x()!=scope.lease.position.x||
                   native.movement.y()!=scope.lease.position.y)return false;
                using Native=std::decay_t<decltype(native)>;
                if constexpr(std::is_same_v<Native,Visibility::Taiwan>){
                    const auto raw=RecoveredRemoteActor::encode_logical(native.spawn);
                    return actual->id()==recipient.session&&actual->account_id==recipient.account&&
                        actual->character_id==recipient.character&&!actual->closing()&&actual->recovered_world_ready()&&
                        actual->common_world_delivery_current(recipient.account,recipient.character,recipient.generation)&&
                        native.movement.state()==(std::uint16_t(raw[7])|(std::uint16_t(raw[8])<<8));
                }else return !actual->closing()&&actual->role()==cn::SharedCredentialConnection::Transport::Role::World&&
                    actual->world_session_id()==recipient.session&&actual->verified_account_id()==recipient.account&&
                    actual->world_character_offered(recipient.character)&&actual->world_admission_current()&&
                    native.movement.state_raw()==native.spawn.state_raw();
            },item.native);
            if(!bound||!outward_ready())return false;
        }
        return outward_ready();
    }
    struct Call {
        State& state;bool entered=false;
        explicit Call(State& value):state(value) {
            if(state.owner->thread!=std::this_thread::get_id())return;
            if(state.running){state.cancelled=true;return;}
            if(!state.cancelled){state.running=true;entered=true;}
        }
        ~Call(){if(entered)state.running=false;}
    };
};
std::optional<TaiwanActorStatusPublication::ActorUnit> OwnedTaiwanInitialActorSceneSource::mint(
        const Profiles::Profile& profile) {
    const auto& status=profile.status();
    if(!status.owned_status_source||!status.owned_status||!profile.actor_override()||
       !profile.actor_override()->replay())return {};
    const auto spawn=RecoveredRemoteActor::encode_logical(profile.spawn());
    const auto replay=RecoveredTaiwanActorOverride::encode_logical(*profile.actor_override()->replay());
    std::vector<std::uint8_t> whole(spawn.begin(),spawn.end());whole.insert(whole.end(),replay.begin(),replay.end());
    return status.owned_status_source->prepare_publication(*status.owned_status,whole);
}
Entered::Source OwnedTaiwanInitialActorSceneSource::wrap(std::shared_ptr<SharedWorldPresence> presence,
        std::shared_ptr<Profiles> profiles,OwnedTaiwanPkReturnSceneSource::MaterialSources material,Entered::Source genuine) {
    if(!presence||!profiles||!profiles->owns_presence(presence)||!material.dependency_owner||
       !material.resources||!material.status||!genuine)
        throw std::invalid_argument("TW initial full actor adapter requires real same-owner material and genuine Source");
    const auto owner=std::make_shared<Owner>(std::move(presence),std::move(profiles),std::move(material),std::move(genuine));
    return [owner](Session& session,const Entered::Scope& scope){return supply(owner,session,scope);};
}
std::optional<Entered::Native> OwnedTaiwanInitialActorSceneSource::supply(
        const std::shared_ptr<Owner>& supplied_owner,Session& session,const Entered::Scope& supplied_scope) {
    const auto owner=supplied_owner;const auto scope=supplied_scope;
    if(owner->thread!=std::this_thread::get_id())throw std::logic_error("TW initial full actor game owner mismatch");
    if(owner->supplying){owner->poisoned=true;return {};}if(owner->poisoned)return {};
    struct Supplying {Owner& owner;explicit Supplying(Owner& value):owner(value){owner.supplying=true;}
        ~Supplying(){owner.supplying=false;}} supplying(*owner);
    const auto state=std::make_shared<State>(owner,scope,session);
    if(!state->pure())return {};
    auto native=owner->genuine(session,scope);if(!native)return {};
    try {state->original=std::make_shared<Entered::Native>(std::move(*native));}
    catch(...) {state->cleanup(&*native);throw;}
    native.reset(); // Original callback custody is now strong and immutable.
    bool delivered=false;
    struct CleanupGuard {std::shared_ptr<State> state;bool& delivered;
        ~CleanupGuard(){if(!delivered)try {state->cleanup();}catch(...) {}}} guard{state,delivered};
    const auto original=state->original;
    if(!original->current||!original->install||!original->cleanup||!state->genuine_current(Entered::Check::AfterSupply)||
       original->incoming.size()!=original->incoming_offsets.size()||original->incoming.size()>128)return {};
    std::vector<RecoveredTaiwanServerRecords::Record> records;
    if(original->decision==Entered::ReplyDecision::ExplicitNoInitialReply){
        if(!original->logical.empty()||!original->incoming.empty()||!original->incoming_offsets.empty())return {};
    }else if(original->decision==Entered::ReplyDecision::CompleteNativeAggregate){
        auto parsed=RecoveredTaiwanServerRecords::read_aggregate(original->logical);if(!parsed)return {};
        records=std::move(*parsed);
    }else return {};
    if(!state->pure())return {};
    std::vector<std::size_t> rows;rows.reserve(original->incoming.size());
    std::set<std::uint64_t> selected_sessions;std::set<std::uint16_t> selected_handles;
    std::size_t actor_index=0;
    // Prove EVERY original6F boundary/selection before authoring any replacement.
    for(const auto& record:records){
        if(record.opcode!=0x6f)continue;
        if(actor_index>=original->incoming.size()||record.offset!=original->incoming_offsets[actor_index]||
           record.bytes.size()!=RecoveredRemoteActor::logical_size)return {};
        const auto& incoming=original->incoming[actor_index++];const auto& source=incoming.source;
        if(source.session==scope.lease.session||source.character==scope.lease.character||
           !selected_sessions.insert(source.session).second||!selected_handles.insert(source.actor_handle).second)return {};
        const auto& saved=scope.actor_input->readset().materials();
        auto found=std::find_if(saved.begin(),saved.end(),[&](const auto& row){return row.actor.lease==source;});
        if(found==saved.end())return {};const auto row=static_cast<std::size_t>(found-saved.begin());
        const auto actual=incoming.native.connection.lock();const auto joining=state->connection.lock();
        if(!actual||actual!=joining||incoming.native.spawn.identity()!=source.actor_handle||
           incoming.native.movement.identity()!=source.actor_handle||incoming.native.removal.identity()!=source.actor_handle||
           incoming.native.spawn.x()!=found->actor.position.x||incoming.native.spawn.y()!=found->actor.position.y||
           incoming.native.movement.x()!=found->actor.position.x||incoming.native.movement.y()!=found->actor.position.y||
           found->actor.position.area!=scope.lease.position.area||found->actor.position.scene!=scope.lease.position.scene)return {};
        const auto raw=RecoveredRemoteActor::encode_logical(incoming.native.spawn);
        if(incoming.native.movement.state()!=(std::uint16_t(raw[7])|(std::uint16_t(raw[8])<<8)))return {};
        bool matches=std::equal(raw.begin(),raw.end(),record.bytes.begin());
        if(incoming.native.common_name_source){
            const auto names=incoming.native.common_name_source;
            if(!names->owns_presence(owner->presence)||!state->pure())return {};
            auto projected=names->project(source,scope.lease,Visibility::Native{incoming.native});
            if(!projected||!state->genuine_current(Entered::Check::AfterSupply))return {};
            const auto* tw=std::get_if<Visibility::Taiwan>(&*projected);if(!tw)return {};
            const auto bytes=RecoveredRemoteActor::encode_logical(tw->spawn);
            matches|=std::equal(bytes.begin(),bytes.end(),record.bytes.begin());
        }
        if(!matches||!state->pure())return {};rows.push_back(row);
    }
    if(actor_index!=original->incoming.size()||!state->genuine_current(Entered::Check::AfterSupply))return {};
    // A later/nonadjacent EA for a selected actor could override its owned
    // replay. Only that actor's actual immediate parsed following EA is allowed.
    for(std::size_t i=0;i<records.size();++i)if(records[i].opcode==0xea){
        const auto replay=RecoveredTaiwanActorOverride::parse_logical(records[i].bytes);if(!replay)return {};
        if(selected_handles.contains(replay->identity())){
            if(!i||records[i-1].opcode!=0x6f||records[i-1].offset+RecoveredRemoteActor::logical_size!=records[i].offset)return {};
            const auto actor=RecoveredRemoteActor::parse_logical(records[i-1].bytes);
            if(!actor||actor->identity()!=replay->identity())return {};
        }
    }
    state->actors.reserve(rows.size());state->roles.reserve(rows.size());state->equipment.reserve(rows.size());
    std::vector<Visibility::InitialTaiwanActor> incoming;incoming.reserve(rows.size());
    for(std::size_t i=0;i<rows.size();++i){
        if(!state->pure())return {};
        // All full Profile/Session owners in this block die before the final
        // live/joint cuts. Captured material is NEVER fetched again on Current.
        const auto row=rows[i];const auto& selected=original->incoming[i];
        auto equipment=scope.actor_input->source()->observe_profile_equipment(scope.actor_input->readset(),row);
        if(!equipment||!state->genuine_current(Entered::Check::AfterSupply))return {};
        auto resources=owner->material.resources(scope.actor_input,row,*equipment,scope.lease);
        if(!resources||!state->genuine_current(Entered::Check::AfterSupply))return {};
        auto status=owner->material.status(scope.actor_input,row,*equipment,scope.lease);
        if(!status||!status->owned_status_source||!status->owned_status||!state->genuine_current(Entered::Check::AfterSupply))return {};
        auto source=scope.actor_endpoints->source(selected.source);if(!source||!state->pure())return {};
        auto receiver=scope.actor_endpoints->receiver(scope.lease);if(!receiver||!state->pure())return {};
        auto profile=owner->profiles->observe(scope.actor_input,row,*equipment,std::move(*source),scope.lease,
            std::move(*receiver),std::move(*resources),std::move(*status));
        if(!profile||!state->pure())return {};
        auto unit=mint(*profile);
        if(!unit||!owner->profiles->current(*profile,Profiles::Check::Prepare)||!state->pure())return {};
        if(selected.actor_status&&(!selected.actor_status->retained()||selected.actor_status->source()!=selected.source||
           selected.actor_status->recipient()!=scope.lease||selected.actor_status->logical()!=unit->logical()))return {};
        state->actors.emplace_back(row,*profile,*unit);
        state->roles.push_back(profile->role_text());state->equipment.push_back(profile->equipment());
        Visibility::Taiwan model{state->connection,profile->spawn(),profile->removal(),profile->movement(),
            Visibility::TaiwanReceiverTextState(profile->receiver().selector),selected.native.common_name_source};
        incoming.push_back({selected.source,std::move(model),std::move(unit)});
        if(!state->pure())return {};
    }
    std::vector<std::uint8_t> logical;std::vector<std::size_t> offsets;offsets.reserve(incoming.size());
    const auto append=[&](std::span<const std::uint8_t> bytes){
        if(bytes.size()>RecoveredTaiwanServerRecords::max_aggregate_logical_size-logical.size())
            throw std::length_error("Initial full actor aggregate exceeds allocation cap");
        logical.insert(logical.end(),bytes.begin(),bytes.end());
    };
    actor_index=0;
    for(std::size_t i=0;i<records.size();++i){
        const auto& record=records[i];
        if(record.opcode!=0x6f){append(record.bytes);continue;}
        const auto& actor=state->actors[actor_index++];offsets.push_back(logical.size());
        const auto& whole=actor.unit.logical();append(std::span<const std::uint8_t>(whole).first(RecoveredRemoteActor::logical_size));
        if(i+1<records.size()&&records[i+1].opcode==0xea){
            const auto following=RecoveredTaiwanActorOverride::parse_logical(records[i+1].bytes);if(!following)return {};
            if(following->identity()==actor.source.actor_handle){
                const auto replay=std::span<const std::uint8_t>(whole).subspan(RecoveredRemoteActor::logical_size);
                if(records[i+1].bytes.size()!=replay.size()||!std::equal(replay.begin(),replay.end(),records[i+1].bytes.begin()))return {};
                ++i;
            }
            // An unselected/self EA is opaque genuine-source material. Insert
            // this actor's owned clear first; retain that original EA in order.
        }
        append(std::span<const std::uint8_t>(whole).subspan(RecoveredRemoteActor::logical_size));
    }
    // Copy all genuine callbacks/material BEFORE replacing any callback. State
    // retains the original, and the returned Native is a DIFFERENT object.
    Entered::Native result=*original;
    Entered::Current current=[state](Entered::Check check,const Entered::Scope& value) {
        State::Call call(*state);if(!call.entered||!same_scope(state->scope,value)||!state->pure())return false;
        const bool okay=state->live(check);
        if(okay&&(check==Entered::Check::QueueReleased||check==Entered::Check::LocalPublished))state->released=true;
        return okay&&state->pure();
    };
    Entered::Install install=[state](Session& actual,const Entered::Scope& value) {
        State::Call call(*state);
        if(!call.entered||state->installed||!same_scope(state->scope,value)||
           state->connection.lock().get()!=&actual||!state->pure())return false;
        state->installed=true;
        // Actual held install remains PURE. Full Profile/SQL Current is only
        // in supply/current, never inside this original real install boundary.
        const bool okay=state->original->install(actual,state->scope);return okay&&state->pure();
    };
    Entered::Cleanup cleanup=[state](const Entered::Scope&){state->cleanup();};
    result.logical=std::move(logical);result.incoming_offsets=std::move(offsets);result.incoming=std::move(incoming);
    result.current=std::move(current);result.install=std::move(install);result.cleanup=std::move(cleanup);
    // Always author outward TW units AFTER the real owned-clear install,
    // private activation, delivery binding and actual initial queue release.
    // State retains only the ORIGINAL immutable Native; this different returned
    // provider captures State, without a Native->State->same Native cycle.
    if((original->outward_decision==Entered::OutwardDecision::Supplied&&original->outward_provider)||
       (original->outward_decision==Entered::OutwardDecision::AfterInitialPublication&&
        (!original->outward.empty()||!original->outward_provider||!*original->outward_provider))||
       (original->outward_decision!=Entered::OutwardDecision::Supplied&&
        original->outward_decision!=Entered::OutwardDecision::AfterInitialPublication))return {};
    Entered::OutwardProvider outward=[state](Session& actual,const Entered::Scope& value)
        ->std::optional<std::vector<Visibility::OutwardRecipient>> {
        State::Call call(*state);
        if(!call.entered)return {};
        if(std::exchange(state->outward_started,true)){state->cancelled=true;return {};}
        bool committed=false;
        struct OutwardAttempt {State& state;bool& committed;~OutwardAttempt(){if(!committed)state.cancelled=true;}} attempt{*state,committed};
        if(!same_scope(state->scope,value)||state->connection.lock().get()!=&actual||!state->outward_ready())return {};
        const auto genuine=state->original;
        std::vector<Visibility::OutwardRecipient> selected;
        if(!state->genuine_current(Entered::Check::BeforeDeferredOutward))return {};
        if(genuine->outward_decision==Entered::OutwardDecision::Supplied)selected=genuine->outward;
        else {
            const auto provider=genuine->outward_provider;
            auto supplied=(*provider)(actual,state->scope);
            if(!supplied||!state->outward_ready())return {};
            selected=std::move(*supplied);
        } // Provider/result temporaries gone before Current and qualification.
        if(!state->genuine_current(Entered::Check::AfterDeferredOutward)||!state->audience(selected))return {};
        const auto& saved=state->scope.actor_input->readset().materials();
        const auto joining=std::find_if(saved.begin(),saved.end(),[&](const auto& row){
            return row.actor.lease==state->scope.lease;});
        if(joining==saved.end())return {};
        const auto row=static_cast<std::size_t>(joining-saved.begin());
        // Candidate copies/allocations precede the final full joint saved cut.
        // Commit no partial prefix of frozen directed actors on failure.
        std::vector<State::Actor> actors;auto roles=state->roles;auto equipment=state->equipment;
        for(auto& item:selected){
            auto* native=std::get_if<Visibility::Taiwan>(&item.native);
            if(!native)continue; // Genuine CN vector/model/order is untouched.
            if(!state->outward_ready())return {};
            {
                auto eq=state->scope.actor_input->source()->observe_profile_equipment(state->scope.actor_input->readset(),row);
                if(!eq||!state->genuine_current(Entered::Check::OutwardPublish))return {};
                auto resources=state->owner->material.resources(state->scope.actor_input,row,*eq,item.lease);
                if(!resources||!state->genuine_current(Entered::Check::OutwardPublish))return {};
                auto status=state->owner->material.status(state->scope.actor_input,row,*eq,item.lease);
                if(!status||!status->owned_status_source||!status->owned_status||
                   !state->genuine_current(Entered::Check::OutwardPublish))return {};
                auto source=state->scope.actor_endpoints->source(state->scope.lease);
                if(!source||!state->outward_ready())return {};
                auto receiver=state->scope.actor_endpoints->receiver(item.lease);
                if(!receiver||!same_owner(receiver->session,native->connection.lock())||!state->outward_ready())return {};
                auto profile=state->owner->profiles->observe(state->scope.actor_input,row,*eq,std::move(*source),item.lease,
                    std::move(*receiver),std::move(*resources),std::move(*status));
                if(!profile||!state->outward_ready())return {};
                auto unit=mint(*profile);
                if(!unit||!state->owner->profiles->current(*profile,Profiles::Check::Prepare)||!state->outward_ready())return {};
                Visibility::Taiwan model{native->connection,profile->spawn(),profile->removal(),profile->movement(),
                    Visibility::TaiwanReceiverTextState(profile->receiver().selector),native->common_name_source};
                if(model.common_name_source){
                    const auto names=model.common_name_source;
                    if(!names->owns_presence(state->owner->presence)||!state->outward_ready())return {};
                    auto projected=names->project(state->scope.lease,item.lease,Visibility::Native{model});
                    if(!projected||!state->genuine_current(Entered::Check::OutwardPublish))return {};
                    const auto* tw=std::get_if<Visibility::Taiwan>(&*projected);
                    if(!tw||RecoveredRemoteActor::encode_logical(tw->spawn)!=RecoveredRemoteActor::encode_logical(profile->spawn()))return {};
                }
                actors.emplace_back(row,*profile,*unit);roles.push_back(profile->role_text());equipment.push_back(profile->equipment());
                item.native=std::move(model);item.actor_status=std::move(unit);
            } // Drop ALL temporary full Profiles/strong endpoint Sessions.
            if(!state->outward_ready())return {};
        }
        const auto frozen=std::make_shared<const State::FrozenOutward>(std::move(actors),std::move(roles),std::move(equipment));
        // All callback-bearing candidate copies are now owned by this immutable
        // box. It survives in State after commit; no old Actor destructors run
        // after the final saved cut. Profiles/strong Sessions are already gone.
        for(const auto& actor:state->actors)if(!state->verify(actor,Profiles::Check::Retained)||!state->outward_ready())return {};
        for(const auto& actor:frozen->actors)if(!state->verify(actor,Profiles::Check::Retained)||!state->outward_ready())return {};
        if(!state->genuine_current(Entered::Check::OutwardPublish)||!state->outward_ready()||
           !state->scope.actor_input->source()->current_with_role_text(state->scope.actor_input->readset(),
                state->scope.actor_input->role_text_source(),frozen->roles,{},frozen->equipment)||!state->outward_ready())return {};
        for(const auto& actor:frozen->actors)if(!state->actor_current(actor))return {};
        state->outward=frozen; // No allocation, callback or partial actor prefix.
        if(!state->pure())return {};
        committed=true;return selected;
    };
    result.outward.clear();result.outward_decision=Entered::OutwardDecision::AfterInitialPublication;
    result.outward_provider=std::make_shared<const Entered::OutwardProvider>(std::move(outward));
    {
        State::Call call(*state);
        if(!call.entered||!state->live(Entered::Check::AfterSupply)||!state->pure())return {};
    }
    if(!state->pure())return {};
    delivered=true;return std::optional<Entered::Native>(std::move(result));
}
}
