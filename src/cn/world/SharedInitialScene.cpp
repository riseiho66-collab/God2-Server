#include "cn/world/SharedInitialScene.h"
#include "cn/world/SharedSceneIdentity.h"
#include "cn/world/SharedWorldReady.h"
#include <algorithm>
#include <stdexcept>
#include <utility>

namespace god2::cn {
struct InitialAppearanceIdentity {};
SharedInitialAppearanceSource::SharedInitialAppearanceSource(std::shared_ptr<const InitialAppearanceIdentity> identity,
    std::uint64_t revision,god2cn::CnAppearanceRomInputs inputs,Current current)
    :identity_(std::move(identity)),revision_(revision),inputs_(std::move(inputs)),current_(std::move(current)) {}
void SharedInitialScene::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN initial-scene game owner mismatch");
}
SharedInitialScene::SharedInitialScene(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,const NativeMapCatalog& maps,
    std::span<const std::uint8_t> begin,std::uint64_t revision,Prepared prepared)
    :connection_(connection),presence_(std::move(presence)),lease_(lease),maps_(maps),
     revision_(revision),prepared_(std::move(prepared)) {
    appearance_identity_=std::make_shared<const InitialAppearanceIdentity>();
    std::copy(begin.begin(),begin.end(),begin_.begin()); // Factory requires all37 bytes.
}
bool SharedInitialScene::bound(const std::shared_ptr<Connection>& connection) const {
    return connection && connection_.lock()==connection && !connection->closing() &&
        connection->role()==Connection::Transport::Role::World &&
        connection->verified_account_id()==lease_.account &&
        connection->world_session_id()==lease_.session &&
        connection->world_character_offered(lease_.character) && presence_->current(lease_);
}
bool SharedInitialScene::map_current() const {
    const auto entry=god2cn::CnWorldEntry::read_begin_play(begin_);
    const auto map=maps_.lookup(NativeMapCatalog::current_dataset_id,lease_.position.area,lease_.position.scene);
    return entry && map && SharedSceneIdentity::matches(*map,lease_.position,*entry,std::nullopt);
}
std::shared_ptr<SharedInitialScene> SharedInitialScene::prepare(
    const std::shared_ptr<Connection>& connection,std::shared_ptr<SharedWorldPresence> presence,
    const Lease& lease,const NativeMapCatalog& maps,const god2cn::CnSceneAssets& assets,
    std::span<const std::uint8_t> begin,std::uint64_t revision,
    std::size_t encoded_budget,std::size_t plain_budget) {
    if(!connection || !presence || !revision || !encoded_budget || !plain_budget ||
       connection->closing() || connection->role()!=Connection::Transport::Role::World ||
       connection->verified_account_id()!=lease.account || connection->world_session_id()!=lease.session ||
       !connection->world_character_offered(lease.character) || !presence->preparation_current(lease) ||
       presence->ready(lease))return {};
    const auto entry=god2cn::CnWorldEntry::read_begin_play(begin);
    if(!entry || entry->actor_handle()!=lease.actor_handle)return {};
    const auto map=maps.lookup(NativeMapCatalog::current_dataset_id,lease.position.area,lease.position.scene);
    const auto* common=SharedSceneIdentity::find(lease.position.area,lease.position.scene);
    const auto* cn=god2cn::CnSceneAssets::find(entry->map_family(),entry->map_index());
    if(!map || !common || !cn || !SharedSceneIdentity::matches(*map,lease.position,*entry,std::nullopt) ||
       cn->declared_mode!=common->declared_kind || cn->native_mdt_path!=common->native_mdt_path)return {};
    // These loaders read the explicitly supplied CN root. They retain selected
    // plain/wrapped resources and compose actual masks/chunks/ordered objects.
    // Native actor mode is not the catalog's declared kind; never substitute it.
    std::optional<Prepared> prepared;
    if(entry->scene_mode()==2) {
        auto house=assets.prepare_initial_house(*entry,encoded_budget,plain_budget);
        if(house)prepared.emplace(std::move(*house));
    } else if(entry->scene_mode()==0) {
        auto outdoor=assets.prepare_initial_outdoor(*entry,encoded_budget,plain_budget);
        if(outdoor)prepared.emplace(std::move(*outdoor));
    }
    if(!prepared)return {};
    auto result=std::shared_ptr<SharedInitialScene>(new SharedInitialScene(
        connection,std::move(presence),lease,maps,begin,revision,std::move(*prepared)));
    result->assets_identity_=&assets;
    // Resource loading may fail/throw; no partial proof or state write escapes.
    // Recheck actual ownership/storage/catalog after all resource preparation.
    if(!result->bound(connection) || !result->presence_->preparation_current(lease) ||
       result->presence_->ready(lease) || !result->map_current())return {};
    if(const auto* outdoor=result->outdoor_initial()) {
        if(!result->initial_outdoor_camera_seed())return {};
        result->outdoor_window_=god2cn::CnOutdoorWindow::from_initial(outdoor->resources,outdoor->placement);
    }
    return result;
}
bool SharedInitialScene::matches(const std::shared_ptr<Connection>& connection,
    const std::shared_ptr<SharedWorldReady>& ready,std::uint64_t character,
    const RecoveredPosition& position,std::span<const std::uint8_t> begin) const {
    owner();return ready && character==lease_.character && position==lease_.position &&
        begin.size()==begin_.size() && std::equal(begin.begin(),begin.end(),begin_.begin()) &&
        bound(connection) && presence_->preparation_current(lease_) &&
        ready->matches_preparation(connection,presence_,lease_) && map_current();
}
const god2cn::CnMapPassability& SharedInitialScene::cells() const {
    if(const auto* house=std::get_if<god2cn::CnPreparedHouseScene>(&prepared_))return house->initial_grid;
    return std::get<god2cn::CnPreparedOutdoorScene>(prepared_).placement.neighborhood.grid;
}
std::optional<SharedMovement::Scene> SharedInitialScene::initial_movement_scene(
    const std::shared_ptr<Connection>& connection,const RecoveredPosition& position,
    std::uint64_t revision,std::uint8_t direction) const {
    owner();
    if(revision!=revision_ || direction>7 || position!=lease_.position || !bound(connection) ||
       !presence_->ready(lease_) || !map_current())return std::nullopt;
    const auto stored=presence_->saved_position(lease_);
    if(!stored || *stored!=position)return std::nullopt;
    const auto entry=god2cn::CnWorldEntry::read_begin_play(begin_);
    if(!entry)return std::nullopt;
    return SharedMovement::Scene{position.area,position.scene,revision_,entry->scene_mode(),direction,cells()};
}
const std::vector<std::filesystem::path>& SharedInitialScene::source_files() const {
    owner();return std::visit([](const auto& scene)->const std::vector<std::filesystem::path>& {
        return scene.source_files;
    },prepared_);
}
std::optional<god2cn::CnWorldEntry::BeginPlay> SharedInitialScene::initial_actor_begin_play(
    const std::shared_ptr<Connection>& connection,const std::shared_ptr<SharedWorldPresence>& presence,const Lease& lease) const {
    owner();
    if(presence!=presence_ || lease!=lease_ || !bound(connection) ||
       !presence_->preparation_current(lease_) || !map_current())return std::nullopt;
    return god2cn::CnWorldEntry::read_begin_play(begin_);
}
std::shared_ptr<const SharedInitialAppearanceSource> SharedInitialScene::prepare_appearance_source(
    const std::shared_ptr<Connection>& connection,const std::shared_ptr<SharedWorldPresence>& presence,const Lease& lease,
    const god2cn::CnSceneAssets& assets,std::uint64_t revision,std::size_t encoded,std::size_t plain,
    SharedInitialAppearanceSource::Current current) const {
    owner();
    if(!current || !encoded || !plain || &assets!=assets_identity_ || revision!=revision_)return {};
    const auto begin=initial_actor_begin_play(connection,presence,lease);if(!begin)return {};
    if(!current(SharedInitialAppearanceCheck::BeforeRead,nullptr))return {};
    auto inputs=assets.prepare_normal_initial_appearance_roms(*begin,encoded,plain);if(!inputs)return {};
    const auto retained=std::get_if<god2cn::CnWorldEntry::BeginPlay>(&inputs->rows().source_record());
    const auto now=initial_actor_begin_play(connection,presence,lease);
    if(!retained || !now || *retained!=*begin || *now!=*begin || &assets!=assets_identity_ ||
       revision!=revision_ || !current(SharedInitialAppearanceCheck::AfterRead,&*inputs))return {};
    return std::shared_ptr<const SharedInitialAppearanceSource>(new SharedInitialAppearanceSource(
        appearance_identity_,revision_,std::move(*inputs),std::move(current)));
}
bool SharedInitialScene::appearance_source_current(const std::shared_ptr<const SharedInitialAppearanceSource>& source,
    const std::shared_ptr<Connection>& connection,const std::shared_ptr<SharedWorldPresence>& presence,const Lease& lease) const {
    owner();
    if(!source || source->identity_!=appearance_identity_ || source->revision_!=revision_ || !source->current_)return false;
    const auto begin=initial_actor_begin_play(connection,presence,lease);
    const auto retained=std::get_if<god2cn::CnWorldEntry::BeginPlay>(&source->inputs_.rows().source_record());
    if(!begin || !retained || *begin!=*retained)return false;
    return source->current_(SharedInitialAppearanceCheck::BeforePublish,&source->inputs_);
}
const god2cn::CnPreparedOutdoorScene* SharedInitialScene::outdoor_initial() const {
    owner();return std::get_if<god2cn::CnPreparedOutdoorScene>(&prepared_);
}
std::optional<god2cn::CnOutdoorCamera::Point> SharedInitialScene::initial_outdoor_camera_seed() const {
    owner();const auto* outdoor=outdoor_initial();
    if(!outdoor)return std::nullopt;
    return god2cn::CnOutdoorCamera::initial_mode0_before_cache_switch(outdoor->placement);
}
std::shared_ptr<god2cn::CnOutdoorWindow> SharedInitialScene::outdoor_window(
    const std::shared_ptr<Connection>& connection,const std::shared_ptr<SharedWorldReady>& ready) {
    owner();
    if(!matches(connection,ready,lease_.character,lease_.position,begin_))return {};
    const auto* outdoor=outdoor_initial();
    if(!outdoor)return {};
    return outdoor_window_;
}
}
