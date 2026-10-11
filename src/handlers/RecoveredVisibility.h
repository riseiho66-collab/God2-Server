#pragma once
#include "protocol/RecoveredRemoteActor.h"
#include "protocol/RecoveredRemoteRoleText.h"
#include "protocol/RecoveredCharacterPose.h"
#include <map>
#include <optional>
#include <stdexcept>
#include <type_traits>
#include <vector>

namespace god2 {
// CUSTOM-0027: same-scene visibility policy, serial game executor only.
// Callers authorize ownership/readiness and deliver every returned logical record.
// No identity allocation, appearance fabrication, socket write or DB mutation.
class RecoveredVisibility {
public:
    struct Scene {
        std::uint16_t area,scene;
        bool operator==(const Scene&) const = default;
    };
    struct Presence {
        std::uint64_t session,account,character;
        Scene location;
        RecoveredRemoteActor::Record spawn;
        RecoveredRemoteActorRemove::Record departure;
        std::optional<std::array<std::uint8_t,3>> pose{};
    };
    struct Delivery {
        std::uint64_t recipient;
        std::vector<std::uint8_t> logical;
    };
    static constexpr std::size_t remote_capacity=128;
    static constexpr bool production_enabled=false;

    std::vector<Delivery> enter(const Presence& incoming) {
        const auto visible=validate_entry(incoming);
        std::vector<Delivery> deliveries;
        deliveries.reserve(visible*2);
        for(const auto& [session,peer]:members_) if(peer.location==incoming.location) {
            const auto other=RecoveredRemoteActor::encode_logical(peer.spawn);
            const auto added=RecoveredRemoteActor::encode_logical(incoming.spawn);
            deliveries.push_back({incoming.session,{other.begin(),other.end()}});
            deliveries.push_back({session,{added.begin(),added.end()}});
        }
        // All validation and delivery allocations precede membership mutation.
        members_.emplace(incoming.session,incoming);
        return deliveries;
    }

    std::vector<Delivery> leave(std::uint64_t session) {
        const auto found=members_.find(session);
        if(found==members_.end()) return {};
        const auto removal=RecoveredRemoteActorRemove::encode_logical(found->second.departure);
        std::vector<Delivery> deliveries;
        for(const auto& [other,peer]:members_)
            if(other!=session && peer.location==found->second.location)
                deliveries.push_back({other,{removal.begin(),removal.end()}});
        members_.erase(found);
        return deliveries;
    }

    std::size_t size() const noexcept { return members_.size(); }
    bool contains(std::uint64_t session) const noexcept { return members_.contains(session); }
    std::optional<Presence> snapshot(std::uint64_t session) const {
        const auto found=members_.find(session);
        return found==members_.end()?std::nullopt:std::optional<Presence>{found->second};
    }
    std::optional<Presence> snapshot_character(std::uint64_t character) const {
        for(const auto& [session,member]:members_)
            if(member.character==character)return member;
        return std::nullopt;
    }

