#include "game/SharedTaiwanIssuedSkillSource.h"
#include "protocol/RecoveredWorldFrame.h"
#include <exception>
#include <limits>
#include <map>
#include <stdexcept>
#include <thread>

namespace god2 {
struct SharedTaiwanIssuedSkillSource::Storage {
    std::weak_ptr<State> origin;
    std::weak_ptr<Session> session;
    SharedWorldPresence::Lease lease;
    RecoveredPosition position;
    std::uint64_t battle_generation,revision;
    Model model;
};
struct SharedTaiwanIssuedSkillSource::PublicationStorage {
    std::weak_ptr<State> origin;
    std::weak_ptr<Session> session;
    Session::NativeBattleSkill delivery;
    std::shared_ptr<const Storage> before,next;
    PublicationStatus status=PublicationStatus::Pending;
    bool before_write_accepted=false;
};
struct SharedTaiwanIssuedSkillSource::State {
    const std::thread::id thread=std::this_thread::get_id();
    const std::shared_ptr<SharedWorldPresence> presence;
    const NativeSkillCatalog& catalog;
    const std::size_t capacity;
    std::map<std::uint64_t,std::shared_ptr<const Storage>> bindings;
    std::map<std::uint64_t,std::shared_ptr<PublicationStorage>> pending;
    std::uint64_t revision=0;
    bool operating=false,poisoned=false;
    State(std::shared_ptr<SharedWorldPresence> p,const NativeSkillCatalog& c,std::size_t limit)
        :presence(std::move(p)),catalog(c),capacity(limit) {}
    ~State(){if(thread!=std::this_thread::get_id())std::terminate();}
    void owner() const {if(thread!=std::this_thread::get_id())throw std::logic_error("TW issued skill game owner mismatch");}
    struct Operation {
        State& state;
        explicit Operation(State& s):state(s) {
            state.owner();if(state.operating){state.poisoned=true;throw std::logic_error("TW issued skill reentry rejected");}
            state.operating=true;state.poisoned=false;
        }
        ~Operation(){state.operating=false;}
    };
    bool ready(Session& s,const Storage& saved) const {
        const auto local=[&] {
            return !poisoned && saved.session.lock().get()==&s && !s.closing() && s.state()==SessionState::InBattle &&
                s.id()==saved.lease.session && s.account_id==saved.lease.account && s.character_id==saved.lease.character &&
                s.battle_generation()==saved.battle_generation && s.recovered_world_ready() &&
                s.common_world_delivery_current(saved.lease.account,saved.lease.character,saved.lease.generation) &&
                !s.common_world_entry_current(saved.lease.account,saved.lease.character,saved.lease.generation);
        };
        if(!local())return false;
        const auto lease=presence->ready_lease(saved.lease.session,saved.lease.account,saved.lease.character);
        const auto position=presence->saved_position(saved.lease);
        return lease && *lease==saved.lease && position && *position==saved.position && local();
    }
    bool stored(Session& s,const std::shared_ptr<const Storage>& saved) const {
        if(!saved)return false;
        const auto at=bindings.find(s.id());
        return at!=bindings.end() && at->second==saved && ready(s,*saved);
    }
    bool retained(Session& s,const std::shared_ptr<const Storage>& saved) const {
        return !pending.contains(s.id()) && !s.native_battle_skill_publication_pending() && stored(s,saved);
    }
    bool pending_current(Session& s,const std::shared_ptr<PublicationStorage>& item) const {
        if(!item || item->origin.lock().get()!=this || item->session.lock().get()!=&s ||
           item->status!=PublicationStatus::Pending)return false;
        const auto at=pending.find(s.id());
        if(at==pending.end() || at->second!=item || !stored(s,item->before))return false;
        const auto& d=item->delivery;
        return d && d->session==s.id() && d->account==item->before->lease.account &&
            d->character==item->before->lease.character && d->common_generation==item->before->lease.generation &&
            d->battle_generation==item->before->battle_generation && d->sequence==item->next->revision &&
            ready(s,*item->next);
    }
    bool definition_current(const NativeSkillRecord& expected) const {
        const auto actual=catalog.lookup_main_digest_checked(NativeSkillCatalog::current_dataset_id,expected.kind,expected.definition_id);
        return !poisoned && actual && *actual==expected;
    }
    bool model_current(Session& s,const Storage& saved) const {
        if(!ready(s,saved))return false;
        const auto source=catalog.lookup_main_source(NativeSkillCatalog::current_dataset_id);
        if(!source || *source!=saved.model.snapshot().catalog_source || !ready(s,saved))return false;
        for(const auto& bank:saved.model.snapshot().banks) {
            for(const auto& row:bank.definitions)
                if(!definition_current(row) || !ready(s,saved))return false;
            for(const auto& row:bank.auxiliary_definitions)
                if(row && (!definition_current(*row) || !ready(s,saved)))return false;
        }
        if(const auto& secondary=saved.model.snapshot().secondary) {
            for(const auto& bank:secondary->banks)
                for(const auto& row:bank.definitions)
                    if(row && (!definition_current(*row) || !ready(s,saved)))return false;
        }
        if(const auto& roster=saved.model.snapshot().roster_rows) {
            for(const auto& row:*roster) {
                for(const auto& definition:row.learned_definitions)
                    if(definition && (!definition_current(*definition) || !ready(s,saved)))return false;
                for(const auto& definition:row.auxiliary_definitions)
                    if(definition && (!definition_current(*definition) || !ready(s,saved)))return false;
            }
        }
        const auto after=catalog.lookup_main_source(NativeSkillCatalog::current_dataset_id);
        return after && *after==saved.model.snapshot().catalog_source && ready(s,saved);
    }
    std::uint64_t next_revision() const {
        if(revision==std::numeric_limits<std::uint64_t>::max())throw std::overflow_error("TW issued skill local revision exhausted");
        return revision+1;
    }
};
const SharedTaiwanIssuedSkillSource::Model& SharedTaiwanIssuedSkillSource::Ticket::model() const {return storage_->model;}
std::uint64_t SharedTaiwanIssuedSkillSource::Ticket::revision() const {return storage_->revision;}
std::shared_ptr<SharedTaiwanIssuedSkillSource> SharedTaiwanIssuedSkillSource::create(
    std::shared_ptr<SharedWorldPresence> presence,const NativeSkillCatalog& catalog,std::size_t capacity) {
    if(!presence || !capacity)throw std::invalid_argument("TW issued skill requires actual common presence/catalog/capacity");
    return std::shared_ptr<SharedTaiwanIssuedSkillSource>(new SharedTaiwanIssuedSkillSource(
        std::make_shared<State>(std::move(presence),catalog,capacity)));
}
bool SharedTaiwanIssuedSkillSource::owns_sources(const std::shared_ptr<SharedWorldPresence>& presence,const NativeSkillCatalog& catalog) const {
    const auto state=state_;state->owner();return presence && presence==state->presence &&
        !presence.owner_before(state->presence) && !state->presence.owner_before(presence) && &catalog==&state->catalog;
}
std::optional<SharedTaiwanIssuedSkillSource::Ticket> SharedTaiwanIssuedSkillSource::install_from_issued(Session& s,Model::Snapshot input) {
    const auto self=shared_from_this();const auto state=state_;State::Operation operation(*state);
    for(auto at=state->bindings.begin();at!=state->bindings.end();)
        if(at->second->session.expired())at=state->bindings.erase(at);else ++at;
    const auto actual=s.weak_from_this().lock();
    if(actual.get()!=&s || s.native_battle_skill_publication_pending() || state->pending.contains(s.id()) || state->bindings.contains(s.id()) ||
       state->bindings.size()>=state->capacity)return std::nullopt;
    auto model=Model::from_actual(std::move(input));if(!model)return std::nullopt;
    const auto generation=s.battle_generation();
    const auto lease=state->presence->ready_lease(s.id(),s.account_id,s.character_id);if(!lease)return std::nullopt;
    const auto position=state->presence->saved_position(*lease);if(!position)return std::nullopt;
    auto staged=std::make_shared<const Storage>(Storage{state,actual,*lease,*position,generation,state->next_revision(),std::move(*model)});
    if(!state->model_current(s,*staged))return std::nullopt;
    state->bindings.emplace(s.id(),staged);state->revision=staged->revision;
    return Ticket(std::move(staged));
}
std::optional<SharedTaiwanIssuedSkillSource::Ticket> SharedTaiwanIssuedSkillSource::replace_from_issued(
    Session& s,const Ticket& before,Model::Snapshot input) {
    const auto self=shared_from_this();const auto state=state_;State::Operation operation(*state);
    const auto saved=before.storage_;const auto actual=saved?saved->session.lock():nullptr;
    if(!saved || actual.get()!=&s || saved->origin.lock()!=state || !state->retained(s,saved))return std::nullopt;
    auto model=Model::from_actual(std::move(input));if(!model)return std::nullopt;
    auto staged=std::make_shared<const Storage>(Storage{state,actual,saved->lease,saved->position,saved->battle_generation,
        state->next_revision(),std::move(*model)});
    if(!state->model_current(s,*staged) || !state->retained(s,saved))return std::nullopt;
    state->bindings.at(s.id())=staged;state->revision=staged->revision;
    return Ticket(std::move(staged));
}
std::optional<SharedTaiwanIssuedSkillSource::Ticket> SharedTaiwanIssuedSkillSource::install_from_initialization_prefix(
    Session& s,Model::InitializationPrefix input) {
    const auto self=shared_from_this();const auto state=state_;state->owner();
    // Pure owned projection before entering the existing concrete game
    // installation operation. No observer/yield or synthetic before ticket.
    auto model=Model::from_initialization_prefix(std::move(input));
    if(!model)return std::nullopt;
    return install_from_issued(s,model->snapshot());
}
std::optional<SharedTaiwanIssuedSkillSource::Ticket> SharedTaiwanIssuedSkillSource::install_from_roster_rebuild_initialization_prefix(
    Session& s,Model::RosterInitializationPrefix input) {
    const auto self=shared_from_this();const auto state=state_;state->owner();
    // Pure full-row helper and prefix materialization before the existing
    // single guarded install. Its retained roster rows participate in full
    // catalog/ready checks for install, selection, replacement and publication.
    auto model=Model::from_roster_rebuild_initialization_prefix(std::move(input));
    if(!model)return std::nullopt;
    return install_from_issued(s,model->snapshot());
}
std::optional<SharedTaiwanIssuedSkillSource::Ticket> SharedTaiwanIssuedSkillSource::apply87_from_issued(
    Session& s,const Ticket& before,std::span<const std::uint8_t> logical) {
    // Own borrowed arguments before any repository observer. One public
    // replacement operation below owns the mutation guard and exact ticket CAS.
    const auto self=shared_from_this();const auto state=state_;state->owner();
    if(logical.size()!=3)return std::nullopt;
    const auto saved=before.storage_;const std::vector<std::uint8_t> bytes(logical.begin(),logical.end());
    if(bytes.size()!=3 || bytes[0]!=0x87 || !saved)return std::nullopt;
    const auto actual_session=saved->session.lock();
    if(actual_session.get()!=&s)return std::nullopt;
    const auto kind=std::uint8_t(bytes[2]&0x3f),id=bytes[1];if(kind>3 || !id)return std::nullopt;
    std::optional<NativeSkillRecord> definition;
    {
        State::Operation operation(*state);
        if(saved->origin.lock()!=state || !state->retained(s,saved))return std::nullopt;
        definition=state->catalog.lookup_main_digest_checked(NativeSkillCatalog::current_dataset_id,kind,id);
        if(!definition || !state->retained(s,saved))return std::nullopt;
    }
    const auto next=saved->model.apply87(bytes,*definition);if(!next)return std::nullopt;
    return replace_from_issued(s,Ticket(saved),next->snapshot());
}
std::optional<SharedTaiwanIssuedSkillSource::Ticket> SharedTaiwanIssuedSkillSource::apply38_from_issued(
    Session& s,const Ticket& before,std::span<const std::uint8_t> logical) {
    const auto self=shared_from_this();const auto state=state_;state->owner();
    if(logical.size()!=2)return std::nullopt;
    const auto saved=before.storage_;const std::vector<std::uint8_t> bytes(logical.begin(),logical.end());
    if(!saved)return std::nullopt;
    const auto actual_session=saved->session.lock();
    if(actual_session.get()!=&s)return std::nullopt;
    // Pure projection has no observer; replacement validates exact identity,
    // complete main/aux catalog and ready scope before any publication.
    const auto next=saved->model.apply38(bytes);if(!next)return std::nullopt;
    return replace_from_issued(s,Ticket(saved),next->snapshot());
}
std::optional<SharedTaiwanIssuedSkillSource::Ticket> SharedTaiwanIssuedSkillSource::apply86_control_from_issued(
    Session& s,const Ticket& before,std::span<const std::uint8_t> logical) {
    const auto self=shared_from_this();const auto state=state_;state->owner();
    if(logical.size()!=17)return std::nullopt;
    const auto saved=before.storage_;const std::vector<std::uint8_t> bytes(logical.begin(),logical.end());
    if(!saved)return std::nullopt;
    const auto actual_session=saved->session.lock();
    if(actual_session.get()!=&s)return std::nullopt;
    // No source observer during pure projection. The common replacement below
    // requalifies exact previous ticket, full main/aux definitions and ready
    // battle tuple before publishing this local observation revision.
    const auto next=saved->model.apply86_control(bytes);if(!next)return std::nullopt;
    return replace_from_issued(s,Ticket(saved),next->snapshot());
}
std::optional<SharedTaiwanIssuedSkillSource::Ticket> SharedTaiwanIssuedSkillSource::apply_enable_clear_from_issued(
    Session& s,const Ticket& before,Model::EnableClear target) {
    const auto self=shared_from_this();const auto state=state_;state->owner();
    const auto saved=before.storage_;
    if(!saved)return std::nullopt;
    const auto actual_session=saved->session.lock();
    if(actual_session.get()!=&s)return std::nullopt;
    // No observer or mutation during this exact local data projection. The
    // existing replacement owns origin/exact-ticket/pending CAS and re-reads
    // every current main/aux/secondary definition plus the actual ready tuple.
    const auto next=saved->model.clear_enable(target);if(!next)return std::nullopt;
    return replace_from_issued(s,Ticket(saved),next->snapshot());
}
std::optional<SharedTaiwanIssuedSkillSource::Publication> SharedTaiwanIssuedSkillSource::publish_updates(
    Session& s,const Ticket& before,std::span<const std::uint8_t> logical) {
    const auto self=shared_from_this();const auto state=state_;state->owner();
    if(logical.empty() || logical.size()>RecoveredWorldFrame::max_logical_size)return std::nullopt;
    const auto saved=before.storage_;const auto actual=saved?saved->session.lock():nullptr;
    if(actual.get()!=&s)return std::nullopt;
    const std::vector<std::uint8_t> bytes(logical.begin(),logical.end());
    std::shared_ptr<PublicationStorage> item;
    {
        State::Operation operation(*state);
        if(!saved || saved->origin.lock()!=state || !state->retained(s,saved) ||
           s.native_battle_skill_publication_pending() || !state->model_current(s,*saved))return std::nullopt;
        auto projected=std::optional<Model>{saved->model};
        std::span<const std::uint8_t> remaining=bytes;
        while(!remaining.empty()) {
            std::optional<Model> next;
            if(remaining[0]==0x87) {
                if(remaining.size()<3)return std::nullopt;
                const auto record=remaining.first(3);
                const auto kind=std::uint8_t(record[2]&0x3fu),id=record[1];
                if(kind>3 || !id)return std::nullopt;
                const auto definition=state->catalog.lookup_main_digest_checked(NativeSkillCatalog::current_dataset_id,kind,id);
                if(!definition || !state->retained(s,saved))return std::nullopt;
                next=projected->apply87(record,*definition);remaining=remaining.subspan(3);
            } else if(remaining[0]==0x38) {
                if(remaining.size()<2)return std::nullopt;
                next=projected->apply38(remaining.first(2));remaining=remaining.subspan(2);
            } else if(remaining[0]==0x86) {
                if(remaining.size()<17)return std::nullopt;
                // Only the documented direct control/actor subset, not the
                // full UI/rearm/clock consumer, server grant or turn policy.
                next=projected->apply86_control(remaining.first(17));remaining=remaining.subspan(17);
            } else return std::nullopt;
            if(!next)return std::nullopt;
            projected=std::move(next);
        }
        const auto revision=state->next_revision();
        auto staged=std::make_shared<const Storage>(Storage{state,actual,saved->lease,saved->position,
            saved->battle_generation,revision,std::move(*projected)});
        if(!state->model_current(s,*staged) || !state->model_current(s,*saved) ||
           !state->retained(s,saved))return std::nullopt;
        auto delivery=std::make_shared<const Session::NativeBattleSkillDelivery>(Session::NativeBattleSkillDelivery{
            s.id(),saved->lease.account,saved->lease.character,saved->lease.generation,saved->battle_generation,revision,bytes});
        item=std::make_shared<PublicationStorage>(PublicationStorage{state,actual,std::move(delivery),saved,staged});
        const auto inserted=state->pending.emplace(s.id(),item).second;
        if(!inserted)return std::nullopt;
        // Reserve the local sequence now. Other sessions may advance it while
        // this write is pending; completion must never move it backwards.
        state->revision=revision;
    }
    try {
        s.send_native_battle_skill_publication(item->delivery,
            std::weak_ptr<Session::NativeBattleSkillPublicationOwner>(self));
    }catch(...) {
        try{complete_native_battle_write(s,item->delivery,false);}catch(...){}
        s.close();
    }
    return Publication(std::move(item));
}
bool SharedTaiwanIssuedSkillSource::before_native_battle_write(Session& s,const Session::NativeBattleSkill& delivery) {
    const auto self=shared_from_this();const auto state=state_;State::Operation operation(*state);
    const auto at=state->pending.find(s.id());if(at==state->pending.end())return false;
    const auto item=at->second;const auto actual=item->session.lock();
    if(actual.get()!=&s || item->delivery!=delivery || item->before_write_accepted ||
       !state->pending_current(s,item) || !state->model_current(s,*item->before) ||
       !state->model_current(s,*item->next) || !state->pending_current(s,item))return false;
    item->before_write_accepted=true;
    return true;
}
bool SharedTaiwanIssuedSkillSource::complete_native_battle_write(
    Session& s,const Session::NativeBattleSkill& delivery,bool written) {
    const auto self=shared_from_this();const auto state=state_;State::Operation operation(*state);
    const auto at=state->pending.find(s.id());if(at==state->pending.end())return false;
    const auto item=at->second;const auto actual=item->session.lock();
    if(actual.get()!=&s || item->delivery!=delivery)return false;
    bool accepted=false;
    try {
        accepted=written && item->before_write_accepted && s.native_battle_skill_written()==delivery &&
            state->pending_current(s,item) && state->model_current(s,*item->before) &&
            state->model_current(s,*item->next) && state->pending_current(s,item);
    }catch(...) {accepted=false;}
    const auto bound=state->bindings.find(s.id());
    if(accepted && bound!=state->bindings.end() && bound->second==item->before) {
        bound->second=item->next;
        item->status=PublicationStatus::Written;
    }else{
        accepted=false;
        // Already sent bytes cannot be undone. Retire only the exact old slot;
        // never restore presumed-client state or erase a newer incarnation.
        if(bound!=state->bindings.end() && bound->second==item->before)state->bindings.erase(bound);
        item->status=PublicationStatus::Failed;item->next.reset();
    }
    item->before.reset();state->pending.erase(at);
    if(!accepted)s.close();
    return accepted;
}
std::optional<SharedTaiwanIssuedSkillSource::PublicationObservation> SharedTaiwanIssuedSkillSource::observe_publication(
    Session& s,const Publication& publication) {
    const auto self=shared_from_this();const auto state=state_;State::Operation operation(*state);
    const auto item=publication.storage_;const auto actual=item?item->session.lock():nullptr;
    if(!item || actual.get()!=&s || item->origin.lock()!=state)return std::nullopt;
    PublicationObservation result{item->status,std::nullopt};
    // No user completion runs while Session's old publication slot is still
    // occupied. A subsequent issuer gets its ticket only after that barrier.
    if(item->status==PublicationStatus::Written && !s.native_battle_skill_publication_pending() &&
       state->retained(s,item->next) && state->model_current(s,*item->next) &&
       !s.native_battle_skill_publication_pending() && state->retained(s,item->next))
        result.current_ticket=Ticket(item->next);
    return result;
}
std::optional<SharedTaiwanIssuedSkillSource::Selection> SharedTaiwanIssuedSkillSource::select(Session& s,std::uint32_t operand) {
    const auto self=shared_from_this();const auto state=state_;State::Operation operation(*state);
    const auto at=state->bindings.find(s.id());if(at==state->bindings.end())return std::nullopt;
    const auto saved=at->second;const auto actual=saved->session.lock();
    if(actual.get()!=&s || !state->retained(s,saved) || !state->model_current(s,*saved) ||
       !state->retained(s,saved))return std::nullopt;
    const auto selected=saved->model.issued_lookup(operand);
    if(!selected || !state->model_current(s,*saved) || !state->retained(s,saved))return std::nullopt;
    return Selection(Ticket(saved),*selected);
}
bool SharedTaiwanIssuedSkillSource::current(Session& s,const Selection& selection) {
    const auto self=shared_from_this();const auto state=state_;State::Operation operation(*state);
    const auto owned=selection;const auto saved=owned.ticket_.storage_;const auto actual=saved?saved->session.lock():nullptr;
    if(!saved || actual.get()!=&s || saved->origin.lock()!=state || !state->retained(s,saved) ||
       !state->model_current(s,*saved) || !state->retained(s,saved))return false;
    const auto key=std::uint32_t(owned.lookup_.definition.definition_id)|(std::uint32_t(owned.lookup_.definition.kind)<<8);
    const auto selected=saved->model.issued_lookup(key);
    return selected && *selected==owned.lookup_ && state->model_current(s,*saved) && state->retained(s,saved);
}
void SharedTaiwanIssuedSkillSource::release(Session& s) {
    const auto self=shared_from_this();const auto state=state_;State::Operation operation(*state);
    const auto actual=s.weak_from_this().lock();if(actual.get()!=&s)return;
    if(s.native_battle_skill_publication_pending())s.close();
    const auto waiting=state->pending.find(s.id());
    if(waiting!=state->pending.end() && waiting->second->session.lock().get()==&s) {
        waiting->second->status=PublicationStatus::Failed;
        waiting->second->before.reset();waiting->second->next.reset();
        state->pending.erase(waiting);s.close();
    }
    const auto at=state->bindings.find(s.id());
    if(at!=state->bindings.end() && at->second->session.lock().get()==&s)state->bindings.erase(at);
}
void SharedTaiwanIssuedSkillSource::invalidate_active() {
    const auto state=state_;state->owner();if(state->operating)state->poisoned=true;
}
}
