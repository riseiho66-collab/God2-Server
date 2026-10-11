# Ordinary weapon restrictions, tooltip arithmetic, and received2C boundary

2026-09-27. Bounded current-client audit; no server runtime, client, production
database or desktop changes. No retired corpus was searched. Instruction
addresses below are VA, base00400000.

## Result for server integration

**No equipment-to-final-attack/defense or damage calculation was established.**
The directly reusable native arithmetic is tooltip display decoding, range
endpoints and encoded-level presentation. It must not generate a2C snapshot
or authorize a server equipment transaction.

A new concrete distinction: original TWP19071 and19072 descriptions explicitly
say male-only and female-only, yet their ordinary double-click28 route sends
the request without reading the role pointer or role data.96 complete native
requests exercise WPN1/2 and these two TWP keys, slots0/34, three poisoned role
blocks and all four deity-status low-bit values. This proves the client can
request an item despite absent client-side role checks; it does **not** prove
the original server would accept it.

The1259 current source weapon rows contain69 explicit gender descriptions,
all TWP:35 male-only and34 female-only. These are useful source restrictions
to preserve. Character-sex encoding, server eligibility enforcement and
exceptions need separate authority; this lane does not map them to a guessed
profile bit or install a new admission rule.

## Pins and reproduction

| Input | SHA256 |
|---|---|
| Current God2.exe | 6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98 |
| Current gamedata.csvZ | 70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731 |
| Decoded gamedata | 75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815 |

```
python -X utf8 -B -m tools.strike_lab.current_weapon_equip_restrictions_20260927 --output artifacts/reports/current-weapon-equip-restrictions-20260927/native-vectors.json
python -O -X utf8 -B -m tools.strike_lab.current_weapon_equip_restrictions_20260927 --output artifacts/reports/current-weapon-equip-restrictions-20260927/native-vectors-optimized.json
```

Both PASS:124 native level-format vectors,16 native range-endpoint vectors,
96 full-return native requests. Source scans retain69 original restriction
texts, physical source lines, raw CP950 bytes and row hashes. Both JSON outputs
are identical SHA256
`2a3e1b8cac3a1219d38c94131f6b5f70f9f5fa754a517a2ca6cf2c5efe982074`.
Checks use explicit exceptions and remain active under optimization. The output
file is replaced only after the entire verification succeeds.

The request harness uses a deliberately exact tooltip-cache hit; it qualifies
the admission/request path, not fresh formatting or graphics. Existing fresh
formatter coverage is in `current-weapon-fresh-tooltip-20260926.md`. Original
game instructions/callees execute; the reused resource fixture supplies current
native definitions, actual WPN ROM data and an absent sound device. Only its
existing imported timeGetTime adapter is outside the game code. Synthetic
instances/role blocks are test operands, never native item generation.

## Encoded source level: presentation, not a character comparison

459420 parses WPN/TWP numeric source column28 into definition WORD+11E.
4B6020..4B6152 consumes it as follows:

```
base = uint16(definition[0x11E])
grade = uint32(instance[12:16]) >> 30
adjustment = [0, 1, 3, 5][grade]       // native SHORT table005926D4
adjusted = signed16((base - adjustment) & 0xFFFF)
shown = max(1, adjusted)               // signed WORD compare at004B603F
if base < 1000:                       // ORIGINAL base, unsigned compare
    display shown + "級"
else:
    display (shown / 1000) + "轉" + (shown % 1000) + "級"
```

Integer division is native signed truncation; after floor1 the value is
positive. The new probe reaches the actual547AF7 formatting-call boundary and
checks format pointer plus numeric arguments, including both quotient and
remainder. It does not merely stop after subtraction.

The format branch uses the unadjusted base, which matters at the boundary:
synthetic base1001 with grade3 displays **0轉996級**; it does not switch to
the plain-level format. Raw32768 and other artificial high WORDs also require
the signed16 wrap/floor order. These synthetic edge values are marked as such
in JSON and do not expand the source-valid domain.

Actual source domains:

- WPN630 rows: levels1,5,10,20,30,40,50,60,70,80,85,90,1030,1060,
  2030,2060,3060,4060,5060.
- TWP629 rows: levels1,10,20,30,40,50,60,70,80,90,2120,3122,
  4120,4124,7125.

Thus5060 is presented as5轉60級 and7125 as7轉125級 before grade adjustment.
This encoded unit is not interchangeable with an arbitrary character level
BYTE/WORD; no ordinary equip comparison to the character's level was found
in the traced route. Source+11E is not a physical attack value.

## Instance centers and definition widths

4B45B0 unpacks physical/magical centers from the20-byte received instance:

```
physical = instance[7]  | (((instance[19] >> 4) & 3) << 8)
magical  = instance[12] | ((instance[19] >> 6) << 8)
```

