#include "core/SharedTaiwanNativeWorldHostPlan.h"
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
    asio::any_io_executor game;
    std::shared_ptr<SharedWorldHost> common;
    const std::thread::id thread=std::this_thread::get_id();
    SharedTaiwanWorldEntrySource::Entry entry;
    SharedTaiwanWorldLifecycle::AsyncOwner entered;
    std::shared_ptr<SharedTaiwanNativeMovementHost> movement;
    SharedTaiwanMovementSource::Binding binding;
    std::optional<Plan::RecordSources> records;
    std::optional<SharedTaiwanNativeCharacterListSource::Binding> characters_source;
    std::function<void()> records_invalidate;
    const std::size_t capacity;
    bool entry_taken=false,entered_taken=false,movement_taken=false,records_taken=false;
    bool characters_taken=false;

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
         game(context.game),common(context.common_world),
         records(std::move(sources.records)),characters_source(std::move(sources.characters)),capacity(sources.actual_session_capacity) {
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
        entry=SharedTaiwanWorldEntrySource::create(*characters,*maps,std::move(sources.entry),
            characters_source?characters_source->selected:SharedTaiwanNativeCharacterListSource::SelectedSource{},
            std::move(sources.entry_prepare),characters_source?presence:nullptr,identity);
        entered=SharedTaiwanWorldEntered::create(presence,visibility,std::move(sources.entered),identity);
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
    }
    ~Owner() {
        if(std::this_thread::get_id()!=thread)std::terminate();
        // Real callbacks are game-affine. The plan factory keeps only a weak
        // reference; these owners therefore drain with Application's facades.
        records_invalidate={};records.reset();characters_source.reset();binding={};movement.reset();entered={};entry={};
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
           context.common_world!=common || context.game!=game || !common->owns_repository(*characters)) {
            invalidate();
            throw std::invalid_argument("TW native host plan cannot join a different Application Context");
        }
    }
    void invalidate() const {
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
        try {
            if(!context.common_world || !context.common_world->owns_repository(context.characters))
                throw std::invalid_argument("TW native host plan needs the actual Application common world");
            auto sources=source(context);
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
SharedTaiwanNativeWorldHostPlan::Sources::with_owned_inventory_movement(const Context& context,Sources sources) {
    if(sources.movement_custody)throw std::invalid_argument("TW movement custody already installed");
    sources.movement_custody=StoredSources::owned_equipment_transaction(context);return sources;
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
    auto plan=create([client=std::move(client),supply=std::move(supply),native_characters,identity](const Context& context) {
        // Check exact borrowed reader before invoking any external supplier.
        // Existing Factory::get owns construction/reentry/lifetime qualification.
        if(!context.native_world_entries || !context.native_world_entries->owns_characters(context.characters))
            throw std::invalid_argument("TW stored host requires its actual Application character delivery reader");
        const auto* reader=context.native_world_entries;
        auto actual=supply(context);
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
        return Sources{std::move(entry),std::move(actual.entered),std::move(actual.movement_rules),
            std::move(actual.movement_resources),actual.actual_session_capacity,std::move(actual.records),std::move(characters),
            std::move(entry_prepare),std::move(actual.movement_custody)};
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
            [owner] {owner->invalidate();},actual.spectator6e,actual.spectator_close,actual.native_selection_input,actual.native_skill_commands,actual.native_world_skill_requests,actual.deity_selection_source
        };
    };
    return plan;
}
}
