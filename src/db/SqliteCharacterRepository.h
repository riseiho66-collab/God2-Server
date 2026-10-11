#pragma once
#include "db/CharacterRepository.h"
struct sqlite3;
namespace god2 {
class SqliteCharacterRepository final : public CharacterRepository {
public:
    explicit SqliteCharacterRepository(sqlite3* db) : db_(db) {}
    Character create(const Character& character) override;
    std::optional<Character> find_by_id(std::uint64_t id) override;
    std::vector<Character> list_for_account(std::uint64_t account_id) override;
    void save(const Character& character) override;
private:
    sqlite3* db_;
};
}
