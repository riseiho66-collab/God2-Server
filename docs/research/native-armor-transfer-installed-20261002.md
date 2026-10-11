# Installed owned armor transport — 2026-10-02

This is the later formal installation record for
[owned armor transport](native-armor-transfer-20261002.md). The earlier report's
candidate-only statement describes its creation time; the release below is now
installed.

## Actual formal state

- Managed server PID at verification: 5580, listening on port2592.
- Executable SHA256:
  `2696f4efc90648aac47df97e5dbbe80cfd1434cac936f2db36c5ec98ff6ad3d3`.
- Schema42 adds one empty armor metadata table and six collision guards.
- The only config delta is `world.owned_armor_transfers.enabled=true`.
- All old schema objects, migration history, table rows and database pragmas
  are preserved. Five existing recovered characters and 1,354 native armor
  definitions remain. New armor metadata rows/grants: **zero**.
- The current original client and frozen chat baseline remain unchanged.
- Actual process argv selects the formal config; newly appended formal
  Application log bytes prove source692/662 and the owned transport enable marker.

Authoritative release directory:
`artifacts/releases/native-armor-transfer-20261002/deployment/`.
It contains `release.json` (INSTALLED), `post-install-verification.json`
(accepted), `formal-startup-proof.json`, before/stage/installed database
snapshots, fresh backups, exact candidate/config copies and 77 archived runtime,
test, tool, evidence and documentation files. The 20 compiled runtime source
pins are distinguished from supporting archive pins. The live database was
migrated in place; no backup was copied over player data and no schema41 binary
was used against schema42. The apply process exited0.

## Accepted scope

| Verification | Result | Scope |
| --- | ---: | --- |
| Current-client TW/CN armor operations | 28/28 | 24 full-instance mutations and four full-bag refusals |
| Current-client TW/CN relogins | 2/2 | Each restores all34 observed bag/equipment cells without saved revision changes |
| Current-client bank operations with equipment present | 22/22 | 20 MED mutations plus two actual armor deposit refusals; full armor/weapon/gem instances retained |
| Related CTest suites | 16/16 | Bank/trade/weapon/armor/database/config/startup |
| True production database adapter | 1/1 | Full catalog, namespace mismatch, transactional corruption rollback and success control |
| Release gate tests | 13/13 | Receipt corruption, schema/save/config boundaries and formal process/startup checks |

The planned armor transport acceptance is100%; source definitions100%; source
physical-part classification94.98%. These do not measure full armor gameplay or
whole-game packet completion. Original role admission, final equipped stats,
appearance/peer pixels, acquisition/enhancement and68 ambiguous special parts
remain OPEN. Live two-player trade with equipment present was not covered by
the bank run; its paired-owner integrity has repository/service tests.

The accepted transport, original bank/MED eligibility and frozen repaired
features must retain behavior during future work. This snapshot is the review
reference for qualified extensions; it does not freeze the still-missing armor
stat/appearance/acquisition implementation into permanent absence. Asset signing
and protection remain deferred under the owner's directive.
