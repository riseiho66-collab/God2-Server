#pragma once
#include <array>
#include <atomic>
#include <cstdint>
#include <map>
#include <memory>
#include <thread>
#include <utility>

namespace god2 {
class RecoveredCharacterRepository;
class SharedWorldPresence;
// CUSTOM-0159: process-local exclusive character custody for the three actual
// game-owner worlds. This is not authentication, durable save or switch proof.
// One owner and its repository must outlive all participating world registries.
class SharedChannelCharacterOwnership final {
public:
    static constexpr std::uint8_t channel_count=3;
    explicit SharedChannelCharacterOwnership(RecoveredCharacterRepository&);
    ~SharedChannelCharacterOwnership();
    SharedChannelCharacterOwnership(const SharedChannelCharacterOwnership&)=delete;
    SharedChannelCharacterOwnership& operator=(const SharedChannelCharacterOwnership&)=delete;
    bool owns_repository(const RecoveredCharacterRepository&) const;
    // Includes pending entry and terminal quarantine, even after its original
    // world unregisters; not just visible/active characters. No SQL.
    bool character_reserved(std::uint64_t character) const;
private:
    friend class SharedWorldPresence;
    struct WorldIdentity {const std::uint8_t channel;mutable bool retired=false;};
    using World=std::shared_ptr<const WorldIdentity>;
    struct Reservation {
        enum class Retirement {None,Pending,Quarantined,Released};
        World world;
        const std::uint64_t session,account,character,generation;
        mutable bool retired=false;
        mutable bool detached=false; // GAME only, after exact local release.
        mutable std::atomic<Retirement> retirement{Retirement::None};
        Reservation(World selected,std::uint64_t s,std::uint64_t a,std::uint64_t c,std::uint64_t g)
            :world(std::move(selected)),session(s),account(a),character(c),generation(g) {}
    };
    using Claim=std::shared_ptr<const Reservation>;
    void owner() const;
    World register_world(std::uint8_t);
    void unregister_world(const World&) noexcept;
    bool registered(const World&) const;
    bool live(const Claim&) const;
    bool occupied(const Claim&) const;
    bool indexed(const Claim&) const;
    Claim reserve(const World&,std::uint64_t session,std::uint64_t account,std::uint64_t character);
    bool current(const Claim&) const;
    bool release(const Claim&);
    bool begin_terminal(const Claim&);
    bool terminal(const Claim&) const noexcept;
    bool detach_terminal(const Claim&);
    bool finish_terminal(const Claim&,bool clean);
    static void quarantine_terminal(const Claim&) noexcept;
    RecoveredCharacterRepository& characters_;
    const std::thread::id thread_=std::this_thread::get_id();
    std::array<std::weak_ptr<const WorldIdentity>,channel_count> worlds_{};
    struct Registry {
        std::map<std::uint64_t,Claim> characters,sessions;
    };
    // Allocation happens on an unpublished candidate; retained immutable map
    // structure survives nested retirement without invalidating iterators.
    // Retirement changes only private flags and never allocates/calls out.
    std::shared_ptr<const Registry> registry_=std::make_shared<const Registry>();
    std::uint64_t generation_=0;
};
}
