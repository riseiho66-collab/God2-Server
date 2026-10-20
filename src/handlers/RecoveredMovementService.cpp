#include "handlers/RecoveredMovementService.h"
#include "db/SqliteOwnedEquipmentTransaction.h"
#include "net/Session.h"
#include "protocol/RecoveredCharacterListCandidate.h"
#include "protocol/RecoveredWorldFrame.h"
#include "protocol/RecoveredWorldEntryView.h"
#include "game/TaiwanWorldEntryIdentity.h"
#include "game/RecoveredWildernessTransfers.h"
#include <algorithm>
#include <fstream>
#include <nlohmann/json.hpp>
#include <cstdlib>
#include <utility>
#include <limits>
#include <string_view>
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2 {
namespace {
int bounded(const nlohmann::json& value,int low,int high) {
    if(!value.is_number_integer()) throw std::invalid_argument("Navigation integer required");
    if(value.is_number_unsigned()) {
        const auto n=value.get<std::uint64_t>();
        if(n>static_cast<std::uint64_t>(high)) throw std::invalid_argument("Navigation integer overflow");
        if(low>0 && n<static_cast<std::uint64_t>(low)) throw std::invalid_argument("Navigation integer below bounds");
        return static_cast<int>(n);
    }
    const auto n=value.get<std::int64_t>();
    if(n<low || n>high) throw std::invalid_argument("Navigation integer outside bounds");
    return static_cast<int>(n);
}
PassGrid pass_grid(const nlohmann::json& value) {
    PassGrid result;
    result.width=bounded(value.at("width"),1,512);
    result.height=bounded(value.at("height"),1,512);
    const auto& cells=value.at("cells");
    if(!cells.is_array() || cells.size()!=static_cast<std::size_t>(result.width*result.height))
        throw std::invalid_argument("Navigation cells mismatch");
    for(const auto& cell:cells) result.cells.push_back(static_cast<std::uint8_t>(bounded(cell,0,255)));
    return result;
}
RecoveredIndoorGrid load_grid(const std::filesystem::path& path) {
    if(std::filesystem::file_size(path)>1024*1024) throw std::invalid_argument("Navigation input too large");
    std::ifstream file(path);
    const auto j=nlohmann::json::parse(file);
    if(j.at("schema")!="god2-recovered-indoor-navigation-v1" ||
       bounded(j.at("area"),0,63)!=2 || bounded(j.at("scene"),0,1023)!=15 ||
       j.at("source").at("asset_sha256")!="42d769c0ff328db3e1e295e17208d0db7a0ff12608976f952dae800ff79c3c00")
        throw std::invalid_argument("Navigation does not match current bootstrap scene");
    const auto base=pass_grid(j.at("base"));
    const auto& objects=j.at("overlays");
    if(!objects.is_array() || objects.size()>1024) throw std::invalid_argument("Navigation placement count rejected");
    std::vector<Placement> overlays;
    for(const auto& object:objects)
        overlays.push_back({pass_grid(object.at("grid")),bounded(object.at("x"),-32767,32767),
                            bounded(object.at("y"),-32767,32767)});
    RecoveredIndoorGrid grid(base,overlays);
    constexpr char digits[]="0123456789abcdef";
    std::string hex;hex.reserve(grid.cells().size()*2);
    for(const auto cell:grid.cells()) { hex+=digits[cell>>4];hex+=digits[cell&15]; }
    if(bounded(j.at("grid").at("side"),1,1025)!=grid.side() || j.at("grid").at("cells_hex")!=hex ||
       grid.cell(17,13)==0)
        throw std::invalid_argument("Navigation reconstruction or initial cell mismatch");
    return grid;
}
// CUSTOM-0052: pin the complete generated bundle, then rebuild every grid from
// its source pass layers. Hash labels alone never qualify editable grid bytes.
std::map<std::uint16_t,RecoveredIndoorGrid> load_indoor_scenes(const std::filesystem::path& path,bool kunlun=false) {
    constexpr std::size_t limit=1024*1024;
    std::ifstream file(path,std::ios::binary);
    if(!file)throw std::invalid_argument("Door navigation bundle unavailable");
    std::string bytes(limit+1,'\0');
    file.read(bytes.data(),static_cast<std::streamsize>(bytes.size()));
    if(file.bad() || file.gcount()<=0 || static_cast<std::size_t>(file.gcount())>limit)
        throw std::invalid_argument("Door navigation bundle size rejected");
    bytes.resize(static_cast<std::size_t>(file.gcount()));
    std::size_t expected_count=kunlun?6u:23u;
#ifdef _WIN32
    BCRYPT_ALG_HANDLE algorithm=nullptr; BCRYPT_HASH_HANDLE hash=nullptr;
    std::array<unsigned char,32> digest{};
    auto status=BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,MS_PRIMITIVE_PROVIDER,0);
    if(BCRYPT_SUCCESS(status))status=BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0);
    if(BCRYPT_SUCCESS(status))status=BCryptHashData(hash,reinterpret_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0);
    if(BCRYPT_SUCCESS(status))status=BCryptFinishHash(hash,digest.data(),static_cast<ULONG>(digest.size()),0);
    const auto destroyed=hash?BCryptDestroyHash(hash):0;
    const auto closed=algorithm?BCryptCloseAlgorithmProvider(algorithm,0):0;
    if(!BCRYPT_SUCCESS(status) || !BCRYPT_SUCCESS(destroyed) || !BCRYPT_SUCCESS(closed))
        throw std::runtime_error("Door navigation SHA256 failed");
    std::string actual;
    for(auto byte:digest) {actual+="0123456789abcdef"[byte>>4];actual+="0123456789abcdef"[byte&15];}
    // CUSTOM-0152: keep the deployed 23-room bundle valid; the independently
    // pinned 26-room Taiwan bundle supplies the three original missing rooms.
    // A count is selected by whole-file SHA, never by caller-controlled JSON.
    if(!kunlun && actual=="cec9ce29fffd1b09e7988d28bc22c330841e7efad2c41a26a0e0cc3a6b1e2868")
        expected_count=26;
    else if(actual!=(kunlun?"9c3af8c338c2c26a5d5ee2156d0105cdf9d893666c656814aaae3973d7333f35":"08ccfb33262913f97383da9abcc8bba58b2705e377fbbec004ee5cdfc35013c2"))
        throw std::invalid_argument("Door navigation bundle source changed");
#else
    throw std::runtime_error("Door navigation requires qualified SHA256 backend");
#endif
    const auto j=nlohmann::json::parse(bytes);
    if(j.at("schema")!=(kunlun?"god2-current-kunlun-doors-v1":"god2-current-town-doors-v1") || j.at("custom_design")!="CUSTOM-0052" ||
       j.at("navigation").size()!=expected_count || j.at("routes").size()!=expected_count)
        throw std::invalid_argument("Door navigation bundle contract rejected");
    std::map<std::uint16_t,RecoveredIndoorGrid> result;
    for(const auto& row:j.at("navigation")) {
        const auto scene=static_cast<std::uint16_t>(bounded(row.at("scene"),kunlun?4:5,kunlun?9:30));
        const auto route=std::find_if(j.at("routes").begin(),j.at("routes").end(),
            [&](const auto& candidate){return candidate.at("scene")==scene;});
        if(route==j.at("routes").end())throw std::invalid_argument("Room route provenance missing");
        if(!route->at("navigation_eligible").template get<bool>())continue;
        if(bounded(row.at("area"),0,63)!=(kunlun?4:2) || bounded(row.at("kind"),0,3)!=2 ||
           result.contains(scene))throw std::invalid_argument("Door navigation scene rejected");
        std::vector<Placement> overlays;
        for(const auto& object:row.at("overlays"))
            overlays.push_back({pass_grid(object.at("grid")),bounded(object.at("x"),-32767,32767),
                                bounded(object.at("y"),-32767,32767)});
        RecoveredIndoorGrid grid(pass_grid(row.at("base")),overlays);
        std::string hex;
        for(auto cell:grid.cells()) {hex+="0123456789abcdef"[cell>>4];hex+="0123456789abcdef"[cell&15];}
        if(row.at("grid").at("side")!=grid.side() || row.at("grid").at("cells_hex")!=hex)
            throw std::invalid_argument("Door navigation grid reconstruction rejected");
        result.emplace(scene,std::move(grid));
    }
    return result;
}
}
RecoveredMovementService::RecoveredMovementService(RecoveredCharacterRepository& characters,
    const std::filesystem::path& navigation):characters_(characters),grid_(load_grid(navigation)) {}
