# Current NPC asset inventory — 2026-09-27

## Result and scope

**New qualified native NPC placements: 0.** No scene + NPC catalog/instance + x/y + direction tuple was recovered in this bounded lane. This does not establish that such data never existed. No runtime, database, client or desktop changes were made.

Read the reconstruction README, server rules/provenance/acceptance and the prior `native-npc-placement-audit-20260926.md` / `native-npc-source-inventory-followup-20260926.md` first. Existing NPCAppearData/NPCList, ROM, map model, coordinate prose, minidump and original-server-packet absence findings were not reclassified as new placement data. Retired corpora were not used.

Applicable current God2.exe SHA256:
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
The reconstruction is analysis pseudocode, not recovered buildable original source. Preserved IME sources are later patches, and its reconstructed gameplay modules are not an original server NPC table.

## Reproducible inventory

Tool: `tools/strike_lab/current_npc_asset_inventory_20260927.py`.

Output: `artifacts/research/npc-asset-inventory-20260927/inventory.json`, SHA256
`466be0d5aecb810ac67f0e3f7ba407f315b5fe1e607c7583d91c0d2ca355ed6b`.
Normal and `python -O` runs succeeded and produced byte-identical JSON.

```powershell
python tools/strike_lab/current_npc_asset_inventory_20260927.py --output artifacts/research/npc-asset-inventory-20260927/inventory.json
python -O tools/strike_lab/current_npc_asset_inventory_20260927.py --output artifacts/research/npc-asset-inventory-20260927/inventory-optimized.json
```

All **8,365** current Data2 files have path, size, first-16-byte header and SHA256 of the first 256 raw bytes recorded. This is a bounded header inventory, not a whole-file hash inventory or recursive archive decode. No `MAP v1.1` / `MAPSIZE` signature occurs in those headers. Thus there is no supplied raw MAP text file beginning with those headers; embedded/decompressed content is not ruled out by this test.

| Extension | Files |
|---|---:|
| ROMZ | 6323 |
| WAV | 944 |
| RTB | 190 |
| HMDZ | 145 |
| MBDZ, MDLZ, MDTZ, MMBZ | 142 each |
| CSVZ | 109 |
| MBD | 71 |
| CAN | 14 |
| BIN | 1 |

All **109 physical CSVZ files decode successfully**, with original/decoded hashes and first four raw lines preserved. There are **108 unique decoded hashes**, and **45 filenames contain `gb`**. These counts are not independent Taiwan gameplay source counts: GB variants remain distinct physical inventory entries and are not promoted to active Taiwan source authority. The only identical decoded pair is `NewCombatPet_QualityStar-gb.csvZ` / `NewCombatPet_QualityStar.csvZ`. Successful decoding does not qualify every table's meaning or loader selection.

Additional inspected headers: Client.csvZ is version/launch-parameter metadata; FieldComm/FieldComm3 enumerate ROM resources; VmHot_C and VmMenus_C are shop/menu lists. None establishes a world NPC instance tuple.

## Previously overlooked binary-format candidates

All **190 RTB files** satisfy exactly:

`14 + object_count * 52 + object_count * frame_count * 12` bytes,
with `rtbv1.0\0` header, signed WORD object/frame counts at +8/+10 and flags at +12/+13. There are no unaccounted tails under that structure.

Actual reader `0042F330` reads those same blocks, allocates frame arrays and replaces object DWORD+0x30 with a process pointer. `0042F1F0` writes the symmetric layout; `0042E0D0` switches the resource filename ending to `b` before calling the binary reader. These are animation/resource records, consistent with the already documented `current-monster-binary-producer-20260920.md`; a frame's positional fields cannot be promoted into world NPC coordinates without an instance/scene binding.

`Data2/Fight/Spg/cbspec2.bin` is 112,660 bytes, SHA256
`7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51`.
Native callsite `00510C45` invokes `0052D3B0`, which checks four-byte `1.03` then reads exactly `0x1B810` bytes into the skill region at object+`0xA7E0444`. It is the already qualified skill binary, not an additional spawn table. This agrees with `current-monster-numeric-sources-20260920.md`.

