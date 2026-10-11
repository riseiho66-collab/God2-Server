#include "game/World.h"
#include <stdexcept>
namespace god2 {
bool World::initialize() { get_or_create_map(1); return true; }
Map& World::get_or_create_map(std::uint32_t id) {
    auto [it,created]=maps_.try_emplace(id);
    if(created) it->second=std::make_unique<Map>(id);
    return *it->second;
}
void World::add_player(std::shared_ptr<Player> p) {
    if(players_.contains(p->id) || character_online(p->character.id)) throw std::runtime_error("Character already in world");
    get_or_create_map(p->map_id).add_entity(p); players_.emplace(p->id,std::move(p));
}
void World::remove_player(std::uint64_t id) {
    const auto it=players_.find(id); if(it==players_.end()) return;
    get_or_create_map(it->second->map_id).remove_entity(id); players_.erase(it);
}
std::shared_ptr<Player> World::find_player(std::uint64_t id) const {
    auto it=players_.find(id); return it==players_.end()?nullptr:it->second;
}
bool World::character_online(std::uint64_t id) const {
    for(const auto& [key,p]:players_) if(p->character.id==id) return true;
    return false;
}
std::vector<std::shared_ptr<Player>> World::players_on_map(std::uint32_t id) const {
    std::vector<std::shared_ptr<Player>> result;
    for(const auto& [key,p]:players_) if(p->map_id==id) result.push_back(p);
    return result;
}
void World::update(float dt) { if(dt>=0 && dt<=1) elapsed_+=dt; }
}
