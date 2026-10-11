# Current inventory occupancy projection

## Result and integration boundary

`god2::RecoveredInventory` in `src/protocol/RecoveredInventory.h` implements a
bounded S2C occupancy-clear projection for the pinned current client. It does not
infer character creation equipment, owned items, quantities, or grants.

API:

- `clear_slot(size_t)` returns an optional 5-byte logical record; rejects >= 50.
- `empty_owned_inventory()` returns 250 logical bytes, clearing slots 0..49.
- `decode_slot_update(span<const uint8_t>)` decodes exactly one S2C41 record,
  preserving `client_item_id`, `slot`, and `raw_count`. This is NOT a C2S handler.
- `RecoveredWorldFrame::encode(logical)` supplies the existing zero-seed envelope.
  One clear is 8 wire bytes; the 50-slot batch is 253 wire bytes.

Example for an already-established, authoritative empty 50-slot owned state:

```cpp
const auto logical = god2::RecoveredInventory::empty_owned_inventory();
const auto wire = god2::RecoveredWorldFrame::encode(logical);
```

Integration is deliberately left to the parent. Require the current world
dispatcher and initialized inventory/UI context after world-ready. There is no
evidence here that absent database rows establish empty starting inventory.
Slots 30..49 include equipment/special branches; this is not a 50-slot bag-capacity
claim. No CMake, Session, Application, importer, persistence, or runtime edits.

## Exact current contract

Native image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
32-bit image base 0x400000; all addresses below are RVAs, equal to file offsets.

| Evidence | Original instructions / effect |
| --- | --- |
| Size table `1324 + 4*41` | Points to `12AC`, `mov eax,5; ret` |
| World table `6B5D4 + 4*41` | Points to `6A04D`; increments packet pointer and calls `991E0` |
| `991E8..991F5` | Signed slot byte at body+2 must be >=0 and <0x32 |
| `991FB..99204` | Body+3 writes count byte at UI+8560C+24*slot |
| `99212..9922D` | Body+0 u16 replaces low 16 bits at UI+85610+24*slot |
| `99236..99266` | Signed count <=0 clears count and low item-id word |
| `99268..992A9` | Special slot branches: 38..41, 42..44, and 45 |
| `992A9..992F7` | Selected-item/companion UI refresh and slot renderer |
| `98D30..98D5F` | Query for slots 0..37 returns null when low item-id word is zero |
| `97FE0..98025` | Local initializer clears 0x12C dwords = 50*24 slot bytes |

Logical record: `41 item_lo item_hi slot raw_count`. Canonical clear:
`41 00 00 slot 00`. Slot bounds are consumer-proven, not copied from Classic.
Counts 0x80..0xff also clear under the native signed test; the builder emits only
zero, and the decoder preserves raw counts without claiming stack rules.

Clear is an absolute occupancy update, not a decrement. Exactly three bytes of
each 24-byte slot change: count at +0 and item id at +4/+5. The dword store at +4
preserves its upper word. All remaining 21 bytes retain their previous values.
This is NOT a full item-structure reset or an equipment-stat recalculation.
The local initializer also clears currency/other structures, but no safe wire
bootstrap invoking that initializer was established here.

## Tests and precise state limits

Run `python tests/research/test_current_inventory.py -v` from the server root.
The runner builds only `tests/test_recovered_inventory.cpp` as C++20 in a private
temporary directory, with warnings as errors. No shared build is used.
Validation on 2026-09-19: all six unittest methods passed, including standalone
C++ assertions and native populate-then-clear residual-state checks.

Original code executes for:

- Zero-seed decrypt/checksum, then parser `13420`, `13650`, `13670`: exactly 50
  records consumed; original parser returns incomplete for lengths 1..4.
- Full world dispatch `68B61` through `6B517` and consumer `991E0`, for all 50
  zero-count records. No callees or branch results are stubbed.
- Guard-page packet placement and whole-array/canary comparison. Write hooks
  permit only native stack writes and the selected count/item dword stores.
- Prior population by the real positive-count scalar instructions (stopped at
  `992A9`, before resource-dependent refresh), followed by full C++-generated
  clear consumption for all 50 slots. Native lookup for slots 0..37 changes from
  the occupied pointer to null. Repeated clear is idempotent for slot memory.
- Signed count oracle for 0,1,30,127,128,255 and slot boundaries/special groups;
  invalid slots 50,127,128,255 leave the array unchanged.
- Black-box C++ rejection of every truncated record, extended record, wrong
  opcode, invalid slot and invalid CLI input; valid decoded fields agree with
  the original scalar oracle. Original checksum rejects a corrupted checksum.

The full-consumer fixture uses synthetic initialized context: UI+232DC8 and
UI+232DD6 are -1 (inactive controls); UI+85ABD is 0xA5 (outside slots 0..49);
UI+232EBC points to mapped companion UI whose selected slot byte +21236 is 0xff;
UI+574C0 points to a manager with +24 != 1; UI+71 is 1, taking D71F0's existing
early return. Old metadata is 0xa5, so special item-category branches do not
activate. Tests prove original behavior in this explicit context, not every
equipment-category/UI mode or a resource-loaded live world. Other contexts can
run additional original UI/companion routines. No sockets, UI, auth, or client
process is launched. No gameplay results are manufactured.

## Both evidence corpora examined before reversing

Classic root:
`C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`.
Files under `src/God2.ClassicServer.Runtime`:

| File | SHA256 |
| --- | --- |
| OfficialInventoryBootstrapWireCodec.cs | `657c5e4d36455d2f9320f53493fdc6f0a7cdfb7f956e25a5a91d4f73ba3b88e5` |
| OfficialInventoryActivationWireCodec.cs | `78032e9e571bed8df1b2c0ccc8dec6d0d17a61c1f2537e16280f1283c5a34846` |
| ObservedItemRequestWireCodec.cs | `8d43c68107284286dc7465c28e8b039777494adef72a5c3e2c48d0bedea58f2d` |

Classic empty bootstrap emits no frames; its nonempty bootstrap replays one
merchant evidence profile. Its activation/item request codecs are C2S25/28
historical leads, not present-image proof. Its merchant codec's 57-byte purchase
and 25-byte sale envelopes differ from the current S2C3B/41 sizes (25/5 logical,
28/8 framed); the old purchase packet must not be copied into this implementation.

XJZ root:
`artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`.

| File | SHA256 |
| --- | --- |
| evidence-warehouse-storage-v0.md | `a17a49381f3c4c6dd15105d0a704b01f6536bf17c77c60f0d62e6309cfe8c66b` |
| evidence-account-character-sync-capture-target-v0.md | `a62746009dabf2f6c77e6ea38df09f3b86f344728dcfac0ebe37856e2a9dcfd4` |

XJZ reports zero inventory synchronization samples and explicitly distinguishes
desired fields from proven packet layouts. Neither corpus establishes current
new-character items. Current native consumers are therefore the authority for
this bounded clear projection. A later bounded C2S25 structural decoder and
original-producer oracle are documented in
[current-inventory-item-request-20260919.md](current-inventory-item-request-20260919.md).
C2S28 activation, item effects, nonempty item construction and birth inventory
remain outside these deliveries.
