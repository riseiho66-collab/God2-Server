# Beast panel connection work — 2026-10-06

Status: native static wire recovery and C++ codec added; gameplay route remains
incomplete. No build, client execution, emulator, packet test, acceptance run,
live save mutation or deployment was performed. The earlier static index reported53 world opcodes. Two new opt-in parser
branches9D/9F are now added in source; this is not a whole-game denominator or
completion percentage, and the full index has not been regenerated.

The current mapped source is SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
`tools/reconstruction/beast_panel_contract.py` reads that exact archived image,
disassembles bounded original functions and decodes selected exact asset rows.
It retains bytes, instruction locations and source hashes in
`artifacts/integration/packet-connections-20261006/beast-panel-static-contract.json`.
The artifact is static analysis, not an acceptance oracle or test result.

## Recovered formats

| Direction | Record | Native evidence | Logical layout |
|---|---|---|---|
| C2S | 6C | 497EE0; control7 caller4A055A | opcode, WORD selected key, BYTE selected selector, BYTE1 |
| C2S | 9D | 4D8F50; control8 in4A04D0 | same fields, distinct operation |
| C2S | 6B/lane0 | food control11 in4A0470 ->4972F0 | 6B, BYTE0, BYTE inventory slot, BYTE selected selector |
| S2C | 4C | size17;469D46 ->4A0840 | opcode plus exact16-byte selected snapshot |
| S2C | 4D | size9;469D6C ->4A0970 | opcode plus exact8-byte partial update |
| C2S | 9E | 4D8780 /4D8810 | opcode, contextDWORD, operationBYTE, selectionBYTE |
| C2S | 9F | 4D8610 | opcode plus old open contextDWORD |
| S2C | C5 | size309;469D7E ->4D8490 | opcode plus exact308-byte exploration snapshot |
| S2C | C6 | size7;469D90 ->4A0A90 | opcode, contextDWORD, stateBYTE, unconsumed tailBYTE |

These belong to the PET/beast panel, not COM/E3 combat-pet snapshots. The native
food producer6B is also used with combat-pet lanes1/3; the new beast codec only
models lane0. It does not reclassify or intercept those other lanes.

`src/protocol/RecoveredBeastPanel.h` preserves all snapshot/delta bytes, models
the exact widths and exposes the four fields changed by the native panel delta.
The low3 status bits and low11 meter bits are kept without assigning growth,
time or economy formulas. No codec is presented as an Application handler.

4C copies its body16 into primary+448C. Controls7/8 split primary+448C into a
low WORD and primary+448E BYTE. Thus selection is received state, not an
account identity supplied by the request. 4D always updates the selected panel;
its separate inventory update only applies to a native class5 cell with a
selector1..6. Those checks do not establish server-side ownership.

4C body DWORD+8 carries meter numerator bits0..10, denominator11..21, label
kind22..23, control7 alternate bit27, control8 condition bit28 plus kind2, and
status29..31. Other bits remain opaque. The body6 WORD was previously called lifetime without sufficient evidence.
Native4A0700 actually renders it as a percentage (FLOAT0.01, %6.2f%s and
ProgramMsg362). The underlying gameplay quantity and all tick/expiry rules
remain unrecovered; see the retained V2 analysis and correction below.

The native initializer49FAA0 (RVA9FAA0) loads three kind
labels from ProgramMsg645/646/647 into5B6824. Kind3 has no qualified label.
ProgramMsg96 is loaded separately into5B6820 as the food label. Preserve that
distinction instead of inventing a fourth kind. Selected PET row5301 identifies
赤煙駒, a 座騎神獸 with 糧草類 food text. Text is not a grant, instance snapshot,
growth formula, eligibility proof or authoritative mapping to actor appearance.

## Remaining connection work

1. Recover authoritative owned PET acquisition, selected instance, full raw
   inventory metadata and saved state. Do not reuse COM/E3 storage for it.
2. Trace controls7/8 for every kind into actual operation/state transitions;
   connect request processing, C++ state/SQLite, Lua rules and native replies.
   Shared UI membership does not prove a specific request/response pair.
