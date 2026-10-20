#pragma once
#include "db/SqliteCompanionRepository.h"
#include "db/SqliteSkillBookLearningRepository.h"
#include "protocol/RecoveredDeitySelection.h"
#include "protocol/RecoveredDeityActivation.h"
#include "protocol/RecoveredWorldFrame.h"
#include "protocol/TaiwanNativeDeityRosterPrefix.h"
#include <thread>
namespace god2 {
class OwnedTaiwanPkCompanionSource;
class RecoveredOwnedCompanions {
public:
    explicit RecoveredOwnedCompanions(SqliteCompanionRepository& repository):repository_(repository) {}
    bool owns_repository(const SqliteCompanionRepository& repository)const noexcept {
        return &repository_==&repository;
    }
    class Restoration {
    public:
        const OwnedDeityRosterReadset& deity_roster() const noexcept {return deity_roster_;}
        const std::optional<SqliteSkillBookLearningRepository::Restoration>& learning_source() const noexcept {return learning_source_;}
        bool owns_learning_repository(const SqliteSkillBookLearningRepository& value) const noexcept {
            return learning_repository_==&value && bool(learning_source_);
        }
        // Exact existing logical-boundary batches, including the separate pet
        // projection. The deity readset does not certify pet revisions or an
        // atomic cross-family snapshot, queue acceptance or socket write.
        const std::vector<std::vector<std::uint8_t>>& batches() const noexcept {return batches_;}
    private:
        friend class RecoveredOwnedCompanions;
        Restoration(OwnedDeityRosterReadset roster,std::vector<std::vector<std::uint8_t>> batches)
            :deity_roster_(std::move(roster)),batches_(std::move(batches)) {}
        Restoration(OwnedDeityRosterReadset roster,std::vector<std::vector<std::uint8_t>> batches,
            SqliteSkillBookLearningRepository::Restoration learning,SqliteSkillBookLearningRepository& repository)
            :deity_roster_(std::move(roster)),batches_(std::move(batches)),
             learning_source_(std::move(learning)),learning_repository_(&repository) {}
        OwnedDeityRosterReadset deity_roster_;
        std::vector<std::vector<std::uint8_t>> batches_;
        std::optional<SqliteSkillBookLearningRepository::Restoration> learning_source_;
        SqliteSkillBookLearningRepository* learning_repository_=nullptr; // Actual DB owner outlives source/current calls.
    };
    // Fresh world entry only, AFTER saved player vitals. Empty ownership sends
    // nothing. Records are split at logical boundaries within native queue cap.
    std::vector<std::vector<std::uint8_t>> restore(std::uint64_t account,std::uint64_t character);
    // Actual same-connection complete deity roster/selection and exact batches
    // from the same existing projection. Construct/current on game; no saved
    // mutations, invented learned flags, battle positions or grant generated.
    Restoration restore_with_source(std::uint64_t account,std::uint64_t character);
    // CUSTOM-0148 one original restoration sender: same full learning readset,
    // legacy pets, and only genuine activation records. No second S30 replay.
    Restoration restore_with_source(std::uint64_t account,std::uint64_t character,
        SqliteSkillBookLearningRepository&);
    // CUSTOM-0148 exclusive Application initial deity publisher. Same full
    // saved source and genuine activation lineage; no pets or player records.
    Restoration restore_deities_with_source(std::uint64_t account,std::uint64_t character,
        SqliteSkillBookLearningRepository&);
    bool restoration_current(const Restoration&);
    std::optional<Restoration> material_successor_from_committed(const Restoration&,
        SqliteOwnedEquipmentTransaction&,const SqliteOwnedEquipmentTransaction::Committed&);
    std::optional<Restoration> material_successor_from_committed_chain(const Restoration&,
        SqliteOwnedEquipmentTransaction&,std::span<const SqliteOwnedEquipmentTransaction::Committed* const>);
    // Learning-present original restoration only. The caller separately checks
    // the original closed roster/room cut; no source is restored or issued here.
    bool restoration_learning_current_in_transaction(const Restoration&,sqlite3* actual_connection);
    // CUSTOM-0148 explicit actual readset + genuinely retained activation source.
    // Deity records only; legacy account/character restoration and pets unchanged.
    // Caller requalifies the actual repository readset before/after this projection.
    static std::optional<std::vector<std::vector<std::uint8_t>>> restore(
        const OwnedDeityRosterReadset&,std::span<const RecoveredDeityActivation::Record>);
    // Expected reset + issued-data prefix only. Application must supply its
    // actual normal-entry/current/write epoch; this API supplies no such lease
    // or remote consumer attestation. Missing qualified448 material is absent.
    std::optional<TaiwanNativeDeityRosterPrefix> normal_entry_prefix(
        const Restoration&,const NativeSkillCatalog&);
    bool normal_entry_prefix_current(const Restoration&,const TaiwanNativeDeityRosterPrefix&,
        const NativeSkillCatalog&);
    class SelectionPublication {
        struct Data;
    public:
        SelectionPublication(const SelectionPublication&) noexcept=default;
        SelectionPublication& operator=(const SelectionPublication&) noexcept=default;
        const SqliteCompanionRepository::CommittedDeitySelection& committed() const noexcept;
        const std::vector<std::uint8_t>& wire() const noexcept;
    private:
        friend class RecoveredOwnedCompanions;
        explicit SelectionPublication(std::shared_ptr<const Data> data) noexcept:data_(std::move(data)) {}
        std::shared_ptr<const Data> data_;
    };
    // Actual private S31 commit chain only. Caller owns its complete Written
    // publication; this source helper supplies no receipt or native adoption.
    // Preserve original history/tails and qualify only the full after source.
    std::optional<Restoration> selection_successor_from_committed(const Restoration&,
        std::span<const SelectionPublication>);
    class SelectionResult {
    public:
        SelectionResult(SelectionResult&&) noexcept=default;
        SelectionResult& operator=(SelectionResult&&) noexcept=default;
        SelectionResult(const SelectionResult&)=delete;
        SelectionResult& operator=(const SelectionResult&)=delete;
        const SqliteCompanionRepository::CommittedDeitySelection& committed() const noexcept {return publication_.committed();}
        const SelectionPublication& publication() const noexcept {return publication_;}
        const std::vector<std::uint8_t>& wire() const noexcept {return wire_;}
        std::vector<std::uint8_t> take_wire() && noexcept {return std::move(wire_);}
    private:
        friend class RecoveredOwnedCompanions;
        SelectionResult(SelectionPublication publication,std::vector<std::uint8_t> wire) noexcept
            :publication_(std::move(publication)),wire_(std::move(wire)) {}
        SelectionPublication publication_;
        std::vector<std::uint8_t> wire_;
    };
    // Exact prebuilt S31 plus the one-row selection commit which qualified it.
    // No socket-written receipt, native adoption or permission is inferred.
    std::optional<SelectionResult> select_deity_with_source(
        std::uint64_t account,std::uint64_t character,const RecoveredDeitySelection::Request& request);
    std::optional<std::vector<std::uint8_t>> select_deity(
        std::uint64_t account,std::uint64_t character,const RecoveredDeitySelection::Request& request);
    std::optional<std::vector<std::uint8_t>> select_pet2(
        std::uint64_t account,std::uint64_t character,const RecoveredSelectionItemRequest::Request& request);
private:
    friend class OwnedTaiwanPkCompanionSource;
    // Actual committed fullafter plus genuine immutable wire history only.
    // No fresh restore/reset, original stale Current or public raw constructor.
    std::optional<Restoration> learning_successor_from_committed(const Restoration&,
        const SqliteSkillBookLearningRepository::Committed&,
        std::vector<std::vector<std::uint8_t>> actual_history);
    struct PrefixRead;
    std::optional<TaiwanNativeDeityRosterPrefix> normal_entry_prefix_impl(
        const Restoration&,const NativeSkillCatalog&);
    std::vector<std::vector<std::uint8_t>> restore_rows(std::uint64_t account,std::uint64_t character,
        std::span<const StoredDeity>,const std::optional<StoredDeitySelection>&,
        std::span<const std::uint8_t> template_keys);
    SqliteCompanionRepository& repository_;
    const std::thread::id prefix_thread_=std::this_thread::get_id();
    bool prefix_reading_=false,prefix_reentered_=false;
};
}
