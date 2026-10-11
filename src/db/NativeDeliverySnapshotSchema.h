#pragma once
#include "db/Migration.h"
struct sqlite3;

namespace god2 {
// Explicit common delivery storage only. No native records, rights, migration
// promotion or login activation. Call on the same migrated Database owner.
class NativeDeliverySnapshotSchema final {
public:
    // Standalone own transaction; missing all four owned objects may be created.
    // Partial/unknown schemas fail without repair, ALTER, DROP or native data.
    static void install(sqlite3*,const std::vector<Migration>& actual_migrations);
    // Standalone consistent qualification only. Never installs on a read path
    // and never borrows a caller transaction or deferred foreign-key state.
    static void require_existing(sqlite3*,const std::vector<Migration>& actual_migrations);
};
}
