# Owned deity skill restoration and native display qualification

## Production result

Release `artifacts/releases/deity-skill-display-20260927-01` is installed.
The C++ owned-snapshot preflight now rejects the39 current skill identities
whose original UI icon cannot be displayed. This applies to repository import,
persisted-state loading, world restoration and deity selection. Raw logical
codecs and the formal448-record skill catalog remain lossless and unchanged.
No account, character, owned deity, pet, resource or progression row was changed;
no skills were granted. Schema remains37. The executable-only deployment
verified an idle local listener and exact stopped-state table/schema preservation.

Candidate and installed server SHA256:
`3b235dab1cbf1a1a74af7d897152a98921c9603a6db1a5e7e4dbab71bbf0e6ed`.
Current original client SHA256:
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
Client, launch settings and server configuration were not modified.

## Concrete defect and native evidence

The initial full-capacity fixture assigned all448 source identities, including
internal/non-display entries. The real client crashed during S2C34 refresh.
Fixtures02/03/04 are failed historical observations, not accepted evidence.
The isolated debugger only continued native events and read registers/stack;
it did not set breakpoints, write memory, alter code, inject code, switch the
owner's desktop or swallow application exceptions.

Fixture04 recorded access violation at `0041E731`, reading address0.
The actual stack includes `004A965C`, `004AA7E2`, `0050692C` and `0041EAB7`.
Icon bank70/action119 (kind0/id120) had an ACT_DATA header whose pointer+30
was null. Native `0041E710` reads that pointer and traverses its10-byte frames
without a null check. `004A9510` displays25 learned definitions per page;
`004A9710` maps kind/id using the actual runtime arrays at005B6F70/005B6F80.
Runtime offsets are0 and banks are70,71,72,73. Static image zeros alone were
not used as evidence for those runtime mappings.

Accepted fixture06 read all448 native icon entries without invoking missing
animations. Its `ui-result.json` SHA256 is
`bb815dbf4daeb4e7d2b597d6c9d2d28cfbb1fce8b5dc7f38da8b6e0d1e03e7a6`.

| Kind | Source definitions | Display resources present | Unavailable IDs |
| --- | ---: | ---: | --- |
| 0 | 121 | 119 | 120–121 |
| 1 | 129 | 113 | 73–88 |
| 2 | 87 | 81 | 63–68 |
| 3 | 111 | 96 | 84–98 |
| Total | 448 | 409 | 39 |

Kind0/id121 is outside bank70's120-action bound. The other38 unavailable
identities have no animation pointer. This is a display qualification result;
it does not prove these records are absent from original combat/internal use.
The server keeps all original records for further research.

## Actual client acceptance

Accepted fixture08:
`artifacts/playtests/private-deity-skills-20260927-08/run-result.json`.
It used the same installed candidate against a disposable own-server database
and an original port-only private client on a hidden God2Lab desktop.

-16 owned rows,100 unique skills per row;1600 learned instances.
-All1600 live pointers' full110 bytes equal the pinned cbspec2 source and
  qualified SQLite catalog. Union409 display-qualified identities across4 banks.
-Actual deity next/previous buttons produce native C2S67 and persist selection.
-Five deity rows, four pages each,500 actual icon/image checks cover all409
  display-qualified identities. Original controls43 and42 respectively advance
  and wrap backwards;10 additional reverse/forward checks passed.
-Page navigation changes no saved state. Returning to deity1 preserves all
  learned bytes, counts and native page counts. Five mixed pet drags and owned
  resource preservation also pass. No native client diagnostic or AV remains.
-Production/source database and both client files unchanged; input desktop
  remains Default. No screenshots or foreground input were used.

Tests `recovered_deity`, `owned_companions` and
`native_deity_skill_capacity_server` pass. The latter checks the compiled C++
predicate against every one of the448 pinned live observations, then exercises
16/100 restoration over real TCP, selection, pet transfer and a restarted own
server with exact persisted bytes. This TCP restart test is separate from UI
acceptance; it is not described as a native-client relogin test.

## Authority and remaining gameplay work

The definitions and actual display routes are native-qualified. Fixture skill
ownership and instance stats are `CUSTOM_TEST_NOT_NATIVE`, not recovered deity
starting skills, rewards, recruitment or learning permissions. Production
grants remain0. Original cast eligibility, MP debits, damage/hit/critical,
growth/EXP and acquisition rules remain separate pending work. This release
does not establish that all409 skills can be cast or have reconstructed formulas.

Scoped results: resource audit448/448(100%); usable current icons409/448(91.3%);
display-qualified identity page coverage409/409(100%); maximum owned restoration
capacity16/16 rows and1600/1600 instances(100%). These are not whole-game
completion percentages.
