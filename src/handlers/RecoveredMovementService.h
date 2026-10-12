#pragma once
#include "db/RecoveredCharacterRepository.h"
#include "game/RecoveredIndoorGrid.h"
#include "game/RecoveredIslandEntryNavigation.h"
#include "game/RecoveredTownNavigation.h"
#include "game/RecoveredKunlunNavigation.h"
#include "game/RecoveredFruitNavigation.h"
#include "game/RecoveredParentNavigation.h"
#include "protocol/RecoveredMovement.h"
#include "protocol/RecoveredWorldEntry.h"
#include <filesystem>
#include <functional>
#include <map>
#include <memory>

namespace god2 {
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
    struct MovePreview {
        std::uint16_t area,scene,before_x,before_y,x,y;
        std::size_t displaced_steps;
    };
    // Returns only after the entire validated batch is durably committed.
    // This is location evidence, not authorization or probability for an encounter.
    // The optional pure precommit check runs after path validation, before a DB
    // write or in-memory queue advance. It may reject by throwing.
    CommittedMove move_committed(std::uint64_t session,std::uint64_t account,
                                 std::uint64_t character,
                                 std::span<const RecoveredMovement::Request> requests,
                                 const std::function<void(const MovePreview&)>& precommit={});
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
    };
    RecoveredCharacterRepository& characters_;
    [[nodiscard]] bool cell_available(int x,int y) const noexcept;
    [[nodiscard]] bool cell_available(std::uint16_t scene,int x,int y) const noexcept;
    [[nodiscard]] bool cell_available(std::uint16_t area,std::uint16_t scene,int x,int y) const noexcept;
    std::vector<std::uint8_t> begin_transfer(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,const std::optional<RecoveredPosition>& expected,
        std::uint16_t source_scene,std::uint16_t scene,std::uint16_t x,std::uint16_t y,std::uint16_t area=2);
    [[nodiscard]] std::uint16_t scene_kind(std::uint16_t area,std::uint16_t scene) const;
    std::optional<RecoveredIndoorGrid> grid_;
    std::map<std::uint16_t,RecoveredIndoorGrid> indoor_scenes_;
    std::map<std::uint16_t,RecoveredIndoorGrid> kunlun_indoor_scenes_;
    std::optional<RecoveredIslandEntryNavigation> island_;
    std::optional<RecoveredParentNavigation> island_full_;
    std::optional<RecoveredTownNavigation> town_;
    std::optional<RecoveredKunlunNavigation> kunlun_;
    std::optional<RecoveredParentNavigation> kunlun_parent_;
    std::shared_ptr<const RecoveredFruitNavigation> fruit_;
    RecoveredTownNavigation::Center center_{};
    std::uint16_t scene_=15,kind_=2,initial_x_=17,initial_y_=13;
    std::uint16_t initial_area_=2;
    bool town_source_consensus_=false;
    std::map<std::uint64_t,Position> active_;
};
}
