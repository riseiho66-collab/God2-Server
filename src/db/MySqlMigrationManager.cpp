#include "db/MySqlMigrationManager.h"
#include "db/DbTypes.h"
namespace god2 {
void MySqlMigrationManager::migrate() {
    throw UnsupportedDatabaseError("MySQL/MariaDB migrations are not implemented");
}
}
