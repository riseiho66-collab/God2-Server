# Current C2S25 item frontier — 2026-09-26

## Result

All five direct calls are present in the current Taiwan client. They belong to several different UI routes: general item activation, selected-slot activation of older PET categories, item shortcuts, a special-item confirmation, and virtual-point/card confirmation. **C2S25 is not a generic consume-one request.**

This bounded review found no additional item operation with an already qualified complete event → authoritative effect → S2C response chain. The closest small extension is **SPI:5576 崑崙仙界地圖**, reusing the map-panel experiment after a new loaded-client acceptance test. That would extend the explicitly CUSTOM-0023 policy; it would not recover an original 25→3F association or prove non-consumption. Do not count a second map ID alone as a new general item service.

The premise that 25 has only a parser needs qualification: `src/core/Application.cpp` around 967–1036 already handles owned item5569 under diagnostic town/map gates and emits `3F 01 00`. Its comments and research correctly label this CUSTOM-0023. Other C2S25 operations remain unimplemented by that route.

No shared source, DB, client or configuration was changed. No game or desktop interaction was performed. No retired corpus was consulted; historical references inside older reports were not followed.

## Sources and validation

- Current `God2/God2.exe` SHA256: `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
- Current `Data2/Patch/Comm/gamedata.csvZ` SHA256: `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
- Analysis pseudocode: `God2-解殼EXE原始碼重建/decompiled/functions/00483c80_FUN_00483c80.c`, `004963c0_FUN_004963c0.c`, `0049a330_FUN_0049a330.c`, `004ea770_FUN_004ea770.c`, `004eb440_FUN_004eb440.c`, `0049f7d0_FUN_0049f7d0.c`, `004ae520_FUN_004ae520.c`.
- Current source rows decoded with `recover_items.build_items`; they are source descriptions/flags, not original server effect implementations.
- Existing native-producer and map-response execution evidence: `current-inventory-item-request-20260919.md`, `current-item-transition-20260919.md`, `current-town-map-use-20260921.md`, `private-map-item-ui-20260923.md`, `live-packet-chain-20260924.md`.

Fresh PE RVA mapping and disassembly confirmed the five CALL instructions all target VA00496350:

| CALL RVA | Current bytes |
| --- | --- |
| 84481 | `e8ca1e0100` |
| 964C1 | `e88afeffff` |
| 9A6B9 | `e892bcffff` |
| 9AA07 | `e844b9ffff` |
| EA85C | `e8efbafaff` |

