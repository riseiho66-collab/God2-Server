# Owned player appearance: actual same-scene peer integration

## Delivered

`Application.cpp` now prepares the peer DA deliveries and replacement6F cache
inside the weapon/appearance transaction. Preparation failure rolls back both
owned instances and appearance. The serial game executor applies the prepared
cache only after durable commit, then sends DA to other members of the same
scene. Pending admission updates its already owner-bound presence instead.
No new membership, identity, item, stat or appearance row is granted.

`RecoveredRemoteActor::with_appearance` checks the complete DA actor WORD
against the6F identity and requires ordinary transform0. It preserves all other
6F fields, replaces components21..28 and scalars79/80. Fresh world presence now
also projects2A body34/35 to6F79/80. Native FC1C0 stores body76 WORD at actor262
and body78/79 bytes at actor264/265; the existing pinned native contract/full
tests and DA oracle qualify these consumers independently of source mapping.

This extends CUSTOM-0047 fixture integration. Synthetic remote actor mode
remains forbidden; loopback owned appearance/weapon dependencies remain
required. Real town visibility can now be combined with the isolated fixture.
The two synthetic full20-byte WPN operands and their knife01/02 projection are
still not an original item-to-appearance rule or production weapon generation.

## Current-client acceptance

Final candidate `build-town-visibility/Release/god2-server-weapon-peer.exe`:
SHA256 `af108e455f06408c22cc41a211cf6c4127ffc43c3c7bca27369f571ed49b3464`.

Hidden two-client artifact:
`artifacts/playtests/private-weapon-peer-20260927-03/{run-result,ui-result}.json`.
Both existing fixture accounts authenticate; actor4 and peer5 see each other.
Four actual28 UI operations produce equipped items1,2,0,1, appearance revisions
2,3,4,5. Owner and peer live weapon handles43,44,42,43 match the pinned
HeroDoll source/cache filenames r02w000.romz, r02w001.romz, r02w300.romz,
r02w000.romz. First three components and variants, names, positions, both
players' HP/MP and unrelated DB rows remain unchanged during these operations.

Peer5 reconnects in a new process. Fresh6F actor4 components
`01c0016001600100`, scalars0/0 and live knife01 resource43 match saved revision5.
Subsequent movement to Kunlun4/3/126/127 agrees in DB and peer state; both
native clocks advance. Source DB, formal and private client files are unchanged.
Input desktop remains Default; hidden input desktop is not switched. All
owned clients, runner and private server close, and2598 is released.

The native DA remote consumer keeps spawn selector bytes while replacing live
resource handles and variant bits. Immediate DA acceptance therefore compares
the actual handles/variants against source-qualified resources, not a false
expectation that every cached spawn byte changes. Fresh6F acceptance checks the
complete eight-byte block. No screenshots or rendered pixel comparison were
performed; no actual God fixture or scene-transition test is claimed.

Earlier attempts are retained:01 failed a prelaunch DB basename constraint;
02 reached mutual visibility but incorrectly compared centered display names
without native leading spaces. The tool was corrected using the known5097D0
name formatter;03 passed every gate. Neither failure justified client patches.

## Rechecks and release safety

- Same-candidate owned appearance TCP tests pass: missing/other-owner rows,
  atomic weapon/DA commit, rejection and server restart/2A restoration.
- Same-candidate owned weapon TCP tests pass: complete instances, swaps,
  rejections, persistence and restart.
-14 pinned native remote contract/full tests pass, plus DA wire/native tests.
- Focused CTest checks pass for appearance storage, weapon transactions,
  visibility,6F projection, configuration, database/Lua, Kunlun and movement.
- Stage `artifacts/releases/owned-player-peer-appearance-20260927-01` migrates
  an online backup to schema29. Pre-existing table changes are empty; new
  appearance rows0. Active binary/config and client remain unchanged.

Release state is **INSTALLED_GATED**, verified after a no-player service update
with backup and rollback support. Formal service uses schema29 and the exact
accepted candidate, PID17568 listening2592. Existing tables, triggers/indexes,
client and config are preserved; weapon/appearance fixture flags remain
disabled, appearance rows0. Original WPN-to-DA
mapping, authoritative equipment conditions and final attack/defense generation
remain open; source category labels and tooltip arithmetic do not establish
those rules. Overall playable completion remains approximately11%, a planning
estimate rather than measured full packet coverage.

## Subsequent test-selection correction

The later source-restriction round found that two CTest ENVIRONMENT properties
overrode the requested binary with older candidates. Accordingly the earlier
same-candidate TCP wording above was not proven by those runs. The hidden peer03
acceptance was correctly pinned. Both TCP routes have now been rechecked with
explicit printed SHA80f09ca536f7b58fc32abd03412f2d44cc40e3931edfab6a93dfbe33a52b4f60,
which includes this peer implementation and is the latest installed candidate.
See owned-weapon-source-restrictions-integration-20260927.md for the correction
and actual current-client regression04.
