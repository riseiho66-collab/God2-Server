#include "handlers/RecoveredMovementService.h"
#include "protocol/RecoveredCharacterListCandidate.h"
#include "protocol/RecoveredWorldFrame.h"
#include "protocol/RecoveredWorldEntryView.h"
#include "game/TaiwanWorldEntryIdentity.h"
#include <algorithm>
#include <fstream>
#include <nlohmann/json.hpp>
#include <cstdlib>
#include <utility>
#include <limits>
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
    const auto expected=kunlun?"9c3af8c338c2c26a5d5ee2156d0105cdf9d893666c656814aaae3973d7333f35":"08ccfb33262913f97383da9abcc8bba58b2705e377fbbec004ee5cdfc35013c2";
    if(actual!=expected)
        throw std::invalid_argument("Door navigation bundle source changed");
#else
    throw std::runtime_error("Door navigation requires qualified SHA256 backend");
#endif
    const auto j=nlohmann::json::parse(bytes);
    if(j.at("schema")!=(kunlun?"god2-current-kunlun-doors-v1":"god2-current-town-doors-v1") || j.at("custom_design")!="CUSTOM-0052" ||
       j.at("navigation").size()!=(kunlun?6:23) || j.at("routes").size()!=(kunlun?6:23))
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
}
bool RecoveredMovementService::cell_available(int x,int y) const noexcept {
    return cell_available(initial_area_,scene_,x,y);
}
bool RecoveredMovementService::cell_available(std::uint16_t area,std::uint16_t scene,int x,int y) const noexcept {
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
                if(saved.area==4 && saved.scene==3)position.kind=0;
                if(saved.area==13 && saved.scene==12)position.kind=0;
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
std::optional<RecoveredPosition> RecoveredMovementService::current_location(
    std::uint64_t session,std::uint64_t account,std::uint64_t character) const {
    const auto it=active_.find(session);
    if(it==active_.end() || !it->second.ready || it->second.transfer_pending ||
       it->second.account!=account || it->second.character!=character ||
       characters_.load_position(account,character)!=it->second.saved)
        return std::nullopt;
    const auto& position=it->second;
    return RecoveredPosition{position.area,position.scene,
        static_cast<std::uint16_t>(position.x),static_cast<std::uint16_t>(position.y),
        position.saved?position.saved->revision:0};
}
std::vector<std::uint8_t> RecoveredMovementService::move(std::uint64_t session,std::uint64_t account,
    std::uint64_t character,std::span<const RecoveredMovement::Request> requests) {
    return move_committed(session,account,character,requests).reply;
}
void RecoveredMovementService::resume_after_battle(std::uint64_t session,std::uint64_t account,std::uint64_t character) {
    const auto it=active_.find(session);
    if(it==active_.end() || !it->second.ready || it->second.transfer_pending || it->second.account!=account ||
       it->second.character!=character || characters_.load_position(account,character)!=it->second.saved)
        throw std::invalid_argument("Battle return movement baseline mismatch");
    // Native world return resets the connection ring, not the saved coordinates.
    it->second.slot=0;
}
std::vector<std::uint8_t> RecoveredMovementService::begin_town_transfer(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y) {
    return begin_transfer(session,account,character,expected,4,4,x,y);
}
std::vector<std::uint8_t> RecoveredMovementService::begin_indoor_transfer(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y) {
    return begin_transfer(session,account,character,expected,4,15,x,y);
}
std::vector<std::uint8_t> RecoveredMovementService::begin_initial_indoor_transfer(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,std::uint16_t x,std::uint16_t y) {
    const auto it=active_.find(session);
    if(it==active_.end() || it->second.saved || it->second.scene!=4 ||
       it->second.x!=initial_x_ || it->second.y!=initial_y_)
        throw std::invalid_argument("Initial indoor transfer requires unsaved town spawn");
    return begin_transfer(session,account,character,std::nullopt,4,15,x,y);
}
std::vector<std::uint8_t> RecoveredMovementService::begin_outdoor_return(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y) {
    return begin_transfer(session,account,character,expected,15,4,x,y);
}
std::vector<std::uint8_t> RecoveredMovementService::begin_island_transfer(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y) {
    return begin_transfer(session,account,character,expected,4,0,x,y);
}
std::vector<std::uint8_t> RecoveredMovementService::begin_island_return(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y) {
    return begin_transfer(session,account,character,expected,0,4,x,y);
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
    const std::optional<RecoveredPosition>& expected,std::uint16_t source_scene,std::uint16_t scene,std::uint16_t x,std::uint16_t y,std::uint16_t area) {
    const auto it=active_.find(session);
    if(!town_ || !town_source_consensus_ || it==active_.end() || !it->second.ready ||
       it->second.transfer_pending || it->second.account!=account || it->second.character!=character ||
       it->second.saved!=expected || (expected && (expected->area!=area || expected->scene!=source_scene)) ||
       it->second.area!=area || it->second.scene!=source_scene || !qualifies_transfer_destination(area,scene,x,y))
        throw std::invalid_argument("Unqualified town transfer");
    std::array<std::uint8_t,9> logical{0x61,2,1,0,0,0,0,0,0};
    const auto selector=static_cast<std::uint16_t>(area|(scene<<6));
    logical[1]=static_cast<std::uint8_t>(selector);logical[2]=static_cast<std::uint8_t>(selector>>8);
    const auto packed=(std::uint32_t{x}<<2)|(std::uint32_t{y}<<17)|
        scene_kind(area,scene)|
        (source_scene==scene?0x10000u:0u);
    for(unsigned i=0;i<4;++i) logical[5+i]=static_cast<std::uint8_t>(packed>>(8*i));
    auto reply=RecoveredWorldFrame::encode(logical);
    auto next=it->second;
    next.saved=characters_.commit_position(account,character,expected,area,scene,x,y);
    next.area=area;next.scene=scene;next.kind=scene_kind(area,scene);
    next.x=x; next.y=y; next.transfer_pending=true;
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
    if(!registered_door_pair(expected.area,expected.scene,scene))
        throw std::invalid_argument("Unregistered current doorway pair");
    return begin_transfer(session,account,character,expected,expected.scene,scene,x,y,expected.area);
}
std::uint16_t RecoveredMovementService::scene_kind(std::uint16_t area,std::uint16_t scene) const {
    // Explicit source-qualified kind registry; scene numbers alias across areas.
    if(area==4 && scene==3 && kunlun_)return 0;
    if(area==4 && scene==0 && kunlun_parent_)return 1;
    if(area==4 && kunlun_indoor_scenes_.contains(scene))return 2;
    if(area==13 && scene==12 && fruit_)return 0;
    if(area==2 && scene==4 && town_)return 0;
    if(area==2 && scene==0 && (island_ || island_full_))return 1;
    if(area==2 && (indoor_scenes_.contains(scene) || (scene==15 && grid_)))return 2;
    throw std::invalid_argument("Unregistered source scene kind");
}
bool RecoveredMovementService::registered_parent_pair(std::uint16_t area,std::uint16_t source_scene,std::uint16_t destination_scene) const noexcept {
    return area==4 && kunlun_ && kunlun_parent_ &&
        ((source_scene==3 && destination_scene==0)||(source_scene==0 && destination_scene==3));
}
std::vector<std::uint8_t> RecoveredMovementService::begin_registered_parent_transfer(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    const RecoveredPosition& expected,std::uint16_t scene,std::uint16_t x,std::uint16_t y) {
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
    const auto it=active_.find(session);
    if(it==active_.end() || !it->second.ready || !it->second.transfer_pending ||
       it->second.account!=account || it->second.character!=character ||
       characters_.load_position(account,character)!=it->second.saved)
        throw std::invalid_argument("Town transfer receipt baseline mismatch");
    // Original6C414 resets the ring then queues the destination as slot0.
    it->second.slot=0;
    it->second.transfer_pending=false;
}
RecoveredMovementService::CommittedMove RecoveredMovementService::move_committed(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    std::span<const RecoveredMovement::Request> requests,
    const std::function<void(const MovePreview&)>& precommit) {
    auto it=active_.find(session);
    if(it==active_.end() || !it->second.ready || it->second.transfer_pending || it->second.account!=account || it->second.character!=character || requests.empty())
        throw std::invalid_argument("Unbound movement rejected");
    auto next=it->second;
    const auto before=next.saved;
    std::size_t displaced_steps=0;
    std::vector<std::uint8_t> response;
    std::vector<CommittedMove::Step> path;
    path.reserve(requests.size());
    for(const auto& request:requests) {
        const auto expected=static_cast<std::uint8_t>((next.slot+1)%40);
        if(request.sequence!=expected || std::abs(static_cast<int>(request.x)-next.x)>1 ||
           std::abs(static_cast<int>(request.y)-next.y)>1 || !cell_available(next.area,next.scene,request.x,request.y))
            throw std::invalid_argument("Movement queue, step or navigation rejected");
        const auto ack=RecoveredMovement::ack(request.sequence);
        response.insert(response.end(),ack.begin(),ack.end());
        if(next.x!=request.x || next.y!=request.y) {
            ++displaced_steps;
            path.push_back({request.x,request.y});
        }
        next.x=request.x;next.y=request.y;next.slot=request.sequence;
    }
    // Validate the entire batch, then commit before publishing state or ACKs.
    if(precommit) precommit(MovePreview{next.area,next.scene,
        static_cast<std::uint16_t>(it->second.x),static_cast<std::uint16_t>(it->second.y),
        static_cast<std::uint16_t>(next.x),static_cast<std::uint16_t>(next.y),displaced_steps});
    next.saved=characters_.commit_position(account,character,it->second.saved,next.area,next.scene,
        static_cast<std::uint16_t>(next.x),static_cast<std::uint16_t>(next.y));
    it->second=next;
    return {std::move(response),before,*next.saved,displaced_steps,std::move(path)};
}
void RecoveredMovementService::remove(std::uint64_t session) noexcept { active_.erase(session); }
bool RecoveredMovementService::character_active(std::uint64_t account,std::uint64_t character) const noexcept {
    if(!account || !character)return false;
    for(const auto& [session,position]:active_) {
        (void)session;
        if(position.account==account && position.character==character)return true;
    }
    return false;
}
}
