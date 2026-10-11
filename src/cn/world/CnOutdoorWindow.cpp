#include "cn/world/CnOutdoorWindow.h"
#include "cn/assets/CnSceneAssets.h"
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2cn {
CnOutdoorWindow::CameraPrepared::CameraPrepared(std::shared_ptr<const Identity> identity,
    std::uint64_t expected,CnOutdoorCamera::Projection projection,std::optional<MapSwitch> change)
    :identity_(std::move(identity)),expected_(expected),projection_(projection),switch_(std::move(change)) {}
CnOutdoorWindow::Prepared::Prepared(std::shared_ptr<const Identity> identity,std::uint64_t expected,
    State next,std::array<bool,9> reloaded)
    :identity_(std::move(identity)),expected_(expected),next_(std::move(next)),reloaded_(reloaded) {}
CnOutdoorWindow::PreparedCameraSwitch::PreparedCameraSwitch(Prepared cache,CameraPrepared camera,
    std::shared_ptr<const CnPreparedStandaloneOutdoorScene> standalone,bool replacement)
    :cache_(std::move(cache)),camera_(std::move(camera)),standalone_(std::move(standalone)),replaces_resource_(replacement) {}
CnOutdoorWindow::CnOutdoorWindow(std::shared_ptr<const CnOutdoorSceneResources> resources,State state)
    :resources_(std::move(resources)),state_(std::move(state)) {}
void CnOutdoorWindow::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN outdoor cache game owner mismatch");
}
std::shared_ptr<CnOutdoorWindow> CnOutdoorWindow::from_initial(
    std::shared_ptr<const CnOutdoorSceneResources> resources,
    const CnOutdoorTerrain::InitialWorldPlacement& initial) {
    if(!resources || initial.neighborhood.grid.mode()!=CnMapPassability::Mode::window0)
        throw std::invalid_argument("CN outdoor cache requires actual mode0 initialization");
    const auto center=initial.neighborhood.center;
    std::array<Slot,9> slots;
    for(std::size_t i=0;i<slots.size();++i) {
        const auto& loaded=initial.neighborhood.loaded_slots[i];
        const Coordinate expected{center.x+static_cast<std::int32_t>(i%3)-1,
            center.y+static_cast<std::int32_t>(i/3)-1};
        if(!loaded || loaded->x!=expected.x || loaded->y!=expected.y || !resources->chunk_available(*loaded))
            throw std::invalid_argument("CN outdoor cache initial slot incomplete");
        slots[i]=Slot{static_cast<std::uint8_t>(i),*loaded,true};
    }
    return std::shared_ptr<CnOutdoorWindow>(new CnOutdoorWindow(std::move(resources),
        State{center,slots,initial.neighborhood.grid,1}));
}
std::array<CnOutdoorWindow::Slot,9> CnOutdoorWindow::rotated_slots(Coordinate center) const {
    owner();
    auto slots=state_.slots;
    const auto dx=std::int64_t(center.x)-state_.center.x;
    const auto dy=std::int64_t(center.y)-state_.center.y;
    //0046D460 clears all+54 for initial(-1,-1) or |delta|>1. Initial
    // construction already loads all9; this branch handles later long shifts.
    if(dx>1 || dx< -1 || dy>1 || dy< -1) {
        for(auto& slot:slots)slot.valid=false;
    } else {
        // Pointer order from pinned assembly: horizontal rotations first,
        // then vertical, including the already invalidated corner on diagonals.
        for(std::size_t row=0;row<3;++row) {
            const auto a=row*3;
            if(dx==1) {
                if(!slots[a].coordinate)throw std::logic_error("CN native horizontal recycle would dereference a null edge");
                auto edge=slots[a];edge.valid=false;
                slots[a]=slots[a+1];slots[a+1]=slots[a+2];slots[a+2]=edge;
            } else if(dx==-1) {
                if(!slots[a+2].coordinate)throw std::logic_error("CN native horizontal recycle would dereference a null edge");
                auto edge=slots[a+2];edge.valid=false;
                slots[a+2]=slots[a+1];slots[a+1]=slots[a];slots[a]=edge;
            }
        }
        for(std::size_t col=0;col<3;++col) {
            if(dy==1) {
                if(!slots[col].coordinate)throw std::logic_error("CN native vertical recycle would dereference a null edge");
                auto edge=slots[col];edge.valid=false;
                slots[col]=slots[col+3];slots[col+3]=slots[col+6];slots[col+6]=edge;
            } else if(dy==-1) {
                if(!slots[col+6].coordinate)throw std::logic_error("CN native vertical recycle would dereference a null edge");
                auto edge=slots[col+6];edge.valid=false;
                slots[col+6]=slots[col+3];slots[col+3]=slots[col];slots[col]=edge;
            }
        }
    }
    return slots;
}
std::optional<CnOutdoorWindow::Prepared> CnOutdoorWindow::prepare_native_46c830(Coordinate requested) const {
    owner();
    if(!resources_->has_retained_mbd() || state_.generation==std::numeric_limits<std::uint64_t>::max())return std::nullopt;
    const auto center=resources_->qualified_center(requested);
    if(!center)return std::nullopt;
    auto slots=rotated_slots(*center);
    std::array<bool,9> reloaded{};
    std::array<std::optional<Coordinate>,9> loaded;
    //0046C830 visits row-major, loads invalid+54, reuses valid+54, and updates
    // slot+3C. Actual terrain comes from the retained decoded MBD profile.
    for(std::size_t i=0;i<slots.size();++i) {
        const Coordinate target{center->x+static_cast<std::int32_t>(i%3)-1,
            center->y+static_cast<std::int32_t>(i/3)-1};
        if(!slots[i].valid) {
            if(!resources_->chunk_available(target))return std::nullopt;
            slots[i].coordinate=target;slots[i].valid=true;reloaded[i]=true;
        } else if(!slots[i].coordinate || slots[i].coordinate->x!=target.x || slots[i].coordinate->y!=target.y) {
            throw std::logic_error("CN valid recycled cache slot has stale coordinates");
        }
        loaded[i]=slots[i].coordinate;
    }
    auto grid=resources_->complete_declared_frame_window(*center,loaded);
    return Prepared(identity_,state_.generation,
        State{*center,slots,std::move(grid),state_.generation+1},reloaded);
}
bool CnOutdoorWindow::commit(Prepared prepared) {
    owner();
    if(prepared.identity_!=identity_ || prepared.expected_!=state_.generation)return false;
    state_=std::move(prepared.next_);return true;
}
std::optional<CnOutdoorWindow::CameraPrepared> CnOutdoorWindow::prepare_camera(
    const CnOutdoorCamera::View& view,std::int32_t native_map34,std::string_view prefix) const {
    owner();
    const auto projection=CnOutdoorCamera::project_mode0(view);
    if(!projection)return std::nullopt;
    std::optional<MapSwitch> change;
    const auto shift=projection->shift;
    if((shift.x || shift.y) && (native_map34==5 || native_map34==0x10 || native_map34==0x11)) {
        const auto x=std::int64_t(state_.center.x)+shift.x,y=std::int64_t(state_.center.y)+shift.y;
        if(x>=0 && y>=0) {
            if(x>std::numeric_limits<std::int32_t>::max() || y>std::numeric_limits<std::int32_t>::max())return std::nullopt;
            const Coordinate requested{static_cast<std::int32_t>(x),static_cast<std::int32_t>(y)};
            const auto reference=CnOutdoorCamera::map_reference(prefix,requested);
            const auto camera=CnOutdoorCamera::success_camera(view.camera,shift);
            if(!reference || !camera)return std::nullopt;
            change=MapSwitch{requested,*reference,*camera};
        }
    }
    return CameraPrepared(identity_,state_.generation,*projection,std::move(change));
}
bool CnOutdoorWindow::current(const CameraPrepared& prepared) const {
    owner();return prepared.identity_==identity_ && prepared.expected_==state_.generation;
}
std::optional<CnOutdoorWindow::PreparedCameraSwitch> CnOutdoorWindow::prepare_camera_switch(
    const CameraPrepared& camera) const {
    owner();
    if(!current(camera) || !camera.switch_)return std::nullopt;
    const auto& change=*camera.switch_;
    if(!resources_->owns_native_map_reference(change.native_reference,change.requested))return std::nullopt;
    //00470C90's same-resource retained-MBD branch uses the same request gate,
    // clamp, rotation, invalid/reused slots and grid compositor as0046C830.
    auto cache=prepare_native_46c830(change.requested);
    if(!cache)return std::nullopt;
    return PreparedCameraSwitch(std::move(*cache),camera);
}
std::optional<CnOutdoorWindow::PreparedCameraSwitch> CnOutdoorWindow::prepare_camera_switch(
    const CameraPrepared& camera,const CnSceneAssets& assets,std::size_t encoded_budget,std::size_t plain_budget) const {
    owner();
    if(!current(camera) || !camera.switch_ || state_.generation==std::numeric_limits<std::uint64_t>::max())
        return std::nullopt;
    const auto& change=*camera.switch_;
    if(resources_->owns_native_map_reference(change.native_reference,change.requested)) {
        if(resources_->has_retained_mbd())return prepare_camera_switch(camera);
        return prepare_standalone_reuse(camera,assets,encoded_budget,plain_budget);
    }
    auto loaded=assets.prepare_standalone_switch(change.native_reference,change.requested,encoded_budget,plain_budget,
        state_.grid.initialized_cells());
    if(!loaded)return std::nullopt;
    // Preparation may perform I/O, but a stale generation cannot replace the
    // active resource. Original actor/DB/scene revision CAS is still separate.
    if(!current(camera) || loaded->resources()->has_retained_mbd() ||
       !loaded->resources()->owns_native_map_reference(change.native_reference,change.requested))return std::nullopt;
    const auto center=loaded->center();
    auto slots=state_.slots;
    std::array<bool,9> reloaded;
    reloaded.fill(true);
    // Native different-MDT sets previous(-1,-1);0046D460 invalidates every
    // retained allocation without rotating it. Known.map open failures leave
    // null slots; no loaded coordinates or zero terrain are fabricated for them.
    for(std::size_t i=0;i<slots.size();++i) {
        const Coordinate target{center.x+static_cast<std::int32_t>(i%3)-1,
            center.y+static_cast<std::int32_t>(i/3)-1};
        slots[i].valid=loaded->chunks()[i].has_value();
        slots[i].coordinate=slots[i].valid ? std::optional<Coordinate>(target) : std::nullopt;
    }
    Prepared cache(identity_,state_.generation,State{center,slots,loaded->grid(),state_.generation+1},reloaded);
    auto snapshot=std::make_shared<const CnPreparedStandaloneOutdoorScene>(std::move(*loaded));
    return PreparedCameraSwitch(std::move(cache),camera,std::move(snapshot),true);
}
std::optional<CnOutdoorWindow::PreparedCameraSwitch> CnOutdoorWindow::prepare_standalone_reuse(
    const CameraPrepared& camera,const CnSceneAssets& assets,std::size_t encoded_budget,std::size_t plain_budget) const {
    owner();
    if(!current(camera) || !camera.switch_ || resources_->has_retained_mbd() || !standalone_snapshot_ ||
       state_.generation==std::numeric_limits<std::uint64_t>::max())return std::nullopt;
    const auto& change=*camera.switch_;
    const auto& previous=*standalone_snapshot_;
    if(previous.resources()!=resources_ || previous.center().x!=state_.center.x || previous.center().y!=state_.center.y)
        throw std::logic_error("CN standalone snapshot does not belong to active resource/cache");
    if(!resources_->owns_native_map_reference(change.native_reference,change.requested))return std::nullopt;
    const auto center=resources_->qualified_center(change.requested);
    if(!center)return std::nullopt;
    auto slots=rotated_slots(*center);
    std::array<std::optional<CnStandaloneMapAsset>,9> chunks;
    std::array<std::filesystem::path,9> chunk_paths;
    std::array<bool,9> reloaded{};
    for(std::size_t i=0;i<slots.size();++i) {
        const Coordinate target{center->x+static_cast<std::int32_t>(i%3)-1,
            center->y+static_cast<std::int32_t>(i/3)-1};
        if(slots[i].valid) {
            // Allocation labels follow native pointer rotation. Locate the
            // actual previously loaded payload; never substitute a disk reread.
            const auto old=std::find_if(state_.slots.begin(),state_.slots.end(),[&](const Slot& slot) {
                return slot.allocation_label==slots[i].allocation_label;
            });
            if(old==state_.slots.end() || !old->valid || !old->coordinate || !slots[i].coordinate ||
               old->coordinate->x!=target.x || old->coordinate->y!=target.y ||
               slots[i].coordinate->x!=target.x || slots[i].coordinate->y!=target.y)
                throw std::logic_error("CN reused standalone allocation has stale coordinates");
            const auto index=static_cast<std::size_t>(old-state_.slots.begin());
            if(!previous.chunks()[index] || previous.chunk_source_files()[index].empty())
                throw std::logic_error("CN reused standalone allocation lacks actual payload/provenance");
            chunks[i]=previous.chunks()[index];
            chunk_paths[i]=previous.chunk_source_files()[index];
        } else {
            auto loaded=assets.read_standalone_chunk(*resources_,target,encoded_budget,plain_budget);
            chunks[i]=std::move(loaded.asset);chunk_paths[i]=std::move(loaded.source_path);
            slots[i].valid=chunks[i].has_value();
            slots[i].coordinate=slots[i].valid ? std::optional<Coordinate>(target) : std::nullopt;
            reloaded[i]=true; // Actual load attempt, including native open failure.
        }
    }
    if(!current(camera))return std::nullopt;
    auto paths=previous.source_files();
    if(paths.size()<9)throw std::logic_error("CN standalone snapshot source manifest incomplete");
    paths.resize(paths.size()-9); // Retain original profile sources; replace slot-ordered chunk paths only.
    paths.insert(paths.end(),chunk_paths.begin(),chunk_paths.end());
    auto grid=resources_->compose_standalone_frame_window(*center,chunks,state_.grid.initialized_cells());
    Prepared cache(identity_,state_.generation,State{*center,slots,grid,state_.generation+1},reloaded);
    auto snapshot=std::shared_ptr<const CnPreparedStandaloneOutdoorScene>(new CnPreparedStandaloneOutdoorScene(
        change.native_reference,std::move(paths),std::move(chunk_paths),*center,std::move(chunks),std::move(grid),resources_));
    return PreparedCameraSwitch(std::move(cache),camera,std::move(snapshot),false);
}
std::optional<CnOutdoorWindow::CommittedCameraSwitch> CnOutdoorWindow::commit_camera_switch(
    PreparedCameraSwitch candidate) {
    owner();
    if(!current(candidate.camera_) || !candidate.camera_.switch_)return std::nullopt;
    const auto camera=candidate.camera_.switch_->camera_after_actual_switch_success;
    const auto visible=candidate.camera_.projection_.visible_slots;
    const auto center=candidate.cache_.center();
    const bool center_available=candidate.cache_.slots()[4].valid;
    if(candidate.standalone_ && !candidate.replaces_resource_ && candidate.standalone_->resources()!=resources_)
        return std::nullopt;
    if(!commit(std::move(candidate.cache_)))return std::nullopt;
    const bool replacement=candidate.replaces_resource_;
    if(candidate.standalone_) {
        resources_=candidate.standalone_->resources();
        standalone_snapshot_=std::move(candidate.standalone_);
    }
    return CommittedCameraSwitch{camera,visible,center,replacement,center_available};
}
const CnMapPassability& CnOutdoorWindow::grid() const {owner();return state_.grid;}
bool CnOutdoorWindow::current(const PreparedCameraSwitch& prepared) const {
    owner();return current(prepared.camera_) && prepared.cache_.identity_==identity_ &&
        prepared.cache_.expected_==state_.generation;
}
CnOutdoorWindow::Coordinate CnOutdoorWindow::center() const {owner();return state_.center;}
std::uint64_t CnOutdoorWindow::generation() const {owner();return state_.generation;}
bool CnOutdoorWindow::center_slot_present() const {owner();return state_.slots[4].coordinate.has_value();}
const CnPreparedStandaloneOutdoorScene* CnOutdoorWindow::standalone_snapshot() const {
    owner();return standalone_snapshot_.get();
}
}
