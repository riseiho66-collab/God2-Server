# Current Owned Appearance: Source Record Differential

## Result and Scope

The current original create-preview block selects the **same four primary
HeroDoll resource records** through the world 61270 component-selection path
for C[33] = 0 and 1, each with all 7 x 7 C[32]/C[36] variant pairs. This is
98 comparisons of freshly native-constructed blocks. Resource identity here
means actual source row, native record pointer, key, filename field, and +2A
byte, not a guessed filename or a synthesized successful handle.

The intermediate mismatch remains: for binary 1, preview's component-1
derivation uses `r1h000`, while world uses `r2h000`. They are distinct records.
Both actual source records name `r01w800.romz` and contain derived byte **2**,
so both paths select `r2f002` for the primary component-1 resource. For binary
0 the derived lookup is the same record. All 49 binary-1 mismatches remain in
the traces and are asserted, not normalized away.

This qualifies a conditional component-block relation under the explicit
source selector 0 and the fresh preview's zero resource indices. It does not
qualify a whole world packet, default selector/mount/area/flags, loaded ROM
handles, animation, rendering, damage, or live acceptance. No historical
body is used as an input. No retired corpus supplies evidence or values.

## Current Source Provenance

All addresses below are RVAs in the image based at VA 400000.

| Input | Location | SHA-256 |
| --- | --- | --- |
| Current native image | `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin` | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |
| HeroDoll compressed | sibling `God2/Data2/Patch/HeroDoll.csvZ` | `df2fa65e0b159b18303b2e135cacc690e0e02e4ea12560cacda3f0d8e6ae1359` |
| HeroDoll decoded | same source, bounded decoder | `0ba373ca45d0f4452f1d847fab5f5e194f00501f26a58f082c5352f71fe921c2` |
| Drv compressed | sibling `God2/Data2/Patch/Drv.csvZ` | `9af4b2ed4d5b007bfde12f2cff4e9895715903a8ffaf5a356aee011f3fb98f2e` |
| Drv decoded | same source, bounded decoder | `72cd006c121a865e10b7d1e2c655895da16a5e760bad2c8d473bf5663996f6e0` |

The existing read-only `current_appearance_resources.py` supplies the pinned
original tokenizer 51BE0, HeroDoll row loader 5201C..521A2, Drv row loader
632C5..633E5, and native hash/key lookup. It produces all 918 HeroDoll records
and 92 Drv records once per oracle; Python does not fabricate record values.
Each selected native record is checked independently against the decoded
source row. HeroDoll source line numbers below are one-based, including the
25 header lines. Drv source row 0 is line 10 and its action column is 0.

| C[33] | Component | Source line | Native key | Actual filename field | +2A |
| --- | --- | --- | --- | --- | --- |
| 0 | 0 | 158 | r1b000 | r01b000.romz | 0 |
| 0 | 1 | 601 | r1f002 | r01f002.romz | 0 |
| 0 | 2 | 26 | r1h000 | r01w800.romz | 2 |
| 0 | 3 | 292 | r1w800 | r01w800.romz | 0 |
| 1 | 0 | 182 | r2b000 | r02b000.romz | 0 |
| 1 | 1 | 611 | r2f002 | r02f002.romz | 0 |
| 1 | 2 | 92 | r2h000 | r01w800.romz | 2 |
| 1 | 3 | 377 | r2w800 | r02w800.romz | 0 |

Identical filenames do not collapse source record identity. In particular,
`r1h000`, `r2h000`, and `r1w800` are distinct records, despite their shared file.

## Instruction-Derived Layout

The probe checks the whole-image pin and explicit unchanged instruction bytes
at the relevant offsets. It also checks native string references. Preview
4225 and world 63C28 reference the same `HeroDoll.csv` string at 1847E8;
425B and 63C54 establish preview +D8C and world bank +12D78. Drv loader 63270
references `\\Data2\\Patch\\Drv.csv` at 18A88C. These are executable-source
references, not filename-pattern inference.

61273/6127A select a manager bank using +16CE18 and stride AD610; 6128E uses
bank +682E0. The harness supplies bank index zero only as its memory topology.
63785 checks the real Drv WORD count at +121F6; 63794 loads the action WORD at
bank +121F8 + selector*32 +12. All five native 63780 calls per world case read
source selector 0 and return 0. No action result is supplied by a hook.

99E0's original prologue establishes the preview stack frame. 9A10/9A1E zero
the eight-byte block. 9A2C reads C[36:38], 9A4A reads C[32], and 9A71 reads
C[33]. The original loop replaces a component's low nibble at 9A81..9A8C
immediately before its lookup. Consequently component 2 is still zero when
the component-1 derived lookup executes at 9AAF/9AB4. World 61369 instead
reads byte 4 of the completed block, and 61394 calls native 63C90 -> 52420.
The +2A source-byte load and the `<2`/addition logic execute on both paths.

