#pragma once
#include "game/Account.h"
#include <optional>
namespace god2 {
class AccountRepository {
public:
    virtual ~AccountRepository() = default;
    virtual Account create(const std::string& username, const std::string& password_hash) = 0;
    virtual std::optional<Account> find_by_username(const std::string& username) = 0;
    virtual std::optional<Account> find_by_id(std::uint64_t id) = 0;
};
}
