# Current-client teleport authority boundary — 2026-09-26

The menu/selection wire contracts are recoverable, but the five-city teleport authority is not yet established. This targeted search found native city metadata for three labels and current teleport item/NPC presentation records. It did **not** establish a native request that opens this menu, a context-to-item/NPC association, five destination arrival coordinates, or authoritative fee/cooldown rules. C2S `6D 00` must not be treated as the request for S2C `6D` merely because the opcode is equal.

## Sources and reproducibility

Read `AGENTS.md`, `IMPLEMENTATION_PROVENANCE.md` and `GOAL_ACCEPTANCE.md` before the work. Only the supplied current client Data2/Data3 CSVZ/CSV files and current reconstructed-source references were used. Retired `legacy-evidence`, `recover_teleports.py` and the old `world-atlas/teleports.json` were not used as authority. No production source, configuration, database or client was edited; no game or desktop interaction occurred.

Run from the server root:

```powershell
python -X utf8 -B artifacts/reports/current-teleport-authority-20260926/search_current_assets.py
python -X utf8 -B artifacts/reports/current-teleport-authority-20260926/qualify_selected_evidence.py
```

`current-assets-search.json` records hashes for **111 current Data2/Data3 CSVZ/CSV files**, decoded successfully using the existing current-client LZSS reader, and exact matching lines/raw bytes. Traditional files are displayed as CP950; files explicitly named `-gb` are displayed as CP936. Replacement characters preserve undecodable text visibly; raw hexadecimal remains the exact evidence. The first report's `section_hint` is only a search aid. `selected-evidence.json` parses explicit section headers/counts for the selected authoritative rows and records exact source lines, hashes, fields and bytes.

