#pragma once
#include "db/SqliteArmorSlotRepository.h"
#include "db/SqliteBankItemsRepository.h"
#include <array>
#include <functional>
#include <string>
#include <vector>

namespace god2 {
// CUSTOM-0067: whole owned armor custody only. Neither acquisition/admission
// rules nor weapon/gem bank transfer are recovered or enabled here.
struct StoredVaultArmor {
    std::uint16_t slot{};
    std::array<std::uint8_t,20> logical20{};
    std::uint64_t revision{};
    std::string origin,provenance,source_sha256,client_sha256,instance_design_id;
    bool operator==(const StoredVaultArmor&) const=default;
};
class SqliteOwnedArmorBankRepository {
public:
    using QualifyArmor=SqliteArmorSlotRepository::QualifyArmor;
    using QualifyInstance=SqliteArmorSlotRepository::QualifyInstance;
    using Operation=SqliteBankItemsRepository::Operation;
    static constexpr const char* design_id="CUSTOM-0067";
    struct Snapshot {
        ArmorSnapshot bag;
        std::array<StoredInventorySlot,300> vault;
        std::vector<StoredVaultArmor> armor;
        bool operator==(const Snapshot&) const=default;
    };
    struct Request {Snapshot expected;Operation operation{};std::uint8_t page{},source{},destination{},quantity{};};
    struct Plan {Snapshot after;bool source_vault{},destination_vault{};std::uint16_t source{},destination{};};
    // Produce ALL response bytes before BEGIN. The callback receives an exact
    // planned full snapshot; it must not send replies before commit succeeds.
    using Prepare=std::function<void(const Plan&)>;
    // Optional additional owner evidence must be captured immutably outside
    // this call. Check runs before COMMIT, followed by another actual readback.
    using Check=std::function<void(const Plan&)>;
    // Requires explicit existing scalar bank capacity + three bag overlays.
    // Occupied-only vault metadata and receipts; no capacity/grant/DDL on read.
    static std::string schema();
    SqliteOwnedArmorBankRepository(sqlite3*,QualifyArmor,QualifyInstance);
    Snapshot load(std::uint64_t account,std::uint64_t character);
    enum class ReceiptLedger {Any,Armor,Plain};
    bool receipt_exists(const std::string& receipt,ReceiptLedger ledger=ReceiptLedger::Any);
    void verify_snapshot_in_transaction(const Snapshot& expected);
    Plan plan(const Request&) const;
    Plan commit(const std::string& receipt,const Request&,const Prepare&,const Check& check={});
private:
    void validate(const Snapshot&) const;
    sqlite3* db_;
    QualifyArmor qualify_;
    QualifyInstance instance_;
};
}