    struct AppearancePlan {
        Presence before,after;
        std::vector<Delivery> deliveries;
    };
    // Native77/4FB980, routed by existing CUSTOM-0027 same-scene ownership.
    // Transient display only; never store poses in account/character saves.
    std::vector<Delivery> set_pose(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,Scene scene,const std::array<std::uint8_t,3>& payload) {
        const auto found=members_.find(session);
        if(found==members_.end() || found->second.account!=account ||
           found->second.character!=character || found->second.location!=scene)
            throw std::invalid_argument("Visibility pose binding rejected");
        const auto logical=RecoveredCharacterPose::logical(found->second.spawn.identity(),payload);
        if(!logical)throw std::invalid_argument("Visibility pose unqualified");
        std::vector<Delivery> deliveries;
        for(const auto& [other,peer]:members_)
            if(other!=session && peer.location==scene)
                deliveries.push_back({other,{logical->begin(),logical->end()}});
        // Ignore the client's opaque tail. All allocations precede mutation.
        if(RecoveredCharacterPose::is_persistent_pose(payload))
            found->second.pose=std::array<std::uint8_t,3>{0,payload[1],0};
        else found->second.pose.reset();
        return deliveries;
    }
    // Native6F/4FC1C0 initializes actor+79 to zero. Replay77 after6F so
    // a new/returning observer sees the existing player's stationary pose.
    std::optional<RecoveredCharacterPose::LogicalRecord> pose_after_spawn(
        const RecoveredRemoteActor::Record& spawn) const {
        for(const auto& [session,member]:members_)
            if(member.spawn.identity()==spawn.identity() && member.pose)
                return RecoveredCharacterPose::logical(spawn.identity(),*member.pose);
        return std::nullopt;
    }
    // CUSTOM-0056: only the new secondary role text field changes. Native6F
    // replaces an existing peer and clears its interpolation queue; retain the
    // latest authoritative position/pose/appearance in the replacement record.
    AppearancePlan prepare_role_text(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,const RecoveredRoleText::Text& text) const {
        const auto found=members_.find(session);
        if(found==members_.end() || found->second.account!=account || found->second.character!=character)
            throw std::invalid_argument("Visibility role text owner rejected");
        const auto spawn=RecoveredRemoteRoleText::with_source_text(found->second.spawn,text);
        if(!spawn)throw std::invalid_argument("Visibility role text projection rejected");
        AppearancePlan plan{found->second,found->second,{}};
        plan.after.spawn=*spawn;
        const auto logical=RecoveredRemoteActor::encode_logical(*spawn);
        if(logical!=RecoveredRemoteActor::encode_logical(found->second.spawn))
            for(const auto& [other,peer]:members_)
                if(other!=session && peer.location==found->second.location)
                    plan.deliveries.push_back({other,{logical.begin(),logical.end()}});
        return plan;
    }
    // Prepare all validation and allocations inside the caller's DB transaction.
    // Serial executor applies the plan only after durable equipment commit.
    AppearancePlan prepare_appearance(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,const RecoveredPlayerAppearanceUpdate::Fields& fields) const {
        const auto found=members_.find(session);
        if(found==members_.end() || found->second.account!=account ||
           found->second.character!=character)
            throw std::invalid_argument("Visibility appearance binding rejected");
        const auto spawn=RecoveredRemoteActor::with_appearance(found->second.spawn,fields);
        if(!spawn)throw std::invalid_argument("Visibility appearance source rejected");
        AppearancePlan plan{found->second,found->second,{}};
        plan.after.spawn=*spawn;
        const auto logical=RecoveredPlayerAppearanceUpdate::encode(fields);
        for(const auto& [other,peer]:members_)
            if(other!=session && peer.location==found->second.location)
                plan.deliveries.push_back({other,{logical.begin(),logical.end()}});
        return plan;
    }
    void commit_appearance(const AppearancePlan& plan) noexcept {
        // No intervening membership mutation is allowed on the serial executor.
        const auto found=members_.find(plan.before.session);
        if(found==members_.end() || found->second.account!=plan.before.account ||
           found->second.character!=plan.before.character ||
           found->second.location!=plan.before.location ||
           RecoveredRemoteActor::encode_logical(found->second.spawn)!=
               RecoveredRemoteActor::encode_logical(plan.before.spawn))std::terminate();
        static_assert(std::is_nothrow_copy_assignable_v<Presence>);
        found->second=plan.after;
    }

    // CUSTOM-0027: rebuild a cleared native world display from current membership.
    // No join/leave mutation or broadcast back to the other players.
    std::vector<Delivery> refresh(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,Scene scene) const {
        const auto found=members_.find(session);
        if(found==members_.end() || found->second.account!=account ||
           found->second.character!=character || found->second.location!=scene)
            throw std::invalid_argument("Visibility refresh binding rejected");
        std::vector<Delivery> deliveries;
        for(const auto& [other,peer]:members_)
            if(other!=session && peer.location==scene) {
                const auto logical=RecoveredRemoteActor::encode_logical(peer.spawn);
                deliveries.push_back({session,{logical.begin(),logical.end()}});
            }
        return deliveries;
    }

    // CUSTOM-0027: caller authorizes the battle lifecycle; this only projects its
    // qualified title. No combat admission, settlement or database mutation here.
    std::vector<Delivery> set_fight_title(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,Scene scene,bool active) {
        const auto found=members_.find(session);
        if(found==members_.end() || found->second.account!=account ||
           found->second.character!=character || found->second.location!=scene)
            throw std::invalid_argument("Visibility title binding rejected");
        auto spawn=RecoveredRemoteActor::encode_logical(found->second.spawn);
        const auto previous=spawn[7]+256u*spawn[8];
        const auto x=found->second.spawn.x(),y=found->second.spawn.y();
        if(previous>1 || spawn[77] || spawn[78] || x>2047 || y>2047)
            throw std::invalid_argument("Visibility title source unqualified");
        if(previous==static_cast<unsigned>(active)) return {};
        RecoveredRemoteActorMove::LogicalRecord update{0x5e};
        const auto identity=found->second.spawn.identity();
        update[1]=static_cast<std::uint8_t>(identity);
        update[2]=static_cast<std::uint8_t>(identity>>8);
        update[5]=static_cast<std::uint8_t>(active);
        const std::uint32_t point=x|(std::uint32_t{y}<<11);
        for(unsigned i=0;i<4;++i) update[9+i]=static_cast<std::uint8_t>(point>>(8*i));
        spawn[7]=static_cast<std::uint8_t>(active);
        const auto changed=RecoveredRemoteActor::parse_logical(spawn).value();
        std::vector<Delivery> deliveries;
        for(const auto& [other,peer]:members_)
            if(other!=session && peer.location==scene)
                deliveries.push_back({other,{update.begin(),update.end()}});
        // Preserve the same title for later6F recipients; allocate before mutation.
        found->second.spawn=changed;
        found->second.pose.reset();
        return deliveries;
    }

