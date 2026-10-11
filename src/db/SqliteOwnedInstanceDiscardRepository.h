#pragma once
#include "db/NativeWeaponCatalog.h"
#include "db/SqliteArmorSlotRepository.h"
#include <functional>

namespace god2 {
// CUSTOM-0071 destruction of one qualified, already-owned typed instance.
// Native27 has no generation/nonce. This does not recover bind/drop policy.
class SqliteOwnedInstanceDiscardRepository {
public:
    using QualifyArmor=SqliteArmorSlotRepository::QualifyArmor;
    using QualifyInstance=SqliteArmorSlotRepository::QualifyInstance;
    using LookupWeapon=std::function<std::optional<NativeWeaponRecord>(std::uint16_t)>;
    // Peripheral typed rows observe existing characters, economic state,
    // banks, battles and older ledgers without requiring or provisioning them.
    // The new discard ledger is separately captured before prepare and guarded
    // throughout commit. load-to-commit ledger changes are not snapshot CAS.
    struct Snapshot {ArmorSnapshot bag;std::string peripheral;bool operator==(const Snapshot&) const=default;};
    struct Request {Snapshot expected;std::uint16_t item{};std::uint8_t source{},quantity{};};
    enum class Kind : std::uint8_t {Armor=1,Weapon=2,Gem=3};
    struct Plan {
        Snapshot after;std::uint8_t slot{};Kind kind{};
        std::array<std::uint8_t,20> removed20{};
        std::string origin,provenance,source_sha256,client_sha256,instance_design_id;
        bool operator==(const Plan&) const=default;
    };
    using Prepare=std::function<void(const Plan&)>;
    using Check=std::function<void(const Plan&)>;
    using PreparePlan=Prepare;using CheckPlan=Check;
    static constexpr const char* design_id="CUSTOM-0071";
    static std::string schema(); // Explicit migration only. No constructor/load DDL or grants.
    // Borrowed armor reader must share this actual writer SQLite connection.
    SqliteOwnedInstanceDiscardRepository(sqlite3*,SqliteArmorSlotRepository&,QualifyArmor,QualifyInstance,LookupWeapon);
    Snapshot load(std::uint64_t account,std::uint64_t character);
    Plan plan(const Request&) const;
    Plan commit(const std::string& receipt,const Request&,const Prepare&,const Check& check={});
    bool receipt_exists(const std::string&);
private:
    void validate(const ArmorSnapshot&) const;
    void no_battle(std::uint64_t character);
    sqlite3* db_;SqliteArmorSlotRepository& armor_reader_;
    QualifyArmor armor_;QualifyInstance armor_instance_;LookupWeapon weapon_;
};
}
