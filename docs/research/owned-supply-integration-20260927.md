# Owned MED02 supply integration — 2026-09-27

**Status: INSTALLED_ENABLED — release `owned-supply-20260927-01`.**

CUSTOM-0050 connects owned self-player supply to the ordinary authenticated
world route. CUSTOM-0016 retains the Lua cap, living-only and conditional debit
policy. Final candidate04 passed actual-client and TCP acceptance and was
installed with the owned route enabled. Verified candidate/server SHA256:
`a6e9202d6b7d7649af8c8dbb814fe316c3a6ddc288141e7edf050b633420b93f`.

## Evidence and authority

- Current MED02 contains100 rows;71 have qualified positive HP/MP declarations
  and use flags. The other29 remain unsupported by this supply policy.
- Recovery quantities are `NATIVE_CLIENT_TEXT`, validated against pinned raw
  source bytes, hashes, lines and parsed declarations. They are not an original
  server healing/debit formula. The owned route requires the complete imported
  catalog; it must not silently use the historical two-item fallback.
- Native requests are exact seven-byte C2S26: opcode, raw target WORD, item
  WORD, slot BYTE and opaque residual BYTE. The residual is neither quantity
  nor replay identity. Native ordinary shortcuts search slots29 down to0 using
  positive signed count and copy the actor WORD unchanged.
- Native S2C41 absolute item/count and S2C24 resources are separately qualified.
  The [native report](current-med02-self-supply-20260927.md) records current PE
  and source pins, source lines, full callee scope and historical references.
  Its normal and optimized runs pass17 producer vectors,2 blocked producers,
  4 complete response pairs,1 neutral24 and1 God-damage counterexample.

## Runtime contract

`world.owned_supply.enabled` defaults false. Enabling it requires authenticated
recovered world entry and movement, with mock login and legacy
`diagnostic_world_supply` excluded. Existing saved resources are restored before
companion binding. Only explicit, source-qualified owned bag0..29 rows are
projected through complete slot records; missing rows remain unknown, and
existing unsupported rows are neither replaced nor granted a supported item.

A frame may contain one26 plus ticks and the qualified optional trailing1F.
Duplicate uses, mixed mutations and unrelated control batches reject before
mutation. Admission requires completed world readiness, prior owned projection,
current owned location, an exact session-bound self actor, matching saved item,
nonempty count/source and a qualified declaration. Pending scene transitions,
in-battle state and saved battle reservations deny use. The item request does
not authorize another player, a God, or a pet.

CUSTOM-0016 computes each resource as
`old + min(source amount, maximum - old)` for a coherent living saved actor.
It consumes one unit only if HP or MP increases. Dead/full actors cause no
resource write, inventory debit, revision advance or successful effect reply.
Reply preparation precedes atomic resource/slot revision checks and commit.
No-op is not a fabricated success, and the opaque byte does not deduplicate
later independently valid uses.

The route grants no item, starting resource, revival, reward or stat. God/pet
healing and battle supply are outside this round. There is no inferred original
cooldown, price, equipment multiplier or general combat formula.

## Companion and client safety

Ordinary world24 can deduct active God HP when the newly supplied player HP is
lower than the client's prior player HP. This was reproduced with player
100→90 and God37→27. Supply therefore depends on an ordered coherent resource
baseline and never intentionally decreases player HP. The native positive/MP
tests preserve all two God records, selected binding, three pet cache records
and pet inventory records. A neutral24 at full HP/MP also preserves inventory.
No-packet cap handling is separately checked in the server/client workflow.

Actual hidden03 retains Gods100/101 and three battle-pet states at slots42..44.
The harness compares saved companion tables, native God vitals and selection,
pet72-byte cache entries, inventory instance metadata and unrelated state.
This preservation is not authorization to heal or consume items for companions.

## Actual-client acceptance

Final `artifacts/playtests/private-owned-supply-20260927-04/run-result.json`
records `accepted=true`, matching candidate/actual server SHA, five observed
requests and fresh reconnect persistence. Hidden03 is retained as preliminary
history; hidden04 qualifies the final correction and installed binary.
Physical hidden-window input drags slot5 金創藥3101 and slot12 順氣藥3107 to the
shortcut bar and uses F1. It does not call a producer directly or edit client
memory. Starting isolated values are explicitly synthetic HP20/120, MP2/80,
slot5 count2 and slot12 count3.

