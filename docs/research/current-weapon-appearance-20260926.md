# Current player weapon appearance: DA versus 36/37

2026-09-26. Bounded current-client audit. No Application, database, client, desktop or shared implementation changes. No retired corpus consulted. Addresses below are VA, image base 00400000.

## Integrator summary

**36/37 are not the ordinary HeroDoll weapon update route.** Both are 11-byte records, but their four-component resolver is 4614A0→463F80 and the actual current PE string at 0058A990 is `\Data\Rom\GodDoll\`. Ordinary player incremental appearance is **S2C DA, 15 bytes**. Do not use 36/37 to make a bag weapon appear on the player.

A usable native DA serializer contract is now established, subject to an already qualified complete component block. An owned WPN key→component selector mapping is **still unverified**. Hence this report does not authorize guessing an appearance from key1/key2, nor claim a complete playable equip chain.

## Pins and reproduced evidence

Current executable SHA256: `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
Current gamedata.csvZ: `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
HeroDoll.csvZ: `df2fa65e0b159b18303b2e135cacc690e0e02e4ea12560cacda3f0d8e6ae1359`.

New tool: `tools/strike_lab/current_weapon_appearance_20260926.py`.

```
python -X utf8 -B -m tools.strike_lab.current_weapon_appearance_20260926
python -O -X utf8 -B -m tools.strike_lab.current_weapon_appearance_20260926
```

Both PASS **49 cases**: 3 actual native length-return routines; 27 DA routing/prefix cases; 16 complete native remote component setter cases; 3 native local saved-block slices. All mandatory checks use non-optimizable require. Executable SHA is checked; image is read/execute only; exact stop PCs, execution limit, permitted writes, packet guards, actor canaries and return stack checks apply. Synthetic handles/flags/IDs are test inputs, not original server mappings.

The DA dispatch runs original actor lookup and local prefix up to entry of 461270. It does **not** replace 461270 with a stub or claim to execute it in this tool. 4FC130 and both leaf setters run to real return. Local persistence is a separately initialized native slice before 501810. No graphic renderer, full world refresh, socket or hidden client acceptance was performed.

## Wire and state contracts

| Logical offset | Width | DA meaning actually supported |
|---|---:|---|
|0|1|DA|
|1|2|Actor identity, little endian, compared without a 3FFF mask|
|3|2|Alternate/transformed resource key; zero selects ordinary path; nonzero invokes 45C100 eligibility and potentially 45C000/45A0A0 substitution|
|5|1|Copied to local world+1539AED1 or remote actor+264; preserve existing authoritative value, semantic name unproven|
|6|1|Copied to local world+1539AED4 or remote actor+265; preserve existing authoritative value, semantic name unproven|
|7|8|Four packed two-byte HeroDoll components|

Native size table 00401324+4*DA points to00401252 (`mov eax,15; ret`); 36/37 point to0040122E (`mov eax,11; ret`). Length includes opcode, excludes outer transport framing.

DA starts at469369. It increments the pointer past opcode and compares WORD(payload) to world+1539683C. Self calls503D30. Other calls4FC990 on world+15383410; this searches128 records at manager+18+index*268 and missing actor causes immediate ignore. A DA packet does not spawn the missing actor.

### Ordinary self

503D30 stores the three scalar fields, then ordinary branch503F61 passes:

- first selector `(DWORD(world+15396880)>>18)&255`;
- second selector `(DWORD(world+15396880)>>10)&255`;
- payload+6 (logical+7), the complete8-byte block;
- six-WORD output array;

into461270 using resource manager world+AA364B8. 503F94 applies all four handles through4FF450, then variants through4FFA20. Variant is component second byte>>5, unless world+1539AD70 bit10 forces7. 502210 refreshes actor animation state. 503FF4..504013 saves the original8 bytes at world+1539ADC0/+1539ADC4 before calling501810. That function re-enters component selection and renderer state; full tail acceptance remains outside this oracle.

### Ordinary remote

469523 passes remote actor WORD+34 and WORD+40 as the first/second selectors, plus the same8-byte block, to461270. Then4FD830 looks up actor by identity again and calls4FC130. The latter executes actual4FF450 and4FFA20 on actor+224: resource handles at component+4+6*i, variants at+8+6*i. It preserves the low5 bits of actor+251+2*i while copying only the variant high3bits there (unless actor+61 bit10 is set, which forces variant7 and leaves saved bytes unchanged).

**Do not claim DA rewrites all remote saved component bytes.** The traced consumer updates live handles and saved variant bits; it does not copy all8 bytes into remote actor+250. Full4FD830 tail includes4FD160, conditional4FC720 and4FC6A0 renderer/visibility refreshes. They have not been dynamically qualified here. Future world actor creation still needs authoritative server appearance after-state.

### Packed ordinary components

461270 extracts the low nibble of first byte as binary/class key, high nibble as category, and low5bits of second byte as ordinal. The second-byte high3bits are display variants. Component1 additionally derives its ordinal through63C90 and component2. Component3 is weapon-position component by HeroDoll lookup naming (`w`). When the first selector is positive, component3 **forces category8, ordinal0**, so simply changing its incoming ordinal cannot establish mounted weapon appearance. Action comes from63780/Drv, not directly from inventory item key.

## Why 36/37 must remain separate

For36, dispatcher469C6B reads logicalWORD+7, masks identity3FFF, and its top2bits feed local world+1539AED0. Local calls5038A0; remote calls4614A0 then4FBC30. 37 follows the remote composite path. Composite resolver takes four one-byte component indices, with zero producingFFFF and positive input subtracting1 before lookup. Resource branch derives from signed payload byte4; 5038A0 distinguishes negative removal, values below101 and composite101+ paths. Composite-specific handling can strip bit7 from its first two component bytes. This format is incompatible with DA's four packed two-byte HeroDoll components and unmasked identity.

## Owned WPN1/2: confirmed source, missing mapping

The existing current native metadata parser59420 was executed on current source rows, zero-based item_row ordinal0/1 (not1/2):

| Source line | Key | Name | Source tag | Parsed metadata |
|---|---:|---|---|---|
|4804|1|菜刀|Wpn01001|+114=1, +116=0, +118=FFFF, +11A=F4, +11B=02, +11C=05, +11D=03, +11E=0001, +120=02|
|4805|2|砍刀|Wpn01002|+114=2, +116=0, +118=FFFF, +11A=F4, +11B=02, +11C=05, +11D=03, +11E=000A, +120=02|

For WPN type1, original59420 reads numeric source columns26,27,28,29 into+11C,+11D,+11E,+120. It reads source column3 into+114 (icon); **source column2 tag Wpn01001/Wpn01002 is not read into this native metadata record**. Neither +114's coincident value nor source tag is a demonstrated HeroDoll weapon selector. The action field is FFFF for both, not a qualified animation index. Existing current_item_battle_reach proves+120 is read as reach from slot34; it does not provide a weapon-appearance binding.

No read in the traced DA/461270 path consults the24-byte inventory slot or these396-byte metadata records. DA consumes server-supplied appearance and prior actor selectors. A current-source relation linking WPN's source row to the particular HeroDoll category/ordinal remains the exact missing authority. Source names alone do not fill it.

## Minimal after-state integration sequence, with limits

1. Validate world state and owned complete20-byte instance from source slot; regular weapon target is34. Commit authoritative equip/unequip transaction and preserve full metadata/revision. Auto-selection of bag cells remains explicit server policy.
2. Project inventory source/destination with qualified3B/41 semantics. Clearing first and then full3B for an occupied after-state avoids additive3B count behavior; full instance must be preserved. Only actually known slots should be sent. Native pending sound flag behavior remains as documented in current-player-equipment-frontier.
3. **Once a source-backed appearance after-state is available**, send DA to self and already-spawned observers, preserving the other three components and scalar fields. Do not zero mount/accessory selectors, invent transform keys, or send36/37 as substitution. Persist server after-state for later actor entry/relogin.
4. Project stats only when their native calculation and mid-session update conditions are separately qualified. Inventory and DA consumers do not calculate authoritative equipment stats.

Thus steps1–2 support a genuine owned-instance equipment transaction. Step3 has a native wire/consumer route but cannot yet derive WPN1/2's appearance from the available item source. Full after-state rendering, remote refresh tail, mounted behavior, item restrictions and stat formulas are distinct remaining gates. Do not report the whole ordinary weapon feature as accepted from these49 offline cases.
