# Current-native WORLD S2C 59/5A/5B/79 text and NPC label effects

The verified mapped image SHA-256 is `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`. [Pinned instruction slices](../../artifacts/integration/packet-connections-20261006/s2c-text-npc-595a5b79-v1.json) join the WORLD dispatch table to the direct consumers. All four S2C opcodes have fixed **9-byte logical records**. These are receive effects, with no original server producer or C2S request pairing established.

| S2C opcode | Native WORLD path | Consumed fields and effect |
| --- | --- | --- |
| `59`, `5B` | `6AB69 -> 4C81A0` | WORD `L[7..8]` selects a text resource row; WORD `L[1..2]` is passed with the selected text pointer to `4C81F0`. The remaining body bytes are retained without guessed semantics. |
| `5A` | `6AB27 -> 4CCD10` | DWORD `L[1..4]` is looked up as an existing NPC pool identity. WORD `L[7..8]` selects a resource row used to update that pool record's visible label. `L[5..6]` is not read in the bounded WORLD branch. |
| `79` | `6AB7B` | If WORD `L[5..6] != FFFF`, it enters the same `4C81A0` text path. If the WORD equals `FFFF`, DWORD `L[1..4]` and WORD `L[7..8]` enter the `4CCD10` NPC pool label path. |

The `4CCD10` consumer first calls `4CCF80` with the complete DWORD identity; only a found pool record receives the selected resource pointer and its UI label refresh. This does not create an NPC or prove that the resource selector is safe to send from the formal server. The `4C81A0` path checks the selector against its client resource table before forwarding the pointer. Neither client-side lookup is server authorization.

`RecoveredWorldTextNpc595A5B79` preserves every raw byte and exposes the mechanical branch and consumed fields. Runtime emission remains disabled. The remaining work includes the authoritative server issuer, causal timing and owner of the NPC identity. No build, tests, native client execution, service activation or deployment were performed in this connection round.

## Continued NPCBossMessage source join

The [pinned source join](../../artifacts/integration/packet-connections-20261006/s2c-npcboss-message-source-v2.json) identifies the `5A` resource selector, and the `79` `FFFF` branch selector, as **NPCBossMessage IDs**. The native resource dispatcher compares the section name at image RVA `18A11C`, calls `457A70`, and stores the count/table at resource offsets `B2C40/B2C44`. The WORLD `5A` branch selects that table with WORD `L[7..8]`. The original current-client `message.csvZ` has the pinned compressed SHA-256 `5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598` and declares exactly 72 source rows, IDs 1..72; each row's physical line, decoded offset, raw-row hash and CP950 content are preserved in the artifact. The `59/5B` and non-`FFFF` `79` text path instead uses the separate NPCNormalMessage table at `B2C3A/B2C3C`.

`4CCF80` compares the entire DWORD NPC pool identity. The native `72` constructor stores its selector's low WORD as that pool identity, so a `5A`/NPC-mode `79` update for that ordinary NPC must address the zero-extended stored identity. This joins the target identity and message namespace to existing scene records, but still does not establish **which** of the 72 messages should be issued for an NPC, when the label changes, or a causal C2S request. The new codec accessors label the two namespaces without enabling emission. No full connection is claimed.
