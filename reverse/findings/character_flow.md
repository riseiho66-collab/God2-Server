# Character List And Selection Flow

## Current Evidence

Actual GOD2 opcodes, payloads and response sequence: **unknown**. No authorized traffic or runtime handler trace was collected. PE-001 does not establish gameplay behavior.

## Recovery Questions

List counts, record widths, name encoding, character IDs, ownership checks, selection reply and create/delete availability.

## Mock Integration Contract

> PLACEHOLDER - waiting for real GOD2 reverse engineering result

Authenticated list request 0x1002/result 0x2002; select 0x1003/result 0x2003 -> CharacterSelected. Default name is TestPlayer; SQLite generates IDs, not fixed 10001. List reply is u16 count then records containing u32 ID, string name, u32 level/job/map, i32 x/y. Selection uses u32 ID with ownership validation; reply is u8 result=0, u32 ID. These values and behaviors come from the requested server scaffold, not from the client.

## Evidence Collection

Correlate list decoder loops with client record storage; trace selection ID writer and result state transition. Record source hash, action, state before/after, direction, raw sample IDs, frame boundaries, transform boundary, handler/encoder RVAs and expected server replies. Include unsolicited messages and failure branches.

## Acceptance Cases

Zero/one/multiple characters, non-ASCII names, invalid counts, unauthorized/unknown selection and repeated selection. A completed finding includes byte-level schemas and independent observations of the required reply sequence. Link promoted results into [GOD2_PROTOCOL_SPEC](../../docs/GOD2_PROTOCOL_SPEC.md) and [PACKET_HANDLER_MAP](../../docs/PACKET_HANDLER_MAP.md); leave unsupported fields unknown.
