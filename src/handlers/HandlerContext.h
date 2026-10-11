#pragma once
#include "net/Session.h"
#include "game/World.h"
#include "db/Database.h"
#include "scripting/LuaEngine.h"
namespace god2 {
class FixtureBattleService;
class ChineseText;
struct HandlerContext {
    Session& session;
    World& world;
    Database& database;
    LuaEngine& lua;
    bool mock_login=true;
    FixtureBattleService* fixture_battles=nullptr;
    const ChineseText* chinese_text=nullptr;
};
}
