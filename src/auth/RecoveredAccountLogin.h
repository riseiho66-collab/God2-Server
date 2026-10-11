#pragma once
#include "db/AccountRepository.h"
#include "protocol/RecoveredC2S0002.h"
#include <cstdint>
#include <asio.hpp>
#include <exception>
#include <functional>

namespace god2 {
// Repository access and async completions belong to the serial game executor.
// Owner must outlive outstanding completions. No protocol success is implied.
class RecoveredAccountLogin {
public:
    RecoveredAccountLogin(AccountRepository& accounts, bool allow_registration)
        : accounts_(accounts), allow_registration_(allow_registration) {}
    std::uint64_t authenticate(const RecoveredC2S0002::Parsed& request);
    // Read-only binding for explicit shared adapters; authentication unchanged.
    bool owns_repository(const AccountRepository& accounts) const noexcept {return &accounts_==&accounts;}
    using Completion=std::function<void(std::uint64_t,std::exception_ptr)>;
    void authenticate_async(const RecoveredC2S0002::Parsed&,asio::any_io_executor workers,
                            asio::any_io_executor game,Completion done);
private:
    struct Attempt { std::string identity,password; std::optional<Account> account; };
    std::optional<Attempt> prepare(const RecoveredC2S0002::Parsed&);
    unsigned pending_=0;
    AccountRepository& accounts_;
    bool allow_registration_;
};
}