3. Recover native food qualification and resulting consumption/growth/lifetime
   state before committing6B/lane0. Preserve instance and inventory revisions.
4. Connect the recovered exploration snapshot/action/close state with actual
   server exploration, timer and reward custody. C6 state4 closes before copying
   its new context; native9F can therefore contain the OLD open context. Changing
   the selected beast in4C can also trigger9F for the old exploration panel.
5. Recover PET-to-Drv/actor appearance authority and self/observer refresh. DA's
   renderer contract does not make a historical mounted appearance owned state.
6. Keep all these paths open until actual Application/state/storage/reply wiring
   exists. Full client testing stays in phase2 after every game route connects.

The mapped image is read selectively from the finalized compact archive; no
historical client/build tree was restored. Existing schemas51..53 work, frozen
features, current service, account saves and client binaries remain unaffected.

## Expanded source and custody backend

The original v1 analysis misattributed4A0A90 toC5. The actual table assignsC5 to
4D8490 andC6 to4A0A90. V2 records those dispatch bytes and both length leaves;
`beast-panel-static-contract-v1-prior-analysis.json` retains the old analysis.
The prior annotation is not a native acceptance result and must not be reused
as a handler binding. The original mapped source and old acceptance evidence
were not changed.

`RecoveredBeastExploration.h` now preserves the entire C5 body: contextDWORD,
stateBYTE, template-countBYTE, fifty WORD message keys, fifty WORD item arguments,
selected indexBYTE, option-countBYTE and two fifty-BYTE argument arrays. Native
4D8B70 clamps template count50. Option count is independent because formatting
can produce multiple display lines. Do not impose template-count semantics on
the selected option or treat any raw byte as a trusted reward quantity.

4D8810 emits9E operation0 from state0 or operation1 from state2, with a one-based
selected index. 4D8780 emits operation2 with a zero-based index, orFF when none
is selected. Their gameplay verbs and backend effect policies remain open.
Close9F preserves the full four-byte context, not only the item key/selector.

`NativeBeastSourceCatalog.h` and `beast-pet-source-catalog.json` retain all147
original PET keys, resource keys, row hashes and source locations. Original
gamedata raw70a4... and decoded75c3... are read from the pinned capture through
the finalized archive. Current installed gamedata rawef297a84... /
decoded544f0a4d... differs as a complete file; all147 ordered PET row bytes match
the original. This is section-specific source qualification, not a silently
refreshed whole-file baseline, native parsed396-byte object or client acceptance.
No current asset was overwritten.

CUSTOM-0085 adds `SqliteBeastSnapshotRepository` and the managed
`SqliteDatabase::beast_snapshots()` accessor. Its explicit schema preserves raw
inventory20, panel4C and optional explorationC5 snapshots, bag/custody revisions,
origin and evidence. Trusted custody import requires an existing owner-matched
count1 PET bag row with the exact expected revision/source; it cannot create a
bag slot or grant an item. Updates compare the entire previous custody row,
retain all opaque bytes and reject an unsettled battle. Source membership never
upgrades an instance's origin. Missing schema throws instead of implying empty
ownership or running DDL-on-read.

The custody DDL now has an explicit additive feature registration and Application
panel presentation path described below. Installation code has not been executed.
Acquisition, complete selected-beast authority and action/economy paths remain open.
No player instance was created and no build/test/client run was performed.


## Application panel presentation connection

`OwnedBeastPanelService` and Application now handle native25 requests for original
PET declaration keys in native52/53/54 same-slot and53/55 shortcut25 groups.
Initial scope matched963C0; the9AA07 expansion is documented below.
The complete original frame is checked before prefix callbacks: one25, any Tick
records and an optional final1F. Mixed writes or multiple uses are rejected.
The existing MED/map/gem handlers retain their routes; only source-qualified PET
keys enter this optional branch. `world.owned_beast_panel.enabled` defaults false;
no formal configuration was changed.

