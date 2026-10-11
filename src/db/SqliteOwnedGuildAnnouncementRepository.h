#pragma once
#include "db/SqliteOwnedGuildMembershipRepository.h"

namespace god2 {
// CUSTOM-0078 announcement persistence candidate. A wire edit flag, officer
// role, read-only governance snapshot or guild name is never write authority.
// Installing schema(), publishing to members and routing native79 remain
// explicit integration steps; this repository opens no gameplay route.
class SqliteOwnedGuildAnnouncementRepository {
public:
    using Membership=SqliteOwnedGuildMembershipRepository;
    struct Value {
        std::string text_utf8;
        std::uint64_t revision{};
        bool operator==(const Value&) const=default;
    };
    struct Snapshot {
        std::uint64_t guild_id{};
        std::optional<Value> value;
        bool operator==(const Snapshot&) const=default;
    };
    explicit SqliteOwnedGuildAnnouncementRepository(sqlite3* db);
    static std::string schema(); // Proposal only; no implicit migration/install.
    // Read-only data, not viewer or mutation permission. Caller must qualify a
    // current authenticated guild viewer before publishing native98.
    Snapshot load(std::uint64_t guild_id);
    // Complete founder, membership, governance and roster lease plus exact
    // announcement CAS. Both proof callbacks run under BEGIN IMMEDIATE. They
    // must validate immutable caller-owned world/session state and must not
    // control the SQL transaction. Empty text is a versioned tombstone.
    Snapshot save(const Membership::Leader& expected_leader,
                  const Snapshot& expected_announcement,
                  const std::string& text_utf8,const Membership::Proof& proof);
private:
    sqlite3* db_;
};
}
