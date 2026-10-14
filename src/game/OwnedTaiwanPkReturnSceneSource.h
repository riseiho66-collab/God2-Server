#pragma once
#include "game/TaiwanCustomFullActorProfile.h"
#include "game/SharedNativeWorldTransports.h"
#include "handlers/OwnedPkOutboxPublication.h"
#include <functional>
#include <memory>
#include <optional>
#include <thread>

namespace god2 {
// CUSTOM-0133 full, freshly authored ordinary TW actors from the backend's
// private population input. This supplies the existing return recipe; it does
// not publish, consume, resume, send, or select a default Application plan.
class OwnedTaiwanPkReturnSceneSource final {
    struct State;
    struct Endpoint;
public:
    using ProfileOwner=TaiwanCustomFullActorProfile;
    using Input=OwnedTaiwanReturnActorSavedSource::PopulationInput;
    using Equipment=OwnedTaiwanReturnActorSavedSource::ProfileEquipment;
    using Request=OwnedPkOutboxPublication::ReturnSceneRequest;
    using Scene=cn::SharedActorVisibility::TaiwanReturnScene;
    using Check=cn::SharedActorVisibility::TaiwanReturnCheck;
    using Lease=SharedWorldPresence::Lease;
    enum class Selection {CustomSameAreaSceneV1}; // CUSTOM-0027; not native audience evidence.
    struct MaterialSources {
        // Real resource/status owners are mandatory. A pinned bank alone is
        // not a live resource epoch; missing EA is not confirmed absence.
        std::shared_ptr<const void> dependency_owner;
        std::function<std::optional<ProfileOwner::ResourceInput>(
            std::shared_ptr<const Input>,std::size_t,const Equipment&,const Lease&)> resources;
        std::function<std::optional<ProfileOwner::StatusInput>(
            std::shared_ptr<const Input>,std::size_t,const Equipment&,const Lease&)> status;
    };
    static std::shared_ptr<OwnedTaiwanPkReturnSceneSource> create(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<SharedNativeWorldTransports>,
        std::shared_ptr<cn::SharedActorVisibility>,std::shared_ptr<ProfileOwner>,
        Selection,MaterialSources);
    OwnedPkOutboxPublication::ReturnSceneSource return_source();
    OwnedTaiwanPkReturnSceneSource(const OwnedTaiwanPkReturnSceneSource&)=delete;
    OwnedTaiwanPkReturnSceneSource& operator=(const OwnedTaiwanPkReturnSceneSource&)=delete;
private:
    OwnedTaiwanPkReturnSceneSource(std::shared_ptr<SharedWorldPresence>,
        std::shared_ptr<SharedNativeWorldTransports>,std::shared_ptr<cn::SharedActorVisibility>,
        std::shared_ptr<ProfileOwner>,Selection,MaterialSources);
    std::optional<Scene> observe(const Request&);
    bool current(const std::shared_ptr<State>&,Check);
    bool qualified(const std::shared_ptr<State>&,const ProfileOwner::Profile&);
    bool fence(const State&,Check) const;
    const std::shared_ptr<SharedWorldPresence> presence_;
    const std::shared_ptr<SharedNativeWorldTransports> transports_;
    const std::shared_ptr<cn::SharedActorVisibility> visibility_;
    const std::shared_ptr<ProfileOwner> profiles_;
    const Selection selection_;
    const MaterialSources material_;
    const std::thread::id thread_=std::this_thread::get_id();
    bool busy_=false,poisoned_=false;
    std::weak_ptr<OwnedTaiwanPkReturnSceneSource> self_;
};
}
