# Current-native S2C WORLD consumer frontier, 2026-10-06

`tools/reconstruction/s2c_world_consumer_frontier.py` reads the verified
mapped image with SHA-256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
It reads the native length and WORLD dispatch tables, compares the retained
static index, and joins the current route ledger. The exact per-opcode
entries and the unclassified list are saved in
`artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v1.json`.
This is source accounting, not client execution or a gameplay test.

| WORLD S2C table category | Current count | Meaning |
| --- | ---: | --- |
| Fixed/variable length accepted | 230 / 22 | 252 length entries; four other opcodes lack supported lengths here. |
| Supported length, non-default WORLD dispatch | 206 | Dispatch-table entry differs from the shared default address; there are 198 distinct target RVAs. |
| Supported length, default WORLD dispatch | 46 | No specialized entry in this WORLD table. This does not rule out battle/login/other-state consumers. |
| Non-default entry registered as a reviewed source reply | 41 | At least one scoped server source branch emits each; it does not qualify every variant or native acceptance. |
| Non-default entry in a pending group's format-only list | 8 | Format knowledge without complete route; S2C `C5` is also among the 41 above. |
| Independently recovered non-default format only | 1 | S2C `68`, with no proven C2S `68` causality. |
| Non-default entry without this route ledger's classification | 157 | Investigation queue, not proof that no older research or server code exists. |

The set arithmetic is `206 - |41 reviewed ∪ 8 pending ∪ 1 independent| = 157`;
the overlap is S2C `C5` in both reviewed and pending. Unsupported native
length entries are `21`, `25`, `FE`, `FF`; `FE`/`FF` lack indexed WORLD
dispatch targets in this retained table. These observations cannot supply
the game's total variant/state denominator or any completion percentage.

The near-term investigation should classify the 157 against existing
research and then trace concrete WORLD consumer effects before assigning
server responses. A separate battle-state receive dispatch inventory is
needed: an opcode using the WORLD default branch may still be actively
consumed during battle. The owner-directed connection phase leaves builds,
tests, native acceptance and deployment for later; none ran in this round.
