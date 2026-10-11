# C2S Opcode Findings

Verified GOD2 rows: **none**. Direction means client to server, not the direction inferred from an opcode's numeric prefix.

| Wire opcode | Width | State | Meaning | Encoder RVA | Payload schema | Evidence | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| unknown | unknown | unknown | Not recovered | unknown | unknown | No wire evidence | Unknown |

For each future row include raw sample IDs, field offsets/constraints, triggering client action and expected server replies, transform mode, artifact hash and unresolved bytes. Keep request-response relations many-to-many until observed.

The 0x1xxx values in [OPCODE_TABLE](../../docs/OPCODE_TABLE.md) are requested framework placeholders, not entries in this table. Cross-check [the other direction](opcode_table_s2c.md) without assuming matching values or symmetric payloads.
