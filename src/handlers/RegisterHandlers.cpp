#include "handlers/RegisterHandlers.h"
#include "handlers/LoginHandler.h"
#include "handlers/CharacterHandler.h"
#include "handlers/WorldHandler.h"
#include "handlers/HeartbeatHandler.h"
#include "handlers/MovementHandler.h"
#include "handlers/ChatHandler.h"
#include "handlers/NpcHandler.h"
#include "handlers/BattleHandler.h"
#include "handlers/DebugHandler.h"
namespace god2 {
void register_handlers(OpcodeDispatcher& d) {
    register_login_handlers(d); register_character_handlers(d); register_world_handlers(d);
    register_heartbeat_handlers(d); register_movement_handlers(d); register_chat_handlers(d);
    register_npc_handlers(d); register_battle_handlers(d); register_debug_handlers(d);
}
}