The following entire mapped byte ranges also match the preserved current-native image (`native-master-01-stable.bin`, SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`) byte for byte. High endpoints are exclusive. This is a fresh static identity check, not newly executed full UI paths.

| RVA range | Current SHA256 |
| --- | --- |
| 83C80–84499 | `b939ba704ac59244c2e0bfc4871e57f52e2f386f08861b6e717497aeeec1c014` |
| 96350–964D0 | `e8e8e00554069d76758f60a348ef2d54896e4962a9867223ee92dabf53e2b762` |
| 9A330–9B5E0 | `5e9c7ddf9224b10d9f88180a355cebb00d5c18a7600f44bedfaf6cfaa0c2f5c3` |
| EA770–EA8A0 | `4a71d2049ece628590771012084099685f24302a50d401cacd6c08422b72ae7f` |
| EB440–EB620 | `eae04066a85daea2109b8c3bd8516c70db474e650b0c9b7ca3a0481fcb1d31c0` |
| 9F7D0–9F7F0 | `d01a0f529eef37f8b4fd92f474812d6d19228542910ad25f6f60c20c96ea8d2c` |
| C3840–C3930 | `6950441ccd7f251d6ee2c230a53c72c16ac3ab4015428ecf0486d35b57ddbf9d` |
| 99300–99350 | `8c7ec67a849e8252c4bd1a864a248bbb7ffcaaad408476d026d8fa0338e92219` |

## Shared producer contract

RVA96350 queues only when DWORD `[UI+866E4] == 0`. It appends exactly five logical bytes:

```text
25 item_low item_high slot_low opaque_tail
```

It overwrites the first argument's low WORD with the item, replaces argument byte2 with the slot, and leaves argument byte3 untouched. The third stack argument is never read, although most callers push1. Thus `raw_tail = (first_argument >> 24) & 255`, not a request quantity. No generic ID/slot/ownership validation occurs in this producer. Each caller has its own preconditions; the server must authorize an owned instance independently.

## The five callsites

### 1. RVA84481: special-item confirmation, kind 0x3B

`483C80` handles confirmation input. For the relevant path, event mask0x01 is set, mask0x02 is clear, control index is0, and `[UI+23D5D8] == 0x3B`. It takes item/slot saved at `[UI+232EBC]+3AE50/+3AE52`, calls96350, sends control request1F/0, and closes the confirmation.

The originating activation in49A330 saves those fields and opens `484710(0x3B,...)` for:

- item6368–6387: five-element attribute-up items;
- item6568–6575, 6665–6669, 6763–6765, 6884–6886: master skill books.

Both retain the bag item and await confirmation before this send. Their messages are loaded from source text indices1018 and873 respectively; the item name is inserted. Cancel does not reach this C2S25 call. A stale saved item/slot is not server ownership proof.

**Response gap:** for attribute-up items, no qualified application/expiry/replacement state transaction and S2C attribute/status projection is linked to this event. For books, no qualified learn eligibility, target actor, learned-skill state mutation and reply is linked. S2C3E visual effects and inventory count changes alone would not implement either feature.

### 2. RVA964C1: item shortcut / item-key resolver

`4AE520` dispatches shortcut entries of kind0 to4963C0. The latter requires the866E4 gate clear and a nonzero item key, then searches **slot29 down to0**, accepting a positive signed count with the same low item WORD. Duplicate item keys therefore select the highest matching slot on this route.

For `(item & 0xFFFF)/100 == 53 or55`, it calls96350 with the resolved slot. Other items use metadata flag4 →496550/C2S28, or the C2S26 target-item path. Do not move the existing potion path into25 merely because this function is an item dispatcher.

Source categories covered include PET530x/53xx 座騎神獸 and SPI55xx (maps, transport items and other special items). The arithmetic itself does not prove a common effect or success response for all55xx. Shortcut packing can carry unrelated higher argument bits; raw_tail remains opaque.

**Response gap:** mounts require a qualified owned PET instance, riding/appearance transition and persistence; transport items require destination/eligibility/usage rules. Current map5569 has an explicitly custom candidate-panel response, not general55xx semantics.

### 3. RVA9A6B9: inventory normal-use activation

World UI dispatcher4820A0 routes inventory node `[UI+232DC8]` to49A330. On event mask0x04, it loads the item from the24-byte slot record and metadata via459A60, saves the selected slot atUI+85ABC, and applies the following order:

1. Existing modal/UI predicates can reject activation; the final96350 gate always remains effective.
2. Metadata flag4 (equippable) takes496550/C2S28 after49B5E0 validation.
3. Missing normal-use flag1 rejects. Flag8 together with normal-use enters target-selection UI instead of this25 path.
4. Item15211–15230 diverts to the type6 confirmation described below.
5. Items6164/6165 open the broadcast interface and return. Items6368–6387 and listed master books divert to the0x3B confirmation above.
6. Other native special cases exist before25: item5525 can queue88; items6238/6239 perform local window changes. These do not establish their subsequent server effect.
7. The remaining path sends25(item,slot,opaque), followed by control request1F/0.

The broad normal-use path includes source-qualified map5576. It also includes many unrelated special items; normal-use eligibility is not enough to determine consumption or response.

### 4. RVA9AA07: same-slot release of equippable PET categories

This is a separate branch within49A330. It requires a selected slot, event mask0x20, release onto the same slot, slot in0..49, nonzero item, resolvable metadata and equippable flag4. The selected-slot UI drag state is reset. It then routes to25 when signed item/100 is52,53 or54, or the packed item record type `(DWORD(slot+4)&0x3F0000)` is0x230000. The relevant UI+232DFE panel must be absent or have its0x20 flag clear, and96350 still applies the866E4 gate.

The current source calls these PET categories **傳送神獸**, **座騎神獸**, **探索神獸** respectively. Do not call52 the currently implemented combat-pet type. The current NCP lifecycle uses packedtype34 and C2S28 from reserve42/43 to active44; it is a different branch. The packedtype35 alternative remains numerically identified here, without an invented category name.

**Response gap:** producer dispatch does not itself distinguish inspect/use/riding/transport effects or change the authoritative PET instance. No direct server response association was recovered. Reusing FB/type34 NCP stats or its selection operation would cross an unproven category boundary.

### 5. RVAEA85C: virtual point/card type6 confirmation

Inventory activation calls49F7D0, which accepts exactly15211..15230, then4EB440. The confirmation window `[UI+232DF4]` must be absent or inactive (neither flag0x20 nor8). Item metadata must resolve. It saves item atUI+AFECC, slot atAFEC8, the caller's third byte (currently1) atAFECF, and mode6 atAFECE.

4EA770 requires event mask0x01 without mask0x02 and control3 or4. In mode6, **only control4** queues25; afterward it resets mode toFF and closes the window. This call assembles argument byte3 fromAFECF, so this particular chain commonly emits tail1. That explains a caller-specific value; it does not make the general field quantity.

The range includes VPT virtual subscription cards and virtual-point redemption items. Range membership alone is insufficient: some source rows inside it have normal-use=false and cannot reach it through the observed normal-use entry.

**Response gap:** no qualified account credit/subscription transaction, durable idempotency or corresponding currency/time S2C update is tied to this confirmation. This is not a small inventory-only effect.

## Relevant source records, not a catalog-count exercise

Lines below come from current decoded gamedata (1-based source lines from the importer).

| Key | Line | Source meaning relevant to this frontier |
| --- | --- | --- |
| PET:5211 楓華野狐 | 6520 | 傳送神獸; 0轉20級;50 uses; destination text楓華鎮. No destination coordinates or authoritative decrement rule. |
| PET:5302 普通赤煙駒 | 6554 | 座騎神獸;0轉1級;100-hour lifetime text. No qualified riding response or lifetime clock policy. |
| PET:5401 玉麒麟 | 6644 | 探索神獸;0轉10級;65-hour lifetime text. No exploration result rule. |
| SPI:5569 金鰲島地區地圖 | 8236 | Normal-use, non-equippable, not target-other; existing CUSTOM0023 experiment. |
| SPI:5576 崑崙仙界地圖 | 8243 | Same pertinent use flags; description崑崙仙界地形圖; native25 entry supported. |
| SPI:6368 金屬性提升道具LV1 | 8882 | Text says+300,3hours, one element buff, subsequent use replaces previous. Those description values do not supply execution widths/caps/timing or a reply contract. |
| SKB:6568 劍大師 | 8983 | Active skill, reincarnated deity only; skill-use50MP and critical-description text. Do not treat50MP as the book-consumption cost or infer learning rules. |
| VPT:15211 虛擬包月卡 | 12951 | Subscription-only card, adds one month by description. |
| VPT:15213 虛擬點數1點 | 12952 | Double-click redemption description; no proven server/account credit implementation. |

Selected exact-row SHA256 values:

- SPI:5576: `6877e19719a222a3ad7bf45d1f61526d7364eb3b822890f15845d6a8ca216404`.
- SPI:6368: `06b8074204120efac904f17bcb9b99e965e1ea4c579c623eb54336aa1292900a`.
- SKB:6568: `ce55ff7c2d80521ec869d78a540683b71f936f095efe98b6b3bf9fa673de7d5e`.
- PET:5302: `af39cdbd46d1164aff24e7ed07f49c69c70293f83d2fa60674ab9353ba695288`.
- VPT:15213: `2c77e9d8fbed8a30bd4907bc27c13dc1ed3d8c7b2df2961aa3cedb31c9609a3a`.

## Why adjacent S2C opcodes are not a ready success response

- **3B/3C/41:** inventory projection/clear/count-ID consumers. Their existence does not decide the requested item effect or whether to consume.
- **3E →499300→52E490:** resolves item metadata and visual-effect ID at+112, then creates an actor/location-bound effect. The effect ID must be in84xx. It is not an attribute increase, learned skill, credit mutation or generic success record.
- **3F →4C3890→4C3840:** map panel control. Existing proof requires3 logical bytes, nonzero byte1, valid scene/UI gates; byte2 remains opaque. PMMap source references support the panel family. Actual25→3F pairing and non-consumption remain CUSTOM0023, including the existing resource-loaded and physical-input tests.
- **40 →4E6270→52EF00:** skill effect family, not evidence that a skill book was learned. Dispatcher resolves a skill record before the effect call.

## Smallest useful next acceptance, if this frontier is selected

For5576 only: seed an explicitly owned instance in an isolated database (not an invented native quest reward); start current client in validated Kunlun4/3; perform the actual inventory activation; capture25/slot and full metadata; qualify3F against the loaded Kunlun panel/resource and actual map content; verify no unintended slot, character or UI changes and restart behavior. Keep consumption and response selection labeled custom unless original authority is found. This can produce a working bounded map feature, but this read-only review does not claim that acceptance occurred.

For a genuinely new consumable/buff, SPI6368 has unusually specific original text and a confirmed confirmation event, but it still needs the native attribute/status consumer plus a server expiry/replacement contract. For a new owned-instance operation, PET5302 is the clearest riding candidate, but old PET metadata/instance, owner appearance projection and lifetime state must be qualified first. Neither is currently a ready native-backed consume implementation.

The audit is complete and stopped at these concrete gaps.
