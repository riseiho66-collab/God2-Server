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
        const Lease source;
        const Profiles::Equipment equipment;
        const Profiles::ResourceInput resources;
        const Profiles::StatusInput status;
        const Role role;
        const RecoveredRemoteActor::LogicalRecord spawn;
        const RecoveredRemoteActorMove::LogicalRecord movement;
        const RecoveredRemoteActorRemove::LogicalRecord removal;
        const TaiwanActorStatusPublication::ActorUnit unit;
        Actor(std::size_t index,const Profiles::Profile& profile,TaiwanActorStatusPublication::ActorUnit publication)
            :row(index),source(profile.source()),equipment(profile.equipment()),resources(profile.resources()),
             status(profile.status()),role(profile.role_text()),spawn(RecoveredRemoteActor::encode_logical(profile.spawn())),
             movement(RecoveredRemoteActorMove::encode_logical(profile.movement())),
             removal(RecoveredRemoteActorRemove::encode_logical(profile.removal())),unit(std::move(publication)){}
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
            for(const auto& actor:actors){
                const auto& status=actor.status;
                if(actor.row>=scope.actor_input->readset().materials().size()||
                   scope.actor_input->readset().materials()[actor.row].actor.lease!=actor.source||
                   !scope.actor_input->source()->profile_equipment_matches(actor.equipment,scope.actor_input->readset(),actor.row)||
                   !status.owned_status_source||!status.owned_status||
                   status.domain!=Profiles::StatusInput::Domain::OrdinaryExplicitClear||status.unsupported_domains||
                   status.epoch!=status.owned_status->revision()||status.actor_override!=status.owned_status->actor_override()||
                   !same_owner(status.dependency_owner,status.owned_status_source)||
                   !status.owned_status_source->matches_inputs(*status.owned_status,scope.actor_input,actor.row,actor.equipment,scope.lease)||
                   !status.owned_status_source->retained(*status.owned_status)||
                   !status.profile_scope_source||!status.profile_scope||
                   !status.profile_scope_source->matches_inputs(*status.profile_scope,scope.actor_input,actor.row,actor.equipment,scope.lease)||
                   !status.profile_scope_source->retained(*status.profile_scope)||
                   !actor.resources.arguments_source||!actor.resources.arguments||
                   !actor.resources.arguments_source->matches_inputs(*actor.resources.arguments,scope.actor_input,actor.row,actor.equipment)||
                   actor.unit.source()!=actor.source||actor.unit.recipient()!=scope.lease||!actor.unit.retained())return false;
            }
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
        return material&&material->current&&pure()&&material->current(check,scope)&&pure();
    }
    bool verify(const Actor& actor,Profiles::Check check) const {
        // Profiles contain strong endpoint Sessions. Keep them TEMPORARY:
        // State->Profile->joining Session->SceneOwner->State would be a cycle.
        auto source=scope.actor_endpoints->source(actor.source);if(!source||!pure())return false;
        auto receiver=scope.actor_endpoints->receiver(scope.lease);if(!receiver||!pure())return false;
        auto resources=actor.resources;auto status=actor.status;
        if(!pure())return false; // Callback-copy allocations can cancel.
        auto profile=owner->profiles->observe(scope.actor_input,actor.row,actor.equipment,std::move(*source),scope.lease,
            std::move(*receiver),std::move(resources),std::move(status));
        if(!profile||!pure()||!owner->profiles->current(*profile,check)||!pure())return false;
        return profile->source()==actor.source&&profile->recipient()==scope.lease&&profile->equipment()==actor.equipment&&
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
        if(!genuine_current(check))return false;
        // Every temporary Profile/Session/provider copy is gone. Qualify ALL
        // frozen roles/equipment together after every actual live observer.
        return pure()&&scope.actor_input->source()->current_with_role_text(scope.actor_input->readset(),
            scope.actor_input->role_text_source(),roles,{},equipment)&&pure();
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
        const bool okay=state->live(check);return okay&&state->pure();
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
    // Original deferred outward provider/vector are retained unchanged.
    {
        State::Call call(*state);
        if(!call.entered||!state->live(Entered::Check::AfterSupply)||!state->pure())return {};
    }
    if(!state->pure())return {};
    delivered=true;return std::optional<Entered::Native>(std::move(result));
}
}
