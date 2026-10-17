#include "game/SharedTaiwanMovement.h"
#include "db/SqliteOwnedEquipmentTransaction.h"
#include <exception>
#include <stdexcept>
#include <utility>

namespace god2 {
SharedTaiwanMovement::SharedTaiwanMovement(const std::shared_ptr<Session>& session,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,TaiwanMovementRules& rules,
    std::shared_ptr<shared::SharedActorVisibility> visibility,WorldOwner& world)
    :connection_(session),presence_(std::move(presence)),lease_(lease),rules_(rules),visibility_(std::move(visibility)),
     publication_(presence_,visibility_),world_(world){}
SharedTaiwanMovement::SharedTaiwanMovement(const std::shared_ptr<Session>& session,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,std::shared_ptr<TaiwanMovementRules> rules,
    std::shared_ptr<shared::SharedActorVisibility> visibility,std::shared_ptr<WorldOwner> world,
    std::shared_ptr<SqliteOwnedEquipmentTransaction> movement_custody)
    :connection_(session),presence_(std::move(presence)),lease_(lease),rules_owner_(std::move(rules)),
     rules_(*rules_owner_),visibility_(std::move(visibility)),publication_(presence_,visibility_),
     world_owner_(std::move(world)),world_(*world_owner_),movement_custody_(std::move(movement_custody)){}
SharedTaiwanMovement::~SharedTaiwanMovement() {
    // Only the new strong-owned path imposes destruction affinity. Existing
    // borrowed controllers retain their previous destruction behavior.
    if(rules_owner_ && thread_!=std::this_thread::get_id())std::terminate();
}
void SharedTaiwanMovement::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("TW common movement game owner mismatch");
}
bool SharedTaiwanMovement::current(Session& session) const {
    if(rules_owner_ && (owned_reentered_ ||
       !session.common_world_delivery_current(lease_.account,lease_.character,lease_.generation) ||
       session.common_world_entry_current(lease_.account,lease_.character,lease_.generation)))return false;
    return connection_.lock().get()==&session && !session.closing() && session.recovered_world_ready() &&
        session.state()==SessionState::InWorld && session.id()==lease_.session &&
        session.account_id==lease_.account && session.character_id==lease_.character && presence_->ready(lease_);
}
std::shared_ptr<SharedTaiwanMovement> SharedTaiwanMovement::attach(const std::shared_ptr<Session>& session,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,TaiwanMovementRules& rules,
    std::shared_ptr<shared::SharedActorVisibility> visibility,WorldOwner& world) {
    if(!session || !presence || !visibility || !visibility->owns_presence(presence))return {};
    auto result=std::shared_ptr<SharedTaiwanMovement>(new SharedTaiwanMovement(session,std::move(presence),lease,
        rules,std::move(visibility),world));
    result->owner();return result->current(*session)?result:std::shared_ptr<SharedTaiwanMovement>{};
}
std::shared_ptr<SharedTaiwanMovement> SharedTaiwanMovement::attach(const std::shared_ptr<Session>& session,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,std::shared_ptr<TaiwanMovementRules> rules,
    std::shared_ptr<shared::SharedActorVisibility> visibility,std::shared_ptr<WorldOwner> world,
    std::shared_ptr<SqliteOwnedEquipmentTransaction> movement_custody) {
    if(!session || !presence || !visibility || !rules || !world || !visibility->owns_presence(presence))return {};
    if(movement_custody && !presence->owns_repository(movement_custody->characters_repository()))return {};
    const auto active=presence->ready_lease(session->id(),session->account_id,session->character_id);
    if(!active || *active!=lease ||
       !session->common_world_delivery_current(lease.account,lease.character,lease.generation) ||
       session->common_world_entry_current(lease.account,lease.character,lease.generation))return {};
    auto result=std::shared_ptr<SharedTaiwanMovement>(new SharedTaiwanMovement(session,std::move(presence),lease,
        std::move(rules),std::move(visibility),std::move(world),std::move(movement_custody)));
    result->owner();return result->current(*session)?result:std::shared_ptr<SharedTaiwanMovement>{};
}
bool SharedTaiwanMovement::scene_current_owned(Session& session,const Scene& scene) {
    if(!current(session))return false;
    const auto accepted=world_.current(lease_,scene);
    // A real callback can reenter or invalidate the lease even if it returns
    // true; its result alone cannot authorize the next mutation/publication.
    return accepted && current(session);
}
std::optional<std::vector<std::uint8_t>> SharedTaiwanMovement::move_owned(Session& session,
    const RecoveredMovement::Request& request) {
    if(!current(session))return std::nullopt;
    const auto before=presence_->saved_position(lease_);
    if(!before)return std::nullopt;
    const auto scene=world_.scene(lease_,*before,request);
    if(!current(session) || !scene || scene->area!=before->area || scene->scene!=before->scene || !scene->revision ||
       scene->previous_direction>7 || !scene_current_owned(session,*scene))return std::nullopt;
    const auto step=rules_.prepare(request,*before,scene->previous_direction,scene->native_cell);
    if(!step || !current(session))return std::nullopt;
    const auto authorization=world_.authorize(lease_,*before,*scene,*step);
    if(!authorization || !scene_current_owned(session,*scene))return std::nullopt;
    const auto ack=RecoveredNativeMovement::read_ack(authorization->full_native_ack);
    if(!ack)return std::nullopt;
    auto framed=RecoveredWorldFrame::encode(ack->logical());
    // CUSTOM-0150 sender custody only: allocate the private exact step before
    // any position CAS. This records supplied5D, not a recovered native ACK rule.
    std::optional<Session::MovementStepWrite> sender_write;
    if(session.native_movement_response_custody_enabled()) {
        sender_write=session.prepare_movement_response_write(lease_,*before,request,
            step->direction,step->native_cell,scene->revision,authorization->full_native_ack,framed);
        if(!sender_write)return std::nullopt;
    }
    auto peers=publication_.prepare(lease_,*before,request.x,request.y);
    if(!peers || !scene_current_owned(session,*scene) || !publication_.current(*peers))return std::nullopt;
    std::optional<RecoveredPosition> after;
    if(movement_custody_) {
        // CUSTOM-0095 retains the actual complete material while the position
        // advances in the same outer transaction. No missing/stale witness is
        // repaired by rebasing metadata, and this opt-in never falls back.
        if(!presence_->owns_repository(movement_custody_->characters_repository()))return std::nullopt;
        const auto custody_before=movement_custody_->observe_before(lease_.account,lease_.character);
        if(!custody_before || !custody_before->inventory || !custody_before->equipment ||
           custody_before->inventory->root.account_id!=lease_.account ||
           custody_before->inventory->root.id!=lease_.character ||
           !NativeEquipmentSnapshot::same_root(custody_before->inventory->root,custody_before->equipment->root) ||
           custody_before->equipment->actor_handle!=lease_.actor_handle ||
           custody_before->equipment->position!=*before || !current(session))return std::nullopt;
        const auto authority_current=[&] {
            if(!current(session) || !scene_current_owned(session,*scene))return false;
            const bool peers_current=publication_.current(*peers);
            return peers_current && current(session) && scene_current_owned(session,*scene) && !owned_reentered_;
        };
        const auto committed=movement_custody_->move_position_from_current(*custody_before,
            lease_.actor_handle,request.x,request.y,authority_current);
        if(!committed)return std::nullopt;
        after=committed->equipment().snapshot().position;
        // The scene still has the old pose until publish below. Never invoke
        // its old-scene Current after SQL staging or roll back a durable prefix.
        if(!current(session) || !movement_custody_->committed_current(*committed) || !current(session) ||
           presence_->saved_position(lease_)!=after || !current(session) || owned_reentered_)return std::nullopt;
    }else {
        after=presence_->commit_owned_step(lease_,*before,request.x,request.y);
    }
    if(!after || !current(session) || (movement_custody_ && owned_reentered_))return std::nullopt;
    const auto published=world_.publish(lease_,*scene,Committed{*before,*after,*step});
    if(!published || !current(session) || (movement_custody_ && owned_reentered_))return std::nullopt;
    if(!publication_.deliver(*peers,*after) || !current(session) || (movement_custody_ && owned_reentered_))return std::nullopt;
    // Seal only this actual durable step after the real authority and peer
    // publication. Failure follows existing terminal cleanup; no position,
    // sequence or rate credit is rewound and no extra send/CAS is introduced.
    if(sender_write && !session.commit_movement_response_write(*sender_write,*after))return std::nullopt;
    return framed;
}
std::vector<std::uint8_t> SharedTaiwanMovement::handle_owned(Session& session,
    std::span<const RecoveredMovement::Request> requests) {
    if(owned_handling_) {
        owned_reentered_=true;
        throw std::runtime_error("TW owned movement callback reentered");
    }
    owned_handling_=true;owned_reentered_=false;
    struct Handling {
        bool& active;
        ~Handling(){active=false;}
    } handling{owned_handling_};
    try {
        if(!current(session) || requests.empty() || requests.size()>RecoveredMovement::max_logical_size/7)
            throw std::runtime_error("TW owned movement batch/owner rejected");
        for(const auto& request:requests)
            if(!RecoveredNativeMovement::ordinary_request(request))throw std::runtime_error("TW native ring index out of range");
        std::vector<std::uint8_t> response;response.reserve(requests.size()*5);
        for(const auto& request:requests) {
            auto ack=move_owned(session,request);
            if(!ack)throw std::runtime_error("TW owned movement authority/publication rejected");
            response.insert(response.end(),ack->begin(),ack->end());
        }
        return response;
    }catch(...) {
        // Preserve committed prefixes. The strong suppliers stay alive while
        // cleanup unwinds; nested caught calls keep this batch poisoned.
        reject(session);throw;
    }
}
std::optional<std::vector<std::uint8_t>> SharedTaiwanMovement::move(Session& session,
    const RecoveredMovement::Request& request) {
    if(!current(session))return std::nullopt;
    const auto before=presence_->saved_position(lease_);
    if(!before)return std::nullopt;
    const auto scene=world_.scene(lease_,*before,request);
    if(!scene || scene->area!=before->area || scene->scene!=before->scene || !scene->revision ||
       scene->previous_direction>7 || !world_.current(lease_,*scene))return std::nullopt;
    const auto step=rules_.prepare(request,*before,scene->previous_direction,scene->native_cell);
    if(!step)return std::nullopt;
    const auto authorization=world_.authorize(lease_,*before,*scene,*step);
    if(!authorization)return std::nullopt;
    const auto ack=RecoveredNativeMovement::read_ack(authorization->full_native_ack);
    if(!ack)return std::nullopt;
    // Actual full supplied ack is framed and allocated before the durable CAS.
    // No index echo or use of the frozen candidate ack() convenience serializer.
    auto framed=RecoveredWorldFrame::encode(ack->logical());
    auto peers=publication_.prepare(lease_,*before,request.x,request.y);
    if(!peers || !current(session) || !world_.current(lease_,*scene) || !publication_.current(*peers))return std::nullopt;
    const auto after=presence_->commit_owned_step(lease_,*before,request.x,request.y);
    if(!after)return std::nullopt;
    if(!world_.publish(lease_,*scene,Committed{*before,*after,*step}) ||
       !publication_.deliver(*peers,*after) || !current(session))return std::nullopt;
    return framed;
}
void SharedTaiwanMovement::reject(Session& session) {
    // Only this actual connection may be closed. Lease release itself is exact
    // generation-qualified; foreign/stale calls cannot evict successor leases.
    if(connection_.lock().get()!=&session || session.id()!=lease_.session ||
       session.account_id!=lease_.account || session.character_id!=lease_.character)return;
    if(!presence_->current(lease_))return; // A successor on this socket is not ours to close.
    std::exception_ptr failure;
    try {visibility_->release(lease_);}catch(...){failure=std::current_exception();}
    try {presence_->release(lease_);}catch(...){if(!failure)failure=std::current_exception();}
    session.close();if(failure)std::rethrow_exception(failure);
}
std::vector<std::uint8_t> SharedTaiwanMovement::handle(Session& session,
    std::span<const RecoveredMovement::Request> requests) {
    owner();
    if(rules_owner_)return handle_owned(session,requests);
    try {
        if(!current(session) || requests.empty() || requests.size()>RecoveredMovement::max_logical_size/7)
            throw std::runtime_error("TW ordinary movement batch/owner rejected");
        // Qualify all formats before the first per-step authority transaction.
        for(const auto& request:requests)
            if(!RecoveredNativeMovement::ordinary_request(request))throw std::runtime_error("TW native ring index out of range");
        std::vector<std::uint8_t> response;response.reserve(requests.size()*5);
        for(const auto& request:requests) {
            auto ack=move(session,request);
            if(!ack)throw std::runtime_error("TW common movement authority/publication rejected");
            response.insert(response.end(),ack->begin(),ack->end());
        }
        return response; // Actual Session later enqueues; no native receipt claim.
    }catch(...) {
        // A committed prefix stays durable even if a later step/output fails.
        // Reentry reloads saved state; never rewind a move peers may have seen.
        reject(session);throw;
    }
}
}
