# Current Monster Variant Identity Qualification

This bounded delivery qualifies original SpecialEnyInfo loader `5A560`, lookup
`5A120`, and the `115C90` identity prefix through calls `115E25` and `115E70`.
It executes the complete one-row current SpecialEnyInfo namespace and all
4,051 source identities reachable through the alternate area0 scenes2/3/13.
It does not establish an ALL-monsters/BOSS denominator, a boss classifier,
original server assignments, or complete actor construction. All requested
stat/skill/drop assignments remain unqualified and runtime-ineligible.

Only these new files belong to this delivery:

- `tools/strike_lab/current_monster_variant_identity.py`
- `tests/research/test_current_monster_variant_identity.py`
- `docs/research/current-monster-variant-identity-20260920.md`

## Pinned Inputs

The tool consumes the shared current inventory parser and its descriptor
fixture from `current_monster_base_stats.py`. The existing base-stats and
inventory 20260920 reports establish the surrounding EnyName namespace and
main's complete original loader regression. This delivery does not rerun
`5A1A0` or the expensive full 7,791-record native loader regression.

- Current source: client `Data2/Patch/Comm/gamedata.csvZ`.
  SHA256 `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
- Decoded SHA256:
  `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
- Exact decoded section `[2781781,2781824)`:
  `SpecialEnyInfo,1\r\n1,IGS_SPECIAL,0,0,149,1\r\n`.
  SHA256 `c3d480f60ba45441c3dfc40fe2c61e420a9e79f32570a5b640f08b82652cc4ad`.
- The only source row starts at **2781799**, source line **29626** (one-based).
  Inventory preserves the raw row, hash, source label `1`, source record index
  `0`, and native lookup ordinal `1`. The loader does not use source column0
  as a global template identifier; row position supplies the lookup ordinal.
