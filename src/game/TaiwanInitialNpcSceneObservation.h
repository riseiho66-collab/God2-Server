#pragma once
#include "db/SqliteWorldDisplayRepository.h"
#include "game/SharedWorldPresence.h"
#include <atomic>
#include <memory>
#include <thread>
#include <utility>

namespace god2 {
class OwnedTaiwanInitialNpcDisplaySource;
class OwnedTaiwanReturnActorSavedSource;
// CUSTOM-0133 actual initial source composition; no NPC gameplay formula.
// Private actual initial NPC observation. No owning Scope, Session, Profile,
// callback, Saved source or NPC source is retained. SQL is reachable only from
// the actual Saved friend inside its already owned same-connection read scope.
class TaiwanInitialNpcSceneObservation final {
    friend class OwnedTaiwanInitialNpcDisplaySource;
    friend class OwnedTaiwanReturnActorSavedSource;
public:
    bool retained() const noexcept {
        return thread_==std::this_thread::get_id()&&owner_live_&&scene_live_&&
            owner_live_->load()&&scene_live_->load()&&!actor_input_.expired()&&
            !saved_source_.expired()&&!npc_owner_.expired();
    }
    bool matches_scope(const SharedWorldPresence::Lease& lease,
            const SharedWorldPresence::InitialPopulation& population,
            const std::shared_ptr<const void>& actor_input) const noexcept {
        return retained()&&lease_==lease&&population_==population&&
            population.joining().lease==lease&&readset_.area()==lease.position.area&&
            readset_.scene()==lease.position.scene&&!readset_.isolated_test()&&
            actor_input&&actor_input.get()==actor_input_address_&&
            !actor_input_.owner_before(actor_input)&&!actor_input.owner_before(actor_input_);
    }
private:
    TaiwanInitialNpcSceneObservation(SqliteWorldDisplayRepository::SceneReadset readset,
            SqliteWorldDisplayRepository& repository,const NativeNpcDisplayCatalog& npcs,
            const NativeEnemyDisplayCatalog& enemies,SharedWorldPresence::Lease lease,
            SharedWorldPresence::InitialPopulation population,
            const std::shared_ptr<const void>& actor_input,
            const std::shared_ptr<OwnedTaiwanReturnActorSavedSource>& saved_source,
            const std::shared_ptr<const void>& npc_owner,
            std::shared_ptr<std::atomic<bool>> owner_live,std::shared_ptr<std::atomic<bool>> scene_live)
        :readset_(std::move(readset)),repository_(repository),npcs_(npcs),enemies_(enemies),
         lease_(std::move(lease)),population_(std::move(population)),actor_input_(actor_input),
         actor_input_address_(actor_input.get()),saved_source_(saved_source),
         saved_source_address_(saved_source.get()),npc_owner_(npc_owner),
         owner_live_(std::move(owner_live)),scene_live_(std::move(scene_live)){}
    bool matches_source(const OwnedTaiwanReturnActorSavedSource* source,
            const SharedWorldPresence::InitialPopulation& population) const noexcept {
        return retained()&&source&&source==saved_source_address_&&population_==population&&
            population.joining().lease==lease_&&readset_.area()==lease_.position.area&&
            readset_.scene()==lease_.position.scene&&!readset_.isolated_test();
    }
    bool stored_current_in_scope(sqlite3* connection) const noexcept {
        return retained()&&repository_.current_scene_in_scope(connection,readset_,npcs_,enemies_)&&retained();
    }
    const SqliteWorldDisplayRepository::SceneReadset readset_;
    SqliteWorldDisplayRepository& repository_;
    const NativeNpcDisplayCatalog& npcs_;
    const NativeEnemyDisplayCatalog& enemies_;
    const SharedWorldPresence::Lease lease_;
    const SharedWorldPresence::InitialPopulation population_;
    const std::weak_ptr<const void> actor_input_;
    const void* const actor_input_address_;
    const std::weak_ptr<OwnedTaiwanReturnActorSavedSource> saved_source_;
    const OwnedTaiwanReturnActorSavedSource* const saved_source_address_;
    const std::weak_ptr<const void> npc_owner_;
    const std::shared_ptr<std::atomic<bool>> owner_live_,scene_live_;
    const std::thread::id thread_=std::this_thread::get_id();
};
}
