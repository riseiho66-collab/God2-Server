#include "cn/world/SharedNativeMovementScene.h"
#include <bit>
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2::cn {
namespace {
struct MutationScope {
    bool& busy;
    explicit MutationScope(bool& value):busy(value){busy=true;}
    ~MutationScope(){busy=false;}
};
}
SharedNativeMovementScene::SharedNativeMovementScene(const std::shared_ptr<SharedCredentialConnection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,std::shared_ptr<SharedInitialScene> initial,
    const god2cn::CnSceneAssets& assets,std::shared_ptr<Authority> authority,std::size_t encoded_budget,
    std::size_t plain_budget,SharedMovement::Scene snapshot)
    :connection_(connection),presence_(std::move(presence)),lease_(lease),initial_(std::move(initial)),assets_(assets),
     authority_(std::move(authority)),encoded_budget_(encoded_budget),plain_budget_(plain_budget),position_(lease.position),
     revision_(snapshot.revision),mode_(snapshot.mode),direction_(snapshot.previous_direction),
     house_or_initial_grid_(std::move(snapshot.cells)),window_(initial_->outdoor_window_) {
    if(window_) {
        cache_generation_=window_->generation();initial_cache_generation_=cache_generation_;
        initial_camera_seed_=initial_->initial_outdoor_camera_seed();
    }
}
void SharedNativeMovementScene::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN live movement scene game owner mismatch");
}
bool SharedNativeMovementScene::bound() const {
    const auto connection=connection_.lock();
    return !frame_failed_ && connection && !connection->closing() && connection->world_session_id()==lease_.session &&
        connection->verified_account_id()==lease_.account && connection->world_character_offered(lease_.character) &&
        initial_->connection_.lock()==connection && initial_->presence_==presence_ && initial_->lease_==lease_ &&
        initial_->map_current() && presence_->ready(lease_);
}
const god2cn::CnMapPassability& SharedNativeMovementScene::cells() const {
    return window_?window_->grid():house_or_initial_grid_;
}
bool SharedNativeMovementScene::snapshot_current(const Lease& lease,const SharedMovement::Scene& snapshot) const {
    return lease==lease_ && bound() && snapshot.area==position_.area && snapshot.scene==position_.scene &&
        snapshot.revision==revision_ && snapshot.mode==mode_ && snapshot.previous_direction==direction_ &&
        snapshot.cells==cells() && (!window_ || window_->generation()==cache_generation_);
}
std::shared_ptr<SharedNativeMovementScene> SharedNativeMovementScene::adopt(
    const std::shared_ptr<SharedCredentialConnection>& connection,std::shared_ptr<SharedWorldPresence> presence,
    const Lease& lease,std::shared_ptr<SharedInitialScene> initial,const god2cn::CnSceneAssets& assets,
    std::shared_ptr<Authority> authority,std::size_t encoded_budget,std::size_t plain_budget) {
    if(!connection || !presence || !initial || !authority || !encoded_budget || !plain_budget)return {};
    initial->owner();
    if(initial->live_claimed_ || initial->assets_identity_!=&assets || initial->presence_!=presence || initial->lease_!=lease || !initial->bound(connection) ||
       !presence->ready(lease) || !initial->map_current())return {};
    const auto begin=god2cn::CnWorldEntry::read_begin_play(initial->begin_);
    if(!begin)return {};
    const auto snapshot=initial->initial_movement_scene(connection,lease.position,initial->revision_,begin->native_direction());
    if(!snapshot || (snapshot->mode==0 && !initial->outdoor_window_) ||
       (snapshot->mode==2 && initial->outdoor_window_) || (snapshot->mode!=0 && snapshot->mode!=2))return {};
    auto result=std::shared_ptr<SharedNativeMovementScene>(new SharedNativeMovementScene(connection,std::move(presence),
        lease,initial,assets,std::move(authority),encoded_budget,plain_budget,*snapshot));
    if(!result->current(lease,*snapshot) || (snapshot->mode==0 && !result->initial_camera_seed_))return {};
    initial->live_claimed_=true;return result;
}
std::optional<god2cn::CnOutdoorCamera::Point> SharedNativeMovementScene::initial_camera_seed(const Lease& lease) const {
    owner();
    if(lease!=lease_ || busy_ || pending_ || mode_!=0 || position_!=lease_.position ||
       revision_!=initial_->revision_ || !bound() || !window_ || camera_view_ ||
       window_->generation()!=initial_cache_generation_)return std::nullopt;
    const auto saved=presence_->saved_position(lease_);
    if(!saved || *saved!=position_)return std::nullopt;
    return initial_camera_seed_;
}
std::optional<SharedMovement::Scene> SharedNativeMovementScene::scene(const Lease& lease,const RecoveredPosition& position) {
    owner();if(lease!=lease_ || position!=position_ || !bound())return std::nullopt;
    const auto saved=presence_->saved_position(lease_);
    if(!saved || *saved!=position_ || (window_ && window_->generation()!=cache_generation_))return std::nullopt;
    return SharedMovement::Scene{position_.area,position_.scene,revision_,mode_,direction_,cells()};
}
bool SharedNativeMovementScene::advance_native_camera_frame(const Lease& lease) {
    owner();
    if(busy_ || pending_ || mode_!=0 || !window_ || lease!=lease_ ||
       revision_==std::numeric_limits<std::uint64_t>::max())return false;
    const auto snapshot=scene(lease,position_);
    if(!snapshot || !current(lease,*snapshot))return false;
    MutationScope mutation(busy_);
    auto permit=authority_->native_frame(FrameCandidate{lease_,position_,revision_,camera_view_,native_clock_});
    if(!permit || !permit->publish_native_frame || !permit->observe_completed_loop_clock ||
       !permit->publish_native_clock || permit->actual_actor_state!=8 ||
       permit->actual_owner_generation<=native_frame_generation_ || !current(lease,*snapshot))return false;
    if(native_clock_ && permit->actual_clock_before!=*native_clock_)return false;
    const auto before=permit->motion_before.camera;
    const auto supplied=permit->camera.actual_native_frame_view.camera;
    const auto expected=camera_view_?std::optional(camera_view_->camera):initial_camera_seed_;
    if(!expected || before.x!=expected->x || before.y!=expected->y ||
       supplied.x!=before.x || supplied.y!=before.y)return false;
    if(permit->actual_started_motion) {
        const auto& start=*permit->actual_started_motion;
        const auto initialized=god2cn::CnNativeCameraMotion::begin(before,start.direction,start.actual_speed_index,
            start.actual_mount_addition);
        const auto& actual=permit->motion_before;
        const auto bits=[](float f){return std::bit_cast<std::uint32_t>(f);};
        if(!initialized || initialized->remaining_x!=actual.remaining_x || initialized->remaining_y!=actual.remaining_y ||
           bits(initialized->velocity_x)!=bits(actual.velocity_x) || bits(initialized->velocity_y)!=bits(actual.velocity_y) ||
           bits(initialized->residue_x)!=bits(actual.residue_x) || bits(initialized->residue_y)!=bits(actual.residue_y))return false;
    }
    const auto motion=god2cn::CnNativeCameraMotion::advance(permit->motion_before,
        permit->actual_clock_before.stored_elapsed);
    if(!motion)return false;
    if(motion->complete && (!permit->observe_deferred_notification ||
       !permit->path_after_deferred_notification || !permit->publish_native_path))return false;
    auto view=permit->camera.actual_native_frame_view;view.camera=motion->after.camera;
    std::optional<god2cn::CnOutdoorWindow::CameraPrepared> camera;
    if(window_->center_slot_present()) {
        camera=window_->prepare_camera(view,permit->camera.native_map34,permit->camera.native_owner_prefix);
        if(!camera)return false;
    } else if(!visible_slots_)return false; // Native preserves prior flags; never fabricate zero flags.
    std::optional<god2cn::CnOutdoorWindow::PreparedCameraSwitch> change;
    if(camera && camera->map_switch()) {
        change=window_->prepare_camera_switch(*camera,assets_,encoded_budget_,plain_budget_);
        if(!change)return false;
    }
    if(!current(lease,*snapshot) || (camera && !window_->current(*camera)) || (change && !window_->current(*change)))return false;
    FramePublished result{*motion,view,std::nullopt,camera?camera->projection().visible_slots:*visible_slots_};
    if(change) {
        const auto committed=window_->commit_camera_switch(std::move(*change));
        if(!committed)return false;
        result.view.camera=committed->camera_after_cache_commit;
        result.motion.after.camera=result.view.camera;
        result.successful_cache_rebase=god2cn::CnOutdoorCamera::Point{
            motion->after.camera.x-result.view.camera.x,motion->after.camera.y-result.view.camera.y};
        result.visibility=committed->native_visibility_before_switch;
    }
    // Ordered camera/cache/model publication, not an ACID gameplay transaction.
    camera_view_=result.view;visible_slots_=result.visibility;cache_generation_=window_->generation();
    native_frame_generation_=permit->actual_owner_generation;++revision_;
    try {
        if(!permit->publish_native_frame(result) || !bound()) {frame_failed_=true;return false;}
        if(motion->complete) {
            //005395E0: frame first, deferred notification/flag clear, cursor
            // increment, next00539150 OR final state0/target. Clock comes later.
            const auto observed_refresh=permit->observe_deferred_notification();
            if(!observed_refresh || !bound()) {frame_failed_=true;return false;}
            const auto drain=observed_refresh->completed_step_operand();
            if(!drain || !drain->current() || !bound()) {frame_failed_=true;return false;}
            const auto path=permit->path_after_deferred_notification(*drain);
            if(!path || !drain->completed_by(path->actual_after_notification) || !bound()) {
                frame_failed_=true;return false;
            }
            const auto plan=god2cn::CnNativePathCompletion::prepare(path->path);
            if(!plan || !permit->publish_native_path(*plan) || !bound()) {frame_failed_=true;return false;}
        }
        //0048AA10/005395E0 publication precedes new timeGetTime samples.
        // Newly bounded elapsed is for NEXT frame, never this motion calculation.
        const auto observed=permit->observe_completed_loop_clock();
        if(!observed || observed->before!=permit->actual_clock_before || !bound()) {frame_failed_=true;return false;}
        const auto next_clock=god2cn::CnNativeFrameClock::after_native_update(*observed);
        if(!next_clock || !permit->publish_native_clock(*next_clock) || !bound()) {frame_failed_=true;return false;}
        native_clock_=next_clock->after;
    } catch(...) {frame_failed_=true;throw;}
    const auto saved=presence_->saved_position(lease_);
    if(!saved || *saved!=position_ || window_->generation()!=cache_generation_) {frame_failed_=true;return false;}
    return true;
}
bool SharedNativeMovementScene::current(const Lease& lease,const SharedMovement::Scene& snapshot) {
    owner();if(!snapshot_current(lease,snapshot))return false;
    const auto saved=presence_->saved_position(lease_);
    if(!saved || *saved!=position_)return false;
    if(pending_) {
        if(pending_->camera_switch && !window_->current(*pending_->camera_switch))return false;
        if(pending_->camera && !window_->current(*pending_->camera))return false;
    }
    return true;
}
bool SharedNativeMovementScene::same_step(const god2cn::CnMapPreparedStep& a,const god2cn::CnMapPreparedStep& b) {
    return a.step.destination.x==b.step.destination.x && a.step.destination.y==b.step.destination.y &&
        a.step.direction==b.step.direction && a.step.client_ring_index==b.step.client_ring_index && a.native_cell==b.native_cell;
}
std::optional<SharedMovement::Authorization> SharedNativeMovementScene::authorize(const Lease& lease,
    const RecoveredPosition& before,const SharedMovement::Scene& snapshot,const god2cn::CnMapPreparedStep& step) {
    owner();if(busy_ || pending_ || before!=position_ || !current(lease,snapshot) ||
       revision_==std::numeric_limits<std::uint64_t>::max() || step.step.direction>7 || step.step.client_ring_index>=40 ||
       step.native_cell==0 || cells().cell_at(step.step.destination.x,step.step.destination.y)!=step.native_cell)return std::nullopt;
    const auto dx=int(step.step.destination.x)-before.x,dy=int(step.step.destination.y)-before.y;
    if(dx< -1 || dx>1 || dy< -1 || dy>1)return std::nullopt;
    MutationScope mutation(busy_);
    Candidate candidate{lease_,before,revision_,mode_,step};
    auto permit=authority_->authorize(candidate);
    if(!permit || !permit->publish_authority || !god2cn::CnMovement::read_step_ack(permit->full_native_ack) ||
       !current(lease,snapshot))return std::nullopt;
    Pending prepared{candidate,std::move(*permit),std::nullopt,std::nullopt};
    if(mode_==0) {
        if(!window_ || !prepared.permit.camera)return std::nullopt;
        const auto& input=*prepared.permit.camera;
        prepared.camera=window_->prepare_camera(input.actual_native_frame_view,input.native_map34,input.native_owner_prefix);
        if(!prepared.camera)return std::nullopt;
        if(prepared.camera->map_switch()) {
            prepared.camera_switch=window_->prepare_camera_switch(*prepared.camera,assets_,encoded_budget_,plain_budget_);
            if(!prepared.camera_switch)return std::nullopt;
        }
    }else if(prepared.permit.camera)return std::nullopt; // No invented indoor camera mode0 conversion.
    if(!current(lease,snapshot) || (prepared.camera && !window_->current(*prepared.camera)) ||
       (prepared.camera_switch && !window_->current(*prepared.camera_switch)))return std::nullopt;
    // All permit/reply/resource/cache preparation and allocation precede DB CAS.
    SharedMovement::Authorization output{prepared.permit.full_native_ack};
    pending_.emplace(std::move(prepared));return output;
}
bool SharedNativeMovementScene::publish(const Lease& lease,const SharedMovement::Scene& snapshot,
    const SharedMovement::Committed& committed) {
    owner();if(busy_ || !pending_ || !snapshot_current(lease,snapshot) || committed.before!=position_ ||
       pending_->candidate.before!=position_ || pending_->candidate.scene_revision!=revision_ ||
       !same_step(pending_->candidate.step,committed.native_step) || committed.after.area!=position_.area ||
       committed.after.scene!=position_.scene || committed.after.x!=committed.native_step.step.destination.x ||
       committed.after.y!=committed.native_step.step.destination.y || committed.after.revision<=position_.revision)return false;
    const auto saved=presence_->saved_position(lease_);
    if(!saved || *saved!=committed.after || (pending_->camera && !window_->current(*pending_->camera)) ||
       (pending_->camera_switch && !window_->current(*pending_->camera_switch)))return false;
    MutationScope mutation(busy_);
    auto prepared=std::move(*pending_);pending_.reset(); // One-use; never replay a partly published commit.
    if(prepared.camera_switch) {
        const auto applied=window_->commit_camera_switch(std::move(*prepared.camera_switch));
        if(!applied)return false;
        camera_view_=prepared.permit.camera->actual_native_frame_view;
        camera_view_->camera=applied->camera_after_cache_commit;
        visible_slots_=applied->native_visibility_before_switch;
    }else if(prepared.camera) {
        camera_view_=prepared.permit.camera->actual_native_frame_view;
        visible_slots_=prepared.camera->projection().visible_slots;
    }
    position_=committed.after;direction_=committed.native_step.step.direction;++revision_;
    if(window_)cache_generation_=window_->generation();
    // The concrete owner now has the real committed actor/direction/cache,
    // including future scene reads after the first movement. External original
    // pending/timing authority still must publish successfully before5E/5D.
    if(!prepared.permit.publish_authority(committed.after) || !bound())return false;
    const auto current_saved=presence_->saved_position(lease_);
    return current_saved && *current_saved==position_ && (!window_ || window_->generation()==cache_generation_);
}
}
