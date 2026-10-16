#pragma once
#include "game/SharedTaiwanNativeMovementScene.h"
#include <chrono>

namespace god2 {
// CUSTOM-0150 explicit owned ordinary movement policy. Native geometry is
// retained, but rate/sequence/admission/5D echo are custom server choices.
// No policy defaults, original-server claim, ring emulation, reset fallback,
// second position writer or socket publication is provided by this leaf.
class OwnedTaiwanOrdinaryMovementAuthority final:
    public SharedTaiwanNativeMovementScene::Authority,
    public std::enable_shared_from_this<OwnedTaiwanOrdinaryMovementAuthority> {
public:
    using Scene=SharedTaiwanNativeMovementScene;
    using Lease=SharedWorldPresence::Lease;
    static std::shared_ptr<OwnedTaiwanOrdinaryMovementAuthority> adopt(
        const std::shared_ptr<Session>&,std::shared_ptr<SharedWorldPresence>,
        const Lease&,const Scene::Resources&,RecoveredPosition,std::uint8_t,
        std::shared_ptr<TaiwanMovementRules>,TaiwanMovementRules::OrdinaryPolicy);
    ~OwnedTaiwanOrdinaryMovementAuthority() override;
    std::optional<Scene::Permit> authorize(const Scene::Candidate&) override;
    // Pure game-affine revocation, including during a caught nested observer.
    // Dependencies stay retained until normal destruction; there is no reset.
    void retire();
    // Pure last-observer phase/weak Session/exact ready registry fence.
    bool retained_current() const;
private:
    struct Operation;
    struct Ticket;
    using Clock=std::chrono::steady_clock;
    OwnedTaiwanOrdinaryMovementAuthority(const std::shared_ptr<Session>&,
        std::shared_ptr<SharedWorldPresence>,const Lease&,Scene::Resources,
        RecoveredPosition,std::uint8_t,std::shared_ptr<TaiwanMovementRules>,
        TaiwanMovementRules::OrdinaryPolicy);
    void owner() const;
    bool bound() const;
    bool candidate_current(const Scene::Candidate&) const;
    bool retained(const std::shared_ptr<const Ticket>&) const;
    bool population_current(const std::shared_ptr<const Ticket>&,bool require_after,bool require_before=false);
    bool current(const std::shared_ptr<const Ticket>&,const Scene::Candidate&);
    bool publish(const std::shared_ptr<const Ticket>&,const SharedTaiwanMovement::Committed&);
    static bool same_step(const TaiwanMovementRules::Step&,const TaiwanMovementRules::Step&);
    static bool same_candidate(const Scene::Candidate&,const Scene::Candidate&);
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Session> connection_;
    const std::shared_ptr<SharedWorldPresence> presence_;
    const Lease lease_;
    const Scene::Resources resources_;
    const std::shared_ptr<TaiwanMovementRules> rules_;
    const TaiwanMovementRules::OrdinaryPolicy policy_;
    const std::uint64_t battle_generation_;
    RecoveredPosition position_;
    std::uint8_t direction_,expected_sequence_;
    std::uint64_t publication_revision_,credit_us_;
    Clock::time_point clock_;
    std::shared_ptr<const Ticket> pending_;
    bool busy_=false,failed_=false;
};
}
