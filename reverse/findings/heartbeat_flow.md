# Heartbeat Flow

## Current Evidence

Actual GOD2 opcodes, payloads and response sequence: **unknown**. No authorized traffic or runtime handler trace was collected. PE-001 does not establish gameplay behavior.

## Recovery Questions

Initiator, interval, allowed states, timestamp units, echo/sequence semantics, timeout and retry behavior.

## Mock Integration Contract

> PLACEHOLDER - waiting for real GOD2 reverse engineering result

Fixture empty request 0x1005 is allowed in every non-disconnected state; reply 0x2005 carries u32 Unix seconds, as observed in current server source. These values and behaviors come from the requested server scaffold, not from the client.

## Evidence Collection

Trace timer registration and expiry paths across login, character screen and world; correlate periodic traffic independently of player actions. Record source hash, action, state before/after, direction, raw sample IDs, frame boundaries, transform boundary, handler/encoder RVAs and expected server replies. Include unsolicited messages and failure branches.

## Acceptance Cases

Idle session, delayed/lost reply, repeated heartbeat, reconnect and time-value wraparound. A completed finding includes byte-level schemas and independent observations of the required reply sequence. Link promoted results into [GOD2_PROTOCOL_SPEC](../../docs/GOD2_PROTOCOL_SPEC.md) and [PACKET_HANDLER_MAP](../../docs/PACKET_HANDLER_MAP.md); leave unsupported fields unknown.
