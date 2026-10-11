#pragma once
#include "cn/assets/CnOutdoorSceneResources.h"
#include "cn/world/CnOutdoorCamera.h"
#include <thread>

namespace god2::cn {class SharedInitialScene;}
namespace god2cn {
class CnSceneAssets;
class CnPreparedStandaloneOutdoorScene;
// Fully loaded mode0 cache branch0046C830/0046D460/0046F630 and the
// same-MDT/retained-MBD and different-MDT/standalone-full9 subsets of00470C90.
// Standalone full9/known-file-open-failure cache reuse is connected. Other
// partial failures, runtime frames and camera application remain owner work.
// This never derives a center from a movement packet.
class CnOutdoorWindow {
    struct Identity {};
public:
    using Coordinate=CnOutdoorTerrain::ChunkCoordinate;
    struct MapSwitch {
        Coordinate requested;
        std::string native_reference;
        CnOutdoorCamera::Point camera_after_actual_switch_success;
    };
    class CameraPrepared {
    public:
        const CnOutdoorCamera::Projection& projection() const noexcept {return projection_;}
        const std::optional<MapSwitch>& map_switch() const noexcept {return switch_;}
    private:
        friend class CnOutdoorWindow;
        CameraPrepared(std::shared_ptr<const Identity>,std::uint64_t,
            CnOutdoorCamera::Projection,std::optional<MapSwitch>);
        std::shared_ptr<const Identity> identity_;
        std::uint64_t expected_;
        CnOutdoorCamera::Projection projection_;
        std::optional<MapSwitch> switch_;
    };
    struct Slot {
        // Internal allocation label for stable cache reuse, not a wire handle
        // or recovered pointer value. Array index is native slot+3C.
        std::uint8_t allocation_label;
        std::optional<Coordinate> coordinate; // Actual loaded+64/+68; null for a deleted slot.
        bool valid; // Native+54; false committed standalone slots are null, not zero cells.
    };
private:
    struct State {
        Coordinate center;
        std::array<Slot,9> slots;
        CnMapPassability grid;
        std::uint64_t generation; // Internal cache CAS, not actor/DB/scene revision.
    };
public:
    class Prepared {
    public:
        const CnMapPassability& grid() const noexcept {return next_.grid;}
        Coordinate center() const noexcept {return next_.center;}
        const std::array<Slot,9>& slots() const noexcept {return next_.slots;}
        const std::array<bool,9>& reloaded() const noexcept {return reloaded_;}
        std::uint64_t expected_generation() const noexcept {return expected_;}
    private:
        friend class CnOutdoorWindow;
        Prepared(std::shared_ptr<const Identity>,std::uint64_t,State,std::array<bool,9>);
        std::shared_ptr<const Identity> identity_;
        std::uint64_t expected_;
        State next_;
        std::array<bool,9> reloaded_;
    };
    class PreparedCameraSwitch {
    public:
        const CnMapPassability& grid() const noexcept {return cache_.grid();}
        Coordinate center() const noexcept {return cache_.center();}
        const std::array<Slot,9>& slots() const noexcept {return cache_.slots();}
        const std::array<bool,9>& reloaded() const noexcept {return cache_.reloaded();}
        bool replaces_resource() const noexcept {return replaces_resource_;}
    private:
        friend class CnOutdoorWindow;
        PreparedCameraSwitch(Prepared,CameraPrepared,std::shared_ptr<const CnPreparedStandaloneOutdoorScene> standalone={},
            bool replaces_resource=false);
        Prepared cache_;
        CameraPrepared camera_;
        std::shared_ptr<const CnPreparedStandaloneOutdoorScene> standalone_;
        bool replaces_resource_;
    };
    struct CommittedCameraSwitch {
        CnOutdoorCamera::Point camera_after_cache_commit;
        std::array<bool,9> native_visibility_before_switch;
        Coordinate loaded_center;
        bool resource_replaced;
        bool center_slot_available; // Native overlay/render gate; never movement permission.
    };
    CnOutdoorWindow(const CnOutdoorWindow&)=delete;
    CnOutdoorWindow& operator=(const CnOutdoorWindow&)=delete;
    // Qualified actual scene owner supplies the native requested center.
    // Builds an owned candidate without changing the active cache; unknown
    // clamped chunks/objects are absence/errors, never fabricated terrain.
    std::optional<Prepared> prepare_native_46c830(Coordinate requested) const;
    // Actual scene owner's viewport/camera/map+34/base prefix, never2E or
    // catalog kind. Produces00473120's qualified native .map request only;
    //00470C90 resource selection/installation must finish before camera change.
    std::optional<CameraPrepared> prepare_camera(const CnOutdoorCamera::View&,
        std::int32_t native_map34,std::string_view native_owner_prefix) const;
    bool current(const CameraPrepared&) const;
    // Actual retained-MBD/same-MDT subset of00470C90. Qualifies native base
    // resource identity before consuming the camera candidate into real cells.
    // Standalone uses the explicit assets overload; partial branches stay open.
    std::optional<PreparedCameraSwitch> prepare_camera_switch(const CameraPrepared&) const;
    // Different-MDT flag0 branch: real explicit-root asset reader, no MBD
    // fallback. Binds the actual loaded/null replacement to this cache generation.
    // Also reuses valid standalone bytes and reloads only invalid rotated slots.
    // Actual plain.map open failures become null slots, preserving existing
    // initialized grid bytes. Other failure variants remain recovery work.
    std::optional<PreparedCameraSwitch> prepare_camera_switch(const CameraPrepared&,
        const CnSceneAssets&,std::size_t max_encoded_bytes,std::size_t max_plain_bytes) const;
    bool current(const PreparedCameraSwitch&) const;
    // Full cache commit precedes the conditional camera result. Actual camera,
    // actor, permission, DB and per-recipient publication remain with WorldOwner.
    std::optional<CommittedCameraSwitch> commit_camera_switch(PreparedCameraSwitch);
    // Same-instance/generation CAS for the actual world lifecycle owner.
    // Does not commit a player position, grant permission, send5D or broadcast.
    bool commit(Prepared);
    const CnMapPassability& grid() const;
    Coordinate center() const;
    std::uint64_t generation() const;
    //00473120 tests map+FEC pointer presence, not native slot-valid+54.
    bool center_slot_present() const;
    const CnPreparedStandaloneOutdoorScene* standalone_snapshot() const;
private:
    friend class god2::cn::SharedInitialScene;
    static std::shared_ptr<CnOutdoorWindow> from_initial(
        std::shared_ptr<const CnOutdoorSceneResources>,const CnOutdoorTerrain::InitialWorldPlacement&);
    CnOutdoorWindow(std::shared_ptr<const CnOutdoorSceneResources>,State);
    std::array<Slot,9> rotated_slots(Coordinate next_center) const;
    std::optional<PreparedCameraSwitch> prepare_standalone_reuse(const CameraPrepared&,
        const CnSceneAssets&,std::size_t max_encoded_bytes,std::size_t max_plain_bytes) const;
    void owner() const;
    std::thread::id thread_=std::this_thread::get_id();
    std::shared_ptr<const Identity> identity_=std::make_shared<const Identity>();
    std::shared_ptr<const CnOutdoorSceneResources> resources_;
    std::shared_ptr<const CnPreparedStandaloneOutdoorScene> standalone_snapshot_;
    State state_;
};
}
