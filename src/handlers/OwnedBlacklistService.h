#pragma once
#include "db/SqliteOwnedBlacklistRepository.h"
#include "protocol/TaiwanNativeBlacklist.h"
#include <optional>
#include <vector>
namespace god2 {
// Actual owned mutation/replay, not a chat filter or native permission policy.
// Application supplies its live authenticated ready-world owner at each call.
class OwnedBlacklistService final {
public:
    explicit OwnedBlacklistService(SqliteOwnedBlacklistRepository& repository):repository_(repository) {}
    std::optional<std::vector<std::uint8_t>> handle(std::uint64_t account,std::uint64_t character,
        const TaiwanNativeBlacklist::Request&,SqliteOwnedBlacklistRepository::Current);
    std::optional<SqliteOwnedBlacklistRepository::CommittedChange> handle_committed(
        std::uint64_t account,std::uint64_t character,const TaiwanNativeBlacklist::Request&,
        SqliteOwnedBlacklistRepository::Current);
    struct Replay {std::vector<std::uint8_t> logical;std::uint32_t last_row;bool done;};
    SqliteOwnedBlacklistRepository::Snapshot observe(std::uint64_t account,std::uint64_t character,SqliteOwnedBlacklistRepository::Current);
    static Replay restore(const SqliteOwnedBlacklistRepository::Snapshot&,std::uint32_t after_row,bool active_phase);
private:
    SqliteOwnedBlacklistRepository& repository_;
};
}
