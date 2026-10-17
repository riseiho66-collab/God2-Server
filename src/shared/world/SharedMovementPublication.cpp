#include "shared/world/SharedMovementPublication.h"
#include <set>
#include <stdexcept>
#include <type_traits>
#include <utility>

namespace god2::shared {
SharedMovementPublication::SharedMovementPublication(std::shared_ptr<SharedWorldPresence> presence,
    std::shared_ptr<SharedActorVisibility> visibility)
    :presence_(std::move(presence)),visibility_(std::move(visibility)) {
    if(!presence_ || !visibility_ || !visibility_->owns_presence(presence_))
        throw std::invalid_argument("Shared movement publication requires matching presence/visibility owners");
}
SharedMovementPublication::Prepared::Prepared(std::shared_ptr<const Identity> identity,Lease source,
    RecoveredPosition before,std::uint16_t x,std::uint16_t y,std::vector<SharedActorVisibility::Binding> bindings,
    std::vector<Delivery> deliveries)
    :identity_(std::move(identity)),source_(source),before_(before),x_(x),y_(y),bindings_(std::move(bindings)),
     deliveries_(std::move(deliveries)){}
void SharedMovementPublication::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("Shared movement publication game owner mismatch");
}
bool SharedMovementPublication::bound(const Recipient& recipient,const RecoveredPosition& source) const {
    if(!presence_->ready(recipient.lease))return false;
    const auto saved=presence_->saved_position(recipient.lease);
    if(!saved || saved->area!=source.area || saved->scene!=source.scene)return false;
    return std::visit([&](const auto& output) {
        const auto connection=output.connection.lock();
        if(!connection)return false;
        using Output=std::decay_t<decltype(output)>;
        return !connection->closing() && connection->id()==recipient.lease.session &&
                connection->account_id==recipient.lease.account && connection->character_id==recipient.lease.character &&
                connection->recovered_world_ready() && (connection->state()==SessionState::InWorld ||
                    connection->state()==SessionState::CharacterSelected);
    },recipient.output);
}
std::optional<SharedMovementPublication::Prepared> SharedMovementPublication::prepare(
    const Lease& source,const RecoveredPosition& before,std::uint16_t x,std::uint16_t y) const {
    owner();
    const auto saved=presence_->saved_position(source);
    if(!saved || *saved!=before || x>0x7ff || y>0x7ff)return std::nullopt;
    const auto dx=int(x)-before.x,dy=int(y)-before.y;
    if(dx< -1 || dx>1 || dy< -1 || dy>1)return std::nullopt;
    auto bindings=visibility_->movement_bindings(source,before);
    if(!bindings)return std::nullopt;
    std::set<std::uint64_t> unique;
    std::vector<Prepared::Delivery> deliveries;
    deliveries.reserve(bindings->size());
    for(const auto& binding:*bindings) {
        if(binding.source()!=source)return std::nullopt;
        const auto resolved=visibility_->movement(binding,before);
        if(!resolved)return std::nullopt;
        const auto& recipient=*resolved;
        if(recipient.lease.session==source.session || recipient.lease.character==source.character ||
           !unique.insert(recipient.lease.session).second || !bound(recipient,before))return std::nullopt;
        auto bytes=std::visit([&](const auto& output)->std::optional<std::vector<std::uint8_t>> {
            const auto& actual=output.actual_visible_actor;
            if(actual.identity()!=source.actor_handle || actual.x()!=before.x || actual.y()!=before.y)
                return std::nullopt; // No character-ID truncation, stale template or synthesized actor.
            using Output=std::decay_t<decltype(output)>;
            {
                if(source.actor_handle>0xfff)return std::nullopt; // TW native spawn's narrower identity.
                const auto projected=RecoveredRemoteActorMove::with_position(actual,x,y);
                if(!projected)return std::nullopt;
                const auto record=RecoveredRemoteActorMove::encode_logical(*projected);
                return std::vector<std::uint8_t>(record.begin(),record.end());
            }
        },recipient.output);
        if(!bytes)return std::nullopt;
        deliveries.push_back({binding,recipient,std::move(*bytes)});
    }
    Prepared prepared(identity_,source,before,x,y,std::move(*bindings),std::move(deliveries));
    if(!current(prepared))return std::nullopt;
    return prepared;
}
bool SharedMovementPublication::current(const Prepared& prepared) const {
    owner();
    if(prepared.consumed_ || prepared.identity_!=identity_)return false;
    const auto saved=presence_->saved_position(prepared.source_);
    if(!saved || *saved!=prepared.before_)return false;
    if(!visibility_->complete_movement_set(prepared.source_,prepared.before_,prepared.before_,prepared.bindings_))return false;
    for(const auto& delivery:prepared.deliveries_)
        if(!bound(delivery.recipient,prepared.before_) ||
           !visibility_->current(delivery.binding,prepared.before_,prepared.before_))return false;
    return true;
}
bool SharedMovementPublication::deliver(Prepared& prepared,const RecoveredPosition& after) {
    owner();
    if(prepared.consumed_ || prepared.identity_!=identity_)return false;
    prepared.consumed_=true; // Never retry a partly queued publication.
    if(after.area!=prepared.before_.area || after.scene!=prepared.before_.scene ||
       after.x!=prepared.x_ || after.y!=prepared.y_ || after.revision<=prepared.before_.revision)return false;
    const auto saved=presence_->saved_position(prepared.source_);
    if(!saved || *saved!=after)return false;
    if(!visibility_->complete_movement_set(prepared.source_,prepared.before_,after,prepared.bindings_))return false;
    // Qualify every actual recipient before the first queue write. Per-recipient
    // advance may invoke observers between sends; this is not atomic fanout.
    // A rejected suffix never retries or rolls back the already submitted prefix.
    for(const auto& delivery:prepared.deliveries_)
        if(!bound(delivery.recipient,after) || !visibility_->current(delivery.binding,prepared.before_,after))return false;
    for(auto& delivery:prepared.deliveries_) {
        const bool submitted=std::visit([&](const auto& output) {
            const auto connection=output.connection.lock();
            if(!connection)return false;
            using Output=std::decay_t<decltype(output)>;
            {
                if(connection->closing())return false;
                connection->send_world_records(std::move(delivery.bytes));
                return !connection->closing() && connection->recovered_world_ready() &&
                    connection->state()!=SessionState::Disconnected;
            }
        },delivery.recipient.output);
        if(!submitted)return false;
        if(!visibility_->advance(delivery.binding,prepared.before_,after))return false;
    }
    return true;
}
}
