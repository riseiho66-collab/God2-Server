# Current inventory item-request structure

## Delivered boundary

`src/protocol/RecoveredInventoryItemRequest.h` adds a C++20 read-only decoder
for one logical C2S25 record: `25 item_lo item_hi raw_slot raw_tail`.
`decode(span<const uint8_t>)` requires exactly five bytes and opcode 0x25,
returning `client_item_id:u16`, `raw_slot:u8`, `raw_tail:u8` or `nullopt`.
The caller must already have validated transport framing and integrity.

No sender, response, ownership mutation, item grant, DB lookup or Lua effect is
added. Structural acceptance is not permission to use an item. In particular,
ID zero and raw slots 50..255 remain representable because the original producer
does not validate them. The S2C41 consumer's 0..49 range is not imported as a
C2S25 gameplay rule. The existing authoritative-empty prerequisite for S2C41
clears remains unchanged; missing DB rows still do not establish empty inventory.

## Evidence reviewed first

Both legacy roots were searched before native analysis:

- `C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`:
  `src/God2.ClassicServer.Runtime/ObservedItemRequestWireCodec.cs` describes C2S25
  as item u16, slot byte and opaque tail. Its nonzero-ID and maximum-slot checks
  belong to that older codec and are not evidence of current producer checks.
  `OfficialInventoryActivationWireCodec.cs` describes the separate C2S28 request.
- `artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`:
  `evidence-warehouse-storage-v0.md` reports zero inventory sync samples;
  `evidence-account-character-sync-capture-target-v0.md` explicitly separates
  desired fields from proven packet formats. `cpp/xjz_item_effect_contracts.hpp`
  and `evidence-item-effect-rule-v0.md` do not establish current item-use effects.

Existing `current-inventory-20260919.md`, `item-recovery-20260919.md`, inventory
source and native tests were read before implementing this addition.

## Current original-code authority

Image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Image base 0x400000; all locations below are RVAs/file offsets.

| RVA | Observed instruction behavior |
| --- | --- |
| 96350..96358 | Nonzero dword at context+866E4 returns without queueing |
| 9635A | Reads low word of first 32-bit stack argument |
| 9635F | Reads low byte of second stack argument |
| 96363 | Loads queue object pointer from context+86874 |
| 96369 | Rewrites only low word of first argument |
| 9636E..96375 | Passes first argument address, payload size 4, opcode 25 |
| 96377 | Replaces byte 2 of first argument with slot; byte 3 is untouched |
| 9637B | Calls original queue append 132E0 |
| 96380 | Returns, removing all three arguments; third argument was never read |
| 13312..1334C | Appends opcode plus four payload bytes and increments queue length |

The resulting tail is `(first_argument >> 24) & 255`. It is not copied from
the third argument, even when callers pass 1 there. Example original execution:
arguments `A5EE9234, 49, 1` append `25 34 92 31 A5`. Changing the first
argument's byte 2 does not change output; changing byte 3 changes the tail.
No quantity/effect meaning is assigned to that retained byte.

Direct callsites to 96350 were found at 84481, 964C1, 9A6B9, 9AA07 and EA85C.
These are static locators, not claims that the complete enclosing UI paths ran.

## Executed validation

Command from server root: `python tests/research/test_current_inventory.py -v`.
The test compiles `tests/test_recovered_inventory.cpp` as C++20 with warnings as
errors in a private temporary directory. No shared CMake files/build are edited.
The existing C++ test fixture gains `--decode-item-request HEX` for process-level
comparisons; the existing inventory test target can continue to use that file.

Nine unittest methods pass, including the previous six occupancy tests and three
new item-request methods:

- 263 native producer outputs passed to the compiled decoder. Byte sweeps use
  distinct little-endian ID bytes and a slot permutation; each raw slot and tail
  0..255 appears, plus explicit ID 0/1/255/256/7FFF/8000/FFFF boundary cases.
- 40 native executions vary tail, overwritten first-argument byte and ignored
  third argument; three nonzero gate values prove the no-append branch.
- Black-box rejection of every length 0..4, extended and concatenated records,
  every other opcode, and malformed hexadecimal CLI inputs.

