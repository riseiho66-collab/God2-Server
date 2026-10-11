# Current World Appearance: Bounded Profile Projection

Current-source follow-up: `current-owned-appearance-20260919.md` now resolves
the derived-record concern for the explicitly fresh, zero-index preview-block
domain and source selector0. All98 native-generated blocks select identical
four primary HeroDoll source records in preview and world selection; binary1
still selects distinct intermediate r1h000/r2h000 records, but their actual+2A
values are both2. This conditional source result does not authorize changing
arbitrary existing world bodies, selectors, equipment, maps or flags. The
historical candidate below is outside that new fresh-block domain.

Result: **two 3-bit component variant fields are qualified at the original
consumer level**. This does not recover a complete create-profile-to-2A
serializer. A tempting four-nibble binary mapping has a demonstrated lookup
mismatch and is not included in the safe projection. No production edits.

Coordinator follow-up: the owned-profile service now uses the two qualified
variant fields in `RecoveredWorldEntry::wire(id, profile)`. The no-profile
overload retains the original historical fixture unchanged. C++ tests cover all
49 variant pairs, rejected out-of-range values, and untouched unowned bits.
The additional `test_current_world_entry.py` case feeds all49 C++ outputs to the
original decoder/checksum and the original component setter path below, comparing
both variants and unchanged resource keys. Account ownership and persisted-profile
selection are exercised by the real C++ loopback tests. This still does not
qualify complete appearance, resource availability, maps, or a live rendered world.

## Image And Notation

- Image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
- SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
- Image base VA `0x400000`; all code addresses below are hexadecimal **RVAs**.
- `C` is the persisted, owned 40-byte create payload, excluding opcode.
- `B` is the 36-byte S2C2A body, excluding opcode, length and checksum.
- Payload offsets are decimal; words/dwords are little-endian.

Read alongside `original-client-create-profile-20260919.md`,
`recovered-character-persistence-20260919.md`,
`recovered-world-entry-20260919.md`,
`src/protocol/RecoveredCharacterListCandidate.h`, and
`tests/research/test_current_world_entry.py`.

The list candidate's consumer correspondences are not an original server
serializer. In particular, copying list appearance bytes into 2A would not
establish this relation. This test follows the actual create preview instead.

## Safe Mapping

Preconditions: repository/account ownership and the existing profile validator
have succeeded; `C[32]` and `(C[36] >> 5) & 7` are in `0..6`. The qualified
world path is the normal component branch, specifically `WORD(B+32) == 0`.
For the requested variants to reach the setter, the client override flag
`world+0x1539AD70 & 0x10` must be clear.

| Owned profile source | 2A destination | Masked replacement | Original consumer |
| --- | --- | --- | --- |
| `C[32]`, component-0 variant | `B[13]` bits 5..7; DWORD B+12 bits 13..15 | `B[13] = (B[13] & 0x1F) \| (C[32] << 5)` | `FFA20(component=0, variant=C[32])`; also actor+28 |
| `C[36]` bits 5..7, component-1 variant | `B[15]` bits 5..7; DWORD B+12 bits 29..31 | `B[15] = (B[15] & 0x1F) \| (C[36] & 0xE0)` | `FFA20(component=1, variant=(C[36] >> 5))` |

Equivalent DWORD replacement, for a validated profile:

```text
D = LE32(B+12)
D' = (D & 0x1FFF1FFF)
   | (uint32(C[32]) << 13)
   | (uint32((C[36] >> 5) & 7) << 29)
```

Only mask `0xE000E000` changes. Preserve every other body bit, including the
low five bits of B[13]/B[15], all binary nibbles, other component variants,
resource selectors, identity/flags and bytes outside DWORD B+12. There is no
increment or decrement in either mapping. C[37] is not copied.

This makes the two numeric component variant consumers agree with the owned
profile. It does not make preserved historical resource/equipment inputs the
character's own inputs, or prove that the selected resources contain those
variants. The existing local actor-ID binding is separate from this result.

## Exact Original-Code Relation

1. Current create setup calls preview `99E0` at `CD5B`. The preview constructs
   an eight-byte temporary component block at its local `ESP+10`.
   `9A0E..9A1E` zero the block. `9A2C..9A50` move C word 36 bits 5..7 into
   temporary byte 3 bits 5..7; the subsequent byte shift discards other bits.
   `9A4A..9A65` move C[32] into temporary byte 1 bits 5..7.
2. For component index `i`, preview `9B97..9BA1` reads temporary byte
   `2*i+1`, shifts right five, and calls `FFA20(i, variant)`.
   Original `FFA20..FFA38` stores the low variant byte at
   component-object `+8+6*i`. This setter executes in the regression.
3. The current create sender `C168..C177` copies all 40 bytes. It increments
   C[29]/C[31] and replaces word 38's low nibble (`C179..C1B1`), leaving
   C[32], C[33] and C[36] unchanged. The regression executes through `C1BB`
   and checks the resulting complete profile against the persisted format.
