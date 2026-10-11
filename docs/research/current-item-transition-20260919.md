# Current item state to request selection

## Delivered behavior

One native-confirmed dependency is now executable: **original inventory state
determines which duplicate slot the original item-ID caller places in C2S25**.
This advances beyond encoding/decoding an already-chosen request.

For item IDs 5301 and 5501, the original resolver searches slots **29 down to 0**
and chooses the first whose signed count is positive and low item-ID word matches.
It ignores matching entries in slots 30..49. The outgoing slot therefore need
not be the slot supplied to the slot entry, or the index of the action record.
An S2C41 clear of the highest matching slot changes the next selection to the
next lower match. Requests themselves preserve the entire inventory.

Example with item 5301 in slots 3, 29 and 49, and raw tail A5:

| State | Original C2S25 output |
| --- | --- |
| Before clear | `25 B5 14 1D A5` (slot 29) |
| After original S2C41 clears slot 29 | `25 B5 14 03 A5` (slot 3) |
| After slot 3 also clears, leaving only slot 49 | No request |

The test supplies S2C41 updates as independent inputs. **This does not establish
S2C41 as a response to C2S25**, nor establish a use, equip, consume, ownership,
quantity, reward or effect rule. There is no server mutation to implement from
this evidence. Production C++ remains unchanged; the existing C++ inventory
encoder and request decoder are compiled and exercised by the new tests.

Only these new source files are delivered:

- `tools/strike_lab/current_item_transition.py`
- `tests/research/test_current_item_transition.py`
- `docs/research/current-item-transition-20260919.md`

## Legacy sources searched first

Classic root:
`C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`.

- `src/God2.ClassicServer.Runtime/ObservedItemRequestWireCodec.cs`: older C2S25
  structural evidence, opaque tail, and references to older response captures.
  Its nonzero-ID/slot/state restrictions do not establish current server rules.
- `src/God2.ClassicServer.Runtime/OfficialInventoryActivationWireCodec.cs`:
  separate C2S28 and older caller quantity-one evidence. Not applied to C2S25.
- `src/God2.ClassicServer.Runtime/GameplayCoreInventoryRuntime.cs:556`:
  `RemoveItem` checks quantity and removes from slots in descending order.
  This is legacy server code, not authority that the current request consumes
  anything. No quantity/removal behavior was copied.
- `tools/God2.GameplayContentRecovery/OfficialItemUsageFlagCatalogWriter.cs`:
  explicitly keeps activation blocked pending an official item-use transition.

XJZ root:
`artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`.

- `cpp/xjz_item_effect_contracts.hpp`: interface/rule/result definitions, not
  current native gameplay execution evidence.
- `evidence-item-effect-capture-target-v0.md`: 2,608 requested capture targets,
  **zero** item-effect execution samples; requests pre/post state, consumption,
  failure and packet results. This remains an unresolved evidence requirement.
- `evidence-item-service-template-v0.md` and
  `evidence-item-effect-rule-v0.md`: newer-client static routes, not current
  server effects. The prior inventory notes also establish zero warehouse
  inventory synchronization samples.

Read before native work: the four requested inventory/item research documents,
`current-inventory-20260919.md`, `test_current_inventory.py`,
`test_inventory_request_blackbox_followup.py`, `test_recovered_inventory.cpp`,
`RecoveredInventory.h` and `RecoveredInventoryItemRequest.h`.

## Current source authority

Mapped original image:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
All addresses below are RVAs; image base is `400000`. The oracle verifies the
hash before execution and maps original code read/execute only.

| RVA | Verified instruction behavior |
| --- | --- |
| `AE520..AE56C` | Enclosing caller; mode at context+A3D08 selects record bank. Tested mode is zero. |
| `AE56C..AE589` | Index selects six bytes at context+A3D18+6*index; copies dword then word to stack. |
| `AE5C1..AE5CD` | Record kind word zero takes dword at record+2 and calls `963C0`. |
| `96390..963A4` | Slot entry checks context+866E4 and signed low-byte slot 0..29. |
| `963A6..963B5` | Loads only DX from context+85610+24*slot, leaving EDX's upper word, then calls `963C0`. |
| `963C9..963DE` | Resolver returns for nonzero gate or zero low item-ID word. |
| `963E4..96404` | Searches 29..0; requires signed slot count >0 and matching low ID word. |
| `96406..96417`, `59A60..59A7B` | Executes original item-definition pointer lookup; empty table returns null. No matching slot plus null definition returns without sending. |
| `9643F..96462` | Low item ID divided by 100; quotients 53 and 55 select C2S25 branch. No category/effect names inferred from the arithmetic. |
| `964BB..964C1` | Pushes literal 1, resolved slot, original item argument; calls `96350`. |
| `96350..96380`, `132E0..13365` | Complete original producer and queue append; third argument remains ignored. |
| `68B61`, `6A04D`, `991E0..992F7` | Original dispatch and complete S2C41 consumer update the same slot storage. |
| `992F0`, `9B850`, `9B720`, `9B770` | Original refresh and definition lookup helpers execute; no resource/helper return is stubbed. |

