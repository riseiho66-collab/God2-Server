# Owned full-instance player trade (CUSTOM-0069)

## Evidence and scope

Original mapped build149c1b45/current clientc5d8f79b/source70a4e7dd.
`artifacts/research/current-trade-instances-20261003/run01/native.json`
contains3832 original-machine cases; the separately preserved
`consumer-boundary-controls-v02.json` contains240: total4072 offline cases.
The primary producer49E440 ->497290 sends logical2A length7:
item WORD, source bag BYTE, quantity BYTE, target WORD. It sends no opaque20.
The real original producer copies the full bag24 into self UI+866E8,
setting byte1 to source bag slot. Consumer49DF10 ->49E1A0 stores all24 from
logical50 into peer UI+867A8, setting/selecting by offer index0..7.
Full24 transport includes opaque20 at body+4; flags/tails are preserved.
Native full8 offer capacity, ordinary source boundaries and malformed peer
indices were tested separately. This is evidence for wire/state copying;
it is not original server admission, binding or item-generation evidence.

## Server route

New independent repository/service selected only by explicit authenticated
`world.owned_instance_trade.enabled=true` together with owned armor transport.
The accepted0063 scalar trade service and repository remain unchanged.
Both owned ready characters must stay in their original area/scene and lease.
Up to8 distinct offers per character, ordinary0..29 only. Full source-qualified
armor, weapon and gem instances transfer whole; existing native MED eligibility
retains partial quantities. The original request supplies identity/slot/count;
all opaque20 comes from actual owned storage. New schema45 adds only the empty
`character_owned_instance_trade_receipts` table. No saved-item grants or reads
that allocate capacity. No price, combat, appearance or stat formula changes.

Custody policy is CUSTOM-0069: remove both offers before choosing each incoming
first explicit empty slot; no merging. Exact immutable before/after snapshots
cover both full50 scalar domains, three metadata overlays, protected equipment,
source/client provenance and wallets. SQL transaction checks both owner CAS,
prepares complete replies before writes, checks final readback/receipt/late
live-world and battle state, and rolls back both owners on any mismatch.
Receipts cannot replay accepted0063 or0069 identifiers. Cancellation, timeout,
disconnect and failure restore authoritative bag/wallet state using original
4F/41/27; inactive slots use the canonical5-byte41 clear, not a fabricated
20-byte zero record. Original inactive client tails may remain in memory.

## Verification and frozen behavior

New tests cover actual production SqliteDatabase catalogs (1354 armor,
1259 weapon/TWP,71 MED declarations), dual-owner full20/provenance custody,
partial MED, same-ID different tails, protected optional slots, replay,
capacity, preparation failure, late mutation and SQL-trigger rollback.
Build/CTest/live acceptance will be appended after actual terminal results.
The formal server remains accepted0068/schema44 until separately accepted
and installed. Existing chat/auth/IME/client binaries remain frozen.

Root repaired NEW0069 test composition after its first build exposed nested
`main` macros in historical test reuse. NEW0069 now directly reuses0067 fixture
and independently imports the original weapon catalog. Failed build01 is
preserved; no runtime fix was needed for this compilation issue.
For future migration/config verification only,0068 adapter assertions now use
the current migration tail and a private configuration with its opt-in erased.
The prior exact0068 test and28 runtime source pins remain preserved in
`artifacts/research/owned-instance-trade-0069/predecessor-20261003/pins.json`
and its source snapshot; the accepted0068 candidate contract is unchanged.

## Terminal build and CTest qualification

Candidate `4a309a8cbc2994b59f235fda008d299b7ba443e2c725edc517a545c3df49bf72` is frozen with32 runtime pins,4 new or
updated test pins and19 regression source pins. Build03 exited0; a single
CTest02 run passed23/23, including all3 new tests, true production adapter,
prior whole bank/scalar trade and database/config/auth/character repository.
Paths and exact hashes are in
`artifacts/research/owned-instance-trade-0069/candidate-20261003/contract.json`.

Initial CTest01 correctly failed2 isolated fixtures for missing wallet DDL.
NEW repository and service fixtures now explicitly install the accepted
wallet schema before provision; production adapter already passed initially.
Build and failed logs were retained. A bounded independent code review
identified `const Plan` return after COMMIT as a potential allocation failure
that could misreport durable success as cancellation. NEW repository now uses
a non-const local and compiler `is_nothrow_move_constructible_v<Plan>` assertion
so NRVO or implicit noexcept move avoids that postcommit copy. This is
compiler qualification, not an allocation-fault test.

Frozen chat gate passed and formal process29548 still served accepted0068
2172c969 on127.0.0.1:2592 and62031 during qualification. No formal migration45,
client binary change or saved-row update has occurred. Live original TW/CN
acceptance remains pending; offline4072 and CTest23 do not substitute for it.

## Original-client acceptance and formal installation

The single cold NEW run01 ended0 with accepted=true:
`artifacts/playtests/private-native-blackbox-owned-instance-trade-20261003-01/run-result.json` (SHA `0000b76ad5f0938f9ca4132c46f6313caf70c6410c333b9540f1c29d0299fda9`). Original hidden TW950 and CN936
produced56 native2A offers (28 each),2 cancellations with all rows unchanged,
2 actual dual-confirm settlements with independent full receipt/row plans,
and5 native29 opens. Each offer checked exact SELF sourceSlot and PEER
offerIndex24 including full opaque20. EQU2,TEQ26,two same-ID/different-tail
WPN1 instances,TWP25,gem8 and partial MED were covered in both directions.

Both clients were closed and launched anew; two distinct new PIDs restored
all50 observed cells, occupied20 and wallets against durable saved rows.
Absent cells were checked only for quantity0, without treating inactive tails
as authoritative items. Money and quantity were conserved; protected equipped
instances, other players and unrelated tables were unchanged. All4 clients,
the isolated server and runner (6 PIDs) were proven terminal; port2598 was
released and the desktop owner/client/source/config/archive hashes unchanged.
This validates the specified custody transport, not original tradability,
binding, acquisition or stat formulas. No pixel/skill-animation claim is made.

NEW release helper qualify and clone stage ended0 before apply. Formal apply
ended0, exact candidate `4a309a8cbc2994b59f235fda008d299b7ba443e2c725edc517a545c3df49bf72` installed as
PID31184; schema44->45 adds only an empty receipt table and index.
Original1354 armor/1259 weapon/71 MED source records and every prior typed
saved row remained unchanged:0 grants,0 added capacity,0 prior rows changed.
Accepted0068 foreign banking and new0069 trade startup markers both appeared.
The active full-instance route is opt-in enabled in formal config.

Receipts: `artifacts/releases/owned-instance-trade-20261003/clone-stage/release.json` and `artifacts/releases/owned-instance-trade-20261003/clone-stage/postinstall-root-proof.json`. Independent root
postinstallation verified source32, clientc5d8f79b, schema45, integrity/FKs,
empty new receipts, frozen-chat baseline and both actual listeners2592/60976.
The original23/23 terminal CTest remains pinned in the candidate contract.

Owner requested stopping after this round. This round is now complete;
remaining whole-game protocol/gameplay work is not complete and will remain
paused. The formal server remains running for the owner.