4. World `68328..68348` copies DWORD B+12 into actor+4584 and writes
   `B[13] >> 5` into actor+28. `6833F`/`68370` copy B+16/B+20 to
   actor+4588/+458C. With word B+32 zero, `68376..68379` selects `684CD`.
5. `684D6..684EB` pass a pointer to B+12 into original `61270`.
   This executes the component resource-key extraction and lookup wrappers.
   `684F4` sets the subsequent variant-source pointer to actor+4585.
   `68527..68534` load its byte, shift right five, and call the same
   `FFA20(i, variant)`. `68539..68556` advance the pointer by two and the
   component index by one, for four components.
6. `6851A..68525` instead force variant 7 on all four components when the
   override flag is set. A nonzero B+32 can select the separate optional
   resource path `6837F..684C8`; this task does not qualify that path.

Resource-key extraction consumes the low five bits of the relevant odd
component bytes, independently of the high three variant bits. The test
also compares original lookup arguments before/after the safe projection
with nonzero unrelated component inputs: all keys remain unchanged.

## Binary Candidate: Specific Missing Relation

`9A6F..9A8C` replace the current preview component's low nibble with C[33].
After the preview loop, the temporary block is:

```text
[s, C32<<5, s, C36&0xE0, s, 0, 0x80|s, 0], where s=C[33]
```

This suggests B[12], B[14], B[16], B[18] low nibbles, but final block equality
does **not** prove lookup equivalence:

- Preview processes components sequentially. During component 1,
  `9A90..9AAF` look up component 2 using its still-zero temporary bytes.
  The returned record's byte +2A contributes to component 1's key at
  `9AB4..9AE2`. Component 2's nibble is assigned only on the next iteration.
- World `61366..61394` (zero selector) or `612DF..6130D` (positive selector)
  derive that key from the already complete B[16]/B[17]. The chain
  `63C90 -> 52420 -> 52460` reaches the same lookup used by the preview.
  The primary component lookup follows `63DE0 -> 526C0 -> 52460`.
- With `s=1`, preview's extra lookup key is `(0,2,0,0,0)` while the proposed
  complete block produces `(1,2,0,0,0)`. The remaining primary keys agree
  only when the synthetic records supply the same derived value.
- A regression supplies synthetic lookup records whose +2A values are 2
  and 3. Original code then requests primary component-1 keys
  `(1,1,0,2,0)` versus `(1,1,0,3,0)`. This is a counterexample to unconditional
  equivalence, not a claim about the real asset tables.

Missing: current resource-table evidence that reconciles those two derived
lookups, or original server serialization evidence establishing the intended
binary projection despite that distinction. Consequently **no binary nibble
replacement is qualified here**, even though individual primary consumers
correspond. The preview's fixed `0x80` is likewise not an owned profile field
or a recovered server equipment default.

## Other Unqualified Fields

| Profile source | Missing relation |
| --- | --- |
| C[29], paired category 1..8 | No original copy or equivalent resource-consumer chain into a 2A bitfield. Similar numeric bounds are insufficient. |
| C[31], four-way selection/sentinel | No relation into world appearance. |
| C[36] low five bits | Current UI image-control index at CC05..CC2A, but no established 2A resource-index relation. The actual 99E0 preview discards these bits. |
| Word C+38 bits 4..9 and 10..15 | Graphic controls at CC4D..CCA0; no established conversion into 2A's component resource keys. 99E0 does not consume these selectors. |
| Remaining profile bytes/bits | No qualified appearance projection in this bounded trace. |

No class, sex, race, face/hair, color/palette, equipment or stat names are
assigned to these neutral selectors. Area/scene resource work is out of scope.

## Runnable Regression And Limits

From the server root:

```powershell
python -B tests/research/test_current_world_appearance.py -v
```

Result: **6 tests passed**. Includes all 98 valid combinations of binary
0/1 and two variants 0..6, sender preservation, both resource-selector branches
with synthetic entries, variant override, the binary counterexample, unchanged
lookup keys under variant projection, input/actor guards, and preservation of
every unowned body bit. The research helper intentionally relies on the stated
valid-profile/ownership preconditions; it is not a production validator.

The SHA check precedes execution. Original code is read/execute-only; each
slice has a one-second/20,000-instruction limit and an exact stopping address.
World execution starts at `68315`, after scene setup, and stops at `68558`,
before subsequent actor/scalar initialization. Create preview runs `9A08`
through `9BBB`; sender runs `C160` through `C1BB`.

Only these callees are stubbed: `52460` returns synthetic resource records,
`106C30` returns a synthetic preview handle, and `63640`/`63AD0` return zero
for unrelated resource results. Component extraction, derived-key wrappers,
cached-handle wrappers, byte packing and `FF450`/`FF490`/`FFA20` setters execute
original instructions. Shared stubs do not establish shared real asset data.

No client/server process, UI, sockets, asset loader or database is started.
No production source, fixture, map, existing test or existing note is edited.
Rendered appearance, resource availability, complete world entry and original
server policy remain unproven.
