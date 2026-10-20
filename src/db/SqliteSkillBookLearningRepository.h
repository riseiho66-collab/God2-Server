#pragma once
#include "db/NativeSkillBookCatalog.h"
#include "db/SharedSkillDefinition.h"
#include "db/SqliteCompanionRepository.h"
#include "db/SqliteNativeEquipmentSnapshotRepository.h"
#include "db/SqliteOwnedInventoryRepository.h"
#include "protocol/RecoveredInventory.h"
#include <functional>
#include <memory>
#include <span>
#include <thread>

namespace god2 {
// CUSTOM-0148: explicit TW selected-owned-deity learning policy. Catalog
// association is source material, not recovered native learning permission.
class SqliteSkillBookLearningRepository final {
    struct State;
    struct ObservationData;
    struct PlanData;
    struct Operation;
public:
    struct Activation {
        std::uint8_t subject{},kind{},definition_id{};
        std::string event_id;
        bool operator==(const Activation&) const=default;
    };
    class Restoration {
    public:
        Restoration(const Restoration&)=default;
        Restoration& operator=(const Restoration&)=default;
        Restoration(Restoration&& value) noexcept:state_(value.state_) {}
        Restoration& operator=(Restoration&& value) noexcept {state_=value.state_;return *this;}
        const OwnedInventorySnapshot& inventory() const noexcept;
        const NativeEquipmentSnapshot& equipment() const noexcept;
        const OwnedDeityRosterReadset& roster() const noexcept;
        const std::vector<Activation>& activations() const noexcept;
    private:
        friend class SqliteSkillBookLearningRepository;
        explicit Restoration(std::shared_ptr<const State> value) noexcept:state_(std::move(value)) {}
        std::shared_ptr<const State> state_;
    };
    class Observation {
    public:
        Observation(const Observation&)=default;
        Observation& operator=(const Observation&)=default;
        Observation(Observation&& value) noexcept:data_(value.data_) {}
        Observation& operator=(Observation&& value) noexcept {data_=value.data_;return *this;}
        const OwnedInventorySnapshot& inventory() const noexcept;
        const NativeEquipmentSnapshot& equipment() const noexcept;
        const OwnedDeityRosterReadset& roster() const noexcept;
        const StoredDeity& deity() const noexcept;
        const StoredDeitySelection& selection() const noexcept;
        const NativeSkillBookRecord& book() const noexcept;
        const SharedSkillDefinition& common_definition() const noexcept;
        const std::vector<Activation>& activations() const noexcept;
        std::uint8_t slot() const noexcept;
        bool already_learned() const noexcept;
    private:
        friend class SqliteSkillBookLearningRepository;
        explicit Observation(std::shared_ptr<const ObservationData> value) noexcept:data_(std::move(value)) {}
        std::shared_ptr<const ObservationData> data_;
    };
    class Plan {
    public:
        Plan(const Plan&)=default;
        Plan& operator=(const Plan&)=default;
        Plan(Plan&& value) noexcept:data_(value.data_) {}
        Plan& operator=(Plan&& value) noexcept {data_=value.data_;return *this;}
        const RecoveredDeityState::Skill& skill() const noexcept;
        const Activation& activation() const noexcept;
        RecoveredInventory::SlotUpdate slot_update() const noexcept;
        const OwnedInventorySnapshot& inventory() const noexcept;
        const NativeEquipmentSnapshot& equipment() const noexcept;
        const StoredDeity& deity() const noexcept;
        const std::vector<Activation>& activations() const noexcept;
    private:
        friend class SqliteSkillBookLearningRepository;
        explicit Plan(std::shared_ptr<const PlanData> value) noexcept:data_(std::move(value)) {}
        std::shared_ptr<const PlanData> data_;
    };
    class Committed {
    public:
        Committed(const Committed&)=default;
        Committed& operator=(const Committed&)=default;
        Committed(Committed&& other) noexcept:data_(other.data_) {}
        Committed& operator=(Committed&& other) noexcept {data_=other.data_;return *this;}
        const OwnedInventorySnapshot& inventory() const noexcept;
        const NativeEquipmentSnapshot& equipment() const noexcept;
        const StoredDeity& deity() const noexcept;
        const std::vector<Activation>& activations() const noexcept;
    private:
        friend class SqliteSkillBookLearningRepository;
        explicit Committed(std::shared_ptr<const PlanData> value) noexcept:data_(std::move(value)) {}
        std::shared_ptr<const PlanData> data_;
    };
    SqliteSkillBookLearningRepository(SqliteOwnedInventoryRepository&,
        SqliteNativeEquipmentSnapshotRepository&,SqliteCompanionRepository&,
        const NativeSkillBookCatalog&,const NativeSkillCatalog&);
    static std::string schema(); // Explicit installer only; no constructor/read DDL.
    bool owns_companions(const SqliteCompanionRepository& value) const noexcept {return &companions_==&value;}
    std::optional<NativeSkillBookRecord> lookup_book(std::uint16_t item) const;
    std::optional<Observation> observe(std::uint64_t account,std::uint64_t character,
        std::uint8_t slot,std::uint16_t item);
    std::optional<Plan> plan(const Observation&);
    bool current(const Observation&);
    using Current=std::function<bool()>; // Actual pure Session/INIT/lease cut only.
    std::optional<Committed> commit(const Plan&,Current);
    Restoration restore(std::uint64_t account,std::uint64_t character);
    bool restoration_current(const Restoration&);
    // Selection-only source continuation. Preserve inventory/equipment and
    // every activation header/event; qualify the final full State once after
    // the private commit chain. This never learns, writes or restores records.
    std::optional<Restoration> selection_successor(const Restoration&,
        std::span<const SqliteCompanionRepository::CommittedDeitySelection* const>);
    // Original private restoration only, on the actual same connection in an
    // already active transaction. Read-only qualification, not room authority;
    // preserves generic pending-battle rejection and never opens a transaction.
    bool restoration_current_in_transaction(const Restoration&,sqlite3* actual_connection);
    // Original preallocated immutable after State/controlblock only. No SQL,
    // restore, vector copy or new allocation. Committed is the actual carrier.
    std::optional<Restoration> committed_after_source(const Committed&) const noexcept;
    bool committed_matches_plan(const Committed&,const Plan&) const noexcept;
    // Actual private Committed -> its complete retained BEFORE source. Pure
    // issuer/full-tuple comparison; no SQL or new State/controlblock.
    bool committed_matches_restoration_before(const Committed&,const Restoration&) const noexcept;
    // PROVISIONAL alias for preallocation before COMMIT. It provides no commit,
    // grant, publication or SourceCurrent authority; match the actual Committed
    // to this exact Plan before using it as an after-source.
    std::optional<Restoration> planned_after_source(const Plan&) const noexcept;
    // Complete retained BEFORE State equality, including ordered raw roster,
    // all activation headers/events and full inventory/equipment provenance.
    bool plan_matches_restoration(const Plan&,const Restoration&) const noexcept;
private:
    friend class SqliteCompanionRepository;
    // Existing trusted import writer only; no public grant/factory. The caller
    // owns its transaction and full before/after rows. Retain the original book
    // events/links exactly, advancing only a matching status-only witness.
    static bool preserve_status_only_activation(sqlite3*,std::uint64_t account,
        std::uint64_t character,const StoredDeity& before,const StoredDeity& after);
    void owner() const;
    void namespaces() const;
    std::shared_ptr<State> read_state(OwnedDeityRosterReadset);
    bool state_current(const State&);
    bool observation_current(const ObservationData&);
    bool retained_plan_issuer(const PlanData&) const noexcept;
    SqliteOwnedInventoryRepository& inventory_;
    SqliteNativeEquipmentSnapshotRepository& equipment_;
    SqliteCompanionRepository& companions_;
    const NativeSkillBookCatalog& books_;
    const NativeSkillCatalog& skills_;
    const std::thread::id thread_=std::this_thread::get_id();
    const std::shared_ptr<const std::uint8_t> identity_=std::make_shared<const std::uint8_t>(0);
    bool busy_=false;
    mutable bool poisoned_=false;
};
}
