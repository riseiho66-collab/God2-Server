#pragma once
#include "protocol/RecoveredPlayerAppearanceUpdate.h"
#include <optional>
#include <string>
struct sqlite3;
namespace god2 {
struct StoredPlayerAppearance {
    std::uint64_t revision{};
    RecoveredPlayerAppearanceUpdate::Fields fields;
    RecoveredPlayerAppearanceUpdate::Components base_components{};
    std::string origin, provenance, client_sha256, design_id;
    bool operator==(const StoredPlayerAppearance&) const = default;
};
// CUSTOM-0047: stores an explicitly supplied owned ordinary-player DA snapshot.
// Does not derive an item-to-appearance mapping or grant an appearance.
class SqlitePlayerAppearanceRepository {
public:
    static constexpr const char* client_sha256 = "6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98";
    static constexpr const char* design_id = "CUSTOM-0047";
    static const char* schema() noexcept;
    explicit SqlitePlayerAppearanceRepository(sqlite3* db);
    // Read is allowed during a pending battle; mutation is not.
    std::optional<StoredPlayerAppearance> load(std::uint64_t account, std::uint64_t character);
    // nullopt revision means insert only; all existing saves require exact CAS.
    // An existing caller transaction is borrowed via a nested savepoint.
    StoredPlayerAppearance save(std::uint64_t account, std::uint64_t character,
        std::optional<std::uint64_t> expected_revision,
        const RecoveredPlayerAppearanceUpdate::Fields& fields,
        std::string origin, std::string provenance,
        std::optional<RecoveredPlayerAppearanceUpdate::Components> baseline = std::nullopt);
private:
    sqlite3* db_;
};
}
