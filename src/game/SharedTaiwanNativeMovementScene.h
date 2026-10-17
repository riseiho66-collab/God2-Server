#pragma once
#include "game/SharedTaiwanMovementSource.h"
#include "game/TaiwanNativeGrid.h"
#include "protocol/RecoveredTaiwanMapCell.h"
#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <thread>
#include <vector>

namespace god2 {
// Concrete retained TW map/actor owner for the explicit native movement source.
// Actual native snapshots or original composition material are required;
// invented map initialization, authority, camera frame or5D is supplied here.
class SharedTaiwanNativeMovementScene final:public SharedTaiwanMovement::WorldOwner {
public:
    using Lease=SharedWorldPresence::Lease;
    enum class CellSource {RawSnapshot,ComposedMode2};
    struct BufferImage {
        std::uint32_t address; // Actual x86 snapshot address, never dereferenced.
        std::vector<std::uint8_t> bytes;
    };
    struct Resources {
        BufferImage map;
        std::optional<BufferImage> grid,cells;
        // Real provider's resource/scene lineage, not recovered native counters.
        std::uint64_t actual_resource_generation,actual_initial_scene_generation;
        // Separate value-owned native composition authority, retaining complete
        // raw masks and actual ordered overlays without mutable shared aliases.
        // Raw map/grid/cells must all be absent.
        std::optional<TaiwanNativeGrid> composed_grid;
        static std::optional<Resources> compose_mode2(TaiwanNativeGrid::Material,
            std::uint64_t actual_resource_generation,std::uint64_t actual_initial_scene_generation);
        CellSource cell_source() const noexcept;
        bool complete() const;
        std::optional<std::uint8_t> read(std::int32_t x,std::int32_t y) const;
        // Raw snapshot path only. Composed grids have no fabricated native map
        // structure or x86 address; asking for such an input is an error.
        RecoveredTaiwanMapCell::Input input() const;
    };
    struct Scope {
        Lease lease;
        RecoveredPosition position;
        std::uint8_t direction;
        // Private owner publication incarnation, never a native wire counter.
        std::uint64_t publication_revision;
    };
    enum class Check {Adopt,Scene,Current,Authorize,BeforePublish,AfterPublish};
    using ResourceCurrent=std::function<bool(Check,const Scope&,const Resources&)>;
    struct Native {
        Resources resources;
        RecoveredPosition actual_position;
        std::uint8_t actual_direction;
        // Actual post-initialization/post-object-overlay snapshot or complete
        // original composition material, selected explicitly in Resources.
        // Current must retain the real owner strongly and qualify identity,
        // generations, raw bytes, center and object/window lifecycle. Complete
        // structural buffers or an installed MBD file do not establish that.
        ResourceCurrent current;
        Native(Resources,RecoveredPosition,std::uint8_t,ResourceCurrent);
    };
    struct Candidate {
        Scope owner;
        std::uint64_t actual_resource_generation,actual_initial_scene_generation;
        TaiwanMovementRules::Step step;
        CellSource cell_source;
    };
    struct Permit {
        std::vector<std::uint8_t> full_native_ack;
        // Real pre-CAS pending/timing/sequence/permission ticket, checked again
        // by current() and before publishing the already durable position.
        std::function<bool(const Candidate&)> current;
        // Publish the actual authoritative actor/pending/ring state once.
        // A partial failure is terminal; the committed prefix is not rewound.
        std::function<bool(const SharedTaiwanMovement::Committed&)> publish_authority;
        Permit(std::vector<std::uint8_t>,std::function<bool(const Candidate&)>,
            std::function<bool(const SharedTaiwanMovement::Committed&)>);
    };
    class Authority {
    public:
        virtual ~Authority()=default;
        // Actual timing, sequence/reset, collision/corner/object/path, battle,
        // transfer and full original5D value remain this owner's responsibility.
        virtual std::optional<Permit> authorize(const Candidate&)=0;
    };
    struct FactoryScope {Lease lease;RecoveredPosition saved_position;};
    struct Material {
        Native scene;
        std::shared_ptr<Authority> authority;
        Material(Native,std::shared_ptr<Authority>);
    };
    using MaterialSource=std::function<std::optional<Material>(Session&,const FactoryScope&)>;
    // Direct actual-material bridge to the existing source factory. The real
    // supplier returns complete post-initialization buffers or original native
    // composition material, current actor state and its actual authority.
    static SharedTaiwanMovementSource::Factory factory(
        std::shared_ptr<SharedWorldPresence>,MaterialSource);
    // Call directly from the existing SharedTaiwanMovementSource::Factory.
    // All use/destruction is on game. Real callbacks must not retain argument
    // references, yield, pump events, perform another position CAS or send.
    // Resources/Authority retain their actual dependencies strongly until
    // source release before lifecycle/DB teardown. No wrapper host is needed.
    static std::shared_ptr<SharedTaiwanNativeMovementScene> adopt(
        const std::shared_ptr<Session>&,std::shared_ptr<SharedWorldPresence>,
        const Lease&,Native,std::shared_ptr<Authority>);
    ~SharedTaiwanNativeMovementScene();
    std::optional<SharedTaiwanMovement::Scene> scene(const Lease&,const RecoveredPosition&,
        const RecoveredMovement::Request&) override;
    bool current(const Lease&,const SharedTaiwanMovement::Scene&) override;
    std::optional<SharedTaiwanMovement::Authorization> authorize(const Lease&,const RecoveredPosition&,
        const SharedTaiwanMovement::Scene&,const TaiwanMovementRules::Step&) override;
    bool publish(const Lease&,const SharedTaiwanMovement::Scene&,const SharedTaiwanMovement::Committed&) override;
private:
    struct Probe {RecoveredMovement::Request request;SharedTaiwanMovement::Scene scene;};
    struct Pending {Candidate candidate;Permit permit;};
    struct Operation;
    SharedTaiwanNativeMovementScene(const std::shared_ptr<Session>&,
        std::shared_ptr<SharedWorldPresence>,const Lease&,Native,std::shared_ptr<Authority>);
    void owner() const;
    bool bound() const;
    Scope scope() const;
    bool resources_current(Check);
    bool snapshot_current(const Lease&,const SharedTaiwanMovement::Scene&) const;
    bool saved_current() const;
    bool ticket_current(Check);
    static bool same_request(const RecoveredMovement::Request&,const RecoveredMovement::Request&);
    static bool same_step(const TaiwanMovementRules::Step&,const TaiwanMovementRules::Step&);
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Session> connection_;
    std::shared_ptr<SharedWorldPresence> presence_;
    Lease lease_;
    Native native_;
    std::shared_ptr<Authority> authority_;
    RecoveredPosition position_;
    std::uint8_t direction_;
    std::uint64_t publication_revision_;
    std::optional<Probe> probe_;
    std::optional<Pending> pending_;
    bool busy_=false,failed_=false;
};
}
