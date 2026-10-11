# Native24 owned reserve pet reorder

Date: 2026-09-30. New server path for the current client's reserve cells42/43.
Existing28 active-pet selection and return behavior is unchanged. Active44 is
not an endpoint of this path. No pet, attribute, currency or item is granted.

## Current native producer

Current `../God2/God2.exe` SHA256 is
`9be38ef858bc9c63b6f296cae4a8e601ddcfaf614700e725c4bec44065b53336`.
The earlier inventory oracle pins6bf75... and correctly refuses this file.
The new bounded oracle pins the actual current executable; producer496610 and
queue4132E0 spans independently match the retained20260926 hashes.

All addresses are VA, image base00400000. Original caller49EAB0 performs source
definition lookup, then49EB44 loads signed source WORD at UI+855F0. Source42/43
branches at49EB55/49EB5F to49ED9D. Destination42/43 branches through49EE6D to
49EF06, which checks reserve source and reaches49EF1C. This reads the source
BYTE, pushes destination first and source second, and calls496610. Native queue
receives exactly `24 2A 2B` or `24 2B 2A`. Caller clears selection toFFFF after
the producer returns. It does not optimistically mutate an inventory slot.

The proof executes the original post-lookup classifier, complete24 producer,
and complete queue append. It does not execute the earlier mouse/tooltip/lookup
part of49EAB0 or claim physical current-client input acceptance. Caller and
queue writes have explicit bounds; stack, queue prefix and suffix are checked.
No game callee is replaced. Native gate+866E4 and the four known modal flags
prevent queueing. Sixteen cases pass in normal and optimized Python execution.

This inspection also prevents an incorrect weapon extension: bag/equipment34
classification goes through selection state and the existing28 path. Generic
496610 accepts arbitrary bytes, but that alone does not establish actual weapon
drag24 production. This change admits only reserve42/43.

## Runtime and persistence

`RecoveredOwnedPetReserveMove` is called from the existing typed inventory24
callback. The surrounding world service accepts one24 plus ticks, requires
world-ready and excludes battle. Application additionally requires the owned
companion snapshot to have been projected, no pending scene transfer and a
current owner-bound location. This path runs before the scalar bag-only gates.

`SqliteCompanionRepository::move_pet_reserves` is a separate additive API.
Both cells must already exist under the authenticated account/character. The
source must contain one qualified E3 or FB instance. `BEGIN IMMEDIATE` rechecks
complete expected bytes, provenance and revisions and refuses unsettled battle
reservations. Complete instances and provenance exchange; only the routing slot
changes in stats (E3 logical+27h, FB logical+3). Each physical cell advances its
own revision with signed64 exhaustion checks. Missing capacity is never created.

CUSTOM-0039 defines this whole-instance move/swap policy. Native24 establishes
source and destination; it does not independently establish original server
instance-transfer rules. No new numerical balance rule is introduced. Existing
instance provenance travels intact and remains distinguishable from the policy.

The response uses the existing qualified41 clear,3B full20-byte metadata,41
absolute count and complete E3/FB stats encoders. Both old cells are cleared
before either new family is installed. The reply is fully encoded inside the
transaction before COMMIT. SQL/encoding/readback failure rolls back. All three
owned cells are checked after each write sequence and again after preparation,
including unchanged44. Empty source and same-cell requests return no reply and
perform no write. Source/destination44, scalar bags and unknown slots stay outside
this helper.

## Reproduce and acceptance boundary

```
python -B -m tools.strike_lab.current_pet_reserve_move_20260930 --output artifacts/reports/pet-reserve-move-20260930/native.json
python -O -B -m tools.strike_lab.current_pet_reserve_move_20260930 --output artifacts/reports/pet-reserve-move-20260930/native-optimized.json
```

`tests/test_pet_reserve_move.cpp` covers mixed E3/FB swaps, exact native record
order, complete bytes/provenance/revisions, both directions, explicit empty
capacity, missing rows, owner/CAS, preparation failure, second-write failure,
active44 trigger corruption and pending battle. `tests/research/test_pet_reserve_move_server.py`
uses disposable SQLite clones and the candidate chosen by
`GOD2_PET_RESERVE_TEST_BINARY`, printing its hash. It exercises authenticated
socket admission, the projection gate, tick batches, duplicate-operation
rejection, exact replies, unrelated-state preservation and server restart.

