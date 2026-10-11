# Current Monster Numeric Source Discovery

**No original wild-monster numeric value was qualified in this bounded scan.**
The delivery supplies14 concrete source candidates with hashes, decoded offsets,
literal schemas and authority limits. It does not complete numeric recovery and
does not justify a default HP, an empty skill/drop list, or a zero probability.
The removal of an unproven HP default is separate from source recovery.

Only the new tool, test and this document are changed. No identity branch was
expanded, no original full loader was rerun, and no previous identity/card
regression sweep was duplicated. No runtime, database, shared document, build,
network, UI, live-client or child-agent work occurred.

## Strongest Candidates

Offsets in this table are decimal decoded byte offsets. Native readers/calls
are hexadecimal RVAs in the pinned mapped image, BASE400000, file offset=RVA.

| Current source | Concrete evidence | Qualification limit / reader |
| --- | --- | --- |
| `Data2/Patch/Comm/NewCombatPet_Category.csvZ` | Header line4 at99 labels columns3..6 strength/constitution/intelligence/speed and column9 probability.464 occurrences of literal `Base100_Index37`, first at210. | Companion category source, not wild-monster stats. `CategoryDetailNum` literal189FA0, call56B01 -> **5C640**. The token is not an actual base-stat vector. |
| `Data2/Patch/Comm/NewCombatPet_QualityStar.csvZ` | Header line3 at51 labels Lv0..Lv15. Existing current-source audit qualifies two16-WORD QualityValue/StarValue rows. | Real numeric table tokens, but no wild-monster identity or base-stat semantics. Prior qualified readers **5CA70/5CAD0**; not rerun here. |
| `Data2/Fight/Spg/cbspec2.bin` | Version1.03,448 populated110-byte definitions, four banks with stride6E04h. Every record offset/hash is retained. | Definition envelope only, not monster ownership or numeric effect semantics. Current static call **110C45 -> 12D3B0** verified; original loader already qualified by main. |
| `Data2/Patch/Comm/ChangeDollEffect.csvZ` | Header line3 at56 labels column3 basic effect value. | Already-audited card-effect definitions; not a wild-monster vector or assignment. |
| `Data2/Patch/Comm/gamedata.csvZ` | `FightPetSkill` declaration at2483701 and `NewFightPet2Skill` at2492739. | Static calls **56813 -> 58920** and **5685E -> 58AC0** verified. No wild-monster ownership, cost or numeric-effect producer qualified. |
| ActMis and four FuDai item-list tables | Explicit item-ID/quantity headers, with exact header bytes and offsets retained. | Requirements/item lists do not prove monster drops, probability units, denominators or conditions. |

The other candidate records preserve gamedata's generic item header and the
two innate-related table schemas. The report records why each remains
unqualified instead of interpreting its number columns by position or name.
No stat values are copied from pets, cards, equipment or descriptions.

The Category reference is validated directly against current image bytes:
literal `CategoryDetailNum` at**189FA0**, pointer operand at**56AC1**, E8 call
at**56B01** targeting**5C640**. All464 `Base100_Index37` token offsets are
reported; the exact byte token has zero occurrences in this pinned image.
This rules out treating that cell itself as a recovered numeric base vector.
It does not rule out a computed/encoded interpretation elsewhere. The earlier
current companion audit qualified Category columns0..8. Its column-access
tracing proves columns9..11, including `Base100_Index37`, are not read by the
qualified row interval. The full loader/other consumers remain outside that
proof; no numeric interpretation of the token is supplied here.

Important source hashes:

- Category raw: `80c2b7d366d2ef0264df78f20de1b20fa21e14f6592f56676b090f83ddc064c6`.
  Decoded: `f8d1a1c22e8fc9195dd625ffc244e2ebbcee07492116976feece0bd9d26b813b`.
- QualityStar raw: `52b414716947b4982d74c7da4166f35f4dd1b8e2cba27265aa3f854a2ba8756e`.
  Decoded: `fde6e5b716e710d39b1b706efabd1cfc9d58ef9fc353033d709b38b4bc1a5fbf`.
- Skill binary: `7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51`.
- Gamedata raw: `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
  Decoded: `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
