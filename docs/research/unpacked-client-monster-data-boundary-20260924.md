# Unpacked client monster data and rendering boundary (2026-09-24)

The game currently launches the directly patched unpacked `God2.exe`
(SHA-256 `230d311bc8dcd9fd0be826dd9878d0331acae4ba27ef06a5b50259db0b0bc423`).
The clean unpacked base has SHA-256
`5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde`.
Direct PE RVA-to-file comparisons show that both EXEs have byte-identical
monster lookup, CSV loader, actor constructor, ROM decompression, render
resource, RTB animation, and result-scalar code at the ranges below when
compared with the previously executed mapped image. Therefore the existing
read-only native probes apply to the actual unpacked client now in use.

| Native RVA range | Verified operation |
| --- | --- |
| `5A0A0..5A1A0`, `5A1A0..5A560` | EnyName lookup and catalog loading |
| `54210..54478` | FightEny row loading |
| `115C90..116080` | Battle participant creation and resource choice |
| `29820..2A1D0` | ROM open/decompression path |
| `121630..1216D0`, `1CD40..1CD90` | Sequence and render-resource selection |
| `2F330..2F4D0`, `30839..30A10` | RTB animation reader and frame renderer |
| `12D970..12D9E5` | Received actor scalar copy |

## Located current-client data

* `Data2/Patch/Comm/gamedata.csvZ` (SHA-256
  `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`)
  contains EnyName source entries. The pinned catalog preserves 7,815
  occurrences in 97 groups; 7,791 remain lookup-visible in 96 groups. These
  are encounter/name lookup entries, **not** a proved count of unique species.
  The safe lookup key within this bank is area, scene, and one-based ordinal.
  Name or source label alone collides across records.
  A readable JSON export at
  `artifacts/research/current-monster-readable-20260924.json` retains every
  occurrence, exact identity/source references and explicit null numeric
  fields. It decodes names strictly as CP950; 11 source names that fail that
  decoding remain null with their original name bytes preserved.
* `Data2/Patch/FightEny.csvZ` (SHA-256
  `887f721a429aaa394d79787ccbd42d544cbcc53a878802cd5f8d010e55dc5a6a`)
  maps battle resource rows to graphics paths. One original native path binds
  EnyName area 1 / scene 0 / ordinal 1, named 三碑鴨 in CP950, to row 15:
  `Data2/Fight/Eny/eny5015.ROMZ` on side 1 and
  `Data2/Fight/Eny1/eny1015.ROMZ` on side 0. Both files are present.
  This is one verified routing example, not a general per-monster art join.
* RTB examples such as `Data2/Fight/Spg/spg9001.rtb` contain animation objects
  and frames. The qualified frame fields control movement, visibility and
  display opacity. A resource-cache slot or sprite number is not a monster ID.

## Numeric result

There is **no verified original, identity-bound wild-monster stat row** in
these sources or qualified render paths. The existing inventory keeps level,
HP, MP, constitution, strength, intelligence, speed, physical/magical
attack and defense, five elements, EXP, capture eligibility, skills and drops
as `null` for all lookup-visible entries. This means unknown, not zero.

The battle participant's displayed level is supplied by logical S2C `1C`
byte `+2`; it is not read as a fixed level from EnyName. The traced ROM load
constructs graphics/animation objects without supplying HP/MP or attack/
defense. A separate result packet can copy supplied scalar DWORDs into actor
fields, but that is a dynamic result, not a species base-stat database.
The tests also show that native `CDCDCDCD` reset bytes and side-0 constants
`1` are initialization values, not original monster statistics.

The following existing focused suites were rerun after the direct unpacked-EXE
comparison: monster inventory 9/9, base stats 7/7, binary/render producer
10/10, ROM resource initialization 5/5, offline monster probe 4/4. No
production monster DB or combat rule was changed.

To recover numeric stats, the next useful edge is the authoritative producer
of the battle participant/result packets with a proven monster/variant identity,
or a current source file that the original client/server demonstrably joins to
that identity and stat field. Names, graphics and animation alone cannot
establish HP, attack, drops or rates.
