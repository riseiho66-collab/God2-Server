#pragma once
#include "db/SqliteCompanionRepository.h"
#include "db/NativeSkillCatalog.h"
#include "game/SharedWorldPresence.h"
#include "net/Session.h"
#include <memory>

namespace god2 {
// Concrete saved30/31/34 observation plus full same149c definition. This is
// not an issued87, controlled86/5 actor, grant, native charge or action owner.
// Construct/use/release on game; borrowed repositories outlive its drain.
class SharedTaiwanOwnedDeitySkillSource final : public std::enable_shared_from_this<SharedTaiwanOwnedDeitySkillSource> {
    struct Impl;
public:
    struct Scope {
        SharedWorldPresence::Lease lease;
        RecoveredPosition position;
        SessionState phase;
        std::uint64_t battle_generation;
    };
    class Observation {
    public:
        const SelectedDeitySkillReadset& saved() const noexcept {return saved_;}
        const NativeSkillRecord& definition() const noexcept {return definition_;}
        const Scope& scope() const noexcept {return scope_;}
    private:
        friend class SharedTaiwanOwnedDeitySkillSource;
        Observation(std::weak_ptr<Impl> origin,std::weak_ptr<Session> session,
            SelectedDeitySkillReadset saved,NativeSkillRecord definition,Scope scope)
            :origin_(std::move(origin)),session_(std::move(session)),saved_(std::move(saved)),
             definition_(std::move(definition)),scope_(std::move(scope)) {}
        std::weak_ptr<Impl> origin_;
        std::weak_ptr<Session> session_;
        SelectedDeitySkillReadset saved_;
        NativeSkillRecord definition_;
        Scope scope_;
    };
    static std::shared_ptr<SharedTaiwanOwnedDeitySkillSource> create(
        std::shared_ptr<SharedWorldPresence>,SqliteCompanionRepository&,const NativeSkillCatalog&);
    std::optional<Observation> observe(Session&,std::uint8_t kind,std::uint8_t definition_id);
    // Re-read full saved row/selection and definition plus exact ready lease.
    // Sequential observations, not an atomic cross-source write/consume CAS.
    // Repository read rejects an already-open transaction; future action must
    // qualify and consume its own complete readset in its real transaction.
    bool current(Session&,const Observation&);
private:
    explicit SharedTaiwanOwnedDeitySkillSource(std::shared_ptr<Impl> state):state_(std::move(state)) {}
    std::shared_ptr<Impl> state_;
};
}
