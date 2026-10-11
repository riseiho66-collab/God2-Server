#pragma once
#include <filesystem>
namespace god2 {
class Database;
class SqliteToMysqlExportTool {
public:
    // Reserved for repository-based export with schema version and migration report.
    static void export_sql(Database& source, const std::filesystem::path& destination);
};
}
