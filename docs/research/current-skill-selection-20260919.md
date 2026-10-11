# Current skill bank-state transition, 2026-09-19

## Delivered contract

One previously unproven contract is now implemented: logical record `38 xx`
updates a primary skill bank's raw state, clears its stored state bits when
leaving state 2, and conditionally changes the current bank through an opaque
WORD key. This is a native client selection contract, not an original
authoritative server rule. No gameplay-completion or live-playability claim.

New files only:

- `tools/strike_lab/current_skill_selection.py`: pure, immutable, bounded
  `apply_selection_record(record, banks, current_bank_byte)` consumer.
- `tests/research/test_current_skill_selection.py`: independent Unicorn oracle,
  original dispatcher/wrappers/producer/accessors and a caller-gate slice.
- `docs/research/current-skill-selection-20260919.md`: this evidence record.

Existing `RecoveredSkillCommand.h`, `current_skill_identity.py` and their
current-native evidence were read first. Historical sections were ignored;
no retired archive was opened or used as a lead. No existing file, shared
helper, runtime, Session or CMake changes; no UI automation or delegated agents.

## Pinned authority

Server root: `C:/Users/risei/Desktop/God2/God2-Server`.
Image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
32-bit x86 base `0x400000`; RVAs equal file offsets. Tests verify the full hash.

The integration test also pins the current client source
`C:/Users/risei/Desktop/God2/God2/Data2/Fight/Spg/cbspec2.bin`, SHA-256
`7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51`.
Its exact body `file[4:]` is mapped for original `11C520` execution, retaining
the established (kind, one-based ID) relationship.

## Instructions and framing

All locations below are RVAs. Selector = battle + `A9DC198`.

| Location | Observed behavior |
| --- | --- |
| `114332..114351` | Read record byte 0, subtract `1C`, range-check, map through byte table `11465C`, then jump table `114634`. |
| Tables, opcode `38` | Byte-table entry `1` selects `114525`, which calls `117560`. |
| Tables, opcode `87` | Byte-table entry `6` selects `114518`, which calls `117540`. |
| `15840 -> 1000 -> 1200` | Native logical-size query; opcode `38` reaches `1216`, returning 2; opcode `87` reaches `12DC`, returning 3. |
| `117560..11756F` | Skip leading byte and call `11C7F0` on the embedded selector. |
| `117574..11757D` | Signed AX < 0 skips notification; otherwise pass returned value to `A9990` via battle + `20`. |
| `117582..117588` | Wrapper returns 1, including state mutations that do not switch banks. |
| `117540..117556` | Opcode `87` wrapper skips leading byte, invokes `11C520` on the following WORD, returns 1. |

These are logical record sizes at the current client's consumer and size query.
The original full receive/decrypt/buffer-consumption loop was not run, and no
transport frame encoder or server packet emitter was added.

## Exact transition

Let `i = xx & 31` and `s = xx >> 5`. The native bank count is the unsigned byte
at selector + `5`; current bank is the byte at selector + `4`.

1. If `i >= count`, return signed AX = -1 without modifying the selector.
2. Otherwise locate `B = selector + 10 + i * 2D0`.
3. If `B[2C0] == 2` and `s != 2`, clear bit 15 of **all 100** WORDs at `B+4`
   and zero **all 100** bytes at `B+25C`. This ignores the entry count at `B+0`.
4. Store `s` at `B+2C0`. Other state values have no assigned gameplay names.
5. If `s != 2`, return signed AX = -1. This return is not a mutation failure.
6. If `s == 2`, dereference the WORD at the pointer stored in `B+2C4`. Scan
   banks from zero, comparing the WORD reached through each bank's `+2C4`.
   Skip a match whose index equals the **signed** current-bank byte. On the
   first other match, set current-bank byte to that index and return the
   **input** index `i`. With no such match, leave current bank and return -1.

Instruction anchors: range check `11C7F8..11C803`; old-state/next-state checks
`11C81D..11C82E`; WORD clearing `11C830..11C841`; auxiliary clearing
`11C844..11C851`; state store `11C854..11C859`; key dereference and call
`11C85F..11C873`; return `11C878..11C88F`; key scan, signed current comparison
and current-bank write `11C8E0..11C928`.

