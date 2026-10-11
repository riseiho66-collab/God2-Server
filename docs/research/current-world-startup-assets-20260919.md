# Current world startup assets: original loader handoff

## Immediate effect-manager binding

The handle supplied to `64FCB -> 10DC70` is **FieldComm3 record 8**, inline
field `records+844`, literal `\Data3\Flow\gcall.ROM`. The current compressed
asset is `God2/Data3/Flow/gcall.ROMZ`. It is not the title resource.

```text
64E0B: EAX = [world+A8D50D0]          ; native FieldComm3 records pointer
64E11: EAX += 844                     ; 8*108+4, inline C string
64E17: 12F550(path)                   ; native CWD resolution
64E27: sprintf(frame+60, "%s", path)
64E36: handle8 = manager.60A90(path)  ; real bank/counter required
64E3B: [frame+1C] = EAX
64F54: EDX = [frame+1C]
64FBD: EAX = [world+ABA32DC]          ; renderer pointer
64FC3: push EDX                       ; argument 2 = handle8
64FC4: ECX = world+AA36488            ; effect manager, embedded object
64FCA: push EAX                       ; argument 1 = renderer
64FCB: call 10DC70
```

`10DC70` writes argument 1 to `[this+0]` (32 bits) and argument 2 to
`[this+2C]` (16 bits), then calls `10DC90`. The reset writes `FFFF` to
`+4,+6,+8,+A,+C,+22` and zero to `+24,+28`; it preserves `+0` and `+2C`.
Those native reset values are not a bypass implemented by this sidecar.
Bind through the original callee using the actual returned handle and actual
renderer. Successful parsing/insertion must be checked independently because
`60A90` returns the slot counter, not the success result from `29820`.

The owner's reported `100180 -> 1004F0 -> 10DCC0 -> 1DA27` integration failure
is outside this sidecar's execution. This trace establishes the missing
startup inputs; it does not claim that this binding alone fixes every later
consumer or that those later calls were executed here.

## Pinned originals

All addresses in this document are RVAs, image base `400000`, RVA equals file
offset. Original image:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

Only the current sibling client `God2` asset tree is read. Source:
`Data2/Patch/FieldComm3.csvZ`, header `FightCommon`, 65 records with IDs 0..64.
Raw SHA-256 `197b0952d33bddb6f3682779208dd396fcecbe451c1b9dc68ec86209ed1a7e05`;
decoded SHA-256 `2c76b311dfcfba4ceb2b23c0faf5011339365673bd01c8a4ed371fb174fd43ac`.
Retired archives and legacy evidence are neither inputs nor leads.

The existing `current_world_ui_resource.py` proves the full source reader:
`815C0 -> 54720`, pointer writer `54776`, stride `108`, ID at record `+0`,
260-byte inline path at `+4`, column getter `54800 -> 51AE0`, byte writers
`51B12/51B19`. Reader is `UI+CFF74`; records pointer is `UI+E2164`, hence
`world+A8D50D0` for `UI=world+A7F2F6C`. This helper reuses that reader and
checks all seven original inline fields, not just the prior record-2 proof.

## Exact load order

All seven selections load `[world+A8D50D0]`, add the inline offset, and pass
the address itself to `12F550`. There is no CString-pointer dereference and
no extra config getter. The outer formatter is `%s` at VA `584954`.
Physical CSV data begins on line 5, so source line = record ID + 5.

| Order | ID / source line | Inline field | Literal path | Selection / resolver / formatter / load call |
| --- | --- | --- | --- | --- |
| 1 | 2 / 7 | `214` | `\Data3\Flow\DTitleGui.ROM` | `64CB6 / 64CC2 / 64CD2 / 64CE1` |
| 2 | 3 / 8 | `31C` | `\Data3\Flow\StateEft.ROM` | `64D32 / 64D3E / 64D4E / 64D5D` |
| 3 | 10 / 15 | `A54` | `\Data3\Fight\Gui\Eft2_8302.ROM` | `64D6C / 64D78 / 64D88 / 64D97` |
| 4 | 12 / 17 | `C64` | `\Data3\Flow\motion.ROM` | `64DC0 / 64DCC / 64DDC / 64DEB` |
| 5 | 8 / 13 | `844` | `\Data3\Flow\gcall.ROM` | `64E0B / 64E17 / 64E27 / 64E36` |
| 6, conditional | 9 / 14 | `94C` | `\Data3\Flow\speceff2.ROM` | `64E3F / 64E4B / 64E5B / 64EAD` |
| 7 | 46 / 51 | `2F74` | `\Data3\Flow\NameShadow.ROMZ` | `64EEB / 64EF7 / 64F07 / 64F16` |

The CSV informational labels, respectively, are `ROM_DTITLEGUI,`,
`ROM_STATEEFT,`, `ROM_TEXTNUMEFT,`, `ROM_EMOTION,`, `ROM_GCALL,`,
`ROM_GALLOP,`, and `ROM_NAMESHADOW`. Trailing commas in the first six labels
are inside quoted fields in the original CSV.

