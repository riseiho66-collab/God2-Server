# Native bank item transfers

Candidate02: `be42a5fd69595384521add5a28a1a07b20d589652d890bd86abf48bb353b6c64`.
Original protocol, custom authoritative storage and live client acceptance are
separate. Read current installation state from
`artifacts/releases/native-bank-items-20261002/deployment/release.json`.
Formal banking NPC locations remain unproved; test coordinates are never
production placement evidence. Whole-game completion denominator is unknown.

## Build-matched original behavior

`current_bank_items_20261002.py` verifies current-client code intervals and
executes the original x86 functions.80/80 cases include the real471610/471720
bank refresh and item catalogue lookup, native quantity dialogue and drop
callers. Declared drawing/queue boundaries are stubs, not live rendered pixels.

-63: target WORD, page/source/destination/quantity BYTEs, logical7.
  Real4723A0 is bag-to-bank. Multiple source items open quantity mode2.
-64: identical layout;49F010 mode17 is bank-to-bag. Quantity mode3.
  Actual4C9ED0 preserves six fields and sends the chosen quantity through
  4976F0/497880. Neither drop path is authority for stored item ownership.
-65: same seven bytes, but trailing1 is a control marker.4719B0 calls
  497510 and immediately swaps all six DWORDs of the24-byte source/destination
  cells. It is **whole-cell movement/swap**, not a one-item quantity.
-48 logical29: page at1, quantity5, slot6, metadata20 bytes at9. Opaque
  fields2..4/7..8 are unconsumed.471E50 replaces all metadata and quantity.
  Qty0 with metadata0 clears icon and count.46 modes7/12 preserve metadata
  tails, so they are not used as substitutes for full canonical48 replacement.
- Native bank storage has300 cells/six cache-page flags. Page arrows make no
  C2S request: they render preloaded cells.232F64==1 wraps two pages; other
  values wrap three. Six cache pages do not prove six unlocked UI pages.
- Slots0/1 are special. Real4722B0/471D40 require metadata kindsD0000,
  200000 or220000. This ordinary MED02 route therefore uses slots2..49.

## Runtime and persistent authority: CUSTOM-0065

The new borrowed repository installs two tables explicitly. Constructors and
loaders do not create schema/items. Startup creates **empty tables only**;
qualified opening allocates300 empty cells for one owned character. Partial
vaults reject instead of filling missing slots or overwriting saved data.
Empty cells use an explicitly custom zero-hash sentinel, never native provenance.
Bank container design is CUSTOM-0065; scalar item domain remains CUSTOM-0015.
Transfer source IDs, counts and pinned catalogue provenance without inventing
equipment/binding/enhancement fields.20 native metadata bytes are projected
only for independently qualified scalar items (ID WORD plus18 zero bytes).

The item service composes the installed CUSTOM-0064 bank money lease. It adds
no banker role or placement, account bypass, funding or access-distance rule.
An owned ready character, no active trade, same target/scene, current monetary
snapshot and unexpired lease are required. Cache the complete30 bag plus300
vault snapshot at opening. Recheck every cell before planning a transfer.
Ordinary requests admit native reachable pages0..2 and bank slots2..49;
edition-specific original server unlock policy is not recovered.

Deposit/withdraw may split a stack;65 moves the whole source cell and requires
marker1. This scoped route accepts empty destinations only: no merges, occupied
cell swapping, enhanced/equipment/bound items or inferred native economics.
These remain open implementation/qualification work, not silently restored.

Pure planning conserves items and advances each changed physical revision once.
Commit uses BEGIN IMMEDIATE, validates account/character ownership and all330
cells, rejects pending battle reservations, applies both full-value/revision
CAS updates, inserts a unique server receipt and reads back receipt and all
cells before COMMIT. Trigger errors, ignored/altered writes and receipt corruption
roll back the entire operation. No purse or bank-money table is written.
Snapshot reads use one consistent read transaction; reads inside an existing
commit transaction do not start a nested transaction. Return/move complete
snapshots without allocating another string copy after COMMIT.

Prepare every native response before writes. A full300-cell48 load is8700
bytes, split at record boundaries into at most0xA00 logical frames. Successful
mutations send changed absolute bank and bag cells only. Rejecting a live
context restores all canonical cells, undoing the native optimistic65 swap,
then removes item and money access. Close39/disconnect and money rejection
drop item context; money packets retain their original serialization. Common
chat/ticks can coexist with one item request. Duplicates/mixed money or other
mutations cannot spend assets. Native packets have no unique request ID, so
server receipts are not independent-frame click deduplication.

## Evidence and remaining work

Installed on the managed local service, port2592, PID16404. The release receipt
records candidate02 SHA above. Final CTest16/16, bank item TCP3/3, bank money
TCP4/4, trade TCP3/3 and party TCP6/6 passed. The frozen chat verifier passed
without refreshing its baseline. Candidate startup added exactly two empty
tables and two indices; every old schema object, migration history and saved
row fingerprint stayed identical. Client/config hashes stayed identical.

Hidden original TW950/CN936 run03 accepted all16 actual native drag/drop
mutations and16 durable receipts, including partial/whole transfers, whole65,
page1 and close/reopen. Both editions showed0..2 reachable pages. Actual native
icon renderer resources and quantity text chains matched saved counts at each
step; this is not a screenshot/pixel or player-load claim. All private clients,
runner and server closed, and2598 was released. Runs01/02 remain failed evidence
and were not promoted. See
`artifacts/playtests/private-native-blackbox-bank-items-20261002-03/run-result.json`,
`artifacts/research/native-bank-items-20261002/live-bank-items-acceptance.json`,
`artifacts/releases/native-bank-items-20261002/manifest.json` and
`artifacts/releases/native-bank-items-20261002/deployment/release.json`.

Formal qualified bank service points remain **0**. Installed handlers and
isolated native UI acceptance do not establish playable original banker access
on production maps. No private role/position/items were copied into live saves.

- Repository tests exercise partial-vault refusal, conservation, whole/partial
  transfers, wrong owner, stale unused cells, replay, page/slot/quantity/revision
  bounds, pending battles, second-update failures, ignored/deleted/corrupted
  receipts and untouched-cell corruption. Old schema/history/money/other saves
  are checked unchanged.
- Application TCP3/3 covers both language peers, fragmentation, native-consumer
  execution of actual C++48 replies, partial/whole transfers,65 whole-stack
  movement, page1, close/reopen/restart and persisted state. Bad targets,
  reserved slots/pages, zero/high quantity, duplicate/mixed requests, closed
  access and coalesced common chat cannot change unrelated state.
- Existing bank-money TCP4/4 passes with the additional full bank projection
  checked explicitly; money serialization, refusal and trade behavior remain.
- Hidden original-client drag/quantity/page/icon/count acceptance is recorded
  separately under `private-native-blackbox-bank-items-20261002-*`. Candidate
  code, synthetic peers and machine oracles alone do not establish that acceptance.
- The release helper requires16 banking/trade/party/world suites plus the
  current hidden-client receipt and frozen-chat baseline, stages an isolated
  startup and compares every old schema/history/row. Only two empty tables
  and their two indices may be added; no private banker is promoted.

Candidate grammar44 C2S producers is structural coverage only. All NPC original
locations, equipment/full instance banking, merging/swapping, bank unlock rules,
official economics and large-player load remain outside this scoped acceptance.
