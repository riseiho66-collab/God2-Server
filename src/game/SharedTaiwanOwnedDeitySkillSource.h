#pragma once
#include "db/SqliteCompanionRepository.h"
#include "db/NativeSkillCatalog.h"
#include "game/SharedWorldPresence.h"
#include "protocol/RecoveredWorldSkillRequest.h"
#include "protocol/RecoveredDeitySelection.h"
#include "net/Session.h"
#include <memory>

namespace god2 {
class RecoveredOwnedCompanions;
// Concrete saved30/31/34 observation plus full same149c definition. This is
// not an issued87, controlled86/5 actor, grant, native charge or action owner.
// Construct/use/release on game; borrowed repositories outlive its drain.
class SharedTaiwanOwnedDeitySkillSource final : public std::enable_shared_from_this<SharedTaiwanOwnedDeitySkillSource> {
    struct Impl;
    struct Publication;
    struct CallbackData;
public:
    enum class Mode {SavedObservationOnly,SelectionPublicationRequired};
    class SelectionCallback {
    public:
        SelectionCallback(const SelectionCallback&) noexcept=default;
        SelectionCallback& operator=(const SelectionCallback&) noexcept=default;
    private:
        friend class SharedTaiwanOwnedDeitySkillSource;
        explicit SelectionCallback(std::shared_ptr<CallbackData> data) noexcept:data_(std::move(data)) {}
        std::shared_ptr<CallbackData> data_;
    };
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
        std::shared_ptr<const Publication> publication_;
    };
    static std::shared_ptr<SharedTaiwanOwnedDeitySkillSource> create(
        std::shared_ptr<SharedWorldPresence>,SqliteCompanionRepository&,const NativeSkillCatalog&,
        Mode=Mode::SavedObservationOnly,std::size_t actual_session_capacity=0);
    bool owns_sources(const std::shared_ptr<SharedWorldPresence>&,const SqliteCompanionRepository&,
        const NativeSkillCatalog&) const noexcept;
    bool publication_required() const noexcept;
    // CUSTOM-0147: actual outer callback owns copied original C67 ordinals.
    // No SQL/cast grant is minted by the draft or local socket receipt.
    void check_selection_callback_entry();
    std::optional<SelectionCallback> begin_selection_callback(Session&,std::span<const std::uint8_t> keys);
    std::optional<std::vector<std::uint8_t>> select_deity_for_callback(
        Session&,RecoveredOwnedCompanions&,const RecoveredDeitySelection::Request&);
    bool selection_response_matches(Session&,const SelectionCallback&,std::span<const std::uint8_t>);
    void publish_selection_callback(Session&,const SelectionCallback&,const Session::WorldResponseWrite&);
    void abandon_selection_callback(const SelectionCallback&) noexcept;
    void release_selection(Session&);
    void invalidate_selection_callbacks();
    void stop_selection_publications() noexcept;
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
