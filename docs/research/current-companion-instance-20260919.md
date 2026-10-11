# Current Companion Incoming Instance, 2026-09-19

## Result

**Concrete current-native message/store writer binding found. Growth remains
OPEN.** For the existing `87690 -> B5BE0` companion display path, the packed
DWORD at record `+0C` comes from opcode-first message `+11` (hexadecimal).
Original instructions copy it unchanged through the slot store and the UI
record. This proves a client-side producer, not server-side construction of
Quality/Star, stat scaling, upgrades, growth, EXP, or live acceptance.

Only these new files belong to this deliverable:

- `tools/strike_lab/current_companion_instance.py`
- `tests/research/test_current_companion_instance.py`
- `docs/research/current-companion-instance-20260919.md`

No runtime/shared/CMake files, other agents' files, or data artifacts were
edited. No retired corpora were read or used as leads. The prior progression
report supplies the already proven selector semantics and downstream boundary;
its display/getter tests and source-table loading were not repeated. No ACTMIS
or quest-instance chain was investigated. The quest agent's independently
reported `3B/98E2B` result arrived after this native binding and tests were
established; it is context, not an input to this helper.

## Authority

Pinned image relative to `C:/Users/risei/Desktop/God2/God2-Server`:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.

SHA-256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

All instruction addresses below are hexadecimal RVAs; load base is `00400000`.
The full image hash is required before emulation. The helper imports no other
recovery helper or source corpus. It uses the already installed Unicorn runtime
at `artifacts/tooling/crypto-oracle-python`. No gameplay table is needed for
these copy instructions; synthetic bytes are explicitly test probes.

## Exact Binding

Let `M` be the opcode-first message pointer, `O` the store owner, `U` the UI
object, and `s` the slot. The following relationship was executed in bounded
slices, with the same store memory retained between the two copies:

```text
M[0] = 3B
s = signed byte M[2]
record = M + 5                          (20 bytes)
packed = little-endian DWORD M[11h]

98E2B: [O + 85610h + 24*s + 0Ch] <- packed   (four-byte copy)
87416: [U + 3AC4h + 0Ch]         <- packed   (four-byte copy)
87230..876AC: wrapper third argument = U + 3AC4h

Existing static continuation:
876B8 pushes that pointer as B5BE0 argument 6; 876C9 calls B5BE0.
B7817 reloads argument 6 into EBX; target is [EBX+0Ch].
Quality = bits 20..23; Star = bits 16..19 (prior progression evidence).
```

| Stage | Current native binding | Evidence level |
| --- | --- | --- |
| Primary dispatch | `68B50` reads opcode byte; table `6B5D4 + 4*3B = 6B6C0` points to `6A029` | Executed |
| Primary handler argument | `6A029` increments message pointer; `6A030` pushes it; `6A031 -> 98DD0`; owner is `EBP+A7F2F6C` | Executed |
| Secondary dispatch | `1193C4` reads opcode; byte `119A04+3B` is 12; table `119908+4*12 = 119938` points to `1194F2` | Executed |
| Secondary handler argument | `1194F5` forms `M+1`; `1194F9 -> 98DD0`; owner is `[EBP+20]` | Executed |
| Handler source/slot | `98DD8` reads `[argument+1]`; `98E0A` sign-extends it; `98E16` forms `argument+4` | Executed |
| Store writer | `98E19` forms `O+85610+24*s`; `98E26` sets count 5; `98E2B rep movsd` copies the 20-byte record | Executed |
| UI store selection | `8739A` reads signed WORD `[O+855F0]`; `8740F` forms `O+85610+24*s` | Executed |
| UI record writer | `873FE` forms `U+3AC4`; `87416 rep movsd` copies five DWORDs | Executed |
| Adjacent UI fields | `8741C` writes record's first WORD to `U+3AD8`; `87429` writes low selector byte to `U+3ADA`; `U+3ADB` is untouched by this slice | Executed |
| Wrapper argument | `87238` pushes the record pointer; `87245 -> 87690`; `87691` loads it as third argument into ESI | Executed, stops before `876AC -> 59A60` |
| Downstream display argument | `876B8/876C9`, `B7817` | Static here; prior boundary retained |
| Reset writer | `869FC` writes DWORD zero at `U+3AD0`; entire reset writes six DWORDs covering `U+3AC4..3ADB` | Executed |

There is no mask, shift, arithmetic conversion, saturation or rounding on the
packed DWORD in either copy. Both copy operations use five four-byte elements,
little-endian order, and an explicitly clear direction flag. The existing
Quality/Star selectors therefore refer to the two nibbles of message byte
`M[13h]`: high nibble Quality, low nibble Star. That byte-location conclusion
combines the new lossless copy evidence with the prior selector evidence.

