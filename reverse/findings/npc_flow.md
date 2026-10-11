# NPC And Quest Flow

## Current Evidence

Actual GOD2 opcodes, payloads and response sequence: **unknown**. No authorized traffic or runtime handler trace was collected. PE-001 does not establish gameplay behavior.

## Recovery Questions

Entity/content IDs, dialogue options, continuation tokens, proximity, quest transitions and close/cancel behavior.

## Mock Integration Contract

> PLACEHOLDER - waiting for real GOD2 reverse engineering result

InWorld NPC talk 0x1030; request is u32 NPC ID; Lua on_talk supplies placeholder reply 0x2031 containing u32 NPC ID and a u16-byte-length-prefixed JSON dialogue string. Spawn 0x2030 is also only a fixture. No real quest opcode exists here. These values and behaviors come from the requested server scaffold, not from the client.

## Evidence Collection

Trace clicks and option selections to serializers and client dialogue consumers; identify whether a reply carries text, IDs or localization references. Record source hash, action, state before/after, direction, raw sample IDs, frame boundaries, transform boundary, handler/encoder RVAs and expected server replies. Include unsolicited messages and failure branches.

## Acceptance Cases

Unknown NPC, out-of-range interaction, invalid option, stale dialogue, script error and quest precondition failure. A completed finding includes byte-level schemas and independent observations of the required reply sequence. Link promoted results into [GOD2_PROTOCOL_SPEC](../../docs/GOD2_PROTOCOL_SPEC.md) and [PACKET_HANDLER_MAP](../../docs/PACKET_HANDLER_MAP.md); leave unsupported fields unknown.