The five lookup tuples, in execution order, are:

| Purpose | Preview | World |
| --- | --- | --- |
| Primary 0 | `(b,0,0,0,0)` | same |
| Derived input for 1 | `(0,2,0,0,0)` | `(b,2,0,0,0)` |
| Primary 1 | `(b,1,0,2,0)` | same |
| Primary 2 | `(b,2,0,0,0)` | same |
| Primary 3 | `(b,3,8,0,0)` | same |

## Bounded Execution, Not Full Preview

Every comparison starts with poisoned stack/component storage and a fresh
40-byte input profile. Only the named input fields carry candidate values;
all other profile bytes are arbitrary poison, not asserted game defaults.
Original 99E0 instructions construct the block; the helper never constructs
the eight input bytes for its differential by hand.

- Execute 99E0..99F0, then 9A08..9B00 and the original four-iteration loop.
  Skip 99F0..9A08 cache/bank resets; all actual records already have FFFF
  cache words. At each 9B00 boundary capture the actual primary record.
- Omit ROM/cache/animation side effects at 9B00..9B97, except execute the
  original EDI adjustment 9B4D..9B53. Execute 9B97..9BA6, including native
  FFA20 variant storage, followed by original loop control through 9BBB.
- Feed that fresh block to 61270. At each 613F1 execute the original call
  chain 63DE0 -> 526C0 -> 52460 and stop at 526DE with the actual record
  pointer. Capture its identity, restore the saved VM registers/stack,
  discard the seven pending call arguments, and execute 613FA..613FE and
  61403 through the next iteration. No resource result is returned to game
  code; handle-output stores and the accessory tail from 61409 are omitted.
- The unused second-selector and output-pointer arguments are CC poison,
  not default state. Execute normal-world variant slice 68527..68539 with
  each component-byte pointer after its override branch. Reset variant
  storage first so it cannot inherit preview's result. Both native setters
  must write only offsets 8, 14, 20, 26 and preserve surrounding canaries.

Thus this is a segmented original-code **selection** differential, not an
uninterrupted 99E0/61270 run. The native instructions themselves are unchanged.
There are no game lookup stubs, synthesized records, fabricated cache hits,
ROM reads, or successful handles. Observational hooks retain derived records
and actual Drv return values. Unexpected ROM/accessory entry fails immediately.
The inherited CRT/CString adapters and reconstructed allocation-backed hash
container are the same bounded infrastructure as the current table oracle.
Code and HeroDoll records remain read-only; the copied world bank is read-only.
Every slice has an exact-PC stop and inherited time/instruction bounds.

## Qualified Masks

Let P be this fresh eight-byte component block and C the 40-byte profile.
For b = C[33] in {0,1}, f = C[32] & 7 in 0..6, and s = C[36] >> 5 in 0..6,
original construction yields `b, f<<5, b, s<<5, b, 0, 80|b, 0` (80 is hex).

| Destination in P | Original mask relation |
| --- | --- |
| 0, 2, 4, 6 | `(old & F0) | (C[33] & 0F)` |
| 1 | `(old & 1F) | ((C[32] & 07) << 5)` |
| 3 | `(old & 1F) | (C[36] & E0)` |

9A81 establishes the nibble assignment mask 0F; only bit 0 varies in the
qualified binary domain. Nothing here admits binary values 2..15 or arbitrary
existing component indices/categories. `project_owned_bits` rejects blocks
outside the fresh preview shape. All 98 x 98 source/target block projections
are compared with independently native-produced blocks and preserve every bit
outside these masks. Poison tests independently confirm that C[32]'s high
bits, C[36]'s low bits, C[37], and all other profile fields do not affect the
qualified selection or variant result.

For coordinate reference only, the normal world's 684D6 call argument points
at body byte 12: P offsets 0/2/4/6 would be body 12/14/16/18, and P offsets
1/3 would be body 13/15. No body is synthesized and this conditional mapping
is not installed into any production serializer. Fresh preview's category
80 and zero indices are native construction results, not proposed defaults
for an independently owned world body.

## Regression

Run from `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B tests/research/test_current_owned_appearance.py -v
python -B -m tools.strike_lab.current_owned_appearance
```

The first command tests the 98 native differentials, 49 preserved intermediate
record mismatches, 9604 mask projections, poisoned inputs/state, instruction
and source provenance, unchanged caches, and rejection outside the qualified
domain. The second emits the full per-case source identities and lookup traces
as JSON on stdout; it writes no artifacts. Existing tools and tests are unchanged.

Final verification on 2026-09-19: **6 tests passed in 60.794 seconds**. The final
run includes explicit source-row expectations and independent variant-storage
canaries on both paths. No ROM or full-world execution was needed.
