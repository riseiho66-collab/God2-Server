#pragma once
#include <cstdint>

namespace god2 {
// PLACEHOLDER - waiting for real GOD2 reverse engineering result.
// These opcode values are placeholders. They are NOT verified GOD2 opcodes.
// Replace them after reverse engineering God2.exe.
enum class Opcode : uint16_t {
    Unknown = 0x0000,
    C2S_Handshake = 0x1000,
    C2S_LoginRequest = 0x1001,
    C2S_RequestCharList = 0x1002,
    C2S_SelectCharacter = 0x1003,
    C2S_EnterWorld = 0x1004,
    C2S_Heartbeat = 0x1005,
    C2S_PlayerMove = 0x1010,
    C2S_ChatMessage = 0x1020,
    C2S_NpcTalk = 0x1030,
    C2S_BattleAction = 0x1040,
    S2C_HandshakeAck = 0x2000,
    S2C_LoginResult = 0x2001,
    S2C_CharacterList = 0x2002,
    S2C_SelectCharResult = 0x2003,
    S2C_EnterWorld = 0x2004,
    S2C_HeartbeatAck = 0x2005,
    S2C_PlayerSpawn = 0x2010,
    S2C_PlayerMove = 0x2011,
    S2C_ChatMessage = 0x2020,
    S2C_NpcSpawn = 0x2030,
    S2C_NpcDialog = 0x2031,
    S2C_BattleStart = 0x2040,
    S2C_BattleResult = 0x2041,
    S2C_Error = 0x2FFF
};
}
