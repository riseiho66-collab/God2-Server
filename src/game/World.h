#pragma once
#include "game/Map.h"
#include "game/Player.h"
#include <unordered_map>
namespace god2 {
// Owned exclusively by the game executor; network callbacks never mutate world state.
class World {
public:
    bool initialize();
    Map& get_or_create_map(std::uint32_t id);
    void add_player(std::shared_ptr<Player> player);
    void remove_player(std::uint64_t id);
    std::shared_ptr<Player> find_player(std::uint64_t id) const;
    bool character_online(std::uint64_t id) const;
    std::vector<std::shared_ptr<Player>> players_on_map(std::uint32_t id) const;
    void update(float dt);
private:
    std::unordered_map<std::uint32_t,std::unique_ptr<Map>> maps_;
    std::unordered_map<std::uint64_t,std::shared_ptr<Player>> players_;
    double elapsed_=0;
};
}