The action-record path is stronger than a direct producer invocation: record
bytes 2..3 supply the requested ID, byte 5 supplies the outgoing opaque tail,
and byte 4 is overwritten by the resolved slot. Tests vary record byte 5 while
holding incoming EDX at a different value. The raw trailing word is not named
quantity. For the separate slot entry, the outgoing tail instead derives from
incoming EDX bits 24..31; literal third argument 1 is still not serialized.

A direct-call byte scan found `963C0` references at `963B5` and `AE5CD`; both
instruction callsites were disassembled. No direct E8 caller of `96390` was
found in scanned RVA range 1000..16FFFF. Its function executes in the fixture,
but no live input route to that wrapper is claimed. `AE520` is executed from
its entry through return; mode one and nonzero record kinds are not covered.

Current client source `../God2/Data2/Patch/Comm/gamedata.csvZ` is independently
read by `build_items` in the source test, SHA256
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.

| Definition | Decoded line | Resource key | Raw row SHA256 |
| --- | --- | --- | --- |
| PET:5301 | 6553 | Pet02001 | `c21baacb33cb7a6648e4c5605d7893caa4f13d873267da7fecb0c3ee124b9aa6` |
| SPI:5501 | 8178 | Spi01001 | `447b9383f38baf52c7078e425cfe6750c3b3507e183908d9729361cafde9a380` |

These are real current IDs; their existence does not make synthetic inventory
authoritative. Their definitions are not loaded into original item structures.

## Verification and fixture limits

From the server root:

```powershell
python -B tests/research/test_current_item_transition.py -v
python -B -m tools.strike_lab.current_item_transition
& artifacts/item-transition/inventory.exe
```

Seven focused tests cover the complete original action-record caller, all 30
searchable slots, duplicate resolution, mismatched identity, signed occupancy,
clear/replacement/repeated-request transitions, gate/slot/zero-ID early returns,
and the two concrete caller sources of the opaque tail. Existing C++20 fixture
compilation uses warnings as errors, with all build outputs confined to
`artifacts/item-transition`. No shared CMake or build tree is used.

Final run on 2026-09-19: **7 tests passed in 5.895 seconds**, exit code 0.
The standalone C++ assertions also passed. The module demonstration returned
`25b5141da5`, then `25b51403a5`, then an empty request, with
`server_use_result: null` as shown in the transition table above.

The tests run 72 full original S2C41 dispatch/consumer executions and 97 complete
caller executions, including 81 real producer/append calls. Eight S2C41 inputs
come from the existing production C++ encoder and pass original zero-seed
decrypt/checksum before consumption; the other logical inputs are explicit
synthetic fixtures. All 81 emitted records are checked independently and passed
to the existing compiled C++ request decoder. This does not rerun parser fuzz
or guard-page sweeps, and does not execute the buffered receive parser.

Every native execution has a 100,000-instruction cap, checks its exact return or
dispatcher stop and balanced stack, and checks the complete mapped context,
network object, companion, manager and definition-table regions. Write hooks
allow only stack and the specific slot count/ID stores or queue append/length
stores. Queue prefix/suffix canaries and all 21 untouched slot bytes are checked.
The lookup table and packet page are read-only during execution. No instruction,
callee or branch result is replaced. The optional queue lock is null; queue
flush and nonnull locks are outside scope. A canary extending into the lock
pointer initially caused an unmapped read; it was corrected to stop before
NET+40D4, preserving the explicit null-lock fixture.

The UI controls are inactive, the item lookup table is explicitly empty, manager
mode is zero, slot metadata has A5 residual bytes, selected slot is out of range,
and companion selection is FF. This permits full original positive-count refresh
to return without requiring loaded item graphics. It proves this concrete native
path, not a populated resource-loaded UI or a full nonempty inventory bootstrap.
Separate raw-slot fixtures isolate the caller predicate before S2C41 normalizes
zero/negative signed counts. There is no client launch, UI, socket, live server,
database, Lua, shared runtime change or gameplay effect in this delivery.

## Exact next input

To implement actual item use, obtain a **current-build original server handler
or a matched request/response execution sample** for PET:5301 or SPI:5501 through
the kind-zero action-record path. The sample must include the six-byte action
record, pre-request inventory (slot count plus all 24 bytes), actual C2S25 bytes,
ordered S2C records and post-request inventory/actor state, including rejection
or no-op results. It must distinguish repeated same-ID slots and establish which
server operation, authorization checks and state change occur. No amount of
client request selection alone supplies those rules.

For resource-loaded client verification, the separate precise input is the
original gamedata loader's item structure/table mapping consumed at
`59A60`, including the flags at definition+11A/+11B and icon fields +116/+118.
Those fields cannot be fabricated from the static importer without verifying
the original mapping. A server ownership/effect implementation remains unknown.
