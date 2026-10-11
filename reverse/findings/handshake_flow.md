# Handshake Flow

## Current Evidence

Actual GOD2 opcodes, payloads and response sequence: **unknown**. No authorized traffic or runtime handler trace was collected. PE-001 does not establish gameplay behavior.

## Recovery Questions

Initial sender, version negotiation, nonce/key material, challenge response, transport switches and failure/disconnect behavior.

## Mock Integration Contract

> PLACEHOLDER - waiting for real GOD2 reverse engineering result

Connected -> Handshaked using C2S_Handshake 0x1000 and S2C_HandshakeAck 0x2000. These values and behaviors come from the requested server scaffold, not from the client.

## Evidence Collection

Record the first bytes in both directions from a fresh local session; compare reconnects and identify what initializes per-session transform state. Record source hash, action, state before/after, direction, raw sample IDs, frame boundaries, transform boundary, handler/encoder RVAs and expected server replies. Include unsolicited messages and failure branches.

## Acceptance Cases

Fresh/repeated connections, incompatible version, incomplete initial message and handshake failure. A completed finding includes byte-level schemas and independent observations of the required reply sequence. Link promoted results into [GOD2_PROTOCOL_SPEC](../../docs/GOD2_PROTOCOL_SPEC.md) and [PACKET_HANDLER_MAP](../../docs/PACKET_HANDLER_MAP.md); leave unsupported fields unknown.