The route requires authenticated ownership, WORLD readiness, already projected
owned beast metadata, current bound scene, no transition/trade and no unsettled battle.
The repository reads the exact existing slot and custody snapshot in one
standalone selection transaction. Key/count1/source/bag revision/metadata20 and instance provenance
remain bound. It prepares native4B(selector,0) then unchanged saved4C before committing the
custom persistent selection described below. The independent
native producers/consumers are recovered; the25->4B/4C relationship is a CUSTOM-0085
presentation policy, not an observed original server exchange. Native4B BYTE2 is
unconsumed by9FB40; custom policy uses0. Current-client display acceptance remains
pending phase2. No food, ride, exploration, inventory consumption or appearance
mutation is inferred. Persistent selection is now connected as described below; no activity permission
lease is established.

Explicit startup registration uses `SqliteDatabase::install_beast_snapshot_schema`
only when that feature is configured. It installs custody and the immutable
`beast_custody_schema_0085` version1 ledger atomically, with exact DDL/index/trigger
qualification on access; partial/altered prior objects are not silently adopted.
This preserves base `schema_migrations`1..53 and strict guild version validators.
Existing guild whole-save preservation guards include these new tables. The code
has not been run, the schema is not installed and the running database remains
untouched. Final release backup/recovery composition must include these additive
objects. Bag relocation, bank/trade/discard, deletion, acquisition and reconnect
still need full custody lifecycle integration; stale bag revisions deny access
rather than relocating opaque instance bytes implicitly.


## Persistent selection, bag projection and reconnect

CUSTOM-0085 now retains `character_beast_selection_0085`: character, stable BYTE
selector, exact custody revision and positive independent selection revision.
Selection origin remains CUSTOM_DESIGNED even when the instance has native
provenance. `beast_selection_schema_0085` has its own immutable version1/SQL text
ledger; the original custody version1 SQL and base1..53 history are unchanged.
The explicit installer composes both additive features atomically. No installer,
SQL migration, build or test has been executed.

Explicit25 prepares the4B/4C wire bytes before writing selection, checks ownership,
full existing custody/scalar and pending battle, then uses revision CAS and checks
the exact resulting selected instance before COMMIT. Repeated selection of the
same selector/custody revision is idempotent. Replacing trusted custody does not
silently reauthorize a selected instance: the old record is retained, and a read
returns no current selection until another explicit25. No ride, food, exploration
or actor-appearance authority follows from this custom selection record.

First owned WORLD restoration now sends each exact existing beast inventory20
through native41-clear/3B-full/41-absolute-count1 and restores valid selected4C.
It does not open4B orC5 unsolicited. This source path is independent of MED-only
projection and maintains its own per-session readiness, cleared at disconnect.
Read-only restore does not block durable unfinished battle recovery; new25
selection mutations still require no unsettled battle. Native-client acceptance
of this reconnect order remains phase2 work.

The shared `OwnedBagProjectionService` has an explicit optional same-connection
beast port. With that feature enabled, native PET declarations are full-instance
categories. Exact custody bytes are projected rather than the canonical plain
zero-tail encoder. Other weapon/armor/gem overlays conflict. Existing plain
mutation proofs now capture and preserve all beast custody plus the raw selection
record (including stale records) before and after writes. Dedicated ordinary-bag relocation is now connected below. Trade/bank/discard
still require their own full instance custody plans. With the feature disabled, existing category/projection policies
remain unchanged. No instance was created, installed client changed or live save
mutated. The full-game goal and remaining operation routes stay open.


## Native24 whole ordinary-bag relocation

`OwnedBeastBagService` and `SqliteBeastBagRepository` connect existing native24
source/destination BYTE records to whole ordinary-bag instance swaps. CUSTOM-0085
policy swaps entire occupied cells/stacks; it does not recover original merge,
equipment or drop rules. At least one affected cell must have separately acquired
owned PET custody. Both slots must have existing capacity rows; missing rows are
not free capacity. Native24 carries no nonce, so snapshot CAS is not a claim of
original replay prevention.

Application identifies PET involvement and captures the whole original frame
before guild/bank/trade prefixes: one24, ticks and optional final1F. It captures
owner, WORLD readiness, beast projection readiness and the complete current bound
position (area/scene/x/y/revision). Before commit it requires the same position and
owner plus no trade/scene transition or durable active battle. This branch runs
before existing armor/weapon swap handlers; unrelated routes retain their existing
handlers. The same opt-in feature creates the shared full bag projector even when
armor transfers are disabled. No formal configuration was changed.