- Image: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`,
  `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.

## Bounded Inventory

The fixed current sibling client `God2/Data2` contains8321 regular files:
65 CSVZ,1 BIN,190 RTB,14 CAN,145 HMDZ,71 MBD,142 each MBDZ/MDLZ/MDTZ/MMBZ,
6323 ROMZ and944 WAV. No CSV/DAT/LUA extension was observed in that inventory.
That is an observed filename-extension result, not a semantic absence claim.

All1054 non-media files were hashed:89594765 raw bytes. The65 CSVZ and142 MDTZ
files decoded to7144581 bytes with the existing bounded0516 reader. Three
previously analyzed card/visual files were not reinterpreted, leaving204 text
outlines. The207 decoded files and known skill envelope are distinguished from
**846 semantically unexamined binary files**. The7267 ROMZ/WAV bodies were not
read. Hashing a binary does not qualify its schema or exclude monster data.

Search scope is explicit: exact field labels within the first80 text lines,
plus lexical ASCII section declarations. CP950 rendering is a search aid;
raw bytes, offsets and hashes are authority. The tool makes no claim of complete
natural-language search, binary/archive parsing, or executable analysis.
The previously covered NPCAppearData and EnyName/SpecialEnyInfo content spans
are excluded from candidate qualification. Their records are not re-enumerated.

Traversal rejects links/reparse points, bounds depth at12 and files at12000,
and reads only the fixed current tree plus the pinned mapped image. Limits:
8MiB per file/expansion,128MiB total raw reads,32MiB total decoded bytes.
Output contains every inventoried path/size/extension, each selected file hash,
decode status, candidate schema evidence and explicit unexamined boundaries.

Existing current-source findings were consulted to avoid repeating card,
visual, companion-growth, skill-catalog and skill-assignment analyses. Historical
recommendations in older audit prose were not followed. No archived source or
script that reads one is used by this tool or its tests.

## Exact Numeric Next Target

The only proposed immediate source check is **NewCombatPet_Category,
56B01 -> 5C640**, conditional on the full loader/consumer path still being
unexamined by main. It is **not wholly unexamined**:
[the existing companion proof](companion-growth-evidence-20260919.md) executes
row interval **5C6A6..5C9B5**, reads columns0..8, and proves columns9..11 are
not read there. Do not repeat that row proof. Only inspect the remaining full
loader/consumers for actual use of the probability/base-token columns. The
established scope is **companion/pet category only**, with no wild-monster
numeric binding. This is not a claim that every possible consumer is pet-only.

**11740A -> 12D970 is disqualified as a source-recovery target.** It was already
qualified in [current_battle_scalar_result.py](../../tools/strike_lab/current_battle_scalar_result.py)
and [its tests](../../tests/research/test_current_battle_scalar_result.py):
logical **86 subtype1**, **side0 only**, packet DWORD **+9 -> actor+DEC** and
packet DWORD **+5 -> actor+DF4**. It copies dynamic incoming scalars; it is not
a numeric producer or original monster-data source. The previous proposed
frontier and ambiguous operand ordering are withdrawn. The machine report,
including summary output, retains this correction under
`disqualified_source_recovery_targets`, separate from `numeric_next_target`.
No scalar proof is rerun. All21 field-authority entries remain null with0
verified monster records.

## Verification and Handoff

```powershell
python -B tests/research/test_current_monster_numeric_sources.py -v
python -B -m tools.strike_lab.current_monster_numeric_sources --summary
python -B -m tools.strike_lab.current_monster_numeric_sources
```

All7 focused tests passed in10.883 seconds after the review correction. The added
seventh regression checks the prior scalar proof's exact mapping, side/subtype
and explicit source-recovery disqualification. Tests check current-only read access,
inventory completeness within scope, every candidate schema's source offset
and hash, all448 definition envelopes, the464 literal offsets, native call
bindings, excluded prior namespaces, read/count bounds, pin rejection and null
authority. JSON is emitted to stdout; no separate artifact file is created.
No native loader/emulator run was needed because no new wild numeric source
qualified. Delivery stops here for main review; numeric recovery remains open.
