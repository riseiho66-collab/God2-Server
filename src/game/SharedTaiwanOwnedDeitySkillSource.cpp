#include "game/SharedTaiwanOwnedDeitySkillSource.h"
#include "protocol/TaiwanNativeSkillCommand.h"
#include "handlers/RecoveredOwnedCompanions.h"
#include <algorithm>
#include <map>
#include <exception>
#include <stdexcept>
#include <thread>

namespace god2 {
struct SharedTaiwanOwnedDeitySkillSource::Publication {
    std::weak_ptr<Impl> origin;
    std::weak_ptr<Session> session;
    Session::NormalWorldInitialization initialization;
    SharedWorldPresence::Lease lease;
    SessionState phase;
    std::uint64_t battle_generation;
    std::optional<RecoveredOwnedCompanions::SelectionPublication> last;
    std::optional<Session::WorldResponseWrite> write;
    Publication(std::weak_ptr<Impl> owner,std::weak_ptr<Session> actual,
        Session::NormalWorldInitialization init,const Scope& scope)
        :origin(std::move(owner)),session(std::move(actual)),initialization(std::move(init)),
         lease(scope.lease),phase(scope.phase),battle_generation(scope.battle_generation) {}
};
struct SharedTaiwanOwnedDeitySkillSource::CallbackData {
    std::weak_ptr<Impl> origin;
    std::weak_ptr<Session> session;
    Session::NormalWorldInitialization initialization;
    SharedWorldPresence::Lease lease;
    SessionState phase;
    std::uint64_t battle_generation;
    const std::vector<std::uint8_t> keys;
    std::vector<std::optional<RecoveredOwnedCompanions::SelectionPublication>> results;
    std::shared_ptr<Publication> candidate;
    std::size_t next=0;
    bool invalid=false,mutation_attempted=false,published=false;
    CallbackData(std::weak_ptr<Impl> owner,std::weak_ptr<Session> actual,
        Session::NormalWorldInitialization init,const Scope& scope,std::span<const std::uint8_t> input)
        :origin(owner),session(actual),initialization(init),lease(scope.lease),phase(scope.phase),
         battle_generation(scope.battle_generation),keys(input.begin(),input.end()),results(keys.size()),
         candidate(std::make_shared<Publication>(std::move(owner),std::move(actual),std::move(init),scope)) {}
};
struct SharedTaiwanOwnedDeitySkillSource::Impl {
    const std::thread::id thread=std::this_thread::get_id();
    const std::shared_ptr<SharedWorldPresence> presence;
    SqliteCompanionRepository& companions;
    const NativeSkillCatalog& catalog;
    const Mode mode;
    const std::size_t capacity;
    struct SelectionSlot {
        std::weak_ptr<Session> session;
        SharedWorldPresence::Lease lease;
        std::shared_ptr<CallbackData> pending;
        std::shared_ptr<const Publication> published;
        SelectionSlot(std::weak_ptr<Session> s,const SharedWorldPresence::Lease& l):session(std::move(s)),lease(l) {}
    };
    std::map<std::uint64_t,std::shared_ptr<SelectionSlot>> selections;
    std::shared_ptr<CallbackData> active;
    bool publication_live=true;
    bool reading=false,reentered=false;
    Impl(std::shared_ptr<SharedWorldPresence> p,SqliteCompanionRepository& c,const NativeSkillCatalog& n,
        Mode selected,std::size_t count)
        :presence(std::move(p)),companions(c),catalog(n),mode(selected),capacity(count) {}
    ~Impl(){if(thread!=std::this_thread::get_id())std::terminate();}
    struct Read {
        Impl& owner;
        explicit Read(Impl& state):owner(state) {
            if(owner.thread!=std::this_thread::get_id())throw std::logic_error("TW saved skill game owner mismatch");
            if(owner.reading){owner.reentered=true;throw std::logic_error("TW saved skill reentry rejected");}
            owner.reading=true;owner.reentered=false;
        }
        ~Read(){owner.reading=false;}
    };
    bool callback_current(Session& s,const std::shared_ptr<CallbackData>& data) const {
        // ready_lease invokes observers; recheck the entire private/local tuple afterwards.
        const auto exact=[&]() {
            if(mode!=Mode::SelectionPublicationRequired || !publication_live || !data || active!=data ||
               data->origin.lock().get()!=this || data->invalid || reentered || data->session.lock().get()!=&s ||
               s.closing() || s.state()!=data->phase || data->phase!=SessionState::InWorld ||
               s.battle_generation()!=data->battle_generation || s.account_id!=data->lease.account ||
               s.character_id!=data->lease.character || s.id()!=data->lease.session ||
               !data->initialization.entry_written() ||
               !s.normal_world_initialization_current_on_game(data->initialization))return false;
            const auto at=selections.find(s.id());
            if(at==selections.end() || at->second->session.lock().get()!=&s ||
               at->second->lease!=data->lease || at->second->pending!=data)return false;
            return presence->retained_ready_current(data->lease) && s.recovered_world_ready() &&
                s.common_world_delivery_current(data->lease.account,data->lease.character,data->lease.generation) &&
                !s.common_world_entry_current(data->lease.account,data->lease.character,data->lease.generation);
        };
        if(!exact())return false;
        const auto lease=presence->ready_lease(s.id(),s.account_id,s.character_id);
        return lease && *lease==data->lease && exact();
    }
    bool publication_current(Session& s,const std::shared_ptr<const Publication>& p) const {
        // ready_lease invokes observers; recheck the entire private/local tuple afterwards.
        const auto exact=[&]() {
            if(mode!=Mode::SelectionPublicationRequired || !publication_live || reentered || !p ||
               p->origin.lock().get()!=this || p->session.lock().get()!=&s || !p->last || !p->write ||
               p->write->status()!=Session::WorldResponseWriteStatus::Written ||
               !s.world_response_write_current_on_game(*p->write) || !p->initialization.entry_written() ||
               !s.normal_world_initialization_current_on_game(p->initialization) ||
               s.state()!=p->phase || p->phase!=SessionState::InWorld ||
               s.battle_generation()!=p->battle_generation || s.account_id!=p->lease.account ||
               s.character_id!=p->lease.character || s.id()!=p->lease.session)return false;
            const auto at=selections.find(s.id());
            if(at==selections.end() || at->second->session.lock().get()!=&s ||
               at->second->lease!=p->lease || at->second->pending || at->second->published!=p)return false;
            return !s.closing() && presence->retained_ready_current(p->lease) && s.recovered_world_ready() &&
                s.common_world_delivery_current(p->lease.account,p->lease.character,p->lease.generation) &&
                !s.common_world_entry_current(p->lease.account,p->lease.character,p->lease.generation);
        };
        if(!exact())return false;
        const auto lease=presence->ready_lease(s.id(),s.account_id,s.character_id);
        return lease && *lease==p->lease && exact();
    }
    static bool matches_saved(const Publication& p,const SelectedDeitySkillReadset& saved) {
        if(!p.last)return false;
        const auto& commit=p.last->committed();const auto& a=commit.deity();const auto& b=saved.deity();
        if(commit.account()!=saved.account() || commit.character()!=saved.character() ||
           commit.after()!=saved.selection() || a.revision!=b.revision || a.provenance!=b.provenance ||
           a.snapshot.declaration.encode()!=b.snapshot.declaration.encode() ||
           a.snapshot.status.encode()!=b.snapshot.status.encode() || a.snapshot.skills.size()!=b.snapshot.skills.size())
            return false;
        for(std::size_t i=0;i<a.snapshot.skills.size();++i)
            if(a.snapshot.skills[i].encode()!=b.snapshot.skills[i].encode())return false;
        return true;
    }
    static bool components_match(const CallbackData& data,std::span<const std::uint8_t> wire) noexcept {
        if(data.keys.empty() || data.next!=data.keys.size())return false;
        std::size_t next=0;
        for(std::size_t at=0;at<wire.size();) {
            if(wire.size()-at<4)return false;
            const auto size=std::size_t(wire[at])+(std::size_t(wire[at+1])<<8);
            if(size<4 || size>RecoveredWorldFrame::max_logical_size+3 || size>wire.size()-at)return false;
            if(next<data.results.size()) {
                if(!data.results[next])return false;
                const auto& expected=data.results[next]->wire();
                if(expected.size()==size && std::equal(expected.begin(),expected.end(),wire.begin()+at))++next;
            }
            at+=size;
        }
        return next==data.results.size();
    }
    bool local(Session& s,const Scope& scope) const {
        const auto& lease=scope.lease;
        return !reentered && !s.closing() && s.id()==lease.session &&
            s.account_id==lease.account && s.character_id==lease.character &&
            s.state()==scope.phase && (scope.phase==SessionState::InWorld || scope.phase==SessionState::InBattle) &&
            s.battle_generation()==scope.battle_generation && s.recovered_world_ready() &&
            s.common_world_delivery_current(lease.account,lease.character,lease.generation) &&
            !s.common_world_entry_current(lease.account,lease.character,lease.generation) &&
            presence->retained_ready_current(lease);
    }
    bool ready(Session& s,const Scope& scope) const {
        if(!local(s,scope))return false;
        const auto lease=presence->ready_lease(scope.lease.session,scope.lease.account,scope.lease.character);
        const auto position=presence->saved_position(scope.lease);
        return lease && *lease==scope.lease && position && *position==scope.position && local(s,scope);
    }
    std::optional<Scope> capture(Session& s) const {
        if(reentered || s.closing() || !s.account_id || !s.character_id ||
           (s.state()!=SessionState::InWorld && s.state()!=SessionState::InBattle))return std::nullopt;
        const auto phase=s.state();const auto generation=s.battle_generation();
        const auto lease=presence->ready_lease(s.id(),s.account_id,s.character_id);
        if(!lease)return std::nullopt;
        const auto position=presence->saved_position(*lease);if(!position)return std::nullopt;
        Scope scope{*lease,*position,phase,generation};
        return ready(s,scope)?std::optional{scope}:std::nullopt;
    }
    bool self_target_current(Session& s,const SelfTargetInput& input,const Scope& scope,
        const NativeSkillRecord& definition) const {
        if(scope.phase!=SessionState::InWorld || !local(s,scope) ||
           !input.initialization().entry_written() ||
           !s.normal_world_initialization_current_on_game(input.initialization()))return false;
        const auto& logical=input.initialization().entry_logical();
        if(logical.size()!=37 || logical[0]!=0x2a)return false;
        // Same149c 468629 masks the entry handle; 497A90 does NOT mask
        // its incoming target. Never truncate the independent64-bit DB owner.
        const auto entry_handle=static_cast<std::uint16_t>(
            (std::uint16_t{logical[1]}|(std::uint16_t{logical[2]}<<8))&0x3fff);
        return entry_handle==scope.lease.actor_handle &&
            input.request().raw_target()==entry_handle &&
            input.request().kind()==definition.kind && input.request().definition_id()==definition.definition_id &&
            s.normal_world_initialization_current_on_game(input.initialization()) && local(s,scope);
    }
    static bool qualified(const NativeSkillRecord& r,std::uint8_t kind,std::uint8_t id,
                          NativeTaiwanSkillProfile profile) {
        // Main catalog lookup checks metadata, raw row shape/key and all110
        // bytes against the stored digest. Here pin
        // native image, raw key and original110-byte row geometry explicitly.
        const auto counts=native_taiwan_skill_bank_counts(profile);
        if(!native_taiwan_skill_source_matches(r.source,profile) || kind>=4 ||
           id<1 || id>counts[std::size_t(kind)])return false;
        std::int64_t ordinal=id-1;
        for(std::size_t i=0;i<std::size_t(kind);++i)ordinal+=counts[i];
        return r.source_record_index==ordinal && r.kind==kind && r.definition_id==id && r.raw_record.size()==110 &&
            r.raw_record[0]==id && r.raw_record[1]==kind &&
            r.source.native_image_sha256==TaiwanNativeSkillCommand::image_sha256 &&
            r.source_offset==8+r.kind*0x6e04+(r.definition_id-1)*110;
    }
    bool definition_current(const NativeSkillRecord& expected) const {
        const auto actual=catalog.lookup_main_digest_checked(catalog.taiwan_dataset_id(),expected.kind,expected.definition_id);
        return !reentered && actual && *actual==expected;
    }
    bool common_definition_current(const NativeSkillRecord& native,const SharedSkillDefinition& common) const {
        if(!definition_current(native))return false;
        const auto actual=catalog.lookup_shared_definition_main(native.kind,native.definition_id);
        // CUSTOM-0144: retain the original TW input independently of the
        // common parameter base; compare the entire owning value, never rebase.
        return !reentered && actual && actual->requested_native &&
            *actual->requested_native==native && actual->definition==common;
    }
};
std::shared_ptr<SharedTaiwanOwnedDeitySkillSource> SharedTaiwanOwnedDeitySkillSource::create(
    std::shared_ptr<SharedWorldPresence> presence,SqliteCompanionRepository& companions,const NativeSkillCatalog& catalog,
    Mode mode,std::size_t capacity) {
    if(!presence || (mode!=Mode::SavedObservationOnly && mode!=Mode::SelectionPublicationRequired) ||
       (mode==Mode::SelectionPublicationRequired && !capacity))
        throw std::invalid_argument("TW saved skill requires real common presence and explicit publication capacity");
    return std::shared_ptr<SharedTaiwanOwnedDeitySkillSource>(new SharedTaiwanOwnedDeitySkillSource(
        std::make_shared<Impl>(std::move(presence),companions,catalog,mode,capacity)));
}
bool SharedTaiwanOwnedDeitySkillSource::owns_sources(const std::shared_ptr<SharedWorldPresence>& presence,
    const SqliteCompanionRepository& companions,const NativeSkillCatalog& catalog) const noexcept {
    const auto& state=*state_;
    return state.thread==std::this_thread::get_id() && state.presence==presence &&
        &state.companions==&companions && &state.catalog==&catalog;
}
bool SharedTaiwanOwnedDeitySkillSource::publication_required() const noexcept {
    return state_->mode==Mode::SelectionPublicationRequired;
}
void SharedTaiwanOwnedDeitySkillSource::check_selection_callback_entry() {
    const auto self=shared_from_this();const auto state=state_;Impl::Read read(*state);
    if(state->mode!=Mode::SelectionPublicationRequired || !state->publication_live)
        throw std::logic_error("TW selection publication owner retired");
    if(state->active) {
        state->active->invalid=true;
        throw std::logic_error("TW selection original callback reentered");
    }
}
std::optional<SharedTaiwanOwnedDeitySkillSource::SelectionCallback>
SharedTaiwanOwnedDeitySkillSource::begin_selection_callback(Session& session,std::span<const std::uint8_t> keys) {
    const auto self=shared_from_this();const auto state=state_;Impl::Read read(*state);
    if(state->mode!=Mode::SelectionPublicationRequired || !state->publication_live)
        throw std::logic_error("TW selection publication owner retired");
    if(state->active) {
        state->active->invalid=true;
        throw std::logic_error("TW selection original callback reentered");
    }
    if(keys.empty())return std::nullopt;
    const auto actual=session.weak_from_this().lock();
    const auto initialization=session.normal_world_initialization();
    const auto scope=state->capture(session);
    if(actual.get()!=&session || !initialization || !initialization->entry_written() || !scope ||
       scope->phase!=SessionState::InWorld || !session.normal_world_initialization_current(*initialization))
        throw std::runtime_error("TW selection requires exact written normal initialization and ready lease");
    // Every key, marker slot, candidate and map allocation precedes delegation.
    auto data=std::make_shared<CallbackData>(state,actual,*initialization,*scope,keys);
    auto slot=std::make_shared<Impl::SelectionSlot>(actual,scope->lease);
    if(const auto at=state->selections.find(session.id());at!=state->selections.end()) {
        const auto previous=at->second->session.lock();
        if(previous && previous.get()!=&session)
            throw std::runtime_error("TW selection Session incarnation conflict");
        if(previous && at->second->lease==scope->lease)slot->published=at->second->published;
    }else if(state->selections.size()>=state->capacity)
        throw std::runtime_error("TW selection actual session capacity reached");
    slot->pending=data;
    state->selections.insert_or_assign(session.id(),std::move(slot));state->active=data;
    if(!state->callback_current(session,data)) {
        data->invalid=true;state->active.reset();state->selections.at(session.id())->pending.reset();
        throw std::runtime_error("TW selection source changed before delegation");
    }
    return SelectionCallback(std::move(data));
}
std::optional<std::vector<std::uint8_t>> SharedTaiwanOwnedDeitySkillSource::select_deity_for_callback(
    Session& session,RecoveredOwnedCompanions& helper,const RecoveredDeitySelection::Request& request) {
    const auto self=shared_from_this();const auto state=state_;Impl::Read read(*state);
    const auto key=request.key;const auto data=state->active;
    if(!data || !state->callback_current(session,data) || !helper.owns_repository(state->companions) ||
       data->next>=data->keys.size() || data->keys[data->next]!=key)return std::nullopt;
    // Movement may advance position, but never rebase INIT/lease/owner/phase.
    const auto scope=state->capture(session);
    if(!scope || scope->lease!=data->lease || scope->phase!=data->phase ||
       scope->battle_generation!=data->battle_generation || !state->callback_current(session,data))return std::nullopt;
    data->mutation_attempted=true;
    auto result=helper.select_deity_with_source(data->lease.account,data->lease.character,RecoveredDeitySelection::Request{key});
    if(!result)return std::nullopt;
    // No consumed-row SQL after the actual commit; issuer check is pure.
    const auto& commit=result->committed();
    if(!state->companions.issued_selection(commit) || commit.account()!=data->lease.account ||
       commit.character()!=data->lease.character || commit.after().key!=key ||
       commit.deity().snapshot.status.key_raw()!=key || !state->callback_current(session,data))
        throw std::runtime_error("TW selection committed source became stale");
    if(data->next && commit.before()!=std::optional{data->results[data->next-1]->committed().after()})
        throw std::runtime_error("TW selection committed prefix changed between original runs");
    data->results[data->next].emplace(result->publication());++data->next;
    if(const auto at=state->selections.find(session.id());at!=state->selections.end() && at->second->pending==data)
        at->second->published.reset(); // Old equal-key publications cannot resurrect.
    return std::move(*result).take_wire();
}
bool SharedTaiwanOwnedDeitySkillSource::selection_response_matches(Session& session,const SelectionCallback& callback,
    std::span<const std::uint8_t> wire) {
    const auto self=shared_from_this();const auto state=state_;Impl::Read read(*state);
    return state->callback_current(session,callback.data_) && Impl::components_match(*callback.data_,wire);
}
void SharedTaiwanOwnedDeitySkillSource::publish_selection_callback(Session& session,const SelectionCallback& callback,
    const Session::WorldResponseWrite& write) {
    const auto self=shared_from_this();const auto state=state_;Impl::Read read(*state);const auto data=callback.data_;
    if(!state->callback_current(session,data) || !Impl::components_match(*data,write.wire()) ||
       write.status()!=Session::WorldResponseWriteStatus::Pending || !session.world_response_write_current(write))
        throw std::runtime_error("TW selection original response publication mismatch");
    // Candidate/slots were allocated before SQL. Receipt copies retain private
    // ownership only; the Session's whole-frame allocation can still fail earlier.
    data->candidate->last.emplace(*data->results.back());data->candidate->write.emplace(write);
    const auto at=state->selections.find(session.id());
    if(at==state->selections.end() || at->second->pending!=data)
        throw std::runtime_error("TW selection publication holder changed");
    at->second->published=data->candidate;at->second->pending.reset();data->published=true;state->active.reset();
}
void SharedTaiwanOwnedDeitySkillSource::abandon_selection_callback(const SelectionCallback& callback) noexcept {
    const auto state=state_;if(state->thread!=std::this_thread::get_id())std::terminate();
    const auto data=callback.data_;if(!data || data->origin.lock()!=state)return;
    if(!data->published) {
        data->invalid=true;
        if(const auto at=state->selections.find(data->lease.session);at!=state->selections.end() && at->second->pending==data) {
            at->second->pending.reset();
            if(data->mutation_attempted)at->second->published.reset();
        }
        if(data->mutation_attempted)if(const auto session=data->session.lock())try {session->close();}catch(...) {}
    }
    if(state->active==data)state->active.reset();
}
void SharedTaiwanOwnedDeitySkillSource::release_selection(Session& session) {
    const auto state=state_;
    if(state->thread!=std::this_thread::get_id())throw std::logic_error("TW selection release game owner mismatch");
    const auto at=state->selections.find(session.id());
    if(at==state->selections.end() || at->second->session.lock().get()!=&session)return;
    if(at->second->pending)at->second->pending->invalid=true;
    if(state->active && state->active->session.lock().get()==&session)state->active->invalid=true;
    state->selections.erase(at);
}
void SharedTaiwanOwnedDeitySkillSource::invalidate_selection_callbacks() {
    const auto state=state_;
    if(state->thread!=std::this_thread::get_id())throw std::logic_error("TW selection invalidation game owner mismatch");
    if(state->active)state->active->invalid=true;
}
void SharedTaiwanOwnedDeitySkillSource::stop_selection_publications() noexcept {
    const auto state=state_;if(state->thread!=std::this_thread::get_id())std::terminate();
    state->publication_live=false;
    if(state->active) {
        const SelectionCallback callback(state->active);abandon_selection_callback(callback);
    }
    state->selections.clear();
}
std::optional<SharedTaiwanOwnedDeitySkillSource::Observation> SharedTaiwanOwnedDeitySkillSource::observe(
    Session& session,std::uint8_t kind,std::uint8_t id) {
    const auto self=shared_from_this();const auto state=state_;Impl::Read read(*state);
    if(kind>3 || !id)return std::nullopt;
    const auto weak=session.weak_from_this();const auto actual_session=weak.lock();
    if(actual_session.get()!=&session)return std::nullopt;
    const auto scope=state->capture(session);if(!scope)return std::nullopt;
    std::shared_ptr<const Publication> publication;
    if(state->mode==Mode::SelectionPublicationRequired) {
        const auto at=state->selections.find(session.id());
        if(at==state->selections.end())return std::nullopt;
        publication=at->second->published;
        if(!state->publication_current(session,publication) || publication->lease!=scope->lease)return std::nullopt;
    }
    auto definition=state->catalog.lookup_main_digest_checked(state->catalog.taiwan_dataset_id(),kind,id);
    if(!definition || !native_taiwan_skill_source_matches(definition->source,state->catalog.taiwan_profile()) ||
       !Impl::qualified(*definition,kind,id,state->catalog.taiwan_profile()) || !state->ready(session,*scope))return std::nullopt;
    auto saved=state->companions.load_selected_deity_skill(scope->lease.account,scope->lease.character,kind,id);
    if(!saved || (publication && (!state->publication_current(session,publication) ||
       !Impl::matches_saved(*publication,*saved))) || !state->ready(session,*scope) || !state->definition_current(*definition) ||
       !state->companions.selected_deity_skill_current(*saved) || !state->ready(session,*scope))return std::nullopt;
    auto shared=state->catalog.lookup_shared_definition_main(kind,id);
    if(!shared || !shared->requested_native || *shared->requested_native!=*definition ||
       !state->ready(session,*scope) || !state->companions.selected_deity_skill_current(*saved) ||
       !state->common_definition_current(*definition,shared->definition) || !state->ready(session,*scope))return std::nullopt;
    if(publication && (!state->publication_current(session,publication) ||
       !Impl::matches_saved(*publication,*saved)))return std::nullopt;
    auto observation=Observation(state,weak,std::move(*saved),std::move(*definition),std::move(shared->definition),*scope);
    observation.publication_=std::move(publication);
    return observation;
}
std::optional<SharedTaiwanOwnedDeitySkillSource::Observation> SharedTaiwanOwnedDeitySkillSource::observe_world_self(
    Session& session,const RecoveredWorldSkillRequest::Request& request) {
    const auto self=shared_from_this();const auto state=state_;
    // Copy input before any repository observer can release the caller holder.
    const auto owned_request=request;
    if(session.closing() || session.state()!=SessionState::InWorld)return std::nullopt;
    auto initialization=session.normal_world_initialization();
    if(!initialization || !initialization->entry_written() ||
       !session.normal_world_initialization_current_on_game(*initialization))return std::nullopt;
    SelfTargetInput input(owned_request,std::move(*initialization));
    auto observation=observe(session,owned_request.kind(),owned_request.definition_id());
    if(!observation || !state->self_target_current(session,input,observation->scope_,observation->definition_))
        return std::nullopt;
    observation->self_target_input_=std::move(input);
    return observation;
}
bool SharedTaiwanOwnedDeitySkillSource::current(Session& session,const Observation& observation) {
    const auto self=shared_from_this();const auto state=state_;Impl::Read read(*state);
    // Own the argument before observers; they may release its caller holder.
    const auto owned=observation;
    const auto actual_session=owned.session_.lock();
    if(owned.origin_.lock()!=state || actual_session.get()!=&session ||
       (state->mode==Mode::SelectionPublicationRequired &&
        (!state->publication_current(session,owned.publication_) || !Impl::matches_saved(*owned.publication_,owned.saved_))) ||
       !state->ready(session,owned.scope_) ||
       (owned.self_target_input_ && !state->self_target_current(session,*owned.self_target_input_,owned.scope_,owned.definition_)) ||
       !state->common_definition_current(owned.definition_,owned.common_definition_) ||
       !state->companions.selected_deity_skill_current(owned.saved_))return false;
    return (state->mode!=Mode::SelectionPublicationRequired ||
            (state->publication_current(session,owned.publication_) && Impl::matches_saved(*owned.publication_,owned.saved_))) &&
        state->ready(session,owned.scope_) &&
        state->common_definition_current(owned.definition_,owned.common_definition_) && state->ready(session,owned.scope_) &&
        (!owned.self_target_input_ || state->self_target_current(session,*owned.self_target_input_,owned.scope_,owned.definition_)) &&
        (state->mode!=Mode::SelectionPublicationRequired || state->publication_current(session,owned.publication_));
}
}
