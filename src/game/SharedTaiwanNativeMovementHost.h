#pragma once
#include "game/TaiwanNativeSceneResourceOwner.h"

namespace god2 {
// Actual common-host TW native resource/controller composition, game-affine.
// Native Current/resources remain actual issuer inputs. Explicit CUSTOM-0150
// may select the concrete owned ordinary authority via LAST Input metadata;
// supplied native Authority is preserved and never replaced implicitly.
class SharedTaiwanNativeMovementHost final:public std::enable_shared_from_this<SharedTaiwanNativeMovementHost> {
public:
    using Lease=SharedWorldPresence::Lease;
    using Input=TaiwanNativeSceneResourceOwner::Input;
    using InputSource=std::function<std::optional<Input>(Session&,
        const SharedTaiwanNativeMovementScene::FactoryScope&)>;
    static std::shared_ptr<SharedTaiwanNativeMovementHost> create(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<shared::SharedActorVisibility>,
        std::shared_ptr<TaiwanMovementRules>,std::size_t actual_session_capacity);
    // Actual input provider is invoked only for the first real movement
    // factory after completed common initial publication. No fallback supplier.
    static std::shared_ptr<SharedTaiwanNativeMovementHost> create(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<shared::SharedActorVisibility>,
        std::shared_ptr<TaiwanMovementRules>,InputSource,std::size_t actual_session_capacity,
        std::shared_ptr<SqliteOwnedEquipmentTransaction> movement_custody={});
    ~SharedTaiwanNativeMovementHost();
    SharedTaiwanNativeMovementHost(const SharedTaiwanNativeMovementHost&)=delete;
    SharedTaiwanNativeMovementHost& operator=(const SharedTaiwanNativeMovementHost&)=delete;
    bool install(const std::shared_ptr<Session>&,const Lease&,const Input&);
    // Retire exact old controller before replacing resource lineage. Failure
    // never resurrects old resources or rewinds a committed common prefix.
    bool replace(const std::shared_ptr<Session>&,const Lease&,const Input&);
    bool remove(Session&,const Lease&);
    // Strong actual host ownership in all four returned callbacks, including
    // exact-generation retire. Cleanup occurs before common lifecycle/DB drain.
    SharedTaiwanMovementSource::Binding binding();
    // Propagates a caught nested hosting rejection into both actual owners.
    void invalidate_active();
private:
    struct State;
    explicit SharedTaiwanNativeMovementHost(std::shared_ptr<State>);
    std::shared_ptr<State> state_;
};
}