RecoveredMovementService::RecoveredMovementService(RecoveredCharacterRepository& characters,
    const TownDiagnostic& town):characters_(characters),town_(std::in_place,town.navigation),
    center_(town.center),scene_(4),kind_(0),initial_x_(town.x),initial_y_(town.y),
    town_source_consensus_(town.source_consensus) {
    if(!town_->available_center(center_.x,center_.y) || !cell_available(initial_x_,initial_y_))
        throw std::invalid_argument("Town diagnostic center or initial cell unavailable");
    if(!town.indoor_navigation.empty()) grid_=load_grid(town.indoor_navigation);
    if(!town.indoor_scenes.empty())indoor_scenes_=load_indoor_scenes(town.indoor_scenes);
    if(!town.kunlun_indoor_scenes.empty())kunlun_indoor_scenes_=load_indoor_scenes(town.kunlun_indoor_scenes,true);
    if(!town.island_navigation.empty()) {
        // Preserve the old nine/24-window source contracts. Full source files
        // must pass their independent whole-file pin in the generic loader.
        if(std::filesystem::file_size(town.island_navigation)>11*1024*1024)
            throw std::invalid_argument("Island navigation input too large");
        std::ifstream file(town.island_navigation);const auto metadata=nlohmann::json::parse(file);
        if(metadata.at("schema")=="god2-current-parent-full-navigation-v1")
            island_full_.emplace(town.island_navigation,2);
        else island_.emplace(town.island_navigation);
    }
    if(!town.kunlun_parent_navigation.empty()) {
        if(town.birthplace_navigation.empty() || !town.source_consensus)
            throw std::invalid_argument("Parent route requires Kunlun city and source consensus");
        kunlun_parent_.emplace(town.kunlun_parent_navigation);
    }
    if(!town.fruit_navigation.empty()) fruit_=std::make_shared<RecoveredFruitNavigation>(town.fruit_navigation);
    if(!town.birthplace_navigation.empty()) {
        kunlun_.emplace(town.birthplace_navigation);
        if(!cell_available(4,3,town.birthplace_x,town.birthplace_y))throw std::invalid_argument("Kunlun birthplace cell unavailable");
        initial_area_=4;scene_=3;kind_=0;initial_x_=town.birthplace_x;initial_y_=town.birthplace_y;
    }
    if(!town.cross_map_navigation.empty()) {
        if(!town.source_consensus || !island_full_)
            throw std::invalid_argument("Cross-map bundle requires full qualified parent navigation");
        cross_maps_.emplace(town.cross_map_navigation);
        // Validate both ends against the actual loaded authorities. A pinned
        // scene alone cannot create an edge into missing/blocked parent cells.
        for(const auto& route:cross_maps_->routes())
            if(!cell_available(route.area,route.source_scene,route.source_x,route.source_y) ||
               !cell_available(route.area,route.target_scene,route.target_x,route.target_y))
                throw std::invalid_argument("Cross-map endpoint navigation unavailable");
    }
    if(!town.world_transfer_catalog.empty()) {
        world_catalog_.emplace(town.world_transfer_catalog);
        if(!cell_available(initial_area_,scene_,initial_x_,initial_y_))
            throw std::invalid_argument("Initial saved-world placement is outside the qualified catalog");
        kind_=scene_kind(initial_area_,scene_);
    }
}
bool RecoveredMovementService::cell_available(int x,int y) const noexcept {
    return cell_available(initial_area_,scene_,x,y);
}
bool RecoveredMovementService::cell_available(std::uint16_t area,std::uint16_t scene,int x,int y) const noexcept {
    if(world_catalog_)return x>=0&&y>=0&&x<=0xffff&&y<=0xffff&&world_catalog_->available(
        {{area,scene},static_cast<std::uint16_t>(x),static_cast<std::uint16_t>(y)});
    if(cross_maps_ && cross_maps_->kind(area,scene)) {
        const auto value=cross_maps_->cell(area,scene,x,y);
        // CUSTOM-0154: only original Cave02 record47's exact trigger has
        // unanimous nonzero 01/02 observations across its nine windows.
        // Native502BF0/502F20 accept either for traversal; 5035B0's separate
        // compare2 branch is not generalized. Every other conflict still fails.
        if(!value && area==2 && scene==2 && x==60 && y==77)
            return cross_maps_->consistently_walkable(area,scene,x,y);
        return value && *value!=0;
    }
    if(area==4 && scene==0 && kunlun_parent_) {
        const auto value=kunlun_parent_->consistent_cell(x,y);
        return value && *value!=0;
    }
    if(area==4 && scene==3 && kunlun_) {
        const auto value=kunlun_->consistent_cell(x,y);
        // CUSTOM-0052 narrow native46FF0/102BF0 nonzero traversal policy.
        // Only current konfu/hofu original trigger points have this 1/2 overlap.
        if(!value && ((kunlun_indoor_scenes_.contains(4) && y==97 && (x==185 || x==186)) ||
          (kunlun_indoor_scenes_.contains(9) && x==185 && (y==152 || y==153))))
            return kunlun_->consistently_walkable(x,y);
        return value && *value!=0;
    }
    if(area==13 && scene==12 && fruit_) return fruit_->consistent_cell(x,y)!=0;
    if(area==4) {
        const auto room=kunlun_indoor_scenes_.find(scene);
        return room!=kunlun_indoor_scenes_.end() && room->second.cell(x,y)!=0;
    }
    return area==2 && cell_available(scene,x,y);
}
bool RecoveredMovementService::cell_available(std::uint16_t scene,int x,int y) const noexcept {
    if(scene==4 && town_) {
        const auto value=town_source_consensus_?town_->consistent_cell(x,y):town_->cell(center_.x,center_.y,x,y);
        // CUSTOM-0052: this one original source point has byte observations1/2
        // but unanimous native nonzero traversal. Original41350 selects3,2 for
        // its one-step approach; original46FF0+102BF0 accepts both bytes.
        // Scope remains one registered doorway; all other conflicts still fail.
        if(!value && town_source_consensus_ && indoor_scenes_.contains(7) && x==82 && y==46)
            return town_->consistently_walkable(x,y);
        return value && *value!=0;
    }
    if(scene==0 && (island_ || island_full_)) {
        const auto value=island_full_?island_full_->consistent_cell(x,y):island_->consistent_cell(x,y);
        // The paired parent trigger is enabled only with the whole pinned
        // Cave02 bundle. No blanket conversion of 01/02 conflicts to walkable.
        if(!value && island_full_ && cross_maps_ && cross_maps_->kind(2,2) && x==394 && y==96)
            return island_full_->consistently_walkable(x,y);
        return value && *value!=0;
    }
    const auto room=indoor_scenes_.find(scene);
    if(room!=indoor_scenes_.end())return room->second.cell(x,y)!=0;
    return scene==15 && grid_ && grid_->cell(x,y)!=0;
}
bool RecoveredMovementService::qualifies_transfer_destination(
    std::uint16_t scene,std::uint16_t x,std::uint16_t y) const noexcept {
    return town_ && town_source_consensus_ && x<0x4000 && y<=0x7fff &&
        cell_available(scene,x,y);
}
RecoveredWorldEntry::Frame RecoveredMovementService::prepare(std::uint64_t session,std::uint64_t account,std::uint64_t character) {
    reject_owned_movement_mutation();
    if(!session || !account || !character || active_.contains(session))
        throw std::invalid_argument("Movement binding rejected");
    for(const auto& [id,position]:active_) {
        (void)id;
        if(position.character==character) throw std::invalid_argument("Recovered character already online");
    }
    for(const auto& owned:characters_.list_for_account(account)) {
        if(owned.id==character && RecoveredCharacterListCandidate::valid_profile(owned.profile)) {
            Position position{account,character};
            position.x=initial_x_;position.y=initial_y_;
            position.scene=scene_;position.kind=kind_;
            position.area=initial_area_;
            position.saved=characters_.load_position(account,character);
            if(position.saved) {
                const auto& saved=*position.saved;
                if(!cell_available(saved.area,saved.scene,saved.x,saved.y))
                    throw std::invalid_argument("Saved movement scene or cell unavailable");
                position.x=saved.x;position.y=saved.y;
                position.scene=saved.scene;position.kind=scene_kind(saved.area,saved.scene);
                position.area=saved.area;
            }
            const auto frame=RecoveredWorldEntry::wire(character,owned.profile,
                static_cast<std::uint16_t>(position.x),static_cast<std::uint16_t>(position.y),position.area,position.scene,position.kind);
            active_.emplace(session,position);
            return frame;
        }
    }
    throw std::invalid_argument("Movement character ownership rejected");
}
void RecoveredMovementService::prepare_native(std::uint64_t session,std::uint64_t account,std::uint64_t character,
                                             const RecoveredWorldEntry::Frame& frame) {
    reject_owned_movement_mutation();
    if(!session || !account || !character || active_.contains(session))
        throw std::invalid_argument("Native movement binding rejected");
    for(const auto& [id,position]:active_) {
        (void)id;
        if(position.character==character)throw std::invalid_argument("Native movement character already online");
    }
    const auto full=RecoveredWorldEntryView::read(frame);
    if(!full || full->actor_handle!=character)
        throw std::invalid_argument("Native movement full entry identity rejected");
    const auto owned=characters_.list_for_account(account);
    if(std::none_of(owned.begin(),owned.end(),[&](const auto& row){return row.id==character && row.account_id==account;}))
        throw std::invalid_argument("Native movement character ownership rejected");
    const auto saved=characters_.load_position(account,character);
    if(!saved || !saved->revision || saved->area!=full->area || saved->scene!=full->scene ||
       saved->x!=full->x || saved->y!=full->y ||
       ((world_catalog_ || registered_cross_map_scene(full->area,full->scene)) && qualified_scene_kind(full->area,full->scene)!=full->kind) ||
       !cell_available(full->area,full->scene,full->x,full->y))
        throw std::invalid_argument("Native movement actual saved geometry unavailable or mismatched");
    // slot/ready/transfer are the existing operational start state, not native
    // placement fields. All geometry/kind/identity fields are explicitly actual.
    Position position{account,character,static_cast<int>(full->x),static_cast<int>(full->y),
        0,false,false,full->scene,full->kind,full->area,*saved};
    if(characters_.load_position(account,character)!=saved)
        throw std::invalid_argument("Native movement saved baseline changed during preparation");
    if(!active_.emplace(session,std::move(position)).second)
        throw std::invalid_argument("Native movement Session already prepared");
}
void RecoveredMovementService::prepare_native_scene(std::uint64_t session,std::uint64_t account,std::uint64_t character,
                                                   const RecoveredWorldEntry::Frame& frame) {
    reject_owned_movement_mutation();
    if(!session || !account || !character || active_.contains(session))
        throw std::invalid_argument("Native scene movement binding rejected");
    for(const auto& [id,position]:active_) {
        (void)id;
        if(position.character==character)throw std::invalid_argument("Native scene movement character already online");
    }
    const auto full=RecoveredWorldEntryView::read(frame);
    if(!full || !qualified_taiwan_scene_handle(full->actor_handle))
        throw std::invalid_argument("Native scene movement full entry handle rejected");
    const auto owned=characters_.list_for_account(account);
    if(std::none_of(owned.begin(),owned.end(),[&](const auto& row){return row.id==character && row.account_id==account;}))
        throw std::invalid_argument("Native scene movement character ownership rejected");
    const auto saved=characters_.load_position(account,character);
    if(!saved || !saved->revision || saved->area!=full->area || saved->scene!=full->scene ||
       saved->x!=full->x || saved->y!=full->y ||
       ((world_catalog_ || registered_cross_map_scene(full->area,full->scene)) && qualified_scene_kind(full->area,full->scene)!=full->kind) ||
       !cell_available(full->area,full->scene,full->x,full->y))
        throw std::invalid_argument("Native scene movement actual saved geometry unavailable or mismatched");
    Position position{account,character,static_cast<int>(full->x),static_cast<int>(full->y),
        0,false,false,full->scene,full->kind,full->area,*saved};
    if(characters_.load_position(account,character)!=saved)
        throw std::invalid_argument("Native scene movement saved baseline changed during preparation");
    if(!active_.emplace(session,std::move(position)).second)
        throw std::invalid_argument("Native scene movement Session already prepared");
}
void RecoveredMovementService::bind(std::uint64_t session,std::uint64_t account,std::uint64_t character) {
    reject_owned_movement_mutation();
    const auto it=active_.find(session);
    if(it==active_.end() || it->second.account!=account || it->second.character!=character || it->second.ready)
        throw std::invalid_argument("Movement world-ready binding rejected");
    // Selection reserved this exact snapshot; external writes must not silently
    // move authority away from the coordinates already sent to the client.
    if(characters_.load_position(account,character)!=it->second.saved)
        throw std::invalid_argument("Saved position changed during world entry");
    it->second.ready=true;
}
std::optional<std::uint16_t> RecoveredMovementService::scene(
    std::uint64_t session,std::uint64_t account,std::uint64_t character) const noexcept {
    const auto it=active_.find(session);
    if(it==active_.end() || !it->second.ready || it->second.transfer_pending ||
       it->second.account!=account || it->second.character!=character)
        return std::nullopt;
    return it->second.scene;
}
std::optional<RecoveredPosition> RecoveredMovementService::current_world_location(
    std::uint64_t session,std::uint64_t account,std::uint64_t character) const {
    if(owned_movement_thread_!=std::this_thread::get_id())
        throw std::logic_error("Guild world snapshot requires its GAME owner");
    if(!session||!account||!character||owned_movement_busy_||owned_movement_invalid_)return {};
    const auto at=active_.find(session);
    if(at==active_.end()||!at->second.ready||at->second.transfer_pending||
       at->second.account!=account||at->second.character!=character)return {};
    const auto& value=at->second;
    if(value.saved&&(!value.saved->revision||value.saved->area!=value.area||value.saved->scene!=value.scene||
       value.saved->x!=value.x||value.saved->y!=value.y))return {};
    return RecoveredPosition{value.area,value.scene,static_cast<std::uint16_t>(value.x),
        static_cast<std::uint16_t>(value.y),value.saved?value.saved->revision:0};
}
std::optional<RecoveredPosition> RecoveredMovementService::current_location(
    std::uint64_t session,std::uint64_t account,std::uint64_t character) const {
    // A read can call an observer too. Apply the same fence as the owned
    // movement transaction, while allowing its existing nested read-only use.
    const bool owns_fence=!owned_movement_busy_;
    if(owns_fence){owned_movement_busy_=true;owned_movement_invalid_=false;}
    struct End {const RecoveredMovementService& self;bool owns;
        ~End(){if(owns)self.owned_movement_busy_=self.owned_movement_invalid_=false;}} end{*this,owns_fence};
    const auto snapshot=[&]()->std::optional<Position> {
        const auto found=active_.find(session);
        if(found==active_.end())return std::nullopt;
        return found->second;
    }();
    if(owned_movement_invalid_ || !snapshot || !snapshot->ready || snapshot->transfer_pending ||
       snapshot->account!=account || snapshot->character!=character)return std::nullopt;
    const auto saved=characters_.load_position(account,character);
    const auto now=active_.find(session);
    if(owned_movement_invalid_ || now==active_.end() || now->second!=*snapshot || saved!=snapshot->saved)
        return std::nullopt;
    return RecoveredPosition{snapshot->area,snapshot->scene,
        static_cast<std::uint16_t>(snapshot->x),static_cast<std::uint16_t>(snapshot->y),
        snapshot->saved?snapshot->saved->revision:0};
}
std::vector<std::uint8_t> RecoveredMovementService::move(std::uint64_t session,std::uint64_t account,
    std::uint64_t character,std::span<const RecoveredMovement::Request> requests) {
    return move_committed(session,account,character,requests).reply;
}
void RecoveredMovementService::resume_after_battle(std::uint64_t session,std::uint64_t account,std::uint64_t character) {
    reject_owned_movement_mutation();
    owned_movement_busy_=true;owned_movement_invalid_=false;
    struct End {RecoveredMovementService& self;~End(){self.owned_movement_busy_=self.owned_movement_invalid_=false;}} end{*this};
    const auto it=active_.find(session);
    if(it==active_.end() || !it->second.ready || it->second.transfer_pending || it->second.account!=account ||
       it->second.character!=character)
        throw std::invalid_argument("Battle return movement baseline mismatch");
    // A repository callback may remove this connection. Never retain its node
    // across SQL; the mutation fence also rejects remove/reprepare with equal
    // values, which a value comparison alone cannot distinguish.
    const auto before=it->second;
    const auto saved=characters_.load_position(account,character);
    const auto now=active_.find(session);
    if(owned_movement_invalid_ || now==active_.end() || now->second!=before || saved!=before.saved)
        throw std::invalid_argument("Battle return movement baseline mismatch");
    // Native world return resets the connection ring, not the saved coordinates.
    now->second.slot=0;
}
std::vector<std::uint8_t> RecoveredMovementService::begin_town_transfer(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y) {
    reject_owned_movement_mutation();
    return begin_transfer(session,account,character,expected,4,4,x,y);
}
std::vector<std::uint8_t> RecoveredMovementService::begin_indoor_transfer(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y) {
    reject_owned_movement_mutation();
    return begin_transfer(session,account,character,expected,4,15,x,y);
}
std::vector<std::uint8_t> RecoveredMovementService::begin_initial_indoor_transfer(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,std::uint16_t x,std::uint16_t y) {
    reject_owned_movement_mutation();
    const auto it=active_.find(session);
    if(it==active_.end() || it->second.saved || it->second.scene!=4 ||
       it->second.x!=initial_x_ || it->second.y!=initial_y_)
        throw std::invalid_argument("Initial indoor transfer requires unsaved town spawn");
    return begin_transfer(session,account,character,std::nullopt,4,15,x,y);
}
std::vector<std::uint8_t> RecoveredMovementService::begin_outdoor_return(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y) {
    reject_owned_movement_mutation();
    return begin_transfer(session,account,character,expected,15,4,x,y);
}
std::vector<std::uint8_t> RecoveredMovementService::begin_island_transfer(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y) {
    reject_owned_movement_mutation();
    return begin_transfer(session,account,character,expected,4,0,x,y);
}
std::vector<std::uint8_t> RecoveredMovementService::begin_island_return(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y) {
    reject_owned_movement_mutation();
    return begin_transfer(session,account,character,expected,0,4,x,y);
}
std::vector<std::uint8_t> RecoveredMovementService::begin_registered_wilderness_transfer(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y) {
    reject_owned_movement_mutation();
    const auto it=active_.find(session);
    // CUSTOM-0153: immutable, source-qualified same-MDL endpoint pairs only.
    // Recheck the committed movement endpoint here; Lua proposal admission is
    // insufficient to authorize another source point or arbitrary destination.
    if(!town_ || !town_source_consensus_ || it==active_.end() || !it->second.ready ||
       it->second.transfer_pending || it->second.account!=account || it->second.character!=character ||
       (expected.area!=2 && expected.area!=4) || expected.scene!=0 ||
       it->second.area!=expected.area || it->second.scene!=0 ||
       it->second.x!=expected.x || it->second.y!=expected.y ||
       it->second.saved!=std::optional{expected} || !expected.revision ||
       expected.revision>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()) ||
       !qualified_wilderness_transfer(expected.area,expected.scene,expected.x,expected.y,x,y) ||
       !qualifies_transfer_destination(expected.area,0,expected.x,expected.y) ||
       !qualifies_transfer_destination(expected.area,0,x,y) ||
       characters_.load_position(account,character)!=std::optional{expected})
        throw std::invalid_argument("Unqualified registered wilderness endpoint or baseline");
    // CUSTOM-0153: moving kind1 parent transfers need the original full reset
    // to clear the old path/motion and rebuild the destination window. The
    // qualified short-range kind0 reuse path does not prove kind1 reuse safe.
    // Preserve the existing revision/pending/ACK-first flow, but omit bit16.
    return begin_transfer(session,account,character,expected,0,0,x,y,expected.area,false);
}
bool RecoveredMovementService::registered_cross_map_scene(std::uint16_t area,std::uint16_t scene) const noexcept {
    return cross_maps_ && cross_maps_->kind(area,scene).has_value();
}
bool RecoveredMovementService::qualified_cross_map_transfer(std::uint16_t area,std::uint16_t source_scene,
    std::uint16_t source_x,std::uint16_t source_y,std::uint16_t target_scene,
    std::uint16_t target_x,std::uint16_t target_y) const noexcept {
    return cross_maps_ && cross_maps_->contains({area,source_scene,source_x,source_y,target_scene,target_x,target_y});
}
std::vector<std::uint8_t> RecoveredMovementService::begin_registered_cross_map_transfer(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    const RecoveredPosition& expected,std::uint16_t scene,std::uint16_t x,std::uint16_t y) {
    reject_owned_movement_mutation();
    const auto it=active_.find(session);
    if(!town_ || !town_source_consensus_ || it==active_.end() || !it->second.ready ||
       it->second.transfer_pending || it->second.account!=account || it->second.character!=character ||
       it->second.area!=expected.area || it->second.scene!=expected.scene ||
       it->second.x!=expected.x || it->second.y!=expected.y ||
       it->second.saved!=std::optional{expected} || !expected.revision ||
       expected.revision>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()) ||
       !qualified_cross_map_transfer(expected.area,expected.scene,expected.x,expected.y,scene,x,y) ||
       !qualifies_transfer_destination(expected.area,expected.scene,expected.x,expected.y) ||
       !qualifies_transfer_destination(expected.area,scene,x,y) ||
       characters_.load_position(account,character)!=std::optional{expected})
        throw std::invalid_argument("Unqualified registered cross-map endpoint or baseline");
    return begin_transfer(session,account,character,expected,expected.scene,scene,x,y,expected.area,false);
}
std::vector<std::uint8_t> RecoveredMovementService::begin_world_transfer(std::uint64_t session,
    std::uint64_t account,std::uint64_t character,const RecoveredPosition& expected,std::string_view route_id) {
    reject_owned_movement_mutation();
    const auto it=active_.find(session);const auto* route=world_catalog_?world_catalog_->route(route_id):nullptr;
    if(!route || route->trigger==WorldTransferCatalog::Trigger::NpcOffer || it==active_.end() ||
       !it->second.last_step || !it->second.last_step->displaced_steps || !expected.revision ||
       expected.revision>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()) ||
       expected.area!=route->source.scene.area || expected.scene!=route->source.scene.scene ||
       expected.x!=route->source.x || expected.y!=route->source.y ||
       it->second.x!=expected.x || it->second.y!=expected.y ||
       !qualifies_transfer_destination(expected.area,expected.scene,expected.x,expected.y) ||
       characters_.load_position(account,character)!=std::optional{expected})
        throw std::invalid_argument("Unqualified world route or movement witness");
    const auto& step=*it->second.last_step;
    const auto* witnessed=world_catalog_->route_for_step({step.area,step.scene},step.before_x,step.before_y,step.x,step.y);
    if(!witnessed || witnessed->id!=route_id || step.area!=expected.area || step.scene!=expected.scene ||
       step.x!=expected.x || step.y!=expected.y)
        throw std::invalid_argument("World route approach witness mismatch");
    return begin_transfer(session,account,character,expected,expected.scene,route->destination.scene.scene,
        route->destination.x,route->destination.y,expected.area,false,route->destination.scene.area);
}
std::vector<std::uint8_t> RecoveredMovementService::begin_npc_world_transfer(OwnedNpcTeleportOffer& offers,
    const OwnedNpcTeleportOffer::Identity& owner,const OwnedNpcTeleportOffer::Prepared& prepared) {
    reject_owned_movement_mutation();
    const auto& expected=prepared.expected_position;
    const auto it=active_.find(owner.session);const auto* route=world_catalog_?world_catalog_->route(prepared.route_id):nullptr;
    if(!route || route->trigger!=WorldTransferCatalog::Trigger::NpcOffer || it==active_.end() ||
       !it->second.ready || it->second.transfer_pending || it->second.account!=owner.account ||
       it->second.character!=owner.character || !expected.revision ||
       expected.revision>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()) ||
       route->source.scene!=WorldTransferCatalog::SceneKey{expected.area,expected.scene} ||
       route->source.scene!=WorldTransferCatalog::SceneKey{prepared.issuer.area,prepared.issuer.scene} ||
       route->source.x!=prepared.issuer.x || route->source.y!=prepared.issuer.y ||
       prepared.issuer.generation!=prepared.npc_generation ||
       it->second.saved!=std::optional{expected} || it->second.area!=expected.area || it->second.scene!=expected.scene ||
       it->second.x!=expected.x || it->second.y!=expected.y)
        throw std::invalid_argument("NPC transfer lacks an exact owned world-catalog route");
    // The issuer reobserves actual NPC publication, world/policy generations
    // and the exact privately retained Prepared value immediately before CAS.
    const auto proof=offers.revalidate(owner,prepared);
    if(!proof)throw std::invalid_argument("NPC transfer issued proof is no longer current");
    if(*proof.value!=OwnedNpcTeleportOffer::CostPolicy::ExplicitNoCost)
        throw std::invalid_argument("NPC joint resource and position transaction supplier unavailable");
    if(characters_.load_position(owner.account,owner.character)!=std::optional{expected})
        throw std::invalid_argument("NPC transfer saved baseline changed during source observation");
    return begin_transfer(owner.session,owner.account,owner.character,expected,expected.scene,
        route->destination.scene.scene,route->destination.x,route->destination.y,expected.area,false,route->destination.scene.area);
}
RecoveredMovementService::OwnedIslandReturnPlan RecoveredMovementService::prepare_owned_island_return(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    const RecoveredPosition& expected) const {
    const auto found=active_.find(session);
    // This landing is the existing source-qualified parent return, not a new
    // arbitrary spawn or a generic authorization for another map.
    if(!town_ || !town_source_consensus_ || found==active_.end() || !found->second.ready ||
       found->second.transfer_pending || found->second.account!=account || found->second.character!=character ||
       found->second.saved!=std::optional{expected} || expected.area!=2 || expected.scene!=0 ||
       found->second.area!=2 || found->second.scene!=0 || found->second.x!=expected.x || found->second.y!=expected.y ||
       !expected.revision || expected.revision>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()) ||
       !qualifies_transfer_destination(2,4,56,75))
        throw std::invalid_argument("Owned teleport gem return lacks qualified source/landing");
    OwnedIslandReturnPlan plan{session,account,character,expected,{2,4,56,75,expected.revision+1},
        {0x61,2,1,0,0,0,0,0,0}};
    const auto packed=(std::uint32_t{56}<<2)|(std::uint32_t{75}<<17)|scene_kind(2,4);
    for(unsigned i=0;i<4;++i)plan.logical[5+i]=static_cast<std::uint8_t>(packed>>(8*i));
    return plan;
}
void RecoveredMovementService::commit_owned_island_return(
    const OwnedIslandReturnPlan& plan,const RecoveredPosition& persisted) noexcept {
    if(owned_movement_busy_){owned_movement_invalid_=true;return;}
    const auto found=active_.find(plan.session);
    if(found==active_.end() || !found->second.ready || found->second.transfer_pending ||
       found->second.account!=plan.account || found->second.character!=plan.character ||
       found->second.saved!=std::optional{plan.before} || persisted!=plan.after ||
       plan.before.area!=2 || plan.before.scene!=0 || plan.after.area!=2 || plan.after.scene!=4 ||
       plan.after.x!=56 || plan.after.y!=75 || plan.after.revision!=plan.before.revision+1)
        std::terminate();
    auto& next=found->second;
    next.saved=persisted;next.area=2;next.scene=4;next.kind=0;next.x=56;next.y=75;
    next.transfer_pending=true;
}
std::vector<std::uint8_t> RecoveredMovementService::begin_transfer(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    const std::optional<RecoveredPosition>& expected,std::uint16_t source_scene,std::uint16_t scene,std::uint16_t x,std::uint16_t y,std::uint16_t area,
    bool reuse_same_scene,std::uint16_t destination_area) {
    reject_owned_movement_mutation();
    if(!destination_area)destination_area=area;
    const auto it=active_.find(session);
    if(!town_ || !town_source_consensus_ || it==active_.end() || !it->second.ready ||
       it->second.transfer_pending || it->second.account!=account || it->second.character!=character ||
       it->second.saved!=expected || (expected && (expected->area!=area || expected->scene!=source_scene)) ||
       it->second.area!=area || it->second.scene!=source_scene || !qualifies_transfer_destination(destination_area,scene,x,y))
        throw std::invalid_argument("Unqualified town transfer");
    std::array<std::uint8_t,9> logical{0x61,2,1,0,0,0,0,0,0};
    const auto selector=static_cast<std::uint16_t>(destination_area|(scene<<6));
    logical[1]=static_cast<std::uint8_t>(selector);logical[2]=static_cast<std::uint8_t>(selector>>8);
    const auto packed=(std::uint32_t{x}<<2)|(std::uint32_t{y}<<17)|
        scene_kind(destination_area,scene)|
        (area==destination_area && source_scene==scene && reuse_same_scene?0x10000u:0u);
    for(unsigned i=0;i<4;++i) logical[5+i]=static_cast<std::uint8_t>(packed>>(8*i));
    auto reply=RecoveredWorldFrame::encode(logical);
    auto next=it->second;
    next.saved=characters_.commit_position(account,character,expected,destination_area,scene,x,y);
    next.area=destination_area;next.scene=scene;next.kind=scene_kind(destination_area,scene);
    next.x=x; next.y=y; next.transfer_pending=true;
    next.last_step.reset();
    it->second=next;
    return reply;
}
bool RecoveredMovementService::qualifies_transfer_destination(
    std::uint16_t area,std::uint16_t scene,std::uint16_t x,std::uint16_t y) const noexcept {
    return town_ && town_source_consensus_ && x<0x4000 && y<=0x7fff && cell_available(area,scene,x,y);
}
bool RecoveredMovementService::registered_door_pair(std::uint16_t source_scene,std::uint16_t destination_scene) const noexcept {
    return registered_door_pair(2,source_scene,destination_scene);
}
bool RecoveredMovementService::registered_door_pair(std::uint16_t area,std::uint16_t source_scene,std::uint16_t destination_scene) const noexcept {
    if(area==4)return kunlun_ && ((source_scene==3 && kunlun_indoor_scenes_.contains(destination_scene)) ||
           (destination_scene==3 && kunlun_indoor_scenes_.contains(source_scene)));
    if(area!=2)return false;
    return (source_scene==4 && indoor_scenes_.contains(destination_scene)) ||
           (destination_scene==4 && indoor_scenes_.contains(source_scene));
}
std::vector<std::uint8_t> RecoveredMovementService::begin_registered_door_transfer(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    const RecoveredPosition& expected,std::uint16_t scene,std::uint16_t x,std::uint16_t y) {
    reject_owned_movement_mutation();
    if(!registered_door_pair(expected.area,expected.scene,scene))
        throw std::invalid_argument("Unregistered current doorway pair");
    return begin_transfer(session,account,character,expected,expected.scene,scene,x,y,expected.area);
}
std::uint16_t RecoveredMovementService::scene_kind(std::uint16_t area,std::uint16_t scene) const {
    if(const auto kind=qualified_scene_kind(area,scene))return *kind;
    throw std::invalid_argument("Unregistered source scene kind");
}
std::optional<std::uint16_t> RecoveredMovementService::qualified_scene_kind(std::uint16_t area,std::uint16_t scene) const noexcept {
    if(world_catalog_){const auto* row=world_catalog_->scene({area,scene});return row?std::optional{row->kind}:std::nullopt;}
    // Explicit source-qualified kind registry; scene numbers alias across areas.
    if(cross_maps_)if(const auto kind=cross_maps_->kind(area,scene))return kind;
    if(area==4 && scene==3 && kunlun_)return 0;
    if(area==4 && scene==0 && kunlun_parent_)return 1;
    if(area==4 && kunlun_indoor_scenes_.contains(scene))return 2;
    if(area==13 && scene==12 && fruit_)return 0;
    if(area==2 && scene==4 && town_)return 0;
    if(area==2 && scene==0 && (island_ || island_full_))return 1;
    if(area==2 && (indoor_scenes_.contains(scene) || (scene==15 && grid_)))return 2;
    return std::nullopt;
}
bool RecoveredMovementService::registered_parent_pair(std::uint16_t area,std::uint16_t source_scene,std::uint16_t destination_scene) const noexcept {
    return area==4 && kunlun_ && kunlun_parent_ &&
        ((source_scene==3 && destination_scene==0)||(source_scene==0 && destination_scene==3));
}
std::vector<std::uint8_t> RecoveredMovementService::begin_registered_parent_transfer(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    const RecoveredPosition& expected,std::uint16_t scene,std::uint16_t x,std::uint16_t y) {
    reject_owned_movement_mutation();
    // CUSTOM-0053: exact native mutual placement anchors, custom point2/point0
    // trigger/arrival choice. The server cannot admit an arbitrary Lua landing.
    const bool outward=expected.scene==3 && expected.x==50 && expected.y==124 && scene==0 && x==318 && y==363;
    const bool inward=expected.scene==0 && expected.x==318 && expected.y==363 && scene==3 && x==50 && y==124;
    if(!registered_parent_pair(expected.area,expected.scene,scene) || (!outward && !inward))
        throw std::invalid_argument("Unqualified current parent edge or point");
    return begin_transfer(session,account,character,expected,expected.scene,scene,x,y,expected.area);
}
void RecoveredMovementService::finish_town_transfer(
    std::uint64_t session,std::uint64_t account,std::uint64_t character) {
    reject_owned_movement_mutation();
    const auto it=active_.find(session);
    if(it==active_.end() || !it->second.ready || !it->second.transfer_pending ||
       it->second.account!=account || it->second.character!=character ||
       characters_.load_position(account,character)!=it->second.saved)
        throw std::invalid_argument("Town transfer receipt baseline mismatch");
    // Original6C414 resets the ring then queues the destination as slot0.
    it->second.slot=0;
    it->second.transfer_pending=false;
}
void RecoveredMovementService::reject_owned_movement_mutation() const {
    if(owned_movement_busy_) {
        owned_movement_invalid_=true;
        throw std::logic_error("Owned normal-entry movement reentered by a mutation");
    }
}
RecoveredMovementService::PreparedMove RecoveredMovementService::prepare_move_batch(
    const Position& position,std::span<const RecoveredMovement::Request> requests,
    const std::function<bool(const MovePreview&)>& stop_after_step) const {
    auto next=position;
    std::size_t displaced_steps=0;
    std::vector<std::uint8_t> response;
    std::vector<CommittedMove::Step> path;
    path.reserve(requests.size());
    for(const auto& request:requests) {
        const auto before_x=static_cast<std::uint16_t>(next.x),before_y=static_cast<std::uint16_t>(next.y);
        const auto expected=static_cast<std::uint8_t>((next.slot+1)%40);
        // Keep the original short-circuit check order; construct diagnostic
        // details only on rejection, without adding authority or relaxing a step.
        if(request.sequence!=expected)
            throw std::invalid_argument("Movement queue, step or navigation rejected reason=sequence expected="+
                std::to_string(expected)+" request="+std::to_string(request.sequence)+
                " from="+std::to_string(next.x)+","+std::to_string(next.y)+
                " target="+std::to_string(request.x)+","+std::to_string(request.y));
        if(std::abs(static_cast<int>(request.x)-next.x)>1 || std::abs(static_cast<int>(request.y)-next.y)>1)
            throw std::invalid_argument("Movement queue, step or navigation rejected reason=step from="+
                std::to_string(next.x)+","+std::to_string(next.y)+
                " target="+std::to_string(request.x)+","+std::to_string(request.y));
        if(!cell_available(next.area,next.scene,request.x,request.y))
            throw std::invalid_argument("Movement queue, step or navigation rejected reason=navigation area="+
                std::to_string(next.area)+" scene="+std::to_string(next.scene)+
                " target="+std::to_string(request.x)+","+std::to_string(request.y));
        const auto ack=RecoveredMovement::ack(request.sequence);
        response.insert(response.end(),ack.begin(),ack.end());
        const bool displaced=next.x!=request.x || next.y!=request.y;
        if(displaced) {
            ++displaced_steps;
            path.push_back({request.x,request.y});
        }
        next.x=request.x;next.y=request.y;next.slot=request.sequence;
        next.last_step=MovePreview{next.area,next.scene,before_x,before_y,request.x,request.y,displaced?1u:0u};
        // CUSTOM-0153: stop at the first admitted portal after its own validated
        // step. Old-scene tail requests must not advance queue, ACK or position.
        if(stop_after_step && stop_after_step(MovePreview{next.area,next.scene,
            before_x,before_y,request.x,request.y,displaced?1u:0u}))break;
    }
    return {std::move(next),std::move(response),std::move(path),displaced_steps};
}
RecoveredMovementService::CommittedMove RecoveredMovementService::move_committed(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    std::span<const RecoveredMovement::Request> requests,
    const std::function<void(const MovePreview&)>& precommit,
    const std::function<bool(const MovePreview&)>& stop_after_step) {
    reject_owned_movement_mutation();
    auto it=active_.find(session);
    if(it==active_.end() || !it->second.ready || it->second.transfer_pending || it->second.account!=account || it->second.character!=character || requests.empty())
        throw std::invalid_argument("Unbound movement rejected");
    auto prepared=prepare_move_batch(it->second,requests,stop_after_step);
    auto& next=prepared.next;
    const auto before=next.saved;
    auto& response=prepared.response;
    auto& path=prepared.path;
    const auto displaced_steps=prepared.displaced_steps;
    // Validate the selected whole batch/prefix, then commit before publishing
    // state or ACKs. Default callers retain their complete legacy batch recipe.
    if(precommit) precommit(MovePreview{next.area,next.scene,
        static_cast<std::uint16_t>(it->second.x),static_cast<std::uint16_t>(it->second.y),
        static_cast<std::uint16_t>(next.x),static_cast<std::uint16_t>(next.y),displaced_steps});
    next.saved=characters_.commit_position(account,character,it->second.saved,next.area,next.scene,
        static_cast<std::uint16_t>(next.x),static_cast<std::uint16_t>(next.y));
    it->second=next;
    return {std::move(response),before,*next.saved,displaced_steps,std::move(path)};
}
RecoveredMovementService::CommittedMove RecoveredMovementService::move_committed_with_owned_material(
    Session& session,SqliteOwnedEquipmentTransaction& custody,
    std::span<const RecoveredMovement::Request> requests) {
    return std::move(move_committed_with_owned_material_and_receipt(session,custody,requests)).take_movement();
}
RecoveredMovementService::OwnedCommittedMove RecoveredMovementService::move_committed_with_owned_material_and_receipt(
    Session& session,SqliteOwnedEquipmentTransaction& custody,
    std::span<const RecoveredMovement::Request> requests) {
    if(owned_movement_thread_!=std::this_thread::get_id())
        throw std::logic_error("Owned normal-entry movement requires its game owner");
    reject_owned_movement_mutation();
    owned_movement_busy_=true;owned_movement_invalid_=false;
    struct End {RecoveredMovementService& self;~End(){self.owned_movement_busy_=self.owned_movement_invalid_=false;}} end{*this};
    if(&custody.characters_repository()!=&characters_)
        throw std::invalid_argument("Owned movement requires the exact common character repository");
    const auto connection=session.shared_from_this();
    const auto initialization=session.normal_world_initialization();
    if(!initialization || !initialization->entry_written() ||
       !session.normal_world_initialization_current_on_game(*initialization))
        throw std::invalid_argument("Owned movement requires actual current normal initialization");
    const auto id=session.id(),account=session.account_id,character=session.character_id;
    const auto phase=session.state();const auto battle=session.battle_generation();
    if(!id || !account || !character || requests.empty() ||
       (phase!=SessionState::CharacterSelected && phase!=SessionState::InWorld))
        throw std::invalid_argument("Owned movement normal owner/batch rejected");
    const auto local=[&] {
        return owned_movement_busy_ && !owned_movement_invalid_ && connection.get()==&session &&
            session.normal_world_initialization_current_on_game(*initialization) && initialization->entry_written() &&
            !session.closing() && session.recovered_world_ready() && session.id()==id &&
            session.account_id==account && session.character_id==character &&
            session.state()==phase && session.battle_generation()==battle;
    };
    const auto old=[&] {
        const auto found=active_.find(id);
        if(found==active_.end() || !found->second.ready || found->second.transfer_pending ||
           found->second.account!=account || found->second.character!=character)
            throw std::invalid_argument("Unbound owned movement rejected");
        return found->second;
    }();
    // Pure in-memory owner check, including exact queue/geometry/saved state.
    // No iterator is retained across a repository or Session observation.
    const auto active_current=[&](const Position& wanted) {
        if(!local())return false;
        const auto found=active_.find(id);
        return found!=active_.end() && found->second==wanted && local();
    };
    if(!old.saved || !old.saved->revision || old.area!=old.saved->area || old.scene!=old.saved->scene ||
       old.x!=old.saved->x || old.y!=old.saved->y || !active_current(old))
        throw std::invalid_argument("Owned movement lacks exact positive saved active pose");
    const auto pose_current=[&](const Position& wanted) {
        return active_current(wanted) && current_location(id,account,character)==wanted.saved && active_current(wanted);
    };
    const auto entry=RecoveredWorldEntryView::read(initialization->entry_frame());
    if(!entry || !pose_current(old))throw std::invalid_argument("Owned movement entry/current pose rejected");
    const auto before=custody.observe_before(account,character);
    if(!before || !before->inventory || !before->equipment ||
       before->inventory->root.account_id!=account || before->inventory->root.id!=character ||
       !NativeEquipmentSnapshot::same_root(before->inventory->root,before->equipment->root) ||
       before->equipment->actor_handle!=entry->actor_handle || before->equipment->position!=*old.saved || !pose_current(old))
        throw std::invalid_argument("Owned movement requires both genuine current complete banks");
    // Reuse the entire legacy batch recipe. All allocation/ACK/path generation
    // completes while live queue and both persisted populations are still OLD.
    auto prepared=prepare_move_batch(old,requests);
    const auto limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
    if(old.saved->revision>=limit || !before->equipment->revision || before->equipment->revision>=limit)
        throw std::invalid_argument("Owned movement revision overflow");
    auto expected_equipment=*before->equipment;
    expected_equipment.position.x=static_cast<std::uint16_t>(prepared.next.x);
    expected_equipment.position.y=static_cast<std::uint16_t>(prepared.next.y);
    ++expected_equipment.position.revision;++expected_equipment.revision;
    constexpr std::string_view marker=";CUSTOM-0095:ordinary-move-preserves-material";
    if(expected_equipment.source_record.find(marker)==std::string::npos) {
        if(expected_equipment.source_record.size()>2048-marker.size())
            throw std::invalid_argument("Owned movement provenance exceeds bounded storage");
        expected_equipment.source_record.append(marker);
    }
    if(!pose_current(old))throw std::invalid_argument("Owned movement before pose became stale");
    // CUSTOM-0095: the actual normal-entry batch owns ONE durable final pose,
    // with the original ACK/path/queue recipe frozen before the sole joint CAS.
    // This private receipt is separate from shared-world per-step/full-Lease
    // custody; no intermediate persisted poses or native5D grant are invented.
    std::optional<Session::NormalMovementBatchWrite> response_write;
    if(session.owned_normal_movement_response_custody_enabled()) {
        std::vector<Session::NormalMovementBatchWrite::Destination> destinations;
        destinations.reserve(prepared.path.size());
        for(const auto& step:prepared.path)destinations.push_back({step.x,step.y});
        response_write=session.prepare_normal_movement_response_write(*initialization,*before,
            expected_equipment,requests,old.slot,prepared.next.slot,destinations,prepared.response);
        if(!response_write || !active_current(old))
            throw std::invalid_argument("Owned movement original batch response custody rejected");
    }
    // Only this pure OLD owner predicate runs inside the joint transaction.
    // No current_location, repository reader, callback, send or SQL reentry.
    const auto committed=custody.move_position_from_current(*before,entry->actor_handle,
        expected_equipment.position.x,expected_equipment.position.y,[&]{return active_current(old);});
    if(!committed)throw std::runtime_error("Owned movement authority rejected before commit");
    if(!active_current(old) || committed->inventory().snapshot()!=*before->inventory ||
       committed->equipment().snapshot()!=expected_equipment || !custody.committed_current(*committed) || !active_current(old))
        throw std::runtime_error("Owned movement committed but old local publication became stale");
    // Storage is now NEW. Publishing this trivially copied Position allocates
    // nothing; old current_location would reject until saved becomes NEW too.
    prepared.next.saved=committed->equipment().snapshot().position;
    {
        const auto found=active_.find(id);
        if(found==active_.end() || found->second!=old || !local())
            throw std::runtime_error("Owned movement committed but active incarnation was retired");
        found->second=prepared.next;
    }
    if(!pose_current(prepared.next) || !custody.committed_current(*committed) || !pose_current(prepared.next))
        throw std::runtime_error("Owned movement committed but ACK delivery became stale");
    // Seal only the actual private joint receipt after complete current checks
    // and local queue publication. Failure terminates this durable prefix;
    // there is no retry, rollback, second CAS or synthesized per-step receipt.
    if(response_write && (!session.commit_normal_movement_response_write(*response_write,*committed,
            *prepared.next.saved) || !active_current(prepared.next)))
        throw std::runtime_error("Owned movement committed but original batch custody became stale");
    return OwnedCommittedMove({std::move(prepared.response),old.saved,*prepared.next.saved,
        prepared.displaced_steps,std::move(prepared.path)},*committed);
}
void RecoveredMovementService::remove(std::uint64_t session) noexcept { if(owned_movement_busy_)owned_movement_invalid_=true;active_.erase(session); }
bool RecoveredMovementService::character_active(std::uint64_t account,std::uint64_t character) const noexcept {
    if(!account || !character)return false;
    for(const auto& [session,position]:active_) {
        (void)session;
        if(position.account==account && position.character==character)return true;
    }
    return false;
}
}
