# Inventory And Shop Flow

## Current Evidence

Actual GOD2 opcodes, payloads and response sequence: **unknown**. No authorized traffic or runtime handler trace was collected. PE-001 does not establish gameplay behavior.

## Recovery Questions

Slots, stack counts, item instance/template IDs, equipment, deltas versus snapshots, currencies and transaction acknowledgments.

## Mock Integration Contract

> PLACEHOLDER - waiting for real GOD2 reverse engineering result

No inventory/shop opcode or payload is allocated by the requested placeholder enum. Do not invent one; persistence is deferred. These values and behaviors come from the requested server scaffold, not from the client.

## Evidence Collection

Correlate authorized inspect/move/split/equip/shop actions with client container updates and transaction ordering. Record source hash, action, state before/after, direction, raw sample IDs, frame boundaries, transform boundary, handler/encoder RVAs and expected server replies. Include unsolicited messages and failure branches.

## Acceptance Cases

Empty/full bag, stack limits, stale slot, duplicate action, failed purchase and consistency of currency/item changes. A completed finding includes byte-level schemas and independent observations of the required reply sequence. Link promoted results into [GOD2_PROTOCOL_SPEC](../../docs/GOD2_PROTOCOL_SPEC.md) and [PACKET_HANDLER_MAP](../../docs/PACKET_HANDLER_MAP.md); leave unsupported fields unknown.