The managed writer shares the exact SQLite connection with beast, armor and
projection ports. Its immutable snapshot includes all50 scalar cells, weapon,
armor and gem overlays, all character PET custody, raw valid/stale selection and
all typed unrelated saved rows/schema. Known affected columns are qualified;
unsupported opaque columns reject rather than being deleted by serialization.
The typed whole-save guard is reused from the new source relations53 helper and
excludes only the two intended cells and the one selection row. All protected
30..49 rows, other characters, banks, combat, guild and opaque data remain in it.

Qualified weapon/armor/gem neighbours retain full20 bytes and provenance. Plain
neighbours must already pass the existing canonical projector. Both physical
slot revisions advance; each moved PET custody revision advances while inventory20,
panel4C, optionalC5, origin/evidence and selector stay with that same instance.
A valid selected custody binding advances to its new revision with the same
selector. A stale binding is preserved and stays stale. The inactive empty weapon
overlay follows the existing retirement policy. Same-slot or empty-source requests
project current authoritative cells without writes. Complete41/3B/41 wire records
are prepared before any write. Readback must equal the entire planned result and
the typed unrelated rows/schema before COMMIT.

The selected row references a stable selector, so moving two PETs requires a
short parent delete/reinsert within one standalone transaction. Foreign keys must
already be ON and deferral OFF; the writer uses defer_foreign_keys=ON in that
transaction and checks final foreign keys before commit. SQLite documents that
this delays enforcement until the outermost commit and resets on commit/rollback;
no code switches it OFF inside an unresolved transaction. Source reference:
[SQLite defer_foreign_keys](https://www.sqlite.org/pragma.html#pragma_defer_foreign_keys).
This is database API design evidence, not a client test or native gameplay rule.
No new DDL, database mutation, build, test, client execution or deployment occurred.
Bank/trade/discard, acquisition, activity effects and actor appearance remain open.


## Exploration presentation and local close connections

Source parsing/Session wiring now admits9D and9F only with `beast_views`, set by
the existing default-false `world.owned_beast_panel.enabled` source option.6B,
6C and9E activity records remain outside this new admission. No parser branch
or source-row count is counted as completed gameplay. Default-disabled formal
services/config/client remain unchanged.

`OwnedBeastExplorationService` supplies actual owner-bound view state. CUSTOM-0085
9D->C5 pairing is a presentation policy, not an observed original-server reply.
It requires native kind2, control8 non-alternate state, exact current persisted
selected key/selector/custody/selection revision and an already acquired fullC5
snapshot with state0..3. No empty/defaultC5 or option/reward bytes are manufactured.
Whole original-frame preflight accepts one open/close, ticks and optional final1F;
selection and complete bound position are captured before any prefix and compared
before display. Existing guild/modal permission retirement remains before final
beast dispatch. Durable active battle, trade and scene transition deny opening.

The service encodes unchanged C5 first, then records session/account/character,
position, full selected snapshot and all four context bytes. Native9F clears only
that exact owned open context. It can clean up the OLD context after25 changed
selection, as the original4C/C6/local-close consumers require; a mismatching late
close cannot remove a different current view. Disconnect removes view state.
There is no fabricated close ACK and no new activity cancellation/reward claim.
The original protocol has no modal nonce, so a close for the same exact context
is not promoted into replay-resistant activity authority. Actual9E rules and
all non-exploration/alternate9D effects still require recovery and integration.

## Correction: body6 WORD is percent display, not a qualified lifetime

New bounded disassembly and source rows are retained in
`beast-display-controls-static.json`, generated by `beast_display_controls.py`.
Mapped149c... is unchanged. Original captured message.csvZ compressed SHA256
5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598 and decoded
370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8 supply
ProgramMsg362 exact percent-sign row (line2388, row9978d3f8...). NativeA0700
extracts primary+4490 highWORD (4C body6), uses FILD and FLOAT atRVA171204 bytes
0ad7233c (0.009999999776482582), then formatRVA190C68 `%6.2f%s` with that suffix.
This is display arithmetic only. It does not establish fatigue, loyalty, lifespan
units, server tick frequency, expiry, food increments or rounding of game rules.

The misleading new-source getter `lifetime_display_raw` is renamed to
`percentage_word_raw` in both snapshot and delta. All wire/raw stored bytes are
unchanged. V2 analysis is preserved in
`beast-panel-static-contract-v2-prior-analysis.json`; current V3 corrects the
annotation. Original mapped/source identities, prior acceptance evidence and
frozen baselines were not changed. No build/test/emulator/client execution occurred.

## PET25 reachability and4D inventory metadata

`OwnedBeastPanelService` now admits source-qualified PET52/54 as well as the
existing53/55 shortcut qualification. Original9A330 same-slot release with event
mask20, metadata flag4 and quotient52/53/54 goes through9AD06 panel gating to
9AA07->96350. These are the native transport/mount/exploration categories;
native source membership is still independently required. SPI55xx and packed
type35 are not automatically beasts. This joins transport and exploration PETs
to the existing owned25 selection/storage/4B4C presentation route; it does not
recover their activity effects. Whole-frame/owner/state admission and default-false
activation remain as implemented. The current custody domain is still0..29.

The original4D receiver has two independent effects. Selected-panel projection
retains the existing implementation. A0A11..A0A8C then indexes the inventory slot
from delta body0 with24-byte stride. Only class5 metadata and body2 in1..6 enter
the writes. **Correction from later native tooltip/base recovery:** in the20-byte
metadata domain, WORD+10 low3 becomes body2 (upper13 preserved), BYTE+9 becomes
the complete body3, and WORD+12 becomes body6. The initial6/5/8 annotation
subtracted the record's4-byte prefix twice and is retained in V1 prior analysis.
Key/type and every other metadata byte remain untouched. Inventory stores the
full BYTE9 (classic level), whereas the selected panel retains only its low3 bits.
`RecoveredBeastPanel::apply_inventory_delta` now models these exact guards and
writes. It is a pure projection helper; no network request may use it as food
authority. Native tooltip now labels body2's inventory value as palette; the
panel selector BYTE is a separate instance-selection namespace.

Bounded disassembly and original PFD source rows are saved in
`beast-inventory-controls-static.json` by `beast_inventory_controls.py`.
Original PFD has65 rows at decoded section line9297/offset774568. The descriptions
separate fatigue reduction (6901..6905 text15), loyalty increase (6906..6910 text10)
and experience increase (6911..6915 text1), with further tiers/special items.
Those descriptions do not establish which4C/4D fields carry the quantities,
their units/caps, matching food class, consumption or server formula. MED01's
second-generation mount3026 onward and MED02 HP/MP supply are separate scopes.

The37 equipment consumer also has a concrete limit:3B at98EF8 closes the old
beast UI through9FBD0 when the key changes.41 at992A9 closes it when the changed
slot equals85ABD.9FBD0 invokesD8610 exploration close andA01A0 local cleanup;
it does not reopen the panel or produce4C. Consequently a full37 equip route
needs its own authoritative state/storage plan and explicit UI/activity recovery.
Immutable custody schema v1 was preserved;37 is not silently added to its domain.
No build, test, emulator, client run, DDL installation or live save mutation occurred.

## Source28 equipment37 connection and additive featurev2

`OwnedBeastEquipmentService` now connects source-qualified native28 requests
from an already owned ordinary bag PET or37 PET to a Lua placement policy and
the full-instance transactional writer. The packet has no destination; under
CUSTOM-0085 `beast_equipment.lua` selects native37 for a bag source and the
lowest explicitly owned empty bag cell for a37 source. A missing scalar row is
not capacity. No food, item grant, riding, teleport, exploration, combat stat,
decay or appearance formula is supplied by that placement rule. Both occupied
cells must have exact PET custody/count1; other classes cannot be swapped into37.

Application captures the entire original frame before prefixes: exactly one28,
ticks and optional final1F. It requires authenticated owner, ready WORLD,
projected beast inventory, full bound position, no trade/scene transition and no
durable active battle. Lua receives source slot and a copy of owned empty slots.
Its destination is checked against that supplied domain; no script reference to
live state is exposed. The captured full50-slot/overlay/PET/selection snapshot
must still match before the standalone writer commits. Late dispatch is ahead
of existing armor/weapon handlers and repeats owner/position/state qualification.
All other frozen/default-disabled routes retain their existing behavior.

`SqliteBeastBagRepository::Domain::BeastEquipment` allows exactly bag/37,
distinct from the original ordinary-only native24 domain. Full inventory20,
panel4C, nullableC5, source/origin/evidence and stable custom selector follow
each instance; physical and custody revisions advance, and a valid selection
binding advances while stale selection remains stale. Typed unrelated rows and
schema are compared before commit. All30..36 and38..49 cells, unrelated owners,
economy, combat and guild rows remain in the preservation guard. The complete
41-clear/3B-metadata20/41-count response is allocated before any write. A dedicated
`RecoveredBeastInventoryProjection` qualifies37 separately; generic ordinary-bag
projection limits are unchanged. Source restore now includes owned37 metadata
plus any valid selected4C, without unsolicited4B/C5. Equipment replies close the
old native UI; the Application also retires its custom exploration presentation.
This grants no new activity lease or original equip/riding semantics.

The original custody `schema()` and custodyv1/selectionv1 ledger records are
retained exactly. `equipment_schema()` adds only37 to the custody slot CHECK;
`beast_equipment_schema_0085` records that complete DDL as version2. The explicit
installer qualifies the old/new known objects, requires foreign keys and an
unborrowed standalone transaction, takes a typed whole-save snapshot, copies
all custody to a temporary table, recreates the parent under its original name
and restores every original value. It uses transaction-local FK deferral; it
does not rename the old parent, disable foreign keys, alter base1..53 ledgers or
allocate slots/instances. It compares custody/selection and every unrelated typed
row/schema after migration and checks final FKs before commit. Unsupported cascade
or other side effects cause rollback. Partial/altered feature objects reject.
Equipment access explicitly requires installed v2; old valid v1 reads remain
qualified as the old domain. No installer or migration has been executed.

SQLite documents that dropping a parent can invoke FK actions and that deferred
violations must be resolved before commit. That is why the typed preservation
guard covers every unrelated row and selection, rather than trusting a row count.
Parent renaming can rewrite child references. These references inform this
explicit fixed-schema migration design, not a completed migration test:
[SQLite foreign-key DDL behavior](https://www.sqlite.org/foreignkeys.html#fk_schemacommands),
[SQLite table reconstruction](https://www.sqlite.org/lang_altertable.html#making_other_kinds_of_table_schema_changes).

Feature activation stays false. Full PET equipment gameplay still needs original
or labeled custom activity/stat/appearance effects, food field/rule binding,
acquisition, other transfer domains and eventual phase2 native client acceptance.

## Correct inventory base and conditional native tooltip fields

Further static recovery follows selected tooltip A06A0 through9B7F0 to4B5BE0.
The third class switch uses byte mapBC1D0[class5-1]=4 and pointerBC188[4] to
B90E7. This is the actual class5/PET field branch. Bounded original instructions,
pointer bytes, exact formats and original ProgramMsg rows are retained in
`beast-inventory-fields-static.json`; no client/emulator was executed.

The 24-byte native inventory record begins at UI8560C and metadata20 begins at
UI85610. A0970's guard reads metadata0 at85610. Writes at8561A,85618 and8561C
therefore target metadata WORD10, WORD8 highBYTE (BYTE9), and WORD12. The earlier
6/5/8 calculation subtracted the prefix twice. Source projection is now corrected
and prior wrong analysis is kept in `beast-inventory-controls-static-v1-prior-analysis.json`.
This source helper has not been activated/deployed or used to mutate live saves.

Native definition59420 dispatches class5 via59984[4]=1 and59960[1] to5970D.
It reads zero-based source column27 through51B50/51B60/51BA0's decimal getter,
then stores AL at definition+11C. The original147 PET rows have143 zero bytes
and four nonzero bytes:5232=1,5350=1,5351=168,5380=72. All original row hashes
and the whole-resource pins remain unchanged. These values select a tooltip
branch; their numeric values/names do not establish server duration or expiry.

| Metadata20 field | Native use and qualification |
| --- | --- |
| WORD4 low14 | ProgramMsg528 fatigue limit; high2 selects modes0/4000/8000/C000 |
| BYTE8 | Withmode8000 and value1, adds ProgramMsg417 exploring label |
| BYTE9 | Definition11C zero: ProgramMsg84 level;4D body3 writes fullBYTE |
| WORD10 low3 | ProgramMsg86 palette;4D body2 guard1..6 replaces only low3 |
| WORD12 | Definition11C zero: ProgramMsg58 EXP percent, FILD times native FLOAT0.01 |
| WORD14 | Classic modes4000/8000: elapsed minutes rendered as hours plus remainder60; other classic modes: use count |
| WORD16 | Classic modes4000/8000 only: bit15 enables ProgramMsg735 transfer-use count, low15 supplies value |
| WORD8/12/14 | Definition11C nonzero: packed-date branch; not the classic EXP/use interpretation |

At B9267 nonzero definition11C takes the date branch. The raw DWORD is
`((((uint32(WORD8) & 0xFF00) << 8) | WORD12) << 14) | WORD14`, with native
DWORD truncation, then passed toB3E80 and native date formatting. Its calendar,
timezone, timer and authoritative expiry behavior are still open. Zero instead
takesB9342. In that classic branch WORD12 is scaled by float bytes0AD7233C
(native value about0.01) and rendered with ProgramMsg58/362. Display scaling
does not supply EXP gain, threshold, cap, level transition or consumption rules.
No field equality is imposed between stored4C and inventory snapshots: existing
opaque bytes and both legitimate display branches must be retained.

`NativeBeastSourceCatalog` now includes the original lowBYTE definition flag.
`RecoveredBeastInventoryFields` exposes optional branch-qualified values;
date-backed records return no classic level, EXP or use/minute values.
`StoredBeastSnapshot::inventory_fields()` connects this interpretation to actual
custody admission without altering ledgers, feature schemas or data. Corrected
4D projection preserves metadata8 lowBYTE, WORD10 upper13 and all other bytes.
Panel body2 selector and inventory palette are separate namespaces. Selected
panel top3 bits share4D body3 but still only hold its low3; no new panel action
authority follows from that copy.

Food6B remains an incomplete gameplay route. PFD source descriptions support
separate fatigue/loyalty/EXP food categories, but the current panel numerator,
percentage BYTE, eligibility, consumption, cap/threshold and atomic state/reply
rules still require native evidence or an explicit qualified custom policy.
The original tag-pointer table independently binds PET selector5 and PFD
selector9; PFD is not a COM/NCP or MED02 declaration family. Further static
inspection of9FF1C..9FF59 finds exactly three22-byte embedded label records at
1711C0/1711D6/1711EC (name,000,empty), not a fourth record at171202, which
overlaps the float constant. Those labels do not qualify loyalty/fatigue gauge
semantics. Local display/producer code contains no original server consumption
formula. Do not replace those unresolved fields with plausible percentage names.
No tests, builds, acceptance runs, DDL installation, deployment or live save
mutations were performed. All file digests describe continuation source only.

## Native27 ordinary PET discard source connection

Original97720 queues C2S27 `itemWORD,slotBYTE,quantityBYTE` as five logical bytes;
the packet has no owner, generation or nonce. `OwnedBeastDiscardService` now
connects this existing world parser variant to the actual managed bag/PET writer.
The request must be exactly one27 plus ticks and optional final1F. The Application
identifies PET by both the requested key and the actual owned scalar before any
gameplay prefix runs, so lying about the client key cannot send a PET through
another category's handler. Existing scalar/armor/weapon/gem discard behavior
is untouched. Live activation remains false.

CUSTOM-0085 `beast_discard.lua` allows one already owned ordinary-bag count1 PET
with no source-qualified native exploring label and no alternate-control7/8
presentation flags. These are explicit custom eligibility restrictions, not
original bind/drop/riding or activity-rule recovery. Equipment37 and other
activity domains stay open. No level/EXP/time/food field or player balance is
changed by the rule. C++ independently enforces its domain before destruction.

Preflight stores the full50-slot/overlays/all-PET/raw-selection/typed peripheral
snapshot and full bound position before prefixes. Ready, authenticated idle
WORLD, projected beasts, no trade/transition or durable pending battle, and any
existing town-slot0 guard are required. Late dispatch repeats the same owner,
position and state. Copied Lua inputs contain no live database/session references.
Bank leases and the ephemeral beast view retire before the standalone transaction.

`SqliteBeastBagRepository::discard` requires an installed independent journal3
feature and exact known custody/selection schema. BEGIN IMMEDIATE repeats full
capture CAS and the durable battle guard. A fresh server receipt key must be
absent. The complete response and removed-state JSON are allocated before writes.
A matching selected binding is removed by exact selector/custody-revision/selection-
revision CAS whether valid or stale; a binding to another beast survives. Full
custody deletes by all byte blobs, nullableC5, revision, source and provenance;
the exact owned count1 scalar is cleared with advanced revision. Other overlays,
all surviving beasts and all unrelated owners/protected slots remain unchanged.

The additive `beast_discard_schema_0085` ledger version3 stores its exact DDL.
`character_beast_discard_receipts_0085` retains owner, request, before/after bag
revision and full removed metadata20/panel4C/nullableC5/origin/evidence/source/
client/instance-revision and retired raw selection in canonical JSON. Owner IDs
have no cascading FK: this server-only journal must survive later character
deletion and never supplies acquisition, capacity or restoration authority.
Installation is explicit, preserves all original typed rows/schema and immutable
custody1/selection1/equipment2/base1..53 ledgers, and creates no item or receipt.
Altered/partial feature objects reject. No installer or SQL mutation has run.

Response pairing is explicitly CUSTOM: `4B physicalSourceBYTE 00` followed by
native41 clear of that same physical slot. The4B receiver9FB40 rebinds85ABD;41
at992A9 then closes matching beast UI through9FBD0, which closes the main window,
sends9F with the old exploration context when visible, and cleans the auxiliary
view. This intentionally retires the current presentation, even when another
persisted logical selection survives; it does not rewrite that selection.
It avoids assuming that the custom stable selector equals a relocated physical
slot. These exact producer/consumer instructions and length leaves are retained
in `beast-discard-static-contract.json`; the original server pairing is not known.
No new ground entity/pickup or activity-cancellation protocol is invented.

Before COMMIT, exact journal readback, full resulting scalar/overlay/PET/raw
selection state, typed unrelated rows/schema/history and FK integrity must match.
The returned result moves without allocation failure. After COMMIT, logging is
outside the rejection boundary and cannot discard the allocated success reply.
For policy refusal or rolled-back writer failure in the same eligible WORLD,
the route rereads and projects the current qualified source cell with complete
metadata; it never echoes stale captured/client state. WORLD reconnect uses the
existing owned restore path and therefore emits surviving instances and any valid
selection; a journaled removed instance has no custody and cannot reappear.

This is source integration of an admitted whole-instance destruction route.
Original bind/drop restrictions, equipped37/activity behavior, world-ground drops,
bank/trade PET transfer, acquisition, food, riding and appearance remain open.
No per-feature test, build, emulator/client execution, feature installation,
activation, deployment or live account/save mutation was performed.

## 2026-10-06 後續修正：C2S6B欄位順序

上方V1表格`6B,0,slot,selector`與原始`972F0`／`8FAF0`的參數
反向拷貝矛盾。最新有界靜態證據與來源codec修正為
`6B,slot,selector,lane`；獸類面板control11對應lane0。
原V1靜態artifact保持原樣，新增
`companion-control6b-static-v2.json`保存兩個producer、已見lane0..4
callers與獨立S2C6B consumer。參見
`docs/research/current-companion-control6b-20261006.md`。
該parser預設關閉；沒有將6B食物、消耗或回覆算成功能串連。
