#pragma once
#include "db/SqliteRecoveredCharacterRepository.h"
#include "game/ExtendedCoinAmount.h"
#include <array>
#include <functional>
#include <utility>
#include <string>
#include <vector>

namespace god2 {
// CUSTOM-0063: isolated transactional settlement, not yet a formal UI route.
// Caller must establish two live consenting leases, native item eligibility,
// scene/readiness and prepare every client projection before commit.
class SqliteTradeRepository {
public:
    struct Wallet {
        // CUSTOM-0088: exact shared amount; legacy native wire is separate.
        std::uint64_t amount{},revision{};
        bool operator==(const Wallet&) const=default;
    };
    struct Snapshot {
        std::uint64_t account{},character{};
        Wallet wallet;
        std::array<StoredInventorySlot,30> bag;
        bool operator==(const Snapshot&) const=default;
    };
    struct Offer {std::uint8_t slot{},quantity{};};
    struct Side {Snapshot expected;std::vector<Offer> items;std::uint64_t money{};};
    struct Settlement {std::array<Snapshot,2> sides;};
    // Capture immutable owner evidence before reply preparation; both checks
    // run in the same mutation transaction, after BEGIN and before COMMIT.
    struct CommitProof {
        std::function<void()> before_write,after_write;
        // Pure no-SQL/provider observation immediately before COMMIT, after
        // all original readback/proof callbacks. Independent of paired proofs.
        std::function<bool()> current;
    };
    using PrepareProof=std::function<CommitProof(const std::array<Snapshot,2>&,const Settlement&)>;
    explicit SqliteTradeRepository(sqlite3* db,PrepareProof proof={}):db_(db),proof_(std::move(proof)) {}
    // Explicit LEGACY installation only; its historical CHECK is unchanged.
    // An existing database requires a separately qualified reversible upgrade
    // before amounts above its DWORD constraint can be persisted.
    // Constructor and load never create rows.
    void install_schema();
    // Custom new-wallet default0. Existing amounts never replaced/reset.
    Wallet provision_wallet(std::uint64_t account,std::uint64_t character);
    std::optional<Wallet> load_wallet(std::uint64_t account,std::uint64_t character);
    Snapshot load(std::uint64_t account,std::uint64_t character);
    // Pure plan with capacity/version/quantity/overflow checks; no grants or
    // stack merges. Transfer item provenance unchanged into empty bag slots.
    static Settlement plan(const std::array<Side,2>& sides);
    // BEGIN IMMEDIATE rechecks both complete snapshots, ownership, pending
    // battles and unique receipt. Failure rolls back both players together.
    CommitProof prepare_proof(const std::array<Snapshot,2>& before,const Settlement& after,const PrepareProof& override_factory={}) const;
    Settlement commit(const std::string& receipt,const std::array<Side,2>& sides,const std::optional<CommitProof>& prepared=std::nullopt);
private:
    sqlite3* db_;
    PrepareProof proof_;
};
}
