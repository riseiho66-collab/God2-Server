# Beta role status: opcode 0x29 to original labels

## Result

The beta character status panel identifies four attack/defense fields and
five element fields. Native packet writer A7B00 and refresh A7C20 were executed
with synthetic inputs; only UI formatting E1A30 and color E1AC0 were mocked.
This establishes packet field meanings, NOT native monster values or formulas.

All addresses below are RVAs in the pinned beta analysis image. Logical offsets
include the opcode byte, unlike body offsets. All packet values are LE WORDs.

|Meaning|Body offset|Logical offset|Role offset|Control decimal|Asset x,y|
|---|---|---|---|---|---|
|Physical attack|0x18|0x19|0x92|23|194,217|
|Physical defense|0x16|0x17|0x94|24|194,242|
|Magic attack|0x1C|0x1D|0x96|30|194,267|
|Magic defense|0x1A|0x1B|0x98|31|194,292|
|Metal|0x08|0x09|0x9C|25|44,216|
|Wood|0x0A|0x0B|0xA0|26|44,235|
|Water|0x0C|0x0D|0xA4|27|44,254|
|Fire|0x0E|0x0F|0xA8|28|44,273|
|Earth|0x10|0x11|0xAC|29|44,292|

## Evidence chain

- Opcode 0x29 dispatch at 64BEA calls A7B00 with packet+1. Length thunk
  returns 31. Existing beta_resource_writers tests cover these links.
- Owner+76BD0 is the role pointer. A7BCE/A7BDF/A7BF0/A7C01 copy
  four packet WORDs into role+94/92/98/96 respectively.
- A7FD8/A7FF7/A8019/A803B read these same fields; formatter calls
  A7FE9/A800B/A802D/A804F target controls 24/23/31/30 respectively.
- Constructor A9068 supplies close action39, open action38, bank34;
  A9096 constructs the panel and A909B saves handle owner+120632.
- FieldComm3.csvZ row34 selects Data3/Flow/FS2_GUI.rom. Its original
  Status_BGOpen action38 selects image26. Descriptor table150120, stride22,
  supplies the matching control coordinates.
- Labels were visually read from decoded original role-panel.png, not inferred
  from marker numbers. Source hashes and asset metadata are in role-stat-labels.json.

## Four attributes are not recovered base values

Body WORDs0..3 go to role+88/8A/8C/8E, adjacent modifier controls18..21.
Their labels align with constitution, strength, intelligence, speed, but the
base-number controls are14..17. Refresh uses signed values and positive/negative
formatting. WORDs9/10 at role+B0/B2 are masks controlling color and conditional
negation of modifiers. Calling these four packet fields base attributes is wrong.

The tests use masks zero and values1,32767,32768,65535. Attack/defense remain
unsigned; modifier format arguments sign-extend. This does not exhaust mask
behavior or validate live combat.

## Formula follow-through and limits

A direct WORD-displacement scan also found 752EE writing object+92. The caller
passes object+90 to status constructor A9030 (75313,75395,75398), so object+92
is NOT role+92. Likewise 69081/690E4 read a pointer at owner+76BD4, not the
identified owner+76BD0 role pointer. Equal displacements do not prove equal fields.
Other object identities remain unqualified. Linear disassembly can miss rebased,
indexed, bulk-copy or indirect accesses; this is not exhaustive writer coverage.

No official damage, defense reduction, critical formula or MP-debit timing is
established by this artifact. No monster stat dataset is created. Production
C++/Lua code and database are unchanged.

## Reproduce

```powershell
python -B -m tools.strike_lab.beta_role_stat_labels
python -B -m unittest discover -s tests/research -p 'test_beta*.py' -v
```
