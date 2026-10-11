# Current ordinary weapon attributes and independent role snapshot

## Result and scope

Current unpacked Taiwan `God2.exe` SHA256
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
Only this PE and current Data2 were executed/read. No retired mapped image,
production client/DB edits, desktop operation, or gameplay formula inference.

**S2C2C is the independently usable received attribute snapshot. S2C22 is not
free of UI side effects. Neither supplies an equipment-to-final-stat formula.**

New header `src/protocol/RecoveredRoleAuxiliary.h` strictly parses 61 bytes and
preserves all raw bytes. Accessors expose physical/magical attack/defense raw
DWORDs. The values' high bits are preserved without assigning gameplay signedness.
The parent owns persistence/routing integration; this report does not claim it
completed. Native oracle success is separate from rendered/live acceptance.

## Source definition versus owned instance

`Data2/Patch/Comm/gamedata.csvZ` SHA256
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
All row numbers below are one-based decoded physical lines. JSON retains exact
raw row bytes and decoded/source hashes.

- Line 4803: `WPN,630`. Line 4804 key1 菜刀: description contains
  `基本能力 物攻+24，魔攻+6`, `基本提昇 體力+10`, `攻擊距離 2`.
- Line 15477: `TWP,629`. Line 15478 key19001 精淬菜刀: description contains
  `基本能力 物攻+38，魔攻+12`, `基本提昇 體力+10`, `攻擊距離 2`.
- At 459420, selectors1/25 (WPN/TWP) copy zero-based CSV columns26/27 to
  definition+11C/+11D BYTE, column28 to+11E WORD, column29 to+120 BYTE.
  The four numeric values are 5,3,1,2 for key1 and 6,4,1,2 for key19001.
  Those are not 24/6 or 38/12. Description columns8..12 are concatenated text.
- 4B4200 uses definition+11C/+11D as the two tooltip range widths, and 4B6020
  uses+11E for the displayed level condition. The confirmed battle reach
  consumer517940 reads weapon slot34's definition+120. None of these edges
  computes final role attack/defense from description text.

The owned 20-byte instance arrives through S2C3B→498DD0, which copies it into
the inventory record. Definition parsing is not an instance constructor.

### Actual weapon tooltip values

4B5BE0 dispatches instance family1/25 to4B45B0. The native unpacker builds six
WORD operands for4B4200. Let `b = instance[19]`, offsets below are zero-based
within the 20-byte instance:

| Label | ProgramMsg ID | Native operand |
|---|---:|---|
| 物攻 | 520 | `instance[7] | (((b >> 4) & 3) << 8)` |
| 魔攻 | 522 | `instance[12] | ((b >> 6) << 8)` |
| 力 | 74 | `instance[8] | ((b & 1) << 8)` |
| 體 | 73 | `instance[9] | (((b >> 1) & 1) << 8)` |
| 智 | 72 | `instance[10] | (((b >> 2) & 1) << 8)` |
| 速 | 75 | `instance[11] | (((b >> 3) & 1) << 8)` |

The first two are 10-bit values; the latter four are 9-bit values. Current-PE
258-vector execution reaches the real formatter call and checks both operands
and label arrays. This proves instance display decoding, not actual equipped
damage or stat aggregation. Armor4B4690 uses the same packing with labels521
物防 and523魔防; it is static follow-up, not included in the weapon vectors.

Message source `message.csvZ` SHA256
`5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598`:
ProgramMsg72..75 at lines2098..2101;520..523 at2546..2549;
569等級限定/570轉/571級 at2595..2597;1066品質 at3092.

### Quality and displayed level condition

- 4B4213 reads DWORD instance+12; SHL2/SAR29 extracts a **signed three-bit**
  quantity from bits27..29, range-4..3. It indexes a prefix table around5926C4
  and appears with ProgramMsg1066品質. Eight bit patterns are executed. Do not
  reinterpret this as an unsigned0..7 enhancement level.
- 4B6027 independently reads the same DWORD's top two bits. Those select
  SHORT table5926D4 `[0,1,3,5]`, subtracted from definition+11E for display,
  with signed WORD floor1. Twelve small positive boundary vectors executed.
  Encoded level>=1000 uses 轉/級 formatting. This is a tooltip path, not a
  character level refusal or recovered enhancement/generation algorithm.
- The origin of valid owned quality/enhancement rolls, associated costs,
  rerolls, and final stat combination remains unproved. Preserve owned bytes.

## Why22 is not attribute-only

22→4E6B40 writes level, four base stats, progress, state word and HP/MP maxima.
It then calls4E6DB0 and4E72D0→4AC070(actor,0,0).