Duplicate-key example: banks 0, 1, 2 all reference key 7; current bank is 0;
record `38 42` updates bank 2 to state 2, selects bank 1, and returns AX = 2.
The implementation preserves this observed behavior without assuming keys are
unique or assigning an identity domain to their WORD values.

The Python consumer checks the physical subset of at most 16 banks, exactly
100 WORDs and 100 auxiliary bytes per bank, raw integer ranges, and exact
record size/opcode. Those are implementation input checks. Native `11C7F0`
trusts its count byte and referenced pointers; it does not reject count > 16.
Unmapped pointers and overflowing native layouts are outside this consumer.
No fallback values or inferred skill costs, ownership or effects are supplied.

## Effect on a real caller

`11B9A0..11B9D6` reads bit 15 of an indexed WORD in the current primary bank.
The real selection caller at `1153B4..115400` requires battle `+A9E9C34 == 0`
and `+A9E9C38 == 1`, searches by event byte 2 (kind) and byte 4 (ID) through
`11BA90`, rejects a null `11B8C0` result, then requires `11B9A0 != 0`.
Those event bytes are not asserted to be a wire record.

Tests execute this caller slice before and after the recovered transition.
An inserted bit-15-set skill passes to `115406`; after leaving state 2 it
branches to `1154AA`. Identity WORD low bits, source pointers and count remain.
Entering state 2 again does not restore cleared flags. Thus the flag affects
this client selection gate; that does not establish server cast eligibility.

The containing routine `1151A0` gets its event pointer through `B0290` on
battle + `20` and dispatches through table `1154B4`. That setup was inspected,
not executed. The gate test starts with explicit synthetic ESI/EDI state.

## Reproducible tests

Run from the server root:

```powershell
python -B tests/research/test_current_skill_selection.py -v
```

Final run: **7 tests passed in 1.838 seconds**. No subprocess/compiler, network,
UI or live client is started by the suite; no generated files are written.
Each emulation invocation has a 10,000-instruction cap and must reach an
explicit expected endpoint. Image code is read/execute only. Hooks observe
execution and stop at declared boundaries; no instruction or helper is stubbed.
Unexpected executed code outside the enumerated native spans fails the test.

- 6,950 native/model full `0x3600`-byte selector comparisons: every payload
  for counts 0..16; all 256 previous state bytes against states 0/2/7;
  every payload at current bytes 0/7/15/16/127/128/255; duplicate WORD keys;
  clearing beyond the declared entry count; signed AX results and switch calls.
- Packet bytes sit at the end of a read-only mapped page followed by unmapped
  memory, catching forward overreads. Full-object comparison catches unintended
  changes to pointers, counts, pages, unrelated banks and alternate storage.
- Execute the original size-query chain for `38` and `87`. Execute `38`'s
  native dispatch and wrapper through either the pre-notification `117579`
  boundary or the returned-to-dispatch `11452D` boundary.
- Switch banks, dispatch three real `87` identity updates, verify current
  cbspec2 pointers for `(0,1)`, `(1,1)`, `(3,111)`, then execute the original
  state reader and caller gate before/after clearing. Include nonzero blocker,
  mode != 1 and absent identity negative controls.
- Reject malformed record lengths/opcodes/types and unsupported snapshot
  shapes/ranges. These are model checks, not invented native rejection rules.

## Byte-span hashes

SHA-256 of exact image slices; end RVAs are exclusive.

