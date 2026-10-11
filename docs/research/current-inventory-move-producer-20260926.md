# Current-client inventory move producer and minimal slot baseline

## Authority and scope

Current `God2.exe` SHA256:
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
Addresses below are virtual addresses, image base `00400000`.
The reconstruction's `decompiled/packet-producers/catalog.json` identifies the
queue call at `004966FD`; exact current executable instructions were then run
offline with Unicorn. No retired archive is an authority for this work.

`src/protocol/RecoveredInventoryMoveRequest.h` provides only the lossless
original C2S wire contract. Original server stack merging, exchange policy,
equipment rules and live acceptance are separate from this proof.

## Wire fields and native state

| Logical offset | Width | Meaning established by current client |
| --- | --- | --- |
| 0 | 1 | Opcode `24` |
| 1 | 1 | Source slot: low byte of producer argument 1 |
| 2 | 1 | Destination slot: low byte of producer argument 2 |

Producer `00496610` sends exactly two payload bytes through `004132E0`, then
returns with `ret 8`. It does not reject any byte value or equal source and
destination. There is no opaque or uninitialized tail. It returns without
sending when UI dword `+866E4` is nonzero. It checks four signed dialog indices
at `+232DEA`, `+232DE6`, `+232DFE`, `+232E20`: negative means absent; otherwise
flag `20` at `UI+E2988+index*2A08` takes the error-message path before queueing.

The two current UI callers establish field order:

- `0049B5AC..0049B5B6` in `0049A330`: read `UI+855F0`, push destination EBX,
  push source, call producer. Cleanup at `0049B5BB` only clears selection to FFFF.
- `0049EF1C..0049EF26` in `0049EAB0`: the same source read, destination EBX,
  argument order and selection cleanup. This caller handles a selected source
  followed by another inventory-slot click.

These callers distinguish bag slots `0..29` from equipment/special slots
`30..49`. An implementation restricted to owned, explicitly persisted bag slots
is a deliberately bounded server policy, not a newly recovered original rule.
No optimistic item-record swap was found in these producer/caller suffixes.

## Initial full-slot state is actually zeroed

`00497FE0` sets EDI to `UI+8560C`, ECX to `12C` (300 DWORDs), EAX to zero,
then executes `rep stosd` at `00497FFA`. This clears all `50*24=1200` inventory
bytes, including each slot's entire 20-byte metadata region. Calls are present
from `00468120` (character reset path) and at the start of `00498030`
(inventory initialization).

The native oracle poisoned all 1200 bytes and both adjoining canaries. The full
initializer zeroed exactly the slots and left both canaries intact. It then ran
the original `004991E0` scalar S2C41 consumer for item IDs 5569, 3101 and 3107
in slots 0, 5 and 29, stopping at `004992A9` before resource-dependent refresh.
All nine results were exactly:

```text
count:u8 00 00 00 item_id:u16le 00...(18 bytes)
```

Thus `item_id + 18 zero bytes` describes the metadata actually established by
the existing scalar-only projection on a freshly initialized slot. This does
not prove that an arbitrary reused live slot has no other metadata, nor recover
original enhanced-item attributes. A server can explicitly limit new minimal
projection to already qualified plain map/MED items and document that policy.

S2C41 only replaces count and low item-ID word. S2C3B's `00498DD0` copies 20
metadata bytes and updates count; S2C3C's `00498FD0` removes counts. The separately
assigned response investigation owns construction/acceptance of a move response.

## Reproducible verification

Compile `tests/test_recovered_inventory_move.cpp` with C++20 and `src` includes;
the isolated MSVC `/W4 /WX` build command is retained in
`artifacts/reports/current-inventory-move-20260926/build-codec.cmd`.

```powershell
python -B -m tools.strike_lab.current_inventory_move --probe artifacts/reports/current-inventory-move-20260926/codec.exe --report artifacts/reports/current-inventory-move-20260926/native-producer.json
python -O -B -m tools.strike_lab.current_inventory_move --probe artifacts/reports/current-inventory-move-20260926/codec.exe --report artifacts/reports/current-inventory-move-20260926/native-producer-optimized.json
```

Both runs pass: 1162 original producer/queue vectors, 15 gate/modal vectors,
12 original caller-suffix vectors, 9 initialization/scalar-baseline cases.
The compiled production codec exhaustively checks 65,536 byte pairs, 256
opcodes and lengths 0..8, and decodes every native output for comparison.
Code execution and writes are bounded; no instruction, game callee return, or
queue behavior is substituted. Reports retain exact executable-span hashes.

## Prepared private-client verification

`tools/strike_lab/private_inventory_move_ui.py` is a private-desktop sidecar
for an explicitly specified disposable client copy and copied SQLite fixture.
It logs in, drags slot 0 to 5 and back, and checks read-only DB rows/revisions,
unchanged position/other slots, full 24-byte live slot records, server success
markers and process liveness. It requires the runner's `God2Lab-*` desktop and
refuses the input desktop. It takes no screenshot or process-memory write.

The static slot table at `005901C0` places slot 0 at `(20,283,59,322)` and
slot 5 at `(20,328,59,367)`. With the existing private fixture's inventory panel
placement, the established slot-0 point `(580,302)` implies slot-5 `(580,347)`.
The helper caches the initial UI base; it never mistakes the relocated slot-5
item for slot zero when checking the result. Script preparation is not live
acceptance; a successful own-server run must be recorded separately.
