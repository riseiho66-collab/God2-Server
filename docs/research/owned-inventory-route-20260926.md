# Owned bag route — 2026-09-26

## Connected and deployed

C2S `24 source:u8 destination:u8` now reaches the native C++ server's owned
inventory transaction. Ordinary bag cells 0..29 move or exchange whole stacks.
The two saved revisions advance atomically; quantities, resources, other cells
and other characters remain unchanged. Original server merge/split/equipment
rules are not recovered; this whole-stack policy is **CUSTOM-0037**.

Eligible item instances are the already-persisted, source-pinned map5569 and
qualified MED02 scalar items. This is not arbitrary equipment/affix support.
The native fresh-slot initializer clears the full 24-byte records. The existing
scalar grants therefore establish item-ID plus 18 zero metadata bytes; the
projection writes all 20 metadata bytes with `41 clear / 3B / 41 absolute count`.
No captured unrelated item instance is copied.

Reconnect restores each item at its saved slot. Map use and quest-gated battle
eligibility look for the actual owned map instead of assuming it remains in
slot0. Before the introductory reward completes, destination0 remains reserved
for that existing reward transaction. Missing bag capacity is allocated as
explicit empty rows. A legacy save with an unfinished battle defers that
allocation, preserving login and all existing rows; a later move retries after
settlement. The actual move still rejects unfinished battles.

## Verification

- CTest: inventory_move, recovered_inventory_move, recovered_world_records,
  recovered_world_service: **4/4 passed**.
- Native current-EXE producer: 1162 producer cases, 15 gates, 12 callers and
  9 initialization baselines. Codec: all65536 byte pairs.
- Native projection: **4 tests passed**, 120 cases applied twice to poisoned
  records; four item IDs, full metadata, native name/icon lookup and count
  boundaries. This is machine-code execution, not visual proof.
- Current original client on an isolated `God2Lab-*` desktop:
  `private-inventory-move-20260926-03` accepted real drag0→5→0. Each move reached
  the server; SQLite and complete24-byte client slots agreed. Other slots and
  position remained unchanged; client stayed alive. Input desktop remained
  `Default`; no screenshots or visible-desktop input were used.
- Final v3 socket regression: inventory plus town visibility **5 tests passed**.
  Covers exchange, empty drag, restart/restore, map use at29, exact initialization
  packets, unchanged resources and unrelated rows, stage0/1/2 reward reservation,
  and existing scene/visibility behavior. Town+world_supply is explicitly
  rejected by existing configuration; no acceptance claim for that combination.
- New CTest entries inventory_move_server and current_inventory_projection:
  **2/2 passed** against the published binary.

The final change after the private UI pass only defers empty-row allocation
during pending battles; the wire projection remains identical. The final
repository regression verifies zero writes during deferral and successful
allocation after settlement. No additional visual acceptance is claimed.

## Persistent local service

Published to the existing server path, preserving the scheduled startup task and
configuration. There were **zero established sessions** at the update.
Final server SHA256:
`0e694f9840ab992547dbda2e9cef48e76c1c3bc5282e38f9093ac806ef09f5e8`.

The prior EXE, unchanged configuration and online SQLite backup are retained in
`artifacts/releases/owned-inventory-20260926-01/`. The staged clone passed native
19-byte seed and SQLite checks. After deployment, localhost2592 returned that
seed and account, character, position, resource, inventory and quest tables
matched the backup. `deployment-result.json` records acceptance. The live client
EXE was not modified. The current service still has world_supply disabled.

This completes this restricted bag-move route, not all inventory gameplay or the
whole server. Overall playability remains a rough **11% planning estimate**;
it is not a packet-count measurement and has not been increased for research
or unit-test counts.