## Four missing INI files: complete relevant consumer chain

Current PE names `Data3/config.ini`, `config_gb.ini`, `config2.ini`, `config2_gb.ini`; all four are absent in the supplied current client. Absence alone was not used to discard them.

* `00411BB0`: a `192.168.` input prefix selects config2 versus config; `00531C10` chooses the GB variant. It calls `00412740` before `WSAStartup`.
* `00412740`: skips whitespace/comments; `$` parses an integer, `@`, `^`, `-` parse strings at object+0x504/0x544/0x5C4. `[section]` text is stored in a 0x1804-byte group. At most 64 groups and ten 0x260-byte rows per group are allocated. `004129E0` copies the left side of `=`, and `00412AA0` copies the right side. No fixed NPCID/Map/Direction/x/y key lookup occurs in these readers. The actual missing section/key text cannot be recovered merely from a generic parser.
* `00411A80`/`00411AD0` expose group count / row-name data to login selection callers (including `00406E00`, `00407440`).
* `00412310` and fallback `00412250` format four table bytes using `%d.%d.%d.%d` and return an adjacent WORD. `00413060` passes these values through `00412440` to `00411D30`.
* `00411D30` calls `socket`, optionally `gethostbyname`, `inet_addr`, `htons` and `connect`. This establishes IP-address/port meaning, not a world coordinate interpretation. The exact source-path xref on `00412310` names `netlib/network.cpp`.

Classification: network server-group configuration and associated strings. There is no evidence here for a developer NPC placement editor or a complete NPC placement section. Unknown meanings of special-prefix strings remain unknown; no native NPC field is inferred from them.

## New map-cell naming evidence

The current PE literal `%s%sx%s.map` leads to `00437D50`; writer `00438D80` opens the file and invokes `0043FF50`. The latter writes `MAP v1.1`, `MAPSIZE 21 21` and these exact labels:

| Output label | Input from each 8-byte cell |
|---|---|
| TileNum | signed WORD +4 |
| SpriteNum | BYTE +7 & 0x0F |
| TileIdx | signed WORD +0 |
| Pass | (BYTE +7 & 0x30) >> 4 |
| LinkIdx | signed WORD +2 |
| PalNum | BYTE +6 & 0x1F |

The original function range `0043FF50..0044024B` inclusive hashes to
`8e815ea9ebae731564487cfa8d4845b9bb240746bf7392007c2affdab62f5ef0`.
Its exported pseudocode file hashes to
`9c4f41bfa1855d8dc13e8c445728b6dfaa06ab5deabd24b674e75592c1bac7d5`.
The artifact also pins 16 other reader/consumer ranges and their pseudocode files. This lane supplies static writer evidence. The parent lane has completed the independent native oracle:

* Tool: [current_npc_mbd_cell_followup_20260927.py](../../tools/strike_lab/current_npc_mbd_cell_followup_20260927.py).
* Report: [current-npc-mbd-cell-followup-20260927.md](current-npc-mbd-cell-followup-20260927.md).
* Results: [evidence.json](../../artifacts/research/npc-mbd-cell-followup-20260927/evidence.json).

That oracle passes 16 source-cell getter cases, 16 full native MAP writer returns (20 captured printf calls each), four boundary cases, nine setter cases and 22 model-group cases. Normal and `python -O` results are byte-identical. These executions qualify the cell access/writer/group behavior; they do not supply missing NPC identities or placements.

`LinkIdx` is a useful precise name for the prior audit's unresolved WORD+2. It is **not proof of an NPC index**. The next missing edge remains a native binding from a scene's link/model entry to an NPC catalog/instance and direction. Parent-lane same-type model-group deletion/ordinal evidence must also be respected before attributing that index to an actor.

## What can be integrated

The inventory and cell-field names can improve research/source qualification. **No NPC placement rows can be added from this evidence.** An original server spawn table, a qualified original-world S2C72 capture with known scene, or a demonstrated current-client loader binding all required fields would change that conclusion. This bounded pass does not justify invented coordinates/directions or a claim that all local assets have been semantically decoded.
