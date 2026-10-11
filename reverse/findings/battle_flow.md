# Battle Flow

## Current Evidence

Actual GOD2 opcodes, payloads and response sequence: **unknown**. No authorized traffic or runtime handler trace was collected. PE-001 does not establish gameplay behavior.

## Recovery Questions

Start participants, turn/tick model, legal actions, target encoding, skill/resource costs, result ordering, death and exit transitions.

## Mock Integration Contract

> PLACEHOLDER - waiting for real GOD2 reverse engineering result

InBattle action 0x1040; start/result 0x2040/0x2041 are fixtures. A placeholder handler does not implement combat or prove a reachable InBattle transition. These values and behaviors come from the requested server scaffold, not from the client.

## Evidence Collection

Trace battle UI/action serialization and result animation/state consumers; distinguish display events from authoritative state updates. Record source hash, action, state before/after, direction, raw sample IDs, frame boundaries, transform boundary, handler/encoder RVAs and expected server replies. Include unsolicited messages and failure branches.

## Acceptance Cases

Invalid target/action, wrong turn/state, repeated action, disconnect, battle end and return to world. A completed finding includes byte-level schemas and independent observations of the required reply sequence. Link promoted results into [GOD2_PROTOCOL_SPEC](../../docs/GOD2_PROTOCOL_SPEC.md) and [PACKET_HANDLER_MAP](../../docs/PACKET_HANDLER_MAP.md); leave unsupported fields unknown.
