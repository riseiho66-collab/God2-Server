#pragma once
#include "db/NativeWeaponCatalog.h"
#include "db/SqliteArmorSlotRepository.h"
#include "db/SqliteTradeRepository.h"
#include "db/SqliteBeastSnapshotRepository.h"
#include <functional>

namespace god2 {
// CUSTOM-0069 whole owned-instance custody. Opaque bytes and source evidence
// travel with the item; this is not native generation, admission or stat math.
// Caller supplies two consenting live leases and prepares all replies.
class SqliteOwnedInstanceTradeRepository {
public:
    using QualifyArmor=SqliteArmorSlotRepository::QualifyArmor;
    using QualifyInstance=SqliteArmorSlotRepository::QualifyInstance;
    using LookupWeapon=std::function<std::optional<NativeWeaponRecord>(std::uint16_t)>;
    using EligiblePlain=std::function<bool(std::uint16_t)>;
    struct Snapshot {
        ArmorSnapshot bag;SqliteTradeRepository::Wallet wallet;
        // CUSTOM-0085 optional same-connection PET scope. Default0069 stays
        // unchanged; full values/selection are authority, not client offers.
        bool beast_scope=false;
        std::vector<StoredBeastSnapshot> beasts;
        std::optional<SqliteBeastSnapshotRepository::SelectionRecord> beast_selection;
        bool operator==(const Snapshot&) const=default;
    };
    struct Side {Snapshot expected;std::vector<SqliteTradeRepository::Offer> items;std::uint64_t money{};};
    struct Transfer {std::uint8_t from_side{},source{},to_side{},destination{},quantity{};bool operator==(const Transfer&) const=default;};
    struct Plan {std::array<Snapshot,2> sides;std::vector<Transfer> transfers;bool operator==(const Plan&) const=default;};
    using PreparePlan=std::function<void(const Plan&)>;
    using CheckPlan=std::function<void(const Plan&)>;
    // Last no-allocation/no-provider/no-SQL observation after the final full
    // readback. The actual service supplies only its operation latch/deadline.
    using FinalCurrent=std::function<bool()>;
    static constexpr const char* design_id="CUSTOM-0069";
    static std::string schema(); // Explicit caller installation only; no DDL in constructor/load.
    SqliteOwnedInstanceTradeRepository(sqlite3*,QualifyArmor,QualifyInstance,LookupWeapon,EligiblePlain,SqliteBeastSnapshotRepository* beasts=nullptr);
    Snapshot load(std::uint64_t account,std::uint64_t character);
    Plan plan(const std::array<Side,2>&) const;
    Plan commit(const std::string& receipt,const std::array<Side,2>&,const PreparePlan&,const CheckPlan& check={},const FinalCurrent& current={});
    bool receipt_exists(const std::string&);
private:
    void validate(const Snapshot&) const;
    void no_battle(std::uint64_t character);
    sqlite3* db_;QualifyArmor armor_;QualifyInstance armor_instance_;LookupWeapon weapon_;EligiblePlain plain_;
    SqliteBeastSnapshotRepository* beasts_;
};
}
