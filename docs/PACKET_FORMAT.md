# Packet Format

> PLACEHOLDER - waiting for real GOD2 reverse engineering result

## Synthetic Framework Format

| Offset | Width | Type | Meaning |
| --- | ---: | --- | --- |
| 0 | 2 | uint16 little-endian | Total frame size, including all four header bytes |
| 2 | 2 | uint16 little-endian | Placeholder opcode |
| 4 | length - 4 | bytes | Payload defined by the mock handler |

Minimum size is 4, representable maximum is 65535, maximum payload is 65531. A configured lower limit may restrict these further. Do not serialize the in-memory C++ struct by casting: explicit byte operations avoid packing/alignment assumptions.

Decoder contract: retain input until at least two bytes, then validate the declared length immediately; reject length < 4 or above the configured limit before waiting for the rest of the header. Wait without consuming an incomplete valid frame; emit complete frames and continue over coalesced input. Offline replay reports residual bytes at EOF as truncation; the network session closes on receive EOF/error. An invalid header is not an invitation to scan arbitrary bytes for a guessed resynchronization point.

Encoder contract: check payload size before adding four or narrowing to uint16; write total size then opcode then payload. No sequence, checksum, flags, crypto or compression is specified for this mock format. Disabled mock transforms say nothing about the real client.

## Synthetic Examples

| Bytes | Interpretation |
| --- | --- |
| 04 00 00 10 | Empty mock C2S_Handshake |
| 06 00 05 10 AA BB | Mock opcode 0x1005 with two arbitrary payload bytes; framing fixture only |
| 04 00 00 10 04 00 05 10 | Two concatenated empty frames |
| 04 00 00 | Incomplete header, retain until more bytes or report truncated EOF |
| 03 00 00 10 | Invalid length smaller than header |

These examples validate framing only, not acceptance by a handler or by God2.exe. The following mock schemas were aligned with current source and the user's integration details; they are not client evidence.


## Implemented Mock Payloads

All multibyte integers are little-endian. Here string means uint16 byte length followed by UTF-8 bytes, without a terminator. Length counts bytes, not Unicode characters. The current reader/writer bounds-checks and copies bytes but does not itself validate UTF-8. Field order is shown below. Handlers reject extra trailing bytes.

| Message | Payload schema / behavior |
| --- | --- |
| C2S_Handshake | Empty |
| S2C_HandshakeAck | string GOD2 PLACEHOLDER v1 |
| C2S_LoginRequest | Empty selects username mock; otherwise string username, string password, string client_version |
| S2C_LoginResult | u8 result=0, u32 generated account_id, string Login OK (MOCK) |
| C2S_RequestCharList | Empty |
| S2C_CharacterList | u16 count; repeated u32 character_id, string name, u32 level, u32 job, u32 map_id, i32 x, i32 y |
| C2S_SelectCharacter | u32 character_id, checked for account ownership |
| S2C_SelectCharResult | u8 result=0, u32 character_id |
| C2S_EnterWorld | Empty |
| S2C_EnterWorld / S2C_PlayerSpawn | u32 player/session_id, u32 character_id, u32 map_id, i32 x, i32 y, u8 direction=0, u32 hp, u32 mp |
| C2S_Heartbeat | Empty; permitted in every non-disconnected state |
| S2C_HeartbeatAck | u32 Unix seconds |
| C2S_PlayerMove | i32 x, i32 y; each in 0..100000 |
| S2C_PlayerMove | u32 player/session_id, i32 x, i32 y; map broadcast |
| C2S_ChatMessage | string text, 1..512 bytes |
| S2C_ChatMessage | u32 player/session_id, string text; map broadcast |
| C2S_NpcTalk | u32 npc_id |
| S2C_NpcDialog | u32 npc_id, string JSON dialogue returned by Lua |
| S2C_Error | string error, capped at 512 bytes |

Explicit mock login accepts username length 1..64 bytes, password <=256 bytes and client_version <=64 bytes. Truncated/malformed fields are rejected, not treated as empty login. Any field-valid username is accepted without authentication. The password is discarded; new accounts store !MOCK-NOT-A-PASSWORD-HASH!. Real authentication is unsupported. Account and character IDs are SQLite-generated, not fixed 1/10001. Character lists currently reject more than 100 records.

EnterWorld payload size is 29 bytes (33 with header). The server first sends S2C_EnterWorld, broadcasts the newcomer's PlayerSpawn to all map players including self, then sends the newcomer PlayerSpawn snapshots for existing map players. All use the same payload schema. Selecting an already-online character is rejected while remaining Authenticated. If the selected character enters elsewhere before EnterWorld, entry resets the session to Authenticated, clears character_id to 0 and returns S2C_Error.

Movement saves the updated character through the repository before updating world position and broadcasting. Unknown opcodes receive S2C_Error with Unknown PLACEHOLDER opcode; invalid state receives Opcode not allowed in current session state; caught handler exceptions produce Request rejected. These are mock error formats.

Real-protocol integration must map recovered wire opcodes and payloads into these internal handler schemas and map responses back out. Updating only PacketHeader, God2ProtocolSpec, CryptoPipeline and CompressionPipeline cannot recover a different payload contract.

## Real GOD2 Format

Transport, length position/width/coverage, opcode position/width, endian, strings, sequence, checksum, flags, cipher and compression are **unknown**. PE32 machine endian does not prove network endian. For every recovered field record offset, width, signedness, byte order, semantic range, evidence and sample bytes. Resolve transforms and length coverage together; a length can describe ciphertext, compressed data, plaintext or a different envelope.
