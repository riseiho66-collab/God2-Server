#pragma once
#include "cn/world/SharedInitialScene.h"
#include "cn/world/CnNativeCameraMotion.h"
#include "cn/world/CnNativeFrameClock.h"
#include "cn/world/CnNativePathCompletion.h"
#include "cn/world/CnDeferredRoleRefresh.h"

namespace god2::cn {
// Concrete CN native scene/cache/actor owner behind SharedMovement. Position
// comes from the same shared character repository used by TW. Native cell/view
// data stays CN-qualified; possession never grants movement or invents5D.
class SharedNativeMovementScene final:public SharedMovement::WorldOwner {
public:
    using Lease=SharedWorldPresence::Lease;
    struct Candidate {
        Lease lease;
        RecoveredPosition before;
        std::uint64_t scene_revision;
        std::uint8_t mode;
        god2cn::CnMapPreparedStep step;
    };
    struct CameraInput {
        //005393B0 supplies pixels per animation frame from elapsed time,
        // velocity and residues. No one-frame-per-C2S-step correspondence.
        god2cn::CnOutdoorCamera::View actual_native_frame_view;
        std::int32_t native_map34;
        std::string native_owner_prefix;
    };
    struct Permit {
        god2cn::Bytes full_native_ack;
        // Required for mode0; actual viewport, pixels, loaded tile dimensions,
        // map+34 and owner prefix, never request coordinates divided by21.
        std::optional<CameraInput> camera;
        // Publish the real pending/timing/permission state after durable position
        // and native scene/cache publication. No default success callback.
        std::function<bool(const RecoveredPosition&)> publish_authority;
    };
    struct FrameCandidate {
        Lease lease;
        RecoveredPosition position;
        std::uint64_t scene_revision;
        std::optional<god2cn::CnOutdoorCamera::View> published_view;
        std::optional<god2cn::CnNativeFrameClock::State> published_clock;
    };
    struct FramePublished {
        god2cn::CnNativeCameraMotion::Frame motion;
        god2cn::CnOutdoorCamera::View view;
        std::optional<god2cn::CnOutdoorCamera::Point> successful_cache_rebase;
        std::array<bool,9> visibility;
    };
    struct FramePermit {
        struct DeferredPath {
            god2cn::CnDeferredRoleRefresh::Snapshot actual_after_notification;
            god2cn::CnNativePathCompletion::Snapshot path;
        };
        struct StartedMotion {
            // Actual accepted00539150 transition; no inferred ring admission.
            std::uint8_t direction,actual_speed_index;
            std::optional<float> actual_mount_addition;
        };
        std::uint64_t actual_owner_generation; // Strictly newer real frame receipt.
        std::int32_t actual_actor_state; //005395E0 executes motion only at state8.
        // Real retained loop state; prior elapsed drives this motion. Clock
        // samples are obtained only after native frame/model publication.
        god2cn::CnNativeFrameClock::State actual_clock_before;
        god2cn::CnNativeCameraMotion::State motion_before;
        std::optional<StartedMotion> actual_started_motion;
        CameraInput camera; // View before this frame, with real extents/map/prefix.
        // Actual residue/travel/path/model owners; rebase actors only on success.
        std::function<bool(const FramePublished&)> publish_native_frame;
        // Invoked ONLY after both axes complete and frame/model publication.
        // Observe the actual retained4A operand/pending word; no empty default
        // or replay of each earlier overwritten4A is supplied.
        std::function<std::optional<god2cn::CnDeferredRoleRefresh::Snapshot>()> observe_deferred_notification;
        // Execute the actual005385F0 when this operand has pending flags,
        // then clear+89B244 AFTER its return, including masks02/04/08 exits.
        // Return a fresh actual owner snapshot and actual path. This callback
        // remains an unconfigured source, not native success or server6D policy.
        std::function<std::optional<DeferredPath>(const god2cn::CnDeferredRoleRefresh::Drain&)> path_after_deferred_notification;
        // Execute native next-segment admission/reset or final target/state0
        // publication. Never generate a server5D or move common DB position.
        std::function<bool(const god2cn::CnNativePathCompletion::Plan&)> publish_native_path;
        std::function<std::optional<god2cn::CnNativeFrameClock::Observation>()> observe_completed_loop_clock;
        std::function<bool(const god2cn::CnNativeFrameClock::Next&)> publish_native_clock;
    };
    class Authority {
    public:
        virtual ~Authority()=default;
        // Real timing, sequence/reset, collision/path/corner/dynamic objects,
        // battle/transfer restrictions and full5D value contract remain owned
        // here. No implementation of guessed original server rules is supplied.
        virtual std::optional<Permit> authorize(const Candidate&)=0;
        // Actual frame scheduler/state owns these inputs, separately from C2S
        // authorization. No default clock, speed, pixels or success is supplied.
        virtual std::optional<FramePermit> native_frame(const FrameCandidate&)=0;
    };
    static std::shared_ptr<SharedNativeMovementScene> adopt(
        const std::shared_ptr<SharedCredentialConnection>&,std::shared_ptr<SharedWorldPresence>,
        const Lease&,std::shared_ptr<SharedInitialScene>,const god2cn::CnSceneAssets&,
        std::shared_ptr<Authority>,std::size_t max_encoded_bytes,std::size_t max_plain_bytes);
    std::optional<SharedMovement::Scene> scene(const Lease&,const RecoveredPosition&) override;
    bool current(const Lease&,const SharedMovement::Scene&) override;
    std::optional<SharedMovement::Authorization> authorize(const Lease&,const RecoveredPosition&,
        const SharedMovement::Scene&,const god2cn::CnMapPreparedStep&) override;
    bool publish(const Lease&,const SharedMovement::Scene&,const SharedMovement::Committed&) override;
    // Available only at the original position/revision/cache generation.
    // Pre-cache-switch seed, not the live camera; no viewport is synthesized.
    std::optional<god2cn::CnOutdoorCamera::Point> initial_camera_seed(const Lease&) const;
    // Independent native renderer frame and completion: no position CAS,5D,5E.
    // A failure after cache commit invalidates this owner; host must reenter.
    bool advance_native_camera_frame(const Lease&);
private:
    struct Pending {
        Candidate candidate;
        Permit permit;
        std::optional<god2cn::CnOutdoorWindow::CameraPrepared> camera;
        std::optional<god2cn::CnOutdoorWindow::PreparedCameraSwitch> camera_switch;
    };
    SharedNativeMovementScene(const std::shared_ptr<SharedCredentialConnection>&,
        std::shared_ptr<SharedWorldPresence>,const Lease&,std::shared_ptr<SharedInitialScene>,
        const god2cn::CnSceneAssets&,std::shared_ptr<Authority>,std::size_t,std::size_t,
        SharedMovement::Scene);
    void owner() const;
    bool bound() const;
    bool snapshot_current(const Lease&,const SharedMovement::Scene&) const;
    const god2cn::CnMapPassability& cells() const;
    static bool same_step(const god2cn::CnMapPreparedStep&,const god2cn::CnMapPreparedStep&);
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<SharedCredentialConnection> connection_;
    std::shared_ptr<SharedWorldPresence> presence_;
    Lease lease_;
    std::shared_ptr<SharedInitialScene> initial_;
    const god2cn::CnSceneAssets& assets_;
    std::shared_ptr<Authority> authority_;
    std::size_t encoded_budget_,plain_budget_;
    RecoveredPosition position_;
    std::uint64_t revision_;
    std::uint8_t mode_,direction_;
    god2cn::CnMapPassability house_or_initial_grid_;
    std::shared_ptr<god2cn::CnOutdoorWindow> window_;
    std::uint64_t cache_generation_=0;
    std::optional<god2cn::CnOutdoorCamera::View> camera_view_;
    std::optional<god2cn::CnOutdoorCamera::Point> initial_camera_seed_;
    std::uint64_t initial_cache_generation_=0;
    std::optional<std::array<bool,9>> visible_slots_;
    std::optional<Pending> pending_;
    std::uint64_t native_frame_generation_=0;
    std::optional<god2cn::CnNativeFrameClock::State> native_clock_;
    bool frame_failed_=false;
    bool busy_=false; // Prevent authority/publication callbacks reentering a mutation.
};
}
