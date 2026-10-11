# Native World Display Construction, 2026-09-19

## Executed Boundary

`NativeWorldDisplay` extends the previously qualified embedded-world host.
No live graphics device, client process, socket, UI input or game-function
success stub is used. The original image and data pins are unchanged.

The original display pool begins at `WORLD+39C`, has 4096 records of stride
`A7E0`, and occupies `A7E0134` bytes. Its end is exactly the component-manager
boundary `WORLD+A7E04D0`. The earlier slice-only heap/second-bank/renderer
addresses overlap this real world-relative extent. This host allocates them
outside the pool from the outset: heap `40000000..50000000`, renderer `51000000`,
second bank `51400000`, rectangle manager `51800000`. No initialized object is
copied or its pointers patched after allocation. Old hosts retain their defaults.

Native calls executed:

- Rectangle manager `188A0` then `188C0`: all 3072 records initialized.
- Display constructor `107F30`, its 4096 object constructors and native reset.
- Source-backed `60A90 -> 29820` loads the title asset into both real ROM banks.
- Original `60B10` checkpoints the banks, then `1081C0` binds scene bridge,
  renderer, rectangle manager, actual title slot and ProgramMsg source.
- Component `FF370 -> FF3C0` initializes and binds the real renderer before
  actor initialization. Binding afterward would reset recovered component IDs.

Title source is independently qualified by
`current-world-ui-resource-20260919.md`: FieldComm3 record 2, inline string at
`2*108+4 = 214`, `\Data3\Flow\DTitleGui.ROM`, with actual ROMZ fallback.
The earlier description of +214 as CString was wrong; it is an inline string.
The virtual file adapter allows only this pinned asset and uses the actual
decompressor/parser in both banks. Tests verify both parser inputs and all
five original binding fields; they do not invent a ROM slot or renderer return.

## Tests and Performance

Final command:

```powershell
python -B -m unittest tests.research.test_current_world_display -v
```

**4/4 passed, 54.691 seconds.** Checks cover contiguous gap mapping with no
changes to existing permissions, invalid range rejection, all 4096 display
records, all 3072 rectangles, allocation overlap, SEH sentinel, both native
ROM parser inputs, title-slot binding, component reset/binding and repeated
binding rejection. The prior single-page mapping run was stopped after its
expensive 176MB mapping setup; it did not count as a passed test. The new
host maps only contiguous unmapped gaps, never executable permissions.
An initial title integration run also caught a helper return-unpacking error;
the final full rerun above includes its fix.

Unchanged-default actor regression after the shared lifecycle extension:
**12/12 passed, 73.579 seconds**, with the retired-source open guard active.

## Next Native Boundary

Full `100180..1004F5` display/startup remains unexecuted. The confirmed title
slot now supplies `1081C0` argument 4. Continue actual mounted-component draw
creation (`100950`, `FF510`) and label allocation (`108300`) in this new host;
additional startup ROM handles at `64F50..64FB7` must also be sourced, not
filled with invalid/default values to skip them. The prior later scene/music/
camera tail remains independently qualified, not a claim of full-function or
live-world completion. No original-client playable E2E is claimed here.
