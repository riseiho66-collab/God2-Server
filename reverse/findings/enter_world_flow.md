# Enter World Flow

## Current Evidence

Actual GOD2 opcodes, payloads and response sequence: **unknown**. No authorized traffic or runtime handler trace was collected. PE-001 does not establish gameplay behavior.

## Recovery Questions

Map/instance identifiers, spawn sequence, player identity, coordinates, direction, hp/mp, readiness ack and loading dependencies.

## Mock Integration Contract

> PLACEHOLDER - waiting for real GOD2 reverse engineering result

CharacterSelected -> InWorld through request 0x1004/reply 0x2004; request payload is empty; reply is u32 player/session ID, u32 character ID, u32 map ID, i32 x, i32 y, u8 direction=0, u32 hp, u32 mp. After the entry reply, PlayerSpawn 0x2010 broadcasts the newcomer's data to everyone including self, then sends the newcomer snapshots of existing players using the same schema. A concurrent entry elsewhere rejects this entry, resets state to Authenticated and clears character_id. These are mock server behaviors, not recovered client facts.

## Evidence Collection

Trace scene transition consumers and distinguish player state, entity spawns and map metadata; retain message order and timing. Record source hash, action, state before/after, direction, raw sample IDs, frame boundaries, transform boundary, handler/encoder RVAs and expected server replies. Include unsolicited messages and failure branches.

## Acceptance Cases

Valid selection, missing prerequisites, map transition, duplicate entry, failure during loading and reconnect. A completed finding includes byte-level schemas and independent observations of the required reply sequence. Link promoted results into [GOD2_PROTOCOL_SPEC](../../docs/GOD2_PROTOCOL_SPEC.md) and [PACKET_HANDLER_MAP](../../docs/PACKET_HANDLER_MAP.md); leave unsupported fields unknown.
