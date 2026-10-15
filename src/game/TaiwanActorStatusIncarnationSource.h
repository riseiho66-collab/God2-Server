#pragma once
#include "game/SharedWorldPresence.h"
#include <cstdint>
#include <map>
#include <memory>
#include <optional>
#include <thread>
#include <utility>

namespace god2 {
class Session;
class SharedTaiwanWorldLifecycle;
// Positive private actor-incarnation lifetime only. Neither admission to this
// registry nor a live token establishes Known/None/EA or writer permission.
class TaiwanActorStatusIncarnationSource final {
    struct Identity;
    struct Entry;
    class Operation;
public:
    using Lease=SharedWorldPresence::Lease;
    class Token final {
    public:
        Token(const Token&) noexcept=default;
        Token& operator=(const Token&) noexcept=default;
        const Lease& lease() const noexcept;
        std::uint64_t sequence() const noexcept;
        bool operator==(const Token& other) const noexcept {return entry_==other.entry_;}
    private:
        friend class TaiwanActorStatusIncarnationSource;
        friend class Session;
        // IO close/failure can revoke this already-issued entry only.
        void retire() const noexcept;
        bool live() const noexcept;
        bool can_bind(Session&) const noexcept;
        explicit Token(std::shared_ptr<Entry> entry) noexcept:entry_(std::move(entry)){}
        std::shared_ptr<Entry> entry_;
    };
    static std::shared_ptr<TaiwanActorStatusIncarnationSource> create(std::shared_ptr<SharedWorldPresence>);
    ~TaiwanActorStatusIncarnationSource() noexcept;
    TaiwanActorStatusIncarnationSource(const TaiwanActorStatusIncarnationSource&)=delete;
    TaiwanActorStatusIncarnationSource& operator=(const TaiwanActorStatusIncarnationSource&)=delete;
    bool owns_presence(const std::shared_ptr<SharedWorldPresence>&) const noexcept;
    // Finds only an earlier private lifecycle admission; never mints/rebases.
    // Wrong-thread/reentrant calls fail before Session or registry access.
    std::optional<Token> observe(const Lease&) const noexcept;
    bool current(const Token&) const noexcept;
    // Pure atomic lifetime fence only: no weak Session lock, presence observer,
    // game fields, readiness, SQL, allocation or status inference.
    bool retained(const Token&) const noexcept;
    void stop() noexcept;
private:
    friend class SharedTaiwanWorldLifecycle;
    explicit TaiwanActorStatusIncarnationSource(const std::shared_ptr<SharedWorldPresence>&);
    std::optional<Token> prepare(Session&,const Lease&) noexcept;
    void retire(const Token&) noexcept;
    bool current_entry(const std::shared_ptr<Entry>&,bool require_bound=true) const;
    const std::thread::id thread_=std::this_thread::get_id();
    const std::weak_ptr<SharedWorldPresence> presence_;
    const SharedWorldPresence* const presence_address_;
    const std::shared_ptr<Identity> identity_;
    std::map<std::uint64_t,std::weak_ptr<Entry>> entries_;
    std::uint64_t sequence_=0;
    mutable bool busy_=false;
};
}