The test message occupies 25 bytes because the observed read is `M+5..M+24`.
This helper does **not** independently certify a fixed wire framing length,
transport header, encryption, or a real captured companion packet.

## State Conditions

- The handler tests the slot as a signed byte. Values `00..31` (0..49 decimal)
  reach the copy; `32..FF` stop at rejection `98FBD` in the tested state.
- For slots `26..29` (38..41 decimal), DWORD `[ [O+574C0] + 24 ] == 1` takes
  a call to `961A0` before the copy. Tests stop at `98E05` before that call.
  This means the branch is unexecuted beyond that boundary, not that the native
  function permanently rejects the slot. Other tested values 0, 2 and FFFFFFFF
  proceed directly to the copy.
- UI entry `87350..87372` requires signed WORD `[O+855F0] >= 0` and bit 0 of
  the second stack argument. Its negative and flag-false paths reach `874C0`.
  The positive path stops before record access and `9B770`. No upper bound is
  claimed from this entry gate.
- Starting separately at `87394`, the selection accepts nonnegative slots
  0..29, 42 and 43. Other in-store slots stop at `873B3`, before message/UI
  calls. The earlier `9B770` call is not executed or given a fake return.
- `87206..87230` statically binds a zero low WORD event argument to
  `EDI=U+3AC4`, then calls `874D0`. The new caller slice starts at `87230`
  with that declared EDI value. It executes through the real `87690` prologue
  and stops before its metadata getter. Its fourth argument is the sign-extended
  byte at `U+3ADB`; the test probe `81` becomes `FFFFFF81`.

These are separate native slices with declared live-ins. They do not assert
that skipped UI calls preserve arbitrary state or that no other packet/UI
writer can later change the stored instance. The reset is explicitly a second
writer and prevents interpreting an all-zero UI record as proof of a received
zero Quality/Star instance.

## Execution Limits

Synthetic owner `12000000`, UI `13000000`, SP `14008000`, message `15000100`,
auxiliary object `16000000`, and secondary dispatcher object `17000000`.
Native code is read/execute; message, auxiliary and secondary pages are
read-only to native execution. Stack writes and each slice's exact destination
range are checked. Slot-store neighbors, record padding and UI neighbors retain
A5 poison. Each copied DWORD has an observed read PC, source address, width,
write PC, destination address and value. No game/CRT adapters are present.

Every slice has an instruction allowlist, exact stop PC, 300-instruction budget
and 1-second timeout. Negative checks cover changed-image rejection, unexpected
callee execution, writes outside the declared destination, null-owner faults
and malformed helper inputs. No tests are skipped if the pinned image/runtime
is unavailable. JSON includes code-interval hashes and the exact executed PCs;
the interval list is an allowlist, not a claim that every byte in it executed.
Static-only intervals separately retain the buffer-return function `13650`,
receive-buffer fill `13558..13597`, dispatch tables and downstream pointer link.

## Verification

From `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B -m unittest tests.research.test_current_companion_instance -v
python -B -m tools.strike_lab.current_companion_instance --native-image artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin
```

**8 tests passed, no skips, 12.299 seconds, exit 0.** Standalone CLI also exited
0. Coverage includes 512 native dispatch/slot cases, 24 auxiliary-state cases,
45 UI entry-gate cases, 50 UI selection cases, the reset and caller pointer.
The 288 two-copy transfers cover both dispatches, four admitted UI slots, all
32 individual DWORD bits, zero, all-one and alternating-bit patterns. Expected
write addresses/widths/values are independently constructed in the tests.

Canonical slot-case SHA-256:
`8ecc1af24c0f4a131fcedd602483668c5dfc2f7661e12b8b3b618ed4b5bbffc6`.

Canonical two-copy transfer SHA-256:
`458d9c29a4fc8e6eba7ed42c479967cf353ddac131b6f7767b54dd1a3e8812ee`.

Raw Windows CLI stdout SHA-256 (including newline translation):
`d3b4d765bd2a2c44aa79923b72d47393c441f938c664e2a0879b97f32e90d649`.

The exact remaining producer boundary is **how the remote/server producer
constructs message DWORD `+11h`, and under which actual instance transitions**.
This deliverable establishes a native receive-dispatch/store/UI binding, not
that upstream rule. Growth, stat effects, upgrade rules and EXP remain OPEN.
Main embedded-scene and integration regressions are owned by the main task;
their results are not counted here.