With valid owner HUD handle and both maxima nonzero,4AC070 clamps current
roleHP/MP to maxima. If actor+D0 is bound, this call's `(0,0)` branch requests
God HUD frame/group31/action75, gauge control4 value0 and empty text. Eight
full-return vectors verify the branch for HUD disabled/enabled and maxima
0/80/100/200. The entire 4096-byte synthetic God record is unchanged.

Thus22 does **not** run24's4E71E0 HP-loss deduction on God HP, but it can hide
the God HUD gauge and clamp role vitals. Even preserving maxima does not avoid
the God HUD refresh. No claim is made that a later native message restores it.
The test uses empty native widget records and captures real call operands; it
does not certify actual rendered pixels or every role-sheet state.

## S2C2C independent contract

Current length-table `[401324 + 4*2C]` points to401228; its native return is61.
World dispatch469EDE→4E6600 and battle519370 case2C call the same consumer.
Logical bytes: opcode2C followed by60 raw body bytes. All offsets below are
decimal body offsets, not logical offsets.

| Body offset/width | Actor offset | Meaning/scope |
|---|---|---|
| 0,4,8,12 / WORD | 88,8A,8C,8E | Raw four modifier operands |
| 16,20,24,28,32 / DWORD | A4,A8,AC,B0,B4 | Five received values; no formula assigned |
| 36,40 / WORD | B8,BA | Formatter positive/negative masks |
| 44 / DWORD | 98 | Physical defense display |
| 48 / DWORD | 94 | Physical attack display |
| 52 / DWORD | A0 | Magical defense display |
| 56 / DWORD | 9C | Magical attack display |

Four attack/defense meanings follow the separately documented current resource
binding in `current-four-stat-ui-binding-20260920.md`; refreshed current C and
native execution here confirm each source offset→actor→formatter edge. The
source spacings of four bytes do not turn the modifier WORDs into DWORD reads.
Keep their unused high bytes and both masks' unused high bytes intact.

4E6600 calls4E6710. It formats the received values; it does not read inventory
to aggregate them. For modifiers at88/8A/8C/8E, respective bits are2/4/1/8.
If BA has a bit and B8 does not, native refresh negates that WORD with16-bit
wrap. Positive-mask presence wins. Replaying the original wire reloads before
negation; serializing already transformed actor fields would be incorrect.

512 full-return cases cover all low-four-bit positive/negative mask pairs and
role-sheet handle disabled/enabled (empty native backing). Each compares all
4096 actor bytes to an independently built expected result and all4096 God
bytes to their canary. Role current/maxHP/MP stay unchanged; there are no God
memory writes and no4AC070 HUD-update calls. No metadata or inventory is read
in the demonstrated stat copy path. This qualifies **received raw snapshot
replay**, not a formula for creating a snapshot after equipment changes.

## Reproduction and C++ connection

New files:

- `src/protocol/RecoveredRoleAuxiliary.h`
- `tests/test_recovered_role_auxiliary.cpp`
- `tools/strike_lab/current_weapon_attributes_native_20260926.py`
- `artifacts/reports/current-weapon-attributes-20260926/native-vectors.json`

Standalone test compiled with MSVC C++20 without the shared core build. It
checks exact framing, all61 truncated lengths, trailing byte, wrong opcode,
opaque roundtrip, field order and high DWORD bits. `--emit-native` returns the
codec's encoded61-byte hex. Powershell after building the test:

```powershell
$wire = & artifacts/reports/current-weapon-attributes-20260926/role-auxiliary.exe --emit-native
& C:/Users/risei/AppData/Local/Programs/Python/Python312/python.exe -O -m tools.strike_lab.current_weapon_attributes_native_20260926 --packet-hex $wire --output artifacts/reports/current-weapon-attributes-20260926/native-vectors.json
```

Result: PASS8 native22 cases,512 native2C cases,258 weapon unpack cases,
8 quality cases,12 displayed-level cases, plus compiled C++ output through
full native2C return. The compiled case uses nonzero opaque bytes/masks and
high-bit values; exact actor comparison and God/role-vitals preservation pass.
Typical runtime about13 seconds. Checks remain active under Python `-O`.

## Remaining edge

There is no demonstrated WPN/TWP definition→owned instance generation or
equipment→final two-attack/two-defense calculation in this bounded trace.
Confirmed current consumer receives final display values via2C. Next original
authority needed is the server-side sender of2C after28, or a distinct current
native producer that populates these values before emission. Tooltip operands,
static description bonuses and independent four-stat snapshot must remain
separate until that edge is proved. Existing owned snapshots may be preserved
and replayed; silently changing them using text bonuses is not justified.
