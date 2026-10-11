# Current Item Action Binding, 2026-09-20

## Result

The original writer is RVA `81763` in function `81700` (VA `481763`
and `481700`). With the current MIS:4660 row and current MIS03 ROM on the
**same VM**, it changes item metadata `+118` from `FFFF` to `007A` (122).
It also changes `+116` from RomMaps index 37 to ROM bank slot 102.
Original consumer `9B720` subsequently returns `(102, 122)`.

This is an executable bounded sidecar, not a completed battle bootstrap.
Main has since integrated native MIS03 loading and this binding into the actual
bootstrap VM. Its normal initializer now crosses the former initialFFFF boundary;
see current-battle-bootstrap-20260920.md for the precise scope and tests.

## Pinned Inputs

All addresses below are RVAs unless marked VA. Base is `400000`; the mapped
master image has RVA equal to file offset.

- Image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`
- Image SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`
- Current client `Data2/Patch/Comm/gamedata.csvZ` SHA-256:
  `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`
- MIS:4660 is decoded physical line 7636, icon 51123.
- RomMaps index 37 is physical line 95: range 51001..51200,
  `data2\ItmImg\MIS03.rom`.
- Current client `Data2/ItmImg/MIS03.romZ`, 252030 bytes, SHA-256:
  `01b319617e60c4bcf478af7a5798b275a61fce0ee28c785176de801639895970`
- Decoded ROM, 384327 bytes, SHA-256:
  `ac9c2649e68bd8e699e296a9c5e7ac3e1afa06d79d095179ee1d5da993f086a7`

## Original Evidence

`current_item_metadata.py` executes `59943` (initial group) and `5994A`
(initial action `FFFF`). Those are initialization stores only.

| RVA | Original operation |
| --- | --- |
| `818D1` | Direct call to `81700`, with the owner in ECX. |
| `81704` | Reads owner `+CFF70`, the catalog pointer. |
| `8170A` | Reads catalog `+D2AA0`; nonzero skips the entire binding. |
| `8171A` | Starts at catalog `+B2D44`, item ID 1. |
| `81723` | Iterates `7F57` entries, IDs 1 through `7F57`. |
| `81731..8173B` | Reads WORD record `+116`; negative groups are skipped. |
| `8173D` | Adds `41` hex to the group. |
| `81742` | Zero-extends WORD icon at record `+114`. |
| `81749` | Writes rebased group to record `+116`. |
| `81754` | Reads the resolver/renderer pointer from owner `+CFF60`. |
| `8175B` | Calls `1AE70(group, icon)` on that renderer. |
| `81763` | Writes returned AX to record `+118`. |
| `8176A` | Accepts a nonnegative signed AX; otherwise enters fallback. |
| `81773..81795` | If item ID 1 exists, copies its group and resolves literal icon 1000; `81795` writes fallback AX. |
| `817B3` | Writes 1 to catalog `+D2AA0`, preventing a second rebase. |

Resource placement is also supported by the original preload caller:
`650E5` stores `41` into object `+AA36474`, then `650EE` calls `64820`.
That function walks the RomMaps array at catalog `+D2D58`, passes each row's
path and current slot to `29820` at `648B3`, and increments the slot at
`648E7`. Therefore RomMaps index 37 occupies slot `65 + 37 = 102`.
The sidecar executes one direct `29820` load for that qualified slot; it does
not claim to execute all 57 preload iterations.

`1AE70` reads renderer `+0C` to obtain the bank, computes
`bank + group * 1514`, then searches the action pointers at record `+1090`
using the DWORD count at `+108C`. Each action's first DWORD is compared to
the icon. The return is the **zero-based ROM action index**, not icon 51123
itself. Unlike `1AE20`, `1AE70` does not accept small values as direct indices.
For this ROM there are 200 actions; entry 122 has ID 51123. No arithmetic
icon-to-action shortcut supplies the game return.

## Executed Stages

1. Reuse the existing ROM-bank constructor and bounded CRT/allocator/file
   adapters from `NativeRoleDollResources`. Its three pinned RoleDoll files
   are read during base initialization, but no RoleDoll resource is loaded.
