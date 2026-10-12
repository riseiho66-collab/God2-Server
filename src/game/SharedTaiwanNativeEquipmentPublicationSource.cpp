#include "game/SharedTaiwanNativeEquipmentPublicationSource.h"
#include <stdexcept>
#include <utility>

namespace god2 {
SharedTaiwanNativeEquipmentPublicationSource::SharedTaiwanNativeEquipmentPublicationSource(
    SqliteNativeEquipmentSnapshotRepository& repository,AccountRepository& accounts,
    RecoveredCharacterRepository& characters,std::shared_ptr<SharedWorldPresence> presence,
    std::shared_ptr<cn::SharedActorVisibility> visibility,SqliteNativeEquipmentSnapshotRepository::Committed committed)
    :repository_(repository),accounts_(accounts),characters_(characters),presence_(std::move(presence)),
     visibility_(std::move(visibility)),committed_(std::move(committed)) {}
void SharedTaiwanNativeEquipmentPublicationSource::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("TW equipment publication game owner mismatch");
}
std::shared_ptr<SharedTaiwanNativeEquipmentPublicationSource> SharedTaiwanNativeEquipmentPublicationSource::create(
    SqliteNativeEquipmentSnapshotRepository& repository,AccountRepository& accounts,
    RecoveredCharacterRepository& characters,std::shared_ptr<SharedWorldPresence> presence,
    std::shared_ptr<cn::SharedActorVisibility> visibility,SqliteNativeEquipmentSnapshotRepository::Committed committed) {
    if(!presence || !visibility || !presence->owns_repository(characters) || !visibility->owns_presence(presence) ||
       !repository.owns_sources(accounts,characters) || !repository.committed_current(committed))
        throw std::invalid_argument("TW equipment requires exact common sources and this writer's durable token");
    return std::shared_ptr<SharedTaiwanNativeEquipmentPublicationSource>(new SharedTaiwanNativeEquipmentPublicationSource(
        repository,accounts,characters,std::move(presence),std::move(visibility),std::move(committed)));
}
std::shared_ptr<SharedTaiwanNativeEquipmentPublicationSource> SharedTaiwanNativeEquipmentPublicationSource::create(
    std::shared_ptr<SqliteOwnedEquipmentTransaction> repository,AccountRepository& accounts,
    RecoveredCharacterRepository& characters,std::shared_ptr<SharedWorldPresence> presence,
    std::shared_ptr<cn::SharedActorVisibility> visibility,SqliteOwnedEquipmentTransaction::Committed committed) {
    if(!repository||!repository->owns_sources(accounts,characters)||!repository->committed_current(committed))
        throw std::invalid_argument("TW joint equipment requires both current committed populations");
    auto source=create(repository->equipment_writer(),accounts,characters,std::move(presence),std::move(visibility),committed.equipment());
    source->joint_repository_=std::move(repository);source->joint_committed_=std::move(committed);
    if(!source->joint_repository_->committed_current(*source->joint_committed_))
        throw std::invalid_argument("TW joint equipment source changed during construction");
    return source;
}
// Keep the complete entry receipt: extracting its material token here would
// silently downgrade every later queue check to a two-population observation.
std::shared_ptr<SharedTaiwanNativeEquipmentPublicationSource> SharedTaiwanNativeEquipmentPublicationSource::create(
    std::shared_ptr<SqliteOwnedEquipmentTransaction> repository,AccountRepository& accounts,
    RecoveredCharacterRepository& characters,std::shared_ptr<SharedWorldPresence> presence,
    std::shared_ptr<cn::SharedActorVisibility> visibility,SqliteOwnedEquipmentTransaction::EntryCommitted committed) {
    if(!repository||!repository->owns_sources(accounts,characters)||!repository->committed_current(committed))
        throw std::invalid_argument("TW entry/equipment requires all three current committed populations");
    auto source=create(repository->equipment_writer(),accounts,characters,std::move(presence),std::move(visibility),
        committed.material().equipment());
    source->joint_repository_=std::move(repository);source->joint_entry_committed_=std::move(committed);
    if(!source->joint_repository_->committed_current(*source->joint_entry_committed_))
        throw std::invalid_argument("TW entry/equipment source changed during construction");
    return source;
}
std::optional<cn::SharedActorVisibility::TaiwanAppearanceAfterState>
SharedTaiwanNativeEquipmentPublicationSource::current(const SharedWorldPresence::Lease& original) {
    owner();if(reading_){reentered_=true;return std::nullopt;}
    reading_=true;reentered_=false;
    struct End {bool& busy;~End(){busy=false;}} end{reading_};
    const auto lease=original;const auto& snapshot=committed_.snapshot();
    const auto qualify=[&] {
        if(reentered_ || !repository_.owns_sources(accounts_,characters_) ||
           !presence_->owns_repository(characters_) || !visibility_->owns_presence(presence_) ||
           lease.account!=snapshot.root.account_id || lease.character!=snapshot.root.id ||
           lease.actor_handle!=snapshot.actor_handle)return false;
        const auto actual=presence_->ready_lease(lease.session,lease.account,lease.character);
        if(reentered_ || !actual || *actual!=lease)return false;
        const auto position=presence_->saved_position(lease);
        return !reentered_ && position && *position==snapshot.position;
    };
    const auto durable_current=[&] {
        if(joint_repository_) {
            if(!joint_repository_->owns_sources(accounts_,characters_))return false;
            if(joint_entry_committed_)return !joint_committed_ &&
                joint_repository_->committed_current(*joint_entry_committed_);
            return joint_committed_ && joint_repository_->committed_current(*joint_committed_);
        }
        return !joint_committed_ && !joint_entry_committed_ && repository_.committed_current(committed_);
    };
    if(!qualify() || !durable_current() || !qualify())return std::nullopt;
    const auto update=snapshot.appearance();if(!update || update->actor_identity()!=lease.actor_handle)return std::nullopt;
    return cn::SharedActorVisibility::TaiwanAppearanceAfterState{snapshot.revision,snapshot.source_record,*update};
}
void SharedTaiwanNativeEquipmentPublicationSource::publish(const cn::SharedActorVisibility::Binding& original,
    cn::SharedActorVisibility::TaiwanAppearanceCompletion done) {
    owner();if(!done)throw std::invalid_argument("TW equipment publication completion required");
    const auto self=shared_from_this();const auto binding=original;const auto lease=binding.source();
    if(reading_){reentered_=true;try {done(false);}catch(...) {}return;}
    const auto supplier=[self,lease](cn::SharedActorVisibility::TaiwanAppearanceCheck) {return self->current(lease);};
    // No data or issuer is re-created here. The existing endpoint requalifies
    // this exact committed fulltuple at Prepare/Before/After/queue completion.
    visibility_->publish_taiwan_appearance(binding,committed_.snapshot().position,supplier,std::move(done));
}
}
