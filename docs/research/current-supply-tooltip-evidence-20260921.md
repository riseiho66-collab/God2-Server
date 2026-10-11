# Current native supply declarations

Fresh extraction uses current client Data2/Patch/Comm/gamedata.csvZ through
recover_items.build_items, pinned compressed SHA256
70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731.
No retired archive is read. New output artifacts/world-atlas/supply-tooltips.json
preserves source hashes, row line/hash, original column8 bytes and use flags.

Of100 MED02 rows,71 have exact positive numeric HP/MP restoration declarations;
29 remain unmatched, not assumed effectless. This is NATIVE_CLIENT_TEXT,
not proof of executable server effect or runtime authorization.

Examples: item3107 (source line6360) declares MP50;3108 MP100;3109 MP200;
3110 MP300;3111 MP500;3112 MP1000. Item3101 declares HP100;3113 HP500/MP150.
Therefore numeric supply amounts need not be guessed for these items. Remaining
semantics include actual cap/overflow policy, target restrictions, stack limit,
consumption transaction, cooldown, purchase price and authoritative acquisition.
The isolated SQLite/C2S26 connection for these 71 declarations is documented in
`native-med02-recovery-sqlite-20260926.md`; it does not qualify the remaining
semantics as native.
Columns5/6 are NOT promoted as price/level from appearance alone.

Current C2S25 item/slot/tail and S2C41 occupancy codecs exist, but the inventory
repository remains an empty interface and world policy does not authorize item
requests. No inventory grant or HP/MP mutation is enabled by this extraction.
Next implement owned inventory plus atomic consumption/resource change, then
qualify original client item use/slot update/resource refresh. Keep any missing
gameplay policy explicitly custom and isolated until balance/live acceptance.

Reproduce with python -B -m tools.strike_lab.recover_supply_tooltips
--client-root C:/Users/risei/Desktop/God2/God2
--output artifacts/world-atlas/supply-tooltips.json.
Tests verify exact forms, reject percentages/negative/zero/overflow/trailing text,
fresh source equality and every saved raw tooltip. No live supply test yet.