2. Attach the main-owned `NativeItemMetadata(vm=...)`. Its original tokenizer,
   RomMaps rows, MIS:4660 parser, index-store instruction and lookup execute
   in the resource VM. Retain the registered record; do not copy it from
   another VM or seed the catalog index from Python.
3. Read the native RomMaps path and call original `29820(path, 102)`.
   Original decompression `1EC0` and ROM parsing `2A1D0` execute. The bytes
   entering the ROM parser are checked against the pinned decoded source.
   The original loader changes `.rom` to `.romZ` before its single open.
   Observed loader EAX is 6539, **not** a fabricated resource handle or slot.
4. Execute original renderer constructor prefix `1AA26..1AA44` with explicit
   RGB555 surface, zero optional argument and the native bank pointer. This
   writes renderer `+0C`; the rest of the renderer constructor does not run.
   Owner `+CFF60` is explicitly bound to this small renderer fixture.
5. Execute the complete `81700` function, including its 32599-entry sparse
   index walk, real `1AE70` call and completion guard. Instruction allowlisting
   admits only `81700..817C0` and `1AE70..1AEBF`. Nonstack writes must be the
   two original record writers and the catalog completion store. Canaries
   and all other record bytes are checked. No game callee is stubbed.
6. Call original `9B720` against the same owner/catalog; verify `(102,122)`
   and output canaries. A second `81700` call makes no writes or resolver calls.

The fallback writer `81795` is a static finding, not an executed fallback
claim. Missing-ID resolver probes execute `1AE70` and return `FFFFFFFF`.
The qualified successful path does not fabricate item ID 1 or invoke fallback.

## Main Integration Handoff

`bind_existing(native, owner=..., table=..., record=...)` executes the writer
on an existing VM without installing a parser, creating a resource handle,
or changing owner bindings. `native` uses the existing resource runner's
`vm`, `u32` and `call` interfaces and its standard `current_indoor_resources`
stack. It deliberately accepts only the sparse MIS:4660 catalog profile.

Required inputs on the **bootstrap VM** before calling it:

- Native `29820` load of the pinned MIS03 source into bank slot 102, retaining
  its original action pointers and count in that VM.
- Owner `+CFF60` pointing to a qualified renderer/resolver whose `+0C` points
  to that bank. Owner `+CFF70` must still point to the retained native catalog.
- Initial catalog completion flag `+D2AA0 = 0` and original record
  `(icon,group,action) = (51123,37,FFFF)`.

After the writer, require `(group,action) = (102,122)` before extending the
normal battle execution. The relationship between that owner resource bank
and subsequent battle rendering/transfer is not established by this sidecar.
Do not pass slot 102 to an unrelated battle bank containing only its ten
FightComm3 resources, transplant action pointers across VMs, or jump past the
main integration's current boundary.

## Verification

Run from the server root:

```powershell
python -m tools.strike_lab.current_item_action_binding
python -m unittest discover -s tests/research -p test_current_item_action_binding.py -v
```

The six focused tests cover same-VM source/parser/index provenance, original
ROM loading, exact writer trace/canaries, ID search and missing-ID returns,
completion-guard idempotence, and rejection of a different catalog/record.
The CLI prints source line, native load result, action count, resolver
arguments, writer addresses, executed RVAs and original consumer output.
Final focused run: **6/6 passed in 11.092 seconds**. The standalone CLI also
completed successfully with 200 actions and consumer output `[102, 122]`.
The observed loader/parser checkpoints are `29820`, `1EC0`, `2A1D0`,
`2C090`, `2D930`, and `28740`; this asset does not visit `2D250`.

Only these new files belong to this sidecar:

- `tools/strike_lab/current_item_action_binding.py`
- `tests/research/test_current_item_action_binding.py`
- `docs/research/current-item-action-binding-20260920.md`

No main loader/bootstrap/parser files were edited. No retired archives,
network, client UI, database/runtime, CMake/sharedfiles or child agents were used.
