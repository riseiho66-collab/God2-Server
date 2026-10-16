#pragma once
#include "core/SharedWorldHostPlan.h"
#include "game/SharedTaiwanWorldEntered.h"
#include "game/SharedTaiwanNativeMovementHost.h"
#include "game/SharedTaiwanNativeChatSource.h"
#include "game/SharedTaiwanNativeSpectatorSource.h"
#include "game/SharedTaiwanStoredWorldEntrySource.h"
#include "game/SharedTaiwanCharacterListHandoff.h"
#include "game/SharedTaiwanNativeCharacterOfferSource.h"
#include "game/SharedTaiwanNativeWorldEntryOfferSource.h"
#include "game/SharedTaiwanNativeEquipmentPublicationSource.h"
#include "game/SharedTaiwanOwnedItemSelectionSource.h"
#include "game/SharedTaiwanOwnedItemRequestSource.h"
#include "game/SharedTaiwanOwnedInventoryReplySource.h"
#include "game/SharedTaiwanOwnedBagMoveSource.h"
#include "game/SharedTaiwanNativeSkillCommandSource.h"
#include "game/SharedTaiwanOwnedDeitySkillSource.h"
#include "game/OwnedTaiwanPkReturnSceneSource.h"
#include "game/TaiwanNativeActorResourceSource.h"
#include "game/TaiwanActorStatusOwnedSource.h"
#include <utility>
#include <optional>
#include <string>

