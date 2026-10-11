# Native armor definitions and transfer frontier — 2026-10-02

## Installed source catalog

Migration41 and all 1,354 EQU/TEQ source definitions are installed in the formal
configured SQLite database. The C++ catalog validates complete provenance,
record bytes and the full-catalog fingerprint. Lua `native_armor_catalog(item)`
provides the same source-only data, including binary fields; reload retains the
lookup callable. No acquisition, equipment bonus or instance grant is implied.

- EQU692; TEQ662. Catalog fingerprint
  `29d1de3729c843571c3a7bc117beb12289bd7110932ec45fc5d846b627282efe`.
- Original Taiwan source70a4/decoded75c3/mapped149c; current custom-skill data
  fileef297 contains the same 1,354 armor raw rows. No retired corpus is used.
- All 1,354 original metadata loaders and 5,416 ordinary equip-guard cases run.
- Source labels map 1,286 physical parts:30=600,31=332,32=178,33=176.
  The remaining68 special items are explicitly unqualified, without guessed
  icon-based placement. All1,055 ordinary category0..7 records map unambiguously.
- The native tooltip exposes six raw instance operands, not the final owner's
  combat attributes.360 native projection cases cover full3B instance consumers,
  2C received stats and DA appearance update consumers. No final formula recovered.

## Release and preservation

Installed candidate SHA256:
`80060831f15e4f27667745848ba9c18fefec441106c935e72f4b64089a6a36ed`.
Managed server PID30952 at post-install verification, loopback2592. Current client
c5d8 and configured server settings remained unchanged.

Release evidence: `artifacts/releases/native-armor-definitions-20261002/deployment-04/`.
`release.json` is INSTALLED and `post-install-verification.json` is accepted.
Migration/import were performed in place after an empty-player stop. All old
schema objects, migration history and saved table rows were compared exactly.
The database was never replaced with an earlier save. The compatible schema41
candidate is retained if a promotion fails; a schema40 executable must not be
used to downgrade a schema41 database.

Deployment01 failed before migration because a staging clone was named stage.db
instead of the diagnostic-required town-diagnostic-accounts.db. That evidence is
retained. Later stages retain their independent backups; deployment04 is the
installed release. These were staging/gate corrections, without client changes.

## Verification scope

Five CTests passed:armor_slots,owned_armor_transfer,recovered_armor_instance,
native_armor_catalog,import_native_armor. The Python importer includes5 cases.
These cover full catalog corruption/partial import, transactions, native vectors,
Lua lookup/reload and prototype owned-instance transfer failures.

`artifacts/playtests/private-native-blackbox-armor-definitions-20261002-01/run-result.json`
is accepted against the exact installed candidate. Actual Migration41 import and
Application startup validate692/662. Original TW950 and CN936 clients completed
10 bank UI mutations each, including occupied65 swaps. All1,354 source rows,
other owners and unrelated rows remained intact. Existing processes and desktop
were preserved; owned test server/runner/clients are terminal and2598 released.

This is source loading and existing-gameplay regression. It is **not** armor
wear/remove, attribute, appearance or acquisition acceptance. No screenshots or
foreground takeover were used. Frozen chat verification passed without refreshing
its baseline. No new armor instances were added to the formal database.

## Active gameplay implementation and next checks

CUSTOM-0066 remains inactive. New SqliteArmorSlotRepository and
OwnedArmorTransferService preserve full20-byte instances, account ownership,
50-cell/3-overlay snapshot CAS, independent physical revisions, pending-battle
checks, native clear41/full3B/absolute41 response and preparation/readback rollback.
Their schema is explicitly installed only in disposable tests, not Migration41.
Source catalog registration does not enable this prototype.

Still required before complete armor gameplay:

1. Owner-bound whole-instance bag projection for trade/bank restore and reject
   paths. Current scalar-only whole-bag projection cannot represent armor.
2. Add the actual28 wear/remove and24 bag-move route with authenticated world,
   scene, transaction and login/relogin restore integration.
