# Opcode Registry

## Real GOD2

No C2S or S2C values are verified. See [C2S research](../reverse/findings/opcode_table_c2s.md), [S2C research](../reverse/findings/opcode_table_s2c.md) and [handler map](PACKET_HANDLER_MAP.md). Promote a row only with artifact-bound dispatch/serializer evidence and a reproducible sample.

## Framework Fixture Values

> These opcode values are placeholders.
> They are NOT verified GOD2 opcodes.
> Replace them after reverse engineering God2.exe.

| Value | Name | Direction | Mock state / intent |
| --- | --- | --- | --- |
| 0x0000 | Unknown | N/A | Sentinel, no recovered meaning |
| 0x1000 | C2S_Handshake | C2S | Connected |
| 0x1001 | C2S_LoginRequest | C2S | Connected or Handshaked |
| 0x1002 | C2S_RequestCharList | C2S | Authenticated |
| 0x1003 | C2S_SelectCharacter | C2S | Authenticated |
| 0x1004 | C2S_EnterWorld | C2S | CharacterSelected |
| 0x1005 | C2S_Heartbeat | C2S | All non-disconnected states |
| 0x1010 | C2S_PlayerMove | C2S | InWorld |
| 0x1020 | C2S_ChatMessage | C2S | InWorld |
| 0x1030 | C2S_NpcTalk | C2S | InWorld |
| 0x1040 | C2S_BattleAction | C2S | InBattle |
| 0x2000 | S2C_HandshakeAck | S2C | Mock handshake reply |
| 0x2001 | S2C_LoginResult | S2C | Mock login reply |
| 0x2002 | S2C_CharacterList | S2C | Mock list |
| 0x2003 | S2C_SelectCharResult | S2C | Mock selection result |
| 0x2004 | S2C_EnterWorld | S2C | Mock world data |
| 0x2005 | S2C_HeartbeatAck | S2C | Mock server time |
| 0x2010 | S2C_PlayerSpawn | S2C | Mock spawn |
| 0x2011 | S2C_PlayerMove | S2C | Mock movement |
| 0x2020 | S2C_ChatMessage | S2C | Mock chat |
| 0x2030 | S2C_NpcSpawn | S2C | Mock NPC spawn |
| 0x2031 | S2C_NpcDialog | S2C | Mock dialogue |
| 0x2040 | S2C_BattleStart | S2C | Future mock battle |
| 0x2041 | S2C_BattleResult | S2C | Future mock battle |
| 0x2FFF | S2C_Error | S2C | Mock error |

This table reflects placeholder integration values. Runtime verification is recorded in [VERIFICATION.md](VERIFICATION.md). Numeric registration does not imply an implemented payload or reachable feature. Inventory/shop/quest opcodes are not allocated here.

Future entries require direction, wire mode, state, payload schema/version, handler evidence, response relations and confidence. Keep real and fixture namespaces distinct even if values happen to coincide.
