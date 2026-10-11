# Current Monster Auxiliary Sources

Bounded Data/Data3 handoff: **zero newly qualified wild-monster/BOSS numeric
values**. Two new candidate reader references survive review: God selection
menu integers and SpgEft resource integers. Neither establishes original wild
stats, a formula, or monster ownership. Cat is explicitly prior-covered.

Only the auxiliary tool, its focused test file, and this document were written.
No Data2 bodies, retired Classic/XJZ, evidence corpora, Save/logs/config contents,
runtime, UI, network, native execution, or child agents were used. Shared
build/status integration belongs to main. The already-covered Category reader
and incoming battle scalar consumer were not repeated or called sources.

## Strongest Sources

Offsets below are decimal decoded byte offsets. Columns are zero-based.
Native addresses are hexadecimal RVAs in the pinned mapped image, base 400000.

| Source | Exact source evidence | Static reader and qualification limit |
| --- | --- | --- |
| `Data/Patch/God.csvZ` | Header line 4 at 102; ten populated menu rows, first at 185. Columns 4..8 are labelled level, constitution, strength, intelligence, speed. Column 1 is `Protocol`; column 3 is an attribute string. | `God.csv` literal 18A224, operand 5E486, open call 5E4C4 -> 51960. Integer calls 5E570/5E58A/5E5A4/5E5BE/5E5D8 -> 51B50; stores 5E581/5E59B/5E5B5/5E5CF/5E5E7 write DWORDs at owner +125CC/+125D0/+125D4/+125D8/+125DC plus 44 times the column-1 index. This is a menu table; no wild identity or combat-stat authority is proven. |
| `Data3/patch/SpgEft.csvZ` | Header line 38 at 1091; first resource row at 1152. Exact columns: role name, special-skill number, file identifier, filename, Rtg filename, sound index, comment, directory. | `SpgEft.csv` literal 19C610; operands 110BED/12E96E; calls 110C1C/12E9A3 -> 5F2C0. Column 2 integer call 5F38E and store 5F39D; column 5 call 5F3DF and store 5F3EE. WORD destinations are owner +121F0/+121F2 plus 76 times the column-1 index. Columns 3/4 are copied as strings. No damage formula, cost, repertoire, or monster assignment is established. |
| `Data/Patch/Cat.csvZ` | Header line 4 at 97; eight CareerType menu rows, first at 206. Columns 6..10 have the same five numeric labels. | Already covered by `current-world-actor-20260919.md`, `NativeWorldActor._load_cat`, and its all-field test. This audit only retains the source and static references, without rerunning or claiming novel Cat qualification. |

Both menu branches reference the literal `\\Data\\Patch\\` at 18A240.
Both SpgEft call sites reference `\\Data3\\Patch\\` at 19C600. The common
integer helper is 51B50 -> 51BA0; its `%d` format operand and conversion call
are byte-checked. These are static references, not a replay of compressed-file
selection, startup loading, or subsequent gameplay use.

Missing proof is specific: an original wild numeric producer/use and an
authoritative monster bank/area/scene/ordinal/variant or participant-lifetime
binding. Menu Protocol/CareerType, an effect identifier, matching name, or
resource reference cannot supply that proof. No companion, card, visual,
header-labelled, or merely hashed value was substituted.

God raw SHA256:
`fa6673ce89374d135d3109bb1381a1fb0755b18f898af3988f34e1995ad8af44`.
Decoded SHA256:
`679ccd778fd63a578d8d41d92cd1a46ead578d92ab6791ce51a16e0eac84b52d`.

SpgEft raw SHA256:
`28deaec92235298a41485ec324d15b2ea0b6b12fd19db4bbd22870b413f23dad`.
Decoded SHA256:
`5fda6887402a9e034caca1ea48c015ebb25e162c41b23f61fcee1374d931b5cf`.

The sole image is
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
The tool pins seven small static spans and checks literal operands, column
pushes, integer calls, and stores. No general native sweep is implemented.

## Coverage Limits

| Tree | Inventoried in-scope files |
| --- | --- |
| Data | 7 CSVZ, 735 ROMZ, 10 WAV |
| Data3 | 2 CSVZ, 85 ROMZ, 1 RTB |

840 files are inventoried. Two additional entries, `Data3/config.iniZ` and
`Data3/config2.iniZ`, were excluded without opening. Ten files were hashed:
27,578 raw bytes. Nine CSVZ files decoded using `omega_assets.decode_csvz` to
71,569 bytes. All 1,365 physical rows retain raw/decoded file hashes, line
numbers, decoded offsets, row lengths/hashes/hex, and exact byte-comma fields.
The output preserves empty fields and line endings. It does not promote tokens.

The other six tables are `Skill.csvZ` (four crafting menu choices),
`GodDoll.csvZ`, `FightGodDoll01.csvZ`, `FightGodDoll05.csvZ` (visual resource
tables), `IGS.csvZ` (static program-name/action list), and `Message2.csvZ`
(reserved/blocked text). Their classification is source-content evidence;
no extra native-reader exploration was performed for them.

**831 binary/media bodies remain semantically unexamined:** one RTB was hashed
without interpreting its schema, and 820 ROMZ plus 10 WAV bodies were not read.
This is not an absence claim for those binaries or the whole client. Referenced
Data2 resources were not followed. No all-monster completeness is claimed.

Traversal rejects symlinks/reparse points and excludes sensitive/retired paths.
Bounds: 2,048 eligible files, 4,096 directory entries, depth 12; 8 MiB per file,
32 MiB aggregate raw reads, 8 MiB aggregate decoded bytes, and a 4 MiB image.
Tables are bounded to 4,096 lines and 4,096 bytes per line. Unknown future text
files remain explicitly unreviewed; changed pinned tables/images fail closed.

## Output and Verification

```powershell
python -B tests/research/test_current_monster_auxiliary_sources.py -v
python -B -m tools.strike_lab.current_monster_auxiliary_sources --summary
python -B -m tools.strike_lab.current_monster_auxiliary_sources
```

Seven focused tests passed in 0.451 seconds. Tests guard every source open,
verify all table bytes/offsets/fields and inventory counts, validate static
references, exercise path/link/size/count/decode/pin rejection, and enforce null
wild-stat authority. No native loader tests or unrelated suites were run.

JSON is stdout-only; no report artifact or shared integration was written.
The report contains three candidate entries (two new leads and prior Cat),
nine table records, the full bounded inventory, explicit exclusions and binary
counts, and 21 requested fields with null values and zero verified monsters.
`runtime_eligible` and `all_monster_numeric_data_complete` remain false.
