#include "core/SharedTaiwanNativeWorldHostPlan.h"
#include "game/TaiwanActorStatusWriteFence.h"
#include "game/TaiwanActorStatusIncarnationSource.h"
#include "game/SharedTaiwanNativeRecordHandlerSource.h"
#include "handlers/RecoveredOwnedCompanions.h"
#include <algorithm>
#include <exception>
#include <mutex>
#include <optional>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2 {
namespace {
using Plan=SharedTaiwanNativeWorldHostPlan;
using Context=SharedWorldHostPlan::Context;
using OwnedPkSources=SharedWorldHostPlan::OwnedPkSources;
// Private callable target types let the final stored-host assembly verify the
// currently selected offer AND qualifier, rather than an earlier bank marker.
struct SceneActorEntryBinding {
    std::shared_ptr<const TaiwanNativeActorResourceBank> bank;
    std::shared_ptr<const TaiwanNativeDrvDoll> drv_doll;
    SharedTaiwanNativeWorldEntryOfferSource::Supply offer;
    SharedTaiwanStoredWorldEntrySource::Qualify qualify;
};
struct SceneActorEntryOffer {
    std::shared_ptr<const SceneActorEntryBinding> binding;
    std::optional<SharedTaiwanNativeWorldEntryOfferSource::Offer> operator()(
            const SharedTaiwanStoredWorldEntrySource::Scope& scope,
            const std::optional<NativeWorldEntrySnapshot>& snapshot) const {
        return binding->offer(scope,snapshot);
    }
};
struct SceneActorEntryQualify {
    std::shared_ptr<const SceneActorEntryBinding> binding;
    bool operator()(const NativeWorldEntrySnapshot& snapshot,
            const SharedTaiwanStoredWorldEntrySource::Scope& scope,
            const SharedTaiwanStoredWorldEntrySource::Frame& frame,
            SharedTaiwanStoredWorldEntrySource::Check check) const {
        return binding->qualify(snapshot,scope,frame,check);
    }
};
void require_owned_pk_context(const Context& context,Plan::Dispatch dispatch) {
    if(context.app_owned_pk&&(dispatch!=Plan::Dispatch::MixedRecords||
       !context.app_owned_initial_player||!context.app_owned_initial_deities))
        throw std::invalid_argument("Owned PK hosting requires actual mixed records and exclusive initial player/deities");
}
void require_owned_pk_sources(const Context& context,const std::optional<OwnedPkSources>& sources,
        Plan::Dispatch dispatch) {
    require_owned_pk_context(context,dispatch);
    if(context.app_owned_pk!=bool(sources))
        throw std::invalid_argument("Owned PK source presence differs from the exact requested Context");
    if(sources)sources->require_complete();
}
// The genuine scene source and all its callbacks see one owned augmented
// Scope. The actual Entered owner retains its original base Scope unchanged.
SharedTaiwanWorldEntered::Source with_initial_saved_actor_input(
        std::shared_ptr<SharedWorldPresence> presence,
        std::shared_ptr<OwnedTaiwanReturnActorSavedSource::InitialIssuer> issuer,
        std::shared_ptr<SharedNativeWorldTransports> transports,asio::any_io_executor game,
        SharedTaiwanWorldEntered::Source source) {
    using Entered=SharedTaiwanWorldEntered;
    if(!presence||!issuer||!issuer->owns_presence(presence)||!transports||!transports->owns_presence(presence)||!source)
        throw std::invalid_argument("TW initial saved input requires exact private owners and real Source");
    struct OwnerState {
        const std::thread::id thread=std::this_thread::get_id();
        bool supplying=false,poisoned=false;
    };
    struct SceneState {
        const std::weak_ptr<Session> connection;
        const Entered::Scope base,augmented;
        const std::shared_ptr<SharedWorldPresence> presence;
        Entered::Cleanup real_cleanup;
        bool cancelled=false,cleaned=false,running=false,installed=false;
        SceneState(Session& session,const Entered::Scope& original,
                std::shared_ptr<const OwnedTaiwanReturnActorSavedSource::PopulationInput> input,
                std::shared_ptr<TaiwanInitialActorEndpoints> endpoints,
                std::shared_ptr<SharedWorldPresence> actual)
            :connection(session.weak_from_this()),base(original),augmented([&]{auto value=original;
                value.actor_input=std::move(input);value.actor_endpoints=std::move(endpoints);
                return value;}()),presence(std::move(actual)){}
        bool matches(const Entered::Scope& value) const noexcept {
            return value.lease==base.lease&&value.entry.wire==base.entry.wire&&
                value.entry.logical==base.entry.logical&&value.entry.actor_handle==base.entry.actor_handle&&
                value.entry.area==base.entry.area&&value.entry.scene==base.entry.scene&&
                value.entry.x==base.entry.x&&value.entry.y==base.entry.y&&value.entry.kind==base.entry.kind&&
                value.tail_language==base.tail_language&&value.population==base.population&&
                value.actor_input==base.actor_input&&value.actor_endpoints==base.actor_endpoints;
        }
        bool pure_current() const {
            const auto session=connection.lock();
            return !cancelled&&session&&!session->closing()&&session->id()==base.lease.session&&
                session->account_id==base.lease.account&&session->character_id==base.lease.character&&
                session->recovered_client_language()==base.tail_language&&base.population&&
                base.population->joining().lease==base.lease&&augmented.actor_input&&
                augmented.actor_input->initial_population()&&
                *augmented.actor_input->initial_population()==*base.population&&
                augmented.actor_input->population_current(presence)&&augmented.actor_endpoints&&
                augmented.actor_endpoints->matches_input(augmented.actor_input)&&augmented.actor_endpoints->retained();
        }
        bool saved_current() const {
            return pure_current()&&augmented.actor_input->source()->current(augmented.actor_input->readset())&&pure_current();
        }
        void cleanup() {
            cancelled=true;
            if(augmented.actor_endpoints)augmented.actor_endpoints->retire();
            if(cleaned)return;
            cleaned=true;
            // Revocation never prevents genuine cleanup with its exact input.
            if(real_cleanup)real_cleanup(augmented);
        }
    };
    struct Call {
        SceneState& state;bool entered=false;
        explicit Call(SceneState& value):state(value) {
            if(state.running){state.cancelled=true;return;}
            if(!state.cancelled){state.running=true;entered=true;}
        }
        ~Call(){if(entered)state.running=false;}
    };
    const auto owner=std::make_shared<OwnerState>();
    return [owner,presence=std::move(presence),issuer=std::move(issuer),transports=std::move(transports),game=std::move(game),source=std::move(source)](
            Session& session,const Entered::Scope& original)->std::optional<Entered::Native> {
        if(owner->thread!=std::this_thread::get_id())throw std::logic_error("TW initial input game owner mismatch");
        if(owner->supplying){owner->poisoned=true;return {};}
        if(owner->poisoned)return {};
        struct Supplying {OwnerState& value;explicit Supplying(OwnerState& v):value(v){value.supplying=true;}
            ~Supplying(){value.supplying=false;}} supplying(*owner);
        const auto base=original;
        if(base.actor_input||base.actor_endpoints||!base.population||base.population->activated()||
           base.population->joining().lease!=base.lease||!issuer->owns_presence(presence)||
           !presence->retained_initial_population_current(*base.population))return {};
        const auto input=issuer->observe(*base.population);
        if(!input)return {};
        const auto endpoints=TaiwanInitialActorEndpoints::create(presence,transports,session,input,game);
        if(!endpoints)return {};
        const auto state=std::make_shared<SceneState>(session,base,input,endpoints,presence);
        if(owner->poisoned||!state->saved_current())return {};
        auto native=source(session,state->augmented);
        if(!native)return {};
        try {
            state->real_cleanup=native->cleanup;
            if(owner->poisoned||!state->saved_current()) {state->cleanup();return {};}
            // Keep original callbacks boxed while constructing every wrapper.
            // No original callback is replaced until all allocations finish.
            const auto real_current=std::make_shared<const Entered::Current>(native->current);
            const auto real_install=std::make_shared<const Entered::Install>(native->install);
            Entered::Current current=[state,real_current](Entered::Check check,const Entered::Scope& value) {
                Call call(*state);
                if(!call.entered||!state->matches(value)||!state->saved_current())return false;
                const bool okay=(*real_current)(check,state->augmented);
                return okay&&state->saved_current();
            };
            Entered::Install install=[state,real_install](Session& actual,const Entered::Scope& value) {
                Call call(*state);
                if(!call.entered||state->installed||state->connection.lock().get()!=&actual||
                   !state->matches(value)||!state->pure_current())return false;
                state->installed=true;
                // Full saved SQL Current belongs to the surrounding Current
                // calls; the held install itself adds only pure retained fences.
                const bool okay=(*real_install)(actual,state->augmented);
                return okay&&state->pure_current();
            };
            Entered::Cleanup cleanup=[state](const Entered::Scope&){state->cleanup();};
            std::shared_ptr<const Entered::OutwardProvider> outward;
            if(native->outward_provider) {
                const auto real=native->outward_provider;
                outward=std::make_shared<const Entered::OutwardProvider>([state,real](
                        Session& actual,const Entered::Scope& value)
                        ->std::optional<std::vector<cn::SharedActorVisibility::OutwardRecipient>> {
                    Call call(*state);
                    if(!call.entered||state->connection.lock().get()!=&actual||!state->matches(value)||
                       !state->saved_current())return {};
                    auto result=(*real)(actual,state->augmented);
                    if(!result||!state->saved_current())return {};
                    return result;
                });
            }
            native->current=std::move(current);native->install=std::move(install);
            native->cleanup=std::move(cleanup);native->outward_provider=std::move(outward);
            // Original callback destruction can cancel; check after replacements.
            if(owner->poisoned||!state->saved_current()) {state->cleanup();return {};}
            return native;
        }catch(...) {
            if(state->real_cleanup)try {state->cleanup();}catch(...) {}
            else try {native->cleanup(state->augmented);}catch(...) {}
            throw;
        }
    };
}
struct Owner {
    RecoveredCharacterRepository* characters;
    const NativeMapCatalog* maps;
    const NativeSkillCatalog* native_skills;
    NativeWorldEntrySnapshotRepository* native_world_entries;
    AccountRepository* accounts;
    NativeCharacterSummarySnapshotRepository* native_character_summaries;
    SqliteNativeCharacterSummarySnapshotRepository* native_character_summary_writer;
    SqliteNativeWorldEntrySnapshotRepository* native_world_entry_writer;
    const NativeEnemyDisplayCatalog* native_enemy_displays;
    NativeEquipmentSnapshotRepository* native_equipment_snapshots;
    SqliteNativeEquipmentSnapshotRepository* native_equipment_snapshot_writer;
    OwnedInventoryRepository* owned_inventory;
    SqliteOwnedInventoryRepository* owned_inventory_writer;
    SqliteCompanionRepository* companions;
    RecoveredOwnedCompanions* owned_companions;
    std::shared_ptr<SharedTaiwanOwnedDeitySkillSource> owned_deity_skills;
    const bool app_owned_initial_deities;
    const bool app_owned_initial_player;
    const bool app_owned_pk;
    asio::any_io_executor game;
    std::shared_ptr<SharedWorldHost> common;
    const std::thread::id thread=std::this_thread::get_id();
    SharedTaiwanWorldEntrySource::Entry entry;
    SharedTaiwanWorldLifecycle::AsyncOwner entered;
    std::shared_ptr<SharedTaiwanNativeMovementHost> movement;
    SharedTaiwanMovementSource::Binding binding;
    std::optional<Plan::RecordSources> records;
    std::optional<OwnedPkSources> owned_pk;
    std::optional<SharedTaiwanNativeCharacterListSource::Binding> characters_source;
    std::function<void()> records_invalidate;
    const std::shared_ptr<TaiwanActorStatusWriteFence> actor_status_write_fence;
    const std::shared_ptr<TaiwanActorStatusIncarnationSource> actor_status_incarnations;
    const std::size_t capacity;
    bool entry_taken=false,entered_taken=false,movement_taken=false,records_taken=false;
    bool characters_taken=false,pk_taken=false;

