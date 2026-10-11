#pragma once
#include <cstdint>

namespace god2 {
enum class EntityType { Player, Npc, Monster, ItemDrop };
struct Entity {
    virtual ~Entity();
    std::uint64_t id = 0;
    EntityType type = EntityType::Player;
    std::uint32_t map_id = 1;
    std::int32_t x = 100, y = 100;
};
}
