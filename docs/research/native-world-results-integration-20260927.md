# Native world display and supplied battle result integration

## Implemented contracts

* S2C72 -> 004CC380: exact21 logical bytes, selectors+1, facing+9 high3,
  packedXY+17 (15bits each). `RecoveredNpcRecord` now owns facing edits too.
* S2C71 -> 004CB120/004CB720: exact21 bytes, instance+1 low16, facing+1 high3,
  packedXY+9, area/group+5, one-based ordinal+19 high13. These three identity
  domains remain separate. Opaque bits and resource override are preserved.
* 83/0D -> 0052C520: exact15 bytes, signedWORD+9, selector+13, nonzeroWORD+11.
  Selectors0..5 add HP accumulator,9 adds MP,20 replaces HP accumulator;
  7/8 leave accumulators unchanged. Other branches are explicitly unqualified.
* 00528A70/00528AC0: DWORD wrap then negative-sign floor0 then signed cap
  comparison, without floating point. C++ avoids signed overflow and casts.

Evidence is the current mapped image SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Source docs: current-npc-record-20260919.md,
current-monster-position-writers-20260927.md, current-damage-formula-20260920.md.
Native71 length was independently checked: length jump table1324+71*4 selects
VA40127C, whose bytes `B8 15 00 00 00 C3` return21, including opcode.

## Runtime and persistence

Migration34 adds explicit scene-bound full71/72 records and source provenance.
`SqliteWorldDisplayRepository` retains exact bytes, checks identity/build and
rejects conflicts. Production loaders exclude ISOLATED_TEST_ONLY. Catalogs do
not generate placements. NPC and enemy pool limits and native namespace lookups
are checked before any frame is sent; batches respect the0xA00 queue limit.
Application projects these records after accepted world entry and on scene change.

Existing attack, MP expenditure and revival paths now use native scalar
application. Their existing CUSTOM-0007/0012/0017 damage/eligibility rules remain
custom; application arithmetic does not establish original damage generation.

`Battle::apply_native_deltas` and the authenticated bound
`RecoveredBattleService::apply_native_deltas` admit trusted, already-computed
server results. Existing action and zeroed per-entry accumulators are required;
the standalone accumulator supports nonzero initial states separately. The
service validates bound session/account/character, authorized source, target
presence, revision and phase; all encoding precedes checkpoint persistence and
publication. It reuses existing atomic resource/checkpoint commits, including
restart restoration. It is not a C2S83 registration. No automatic skill producer
or death/animation rules are guessed from these received values.

## Verification and limits

`native_world_results`, `recovered_battle_service`, `battle_transaction`,
`battle_revival`, `recovered_world_service`:5/5 passed.
Native differential:70 actual83/0D receive cases and52 executed scalar cases
matched the compiled C++ implementation exactly, including signed caps/wrap.
Complete native catalog clone verifies distinct instance/catalog/map keys,
71/72 exact-byte scene projection and transport framing; test rows cannot reach
the production loader. An initial fixture used an absent enemy catalog2/4/1;
qualification rejected it. Corrected fixture uses actual source1/0/1. Its map
and coordinates are synthetic supplied operands, never original spawn evidence.

Results: artifacts/research/native-world-results-20260927-03/verification.json.
The private-desktop regression separately covers login, Kunlun world admission
and existing playable state. It does not certify live71 monster rendering or
83/0D animation application; those require qualified scene/action fixtures.

Original NPC/monster placements added:0. Original attack/defense-to-damage
formulas added:0. These missing producer datasets are not hidden by interface
completion percentages. Entire-game playable acceptance has no verified
denominator, so this round does not invent an overall percentage.

Actual current-client regression found and repaired a world-admission gate:
the client renders the world while the session retains CharacterSelected.
Restore now requires recovered_world_ready plus bound movement location, allowing
this established entry phase as well as InWorld. A subsequent hidden-client run
recorded NATIVE_WORLD_DISPLAY_RESTORED area4/scene3 and successful movement.
NPC scene qualification reads/hashes the full4043-row catalog once per batch,
avoiding a full source integrity scan for every placed NPC.

## Installed release

`artifacts/releases/native-world-results-20260927-02/verification.json` confirms
schema34 and running local listener2592 (PID176 at verification). Server SHA256
`955b849984cabe06c48654bd8d8fcccbee020aa60a788609c995d4a7901956af`.
All existing player tables are byte/value-identical to the pre-release snapshot:
4accounts,3characters. Production world_display_records is empty. Client and
config hashes are unchanged. Backup and rollback files are in the release folder.
Final private-client receipt: private-native-results-20260927-04/run-result.json;
input desktop remains Default, and the owned test client/server are closed.

Scoped progress:4/4 requested consumer contracts have C++ integration (100% of
this code scope);5/5 selected regression suites and122/122 executed arithmetic
comparisons pass. This is not100% playable restoration. Complete current-client
acceptance of all four requested paths remains open, particularly monster71
resource/render continuation and83/0D full action/animation phases. Formal
unrecovered skills do not automatically emit this result type.

## Subsequent own-server acceptance and schema35 release

The previous open consumer gates now have actual hidden-desktop client receipts:
`private-native-blackbox-20260927-14` checks NPC72 and monster71 native active
renderers, coordinates, facing and level78, restoring existing persisted rows
on reconnect and retaining them after player movement. Input desktop remained
Default; there were no screenshots, memory writes, injections or desktop swaps.

`private-native-blackbox-20260927-13` checks83/0D through the actual battle
animation/application flow following a real client attack command. Enemy
HP150->120 and owned player MP26->16 match trusted server state and saved MP16,
without subsequent86/88 correction snapshots. A known zero-damage opposing
action closes the isolated animation group. Synthetic magnitudes, resources and
placements remain lab-only; this is not native damage-generation recovery.

The first result experiment exposed logical14 as a target outcome: native
52CB8E/52CBDE ->52BFC0 maps0 to death9 and28 to live0. Leaving this field zero
made the client kill a monster that retained120 HP on the server. The trusted
transaction now permits only these qualified outcomes and rejects a mismatch
with staged HP before encoding/storage/publication. Parser roundtrips still
retain all supplied bytes. Unsupported outcome types remain unqualified.

The new monster level codec/schema and native behavior are documented in
`native-monster-level-integration-20260927.md`. The native NPC capacity is256,
not512; the overflow boundary now has a rejection test.

Installed release `native-world-results-20260927-03`: schema35, server SHA256
`fd9219028aa2ecc598707a33077941b451b02a28a6c5d7be3ef6a3e37edc2106`.
Listener2592 PID26604 at installation. Existing4 accounts/3 characters and all
previous player-table values are preserved; client/config hashes are unchanged.
Formal `world_display_records` and `world_monster_levels` both contain0 rows.
No original locations/levels were manufactured from synthetic operands.

Final native arithmetic differential receipt is
`artifacts/research/native-world-results-20260927-06/verification.json`:
70 accumulator cases,52 scalar cases, exact compiled/native equivalence.
Five scoped consumer acceptance gates (NPC,monster,damage result,HP/MP,level)
are complete. All-map placements, original levels/stats and complete gameplay
remain separate open recovery/integration tasks.
