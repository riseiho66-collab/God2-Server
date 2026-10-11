# Current-client item definitions

Run from the server root:

```powershell
python -m tools.strike_lab.recover_items --client-root C:\Users\risei\Desktop\God2\God2 --output artifacts/world-atlas/items.json
python -m unittest discover -s tests/research -p test_recover_items.py -v
```

Authority: current `Data2/Patch/Comm/gamedata.csvZ`, SHA-256
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
The source's RowDesc at decoded line 3 supplies the exact 25 column labels.
The importer requires those labels before applying its projection. ItemType
supplies category tags and declared ranges; exact tagged sections supply rows.
CP950 is only a display projection; original field bytes, line locators, row
hashes, compressed and decoded source hashes remain authoritative.

Result: 16,127 definitions, 46 type declarations, 45 populated sections;
reserved XXX has no section. 7,819 rows have equippable=1, 3,010 stackable=1,
and 1,667 have nonzero client visual-effect IDs. 178 rows fall outside their
declared type range, including MAP; these are preserved without correction.
GOD/MAP have short layouts. Their unexplained tails are not assigned the
semantics of full item rows. WPN has 630 rows; EQU has 692.

Every exported row is tested byte-for-byte against the source (excluding line
terminators); two imports and the saved artifact must serialize identically.
This verifies static extraction, not original loader execution or gameplay.
Synthetic malformed inputs exist only in parser tests, never in the artifact.

Both legacy roots were searched before implementation:

- Classic `tools/God2.GameplayContentRecovery/OfficialItemCatalogWriter.cs`
  and `OfficialItemUsageFlagCatalogWriter.cs` corroborate columns 0..4 and
  14..24. Their newer-client counts are not used. The latter's WriteAsync is
  a concrete static catalog consumer to compare when integrating these flags.
- Classic `database/schema/128_publish_verified_equipment_requirements.sql`
  uses a different source hash and explicitly notes older clients differ in
  field 28. No rebirth/level formula is transferred. Migrations 136/137 locate
  restriction evidence in field 7; this importer retains that description
  and leaves executable restrictions unresolved.
- XJZ `evidence-gamedata-item-type-v0.md`,
  `evidence-item-category-split-v0.md`, and `evidence-item-effect-rule-v0.md`
  expose cross-version type overlap and candidate effect routes. They do not
  establish current-client server effects. The concrete next effect hook is
  `cpp/xjz_item_effect_contracts.hpp`, to reconcile each rule with current
  source evidence before creating a Lua handler.

Next executable integration hook: `build_items(client_root)` returns a stable
catalog keyed by `section:client_item_id` for an owner-written C++ catalog loader.
`client_visual_effect_id` comes only from RowDesc column 13 (visual graphic code),
not an executable effect ID. No ROM lookup or server handler join is claimed.
Fields 25 onward, authoritative server IDs, prices/stats, stack limits, equip
slots/restrictions and effects remain unresolved. Nothing is wired into C++,
Lua, inventory packets, persistence or client visibility in this slice.