The latter also verifies **11 entire contiguous native function spans** against deployed God2.exe by PE RVA mapping. All match the pinned mapped image SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`; deployed client SHA256 is `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`. Decompiler output is an analysis aid, not recovered source text or proof that every byte in a span is reachable.

## Context and true entry trigger

RVA `F6DA0` checks the exact WORD values `061E..0622` (decimal 1566..1570). `F72B0` echoes the menu's first WORD as selection context and emits `A9` for those five values, `99` otherwise. This proves a discriminator, not an item/NPC identity or list of server-authorized contexts. The normal branch means all other WORD values at the native client branch; it does not authorize a server to accept all such values.

Current `NPCAppearData` contains **zero** records with IDs 1566..1570. Same-number `EQU` rows are 合金護手, 刺針拳套, 魔手-魁魅, 魔手-魍魎 and 五行之戒 (gamedata lines 5924..5928). Other tables reuse the same numbers for unrelated messages/enemies. Therefore a numeric join cannot establish that the special contexts identify those items. The selected evidence preserves those negative/contradictory checks rather than naming contexts speculatively.

The decompiled context storage references are bounded:

- `F6360` copies the 28-byte incoming menu into object `+790EC` and calls `F6B30` to refresh/open it.
- `F6450` initializes/clears that storage and includes initial sample-looking values. Initialization literals are not official server fees or destinations.
- `F6DF0`, `F7160`, `F72B0` read the context; selection subsequently clears the copied menu.
- `F6410` closes the menu; it is not a native menu-request producer.
- `4820A0` dispatches menu controls to `F6A40`: control 3 submits selection; cancel/right-click/control 0/control 4 call `F6A00` and close. `F6A00` queues C2S `86`, length four, with its low WORD derived from `**(this+8688C)` and upper stack bytes not assigned by that local. This is an additional native cancellation path that needs independent server qualification; it does not identify the opening NPC/item.

Only the receiver-to-open chain was found for this menu in these targeted references. No local construction mapping an inventory ID to `+790EC` was found. Independently, the ongoing producer analysis identifies C2S `6D` callers in equipment/inventory state updates; this further rules out establishing request/response semantics from opcode equality. The missing next evidence is an actual UI/NPC/item action producing a request, followed by the corresponding S2C menu on the same owned connection, or a fully traced current native action path. An unsolicited laboratory S2C menu can qualify rendering and selection but cannot recover the official trigger.

## Five labels and current map identities

The native `F6450` table uses ProgramMsg IDs `9,15,16,17,18,506`: blank, 葛城, 昆吾, 韋城, 南巢, 楓華鎮. These exact strings remain in current `Data2/Patch/Comm/message.csvZ`.

| Menu label index | Label | Current Map_City_Coordniate match | Evidence boundary |
|---|---|---|---|
| 1 | 葛城 | area 1 / scene 12 / kind 0, `cityS01`, gamedata line 21021 | Exact catalog name; arrival coordinates unknown |
| 2 | 昆吾 | area 5 / scene 27 / kind 0, `cityS02`, line 21030, name 昆吾鎮 | Name association supported by the 昆吾 teleport-item text; no validated menu-to-scene route |
| 3 | 韋城 | No matching name among all 144 current catalog records | No substitute destination assigned |
| 4 | 南巢 | No matching name among all 144 current catalog records | No substitute destination assigned |
| 5 | 楓華鎮 | area 2 / scene 4 / kind 0, `CityI1`, line 21082 | Exact catalog name; official teleport arrival unknown |

The complete current Traditional gamedata text contains no 韋城 or 南巢 occurrence. This is a bounded absence in the searched current file, not proof those cities never existed. Catalog `x/y` are atlas coordinates and must not be used as arrival positions. CAN/MDT resource presence establishes scene identity/loading metadata, not a server-authorized route or spawn.

## Native NPC and item leads

`Data2/Patch/NPC.csvZ` line 293 defines model `npc3025.ROM` as 城鎮傳送點 / 傳送NPC. Current gamedata `NPCAppearData` IDs 2250 and 2251 (lines 1343/1344) are 傳送法陣 using model 3025; IDs 2277, 2287 and 2288 are 傳送仙童. Additional clearly named presentation records include 4509 傳送仙人, 5066/5070 陵寢傳送師 and 6022 隱藏地傳送師. These records contain appearance information, not qualified world placements, NPC dialogue tokens, activation distances, destinations or menu-context IDs. They must not be spawned at guessed coordinates and called native placements.

Current `SPI` item rows give independent teleport **description** leads:

| Item ID | Name | Native description boundary |
|---|---|---|
| 5501..5504 | 青龍/白虎/朱雀/玄武寶珠 | Regional return to nearest town; no recovered nearest-town algorithm |
| 5571 | 楓華鎮傳送珠 | Return to 楓華鎮; no arrival or five-city menu association |
| 5601 | 楓華鎮傳送寶珠 | Single-player teleport; description says consumed after one use |
| 5605 | 葛城傳送寶珠 | Same description class, destination name 葛城 |
| 5609 | 昆吾傳送寶珠 | Same description class, destination name 昆吾 |

IDs 5601/5605/5609 are gamedata lines 8268/8272/8276. Their shop/value columns are not evidence for teleport fees. Existing current-client `25` item-use qualification for item 5569 concerns 金鰲島地區地圖 and a labeled diagnostic transfer; it does not authorize substituting a teleport gem or tying `25` to this menu. Item 16055 elsewhere is 高級傳送珠 with selectable destination/ten-use descriptive text, but no native context link was recovered in this search.

## Fees, level and cooldown

The native display proves server-supplied fields: each row's trailing WORD is shown as coin cost; body byte 6 below ten selects free text; body byte 5 fills a minute placeholder; body byte 4 high bit enables rows. Normal selection with byte 6 below ten shows the free confirmation; special contexts follow the paid confirmation branch even when the row renderer shows free text. Keep this discrepancy visible rather than deriving a server charging rule from UI prose.

ProgramMsg 14/19/20 are cost/confirmation formats. ProgramMsg 507..511 are free, not-yet-available, waiting-minute and confirmation strings. SystemMessage 516 says level insufficient for the travel service; 517 says below-level-ten free; 518 says below-level-ten unavailable. `F6DF0` selects differing restriction strings by context. These are display branches, not proof of the official cooldown length, free-travel eligibility computation, fee schedule, deduction timing or atomic transaction policy.

Other NPC dialogues mention 500/10,000 coin travel services and mount records describe minute consumption for specific mounts. They concern different identified content; this report does not transfer those prices or cooldowns to the five-city menu. No custom price, destination or cooldown was selected, so historical community references were not needed for a balance choice. If a custom design is chosen later, consult the owner-specified historical references and record that version/source scope separately.

## Existing scene-transfer implementation and hidden-client gate

`RecoveredMovementService` already owns authenticated session/account/character bindings and committed positions. `begin_transfer` checks ready/not-pending state, expected saved baseline, source scene and source-pinned destination cell, commits through the character repository, emits framed S2C `61` and marks transfer pending. `finish_town_transfer` verifies the persisted baseline and resets the movement ring. Existing wrappers support **area 2 scenes 4, 15 and 0 only** (town, qualified indoor, Island01), with source-consensus navigation gates. This is not generic cross-area or five-city teleport support. Town-to-indoor/return and same-position probes are labeled custom diagnostics with separate recorded native-client acceptance.

Application's existing diagnostic route also manages pending transfer receipts, presence and scene-local NPC projection. Reuse its ownership/receipt/cleanup pattern only after qualifying the new contract. A general teleport implementation still needs a validated menu offer, request binding/expiry/replay behavior, destination authorization, authoritative resource deduction and atomic failure semantics. A zero-cost fake success is not a substitute for missing authority. Active parallel work may extend selection grammar/callbacks; that transport work does not close these route gaps.

Available hidden-client harness parts are `tools/strike_lab/private_desktop_runner.cpp`, `private_unpacked_smoke.py`, `private_map_item_current_ui.py`, `apex.py` and `current_scene_live.py`. The C++ runner creates a separate desktop, starts the process/optional observer there and verifies the owner's input desktop stayed unchanged. Existing UI probes are fixed workflows, not an implemented teleport acceptance test. The map probe currently exercises item 5569 and checks a diagnostic marker while preserving position/inventory; it cannot certify teleport completion.

A real isolated teleport acceptance must record:

1. Exact current binary/assets, own-server isolated port/config and a separate account/save copy, with the production inputs unchanged.
2. The actual native opening action/request and S2C `6D` ordering; menu memory at `+790EC`, labels/enabled state and UI selection/cancel behavior.
3. Actual C2S `99` or `A9` payload produced by the native UI, including opaque tail; only a previously authorized offered context/destination can mutate state.
4. S2C `61` receiver completion, correct loaded scene/coordinates/kind/ring and the exact follow-up context receipt on the same socket; no policy-disconnect or stale scene NPCs/presence.
5. Saved position and any qualified payment/item/cooldown state, duplicate/replay rejection, cancel with no mutation, and reconnect restoration. Native UI rendering/selection and durable world transfer are separate checks.

No fresh runtime acceptance is claimed here. The immediately supported route is to retain the qualified transport/selection representation, add a deliberately labeled isolated renderer/selection probe if needed, and trace the real entry action. Production five-city travel remains blocked on the exact authority gaps above; the user-authorized custom fallback, if pursued, must retain its own CUSTOM record and pass its own current-client acceptance.
