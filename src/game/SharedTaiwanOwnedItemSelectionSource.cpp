#include "game/SharedTaiwanOwnedItemSelectionSource.h"
#include <stdexcept>
#include <utility>

namespace god2 {
SharedTaiwanOwnedItemSelectionSource::SharedTaiwanOwnedItemSelectionSource(SqliteOwnedInventoryRepository& r,
    AccountRepository& a,RecoveredCharacterRepository& c,std::shared_ptr<SharedWorldPresence> p,bool definitions,bool deity_equipment)
    :repository_(r),accounts_(a),characters_(c),presence_(std::move(p)),definitions_(definitions),deity_equipment_(deity_equipment) {}
void SharedTaiwanOwnedItemSelectionSource::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("TW owned item selection game owner mismatch");
}
std::shared_ptr<SharedTaiwanOwnedItemSelectionSource> SharedTaiwanOwnedItemSelectionSource::create(
    SqliteOwnedInventoryRepository& r,AccountRepository& a,RecoveredCharacterRepository& c,std::shared_ptr<SharedWorldPresence> p) {
    if(!p||!p->owns_repository(c)||!r.owns_sources(a,c))throw std::invalid_argument("TW owned selection requires actual common sources");
    return std::shared_ptr<SharedTaiwanOwnedItemSelectionSource>(new SharedTaiwanOwnedItemSelectionSource(r,a,c,std::move(p),false));
}
std::shared_ptr<SharedTaiwanOwnedItemSelectionSource> SharedTaiwanOwnedItemSelectionSource::create_with_definitions(
    SqliteOwnedInventoryRepository& r,AccountRepository& a,RecoveredCharacterRepository& c,std::shared_ptr<SharedWorldPresence> p) {
    if(!p||!p->owns_repository(c)||!r.owns_sources(a,c))throw std::invalid_argument("TW defined owned selection requires actual common sources");
    return std::shared_ptr<SharedTaiwanOwnedItemSelectionSource>(new SharedTaiwanOwnedItemSelectionSource(r,a,c,std::move(p),true));
}
std::shared_ptr<SharedTaiwanOwnedItemSelectionSource> SharedTaiwanOwnedItemSelectionSource::create_with_deity_equipment(
    SqliteOwnedInventoryRepository& r,AccountRepository& a,RecoveredCharacterRepository& c,std::shared_ptr<SharedWorldPresence> p) {
    if(!p||!p->owns_repository(c)||!r.owns_sources(a,c))throw std::invalid_argument("TW deity owned selection requires actual common sources");
    return std::shared_ptr<SharedTaiwanOwnedItemSelectionSource>(new SharedTaiwanOwnedItemSelectionSource(r,a,c,std::move(p),true,true));
}
bool SharedTaiwanOwnedItemSelectionSource::ready(Session& s,const SharedWorldPresence::Lease& lease,
    const RecoveredPosition& position,std::uint64_t battle) const {
    const auto local=[&] {return presence_->retained_ready_current(lease) && !(reentered_||s.closing()||s.state()!=SessionState::InWorld||!s.recovered_world_ready()||
       s.id()!=lease.session||s.account_id!=lease.account||s.character_id!=lease.character||s.battle_generation()!=battle||
       !s.common_world_delivery_current(lease.account,lease.character,lease.generation)||
       s.common_world_entry_current(lease.account,lease.character,lease.generation)||
       !repository_.owns_sources(accounts_,characters_)||!presence_->owns_repository(characters_));};
    if(!local())return false;
    const auto actual=presence_->ready_lease(lease.session,lease.account,lease.character);
    const auto saved=presence_->saved_position(lease);
    return actual&&*actual==lease&&saved&&*saved==position&&local();
}
std::optional<SharedTaiwanOwnedItemSelectionSource::Selection> SharedTaiwanOwnedItemSelectionSource::select(
    Session& session,RecoveredSelectionItemRequest::Request request) {
    owner();const auto self=shared_from_this();
    if(reading_){reentered_=true;return std::nullopt;}
    reading_=true;reentered_=false;struct Leave {bool& value;~Leave(){value=false;}} leave{reading_};
    if(!request.client_item_id||request.raw_slot>=50)return std::nullopt;
    const auto weak=session.weak_from_this();if(weak.lock().get()!=&session)return std::nullopt;
    const auto lease=presence_->ready_lease(session.id(),session.account_id,session.character_id);if(!lease)return std::nullopt;
    const auto position=presence_->saved_position(*lease);const auto battle=session.battle_generation();
    if(!position||!ready(session,*lease,*position,battle))return std::nullopt;
    auto committed=repository_.observe_committed(lease->account,lease->character);
    if(!committed||reentered_||!ready(session,*lease,*position,battle))return std::nullopt;
    const auto& snapshot=committed->snapshot();std::optional<std::pair<std::size_t,std::size_t>> found;
    for(std::size_t c=0;c<snapshot.cells.size();++c)if(snapshot.cells[c].instance) {
        const auto& item=*snapshot.cells[c].instance;
        for(std::size_t a=0;a<item.aliases.size();++a) {
            const auto& alias=item.aliases[a];
            if(alias.client_sha256!=client_pin||alias.profile!=alias_profile||alias.native_slot!=request.raw_slot)continue;
            // Same149c full20 is preserved exactly. Its first WORD is the
            // client key only; no common ID/definition/quantity is decoded.
            if(found||alias.record.size()!=20||alias.native_key!=request.client_item_id||alias.revision!=item.revision||
               (static_cast<unsigned>(alias.record[0])|static_cast<unsigned>(alias.record[1])<<8)!=request.client_item_id)
                return std::nullopt;
            found=std::pair{c,a};
        }
    }
    if(!found||!repository_.committed_current(*committed)||!ready(session,*lease,*position,battle))return std::nullopt;
    std::optional<NativeItemDefinitionObservation> definition;
    if(definitions_) {
        definition=repository_.observe_native_definition(request.client_item_id);
        if(!definition||!repository_.committed_current(*committed)||!ready(session,*lease,*position,battle))return std::nullopt;
    }
    std::optional<NativeDeityEquipmentObservation> deity_equipment;
    if(deity_equipment_) {
        deity_equipment=repository_.observe_native_deity_equipment(lease->account,lease->character);
        if(!deity_equipment || !OwnedInventorySnapshot::same_root(deity_equipment->snapshot().root,snapshot.root) ||
           deity_equipment->snapshot().position!=*position || !repository_.committed_current(*committed) ||
           !ready(session,*lease,*position,battle))return std::nullopt;
    }
    return Selection(std::move(*committed),found->first,found->second,weak,*lease,*position,battle,request,
        std::move(definition),std::move(deity_equipment));
}
bool SharedTaiwanOwnedItemSelectionSource::current(Session& session,const Selection& selection) {
    owner();const auto self=shared_from_this();if(reading_){reentered_=true;return false;}
    reading_=true;reentered_=false;struct Leave {bool& value;~Leave(){value=false;}} leave{reading_};
    if(selection.session_.lock().get()!=&session||definitions_!=bool(selection.definition_)||
       deity_equipment_!=bool(selection.deity_equipment_)||
       !ready(session,selection.lease_,selection.position_,selection.battle_generation_))return false;
    if(definitions_) {
        if(!repository_.committed_current(selection.committed_)||
           repository_.observe_native_definition(selection.alias().native_key)!=selection.definition_)return false;
    }
    if(deity_equipment_ && repository_.observe_native_deity_equipment(selection.lease_.account,selection.lease_.character)
       !=selection.deity_equipment_)return false;
    return repository_.committed_current(selection.committed_)&&
        ready(session,selection.lease_,selection.position_,selection.battle_generation_);
}
bool SharedTaiwanOwnedItemSelectionSource::ready_current(Session& session,const Selection& selection) {
    owner();const auto self=shared_from_this();if(reading_){reentered_=true;return false;}
    reading_=true;reentered_=false;struct Leave {bool& value;~Leave(){value=false;}} leave{reading_};
    return selection.session_.lock().get()==&session&&
        ready(session,selection.lease_,selection.position_,selection.battle_generation_);
}
}
