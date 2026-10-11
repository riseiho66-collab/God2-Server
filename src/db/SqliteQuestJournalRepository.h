#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <string>
struct sqlite3;
namespace god2 {
// CUSTOM-0041: owned display snapshot only. Packed high WORD is a native text
// selector, never a quest-completion, grant, reward or transition authority.
struct QuestJournalSnapshot {
    std::array<std::uint32_t,15> values{};
    std::uint64_t revision{};
    std::string origin,provenance;
    bool operator==(const QuestJournalSnapshot&) const = default;
};
class SqliteQuestJournalRepository final {
public:
    explicit SqliteQuestJournalRepository(sqlite3* db);
    std::optional<QuestJournalSnapshot> load(std::uint64_t account,std::uint64_t character);
    // Absent expected_revision means insert only. Every successful save,
    // including identical values, advances revision; stale writes roll back.
    QuestJournalSnapshot save(std::uint64_t account,std::uint64_t character,
        std::optional<std::uint64_t> expected_revision,
        std::array<std::uint32_t,15> values,std::string origin,std::string provenance);
private:
    std::optional<QuestJournalSnapshot> load_in_transaction(std::uint64_t account,
        std::uint64_t character,const std::array<std::uint16_t,418>& counts);
    std::array<std::uint16_t,418> description_counts();
    sqlite3* db_;
};
}