Each producer run executes 96350 through its return and the complete original
132E0 append routine, with no stubbed code, calls or branch results. The synthetic
queue starts with a three-byte canary prefix, stays below its flush threshold,
and has a null optional lock pointer. Tests verify prefix/suffix preservation,
queue length, balanced stack, unchanged mapped UI context and a write allowlist
limited to stack, selected queue bytes and queue length. No client process,
network sockets, UI automation or authentication is used.

## Exact remaining gap

This is an internal, offline producer-to-decoder contract test. It does not
execute a resource-loaded caller, queue flushing, transport encryption for
C2S25, a live server handler, or item effects. A future integration needs proven
ownership and item-state validation, current operation semantics, and response
rules before authorizing or mutating inventory. C2S28, full inventory state,
starting items, equipment transitions and use results remain unresolved here.
There is no end-to-end or playability claim.

## Follow-up: S2C41 scalar synchronization encoder

`RecoveredInventory::encode_slot_update(SlotUpdate)` now returns an optional
five-byte `LogicalRecord`: `41 item_lo item_hi slot raw_count`. Slots 50..255
are rejected. Every u16 item ID and u8 count is preserved, including ID zero
and signed-clear counts 128..255. `ClearRecord` remains an alias of the same
array type, and the established empty projection APIs retain their behavior.
This is a scalar projection for an already-established client slot, not a
nonempty item constructor, full inventory bootstrap, or C2S25 response rule.

The targeted follow-up reread the current inventory/item recovery documents,
the existing native tests, Classic `OfficialInventoryBootstrapWireCodec.cs` and
`ObservedItemRequestWireCodec.cs`, and XJZ `evidence-warehouse-storage-v0.md`.
Classic only replays an older merchant profile for its nonempty bootstrap;
XJZ still has zero inventory synchronization samples. Neither establishes a
new current-client item effect, placement or grant rule.

Direct disassembly of the pinned image reconfirmed the authority:

- `991E8..991F5` rejects negative signed slots and slots >=50.
- `991FB..9922D` writes the count byte and low item-ID word, retaining the
  upper ID word. `99246` jumps directly to `992A9` for a positive signed count.
- `99248..99266` additionally clears count and low ID word for count zero or
  a negative signed count. Special clear effects begin at `99268`.

No encoder normalization is justified: a positive count with ID zero still
writes that exact scalar pair, while a nonzero ID with a signed-clear count
ends with count/ID zero in native slot memory. Repeated updates replace these
fields absolutely. They do not increment a quantity or reconstruct the other
21 bytes of each 24-byte slot.

### Independent composition and rejection tests

The standalone C++ fixture adds decimal `--updates ITEM SLOT COUNT ...` input
and builds framed batches using the production encoder. It validates wide
input values before narrowing, retains update order and duplicates, and emits
no bytes when any triple is invalid. The inherited envelope cap admits at most
512 five-byte records. This is a framing bound, not a bag-size rule.

Test-only `--frame-logical HEX` makes correctly checksummed malformed logical
records. Test-only `--decode-wire HEX` composes the existing frame decoder with
the slot decoder and validates all records before printing anything. Neither
adapter is a production batch API, handler, or transaction guarantee.

Five new Python methods cover:

- `test_encoder_native_all_slots_and_raw_counts_in_composed_frames`: 12,800
  encoder-produced records, every 50 slots x 256 raw counts, through original
  zero-seed decrypt/checksum, receive parser and world dispatch. Twenty-six
  frames share one native inventory state. Every record is checked against an
  independent little-endian packing and whole-array/canary state expectation.
  Write hooks permit only the native stack and selected count/ID stores.
- `test_encoder_snapshot_replacement_duplicate_order_and_residual_bytes`:
  all-slot scalar snapshot, reversed-slot updates, repeated updates, replace,
  clear, repopulate, ID-zero/positive-count pairs and final all-slot clear.
  IDs cover 0, 1, FF, 100, 7FFF, 8000, FFFF and 9234. Another 100 bounded
  scalar executions verify retention of distinct per-slot metadata bytes.
- `test_composed_response_truncation_integrity_and_invalid_late_record`:
  all 253 shorter wire prefixes; trailing/concatenated wire data; changed
  length bytes; all 255 alternative encrypted checksum bytes; all 200
  checksummed partial-record prefixes in a 50-record batch; and invalid
  opcode/slot records at the beginning, middle and end. Rejection emits no
  partial decoded output. All 49 shorter complete-record batches are accepted:
  the evidence does not require exactly 50 records per frame.
