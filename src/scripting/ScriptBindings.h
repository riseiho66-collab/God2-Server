#pragma once
#include "scripting/LuaRegistry.h"
namespace god2 {
void bind_scripts(sol::state& lua, LuaRegistry& registry);
}
