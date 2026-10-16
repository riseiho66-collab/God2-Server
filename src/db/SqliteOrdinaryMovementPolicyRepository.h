#pragma once
#include "db/OrdinaryMovementPolicyRepository.h"
#include <sqlite3.h>
#include <atomic>
#include <thread>

namespace god2 {
class SqliteOrdinaryMovementPolicyRepository final : public OrdinaryMovementPolicyRepository {
public:
    // Borrow the actual Database connection. Construction performs no SQL.
    explicit SqliteOrdinaryMovementPolicyRepository(sqlite3*);
    ~SqliteOrdinaryMovementPolicyRepository() override {revoke_lifetime();}
    bool uses_connection(sqlite3* actual) const noexcept {return actual&&actual==db_;}
    Snapshot load(std::size_t max_profiles) override;
    static std::string schema();
    static std::string mysql80_schema();
    // Own one validated table snapshot, then return fresh-target DDL + data.
    // No stdout/file/DB write or full-database/atomic-publish claim.
    std::string mysql80_snapshot(std::size_t max_profiles);
    // Explicit fresh installation only: no data/defaults/migration/version bump.
    static void install_schema(sqlite3*);
private:
    struct Operation;
    struct ReadScope;
    sqlite3* const db_;
    std::thread::id thread_;
    std::atomic<bool> busy_{false},poisoned_{false};
};
}
