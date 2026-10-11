# Movement Flow

## Current Evidence

Actual GOD2 opcodes, payloads and response sequence: **unknown**. No authorized traffic or runtime handler trace was collected. PE-001 does not establish gameplay behavior.

## Recovery Questions

Position encoding, units, signedness, direction, timestamps, sequence, path versus destination and authoritative correction.

## Mock Integration Contract

> PLACEHOLDER - waiting for real GOD2 reverse engineering result

InWorld request 0x1010; payload is i32 x/y, each constrained to 0..100000. The handler saves through CharacterRepository, updates world position, logs and broadcasts 0x2011 with u32 player/session ID and i32 x/y. This does not establish actual GOD2 movement validation. These values and behaviors come from the requested server scaffold, not from the client.

## Evidence Collection

Capture stationary, one-step, axis/diagonal and map-edge actions; correlate coordinate writers/readers with world state. Record source hash, action, state before/after, direction, raw sample IDs, frame boundaries, transform boundary, handler/encoder RVAs and expected server replies. Include unsolicited messages and failure branches.

## Acceptance Cases

Negative/extreme coordinates, movement in wrong state, stale updates, map mismatch and multiple recipients. A completed finding includes byte-level schemas and independent observations of the required reply sequence. Link promoted results into [GOD2_PROTOCOL_SPEC](../../docs/GOD2_PROTOCOL_SPEC.md) and [PACKET_HANDLER_MAP](../../docs/PACKET_HANDLER_MAP.md); leave unsupported fields unknown.
