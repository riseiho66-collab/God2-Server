#include "game/SharedTaiwanOwnedDeitySkillSource.h"
#include "protocol/TaiwanNativeSkillCommand.h"
#include <exception>
#include <stdexcept>
#include <thread>

namespace god2 {
struct SharedTaiwanOwnedDeitySkillSource::Impl {
    const std::thread::id thread=std::this_thread::get_id();
    const std::shared_ptr<SharedWorldPresence> presence;
    SqliteCompanionRepository& companions;
    const NativeSkillCatalog& catalog;
    bool reading=false,reentered=false;
    Impl(std::shared_ptr<SharedWorldPresence> p,SqliteCompanionRepository& c,const NativeSkillCatalog& n)
        :presence(std::move(p)),companions(c),catalog(n) {}
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
    bool local(Session& s,const Scope& scope) const {
        const auto& lease=scope.lease;
        return !reentered && !s.closing() && s.id()==lease.session &&
            s.account_id==lease.account && s.character_id==lease.character &&
            s.state()==scope.phase && (scope.phase==SessionState::InWorld || scope.phase==SessionState::InBattle) &&
            s.battle_generation()==scope.battle_generation && s.recovered_world_ready() &&
            s.common_world_delivery_current(lease.account,lease.character,lease.generation) &&
            !s.common_world_entry_current(lease.account,lease.character,lease.generation);
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
    static bool qualified(const NativeSkillRecord& r,std::uint8_t kind,std::uint8_t id) {
        // Main catalog lookup checks metadata, raw row shape/key and all110
        // bytes against the stored digest. Here pin
        // native image, raw key and original110-byte row geometry explicitly.
        return r.kind==kind && r.definition_id==id && r.raw_record.size()==110 &&
            r.raw_record[0]==id && r.raw_record[1]==kind &&
            r.source.native_image_sha256==TaiwanNativeSkillCommand::image_sha256 &&
            r.source_offset==8+r.kind*0x6e04+(r.definition_id-1)*110;
    }
    bool definition_current(const NativeSkillRecord& expected) const {
        const auto actual=catalog.lookup_main_digest_checked(NativeSkillCatalog::current_dataset_id,expected.kind,expected.definition_id);
        return !reentered && actual && *actual==expected;
    }
};
std::shared_ptr<SharedTaiwanOwnedDeitySkillSource> SharedTaiwanOwnedDeitySkillSource::create(
    std::shared_ptr<SharedWorldPresence> presence,SqliteCompanionRepository& companions,const NativeSkillCatalog& catalog) {
    if(!presence)throw std::invalid_argument("TW saved skill requires real common presence");
    return std::shared_ptr<SharedTaiwanOwnedDeitySkillSource>(new SharedTaiwanOwnedDeitySkillSource(
        std::make_shared<Impl>(std::move(presence),companions,catalog)));
}
std::optional<SharedTaiwanOwnedDeitySkillSource::Observation> SharedTaiwanOwnedDeitySkillSource::observe(
    Session& session,std::uint8_t kind,std::uint8_t id) {
    const auto self=shared_from_this();const auto state=state_;Impl::Read read(*state);
    if(kind>3 || !id)return std::nullopt;
    const auto weak=session.weak_from_this();const auto actual_session=weak.lock();
    if(actual_session.get()!=&session)return std::nullopt;
    const auto scope=state->capture(session);if(!scope)return std::nullopt;
    auto definition=state->catalog.lookup_main_digest_checked(NativeSkillCatalog::current_dataset_id,kind,id);
    if(!definition || !Impl::qualified(*definition,kind,id) || !state->ready(session,*scope))return std::nullopt;
    auto saved=state->companions.load_selected_deity_skill(scope->lease.account,scope->lease.character,kind,id);
    if(!saved || !state->ready(session,*scope) || !state->definition_current(*definition) ||
       !state->companions.selected_deity_skill_current(*saved) || !state->ready(session,*scope))return std::nullopt;
    return Observation(state,weak,std::move(*saved),std::move(*definition),*scope);
}
bool SharedTaiwanOwnedDeitySkillSource::current(Session& session,const Observation& observation) {
    const auto self=shared_from_this();const auto state=state_;Impl::Read read(*state);
    // Own the argument before observers; they may release its caller holder.
    const auto owned=observation;
    const auto actual_session=owned.session_.lock();
    if(owned.origin_.lock()!=state || actual_session.get()!=&session ||
       !state->ready(session,owned.scope_) || !state->definition_current(owned.definition_) ||
       !state->companions.selected_deity_skill_current(owned.saved_))return false;
    return state->ready(session,owned.scope_);
}
}
