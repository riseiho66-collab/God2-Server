#pragma once
#include "protocol/RecoveredDeityState.h"
#include "protocol/RecoveredPet2Lifecycle.h"
#include "protocol/RecoveredPet1Lifecycle.h"
#include "db/NativePet2CategoryCatalog.h"
#include <functional>
#include <memory>
#include <string>
#include <utility>
struct sqlite3;
namespace god2 {
// CUSTOM-0039 owns persistence and selection policy only. Raw instance values
// retain their field/source authority; this repository never generates stats.
struct CompanionProvenance {
    std::string source_sha256;
    std::string authority;
    std::string evidence_id;
    bool operator==(const CompanionProvenance&) const = default;
};
struct StoredDeity {
    RecoveredDeityState::Snapshot snapshot;
    std::uint64_t revision;
    CompanionProvenance provenance;
};
struct StoredDeitySelection {
    std::uint8_t key;
    std::uint64_t revision;
    bool operator==(const StoredDeitySelection&) const = default;
};
class SqliteCompanionRepository;
class OwnedTaiwanPkCompanionSource;
// Complete saved world roster observation on one actual repository/connection.
// Raw30/31/34, row order, revisions, provenance and selection remain separate
// from battle actor identities, issued87, grants, learning or action permission.
class OwnedDeityRosterReadset {
public:
    std::uint64_t account() const noexcept { return account_; }
    std::uint64_t character() const noexcept { return character_; }
    const std::vector<StoredDeity>& rows() const noexcept { return rows_; }
    const std::optional<StoredDeitySelection>& selection() const noexcept { return selection_; }
    const std::vector<std::uint8_t>& template_keys() const noexcept { return template_keys_; }
private:
    friend class SqliteCompanionRepository;
    OwnedDeityRosterReadset(const SqliteCompanionRepository* repository,
        std::weak_ptr<const std::uint8_t> identity,std::uint64_t account,
        std::uint64_t character,std::vector<StoredDeity> rows,
        std::optional<StoredDeitySelection> selection,std::vector<std::uint8_t> template_keys)
        :repository_(repository),identity_(std::move(identity)),account_(account),
         character_(character),rows_(std::move(rows)),selection_(selection),
         template_keys_(std::move(template_keys)) {}
    const SqliteCompanionRepository* repository_;
    std::weak_ptr<const std::uint8_t> identity_;
    std::uint64_t account_,character_;
    std::vector<StoredDeity> rows_;
    std::optional<StoredDeitySelection> selection_;
    std::vector<std::uint8_t> template_keys_;
};
// Owned saved-state observation, not a C35 caster/grant or native cost rule.
// Retains CUSTOM-0039 provenance and the existing display qualification;
// neither those origins nor a catalog definition become casting authority.
class SelectedDeitySkillReadset {
public:
    std::uint64_t account() const noexcept { return account_; }
    std::uint64_t character() const noexcept { return character_; }
    std::uint8_t kind() const noexcept { return skill_.encode()[2]; }
    std::uint8_t definition_id() const noexcept { return skill_.encode()[3]; }
    const StoredDeitySelection& selection() const noexcept { return selection_; }
    const StoredDeity& deity() const noexcept { return deity_; }
    const RecoveredDeityState::Skill& skill() const noexcept { return skill_; }
private:
    friend class SqliteCompanionRepository;
    SelectedDeitySkillReadset(const SqliteCompanionRepository* repository,
        std::weak_ptr<const std::uint8_t> identity,std::uint64_t account,
        std::uint64_t character,StoredDeitySelection selection,StoredDeity deity,
        RecoveredDeityState::Skill skill)
        :repository_(repository),identity_(std::move(identity)),account_(account),
         character_(character),selection_(selection),deity_(std::move(deity)),skill_(skill) {}
    const SqliteCompanionRepository* repository_;
    std::weak_ptr<const std::uint8_t> identity_;
    std::uint64_t account_,character_;
    StoredDeitySelection selection_;
    StoredDeity deity_;
    RecoveredDeityState::Skill skill_;
};
struct StoredPet2Slot {
    std::uint8_t slot;
    std::optional<RecoveredPet2Lifecycle::Snapshot> pet;
    std::uint64_t revision;
    CompanionProvenance provenance;
    // Native display classification; unknown/unimported remains absent. It is
    // not an authoritative species/generation/growth rule or instance grant.
    std::optional<NativePet2Category> display_category;
    std::optional<RecoveredPet1Lifecycle::Snapshot> pet1;
    bool occupied() const noexcept {return pet.has_value() || pet1.has_value();}
};
struct Pet2TransferCommit { StoredPet2Slot source,destination; };
class SqliteCompanionRepository {
public:
    explicit SqliteCompanionRepository(sqlite3* db):db_(db) {}
    bool uses_connection(const sqlite3* db) const noexcept {return db_==db;}
    static constexpr const char* source_sha256=
        "70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731";
    // Catalog rows are independently native-parsed current GOD/NCP metadata.
    std::vector<std::uint8_t> deity_template_keys();
    bool resolves_pet2(std::uint16_t key);
    bool resolves_pet1(std::uint16_t key);
    std::vector<StoredDeity> load_deities(std::uint64_t account,std::uint64_t character);
    std::optional<StoredDeitySelection> load_deity_selection(std::uint64_t account,std::uint64_t character);
    // Own READ transaction, rejecting an existing transaction, TEMP shadows
    // and cross-readset reentry. Empty roster/absent selection are valid;
    // malformed storage or a dangling selection throws, never an empty fallback.
    // Template keys are qualified within this same observation so restoration
    // need not re-read a different catalog epoch. This is not future write CAS
    // or a socket-written/battle roster receipt. Borrowed DB must outlive use.
    OwnedDeityRosterReadset load_deity_roster(std::uint64_t account,std::uint64_t character);
    bool deity_roster_current(const OwnedDeityRosterReadset& readset);
    // Trusted saved S2C34 on the selected owned deity; never a client grant.
    bool selected_deity_has_skill(std::uint64_t account,std::uint64_t character,
        std::uint8_t kind,std::uint8_t skill);
    // Own READ transaction; reject an existing transaction and TEMP shadows.
    // Missing selection/skill returns nullopt; malformed/unqualified storage
    // throws. Current re-reads the full chosen row, including every saved34.
    // This is a consistent observation, not future action/consumption CAS.
    std::optional<SelectedDeitySkillReadset> load_selected_deity_skill(
        std::uint64_t account,std::uint64_t character,std::uint8_t kind,std::uint8_t skill);
    bool selected_deity_skill_current(const SelectedDeitySkillReadset& readset);
    StoredDeitySelection select_deity(std::uint64_t account,std::uint64_t character,
        std::uint8_t key,const std::optional<StoredDeitySelection>& expected);
    // Explicit trusted acquisition/import API. Network requests cannot grant.
    StoredDeity store_deity(std::uint64_t account,std::uint64_t character,
        const RecoveredDeityState::Snapshot& snapshot,std::optional<std::uint64_t> expected_revision,
        const CompanionProvenance& provenance);
    std::vector<StoredPet2Slot> load_pet2_slots(std::uint64_t account,std::uint64_t character);
    // Explicitly allocate three empty instance cells without acquiring a pet.
    std::size_t provision_pet2_slots(std::uint64_t account,std::uint64_t character);
    StoredPet2Slot store_pet2(std::uint64_t account,std::uint64_t character,std::uint8_t slot,
        const RecoveredPet2Lifecycle::Snapshot& pet,std::uint64_t expected_revision,
        const CompanionProvenance& provenance);
    StoredPet2Slot store_pet1(std::uint64_t account,std::uint64_t character,std::uint8_t slot,
        const RecoveredPet1Lifecycle::Snapshot& pet,std::uint64_t expected_revision,
        const CompanionProvenance& provenance);
    Pet2TransferCommit transfer_pet2(std::uint64_t account,std::uint64_t character,
        const StoredPet2Slot& source,const StoredPet2Slot& destination);
    // CUSTOM-0039: explicit native24 reserve42/43 reorder. Both owned cells
    // must exist; active44 and existing28 selection policy are not involved.
    // Prepare the complete reply before COMMIT; failure rolls back both cells.
    Pet2TransferCommit move_pet_reserves(std::uint64_t account,std::uint64_t character,
        const StoredPet2Slot& source,const StoredPet2Slot& destination,
        const std::function<void(const Pet2TransferCommit&)>& prepare);
private:
    friend class OwnedTaiwanPkCompanionSource;
    // CUSTOM-0129 borrow the RESERVED transaction; no BEGIN, callback or write.
    // Complete privately minted roster equality, not a live Session qualifier.
    bool deity_roster_current_in_transaction(const OwnedDeityRosterReadset&);
    std::optional<SelectedDeitySkillReadset> read_selected_deity_skill(
        std::uint64_t account,std::uint64_t character,std::uint8_t kind,std::uint8_t skill);
    void require_owner(std::uint64_t account,std::uint64_t character);
    void require_no_pending_battle(std::uint64_t character);
    static void require_provenance(const CompanionProvenance& provenance);
    sqlite3* db_;
    std::shared_ptr<const std::uint8_t> readset_identity_=std::make_shared<const std::uint8_t>(0);
    bool readset_reading_=false,readset_reentered_=false;
};
}
