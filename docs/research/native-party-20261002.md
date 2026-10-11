# Native party integration — 2026-10-02

## Evidence and scope

Pinned mapped image: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Current client: `c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575`.
Pseudocode is a trace aid; original machine execution establishes field layout.

| Direction | Opcode | Logical bytes | Verified native contract |
| --- | --- | ---: | --- |
| C2S | 6A | 9 | 497140: self DWORD, target DWORD |
| C2S | 57 | 5 | 497170: target DWORD; self argument ignored |
| C2S | 58 | 5 | 497230; 4EA770: joiner WORD, answer0/1/2, opaque stack byte |
| C2S | 5A | 19 | 4971B0: self WORD, name16; after NUL bytes unwritten |
| S2C | 54 | 29 | 4EA8A0: name16, joiner WORD, profession, transfer, HUD4, level DWORD |
| S2C | 55 | 25 | 4E9BC0: id WORD, flags, leader, HUD4, name16 |
| S2C | 56 | 7 | 4EA140: id/x/y WORDs |
| S2C | 57 | 19 | 4E9EB0: id WORD, name16; own name clears own roster |
| S2C | 58 | 21 | 4E9AD0: id/opaque WORDs, HP/MP/maxHP/maxMP DWORDs |

C2S58 is an invitation response, not the S2C58 vitals record. Trade C2S69 and
S2C8A are separate and remain open. Never infer direction from opcode alone.

Native55 excludes self from its four-other roster, deduplicates names and updates
the designated leader. 57 shifts roster/position/vitals arrays when removing a
member. Native58 retains DWORDs but 4E9990/4E9A30 calculate bars from signed low
WORDs. Values32768+ can display negative or excessive percentages. Such resource
variants are not qualified for this route; no saved resources are clamped.

Native profession initialization4E8E80 uses WORD indices005974C8=(9,1..8).
Create17/1B producers store profile29=2*category+sex+1, matching party54 low-nibble
labels male/female sword, taoist, warlock, pharmacist. The high nibble and transfer
byte source remain open; sending transfer0 is expressly a custom default.

## Installed policy

`CUSTOM-0062` owns transient consenting membership. Authenticated owned selected
ready-world role and resource snapshots required, same scene at join/accept,
capacity5, pending30seconds, one visible offer per leader, leader-only kick,
leave/cancel/disconnect cleanup and leader disband. Strict recipient-localized
names are prepared before state publication. Colliding converted names or
unrepresentable text deny publication. Raw submitted leave names grant no authority.
The recipient's own name retains its Unicode spelling without OpenCC conversion:
native55/57 compare the raw actor name to recognize self. Other members use the
recipient's display language. All existing members must remain ready and in the
joining scene before accepting another member; full replay cannot bypass this gate.

No durable party row, item, money, EXP, resource debit or reward is created.
Follow, group combat, shared loot/EXP and persistent/offline groups remain open.
Position/vitals refresh observes at most the relevant five member leases after
an accepted handler commits movement/resources. Every snapshot is observed before
diff generation; readiness recovery replays missed current data in both directions.
Scene return rehydrates same-scene positions; cross-scene coordinates are not sent.
An explicit scene-invalid marker and full cross-scene UI tracking remain open.
One party request may coalesce with common chat and idle ticks; the existing frozen
chat handler receives the remaining records unchanged. Other mixed action batches
remain unsupported. Structural33 world parser cases are not33 complete systems.

## Verification

`python -B -m tools.strike_lab.current_party_20261002`:
79 original-machine cases and5 receive-length checks pass. Original queue,
roster, position, vitals, removal, signed x87 bar arithmetic and profession
initialization/create producers execute; only external UI/time/queue boundaries
are stubbed. This is not a rendered-client or network acceptance claim.

`python -B -m unittest discover -s tests/research -p test_native_party_server.py -v`:
6 isolated Application/SQLite TCP cases pass: fragmented invitations, forged
source/target, duplicate/mixed batches, decline/busy/stale answer, acceptance,
leader-only kick, member leave, pending cancellation, leader disconnect and true
relogin with a fresh lease. Added variant-name self identification by executing
native55/57 on actual server bytes, bilingual common chat after joining and in a
coalesced join batch, position delivery before another tick, and missed-resource
rehydration after a synthetic resource-unavailable interval.
Native responses are decoded independently, including HP/MP field order.
All saved tables and schema are compared; only the movement test permits its
explicit position mutation. The synthetic resource test restores the exact rows.
Old companion fixture lacked role5/resources;
its disposable clone imports the existing qualified synthetic role5/resource rows
from the read-only peer fixture. No production player receives test defaults.

## Current-client acceptance and deployment

Runs05/06 accepted original TW/CN clients on the owned hidden desktop in both
language directions. Each exercised decline, acceptance, actual native out/back
mouse movement and observer party56 arrays, leave, leader kick, rejoin and leader
disconnect. Raw names台(TW) and臺(CN) retained self recognition. Native roster and
vitals arrays were read using read-only handles; no screenshots/pixel-rendering
claim, foreground desktop switch, memory writes or packet injection. All schema
and unrelated saves were unchanged; only the two test roles' movement revisions
advanced. Both clients and isolated servers were closed.

Run01 used the wrong kick action; run02 the wrong trade action; neither is party
acceptance. Run03 was interrupted before two clients completed, has no terminal
receipt and is unqualified; OS process/port absence was checked before run04.
Run04 passed basic UI before the review fixes; only05/06 qualify the current hash.
One early TCP suite encountered an unlocalized login/list EOF before party input;
the isolated case and subsequent complete suites passed. Diagnostic capture was
added; this is not a claim of exhaustive authentication reliability.

CTest5/5, TCP6/6, machine79 cases plus5 lengths, packet ledger1/1 and frozen chat
passed. Executable-only managed release:
`artifacts/releases/native-party-20261002/deployment/release.json`.
Installed SHA256 `e2fb3ab7f2954ff420a908c8f7e9093d0cae3274ff78e09a14596a1aa90302c2`,
PID2076 at deployment, port2592; no schema/saved-row/config/current-client changes.
Backup and executable-only rollback retained. Actual group battles, transitions,
five rendered clients and hundreds-player load remain unqualified. The configured
formal server currently allows8 sessions. Overall game completion remains unknown;
formal world parser entries increased29→33, not a whole-game percentage.
