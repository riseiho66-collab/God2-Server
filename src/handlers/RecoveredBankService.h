#pragma once
#include "handlers/SynchronousCallbackFence.h"
#include <type_traits>
#include <utility>
#include "db/SqliteBankRepository.h"
#include "protocol/RecoveredBank.h"
#include <chrono>
#include <functional>
#include <map>
#include <memory>
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
    // CUSTOM-0064: one immutable lease identity shared by money and items.
    // Copies cannot keep a retired context valid or resurrect it after reopen.
    class LeaseSource {
    public:
        LeaseSource()=default;
        bool current() const noexcept {
            const auto state=state_.lock();
            return state && state->valid && Clock::now()<state->expires;
        }
        bool owns(std::uint64_t session,std::uint64_t account,std::uint64_t character,std::uint16_t target) const noexcept {
            const auto state=state_.lock();
            return state && current() && state->target==target && state->peer.session==session &&
                state->peer.account==account && state->peer.character==character;
        }
        bool matches(const Peer& peer,std::uint16_t target) const noexcept {
            const auto state=state_.lock();
            return state && current() && state->target==target &&
                state->peer.session==peer.session && state->peer.account==peer.account &&
                state->peer.character==peer.character && state->peer.area==peer.area && state->peer.scene==peer.scene;
        }
        void require_current() const {if(!current())throw DatabaseError("Bank lease source retired or expired");}
    private:
        friend class RecoveredBankService;
        struct State {Peer peer;std::uint16_t target;Clock::time_point expires;bool valid=true;};
        explicit LeaseSource(const std::shared_ptr<State>& state):state_(state){}
        std::weak_ptr<const State> state_;
    };
    using CaptureLease=std::function<LeaseSource(std::uint64_t,std::uint16_t,Clock::time_point)>;
    LeaseSource capture_lease(std::uint64_t session,std::uint16_t target,Clock::time_point now);
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
    void disconnect(std::uint64_t session){callbacks_.invalidate_if_running();retire_context(session);}
private:
    struct Context {Peer peer;std::uint16_t target;SqliteBankRepository::Snapshot expected;Clock::time_point expires;std::shared_ptr<LeaseSource::State> lease;};
    void retire_context(std::uint64_t session) noexcept;
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
