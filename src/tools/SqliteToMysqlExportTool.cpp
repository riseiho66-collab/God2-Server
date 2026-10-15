#include "tools/SqliteToMysqlExportTool.h"
#include "db/DbTypes.h"
#include <utility>
namespace god2 {
void SqliteToMysqlExportTool::export_sql(Database&,const std::filesystem::path&) {
    throw UnsupportedDatabaseError("Complete SQLite-to-MySQL8 export requires an audited read snapshot and all installed schema/constraint mappings; no source file or destination was opened");
}
MySql80ExportFormat::Report SqliteToMysqlExportTool::write_mysql80_snapshot(
        MySql80ExportFormat::Schema schema,std::vector<MySql80ExportFormat::TableRows> rows,
        std::ostream& output) {
    return MySql80ExportFormat::write_snapshot(std::move(schema),std::move(rows),output);
}
}
