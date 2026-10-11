#pragma once
#include "protocol/RecoveredRoleAuxiliary.h"
#include <optional>
#include <string>
struct sqlite3;
namespace god2 {
struct RoleAuxiliarySnapshot {
    RecoveredRoleAuxiliary::Logical logical;
    std::uint64_t revision;
    std::string origin,provenance;
    bool operator==(const RoleAuxiliarySnapshot&) const = default;
};
// CUSTOM-0045 stores/replays already-owned raw after-state, never derives
// equipment attack/defense, grants stats or treats this as a combat formula.
class SqliteRoleAuxiliaryRepository {
    sqlite3* db_;
public:
    explicit SqliteRoleAuxiliaryRepository(sqlite3* db);
    // Backend identity only. Existing old-build schema/rows/writes stay unchanged.
    bool uses_connection(const sqlite3* db) const noexcept {return db_==db;}
    std::optional<RoleAuxiliarySnapshot> load(std::uint64_t account,std::uint64_t character);
    RoleAuxiliarySnapshot save(std::uint64_t account,std::uint64_t character,
        std::optional<std::uint64_t> expected_revision,const RecoveredRoleAuxiliary::Logical& raw,
        std::string origin,std::string provenance);
};
}