- `test_original_parser_partial_tail_after_each_snapshot_slot`: 200 partial
  tails after 0..49 complete records are reported incomplete by the original
  parser after it returns each complete prefix record correctly.
- `test_encoder_rejects_invalid_fields_without_partial_output`: incomplete
  triples, negative/overflow/nonnumeric fields, invalid late triples and 513
  records reject; a 512-record frame passes original decrypt/checksum and the
  composed C++ validation adapter.

Standalone assertions additionally sweep all 65,536 slot/count byte pairs
and all 65,536 item IDs, preserving canonical-clear compatibility. Compilation
uses the existing C++20 warning-as-error fixture in a private temporary folder.

Native positive-count paths stop at `992A9`, before resource-dependent refresh.
Full clear paths execute through the original dispatcher return in the existing
explicit inactive-UI/A5-metadata fixture. Distinct metadata clear checks stop at
`99268`, before metadata-dependent effects. A precise instruction hook ensures
the stop also holds when a cached translated block spans a previous slice's
boundary; it only stops emulation, without replacing instructions or callees.
Each slice retains a 100,000-instruction cap and asserts its exact stop address.

Exact parser exhaustion enters the original socket-read path, which is outside
this offline fixture. Complete batches are checked by their consumed cursor;
the incomplete-parser tests intentionally retain 1..4 buffered tail bytes.
This does not claim socket behavior or atomic application of a partial batch.

Focused rerun command for the five new methods:

```powershell
$inventoryTests = @(
  'CurrentInventoryTests.test_encoder_native_all_slots_and_raw_counts_in_composed_frames'
  'CurrentInventoryTests.test_encoder_snapshot_replacement_duplicate_order_and_residual_bytes'
  'CurrentInventoryTests.test_composed_response_truncation_integrity_and_invalid_late_record'
  'CurrentInventoryTests.test_original_parser_partial_tail_after_each_snapshot_slot'
  'CurrentInventoryTests.test_encoder_rejects_invalid_fields_without_partial_output'
)
python -B tests/research/test_current_inventory.py -v @inventoryTests
```

Final validation on 2026-09-19: **14 tests passed in 23.493 seconds**, comprising
the five new methods and the nine existing non-guard-page methods below.
The already-established 743-case/1,486-call guard-page work was not repeated.
No production defect was reproduced; this delivery adds the missing encoder
and verifies its native scalar synchronization contract. Two test-harness
boundaries discovered during development were resolved as described above:
socket reads after exact exhaustion and cached-block scalar stop placement.

```powershell
$inventoryRegression = @(
  'CurrentInventoryTests.test_standalone_cpp_and_current_dispatch'
  'CurrentInventoryTests.test_cpp_empty_batch_original_crypto_parser_and_all_fifty_consumers'
  'CurrentInventoryTests.test_native_slot_bounds_and_signed_count_field_oracle'
  'CurrentInventoryTests.test_original_populate_then_cpp_clear_preserves_residual_metadata'
  'CurrentInventoryTests.test_black_box_truncated_extended_wrong_opcode_and_slot'
  'CurrentInventoryTests.test_original_parser_truncation_and_native_checksum_rejection'
  'CurrentInventoryTests.test_item_request_original_producer_cpp_fields_and_raw_bounds'
  'CurrentInventoryTests.test_item_request_opaque_tail_unused_argument_and_original_gate'
  'CurrentInventoryTests.test_item_request_black_box_rejects_nonrecords'
)
python -B tests/research/test_current_inventory.py -v @inventoryRegression @inventoryTests
```

The remaining integration boundary is unchanged: no ownership authorization,
item grants/effects, full item metadata, resource-loaded positive-count render,
equipment rules, live runtime registration or Lua gameplay behavior is added.
The C++20 core and Lua gameplay architecture remain intact. No real client,
desktop, socket, shared build/CMake, persistence or common helper is touched.

Coordinator integration subsequently rebuilt the complete shared Release tree
and reran all 17 inventory Python tests, including the earlier guard-page
methods: passed in 28.053 seconds. The final 32 core CTest suites also passed.
These checks retain the scalar/rendering and gameplay boundaries above.
