#pragma once
#include "cn/assets/CnNativeSkillBookBindings.h"
#include "db/NativeSkillBookSourceCatalog.h"

namespace god2::cn {
// Exact pinned CN raw SKB source on the SAME shared SQLite connection. This
// opt-in importer is never called by migration/login/Application. It does not
// grant skills, identify common items, debit books or synthesize a396 image.
class CnNativeSkillBookSourceImport final {
public:
    enum class Result { Inserted, AlreadyPresent };
    static NativeSkillSource expected_source();
    // Explicit additive shared schema only; requires existing source schema
    // and foreign keys. An existing incompatible table is never altered.
    static void install_schema(sqlite3*);
    static void require_schema(sqlite3*);
    static Result import_actual_source(sqlite3*,std::shared_ptr<const CnNativeSkillBookBindings>);
};
}
