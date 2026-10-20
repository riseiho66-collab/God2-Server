#pragma once
#include "db/SqliteRecoveredCharacterRepository.h"
#include <array>
#include <functional>
#include <utility>

namespace god2 {
// CUSTOM-0065: per-character scalar bank items. Original account scope,
// equipment/instance policy and stacking rules remain unrecovered. Callers
// must qualify live banker access and scalar MED02 eligibility before commit.
class SqliteBankItemsRepository {
public:
    using BankSlot=StoredInventorySlot;
    static constexpr std::size_t bag_size=30,vault_size=300,page_size=50,page_count=6;
    // Custom empty-cell sentinel, never an item grant or native source claim.
    static constexpr const char* empty_source_sha256=
        "0000000000000000000000000000000000000000000000000000000000000000";
    struct Snapshot {
        std::uint64_t account{},character{};
        std::array<StoredInventorySlot,bag_size> bag;
        std::array<BankSlot,vault_size> vault;
        bool operator==(const Snapshot&) const=default;
    };
    enum class Operation : std::uint8_t { Deposit=0x63,Withdraw=0x64,Move=0x65 };
    struct Request {
        Snapshot expected;
        Operation operation{};
        std::uint8_t page{},source{},destination{},quantity{};
    };
    // Capture immutable owner evidence before reply preparation; both checks
    // run in the same mutation transaction, after BEGIN and before COMMIT.
    struct CommitProof {
        std::function<void()> before_write,after_write;
        // Pure no-SQL revocation check after ALL verification, before COMMIT.
        // Independent of paired owner proofs; cannot grant new eligibility.
        std::function<void()> current;
    };
    using PrepareProof=std::function<CommitProof(const Snapshot&,const Snapshot&)>;
    explicit SqliteBankItemsRepository(sqlite3* db,PrepareProof proof={}):db_(db),proof_(std::move(proof)) {}
    void install_schema();
    // Explicit qualified-bank-open allocation only. Returns300 on new vault,
    // zero for an existing complete vault. Partial/invalid vaults reject;
    // existing values are never upgraded, reset or supplemented.
    std::size_t provision_empty(std::uint64_t account,std::uint64_t character,const std::function<void()>& current={});
    // Borrowed read only; no DDL or automatic provisioning.
    Snapshot load(std::uint64_t account,std::uint64_t character);
    // Deposit/withdraw require an empty destination and permit partial stacks.
    // Native65's trailing1 is a control marker, not a split quantity: move the
    // whole cell or exchange two occupied cells without merging. Item/count/
    // source travel together; each physical position increments its own revision.
    // Callers must qualify both occupied cells; special slots remain excluded.
    static Snapshot plan(const Request& request);
    // Complete owned330-slot CAS, pending-battle guard, two physical revisions,
    // unique server receipt and full actual readback before atomic COMMIT.
    CommitProof prepare_proof(const Snapshot& before,const Snapshot& after,const PrepareProof& override_factory={}) const;
    Snapshot commit(const std::string& server_receipt,const Request& request,const std::optional<CommitProof>& prepared=std::nullopt);
private:
    sqlite3* db_;
    PrepareProof proof_;
};
}
