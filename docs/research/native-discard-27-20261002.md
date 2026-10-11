# Native inventory discard 27 — 2026-10-02

## Native evidence

Build-matched native image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Current production client SHA256:
`c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575`.

`496720` queues opcode27 and four unmodified bytes when UI+866E4 is zero.
Native `49A330` bag callback control56 is the discard target. It copies itemWORD,
source slotBYTE and countBYTE from the selected native24-byte inventory record.
Counts >=2 open `4C9820` quantity mode4; `4C9ED0` submits the chosen quantity.
`4EA770` confirmation mode5 also emits27. Logical wire:
`27 item_lo item_hi slot quantity`, exactly5bytes. Producer does not validate
item ownership or quantity; server must not equate queue success with authority.

Native `4991E0` S2C41 consumes `41 itemWORD slotBYTE countBYTE`, writes count
at UI+8560C+24*slot and itemWORD at +85610+24*slot. Signed nonpositive count
clears count/item; the other instance bytes remain untouched. Server scope
therefore restricts count1..127. Clearing is `41 00 00 slot 00`.

`tools/strike_lab/current_discard_27_20261002.py` executes the original producer
and receiver machine code:12 queue/gating cases plus12 slot/count/metadata cases.
Receipt: `artifacts/research/native-discard-27-20261002.json`. All24 passed.

## Server route and limits

`CUSTOM-0061` connects the native request parser to owned ordinary scalar bag
slots0..29. Exact authenticated owner, selected ready-world character, projected
inventory, current location, source hash and existing scalar item policy required.
Only one discard plus optional idle ticks per batch. Pending battles, map
transitions, mixed mutations, unprojected state and protected guide slot0 denied.

BEGIN IMMEDIATE validates the saved owner/revision, decrements exactly once,
clears item at zero and increments revision. Source hash and allocation design
ID remain unchanged. Absolute41 is prepared before committing. Wrong item or
quantity does not debit; existing slot is reprojected. SQL failure/readback
corruption rolls back. No grant, money or ground drop is produced.

The **wire and client controls are native verified**. Original server discard
restrictions, ground-drop creation, enhanced/bound/equipment metadata and battle
variants are not recovered. The scoped destructive stack policy is explicitly
custom; this is not an all-item/native-economy completion claim.

## Verification

- CTest4/4: inventory_discard, inventory_move, recovered_world_records,
  recovered_world_service. Includes SQL abort/readback rollback, owner/CAS,
  pending battle, stale revisions and65536 byte-pair codec roundtrips.
- Isolated actual TCP discard2/2: partial/complete decrement, invalid operands,
  duplicate/mixed mutation, coalesced idle ticks, fragmented framing,
  premature request and truncated disconnect; other saved rows preserved.
- Regression TCP6/6: inventory movement3, peer pose2, native options1.
- Packet ledger test1/1; frozen chat baseline passes without refresh.
- Actual current TW/CN clients, hidden desktop, read-only native observation:
  native drag to discard, quantity edit and confirmation;7→5→0 plus1→0.
  Each DB change matches the native inventory record; other50-slot bytes and
  all unrelated saved rows stay unchanged. Six total operations.

Final native receipts:
`artifacts/playtests/private-discard-27-20261002-06/run-result.json` (TW),
`artifacts/playtests/private-discard-27-20261002-05/run-result.json` (CN).
No foreground/input desktop switch, screenshots, injected packets or client
memory writes. These prove current control/transport/state acceptance, **not a
pixel rendering review**. Test grants/catalog copies are disposable fixtures.

Earlier runs01..03 failed because the historical fixture did not project MED02
and its legacy importer no longer matched the expanded current asset. No
production code/client was changed to suppress those guards. Run04 imported the
previous qualified71-row catalog from a read-only fixture; candidate verifies
the complete pinned catalog digest. Runs05/06 additionally check native language
and all unrelated database/native slots. Historical failures remain recorded.

## Completion reporting

This scoped route's three requested UI cases are accepted for both locales:
6/6,100%. This is not whole-game or all-item completion. World parser now has
29 distinct C2S opcode cases; original S2C dispatch table is a different count.
Whole-game completion remains unknown without exhaustive state/variant coverage.

Executable-only deployment and save-preservation evidence belongs in
`artifacts/releases/native-discard-27-20261002/deployment/release.json`.

Installed executable SHA256: `7840fbea217b66920f99c906bfc12d424311f5dccac166a42ad708d3ae6c6503`. Guarded release state INSTALLED, listener PID18180, saved_rows_preserved=true. Production database schema/rows, configuration and client file hashes preserved.
