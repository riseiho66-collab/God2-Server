#pragma once
#include "game/SharedWorldHost.h"
#include "game/SharedTaiwanWorldLifecycle.h"
#include "game/SharedTaiwanWorldEntrySource.h"
#include "game/SharedTaiwanMovementSource.h"
#include "game/SharedTaiwanWorldRecordSource.h"
#include "game/SharedTaiwanNativeCharacterListSource.h"
#include "db/NativeMapCatalog.h"
#include "game/OwnedTaiwanReturnActorSavedSource.h"
#include <asio.hpp>
#include <functional>
#include "handlers/OwnedTaiwanPkRoomBackend.h"
#include <array>
#include <chrono>
#include <filesystem>
#include <memory>
#include <optional>
#include <stdexcept>
#include <utility>

namespace god2 {
class NativeSkillCatalog;
class OrdinaryMovementPolicyRepository;
class OwnedOrdinaryMovementPolicyReloads;
class NativeWorldEntrySnapshotRepository;
class SqliteNativeCharacterSummarySnapshotRepository;
class SqliteNativeWorldEntrySnapshotRepository;
class NativeEnemyDisplayCatalog;
class NativeNpcDisplayCatalog;
class SqliteWorldDisplayRepository;
class NativeEquipmentSnapshotRepository;
class SqliteNativeEquipmentSnapshotRepository;
class OwnedInventoryRepository;
class SqliteOwnedInventoryRepository;
class SqliteCompanionRepository;
class RecoveredOwnedCompanions;
class SharedTaiwanOwnedDeitySkillSource;
// Explicit Application common-world hosting only. No native frame, placement,
// scene authority or success callback is supplied by this plan or the host.
struct SharedWorldHostPlan {
    // Explicit complete CUSTOM PK hosting recipe; no native rule, seed or
    // return material is manufactured. Construct and drain runtime owners on
    // the actual game executor, retaining the original dependencies strongly.
    struct OwnedPkSources {
    private:
        friend class SharedTaiwanNativeWorldHostPlan;
        // Destroy last, after callable/dependency targets. Set only by the
        // exact one-use native Owner take; the public dependency is untouched.
        std::shared_ptr<const void> host_owner_;
    public:
        // Declared before callables so their destruction retains dependencies.
        std::shared_ptr<const void> dependency_owner;
        std::filesystem::path fight_archive;
        OwnedTaiwanPkRoomBackend::Parameters parameters;
        std::array<std::uint8_t,2> order;
        std::chrono::milliseconds retry;
        OwnedTaiwanPkEntryPreparation::Seed seed;
        OwnedTaiwanPkRoomBackend::ReturnSceneSource return_scene;
        OwnedPkSources(std::filesystem::path archive,OwnedTaiwanPkRoomBackend::Parameters actual_parameters,
            std::array<std::uint8_t,2> actual_order,std::chrono::milliseconds actual_retry,
            OwnedTaiwanPkEntryPreparation::Seed actual_seed,
            OwnedTaiwanPkRoomBackend::ReturnSceneSource actual_return_scene,
            std::shared_ptr<const void> actual_dependency_owner)
            :dependency_owner(std::move(actual_dependency_owner)),fight_archive(std::move(archive)),
             parameters(actual_parameters),order(actual_order),retry(actual_retry),
             seed(std::move(actual_seed)),return_scene(std::move(actual_return_scene)) {
            require_complete();
        }
        void require_complete()const {
            if(fight_archive.empty()||!seed||!return_scene||!dependency_owner)
                throw std::invalid_argument("Owned PK hosting requires original archive/seed/full return/dependencies");
            // Unchanged explicit CUSTOM-0125 backend bounds, not native defaults.
            if(parameters.power_percent>10000||parameters.defense_percent>100||parameters.critical_chance_bp>10000||
               parameters.critical_multiplier_percent<100||parameters.critical_multiplier_percent>1000||
               (order!=std::array<std::uint8_t,2>{0,1}&&order!=std::array<std::uint8_t,2>{1,0})||
               retry.count()<1||retry>std::chrono::seconds(1))
                throw std::invalid_argument("Owned PK hosting requires explicit bounded basic/order/retry policy");
        }
    };
    struct Context {
        RecoveredCharacterRepository& characters;
        const NativeMapCatalog& maps;
        asio::any_io_executor game;
        std::shared_ptr<SharedWorldHost> common_world;
        // Application's exact shared SQLite reader, borrowed through game-owner
        // drain. Null is legacy source absence, never an empty learned list.
        // TW uses its pinned dataset; CN must qualify all native CN rows with
        // CnSharedSkillCatalog. Catalog membership supplies no gameplay grants.
        const NativeSkillCatalog* native_skills=nullptr;
        // Explicit same-Database raw delivery reader. Borrowed until game-owner
        // vault/handler drain, never a fake shared Database lifetime token.
        // Absent for existing legacy/generic plans; absent is not empty material.
        NativeWorldEntrySnapshotRepository* native_world_entries=nullptr;
        AccountRepository* accounts=nullptr;
        NativeCharacterSummarySnapshotRepository* native_character_summaries=nullptr;
        // Explicit same object as the reader, only for actual List issuer
        // preparation. Borrowed through game-owner drain; accessor does no DDL.
        SqliteNativeCharacterSummarySnapshotRepository* native_character_summary_writer=nullptr;
        // Exact same stored-entry reader object; explicit issuer only. Access
        // performs no DDL and borrows the existing Application game lifetime.
        SqliteNativeWorldEntrySnapshotRepository* native_world_entry_writer=nullptr;
        // Exact Application same-Database catalog, borrowed through game-owner
        // drain. Accessor does no SQL/DDL; absence is not a qualified empty bank.
        const NativeEnemyDisplayCatalog* native_enemy_displays=nullptr;
        // Exact same optional delivery-witness reader/writer, borrowed through
        // game drain. No native grants, schema creation or equip rule defaults.
        NativeEquipmentSnapshotRepository* native_equipment_snapshots=nullptr;
        SqliteNativeEquipmentSnapshotRepository* native_equipment_snapshot_writer=nullptr;
        // Same optional shared custody reader/writer; no grants, DDL or legacy
        // item import. Borrowed until actual Application game-owner drain.
        OwnedInventoryRepository* owned_inventory=nullptr;
        SqliteOwnedInventoryRepository* owned_inventory_writer=nullptr;
        // Actual existing Application same-DB owned companion reader. Stored
        // selected30/31/34 evidence supplies no battle actor or87/grant/cost.
        // Borrowed through the game-owner drain; no schema install on access.
        SqliteCompanionRepository* companions=nullptr;
        // CUSTOM-0147: same actual helper/source through game-owner drain.
        // Null retains saved-observation-only plans; no synthetic publisher.
        RecoveredOwnedCompanions* owned_companions=nullptr;
        std::shared_ptr<SharedTaiwanOwnedDeitySkillSource> owned_deity_skills={};
        // CUSTOM-0148: Application exclusively publishes initial30/31/34/35.
        // Default native scene ownership of all initial records is unchanged.
        bool app_owned_initial_deities=false;
        // CUSTOM-0149 explicit saved player22/24 publisher; requires deities.
        bool app_owned_initial_player=false;
        bool app_owned_pk=false; // Explicit complete hosted PK only; default off.
        // Actual same-Database initial saved-input owner, selected only
        // with all existing entry/equipment/inventory capabilities. No DB borrow.
        std::shared_ptr<OwnedTaiwanReturnActorSavedSource::InitialIssuer> initial_actor_inputs{};
        // LAST: exact existing same-Database scene/catalog readers. Borrowed
        // through Application game-owner drain; no placement defaults or DDL.
        SqliteWorldDisplayRepository* world_displays=nullptr;
        const NativeNpcDisplayCatalog* native_npc_displays=nullptr;
        // LAST CUSTOM-0150 borrowed actual same-Database policy reader; no DDL.
        OrdinaryMovementPolicyRepository* ordinary_movement_policies=nullptr;
        // LAST CUSTOM-0150 actual Application GAME scheduler owner. Same-cache
        // registration only; legacy plans may leave it absent. No input SQL.
        std::shared_ptr<OwnedOrdinaryMovementPolicyReloads> ordinary_movement_policy_reloads{};
    };
    // Called once on the actual Application game owner before any listener.
    // Assemble the real Entered owner; retain its actual resources strongly in
    // the returned callable. Do not retain Context/borrowed endpoint locals,
    // open listeners, send, persist, pump events or reenter Application here.
    // Entered remains responsible for real native publication and InWorld;
    // a true/state-only callback does not qualify the missing gameplay route.
    // Full native entry/real saved placement/WorldOwner/5D/recipient sources
    // remain caller-owned; existing Application candidate bytes stay candidates.
    std::function<SharedTaiwanWorldLifecycle::Entered(const Context&)> make_taiwan_entered;
    // Optional explicit full native TW entry source, assembled once on this
    // same game owner from actual Context resources. If selected, the returned
    // Entry must be nonempty and own its real supplier; no candidate fallback.
    // Do not retain Context references or manufacture placement/profile bytes.
    // The trusted provider must qualify complete native material against these
    // actual repository/maps; SharedTaiwanWorldEntrySource::create supplies the
    // mandatory NativeSource/Current pre-use contract. An arbitrary Entry or
    // unconditional Current is not native qualification or later queue proof.
    std::function<SharedTaiwanWorldEntrySource::Entry(const Context&)> make_taiwan_world_entry;
    // Explicit deferred native scene owner, exclusive with make_taiwan_entered.
    // Its actual cancellation owner is mandatory; no success-only replacement.
    std::function<SharedTaiwanWorldLifecycle::AsyncOwner(const Context&)> make_taiwan_entered_async;
    // Optional explicit native movement source, assembled once on this game
    // owner from the same actual common host. Requires the async scene and full
    // native entry above. Movement, exact Session release and active dispatch
    // invalidation are mandatory; caught outer reentry must prevent later CAS.
    // real native WorldOwner/cells/authority/full5D and rules remain supplied.
    // No fallback to the frozen CUSTOM movement or mixed world-record dispatcher.
    std::function<SharedTaiwanMovementSource::Binding(const Context&)> make_taiwan_movement;
    // Optional explicit native mixed-record dispatcher. Assembled on this
    // same game owner after the actual movement source. It must retain that
    // exact source and the real nonmovement handlers/Current, not call a vault
    // movement facade recursively or reuse frozen CUSTOM gameplay implicitly.
    // Both release and active invalidation are mandatory. Session receives
    // exactly one dispatcher; a mixed plan replaces only the explicit opt-in.
    std::function<SharedTaiwanWorldRecordSource::Binding(const Context&)> make_taiwan_world_records;
    // Only the explicit stored-entry plan selects this optional capability.
    // Application supplies its exact migrated Database reader, with no schema
    // install/import or stored data generation. Requires full entry factory.
    bool requires_native_world_entry_snapshots=false;
    // Explicit full TW07/issued-token source on this same Context. Default
    // legacy plans do not request the optional reader or replace their list.
    std::function<SharedTaiwanNativeCharacterListSource::Binding(const Context&)> make_taiwan_native_characters;
    bool requires_native_character_summaries=false;
    bool requires_native_equipment_snapshots=false;
    bool requires_owned_inventory_storage=false;
    // Explicit complete native-source plan only. Common character keys stay
    // uint64; the full entry and prepared private lease supply the scene handle.
    TaiwanWorldEntryIdentity taiwan_entry_identity=TaiwanWorldEntryIdentity::SelectedCharacter;
    // Explicit constructed mixed plan only; no ordinary CLI/default activation.
    bool owned_deity_selection_publication=false;
    // Advertised only by a factory enforcing the exact initial deity policy.
    bool supports_app_owned_initial_deities=false;
    // CUSTOM-0149 actual factory enforcing exclusive player/deity boundaries.
    bool supports_app_owned_initial_player=false;
    // Actual same-Context native Owner recipe, taken at most once. Default
    // plans retain absence; no ordinary configuration or supplier is activated.
    std::function<std::optional<OwnedPkSources>(const Context&)> make_owned_taiwan_pk_sources;
    // Pure revocation holder only; no affine callbacks in network copies.
    // Null explicitly preserves legacy plans. Does not initialize actor status.
    std::function<std::shared_ptr<TaiwanActorStatusWriteFence>(const Context&)> make_taiwan_actor_status_write_fence;
    std::function<std::shared_ptr<TaiwanActorStatusIncarnationSource>(const Context&)> make_taiwan_actor_status_incarnations;
};
}
