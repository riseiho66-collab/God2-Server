# Inventory exact-record validation coverage

## Gap and focused change

Review of `RecoveredInventoryItemRequest`, `RecoveredInventory`, the native
inventory tests, and the current inventory/item-recovery notes found no decoder
implementation defect. Both decoders already require exactly five logical bytes
and the correct directional opcode. Existing C++ inputs used vectors/arrays;
their adjacent readable storage could hide an out-of-span decoder read.
S2C rejection coverage also sampled only one wrong opcode and a few invalid slots.

This patch closes those coverage gaps without changing production protocol or
state handling. `tests/inventory_guarded_record.h` provides an inventory-only
fixture with a read-only middle page and inaccessible pages on either side.
The C++ fixture exposes `--guarded-decode` and `--guarded-decode-item-request`.
Each command decodes at both ends of the middle page and checks decoded fields
against the ordinary invocation. The Python tests independently check expected
exit status and fields. An empty suffix span points at the inaccessible page,
so an attempted opcode read before checking length faults the test process.
Writes to the input also fault. Fixture allocation/protection failures fail the
test; there is no unprotected fallback. Guarded inputs are limited to one page.

## Evidence boundary

Authority remains the pinned current image, SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`:

- S2C41 size RVA `12AC`, dispatch `6A04D`, consumer slot test `991E8..991F5`:
  five bytes and slots 0..49, as documented in
  [current-inventory-20260919.md](current-inventory-20260919.md).
- C2S25 producer `96350` and queue append `132E0`: five bytes, low-word item ID,
  raw slot byte and retained high argument byte, as documented in
  [current-inventory-item-request-20260919.md](current-inventory-item-request-20260919.md).
  The producer does not apply the S2C slot bound or quantity semantics.

The existing native producer, consumer and transport oracles run unchanged.
Legacy findings remain reference material; no legacy gameplay rules are added.
No ownership, effects, quantities, persistence, runtime wiring or Lua behavior
is introduced. CMake and shared oracle bases are untouched.

## Verification

Command: `python tests/research/test_current_inventory.py -v` from server root.
Windows validation on 2026-09-19: **12 unittest methods passed in 23.027s**,
including all nine prior methods. The fixture compiles privately as C++20 with
warnings treated as errors, and the three added methods execute 743 processes:

- 26 boundary cases across both decoders: lengths 0..4, exact record, appended
  lengths 6..10, a concatenated pair, and a wrong opcode. Exactly two are valid.
- 461 S2C negatives: all 255 wrong opcodes and every invalid slot 50..255.
- 256 C2S positives: every slot and tail byte value, with distinct little-endian
  ID bytes. These preserve opaque data without interpreting or authorizing it.

All 743 cases use both protected placements (1,486 guarded decoder calls).
Rejected inputs return exit code 2 with no decoded output; accepted inputs
return exit code 0 and the expected three fields. A crash cannot count as a
successful rejection. Existing unguarded ID-zero/native-producer cases remain.

This is internal offline validation, not a live handler or gameplay result.
The POSIX mmap/mprotect fixture branch is included but was not exercised here.
Guard pages test immediate span-boundary reads and input writes; they are not a
general sanitizer or a proof against every possible memory access defect.
The original synthetic-context and resource-loaded UI limitations still apply.