- Mapped image:
  `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
  SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
  x86 BASE `400000`; hexadecimal RVAs below equal image file offsets.

| Native span, end exclusive | SHA256 |
| --- | --- |
| `5A560..5A860` loader | `84e6d741ed7299a6c6347fdb8cb33abe39051db60b60946937c31c3cfe700153` |
| `5A120..5A198` lookup | `0e3575fbbb9d709fc282db4ffd6668501199b96c0de286b675a16778244f5b1b` |
| `115C90..115E77` consumer prefix | `b30d77a99f2f5503637e0f35b59ba7a9b2019b609ca522c87becc1f4b77594f1` |
| `11662C..11663C` dispatch table | `6c646b558cbdd657b7af3b391be9fe393f0b895ac2f882052cd23e082143c6f2` |

The machine report additionally hashes the original row reader, field
accessors, CSV parser, stack probe, normal lookup, and participant lookup.

## Executed Loader and Lookup

Original `5A560(1)` executes continuously through its `ret 4`, including
`51A90` row reading, `51BE0` parsing and `51B50/51BA0` numeric accessors.
Explicit bounded CRT adapters provide allocation, fgets, strchr, memcpy,
strncmp and decimal sscanf. They validate callers and bounded operands;
these CRT functions themselves are not claimed as original native execution.
The original stack probe `147B50` executes. The fgets adapter supplies only
the exact current row with CRLF converted to LF, matching the existing text
stream harness. Allocation is exactly 26 bytes, with explicit poison fill.
No host file is written by the tool and no live process, UI or network runs.

The loader writes the count at manager `+D2E2C` and allocation pointer at
`+D2E28`. `IGS_SPECIAL` comparison selects `5A5FC`: it writes zero DWORD at
record `+2` and clears the first byte's high nibble. Subsequent original
writes produce byte0 `02` and byte1 `95`. These are packed record bytes,
not numeric stats or a demonstrated boss/category label.

Native write tracing proves that only byte offsets **0..5** are initialized.
With allocation poison A5 the exact record is:

```text
02 95 00 00 00 00 A5 A5 A5 A5 A5 A5 A5 A5 A5 A5 A5 A5 A5 A5 A5 A5 A5 A5 A5 A5
```

Poison 00/A5/FF leaves the first six bytes identical and the remaining twenty
bytes equal to the allocator input. Those twenty bytes are explicitly marked
uninitialized in the report; no zero-filled or source-authoritative record is
claimed for them.

Original `5A120(base_pointer, selector)` masks selector to WORD, compares it
with the loaded count, and uses one-based `26*(selector-1)` addressing:

- Selector1 copies the special record into shared scratch manager `+D2E30`.
  Its empty name triggers inheritance at `5A161..5A184`: scratch byte0 gets
  the special low nibble and the base high nibble, and 16 base bytes at `+2`
  replace the scratch name. The returned pointer is this shared scratch.
- Selector2..65535 returns the original base pointer. Direct diagnostic
  checks include 2,255,256,32768,65535; every consumer low-byte value is
  covered separately. No out-of-range special record is synthesized.
- Selector0 has no native lower-bound guard and attempts a pre-arena read.
  The test observes the fault with that page unmapped. The consumer bypasses
  `5A120` for zero; the helper does not silently repair the original lookup.

The inherited base name/header are explicitly synthetic diagnostic payloads.
For base header AB, output byte0 is A2; byte1 stays95. Bytes18..25 retain
allocation poison even after name inheritance. Lookup does not mutate the
loaded special row, but subsequent lookups overwrite the shared result.

## Executed Consumer Routing

Execution starts at original `115C90` with an empty participant slot and an
exact 45-byte synthetic logical 1C packet. It includes original `11E6E0`
slot lookup. It stops **before** `115E77` payload consumption, or at a named
alternate dispatch/null exit. Actor construction and graphics never execute.

The outer jump table at `11662C` uses `(WORD packet+5 >> 13) & 3`:

| Field value | Entry | Qualification |
| --- | --- | --- |
| `0000` | `115DF1` | Normal EnyName coordinates, optional special override |
| `2000` | `116149` | Entry reached, stopped before execution |
| `4000` | `115DF1` then `115E4D` | Alternate area0 coordinates |
| `6000` | `11608B` | Entry reached, stopped before execution |

This refines the earlier base-stats frontier description: testing bits6000
inside `115DF1` does not mean all nonzero field values reach `115E70`.

On the normal branch, original `115E07 -> 5A0A0` consumes packet area byte+9,
scene WORD+11, ordinal WORD+7. A nonzero low byte of WORD+5 invokes
`115E25 -> 5A120` only after a nonnull base lookup. Zero skips the special
lookup; absent base identity reaches `116037` without invoking it.

After a nonzero selector, `115E2F..115E47` rewrites packet WORD+5 bits1C00
from `(returned_record_byte0 >> 1) & 7`. All 256 low-byte selectors are
executed against one explicitly staged diagnostic base identity. With input
`1C00 | selector` and diagnostic base header AB:

- Selector0 returns the base pointer and leaves WORD+5 at1C00.
- Selector1 returns the special scratch and writes WORD+5 to0401.
- Selector2..255 returns the base pointer and writes WORD+5 to1400|selector.

Only packet bytes5..6 change; the original store is at `115E47`. Packet
producer values and these synthetic counterfactuals are never conflated.
The result identity must retain both the base EnyName source key and special
ordinal1; the special row alone is not a standalone monster species.

On the alternate branch, `115E70 -> 5A0A0` always uses area0. WORD packet+7
low14 selects the ordinal; bit8000 selects scene3, otherwise bit4000 selects
scene13, otherwise scene2. If both flags are set, scene3 wins. Packet area,
scene, and the low special selector are bypassed for this lookup.

| Area0 scene | Complete source identities checked |
| --- | ---: |
| 2 | 816 |
| 3 | 2070 |
| 13 | 1165 |
| Total | 4051 |

The report retains every source record index, generation, area, scene,
ordinal, raw source row/hash/offset/line, and actual native pointer. Every
pointer equals the independently staged descriptor's source index address.
All alternate record pages remain **unmapped**, and execution stops before
reading their payloads. Bounds 0, count+1, low14 maximum, competing ordinal
flags and alternate variant counterfactuals are also tested.

The only EnyName payload mapped for the special-consumer sweep is the page
containing source record index0, with synthetic header/name at that record.
Other records on that page are not qualified: read guards reject any unstaged
record. The descriptor fixture comes from the complete shared source inventory;
neither it nor that diagnostic payload is represented as original loader output.

## Verification and Remaining Frontier

```powershell
python -B tests/research/test_current_monster_variant_identity.py -v
python -B -m tools.strike_lab.current_monster_variant_identity
```

Seven focused tests passed in **5.003 seconds**. Coverage includes the complete
special source/loader, all4051 alternate identities, all256 low-byte consumer
selectors, direct lookup boundaries and zero fault, missing base identity,
dispatch entries, packet rewrites, register/stack/allocation poisons, source
and image pin rejection, instruction budget enforcement, and null authority
after JSON serialization. The second command emits the complete report on
stdout; no generated output file is required or owned by this delivery.

The requested ALL-monsters including BOSS scope remains open. Next authority
is the original sender of 1C identity/variant fields and original classifier
evidence, plus the unexecuted `116149`/`11608B` paths and continuation after
`115E77`. A special override combined with every real base payload still
requires attaching main's qualified original loader output; this diagnostic
payload sweep does not claim that cross-product. Identity-bound base stats,
skills/AI predicates and drop producers remain separate unresolved work.
No special-equals-BOSS inference, guessed assignment, sample-based completion,
or global absence conclusion follows. Main owns review and closure.

Main review completed: all7 tests independently passed in5.068 seconds; the
worker was closed and the suite registered with CTest. The4051 alternate
identities overlap the existing EnyName inventory and must not inflate its
species/record denominator. No production promotion followed this review.
