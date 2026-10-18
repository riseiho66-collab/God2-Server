#pragma once
#include "db/SqliteArmorSlotRepository.h"
#include "db/SqliteBeastSnapshotRepository.h"
#include "protocol/RecoveredInventoryMoveRequest.h"
#include "protocol/RecoveredInventoryDiscard.h"
#include <string>
#include <utility>
#include <vector>
namespace god2 {
class OwnedBagProjectionService;
// CUSTOM-0085: whole ordinary-bag swap including PET and qualified neighbouring
// instances. Native24 has no nonce; this is custom server policy, not recovery
// of original merge/equipment/drop rules. Explicit BeastEquipment domain
// supports owned PET bag/37 only;24 keeps its ordinary domain. No schema or
// capacity is created by capture or move.
class SqliteBeastBagRepository {
public:
    enum class Domain {OrdinaryBag,BeastEquipment};
    using Rows=std::vector<std::vector<std::uint8_t>>;
    // Map-key order and exact typed rows, stored without a tree sentinel:
    // MSVC map move can allocate, which is unsafe when returning after COMMIT.
    struct Preservation {
        std::vector<std::pair<std::string,Rows>> ordered;
        bool operator==(const Preservation&) const=default;
    };
    struct Snapshot {
        RecoveredInventoryMoveRequest::Request request;
        Domain domain=Domain::OrdinaryBag;
        ArmorSnapshot bag;
        std::vector<StoredBeastSnapshot> beasts;
        std::optional<SqliteBeastSnapshotRepository::SelectionRecord> selection;
        Preservation peripheral;
        bool operator==(const Snapshot&) const=default;
    };
    struct Result {Snapshot after;std::vector<std::uint8_t> wire;bool changed{};};
    SqliteBeastBagRepository(sqlite3*,SqliteBeastSnapshotRepository&,
        SqliteArmorSlotRepository&,OwnedBagProjectionService&);
    Snapshot capture(std::uint64_t account,std::uint64_t character,
        const RecoveredInventoryMoveRequest::Request&,Domain=Domain::OrdinaryBag);
    Result move(const Snapshot&); // immutable whole-frame capture, standalone CAS
    // CUSTOM-0085 native27 whole owned ordinary-bag PET destruction. Feature
    // journal3 is independent of immutable custody/selection1/equipment2.
    static std::string discard_schema();
    static void install_discard_schema(sqlite3*); // explicit startup only
    static void require_discard_schema(sqlite3*);
    Result discard(const Snapshot&,const RecoveredInventoryDiscard::Request&,
        const std::string& receipt);
    // Current owned source projection after a rejected mutation. Includes full
    // typed instances; never echo the stale client key or the old captured row.
    std::vector<std::uint8_t> refresh_source(std::uint64_t account,std::uint64_t character,std::uint8_t slot);
private:
    sqlite3* db_;SqliteBeastSnapshotRepository& beasts_;
    SqliteArmorSlotRepository& armor_;OwnedBagProjectionService& projector_;
};
}
