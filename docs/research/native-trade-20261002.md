# Current native player trade: installed scalar consumable route

Status: **installed on the managed server**, candidate SHA256
`4d00868cc4e6d3b945e5450b273ff8a3c8c7a44e698c9a0397f42f3531855cd0`.
The formal world grammar now admits38 distinct producers, including native
29/2A/2B/2C/2D. This count is structural coverage, not whole-game completion.
Whole-game denominator/completion remains unknown.

## Classification and machine evidence

`current_trade_20261002.py` executes the pinned original x86 image, checks the
matching intervals against current `God2.exe`, and checks original message.csvZ.
61 cases pass, including the five compiled C++ producer fixture comparisons.
External UI drawing helpers are intercepted; tested producers/consumers execute
original instructions. This is bounded machine evidence, not rendered/live UI.

- `69/8A` is **PK**, ProgramMsg733. Do not implement it as player trade.
- `29` logical5: targetWORD, opaqueWORD; native initial opaque0.
- `2A` logical7: itemWORD, sourceSlotBYTE, quantityBYTE, targetWORD.
  497290 emits quantity1; 4972D0 copies6 bytes from the native quantity dialogue.
- `2B` logical9: targetWORD, uninitialized opaqueWORD, moneyDWORD.
- `2C/2D` logical2: native confirm/cancel BYTE0.
- `4E` logical19: name16, peerWORD opens the trade widgets.
- `50` logical25: entire24-byte item instance, signed slot at body1 is0..7.
- `51` logical9: amountDWORD at **body4/logical5**; leadingDWORD unconsumed.
- `53` logical3: peer confirmation displayWORD; does not settle assets.
- `4F` logical3: resets lists, refunds locally deducted money when866DC is set,
  then closes. **Does not put items back into native inventory**; server sync
  must do that. `52` logical3 only closes without reset/refund.
- `27` logical5: absolute purseDWORD, 498D70 writes UI85604. This is S2C27;
  the unrelated C2S27 is the installed inventory discard request.

The native trade confirm button is controlB/flag20, ProgramMsg726, mode2.
483C80 mode2 submits money if needed, sends2C00 and marks local confirmed state.
The generic D6/4EAC00 modal, bank61/62 and 232DCE three-slot UI are not this trade.

## Implemented storage, CUSTOM-0063

`SqliteTradeRepository` borrows a SQLite handle; its constructor/load never
install schema or create rows. Application explicitly installs the two trade
tables at native startup and provisions owned wallets at world readiness.
New wallets start0 by custom
policy; existing values are preserved. Tests fund wallets explicitly as fixtures.

The pure plan removes both sides' offers before assigning incoming items, so
released capacity can be used. Maximum8 distinct ordinary source slots per
side; no merge/invented metadata. Preserve item provenance and quantities.
Compute money in uint64 before checking native uint32 limits. Increment changed
physical-slot and wallet revisions once, not the transferred source revision.

Commit uses BEGIN IMMEDIATE, checks both complete owned snapshots and pending
battles, applies both sides, inserts a unique receipt, and reads back both sides
and the receipt before COMMIT. Errors roll back all writes. Tests exercise
wrong owner/stale snapshot/insufficient money/quantity/duplicate source/full bag/
overflow/revision limit, second-player write failure, altered or deleted receipt
triggers, successful partial/full exchange, conservation, unrelated character
preservation, replay and pending battle rejection.

The repository foundation's historical3-suite receipt remains at
`artifacts/research/native-trade-20261002/foundation.json`; it is not the
current runtime/deployment gate.

## Runtime authority and synchronization

`RecoveredTradeService` handles serialized live-session leases. Opening requires
two distinct ready owned characters in the same area/scene and complete30-slot
saved bags. Only qualified scalar MED02 consumables with the pinned native
item provenance are eligible. Equipment, enhanced/bound/quest/map instances
remain unqualified; no instance fields are silently dropped to admit them.
The native8-offer limit is enforced. A custom60-second inactivity timeout
cancels and restores saved inventory and purse. Original distance, eligibility,
stack merging and timeout rules have not been recovered.

Offers stay transient until both confirmations. The native coalesced2B+2C
batch is accepted. Confirmed offers cannot change; stale snapshots, scene/lease
changes, duplicate/mixed mutations, cancellation, disconnect and timeout close
and resynchronize canonical storage. Prepare both full inventory/purse replies
before the atomic commit.4F on cancellation is followed by all30 saved bag
slots and27 absolute purse;52 on success is followed by the same authoritative
projection. No local client refund is treated as persistent authority.
Coalesced common chat continues through the frozen existing chat route.

Run:

```
cmake --build build-town-visibility --config Release --target recovered-trade trade-repository trade-service recovered-world-records recovered-world-service god2-server-native-results
ctest --test-dir build-town-visibility -C Release -R "^(recovered_trade|trade_repository|trade_service|native_trade_machine|native_trade_tcp|native_party|native_party_tcp|recovered_world_records|recovered_world_service)$" --output-on-failure
```

Result:9/9 suites pass; native61/61; native/C++ five-producer comparison5/5;
actual isolated Application TCP3/3 trade cases and6/6 existing party cases.
TCP checks fragmented item offers, cancel/disconnect restoration, coalesced
money+confirmation, both-player settlement, relogin, replay, wrong target,
duplicate requests and mixed inventory mutations without spending assets.
The packet ledger also passes: its matcher now counts adjacent case labels.
The world parser test no longer misclassifies a structurally valid2A as unknown.

## Original TW/CN client acceptance

`artifacts/playtests/private-trade-20261002-05/run-result.json` records20 native
operations on the unchanged original client in a private desktop, one CP950
and one CP936 client, against immutable candidate01 on our own private server.
Both directions open29, offer a specified quantity through the real native
quantity dialog, confirm numeric money through **control12**, deliver2B+2C,
and cancel via2D. Both directions also complete two-player exchanges.
Read-only observations verify native escrow/peer item instances,30 bag cells,
27 purse,51 renderer money text and actual SQLite rows/receipts. Two settlements
conserve final money1000/2000 and total item counts10/8, with two distinct
receipts. All owned processes close, source/client/candidate hashes match,
unrelated saves are preserved and the foreground desktop is unchanged.
This is actual UI operation/native renderer-buffer acceptance, **not pixel
screenshot acceptance**. Earlier runs were fixture/control failures, not
qualified evidence. Native disconnect/relogin is still covered only by TCP,
not a claimed original-client screenshot or UI scenario.

## Formal deployment

`tools/operations/native_trade_release_20261002.py` pins sources, nine CTest
suites and the original-client receipt. It starts the candidate on a full
formal-save clone to qualify Application's explicit schema install;
`--migrate-only` would not exercise that path. Only two empty tables and the
receipt primary-key index may be added. All prior schema, migration history,
database metadata and saved-row fingerprints must match exactly.

The managed executable was replaced and server restarted, PID24828 at release.
`artifacts/releases/native-trade-20261002/deployment/release.json` reports
INSTALLED and saved_rows_preserved=true; installed snapshots prove the same
additive schema and all old rows preserved. Client/config were unchanged.
Frozen chat verification passed before installation; its baseline was retained.
Rollback restores only the executable and never an older player database.

Scoped qualification pass100% (9/9 suites,20/20 native UI operations);
this scalar consumable route is installed. Full trade rules, all item categories,
official economy and high-player-load acceptance remain incomplete. A
whole-game completion percentage cannot be calculated from these tests.
