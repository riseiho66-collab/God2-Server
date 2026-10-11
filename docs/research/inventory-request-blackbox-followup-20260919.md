# Inventory request black-box follow-up, 2026-09-19

## Delivered API

No existing C2S25 decoder defect was reproduced. The narrowly missing API is
`RecoveredInventoryItemRequest::encode(Request)`: a constexpr, noexcept,
allocation-free reconstruction of one five-byte C2S logical record. It returns
`LogicalRecord`, an array containing `25 item_lo item_hi raw_slot raw_tail`.
The decoder remains unchanged. Every representable field is preserved, including
item zero, raw slots 50..255 and tail 128..255.

This is useful for lossless request reconstruction and offline replay. It does
not send packets, implement the client UI gate, authorize ownership, infer an
effect, mutate inventory, or establish a response. Callers supply an explicit
opaque tail; no quantity or default tail is introduced.

Only these Lane D files were changed:

- `src/protocol/RecoveredInventoryItemRequest.h`
- `tests/research/test_inventory_request_blackbox_followup.py`
- `docs/research/inventory-request-blackbox-followup-20260919.md`

No CMake, shared build, state/summary, runtime, Lua or SQLite changes were made.

## Evidence Reviewed

Before implementation, read `current-inventory-item-request-20260919.md`,
`current-inventory-exact-validation-20260919.md`,
`current-inventory-20260919.md`, the production request decoder, the existing
inventory Python tests, and their C++ process fixture.

Both required legacy roots were consulted:

- `artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`:
  `evidence-warehouse-storage-v0.md` records zero inventory synchronization
  samples; `cpp/xjz_item_effect_contracts.hpp` describes older effect interfaces
  without proving current request authorization or effects.
- `C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`:
  `src/God2.ClassicServer.Runtime/ObservedItemRequestWireCodec.cs` preserves an
  opaque C2S25 tail but adds older world-state, nonzero-ID and maximum-slot
  checks. `OfficialInventoryActivationWireCodec.cs` concerns separate C2S28
  activation semantics. Neither supplies new current-client rules here.

Authority is the current original image:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
The new runner verifies this hash before executing original instructions.
Fresh Capstone disassembly reconfirmed these RVAs:

| RVA | Original behavior |
| --- | --- |
| `96350..96358` | Any nonzero context+866E4 value returns before reading the queue pointer. |
| `9635A..9637B` | Low item word and low slot byte form C2S25; the first argument's high byte survives as tail; third argument is unused. |
| `132F0..132FE` | Append flushes only when resulting length exceeds 0xA00, so equality is permitted. |
| `13303..1330B`, `13352..1335C` | Null optional lock pointer bypasses lock/unlock calls. |
| `13312..1334C` | Append copies opcode plus four payload bytes and advances queue length. |
| `13365`, `96380` | Original append and producer return normally. |

These instructions support a structural encoder. They do not prove any
server-side ownership rule or that UI callers permit arbitrary slot arguments.

## New Risk Coverage

The dedicated runner imports existing VM helpers without inheriting or running
their unittest methods. It creates a separate C++20 executable in a private
temporary directory, with `/W4 /WX` on MSVC (or warning-as-error equivalents).
The executable includes only the production request header and standard
library headers. Its line-oriented commands are a test adapter, not a new
production batch API. Compile-time assertions check maximum-field encoding
and the noexcept contract.

1. **Mutation and rejection recovery:** 1,276 records comprise a seed and every
   alternative value at each of its five byte positions. Each is surrounded by
   a truncated or extended record and a distinct valid recovery record, making
   3,828 calls in one C++ process. Rejected records cannot leak a previous result;
   accepted payload mutations re-encode byte-for-byte, and the input buffer must
   remain unchanged. Prior isolated-process length/opcode tests did not cover
   this new reconstruction API or sequential rejection recovery.
2. **Inventory and gate transitions:** 54 raw slots (0..49, 50, 127, 128, 255)
   each receive open/blocked/reopened gate calls, sharing one original queue.
   Synthetic slot state alternates between zero occupancy and distinct occupied
   metadata with IDs unrelated to request IDs. Eight ID boundaries and varying
   opaque tails are used. All 162 original calls preserve the complete mapped
   UI context, including inventory. The 108 ungated requests match C++ encoding.
3. **Exact queue boundary:** four original appends advance length 2,540 to exactly
   2,560, then two nonzero-gate requests leave the full queue untouched. The four
   emitted records match C++ encoding. The prior short-prefix fixture did not
   exercise equality at the native queue threshold.

In total, 168 original producer invocations execute through the real append
routine where ungated, and 112 encoded records match their output. Each call
checks balanced stack, whole network-object state, whole UI-context state,
queue prefix/suffix canaries and a write allowlist limited to native stack,
new queue bytes and queue length. Each native call has a 100,000-instruction
cap and must reach its exact return address. No original instruction, callee
or branch result is stubbed.

## Executed Verification

From `C:\Users\risei\Desktop\God2\God2-Server`:

```powershell
python -B tests/research/test_inventory_request_blackbox_followup.py -v
```

Result: exit code **0**, **3 tests passed in 3.686 seconds** on 2026-09-19:

```text
test_mutated_records_and_rejection_recovery_in_one_process ... ok
test_native_exact_queue_capacity_and_gated_full_queue ... ok
test_native_requests_across_inventory_and_gate_transitions ... ok
Ran 3 tests in 3.686s
OK
```

The prior S2C41 encoder, 12,800 scalar cases and guard-page sweeps were not
rerun. Their implementation was untouched; the new tests target request-only
risks and the new encoder.

## Limits

All verification is internal and offline. Inventory contents are explicit
synthetic preconditions, not granted or loaded items. The observed absence of
producer inventory writes is not a claim of server ownership validation.
The client gate remains an unnamed raw context field, not an inferred login,
combat or inventory state. Queue overflow/flush, nonnull locking, transport
framing/encryption, resource-loaded UI callers and live server handling are
outside this fixture. No actual client, UI automation, sockets or public
connections ran. This is not live E2E, an item-use implementation, or a claim
of gameplay effects, rewards, ownership operations or persistence behavior.
