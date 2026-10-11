#pragma once
#include "game/Character.h"
#include <optional>
#include <vector>
namespace god2 {
class CharacterRepository {
public:
    virtual ~CharacterRepository() = default;
    // create assigns id and created_at; save preserves both and account ownership.
    virtual Character create(const Character& character) = 0;
    virtual std::optional<Character> find_by_id(std::uint64_t id) = 0;
    virtual std::vector<Character> list_for_account(std::uint64_t account_id) = 0;
    virtual void save(const Character& character) = 0;
};
}
