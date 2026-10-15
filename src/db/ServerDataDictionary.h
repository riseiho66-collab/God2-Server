#pragma once
#include <cstddef>
#include <span>
#include <string_view>

namespace god2 {
// Descriptive metadata from compiled source declarations, NOT an inventory of
// an opened database, a DDL translator, field-type validator or permission.
// Keep physical names/raw bytes unchanged. Missing metadata remains absent.
class ServerDataDictionary final {
public:
    enum class Storage {Authoritative,NativeSource,NativeDelivery,AuditHistory,SchemaMetadata,Diagnostic,MigrationTransient};
    enum class Domain {Account,Character,Inventory,Companion,Battle,Pk,Guild,Quest,World,NativeCatalog,Migration};
    enum class Installation {VersionedMigration,ConditionalMigration,ExplicitExtension,TransientMigration};
    enum class ValueKind {Integer,Text,Binary};
    struct SourceLocation {std::string_view path;std::size_t line;};
    struct Column {std::string_view name,title_zh,purpose_zh;ValueKind kind;};
    struct Table {
        std::string_view name,title_zh,purpose_zh;
        Storage storage;
        Domain domain;
        Installation installation;
        std::span<const SourceLocation> sources;
        // Deliberately partial: only positively identified field semantics.
        // An unknown field returns nullptr; a caller must never infer its type
        // or silently drop its data/constraints from this descriptive absence.
        std::span<const Column> columns;
    };
    static std::span<const Table> tables() noexcept;
    static const Table* find_table(std::string_view exact_name) noexcept;
    static const Column* find_column(std::string_view table,std::string_view column) noexcept;
    ServerDataDictionary()=delete;
};
}
