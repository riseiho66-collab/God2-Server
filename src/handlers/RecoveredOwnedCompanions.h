#pragma once
#include "db/SqliteCompanionRepository.h"
#include "protocol/RecoveredDeitySelection.h"
#include "protocol/RecoveredWorldFrame.h"
#include "protocol/TaiwanNativeDeityRosterPrefix.h"
#include <thread>
namespace god2 {
class RecoveredOwnedCompanions {
public:
    explicit RecoveredOwnedCompanions(SqliteCompanionRepository& repository):repository_(repository) {}
    bool owns_repository(const SqliteCompanionRepository& repository)const noexcept {
        return &repository_==&repository;
    }
    class Restoration {
    public:
        const OwnedDeityRosterReadset& deity_roster() const noexcept {return deity_roster_;}
        // Exact existing logical-boundary batches, including the separate pet
        // projection. The deity readset does not certify pet revisions or an
        // atomic cross-family snapshot, queue acceptance or socket write.
        const std::vector<std::vector<std::uint8_t>>& batches() const noexcept {return batches_;}
    private:
        friend class RecoveredOwnedCompanions;
        Restoration(OwnedDeityRosterReadset roster,std::vector<std::vector<std::uint8_t>> batches)
            :deity_roster_(std::move(roster)),batches_(std::move(batches)) {}
        OwnedDeityRosterReadset deity_roster_;
        std::vector<std::vector<std::uint8_t>> batches_;
    };
    // Fresh world entry only, AFTER saved player vitals. Empty ownership sends
    // nothing. Records are split at logical boundaries within native queue cap.
    std::vector<std::vector<std::uint8_t>> restore(std::uint64_t account,std::uint64_t character);
    // Actual same-connection complete deity roster/selection and exact batches
    // from the same existing projection. Construct/current on game; no saved
    // mutations, invented learned flags, battle positions or grant generated.
    Restoration restore_with_source(std::uint64_t account,std::uint64_t character);
    bool restoration_current(const Restoration&);
    // Expected reset + issued-data prefix only. Application must supply its
    // actual normal-entry/current/write epoch; this API supplies no such lease
    // or remote consumer attestation. Missing qualified448 material is absent.
    std::optional<TaiwanNativeDeityRosterPrefix> normal_entry_prefix(
        const Restoration&,const NativeSkillCatalog&);
    bool normal_entry_prefix_current(const Restoration&,const TaiwanNativeDeityRosterPrefix&,
        const NativeSkillCatalog&);
    std::optional<std::vector<std::uint8_t>> select_deity(
        std::uint64_t account,std::uint64_t character,const RecoveredDeitySelection::Request& request);
    std::optional<std::vector<std::uint8_t>> select_pet2(
        std::uint64_t account,std::uint64_t character,const RecoveredSelectionItemRequest::Request& request);
private:
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
