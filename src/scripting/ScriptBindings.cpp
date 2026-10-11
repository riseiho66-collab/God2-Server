#include "scripting/ScriptBindings.h"
#include "scripting/LuaLog.h"
#include <stdexcept>

namespace god2 {
namespace {
template<class Map, class Key, class Value>
void insert_unique(Map& map, Key key, Value value) {
    if (!map.emplace(std::move(key), std::move(value)).second)
        throw std::runtime_error("duplicate script registration");
}
}

void bind_scripts(sol::state& lua, LuaRegistry& registry) {
    lua.set_function("log", [](const std::string& text) { detail::lua_logger()->info("{}", text); });
    lua.set_function("register_npc", [&registry](sol::object id, sol::table spec) {
        insert_unique(registry.npcs, script_id(id), ScriptNpc{
            script_name(spec.raw_get<sol::object>("name")),
            script_function(spec.raw_get<sol::object>("on_talk"))});
    });
    lua.set_function("register_quest", [&registry](sol::object id, sol::table spec) {
        insert_unique(registry.quests, script_id(id), ScriptQuest{
            script_name(spec.raw_get<sol::object>("name")),
            script_function(spec.raw_get<sol::object>("on_accept")),
            script_function(spec.raw_get<sol::object>("on_complete"))});
    });
    lua.set_function("register_monster_ai", [&registry](sol::object id, sol::table spec) {
        insert_unique(registry.monster_ais, script_id(id), ScriptMonsterAi{
            script_function(spec.raw_get<sol::object>("on_spawn")),
            script_function(spec.raw_get<sol::object>("on_update")),
            script_function(spec.raw_get<sol::object>("on_death"))});
    });
    lua.set_function("register_event", [&registry](sol::object name, sol::object callback) {
        registry.events[script_name(name)].push_back({script_function(callback)});
    });
    lua.set_function("register_gm_command", [&registry](sol::object name, sol::object callback) {
        insert_unique(registry.gm_commands, script_name(name), ScriptGm{script_function(callback)});
    });
}
} // namespace god2
