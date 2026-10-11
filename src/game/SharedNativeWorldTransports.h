#pragma once
#include "game/SharedWorldPresence.h"
#include "net/Session.h"
#include "cn/net/SharedCredentialConnection.h"
#include <map>
#include <memory>
#include <optional>
#include <thread>
#include <variant>

namespace god2 {
// Actual ready common lease -> actual native connection. This is a game-owned
// transport source, not audience, visibility, permission, map or reply policy.
// Registry/cleanup tokens retain connections weakly to avoid cleanup cycles.
class SharedNativeWorldTransports {
    struct Identity;
    struct TokenStorage;
    struct SnapshotStorage;
public:
    using Lease=SharedWorldPresence::Lease;
    using WeakTransport=std::variant<std::weak_ptr<Session>,std::weak_ptr<cn::SharedCredentialConnection>>;
    using StrongTransport=std::variant<std::shared_ptr<Session>,std::shared_ptr<cn::SharedCredentialConnection>>;
    class Token {
    public:
        Token(const Token&)=default;
        Token& operator=(const Token&)=default;
        Token(Token&&) noexcept;
        Token& operator=(Token&&) noexcept;
        const Lease& lease() const noexcept;
    private:
        friend class SharedNativeWorldTransports;
        explicit Token(std::shared_ptr<const TokenStorage>);
        std::shared_ptr<const TokenStorage> storage_;
    };
    class Snapshot {
    public:
        Snapshot(const Snapshot&)=default;
        Snapshot& operator=(const Snapshot&)=default;
        Snapshot(Snapshot&&) noexcept;
        Snapshot& operator=(Snapshot&&) noexcept;
        const Token& token() const noexcept;
        const Lease& lease() const noexcept;
        const StrongTransport& transport() const noexcept;
    private:
        friend class SharedNativeWorldTransports;
        explicit Snapshot(std::shared_ptr<const SnapshotStorage>);
        std::shared_ptr<const SnapshotStorage> storage_;
    };
    static std::shared_ptr<SharedNativeWorldTransports> create(std::shared_ptr<SharedWorldPresence>);
    ~SharedNativeWorldTransports();
    SharedNativeWorldTransports(const SharedNativeWorldTransports&)=delete;
    SharedNativeWorldTransports& operator=(const SharedNativeWorldTransports&)=delete;
    bool owns_presence(const std::shared_ptr<SharedWorldPresence>&) const;
    std::optional<Token> bind(const Lease&,const std::shared_ptr<Session>&);
    std::optional<Token> bind(const Lease&,const std::shared_ptr<cn::SharedCredentialConnection>&);
    bool current(const Token&) const;
    bool release(const Token&); // Exact registry incarnation only; no repository/common cleanup.
    std::optional<Snapshot> lookup(const Lease&) const;
    bool current(const Snapshot&) const;
    // Callback/repository-free exact endpoint fence after caller observers.
    // It does not replace full current() or grant audience/native reply rights.
    bool registry_current(const Snapshot&) const;
    // Exact endpoint incarnation without freezing a prior snapshot's phase.
    // Caller must separately qualify the actual post-operation phase/owner.
    bool registry_current(const Token&) const;
    // Same currently stored private registration, never just an equal lease.
    bool same_registration(const Token&,const Token&) const;
private:
    explicit SharedNativeWorldTransports(std::shared_ptr<SharedWorldPresence>);
    void owner() const;
    std::optional<Token> bind_owned(const Lease&,StrongTransport);
    bool stored(const Token&) const;
    bool tuple(const Lease&,const StrongTransport&) const;
    bool qualified(const Token&,const StrongTransport&) const;
    std::shared_ptr<SharedWorldPresence> presence_;
    std::shared_ptr<const Identity> identity_;
    std::map<std::uint64_t,Token> slots_;
    std::uint64_t generation_=0; // Private registry incarnation, not a native counter.
    std::thread::id thread_=std::this_thread::get_id();
    mutable bool busy_=false,reentered_=false;
    bool terminal_=false;
};
}