The actual load target at every listed load call is `60A90`. `EDI` initially
names `world+AA364B8` (`64CA0`). `64CB1 -> 60A10` binds its primary ROM bank
from `[world+ABA32D4]` and secondary bank from `[world+ABA32D8]`.
`60A90` uses primary bank `manager+121F8` and signed 16-bit next-slot counter
`+121FC`; `60ACC -> 29820(path, slot)` loads it, then the counter advances.
Optional secondary bank `+BF808` has its own counter `+BF80C` and load call
`60AF6`. No absolute slot number follows from this source table.

Record 9's path is resolved unconditionally, but `64E60..64E6B` skips its
allocation/load/binding when `[world+398]` is non-null. Otherwise it allocates
12 bytes (`64E6F`), invokes `10FA30` (`64E8C`) when allocation succeeds,
stores the owner pointer at `world+398` (`64E95`), loads the resource, and
calls `10FA50([world+AA36484], handle9)` at `64EC0`. The latter stores the
renderer at `owner+0` and low-word handle at `owner+8`. Allocation failure
is not repaired by this helper. If this conditional load is skipped, later
slot counter values differ; never infer the NameShadow slot from ordinal 7.

After the NameShadow return is saved, `64F21 -> 60B10` calls `2D9A0(0)` on
each present bank and snapshots each next-slot counter to `+121FE/+BF80E`.
The underlying bank operation is not executed here.

## Handle handoff map

`hN` below means the actual primary slot returned by `60A90` for record N,
never a numeric fixture. `F` is startup ESP between calls; `S=world+ABA32E0`
is the secondary UI owner (`64D02`); `P=world+39C` is the primary UI owner
(`64F40`). Widths matter: some stores retain 32 bits, others only 16.

| Writer RVA | Value | Destination | Width |
| --- | --- | --- | --- |
| `64CF2` | h2 | ESI, retained for both owner calls | 32 |
| `64D12`, `64D22` | h2 | `S+A7E004C`, `S+A7E0050` | 16 |
| `64D62`, `64D66` | h3 | `F+14`, `world+ABA32F8` (= S+18) | 32 |
| `64D9C` | h10 | `F+18` | 32 |
| `64DA0`, `64DA7` | h10 | `world+ABA32F4` (= S+14), `S+A7E0040` | 16 |
| `64DF0`, `64DFB` | h12 | `world+15383338` (= S+A7E0058), `S+A7E0054` | 16 |
| `64DF7` | h12 | `F+20` | 32 |
| `64E3B` | h8 | `F+1C` | 32 |
| `64F1D` | h46 | `F+10` | 32 |
| `64F58` | h3, reloaded at `64F50` | `world+3B4` (= P+18) | 32 |
| `64F62`, `64F69` | h10, reloaded at `64F5E` | `world+3B0` (= P+14), `P+A7E0040` | 16 |
| `64F86`, `64F9D` | h12, reloaded at `64F70` | `world+A7E03F4` (= P+A7E0058), `P+A7E0054` | 16 |
| `64F8D` | h2 from SI | `P+A7E0050` | 16 |
| `64FB1`, `64FB7` | h46, reloaded at `64FA4` | `world+A7E03E4` (= P+A7E0048), `world+15383328` (= S+A7E0048) | 32 |

Associated 16-bit selector constants, not handles:
`S+A7E004E=10` at `64D19`; `S/P+A7E0042=3B` at `64DAE/64F74`;
`S+A7E0044=48` at `64DB7` and `P+A7E0044=48` at `64F7D`;
`S/P+A7E0052=11` at `64D29/64F94`;
`S/P+A7E0056=58` at `64E02/64FA8`. Values are hexadecimal.
This range does not write the primary owner's `A7E004C` counterpart.

Both `64D0D` and `64F4B` call `1081C0` with, in argument order:
`[world+A7E05DC], [world+ABA32DC], [world+A7E05C8], h2, [world+AA36480]`.
The first `this` is S, the second P. The original callee stores these at
owner `+0,+4,+8,+10,+C`, respectively, after its `1080A0` reset; its remaining
initialization is not run by this sidecar.

Record 8's separate `64FCB -> 10DC70` contract is detailed first above.
Finally, `64FDD -> FF3C0([world+ABA32DC])` has `this=world+A7E04D0`; it calls
`FF420` then stores the renderer at `this+28`. This call takes a renderer
pointer, not another resource slot.

## Asset identities

The asset path is the literal above with the leading separator removed and
`Z` appended only to `.ROM`. All decoded assets begin
`IGSROM02\0\0\0\0ACTINDEX`. Both raw and decoded bytes are checked, and
original `1EC0` independently reproduces every decoded SHA-256.