Both centers are unsigned10-bit values. The four other displayed attributes
are the existing9-bit unpack documented in
`current-weapon-attributes-snapshot-20260926.md`; they are not role prerequisites.
4B4414/4B448B read definition BYTE+11C/+11D (source columns26/27) as physical
and magical display widths. Nonzero width produces endpoints `center-width`
and `center+width` at4B445C..4B446D using32-bit arithmetic. **There is no lower
clamp**: synthetic center0,width5 gives-5..5. Width0 takes the other scalar
formatting branch; the new endpoint vectors deliberately cover nonzero widths.

WPN1 has widths5/3 while source description says attack24/6. TWP19001 has
widths6/4 while its description says38/12. These distinct values are not an
item generation, aggregation, damage randomization or roll-probability formula.
The signed quality extraction at4B4213 remains the prior verified bits27..29
of instance DWORD+12, range-4..3; it is separate from grade bits30..31.

## Exact ordinary request conditions and source labels

For a valid inventory control and event bit04,49A330 performs source lookup
459A60 by the slot's lowWORD key. It handles the UI+866E4==1 modal message,
checks open panel UI+232DFE, requires an existing definition and tests
definition+11A bit04. That flag corresponds to source RowDesc column16
`可否裝備`. It then calls49B5E0 and496550, followed by4D5910.

496550 independently requires UI+866E4==0 and no bit20-open panels at
UI+232DEA/UI+232E20. It sets DWORD UI+85608 to1 and queues exact logical
`28 key:u16 slot:u8 flag:u8`; this UI branch passes flag1. The producer itself
does not validate a role level, owned item, slot class, or destination. Native
UI input constraints must not be confused with server authorization.

49B5E0 only considers7000<key<8000. UI+866BA low2bits==2 rejects7101..7200
or7401..7500; value1 rejects7201..7300 or7501..7600. Its SystemMessage866 is
the deity-equipment sex message, not ProgramMsg866 and not an ordinary-player
sex check. Existing4012 native guard vectors already cover that domain; this
lane does not relabel it as a general player predicate.

New source-backed counterexamples:

| Key | Family / physical source line | Source column7 / parsed definition+2E | +11E |
|---|---|---|---|
|19071|TWP /15548|限男性角色裝備|10|
|19072|TWP /15549|限女性角色裝備|10|

The original metadata parser executes for both; its actual+2E text and+11E
WORD are checked. Each still emits28 for every tested synthetic role/deity
configuration. A read hook sees neither UI+86888 nor the role block accessed
on the complete cached-tooltip request path. There is no role write.
This is evidence of a **missing client-side check on this path**, not permission
for the server to ignore the source restriction.

No ordinary-player profession or two-attribute minimum comparison was found
on this exact double-click path. The two+11C/+11D numbers are display widths,
not such minima.4B4060's three high instance flags format ProgramMsg518
無法強化,519無法修理,517不會損壞.4B632B's bits22..23 display1034此道具已鎖定
or1037解鎖中. None is a profession/sex comparison.

## Targeted alternative-reader audit

The current decompiled+11E readers were checked to avoid borrowing another
item-family predicate:

- 4A2D60 indexes selected pet slots42/43 and reads **BYTE**+11C/+11E/+120
  thresholds against pet record+23 for action controls3/4/5.
- 4A53C0 indexes slots42..44 at stride48h and compares **BYTE** thresholds
  to record+3 for pet action controls7/8/9.
- 4AD880 likewise uses BYTE threshold/skill-key pairs for companion UI
  selection. These are not WPN's WORD+11E equip checks.
- 49A330 contains other drag/drop and companion routes. Its role+449E read
  appears in the item-drop/other action branch, not the double-click28 route
  tested here. The bounded negative result is not a claim about every UI path.

## 2C and the remaining authority gap

The current61-byte2C consumer4E6600→4E6710 copies and formats received values.
Logical offsets45/49/53/57 are physical defense/physical attack/magical
defense/magical attack DWORDs, copied to role+98/+94/+A0/+9C. Modifier WORDs
and masks have the prior verified16-bit sign behavior; preserve the raw61
bytes rather than reserializing already-negated actor memory.

Existing512 full-return2C vectors establish unchanged role vitals/God memory
and no inventory aggregation. No new edge in this lane connects weapon
definition/instance centers to these final four received values. Reuse the
strict `RecoveredRoleAuxiliary` snapshot contract for independently owned saved
values. Do not add/subtract tooltip centers or source description bonuses to
manufacture a snapshot after28.

Remaining concrete authority: original server equip legality (including sex,
profession, level/turn and other requirements), owned-instance generation,
equipment/buff/base-stat aggregation, and damage/defense settlement. Source
text and native display arithmetic narrow those questions but do not answer
them. No custom formula or unverified runtime restriction was installed.
