#pragma once
#include "db/SqliteOwnedForeignBankRepository.h"

namespace god2 {
// CUSTOM-0070 explicit custody policy, not proof of original server admission.
// Only complete occupied vault cells (or an empty owned destination) on pages
// 0..2/local2..49; neither construction nor reading grants rows/capacity.
class SqliteOwnedMixedBankRepository {
public:
    using Snapshot=SqliteOwnedForeignBankRepository::Snapshot;
    using EligiblePlain=std::function<bool(std::uint16_t)>;
    // quantity is the authoritative whole source count. Native65 wire byte
    // remains marker1; the service resolves that marker before calling here.
    struct Request {Snapshot expected;std::uint8_t page{},source{},destination{},quantity{};};
    struct Plan {Snapshot after;std::uint16_t source{},destination{};bool operator==(const Plan&) const=default;};
    using Prepare=std::function<void(const Plan&)>;
    using Check=std::function<void(const Plan&)>;
    static constexpr const char* design_id="CUSTOM-0070";
    static std::string schema();
    // foreign must use this same SQLite connection and complete native
    // qualifiers. plan reads a qualified before snapshot without writing.
    SqliteOwnedMixedBankRepository(sqlite3*,SqliteOwnedForeignBankRepository&,EligiblePlain);
    Snapshot load(std::uint64_t account,std::uint64_t character);
    Plan plan(const Request&) const;
    Plan commit(const std::string& receipt,const Request&,const Prepare&,const Check& check={},const std::function<void()>& current={});
    enum class ReceiptLedger {Any,Mixed,Foreign,Armor,Plain};
    bool receipt_exists(const std::string&,ReceiptLedger ledger=ReceiptLedger::Any);
    void verify_snapshot_in_transaction(const Snapshot&);
private:
    sqlite3* db_;SqliteOwnedForeignBankRepository& foreign_;EligiblePlain plain_;
};
}