    // CUSTOM-0027: only the qualified ordinary, state-preserving adjacent step.
    // Call after durable movement; this does not validate terrain or speed.
    std::vector<Delivery> move(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,Scene scene,const RecoveredRemoteActorMove::Record& movement) {
        return move_batch(session,account,character,scene,{&movement,1});
    }

    std::vector<Delivery> move_batch(std::uint64_t session,std::uint64_t account,
        std::uint64_t character,Scene scene,std::span<const RecoveredRemoteActorMove::Record> movements) {
        const auto found=members_.find(session);
        if(found==members_.end() || found->second.account!=account ||
           found->second.character!=character || found->second.location!=scene)
            throw std::invalid_argument("Visibility movement binding rejected");
        auto positioned=found->second.spawn;
        bool moved=false;
        const auto spawn=RecoveredRemoteActor::encode_logical(found->second.spawn);
        std::vector<Delivery> deliveries;
        for(const auto& movement:movements) {
            if(positioned.identity()!=movement.identity())
                throw std::invalid_argument("Visibility movement identity rejected");
            const auto logical=RecoveredRemoteActorMove::encode_logical(movement);
            if(spawn[77] || spawn[78] || movement.state()!=spawn[7]+256u*spawn[8] ||
               logical[3] || logical[4] || logical[7] || logical[8] || (logical[11]&0xc0) || logical[12])
                throw std::invalid_argument("Visibility movement appearance change unqualified");
            const int dx=static_cast<int>(movement.x())-positioned.x();
            const int dy=static_cast<int>(movement.y())-positioned.y();
            if(dx < -1 || dx>1 || dy < -1 || dy>1)
                throw std::invalid_argument("Visibility movement must retain every adjacent step");
            if(dx==0 && dy==0) continue;
            moved=true;
            positioned=RecoveredRemoteActor::with_position(positioned,movement.x(),movement.y()).value();
            for(const auto& [other,peer]:members_)
                if(other!=session && peer.location==scene)
                    deliveries.push_back({other,{logical.begin(),logical.end()}});
        }
        static_assert(std::is_nothrow_copy_assignable_v<RecoveredRemoteActor::Record>);
        if(moved)found->second.pose.reset();
        found->second.spawn=positioned;
        return deliveries;
    }

    // Caller invokes only after authoritative scene transfer acceptance. All old
    // removals precede new spawns, including clearing the traveller's old peers.
    std::vector<Delivery> transfer(const Presence& incoming) {
        const auto found=members_.find(incoming.session);
        if(found==members_.end() || found->second.account!=incoming.account ||
           found->second.character!=incoming.character ||
           found->second.spawn.identity()!=incoming.spawn.identity() ||
           found->second.location==incoming.location)
            throw std::invalid_argument("Visibility transfer binding rejected");
        validate_entry(incoming,incoming.session);
        const auto& before=found->second;
        std::vector<Delivery> deliveries;
        const auto removal=RecoveredRemoteActorRemove::encode_logical(before.departure);
        for(const auto& [other,peer]:members_)
            if(other!=incoming.session && peer.location==before.location) {
                const auto old_peer=RecoveredRemoteActorRemove::encode_logical(peer.departure);
                deliveries.push_back({other,{removal.begin(),removal.end()}});
                deliveries.push_back({incoming.session,{old_peer.begin(),old_peer.end()}});
            }
        const auto spawn=RecoveredRemoteActor::encode_logical(incoming.spawn);
        for(const auto& [other,peer]:members_)
            if(other!=incoming.session && peer.location==incoming.location) {
                const auto new_peer=RecoveredRemoteActor::encode_logical(peer.spawn);
                deliveries.push_back({incoming.session,{new_peer.begin(),new_peer.end()}});
                deliveries.push_back({other,{spawn.begin(),spawn.end()}});
            }
        static_assert(std::is_nothrow_copy_assignable_v<Presence>);
        found->second=incoming;
        found->second.pose.reset();
        return deliveries;
    }
private:
    std::size_t validate_entry(const Presence& incoming,std::uint64_t replacing=0) const {
        if(!incoming.session || !incoming.account || !incoming.character ||
           !incoming.spawn.identity() || incoming.spawn.identity()!=incoming.departure.identity() ||
           incoming.location.area<1 || incoming.location.area>16 || incoming.location.scene>1023 ||
           (members_.contains(incoming.session) && incoming.session!=replacing))
            throw std::invalid_argument("Visibility entry identity/scene rejected");
        std::size_t visible=0;
        for(const auto& [session,peer]:members_) {
            if(session==replacing) continue;
            if(peer.character==incoming.character || peer.spawn.identity()==incoming.spawn.identity())
                throw std::invalid_argument("Visibility character or native identity already bound");
            if(peer.location==incoming.location) ++visible;
        }
        if(visible>remote_capacity)
            throw std::invalid_argument("Visibility native remote pool capacity exceeded");
        return visible;
    }
    std::map<std::uint64_t,Presence> members_;
};
}