The standalone C++20 `/W4` unit build passes; its exact command is retained at
`artifacts/reports/pet-reserve-move-20260930/build-unit.cmd`. This interim link
uses the existing core library plus the new repository translation unit. Full
candidate `8e24ec1f21c7197b9387d31d7380b9defa9cb2d7203cbfb1ac2f03d7c24f5b1a`
then passed the registered `pet-reserve-move.exe` and both TCP cases in5.150s.
The copied candidate is retained as
`artifacts/reports/pet-reserve-move-20260930/god2-pet-reserve-candidate.exe`.
Initial TCP startup correctly refused an incorrectly named disposable fixture;
the test now uses required `town-diagnostic-accounts.db`. No server isolation
gate was relaxed. These receipts are specific to that candidate hash; later
shared changes require a final candidate recheck.

## Actual current-client acceptance

`artifacts/playtests/private-pet-reserve-20260930-01/run-result.json` records
`accepted=true` on the same8e24 candidate above. The current9be38... executable
was copied under a unique disposable name and only its startup port immediate
was changed to2598; the copy receipt preserves the exact changed offsets and
both hashes. The deployed executable was read and hash-checked without writes.

Under the owner's standing instruction to automate inside the internal sandbox
without taking the visible desktop, the existing pinned private runner created
`God2Lab-23196-790960218`. Input desktop remained `Default`. The new bounded
worker reused established window-local click/drag helpers and read-only native
inventory/companion checks; it did not use screenshots, foreground activation,
desktop switching, injected packets or process-memory writes.

The original client's real42→43 and43→42 drags produced two native24 requests.
The server committed both; full20-byte metadata, E3/FB caches, source provenance
and physical row revisions matched saved state. Each previous generation's
cache was cleared. The fixture deliberately retained an occupied FB in44 and
a selected deity: their native records, player resources, other inventory
cells and unrelated saved rows remained unchanged. These are explicitly
synthetic owned fixture instances, not native pet generation or growth values.

A second fresh client process reconnected and restored the exact saved order,
full inventory records, occupied generation caches, player/deity values and
active44. Inactive opposite-family caches are not compared between separate
processes because original initialization does not guarantee their bytes.
Both client processes, private server and runner closed. Source database,
source config, deployed client and the copied candidate hashes stayed unchanged.
No production database or running service was changed. This closes the bounded
current-client input/state gate for8e24, not complete pet gameplay or deployment.

## Final integrated candidate recheck

The integrated candidate including schema39 and role20/23 is pinned to SHA256
`1c2a6d090c6759eca2786adba690ab7da60e6a821ff87c73005e7df01ad72fc5`.
Its copied executable is
`artifacts/reports/pet-reserve-move-20260930/god2-pet-reserve-final.exe`.
Both TCP cases passed in11.074s (retained `tcp-final.log`) and the registered
`pet_reserve_move` CTest passed in0.22s. Hidden run02 confirmed both native24
directions on this candidate, then stopped before reconnect when the added
role test treated native caret27 as a hit rectangle. The driver correctly
rejected that rectangle; no role request was sent. All owned processes closed
and source hashes stayed unchanged. The corrected driver uses the role panel's
already selected input mode2; caret27 is not a mouse input target.

`artifacts/playtests/private-pet-reserve-20260930-03/run-result.json` then
completed with `accepted=true` on the final1c2a candidate. Its SHA256 is
`70319eb80148b148ab058255cea374c59e10acc0c7ef1ead9b2d201dccdae5cb`.
Both real42/43 drags, exact owned metadata/stats/provenance/revisions, active44
preservation and a fresh-process reconnect passed again. The private desktop
was `God2Lab-12500-791406812`; input remained `Default`. Every owned process
closed, and source database/config/client plus candidate/copy hashes remained
unchanged.

