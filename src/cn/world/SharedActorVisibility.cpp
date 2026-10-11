#include "cn/world/SharedActorVisibility.h"
#include "cn/world/SharedInitialScene.h"
#include "game/SharedNativeActorNameSource.h"
#include <limits>
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
bool SharedActorVisibility::taiwan_pk_departed(const Lease& lease)const noexcept {
    // The in-progress pair stays blocked even if an exact lifecycle release
    // reenters cancellation. Old markers never block a successor lease.
    if(taiwan_pk_withdrawing_)for(const auto& owner:taiwan_pk_withdrawing_->leases)if(owner==lease)return true;
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
            return !actual.raw_name_state || (actual.raw_name_state->source_revision==expected->raw_name_state->source_revision &&
                actual.raw_name_state->wire_codepage==expected->raw_name_state->wire_codepage &&
                actual.raw_name_state->actual_global_word_d8==expected->raw_name_state->actual_global_word_d8 &&
                actual.raw_name_state->actual_global_word_da==expected->raw_name_state->actual_global_word_da);
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
std::optional<SharedActorVisibility::TaiwanPkDeparture> SharedActorVisibility::withdraw_taiwan_pk(
    std::array<Lease,2> leases,std::array<std::shared_ptr<Session>,2> sessions,
    std::array<Session::NativePkEntryHold,2> holds) {
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
    const auto source=original_source;
    owner();if(!done)throw std::invalid_argument("Outward initial visibility completion required");
    if(taiwan_pk_departed(source)){try{done(std::nullopt);}catch(...){}return;}
    auto state=std::make_shared<OutwardState>();state->source=source;state->current=std::move(current);state->done=std::move(done);
    try {
        const auto self=shared_from_this();
        const auto position=presence_->saved_position(source);
        const auto old=outward_.find(source.session);
    if(!state->current || !position || taiwan_pk_departed(source) || source.actor_handle>0xfff ||
           recipients.size()>256 || recipients.size()>std::numeric_limits<std::uint64_t>::max()-generation_ ||
           (old!=outward_.end() && !old->second.expired())){finish_outward(state,false);return;}
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
            Binding binding(identity_,source,recipient.lease,generation_+state->bindings.size()+1);
            if(!state->staged.emplace(key,Entry{binding,*position,native}).second){finish_outward(state,false);return;}
            std::vector<god2cn::Bytes> records;records.push_back(std::move(*bytes));
            state->bindings.push_back(binding);
            state->deliveries.push_back({key,std::move(recipient.native),std::move(records)});
        }
        // All model nodes/bindings/complete81-byte records allocate before IO.
        if(old!=outward_.end())outward_.erase(old);
        outward_.emplace(source.session,state);generation_+=state->bindings.size();
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
    bool published=false;
};
SharedActorVisibility::TaiwanInitialPublication::TaiwanInitialPublication(std::shared_ptr<State> state)
    :state_(std::move(state)){}
std::span<const god2cn::Bytes> SharedActorVisibility::TaiwanInitialPublication::records() const {
    return state_->records;
}
std::span<const god2cn::Bytes> SharedActorVisibility::TaiwanInitialPublication::supplied_records() const {
    return state_->supplied_records;
}
std::shared_ptr<SharedActorVisibility::TaiwanInitialPublication>
SharedActorVisibility::prepare_initial_taiwan_recipient(const Lease& recipient,
    const std::shared_ptr<Session>& connection,std::vector<InitialTaiwanActor> actors) {
    owner();
    if(actors.size()>128 || actors.size()>std::numeric_limits<std::uint64_t>::max()-generation_)return {};
    auto state=std::make_shared<TaiwanInitialPublication::State>();
    state->identity=identity_;state->connection=connection;state->recipient=recipient;
    auto token=std::shared_ptr<TaiwanInitialPublication>(new TaiwanInitialPublication(state));
    if(!taiwan_initial_current(token,connection,recipient,false))return {};
    state->records.reserve(actors.size());state->supplied_records.reserve(actors.size());
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
        Binding binding(identity_,actor.source,recipient,generation_+state->staged.size()+1);
        if(!state->staged.emplace(Key{actor.source.session,recipient.session},
            Entry{binding,*position,Native{std::move(actor.native)}}).second)return {};
        state->records.emplace_back(record.begin(),record.end());
        state->supplied_records.emplace_back(supplied.begin(),supplied.end());
    }
    if(!taiwan_initial_current(token,connection,recipient,false))return {};
    // Server incarnation lineage only, never a native pool counter or rule.
    generation_+=state->staged.size();return token;
}
bool SharedActorVisibility::taiwan_initial_current(const std::shared_ptr<TaiwanInitialPublication>& token,
    const std::shared_ptr<Session>& connection,const Lease& recipient,bool activated) const {
    owner();if(!token || !token->state_ || !connection)return false;
    const auto& state=*token->state_;
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
    return !taiwan_pk_departed(recipient)&&!state.published && state.staged.size()==staged.size(); // Native resources, complete peer policy and scene causality remain with actual issuer.
}
bool SharedActorVisibility::publish_initial_taiwan(const std::shared_ptr<TaiwanInitialPublication>& token,
    const std::shared_ptr<Session>& connection,const Lease& recipient) {
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
    if(!state.source_revision || !state.current || (state.wire_codepage!=936 && state.wire_codepage!=950))return std::nullopt;
    const auto logical=RecoveredRemoteActor::encode_logical(native->spawn);
    const auto first=std::uint32_t(logical[1])|(std::uint32_t(logical[2])<<8)|
        (std::uint32_t(logical[3])<<16)|(std::uint32_t(logical[4])<<24);
    const bool raw_selector=(first&(std::uint32_t{1}<<25))!=0;
    const bool actual_selector=state.actual_global_word_d8==4 && state.actual_global_word_da==2;
    if(raw_selector!=actual_selector)return std::nullopt; // Actual postadapted names need their own issuer.
    const auto same_entry=[&] {
        if(taiwan_chat_reentered_ || !chat_actor_snapshot_current(*retained))return false;
        const auto actual=entries_.find({binding.source().session,binding.recipient().session});
        if(actual==entries_.end() || !matches(binding,actual->second) || actual->second.position!=position)return false;
        const auto tw=std::get_if<Taiwan>(&actual->second.native);
        return tw && tw->connection.lock()==receiver && RecoveredRemoteActor::encode_logical(tw->spawn)==logical &&
            tw->raw_name_state && tw->raw_name_state->source_revision==state.source_revision &&
            tw->raw_name_state->wire_codepage==state.wire_codepage &&
            tw->raw_name_state->actual_global_word_d8==state.actual_global_word_d8 &&
            tw->raw_name_state->actual_global_word_da==state.actual_global_word_da;
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
    const bool current_before=state.current(*receiver,state.source_revision,state.wire_codepage,state.actual_global_word_d8,state.actual_global_word_da);
    if(!current_before || !qualify() || receiver->state()!=phase || receiver->battle_generation()!=battle)return std::nullopt;
    const auto begin=logical.begin()+29,end_name=std::find(begin,logical.begin()+45,0);
    if(end_name==logical.begin()+45)return std::nullopt;
    const std::string name(begin,end_name);
    const bool current_after=state.current(*receiver,state.source_revision,state.wire_codepage,state.actual_global_word_d8,state.actual_global_word_da);
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
    const auto lease=original_lease;
    owner();const auto keepalive=taiwan_appearance_.empty()?std::shared_ptr<SharedActorVisibility>{}:shared_from_this();
    cancel_taiwan_appearance(lease);cancel_outward(lease);
    for(auto it=entries_.begin();it!=entries_.end();)
        if(it->second.binding.recipient()==lease)it=entries_.erase(it);else ++it;
}
void SharedActorVisibility::release(const Lease& original_lease) {
    const auto lease=original_lease;
    owner();const auto keepalive=taiwan_appearance_.empty()?std::shared_ptr<SharedActorVisibility>{}:shared_from_this();
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
