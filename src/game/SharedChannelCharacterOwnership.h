#pragma once
#include <array>
#include <cstdint>
#include <map>
#include <memory>
#include <thread>

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
    // Includes pending entry, not just visible/active characters. No SQL.
    bool character_reserved(std::uint64_t character) const;
private:
    friend class SharedWorldPresence;
    struct WorldIdentity {const std::uint8_t channel;mutable bool retired=false;};
    using World=std::shared_ptr<const WorldIdentity>;
    struct Reservation {
        World world;
        const std::uint64_t session,account,character,generation;
        mutable bool retired=false;
    };
    using Claim=std::shared_ptr<const Reservation>;
    void owner() const;
    World register_world(std::uint8_t);
    void unregister_world(const World&) noexcept;
    bool registered(const World&) const;
    bool live(const Claim&) const;
    Claim reserve(const World&,std::uint64_t session,std::uint64_t account,std::uint64_t character);
    bool current(const Claim&) const;
    bool release(const Claim&);
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