namespace god2 {
// Assemble the existing Application entry, initial publication and movement
// callers from one actual common-world Context. No native input is defaulted.
class SharedTaiwanNativeWorldHostPlan final {
public:
    enum class Dispatch {MovementOnly,MixedRecords};
    struct RecordSources {
        // Existing primary factory retains its name; it also holds explicitly
        // supplied independent secondary state. Empty until a real publisher
        // installs actual main/aux/control (and optional secondary) state.
        static std::shared_ptr<SharedTaiwanIssuedSkillSource> issued_primary_skills(
            const SharedWorldHostPlan::Context&,std::size_t actual_session_capacity);
        // Concrete same-Application persisted selected30/31/all34 + definition
        // observer. Does not install a C35 owner, generate87 or opt Main in.
        static std::shared_ptr<SharedTaiwanOwnedDeitySkillSource> owned_deity_skills(
            const SharedWorldHostPlan::Context&);
        SharedTaiwanWorldRecordSource::OtherBinding others;
        SharedTaiwanWorldRecordSource::Current current;
        SharedTaiwanWorldRecordSource::Budgets budgets;
        // Explicit same-Context full native skill catalog and actual battle
        // owner. Only this complete binding selects the separate C35 grammar.
        // It supplies no learned/grant/cost/rule/reply defaults and opts no
        // ordinary Main route in. Can compose before or after native chat.
        static RecordSources with_native_skills(const SharedWorldHostPlan::Context&,
            std::shared_ptr<SharedTaiwanIssuedSkillSource>,
            std::shared_ptr<SharedTaiwanNativeSkillCommandSource::WorldOwner>,
            SharedTaiwanNativeSkillCommandSource::Budgets,RecordSources);
        // CUSTOM-0093 complete conditional C24 bag mutation and41 reply source.
        // Both real stores must be explicitly present; no caller action stub.
        static RecordSources with_owned_bag_moves(const SharedWorldHostPlan::Context&,RecordSources);
        static RecordSources with_owned_bag_move_material(const SharedWorldHostPlan::Context&,RecordSources);
        // Construct actual ready owned reader on this same game Context and
        // intercept original C28 in mixed dispatch. Complete action/rules and
        // real native reply are mandatory; no defaults or Main opt-in.
        static RecordSources with_owned_item_requests(const SharedWorldHostPlan::Context&,
            SharedTaiwanOwnedItemRequestSource::Action,RecordSources);
        // Actual same-connection full historical definition observations are
        // attached to the selected owned alias. This supplies data, not rules.
        static RecordSources with_owned_item_definition_requests(const SharedWorldHostPlan::Context&,
            SharedTaiwanOwnedItemRequestSource::Action,RecordSources);
        static RecordSources with_owned_item_deity_equipment_requests(const SharedWorldHostPlan::Context&,
            SharedTaiwanOwnedItemRequestSource::Action,RecordSources);
        RecordSources(SharedTaiwanWorldRecordSource::OtherBinding actual_others,
            SharedTaiwanWorldRecordSource::Current actual_current,
            SharedTaiwanWorldRecordSource::Budgets actual_budgets)
            :others(std::move(actual_others)),current(std::move(actual_current)),budgets(actual_budgets) {}
        // Actual same-Context source construction for the mixed plan. The
        // caller supplies complete native chat authority/profile and remaining
        // handlers; this factory does not select default audience or rules.
        static RecordSources with_native_chat(const SharedWorldHostPlan::Context&,
            std::shared_ptr<SharedTaiwanNativeChatSource::WorldOwner>,
            std::shared_ptr<const ChineseText>,SharedTaiwanNativeChatSource::Budgets,
            std::size_t actual_session_capacity,SharedTaiwanWorldRecordSource::OtherBinding remaining,
            SharedTaiwanWorldRecordSource::Current,SharedTaiwanWorldRecordSource::Budgets);
        // Explicit actual typed6E owner from the same Context. This selects
        // parser availability only after real bindings are installed; no
        // spectator permission, battle state or default native reply follows.
        static RecordSources with_native_chat_and_spectator(const SharedWorldHostPlan::Context&,
            std::shared_ptr<SharedTaiwanNativeChatSource::WorldOwner>,
            std::shared_ptr<const ChineseText>,SharedTaiwanNativeChatSource::Budgets,
            std::size_t actual_session_capacity,
            std::shared_ptr<SharedTaiwanNativeSpectatorSource::WorldOwner>,SharedTaiwanNativeSpectatorSource::Budgets,
            SharedTaiwanWorldRecordSource::OtherBinding remaining,
            SharedTaiwanWorldRecordSource::Current,SharedTaiwanWorldRecordSource::Budgets);
        // Explicit supplied native CD/D0 publication source. Installed once in
        // this same host; it supplies immutable actual UI observations only.
        // No data, target namespace, spectator admission or Main opt-in defaults.
        static RecordSources with_native_chat_spectator_and_publication(const SharedWorldHostPlan::Context&,
            std::shared_ptr<SharedTaiwanNativeChatSource::WorldOwner>,
            std::shared_ptr<const ChineseText>,SharedTaiwanNativeChatSource::Budgets,
            std::size_t actual_session_capacity,
            std::shared_ptr<SharedTaiwanNativeSpectatorSource::WorldOwner>,SharedTaiwanNativeSpectatorSource::Budgets,
            SharedTaiwanWorldRecordSource::OtherBinding remaining,
            SharedTaiwanWorldRecordSource::Current,SharedTaiwanWorldRecordSource::Budgets,
            std::shared_ptr<SharedNativeSpectatorPublication> actual_publication,
            std::shared_ptr<SharedNativeSpectatorTargets> actual_targets = {},
            std::shared_ptr<SharedTaiwanNativeSpectatorSource::CloseOwner> actual_close_owner = {});
    };
    struct Sources {
        SharedTaiwanWorldEntrySource::NativeSource entry;
        SharedTaiwanWorldEntered::Source entered;
        std::shared_ptr<TaiwanMovementRules> movement_rules;
        SharedTaiwanNativeMovementHost::InputSource movement_resources;
        std::size_t actual_session_capacity;
        std::optional<RecordSources> records;
        std::optional<SharedTaiwanNativeCharacterListSource::Binding> characters;
        SharedTaiwanWorldEntrySource::Prepare entry_prepare;
        // CUSTOM-0095 explicit ordinary-walk custody retention on the actual
        // common connection. Absence preserves the existing movement path.
        std::shared_ptr<SqliteOwnedEquipmentTransaction> movement_custody;
        std::optional<SharedWorldHostPlan::OwnedPkSources> owned_pk;
        // Explicit revocation-only monitor on the actual same common host.
        std::shared_ptr<TaiwanActorStatusWriteFence> actor_status_write_fence;
        std::shared_ptr<TaiwanActorStatusIncarnationSource> actor_status_incarnations;
        static Sources with_actor_status_write_fence(const SharedWorldHostPlan::Context&,Sources);
        static Sources with_actor_status_incarnations(const SharedWorldHostPlan::Context&,Sources);
        static Sources with_owned_inventory_movement(const SharedWorldHostPlan::Context&,Sources);
        Sources(SharedTaiwanWorldEntrySource::NativeSource native_entry,
            SharedTaiwanWorldEntered::Source native_entered,
            std::shared_ptr<TaiwanMovementRules> rules,
            SharedTaiwanNativeMovementHost::InputSource resources,std::size_t capacity,
            std::optional<RecordSources> native_records=std::nullopt,
            std::optional<SharedTaiwanNativeCharacterListSource::Binding> native_characters=std::nullopt,
            SharedTaiwanWorldEntrySource::Prepare actual_entry_issuer={},
            std::shared_ptr<SqliteOwnedEquipmentTransaction> actual_movement_custody={},
            std::optional<SharedWorldHostPlan::OwnedPkSources> actual_owned_pk=std::nullopt,
            std::shared_ptr<TaiwanActorStatusWriteFence> actual_status_write_fence={},
            std::shared_ptr<TaiwanActorStatusIncarnationSource> actual_status_incarnations={})
            :entry(std::move(native_entry)),entered(std::move(native_entered)),
             movement_rules(std::move(rules)),movement_resources(std::move(resources)),
             actual_session_capacity(capacity),records(std::move(native_records)),characters(std::move(native_characters)),
             entry_prepare(std::move(actual_entry_issuer)),movement_custody(std::move(actual_movement_custody)),
             owned_pk(std::move(actual_owned_pk)),actor_status_write_fence(std::move(actual_status_write_fence)),
             actor_status_incarnations(std::move(actual_status_incarnations)) {}
    };
    // Called once on Application's game owner. The returned suppliers retain
    // their real entry/peer/resource/Current/Authority dependencies strongly.
    // Never retain Context or borrowed endpoint locals. Repository/catalog
    // connections must outlive the existing Application vault and its drain.
    // The factory itself must not own game-affine runtime objects on main;
    // create those in this callback. No listeners, sends, writes or event pumps.
    using SourceFactory=std::function<Sources(const SharedWorldHostPlan::Context&)>;
    // Same complete scene/movement suppliers, plus actual stored-material
    // qualification. This form has no placeholder/native-entry callback slot.
    struct StoredSources {
        struct ListSources {
            SharedTaiwanNativeCharacterListSource::TargetSource target;
            SharedTaiwanNativeCharacterListSource::Qualify qualify;
            SharedTaiwanNativeCharacterListSource::Publish publish;
            SharedTaiwanNativeCharacterListSource::LinkSource link;
            std::shared_ptr<SharedTaiwanCharacterListHandoff> handoff;
            SharedTaiwanNativeCharacterOfferSource::Supply offer;
            static ListSources with_handoff(SharedTaiwanNativeCharacterListSource::TargetSource,
                SharedTaiwanNativeCharacterListSource::Qualify,std::shared_ptr<SharedTaiwanCharacterListHandoff>);
            // Construct the config owner inside the actual game Context
            // factory; no borrowed Context or policy-provided count retained.
            static ListSources with_configured_handoff(const SharedWorldHostPlan::Context&,
                std::shared_ptr<const TaiwanNativeClientGroupConfiguration>,std::string client_sha256,
                std::size_t actual_session_capacity,SharedTaiwanCharacterListHandoff::Live,
                SharedTaiwanCharacterListHandoff::Authority,
                SharedTaiwanNativeCharacterListSource::TargetSource,SharedTaiwanNativeCharacterListSource::Qualify,
                SharedTaiwanNativeCharacterOfferSource::Supply actual_offer={});
        };
        SharedTaiwanStoredWorldEntrySource::Qualify entry_qualify;
        SharedTaiwanWorldEntered::Source entered;
        std::shared_ptr<TaiwanMovementRules> movement_rules;
        SharedTaiwanNativeMovementHost::InputSource movement_resources;
        std::size_t actual_session_capacity;
        std::optional<RecordSources> records;
        std::optional<ListSources> characters;
        SharedTaiwanNativeWorldEntryOfferSource::Supply entry_offer;
        std::shared_ptr<SqliteOwnedEquipmentTransaction> movement_custody;
        std::optional<SharedWorldHostPlan::OwnedPkSources> owned_pk;
        std::shared_ptr<TaiwanActorStatusWriteFence> actor_status_write_fence;
        std::shared_ptr<TaiwanActorStatusIncarnationSource> actor_status_incarnations;
        static StoredSources with_actor_status_write_fence(const SharedWorldHostPlan::Context&,StoredSources);
        static StoredSources with_actor_status_incarnations(const SharedWorldHostPlan::Context&,StoredSources);
        static StoredSources with_owned_inventory_movement(const SharedWorldHostPlan::Context&,StoredSources);
        // Actual same-Context scene inputs -> complete entry producer -> the
        // existing stored-entry issuer/CAS path. Call inside StoredSourceFactory.
        // Does not load NPC bytes, install a catalog, infer opaque2A or opt Main in.
        static SharedTaiwanNativeWorldEntryOfferSource::Supply scene_entry_offer(
            const SharedWorldHostPlan::Context&,std::shared_ptr<const TaiwanNativeNpcSceneGroups>,
            SharedTaiwanNativeWorldEntryOfferSource::SceneSupply);
        static SharedTaiwanNativeWorldEntryOfferSource::Supply scene_entry_offer(
            const SharedWorldHostPlan::Context&,std::shared_ptr<const TaiwanNativeNpcSceneGroups>,
            std::shared_ptr<const TaiwanNativeTransformCards>,
            SharedTaiwanNativeWorldEntryOfferSource::SceneSupply);
        // Install paired issuer and post-COMMIT Supply/Current resource checks
        // from the same actual Context. Existing full qualifier is required;
        // refuse replacement of an already selected entry issuer.
        static StoredSources with_scene_entry_content(const SharedWorldHostPlan::Context&,
            std::shared_ptr<const TaiwanNativeNpcSceneGroups>,
            std::shared_ptr<const TaiwanNativeTransformCards>,
            SharedTaiwanNativeWorldEntryOfferSource::SceneSupply,StoredSources);
        // Same Application writer/read lifecycle, with full immutable DrvDoll
        // source facts available to the mandatory actual complete producer.
        static StoredSources with_scene_entry_content(const SharedWorldHostPlan::Context&,
            std::shared_ptr<const TaiwanNativeNpcSceneGroups>,
            std::shared_ptr<const TaiwanNativeTransformCards>,std::shared_ptr<const TaiwanNativeDrvDoll>,
            SharedTaiwanNativeWorldEntryOfferSource::SceneSupply,StoredSources);
        // Ordinary Drv/HeroDoll full sources reach the same actual producer,
        // paired stored qualifier and Application writer/read lifecycle.
        static StoredSources with_scene_entry_content(const SharedWorldHostPlan::Context&,
            std::shared_ptr<const TaiwanNativeNpcSceneGroups>,
            std::shared_ptr<const TaiwanNativeTransformCards>,std::shared_ptr<const TaiwanNativeDrvDoll>,
            std::shared_ptr<const TaiwanNativeActorResourceBank>,
            SharedTaiwanNativeWorldEntryOfferSource::SceneSupply,StoredSources);
        // CUSTOM-0133: same game Context and the exact bank already installed
        // by the full scene-entry overload. Replaces the recipe's mandatory
        // return supplier with freshly authored complete ordinary actors.
        // Actual live resource/status owners and explicit policy are required;
        // unsupported domains fail. Main/default activation remains absent.
        static StoredSources with_owned_pk_return_profiles(const SharedWorldHostPlan::Context&,
            std::shared_ptr<const TaiwanNativeActorResourceBank>,TaiwanCustomFullActorProfile::Policy,
            OwnedTaiwanPkReturnSceneSource::Selection,OwnedTaiwanPkReturnSceneSource::MaterialSources,StoredSources);
        struct OwnedPkProfileRecipe {
            std::shared_ptr<const void> dependency_owner;
            std::filesystem::path fight_archive;
            OwnedTaiwanPkRoomBackend::Parameters parameters;
            std::array<std::uint8_t,2> order;
            std::chrono::milliseconds retry;
            OwnedTaiwanPkEntryPreparation::Seed seed;
            OwnedPkProfileRecipe(std::shared_ptr<const void> dependency,std::filesystem::path archive,
                OwnedTaiwanPkRoomBackend::Parameters actual_parameters,std::array<std::uint8_t,2> actual_order,
                std::chrono::milliseconds actual_retry,OwnedTaiwanPkEntryPreparation::Seed actual_seed)
                :dependency_owner(std::move(dependency)),fight_archive(std::move(archive)),parameters(actual_parameters),
                 order(actual_order),retry(actual_retry),seed(std::move(actual_seed)) {}
        };
        // First-time recipe assembly: no earlier external ReturnScene supplier
        // or dummy callback is needed. Only the actual SceneOwner supplies it.
        static StoredSources with_owned_pk_return_profiles(const SharedWorldHostPlan::Context&,
            std::shared_ptr<const TaiwanNativeActorResourceBank>,TaiwanCustomFullActorProfile::Policy,
            OwnedTaiwanPkReturnSceneSource::Selection,OwnedTaiwanPkReturnSceneSource::MaterialSources,
            OwnedPkProfileRecipe,StoredSources);
        struct ActualStatusSources {
            // with_owned_pk_return_resources also requires this StoredSources'
            // actual actor_status_incarnations. It stamps private profile scope;
            // callback returns real status with both scope fields initially empty.
            // Actual status writer/lifecycle ownership is still mandatory.
            // No packet absence or immutable resource pin proves ordinary status.
            std::shared_ptr<const void> dependency_owner;
            std::function<std::optional<TaiwanCustomFullActorProfile::StatusInput>(
                std::shared_ptr<const OwnedTaiwanPkReturnSceneSource::Input>,std::size_t,
                const OwnedTaiwanPkReturnSceneSource::Equipment&,const SharedWorldPresence::Lease&)> status;
        };
        // CUSTOM-0133 explicit server resource generation / physical selection
        // owner, created inside this same actual Context from installed banks.
        // Native contexts/actions/bounds and real status source have no defaults.
        // Actual private shared population input reaches both material owners.
        static StoredSources with_owned_pk_return_resources(const SharedWorldHostPlan::Context&,
            std::shared_ptr<const TaiwanNativeActorResourceBank>,TaiwanCustomFullActorProfile::Policy,
            OwnedTaiwanPkReturnSceneSource::Selection,TaiwanNativeActorResourceSource::Configuration,
            ActualStatusSources,OwnedPkProfileRecipe,StoredSources);
        // Explicit CUSTOM-0133 initial scene install owns the ordinary clear
        // state. No caller-supplied status callback or lazy observation mint.
        // The actual install/cleanup and incarnation remain mandatory; complete
        // writer exclusion/private byte permits are separate unfinished work.
        // The same Profile/resource/status owners also author the actual ordered
        // initial incoming actors and directed post-install outward status.
        // Same-DB NPC observations qualify genuine ordered scene bytes; every
        // opaque record and original selection remain genuine-supplier owned.
        // No default Main, complete placements or full writer exclusion follows.
        static StoredSources with_owned_pk_return_owned_status(const SharedWorldHostPlan::Context&,
            std::shared_ptr<const TaiwanNativeActorResourceBank>,TaiwanCustomFullActorProfile::Policy,
            OwnedTaiwanPkReturnSceneSource::Selection,TaiwanNativeActorResourceSource::Configuration,
            TaiwanActorStatusOwnedSource::Policy,OwnedPkProfileRecipe,StoredSources);
        // Construct on startup's game owner without writes. The returned
        // game-only closure accepts a future real post-COMMIT token; retain it
        // in the later request owner, never retain this borrowed Context.
        // Borrowed repositories must outlive the Application vault/drain.
        using EquipmentPublicationFactory=std::function<std::shared_ptr<SharedTaiwanNativeEquipmentPublicationSource>(
            SqliteNativeEquipmentSnapshotRepository::Committed)>;
        static EquipmentPublicationFactory equipment_publication_factory(const SharedWorldHostPlan::Context&);
        // Both existing storage flags must be explicitly supplied. Same actual
        // Application writers/connection; this construction performs no writes.
        static std::shared_ptr<SqliteOwnedEquipmentTransaction> owned_equipment_transaction(
            const SharedWorldHostPlan::Context&);
        using OwnedEquipmentPublicationFactory=std::function<std::shared_ptr<SharedTaiwanNativeEquipmentPublicationSource>(
            SqliteOwnedEquipmentTransaction::Committed)>;
        static OwnedEquipmentPublicationFactory owned_equipment_publication_factory(
            const SharedWorldHostPlan::Context&,std::shared_ptr<SqliteOwnedEquipmentTransaction>);
        // Explicit existing-entry appearance synchronization. Requires all
        // three actual reader/writer pairs in the same Application Context.
        // No first entry, item/equip rule, native field defaults or Main opt-in.
        static std::shared_ptr<SqliteOwnedEquipmentTransaction> owned_equipment_entry_transaction(
            const SharedWorldHostPlan::Context&);
        using OwnedEquipmentEntryPublicationFactory=std::function<std::shared_ptr<SharedTaiwanNativeEquipmentPublicationSource>(
            SqliteOwnedEquipmentTransaction::EntryCommitted)>;
        static OwnedEquipmentEntryPublicationFactory owned_equipment_entry_publication_factory(
            const SharedWorldHostPlan::Context&,std::shared_ptr<SqliteOwnedEquipmentTransaction>);
        // Actual same-Context transaction and owned reader retained on game.
        // Invocation prepares explicit inventory bytes BEFORE mutation. The
        // returned component cannot stand in for full equip rules/replies.
        using OwnedInventoryReplyFactory=std::function<std::shared_ptr<SharedTaiwanOwnedInventoryReplySource>(
            Session&,const Session::NativeWorldSelectionInput&,const SharedTaiwanOwnedItemSelectionSource::Selection&,
            SqliteOwnedEquipmentTransaction::Before,SqliteOwnedEquipmentTransaction::State,
            std::vector<SharedTaiwanOwnedInventoryReplySource::Operation>,SharedTaiwanOwnedInventoryReplySource::Budgets)>;
        static OwnedInventoryReplyFactory owned_inventory_reply_factory(
            const SharedWorldHostPlan::Context&,std::shared_ptr<SqliteOwnedEquipmentTransaction>,
            bool definitions=false,bool deity_equipment=false);
        // Same actual Application common custody/presence -> native C28 owned
        // selection reader, constructed on game. No actual equip/rule handler
        // is installed and no legacy snapshot becomes native authority here.
        static std::shared_ptr<SharedTaiwanOwnedItemSelectionSource> owned_item_selection(
            const SharedWorldHostPlan::Context&,bool definitions=false,bool deity_equipment=false);
        StoredSources(SharedTaiwanStoredWorldEntrySource::Qualify qualify,
            SharedTaiwanWorldEntered::Source native_entered,std::shared_ptr<TaiwanMovementRules> rules,
            SharedTaiwanNativeMovementHost::InputSource resources,std::size_t capacity,
            std::optional<RecordSources> native_records=std::nullopt,std::optional<ListSources> native_characters=std::nullopt,
            SharedTaiwanNativeWorldEntryOfferSource::Supply actual_entry_offer={},
            std::shared_ptr<SqliteOwnedEquipmentTransaction> actual_movement_custody={},
            std::optional<SharedWorldHostPlan::OwnedPkSources> actual_owned_pk=std::nullopt,
            std::shared_ptr<TaiwanActorStatusWriteFence> actual_status_write_fence={},
            std::shared_ptr<TaiwanActorStatusIncarnationSource> actual_status_incarnations={})
            :entry_qualify(std::move(qualify)),entered(std::move(native_entered)),
             movement_rules(std::move(rules)),movement_resources(std::move(resources)),
             actual_session_capacity(capacity),records(std::move(native_records)),characters(std::move(native_characters)),
             entry_offer(std::move(actual_entry_offer)),movement_custody(std::move(actual_movement_custody)),
             owned_pk(std::move(actual_owned_pk)),actor_status_write_fence(std::move(actual_status_write_fence)),
             actor_status_incarnations(std::move(actual_status_incarnations)) {}
    private:
        friend class SharedTaiwanNativeWorldHostPlan;
        // Issued only by the full scene-content assembly, not caller scalars.
        std::shared_ptr<const TaiwanNativeActorResourceBank> scene_actor_bank_;
        std::shared_ptr<const TaiwanNativeDrvDoll> scene_drv_doll_bank_;
        std::shared_ptr<const void> scene_entry_binding_;
        bool return_profiles_installed_=false;
        // Private one-shot request from the actual owned-clear recipe only.
        // External status/profile recipes keep their original initial source.
        bool initial_profiles_requested_=false;
        void require_profile_entry_binding() const;
    };
    using StoredSourceFactory=std::function<StoredSources(const SharedWorldHostPlan::Context&)>;
    // Explicit Application Context -> exact shared raw reader -> NativeSource
    // -> existing guarded Sources/Owner/entry/scene/movement composition.
    // Build identity and real full material qualification remain mandatory.
    // All runtime suppliers are created on game owner in the supplied factory;
    // calling this metadata-only function does not read/install/write storage.
    static SharedWorldHostPlan create_from_stored_entry(std::string client_sha256,
        StoredSourceFactory,Dispatch=Dispatch::MovementOnly,bool native_characters=false,
        bool native_equipment_snapshots=false,bool owned_inventory_storage=false,
        TaiwanWorldEntryIdentity identity=TaiwanWorldEntryIdentity::SelectedCharacter);
    // Pass the result to an existing run_server overload taking a world plan.
    // One plan binds one Application lifetime. Main remains explicitly opted
    // out until actual full native suppliers are available. This is source
    // composition, not an activated server or a completed gameplay route.
    // MixedRecords requires actual nonmovement suppliers and full Current;
    // MovementOnly preserves the prior exclusive movement plan unchanged.
    static SharedWorldHostPlan create(SourceFactory,Dispatch=Dispatch::MovementOnly,bool native_characters=false,
        TaiwanWorldEntryIdentity identity=TaiwanWorldEntryIdentity::SelectedCharacter);
};
}
