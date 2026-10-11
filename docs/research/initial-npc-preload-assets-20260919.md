# Initial NPC preload assets, 2026-09-19

For area 2 / scene 15, cold NPC preload needs exactly these three ROM sources,
in call order: `Data2/Rom/Npc/npc2401.ROMZ` (mandatory default),
`Data2/Rom/Npc/npc2721.ROMZ` (21), and `Data2/Rom/Npc/npc2643.ROMZ` (2143).
Its catalog is `Data2/Patch/NPC.csvZ`; group provenance is
`Data2/Patch/Comm/gamedata.csvZ`. Paths here are relative to the inspected
client root `C:/Users/risei/Desktop/God2/God2`. This is the NPC portion of
`61AD0`, not an inventory of the other world-entry resource banks.

## Authority and index rules

Read first: `current-npc-resource-groups-20260919.md` and
`current-world-enemy-groups-20260919.md` in this directory; both legacy corpora:

- XJZ root `artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`:
  `evidence-gamedata-npc-list-v0.md`, `evidence-npc-visual-service-binding-v0.md`,
  and `evidence-monster-client-v0.md`. Their grouping/visual evidence does not
  establish this current consumer's argument normalization.
- Classic root `C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`:
  `tools/God2.GameplayContentRecovery/OfficialClientExtractor.cs`, specifically
  NPC template, NPCList and EnyNameTotal extraction. Its preserved source
  fields are not a replacement for the current native lookup.

Pinned mapped image, server-relative:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
3,174,400 bytes, SHA-256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Instruction addresses below are RVAs, image base `00400000`; globals are VAs.

- `5A9F1..5AA25` stores positive NPCList codes as byte quotient/remainder
  of division by 1000. Current decoded gamedata line 4245, byte offset
  142380, is exactly `b'2,15,21,2143\r\n'`. The resulting group is
  `0F 02 00 15 02 8F`: scene 15, count 2, pairs `(0,21)`, `(2,143)`.
- `61BB3` calls `60C60(NPCListPointer, progressObject)`, ECX = resource
  manager. Active NPC bank = manager + `3D5D4 + bankIndex*AD610`, where
  bankIndex is manager+`16CE18`. `60CC8..60CF9` loads both NPC catalogs
  through `5E850(path, 8)` (first call instruction is `60CDE`).
- `60D19..60D34` runs the mandatory default BEFORE testing the group pointer.
  Image bytes at VA `58A58C..58A58F` are `09 01 00 00`.
  Although read as overlapping DWORDs, both values are masked with `FF`:
  category = byte `[58A58C]` = 9; ordinal = byte `[58A58D]` - 1 = 0.
  It calls `5F0E0(9,0)`. Do not apply the scene category `<5` gate here.
- Scene pairs with category `<5` take `60D76..60DAE`: category is unchanged,
  second byte is zero-extended and decremented ONCE, then
  `5F0E0(category, ordinal)`. Thus 21 -> `(0,20)` and 2143 -> `(2,142)`.
- `5F0E0`: category must be nonnegative and below DWORD bank+`2ACCC`;
  ordinal must be nonnegative and below signed WORD bank+`2ACD4+6*category`.
  Signed WORD bank+`2ACD0+6*category` is added to the ordinal, then `5EEC0`
  receives that absolute record index. Both arguments are stack DWORDs,
  ECX = NPC bank, and return cleanup is 8 bytes. No category decrement or
  filename-number arithmetic occurs.

## Catalog records and exact rows

`5E850` uses original tokenizer `51BE0` and row body `5E9B0..5EBF7`.
Header field 2 is 12: data starts on physical line 12. Nonempty column 2
admits a row; column 0 numerically zero/empty uses the running row index
(`5E9D8..5E9EC`). Column 1 is copied verbatim to the record path, column 6
builds category ranges (`5EA41..5EAFA`). Empty paths still occupy records.
All 319 current records have empty column 0, so no index renumbering is needed.

Native category descriptors `(first,last,count)` are:
0 `(0,88,89)`, 1 `(89,94,6)`, 2 `(95,256,162)`, 3 `(257,283,27)`,
4 `(284,317,34)`, 9 `(318,318,1)`; categories 5..8 retain `(-1,-1,-1)`.
Category bound is 10. Records start at bank+`244E4`, stride `4C` (76);
path occupies the first 64 bytes; slot WORD at +64 starts as `FFFF`.

| Request | `5F0E0` args | Absolute record | NPC.csvZ decoded line / byte offset | Exact path column |
| --- | --- | --- | --- | --- |
| Default | `(9,0)` | 318 | 330 / 17611 | `data2\rom\npc\npc2401.ROM` |
| 21 | `(0,20)` | 20 | 32 / 1122 | `data2\rom\npc\npc2721.ROM` |
| 2143 | `(2,142)` | 237 = 95+142 | 249 / 13090 | `data2\rom\npc\npc2643.ROM` |

