#include "game/SharedTaiwanNativeMovementScene.h"
#include <exception>
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2 {
namespace {
struct NativeFactoryOwner {
    std::shared_ptr<SharedWorldPresence> presence;
    SharedTaiwanNativeMovementScene::MaterialSource source;
    const std::thread::id thread=std::this_thread::get_id();
    bool busy=false,reentered=false;
    ~NativeFactoryOwner() {
        if(thread!=std::this_thread::get_id())std::terminate();
    }
    bool bound(Session& session,const SharedWorldPresence::Lease& lease) const {
        if(reentered || session.closing() || session.id()!=lease.session || session.account_id!=lease.account ||
           session.character_id!=lease.character || session.state()!=SessionState::InWorld ||
           !session.recovered_world_ready() ||
           !session.common_world_delivery_current(lease.account,lease.character,lease.generation) ||
           session.common_world_entry_current(lease.account,lease.character,lease.generation))return false;
        const auto actual=presence->ready_lease(lease.session,lease.account,lease.character);
        return actual && *actual==lease;
    }
    bool current(Session& session,const SharedTaiwanNativeMovementScene::FactoryScope& expected) const {
        const auto& lease=expected.lease;
        if(!bound(session,lease) || expected.saved_position.area!=lease.position.area ||
           expected.saved_position.scene!=lease.position.scene)return false;
        const auto saved=presence->saved_position(lease);
        return saved && *saved==expected.saved_position;
    }
};
}
std::optional<SharedTaiwanNativeMovementScene::Resources>
SharedTaiwanNativeMovementScene::Resources::compose_mode2(TaiwanNativeGrid::Material material,
    std::uint64_t resource_generation,std::uint64_t initial_scene_generation) {
    if(!resource_generation || !initial_scene_generation)return std::nullopt;
    auto actual=TaiwanNativeGrid::compose(std::move(material));
    if(!actual || !actual->complete())return std::nullopt;
    // A server-owned native composition is not an x86 snapshot. Do not invent
    // map/grid structures, pointer links or addresses to fit the other path.
    return Resources{BufferImage{0,{}},{},{},resource_generation,initial_scene_generation,
        std::move(*actual)};
}
SharedTaiwanNativeMovementScene::CellSource SharedTaiwanNativeMovementScene::Resources::cell_source() const noexcept {
    return composed_grid?CellSource::ComposedMode2:CellSource::RawSnapshot;
}
bool SharedTaiwanNativeMovementScene::Resources::complete() const {
    if(composed_grid)
        return !map.address && map.bytes.empty() && !grid && !cells && composed_grid->complete();
    return RecoveredTaiwanMapCell::complete(input());
}
std::optional<std::uint8_t> SharedTaiwanNativeMovementScene::Resources::read(std::int32_t x,std::int32_t y) const {
    if(!complete())return std::nullopt;
    if(composed_grid)return composed_grid->read(x,y);
    return RecoveredTaiwanMapCell::read(input(),x,y);
}
RecoveredTaiwanMapCell::Input SharedTaiwanNativeMovementScene::Resources::input() const {
    if(composed_grid)throw std::logic_error("Composed TW native grid has no raw x86 map input");
    RecoveredTaiwanMapCell::Input result{{map.address,map.bytes},{},{}};
    if(grid)result.grid=RecoveredTaiwanMapCell::Buffer{grid->address,grid->bytes};
    if(cells)result.cells=RecoveredTaiwanMapCell::Buffer{cells->address,cells->bytes};
    return result;
}
SharedTaiwanNativeMovementScene::Native::Native(Resources images,RecoveredPosition position,
    std::uint8_t direction,ResourceCurrent observe)
    :resources(std::move(images)),actual_position(position),actual_direction(direction),current(std::move(observe)) {
    if(!current || actual_direction>7 || !resources.actual_resource_generation ||
       !resources.actual_initial_scene_generation || !resources.complete())
        throw std::invalid_argument("TW native movement scene requires complete actual buffers/generations/direction/Current");
}
SharedTaiwanNativeMovementScene::Permit::Permit(std::vector<std::uint8_t> ack,
    std::function<bool(const Candidate&)> observe,
    std::function<bool(const SharedTaiwanMovement::Committed&)> publish)
    :full_native_ack(std::move(ack)),current(std::move(observe)),publish_authority(std::move(publish)) {
    if(!RecoveredNativeMovement::read_ack(full_native_ack) || !current || !publish_authority)
        throw std::invalid_argument("TW native movement permit requires full native5D and actual ticket/publication");
}
SharedTaiwanNativeMovementScene::Material::Material(Native native,std::shared_ptr<Authority> owner)
    :scene(std::move(native)),authority(std::move(owner)) {
    if(!authority)throw std::invalid_argument("TW native scene material requires actual authority");
}
SharedTaiwanMovementSource::Factory SharedTaiwanNativeMovementScene::factory(
    std::shared_ptr<SharedWorldPresence> presence,MaterialSource source) {
    if(!presence || !source)throw std::invalid_argument("TW native scene factory requires real presence/material supplier");
    auto state=std::make_shared<NativeFactoryOwner>();state->presence=std::move(presence);state->source=std::move(source);
    return [state](Session& session,const Lease& lease)->std::shared_ptr<SharedTaiwanMovement::WorldOwner> {
        if(state->thread!=std::this_thread::get_id())throw std::logic_error("TW native scene factory game owner mismatch");
        if(state->busy) {state->reentered=true;throw std::logic_error("TW native scene factory callback reentered");}
        state->busy=true;state->reentered=false;
        struct End {NativeFactoryOwner& state;~End(){state.busy=false;}} end{*state};
        if(!state->bound(session,lease))return {};
        const auto saved=state->presence->saved_position(lease);
        if(!saved)return {};
        const FactoryScope expected{lease,*saved};
        if(!state->current(session,expected))return {};
        const auto connection=session.shared_from_this();const auto supply=state->source;
        auto material=supply(session,expected);
        if(!material || !state->current(session,expected) || material->scene.actual_position!=expected.saved_position)return {};
        auto result=adopt(connection,state->presence,lease,std::move(material->scene),std::move(material->authority));
        return result && state->current(session,expected)?result:std::shared_ptr<SharedTaiwanMovement::WorldOwner>{};
    };
}
struct SharedTaiwanNativeMovementScene::Operation {
    SharedTaiwanNativeMovementScene& scene;
    explicit Operation(SharedTaiwanNativeMovementScene& value):scene(value) {
        scene.owner();
        if(scene.busy_) {
            scene.failed_=true;
            throw std::logic_error("TW native movement scene callback reentered");
        }
        scene.busy_=true;
    }
    ~Operation() {scene.busy_=false;}
};
SharedTaiwanNativeMovementScene::SharedTaiwanNativeMovementScene(const std::shared_ptr<Session>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,Native native,std::shared_ptr<Authority> authority)
    :connection_(connection),presence_(std::move(presence)),lease_(lease),native_(std::move(native)),
     authority_(std::move(authority)),position_(native_.actual_position),direction_(native_.actual_direction),
     publication_revision_(native_.resources.actual_initial_scene_generation){}
SharedTaiwanNativeMovementScene::~SharedTaiwanNativeMovementScene() {
    if(thread_!=std::this_thread::get_id())std::terminate();
    failed_=true;busy_=true;
    pending_.reset();probe_.reset();authority_.reset();native_.current={};
}
void SharedTaiwanNativeMovementScene::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("TW native movement scene game owner mismatch");
}
bool SharedTaiwanNativeMovementScene::bound() const {
    const auto session=connection_.lock();
    if(failed_ || !session || position_.area!=lease_.position.area || position_.scene!=lease_.position.scene ||
       session->closing() || session->id()!=lease_.session ||
       session->account_id!=lease_.account || session->character_id!=lease_.character ||
       !session->recovered_world_ready() || session->state()!=SessionState::InWorld ||
       !session->common_world_delivery_current(lease_.account,lease_.character,lease_.generation) ||
       session->common_world_entry_current(lease_.account,lease_.character,lease_.generation))return false;
    const auto actual=presence_->ready_lease(lease_.session,lease_.account,lease_.character);
    return actual && *actual==lease_;
}
SharedTaiwanNativeMovementScene::Scope SharedTaiwanNativeMovementScene::scope() const {
    return {lease_,position_,direction_,publication_revision_};
}
bool SharedTaiwanNativeMovementScene::resources_current(Check check) {
    if(!bound() || !native_.resources.complete())return false;
    const auto observe=native_.current;const auto expected=scope();
    if(!observe(check,expected,native_.resources) || !bound() || position_!=expected.position ||
       direction_!=expected.direction || publication_revision_!=expected.publication_revision) {
        failed_=true;return false;
    }
    return true;
}
bool SharedTaiwanNativeMovementScene::saved_current() const {
    if(!bound())return false;
    const auto saved=presence_->saved_position(lease_);
    return saved && *saved==position_;
}
bool SharedTaiwanNativeMovementScene::same_request(const RecoveredMovement::Request& a,
    const RecoveredMovement::Request& b) {
    return a.x==b.x && a.y==b.y && a.sequence==b.sequence && a.opaque_tail==b.opaque_tail;
}
bool SharedTaiwanNativeMovementScene::same_step(const TaiwanMovementRules::Step& a,
    const TaiwanMovementRules::Step& b) {
    return same_request(a.request,b.request) && a.direction==b.direction && a.native_cell==b.native_cell;
}
bool SharedTaiwanNativeMovementScene::snapshot_current(const Lease& lease,
    const SharedTaiwanMovement::Scene& snapshot) const {
    if(lease!=lease_ || !probe_ || !bound() || snapshot.area!=position_.area || snapshot.scene!=position_.scene ||
       snapshot.revision!=publication_revision_ || snapshot.previous_direction!=direction_ ||
       snapshot.native_cell!=probe_->scene.native_cell)return false;
    const auto cell=native_.resources.read(probe_->request.x,probe_->request.y);
    return cell && *cell==snapshot.native_cell;
}
bool SharedTaiwanNativeMovementScene::ticket_current(Check check) {
    if(!pending_ || !bound())return false;
    const auto observe=pending_->permit.current;const auto candidate=pending_->candidate;
    if(!observe(candidate) || !bound() || !pending_ || !same_step(pending_->candidate.step,candidate.step) ||
       pending_->candidate.owner.position!=candidate.owner.position ||
       pending_->candidate.owner.publication_revision!=candidate.owner.publication_revision ||
       !resources_current(check)) {failed_=true;return false;}
    return true;
}
std::shared_ptr<SharedTaiwanNativeMovementScene> SharedTaiwanNativeMovementScene::adopt(
    const std::shared_ptr<Session>& session,std::shared_ptr<SharedWorldPresence> presence,
    const Lease& lease,Native native,std::shared_ptr<Authority> authority) {
    if(!session || !presence || !authority || native.actual_direction>7 || !native.current ||
       !native.resources.actual_resource_generation || !native.resources.actual_initial_scene_generation ||
       !native.resources.complete())return {};
    auto result=std::shared_ptr<SharedTaiwanNativeMovementScene>(new SharedTaiwanNativeMovementScene(
        session,std::move(presence),lease,std::move(native),std::move(authority)));
    Operation operation(*result);
    if(!result->bound() || !result->saved_current() || !result->resources_current(Check::Adopt) ||
       !result->saved_current())return {};
    return result;
}
std::optional<SharedTaiwanMovement::Scene> SharedTaiwanNativeMovementScene::scene(const Lease& lease,
    const RecoveredPosition& before,const RecoveredMovement::Request& request) {
    Operation operation(*this);
    try {
        if(lease!=lease_ || pending_ || before!=position_ || !saved_current() ||
           !resources_current(Check::Scene) || !saved_current())return std::nullopt;
        const auto cell=native_.resources.read(request.x,request.y);
        if(!cell)return std::nullopt;
        SharedTaiwanMovement::Scene snapshot{position_.area,position_.scene,publication_revision_,direction_,*cell};
        probe_=Probe{request,snapshot};return snapshot;
    }catch(...) {failed_=true;throw;}
}
bool SharedTaiwanNativeMovementScene::current(const Lease& lease,const SharedTaiwanMovement::Scene& snapshot) {
    Operation operation(*this);
    try {
        if(!snapshot_current(lease,snapshot) || !saved_current() || !resources_current(Check::Current) ||
           !snapshot_current(lease,snapshot) || !saved_current())return false;
        return !pending_ || (ticket_current(Check::Current) && snapshot_current(lease,snapshot) && saved_current());
    }catch(...) {failed_=true;throw;}
}
std::optional<SharedTaiwanMovement::Authorization> SharedTaiwanNativeMovementScene::authorize(const Lease& lease,
    const RecoveredPosition& before,const SharedTaiwanMovement::Scene& snapshot,const TaiwanMovementRules::Step& step) {
    Operation operation(*this);
    try {
        if(pending_ || !probe_ || before!=position_ || !snapshot_current(lease,snapshot) || !saved_current() ||
           !same_request(step.request,probe_->request) || step.direction>7 || !step.native_cell ||
           step.native_cell!=snapshot.native_cell || !RecoveredNativeMovement::ordinary_request(step.request) ||
           publication_revision_==std::numeric_limits<std::uint64_t>::max() ||
           !resources_current(Check::Authorize) || !snapshot_current(lease,snapshot) || !saved_current())return std::nullopt;
        const auto dx=int(step.request.x)-before.x,dy=int(step.request.y)-before.y;
        if(dx< -1 || dx>1 || dy< -1 || dy>1)return std::nullopt;
        Candidate candidate{scope(),native_.resources.actual_resource_generation,
            native_.resources.actual_initial_scene_generation,step,native_.resources.cell_source()};
        const auto authority=authority_;auto permit=authority->authorize(candidate);
        if(!permit || !permit->current || !permit->publish_authority ||
           !RecoveredNativeMovement::read_ack(permit->full_native_ack) ||
           !snapshot_current(lease,snapshot) || !saved_current() || !resources_current(Check::Authorize) ||
           !snapshot_current(lease,snapshot) || !saved_current())return std::nullopt;
        // Complete real reply allocation and actual ticket preparation precede
        // the caller's sole common position CAS. No request-index echo builder.
        SharedTaiwanMovement::Authorization output{permit->full_native_ack};
        pending_.emplace(Pending{candidate,std::move(*permit)});
        if(!ticket_current(Check::Authorize) || !snapshot_current(lease,snapshot) || !saved_current()) {
            pending_.reset();return std::nullopt;
        }
        return output;
    }catch(...) {failed_=true;pending_.reset();throw;}
}
bool SharedTaiwanNativeMovementScene::publish(const Lease& lease,const SharedTaiwanMovement::Scene& snapshot,
    const SharedTaiwanMovement::Committed& committed) {
    Operation operation(*this);
    try {
        if(!pending_ || !snapshot_current(lease,snapshot) || committed.before!=position_ ||
           pending_->candidate.owner.position!=position_ || pending_->candidate.owner.publication_revision!=publication_revision_ ||
           !same_step(pending_->candidate.step,committed.step) || committed.after.area!=position_.area ||
           committed.after.scene!=position_.scene || committed.after.x!=committed.step.request.x ||
           committed.after.y!=committed.step.request.y || committed.after.revision<=position_.revision ||
           publication_revision_==std::numeric_limits<std::uint64_t>::max()) {failed_=true;return false;}
        const auto saved=presence_->saved_position(lease_);
        // Ticket/resource qualification intentionally observes the actor's
        // before scope while the single common DB CAS is already at after.
        if(!saved || *saved!=committed.after || !resources_current(Check::BeforePublish) ||
           !snapshot_current(lease,snapshot) || !ticket_current(Check::BeforePublish) ||
           !snapshot_current(lease,snapshot)) {failed_=true;return false;}
        const auto rechecked=presence_->saved_position(lease_);
        if(!rechecked || *rechecked!=committed.after) {failed_=true;return false;}
        auto prepared=std::move(*pending_);pending_.reset();probe_.reset(); // One use, before actual callback.
        position_=committed.after;direction_=committed.step.direction;
        ++publication_revision_; // Private publication incarnation, not a native counter.
        if(!prepared.permit.publish_authority(committed) || !resources_current(Check::AfterPublish) ||
           !saved_current()) {failed_=true;return false;}
        return true;
    }catch(...) {failed_=true;pending_.reset();probe_.reset();throw;}
}
}
