#pragma once
#include "db/SqliteGuildRepository.h"
#include <cstdint>
struct sqlite3;

namespace god2 {
// CUSTOM-0077: authenticated self-leave storage operation. The caller must
// resolve account/character from the current owned session and supply the
// complete observed membership. It grants no officer, leader or other-member
// mutation authority. Existing CUSTOM-0075 storage provenance is preserved.
class SqliteOwnedGuildLeaveRepository {
    sqlite3* db_;
public:
    explicit SqliteOwnedGuildLeaveRepository(sqlite3* db);
    void leave(std::uint64_t account, std::uint64_t character,
               const StoredGuildMembership& expected);
};
}
