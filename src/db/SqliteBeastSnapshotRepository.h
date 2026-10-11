#pragma once
#include "db/NativeBeastSourceCatalog.h"
#include "protocol/RecoveredBeastPanel.h"
#include "protocol/RecoveredBeastExploration.h"
#include "protocol/RecoveredBeastInventoryFields.h"
#include <string>
#include <vector>
struct sqlite3;
namespace god2 {
struct StoredBeastSnapshot {
    std::uint64_t account{},character{},revision{},bag_revision{};
    std::uint8_t inventory_slot{};
    std::array<std::uint8_t,20> inventory_metadata{};
    // Source-qualified tooltip branch. Date records never expose EXP/level
    // through this view; this interpretation does not authorize a mutation.
    std::optional<RecoveredBeastInventoryFields::View> inventory_fields() const noexcept {
        return RecoveredBeastInventoryFields::decode(inventory_metadata);
    }
    RecoveredBeastPanel::Snapshot panel{};
    std::optional<RecoveredBeastExploration::Snapshot> exploration;
    // Origin applies to instance values; native PET source membership alone
    // never upgrades this to native instance/growth/formula authority.
    std::string origin,evidence_id;
    bool operator==(const StoredBeastSnapshot&) const=default;
};
// CUSTOM-0085: owned raw PET snapshot custody, distinct from COM/E3/NCP/FB.
// Explicit additive feature schema; no grant, timer, food or action rule.
class SqliteBeastSnapshotRepository {
public:
    struct SelectionRecord {
        std::uint8_t selector{};
        std::uint64_t custody_revision{},revision{};
        bool operator==(const SelectionRecord&) const=default;
    };
    struct Selected {
        StoredBeastSnapshot instance;
        std::uint64_t revision{};
        bool operator==(const Selected&) const=default;
    };
    struct Projection {
        std::vector<std::uint8_t> logical;
        std::vector<StoredBeastSnapshot> instances;
        std::optional<Selected> selected;
    };
    static constexpr const char* design_id="CUSTOM-0085";
    static constexpr const char* client_sha256="6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98";
    explicit SqliteBeastSnapshotRepository(sqlite3*);
    bool shares_connection(sqlite3* db) const noexcept{return db_==db;}
    static const char* schema() noexcept;
    static const char* selection_schema() noexcept;
    // Explicit v2 feature extension; original schema()/v1 ledger retained.
    static std::string equipment_schema();
    static void install_schema(sqlite3*); // explicit, preserves base migration history
    static void require_schema(sqlite3*);
    static void require_equipment_schema(sqlite3*);
    // CUSTOM persistent panel selection. Never grants or changes instance bytes.
    std::optional<std::vector<std::uint8_t>> open_owned_panel(
        std::uint64_t account,std::uint64_t character,std::uint8_t slot,std::uint16_t key);
    std::optional<StoredBeastSnapshot> load(std::uint64_t account,std::uint64_t character,std::uint8_t slot);
    std::vector<StoredBeastSnapshot> load_owned(std::uint64_t account,std::uint64_t character);
    std::optional<Selected> load_selected(std::uint64_t account,std::uint64_t character);
    std::optional<SelectionRecord> load_selection_record(std::uint64_t account,std::uint64_t character);
    Projection restore(std::uint64_t account,std::uint64_t character);
    // Server-only custody of a separately acquired existing owned bag/37 item.
    // Never call from a network request. Caller supplies every opaque byte and
    // its evidence; inventory capacity/count/item/revision are not changed.
    // Exact existing expected row required for replacement, including origin.
    StoredBeastSnapshot store_existing_owned(const StoredBeastSnapshot& next,
        const std::optional<StoredBeastSnapshot>& expected);
private:
    void owner(std::uint64_t,std::uint64_t);
    void no_pending_battle(std::uint64_t);
    void validate(const StoredBeastSnapshot&);
    std::optional<StoredBeastSnapshot> read(std::uint64_t,std::uint64_t,std::uint8_t);
    std::optional<Selected> selected(std::uint64_t,std::uint64_t);
    sqlite3* db_;
};
}