| Action | HP | MP | Relevant count | Commit |
|---|---:|---:|---:|---|
|Slot5 HP100|120|2|1|yes|
|Slot5 at cap|120|2|1|no|
|Slot12 MP50|120|52|2|yes|
|Slot12 MP50 capped|120|80|1|yes|
|Slot12 at cap|120|80|1|no|

Three successful uses advance only their saved slot/resource revisions; the
two cap actions change nothing. Fresh reconnect restores the final state
without a grant or another debit. Hidden04 also confirms all owned clients,
server and runner closed, desktop unchanged, candidate unchanged, and unchanged
source database, formal config, live client and private client source files.
This is native state/input acceptance; rendered pixels were not tested.

## Empty-bag correction and final receipts

A later isolated fresh-world test enabled the formal guide flags while leaving
the actor without bag rows. It exposed a dependency on legacy world-ready
guide-slot/bag provisioning. Such provisioning would violate this route's
no-grant/no-mutation admission contract even if potion use itself were correct.

Root corrected supply-enabled world admission to bypass that legacy fixture
provisioning and accept absent bags without inventing tombstones. A second
case retains an existing unsupported MED02 row3120 unchanged, without projecting
it as qualified supply. Final candidate04 and its TCP suite passed after this
correction, including fresh empty-bag and unsupported-row admission.

The final exact binary is covered by these receipts:

| Required result | Current record |
|---|---|
|Candidate SHA256|`a6e9202d6b7d7649af8c8dbb814fe316c3a6ddc288141e7edf050b633420b93f`|
|TCP22 cases, including empty/unsupported bags and reconnect|PASS: `artifacts/playtests/owned-supply-tcp-20260927-06e3cbbe/result.json`|
|4 corrupt-source startup refusals with unchanged databases|PASS in the same TCP receipt|
|Hidden04 five native uses, cap no-ops, companions and reconnect|PASS: `artifacts/playtests/private-owned-supply-20260927-04/run-result.json`|
|Formal installation|INSTALLED_ENABLED: `artifacts/releases/owned-supply-20260927-01/verification.json`|
|Registered `owned_supply_server` against installed binary|PASS,7.12s: release `registered-tcp-ctest.log`; tests use disposable databases|

Formal verification records schema30,71 MED02 declarations,
`player_tables_changed=[]`, `synthetic_grants=0`, client unchanged, and only
`world.owned_supply.enabled=true` changed in configuration. Service PID at
verification was13112. Original supply formula restoration remains false.
The option still defaults false in code; this installation explicitly enables it.

`tools/operations/owned_supply_release.py` implements stage/apply/verify. The
release retains `accounts.before.db`, `god2-server.active-before.exe` and
`server-config.active-before.json` alongside candidate files and the manifest.
Apply rechecks evidence/file identities and saved-state snapshots before the
stop/copy/start sequence; its failure handler restores the saved database,
executable and configuration and restarts the service. This is an implemented
rollback path, not a claim that failure rollback was triggered during this
successful installation.

Tests: `tests/research/test_owned_supply_server.py` and
`tools/strike_lab/private_owned_supply_20260927.py`. Both use disposable clone
state. This documentation update records the verified installation receipts;
it does not itself run tests or change production state.

## Balance assessment and replacement boundary

The [source and historical review](current-med02-self-supply-20260927.md#historical-references-and-custom-0016-balance-review)
supports the existing HP100/MP50 declarations, including the Bahamut8591 table,
while recording unavailable cap/debit authority and version-specific recipe
cost differences. No new recovery amount or economy value was selected.

Living-only use, cap and one-item debit iff any gain remain CUSTOM-0016.
Partial recovery can waste capacity: HP119→120 spends one HP100 unit; MP52→80
spends one MP50 unit. Full capacity consumes nothing. Those are deliberate
custom tradeoffs, not recovered original rules. Lua arithmetic tests and the
bounded client acceptance do not establish long-term economy/cooldown balance.

Replace custom rules only when qualified original evidence exists, preserving
source provenance, owned atomic revisions and no-grant admission. Separate
native authority and actual-client acceptance are required before adding
God/pet targets, revival or in-battle use.
