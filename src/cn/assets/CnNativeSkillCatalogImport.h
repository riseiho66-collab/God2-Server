#pragma once
#include "cn/assets/CnNativeSkillCatalog.h"
#include <memory>

struct sqlite3;

namespace god2::cn {
// Explicit definition materialization into the existing shared tables. This
// operation is never called by login, a client request or default migration.
// It grants no skill, changes no character and selects no common skill identity.
class CnNativeSkillCatalogImport final {
public:
    enum class Result {Inserted,AlreadyPresent};
    // Caller owns the migrated connection on its game/database owner. Require
    // no enclosing transaction: success means this whole import committed.
    // Only the qualified immutable pinned CN provider can supply row bytes.
    // Exact existing source+453 rows is an idempotent success; partial,
    // conflicting or orphan data throws DatabaseError without replacement.
    // Caller retains its existing NativeSkillCatalog reader for later binding.
    static Result import_actual_source(
        sqlite3*,std::shared_ptr<const god2cn::CnNativeSkillCatalog>);
};
}
