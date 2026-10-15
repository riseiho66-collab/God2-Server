#pragma once
#include "db/MySql80ExportFormat.h"
#include <filesystem>
#include <iosfwd>
namespace god2 {
class Database;
class SqliteToMysqlExportTool {
public:
    // Full SQLite export still requires a verified same-transaction reader and
    // complete schema/constraint mapping. Never initialize/migrate as an opener.
    static void export_sql(Database& source,const std::filesystem::path& destination);
    // Concrete typed MySQL8.0.17+ formatting of one privately owned caller image.
    // This stream API creates no files and certifies neither SQLite provenance
    // nor a real target import. The caller must stage output before publication.
    static MySql80ExportFormat::Report write_mysql80_snapshot(
        MySql80ExportFormat::Schema,std::vector<MySql80ExportFormat::TableRows>,std::ostream&);
};
}
