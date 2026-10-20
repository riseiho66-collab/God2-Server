#pragma once
#include "handlers/SynchronousCallbackFence.h"
#include <type_traits>
#include <utility>
#include "db/SqliteBankRepository.h"
#include "protocol/RecoveredBank.h"
#include <chrono>
#include <functional>
#include <map>
namespace god2 {
// CUSTOM-0064: serialized live bank leases, not native server-policy recovery.
class RecoveredBankService {
public:
    using Clock=std::chrono::steady_clock;
    struct Peer {
        std::uint64_t session{},account{},character{};
        std::uint16_t area{},scene{},x{},y{};
        bool ready{};
    };
    using Lookup=std::function<std::optional<Peer>(std::uint64_t)>;
    using Access=std::function<bool(const Peer&,std::uint16_t)>;
    using Receipt=std::function<std::string()>;
    struct Result {std::vector<std::uint8_t> logical;bool committed{},rejected{};};
    RecoveredBankService(SqliteBankRepository& repository,Lookup lookup,Access access,Receipt receipt)
        :repo_(repository),lookup_(std::move(lookup)),access_(std::move(access)),receipt_(std::move(receipt)){}
    // No context or bank provision unless the caller's authoritative NPC access
    // predicate accepts. Unknown NPC37 continues to its existing route.
    std::optional<std::vector<std::uint8_t>> open(std::uint64_t session,std::uint16_t target,Clock::time_point now);
    Result handle(std::uint64_t session,std::span<const RecoveredBank::Request> requests,Clock::time_point now);
    // CUSTOM-0065 composes the already qualified money lease for item banking.
    // Access query grants no money or NPC role. A callback failure retires the lease.
    bool permits_items(std::uint64_t session,std::uint16_t target,Clock::time_point now);
    void renew_items(std::uint64_t session,Clock::time_point now);
    void disconnect(std::uint64_t session){callbacks_.invalidate_if_running();contexts_.erase(session);}
private:
    struct Context {Peer peer;std::uint16_t target;SqliteBankRepository::Snapshot expected;Clock::time_point expires;};
    static std::vector<std::uint8_t> synchronization(const SqliteBankRepository::Snapshot& snapshot);
    SqliteBankRepository& repo_;
    Lookup lookup_;
    Access access_;
    Receipt receipt_;
    std::map<std::uint64_t,Context> contexts_;
    template<class F,class... Args>
    auto invoke_adapter(const F& function,Args&&... args) const {
        callbacks_.require_current();
        if constexpr(std::is_void_v<std::invoke_result_t<const F&,Args...>>) {
            function(std::forward<Args>(args)...);callbacks_.require_current();
        } else {
            auto result=function(std::forward<Args>(args)...);
            callbacks_.require_current();return result;
        }
    }
    SynchronousCallbackFence callbacks_;

};
}