The same final run additionally opened the native role panel through HUD
control5, typed15 ASCII bytes `RoleNativeProof` in its selected mode2, and
closed through role control10. That real UI path sent native20. The candidate
saved canonical16-byte text, codepage950, revision1, qualified source hash and
CUSTOM-0056. The native actor secondary field, overhead renderer buffer and
widget7 static copy all contained that value. A fresh client then received
native23 and restored the same three fields without changing the saved row.
This covers ASCII role input and the actual native receiver/state path; no
pixel screenshots or IME behavior were tested or changed. The role persistence
implementation and its wider codec tests are documented by the roletext lane.

Reproduce with a new output directory and a new port-only clone filename:

```
python -B tools/strike_lab/private_pet_reserve_move_20260930.py --output artifacts/playtests/private-pet-reserve-20260930-03 --client ../God2/God2-pet-reserve-lab-2598-20260930-03.exe --server-candidate artifacts/reports/pet-reserve-move-20260930/god2-pet-reserve-final.exe --role-text
```

The command above records the completed run; its existing output and clone
names deliberately cannot be reused. This completes the bounded current-client
gate for the final candidate. It does not claim deployment, original pet
generation/growth formulas, or complete inventory/shop gameplay.

## Independent release-helper review

The reserve-lane reviewer independently read
`tools/operations/packet_links_release_20260930.py`, its shared managed-service
helpers, the migration manager and its release-safety tests. Reviewed helper
SHA256: `8fbe9935ae5853f6314e6cc561c81b940e60967c764f226acbc679b452677c48`.
The review did not edit that helper, execute apply, or stop/start any service.

Two findings were reported to its author and corrected before staging:

- A partial failure in `stop_idle` previously escaped the apply recovery block.
  Stop now executes inside it. Before any binary/database mutation, an error
  validates the original executable/config and either observes its qualified
  listener, restarts only when the owned process is absent, or records that
  availability requires manual repair.
- The listener identity previously established only its executable path.
  `managed_listener` now also checks CIM executable identity and the exact
  three command-line arguments: managed image, `--config`, formal config.
  Alternate configs and extra arguments are rejected. Config scope additionally
  requires127.0.0.1:2592 and no separate character listener.

The remaining review found no blocking defect in the stated release scope:

- Stage uses read-only backup sources, new release artifacts and a disposable
  migration target. It pins candidate/old image/config/client/frozen contract
  hashes plus exact hidden-client and eight-case TCP evidence. Existing schema,
  history and53 old table fingerprints are preserved; only the empty role text
  table and migration39 history row may be added. Migration is run twice to
  verify idempotence. Apply rechecks those pins and current evidence.
- Apply refuses existing players before any stop/mutation and checks established
  or connecting sockets again immediately before stopping the exact owned PID.
  The at-install backup is fresh after shutdown, so intervening saved state is
  retained. Candidate installation is hashed and atomic; migration runs in
  place and is verified before the gameplay listener opens. No backup database
  is copied onto the formal save.
- The old migration manager explicitly refuses schema39. Recovery therefore
  cannot switch back to old code alone: under `BEGIN IMMEDIATE`, it requires
  complete old schema/history/metadata/fingerprint equality and an empty new
  table, removes only that table and history39, and verifies full equality
  before committing and restoring the old image. New player rows or any old
  save change reject the inverse without overwriting data. Connected players
  also prevent recovery from stopping the candidate. Unsafe recovery keeps
  the candidate artifact/save and records that repair is required.
- Verify accepts legitimate saved-state changes after startup and reports them;
  it does not treat a stage snapshot as authority to discard newer saves.
  It still requires exact migration schema/history, binary/config/client pins,
  durable pre-listen migration proof and the qualified listener identity.

The author-run safety log
`artifacts/releases/packet-links-20260930-01/release-safety-tests.log` reports
18/18 PASS in0.672s. The reviewer inspected the cases and retained result,
including transaction rollback, old-row/new-role-row rejection, active-player
refusal, partial-stop recovery, wrong argv and hash gates. The retained
`prepared.json` reports `prepared=true`, `applied=false`,53 old tables unchanged,
empty39 table and idempotent migration for the final1c2a candidate. This is
release preparation and a code review result; actual apply/verification is a
separate parent-agent operation and is not claimed by this receipt.
