#pragma once
#include "db/SqliteOwnedEquipmentTransaction.h"
#include "db/RecoveredCharacterRepository.h"
#include "game/RecoveredIndoorGrid.h"
#include "game/RecoveredIslandEntryNavigation.h"
#include "game/RecoveredTownNavigation.h"
#include "game/RecoveredKunlunNavigation.h"
#include "game/RecoveredFruitNavigation.h"
#include "game/RecoveredParentNavigation.h"
#include "game/RecoveredCrossMapNavigation.h"
#include "game/WorldTransferCatalog.h"
#include "handlers/OwnedNpcTeleportOffer.h"
#include "protocol/RecoveredMovement.h"
#include "protocol/RecoveredWorldEntry.h"
#include <filesystem>
#include <functional>
#include <map>
#include <memory>
#include <thread>

namespace god2 {
class Session;
class SqliteOwnedEquipmentTransaction;
// Serial game-executor state, deliberately separate from fixture World/map 1.
class RecoveredMovementService {
public:
    RecoveredMovementService(RecoveredCharacterRepository& characters,
                             const std::filesystem::path& navigation);
    // Explicit laboratory placement, not a recovered spawn or streaming policy.
    struct TownDiagnostic {
        std::filesystem::path navigation;
        RecoveredTownNavigation::Center center;
        std::uint16_t x,y;
        bool source_consensus=false; // CUSTOM-0019: isolated conservative authority gate.
        std::filesystem::path indoor_navigation; // Optional qualified scene15; empty keeps town-only behavior.
        std::filesystem::path island_navigation; // Optional static scene0 consensus; no route implied.
        std::filesystem::path birthplace_navigation;
        std::uint16_t birthplace_x{},birthplace_y{};
        std::filesystem::path fruit_navigation; // Optional source-pinned area13/scene12; no automatic transfer.
        std::filesystem::path indoor_scenes; // CUSTOM-0052 current-town multi-room pinned bundle.
        std::filesystem::path kunlun_indoor_scenes; // CUSTOM-0052 area4 registry, never town scene aliases.
        std::filesystem::path kunlun_parent_navigation; // CUSTOM-0053 source-pinned area4/scene0.
        std::filesystem::path cross_map_navigation; // CUSTOM-0154 whole-file-pinned cross-MDL bundle.
        std::filesystem::path world_transfer_catalog; // CUSTOM-0155 complete qualified world snapshot.
    };
    RecoveredMovementService(RecoveredCharacterRepository& characters,const TownDiagnostic& town);
    RecoveredWorldEntry::Frame prepare(std::uint64_t session,std::uint64_t account,std::uint64_t character);
    // Explicit full native entry only: bind actual saved geometry and native
    // wire kind for existing ready/movement bookkeeping. No candidate frame,
    // initial placement, profile projection or persistence write is produced.
    // Existing cell_available navigation remains its labelled CUSTOM policy.
    void prepare_native(std::uint64_t session,std::uint64_t account,std::uint64_t character,
                        const RecoveredWorldEntry::Frame&);
    // Explicit native scene plan: actual full entry supplies the independent
    // twelve-bit scene handle; ownership/persistence continue using common64.
    // Bookkeeping only, not the legacy movement reply builder or scene admission.
    void prepare_native_scene(std::uint64_t session,std::uint64_t account,std::uint64_t character,
                              const RecoveredWorldEntry::Frame&);
    void bind(std::uint64_t session,std::uint64_t account,std::uint64_t character);
    // Includes authenticated prepared leases before world-tail readiness.
    [[nodiscard]] bool character_active(std::uint64_t account,std::uint64_t character) const noexcept;
    // Read-only binding identity for common mutation exclusion. No movement,
    // readiness, placement, packet or release behavior is changed by this view.
    [[nodiscard]] bool owns_repository(const RecoveredCharacterRepository& characters) const noexcept {
        return &characters_==&characters;
    }
    // Authenticated, world-ready location for same-scene routing.
    std::optional<std::uint16_t> scene(std::uint64_t session,std::uint64_t account,std::uint64_t character) const noexcept;
    // Bound current location, including the initial world-entry position before
    // the first move. Rejects stale SQLite baselines and pending transfers.
    std::optional<RecoveredPosition> current_location(std::uint64_t session,
        std::uint64_t account,std::uint64_t character) const;
    // CUSTOM-0159 pure GAME snapshot for paired guild world proof. Refuses
    // in-progress owned movement; does not certify the current DB saved row.
    // Outside SQL, separately compare current_location to this same snapshot.
    std::optional<RecoveredPosition> current_world_location(std::uint64_t session,
        std::uint64_t account,std::uint64_t character) const;
    // Pure read evidence for one actual ready binding and pose, not movement or
    // world admission authority. A new same-value prepare cannot revive it.
    class WorldLocationObservation {
    public:
        const RecoveredPosition& position()const noexcept{return position_;}
        bool same_binding(const WorldLocationObservation& other)const noexcept {
            return service_==other.service_&&session_==other.session_&&account_==other.account_&&
                character_==other.character_&&identity_&&identity_==other.identity_;
        }
    private:
        friend class RecoveredMovementService;
        WorldLocationObservation(const RecoveredMovementService* service,std::uint64_t session,
                std::uint64_t account,std::uint64_t character,RecoveredPosition position,
                std::shared_ptr<const std::uint8_t> identity)
            :service_(service),session_(session),account_(account),character_(character),position_(position),identity_(std::move(identity)){}
        const RecoveredMovementService* service_;
        std::uint64_t session_,account_,character_;
        RecoveredPosition position_;
        std::shared_ptr<const std::uint8_t> identity_;
    };
    std::optional<WorldLocationObservation> observe_world_location(std::uint64_t session,
        std::uint64_t account,std::uint64_t character)const;
    bool world_location_current(const WorldLocationObservation&)const;
    // Same actual ready owner only; an ordinary authorized step may change pose.
    bool world_binding_current(const WorldLocationObservation&)const;
    void resume_after_battle(std::uint64_t session,std::uint64_t account,std::uint64_t character);
    // Source-pinned destination check for a proposed town/indoor transfer.
    [[nodiscard]] bool qualifies_transfer_destination(std::uint16_t scene,
        std::uint16_t x,std::uint16_t y) const noexcept;
    // CUSTOM-0024: trusted isolated same-town transfer; not a client destination request.
    std::vector<std::uint8_t> begin_town_transfer(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y);
    std::vector<std::uint8_t> begin_indoor_transfer(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y);
    // CUSTOM-0032: first map-item use from the bound, unsaved town spawn.
    std::vector<std::uint8_t> begin_initial_indoor_transfer(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,std::uint16_t x,std::uint16_t y);
    std::vector<std::uint8_t> begin_outdoor_return(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y);
    // Scene0 packet/position support only; caller must separately qualify a portal trigger.
    std::vector<std::uint8_t> begin_island_transfer(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y);
    std::vector<std::uint8_t> begin_island_return(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y);
    // CUSTOM-0153: registry-exact source/target points in one qualified parent
    // scene. Independently rechecks owner, current baseline and both endpoints.
    std::vector<std::uint8_t> begin_registered_wilderness_transfer(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y);
    [[nodiscard]] bool has_cross_map_navigation() const noexcept {return cross_maps_.has_value();}
    [[nodiscard]] bool registered_cross_map_scene(std::uint16_t area,std::uint16_t scene) const noexcept;
    [[nodiscard]] bool qualified_cross_map_transfer(std::uint16_t area,std::uint16_t source_scene,
        std::uint16_t source_x,std::uint16_t source_y,std::uint16_t target_scene,
        std::uint16_t target_x,std::uint16_t target_y) const noexcept;
    std::vector<std::uint8_t> begin_registered_cross_map_transfer(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,const RecoveredPosition& expected,std::uint16_t scene,std::uint16_t x,std::uint16_t y);
    // One qualified kind registry for saved-entry, native61 and peer visibility.
    [[nodiscard]] std::optional<std::uint16_t> qualified_scene_kind(std::uint16_t area,std::uint16_t scene) const noexcept;
    [[nodiscard]] const WorldTransferCatalog* world_catalog() const noexcept {return world_catalog_?&*world_catalog_:nullptr;}
    std::vector<std::uint8_t> begin_world_transfer(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,const RecoveredPosition& expected,std::string_view route_id);
    std::vector<std::uint8_t> begin_npc_world_transfer(OwnedNpcTeleportOffer&,
        const OwnedNpcTeleportOffer::Identity&,const OwnedNpcTeleportOffer::Prepared&);
    // CUSTOM-0057: prepare the already source-qualified Island01 -> CityI1
    // arrival, then publish only after an external atomic item+position commit.
    struct OwnedIslandReturnPlan {
        std::uint64_t session,account,character;
        RecoveredPosition before,after;
        std::array<std::uint8_t,9> logical;
    };
    OwnedIslandReturnPlan prepare_owned_island_return(std::uint64_t session,
        std::uint64_t account,std::uint64_t character,const RecoveredPosition& expected) const;
    void commit_owned_island_return(const OwnedIslandReturnPlan& plan,
        const RecoveredPosition& persisted) noexcept;
    // CUSTOM-0052: only the registered current town/room pairs may use this.
    std::vector<std::uint8_t> begin_registered_door_transfer(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,const RecoveredPosition& expected,std::uint16_t scene,
        std::uint16_t x,std::uint16_t y);
    [[nodiscard]] bool registered_door_pair(std::uint16_t source_scene,std::uint16_t destination_scene) const noexcept;
    [[nodiscard]] bool registered_door_pair(std::uint16_t area,std::uint16_t source_scene,std::uint16_t destination_scene) const noexcept;
    [[nodiscard]] bool registered_parent_pair(std::uint16_t area,std::uint16_t source_scene,std::uint16_t destination_scene) const noexcept;
    std::vector<std::uint8_t> begin_registered_parent_transfer(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,const RecoveredPosition& expected,std::uint16_t scene,
        std::uint16_t x,std::uint16_t y);
    [[nodiscard]] bool qualifies_transfer_destination(std::uint16_t area,std::uint16_t scene,std::uint16_t x,std::uint16_t y) const noexcept;
    void finish_town_transfer(std::uint64_t session,std::uint64_t account,std::uint64_t character);
    struct CommittedMove {
        struct Step {
            std::uint16_t x,y;
            bool operator==(const Step&) const = default;
        };
        std::vector<std::uint8_t> reply;
        std::optional<RecoveredPosition> before;
        RecoveredPosition after;
        std::size_t displaced_steps{};
        // Ordered displaced destinations, published only after the batch commits.
        std::vector<Step> path;
    };
    // Actual CUSTOM-0095 mutation receipt plus the ORIGINAL batch ACKs/path.
    // Passive proof transport, not native5D issuer or socket/client acceptance.
    class OwnedCommittedMove final {
    public:
        OwnedCommittedMove(const OwnedCommittedMove&)=delete;
        OwnedCommittedMove& operator=(const OwnedCommittedMove&)=delete;
        OwnedCommittedMove(OwnedCommittedMove&&) noexcept=default;
        OwnedCommittedMove& operator=(OwnedCommittedMove&&) noexcept=default;
        const SqliteOwnedEquipmentTransaction::Committed& committed() const noexcept{return committed_;}
        const CommittedMove& movement() const noexcept{return movement_;}
        CommittedMove take_movement() && noexcept{return std::move(movement_);}
    private:
        friend class RecoveredMovementService;
        OwnedCommittedMove(CommittedMove movement,SqliteOwnedEquipmentTransaction::Committed committed) noexcept
            :movement_(std::move(movement)),committed_(std::move(committed)) {}
        CommittedMove movement_;
        SqliteOwnedEquipmentTransaction::Committed committed_;
    };
    struct MovePreview {
        std::uint16_t area,scene,before_x,before_y,x,y;
        std::size_t displaced_steps;
        bool operator==(const MovePreview&) const = default;
    };
    // Returns only after the validated batch (or trusted-host-selected prefix)
    // is durably committed. A stop predicate observes each validated step with
    // its own origin and displacement; its accepted step is ACKed, later steps
    // are neither validated nor ACKed. Empty keeps the complete legacy batch.
    // This is location evidence, not authorization or probability for an encounter.
    // The optional pure precommit check runs after path validation, before a DB
    // write or in-memory queue advance. It may reject by throwing.
    CommittedMove move_committed(std::uint64_t session,std::uint64_t account,
                                 std::uint64_t character,
                                 std::span<const RecoveredMovement::Request> requests,
                                 const std::function<void(const MovePreview&)>& precommit={},
                                 const std::function<bool(const MovePreview&)>& stop_after_step={});
    // CUSTOM-0095: actual normal-entry callback only, one atomic whole-batch
    // saved-pose/native-witness update. Complete current banks are mandatory;
    // no fallback, grant, stale-witness rebase or recovered native5D claim.
    CommittedMove move_committed_with_owned_material(Session&,SqliteOwnedEquipmentTransaction&,
        std::span<const RecoveredMovement::Request> requests);
    // Same actual owner, batch recipe, one joint COMMIT and publication checks;
    // return its private durable receipt without a later observe_committed read.
    OwnedCommittedMove move_committed_with_owned_material_and_receipt(Session&,SqliteOwnedEquipmentTransaction&,
        std::span<const RecoveredMovement::Request> requests);
    std::vector<std::uint8_t> move(std::uint64_t session,std::uint64_t account,
                                 std::uint64_t character,
                                 std::span<const RecoveredMovement::Request> requests);
    void remove(std::uint64_t session) noexcept;
private:
    struct Position {
        std::uint64_t account,character;
        int x=17,y=13;
        std::uint8_t slot=0;
        bool ready=false;
        bool transfer_pending=false;
        std::uint16_t scene=15,kind=2;
        std::uint16_t area=2;
        std::optional<RecoveredPosition> saved;
        std::optional<MovePreview> last_step;
        // Construct before insertion; normal Position copies retain the owner.
        std::shared_ptr<const std::uint8_t> incarnation=std::make_shared<const std::uint8_t>(0);
        bool operator==(const Position&) const = default;
    };
    struct PreparedMove {
        Position next;
        std::vector<std::uint8_t> response;
        std::vector<CommittedMove::Step> path;
        std::size_t displaced_steps{};
    };
    PreparedMove prepare_move_batch(const Position&,std::span<const RecoveredMovement::Request>,
        const std::function<bool(const MovePreview&)>& stop_after_step={}) const;
    void reject_owned_movement_mutation() const;
    const std::thread::id owned_movement_thread_=std::this_thread::get_id();
    mutable bool owned_movement_busy_=false,owned_movement_invalid_=false;
    RecoveredCharacterRepository& characters_;
    [[nodiscard]] bool cell_available(int x,int y) const noexcept;
    [[nodiscard]] bool cell_available(std::uint16_t scene,int x,int y) const noexcept;
    [[nodiscard]] bool cell_available(std::uint16_t area,std::uint16_t scene,int x,int y) const noexcept;
    std::vector<std::uint8_t> begin_transfer(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,const std::optional<RecoveredPosition>& expected,
        std::uint16_t source_scene,std::uint16_t scene,std::uint16_t x,std::uint16_t y,std::uint16_t area=2,
        bool reuse_same_scene=true,std::uint16_t destination_area=0);
    [[nodiscard]] std::uint16_t scene_kind(std::uint16_t area,std::uint16_t scene) const;
    std::optional<RecoveredIndoorGrid> grid_;
    std::map<std::uint16_t,RecoveredIndoorGrid> indoor_scenes_;
    std::map<std::uint16_t,RecoveredIndoorGrid> kunlun_indoor_scenes_;
    std::optional<RecoveredIslandEntryNavigation> island_;
    std::optional<RecoveredParentNavigation> island_full_;
    std::optional<RecoveredTownNavigation> town_;
    std::optional<RecoveredKunlunNavigation> kunlun_;
    std::optional<RecoveredParentNavigation> kunlun_parent_;
    std::optional<RecoveredCrossMapNavigation> cross_maps_;
    std::optional<WorldTransferCatalog> world_catalog_;
    std::shared_ptr<const RecoveredFruitNavigation> fruit_;
    RecoveredTownNavigation::Center center_{};
    std::uint16_t scene_=15,kind_=2,initial_x_=17,initial_y_=13;
    std::uint16_t initial_area_=2;
    bool town_source_consensus_=false;
    std::map<std::uint64_t,Position> active_;
};
}
