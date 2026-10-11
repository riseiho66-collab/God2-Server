#include "game/Map.h"
#include "game/Player.h"
namespace god2 {
void Map::add_entity(std::shared_ptr<Entity> e) { entities_.insert_or_assign(e->id,std::move(e)); }
void Map::remove_entity(std::uint64_t id) { entities_.erase(id); }
void Map::broadcast(const Packet& packet) {
    for(auto& [id,e]:entities_) {
        if(auto p=std::dynamic_pointer_cast<Player>(e))
            if(auto s=p->session.lock()) s->send(packet);
    }
}
}
