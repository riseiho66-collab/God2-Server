#pragma once
#include "game/Entity.h"
#include "protocol/Packet.h"
#include <memory>
#include <unordered_map>
#include <vector>
namespace god2 {
class InterestPolicy {
public:
    virtual ~InterestPolicy()=default;
    virtual bool visible(const Entity& observer,const Entity& target) const=0;
};
class Map {
public:
    explicit Map(std::uint32_t id):id_(id){}
    std::uint32_t id() const { return id_; }
    void add_entity(std::shared_ptr<Entity> entity);
    void remove_entity(std::uint64_t id);
    void broadcast(const Packet& packet);
    void set_interest_policy(std::unique_ptr<InterestPolicy> policy) { interest_=std::move(policy); }
private:
    std::uint32_t id_;
    std::unordered_map<std::uint64_t,std::shared_ptr<Entity>> entities_;
    std::unique_ptr<InterestPolicy> interest_;
};
}
