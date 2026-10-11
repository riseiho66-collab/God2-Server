#include "tools/SqliteToMysqlExportTool.h"
#include "db/DbTypes.h"
namespace god2 {
void SqliteToMysqlExportTool::export_sql(Database&, const std::filesystem::path&) {
    throw UnsupportedDatabaseError("SQLite to MySQL/MariaDB export is not implemented");
}
}
