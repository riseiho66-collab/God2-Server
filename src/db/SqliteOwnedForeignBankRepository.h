#pragma once
#include "db/NativeWeaponCatalog.h"
#include "db/SqliteOwnedArmorBankRepository.h"
#include <functional>

namespace god2 {
enum class OwnedBankForeignKind : std::uint8_t {Weapon=1,Gem=8};
struct StoredVaultForeign {
    std::uint16_t slot{};
    OwnedBankForeignKind kind{};
    std::array<std::uint8_t,20> logical20{};
    std::uint64_t revision{};
    std::string origin,provenance,source_sha256,client_sha256,instance_design_id;
    // Qualified definition identity, not invented instance attributes.
    std::string source_family,parsed_sha256;
    bool operator==(const StoredVaultForeign&) const=default;
};
// CUSTOM-0068 foreign custody only. Existing source pins/designs remain intact.
// No grant/capacity/DDL-on-load, equipment transfer or new native admission.
class SqliteOwnedForeignBankRepository {
public:
    using QualifyArmor=SqliteArmorSlotRepository::QualifyArmor;
    using QualifyInstance=SqliteArmorSlotRepository::QualifyInstance;
    using LookupWeapon=std::function<std::optional<NativeWeaponRecord>(std::uint16_t)>;
    using Operation=SqliteBankItemsRepository::Operation;
    static constexpr const char* design_id="CUSTOM-0068";
    struct Snapshot {SqliteOwnedArmorBankRepository::Snapshot base;std::vector<StoredVaultForeign> foreign;bool operator==(const Snapshot&) const=default;};
    struct Request {Snapshot expected;Operation operation{};std::uint8_t page{},source{},destination{},quantity{};};
    struct Plan {Snapshot after;bool source_vault{},destination_vault{};std::uint16_t source{},destination{};};
    using Prepare=std::function<void(const Plan&)>;
    using Check=std::function<void(const Plan&)>;
    enum class ReceiptLedger {Any,Foreign,Armor,Plain};
    static std::string schema();
    SqliteOwnedForeignBankRepository(sqlite3*,QualifyArmor,QualifyInstance,LookupWeapon);
    bool shares_connection(sqlite3* db) const noexcept{return db_==db;}
    Snapshot load(std::uint64_t account,std::uint64_t character);
    Plan plan(const Request&) const;
    Plan commit(const std::string& receipt,const Request&,const Prepare&,const Check& check={});
    bool receipt_exists(const std::string&,ReceiptLedger ledger=ReceiptLedger::Any);
    void verify_snapshot_in_transaction(const Snapshot&);
private:
    void validate(const Snapshot&) const;
    void qualify(const StoredVaultForeign&,std::uint16_t item) const;
    std::optional<StoredVaultForeign> instance(const Snapshot&,bool vault,std::uint16_t slot) const;
    sqlite3* db_;QualifyArmor armor_;QualifyInstance armor_instance_;LookupWeapon weapon_;
};
}
