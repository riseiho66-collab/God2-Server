#pragma once
#include "cn/assets/CnSceneAssets.h"
#include "cn/protocol/CnWorldEntry.h"
#include "cn/world/SharedMovement.h"
#include "cn/world/CnOutdoorWindow.h"
#include "db/NativeMapCatalog.h"
#include <functional>
#include <variant>

namespace god2::cn {
class SharedWorldReady;
class SharedNativeMovementScene;
struct InitialAppearanceIdentity;
enum class SharedInitialAppearanceCheck {BeforeRead,AfterRead,BeforePublish};
class SharedInitialAppearanceSource {
public:
    // Actual profile/revision/native source lifetime observation only; no
    // yield, save, send, event pumping or default true resource permission.
    using Current=std::function<bool(SharedInitialAppearanceCheck,const god2cn::CnAppearanceRomInputs*)>;
    const auto& inputs() const noexcept {return inputs_;}
private:
    friend class SharedInitialScene;
    SharedInitialAppearanceSource(std::shared_ptr<const InitialAppearanceIdentity>,std::uint64_t,
        god2cn::CnAppearanceRomInputs,Current);
    std::shared_ptr<const InitialAppearanceIdentity> identity_;
    std::uint64_t revision_;
    god2cn::CnAppearanceRomInputs inputs_;
    Current current_; // Actual source owner remains mandatory even with immutable snapshots.
};
// Normal initial2A only: actual shared preparation -> native CAN/resource
// loaders -> owned complete grid. No actor allocation, spawn, reply generation,
// movement permission or transfer/live-window implementation is implied.
class SharedInitialScene {
public:
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    static std::shared_ptr<SharedInitialScene> prepare(
        const std::shared_ptr<Connection>&,std::shared_ptr<SharedWorldPresence>,
        const Lease&,const NativeMapCatalog&,const god2cn::CnSceneAssets&,
        std::span<const std::uint8_t> complete_begin2a,std::uint64_t scene_owner_revision,
        std::size_t max_encoded_bytes,std::size_t max_plain_bytes);
    // Selection checks this same resource snapshot, full2A and ready's exact
    // registry/generation before output. Missing modes/files are never success.
    bool matches(const std::shared_ptr<Connection>&,
        const std::shared_ptr<SharedWorldReady>&,std::uint64_t character,
        const RecoveredPosition&,std::span<const std::uint8_t> complete_begin2a) const;
    // Actual WorldOwner may consume this snapshot once active at the initial
    // saved position/revision. After a move or scene revision change it must
    // supply its real actor/window lifecycle instead of reusing initial cells.
    // Direction is from that actor owner, not a guessed2A renderer projection.
    std::optional<SharedMovement::Scene> initial_movement_scene(
        const std::shared_ptr<Connection>&,const RecoveredPosition& current_position,
        std::uint64_t current_scene_revision,std::uint8_t actual_actor_direction) const;
    // Selected file paths are runtime provenance, not immutable asset hashes.
    // Actual scene owner must pin the loaded profile and revision for lifetime.
    const std::vector<std::filesystem::path>& source_files() const;
    // Same exact normal scene/presence/lease and initial stored position.
    // Retained original input only, not an appearance/equipment grant or proof
    // of unchanged runtime rules/assets. Real issuer's Current is mandatory.
    std::optional<god2cn::CnWorldEntry::BeginPlay> initial_actor_begin_play(
        const std::shared_ptr<Connection>&,const std::shared_ptr<SharedWorldPresence>&,const Lease&) const;
    // Explicit opt-in actual same CN assets owner, exact scene/lease/revision
    // and retained full2A ->immutable CSV/ROM inputs. No implicit scene reload.
    std::shared_ptr<const SharedInitialAppearanceSource> prepare_appearance_source(
        const std::shared_ptr<Connection>&,const std::shared_ptr<SharedWorldPresence>&,const Lease&,
        const god2cn::CnSceneAssets&,std::uint64_t current_scene_revision,
        std::size_t max_encoded_bytes,std::size_t max_plain_bytes,SharedInitialAppearanceSource::Current) const;
    bool appearance_source_current(const std::shared_ptr<const SharedInitialAppearanceSource>&,
        const std::shared_ptr<Connection>&,const std::shared_ptr<SharedWorldPresence>&,const Lease&) const;
    const god2cn::CnPreparedOutdoorScene* outdoor_initial() const;
    // Immutable initial placement projection BEFORE a successful native cache
    // switch. Never substitute for the ongoing frame/viewport/camera owner.
    std::optional<god2cn::CnOutdoorCamera::Point> initial_outdoor_camera_seed() const;
    // Allocate one cache from this exact preparation before initial ready.
    // Actual later owner selects the native reload branch and commits it;
    // possession of this cache is not permission to move the character.
    std::shared_ptr<god2cn::CnOutdoorWindow> outdoor_window(
        const std::shared_ptr<Connection>&,const std::shared_ptr<SharedWorldReady>&);
private:
    friend class SharedNativeMovementScene;
    bool live_claimed_=false; // One actual live owner per initial native resource lease.
    const god2cn::CnSceneAssets* assets_identity_=nullptr; // Exact factory's real profile owner.
    std::shared_ptr<const InitialAppearanceIdentity> appearance_identity_;
    using Prepared=std::variant<god2cn::CnPreparedHouseScene,god2cn::CnPreparedOutdoorScene>;
    SharedInitialScene(const std::shared_ptr<Connection>&,std::shared_ptr<SharedWorldPresence>,
        const Lease&,const NativeMapCatalog&,std::span<const std::uint8_t>,std::uint64_t,Prepared);
    void owner() const;
    bool bound(const std::shared_ptr<Connection>&) const;
    bool map_current() const;
    const god2cn::CnMapPassability& cells() const;
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    std::shared_ptr<SharedWorldPresence> presence_;
    Lease lease_;
    const NativeMapCatalog& maps_; // Actual shared DB owner must outlive this snapshot.
    std::array<std::uint8_t,37> begin_;
    std::uint64_t revision_;
    Prepared prepared_;
    std::shared_ptr<god2cn::CnOutdoorWindow> outdoor_window_;
};
}
