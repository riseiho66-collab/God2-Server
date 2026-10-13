#pragma once
#include "db/SqliteCompanionRepository.h"
#include "db/NativeSkillCatalog.h"
#include "game/SharedWorldPresence.h"
#include "protocol/RecoveredWorldSkillRequest.h"
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
    // CUSTOM-0145: owning self target input plus the actual private normal
    // entry holder. Written is local delivery, not remote adoption or a cast.
    class SelfTargetInput {
    public:
        const RecoveredWorldSkillRequest::Request& request() const noexcept {return request_;}
        const Session::NormalWorldInitialization& initialization() const noexcept {return initialization_;}
    private:
        friend class SharedTaiwanOwnedDeitySkillSource;
        SelfTargetInput(RecoveredWorldSkillRequest::Request request,Session::NormalWorldInitialization initialization)
            :request_(std::move(request)),initialization_(std::move(initialization)) {}
        RecoveredWorldSkillRequest::Request request_;
        Session::NormalWorldInitialization initialization_;
    };
    class Observation {
    public:
        const SelectedDeitySkillReadset& saved() const noexcept {return saved_;}
        const NativeSkillRecord& definition() const noexcept {return definition_;}
        // CUSTOM-0144: owning common data, never a cast/list/publication grant.
        const SharedSkillDefinition& common_definition() const noexcept {return common_definition_;}
        const Scope& scope() const noexcept {return scope_;}
        const std::optional<SelfTargetInput>& self_target_input() const noexcept {return self_target_input_;}
    private:
        friend class SharedTaiwanOwnedDeitySkillSource;
        Observation(std::weak_ptr<Impl> origin,std::weak_ptr<Session> session,
            SelectedDeitySkillReadset saved,NativeSkillRecord definition,SharedSkillDefinition common,Scope scope)
            :origin_(std::move(origin)),session_(std::move(session)),saved_(std::move(saved)),
             definition_(std::move(definition)),common_definition_(std::move(common)),scope_(std::move(scope)) {}
        std::weak_ptr<Impl> origin_;
        std::weak_ptr<Session> session_;
        SelectedDeitySkillReadset saved_;
        NativeSkillRecord definition_;
        SharedSkillDefinition common_definition_;
        Scope scope_;
        std::optional<SelfTargetInput> self_target_input_;
    };
    static std::shared_ptr<SharedTaiwanOwnedDeitySkillSource> create(
        std::shared_ptr<SharedWorldPresence>,SqliteCompanionRepository&,const NativeSkillCatalog&);
    std::optional<Observation> observe(Session&,std::uint8_t kind,std::uint8_t definition_id);
    // Own actual world-records callback only. Keeps every raw C56 byte and
    // joins its complete target WORD to the same current entry/ready lease.
    // Other targets, selected-menu publication, rules and action stay separate.
    std::optional<Observation> observe_world_self(Session&,const RecoveredWorldSkillRequest::Request&);
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
