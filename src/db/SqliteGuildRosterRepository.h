#pragma once
#include "db/SqliteGuildRepository.h"
#include "db/RecoveredCharacterRepository.h"
#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>
struct sqlite3;

namespace god2 {
struct GuildRosterMember {
    std::uint64_t character_id=0,account_id=0,membership_revision=0;
    std::uint8_t slot=0;
    std::array<std::uint8_t,40> profile{};
    std::vector<std::uint8_t> name_bytes;
    std::uint16_t name_codepage=0;
    std::string name_utf8;
    std::optional<CharacterRoleSnapshot> role;
    bool operator==(const GuildRosterMember&) const=default;
};
struct StoredGuildRoster {
    std::uint64_t requester_account=0,requester_character=0;
    StoredGuildMembership membership;
    std::vector<GuildRosterMember> members;
    bool operator==(const StoredGuildRoster&) const=default;
};

// CUSTOM-0076: read-only owned guild audience snapshot. This reader invents no
// rank, leader, online status, economy or client action authorization. Retain
// complete equality tokens: a character deletion/name/level change need not
// increment the frozen CUSTOM-0075 guild generation.
class SqliteGuildRosterRepository {
    sqlite3* db_;
public:
    explicit SqliteGuildRosterRepository(sqlite3* db);
    // Independent deferred READ transaction; do not call inside another SQL
    // transaction. Owned non-member returns nullopt, foreign/malformed throws.
    std::optional<StoredGuildRoster> load(std::uint64_t account,std::uint64_t character);
};
}