| ID | Raw / decoded bytes | Raw SHA-256 | Decoded SHA-256 |
| --- | --- | --- | --- |
| 2 | 10310 / 30310 | `aef52204cba53037a97658de390e916fd1d418040f92a6c95e3bd4e766470b92` | `8920aec8158d2fb82814d2a61e101ec4a35f1adfbdc208d249cb56702c99faf2` |
| 3 | 150825 / 369164 | `dd7e4f767b5821db267d1ad109af39b94b8f316e63557b0a207a4025369a0a88` | `f7792beb9deef4eeffe026d6b403ec629052dc1eedf3d8b01eaaf9d9d826e842` |
| 10 | 793930 / 2262740 | `37241f1e1af509e8254b7b182eeaee43b541ecdbfdfa979463f6ffc483723254` | `54303d9af579c7b5f5cc4e65b5ab31c843a53643846eaf13a50eeddd80636ed0` |
| 12 | 281578 / 567998 | `efa62f3528d9b9e8d19d3885eca4706f851cc4dbaed62b7438fd80a808c6ed7f` | `86a71831926432c81835873bd37de73c3b0bfa1677c968d487a16cf2f9fffd95` |
| 8 | 1175259 / 3424824 | `e27e8ab9d5859c1337609095e90fa116898fd06722242edc8cdf5001d4a67901` | `a562820d3f8f31955a309cc5916561c7eaa3c13eb49b5e864d406f8debcc3a5c` |
| 9 | 313016 / 1156346 | `6867c8639cafafb95077de1a583d737262f4f2f50b98e1ce26b4c49a1e3502b8` | `6694fbe66c07e31553ae50a11757ce8a6660b1f3024846534711f3d223b33739` |
| 46 | 92448 / 251378 | `6ecd4b398d344e28bf704a9436981a1c8670a4e562c74bf61a25c77d7a4c8dc9` | `e1b35fc578842049e6b55da80615047572e9a4602a58f293e0cc4c3691fb5fba` |

Original `29820..298ED` filename preparation is independently run for every
path. It appends `Z` when the byte four positions before the string end is
`.` (`298AB`), so the already-compressed NameShadow path stays `.ROMZ`, not
`.ROMZZ`. The prepared mode is `rb`. The concrete prefix is the current
client CWD `C:\Users\risei\Desktop\God2\God2`.

## Reproduction and boundaries

From `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B -m tools.strike_lab.current_world_startup_assets
python -B -m unittest discover -s tests/research -p test_current_world_startup_assets.py -v
```

The existing reader import adds `artifacts/tooling/crypto-oracle-python` to
the Python search path for Unicorn. Tests also require the existing Capstone
installation. The CLI prints a JSON manifest; it does not write artifacts.
Manifest RVAs/offsets are JSON integers. `HANDLE_STORES` tuple columns are
writer RVA, source record, base label, offset, width in bytes. `CONSUMERS`
lists callee targets, receiver expressions, argument order, and store effects.

Six bounded tests cover all source rows and native fields, all original
decompressions, seven original startup/ROM open arguments, conditional owner
and finalization callsites, static symbolic handle-store dataflow, and the
record-8 effect-manager setter/reset instructions. The symbolic test reads
the pinned machine instructions; symbolic loader returns never enter the VM.
Original decompression has a 400-million-instruction/60-second per-call cap;
other native calls retain the existing 50-million/30-second caps. Raw sizes
are pinned before reads, decoded outputs capped at 4 MiB, heap at 16 MiB.

Explicit limits and unresolved integration:

- Reused CRT/CSV adapters supply decoded text at `2530/27B0`, including CRLF
  translation. The original parser, record indexing, inline writes, path
  resolver, and independent decompressor execute unchanged. Native temporary
  file lifecycle and live application construction remain outside this probe.
- Startup slices stop before `60A90`. Record 9's formatting and argument
  slices are separate; its world predicate, allocation, and owner constructor
  are source-traced but not executed. The EBP alias exposes only the existing
  reader pointer. No display world or actual manager is constructed.
- The ROM prefix uses slot zero solely as a filename-probe input, as in the
  existing reader helper. It stops before fopen, never inserts a bank slot,
  never returns a startup handle, and never bypasses a negative-handle check.
- Full `60A90 -> 29820 -> 2A1D0` insertion, current counter values, optional
  secondary-bank state, success/failure, graphics dependencies, handle
  lifetimes, and live `100180` execution remain the main owner's work.
- The `64F50..64FB7` stores and final consumer calls are statically traced;
  this helper does not execute a fabricated handle continuation. Source IDs,
  paths, hashes, load ordering, and the record-8 handoff are resolved.

Only these three new files are authored:

- `tools/strike_lab/current_world_startup_assets.py`
- `tests/research/test_current_world_startup_assets.py`
- `docs/research/current-world-startup-assets-20260919.md`

No UI, network, descendant agents, or modifications to the shared host.