3. Recover or explicitly qualify level/class/sex admission. Source text and
   displayed level alone are not an original server rule.
4. Complete item-to-HeroDoll/DA mapping and final equipped stats/HP/MP calculation.
   The existing native consumers only prove how received values are displayed.
5. Real original TW/CN equip/swap/unequip/full-bag refusal/relogin and peer views.
   Do not promote synthetic fixture ownership as native item generation.

Scoped progress:source catalog1,354/1,354=100%; physical source classification
1,286/1,354=94.98%. Armor complete gameplay acceptance remains uncompleted.
Global native packet completion has no validated complete denominator.

## Follow-on worktree only (not installed)

A separate owner-bound `OwnedBagProjectionService` now distinguishes full weapon,
armor and teleport-gem20-byte instances from canonical plain scalar/MED records.
It accepts explicit account/character/current physical revision, not an ambient
session. Planned scalar changes cannot transfer or flatten whole instances.
A full50-cell/3-overlay proof must be verified inside the mutation transaction,
including postwrite verification before COMMIT. Connecting the existing bank and
trade services to that proof is still pending; rendering does not expand their
item eligibility.

Review found the inactive armor repository/projector did not reject an invalid
instance family flag. Worktree validation now checks native family2/26 (low6bits
of byte2), independently from item-ID/part checks. The new repository and reply
checks passed all64family values and4 high-bit combinations (256 vectors).
The installed800608 source-only candidate contains no armor instances or armor
runtime route, so this follow-on repair is not an additional formal deployment.
All26 sources of its accepted release are preserved in deployment04/tested-sources.

New native appearance tracing confirms the original track character table is
`bfhw`: component0 body(B),1 face/hair(F),2 head(H),3 weapon(W). There is no
independent glove/shoe track. Never assign shoe slot33 to component3. Exact
item-to-component generation and completed original-client armor appearance
remain open; this trace alone does not establish that missing mapping.

Follow-on storage tests passed3/3 after repair, including9 executed SQL-trigger
pollution/rollback cases. Evidence is
`artifacts/research/native-armor-20261002/follow-on-storage-01/`.
An initial test failure was an owner-change fixture violating UNIQUE(account_id,slot)
before the intended write. The fixture now uses a valid second-owner destination;
the SQL mutation executes, the new proof rejects it and the outer transaction
rolls back. No guard was relaxed to make that case pass.

Prepared original-client armor test contract:
`artifacts/research/native-armor-transfer-20261002/preparation-02/required-integration.json`.
It schedules TW14/CN14 operations (24 planned mutations,4 full-bag refusals),
using source-qualified level1/unrestricted EQU1201/1001/1501/1601 and
TEQ20201/20001/20501/20601. These are future test fixtures, not live acceptance;
the new Application route/config and full transactional integration must exist
before execution. The prepared instance attributes are CUSTOM_TEST_NOT_NATIVE.

Additional appearance evidence:
`artifacts/research/current-armor-appearance-20261002/native.json` is PASS against
current c5d8.128 full native resolver cases,10 source-field differentials,
32 inventory transport cases and8 icon-map cases executed. The resolver runs
with an exhausted resource pool to follow original refusal of ROM loading;
this verifies source lookup/parser/transport, not loaded ROM pixels or completed
appearance rendering. Original H source byte42 supplies the F face/hair ordinal.
The8-byte component block is received server data; an item-ID/icon-to-H/B
conversion is still not established and must not be manufactured from the icon.

## Later transport qualification (same date)

The prototype-only status above records the earlier source-only release.
The subsequent candidate now connects schema42, authenticated armor28/24,
whole-instance login/relogin restore and owner-bound bank/trade proofs.
See [owned armor transport](native-armor-transfer-20261002.md) for the exact
candidate, TW/CN28/28 UI acceptance, 20 bank mutations plus two armor refusals,
production adapter checks and remaining original-rule/appearance/stat gaps.
Formal activation is proved only by its separate installed release receipt;
this source-only document must not be used as an armor gameplay acceptance gate.
