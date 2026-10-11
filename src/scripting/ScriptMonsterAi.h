#pragma once
#include <sol/sol.hpp>
namespace god2 {
struct ScriptMonsterAi {
    sol::protected_function on_spawn;
    sol::protected_function on_update;
    sol::protected_function on_death;
};
}
