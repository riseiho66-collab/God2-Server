#pragma once
#include <cstdint>
#include <optional>
#include <string>
struct sqlite3;

namespace god2 {
struct StoredGuildMembership {
    std::uint64_t guild_id=0;
    std::string name_utf8;
    std::uint64_t guild_revision=0;
    std::uint64_t membership_revision=0;
    bool operator==(const StoredGuildMembership&) const=default;
};

// CUSTOM-0075: owned durable guild membership is an explicit server policy.
// Native family display/chat establishes wire bytes, not guild economics,
// creation permissions or original persistence. Admin APIs are maintenance
// operations only and must never be treated as client authorization.
class SqliteGuildRepository {
    sqlite3* db_;
public:
    explicit SqliteGuildRepository(sqlite3* db);
    static std::string schema();
    std::optional<StoredGuildMembership> load(std::uint64_t account,std::uint64_t character);
    std::uint64_t admin_create(const std::string& name_utf8);
    StoredGuildMembership admin_assign(std::uint64_t account,std::uint64_t character,
        std::uint64_t guild,std::optional<std::uint64_t> expected_revision);
    void admin_remove(std::uint64_t account,std::uint64_t character,std::uint64_t expected_revision);
};
}
