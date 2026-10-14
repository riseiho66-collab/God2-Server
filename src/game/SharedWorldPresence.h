#pragma once
#include "db/RecoveredCharacterRepository.h"
#include <map>
#include <memory>
#include <optional>
#include <span>
#include <thread>
#include <utility>
#include <vector>

namespace god2 {
// Serial game-owner lease over actual common character/storage identity.
// This integration policy does not recover spawn rules or manufacture wire
// data. The scene owner supplies its already reserved native actor handle.
// Both adapters must use the same registry before cross-version exclusion can
// be claimed. Existing TW movement/presence is not implicitly registered here.
class SharedWorldPresence {
public:
    struct Lease {
        std::uint64_t session,account,character,generation;
        std::uint16_t actor_handle;
        RecoveredPosition position;
        bool operator==(const Lease&) const = default;
    };
    struct ReadyCharacter {
        Lease lease;
        RecoveredCharacter character; // Entire actual common root; IDs stay64-bit.
        RecoveredPosition position; // Actual saved prefix, not lease entry pose.
    };
    explicit SharedWorldPresence(RecoveredCharacterRepository& characters):characters_(characters){}
    SharedWorldPresence(const SharedWorldPresence&)=delete;
    SharedWorldPresence& operator=(const SharedWorldPresence&)=delete;
    bool owns_repository(const RecoveredCharacterRepository& characters) const {
        owner();return &characters_==&characters;
    }
    // Raw owner reservation, including prepare-before-ready. Do not consult
    // repository ownership here: removal's BeforeCommit already staged the
    // root absent. A stale/unreleased entry still blocks mutation until its
    // exact generation's existing release(), rather than becoming invisible.
    bool character_reserved(std::uint64_t character) const;
    // No fallback placement: the real placement owner must persist/qualify an
    // initial position before reserving. Native resource/scene-mode data stays
    // with that owner. A DB character ID is never truncated into a wire handle.
    std::optional<Lease> prepare(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,std::uint16_t scene_owner_handle,const RecoveredPosition&);
    // TW's actual full2A carries geometry but no DB revision. Qualify against
    // the real shared saved position, then reserve that exact version through
    // prepare(). Never persist placement or manufacture a revision/default.
    std::optional<Lease> prepare_geometry(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,std::uint16_t scene_owner_handle,std::uint16_t area,
        std::uint16_t scene,std::uint16_t x,std::uint16_t y);
    bool current(const Lease&) const;
    bool preparation_current(const Lease&) const;
    // CUSTOM-0130 exact retained prepared registry, after the caller's actual
    // repository qualification. No observer, admission or activation occurs.
    bool retained_preparation_current(const Lease&) const;
    bool activate(const Lease&,std::uint16_t claimed_handle);
    // Explicit independent native scene path. Copy the lease before repository
    // observers, then find the same prepared generation again before activation.
    bool activate_qualified_scene(const Lease&,std::uint16_t claimed_handle);
    bool ready(const Lease&) const;
    // CUSTOM-0130 exact retained registry only. No repository observer or
    // resource/position refresh; callers retain their separately qualified data.
    bool retained_ready_current(const Lease&) const;
    // Read only the exact currently active registry lease for this tuple.
    // Requalifies actual character ownership; never reserves, activates or
    // manufactures a position. Saved position may have advanced after entry.
    std::optional<Lease> ready_lease(std::uint64_t session,std::uint64_t account,
        std::uint64_t character) const;
    // Complete currently active population only. Missing ownership/root/position
    // invalidates the whole read; it is never silently interpreted as offline.
    // Copies registry before virtual repository reads; every read is requalified
    // against that same registry and a second complete root/position population.
    // Actual repository reads must not yield, pump or mutate. Caught nested
    // snapshots/registry mutations invalidate this observation, not old leases.
    std::optional<std::vector<ReadyCharacter>> ready_characters() const;
    // CUSTOM-0133 full population witness, privately issued by this registry.
    // Owns all ready rows and the complete registry (including pending leases).
    // Retain the value, not a borrowed characters() span, across observers.
    class ReadyPopulation final {
    public:
        ReadyPopulation(const ReadyPopulation&)=default;
        ReadyPopulation& operator=(const ReadyPopulation&)=default;
        std::span<const ReadyCharacter> characters() const noexcept;
    private:
        friend class SharedWorldPresence;
        struct Data;
        explicit ReadyPopulation(std::shared_ptr<const Data> data):data_(std::move(data)) {}
        std::shared_ptr<const Data> data_;
    };
    std::optional<ReadyPopulation> observe_ready_population() const;
    // Pure final fence: exact private issuer + whole registry + allocation
    // epoch. Saved root/pose/resource Current is qualified separately.
    // A new actor that appears and disappears also changes this epoch.
    bool retained_population_current(const ReadyPopulation&) const;
    // Actual currently stored owner position. Movement authority remains with
    // the gameplay controller; these methods do not grant walkability/timing.
    std::optional<RecoveredPosition> saved_position(const Lease&) const;
    std::optional<RecoveredPosition> commit_owned_step(const Lease&,
        const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y);
    // Generation-qualified cleanup: a stale transport cannot evict a successor.
    bool release(const Lease&);
private:
    struct Entry {Lease lease;bool active=false;bool operator==(const Entry&) const = default;};
    struct PopulationIdentity {};
    void owner() const;
    bool stored(const Lease&) const;
    bool owned(const Lease&) const;
    RecoveredCharacterRepository& characters_;
    std::thread::id thread_=std::this_thread::get_id();
    std::map<std::uint64_t,Entry> sessions_;
    std::uint64_t generation_=0;
    // Owning identity prevents address reuse of a destroyed registry from
    // making an old population token valid in a new instance.
    const std::shared_ptr<const PopulationIdentity> population_identity_=
        std::make_shared<const PopulationIdentity>();
    mutable bool snapshot_busy_=false,snapshot_reentered_=false;
};
}
