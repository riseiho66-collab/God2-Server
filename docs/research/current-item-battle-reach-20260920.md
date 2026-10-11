# Native Item Data to Battle Reach

## Result and Boundary

The previously static metadata+120 -> battle+64 edge now executes with actual
current client item rows. Original item parsing, original index publication,
original59A60 lookup, battle field write and original target selection are
tested in the SAME VM. They have explicit staged entry points, not a continuous
live item-equip-to-battle session. The existing loader's decimal CRT adapter
remains in use; neither consumer stage replaces a callee or patches code.

This establishes an item-derived target reach value. It does NOT recover
attack/defense damage, critical probability, MP charge timing or wild stats.
No production combat, database, original game executable or archive was edited.

## Source Binding

The hash-pinned current gamedata.csvZ and image are loaded by
`NativeItemMetadata`. In the native WPN/EQU/TWP/TEQ parser arm59721:

- 59748 supplies column index29 to original51B50.
- 59753 calls that field reader.
- 59758 writes AL to item metadata+120, truncating to one byte.

First current rows tested:

| Section / item key | Source line | Column29 | Parsed byte120 | Battle field64 |
| --- | --- | --- | --- | --- |
| WPN / 1 | 4804 | 2 | 2 | 2 |
| EQU / 1001 | 5435 | 0 | 0 | 0 |
| TWP / 19001 | 15478 | 2 | 2 | 2 |
| TEQ / 20001 | 16108 | 0 | 0 | 0 |

These are four actual records, not an all-item audit or proof that every
category is equipped into this caller's slot during legitimate gameplay.
The harness explicitly supplies the lookup key in owner+85940.

## Native Consumer Stages

Stage1 enters117940, calls original59A60, and stops at11796B. The native loader
previously published the record pointer through59A20. For the retained valid
key,117959 reads metadata byte120 and117968 writes its zero-extended value to
battle+64. The complete metadata record remains unchanged. No source reach
value is manually copied into battle state.

For missing metadata, the diagnostic key7F58 exercises59A60's actual rejected
key branch. The consumer chooses constant2 at117963 and stores it at117968.
There are no metadata reads on that path, and the valid retained pointer is
not cleared or replaced to fabricate a lookup failure.

Stage2 enters114A35 separately with actor0 and both occupancy masks3FFF.
It retains the value written by stage1, calls original115700/1156E0 and the
full11EDA0 target-filter path, then stops at114A5E. Only battle+434/+438 are
written outside the stack. Both stages restore their stacks. This is native
source-to-field and field-to-target evidence with explicit entry boundaries.

## Verification

Three unittest methods pass: four source-record cases, native missing-key
fallback, and invalid-section rejection. The tests check source column versus
parsed byte, retained lookup, exact metadata read, allowed writes, unchanged
record and target-mask agreement with the previously qualified range model.
An initial test-harness boolean-precedence bug omitted write observations; it
was corrected without changing original instructions or relaxing assertions.

```powershell
python -B -m unittest discover -s tests/research -p test_current_item_battle_reach.py -v
python -B -m tools.strike_lab.current_item_battle_reach
```

The CLI reports source line, key, column, byte, battle value, masks, stage
boundaries and native read/write observations. Loader input hashes retain
their existing enforced pins. This result narrows the formula investigation:
do not reuse item column29 or battle+64 as a damage multiplier.