| Start..end | SHA-256 |
| --- | --- |
| `11C7F0..11C892` | `ff720034bcae4b2654a7b2061a0c211fc9330e02818bb8471f12d4cccc3eaad8` |
| `11C8E0..11C92B` | `b32c292df12d911b3f9ed775fa685a9c91d033e3909bd07318ac9565a7c976ad` |
| `117560..11758B` | `e1a0e8d2309a38ad4fcd63c63eceb8b5f4c92a250948464b8a4f85dfe7812c89` |
| `114332..114358` | `b5b0a198747e09dbb7c6cb83663e37965386bfe0cbff116c741b411eda67c499` |
| `114518..114538` | `db96e85474065843b843cafa75a5360d928cfd4b43ead1f4c63268e196f462d1` |
| `114634..1146CA` | `186ad0ceb76952e66c5489dbcf372e23d953df9fef8b3ba557774b57f984f851` |
| `1216..121C` | `7140f35dee6220b79b12aecc27acf5105bf3b77d1588e89fce345de7c16c72b7` |
| `12DC..12E2` | `7adb2a5467d3718ab3b55c6851599af573d4fbeadcd90dd961cfd69d4f94cc9f` |
| `11B9A0..11B9D9` | `07d1ca1d1708d78f5ea084be26be6530e519159a6878c38a24c36949e2195994` |
| `1153B4..115406` | `da82cbcee93c2162a9d73d9b02fc1b92e873ada9ff593b0152f9b984052283ca` |
| `11BA90..11BAE2` | `7d8e5991729af985b90f97c6c4968480757979d9b8f7ace149ed75c0f6264e2a` |

## Open original evidence, not completed gameplay

The original authoritative producer and rule deciding when to send `38`/`87`
remain unresolved. The pinned client proves their consumption, not who may
learn or cast a skill, costs, turn legality, target legality, outcomes or rates.
No original server implementation or live transaction was established here.

Concrete continuation points from the current image:

- Key provenance: `11BB80` initializer uses argument 7 + `D8`, advancing by
  `3EC` per bank, to populate bank `+2C4`; it copies current/count from that
  argument's `+CF`/`+D4` at `11BC14..11BC27`. Trace that argument back through
  current caller `111671..1116A4` and its producers to establish the key domain.
- After the tested gate, `115406..115435` may call `1108C0` and `112800`, writes
  the slot at battle `+A9DF73C`, then invokes `1154E0`. Its current instructions
  inspect definition kind and WORD `+3E` at `115571..11557D`, and feed bytes
  `+44`/`+45` to `1156E0`, `11EE90` (call `1155E4`) and `11EAD0` (call `115614`).
  Trace those helpers before assigning target/action meanings or connecting
  this gate to the later `118E50` request builder. No formulas inferred.
- Notification `A9990`, full event retrieval `B0290`, receive-loop provenance,
  and post-selection action setup remain unexecuted. Original-source evidence
  for authoritative server validation/results is still required; this client
  path cannot supply that authority by itself.

These open rules stay open. The validated bounded transition and emulator
results do not mark the broader original battle rules or gameplay complete.
# Full hotbar entry qualification (2026-09-21)

The pinned native entry `1151A0` obtains a six-byte hotbar record by calling
the unchanged `0B0290` getter. Record WORD 0 equal to 2 dispatches to the
primary skill branch `1153B4`; kind comes from byte 2 and ID from byte 4.
This is not a direct skill-ID or selected-index argument.

The getter accepts the low argument byte only when below 10. UI DWORD
`+A3D08 == 1` selects `UI+A3D54+60*signed_byte(source+CF)+6*slot`, with
source at `UI+86888`. Mode 2 selects `UI+A4114+6*slot`. Other modes return
null. No claim is made that the signed source index is bounds-checked here.

`test_full_hotbar_entry_reaches_native_selected_index_write` executes from
the real entry, through the real getter, dispatch and skill accessors, to
`11542E`, immediately before target setup. Forty synthetic valid fixtures
cover all ten slots, mode-1 source rows 0/3/15, and mode 2. The original
instruction changes selected index from -1 to 0 and forwards the first
argument unchanged to `1154E0`. Four invalid-slot cases (10/255 in both
modes) return normally without changing selection. All eight selection
suite tests pass after this addition.

Important limits: the fixture starts with battle mode `+46C == 3`, an
enabled primary entry and an existing grant. Mode-change/UI calls, actual
hotbar population, full target setup, live selection, skill casting and MP
settlement are not proved by this test. No original callee is stubbed;
execution stops explicitly before the target-setup call. No production
gameplay configuration or client executable was changed.