Full original row bytes, Python bytes-literal notation (including CRLF;
no text transcoding):

```python
b',data2\\rom\\npc\\npc2401.ROM,8,1,0,0,9,5,\xb7\xc6\xb9\xab\xab\xfc\xa9w\xc2I,\xa8t\xb2\xceNPC\r\n'
b',data2\\rom\\npc\\npc2721.ROM,16,6,0,0,0,0,\xb8G\xa7\xa7\xa8k,\xa4@\xaf\xebNPC\r\n'
b',data2\\rom\\npc\\npc2643.ROM,8,6,0,0,2,0,\xc2\xf8\xb3f\xa6\xd1\xc1\xf3,\xa6\xd1\xc1\xf3NPC\r\n'
```

## Paths, availability and hashes

`60C85` supplies `.\` through root resolver `12F550`; `5E7D0` stores the
resolved prefix at bank+`243DC`. `5EEC0` concatenates that prefix with the
record path and calls `29820(path, slot)` at `5EF74`. For `.ROM` paths,
`298AB..298DF` appends literal `Z`, then `298ED` opens `.ROMZ` in `rb`.
It checks `05 16` and decodes through `1EC0`; `299D1` calls `2A1D0` with
declared decoded size + 3. The decoded hashes below exclude that extra
allocation/parser allowance. The original `.ROM` path is the fallback at
`29A6A..29A82`, not an extra required source when compressed loading succeeds.

Catalog literal VA `58A5FC` is `\Data2\Patch\NPC.csv`, root-resolved by
`12F550`; `51960 -> 2530` first opens the path plus `Z` and decodes it,
falling back to the unsuffixed text file when appropriate.
On this client, `NPC.csv` and all three listed `.ROM` paths are absent;
`NPC.csvZ` and all three `.ROMZ` paths exist. No required compressed source
in this bounded list is missing. These are real `Data2` row paths, not a
substitution for a missing `data` path.

SHA-256 over exact on-disk raw bytes and exact `05 16` decoded bytes:

| Source relative to client root | Raw bytes / SHA-256 | Decoded bytes / SHA-256 |
| --- | --- | --- |
| `Data2/Patch/Comm/gamedata.csvZ` | 719032 / `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731` | 2783008 / `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815` |
| `Data2/Patch/NPC.csvZ` | 4050 / `b6afccc3a66e8b3b6f291e62cbdb221b370e1bb5146ed6c2c6f2dd94ee38777f` | 17670 / `2b6f631eb8b5f34333289c958f07e808d9985ebc21c27c6f6ac48f4d1731df63` |
| `Data2/Rom/Npc/npc2401.ROMZ` | 10852 / `4e728a03487842cd09334603dff50e7f52eef3e7c89401597866048db0123e02` | 23139 / `d35c29b93dde80c499feafd4fb46e2a609544eed1f6cc5db4891cfff05c4b512` |
| `Data2/Rom/Npc/npc2721.ROMZ` | 231827 / `0c854a40de383269f6dde53cfc87a94d6d27b0cf590357cb6221ca4837110eda` | 330378 / `4977df017039bc671199962032d041fc6f3e97d655b3ea7ec546d43801688cae` |
| `Data2/Rom/Npc/npc2643.ROMZ` | 40978 / `ef4625d222b9dc3e0cf182fedfc72ffc4d70e69f4c716c8796d4ecbc973fdc08` | 56146 / `92cb6316d08ce79b496bd7deb0f2aacc78fc8afc918e6872f95fbfc28bba7f1d` |

## Verification boundary

Read-only Capstone inspection of the pinned image, current-file existence
checks, and byte decoding/hashing were performed. An ephemeral Unicorn VM
also executed original tokenizer/row-loader slices for all 319 rows using
the existing `NativeNpcResources.load_csv` method and decimal sscanf adapter,
then original lookup `5F130(9,0)`, `(0,20)`, `(2,142)`. It returned precisely
records 318, 20, 237 and the three paths above; native descriptors matched
the independently inspected source rows. Full file-opening/catalog loop,
`60C60` and these three ROM loads were inspected, not executed in that VM.

No bank construction, resource-slot assignment, rendered-world acceptance,
or live client/server execution is claimed here. Existing
`current_npc_resources.py` ordinals 81/87 select different records and its
two-ROM allowlist cannot validate these initial-scene assets unchanged.
Only this document was written; shared world code/tests were not modified.
