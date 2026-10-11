# Login Flow

## Current Evidence

Actual GOD2 opcodes, payloads and response sequence: **unknown**. No authorized traffic or runtime handler trace was collected. PE-001 does not establish gameplay behavior.

## Recovery Questions

Account/password representation, client version, result codes, tokens, endpoint handoff and retry policy.

## Mock Integration Contract

> PLACEHOLDER - waiting for real GOD2 reverse engineering result

Login from Connected or Handshaked -> Authenticated; fixture request 0x1001 and result 0x2001. Empty payload selects username mock; otherwise three u16-byte-length-prefixed strings encode username/password/client_version. Malformed fields are rejected. Any field-valid username is accepted; password is discarded and new accounts store !MOCK-NOT-A-PASSWORD-HASH!. Reply is u8 result=0, u32 SQLite-generated account ID, string Login OK (MOCK). Real authentication is unsupported, and mock auth is blocked on non-loopback bind addresses. These values and behaviors come from the requested server scaffold, not from the client.

## Evidence Collection

Trace login UI serialization and result consumers; protect credentials and distinguish successful transport from accepted authentication. Record source hash, action, state before/after, direction, raw sample IDs, frame boundaries, transform boundary, handler/encoder RVAs and expected server replies. Include unsolicited messages and failure branches.

## Acceptance Cases

Successful/failed login, malformed fields, duplicate/repeated request, wrong state and reconnect. A completed finding includes byte-level schemas and independent observations of the required reply sequence. Link promoted results into [GOD2_PROTOCOL_SPEC](../../docs/GOD2_PROTOCOL_SPEC.md) and [PACKET_HANDLER_MAP](../../docs/PACKET_HANDLER_MAP.md); leave unsupported fields unknown.
