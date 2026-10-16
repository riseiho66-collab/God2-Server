#include "cn/world/SharedActorVisibility.h"
#include "cn/world/SharedInitialScene.h"
#include "game/SharedNativeActorNameSource.h"
#include "game/OwnedTaiwanPkReturnRoleTextSource.h"
#include "protocol/RecoveredRemoteRoleText.h"
#include "protocol/RecoveredGuildChat.h"
#include "text/LegacyChineseCodec.h"
#include "text/NativePeerRoleTextCodec.h"
#include <limits>
#include <iterator>
#include <stdexcept>
#include <type_traits>
#include <utility>

namespace god2::cn {
struct SharedActorVisibility::ChatActorSnapshot::State {
    Entry entry;
    std::variant<std::shared_ptr<Session>,std::shared_ptr<SharedCredentialConnection>> receiver;
};
struct SharedActorVisibility::TaiwanAppearanceState {
    TaiwanAppearanceState(ChatActorSnapshot token,TaiwanAppearanceSource supply,TaiwanAppearanceCompletion complete)
        :before(std::move(token)),source(std::move(supply)),done(std::move(complete)) {}
    ChatActorSnapshot before;
    std::optional<ChatActorSnapshot> after;
    std::shared_ptr<const TaiwanAppearanceAfterState> receipt;
    TaiwanAppearanceSource source;
    TaiwanAppearanceCompletion done;
    std::shared_ptr<Session> receiver;
    std::shared_ptr<SharedActorVisibility> owner_keepalive;
    std::uint64_t nonce=0,battle=0;
    bool checking=false,poisoned=false,issued=false,published=false,finished=false;
};
struct SharedActorVisibility::TaiwanPkDepartureState {
    TaiwanPkDepartureState(std::shared_ptr<const Identity> id,std::array<Lease,2> owners,
        const std::array<std::shared_ptr<Session>,2>& sessions,std::array<Session::NativePkEntryHold,2> transports)
        :identity(std::move(id)),leases(std::move(owners)),connections{sessions[0],sessions[1]},holds(std::move(transports)){}
    std::shared_ptr<const Identity> identity;
    std::array<Lease,2> leases;
    std::array<std::weak_ptr<Session>,2> connections;
    std::array<Session::NativePkEntryHold,2> holds;
    std::array<RecoveredPosition,2> positions{};
    std::array<bool,2> retiring{};
    bool poisoned=false;
};
// CUSTOM-0133 preallocated nodes and ordered native records remain private.
// This plan is consumed only through its exact private Held successor below.
struct SharedActorVisibility::TaiwanPkReturnPlan::State {
    State(TaiwanPkDeparture departed,std::array<Lease,2> owners,std::array<RecoveredPosition,2> poses,
        std::array<std::shared_ptr<Session>,2> peers,std::array<Session::NativePkEntryHold,2> entries,
        std::array<Session::NativePkReturnPreparation,2> returns,TaiwanReturnScene supplied)
        :departure(std::move(departed)),leases(std::move(owners)),positions(std::move(poses)),
         sessions(std::move(peers)),holds(std::move(entries)),preparations(std::move(returns)),scene(std::move(supplied)){}
    TaiwanPkDeparture departure;
    std::array<Lease,2> leases;
    std::array<RecoveredPosition,2> positions;
    std::array<std::shared_ptr<Session>,2> sessions;
    std::array<Session::NativePkEntryHold,2> holds;
    std::array<Session::NativePkReturnPreparation,2> preparations;
    TaiwanReturnScene scene;
    std::shared_ptr<const Identity> identity;
    std::uint64_t base_generation=0;
    std::map<Key,Entry> baseline,staged;
    std::map<Key,TaiwanReturnActor> actors;
    struct Endpoint {Lease lease;RecoveredPosition position;std::shared_ptr<Session> session;std::uint64_t battle;};
    std::map<std::uint64_t,Endpoint> endpoints;
    std::array<std::vector<god2cn::Bytes>,2> incoming_records,outgoing_records;
    // CUSTOM-0134 every ordered copy is allocated before actual name readers.
    struct RecordSlot {std::size_t member,side,index;};
    std::map<Key,std::vector<RecordSlot>> record_slots;
    // CUSTOM-0135/0136 canonical map order, joint text/guild row per directed edge.
    std::vector<OwnedTaiwanPkReturnRoleTextSource::Observation> role_rows;
    // CUSTOM-0137 current common endpoints, independent of directed text rows.
    // Both participants exist here even when no fullactor edge was selected.
    std::vector<OwnedTaiwanPkReturnRoleTextSource::EndpointRequest> endpoint_requests;
    std::vector<OwnedTaiwanPkReturnRoleTextSource::EndpointObservation> endpoint_rows;
    bool poisoned=false;
};
// Owning source only: visibility does not retain this token, so there is no
// owner/token registry cycle. The actual game owner retains and destroys it.
struct SharedActorVisibility::TaiwanPkReturnRecords::State {
    State(std::shared_ptr<SharedActorVisibility> owner,std::shared_ptr<TaiwanPkReturnPlan::State> source,
        Session::NativePkReturnReservation reserved,std::vector<Record> ordered)
        :creator(std::move(owner)),plan(std::move(source)),reservation(std::move(reserved)),records(std::move(ordered)){}
    std::shared_ptr<SharedActorVisibility> creator;
    std::shared_ptr<TaiwanPkReturnPlan::State> plan;
    Session::NativePkReturnReservation reservation;
    const std::vector<Record> records;
};
const std::vector<SharedActorVisibility::TaiwanPkReturnRecords::Record>&
SharedActorVisibility::TaiwanPkReturnRecords::records()const noexcept {return state_->records;}
struct SharedActorVisibility::TaiwanPkReturnConsumption::State {
    State(TaiwanPkReturnRecords source,Session::NativePkReturnOutputPlan output,
        Session::NativePkReturnOutputHold held,Session::NativePkReturnConsumption successor)
        :records(std::move(source)),output_plan(std::move(output)),output_hold(std::move(held)),
         transport(std::move(successor)),expected(records.state_->plan->staged){}
    const TaiwanPkReturnRecords records;
    const Session::NativePkReturnOutputPlan output_plan;
    const Session::NativePkReturnOutputHold output_hold;
    const Session::NativePkReturnConsumption transport;
    std::optional<Session::NativePkReturnPublication> publication; // Game-owned Custody only.
    std::optional<Session::NativePkReturnFinalisation> finalisation;
    bool finished=false; // Exact successful model adoption, never a guessed ACK.
    const std::map<Key,Entry> expected; // Survives node transfer; allocated BEFORE final observers.
    std::map<std::uint64_t,std::weak_ptr<State>> registrations;
    std::weak_ptr<State> identity;
    bool claimed=false,published=false,poisoned=false;
    ~State(){records.state_->creator->cancel_taiwan_pk_return_consumption_state(*this);}
};
void SharedActorVisibility::reject_taiwan_return_reentry()const {
    owner();
    if(taiwan_return_reading_){taiwan_return_reentered_=true;
        throw std::logic_error("TW pure return source reentered visibility mutation");}
}
bool SharedActorVisibility::taiwan_pk_return_population_fence(const std::shared_ptr<TaiwanPkReturnPlan::State>& state)const {
    owner();if(!state)return false;
    const auto& scene=state->scene;
    const bool population=bool(scene.ready_population),source=bool(scene.actor_saved_source),rows=bool(scene.actor_saved_rows);
    if(!population && !source && !rows)return !scene.actor_input&&
        scene.actor_profile_equipment.empty()&&!scene.actor_profile_equipment_required; // Existing full supplier contract.
    if(!population || !source || !rows || !scene.actor_saved_source->owns_presence(presence_) ||
       !scene.actor_saved_source->owns_readset(*scene.actor_saved_rows) ||
       !presence_->retained_population_current(*scene.ready_population) ||
       !scene.actor_saved_rows->matches_population(scene.ready_population->characters()))return false;
    if(scene.actor_input&&(scene.actor_input->initial_population()||scene.actor_input->source()!=scene.actor_saved_source||
       scene.actor_input->role_text_source()!=scene.role_text_source||
       scene.actor_input->population()!=*scene.ready_population||
       scene.actor_input->readset()!=*scene.actor_saved_rows))return false;
    if(scene.actor_profile_equipment_required&&!scene.actor_input)return false;
    // A complete population is not the visible edge list. Every selected
    // endpoint and both actual returners must belong to this same full readset.
    const auto ready=scene.ready_population->characters();
    for(const auto& [session,endpoint]:state->endpoints){
        std::size_t matches=0;
        for(const auto& actor:ready)
            if(actor.lease.session==session && actor.lease==endpoint.lease && actor.position==endpoint.position)++matches;
        if(matches!=1)return false;
    }
    const auto& profiles=scene.actor_profile_equipment;
    for(std::size_t i=0;i<profiles.size();++i){
        const auto& observed=profiles[i];
        const auto row=observed.row_index();
        if(row>=ready.size()||
           !scene.actor_saved_source->profile_equipment_matches(observed,*scene.actor_saved_rows,row))return false;
        for(std::size_t j=0;j<i;++j)if(profiles[j].row_index()==row)return false;
        bool selected=false;
        for(const auto& [key,actor]:state->actors)if(actor.source==ready[row].lease){selected=true;break;}
        if(!selected)return false;
    }
    if(scene.actor_profile_equipment_required)for(const auto& [key,actor]:state->actors){
        std::size_t matches=0;
        for(const auto& observed:profiles)if(ready[observed.row_index()].lease==actor.source){
            ++matches;
            // CUSTOM-0133 fresh ordinary appearance projection, not a remote
            // DA-after-cache display claim. Pure byte equality with the exact
            // private joined witness; no parser, allocation or observer here.
            const auto& raw=observed.equipment().record;
            if(raw.size()!=NativeEquipmentSnapshot::record_bytes)return false;
            const auto spawn=RecoveredRemoteActor::encode_logical(actor.native.spawn);
            for(std::size_t component=0;component<8;++component)
                if(spawn[21+component]!=raw[NativeEquipmentSnapshot::inventory_bytes+
                    RecoveredTaiwanPlayerAppearanceUpdate::components_offset+component])return false;
            if(spawn[77]!=raw[NativeEquipmentSnapshot::inventory_bytes+RecoveredTaiwanPlayerAppearanceUpdate::transform_offset]||
               spawn[78]!=raw[NativeEquipmentSnapshot::inventory_bytes+RecoveredTaiwanPlayerAppearanceUpdate::transform_offset+1]||
               spawn[79]!=raw[NativeEquipmentSnapshot::inventory_bytes+RecoveredTaiwanPlayerAppearanceUpdate::raw_scalar5_offset]||
               spawn[80]!=raw[NativeEquipmentSnapshot::inventory_bytes+RecoveredTaiwanPlayerAppearanceUpdate::raw_scalar6_offset])return false;
        }
        if(matches!=1)return false;
    }
    return true;
}
bool SharedActorVisibility::taiwan_pk_return_status_unit_matches(const TaiwanReturnActor& actor)const noexcept {
    if(!actor.status_publication)return true; // Existing external status source.
    const auto& unit=*actor.status_publication;
    if(!unit.retained()||unit.source()!=actor.source||unit.recipient()!=actor.recipient||!actor.actor_override)return false;
    const auto spawn=RecoveredRemoteActor::encode_logical(actor.native.spawn);
    const auto& replay=actor.actor_override->replay();const auto& logical=unit.logical();
    const auto size=spawn.size()+(replay?RecoveredTaiwanActorOverride::logical_size:0);
    if(logical.size()!=size||!std::equal(spawn.begin(),spawn.end(),logical.begin()))return false;
    if(replay){
        const auto bytes=RecoveredTaiwanActorOverride::encode_logical(*replay);
        if(!std::equal(bytes.begin(),bytes.end(),logical.begin()+spawn.size()))return false;
    }
    // Cached complete bytes and atomics only. No text/source/SQL callback or allocation.
    return unit.retained();
}
bool SharedActorVisibility::taiwan_pk_return_fence(const std::shared_ptr<TaiwanPkReturnPlan::State>& state)const {
    // Pure registry/Session fence: no source/repository/name callbacks.
    if(!state||state->poisoned||taiwan_return_reentered_||state->identity!=identity_||
       generation_!=state->base_generation||state->baseline.size()!=entries_.size()||taiwan_pk_return_pending(state)||
       !taiwan_pk_return_population_fence(state))return false;
    for(std::uint8_t i=0;i<2;++i)
        if(!state->sessions[i]||!state->sessions[i]->native_pk_return_preparation_current(state->preparations[i])||
           !taiwan_pk_departure_retained_current(state->departure,state->leases,state->positions,
                state->sessions,state->holds,i))return false;
    const auto endpoint=[&](const Lease& lease,const std::shared_ptr<Session>& session){
        if(!session||!presence_->retained_ready_current(lease)||
           !session->same_native_pk_game_executor(*state->sessions[0]))return false;
        for(std::size_t i=0;i<2;++i)if(lease==state->leases[i])return session==state->sessions[i];
        const auto endpoint=state->endpoints.find(lease.session);
        return !taiwan_pk_departed(lease)&&!session->closing()&&session->id()==lease.session&&
            session->account_id==lease.account&&session->character_id==lease.character&&
            session->recovered_world_ready()&&session->state()==SessionState::InWorld&&
            endpoint!=state->endpoints.end()&&endpoint->second.lease==lease&&endpoint->second.session==session&&
            session->battle_generation()==endpoint->second.battle&&
            session->common_world_delivery_current(lease.account,lease.character,lease.generation);
    };
    if(!taiwan_pk_return_models_match(state->baseline))return false;
    for(const auto& [key,actor]:state->actors){
        const auto receiver=actor.native.connection.lock();
        std::size_t count=0;
        for(const auto& [present,entry]:entries_)if(present.second==key.second)++count;
        for(const auto& [prepared,other]:state->actors)if(prepared.second==key.second)++count;
        if(!taiwan_pk_return_status_unit_matches(actor)||
           !endpoint(actor.source,actor.source_connection)||!endpoint(actor.recipient,receiver)||
           outward_pending(actor.source)||outward_pending(actor.recipient)||
           taiwan_appearance_pending(key)||entries_.contains(key)||count>128)return false;
    }
    // Departure must still have no incident old models, including empty plans.
    for(const auto& [key,entry]:entries_)for(const auto& lease:state->leases)
        if(key.first==lease.session||key.second==lease.session)return false;
    return true;
}
bool SharedActorVisibility::taiwan_pk_return_models_match(const std::map<Key,Entry>& expected)const {
    for(const auto& [key,entry]:expected){
        const auto actual=entries_.find(key);
        if(actual==entries_.end()||!matches(entry.binding,actual->second)||
           actual->second.position!=entry.position||actual->second.last_taiwan_appearance!=entry.last_taiwan_appearance)
            return false;
        const bool same=std::visit([&](const auto& before){
            using Output=std::decay_t<decltype(before)>;
            const auto* now=std::get_if<Output>(&actual->second.native);
            if(!now||now->connection.lock()!=before.connection.lock()||
               now->common_name_source!=before.common_name_source||
               bool(now->raw_name_state)!=bool(before.raw_name_state))return false;
            if constexpr(std::is_same_v<Output,Taiwan>){
                if(RecoveredRemoteActor::encode_logical(now->spawn)!=RecoveredRemoteActor::encode_logical(before.spawn)||
                   RecoveredRemoteActorMove::encode_logical(now->movement)!=RecoveredRemoteActorMove::encode_logical(before.movement)||
                   RecoveredRemoteActorRemove::encode_logical(now->removal)!=RecoveredRemoteActorRemove::encode_logical(before.removal))return false;
                return !now->raw_name_state||now->raw_name_state->same_source(*before.raw_name_state);
            }else{
                if(god2cn::CnRemoteActor::encode_logical(now->spawn)!=god2cn::CnRemoteActor::encode_logical(before.spawn)||
                   god2cn::CnRemoteActorMove::encode_logical(now->movement)!=god2cn::CnRemoteActorMove::encode_logical(before.movement)||
                   god2cn::CnRemoteActorRemove::encode_logical(now->removal)!=god2cn::CnRemoteActorRemove::encode_logical(before.removal)||
                   now->normal_source!=before.normal_source)return false;
                return !now->raw_name_state||(now->raw_name_state->source_revision==before.raw_name_state->source_revision&&
                    now->raw_name_state->wire_codepage==before.raw_name_state->wire_codepage);
            }
        },entry.native);
        if(!same)return false;
    }
    return true;
}
bool SharedActorVisibility::taiwan_pk_return_read(const std::shared_ptr<TaiwanPkReturnPlan::State>& state,
        TaiwanReturnCheck check,bool stored_only,
        const std::shared_ptr<TaiwanPkReturnConsumption::State>& successor,sqlite3* in_scope)const {
    owner();
    if(taiwan_return_reading_){taiwan_return_reentered_=true;if(state)state->poisoned=true;return false;}
    taiwan_return_reading_=true;taiwan_return_reentered_=false;
    struct End{
        bool& busy;bool& reentered;
        const std::shared_ptr<TaiwanPkReturnPlan::State>& state;
        ~End(){if(reentered&&state)state->poisoned=true;busy=false;}
    }end{taiwan_return_reading_,taiwan_return_reentered_,state};
    if((in_scope&&!stored_only)||(check==TaiwanReturnCheck::Consumed)!=bool(successor)||
       (successor&&successor->records.state_->plan!=state))return false;
    const auto valid=[&]{return successor?taiwan_pk_return_consumption_fence(successor,true):taiwan_pk_return_fence(state);};
    try{
        // CUSTOM-0136 actual Publication requalifies terminal SQL after full
        // scene observation. Close that tail without replaying scene/name/pose
        // callbacks. The same persistent visibility guard covers SQLite hooks.
        if(stored_only){
            if(!valid())return false;
            const auto source=state->scene.role_text_source;
            const auto saved=state->scene.actor_saved_source;
            if(saved){
                if(in_scope){
                    // Both known closed readers share the actual room's one
                    // transaction. No scene/session/resource/provider callbacks.
                    if(!saved->stored_current_in_scope(in_scope,*state->scene.actor_saved_rows,
                            state->scene.actor_profile_equipment)||!valid())return false;
                    if(source&&(!source->owns_presence(presence_)||state->role_rows.size()!=state->actors.size()||
                       state->endpoint_rows.size()!=state->endpoints.size()||
                       !source->stored_current_in_scope(in_scope,state->role_rows,state->endpoint_rows)||!valid()))return false;
                    return valid(); // Saved readset is checked even without role text.
                }
                if(source&&(!source->owns_presence(presence_)||state->role_rows.size()!=state->actors.size()||
                   state->endpoint_rows.size()!=state->endpoints.size()))return false;
                return saved->current_with_role_text(*state->scene.actor_saved_rows,source,
                    state->role_rows,state->endpoint_rows,state->scene.actor_profile_equipment)&&valid();
            }
            if(!source)return !in_scope&&valid();
            return source->owns_presence(presence_)&&state->role_rows.size()==state->actors.size()&&
                state->endpoint_rows.size()==state->endpoints.size()&&
                (in_scope?source->stored_current_in_scope(in_scope,state->role_rows,state->endpoint_rows):
                    source->stored_current(state->role_rows,state->endpoint_rows))&&valid();
        }
        if(!valid())return false;
        const auto saved_source=state->scene.actor_saved_source;
        if(saved_source&&(!saved_source->current(*state->scene.actor_saved_rows)||!valid()))return false;
        if(!state->scene.current||!state->scene.current(check)||!valid())return false;
        // Empty scenes still qualify BOTH exact saved participant poses.
        for(std::size_t i=0;i<2;++i)
            if(presence_->saved_position(state->leases[i])!=std::optional{state->positions[i]}||!valid())return false;
        const auto role_source=state->scene.role_text_source;
        if(role_source&&(!role_source->owns_presence(presence_)||!valid()||
           (check==TaiwanReturnCheck::Prepare?
                (!state->role_rows.empty()||!state->endpoint_rows.empty()):
                (state->role_rows.size()!=state->actors.size()||state->endpoint_rows.size()!=state->endpoints.size()))))return false;
        std::size_t role_index=0;
        for(auto& [key,actor]:state->actors){
            if(presence_->saved_position(actor.source)!=std::optional{actor.source_position}||!valid()||
               presence_->saved_position(actor.recipient)!=std::optional{actor.recipient_position}||!valid()||
               !actor.qualification->current()||!valid())return false;
            const auto receiver=actor.native.connection.lock();const auto raw=*actor.native.raw_name_state;
            if(!receiver||!raw.current(*receiver)||!valid()||
               !raw.permits_source_codepage(RecoveredRemoteRoleText::source_codepage(actor.native.spawn)))return false;
            // CUSTOM-0134 this private paired return authority already qualified
            // BOTH genuine terminal preparations; ordinary departed wrappers
            // remain closed. Reuse the actual common stored-name owner, never
            // an invented full6F issuer or a legacy raw-name witness.
            const auto issuer=actor.native.common_name_source;
            if(issuer){
                if(!issuer->owns_presence(presence_)||!valid())return false;
                if(check==TaiwanReturnCheck::Prepare){
                    const auto before=RecoveredRemoteActor::encode_logical(actor.native.spawn);
                    const auto projected=issuer->project(actor.source,actor.recipient,Native{actor.native});
                    if(!projected||!valid())return false;
                    const auto* native=std::get_if<Taiwan>(&*projected);
                    if(!native||native->connection.lock()!=receiver||native->common_name_source!=issuer||
                       !native->raw_name_state||
                       !native->raw_name_state->same_source(raw)||
                       RecoveredRemoteActorMove::encode_logical(native->movement)!=RecoveredRemoteActorMove::encode_logical(actor.native.movement)||
                       RecoveredRemoteActorRemove::encode_logical(native->removal)!=RecoveredRemoteActorRemove::encode_logical(actor.native.removal))return false;
                    const auto after=RecoveredRemoteActor::encode_logical(native->spawn);
                    for(std::size_t offset=0;offset<before.size();++offset)
                        if((offset<29||offset>=45)&&before[offset]!=after[offset])return false;
                    // Assign only the immutable first-name projection. The
                    // canonical qualification/raw callback and all other model
                    // fields retain their exact owned inputs. No allocation.
                    actor.native.spawn=native->spawn;
                    std::get<Taiwan>(state->staged.at(key).native).spawn=native->spawn;
                    for(const auto& slot:state->record_slots.at(key)){
                        auto& records=slot.side==0?state->incoming_records[slot.member]:state->outgoing_records[slot.member];
                        auto& record=records.at(slot.index);
                        for(std::size_t offset=29;offset<45;++offset)record[offset]=after[offset];
                    }
                }else if(!issuer->current(actor.source,actor.recipient,Native{actor.native})||!valid())return false;
            }
            // CUSTOM-0135/0136 actual common secondary/guild text, never the
            // legacy blank-on-failure projector or a supplied row callback.
            if(role_source){
                if(check==TaiwanReturnCheck::Prepare){
                    auto observed=role_source->observe(actor.source);
                    if(!observed||!valid())return false;
                    state->role_rows.emplace_back(std::move(*observed));
                }else if(!role_source->current(state->role_rows.at(role_index))||!valid())return false;
                const auto& observation=state->role_rows.at(role_index++);
                const auto& saved=observation.row();
                const auto source_page=RecoveredRemoteRoleText::source_codepage(actor.native.spawn);
                // Raw NLS authority remains explicit; a typed accepted C1C
                // selects only exact same-page bytes, without adaptation.
                if(!raw.available()||!raw.permits_source_codepage(source_page))return false;
                const auto text=SqliteRoleTextRepository::project(saved,source_page);
                if(!text)return false;
                const auto end=std::find(text->begin(),text->end(),0);
                const std::string_view bytes(reinterpret_cast<const char*>(text->data()),
                    static_cast<std::size_t>(end-text->begin()));
                if(!NativePeerRoleTextCodec::project(bytes,source_page,raw.wire_codepage()))return false;
                const auto secondary=RecoveredRemoteRoleText::with_source_text(actor.native.spawn,*text);
                if(!secondary||!valid())return false;
                // Native2D assigns the local saved third string; remote6F61
                // reaches that same third display setter. CUSTOM-0075 supplies
                // our actual common guild membership/name, not native storage.
                // Only a successfully observed nonmember produces empty text.
                const auto& guild=observation.guild();
                const auto guild_name=guild?LegacyChineseCodec::encode(guild->name_utf8,source_page==936):std::string{};
                if(guild&&LegacyChineseCodec::decode(guild_name,source_page==936)!=guild->name_utf8)return false;
                const auto local_name=RecoveredGuildChat::name(guild_name);
                if(!NativePeerRoleTextCodec::project(guild_name,source_page,raw.wire_codepage())||!valid())return false;
                auto projected_bytes=RecoveredRemoteActor::encode_logical(*secondary);
                std::copy(local_name.begin()+1,local_name.end(),projected_bytes.begin()+61);
                const auto projected=RecoveredRemoteActor::parse_logical(projected_bytes);
                if(!projected)return false;
                const auto before=RecoveredRemoteActor::encode_logical(actor.native.spawn);
                const auto after=RecoveredRemoteActor::encode_logical(*projected);
                // All post-preparation reads compare the immutable full bytes;
                // Consumed must never rewrite staged nodes after their transfer.
                if(check!=TaiwanReturnCheck::Prepare){if(before!=after)return false;}
                else{
                    for(std::size_t offset=0;offset<before.size();++offset)
                        if((offset<45||offset>=77)&&before[offset]!=after[offset])return false;
                    actor.native.spawn=*projected;
                    std::get<Taiwan>(state->staged.at(key).native).spawn=*projected;
                    for(const auto& slot:state->record_slots.at(key)){
                        auto& records=slot.side==0?state->incoming_records[slot.member]:state->outgoing_records[slot.member];
                        auto& record=records.at(slot.index);
                        for(std::size_t offset=45;offset<77;++offset)record[offset]=after[offset];
                    }
                }
            }
        }
        // The full supplier requalifies ordered selection/entire current after
        // all position/resource/native-name observers. Final fence is pure.
        if(!state->scene.current(check)||!valid())return false;
        if(role_source&&check==TaiwanReturnCheck::Prepare){
            auto observed=role_source->observe_endpoints(state->endpoint_requests);
            if(!observed||observed->size()!=state->endpoints.size()||!valid())return false;
            state->endpoint_rows=std::move(*observed);
        }
        // All rows in ONE final read snapshot after every external scene,
        // name, profile and presence observer; secondary and guild share the
        // same snapshot. No callbacks after this cut.
        if(saved_source){
            // One final same-connection read scope closes the complete saved
            // population together with all optional role/guild/endpoint rows.
            // No external source callbacks follow this joint cut.
            if(!saved_source->current_with_role_text(*state->scene.actor_saved_rows,role_source,
                    state->role_rows,state->endpoint_rows,state->scene.actor_profile_equipment)||!valid())return false;
        }else if(role_source&&(!role_source->stored_current(state->role_rows,state->endpoint_rows)||!valid()))return false;
        return valid();
    }catch(...){state->poisoned=true;return false;}
}
std::optional<SharedActorVisibility::TaiwanPkReturnPlan> SharedActorVisibility::prepare_taiwan_pk_return(
        const TaiwanPkDeparture& departure,std::array<Lease,2> leases,std::array<RecoveredPosition,2> positions,
        std::array<std::shared_ptr<Session>,2> sessions,std::array<Session::NativePkEntryHold,2> holds,
        std::array<Session::NativePkReturnPreparation,2> preparations,TaiwanReturnScene scene){
    owner();
    if(taiwan_return_reading_){taiwan_return_reentered_=true;return {};}
    auto state=std::make_shared<TaiwanPkReturnPlan::State>(departure,leases,positions,
        std::move(sessions),std::move(holds),std::move(preparations),std::move(scene));
    state->identity=identity_;state->base_generation=generation_;state->baseline=entries_;
    if(!state->scene.current)return {};
    for(std::uint8_t i=0;i<2;++i)
        if(!state->sessions[i]||!state->sessions[i]->native_pk_return_preparation_current(state->preparations[i])||
           !taiwan_pk_departure_retained_current(departure,leases,positions,state->sessions,state->holds,i))return {};
    const auto pair_index=[&](const Lease& lease)->std::optional<std::size_t>{
        for(std::size_t i=0;i<2;++i)if(lease==leases[i])return i;return {};
    };
    const auto equal=[](const TaiwanReturnActor& a,const TaiwanReturnActor& b){
        return a.source==b.source&&a.recipient==b.recipient&&a.source_position==b.source_position&&
            a.recipient_position==b.recipient_position&&a.source_connection==b.source_connection&&
            a.native.connection.lock()==b.native.connection.lock()&&a.qualification==b.qualification&&
            a.native.common_name_source==b.native.common_name_source&&a.actor_override==b.actor_override&&
            a.status_publication==b.status_publication&&
            RecoveredRemoteActor::encode_logical(a.native.spawn)==RecoveredRemoteActor::encode_logical(b.native.spawn)&&
            RecoveredRemoteActorMove::encode_logical(a.native.movement)==RecoveredRemoteActorMove::encode_logical(b.native.movement)&&
            RecoveredRemoteActorRemove::encode_logical(a.native.removal)==RecoveredRemoteActorRemove::encode_logical(b.native.removal);
    };
    std::map<Key,std::uint8_t> occurrences;
    std::map<std::uint64_t,std::shared_ptr<const TaiwanReceiverTextState>> receiver_profiles;
    // CUSTOM-0137 an empty scene is not permission to omit the returning pair's
    // actual current roots/poses. Actor loops below retain exact deduplication.
    for(std::size_t i=0;i<2;++i)
        if(!state->endpoints.emplace(leases[i].session,TaiwanPkReturnPlan::State::Endpoint{
                leases[i],positions[i],state->sessions[i],state->sessions[i]->battle_generation()}).second)return {};
    for(std::size_t i=0;i<2;++i)for(std::size_t side=0;side<2;++side){
        const auto& actors=side==0?state->scene.incoming[i]:state->scene.outgoing[i];
        //128 is the recovered per-receiver actor pool.256 outgoing is only
        // this opt-in server allocation quota, not an original sender rule.
        if(actors.size()>(side==0?128u:256u))return {};
        auto& records=side==0?state->incoming_records[i]:state->outgoing_records[i];records.reserve(actors.size());
        for(const auto& actor:actors){
            const auto receiver=actor.native.connection.lock();
            if((side==0?actor.recipient:actor.source)!=leases[i]||!actor.source_connection||!receiver||
               actor.source.session==actor.recipient.session||actor.source.character==actor.recipient.character||
               actor.source.actor_handle>0xfff||actor.source_position.area!=actor.recipient_position.area||
               actor.source_position.scene!=actor.recipient_position.scene||
               !actor.actor_override||!actor.qualification||!actor.qualification->revision||!actor.qualification->current||

               actor.native.spawn.identity()!=actor.source.actor_handle||actor.native.removal.identity()!=actor.source.actor_handle||
               actor.native.movement.identity()!=actor.source.actor_handle||
               actor.native.spawn.x()!=actor.source_position.x||actor.native.spawn.y()!=actor.source_position.y||
               actor.native.movement.x()!=actor.source_position.x||actor.native.movement.y()!=actor.source_position.y)return {};
            // Native EA uses full WORD identity, without the6F12-bit mask.
            // This path is remote only; its self consumer has different state.
            if(const auto& replay=actor.actor_override->replay();replay&&
               (replay->identity()!=actor.source.actor_handle||replay->is_self(actor.recipient.actor_handle)))return {};
            // Concrete receiving profile producer, after exact private endpoint
            // checks. Never derive fake D8/DA from a public language scalar.
            std::shared_ptr<const TaiwanReceiverTextState> profile;
            if(actor.qualification->receiver_text)
                profile=std::make_shared<const TaiwanReceiverTextState>(*actor.qualification->receiver_text);
            else{
                const auto member=pair_index(actor.recipient);
                const auto selector=member?receiver->native_taiwan_return_receiver_selector(state->preparations[*member]):
                    receiver->native_taiwan_receiver_selector_on_game();
                if(!selector)return {};
                profile=std::make_shared<const TaiwanReceiverTextState>(*selector);
            }
            if(!profile->available())return {};
            const auto [canonical,first_profile]=receiver_profiles.emplace(actor.recipient.session,profile);
            if(!first_profile&&!canonical->second->same_source(*profile))return {};
            profile=canonical->second;
            // Complete supplied actor/resources/override remains mandatory.
            // Text2/3 are replaced only by the factory-owned actual saved source.
            // Optional common stored first-name source is qualified privately
            // only after all nodes and ordered copies have been allocated.
            const auto record=RecoveredRemoteActor::encode_logical(actor.native.spawn);
            if(actor.native.movement.state()!=(std::uint16_t(record[7])|(std::uint16_t(record[8])<<8)))return {};
            for(const auto& [lease,session]:{std::pair{actor.source,actor.source_connection},std::pair{actor.recipient,receiver}}){
                const auto pose=lease==actor.source?actor.source_position:actor.recipient_position;
                if(!session->same_native_pk_game_executor(*state->sessions[0]))return {};
                const auto [endpoint,inserted]=state->endpoints.emplace(lease.session,
                    TaiwanPkReturnPlan::State::Endpoint{lease,pose,session,session->battle_generation()});
                if(!inserted&&(endpoint->second.lease!=lease||endpoint->second.position!=pose||
                   endpoint->second.session!=session||endpoint->second.battle!=session->battle_generation()))return {};
                if(const auto member=pair_index(lease)){
                    if(session!=state->sessions[*member]||
                       pose!=positions[*member])return {};
                }
            }
            const Key key{actor.source.session,actor.recipient.session};const auto bit=std::uint8_t(1u<<(i*2+side));
            if(occurrences[key]&bit)return {};occurrences[key]|=bit;
            const auto [found,inserted]=state->actors.emplace(key,actor);
            if(!inserted&&!equal(found->second,actor))return {};
            // Explicit canonical actual receiver witness, no name/byte rewrite.
            found->second.native.raw_name_state=*profile;
            state->record_slots[key].push_back({i,side,records.size()});
            records.emplace_back(record.begin(),record.end());
        }
    }
    for(const auto& [key,actor]:state->actors){
        std::uint8_t expected=0;
        if(const auto source=pair_index(actor.source))expected|=std::uint8_t(1u<<(*source*2+1));
        if(const auto recipient=pair_index(actor.recipient))expected|=std::uint8_t(1u<<(*recipient*2));
        if(!expected||occurrences.at(key)!=expected)return {}; // Mutual directed edge deduplicated exactly once.
        if(state->staged.size()==std::numeric_limits<std::uint64_t>::max()-generation_)return {};
        Binding binding(identity_,actor.source,actor.recipient,generation_+state->staged.size()+1);
        state->staged.emplace(key,Entry{binding,actor.source_position,Native{actor.native}});
    }
    if(state->scene.role_text_source){
        state->role_rows.reserve(state->actors.size());
        state->endpoint_requests.reserve(state->endpoints.size());
        for(const auto& [session,endpoint]:state->endpoints)
            state->endpoint_requests.push_back({endpoint.lease,endpoint.position});
    }
    if(!taiwan_pk_return_read(state,TaiwanReturnCheck::Prepare))return {};
    return TaiwanPkReturnPlan(std::move(state));
}
bool SharedActorVisibility::taiwan_pk_return_current(const TaiwanPkReturnPlan& plan)const {
    const auto state=plan.state_; // Own private material before source callbacks.
    return taiwan_pk_return_read(state,TaiwanReturnCheck::Retained);
}
bool SharedActorVisibility::taiwan_pk_return_stored_current(const TaiwanPkReturnPlan& plan)const {
    const auto state=plan.state_;
    return taiwan_pk_return_read(state,TaiwanReturnCheck::Retained,true);
}
bool SharedActorVisibility::taiwan_pk_return_retained_current(const TaiwanPkReturnPlan& plan)const {
    owner();return taiwan_pk_return_fence(plan.state_);
}
bool SharedActorVisibility::taiwan_pk_return_records_fence(
        const std::shared_ptr<const TaiwanPkReturnRecords::State>& state)const {
    owner();
    if(taiwan_return_reading_){
        taiwan_return_reentered_=true;if(state&&state->plan)state->plan->poisoned=true;return false;
    }
    return state&&state->creator.get()==this&&state->plan&&
        Session::native_pk_return_reservation_matches(state->reservation,state->plan->sessions,state->plan->preparations)&&
        taiwan_pk_return_fence(state->plan)&&
        Session::native_pk_return_reservation_matches(state->reservation,state->plan->sessions,state->plan->preparations);
}
std::optional<SharedActorVisibility::TaiwanPkReturnRecords> SharedActorVisibility::prepare_taiwan_pk_return_records(
        const TaiwanPkReturnPlan& plan,const Session::NativePkReturnReservation& reservation){
    owner();
    if(taiwan_return_reading_){taiwan_return_reentered_=true;if(plan.state_)plan.state_->poisoned=true;return {};}
    // Own actual private inputs before allocation or any scene/repository observer.
    const auto source=plan.state_;const auto reserved=reservation;
    const auto creator=weak_from_this().lock();
    if(!creator||creator.get()!=this||!source||
       !Session::native_pk_return_reservation_matches(reserved,source->sessions,source->preparations)||
       !taiwan_pk_return_fence(source))return {};
    std::vector<TaiwanPkReturnRecords::Record> ordered;ordered.reserve(source->actors.size());
    std::map<Key,bool> emitted; // bool identifies exact incoming directed edges.
    const auto append=[&](const TaiwanReturnActor& supplied,const god2cn::Bytes& bytes,bool incoming){
        const Key key{supplied.source.session,supplied.recipient.session};
        const auto found=source->actors.find(key);
        if(found==source->actors.end())return false;
        const auto& actor=found->second;const auto receiver=actor.native.connection.lock();
        const auto from=source->endpoints.find(key.first),to=source->endpoints.find(key.second);
        const auto logical=RecoveredRemoteActor::encode_logical(actor.native.spawn);
        if(!actor.actor_override||actor.actor_override!=supplied.actor_override||
           actor.status_publication!=supplied.status_publication||!taiwan_pk_return_status_unit_matches(actor)||
           actor.source!=supplied.source||actor.recipient!=supplied.recipient||
           from==source->endpoints.end()||to==source->endpoints.end()||
           from->second.lease!=actor.source||to->second.lease!=actor.recipient||
           from->second.session!=actor.source_connection||to->second.session!=receiver||
           !receiver||bytes.size()!=logical.size()||!std::equal(bytes.begin(),bytes.end(),logical.begin()))return false;
        if(const auto duplicate=emitted.find(key);duplicate!=emitted.end()){
            // Only a mutual outgoing copy already present in incoming is skipped.
            if(incoming||!duplicate->second)return false;
            bool returning_source=false,returning_recipient=false;
            for(const auto& lease:source->leases){returning_source|=lease==actor.source;returning_recipient|=lease==actor.recipient;}
            return returning_source&&returning_recipient;
        }
        emitted.emplace(key,incoming);
        std::optional<RecoveredTaiwanActorOverride::LogicalRecord> actor_override;
        if(const auto& replay=actor.actor_override->replay())
            actor_override=RecoveredTaiwanActorOverride::encode_logical(*replay);
        ordered.push_back(TaiwanPkReturnRecords::Record(actor.source,actor.recipient,
            actor.source_connection,receiver,bytes,std::move(actor_override),actor.status_publication));
        return true;
    };
    // Each returning recipient keeps its supplied incoming order.
    for(std::size_t member=0;member<2;++member){
        const auto& actors=source->scene.incoming[member];const auto& records=source->incoming_records[member];
        if(actors.size()!=records.size())return {};
        for(std::size_t at=0;at<actors.size();++at)
            if(actors[at].recipient!=source->leases[member]||!append(actors[at],records[at],true))return {};
    }
    // CUSTOM-0133 deterministic normal-observer composition: member0 then1,
    // preserving within-member order. Not a recovered joint native sender order.
    for(std::size_t member=0;member<2;++member){
        const auto& actors=source->scene.outgoing[member];const auto& records=source->outgoing_records[member];
        if(actors.size()!=records.size())return {};
        for(std::size_t at=0;at<actors.size();++at)
            if(actors[at].source!=source->leases[member]||!append(actors[at],records[at],false))return {};
    }
    if(ordered.size()!=source->actors.size()||emitted.size()!=source->actors.size())return {};
    // All logical copies/holders and token storage precede the actual observers.
    // A deliberate empty source remains empty; no frame or placeholder is added.
    const auto state=std::make_shared<const TaiwanPkReturnRecords::State>(creator,source,reserved,std::move(ordered));
    if(!taiwan_pk_return_records_fence(state)||
       !taiwan_pk_return_read(source,TaiwanReturnCheck::Retained)||
       !taiwan_pk_return_records_fence(state))return {};
    return TaiwanPkReturnRecords(state);
}
bool SharedActorVisibility::taiwan_pk_return_records_current(const TaiwanPkReturnRecords& records)const {
    const auto state=records.state_;
    return taiwan_pk_return_records_fence(state)&&
        taiwan_pk_return_read(state->plan,TaiwanReturnCheck::Retained)&&taiwan_pk_return_records_fence(state);
}
bool SharedActorVisibility::taiwan_pk_return_records_stored_current(const TaiwanPkReturnRecords& records)const {
    const auto state=records.state_;
    return taiwan_pk_return_records_fence(state)&&
        taiwan_pk_return_read(state->plan,TaiwanReturnCheck::Retained,true)&&taiwan_pk_return_records_fence(state);
}
bool SharedActorVisibility::taiwan_pk_return_records_retained_current(const TaiwanPkReturnRecords& records)const {
    const auto state=records.state_;return taiwan_pk_return_records_fence(state);
}
bool SharedActorVisibility::taiwan_pk_return_records_matches(const TaiwanPkReturnRecords& records,
        const TaiwanPkReturnPlan& plan,const Session::NativePkReturnReservation& reservation)const {
    const auto state=records.state_;const auto source=plan.state_;const auto reserved=reservation;
    return taiwan_pk_return_records_fence(state)&&state->plan==source&&state->reservation==reserved&&
        taiwan_pk_return_records_fence(state);
}
std::optional<Session::NativePkReturnOutputPlan> SharedActorVisibility::prepare_taiwan_pk_return_output(
        const TaiwanPkReturnRecords& records,const TaiwanPkReturnPlan& plan,
        const Session::NativePkReturnReservation& reservation){
    owner();
    if(!taiwan_pk_return_records_matches(records,plan,reservation))return {};
    const auto state=records.state_;const auto source=plan.state_;
    // Include BOTH actual returning endpoints even when either has no6F. A
    // real empty strand cut must not be represented by a fabricated frame.
    std::vector<Session::NativePkReturnOutputGroup> groups;
    groups.reserve(state->records.size()+2);
    groups.push_back({source->sessions[0],{}});
    groups.push_back({source->sessions[1],{}});
    for(const auto& record:state->records){
        const auto receiver=record.recipient_session();
        if(!receiver||record.logical().size()!=RecoveredRemoteActor::logical_size)return {};
        const auto endpoint=source->endpoints.find(record.recipient().session);
        if(endpoint==source->endpoints.end()||endpoint->second.lease!=record.recipient()||
           endpoint->second.session!=receiver)return {};
        auto group=std::find_if(groups.begin(),groups.end(),[&](const auto& candidate){
            return candidate.recipient==receiver;
        });
        if(group==groups.end()){
            groups.push_back({receiver,{}});group=std::prev(groups.end());
        }
        // Filter the canonical ordered records into their actual recipient;
        // never treat an outgoing SOURCE list as a returning receiver batch.
        auto& actor=group->actors.emplace_back(record.logical());
        // Keep the native6F reset and its optional actual remoteEA together.
        // No normalized-index inversion, guessed clear or self override.
        if(const auto& replay=record.override_logical())
            actor.insert(actor.end(),replay->begin(),replay->end());
        // Parallel optional witnesses preserve every exact actor slot, including
        // genuinely external-status units sharing the same complete frame.
        group->actor_status.push_back(record.status_publication());
        if(const auto& unit=record.status_publication();unit&&
           (!unit->retained()||unit->source()!=record.source()||unit->recipient()!=record.recipient()||
            unit->logical()!=actor))return {};
    }
    const std::weak_ptr<const void> identity(state);
    auto output=Session::prepare_native_pk_return_output(reservation,source->sessions,
        source->preparations,identity,std::move(groups));
    // Session's private factory captures actual survivor INIT/output epochs
    // and allocates complete boundary-preserving frames before these observers.
    if(!taiwan_pk_return_records_current(records)||
       !taiwan_pk_return_output_plan_matches(records,output,plan,reservation))return {};
    return output;
}
bool SharedActorVisibility::taiwan_pk_return_output_plan_matches(const TaiwanPkReturnRecords& records,
        const Session::NativePkReturnOutputPlan& output,const TaiwanPkReturnPlan& plan,
        const Session::NativePkReturnReservation& reservation)const {
    owner();const std::weak_ptr<const void> identity(records.state_);
    return taiwan_pk_return_records_matches(records,plan,reservation)&&
        Session::native_pk_return_output_plan_matches(output,reservation,identity)&&
        taiwan_pk_return_records_matches(records,plan,reservation);
}
std::optional<SharedActorVisibility::TaiwanPkReturnConsumption>
SharedActorVisibility::prepare_taiwan_pk_return_consumption(const TaiwanPkReturnRecords& records,
        const TaiwanPkReturnPlan& plan,const Session::NativePkReturnReservation& reservation,
        const Session::NativePkReturnOutputPlan& output,const Session::NativePkReturnOutputHold& held,
        std::weak_ptr<Session::NativePkReturnConsumptionOwner> owner_source){
    owner();
    if(!taiwan_pk_return_output_plan_matches(records,output,plan,reservation)||
       !Session::native_pk_return_output_matches(held,output,reservation))return {};
    const auto source=records.state_->plan;
    for(const auto& [id,endpoint]:source->endpoints)
        if(const auto at=taiwan_pk_return_consumptions_.find(id);
           at!=taiwan_pk_return_consumptions_.end()&&!at->second.expired())return {};
    // Complete successor/expected entries/registration nodes precede all final
    // resource, scene and SQL observers performed by the actual Outbox owner.
    auto transport=Session::prepare_native_pk_return_consumption(held,std::move(owner_source));
    auto state=std::make_shared<TaiwanPkReturnConsumption::State>(records,output,held,std::move(transport));
    state->identity=state;
    for(const auto& [id,endpoint]:source->endpoints)state->registrations.emplace(id,state);
    if(!taiwan_pk_return_output_plan_matches(records,output,plan,reservation)||
       !Session::native_pk_return_output_matches(held,output,reservation))return {};
    return TaiwanPkReturnConsumption(std::move(state));
}
bool SharedActorVisibility::consume_taiwan_pk_return(const TaiwanPkReturnConsumption& token){
    owner();const auto state=token.state_;
    if(!state||state->claimed||state->poisoned||state->records.state_->creator.get()!=this)return false;
    const auto records=state->records.state_;const auto source=records->plan;
    if(!taiwan_pk_return_records_fence(records)||
       !Session::native_pk_return_output_matches(state->output_hold,state->output_plan,records->reservation))return false;
    for(const auto& [id,endpoint]:source->endpoints){
        const auto at=taiwan_pk_return_consumptions_.find(id);
        if(at!=taiwan_pk_return_consumptions_.end()&&!at->second.expired())return false;
    }
    state->claimed=true; // Once, even a failed transition must never be retried.
    if(!Session::consume_native_pk_return_output(state->transport)){
        state->poisoned=true;source->poisoned=true;return false;
    }
    // No observer, send, allocation or ordinary set_state between Session commit
    // and transfer of the previously qualified exact nodes/departure markers.
    try{
        for(const auto& [id,endpoint]:source->endpoints)
            if(const auto at=taiwan_pk_return_consumptions_.find(id);at!=taiwan_pk_return_consumptions_.end())
                taiwan_pk_return_consumptions_.erase(at); // Only an expired registration admitted above.
        taiwan_pk_return_consumptions_.merge(state->registrations);
        state->published=true; // Cleanup covers any partial node transfer.
        entries_.merge(source->staged);
        generation_+=state->expected.size();
        for(const auto& lease:source->leases){
            const auto at=taiwan_pk_departures_.find(lease.session);
            if(at==taiwan_pk_departures_.end()||at->second!=source->departure.state_)
                throw std::logic_error("Return lost its exact old departure marker");
            taiwan_pk_departures_.erase(at);
        }
        if(!source->staged.empty()||!state->registrations.empty()||
           !taiwan_pk_return_consumption_current(token))throw std::logic_error("Return successor registry commit retired");
        return true;
    }catch(...){cancel_taiwan_pk_return_consumption(token);return false;}
}
bool SharedActorVisibility::taiwan_pk_return_consumption_current(const TaiwanPkReturnConsumption& token)const{
    owner();return taiwan_pk_return_consumption_fence(token.state_);
}
bool SharedActorVisibility::taiwan_pk_return_consumption_fence(
        const std::shared_ptr<TaiwanPkReturnConsumption::State>& state,bool guarded_read)const{
    owner();
    if(!state||state->finished||state->poisoned||!state->claimed||!state->published||
       state->records.state_->creator.get()!=this||
       (taiwan_return_reading_&&!guarded_read)||taiwan_return_reentered_)return false;
    const auto records=state->records.state_;const auto source=records->plan;
    const std::weak_ptr<const void> identity(records);
    if(source->poisoned||source->identity!=identity_||
       !Session::native_pk_return_consumption_matches(state->transport,state->output_hold,state->output_plan,records->reservation)||
       !Session::native_pk_return_consumption_records_matches(state->transport,identity)||
       generation_!=source->base_generation+state->expected.size()||
       entries_.size()!=source->baseline.size()+state->expected.size()||taiwan_pk_return_pending(source)||
       !taiwan_pk_return_models_match(source->baseline)||!taiwan_pk_return_models_match(state->expected)||
       !taiwan_pk_return_population_fence(source))return false;
    for(const auto& lease:source->leases)
        if(taiwan_pk_departures_.contains(lease.session))return false;
    for(const auto& [id,endpoint]:source->endpoints){
        const auto at=taiwan_pk_return_consumptions_.find(id);
        if(at==taiwan_pk_return_consumptions_.end()||at->second.lock()!=state||
           !presence_->retained_ready_current(endpoint.lease)||!endpoint.session||endpoint.session->closing())return false;
        bool returning=false;for(const auto& lease:source->leases)returning|=lease==endpoint.lease;
        if(!returning&&(taiwan_pk_departed(endpoint.lease)||endpoint.session->state()!=SessionState::InWorld||
           endpoint.session->battle_generation()!=endpoint.battle||
           !endpoint.session->common_world_delivery_current(endpoint.lease.account,endpoint.lease.character,endpoint.lease.generation)))return false;
    }
    if(state->publication){
        if(!Session::native_pk_return_publication_matches(*state->publication,state->transport)||
           !Session::native_pk_return_publication_records_matches(*state->publication,identity))return false;
    }
    // This pure status/version/whole-unit cut also follows the final stored or
    // in-scope saved-role-EQ SQL observers through taiwan_pk_return_read.valid().
    for(const auto& [key,actor]:source->actors)
        if(!taiwan_pk_return_status_unit_matches(actor))return false;
    return Session::native_pk_return_consumption_current(state->transport);
}
bool SharedActorVisibility::taiwan_pk_return_consumption_source_current(const TaiwanPkReturnConsumption& token)const{
    const auto state=token.state_;
    return taiwan_pk_return_consumption_fence(state)&&
        taiwan_pk_return_read(state->records.state_->plan,TaiwanReturnCheck::Consumed,false,state)&&
        taiwan_pk_return_consumption_fence(state);
}
bool SharedActorVisibility::taiwan_pk_return_consumption_stored_current(const TaiwanPkReturnConsumption& token)const{
    const auto state=token.state_;
    return taiwan_pk_return_consumption_fence(state)&&
        taiwan_pk_return_read(state->records.state_->plan,TaiwanReturnCheck::Consumed,true,state)&&
        taiwan_pk_return_consumption_fence(state);
}
bool SharedActorVisibility::taiwan_pk_return_consumption_stored_in_scope(
        const TaiwanPkReturnConsumption& token,sqlite3* connection)const{
    const auto state=token.state_;
    return connection&&taiwan_pk_return_consumption_fence(state)&&
        taiwan_pk_return_read(state->records.state_->plan,TaiwanReturnCheck::Consumed,true,state,connection)&&
        taiwan_pk_return_consumption_fence(state);
}
std::optional<Session::NativePkReturnFinalisation> SharedActorVisibility::prepare_taiwan_pk_return_finalisation(
        const TaiwanPkReturnConsumption& token,const Session::NativePkReturnPublication& publication,
        std::weak_ptr<Session::NativePkReturnFinalisationOwner> owner_source){
    owner();const auto state=token.state_;
    if(!taiwan_pk_return_publication_matches(token,publication)||state->finalisation||
       publication.status()!=Session::NativePkReturnPublicationStatus::Written)return {};
    auto finalisation=Session::prepare_native_pk_return_finalisation(publication,std::move(owner_source));
    state->finalisation.emplace(finalisation);
    if(!taiwan_pk_return_finalisation_matches(token,finalisation))return {};
    return finalisation;
}
bool SharedActorVisibility::taiwan_pk_return_finalisation_identity_matches(
        const TaiwanPkReturnConsumption& token,const Session::NativePkReturnFinalisation& value)const noexcept{
    const auto state=token.state_;
    return thread_==std::this_thread::get_id()&&state&&state->records.state_->creator.get()==this&&
        state->finalisation&&*state->finalisation==value;
}
bool SharedActorVisibility::taiwan_pk_return_finalisation_matches(
        const TaiwanPkReturnConsumption& token,const Session::NativePkReturnFinalisation& value)const{
    owner();const auto state=token.state_;const std::weak_ptr<const void> identity(state?state->records.state_:nullptr);
    return taiwan_pk_return_finalisation_identity_matches(token,value)&&
        taiwan_pk_return_consumption_fence(state)&&state->publication&&
        Session::native_pk_return_finalisation_matches(value,*state->publication)&&
        Session::native_pk_return_finalisation_records_matches(value,identity)&&
        Session::native_pk_return_finalisation_current(value);
}
bool SharedActorVisibility::acquire_taiwan_pk_return_finalisation(
        const TaiwanPkReturnConsumption& token,const Session::NativePkReturnFinalisation& value){
    owner();return taiwan_pk_return_finalisation_matches(token,value)&&
        value.status()==Session::NativePkReturnFinalisationStatus::Prepared&&
        Session::acquire_native_pk_return_finalisation(value);
}
bool SharedActorVisibility::finish_taiwan_pk_return_visibility(
        const TaiwanPkReturnConsumption& token,const Session::NativePkReturnFinalisation& value){
    owner();const auto state=token.state_;
    if(value.status()!=Session::NativePkReturnFinalisationStatus::Ready||
       !taiwan_pk_return_finalisation_matches(token,value))return false;
    // No observer, allocation, model erase, generation rewind or transport send.
    // These exact successful models become ordinary owned world visibility.
    state->finished=true;
    for(const auto& [id,endpoint]:state->records.state_->plan->endpoints){
        const auto at=taiwan_pk_return_consumptions_.find(id);
        if(at!=taiwan_pk_return_consumptions_.end()&&!at->second.owner_before(state->identity)&&
           !state->identity.owner_before(at->second))taiwan_pk_return_consumptions_.erase(at);
    }
    return true;
}
std::optional<Session::NativePkReturnPublication> SharedActorVisibility::prepare_taiwan_pk_return_publication(
        const TaiwanPkReturnConsumption& token,std::weak_ptr<Session::NativePkReturnPublicationOwner> source){
    owner();const auto state=token.state_;
    if(!taiwan_pk_return_consumption_fence(state)||state->publication)return {};
    auto publication=Session::prepare_native_pk_return_publication(state->transport,std::move(source));
    // Retain exact token-only Custody before all actual Outbox source observers.
    state->publication.emplace(publication);
    if(!taiwan_pk_return_publication_matches(token,publication))return {};
    return publication;
}
bool SharedActorVisibility::taiwan_pk_return_publication_identity_matches(const TaiwanPkReturnConsumption& token,
        const Session::NativePkReturnPublication& value)const noexcept{
    const auto state=token.state_;
    return thread_==std::this_thread::get_id()&&state&&state->records.state_->creator.get()==this&&
        state->publication&&*state->publication==value;
}
bool SharedActorVisibility::taiwan_pk_return_publication_matches(const TaiwanPkReturnConsumption& token,
        const Session::NativePkReturnPublication& value)const{
    owner();return taiwan_pk_return_publication_identity_matches(token,value)&&
        taiwan_pk_return_consumption_fence(token.state_)&&
        Session::native_pk_return_publication_matches(value,token.state_->transport);
}
bool SharedActorVisibility::release_taiwan_pk_return_publication(const TaiwanPkReturnConsumption& token,
        const Session::NativePkReturnPublication& value){
    owner();
    return taiwan_pk_return_publication_matches(token,value)&&
        value.status()==Session::NativePkReturnPublicationStatus::Prepared&&
        Session::release_native_pk_return_publication(value);
}
bool SharedActorVisibility::taiwan_pk_return_consumption_matches_transport(const TaiwanPkReturnConsumption& token,
        const Session::NativePkReturnConsumption& value)const noexcept{
    return thread_==std::this_thread::get_id()&&token.state_&&
        token.state_->records.state_->creator.get()==this&&token.state_->transport==value;
}
void SharedActorVisibility::cancel_taiwan_pk_return_consumption_state(TaiwanPkReturnConsumption::State& state)noexcept{
    // Token custody is game-only; weak registry values never retain it on IO.
    if(thread_!=std::this_thread::get_id()||state.records.state_->creator.get()!=this||state.finished)return;
    state.poisoned=true;
    if(!state.claimed)return; // An unused preallocation leaves the original source untouched.
    state.records.state_->plan->poisoned=true;
    // Released bytes cannot be rolled back. Close the exact acquired cohort
    // BEFORE detaching models, including lifecycle-before-failure-callback.
    if(state.publication)Session::abandon_native_pk_return_publication(*state.publication);
    for(const auto& [id,endpoint]:state.records.state_->plan->endpoints){
        const auto at=taiwan_pk_return_consumptions_.find(id);
        if(at!=taiwan_pk_return_consumptions_.end()&&!at->second.owner_before(state.identity)&&
           !state.identity.owner_before(at->second))taiwan_pk_return_consumptions_.erase(at);
    }
    if(state.published)for(const auto& [key,expected]:state.expected){
        const auto at=entries_.find(key);
        if(at!=entries_.end()&&matches(expected.binding,at->second))entries_.erase(at);
    }
    // No hide/S73: before exposure these models were never sent; after possible
    // exposure all actual acquired receivers are closing and recovery is retained.
    // No restore of old markers, generation rollback or successor deletion.
}
void SharedActorVisibility::cancel_taiwan_pk_return_consumption(const TaiwanPkReturnConsumption& token)noexcept{
    if(token.state_)cancel_taiwan_pk_return_consumption_state(*token.state_);
}
bool SharedActorVisibility::taiwan_pk_departed(const Lease& lease)const noexcept {
    // The in-progress pair stays blocked even if an exact lifecycle release
    // reenters cancellation. Old markers never block a successor lease.
    if(taiwan_pk_withdrawing_)for(const auto& owner:taiwan_pk_withdrawing_->leases)if(owner==lease)return true;
    // Future identities alone do not permit ordinary world publication/input.
    if(const auto at=taiwan_pk_return_consumptions_.find(lease.session);at!=taiwan_pk_return_consumptions_.end())
        if(const auto pending=at->second.lock();pending&&!pending->poisoned)
            for(const auto& returning:pending->records.state_->plan->leases)if(returning==lease)return true;
    const auto found=taiwan_pk_departures_.find(lease.session);
    if(found==taiwan_pk_departures_.end())return false;
    for(const auto& owner:found->second->leases)if(owner==lease)return true;
    return false;
}
bool SharedActorVisibility::taiwan_pk_departure_fence(const std::shared_ptr<TaiwanPkDepartureState>& state,
        bool installed,bool held_only)const {
    owner();if(taiwan_pk_reading_){taiwan_pk_reentered_=true;return false;}
    taiwan_pk_reading_=true;taiwan_pk_reentered_=false;
    struct End{bool& busy;~End(){busy=false;}}end{taiwan_pk_reading_};
    const auto local=[&]{
        if(!state||state->identity!=identity_||state->poisoned||taiwan_pk_reentered_)return false;
        std::array<std::shared_ptr<Session>,2> sessions;
        for(std::size_t i=0;i<2;++i){
            sessions[i]=state->connections[i].lock();
            if(!sessions[i]||(!sessions[i]->native_pk_entry_current(state->holds[i])&&
                (held_only||!sessions[i]->native_pk_entry_committed_current(state->holds[i]))))return false;
            // Private exact transport guard precedes mutable Session fields.
            const auto& lease=state->leases[i];const auto& request=state->holds[i].request();
            if(state->holds[i].session_id()!=lease.session||sessions[i]->id()!=lease.session||
               request.account!=lease.account||request.character!=lease.character||
               request.common_generation!=lease.generation||sessions[i]->account_id!=lease.account||
               sessions[i]->character_id!=lease.character)return false;
            const auto marker=taiwan_pk_departures_.find(lease.session);
            if(installed?(marker==taiwan_pk_departures_.end()||marker->second!=state):
                marker!=taiwan_pk_departures_.end())return false;
        }
        return sessions[0]!=sessions[1]&&sessions[0]->same_native_pk_game_executor(*sessions[1]);
    };
    if(!local())return false;
    for(std::size_t i=0;i<2;++i){
        const auto& lease=state->leases[i];
        if(presence_->ready_lease(lease.session,lease.account,lease.character)!=std::optional{lease}||!local()||
           presence_->saved_position(lease)!=std::optional{state->positions[i]}||!local())return false;
    }
    return local();
}
bool SharedActorVisibility::taiwan_pk_departure_current(const TaiwanPkDeparture& token)const {
    return taiwan_pk_departure_fence(token.state_,true,false);
}
bool SharedActorVisibility::taiwan_pk_departure_exact_current(const TaiwanPkDeparture& token,
        const std::array<Lease,2>& leases,const std::array<RecoveredPosition,2>& positions,
        const std::array<std::shared_ptr<Session>,2>& sessions,
        const std::array<Session::NativePkEntryHold,2>& holds,bool retained,std::uint8_t viewer)const {
    // CUSTOM-0130 no callbackful current()/ready()/saved_position() here:
    // this exact process-local departure is not a fresh stored-world read.
    owner();const auto& state=token.state_;
    if(viewer>1 || !state || state->identity!=identity_ || state->poisoned ||
       state->retiring[0] || state->retiring[1] || state->leases!=leases || state->positions!=positions ||
       !sessions[0] || !sessions[1] || sessions[0]==sessions[1])return false;
    for(std::size_t i=0;i<2;++i){
        if(state->connections[i].lock()!=sessions[i] || state->holds[i]!=holds[i])return false;
        // Private game-owner/transport predicate before mutable Session fields.
        if(retained ? !sessions[i]->native_pk_entry_binding_current(holds[i]) :
                      !sessions[i]->native_pk_entry_committed_current(holds[i]))return false;
        const auto& lease=leases[i];const auto& request=holds[i].request();
        if(holds[i].session_id()!=lease.session || sessions[i]->id()!=lease.session ||
           request.account!=lease.account || request.character!=lease.character ||
           request.common_generation!=lease.generation || sessions[i]->account_id!=lease.account ||
           sessions[i]->character_id!=lease.character)return false;
        const auto marker=taiwan_pk_departures_.find(lease.session);
        if(marker==taiwan_pk_departures_.end() || marker->second!=state ||
           !presence_->retained_ready_current(lease))return false;
    }
    return sessions[0]->same_native_pk_game_executor(*sessions[1]) &&
        (!retained || sessions[viewer]->native_pk_entry_written_current(holds[viewer]));
}
bool SharedActorVisibility::taiwan_pk_departure_bound_current(const TaiwanPkDeparture& token,
        const std::array<Lease,2>& leases,const std::array<RecoveredPosition,2>& positions,
        const std::array<std::shared_ptr<Session>,2>& sessions,
        const std::array<Session::NativePkEntryHold,2>& holds)const {
    return taiwan_pk_departure_exact_current(token,leases,positions,sessions,holds,false,0);
}
bool SharedActorVisibility::taiwan_pk_departure_retained_current(const TaiwanPkDeparture& token,
        const std::array<Lease,2>& leases,const std::array<RecoveredPosition,2>& positions,
        const std::array<std::shared_ptr<Session>,2>& sessions,
        const std::array<Session::NativePkEntryHold,2>& holds,std::uint8_t viewer)const {
    return taiwan_pk_departure_exact_current(token,leases,positions,sessions,holds,true,viewer);
}
SharedActorVisibility::ChatActorSnapshot::ChatActorSnapshot(std::shared_ptr<const State> s):state_(std::move(s)) {}
SharedActorVisibility::ChatActorSnapshot::ChatActorSnapshot(ChatActorSnapshot&& other) noexcept:state_(other.state_) {}
SharedActorVisibility::ChatActorSnapshot& SharedActorVisibility::ChatActorSnapshot::operator=(ChatActorSnapshot&& other) noexcept {
    state_=other.state_;return *this;
}
std::optional<SharedActorVisibility::ChatActorSnapshot> SharedActorVisibility::chat_actor_snapshot(
    const Binding& binding,const RecoveredPosition& position) const {
    owner();if(taiwan_pk_departed(binding.source())||taiwan_pk_departed(binding.recipient())||
        outward_pending(binding.source()))return std::nullopt;
    const auto found=entries_.find({binding.source().session,binding.recipient().session});
    if(found==entries_.end() || !matches(binding,found->second) || found->second.position!=position)return std::nullopt;
    const auto entry=found->second;
    const auto receiver=std::visit([](const auto& native)->std::variant<std::shared_ptr<Session>,std::shared_ptr<SharedCredentialConnection>> {
        return native.connection.lock();
    },entry.native);
    if(!std::visit([](const auto& c){return bool(c);},receiver))return std::nullopt;
    return ChatActorSnapshot(std::make_shared<const ChatActorSnapshot::State>(ChatActorSnapshot::State{entry,receiver}));
}
bool SharedActorVisibility::chat_actor_snapshot_current(const ChatActorSnapshot& token) const {
    owner();const auto& snapshot=*token.state_;
    const auto& binding=snapshot.entry.binding;
    if(taiwan_pk_departed(binding.source())||taiwan_pk_departed(binding.recipient())||outward_pending(binding.source()))return false;
    const auto found=entries_.find({binding.source().session,binding.recipient().session});
    if(found==entries_.end() || !matches(binding,found->second) || found->second.position!=snapshot.entry.position ||
       found->second.last_taiwan_appearance!=snapshot.entry.last_taiwan_appearance)return false;
    // This endpoint deliberately invokes no external/repository predicates.
    return std::visit([&](const auto& actual) {
        using Output=std::decay_t<decltype(actual)>;
        using Connection=decltype(actual.connection.lock());
        const auto expected=std::get_if<Output>(&snapshot.entry.native);
        const auto retained=std::get_if<Connection>(&snapshot.receiver);
        if(!expected || !retained || !*retained || actual.connection.lock()!=*retained ||
           actual.common_name_source!=expected->common_name_source)return false;
        if constexpr(std::is_same_v<Output,Taiwan>) {
            if(RecoveredRemoteActor::encode_logical(actual.spawn)!=RecoveredRemoteActor::encode_logical(expected->spawn) ||
               RecoveredRemoteActorRemove::encode_logical(actual.removal)!=RecoveredRemoteActorRemove::encode_logical(expected->removal) ||
               RecoveredRemoteActorMove::encode_logical(actual.movement)!=RecoveredRemoteActorMove::encode_logical(expected->movement) ||
               bool(actual.raw_name_state)!=bool(expected->raw_name_state))return false;
            return !actual.raw_name_state || actual.raw_name_state->same_source(*expected->raw_name_state);
        }else {
            if(god2cn::CnRemoteActor::encode_logical(actual.spawn)!=god2cn::CnRemoteActor::encode_logical(expected->spawn) ||
               god2cn::CnRemoteActorRemove::encode_logical(actual.removal)!=god2cn::CnRemoteActorRemove::encode_logical(expected->removal) ||
               god2cn::CnRemoteActorMove::encode_logical(actual.movement)!=god2cn::CnRemoteActorMove::encode_logical(expected->movement) ||
               actual.normal_source!=expected->normal_source || bool(actual.raw_name_state)!=bool(expected->raw_name_state))return false;
            return !actual.raw_name_state || (actual.raw_name_state->source_revision==expected->raw_name_state->source_revision &&
                actual.raw_name_state->wire_codepage==expected->raw_name_state->wire_codepage);
        }
    },found->second.native);
}
SharedActorVisibility::NormalSource::NormalSource(std::shared_ptr<const Identity> identity,const Lease& source,
    std::weak_ptr<SharedCredentialConnection> connection,std::shared_ptr<const SharedInitialScene> scene,
    god2cn::CnWorldEntry::BeginPlay begin,std::shared_ptr<const SharedInitialAppearanceSource> appearance)
    :identity_(std::move(identity)),source_(source),connection_(std::move(connection)),
    scene_(std::move(scene)),begin_(std::move(begin)),appearance_(std::move(appearance)){}
std::optional<SharedActorVisibility::Mainland> SharedActorVisibility::normal_mainland_from_scene(
    const Lease& source,const std::shared_ptr<SharedCredentialConnection>& connection,
    std::shared_ptr<const SharedInitialScene> scene,Mainland actual) const {
    owner();if(taiwan_pk_departed(source)||!scene || !connection || actual.normal_source)return std::nullopt;
    const auto begin=scene->initial_actor_begin_play(connection,presence_,source);if(!begin)return std::nullopt;
    const auto spawn=god2cn::CnRemoteActor::with_normal_world_components(actual.spawn,*begin);
    if(!spawn)return std::nullopt;
    actual.spawn=*spawn;
    actual.normal_source=std::shared_ptr<const NormalSource>(new NormalSource(identity_,source,connection,std::move(scene),*begin));
    if(!normal_source_matches(source,actual))return std::nullopt;
    return actual;
}
std::optional<SharedActorVisibility::Mainland> SharedActorVisibility::normal_mainland_with_appearance_source(
    const Lease& source,const std::shared_ptr<SharedCredentialConnection>& connection,
    std::shared_ptr<const SharedInitialScene> scene,std::shared_ptr<const SharedInitialAppearanceSource> appearance,
    Mainland actual) const {
    owner();
    if(taiwan_pk_departed(source)||!scene || !appearance || !connection || actual.normal_source ||
       !scene->appearance_source_current(appearance,connection,presence_,source))return std::nullopt;
    const auto begin=scene->initial_actor_begin_play(connection,presence_,source);if(!begin)return std::nullopt;
    const auto spawn=god2cn::CnRemoteActor::with_normal_world_components(actual.spawn,*begin);if(!spawn)return std::nullopt;
    actual.spawn=*spawn;
    actual.normal_source=std::shared_ptr<const NormalSource>(new NormalSource(
        identity_,source,connection,std::move(scene),*begin,std::move(appearance)));
    if(!normal_source_matches(source,actual))return std::nullopt;
    return actual;
}
bool SharedActorVisibility::normal_source_matches(const Lease& source,const Mainland& native) const {
    if(taiwan_pk_departed(source))return false;
    // The supplied native may refer to a registry node. Own its full model and
    // strong issuer before any real scene callbacks; no caller alias survives.
    const auto snapshot=native;
    if(!snapshot.normal_source)return true; // Existing complete real native inputs remain independent.
    const auto& witness=*snapshot.normal_source;
    if(witness.identity_!=identity_ || witness.source_!=source || !witness.scene_)return false;
    const auto begin=witness.scene_->initial_actor_begin_play(witness.connection_.lock(),presence_,source);
    return begin && *begin==witness.begin_ && snapshot.spawn.matches_normal_world_components(*begin) &&
        (!witness.appearance_ || witness.scene_->appearance_source_current(witness.appearance_,
            witness.connection_.lock(),presence_,source))&&!taiwan_pk_departed(source);
}
bool SharedActorVisibility::project_common_name(const Lease& original_source,const Lease& original_recipient,Native& native) const {
    const auto source=original_source,recipient=original_recipient;
    if(taiwan_pk_departed(source)||taiwan_pk_departed(recipient))return false;
    const auto issuer=std::visit([](const auto& output){return output.common_name_source;},native);
    if(!issuer)return true; // Existing complete-native sources remain independent.
    if(!issuer->owns_presence(presence_))return false;
    auto projected=issuer->project(source,recipient,native);
    if(!projected || projected->index()!=native.index() ||
       std::visit([](const auto& output){return output.common_name_source;},*projected)!=issuer||
       taiwan_pk_departed(source)||taiwan_pk_departed(recipient))return false;
    native=std::move(*projected);return true;
}
bool SharedActorVisibility::common_name_current(const Lease& original_source,const Lease& original_recipient,const Native& native) const {
    // Input may be a registry entry; retain the full source before actual readers.
    const auto source=original_source,recipient=original_recipient;
    if(taiwan_pk_departed(source)||taiwan_pk_departed(recipient))return false;
    const auto snapshot=native;
    const auto issuer=std::visit([](const auto& output){return output.common_name_source;},snapshot);
    return (!issuer || (issuer->owns_presence(presence_) && issuer->current(source,recipient,snapshot)))&&
        !taiwan_pk_departed(source)&&!taiwan_pk_departed(recipient);
}
struct SharedActorVisibility::OutwardState {
    struct Delivery {Key key;Native native;std::vector<god2cn::Bytes> records;bool issued=false,published=false,released=false;};
    Lease source;
    RecoveredPosition position;
    std::map<Key,Entry> staged;
    std::vector<Delivery> deliveries;
    std::vector<Binding> bindings;
    OutwardCurrent current;
    OutwardCompletion done;
    bool finished=false;
};
bool SharedActorVisibility::taiwan_pk_return_pending(const std::shared_ptr<TaiwanPkReturnPlan::State>& state)const {
    const auto included=[&](const Lease& lease){
        for(const auto& pair:state->leases)if(pair==lease)return true;
        const auto found=state->endpoints.find(lease.session);
        return found!=state->endpoints.end()&&found->second.lease==lease;
    };
    for(const auto& [id,weak]:outward_)if(const auto pending=weak.lock();pending&&!pending->finished)
        for(const auto& binding:pending->bindings)
            if(included(binding.source())||included(binding.recipient()))return true;
    for(const auto& [key,pending]:taiwan_appearance_)if(pending&&!pending->finished){
        const auto& binding=pending->before.state_->entry.binding;
        if(included(binding.source())||included(binding.recipient()))return true;
    }
    return false;
}
std::optional<SharedActorVisibility::TaiwanPkDeparture> SharedActorVisibility::withdraw_taiwan_pk(
    std::array<Lease,2> leases,std::array<std::shared_ptr<Session>,2> sessions,
    std::array<Session::NativePkEntryHold,2> holds) {
    reject_taiwan_return_reentry();
    owner();
    if(taiwan_pk_withdrawing_){taiwan_pk_withdrawing_->poisoned=true;return std::nullopt;}
    if(taiwan_pk_reading_){taiwan_pk_reentered_=true;return std::nullopt;}
    // Allocate the pair and both map nodes before changing visibility. The
    // private held transport is checked before any mutable Session fields.
    if(leases[0].session==leases[1].session||leases[0].character==leases[1].character||
       !sessions[0]||!sessions[1]||sessions[0]==sessions[1])return std::nullopt;
    for(std::size_t i=0;i<2;++i)if(!sessions[i]->native_pk_entry_current(holds[i]))return std::nullopt;
    auto state=std::make_shared<TaiwanPkDepartureState>(identity_,leases,sessions,std::move(holds));
    for(std::size_t i=0;i<2;++i){
        if(presence_->ready_lease(leases[i].session,leases[i].account,leases[i].character)!=std::optional{leases[i]})return std::nullopt;
        const auto position=presence_->saved_position(leases[i]);if(!position)return std::nullopt;
        state->positions[i]=*position;
    }
    if(state->positions[0].area!=state->positions[1].area||state->positions[0].scene!=state->positions[1].scene||
       !taiwan_pk_departure_fence(state,false,true))return std::nullopt;
    const auto included=[&](const Lease& lease){return lease==leases[0]||lease==leases[1];};
    std::vector<std::shared_ptr<OutwardState>> outward;
    std::vector<std::shared_ptr<TaiwanAppearanceState>> appearance;
    for(const auto& [key,weak]:outward_){
        const auto pending=weak.lock();if(!pending||pending->finished)continue;
        bool affected=included(pending->source);
        for(std::size_t i=0;i<pending->bindings.size();++i){
            const bool recipient=included(pending->bindings[i].recipient());affected=affected||recipient;
            // An issued common-world publication has its own Session failure
            // continuation. Visibility cancellation cannot safely drain it.
            if(recipient&&pending->deliveries[i].issued)return std::nullopt;
        }
        if(affected)outward.push_back(pending);
    }
    for(const auto& [key,pending]:taiwan_appearance_){
        if(!pending||pending->finished)continue;
        const auto& binding=pending->before.state_->entry.binding;
        if(included(binding.recipient())&&pending->issued)return std::nullopt;
        if(included(binding.source())||included(binding.recipient()))appearance.push_back(pending);
    }
    struct Removal{Entry entry;std::vector<std::uint8_t> bytes;};
    std::vector<Removal> removals;
    for(const auto& [key,entry]:entries_)if(included(entry.binding.source())&&!included(entry.binding.recipient())){
        auto bytes=std::visit([](const auto& output){
            using Output=std::decay_t<decltype(output)>;
            if constexpr(std::is_same_v<Output,Taiwan>){
                const auto record=RecoveredRemoteActorRemove::encode_logical(output.removal);
                return std::vector<std::uint8_t>(record.begin(),record.end());
            }else{
                const auto record=god2cn::CnRemoteActorRemove::encode_logical(output.removal);
                return std::vector<std::uint8_t>(record.begin(),record.end());
            }
        },entry.native);
        removals.push_back(Removal{entry,std::move(bytes)});
    }
    std::map<std::uint64_t,std::shared_ptr<TaiwanPkDepartureState>> staged;
    for(const auto& lease:leases)staged.emplace(lease.session,state);
    // The last observer/repository fence is BEFORE the complete incidence
    // collection above. Everything since that fence is owned registry reads,
    // full-record encoding and allocation only, never external callbacks that
    // could introduce an uncollected issued recipient publication.
    taiwan_pk_departures_.merge(staged); // Both preallocated nodes, no callbacks.
    taiwan_pk_withdrawing_=state;
    struct End{std::shared_ptr<TaiwanPkDepartureState>& busy;~End(){busy.reset();}}end{taiwan_pk_withdrawing_};
    // Detach ALL incoming and outgoing incidences of BOTH endpoints before any
    // completion, close, name/repository callback or native removal submission.
    for(auto it=entries_.begin();it!=entries_.end();)
        if(included(it->second.binding.source())||included(it->second.binding.recipient()))it=entries_.erase(it);else ++it;
    for(const auto& pending:outward){
        const auto found=outward_.find(pending->source.session);
        if(found!=outward_.end()&&found->second.lock()==pending)outward_.erase(found);
    }
    for(const auto& pending:appearance){
        const auto& binding=pending->before.state_->entry.binding;
        const auto found=taiwan_appearance_.find({binding.source().session,binding.recipient().session});
        if(found!=taiwan_appearance_.end()&&found->second==pending)taiwan_appearance_.erase(found);
    }
    for(const auto& pending:appearance)finish_taiwan_appearance(pending,false);
    for(const auto& pending:outward)finish_outward(pending,false);
    // Only stored actual removals to surviving observers. No participant gets
    // a world record appended behind its private PK entry barrier.
    for(auto& removal:removals)try{
        const auto& binding=removal.entry.binding;
        if(!recipient_bound(binding.recipient(),removal.entry.native,removal.entry.position)||
           !submit(removal.entry.native,std::move(removal.bytes)))reject_output(binding.recipient(),removal.entry.native);
    }catch(...){try{reject_output(removal.entry.binding.recipient(),removal.entry.native);}catch(...) {}}
    if(!taiwan_pk_departure_fence(state,true,true)){state->poisoned=true;return std::nullopt;}
    return TaiwanPkDeparture(std::move(state));
}
bool SharedActorVisibility::outward_pending(const Lease& source) const {
    const auto found=outward_.find(source.session);
    if(found==outward_.end())return false;
    const auto state=found->second.lock();
    return state && !state->finished && state->source==source;
}
bool SharedActorVisibility::outward_current(const std::shared_ptr<OutwardState>& state,
    std::size_t index,bool published) const {
    owner();
    if(!state || state->finished || index>=state->deliveries.size()||taiwan_pk_departed(state->source)||
        taiwan_pk_departed(state->bindings[index].recipient()))return false;
    const auto saved=presence_->saved_position(state->source);
    const auto pending=outward_.find(state->source.session);
    if(state->finished||taiwan_pk_departed(state->source)||pending==outward_.end() ||
       pending->second.lock()!=state || !saved || *saved!=state->position)return false;
    const auto delivery=state->deliveries[index];
    const auto binding=state->bindings[index];
    if(!common_name_current(binding.source(),binding.recipient(),delivery.native))return false;
    if(const auto* native=std::get_if<Mainland>(&delivery.native);native && !normal_source_matches(binding.source(),*native))return false;
    const auto& models=published?entries_:state->staged;
    const auto found=models.find(delivery.key);
    if(found==models.end() || !matches(binding,found->second) || found->second.position!=state->position ||
       (!published && entries_.contains(delivery.key)) ||
       !recipient_bound(binding.recipient(),delivery.native,state->position))return false;
    if(!published) {
        std::size_t occupied=0;
        for(const auto& [key,entry]:entries_)if(key.second==binding.recipient().session)++occupied;
        if(occupied>=128)return false; // Other source publications may have advanced this pool.
    }
    // This new path requires the actual common TW generation, independent of
    // PRIVATE0083, and the CN world's current admission ticket.
    const bool transport_current=std::visit([&](const auto& output) {
        const auto connection=output.connection.lock();if(!connection)return false;
        using Output=std::decay_t<decltype(output)>;
        if constexpr(std::is_same_v<Output,Taiwan>)
            return connection->common_world_delivery_current(binding.recipient().account,
                binding.recipient().character,binding.recipient().generation);
        else return connection->world_admission_current();
    },delivery.native);
    // recipient_bound invokes actual Presence readers. They may synchronously
    // withdraw/cancel this publication; prevent its final pre-insert check
    // from authorizing a stale staged node after that callback.
    const auto still_pending=outward_.find(state->source.session);
    return transport_current&&!state->finished&&!taiwan_pk_departed(binding.source())&&
        !taiwan_pk_departed(binding.recipient())&&still_pending!=outward_.end()&&still_pending->second.lock()==state;
}
void SharedActorVisibility::finish_outward(const std::shared_ptr<OutwardState>& state,bool accepted) {
    owner();if(!state || state->finished)return;
    state->finished=true;
    const auto found=outward_.find(state->source.session);
    if(found!=outward_.end() && found->second.lock()==state)outward_.erase(found);
    if(!accepted)for(std::size_t i=0;i<state->deliveries.size();++i) {
        auto& delivery=state->deliveries[i];
        // Some peers may already have received6F. Do not pretend fanout is
        // atomic or roll back saved state. Only this exact model incarnation
        // is removed; issued old transports require real close/re-entry.
        const auto model=entries_.find(delivery.key);
        if(delivery.published && model!=entries_.end() && matches(state->bindings[i],model->second))entries_.erase(model);
        if(delivery.issued)try {reject_output(state->bindings[i].recipient(),delivery.native);}catch(...) {}
    }
    if(state->done) {
        auto done=std::move(state->done);
        try {
            if(accepted)done(std::move(state->bindings));else done(std::nullopt);
        }catch(...) {}
    }
}
void SharedActorVisibility::cancel_outward(const Lease& lease) {
    owner();
    // Cleanup may synchronously complete a pending ingress. Start each search
    // afresh, never retain map iterators across its owner completion.
    for(;;) {
        std::shared_ptr<OutwardState> selected;
        for(auto it=outward_.begin();it!=outward_.end();) {
            const auto state=it->second.lock();
            if(!state || state->finished){it=outward_.erase(it);continue;}
            bool included=state->source==lease;
            for(const auto& binding:state->bindings)included=included || binding.recipient()==lease;
            if(included){selected=state;break;}++it;
        }
        if(!selected)return;finish_outward(selected,false);
    }
}
void SharedActorVisibility::publish_outward_initial(const Lease& original_source,std::vector<OutwardRecipient> recipients,
    OutwardCurrent current,OutwardCompletion done) {
    reject_taiwan_return_reentry();
    const auto source=original_source;
    owner();if(!done)throw std::invalid_argument("Outward initial visibility completion required");
    if(taiwan_pk_departed(source)){try{done(std::nullopt);}catch(...){}return;}
    auto state=std::make_shared<OutwardState>();state->source=source;state->current=std::move(current);state->done=std::move(done);
    try {
        const auto self=shared_from_this();
        const auto position=presence_->saved_position(source);
        const auto original_generation=generation_;
        // Never retain an actual registry iterator across name/Presence readers
        // or allocation callbacks while building this independent candidate.
        const bool already_pending=[&] {
            const auto found=outward_.find(source.session);
            return found!=outward_.end()&&!found->second.expired();
        }();
        if(!state->current || !position || taiwan_pk_departed(source) || source.actor_handle>0xfff ||
           recipients.size()>256 || recipients.size()>std::numeric_limits<std::uint64_t>::max()-original_generation ||
           already_pending){finish_outward(state,false);return;}
        // Joining-source only: replacements/later visibility changes have a
        // separate native lifecycle. Never overwrite prior expected actors.
        for(const auto& [key,entry]:entries_)if(entry.binding.source().session==source.session) {
            finish_outward(state,false);return;
        }
        state->position=*position;state->deliveries.reserve(recipients.size());state->bindings.reserve(recipients.size());
        for(auto& recipient:recipients) {
            if(!project_common_name(source,recipient.lease,recipient.native)){finish_outward(state,false);return;}
            const auto& native=recipient.native;
            if(recipient.lease.session==source.session || recipient.lease.character==source.character ||
               !recipient_bound(recipient.lease,native,*position)){finish_outward(state,false);return;}
            std::size_t occupied=0;
            for(const auto& [key,entry]:entries_)if(key.second==recipient.lease.session)++occupied;
            if(occupied>=128){finish_outward(state,false);return;}
            auto bytes=std::visit([&](const auto& output)->std::optional<god2cn::Bytes> {
                if(output.spawn.identity()!=source.actor_handle || output.removal.identity()!=source.actor_handle ||
                   output.movement.identity()!=source.actor_handle || output.spawn.x()!=position->x ||
                   output.spawn.y()!=position->y || output.movement.x()!=position->x || output.movement.y()!=position->y)
                    return std::nullopt;
                using Output=std::decay_t<decltype(output)>;
                if constexpr(std::is_same_v<Output,Taiwan>) {
                    const auto connection=output.connection.lock();
                    if(!connection || !connection->common_world_delivery_current(recipient.lease.account,
                        recipient.lease.character,recipient.lease.generation))return std::nullopt;
                    const auto record=RecoveredRemoteActor::encode_logical(output.spawn);
                    if(output.movement.state()!=(std::uint16_t(record[7])|(std::uint16_t(record[8])<<8)))return std::nullopt;
                    return god2cn::Bytes(record.begin(),record.end());
                } else {
                    const auto connection=output.connection.lock();
                    if(!connection || !connection->world_admission_current() || !normal_source_matches(source,output) ||
                       output.movement.state_raw()!=output.spawn.state_raw())return std::nullopt;
                    const auto record=god2cn::CnRemoteActor::encode_logical(output.spawn);
                    return god2cn::Bytes(record.begin(),record.end());
                }
            },native);
            if(!bytes){finish_outward(state,false);return;}
            const Key key{source.session,recipient.lease.session};
            Binding binding(identity_,source,recipient.lease,original_generation+state->bindings.size()+1);
            if(!state->staged.emplace(key,Entry{binding,*position,native}).second){finish_outward(state,false);return;}
            std::vector<god2cn::Bytes> records;records.push_back(std::move(*bytes));
            state->bindings.push_back(binding);
            state->deliveries.push_back({key,std::move(recipient.native),std::move(records)});
        }
        // Allocate the actual registry node in a LOCAL map. Allocation/reentry
        // precedes the final fresh registry/generation/quota qualification.
        std::map<std::uint64_t,std::weak_ptr<OutwardState>> candidate_registry;
        candidate_registry.emplace(source.session,state);
        auto candidate_node=candidate_registry.extract(source.session);
        bool quota_current=true,source_present=false;
        for(const auto& [key,entry]:entries_)
            if(entry.binding.source().session==source.session)source_present=true;
        for(const auto& delivery:state->deliveries){
            std::size_t occupied=0;
            for(const auto& [key,entry]:entries_)if(key.second==delivery.key.second)++occupied;
            if(occupied>=128)quota_current=false;
        }
        if(generation_!=original_generation||source_present||!quota_current||taiwan_pk_departed(source)){
            finish_outward(state,false);return;
        }
        bool live_successor=false;
        {
            // This iterator is acquired AFTER every observer/allocation. Only
            // this exact expired entry may be erased; never a live successor.
            const auto fresh=outward_.find(source.session);
            live_successor=fresh!=outward_.end()&&!fresh->second.expired();
            if(!live_successor&&fresh!=outward_.end())outward_.erase(fresh);
        }
        if(live_successor){finish_outward(state,false);return;}
        const auto inserted=outward_.insert(std::move(candidate_node));
        if(!inserted.inserted){finish_outward(state,false);return;}
        // Existing generation and all binding additions were checked before
        // construction, then required unchanged; never rebase or wrap them.
        generation_+=state->bindings.size();
        const auto source_current=[self,state] {
            const auto saved=self->presence_->saved_position(state->source);
            const auto found=self->outward_.find(state->source.session);
            return !state->finished && !self->taiwan_pk_departed(state->source) &&
                found!=self->outward_.end() && found->second.lock()==state &&
                saved && *saved==state->position;
        };
        if(!source_current() || !state->current(OutwardCheck::Prepare) || !source_current()) {
            finish_outward(state,false);return;
        }
        for(std::size_t i=0;i<state->deliveries.size();++i)if(!outward_current(state,i,false)) {
            finish_outward(state,false);return;
        }
        if(state->deliveries.empty()) {
            const bool accepted=source_current() && state->current(OutwardCheck::BeforePublish) && source_current();
            finish_outward(state,accepted);return; // Actual source's explicit empty observer set.
        }
        for(std::size_t i=0;i<state->deliveries.size() && !state->finished;++i) {
            const auto publish=[self,state,i] {
                self->owner();
                if(state->deliveries[i].published || !self->outward_current(state,i,false) ||
                   !state->current(OutwardCheck::BeforePublish) || !self->outward_current(state,i,false))return false;
                // Transfer this preallocated exact node before either native
                // recipient transport can release its held6F. No save/send.
                auto node=state->staged.extract(state->deliveries[i].key);
                auto inserted=self->entries_.insert(std::move(node));
                if(!inserted.inserted)return false;
                state->deliveries[i].published=true;
                return self->outward_current(state,i,true);
            };
            const auto queued=[self,state,i](bool accepted) {
                self->owner();if(state->finished || state->deliveries[i].released)return;
                try {
                if(!accepted || !state->deliveries[i].published || !self->outward_current(state,i,true)) {
                    self->finish_outward(state,false);return;
                }
                state->deliveries[i].released=true;
                for(const auto& delivery:state->deliveries)if(!delivery.released)return;
                for(std::size_t n=0;n<state->deliveries.size();++n)if(!self->outward_current(state,n,true)) {
                    self->finish_outward(state,false);return;
                }
                self->finish_outward(state,true);
                }catch(...) {self->finish_outward(state,false);}
            };
            auto& delivery=state->deliveries[i];delivery.issued=true;
            std::visit([&](const auto& output) {
                const auto connection=output.connection.lock();
                if(!connection){queued(false);return;}
                using Output=std::decay_t<decltype(output)>;
                const auto& recipient=state->bindings[i].recipient();
                if constexpr(std::is_same_v<Output,Taiwan>)
                    connection->send_common_world_records_with_publication(std::move(delivery.records.front()),recipient.account,
                        recipient.character,recipient.generation,publish,queued);
                else connection->send_world_batch_with_publication(std::move(delivery.records),publish,queued);
            },delivery.native);
        }
    }catch(...) {finish_outward(state,false);}
}
struct SharedActorVisibility::InitialPublication::State {
    std::shared_ptr<const Identity> identity;
    std::weak_ptr<SharedCredentialConnection> connection;
    Lease recipient;
    std::map<Key,Entry> staged;
    std::vector<god2cn::Bytes> records,supplied_records;
    bool published=false;
};
SharedActorVisibility::InitialPublication::InitialPublication(std::shared_ptr<State> state):state_(std::move(state)){}
std::span<const god2cn::Bytes> SharedActorVisibility::InitialPublication::records() const {return state_->records;}
std::span<const god2cn::Bytes> SharedActorVisibility::InitialPublication::supplied_records() const {return state_->supplied_records;}
std::shared_ptr<SharedActorVisibility::InitialPublication> SharedActorVisibility::prepare_initial_recipient(
    const Lease& recipient,const std::shared_ptr<SharedCredentialConnection>& connection,std::vector<InitialActor> actors) {
    reject_taiwan_return_reentry();
    owner();
    if(actors.size()>128 || actors.size()>std::numeric_limits<std::uint64_t>::max()-generation_)return {};
    auto state=std::make_shared<InitialPublication::State>();
    state->identity=identity_;state->connection=connection;state->recipient=recipient;
    auto token=std::shared_ptr<InitialPublication>(new InitialPublication(state));
    if(!initial_current(token,connection,recipient,false))return {};
    state->records.reserve(actors.size());state->supplied_records.reserve(actors.size());
    for(auto& actor:actors) {
        const auto supplied=god2cn::CnRemoteActor::encode_logical(actor.native.spawn);
        Native projected{actor.native};
        if(!project_common_name(actor.source,recipient,projected))return {};
        actor.native=std::get<Mainland>(std::move(projected));
        const auto position=presence_->saved_position(actor.source);
        const auto& native=actor.native;
        if(!position || !normal_source_matches(actor.source,native) || outward_pending(actor.source) || actor.source.actor_handle>0xfff || actor.source.session==recipient.session ||
           actor.source.character==recipient.character || position->area!=recipient.position.area ||
           position->scene!=recipient.position.scene || native.connection.lock()!=connection ||
           native.spawn.identity()!=actor.source.actor_handle || native.removal.identity()!=actor.source.actor_handle ||
           native.movement.identity()!=actor.source.actor_handle || native.spawn.x()!=position->x ||
           native.spawn.y()!=position->y || native.movement.x()!=position->x || native.movement.y()!=position->y ||
           native.movement.state_raw()!=native.spawn.state_raw())return {};
        const auto record=god2cn::CnRemoteActor::encode_logical(native.spawn);
        Binding binding(identity_,actor.source,recipient,generation_+state->staged.size()+1);
        if(!state->staged.emplace(Key{actor.source.session,recipient.session},
            Entry{binding,*position,Native{std::move(actor.native)}}).second)return {};
        state->records.emplace_back(record.begin(),record.end());
        state->supplied_records.emplace_back(supplied.begin(),supplied.end());
    }
    if(!initial_current(token,connection,recipient,false))return {};
    // Reserve private incarnation IDs only after all allocations/qualification.
    // These are server lineage, never native pool counters or visibility rules.
    generation_+=state->staged.size();return token;
}
bool SharedActorVisibility::initial_current(const std::shared_ptr<InitialPublication>& token,
    const std::shared_ptr<SharedCredentialConnection>& connection,const Lease& recipient,bool activated) const {
    owner();
    if(!token || !token->state_ || !connection)return false;
    const auto& state=*token->state_;
    if(taiwan_pk_departed(recipient)||state.identity!=identity_ || state.published || state.connection.lock()!=connection || state.recipient!=recipient ||
       connection->closing() || connection->role()!=SharedCredentialConnection::Transport::Role::World ||
       connection->world_session_id()!=recipient.session || connection->verified_account_id()!=recipient.account ||
       !connection->world_character_offered(recipient.character) || !connection->world_admission_current() ||
       !presence_->preparation_current(recipient) || presence_->ready(recipient)!=activated)return false;
    // Fresh incoming receiver only. Stale/old pairs require their real cleanup,
    // never implicit pool reset, overwrite or generation reuse here.
    for(const auto& [key,entry]:entries_)if(key.second==recipient.session)return false;
    const auto staged=state.staged;
    for(const auto& [key,entry]:staged) {
        if(!common_name_current(entry.binding.source(),recipient,entry.native))return false;
        const auto position=presence_->saved_position(entry.binding.source());
        const auto* native=std::get_if<Mainland>(&entry.native);
        if(!position || outward_pending(entry.binding.source()) || *position!=entry.position || position->area!=recipient.position.area ||
           position->scene!=recipient.position.scene || !native || !normal_source_matches(entry.binding.source(),*native) || native->connection.lock()!=connection ||
           entry.binding.identity_!=identity_ || entry.binding.recipient()!=recipient ||
           key!=Key{entry.binding.source().session,recipient.session})return false;
    }
    for(const auto& [key,entry]:staged)if(taiwan_pk_departed(entry.binding.source()))return false;
    return !taiwan_pk_departed(recipient)&&!state.published && state.staged.size()==staged.size(); // Actual scene policy/resources/full-set causality remain with issuer.
}
bool SharedActorVisibility::publish_initial(const std::shared_ptr<InitialPublication>& token,
    const std::shared_ptr<SharedCredentialConnection>& connection,const Lease& recipient) {
    reject_taiwan_return_reentry();
    owner();if(!initial_current(token,connection,recipient,true))return false;
    // All fixed integer keys were qualified absent on this serial game owner.
    // Existing map nodes transfer without allocation, native send or callbacks.
    entries_.merge(token->state_->staged);
    if(!token->state_->staged.empty())return false;
    token->state_->published=true;return true;
}
SharedActorVisibility::SharedActorVisibility(std::shared_ptr<SharedWorldPresence> presence)
    :presence_(std::move(presence)) {
    if(!presence_)throw std::invalid_argument("Shared actor visibility requires common presence owner");
}
struct SharedActorVisibility::TaiwanInitialPublication::State {
    std::shared_ptr<const Identity> identity;
    std::weak_ptr<Session> connection;
    Lease recipient;
    std::map<Key,Entry> staged;
    std::vector<god2cn::Bytes> records,supplied_records;
    // Publication-local ordered proof. Entry/native movement/removal models
    // never retain ActorUnit. Null slots preserve the original actor order.
    std::vector<Lease> sources;
    std::vector<std::optional<TaiwanActorStatusPublication::ActorUnit>> actor_status;
    bool published=false;
    bool status_current() const noexcept {
        constexpr auto actor_size=RecoveredRemoteActor::logical_size;
        constexpr auto unit_size=actor_size+RecoveredTaiwanActorOverride::logical_size;
        if(records.size()!=sources.size() || records.size()!=actor_status.size() ||
           records.size()!=supplied_records.size() || records.size()!=staged.size())return false;
        for(std::size_t i=0;i<actor_status.size();++i) {
            const auto found=staged.find(Key{sources[i].session,recipient.session});
            if(found==staged.end() || found->second.binding.source()!=sources[i] ||
               found->second.binding.recipient()!=recipient)return false;
            const auto& unit=actor_status[i];
            if(unit && (unit->source()!=sources[i] || unit->recipient()!=recipient ||
               !unit->retained() || unit->logical().size()!=unit_size || records[i].size()!=actor_size ||
               !std::equal(records[i].begin(),records[i].end(),unit->logical().begin())))return false;
        }
        return true;
    }
};
SharedActorVisibility::TaiwanInitialPublication::TaiwanInitialPublication(std::shared_ptr<State> state)
    :state_(std::move(state)){}
std::span<const god2cn::Bytes> SharedActorVisibility::TaiwanInitialPublication::records() const {
    return state_->records;
}
std::span<const god2cn::Bytes> SharedActorVisibility::TaiwanInitialPublication::supplied_records() const {
    return state_->supplied_records;
}
std::span<const std::optional<TaiwanActorStatusPublication::ActorUnit>>
SharedActorVisibility::TaiwanInitialPublication::actor_status() const {
    return state_->actor_status;
}
std::shared_ptr<SharedActorVisibility::TaiwanInitialPublication>
SharedActorVisibility::prepare_initial_taiwan_recipient(const Lease& recipient,
    const std::shared_ptr<Session>& connection,std::vector<InitialTaiwanActor> actors) {
    reject_taiwan_return_reentry();
    owner();
    if(actors.size()>128 || actors.size()>std::numeric_limits<std::uint64_t>::max()-generation_)return {};
    auto state=std::make_shared<TaiwanInitialPublication::State>();
    state->identity=identity_;state->connection=connection;state->recipient=recipient;
    auto token=std::shared_ptr<TaiwanInitialPublication>(new TaiwanInitialPublication(state));
    if(!taiwan_initial_current(token,connection,recipient,false))return {};
    state->records.reserve(actors.size());state->supplied_records.reserve(actors.size());
    state->sources.reserve(actors.size());state->actor_status.reserve(actors.size());
    for(auto& actor:actors) {
        const auto supplied=RecoveredRemoteActor::encode_logical(actor.native.spawn);
        Native projected{actor.native};
        if(!project_common_name(actor.source,recipient,projected))return {};
        actor.native=std::get<Taiwan>(std::move(projected));
        const auto position=presence_->saved_position(actor.source);
        const auto& native=actor.native;
        if(!position || outward_pending(actor.source) || actor.source.actor_handle>0xfff ||
           actor.source.session==recipient.session || actor.source.character==recipient.character ||
           position->area!=recipient.position.area || position->scene!=recipient.position.scene ||
           native.connection.lock()!=connection || native.spawn.identity()!=actor.source.actor_handle ||
           native.removal.identity()!=actor.source.actor_handle || native.movement.identity()!=actor.source.actor_handle ||
           native.spawn.x()!=position->x || native.spawn.y()!=position->y ||
           native.movement.x()!=position->x || native.movement.y()!=position->y)return {};
        const auto record=RecoveredRemoteActor::encode_logical(native.spawn);
        if(native.movement.state()!=(std::uint16_t(record[7])|(std::uint16_t(record[8])<<8)))return {};
        // Name projection precedes proof comparison. A unit for earlier raw
        // bytes cannot authorize a changed final model, even when its EA agrees.
        if(actor.actor_status && (actor.actor_status->source()!=actor.source ||
           actor.actor_status->recipient()!=recipient || !actor.actor_status->retained() ||
           actor.actor_status->logical().size()!=RecoveredRemoteActor::logical_size+
               RecoveredTaiwanActorOverride::logical_size ||
           !std::equal(record.begin(),record.end(),actor.actor_status->logical().begin())))return {};
        Binding binding(identity_,actor.source,recipient,generation_+state->staged.size()+1);
        if(!state->staged.emplace(Key{actor.source.session,recipient.session},
            Entry{binding,*position,Native{std::move(actor.native)}}).second)return {};
        state->records.emplace_back(record.begin(),record.end());
        state->supplied_records.emplace_back(supplied.begin(),supplied.end());
        state->sources.push_back(actor.source);state->actor_status.push_back(std::move(actor.actor_status));
    }
    if(!taiwan_initial_current(token,connection,recipient,false))return {};
    // Server incarnation lineage only, never a native pool counter or rule.
    generation_+=state->staged.size();return token;
}
bool SharedActorVisibility::taiwan_initial_current(const std::shared_ptr<TaiwanInitialPublication>& token,
    const std::shared_ptr<Session>& connection,const Lease& recipient,bool activated) const {
    owner();if(!token || !token->state_ || !connection)return false;
    const auto& state=*token->state_;
    if(!state.status_current())return false;
    if(taiwan_pk_departed(recipient)||state.identity!=identity_ || state.published || state.connection.lock()!=connection || state.recipient!=recipient ||
       connection->closing() || connection->id()!=recipient.session || connection->account_id!=recipient.account ||
       connection->character_id!=recipient.character || !connection->recovered_world_ready() ||
       (activated ? connection->state()!=SessionState::InWorld :
           (connection->state()!=SessionState::CharacterSelected && connection->state()!=SessionState::InWorld)) ||
       !presence_->preparation_current(recipient) ||
       presence_->ready(recipient)!=activated ||
       (activated && !connection->common_world_delivery_current(recipient.account,recipient.character,recipient.generation)))
        return false;
    // Fresh recipient only: old nodes require their actual generation cleanup.
    for(const auto& [key,entry]:entries_)if(key.second==recipient.session)return false;
    const auto staged=state.staged;
    for(const auto& [key,entry]:staged) {
        if(!common_name_current(entry.binding.source(),recipient,entry.native))return false;
        const auto position=presence_->saved_position(entry.binding.source());
        const auto* native=std::get_if<Taiwan>(&entry.native);
        if(!position || outward_pending(entry.binding.source()) || *position!=entry.position ||
           position->area!=recipient.position.area || position->scene!=recipient.position.scene ||
           !native || native->connection.lock()!=connection || entry.binding.identity_!=identity_ ||
           entry.binding.recipient()!=recipient || key!=Key{entry.binding.source().session,recipient.session})return false;
    }
    for(const auto& [key,entry]:staged)if(taiwan_pk_departed(entry.binding.source()))return false;
    return !taiwan_pk_departed(recipient)&&!state.published && state.staged.size()==staged.size() &&
        state.status_current(); // Recheck pure units after all actual name/presence observers.
}
bool SharedActorVisibility::publish_initial_taiwan(const std::shared_ptr<TaiwanInitialPublication>& token,
    const std::shared_ptr<Session>& connection,const Lease& recipient) {
    reject_taiwan_return_reentry();
    owner();if(!taiwan_initial_current(token,connection,recipient,true))return false;
    // Serial owner qualified fixed keys absent; these map nodes allocate before
    // IO and transfer without callbacks, native sends or save mutations.
    entries_.merge(token->state_->staged);
    if(!token->state_->staged.empty())return false;
    token->state_->published=true;return true;
}
SharedActorVisibility::Binding::Binding(std::shared_ptr<const Identity> identity,Lease source,Lease recipient,
    std::uint64_t generation):identity_(std::move(identity)),source_(source),recipient_(recipient),generation_(generation){}
bool SharedActorVisibility::taiwan_appearance_pending(const Key& key) const {
    const auto found=taiwan_appearance_.find(key);
    return found!=taiwan_appearance_.end() && !found->second->finished;
}
bool SharedActorVisibility::taiwan_appearance_fence(const std::shared_ptr<TaiwanAppearanceState>& state,bool published) const {
    owner();if(!state || state->finished || state->poisoned)return false;
    const auto& entry=state->before.state_->entry;
    const auto binding=entry.binding;const auto position=entry.position;
    const auto token=published?state->after:std::optional<ChatActorSnapshot>(state->before);
    if(!token || state->published!=published)return false;
    const auto exact=[&] {
        const auto pending=taiwan_appearance_.find({binding.source().session,binding.recipient().session});
        return !state->finished && !state->poisoned && pending!=taiwan_appearance_.end() && pending->second==state &&
            chat_actor_snapshot_current(*token) && state->receiver &&
            state->receiver->id()==binding.recipient().session &&
            state->receiver->account_id==binding.recipient().account &&
            state->receiver->character_id==binding.recipient().character &&
            state->receiver->battle_generation()==state->battle &&
            state->receiver->common_world_delivery_current(binding.recipient().account,
                binding.recipient().character,binding.recipient().generation);
    };
    // Full expected Entry/strong receiving connection surround every actual
    // repository/name owner invoked by current(). No live iterator survives.
    return exact() && current(binding,position,position) && exact();
}
bool SharedActorVisibility::taiwan_appearance_check(const std::shared_ptr<TaiwanAppearanceState>& state,
    TaiwanAppearanceCheck check,bool published) {
    owner();if(state->checking){state->poisoned=true;return false;}
    state->checking=true;
    struct EndCheck {bool& value;~EndCheck(){value=false;}} end{state->checking};
    if(!taiwan_appearance_fence(state,published))return false;
    // Cleanup from a forbidden nested owner must not destroy the callable
    // while it is executing. This full provider copy also dies on game.
    const auto supply=state->source;
    if(!supply)return false;
    const auto supplied=supply(check);
    if(!supplied || !supplied->source_revision || supplied->source_record.empty() ||
       supplied->source_record.size()>2048 || supplied->source_record.find('\0')!=std::string::npos ||
       supplied->update.actor_identity()!=state->before.state_->entry.binding.source().actor_handle ||
       !taiwan_appearance_fence(state,published))return false;
    if(state->receipt)return *supplied==*state->receipt;
    const auto& previous=state->before.state_->entry.last_taiwan_appearance;
    if(previous && supplied->source_revision<=previous->source_revision)return false;
    // All allocation and complete actual bytes precede transport submission.
    state->receipt=std::make_shared<const TaiwanAppearanceAfterState>(*supplied);
    auto next=state->before.state_->entry;next.last_taiwan_appearance=state->receipt;
    state->after=ChatActorSnapshot(std::make_shared<const ChatActorSnapshot::State>(
        ChatActorSnapshot::State{std::move(next),state->receiver}));
    return taiwan_appearance_fence(state,false);
}
void SharedActorVisibility::finish_taiwan_appearance(const std::shared_ptr<TaiwanAppearanceState>& state,bool accepted) {
    owner();if(!state || state->finished)return;
    const auto keepalive=state->owner_keepalive;
    state->finished=true;
    const auto binding=state->before.state_->entry.binding;
    const Key key{binding.source().session,binding.recipient().session};
    const auto pending=taiwan_appearance_.find(key);
    if(pending!=taiwan_appearance_.end() && pending->second==state)taiwan_appearance_.erase(pending);
    if(!accepted && state->issued) {
        const auto found=entries_.find(key);
        if(found!=entries_.end() && matches(binding,found->second)) {
            // Only this exact incarnation is forgotten. No repository callback
            // or rollback of the already committed authoritative mutation.
            entries_.erase(found);
            const auto& recipient=binding.recipient();
            if(!taiwan_pk_departed(recipient)&&state->receiver && state->receiver->id()==recipient.session &&
               state->receiver->account_id==recipient.account && state->receiver->character_id==recipient.character &&
               state->receiver->common_world_delivery_current(recipient.account,recipient.character,recipient.generation))
                try {state->receiver->close();}catch(...) {} // IO-post failure must not strand once-completion.
        }
    }
    auto done=std::move(state->done);state->source={};state->owner_keepalive.reset();
    if(done)try {done(accepted);}catch(...) {}
}
void SharedActorVisibility::publish_taiwan_appearance(const Binding& original_binding,
    const RecoveredPosition& original_position,TaiwanAppearanceSource source,TaiwanAppearanceCompletion done) {
    reject_taiwan_return_reentry();
    owner();if(!done)throw std::invalid_argument("Taiwan appearance completion required");
    const auto binding=original_binding;const auto position=original_position;
    const auto refuse=[&] {auto callback=std::move(done);if(callback)try {callback(false);}catch(...) {}};
    if(taiwan_appearance_cancelling_||taiwan_pk_departed(binding.source())||taiwan_pk_departed(binding.recipient())){refuse();return;}
    // Source predicates must not reenter publication, even on a different pair.
    bool nested=false;
    for(const auto& [key,pending]:taiwan_appearance_)if(pending->checking){pending->poisoned=true;nested=true;}
    if(nested){refuse();return;}
    const Key key{binding.source().session,binding.recipient().session};
    if(taiwan_appearance_pending(key)){taiwan_appearance_.at(key)->poisoned=true;refuse();return;}
    std::shared_ptr<TaiwanAppearanceState> state;
    try {
        const auto self=shared_from_this();
        const auto before=chat_actor_snapshot(binding,position);
        if(!source || !before || binding.source().actor_handle>0xfff ||
           taiwan_appearance_generation_==std::numeric_limits<std::uint64_t>::max()) {refuse();return;}
        const auto* native=std::get_if<Taiwan>(&before->state_->entry.native);
        if(!native){refuse();return;} // Never silently omit CN from a fanout.
        const auto receiver=native->connection.lock();if(!receiver){refuse();return;}
        state=std::make_shared<TaiwanAppearanceState>(*before,std::move(source),std::move(done));
        state->receiver=receiver;state->battle=receiver->battle_generation();
        state->nonce=++taiwan_appearance_generation_;state->owner_keepalive=self;
        taiwan_appearance_.emplace(key,state);
        if(!taiwan_appearance_check(state,TaiwanAppearanceCheck::Prepare,false)) {
            finish_taiwan_appearance(state,false);return;
        }
        const auto& actual=RecoveredTaiwanPlayerAppearanceUpdate::encode_logical(state->receipt->update);
        std::vector<std::uint8_t> bytes(actual.begin(),actual.end());
        // IO facades own no game-affine provider, completion or registry. The
        // pending owner vault retains those until the game completion/drain.
        const std::weak_ptr<SharedActorVisibility> weak=self;const auto nonce=state->nonce;
        const auto publish=[weak,key,nonce] {
            const auto self=weak.lock();if(!self)return false;self->owner();
            const auto found=self->taiwan_appearance_.find(key);
            if(found==self->taiwan_appearance_.end() || found->second->nonce!=nonce)return false;
            const auto pending=found->second;
            if(pending->published || !self->taiwan_appearance_check(pending,TaiwanAppearanceCheck::BeforePublish,false))return false;
            const auto model=self->entries_.find(key);
            if(model==self->entries_.end() || !self->chat_actor_snapshot_current(pending->before))return false;
            model->second.last_taiwan_appearance=pending->receipt;pending->published=true;
            return self->taiwan_appearance_check(pending,TaiwanAppearanceCheck::AfterPublish,true);
        };
        const auto queued=[weak,key,nonce](bool accepted) {
            const auto self=weak.lock();if(!self)return;self->owner();
            const auto found=self->taiwan_appearance_.find(key);
            if(found==self->taiwan_appearance_.end() || found->second->nonce!=nonce)return;
            const auto pending=found->second;
            try {accepted=accepted && pending->published &&
                self->taiwan_appearance_check(pending,TaiwanAppearanceCheck::AfterPublish,true);}
            catch(...) {accepted=false;}
            self->finish_taiwan_appearance(pending,accepted);
        };
        state->issued=true;
        receiver->send_common_world_records_with_publication(std::move(bytes),binding.recipient().account,
            binding.recipient().character,binding.recipient().generation,publish,queued);
    }catch(...) {if(state)finish_taiwan_appearance(state,false);else refuse();}
}
void SharedActorVisibility::cancel_taiwan_appearance(const Lease& original_lease) {
    owner();const auto keepalive=taiwan_appearance_.empty()?std::shared_ptr<SharedActorVisibility>{}:shared_from_this();
    const auto lease=original_lease;
    const bool previous=taiwan_appearance_cancelling_;taiwan_appearance_cancelling_=true;
    struct EndCancel {bool& value;bool previous;~EndCancel(){value=previous;}} end{taiwan_appearance_cancelling_,previous};
    for(;;) {
        std::shared_ptr<TaiwanAppearanceState> selected;
        for(const auto& [key,state]:taiwan_appearance_) {
            const auto& binding=state->before.state_->entry.binding;
            if(binding.source()==lease || binding.recipient()==lease){selected=state;break;}
        }
        if(!selected)return;finish_taiwan_appearance(selected,false);
    }
}
void SharedActorVisibility::cancel_taiwan_appearance_publications() {
    reject_taiwan_return_reentry();
    owner();const auto keepalive=taiwan_appearance_.empty()?std::shared_ptr<SharedActorVisibility>{}:shared_from_this();
    const bool previous=taiwan_appearance_cancelling_;taiwan_appearance_cancelling_=true;
    struct EndCancel {bool& value;bool previous;~EndCancel(){value=previous;}} end{taiwan_appearance_cancelling_,previous};
    while(!taiwan_appearance_.empty()) {
        const auto state=taiwan_appearance_.begin()->second;finish_taiwan_appearance(state,false);
    }
}
void SharedActorVisibility::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("Shared actor visibility game owner mismatch");
}
bool SharedActorVisibility::owns_presence(const std::shared_ptr<SharedWorldPresence>& presence) const {
    owner();return presence_==presence;
}
bool SharedActorVisibility::matches(const Binding& binding,const Entry& entry) const {
    return binding.identity_==identity_ && entry.binding.identity_==identity_ &&
        binding.source_==entry.binding.source_ && binding.recipient_==entry.binding.recipient_ &&
        binding.generation_==entry.binding.generation_;
}
bool SharedActorVisibility::recipient_bound(const Lease& recipient,const Native& native,
    const RecoveredPosition& source_position) const {
    if(taiwan_pk_departed(recipient)||!presence_->ready(recipient))return false;
    const auto saved=presence_->saved_position(recipient);
    if(!saved || saved->area!=source_position.area || saved->scene!=source_position.scene)return false;
    const bool bound=std::visit([&](const auto& output) {
        const auto connection=output.connection.lock();
        if(!connection)return false;
        using Output=std::decay_t<decltype(output)>;
        if constexpr(std::is_same_v<Output,Taiwan>)
            return connection->id()==recipient.session && connection->account_id==recipient.account &&
                connection->character_id==recipient.character && connection->recovered_world_ready() &&
                (connection->state()==SessionState::InWorld || connection->state()==SessionState::CharacterSelected);
        else
            return !connection->closing() && connection->role()==SharedCredentialConnection::Transport::Role::World &&
                connection->world_session_id()==recipient.session && connection->verified_account_id()==recipient.account &&
                connection->world_character_offered(recipient.character);
    },native);
    return bound&&!taiwan_pk_departed(recipient);
}
bool SharedActorVisibility::submit(Native& native,std::vector<std::uint8_t> bytes) {
    return std::visit([&](const auto& output) {
        const auto connection=output.connection.lock();
        if(!connection)return false;
        using Output=std::decay_t<decltype(output)>;
        if constexpr(std::is_same_v<Output,Taiwan>) {
            connection->send_world_records(std::move(bytes));
            return connection->recovered_world_ready() && connection->state()!=SessionState::Disconnected;
        } else {
            connection->send(std::move(bytes));return !connection->closing();
        }
    },native); // Submission only; no asynchronous acceptance is observed.
}
void SharedActorVisibility::reject_output(const Lease& recipient,Native& native) {
    // A failed expected-model mutation must force fresh owner recovery, while
    // stale cleanup may never close a new incarnation on the same session ID.
    if(taiwan_pk_departed(recipient)||!presence_->current(recipient)||taiwan_pk_departed(recipient))return;
    std::visit([&](const auto& output) {
        const auto connection=output.connection.lock();
        if(!connection)return;
        using Output=std::decay_t<decltype(output)>;
        if constexpr(std::is_same_v<Output,Taiwan>) {
            if(connection->id()==recipient.session && connection->account_id==recipient.account &&
               connection->character_id==recipient.character)connection->close();
        } else {
            if(connection->world_session_id()==recipient.session && connection->verified_account_id()==recipient.account &&
               connection->world_character_offered(recipient.character))connection->close();
        }
    },native);
}
std::optional<SharedActorVisibility::Binding> SharedActorVisibility::show(
    const Lease& original_source,const Lease& original_recipient,Native native) {
    reject_taiwan_return_reentry();
    const auto source=original_source,recipient=original_recipient;
    owner();
    if(taiwan_pk_departed(source)||taiwan_pk_departed(recipient))return std::nullopt;
    if(!project_common_name(source,recipient,native))return std::nullopt;
    const auto position=presence_->saved_position(source);
    // Both native6F constructors use12-bit identity, though5E/73 use low16.
    if(!position || outward_pending(source) || source.actor_handle>0xfff || source.session==recipient.session ||
       source.character==recipient.character || !recipient_bound(recipient,native,*position))return std::nullopt;
    const Key key{source.session,recipient.session};
    if(taiwan_appearance_pending(key))return std::nullopt;
    const auto old=entries_.find(key);
    if(old!=entries_.end() && (old->second.binding.source()!=source || old->second.binding.recipient()!=recipient))
        return std::nullopt; // Require generation-qualified cleanup; never silently reuse a pair.
    if(old!=entries_.end() && old->second.native.index()!=native.index())return std::nullopt;
    std::size_t occupied=0;
    for(const auto& [pair,entry]:entries_)
        if(pair.second==recipient.session && pair!=key)++occupied;
    if(occupied>=128 || generation_==std::numeric_limits<std::uint64_t>::max())return std::nullopt;
    auto bytes=std::visit([&](const auto& output)->std::optional<std::vector<std::uint8_t>> {
        if(output.spawn.identity()!=source.actor_handle || output.removal.identity()!=source.actor_handle ||
           output.movement.identity()!=source.actor_handle || output.spawn.x()!=position->x || output.spawn.y()!=position->y ||
           output.movement.x()!=position->x || output.movement.y()!=position->y)return std::nullopt;
        using Output=std::decay_t<decltype(output)>;
        if constexpr(std::is_same_v<Output,Taiwan>) {
            const auto spawn=RecoveredRemoteActor::encode_logical(output.spawn);
            const auto state=std::uint16_t(spawn[7])|(std::uint16_t(spawn[8])<<8);
            if(output.movement.state()!=state)return std::nullopt;
            return std::vector<std::uint8_t>(spawn.begin(),spawn.end());
        } else {
            if(!normal_source_matches(source,output) || output.movement.state_raw()!=output.spawn.state_raw())return std::nullopt;
            const auto spawn=god2cn::CnRemoteActor::encode_logical(output.spawn);
            return std::vector<std::uint8_t>(spawn.begin(),spawn.end());
        }
    },native);
    if(!bytes || !common_name_current(source,recipient,native))return std::nullopt;
    Binding binding(identity_,source,recipient,generation_+1);
    // Prepare the actual map node before send. A native6F replacement clears the
    // old actor/queue: invalidate old tokens even if its submission later fails.
    entries_.insert_or_assign(key,Entry{binding,*position,std::move(native)});++generation_;
    const auto installed=entries_.find(key);
    try {
        if(!submit(installed->second.native,std::move(*bytes))) {
            reject_output(recipient,installed->second.native);entries_.erase(installed);return std::nullopt;
        }
    } catch(...) {reject_output(recipient,installed->second.native);entries_.erase(installed);throw;}
    return binding;
}
bool SharedActorVisibility::current(const Binding& original_binding,const RecoveredPosition& original_model,
    const RecoveredPosition& original_saved) const {
    // Callers may supply a registry-owned Binding; retain all inputs before observers.
    const auto binding=original_binding;const auto model_before=original_model;const auto saved_now=original_saved;
    owner();if(current_busy_){current_reentered_=true;return false;}
    current_busy_=true;current_reentered_=false;
    struct EndCurrent {bool& busy;~EndCurrent(){busy=false;}} end{current_busy_};
    if(taiwan_pk_departed(binding.source())||taiwan_pk_departed(binding.recipient())||outward_pending(binding.source()))return false;
    const auto retained=chat_actor_snapshot(binding,model_before);if(!retained)return false;
    const auto snapshot=retained->state_->entry;
    const auto receiver=std::visit([](const auto& native)->std::variant<std::shared_ptr<Session>,std::shared_ptr<SharedCredentialConnection>> {
        return native.connection.lock();
    },snapshot.native);
    const auto same_entry=[&] {
        if(current_reentered_ || !chat_actor_snapshot_current(*retained))return false;
        const auto actual=entries_.find({binding.source().session,binding.recipient().session});
        if(actual==entries_.end() || !matches(binding,actual->second) || actual->second.position!=model_before ||
           actual->second.native.index()!=snapshot.native.index())return false;
        return std::visit([&](const auto& native) {
            using Connection=decltype(native.connection.lock());
            const auto retained=std::get_if<Connection>(&receiver);
            return retained && *retained && native.connection.lock()==*retained;
        },actual->second.native);
    };
    if(!same_entry() || !common_name_current(binding.source(),binding.recipient(),snapshot.native) || !same_entry())return false;
    const auto saved=presence_->saved_position(binding.source());
    if(!same_entry() || !saved || *saved!=saved_now || saved_now.area!=model_before.area || saved_now.scene!=model_before.scene)return false;
    const bool bound=recipient_bound(binding.recipient(),snapshot.native,model_before);
    if(!bound || !same_entry())return false;
    // Re-read source after receiver repository observers; no stale map iterator
    // is dereferenced if one of those actual observers replaced/released a node.
    const auto after=presence_->saved_position(binding.source());
    if(!after || *after!=saved_now || !same_entry() ||
       !common_name_current(binding.source(),binding.recipient(),snapshot.native) || !same_entry())return false;
    // Repeat the original non-callback transport conditions after the final
    // repository observer. Keep legacy phase policy; raw chat has its own path.
    return std::visit([&](const auto& connection) {
        using Connection=typename std::decay_t<decltype(connection)>::element_type;
        if constexpr(std::is_same_v<Connection,Session>)
            return connection->id()==binding.recipient().session && connection->account_id==binding.recipient().account &&
                connection->character_id==binding.recipient().character && connection->recovered_world_ready() &&
                (connection->state()==SessionState::InWorld || connection->state()==SessionState::CharacterSelected);
        else return !connection->closing() && connection->role()==SharedCredentialConnection::Transport::Role::World &&
            connection->world_session_id()==binding.recipient().session && connection->verified_account_id()==binding.recipient().account &&
            connection->world_character_offered(binding.recipient().character);
    },receiver);
}
std::optional<SharedActorVisibility::MovementRecipient> SharedActorVisibility::movement(
    const Binding& binding,const RecoveredPosition& before) const {
    owner();if(!current(binding,before,before))return std::nullopt;
    const auto& entry=entries_.at({binding.source().session,binding.recipient().session});
    return std::visit([&](const auto& output)->MovementRecipient {
        using Output=std::decay_t<decltype(output)>;
        if constexpr(std::is_same_v<Output,Taiwan>)
            return {binding.recipient(),TaiwanMovement{output.connection,output.movement}};
        else return {binding.recipient(),MainlandMovement{output.connection,output.movement}};
    },entry.native);
}
std::optional<SharedActorVisibility::MainlandChatActor> SharedActorVisibility::mainland_chat_actor(
    const Binding& binding,const RecoveredPosition& position) const {
    owner();if(!current(binding,position,position))return std::nullopt;
    const auto entry=entries_.at({binding.source().session,binding.recipient().session});
    const auto cn=std::get_if<Mainland>(&entry.native);
    if(!cn)return std::nullopt;
    // Copy before receiver-environment callbacks: they may invalidate/replace
    // the registry. Never retain a map-entry pointer across an actual owner.
    const auto snapshot=*cn;std::string expected_name;
    if(snapshot.spawn.native_language_tag()==0)expected_name=std::string(snapshot.spawn.wire_name());
    else {
        if(!snapshot.native_text || !snapshot.native_text->current(snapshot.spawn))return std::nullopt;
        expected_name=snapshot.native_text->expected_native_strings()[0];
    }
    if(expected_name.empty() || !current(binding,position,position))return std::nullopt;
    // Native00532410 stores low12 identity as DWORD+18;00531EA0 compares
    // replyDWORD5 with exactly that entry. Not a DB ID or an allocated alias.
    return MainlandChatActor{snapshot.connection,snapshot.spawn.identity(),std::move(expected_name),
        snapshot.spawn.native_language_tag(),snapshot.raw_name_state};
}
std::optional<SharedActorVisibility::TaiwanChatActor> SharedActorVisibility::taiwan_chat_actor(
    const Binding& binding,const RecoveredPosition& position) const {
    owner();if(taiwan_chat_busy_){taiwan_chat_reentered_=true;return std::nullopt;}
    taiwan_chat_busy_=true;taiwan_chat_reentered_=false;
    struct EndRead {bool& busy;~EndRead(){busy=false;}} end{taiwan_chat_busy_};
    if(taiwan_pk_departed(binding.source())||taiwan_pk_departed(binding.recipient())||outward_pending(binding.source()))return std::nullopt;
    const auto retained=chat_actor_snapshot(binding,position);if(!retained)return std::nullopt;
    const auto snapshot=retained->state_->entry;
    const auto native=std::get_if<Taiwan>(&snapshot.native);if(!native)return std::nullopt;
    const auto receiver=native->connection.lock();
    if(!receiver || !native->raw_name_state)return std::nullopt;
    const auto state=*native->raw_name_state;
    if(!state.available())return std::nullopt;
    const auto logical=RecoveredRemoteActor::encode_logical(native->spawn);
    const auto first=std::uint32_t(logical[1])|(std::uint32_t(logical[2])<<8)|
        (std::uint32_t(logical[3])<<16)|(std::uint32_t(logical[4])<<24);
    const bool raw_selector=(first&(std::uint32_t{1}<<25))!=0;
    const bool actual_selector=state.simplified();
    if(raw_selector!=actual_selector)return std::nullopt; // Actual postadapted names need their own issuer.
    const auto same_entry=[&] {
        if(taiwan_chat_reentered_ || !chat_actor_snapshot_current(*retained))return false;
        const auto actual=entries_.find({binding.source().session,binding.recipient().session});
        if(actual==entries_.end() || !matches(binding,actual->second) || actual->second.position!=position)return false;
        const auto tw=std::get_if<Taiwan>(&actual->second.native);
        return tw && tw->connection.lock()==receiver && RecoveredRemoteActor::encode_logical(tw->spawn)==logical &&
            tw->raw_name_state && tw->raw_name_state->same_source(state);
    };
    const auto qualify=[&] {
        if(!same_entry())return false;
        const auto source=presence_->ready_lease(binding.source().session,binding.source().account,binding.source().character);
        if(!same_entry() || !source || *source!=binding.source())return false;
        const auto saved=presence_->saved_position(binding.source());
        if(!same_entry() || !saved || *saved!=position)return false;
        const auto recipient=presence_->ready_lease(binding.recipient().session,binding.recipient().account,binding.recipient().character);
        if(!same_entry() || !recipient || *recipient!=binding.recipient())return false;
        const auto receiver_position=presence_->saved_position(binding.recipient());
        return same_entry() && receiver_position && receiver_position->area==position.area && receiver_position->scene==position.scene &&
            !receiver->closing() && receiver->id()==binding.recipient().session && receiver->account_id==binding.recipient().account &&
            receiver->character_id==binding.recipient().character && receiver->recovered_world_ready() &&
            (receiver->state()==SessionState::InWorld || receiver->state()==SessionState::InBattle) &&
            receiver->common_world_delivery_current(binding.recipient().account,binding.recipient().character,binding.recipient().generation) &&
            !receiver->common_world_entry_current(binding.recipient().account,binding.recipient().character,binding.recipient().generation);
    };
    if(!qualify())return std::nullopt;
    const auto phase=receiver->state();const auto battle=receiver->battle_generation();
    const bool current_before=state.current(*receiver);
    if(!current_before || !qualify() || receiver->state()!=phase || receiver->battle_generation()!=battle)return std::nullopt;
    const auto begin=logical.begin()+29,end_name=std::find(begin,logical.begin()+45,0);
    if(end_name==logical.begin()+45)return std::nullopt;
    const std::string name(begin,end_name);
    const bool current_after=state.current(*receiver);
    if(!current_after || !qualify() || receiver->state()!=phase || receiver->battle_generation()!=battle)return std::nullopt;
    return TaiwanChatActor{receiver,native->spawn.identity(),name,state};
}
std::optional<std::vector<SharedActorVisibility::Binding>> SharedActorVisibility::movement_bindings(
    const Lease& source,const RecoveredPosition& before) const {
    owner();if(taiwan_pk_departed(source))return std::nullopt;
    const auto saved=presence_->saved_position(source);
    if(!saved || taiwan_pk_departed(source)||outward_pending(source) || *saved!=before)return std::nullopt;
    std::vector<Binding> bindings;
    for(const auto& [key,entry]:entries_)if(entry.binding.source()==source) {
        if(taiwan_appearance_pending(key))return std::nullopt;
        if(!current(entry.binding,before,before))return std::nullopt;
        bindings.push_back(entry.binding);
    }
    return bindings;
}
bool SharedActorVisibility::complete_movement_set(const Lease& source,const RecoveredPosition& before,
    const RecoveredPosition& saved_now,std::span<const Binding> supplied) const {
    owner();if(taiwan_pk_departed(source)||outward_pending(source))return false;
    std::size_t count=0;
    for(const auto& [key,entry]:entries_)if(entry.binding.source()==source) {
        if(taiwan_appearance_pending(key))return false;
        ++count;bool included=false;
        for(const auto& token:supplied)if(matches(token,entry)) {included=true;break;}
        if(!included || !current(entry.binding,before,saved_now))return false;
    }
    return count==supplied.size(); // Preparation separately rejects duplicates.
}
bool SharedActorVisibility::advance(const Binding& binding,const RecoveredPosition& before,const RecoveredPosition& after) {
    reject_taiwan_return_reentry();
    owner();
    if(taiwan_appearance_pending({binding.source().session,binding.recipient().session}))return false;
    if(after.revision<=before.revision || after.x>0x7ff || after.y>0x7ff || !current(binding,before,after))return false;
    auto& entry=entries_.at({binding.source().session,binding.recipient().session});
    const bool advanced=std::visit([&](auto& output) {
        using Output=std::decay_t<decltype(output)>;
        if constexpr(std::is_same_v<Output,Taiwan>) {
            const auto spawn=RecoveredRemoteActor::with_position(output.spawn,after.x,after.y);
            const auto move=RecoveredRemoteActorMove::with_position(output.movement,after.x,after.y);
            if(!spawn || !move)return false;
            output.spawn=*spawn;output.movement=*move;
        } else {
            const auto spawn=god2cn::CnRemoteActor::with_position(output.spawn,after.x,after.y);
            const auto move=god2cn::CnRemoteActorMove::with_position(output.movement,after.x,after.y);
            if(!spawn || !move)return false;
            output.spawn=*spawn;output.movement=*move;
        }
        return true;
    },entry.native);
    if(advanced)entry.position=after;
    return advanced;
}
bool SharedActorVisibility::hide(const Binding& original_binding) {
    reject_taiwan_return_reentry();
    const auto binding=original_binding;
    owner();if(outward_pending(binding.source()))return false;
    const auto keepalive=taiwan_appearance_.empty()?std::shared_ptr<SharedActorVisibility>{}:shared_from_this();
    const auto pending=taiwan_appearance_.find({binding.source().session,binding.recipient().session});
    if(pending!=taiwan_appearance_.end() && matches(binding,pending->second->before.state_->entry)) {
        const auto state=pending->second;const bool issued=state->issued;
        finish_taiwan_appearance(state,false);if(issued)return true;
    }
    const auto found=entries_.find({binding.source().session,binding.recipient().session});
    if(found==entries_.end() || !matches(binding,found->second))return false;
    auto entry=std::move(found->second);entries_.erase(found); // Invalidate before callbacks/allocations.
    if(!recipient_bound(binding.recipient(),entry.native,entry.position)) {
        reject_output(binding.recipient(),entry.native);return true;
    }
    try {
    auto bytes=std::visit([](const auto& output) {
        using Output=std::decay_t<decltype(output)>;
        if constexpr(std::is_same_v<Output,Taiwan>) {
            const auto record=RecoveredRemoteActorRemove::encode_logical(output.removal);
            return std::vector<std::uint8_t>(record.begin(),record.end());
        } else {
            const auto record=god2cn::CnRemoteActorRemove::encode_logical(output.removal);
            return std::vector<std::uint8_t>(record.begin(),record.end());
        }
    },entry.native);
    if(submit(entry.native,std::move(bytes)))return true;
    reject_output(binding.recipient(),entry.native);return false;
    } catch(...) {reject_output(binding.recipient(),entry.native);throw;}
}
void SharedActorVisibility::reset_recipient(const Lease& original_lease) {
    reject_taiwan_return_reentry();
    const auto lease=original_lease;
    owner();const auto keepalive=taiwan_appearance_.empty()?std::shared_ptr<SharedActorVisibility>{}:shared_from_this();
    cancel_taiwan_appearance(lease);cancel_outward(lease);
    for(auto it=entries_.begin();it!=entries_.end();)
        if(it->second.binding.recipient()==lease)it=entries_.erase(it);else ++it;
}
void SharedActorVisibility::release(const Lease& original_lease) {
    reject_taiwan_return_reentry();
    const auto lease=original_lease;
    owner();
    // Lifecycle may arrive before the asynchronous cohort failure callback.
    // Detach exact UNSENT successor models before generic hide can emit73.
    if(const auto at=taiwan_pk_return_consumptions_.find(lease.session);at!=taiwan_pk_return_consumptions_.end())
        if(const auto pending=at->second.lock()){
            const auto endpoint=pending->records.state_->plan->endpoints.find(lease.session);
            if(endpoint!=pending->records.state_->plan->endpoints.end()&&endpoint->second.lease==lease)
                cancel_taiwan_pk_return_consumption_state(*pending);
        }const auto keepalive=taiwan_appearance_.empty()?std::shared_ptr<SharedActorVisibility>{}:shared_from_this();
    std::shared_ptr<TaiwanPkDepartureState> retiring;std::size_t retiring_index=0;
    if(const auto found=taiwan_pk_departures_.find(lease.session);found!=taiwan_pk_departures_.end())
        for(std::size_t i=0;i<2;++i)if(found->second->leases[i]==lease){
            retiring=found->second;retiring_index=i;break;
        }
    if(retiring){
        retiring->poisoned=true;
        if(retiring->retiring[retiring_index])return; // Outer exact release still owns cleanup/blocking.
        retiring->retiring[retiring_index]=true;
    }
    struct EndRetire{std::shared_ptr<TaiwanPkDepartureState> state;std::size_t index;
        ~EndRetire(){if(state)state->retiring[index]=false;}}end_retire{retiring,retiring_index};
    cancel_taiwan_appearance(lease);cancel_outward(lease);
    for(auto it=entries_.begin();it!=entries_.end();) {
        const auto& binding=it->second.binding;
        if(binding.recipient()==lease) {it=entries_.erase(it);continue;}
        if(binding.source()==lease) {
            const auto token=binding;++it;
            // Continue removing every incidence even if one native send fails.
            // No committed position is rolled back. Real owner re-entry recovers.
            try {hide(token);}catch(...) {}
        } else ++it;
    }
    // CUSTOM-0113 only this exact lifecycle lease retires its marker. Never
    // unblock the other participant, an unrelated token or a successor lease.
    const auto marker=taiwan_pk_departures_.find(lease.session);
    if(retiring&&marker!=taiwan_pk_departures_.end()&&marker->second==retiring)
        taiwan_pk_departures_.erase(marker);
}
}
