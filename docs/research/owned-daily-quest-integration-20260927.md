# Owned daily display integration — 2026-09-27

## Installed result

Release `artifacts/releases/owned-daily-quest-views-20260927-01` is
`INSTALLED_GATED`, schema30. Active server SHA256:
`bbaee10f790d23b7ee1827bd36511bba3a322e33158455db0882ce1bfe9d0f05`.
The formal DB contains85 qualified native316 display rows. No character daily
lists were granted, and `world.owned_daily_quest_views.enabled` defaultsfalse.
The deployment verified every pre-existing table, migration history,
trigger/index, account/save, config and client unchanged. Service listens on
127.0.0.1:2592. Full installation checks are in the release verification JSON.

This connects an owner-bound daily opening/display route. It does **not**
restore playable original daily quests, NPC transport, ticket consumption or
claim rewards. Whole-server progress remains approximately11% as a planning
estimate, not measured complete packet coverage or verified playability.

## Native evidence and storage

See [source qualification](current-daily-quest-source-20260927.md) and
[native lifecycle](current-daily-quest-lifecycle-20260927.md).

The current457FF0 parser returns85 records of316 bytes;458430 lookup scans
source order and keeps the first matching BYTE pair, including(0,0). The
source's current85 pairs happen to be unique. A synthetic duplicate test
qualifies first-match semantics without modifying stored native records.
Keep raw CP950 and bounded text. Source lines12–15 have description2/reward
blocks without an in-block NUL; silently rebuilding the text would lose the
actual cross-field parser behavior. The catalog stores exact bytes, not
invented source availability rules.

Parsed85 concatenation fingerprint:
`df0bc3a96425c3440cd2fefc867840aa10e3ad35c4a3be32e332c6204f30236a`.
Raw85 length-prefixed rows fingerprint:
`29b67f9d734a30ca584b6b09a295713cd2e32e00de44ce4472c47a2d65dc079b`.
C++ validates both, source lines/ordinals, row hashes, client/source pins and
authority. Python import executes the native parser/lookup afresh, requires
the complete unchanged raw source, owns its transaction, rejects conflicts
and preserves source rows even against side-effect triggers.

## Runtime and authority

| Record | Qualified behavior | Runtime scope |
|---|---|---|
| C2S D7 00 | Actual HUD/menu daily opener, fixed2 bytes | Authenticated ready owner with saved list receives FD |
| S2C FD AC00 02 | Fixed172 bytes, 40 DWORD rows plus8-byte context | Preserve full context/finalWORD; count<=40; every issued pair must exist in pinned source |
| C2S D8 mode1 | Native source start/end NPC, first18CA slot orFF, side1/2 | Check issued owner/session/scene/revision/full list/source flags/NPC, then log unresolved intent |
| C2S D8 mode2 | Actual source label952「每日領取」 | Check previously issued gate and itemWORD, log unresolved claim; no reward |

Row buttons are「傳送至NPC」, not quest acceptance. Renderer enables rows only
when flags high2 bits are40h; producer additionally requires low6 bits nonzero.
Server checks both. Original availability/current-count production remains
unrecovered. No inferred time/week/rebirth predicate is enforced from display
fields. D8's qualified current tail is0; the structural codec preserves other
values, but this runtime route does not authorize unqualified tails.

CUSTOM-0049 describes the owner-bound issuance policy and diagnostic operands.
It does not create gameplay rewards or authority. Mixed/multiple operations,
unissued selection, wrong source NPC, disabled row, stale revision, wrong
ticket slot and cross-owner state produce no mutation or fake success.
Session bindings are removed at disconnect. Restart requires a freshD7.

## Actual-client acceptance

`artifacts/playtests/private-daily-quest-20260927-02/run-result.json` and
`ui-result.json` use the same final executable SHA as installed. The client
ran on an owned hidden desktop, without screenshots, desktop switching,
injection or process-memory writes. Native UI controls opened the panel;
the harness read panel/text/packet-buffer state and paired it with server logs.

- Native HUD8/menu27 generatedD700 twice.
- Nine native source rows,32 text cells, two pages, disabled row, previous/next,
  close and reopen were accepted.
- Start/end buttons generated four actualD8 logical records:
  `d8010000ff80130100` and `d8010000ff80130200`, twice each.
  These use source NPC4992 and pair(0,0), not guessed coordinates.
- Full50 inventory cells, HP/MP/stats, ordinary appearance, quest journal,
  map and gameplay DB remained unchanged. God preservation was not tested:
  this fixture has no God and claims none.
- Client/source DB/formal config hashes were unchanged, all owned processes
  closed and private2598 released; input desktop unchanged.

The synthetic9-row availability flags are41 for enabled test rows and0 for
one disabled row. They are CUSTOM_TEST_NOT_NATIVE. Pixels and original quest
availability/reward rules are not certified by this test.

## TCP and regression evidence

`artifacts/playtests/owned-daily-tcp-20260927-b8878927/result.json` records21
TCP cases and3 corruption-startup refusals on the same SHA. ExactFD response,
unissued/mixed/stale/other-owner/disabled/ticket checks and restart passed.
Partial parsed84, one parsed byte changed, and raw+row/provenance hashes
changed together with parsed bytes unchanged were all refused by the full
catalog qualification, with test DB unchanged.

An initial corruption fixture had a diagnostic-incompatible basename; its
failure is explicitly INVALID_STARTUP_TEST_FIXTURE, not catalog proof. Final
three refusals match the actual catalog error.

Normal and optimized native source/import tests agree;13 atomic-import cases
pass in both. Native lifecycle tests qualify18 full list flows,24 claim gates
and4 dialogue slices per mode. C++ codec/binding and current rebuilt
config/database regressions are separate from actual-client acceptance.

## Next concrete work

Recover the server-issued original count/flags/availability and claim-item
authority; join actual NPC4992 and other source identities to build-matched
placement coordinates/facing; then qualify original transport/ticket behavior
and daily rewards/reset/progression. Native NPC/monster placement coverage is
still0 qualified complete records. No random placement or inferred reward is
introduced to disguise these gaps.
