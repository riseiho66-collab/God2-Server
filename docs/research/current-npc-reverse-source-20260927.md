# NPC source reversal: remaining setter and world-owner edges

Date: 2026-09-27. Scope: current Taiwan unpacked client only.

## Result

No new original NPC placement was recovered. This pass specifically checked
the previously open `004CCEC0` interior-entry/reference frontier and the
`00464910/0046BCC0` NPC-pool owner paths. It did not replay the already qualified
S2C72 appearance, network movement, or local cursor-marker experiments.

The new result is narrower than global unreachability: **no valid external
direct branch or literal VA/RVA pointer to any byte inside this setter was
found in the checked image**. Computed register targets, constructed pointers,
and unconventional stack/control paths are still unproven.

The scene-dependent NPC table reached through `46BCC0` does have a genuine
native use: it preloads named sprite resources by family and ordinal. The
checked path does not produce NPC world instances or coordinates.

No runtime, client, database, canonical Ghidra analysis, or visible desktop was
modified. No retired source was opened.

## Reproducible evidence

Tool: `tools/strike_lab/current_npc_reverse_source_20260927.py`.

```powershell
& 'C:/Users/risei/AppData/Local/Programs/Python/Python312/python.exe' `
  tools/strike_lab/current_npc_reverse_source_20260927.py `
  --output artifacts/research/npc-reverse-source-20260927/new-run

# Repeat the delivered export's byte checks and isolated native vectors:
& 'C:/Users/risei/AppData/Local/Programs/Python/Python312/python.exe' -O `
  tools/strike_lab/current_npc_reverse_source_20260927.py `
  --output artifacts/research/npc-reverse-source-20260927/qualified --reuse-export
```

Final evidence is under `artifacts/research/npc-reverse-source-20260927/qualified/`.
The parent directory retains an earlier exploratory export. Both are read-only
exports; the final directory additionally contains exact candidate instruction
contexts. The script imports only the generic Java exporter template and pinned
paths from the preceding NPC writer tool.

Pinned current EXE SHA256:
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.

Pinned mapped image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

Saved project executable SHA was checked before export. Fourteen selected
functions plus caller and candidate contexts produced **2,686 instruction
rows**, all byte-identical to both inputs. `evidence.json` stores function VA
extents, raw offsets and SHA256 values. Native setter prefix tests passed all
**16 vectors**, including the repeated `-O` run; validation uses explicit
exceptions rather than Python assertions.

## Setter interior/control reachability

`004CCEC0..004CCF74`, 181 bytes, raw PE offset `000CC4C0`, SHA256:
`6c3a2d74bcdd0cc4c4d7287a909c2bc75b2836cc51753bf59fecbb260612b769`.

The new census checked:

1. Ghidra references to **each byte**, including instruction offcuts, in the
   setter range; zero saved references.
2. All analyzed instruction flow/address/scalar operands targeting that range;
   zero additional references. The setter itself is not a saved function.
3. Raw `.text` plus executable-section E8/E9, short branch/loop, and near Jcc
   target calculations, including interior targets. `.text` is explicitly
   included because this unpacked PE retains RW flags on that original section.
4. Whole mapped-image absolute-VA and RVA DWORD patterns for every byte in the
   range, including unaligned candidates.
5. Prior function termination and padding, to check ordinary fallthrough.

Seven raw control candidates were found:

| Source | Result |
|---|---|
| `4CCEF6→4CCF5A` | Legitimate internal setter branch |
| `4CCF04→4CCF10` | Legitimate internal setter branch |
| `4CCF0E→4CCF1A` | Legitimate internal setter branch |
| `4CCF1D→4CCF23` | Legitimate internal setter branch |
| `4CCF21→4CCF29` | Legitimate internal setter branch |
| apparent `4CCE7F→4CCEE7` | False boundary: byte `7C` is the displacement of `MOV AX,[ESI+7C]` at `4CCE7C` |
| apparent `4CCEE0→4CCEF1` | False boundary: byte `70` is the displacement of `LEA ESI,[EDI+EAX*8+70]` at `4CCEDD` |

There were **zero absolute VA pointer patterns** and three RVA-shaped integers:

| Pattern location | Actual instruction context |
|---|---|
| `4CFA7D` value `000CCEE8` | Overlaps opcode/operand of `CALL 4D0750` at `4CFA7D` |
| `47AC02` value `000CCEF1` | Relative displacement of `CALL 547AF7` at `47AC01` |
| `47ABA6` value `000CCF4D` | Relative displacement of `CALL 547AF7` at `47ABA5` |

These were qualified using saved instruction boundaries, not by assuming a
nearby arbitrary disassembly start. See `candidate-context.tsv`.

The preceding function executes `RET 4` at `4CCEAE`, followed by exactly 15
NOP bytes `4CCEB1..4CCEBF`. There is no normal fallthrough from it into the setter.
This does not prove that some unknown computed dispatch can never enter it.

