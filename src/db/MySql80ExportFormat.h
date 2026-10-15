#pragma once
#include <cstdint>
#include <iosfwd>
#include <optional>
#include <span>
#include <string>
#include <variant>
#include <vector>
namespace god2 {
// Typed target SQL formatting only. Does NOT read a SQLite database, translate
// arbitrary constraints, certify a snapshot or implement the MySQL backend.
class MySql80ExportFormat final {
public:
    enum class Kind {Signed64,Unsigned64,Utf8Text,Binary};
    using Value=std::variant<std::monostate,std::int64_t,std::uint64_t,std::string,std::vector<std::uint8_t>>;
    struct Column {
        std::string name;
        Kind kind;
        bool nullable=false;
        // Explicit reviewed target width; never inferred from current max(data).
        // Text: characters; binary: bytes. Absent maps to LONGTEXT/LONGBLOB.
        std::optional<std::uint32_t> width;
        std::string comment_zh;
    };
    struct Key {std::string name;std::vector<std::size_t> columns;};
    struct Table {
        std::string name,comment_zh;
        std::vector<Column> columns;
        std::vector<std::size_t> primary_key;
        std::vector<Key> unique_keys;
    };
    struct Schema {
        // Explicit target capability for this first reviewed format profile.
        std::uint32_t target_innodb_page_bytes;
        std::int64_t sqlite_source_version;
        std::string sqlite_source_schema_sha256;
        std::vector<Table> tables;
    };
    struct TableRows {std::string table;std::vector<std::vector<Value>> rows;};
    struct Report {
        std::uint64_t tables=0,rows=0;
        bool typed_snapshot_serialized=false;
        bool sqlite_source_snapshot_verified=false;
        bool import_verified=false;
    };
    // MySQL8.0.17+ target: no-pad binary text collation, UTF8/binary hex literals,
    // full-width integer decimals, mandatory readable metadata, no DROP/REPLACE.
    // Provided model supports only the declared PK/UNIQUE constraints; arbitrary
    // SQLite CHECK/FK/index/trigger/default mappings must be supplied by a future
    // complete audited schema adapter, never silently passed through this API.
    // Requires a fresh empty target. DDL is not transactional in MySQL.
    // Own all input before invoking arbitrary output stream callbacks. No live
    // DB or source authority follows; the caller supplies one complete image.
    static Report write_snapshot(Schema,std::vector<TableRows>,std::ostream&);
    MySql80ExportFormat()=delete;
};
}
