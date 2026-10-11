# Unpacked client level and experience boundary (2026-09-24)

The clean unpacked `God2.unpacked.exe` has SHA-256
`5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde`;
the directly patched game `God2.exe` has SHA-256
`230d311bc8dcd9fd0be826dd9878d0331acae4ba27ef06a5b50259db0b0bc423`.
Direct PE RVA-to-file comparisons confirm that both contain byte-identical
native code in the role-level receiver, role-EXP display, packed progression
receiver, progress-bar geometry, battle-EXP display, and `GodLevel` loader
spans below, compared with the previously executed mapped client image.

| Native RVA range | Verified use |
| --- | --- |
| `E6B40..E6BD4` | S2C `22` copies supplied level byte and EXP-display WORD into role state |
| `E6390..E63F0` | S2C `2B` copies supplied state including EXP-display WORD |
| `E6C90..E6D25` | Converts role EXP-display WORD to displayed percentage |
| `AA200..AA2E1`, `AA480..AA508` | S2C `31` copies packed per-row percentage and formats it |
| `1060F0..106202` | Progress-bar width geometry; drawing itself is beyond the executed slice |
| `118BF0..118CA8` | S2C `89` displays received battle EXP for different recipients |
| `5A880..5A9C0` | Loads the four-row `GodLevel` category names |

## What the client actually supplies

* S2C `22` body byte `+0` becomes role level at actor `+26`; body WORD `+12`
  becomes actor `+58`, used by the EXP percent display. These are copies, not
  a level-from-total-EXP calculation.
* The role display multiplies actor `+58` by float32 approximately `0.01`.
  This converts the supplied display unit to a percentage; it does not reveal
  the total EXP or next-level requirement.
* S2C `31` stores low 15 bits of packet WORD `+25..26` as a per-row progress
  amount and stores the high bit separately. The client formats the amount as
  a percentage and turns it into bar geometry. The observed bar truncation
  and saturation are drawing behavior, not a leveling formula.
* S2C `89` contains concrete received-battle-EXP display numbers at logical
  offsets `+5` (character), `+9` (companion), `+13` (pet) and `+53` (cave).
  The client display path does not show how the award was calculated or
  credited to persistent total EXP.

## Source-table check

The current `Data2/Patch/Comm/gamedata.csvZ` and `message.csvZ` retain their
previously pinned hashes. A bounded scan decoded all 66 non-GB CSVZ files under
`Data2`/`Data3` (111 CSVZ including GB variants) and examined ASCII
`section_name,count` declarations containing `exp`, `experience`, `level`,
`upgrade`, or `growth`. The only match is `GodLevel,4` at gamedata line 21164.
Its four CP950 rows are 小仙位, 正仙位, 強仙位 and 齊仙位 with IDs 1..4.
Original loader/reader tests identify them as category text, **not** XP
thresholds. This bounded name search cannot exclude an encoded, unnamed,
strided, dynamically generated, or server-only table.

No original per-level XP requirement, cumulative curve, level transition,
cap or stat-growth formula is established. Character, companion and pet
progression must remain distinct. The server's explicit-table Lua diagnostic
policy and test vector `0/100/300/1000` are custom fixtures, not original game
values; they must not be imported as the recovered curve.

The machine-readable, hash-pinned current-client role-growth inventory is
`artifacts/research/role-growth-unpacked-20260924.json` (SHA-256
`0c839aa460912005092e3671db053069c9a14088008bd94205883358f322c5b3`).
Its missing original requirements remain explicit nulls. A second `--check`
run reproduced the artifact byte-for-byte.

Direct unpacked-code comparison was followed by 14/14 role-progression,
9/9 packed-progress, 16/16 role-growth and 7/7 battle-EXP focused tests.
No production leveling values or rules were changed. Recovering the original
curve needs the authoritative sender/source for total EXP, next-level
requirement and level transition, or verified original threshold data.