## Caller assumptions and parameter freedom

The setter does not take an NPC catalog identity, map, area, or scene. Its
contract, before map/rendering work, is exactly:

```text
ECX = pool pointer supplied by caller
slot = sign_extend_16(stack arg1)
x    = sign_extend_16(stack arg2)
y    = sign_extend_16(stack arg3)
record = pool + 0x70 + slot * 0x1D8
record.DWORD[0x10] = x
record.DWORD[0x14] = y
```

There is no identity lookup, occupancy check, or slot bound guard before these
writes. It does not set facing or identity. Afterward it obtains map context
through `*pool`, converts coordinates to rendering coordinates if available,
and calls `4CDAA0`. That later projection is not an original coordinate source.

Sixteen native prefix vectors stop at `4CCEEC`, immediately after both writes,
before any map-context read. They cover slots 0, 255, 256, and signed -1; caller
argument upper halves 0000/ABCD; coordinates 126/127 and FFFF/8000. Only the two
coordinate DWORDs change in the poisoned synthetic record. Slots -1/256 are
deliberately mapped synthetic memory showing the missing guard, **not valid
gameplay slots or safe invocation advice**.

Thus all three caller argument upper halves are irrelevant to this prefix;
each coordinate retains an independent signed 16-bit degree of freedom. The
function itself supplies no constraint selecting one historical coordinate
pair for a particular NPC. For a fixed valid slot and identity, the write
calculation accepts every such pair without consulting an NPC table. Map
validity and original server selection are separate, missing evidence. The
consumer cannot uniquely determine the original caller coordinates merely
from knowing an NPC identity or seeing this function's code.

## World-owner alias edges checked

### `00464910`: pool creation

At `4654AC` the code computes `ECX=W+1539AED8`; the immediately following call
`4654B2→4CA680` initializes the NPC pool. At `4654CF`, it independently computes
`W+153B8758` and initializes the monster pool at `4654D5`.

`4CA680` writes its manager/context arguments into pool header/footer fields,
zeros 256 records, and marks each identity unused. The NPC-pool pointer itself
is not passed as a data-source or placement-table argument in this call site.
Its nested `4FF3C0` call is given the resource-manager argument, not an NPC record
pointer. No local NPC coordinate constants or per-NPC source records enter
through this initializer.

### `0046BCC0`: scene change and resource preload

At `46C2BF`, `ECX=W+1539AED8`, followed immediately by `46C2C5→4CA730` to clear
NPC records; the next call clears the monster pool. The code then repositions
the player and viewport. This pool alias is a reset target, not a placement
source. This statement is limited to these actual LEA/call uses, not a global
symbolic alias proof over every world pointer operation.

The higher-value new source edge is earlier in this same function:

```text
received scene context
  → 45AA70(area,scene): NPC scene-resource record
  → 461C40(area,scene,npc_record,enemy_record,UI)
  → 460E50(npc_record,UI): preload NPC appearance resources
  → 45F0E0(family,ordinal-1) / 45EEC0(flat_resource_index)
  → 429820(resource filename, cache handle)
```

`45AA70` checks area <17, searches that area's scene records of stride `8E`,
matches the scene byte at record+0, and returns the matching record. `460E50`
reads count at record+1 and iterates **two-byte entries** at record+2:

- Family <5: `45F0E0(family, second_byte-1)`.
- Family 6: `45EEC0(second_byte-1)`.
- Family 7: `45EEC0(second_byte+100-1)`.
- Family 5 is skipped by this checked branch.

`45F0E0` bounds-checks a family/count and maps to a flat resource index.
`45EEC0` builds a filename from the native resource base path and that index's
76-byte filename/cache record, loads it through `429820`, and stores a cache
handle. `4619D0` selects one of two area/scene cache banks. The UI uses the
NPC count plus enemy count plus two as a loading-progress total.

This is useful native **scene→resource membership** evidence. It is not a
world-instance list: the checked entries contain family/ordinal bytes, and
this path passes resource-manager context, not `W+1539AED8`, to its loaders.
It supplies no x/y/facing to `4CCEC0` or an appearance constructor. Reading these
two bytes as coordinates or scene NPC instance IDs would conflate namespaces.

## Remaining open edge and stopping point

The previously open direct/interior/literal-pointer frontier is now checked
more tightly. An arithmetic-derived callback, pointer copy outside the selected
families, or unconventional computed control flow remains possible; no positive
example was found here. This report does not mark the entire binary unreachable
or claim a full formal alias analysis.

The scene-resource edge provides no placement fields. A next positive lead must
connect an actual pool-record pointer to a new coordinate-producing loader or
provide an original server placement record. Repeating S2C72 acceptance with
arbitrary coordinates would establish consumer freedom, not recover those
original values. Parent handles that separate differential demonstration.

Complete new original placement records: **0**. All tooling processes ended.
