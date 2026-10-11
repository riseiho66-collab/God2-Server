#pragma once
#include "db/AccountRepository.h"
#include <asio.hpp>
#include <cstdint>
#include <functional>
#include <memory>
#include <string_view>
#include <thread>

namespace god2::cn {
enum class CredentialOutcome { Verified, NotRegistered, Rejected, Changed, Busy, InternalFailure };
// Issued only by the real verifier after its worker result and repository
// snapshot agree. The observer retains no raw password and weakly owns the
// verifier. Keep this token only through the suspended login publication;
// it is current-value continuity, not a durable credential revision/lease.
class VerifiedCredentialSource final {
public:
    bool current(std::uint32_t verified_account) const;
    VerifiedCredentialSource(const VerifiedCredentialSource&)=delete;
    VerifiedCredentialSource& operator=(const VerifiedCredentialSource&)=delete;
private:
    friend class SharedAccountVerifier;
    VerifiedCredentialSource(std::uint32_t,std::function<bool()>);
    const std::uint32_t account_;
    const std::thread::id thread_=std::this_thread::get_id();
    const std::function<bool()> current_;
};
struct CredentialResult {
    CredentialOutcome outcome=CredentialOutcome::InternalFailure;
    std::uint32_t account_id=0; // Nonzero only after shared repository verification.
    std::shared_ptr<const VerifiedCredentialSource> source;
};

// CN raw UI credentials -> the existing authoritative AccountRepository and
// PasswordHash format. Never opens god2-cn.db or fabricates a Taiwan packet.
// Same byte identity policy as RecoveredAccountLogin: exact first, ASCII-only
// lowercase alias second. This is shared account policy, not CN-native recovery.
// Read-only existing-account binding; account creation remains a separate route.
// Construction, calls, completion, destruction and repository share one thread.
class SharedAccountVerifier {
public:
    using Completion=std::function<void(CredentialResult)>;
    SharedAccountVerifier(AccountRepository&,asio::any_io_executor game,
                          std::size_t workers=2,std::size_t capacity=64);
    ~SharedAccountVerifier();
    SharedAccountVerifier(const SharedAccountVerifier&)=delete;
    SharedAccountVerifier& operator=(const SharedAccountVerifier&)=delete;
    void verify_raw_ui(std::string_view account,std::string_view password,Completion);
private:
    struct State;
    std::shared_ptr<State> state_;
    asio::thread_pool workers_;
};
}
