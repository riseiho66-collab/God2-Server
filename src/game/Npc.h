#pragma once
#include "game/Entity.h"
#include <string>
namespace god2 {
struct Npc : Entity {
    Npc() { type = EntityType::Npc; }
    std::uint32_t template_id = 0;
    std::string name;
};
}
