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
    enum class ReferentialAction {Restrict,NoAction,Cascade,SetNull};
    struct ForeignKey {
        std::string name;
        std::vector<std::size_t> columns;
        std::string referenced_table;
        std::vector<std::size_t> referenced_columns;
        // Deliberately no SET DEFAULT, MATCH FULL or deferred constraint model:
        // they cannot silently map to immediate InnoDB MATCH SIMPLE behavior.
        ReferentialAction on_delete=ReferentialAction::NoAction;
        ReferentialAction on_update=ReferentialAction::NoAction;
    };
    struct Table {
        std::string name,comment_zh;
        std::vector<Column> columns;
        std::vector<std::size_t> primary_key;
        std::vector<Key> unique_keys;
        // Explicit nonunique supporting indexes. FK columns must be a leading
        // index tuple; never rely on implicit indexes with unaccounted limits.
        std::vector<Key> indexes;
        std::vector<ForeignKey> foreign_keys;
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
        std::uint64_t foreign_keys=0;
        bool declared_foreign_key_rows_validated=false;
    };
    // MySQL8.0.17+ target: no-pad binary text collation, UTF8/binary hex literals,
    // full-width integer decimals, mandatory readable metadata, no DROP/REPLACE.
    // Supports declared PK/UNIQUE, full nonunique indexes and immediate typed
    // foreign keys with complete unique parent keys. All declared references
    // and non-NULL child tuples are checked before any output. Cycles may load
    // because FKs are added after all data, with target checks explicitly ON.
    // This is a target model, not an arbitrary SQLite constraint translator:
    // CHECK/partial index/trigger/default/deferred mappings still need an audit.
    // DDL/ADD failure can leave a partial target; no atomic import is claimed.
    // Requires a fresh empty target. DDL is not transactional in MySQL.
    // Own all input before invoking arbitrary output stream callbacks. No live
    // DB or source authority follows; the caller supplies one complete image.
    static Report write_snapshot(Schema,std::vector<TableRows>,std::ostream&);
    MySql80ExportFormat()=delete;
};
}
