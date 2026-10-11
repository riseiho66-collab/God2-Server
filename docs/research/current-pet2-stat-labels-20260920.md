# Native pet2 stat labels

## New evidence

The original pet2 background has now been decoded and visually inspected.
Unlike equipment tooltip arguments, these labels belong to the pet2 ability
panel reached by S2C FB. This resolves13 previously unnamed numeric controls,
including four attack/defense fields. It does not recover original wild values.

Source chain (addresses are hexadecimal RVAs):

1. Pinned image A3B20..A3B4E passes bank36(decimal), action75/open and76/close
   to104EA0. Descriptor1913C0 sets origin0,0 and dimensions252x427.
2. Pinned FieldComm3.csvZ row36 binds bank36 to Data3/Flow/petegg.romZ.
3. Original ROM action75 is named FPet2_BGOpen; action76 is FPet2_BGClose.
   Both select image69/palette3. The decoded background visibly contains
   physical/magical attack/defense, four attributes and five-element labels.
4. Descriptor array1913E0 has28 records of22 bytes, with control ID and x/y.
   A4076..A40B8 iterates this array for text creation.
5. Existing executed FB receive ->72-byte record -> selection -> numerical
   consumers are documented in current-monster-inspect-identity. This new
   audit independently checks each numeric read, control argument, formatter
   call, descriptor position and original asset identity.

## Label mapping

Offsets below are hexadecimal, measured from the72-byte FB body (opcode at
logical offset0; body begins at logical+1). Each listed input is an unsigned
little-endian WORD. Coordinates/control IDs are decimal.

| Original label | Meaning | Body offset | Logical offset | Control | x,y |
| --- | --- | --- | --- | --- | --- |
| 物攻 | physical attack | 10 | 11 | 8 | 85,143 |
| 物防 | physical defense | 12 | 13 | 9 | 85,163 |
| 魔攻 | magical attack | 14 | 15 | 10 | 188,143 |
| 魔防 | magical defense | 16 | 17 | 11 | 188,163 |
| 力 | strength | 24 | 25 | 13 | 45,216 |
| 體 | constitution | 26 | 27 | 12 | 45,197 |
| 智 | intelligence | 28 | 29 | 14 | 45,235 |
| 速 | speed | 2A | 2B | 15 | 45,254 |
| 金 | metal | 18 | 19 | 20 | 200,197 |
| 木 | wood | 1A | 1B | 21 | 200,216 |
| 水 | water | 1C | 1D | 22 | 200,235 |
| 火 | fire | 1E | 1F | 23 | 200,254 |
| 土 | earth | 20 | 21 | 24 | 200,273 |

Attack/defense uses `%3d`; attribute/element fields use `%4d`. These are minimum
print widths, not numeric limits. Placeholder999/9999 text in descriptors is
not an original stat value. No base/current/buff semantics or stat formula is
inferred from the labels. Body24..2A is four attributes, NOT four attack/defense.

## Provenance and validation

- Image SHA256:149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
- ROM raw SHA256:b5b8e903bc3c95b8f3205a51f5c59125396c99ef346eb084ae26cae91ef37d37.
- ROM decoded SHA256:d608021aa5d731ea43526c6ce6643a78e8c786bd08d10fa3462a11e9b0e583e8.
- Indexed pixels SHA256:248c2b7ca5ec437efb2d0d9070dade162bc157f51e8d231e21adad1c078c4f21.
- Action offset501655, pool offset501759, image offset415760 (decimal).

The resource decoder and coordinate model reuse current_four_stat_ui_binding.
Labels were read from the original252x427 background, not guessed from byte
order or message proximity. The new audit is static code/asset analysis, not
a live render. Existing original instruction receiver/consumer tests were
rerun:5 pass; new resource/binding test:1 pass.

```powershell
python -B -m unittest tests.research.test_current_pet2_stat_labels tests.research.test_current_monster_inspect_identity -v
python -B -m tools.strike_lab.current_pet2_stat_labels
```

Initial audit failures were hardcoded format assumptions: actual stat format
is%3d, while attribute/element format is%4d. Both literals are now pinned and
checked separately. No client code was patched to satisfy the test.

## Remaining boundary

### Full inactive receiver follow-up

`test_full_inactive_receiver_preserves_sequential_supplied_values` now runs
the original A52A0 receiver through its actual `ret 4` at A5392, not merely
through the copy at A52F3. The pinned image is unchanged. Three related UI
handles (world+232DC8, +232E50, +232E6A) are explicitly -1 for this diagnostic.
The genuine AD080 call executes its negative-handle branch and AD547 epilogue;
no callee is stubbed. Rendering calls A5345 and A538B are not reached.

Nine sequential synthetic updates (three slots, three payload seeds) retain
all 72 supplied bytes exactly, preserve other slots and object storage, and
perform only eighteen DWORD row writes per accepted update. A missing
metadata key returns without writes. Stack cleanup, callee-saved registers
and unchanged image bytes are checked. Handles are restored after each probe.
This excludes a post-copy stat recalculation on this inactive-UI path only.
Active UI paths, actual incoming official values and wild-to-pet conversion
remain unproven; none are replaced by the synthetic diagnostic payloads.

An initial harness run attempted to fetch the inherited non-executable stack
return sentinel. The probe now stops at an RX image address before executing
it; neither stack execution permission nor original instructions were changed.

FB receives these values from the server. The identified ROM supplies labels
and layout, not the stat values. Native metadata selection still uses an NCP
item key, not the wild area/scene/ordinal identity. No official capture, wild
conversion preservation or native monster species values have been recovered.
Original wild attack/defense values remain0; database promotions remain0.
Next investigate the wild-to-owned-pet identity/value relationship, not the
already-resolved control names. Production combat remains incomplete.
