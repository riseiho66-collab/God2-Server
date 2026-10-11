# Chat Flow

## Current Evidence

Actual GOD2 opcodes, payloads and response sequence: **unknown**. No authorized traffic or runtime handler trace was collected. PE-001 does not establish gameplay behavior.

## Recovery Questions

Channel identifiers, text encoding, byte/character limits, sender identity, whisper target, routing and response/error behavior.

## Mock Integration Contract

> PLACEHOLDER - waiting for real GOD2 reverse engineering result

Fixture C2S 0x1020 takes a u16-byte-length-prefixed text string of 1..512 bytes in InWorld; S2C 0x2020 map-broadcasts u32 player/session ID and the string. This is a mock server restriction, not a verified GOD2 restriction. These values and behaviors come from the requested server scaffold, not from the client.

## Evidence Collection

Trace text entry serialization and received message display with ASCII/non-ASCII text and multiple channels. Record source hash, action, state before/after, direction, raw sample IDs, frame boundaries, transform boundary, handler/encoder RVAs and expected server replies. Include unsolicited messages and failure branches.

## Acceptance Cases

Empty/oversize text, malformed encoding, invalid channel/recipient, wrong state and multiple recipients. A completed finding includes byte-level schemas and independent observations of the required reply sequence. Link promoted results into [GOD2_PROTOCOL_SPEC](../../docs/GOD2_PROTOCOL_SPEC.md) and [PACKET_HANDLER_MAP](../../docs/PACKET_HANDLER_MAP.md); leave unsupported fields unknown.
