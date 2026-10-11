#include "cn/world/SharedMovement.h"
#include <stdexcept>
#include <utility>

namespace god2::cn {
SharedMovement::SharedMovement(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,
    god2cn::CnMovementRules& rules,std::shared_ptr<SharedActorVisibility> visibility,WorldOwner& world)
    :connection_(connection),presence_(std::move(presence)),lease_(lease),rules_(rules),world_(world),
     visibility_(std::move(visibility)),publication_(presence_,visibility_) {}
void SharedMovement::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN movement game owner mismatch");
}
bool SharedMovement::current() const {
    const auto connection=connection_.lock();
    return connection && !connection->closing() && connection->world_session_id()==lease_.session &&
        connection->verified_account_id()==lease_.account && connection->world_character_offered(lease_.character) &&
        presence_->ready(lease_);
}
std::shared_ptr<SharedMovement> SharedMovement::attach(const std::shared_ptr<Connection>& connection,
    std::shared_ptr<SharedWorldPresence> presence,const Lease& lease,
    god2cn::CnMovementRules& rules,std::shared_ptr<SharedActorVisibility> visibility,WorldOwner& world) {
    if(!connection || !presence || !visibility || !visibility->owns_presence(presence))return {};
    auto result=std::shared_ptr<SharedMovement>(new SharedMovement(connection,std::move(presence),lease,rules,
        std::move(visibility),world));
    result->owner();return result->current()?result:std::shared_ptr<SharedMovement>{};
}
SharedMovement::Connection::Ingress SharedMovement::ingress() {
    owner();return [self=shared_from_this()](god2cn::Bytes records,Connection::Transport::Completion done) {
        self->receive(std::move(records),std::move(done));
    };
}
bool SharedMovement::move(std::span<const std::uint8_t> record) {
    if(!current())return false;
    const auto saved=presence_->saved_position(lease_);
    if(!saved)return false;
    const auto scene=world_.scene(lease_,*saved);
    if(!scene || scene->area!=saved->area || scene->scene!=saved->scene || !scene->revision ||
       scene->previous_direction>7 || !world_.current(lease_,*scene))return false;
    const bool mode0=scene->mode==0 && scene->cells.mode()==god2cn::CnMapPassability::Mode::window0;
    const bool mode2=scene->mode==2 && scene->cells.mode()==god2cn::CnMapPassability::Mode::grid2;
    if(!mode0 && !mode2)return false; // Other native map branches stay open.
    const auto step=rules_.prepare_native_map_step(record,{saved->x,saved->y},scene->previous_direction,scene->cells);
    if(!step)return false;
    auto authorization=world_.authorize(lease_,*saved,*scene,*step);
    if(!authorization || !god2cn::CnMovement::read_step_ack(authorization->native_ack))return false;
    auto publication=publication_.prepare(lease_,*saved,step->step.destination.x,step->step.destination.y);
    if(!publication)return false;
    // Authority callbacks run on this same game owner, but may change state.
    // Recheck connection, actual actor/scene and saved revision before any write.
    if(!current() || !world_.current(lease_,*scene) || !publication_.current(*publication))return false;
    const auto committed=presence_->commit_owned_step(lease_,*saved,step->step.destination.x,step->step.destination.y);
    if(!committed)return false;
    if(!world_.publish(lease_,*scene,Committed{*saved,*committed,*step}))return false;
    if(!publication_.deliver(*publication,*committed))return false;
    const auto connection=connection_.lock();
    if(!connection || !current())return false;
    connection->send(std::move(authorization->native_ack));return !connection->closing();
}
void SharedMovement::receive(god2cn::Bytes records,Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN movement completion required");
    bool accepted=false;
    try {
        const auto process=[&] {
            if(records.empty() || records.size()>god2cn::CnTransport::max_logical || records.size()%7)return false;
            // Format-qualify the whole run before the first individual movement
            // transaction. Permission/publication remains per actual step.
            const auto bytes=std::span<const std::uint8_t>(records);
            for(std::size_t offset=0;offset<records.size();offset+=7)
                if(!god2cn::CnMovement::parse_step(bytes.subspan(offset,7)))return false;
            for(std::size_t offset=0;offset<records.size();offset+=7)
                if(!move(bytes.subspan(offset,7)))return false;
            return true;
        };
        accepted=process();
    }catch(...) {accepted=false;}
    if(!accepted) {
        // A committed position is retained if later publication/output fails.
        // Do not rewind an authorized move after any peers could observe it.
        // Actual recovery must re-load saved state at next owned entry.
        visibility_->release(lease_);presence_->release(lease_);
        if(const auto connection=connection_.lock())connection->close();
    }
    done(accepted); // Source queue acceptance, not native rendered acceptance.
}
}