    Owner(const Context& context,Plan::Sources sources,Plan::Dispatch dispatch,bool native_characters,
          TaiwanWorldEntryIdentity identity)
        :characters(&context.characters),maps(&context.maps),native_skills(context.native_skills),
         native_world_entries(context.native_world_entries),
         accounts(context.accounts),native_character_summaries(context.native_character_summaries),
         native_character_summary_writer(context.native_character_summary_writer),
         native_world_entry_writer(context.native_world_entry_writer),
         native_enemy_displays(context.native_enemy_displays),
         native_equipment_snapshots(context.native_equipment_snapshots),
         native_equipment_snapshot_writer(context.native_equipment_snapshot_writer),
         owned_inventory(context.owned_inventory),owned_inventory_writer(context.owned_inventory_writer),
         companions(context.companions),owned_companions(context.owned_companions),owned_deity_skills(context.owned_deity_skills),
         app_owned_initial_deities(context.app_owned_initial_deities),
         app_owned_initial_player(context.app_owned_initial_player),app_owned_pk(context.app_owned_pk),
         game(context.game),common(context.common_world),
         records(std::move(sources.records)),owned_pk(std::move(sources.owned_pk)),
         characters_source(std::move(sources.characters)),
         actor_status_write_fence(std::move(sources.actor_status_write_fence)),
         actor_status_incarnations(std::move(sources.actor_status_incarnations)),capacity(sources.actual_session_capacity) {
        struct ConstructionMonitor {
            TaiwanActorStatusWriteFence* fence;TaiwanActorStatusIncarnationSource* incarnations;bool published=false;
            ~ConstructionMonitor(){if(!published){if(fence)fence->stop();if(incarnations)incarnations->stop();}}
        } monitor{actor_status_write_fence.get(),actor_status_incarnations.get()};
        require_owned_pk_sources(context,owned_pk,dispatch);
        if(app_owned_initial_player&&!app_owned_initial_deities)
            throw std::invalid_argument("Owned initial player requires exclusive initial deity ownership");
        if(!valid_taiwan_world_entry_identity(identity) ||
           (identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle && !native_characters) ||
           !common || !common->owns_repository(*characters) || !sources.entry ||
           !sources.entered || !sources.movement_rules || !sources.movement_resources ||
           !sources.actual_session_capacity)
            throw std::invalid_argument("TW native host plan requires complete actual common-world suppliers");
        if(native_characters!=bool(characters_source) ||
           (characters_source && (!characters_source->list || !characters_source->select || !characters_source->invalidate_active ||
                                  !characters_source->current || !characters_source->complete || !characters_source->selected ||
                                  !characters_source->invalidate_selection)))
            throw std::invalid_argument("TW native host requires exclusive complete actual list and issued-token sources");
        if(native_characters && (!accounts || !native_character_summaries ||
           !native_character_summaries->owns_sources(*accounts,*characters)))
            throw std::invalid_argument("TW native host character sources require the exact Application database readers");
        if((dispatch==Plan::Dispatch::MixedRecords)!=bool(records) ||
           (records && (!records->others.records || !records->others.release ||
                        !records->others.invalidate_active || !records->current)))
            throw std::invalid_argument("TW native mixed plan requires explicit matching nonmovement suppliers");
        if(owned_deity_skills) {
            if(!records || !companions || !owned_companions || !native_skills ||
               !owned_companions->owns_repository(*companions) ||
               !owned_deity_skills->publication_required() ||
               !owned_deity_skills->owns_sources(common->presence(),*companions,*native_skills) ||
               records->others.deity_selection)
                throw std::invalid_argument("TW C67 publication requires exact constructed mixed Context sources");
            // AFTER all chat/spectator assembly: no aggregate wrapper can drop
            // this typed actual supplier. Owner retains its game-affine source.
            const std::weak_ptr<SharedTaiwanOwnedDeitySkillSource> weak=owned_deity_skills;
            auto* helper=owned_companions;
            records->others.deity_selection=SharedTaiwanWorldRecordSource::DeitySelectionBinding{
                [weak,helper](Session& session,const RecoveredDeitySelection::Request& request)
                    ->std::optional<SharedTaiwanWorldRecordSource::Reply> {
                    const auto source=weak.lock();if(!source)return std::nullopt;
                    auto wire=source->select_deity_for_callback(session,*helper,request);
                    if(!wire)return std::nullopt;
                    return SharedTaiwanWorldRecordSource::Reply::wire(std::move(*wire));
                },
                [weak](Session& session){if(const auto source=weak.lock())source->release_selection(session);},
                [weak]{if(const auto source=weak.lock())source->invalidate_selection_callbacks();},weak};
        }
        auto presence=common->presence();auto visibility=common->visibility();
        if(actor_status_write_fence && !actor_status_write_fence->owns_presence(presence))
            throw std::invalid_argument("TW status writer fence requires this exact common presence");
        if(actor_status_incarnations && !actor_status_incarnations->owns_presence(presence))
            throw std::invalid_argument("TW actor incarnations require this exact common presence");
        entry=SharedTaiwanWorldEntrySource::create(*characters,*maps,std::move(sources.entry),
            characters_source?characters_source->selected:SharedTaiwanNativeCharacterListSource::SelectedSource{},
            std::move(sources.entry_prepare),characters_source?presence:nullptr,identity);
        entered=SharedTaiwanWorldEntered::create(presence,visibility,std::move(sources.entered),identity,
            app_owned_initial_player?SharedTaiwanWorldEntered::InitialDeityPublisher::ApplicationOwnedPlayerAndDeities:
                app_owned_initial_deities?SharedTaiwanWorldEntered::InitialDeityPublisher::ApplicationOwned:
                    SharedTaiwanWorldEntered::InitialDeityPublisher::External);
        if(sources.movement_custody && (!accounts || !owned_inventory_writer || !native_equipment_snapshot_writer ||
           !sources.movement_custody->owns_sources(*accounts,*characters) ||
           !sources.movement_custody->owns_writers(*owned_inventory_writer,*native_equipment_snapshot_writer)))
            throw std::invalid_argument("TW movement custody requires both exact Application writers");
        movement=SharedTaiwanNativeMovementHost::create(presence,visibility,
            std::move(sources.movement_rules),std::move(sources.movement_resources),sources.actual_session_capacity,
            std::move(sources.movement_custody));
        if(!movement || !entry || !entered.entered || !entered.cancel)
            throw std::invalid_argument("TW native host plan did not retain complete actual owners");
        binding=movement->binding();
        if(!binding.movement || !binding.release || !binding.invalidate_active || !binding.retire)
            throw std::invalid_argument("TW native host plan requires exact movement retirement");
        monitor.published=true;
    }
    ~Owner() {
        if(actor_status_incarnations)actor_status_incarnations->stop();
        if(actor_status_write_fence)actor_status_write_fence->stop();
        if(std::this_thread::get_id()!=thread)std::terminate();
        // Real callbacks are game-affine. The plan factory keeps only a weak
        // reference; these owners therefore drain with Application's facades.
        records_invalidate={};records.reset();characters_source.reset();binding={};movement.reset();entered={};entry={};
        owned_pk.reset(); // Untaken recipe dependencies drain before common world.
        if(owned_deity_skills)owned_deity_skills->stop_selection_publications();
        owned_deity_skills.reset();common.reset();
    }
    void check() const {
        if(std::this_thread::get_id()!=thread)
            throw std::logic_error("TW native host plan game owner mismatch");
    }
    void same(const Context& context) const {
        check();
        if(&context.characters!=characters || &context.maps!=maps || context.native_skills!=native_skills ||
           context.native_world_entries!=native_world_entries ||
           context.accounts!=accounts || context.native_character_summaries!=native_character_summaries ||
           context.native_character_summary_writer!=native_character_summary_writer ||
           context.native_world_entry_writer!=native_world_entry_writer ||
           context.native_enemy_displays!=native_enemy_displays ||
           context.native_equipment_snapshots!=native_equipment_snapshots ||
           context.native_equipment_snapshot_writer!=native_equipment_snapshot_writer ||
           context.owned_inventory!=owned_inventory || context.owned_inventory_writer!=owned_inventory_writer ||
           context.companions!=companions || context.owned_companions!=owned_companions ||
           context.owned_deity_skills!=owned_deity_skills ||
           context.app_owned_initial_deities!=app_owned_initial_deities ||
           context.app_owned_initial_player!=app_owned_initial_player ||context.app_owned_pk!=app_owned_pk ||
           context.common_world!=common || context.game!=game || !common->owns_repository(*characters)) {
            invalidate();
            throw std::invalid_argument("TW native host plan cannot join a different Application Context");
        }
    }
    void invalidate() const {
        if(actor_status_incarnations)actor_status_incarnations->stop();
        if(actor_status_write_fence)actor_status_write_fence->stop();
        check();
        const auto record=records_invalidate;const auto move=binding.invalidate_active;
        const auto character=characters_source?characters_source->invalidate_active:std::function<void()>{};
        std::exception_ptr failure;
        try {if(record)record();}catch(...) {failure=std::current_exception();}
        try {if(owned_deity_skills)owned_deity_skills->invalidate_selection_callbacks();}
        catch(...) {if(!failure)failure=std::current_exception();}
        try {if(move)move();}catch(...) {if(!failure)failure=std::current_exception();}
        try {if(character)character();}catch(...) {if(!failure)failure=std::current_exception();}
        if(failure)std::rethrow_exception(failure);
    }
    void cancel(Session& session,const SharedWorldPresence::Lease& lease) {
        if(actor_status_write_fence)actor_status_write_fence->stop();
        check();std::exception_ptr failure;
        // Retire exact controller and resource lineage before the real native
        // initial-scene cleanup; both paths run even if one cleanup throws.
        try {movement->remove(session,lease);}catch(...) {failure=std::current_exception();}
        try {entered.cancel(session,lease);}catch(...) {if(!failure)failure=std::current_exception();}
        if(failure)std::rethrow_exception(failure);
    }
};
struct Factory {
    enum class Stage {Fresh,Preparing,Bound,Failed};
    std::mutex mutex;
    Stage stage=Stage::Fresh;
    std::optional<std::thread::id> thread;
    Plan::SourceFactory supply;
    const Plan::Dispatch dispatch;
    const bool native_characters;
    const TaiwanWorldEntryIdentity identity;
    std::weak_ptr<Owner> bound;
    Factory(Plan::SourceFactory source,Plan::Dispatch mode,bool characters,TaiwanWorldEntryIdentity entry_identity)
        :supply(std::move(source)),dispatch(mode),native_characters(characters),identity(entry_identity){}
    std::shared_ptr<Owner> get(const Context& context) {
        Plan::SourceFactory source;
        std::shared_ptr<Owner> existing;
        {
            std::lock_guard lock(mutex);
            if(thread && *thread!=std::this_thread::get_id())
                throw std::logic_error("TW native host plan factory game owner mismatch");
            if(stage==Stage::Preparing) {
                stage=Stage::Failed;
                throw std::logic_error("TW native host plan source construction reentered");
            }
            if(stage==Stage::Bound) {
                existing=bound.lock();
                if(!existing)throw std::logic_error("TW native host plan lifetime has already drained");
            }else {
                if(stage!=Stage::Fresh)throw std::logic_error("TW native host plan construction failed");
                thread=std::this_thread::get_id();stage=Stage::Preparing;source=std::move(supply);
            }
        }
        if(existing) {existing->same(context);return existing;}
        std::shared_ptr<TaiwanActorStatusWriteFence> constructing_fence;
        std::shared_ptr<TaiwanActorStatusIncarnationSource> constructing_incarnations;
        try {
            // Reject requested PK mode before invoking any actual supplier.
            require_owned_pk_context(context,dispatch);
            // CUSTOM-0149 reject before invoking any actual source supplier.
            if(context.app_owned_initial_player&&!context.app_owned_initial_deities)
                throw std::invalid_argument("Owned initial player requires exclusive initial deity ownership");
            if(!context.common_world || !context.common_world->owns_repository(context.characters))
                throw std::invalid_argument("TW native host plan needs the actual Application common world");
            auto sources=source(context);
            constructing_fence=sources.actor_status_write_fence;
            constructing_incarnations=sources.actor_status_incarnations;
            require_owned_pk_sources(context,sources.owned_pk,dispatch);
            {
                std::lock_guard lock(mutex);
                if(stage!=Stage::Preparing)
                    throw std::logic_error("TW native host plan supplier caught rejected reentry");
            }
            auto owner=std::make_shared<Owner>(context,std::move(sources),dispatch,native_characters,identity);
            {
                std::lock_guard lock(mutex);
                if(stage!=Stage::Preparing)
                    throw std::logic_error("TW native host plan source owner construction was invalidated");
                bound=owner;stage=Stage::Bound;
            }
            return owner;
        }catch(...) {
            if(constructing_incarnations)constructing_incarnations->stop();
            if(constructing_fence)constructing_fence->stop();
            std::lock_guard lock(mutex);stage=Stage::Failed;bound.reset();throw;
        }
    }
};
}
std::shared_ptr<SharedTaiwanOwnedDeitySkillSource> SharedTaiwanNativeWorldHostPlan::RecordSources::owned_deity_skills(
    const SharedWorldHostPlan::Context& context) {
    if(!context.common_world || !context.common_world->owns_repository(context.characters) ||
       !context.companions || !context.native_skills)
        throw std::invalid_argument("TW saved skill source requires actual same Context presence/companions/catalog");
    if(context.owned_deity_skills) {
        if(!context.owned_companions || !context.owned_companions->owns_repository(*context.companions) ||
           !context.owned_deity_skills->publication_required() ||
           !context.owned_deity_skills->owns_sources(context.common_world->presence(),*context.companions,*context.native_skills))
            throw std::invalid_argument("TW selected publication source differs from actual Context");
        return context.owned_deity_skills;
    }
    return SharedTaiwanOwnedDeitySkillSource::create(context.common_world->presence(),
        *context.companions,*context.native_skills);
}
std::shared_ptr<SharedTaiwanIssuedSkillSource> SharedTaiwanNativeWorldHostPlan::RecordSources::issued_primary_skills(
    const SharedWorldHostPlan::Context& context,std::size_t capacity) {
    if(!context.common_world || !context.common_world->owns_repository(context.characters) || !context.native_skills)
        throw std::invalid_argument("TW issued skills require actual common Context presence/catalog");
    return SharedTaiwanIssuedSkillSource::create(context.common_world->presence(),*context.native_skills,capacity);
}
SharedTaiwanNativeWorldHostPlan::RecordSources SharedTaiwanNativeWorldHostPlan::RecordSources::with_native_skills(
    const SharedWorldHostPlan::Context& context,
    std::shared_ptr<SharedTaiwanIssuedSkillSource> issued,
    std::shared_ptr<SharedTaiwanNativeSkillCommandSource::WorldOwner> world,
    SharedTaiwanNativeSkillCommandSource::Budgets budgets,RecordSources sources) {
    if(!context.common_world || !context.common_world->owns_repository(context.characters) ||
       !context.native_skills || !issued || !issued->owns_sources(context.common_world->presence(),*context.native_skills) ||
       !world || !sources.current || !sources.others.records ||
       !sources.others.release || !sources.others.invalidate_active || sources.others.native_skills)
        throw std::invalid_argument("TW native skills require the actual common Context, catalog and exclusive complete owner");
    sources.others.native_skills=SharedTaiwanNativeSkillCommandSource::create(
        context.common_world->presence(),*context.native_skills,std::move(issued),std::move(world),budgets);
    return sources;
}
SharedTaiwanNativeWorldHostPlan::RecordSources SharedTaiwanNativeWorldHostPlan::RecordSources::with_native_chat(
    const SharedWorldHostPlan::Context& context,std::shared_ptr<SharedTaiwanNativeChatSource::WorldOwner> world,
    std::shared_ptr<const ChineseText> text,SharedTaiwanNativeChatSource::Budgets chat_budgets,
    std::size_t capacity,SharedTaiwanWorldRecordSource::OtherBinding remaining,
    SharedTaiwanWorldRecordSource::Current current,SharedTaiwanWorldRecordSource::Budgets record_budgets) {
    if(!context.common_world || !context.common_world->owns_repository(context.characters) || !current)
        throw std::invalid_argument("TW native chat records require the actual Application common-world Context");
    auto chat=SharedTaiwanNativeChatSource::create(context.common_world->presence(),context.common_world->visibility(),
        std::move(world),std::move(text),chat_budgets,capacity,context.common_world->transports());
    auto handlers=SharedTaiwanNativeRecordHandlerSource::create(std::move(chat),std::move(remaining),record_budgets.max_output_bytes);
    return RecordSources{std::move(handlers),std::move(current),record_budgets};
}
SharedTaiwanNativeWorldHostPlan::RecordSources SharedTaiwanNativeWorldHostPlan::RecordSources::with_native_chat_and_spectator(
    const SharedWorldHostPlan::Context& context,std::shared_ptr<SharedTaiwanNativeChatSource::WorldOwner> world,
    std::shared_ptr<const ChineseText> text,SharedTaiwanNativeChatSource::Budgets chat_budgets,
    std::size_t capacity,std::shared_ptr<SharedTaiwanNativeSpectatorSource::WorldOwner> spectator_world,
    SharedTaiwanNativeSpectatorSource::Budgets spectator_budgets,
    SharedTaiwanWorldRecordSource::OtherBinding remaining,
    SharedTaiwanWorldRecordSource::Current current,SharedTaiwanWorldRecordSource::Budgets record_budgets) {
    if(!context.common_world || !context.common_world->owns_repository(context.characters) || !current)
        throw std::invalid_argument("TW typed spectator records require the actual Application common-world Context");
    auto presence=context.common_world->presence();auto transports=context.common_world->transports();
    auto chat=SharedTaiwanNativeChatSource::create(presence,context.common_world->visibility(),
        std::move(world),std::move(text),chat_budgets,capacity,transports);
    auto spectator=SharedTaiwanNativeSpectatorSource::create(presence,transports,
        std::move(spectator_world),spectator_budgets,capacity);
    auto handlers=SharedTaiwanNativeRecordHandlerSource::create(std::move(chat),std::move(spectator),
        std::move(remaining),record_budgets.max_output_bytes);
    return RecordSources{std::move(handlers),std::move(current),record_budgets};
}
SharedTaiwanNativeWorldHostPlan::RecordSources SharedTaiwanNativeWorldHostPlan::RecordSources::with_native_chat_spectator_and_publication(
    const SharedWorldHostPlan::Context& context,std::shared_ptr<SharedTaiwanNativeChatSource::WorldOwner> world,
    std::shared_ptr<const ChineseText> text,SharedTaiwanNativeChatSource::Budgets chat_budgets,
    std::size_t capacity,std::shared_ptr<SharedTaiwanNativeSpectatorSource::WorldOwner> spectator_world,
    SharedTaiwanNativeSpectatorSource::Budgets spectator_budgets,
    SharedTaiwanWorldRecordSource::OtherBinding remaining,
    SharedTaiwanWorldRecordSource::Current current,SharedTaiwanWorldRecordSource::Budgets record_budgets,
    std::shared_ptr<SharedNativeSpectatorPublication> publication,
    std::shared_ptr<SharedNativeSpectatorTargets> targets,
    std::shared_ptr<SharedTaiwanNativeSpectatorSource::CloseOwner> close_owner) {
    if(!context.common_world || !context.common_world->owns_repository(context.characters) || !current || !publication)
        throw std::invalid_argument("TW spectator UI records require the actual host and supplied publication source");
    auto presence=context.common_world->presence();auto transports=context.common_world->transports();
    if(!publication->owns_source(presence,transports) ||
       (targets && !targets->owns_source(presence,transports,publication)))
        throw std::invalid_argument("TW spectator UI publication belongs to a different actual common source");
    context.common_world->install_native_spectator_publication(publication);
    const auto selected=context.common_world->native_spectator_publication();
    if(selected!=publication || !selected->owns_source(presence,transports))
        throw std::invalid_argument("TW spectator UI host did not retain the exact supplied publication source");
    if(targets)context.common_world->install_native_spectator_targets(targets);
    const auto selected_targets=context.common_world->native_spectator_targets();
    if(selected_targets!=targets || (selected_targets && !selected_targets->owns_source(presence,transports,selected)))
        throw std::invalid_argument("TW spectator target host did not retain the exact supplied namespace source");
    auto chat=SharedTaiwanNativeChatSource::create(presence,context.common_world->visibility(),
        std::move(world),std::move(text),chat_budgets,capacity,transports);
    auto spectator=SharedTaiwanNativeSpectatorSource::create(presence,transports,
        std::move(spectator_world),spectator_budgets,capacity,selected,selected_targets,std::move(close_owner));
    auto handlers=SharedTaiwanNativeRecordHandlerSource::create(std::move(chat),std::move(spectator),
        std::move(remaining),record_budgets.max_output_bytes);
    return RecordSources{std::move(handlers),std::move(current),record_budgets};
}
SharedTaiwanNativeWorldHostPlan::StoredSources::ListSources
SharedTaiwanNativeWorldHostPlan::StoredSources::ListSources::with_handoff(
        SharedTaiwanNativeCharacterListSource::TargetSource target,
        SharedTaiwanNativeCharacterListSource::Qualify qualify,std::shared_ptr<SharedTaiwanCharacterListHandoff> owner) {
    if(!target || !qualify || !owner)throw std::invalid_argument("TW list handoff requires complete actual sources");
    return ListSources{std::move(target),std::move(qualify),{},{},std::move(owner)};
}
SharedTaiwanNativeWorldHostPlan::StoredSources::ListSources
SharedTaiwanNativeWorldHostPlan::StoredSources::ListSources::with_configured_handoff(
        const Context& context,std::shared_ptr<const TaiwanNativeClientGroupConfiguration> configuration,
        std::string client,std::size_t capacity,SharedTaiwanCharacterListHandoff::Live live,
        SharedTaiwanCharacterListHandoff::Authority authority,
        SharedTaiwanNativeCharacterListSource::TargetSource target,SharedTaiwanNativeCharacterListSource::Qualify qualify,
        SharedTaiwanNativeCharacterOfferSource::Supply offer) {
    if(!context.accounts || !context.native_character_summaries || !target || !qualify)
        throw std::invalid_argument("TW configured handoff requires its actual Context and complete list sources");
    auto owner=SharedTaiwanCharacterListHandoff::create(*context.accounts,context.characters,
        *context.native_character_summaries,std::move(client),capacity,std::move(configuration),
        std::move(live),std::move(authority));
    auto sources=with_handoff(std::move(target),std::move(qualify),std::move(owner));
    sources.offer=std::move(offer);return sources;
}
SharedTaiwanNativeWorldEntryOfferSource::Supply SharedTaiwanNativeWorldHostPlan::StoredSources::scene_entry_offer(
        const Context& context,std::shared_ptr<const TaiwanNativeNpcSceneGroups> npcs,
        SharedTaiwanNativeWorldEntryOfferSource::SceneSupply supply) {
    if(!context.common_world || !context.common_world->owns_repository(context.characters) ||
       !context.accounts || !context.native_world_entries || !context.native_world_entry_writer ||
       !context.native_enemy_displays ||
       static_cast<NativeWorldEntrySnapshotRepository*>(context.native_world_entry_writer)!=context.native_world_entries ||
       !context.native_world_entry_writer->owns_sources(*context.accounts,context.characters))
        throw std::invalid_argument("TW scene entry offer requires the actual Application Context readers");
    return SharedTaiwanNativeWorldEntryOfferSource::with_scene_content(*context.native_enemy_displays,
        std::move(npcs),std::move(supply));
}
SharedTaiwanNativeWorldEntryOfferSource::Supply SharedTaiwanNativeWorldHostPlan::StoredSources::scene_entry_offer(
        const Context& context,std::shared_ptr<const TaiwanNativeNpcSceneGroups> npcs,
        std::shared_ptr<const TaiwanNativeTransformCards> cards,
        SharedTaiwanNativeWorldEntryOfferSource::SceneSupply supply) {
    if(!context.common_world || !context.common_world->owns_repository(context.characters) ||
       !context.accounts || !context.native_world_entries || !context.native_world_entry_writer ||
       !context.native_enemy_displays ||
       static_cast<NativeWorldEntrySnapshotRepository*>(context.native_world_entry_writer)!=context.native_world_entries ||
       !context.native_world_entry_writer->owns_sources(*context.accounts,context.characters))
        throw std::invalid_argument("TW card-aware entry requires the actual Application Context readers");
    return SharedTaiwanNativeWorldEntryOfferSource::with_scene_content(*context.native_enemy_displays,
        std::move(npcs),std::move(cards),std::move(supply));
}
SharedTaiwanNativeWorldHostPlan::StoredSources
SharedTaiwanNativeWorldHostPlan::StoredSources::with_scene_entry_content(
        const Context& context,std::shared_ptr<const TaiwanNativeNpcSceneGroups> npcs,
        std::shared_ptr<const TaiwanNativeTransformCards> cards,
        SharedTaiwanNativeWorldEntryOfferSource::SceneSupply supply,StoredSources sources) {
    if(!context.common_world || !context.common_world->owns_repository(context.characters) ||
       !context.accounts || !context.native_world_entries || !context.native_world_entry_writer ||
       !context.native_enemy_displays || !sources.entry_qualify || sources.entry_offer ||
       static_cast<NativeWorldEntrySnapshotRepository*>(context.native_world_entry_writer)!=context.native_world_entries ||
       !context.native_world_entry_writer->owns_sources(*context.accounts,context.characters))
        throw std::invalid_argument("TW paired scene entry requires actual Context and unbound complete qualifier");
    auto binding=SharedTaiwanNativeWorldEntryOfferSource::with_scene_content_and_qualification(
        *context.native_enemy_displays,std::move(npcs),std::move(cards),std::move(supply),
        std::move(sources.entry_qualify));
    sources.entry_offer=std::move(binding.offer);sources.entry_qualify=std::move(binding.qualify);
    return sources;
}
SharedTaiwanNativeWorldHostPlan::StoredSources
SharedTaiwanNativeWorldHostPlan::StoredSources::with_scene_entry_content(
        const Context& context,std::shared_ptr<const TaiwanNativeNpcSceneGroups> npcs,
        std::shared_ptr<const TaiwanNativeTransformCards> cards,std::shared_ptr<const TaiwanNativeDrvDoll> drv_doll,
        SharedTaiwanNativeWorldEntryOfferSource::SceneSupply supply,StoredSources sources) {
    if(!context.common_world || !context.common_world->owns_repository(context.characters) ||
       !context.accounts || !context.native_world_entries || !context.native_world_entry_writer ||
       !context.native_enemy_displays || !sources.entry_qualify || sources.entry_offer ||
       static_cast<NativeWorldEntrySnapshotRepository*>(context.native_world_entry_writer)!=context.native_world_entries ||
       !context.native_world_entry_writer->owns_sources(*context.accounts,context.characters))
        throw std::invalid_argument("TW resource-aware paired entry requires actual Context and unbound complete qualifier");
    auto binding=SharedTaiwanNativeWorldEntryOfferSource::with_scene_content_and_qualification(
        *context.native_enemy_displays,std::move(npcs),std::move(cards),std::move(drv_doll),std::move(supply),
        std::move(sources.entry_qualify));
    sources.entry_offer=std::move(binding.offer);sources.entry_qualify=std::move(binding.qualify);
    return sources;
}
SharedTaiwanNativeWorldHostPlan::StoredSources
SharedTaiwanNativeWorldHostPlan::StoredSources::with_scene_entry_content(
        const Context& context,std::shared_ptr<const TaiwanNativeNpcSceneGroups> npcs,
        std::shared_ptr<const TaiwanNativeTransformCards> cards,std::shared_ptr<const TaiwanNativeDrvDoll> drv_doll,
        std::shared_ptr<const TaiwanNativeActorResourceBank> actor_resources,
        SharedTaiwanNativeWorldEntryOfferSource::SceneSupply supply,StoredSources sources) {
    if(!context.common_world || !context.common_world->owns_repository(context.characters) ||
       !context.accounts || !context.native_world_entries || !context.native_world_entry_writer ||
       !context.native_enemy_displays || !sources.entry_qualify || sources.entry_offer ||
       static_cast<NativeWorldEntrySnapshotRepository*>(context.native_world_entry_writer)!=context.native_world_entries ||
       !context.native_world_entry_writer->owns_sources(*context.accounts,context.characters))
        throw std::invalid_argument("TW actor bank entry requires actual Context and unbound complete qualifier");
    const auto same_actor_bank=actor_resources;
    const auto same_drv_doll_bank=drv_doll;
    auto binding=SharedTaiwanNativeWorldEntryOfferSource::with_scene_content_and_qualification(
        *context.native_enemy_displays,std::move(npcs),std::move(cards),std::move(drv_doll),std::move(actor_resources),
        std::move(supply),std::move(sources.entry_qualify));
    auto actual_binding=std::make_shared<const SceneActorEntryBinding>(SceneActorEntryBinding{
        same_actor_bank,same_drv_doll_bank,std::move(binding.offer),std::move(binding.qualify)});
    sources.entry_offer=SceneActorEntryOffer{actual_binding};
    sources.entry_qualify=SceneActorEntryQualify{actual_binding};
    sources.scene_actor_bank_=same_actor_bank;sources.scene_entry_binding_=std::move(actual_binding);
    sources.scene_drv_doll_bank_=same_drv_doll_bank;
    return sources;
}
void SharedTaiwanNativeWorldHostPlan::StoredSources::require_profile_entry_binding() const {
    const auto* offer=entry_offer.target<SceneActorEntryOffer>();
    const auto* qualify=entry_qualify.target<SceneActorEntryQualify>();
    if(!scene_actor_bank_||!scene_drv_doll_bank_||!scene_entry_binding_||!offer||!qualify||
       offer->binding!=scene_entry_binding_||qualify->binding!=scene_entry_binding_||
       offer->binding->bank!=scene_actor_bank_||qualify->binding->bank!=scene_actor_bank_||
       offer->binding->drv_doll!=scene_drv_doll_bank_||qualify->binding->drv_doll!=scene_drv_doll_bank_)
        throw std::invalid_argument("TW return profile entry callable incarnation changed");
}
SharedTaiwanNativeWorldHostPlan::StoredSources
SharedTaiwanNativeWorldHostPlan::StoredSources::with_owned_pk_return_profiles(
        const Context& context,std::shared_ptr<const TaiwanNativeActorResourceBank> bank,
        TaiwanCustomFullActorProfile::Policy policy,OwnedTaiwanPkReturnSceneSource::Selection selection,
        OwnedTaiwanPkReturnSceneSource::MaterialSources material,StoredSources sources) {
    if(!sources.owned_pk)throw std::invalid_argument("TW return profile replacement lacks an existing recipe");
    sources.owned_pk->require_complete();
    auto prior=std::move(*sources.owned_pk);sources.owned_pk.reset();
    OwnedPkProfileRecipe recipe{std::move(prior.dependency_owner),std::move(prior.fight_archive),
        prior.parameters,prior.order,prior.retry,std::move(prior.seed)};
    return with_owned_pk_return_profiles(context,std::move(bank),std::move(policy),selection,
        std::move(material),std::move(recipe),std::move(sources));
}
SharedTaiwanNativeWorldHostPlan::StoredSources
SharedTaiwanNativeWorldHostPlan::StoredSources::with_owned_pk_return_profiles(
        const Context& context,std::shared_ptr<const TaiwanNativeActorResourceBank> bank,
        TaiwanCustomFullActorProfile::Policy policy,OwnedTaiwanPkReturnSceneSource::Selection selection,
        OwnedTaiwanPkReturnSceneSource::MaterialSources material,OwnedPkProfileRecipe recipe,StoredSources sources) {
    if(!context.app_owned_pk||!context.app_owned_initial_player||!context.app_owned_initial_deities||
       !context.common_world||!context.common_world->owns_repository(context.characters)||
       !context.native_equipment_snapshots||!context.native_equipment_snapshot_writer||
       !context.owned_inventory||!context.owned_inventory_writer||sources.owned_pk||
       !sources.entry_offer||!sources.entry_qualify||!bank||sources.scene_actor_bank_!=bank||
       sources.return_profiles_installed_||
       static_cast<NativeEquipmentSnapshotRepository*>(context.native_equipment_snapshot_writer)!=context.native_equipment_snapshots||
       static_cast<OwnedInventoryRepository*>(context.owned_inventory_writer)!=context.owned_inventory)
        throw std::invalid_argument("TW full return profiles require actual owned PK and the same installed scene bank");
    if(!recipe.dependency_owner||recipe.fight_archive.empty()||!recipe.seed)
        throw std::invalid_argument("TW first profile recipe requires actual archive seed and dependencies");
    sources.require_profile_entry_binding();
    auto profiles=TaiwanCustomFullActorProfile::create(context.common_world->presence(),bank,
        sources.scene_drv_doll_bank_,std::move(policy));
    auto scene=OwnedTaiwanPkReturnSceneSource::create(context.common_world->presence(),
        context.common_world->transports(),context.common_world->visibility(),std::move(profiles),selection,std::move(material));
    struct Dependencies {
        std::shared_ptr<const void> original;
        std::shared_ptr<OwnedTaiwanPkReturnSceneSource> scene;
    };
    auto retained=std::make_shared<const Dependencies>(Dependencies{std::move(recipe.dependency_owner),scene});
    auto actual_return=scene->return_source();
    sources.owned_pk.emplace(std::move(recipe.fight_archive),recipe.parameters,recipe.order,recipe.retry,
        std::move(recipe.seed),std::move(actual_return),std::move(retained));
    sources.return_profiles_installed_=true;
    return sources;
}
SharedTaiwanNativeWorldHostPlan::StoredSources
SharedTaiwanNativeWorldHostPlan::StoredSources::with_owned_pk_return_resources(
        const Context& context,std::shared_ptr<const TaiwanNativeActorResourceBank> bank,
        TaiwanCustomFullActorProfile::Policy policy,OwnedTaiwanPkReturnSceneSource::Selection selection,
        TaiwanNativeActorResourceSource::Configuration configuration,ActualStatusSources status,
        OwnedPkProfileRecipe recipe,StoredSources sources) {
    if(!context.app_owned_pk||!context.app_owned_initial_player||!context.app_owned_initial_deities||
       !context.common_world||!context.common_world->owns_repository(context.characters)||
       !context.native_equipment_snapshots||!context.native_equipment_snapshot_writer||
       !context.owned_inventory||!context.owned_inventory_writer||sources.owned_pk||
       sources.return_profiles_installed_||!bank||sources.scene_actor_bank_!=bank||
       static_cast<NativeEquipmentSnapshotRepository*>(context.native_equipment_snapshot_writer)!=context.native_equipment_snapshots||
       static_cast<OwnedInventoryRepository*>(context.owned_inventory_writer)!=context.owned_inventory||
       !status.dependency_owner||!status.status||!sources.actor_status_incarnations)
        throw std::invalid_argument("TW return resources require the same installed Context, actor incarnations and actual status owner");
    sources.require_profile_entry_binding();
    const auto presence=context.common_world->presence();
    auto profile_scope=TaiwanActorStatusProfileScope::create(presence,sources.actor_status_incarnations);
    if(!profile_scope)throw std::invalid_argument("TW profile status scope requires the actual host incarnation source");
    auto arguments=TaiwanNativeActorArgumentSource::create(presence,bank,sources.scene_drv_doll_bank_);
    auto resources=TaiwanNativeActorResourceSource::create(presence,std::move(arguments),std::move(configuration));
    if(!resources)throw std::invalid_argument("TW return resource owner could not retain the actual argument source");
    struct Dependencies {
        std::shared_ptr<TaiwanNativeActorResourceSource> resources;
        std::shared_ptr<TaiwanActorStatusProfileScope> profile_scope;
        std::shared_ptr<const void> status;
    };
    auto retained=std::make_shared<const Dependencies>(Dependencies{resources,profile_scope,std::move(status.dependency_owner)});
    OwnedTaiwanPkReturnSceneSource::MaterialSources material{
        std::move(retained),
        [resources](std::shared_ptr<const OwnedTaiwanPkReturnSceneSource::Input> input,std::size_t row,
                    const OwnedTaiwanPkReturnSceneSource::Equipment& equipment,const SharedWorldPresence::Lease&) {
            // Asset validity is independent of the receiver's Prepare/Consumed
            // phase; Profile and Scene own those private endpoint fences.
            return resources->observe(std::move(input),row,equipment);
        },[profile_scope,actual_status=std::move(status.status)](
                std::shared_ptr<const OwnedTaiwanPkReturnSceneSource::Input> input,std::size_t row,
                const OwnedTaiwanPkReturnSceneSource::Equipment& equipment,const SharedWorldPresence::Lease& recipient)
                ->std::optional<TaiwanCustomFullActorProfile::StatusInput> {
            // Own exact values across the real status provider; scope qualifies
            // actor/input lifetime only and never substitutes status authority.
            const auto own_input=std::move(input);const auto own_equipment=equipment;const auto own_recipient=recipient;
            const auto scope=profile_scope->observe(own_input,row,own_equipment,own_recipient);
            if(!scope)return {};
            auto value=actual_status(own_input,row,own_equipment,own_recipient);
            if(!value||value->profile_scope_source||value->profile_scope||
               !profile_scope->current(*scope)||
               !profile_scope->matches_inputs(*scope,own_input,row,own_equipment,own_recipient))return {};
            // Never overwrite epoch/domain/override/current from actual status.
            value->profile_scope_source=profile_scope;value->profile_scope=*scope;
            return value;
        }};
    return with_owned_pk_return_profiles(context,std::move(bank),std::move(policy),selection,
        std::move(material),std::move(recipe),std::move(sources));
}
SharedTaiwanNativeWorldHostPlan::StoredSources
SharedTaiwanNativeWorldHostPlan::StoredSources::with_owned_pk_return_owned_status(
        const Context& context,std::shared_ptr<const TaiwanNativeActorResourceBank> bank,
        TaiwanCustomFullActorProfile::Policy policy,OwnedTaiwanPkReturnSceneSource::Selection selection,
        TaiwanNativeActorResourceSource::Configuration configuration,TaiwanActorStatusOwnedSource::Policy status_policy,
        OwnedPkProfileRecipe recipe,StoredSources sources) {
    if(!context.common_world||!sources.entered||!sources.actor_status_incarnations)
        throw std::invalid_argument("TW owned status requires actual initial scene and host incarnations");
    auto status=TaiwanActorStatusOwnedSource::create(context.common_world->presence(),
        sources.actor_status_incarnations,std::move(status_policy));
    if(!status)throw std::invalid_argument("TW owned status cannot retain the actual host incarnation source");
    auto real_source=with_initial_saved_actor_input(context.common_world->presence(),
        context.initial_actor_inputs,context.common_world->transports(),context.game,std::move(sources.entered));
    sources.entered=[status,real_source=std::move(real_source)](
            Session& session,const SharedTaiwanWorldEntered::Scope& scope)
            ->std::optional<SharedTaiwanWorldEntered::Native> {
        auto native=real_source(session,scope);
        if(!native)return {};
        try {
            struct InitialScene {
                const std::weak_ptr<Session> connection;
                const SharedTaiwanWorldEntered::Scope scope;
                std::optional<TaiwanActorStatusOwnedSource::InitialInstall> ticket;
                bool started=false,cancelled=false;
                InitialScene(Session& session,const SharedTaiwanWorldEntered::Scope& value)
                    :connection(session.weak_from_this()),scope(value){}
            };
            const auto state=std::make_shared<InitialScene>(session,scope);
            const auto matches=[state](Session& candidate,const SharedTaiwanWorldEntered::Scope& value) {
                return state->connection.lock().get()==&candidate&&value.lease==state->scope.lease&&
                    value.entry.wire==state->scope.entry.wire&&value.tail_language==state->scope.tail_language&&
                    value.population==state->scope.population;
            };
            // Preallocate both owning function wrappers before replacing either
            // original callback. A failed construction still owns real cleanup.
            SharedTaiwanWorldEntered::Install install=[status,state,matches,real=native->install](
                    Session& actual,const SharedTaiwanWorldEntered::Scope& value) {
                const auto revoke=[&] {
                    state->cancelled=true;
                    if(state->ticket)status->retire_initial_install(*state->ticket);
                };
                if(state->cancelled||state->started||!matches(actual,value)) {revoke();return false;}
                state->started=true;
                const auto ticket=status->begin_initial_install(actual,value.lease);
                if(!ticket){revoke();return false;}
                state->ticket=*ticket; // Exact entry retained before the real provider.
                // begin allocation can reenter cleanup before the ticket is stored.
                // Never invoke a real install after that scene has been cancelled.
                if(state->cancelled||!matches(actual,value)) {revoke();return false;}
                try {
                    if(!real(actual,value)||state->cancelled||!matches(actual,value)||
                       !status->commit_initial_clear(*ticket)) {revoke();return false;}
                    return true;
                }catch(...) {revoke();throw;}
            };
            SharedTaiwanWorldEntered::Cleanup cleanup=[status,state,real=native->cleanup](
                    const SharedTaiwanWorldEntered::Scope& value) {
                // Retire the exact earlier entry before any real cleanup callback;
                // a stale same-scalar lease never retires a successor incarnation.
                state->cancelled=true;
                if(state->ticket)status->retire_initial_install(*state->ticket);
                real(value);
            };
            native->install=std::move(install);native->cleanup=std::move(cleanup);
            return native;
        }catch(...) {
            try {native->cleanup(scope);}catch(...) {}
            throw;
        }
    };
    ActualStatusSources actual{status,[status](
            std::shared_ptr<const OwnedTaiwanPkReturnSceneSource::Input> input,std::size_t row,
            const OwnedTaiwanPkReturnSceneSource::Equipment& equipment,const SharedWorldPresence::Lease& recipient)
            ->std::optional<TaiwanCustomFullActorProfile::StatusInput> {
        const auto observation=status->observe(std::move(input),row,equipment,recipient);
        if(!observation)return {};
        TaiwanCustomFullActorProfile::StatusInput result{
            TaiwanCustomFullActorProfile::StatusInput::Domain::OrdinaryExplicitClear,
            observation->revision(),0,observation->actor_override(),status,
            [status,observation=*observation](TaiwanCustomFullActorProfile::Check,
                    const TaiwanCustomFullActorProfile::StatusInput& material) {
                return material.owned_status_source.get()==status.get()&&
                    !material.owned_status_source.owner_before(status)&&!status.owner_before(material.owned_status_source)&&
                    material.owned_status&&*material.owned_status==observation&&
                    material.domain==TaiwanCustomFullActorProfile::StatusInput::Domain::OrdinaryExplicitClear&&
                    material.epoch==observation.revision()&&!material.unsupported_domains&&
                    material.actor_override==observation.actor_override()&&material.dependency_owner.get()==status.get()&&
                    !material.dependency_owner.owner_before(status)&&!status.owner_before(material.dependency_owner)&&
                    status->current(observation);
            }};
        result.owned_status_source=status;result.owned_status=*observation;
        return result;
    }};
    return with_owned_pk_return_resources(context,std::move(bank),std::move(policy),selection,
        std::move(configuration),std::move(actual),std::move(recipe),std::move(sources));
}
SharedTaiwanNativeWorldHostPlan::StoredSources::EquipmentPublicationFactory
SharedTaiwanNativeWorldHostPlan::StoredSources::equipment_publication_factory(const Context& context) {
    if(!context.common_world || !context.common_world->owns_repository(context.characters) ||
       !context.accounts || !context.native_equipment_snapshots || !context.native_equipment_snapshot_writer ||
       static_cast<NativeEquipmentSnapshotRepository*>(context.native_equipment_snapshot_writer)!=context.native_equipment_snapshots ||
       !context.native_equipment_snapshot_writer->owns_sources(*context.accounts,context.characters))
        throw std::invalid_argument("TW equipment publication requires actual same Application Context sources");
    auto* writer=context.native_equipment_snapshot_writer;
    auto* accounts=context.accounts;auto* characters=&context.characters;
    auto common=context.common_world;const auto thread=std::this_thread::get_id();
    return [writer,accounts,characters,common=std::move(common),thread](
            SqliteNativeEquipmentSnapshotRepository::Committed committed) {
        if(std::this_thread::get_id()!=thread)
            throw std::logic_error("TW equipment publication factory game owner mismatch");
        return SharedTaiwanNativeEquipmentPublicationSource::create(*writer,*accounts,*characters,
            common->presence(),common->visibility(),std::move(committed));
    };
}
SharedTaiwanNativeWorldHostPlan::Sources
SharedTaiwanNativeWorldHostPlan::Sources::with_actor_status_write_fence(const Context& context,Sources sources) {
    if(!context.common_world || sources.actor_status_write_fence)
        throw std::invalid_argument("TW status writer fence requires a fresh explicit actual host binding");
    sources.actor_status_write_fence=TaiwanActorStatusWriteFence::create(context.common_world->presence());
    return sources;
}
SharedTaiwanNativeWorldHostPlan::Sources
SharedTaiwanNativeWorldHostPlan::Sources::with_actor_status_incarnations(const Context& context,Sources sources) {
    if(!context.common_world||sources.actor_status_incarnations)
        throw std::invalid_argument("TW actor incarnations require a fresh explicit actual host binding");
    sources.actor_status_incarnations=TaiwanActorStatusIncarnationSource::create(context.common_world->presence());
    return sources;
}
SharedTaiwanNativeWorldHostPlan::Sources
SharedTaiwanNativeWorldHostPlan::Sources::with_owned_inventory_movement(const Context& context,Sources sources) {
    if(sources.movement_custody)throw std::invalid_argument("TW movement custody already installed");
    sources.movement_custody=StoredSources::owned_equipment_transaction(context);return sources;
}
SharedTaiwanNativeWorldHostPlan::StoredSources
SharedTaiwanNativeWorldHostPlan::StoredSources::with_actor_status_write_fence(const Context& context,StoredSources sources) {
    if(!context.common_world || sources.actor_status_write_fence)
        throw std::invalid_argument("TW stored writer fence requires a fresh explicit actual host binding");
    sources.actor_status_write_fence=TaiwanActorStatusWriteFence::create(context.common_world->presence());
    return sources;
}
SharedTaiwanNativeWorldHostPlan::StoredSources
SharedTaiwanNativeWorldHostPlan::StoredSources::with_actor_status_incarnations(const Context& context,StoredSources sources) {
    if(!context.common_world||sources.actor_status_incarnations)
        throw std::invalid_argument("TW stored actor incarnations require a fresh explicit actual host binding");
    sources.actor_status_incarnations=TaiwanActorStatusIncarnationSource::create(context.common_world->presence());
    return sources;
}
SharedTaiwanNativeWorldHostPlan::StoredSources
SharedTaiwanNativeWorldHostPlan::StoredSources::with_owned_inventory_movement(const Context& context,StoredSources sources) {
    if(sources.movement_custody)throw std::invalid_argument("TW movement custody already installed");
    sources.movement_custody=owned_equipment_transaction(context);return sources;
}
SharedTaiwanNativeWorldHostPlan::RecordSources
SharedTaiwanNativeWorldHostPlan::RecordSources::with_owned_bag_move_material(
    const Context& context,RecordSources records) {
    if(records.others.inventory_move)throw std::invalid_argument("TW actual C24 source already installed");
    auto transaction=StoredSources::owned_equipment_transaction(context);
    records.others.inventory_move=SharedTaiwanOwnedBagMoveSource::create_with_item_material(std::move(transaction),
        *context.accounts,context.characters,context.common_world->presence());
    return records;
}
SharedTaiwanNativeWorldHostPlan::RecordSources
SharedTaiwanNativeWorldHostPlan::RecordSources::with_owned_bag_moves(
    const Context& context,RecordSources records) {
    if(records.others.inventory_move)throw std::invalid_argument("TW actual C24 source already installed");
    auto transaction=StoredSources::owned_equipment_transaction(context);
    records.others.inventory_move=SharedTaiwanOwnedBagMoveSource::create(std::move(transaction),
        *context.accounts,context.characters,context.common_world->presence());
    return records;
}
SharedTaiwanNativeWorldHostPlan::RecordSources
SharedTaiwanNativeWorldHostPlan::RecordSources::with_owned_item_requests(
    const Context& context,SharedTaiwanOwnedItemRequestSource::Action action,RecordSources records) {
    if(records.others.selection_item)throw std::invalid_argument("TW actual C28 source already installed");
    auto selection=StoredSources::owned_item_selection(context);
    records.others.selection_item=SharedTaiwanOwnedItemRequestSource::create(
        std::move(selection),context.common_world->presence(),std::move(action));
    return records;
}
SharedTaiwanNativeWorldHostPlan::RecordSources
SharedTaiwanNativeWorldHostPlan::RecordSources::with_owned_item_definition_requests(
    const Context& context,SharedTaiwanOwnedItemRequestSource::Action action,RecordSources records) {
    if(records.others.selection_item)throw std::invalid_argument("TW actual C28 source already installed");
    auto selection=StoredSources::owned_item_selection(context,true);
    records.others.selection_item=SharedTaiwanOwnedItemRequestSource::create(
        std::move(selection),context.common_world->presence(),std::move(action));
    return records;
}
SharedTaiwanNativeWorldHostPlan::RecordSources
SharedTaiwanNativeWorldHostPlan::RecordSources::with_owned_item_deity_equipment_requests(
    const Context& context,SharedTaiwanOwnedItemRequestSource::Action action,RecordSources records) {
    if(records.others.selection_item)throw std::invalid_argument("TW actual C28 source already installed");
    auto selection=StoredSources::owned_item_selection(context,true,true);
    records.others.selection_item=SharedTaiwanOwnedItemRequestSource::create(
        std::move(selection),context.common_world->presence(),std::move(action));
    return records;
}
std::shared_ptr<SharedTaiwanOwnedItemSelectionSource>
SharedTaiwanNativeWorldHostPlan::StoredSources::owned_item_selection(const Context& context,bool definitions,bool deity_equipment) {
    if(deity_equipment&&!definitions)throw std::invalid_argument("TW deity selection requires definitions mode");
    if(!context.common_world||!context.common_world->owns_repository(context.characters)||!context.accounts||
       !context.owned_inventory||!context.owned_inventory_writer||
       static_cast<OwnedInventoryRepository*>(context.owned_inventory_writer)!=context.owned_inventory||
       !context.owned_inventory_writer->owns_sources(*context.accounts,context.characters))
        throw std::invalid_argument("TW owned item selection requires actual same Application Context sources");
    if(deity_equipment)return SharedTaiwanOwnedItemSelectionSource::create_with_deity_equipment(*context.owned_inventory_writer,*context.accounts,
        context.characters,context.common_world->presence());
    if(definitions)return SharedTaiwanOwnedItemSelectionSource::create_with_definitions(*context.owned_inventory_writer,*context.accounts,
        context.characters,context.common_world->presence());
    return SharedTaiwanOwnedItemSelectionSource::create(*context.owned_inventory_writer,*context.accounts,
        context.characters,context.common_world->presence());
}
std::shared_ptr<SqliteOwnedEquipmentTransaction>
SharedTaiwanNativeWorldHostPlan::StoredSources::owned_equipment_transaction(const Context& context) {
    if(!context.common_world||!context.common_world->owns_repository(context.characters)||!context.accounts||
       !context.owned_inventory||!context.owned_inventory_writer||!context.native_equipment_snapshots||
       !context.native_equipment_snapshot_writer||
       static_cast<OwnedInventoryRepository*>(context.owned_inventory_writer)!=context.owned_inventory||
       static_cast<NativeEquipmentSnapshotRepository*>(context.native_equipment_snapshot_writer)!=context.native_equipment_snapshots||
       !context.owned_inventory_writer->owns_sources(*context.accounts,context.characters)||
       !context.native_equipment_snapshot_writer->owns_sources(*context.accounts,context.characters))
        throw std::invalid_argument("TW joint equipment requires both actual Application writers");
    return std::make_shared<SqliteOwnedEquipmentTransaction>(*context.owned_inventory_writer,*context.native_equipment_snapshot_writer);
}
SharedTaiwanNativeWorldHostPlan::StoredSources::OwnedEquipmentPublicationFactory
SharedTaiwanNativeWorldHostPlan::StoredSources::owned_equipment_publication_factory(
    const Context& context,std::shared_ptr<SqliteOwnedEquipmentTransaction> transaction) {
    if(!transaction||!context.accounts||!context.common_world||
       !context.common_world->owns_repository(context.characters)||!context.owned_inventory_writer||
       !context.native_equipment_snapshot_writer||
       static_cast<OwnedInventoryRepository*>(context.owned_inventory_writer)!=context.owned_inventory||
       static_cast<NativeEquipmentSnapshotRepository*>(context.native_equipment_snapshot_writer)!=context.native_equipment_snapshots||
       !transaction->owns_writers(*context.owned_inventory_writer,*context.native_equipment_snapshot_writer)||
       !transaction->owns_sources(*context.accounts,context.characters))
        throw std::invalid_argument("TW joint publication requires exact same Application transaction");
    auto* accounts=context.accounts;auto* characters=&context.characters;
    auto common=context.common_world;const auto thread=std::this_thread::get_id();
    return [transaction=std::move(transaction),accounts,characters,common=std::move(common),thread](
        SqliteOwnedEquipmentTransaction::Committed committed) {
        if(std::this_thread::get_id()!=thread)throw std::logic_error("TW joint publication factory game owner mismatch");
        return SharedTaiwanNativeEquipmentPublicationSource::create(transaction,*accounts,*characters,
            common->presence(),common->visibility(),std::move(committed));
    };
}
std::shared_ptr<SqliteOwnedEquipmentTransaction>
SharedTaiwanNativeWorldHostPlan::StoredSources::owned_equipment_entry_transaction(const Context& context) {
    if(!context.common_world||!context.common_world->owns_repository(context.characters)||!context.accounts||
       !context.owned_inventory||!context.owned_inventory_writer||!context.native_equipment_snapshots||
       !context.native_equipment_snapshot_writer||!context.native_world_entries||!context.native_world_entry_writer||
       static_cast<OwnedInventoryRepository*>(context.owned_inventory_writer)!=context.owned_inventory||
       static_cast<NativeEquipmentSnapshotRepository*>(context.native_equipment_snapshot_writer)!=context.native_equipment_snapshots||
       static_cast<NativeWorldEntrySnapshotRepository*>(context.native_world_entry_writer)!=context.native_world_entries||
       !context.owned_inventory_writer->owns_sources(*context.accounts,context.characters)||
       !context.native_equipment_snapshot_writer->owns_sources(*context.accounts,context.characters)||
       !context.native_world_entry_writer->owns_sources(*context.accounts,context.characters))
        throw std::invalid_argument("TW entry/equipment requires all three actual Application writers");
    return std::make_shared<SqliteOwnedEquipmentTransaction>(*context.owned_inventory_writer,
        *context.native_equipment_snapshot_writer,*context.native_world_entry_writer);
}
SharedTaiwanNativeWorldHostPlan::StoredSources::OwnedEquipmentEntryPublicationFactory
SharedTaiwanNativeWorldHostPlan::StoredSources::owned_equipment_entry_publication_factory(
    const Context& context,std::shared_ptr<SqliteOwnedEquipmentTransaction> transaction) {
    if(!transaction||!context.accounts||!context.common_world||
       !context.common_world->owns_repository(context.characters)||!context.owned_inventory_writer||
       !context.native_equipment_snapshot_writer||!context.native_world_entry_writer||
       static_cast<OwnedInventoryRepository*>(context.owned_inventory_writer)!=context.owned_inventory||
       static_cast<NativeEquipmentSnapshotRepository*>(context.native_equipment_snapshot_writer)!=context.native_equipment_snapshots||
       static_cast<NativeWorldEntrySnapshotRepository*>(context.native_world_entry_writer)!=context.native_world_entries||
       !transaction->owns_writers(*context.owned_inventory_writer,*context.native_equipment_snapshot_writer)||
       !transaction->owns_entry_writer(*context.native_world_entry_writer)||
       !transaction->owns_sources(*context.accounts,context.characters))
        throw std::invalid_argument("TW entry/equipment publication requires exact three-writer Context");
    auto* accounts=context.accounts;auto* characters=&context.characters;
    auto common=context.common_world;const auto thread=std::this_thread::get_id();
    return [transaction=std::move(transaction),accounts,characters,common=std::move(common),thread](
        SqliteOwnedEquipmentTransaction::EntryCommitted committed) {
        if(std::this_thread::get_id()!=thread)throw std::logic_error("TW entry/equipment publication game owner mismatch");
        return SharedTaiwanNativeEquipmentPublicationSource::create(transaction,*accounts,*characters,
            common->presence(),common->visibility(),std::move(committed));
    };
}
SharedTaiwanNativeWorldHostPlan::StoredSources::OwnedInventoryReplyFactory
SharedTaiwanNativeWorldHostPlan::StoredSources::owned_inventory_reply_factory(
    const Context& context,std::shared_ptr<SqliteOwnedEquipmentTransaction> transaction,bool definitions,bool deity_equipment) {
    if(!transaction || !context.accounts || !context.native_equipment_snapshot_writer ||
       static_cast<NativeEquipmentSnapshotRepository*>(context.native_equipment_snapshot_writer)!=context.native_equipment_snapshots ||
       !context.owned_inventory_writer ||
       !transaction->owns_writers(*context.owned_inventory_writer,*context.native_equipment_snapshot_writer) ||
       !transaction->owns_sources(*context.accounts,context.characters))
        throw std::invalid_argument("TW inventory reply requires exact same Application joint transaction");
    auto reader=owned_item_selection(context,definitions,deity_equipment);const auto thread=std::this_thread::get_id();
    return [transaction=std::move(transaction),reader=std::move(reader),thread](
        Session& session,const Session::NativeWorldSelectionInput& input,
        const SharedTaiwanOwnedItemSelectionSource::Selection& selection,
        SqliteOwnedEquipmentTransaction::Before before,SqliteOwnedEquipmentTransaction::State after,
        std::vector<SharedTaiwanOwnedInventoryReplySource::Operation> operations,
        SharedTaiwanOwnedInventoryReplySource::Budgets budgets) {
        if(std::this_thread::get_id()!=thread)throw std::logic_error("TW inventory reply factory game owner mismatch");
        return SharedTaiwanOwnedInventoryReplySource::prepare(transaction,reader,session,input,selection,
            std::move(before),std::move(after),std::move(operations),budgets);
    };
}
SharedWorldHostPlan SharedTaiwanNativeWorldHostPlan::create_from_stored_entry(
        std::string client,StoredSourceFactory supply,Dispatch dispatch,bool native_characters,bool native_equipment,bool owned_inventory,
        TaiwanWorldEntryIdentity identity) {
    const auto digest=client.size()==64 && std::all_of(client.begin(),client.end(),[](char c) {
        return (c>='0' && c<='9') || (c>='a' && c<='f');
    });
    if(!digest || !supply || !valid_taiwan_world_entry_identity(identity) ||
       (identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle && !native_characters))
        throw std::invalid_argument("TW stored host requires actual build and complete source factory");
    if(owned_inventory && client!=SharedTaiwanOwnedItemSelectionSource::client_pin)
        throw std::invalid_argument("TW owned selection requires the exact recovered native build");
    auto plan=create([client=std::move(client),supply=std::move(supply),native_characters,identity,dispatch](const Context& context) {
        // Check exact borrowed reader before invoking any external supplier.
        // Existing Factory::get owns construction/reentry/lifetime qualification.
        if(!context.native_world_entries || !context.native_world_entries->owns_characters(context.characters))
            throw std::invalid_argument("TW stored host requires its actual Application character delivery reader");
        const auto* reader=context.native_world_entries;
        auto actual=supply(context);
        struct ForwardMonitor {
            TaiwanActorStatusWriteFence* fence;TaiwanActorStatusIncarnationSource* incarnations;bool forwarded=false;
            ~ForwardMonitor(){if(!forwarded){if(fence)fence->stop();if(incarnations)incarnations->stop();}}
        } monitor{actual.actor_status_write_fence.get(),actual.actor_status_incarnations.get()};
        if(actual.return_profiles_installed_)actual.require_profile_entry_binding();
        // Before constructing list/entry owners from the stored wrapper.
        require_owned_pk_sources(context,actual.owned_pk,dispatch);
        if(native_characters!=bool(actual.characters))
            throw std::invalid_argument("TW stored native list selection differs from the explicit plan");
        std::optional<SharedTaiwanNativeCharacterListSource::Binding> characters;
        if(native_characters) {
            if(!context.accounts || !context.native_character_summaries)
                throw std::invalid_argument("TW stored native list lacks its exact common account/summary readers");
            if(actual.characters->handoff) {
                if(actual.characters->publish || actual.characters->link ||
                   !actual.characters->handoff->matches_sources(*context.accounts,context.characters,
                        *context.native_character_summaries,client,actual.actual_session_capacity))
                    throw std::invalid_argument("TW list handoff differs from actual host readers/build/capacity");
                auto handoff=actual.characters->handoff->binding();
                actual.characters->publish=std::move(handoff.publish);
                actual.characters->link=std::move(handoff.link);
            }
            SharedTaiwanNativeCharacterListSource::Prepare prepare;
            if(actual.characters->offer) {
                if(!context.native_character_summary_writer ||
                   static_cast<NativeCharacterSummarySnapshotRepository*>(context.native_character_summary_writer)!=context.native_character_summaries)
                    throw std::invalid_argument("TW native offer requires the exact Application writer/reader object");
                prepare=SharedTaiwanNativeCharacterOfferSource::create(*context.native_character_summary_writer,
                    *context.accounts,context.characters,client,std::move(actual.characters->offer));
            }
            characters=SharedTaiwanNativeCharacterListSource::create(*context.accounts,context.characters,
                *context.native_character_summaries,client,std::move(actual.characters->target),std::move(actual.characters->qualify),
                actual.actual_session_capacity,std::move(actual.characters->publish),std::move(actual.characters->link),std::move(prepare));
        }
        if(context.native_world_entries!=reader || !reader->owns_characters(context.characters) || !actual.entry_qualify)
            throw std::invalid_argument("TW stored host source changed or lacks actual full material qualification");
        auto entry=SharedTaiwanStoredWorldEntrySource::create(*context.native_world_entries,context.characters,
            context.maps,client,std::move(actual.entry_qualify),identity);
        SharedTaiwanWorldEntrySource::Prepare entry_prepare;
        if(actual.entry_offer) {
            if(!native_characters || !characters || !context.accounts || !context.native_world_entry_writer ||
               static_cast<NativeWorldEntrySnapshotRepository*>(context.native_world_entry_writer)!=context.native_world_entries)
                throw std::invalid_argument("TW entry offer requires actual native selection and identical writer/reader");
            entry_prepare=SharedTaiwanNativeWorldEntryOfferSource::create(*context.native_world_entry_writer,
                *context.accounts,context.characters,context.maps,client,std::move(actual.entry_offer),identity);
        }
        auto forwarded=Sources{std::move(entry),std::move(actual.entered),std::move(actual.movement_rules),
            std::move(actual.movement_resources),actual.actual_session_capacity,std::move(actual.records),std::move(characters),
            std::move(entry_prepare),std::move(actual.movement_custody),std::move(actual.owned_pk),
            std::move(actual.actor_status_write_fence),std::move(actual.actor_status_incarnations)};
        monitor.forwarded=true;return forwarded;
    },dispatch,native_characters,identity);
    plan.requires_native_world_entry_snapshots=true;
    plan.requires_native_character_summaries=native_characters;
    plan.requires_native_equipment_snapshots=native_equipment;
    plan.requires_owned_inventory_storage=owned_inventory;
    return plan;
}
SharedWorldHostPlan SharedTaiwanNativeWorldHostPlan::create(SourceFactory source,Dispatch dispatch,bool native_characters,
        TaiwanWorldEntryIdentity identity) {
    if(!source)throw std::invalid_argument("TW native host plan requires an actual source factory");
    if(dispatch!=Dispatch::MovementOnly && dispatch!=Dispatch::MixedRecords)
        throw std::invalid_argument("TW native host plan dispatch is not a qualified selection");
    if(!valid_taiwan_world_entry_identity(identity) ||
       (identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle && !native_characters))
        throw std::invalid_argument("Independent TW entry identity requires the complete native selection source");
    auto factory=std::make_shared<Factory>(std::move(source),dispatch,native_characters,identity);SharedWorldHostPlan plan;
    plan.taiwan_entry_identity=identity;
    plan.supports_app_owned_initial_deities=true;
    plan.supports_app_owned_initial_player=true; // CUSTOM-0149 enforced by this actual Entered owner.
    plan.make_owned_taiwan_pk_sources=[factory](const Context& context)->std::optional<OwnedPkSources> {
        // Unrequested recipe calls do not invoke or drain the weak source owner.
        if(!context.app_owned_pk)return std::nullopt;
        auto owner=factory->get(context); // Exact existing Context or one guarded construction.
        if(!owner->owned_pk||std::exchange(owner->pk_taken,true)) {
            owner->invalidate();throw std::logic_error("TW owned PK source was already taken or missing");
        }
        owner->owned_pk->require_complete();
        auto actual=std::move(owner->owned_pk);
        owner->owned_pk.reset(); // Remove before retaining Owner; never create a cycle.
        actual->host_owner_=owner; // Keeps callback-first Factory::bound alive.
        return actual;
    };
    plan.requires_native_character_summaries=native_characters;
    if(native_characters)plan.make_taiwan_native_characters=[factory](const Context& context) {
        auto owner=factory->get(context);
        if(!owner->characters_source || std::exchange(owner->characters_taken,true)) {
            owner->invalidate();throw std::logic_error("TW native list/selection owner was already taken or missing");
        }
        return SharedTaiwanNativeCharacterListSource::Binding{
            [owner,invoke=owner->characters_source->list](Session& session) {
                owner->check();return invoke(session);
            },
            [owner,invoke=owner->characters_source->select](Session& session,const RecoveredPostCreateSelect::Selection& input,std::optional<std::uint64_t> created) {
                owner->check();return invoke(session,input,created);
            },
            [owner,invoke=owner->characters_source->invalidate_active] {owner->check();invoke();},
            [owner,invoke=owner->characters_source->current](Session& session,const Session::NativeCharacterList& delivery) {
                owner->check();return invoke(session,delivery);
            },
            [owner,invoke=owner->characters_source->complete](Session& session,const Session::NativeCharacterList& delivery,bool written) {
                owner->check();return invoke(session,delivery,written);
            },
            [owner,invoke=owner->characters_source->selected](std::uint64_t session,std::uint64_t account,std::uint64_t character) {
                owner->check();return invoke(session,account,character);
            },
            [owner,invoke=owner->characters_source->invalidate_selection](std::uint64_t session) {
                owner->check();invoke(session);
            }
        };
    };
    plan.make_taiwan_actor_status_incarnations=[factory](const Context& context) {
        auto owner=factory->get(context);owner->check();return owner->actor_status_incarnations;
    };
    plan.make_taiwan_actor_status_write_fence=[factory](const Context& context) {
        auto owner=factory->get(context);owner->check();
        return owner->actor_status_write_fence;
    };
    plan.make_taiwan_entered_async=[factory](const Context& context) {
        auto owner=factory->get(context);
        if(std::exchange(owner->entered_taken,true)) {
            owner->invalidate();
            throw std::logic_error("TW native host plan initial scene owner was already taken");
        }
        return SharedTaiwanWorldLifecycle::AsyncOwner{
            [owner](Session& session,const SharedWorldPresence::Lease& lease,const RecoveredWorldEntryView& view,
                    SharedTaiwanWorldLifecycle::ReadyCompletion done) {
                owner->check();owner->entered.entered(session,lease,view,std::move(done));
            },
            [owner](Session& session,const SharedWorldPresence::Lease& lease) {owner->cancel(session,lease);}
        };
    };
    plan.make_taiwan_world_entry=[factory](const Context& context) {
        auto owner=factory->get(context);
        if(std::exchange(owner->entry_taken,true)) {
            owner->invalidate();
            throw std::logic_error("TW native host plan entry owner was already taken");
        }
        return SharedTaiwanWorldEntrySource::Entry{
            [owner](std::uint64_t session,std::uint64_t account,std::uint64_t character) {
                owner->check();return owner->entry(session,account,character);
            }
        };
    };
    plan.make_taiwan_movement=[factory](const Context& context) {
        auto owner=factory->get(context);
        if(std::exchange(owner->movement_taken,true)) {
            owner->invalidate();
            throw std::logic_error("TW native host plan movement owner was already taken");
        }
        return SharedTaiwanMovementSource::Binding{
            [owner](Session& session,std::span<const RecoveredMovement::Request> requests) {
                owner->check();return owner->binding.movement(session,requests);
            },
            [owner](Session& session) {owner->check();owner->binding.release(session);},
            [owner] {owner->check();owner->binding.invalidate_active();},
            [owner](Session& session,const SharedWorldPresence::Lease& lease) {
                owner->check();return owner->binding.retire(session,lease);
            }
        };
    };
    if(dispatch==Dispatch::MixedRecords)plan.make_taiwan_world_records=[factory](const Context& context) {
        auto owner=factory->get(context);
        if(!owner->movement_taken || !owner->records || std::exchange(owner->records_taken,true)) {
            owner->invalidate();
            throw std::logic_error("TW native records require their actual movement owner and fresh sources");
        }
        auto sources=std::move(*owner->records);owner->records.reset();
        auto actual=SharedTaiwanWorldRecordSource::create(owner->common->presence(),owner->binding,
            std::move(sources.others),std::move(sources.current),sources.budgets,owner->capacity);
        if(!actual.records || !actual.release || !actual.invalidate_active)
            throw std::invalid_argument("TW native records did not retain complete actual sources");
        // This invalidator owns only the actual record source. Its movement
        // input is the raw same-host binding, not a facade capturing Owner;
        // retaining it here therefore creates no Owner/source ownership cycle.
        owner->records_invalidate=actual.invalidate_active;
        return SharedTaiwanWorldRecordSource::Binding{
            [owner,invoke=std::move(actual.records)](Session& session,
                std::span<const RecoveredWorldRecords::Record> records) {
                owner->check();return invoke(session,records);
            },
            [owner,release=std::move(actual.release)](Session& session) {owner->check();release(session);},
            [owner] {owner->invalidate();},actual.spectator6e,actual.spectator_close,actual.native_selection_input,actual.native_skill_commands,actual.native_world_skill_requests,actual.deity_selection_source,actual.native_preborn_requests
        };
    };
    return plan;
}
}
