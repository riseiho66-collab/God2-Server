#pragma once

#include "scripting/ScriptNpc.h"
#include "scripting/ScriptQuest.h"
#include "scripting/ScriptMonsterAi.h"
#include "scripting/ScriptEvent.h"
#include "scripting/ScriptGm.h"
#include <cstdint>
#include <map>
#include <vector>

namespace god2 {

// VM-private storage. References must be destroyed before their owning state.
struct LuaRegistry {
    std::map<std::uint32_t, ScriptNpc> npcs;
    std::map<std::uint32_t, ScriptQuest> quests;
    std::map<std::uint32_t, ScriptMonsterAi> monster_ais;
    std::map<std::string, std::vector<ScriptEvent>> events;
    std::map<std::string, ScriptGm> gm_commands;
};

std::uint32_t script_id(const sol::object& value);
std::string script_name(const sol::object& value);
sol::protected_function script_function(const sol::object& value);

} // namespace god2
