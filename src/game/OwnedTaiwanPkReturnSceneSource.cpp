#include "game/OwnedTaiwanPkReturnSceneSource.h"
#include <algorithm>
#include <map>
#include <stdexcept>
#include <utility>

namespace god2 {
struct OwnedTaiwanPkReturnSceneSource::Endpoint {
    const std::shared_ptr<const Request> request;
    const std::shared_ptr<SharedWorldPresence> presence;
    const std::shared_ptr<SharedNativeWorldTransports> transports;
    const SharedNativeWorldTransports::Snapshot snapshot;
    const std::shared_ptr<Session> session;
    const std::array<Lease,2> returning;
    const std::array<RecoveredPosition,2> positions;
    const std::optional<std::size_t> member;
    const std::optional<Session::NativeTaiwanReceiverSelector> selector;
    const std::optional<Session::NormalWorldInitialization> normal;
    const std::thread::id thread=std::this_thread::get_id();
    bool current(Check check) const {
        if(thread!=std::this_thread::get_id()||!request->actor_input||
           !presence->retained_population_current(request->actor_input->population())||
           !transports->registry_current(snapshot.token())||!session||!selector||
           !session->same_native_pk_game_executor(*request->sessions[0])||
           !session->native_taiwan_receiver_selector_current(*selector))return false;
        if(member){
            if(session!=request->sessions[*member]||snapshot.lease()!=returning[*member])return false;
            // After consume, the actual outer Visibility consumption token
            // owns successor authority. This leaf owns only its exact endpoint
            // registration and private selector, never the old preparation.
            if(check==Check::Consumed)return true;
            for(std::uint8_t i=0;i<2;++i)
                if(!request->sessions[i]->native_pk_return_preparation_current(request->preparations[i])||
                   !request->departure.visibility->taiwan_pk_departure_retained_current(
                       request->departure.token,returning,positions,request->sessions,request->holds,i))return false;
            return true;
        }
        return normal&&transports->registry_current(snapshot)&&session->state()==SessionState::InWorld&&
            session->normal_world_initialization_current_on_game(*normal);
    }
};
struct OwnedTaiwanPkReturnSceneSource::State {
    const std::shared_ptr<const Request> request;
    const std::array<Lease,2> returning;
    const std::array<RecoveredPosition,2> positions;
    std::vector<std::shared_ptr<const Endpoint>> endpoints;
    std::vector<ProfileOwner::Profile> profiles;
    std::vector<Equipment> equipment;
    Check check=Check::Prepare;
    bool poisoned=false;
    State(std::shared_ptr<const Request> actual,std::array<Lease,2> leases,
          std::array<RecoveredPosition,2> poses)
        :request(std::move(actual)),returning(std::move(leases)),positions(std::move(poses)){}
};
OwnedTaiwanPkReturnSceneSource::OwnedTaiwanPkReturnSceneSource(
        std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<SharedNativeWorldTransports> transports,
        std::shared_ptr<cn::SharedActorVisibility> visibility,std::shared_ptr<ProfileOwner> profiles,
        Selection selection,MaterialSources material)
    :presence_(std::move(presence)),transports_(std::move(transports)),visibility_(std::move(visibility)),
     profiles_(std::move(profiles)),selection_(selection),material_(std::move(material)){}
std::shared_ptr<OwnedTaiwanPkReturnSceneSource> OwnedTaiwanPkReturnSceneSource::create(
        std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<SharedNativeWorldTransports> transports,
        std::shared_ptr<cn::SharedActorVisibility> visibility,std::shared_ptr<ProfileOwner> profiles,
        Selection selection,MaterialSources material){
    if(!presence||!transports||!visibility||!profiles||!transports->owns_presence(presence)||
       !visibility->owns_presence(presence)||!profiles->owns_presence(presence)||
       selection!=Selection::CustomSameAreaSceneV1||!material.dependency_owner||
       !material.resources||!material.status)
        throw std::invalid_argument("TW full return scene requires same host and actual complete material owners");
    auto owner=std::shared_ptr<OwnedTaiwanPkReturnSceneSource>(new OwnedTaiwanPkReturnSceneSource(
        std::move(presence),std::move(transports),std::move(visibility),std::move(profiles),selection,std::move(material)));
    owner->self_=owner;return owner;
}
OwnedPkOutboxPublication::ReturnSceneSource OwnedTaiwanPkReturnSceneSource::return_source(){
    if(thread_!=std::this_thread::get_id())throw std::logic_error("TW return scene game owner mismatch");
    auto owner=self_.lock();if(!owner||poisoned_)throw std::logic_error("TW return scene owner retired");
    return [owner](const Request& request){return owner->observe(request);};
}
bool OwnedTaiwanPkReturnSceneSource::fence(const State& state,Check check)const{
    if(thread_!=std::this_thread::get_id()||poisoned_||state.poisoned||!state.request->actor_input||
       state.request->departure.presence!=presence_||state.request->departure.visibility!=visibility_)return false;
    const auto input=state.request->actor_input;
    if(!input->source()||!input->source()->owns_presence(presence_)||
       !input->source()->owns_readset(input->readset())||
       !input->readset().matches_population(input->population().characters())||
       !presence_->retained_population_current(input->population())||
       state.endpoints.size()!=input->readset().materials().size())return false;
    for(const auto& endpoint:state.endpoints){
        if(!endpoint||!transports_->registry_current(endpoint->snapshot.token()))return false;
        if(endpoint->selector&&!endpoint->current(check))return false;
    }
    for(const auto& profile:state.profiles)
        if(profile.saved_input()!=input||!profiles_->owns_profile(profile))return false;
    return true;
}
bool OwnedTaiwanPkReturnSceneSource::current(const std::shared_ptr<State>& state,Check check){
    if(thread_!=std::this_thread::get_id())return false;
    if(busy_){poisoned_=true;if(state)state->poisoned=true;return false;}
    busy_=true;struct End{bool& busy;~End(){busy=false;}}end{busy_};
    if(!state||(check!=Check::Prepare&&check!=Check::Retained&&check!=Check::Consumed)||
       (state->check==Check::Consumed&&check!=Check::Consumed)||!fence(*state,check))return false;
    state->check=check;
    try{
        for(const auto& profile:state->profiles)
            if(!profiles_->current(profile,check)||!fence(*state,check)){state->poisoned=true;return false;}
        return fence(*state,check);
    }catch(...){state->poisoned=true;return false;}
}
bool OwnedTaiwanPkReturnSceneSource::qualified(const std::shared_ptr<State>& state,const ProfileOwner::Profile& profile){
    if(thread_!=std::this_thread::get_id())return false;
    if(busy_){poisoned_=true;if(state)state->poisoned=true;return false;}
    busy_=true;struct End{bool& busy;~End(){busy=false;}}end{busy_};
    if(!state||!fence(*state,state->check))return false;
    try{return profiles_->current(profile,state->check)&&fence(*state,state->check);}
    catch(...){state->poisoned=true;return false;}
}
std::optional<OwnedTaiwanPkReturnSceneSource::Scene> OwnedTaiwanPkReturnSceneSource::observe(const Request& supplied){
    if(thread_!=std::this_thread::get_id())return {};
    if(busy_){poisoned_=true;return {};}
    busy_=true;struct End{bool& busy;~End(){busy=false;}}end{busy_};
    if(poisoned_)return {};
    // Own all request/private input before repository, Session or provider observers.
    const auto request=std::make_shared<const Request>(supplied);
    if(!request->actor_input||!request->sessions[0]||!request->sessions[1]||
       request->sessions[0]==request->sessions[1]||request->departure.presence!=presence_||
       request->departure.visibility!=visibility_)return {};
    const auto appearances=request->ticket.input().entry.owned_appearances();
    if(!appearances)return {};
    const std::array<Lease,2> returning{(*appearances)[0].material().lease,(*appearances)[1].material().lease};
    const std::array<RecoveredPosition,2> positions{
        request->ticket.input().pair.challenger.position,request->ticket.input().pair.recipient.position};
    const auto input=request->actor_input;
    if(!input->source()||!input->source()->owns_presence(presence_)||!input->source()->owns_readset(input->readset())||
       !input->readset().matches_population(input->population().characters())||
       !presence_->retained_population_current(input->population()))return {};
    auto state=std::make_shared<State>(request,returning,positions);
    auto owner=self_.lock();if(!owner)return {};
    try{
        const auto& rows=input->readset().materials();
        std::map<std::uint64_t,std::size_t> indices;
        std::array<std::size_t,2> returning_rows{};
        std::array<bool,2> found{};
        for(std::size_t index=0;index<rows.size();++index){
            const auto& row=rows[index];
            if(!indices.emplace(row.actor.lease.session,index).second)return {};
            const auto snapshot=transports_->lookup(row.actor.lease);
            if(!snapshot||poisoned_||!presence_->retained_population_current(input->population()))return {};
            const auto tw=std::get_if<std::shared_ptr<Session>>(&snapshot->transport());
            std::optional<std::size_t> member;
            for(std::size_t i=0;i<2;++i)if(row.actor.lease==returning[i]){
                if(found[i]||!tw||*tw!=request->sessions[i]||row.actor.position!=positions[i])return {};
                member=i;found[i]=true;returning_rows[i]=index;
            }
            bool selected=bool(member);
            for(const auto& position:positions)
                selected|=row.actor.position.area==position.area&&row.actor.position.scene==position.scene;
            // A same-scene CN endpoint needs its native adapter. Refuse the
            // whole selection; never silently omit it from a TW-only roster.
            if(selected&&!tw)return {};
            std::optional<Session::NativeTaiwanReceiverSelector> selector;
            std::optional<Session::NormalWorldInitialization> normal;
            if(selected){
                selector=member?(*tw)->native_taiwan_return_receiver_selector(request->preparations[*member]):
                    (*tw)->native_taiwan_receiver_selector_on_game();
                if(!selector)return {};
                if(!member){normal=(*tw)->normal_world_initialization();if(!normal)return {};}
            }
            state->endpoints.push_back(std::make_shared<const Endpoint>(Endpoint{request,presence_,transports_,
                *snapshot,tw?*tw:std::shared_ptr<Session>{},returning,positions,member,selector,normal}));
        }
        if(!found[0]||!found[1]||!fence(*state,Check::Prepare))return {};
        Scene scene;
        using Key=std::pair<std::uint64_t,std::uint64_t>;
        std::map<Key,cn::SharedActorVisibility::TaiwanReturnActor> actors;
        std::map<std::size_t,Equipment> equipment;
        const auto actor=[&](std::size_t source_row,std::size_t recipient_row)
                ->std::optional<cn::SharedActorVisibility::TaiwanReturnActor>{
            const auto source=state->endpoints[source_row],recipient=state->endpoints[recipient_row];
            const auto& source_saved=rows[source_row].actor;
            const auto& recipient_saved=rows[recipient_row].actor;
            const Key key{source_saved.lease.session,recipient_saved.lease.session};
            if(const auto at=actors.find(key);at!=actors.end())return at->second;
            if(!source->session||!source->selector||!recipient->session||!recipient->selector)return {};
            auto eq=equipment.find(source_row);
            if(eq==equipment.end()){
                auto observed=input->source()->observe_profile_equipment(input->readset(),source_row);
                if(!observed||!fence(*state,Check::Prepare))return {};
                eq=equipment.emplace(source_row,std::move(*observed)).first;
            }
            auto resources=material_.resources(*input,source_row,eq->second,recipient_saved.lease);
            if(!resources||!fence(*state,Check::Prepare))return {};
            auto status=material_.status(*input,source_row,eq->second,recipient_saved.lease);
            if(!status||!fence(*state,Check::Prepare))return {};
            ProfileOwner::SourceInput source_input{source->session,source,
                [source](Check check,const Lease& lease,Session& actual){
                    return lease==source->snapshot.lease()&&source->session.get()==&actual&&source->current(check);}};
            ProfileOwner::ReceiverInput receiver_input{recipient->session,*recipient->selector,recipient,
                [recipient](Check check,Session& actual,const Session::NativeTaiwanReceiverSelector& selector){
                    return recipient->session.get()==&actual&&recipient->selector&&
                        *recipient->selector==selector&&recipient->current(check);}};
            auto profile=profiles_->observe(input,source_row,eq->second,std::move(source_input),recipient_saved.lease,
                std::move(receiver_input),std::move(*resources),std::move(*status));
            if(!profile||!fence(*state,Check::Prepare))return {};
            state->profiles.push_back(*profile);
            auto qualification=std::make_shared<const cn::SharedActorVisibility::TaiwanReturnQualification>(
                cn::SharedActorVisibility::TaiwanReturnQualification{profile->revision(),
                    [owner,state,profile=*profile]{return owner->qualified(state,profile);},{}});
            cn::SharedActorVisibility::Taiwan native{recipient->session,profile->spawn(),profile->removal(),
                profile->movement(),cn::SharedActorVisibility::TaiwanReceiverTextState(*recipient->selector),{}};
            cn::SharedActorVisibility::TaiwanReturnActor output{source_saved.lease,recipient_saved.lease,
                source_saved.position,recipient_saved.position,source->session,std::move(native),
                std::move(qualification),profile->actor_override()};
            actors.emplace(key,output);return output;
        };
        for(std::size_t member=0;member<2;++member){
            for(const auto& [session,row]:indices){
                if(row==returning_rows[member])continue;
                const auto& other=rows[row].actor.position;
                if(other.area!=positions[member].area||other.scene!=positions[member].scene)continue;
                auto incoming=actor(row,returning_rows[member]);
                auto outgoing=actor(returning_rows[member],row);
                if(!incoming||!outgoing)return {};
                scene.incoming[member].push_back(std::move(*incoming));
                scene.outgoing[member].push_back(std::move(*outgoing));
                if(scene.incoming[member].size()>128||scene.outgoing[member].size()>256)return {};
            }
        }
        for(auto& [row,eq]:equipment)state->equipment.push_back(std::move(eq));
        // All vectors/canonical shared witnesses are allocated before final
        // live qualifications; the existing backend/Visibility own closed SQL.
        scene.actor_input=input;scene.actor_saved_source=input->source();scene.actor_saved_rows=input->readset();
        scene.ready_population=input->population();scene.role_text_source=input->role_text_source();
        scene.actor_profile_equipment=state->equipment;
        scene.current=[owner,state](Check check){return owner->current(state,check);};
        for(const auto& profile:state->profiles)
            if(!profiles_->current(profile,Check::Prepare)||!fence(*state,Check::Prepare))return {};
        if(!fence(*state,Check::Prepare))return {};
        return scene;
    }catch(...){state->poisoned=true;return {};}
}
}
