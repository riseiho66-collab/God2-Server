#pragma once
#include "game/Entity.h"
#include <optional>
namespace god2 {
struct Monster : Entity {
    Monster() { type = EntityType::Monster; }
    std::uint32_t template_id = 0;
    std::optional<std::uint32_t> hp;
};
}
