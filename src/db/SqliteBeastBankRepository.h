#pragma once
#include "db/SqliteOwnedForeignBankRepository.h"
#include "db/SqliteBeastSnapshotRepository.h"
#include "protocol/RecoveredBankItems.h"
#include <utility>

namespace god2 {
// CUSTOM0085 vault custody is separate from the native BYTE bag namespace.
// Full raw instance fields follow ownership; no item generation or activity.
struct StoredVaultBeast {
    std::uint16_t slot{};
    std::uint64_t revision{},physical_revision{};
    std::array<std::uint8_t,20> inventory_metadata{};
    RecoveredBeastPanel::Snapshot panel{};
    std::optional<RecoveredBeastExploration::Snapshot> exploration;
    std::string origin,evidence_id;
    bool operator==(const StoredVaultBeast&) const=default;
};
class SqliteBeastBankRepository {
public:
    using Base=SqliteOwnedForeignBankRepository::Snapshot;
    struct Snapshot : Base {
        Snapshot()=default;
        Snapshot(Base value):Base(std::move(value)){}
        bool beast_scope=false;
        std::vector<StoredBeastSnapshot> beasts;
        std::optional<SqliteBeastSnapshotRepository::SelectionRecord> selection;
        std::vector<StoredVaultBeast> vault_beasts;
        bool operator==(const Snapshot&) const=default;
    };
    struct Request {Snapshot expected;RecoveredBankItems::Request wire;};
    struct Plan {Snapshot after;bool source_vault{},destination_vault{};std::uint16_t source{},destination{};};
    using Prepare=std::function<void(const Plan&)>;
    using Check=std::function<void(const Plan&)>;
    using LookupWeapon=SqliteOwnedForeignBankRepository::LookupWeapon;
    using EligiblePlain=std::function<bool(std::uint16_t)>;
    SqliteBeastBankRepository(sqlite3*,SqliteOwnedForeignBankRepository&,SqliteBeastSnapshotRepository&,LookupWeapon,EligiblePlain);
    static std::string schema();
    static void install_schema(sqlite3*); // explicit empty extension only
    static void require_schema(sqlite3*);
    Snapshot load(std::uint64_t account,std::uint64_t character);
    Plan plan(const Request&) const;
    Plan commit(const std::string&,const Request&,const Prepare&,const Check&);
    void verify_snapshot_in_transaction(const Snapshot&);
    bool receipt_exists(const std::string&,bool own_only=false);
private:
    void validate(const Snapshot&) const;
    sqlite3* db_;SqliteOwnedForeignBankRepository& foreign_;
    SqliteBeastSnapshotRepository& beasts_;LookupWeapon weapon_;EligiblePlain plain_;
};
}
