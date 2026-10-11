# Current packet gap ledger — 2026-09-30

This is a reproducible inventory for the current Taiwan client and current
formal server source. It is not a whole-game packet completion percentage.

## Reproduce

From `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B -m tools.strike_lab.current_packet_gap_ledger --output artifacts/research/packet-gap-ledger-20260930.json
python -B -m tools.strike_lab.current_c2s_queue_callers --output artifacts/research/c2s-queue-callers-20260930.json
python -B -m unittest tests.research.test_current_packet_gap_ledger tests.research.test_current_c2s_queue_callers tests.research.test_current_opaque74_server -v
python -B -m tools.operations.verify_frozen_chat_20260927
```

Original-client acceptance receipt:
`artifacts/playtests/private-panel-88-74-20260930-03/run-result.json`.
The test ran a port-only private copy of the current client on a hidden desktop
against the isolated candidate server. The source client, live database and
config hashes stayed unchanged, and all owned game processes closed.

The pinned mapped client image is SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
The census validates this hash before reading. Each report includes the
relevant source hash so a later parser edit can be distinguished from this run.

## Distinct layers

| Layer | Observed count | Meaning |
| --- | ---: | --- |
| Native S2C receive-size domain | 230 fixed, 22 variable, 4 unsupported | All 256 byte values queried; 252 have receive-size contracts, not identified gameplay handlers or server implementations. |
| Formal C2S world parser switch | 27 distinct opcodes | Structural parsing in one world-stage switch. It excludes login/character stages and does not prove an Application handler. Opcode35 has several action variants. |
| Native direct queue-call byte candidates | 225 sites | Distinct direct call locations in mapped `.text`, not 225 unique packet types or necessarily reachable actions. Indirect/wrapper calls are excluded. The unpacked image retains packer-era PE flags, so the scanner uses the pinned `.text` RVA and validates each relative call target. |

No count above is a numerator/denominator pair. Direction, game state, variant,
authoritative response and actual current-client acceptance still need to be
recorded per route. The previously cited 11% planning estimate is not packet
coverage.

## Connected transport boundary: C2S88 and C2S74

At RVA `073E00`, current native instructions are `push 1; push eax; push 74;
call 132E0`. This queues a two-byte logical record, `74` followed by one
stack byte. The producer does not write that payload byte, so its value is
opaque. Reconstructed caller `00473600` invokes it during a local UI mode
transition from mode 0 or 2 to mode 1. The reconstructed source is a trace aid;
the pinned machine instructions establish the queue arguments.

The `RecoveredWorldRecords` switch now preserves all 256 possible
opaque payload values as a typed `74` record. `Application` forwards only a
standalone record to `RecoveredWorldService`; its world-ready gate accepts it
without state mutation or a fabricated reply. A premature character-stage or
battle request and a mixed movement batch are denied. This closes the parser
and transport gap **only**. It does not prove the original server treated the
record as no-effect or that every UI transition is satisfied. In the isolated
current-client run, Ctrl+F opened widget 77, its native control 7 emitted 74,
the candidate admitted it, and client mode changed from 0 to 1 without a
server reply. Other states and authoritative semantics remain open.

The same panel-open path at `072BD0` queues `88` with two raw bytes copied from
a UI-selected WORD: `push 2` at `072BD8`, `push 88` at `072BE1`, and direct
queue call at `072BF4`. The new typed `88` record preserves both bytes. It has
the same standalone, ready-world, no-mutation admission boundary. The WORD's
server meaning and any required panel data reply remain unqualified; the
transport route is not a complete panel feature. In the same original-client
run, Ctrl+F emitted 88 and opened widget 77. Its input-enabled flag changed
from 0x13 to 0x23. The candidate admitted 88 without a reply.

## Checks and effect

The two inventory tests passed (2/2). They pin five previously qualified queue
calls, the `74`/`88` call arguments, the 27 current parser opcodes and the separation
of C2S versus S2C counts. Two C++ route suites passed (2/2). An isolated real
TCP run sent `88` with a raw WORD and `74` with three opaque payloads, observed no saved-state change or
invented reply, then received a valid S2C77 pose reply on the same socket
(1/1). The frozen-chat verifier passed with its baseline unchanged. The formal
running server, client binary, configuration, live database and saved character
were not changed. Current-client transport acceptance is 2/2 for these two
routes in the qualified panel flow; whole-game packet completion remains
unmeasured.

The rebuilt isolated server candidate is SHA256
`bdd923fe4a69e34d2c06604829fceff211da3874f574e85cba3b848c103a8f5a`.
Six related CTest suites passed (6/6): world service, session state, network,
world entry, world frame and world records. The complete solution build also
compiled the changed core and other targets, but could not relink the formal
`god2-server.exe`: the running formal service holds that Windows executable
open. This is a file-lock limitation, not a C++ compiler or test failure. The
separate candidate built and passed the isolated TCP check.

## 2026-10-03: complete-instance vault65 custody activated

CUSTOM0070 connects the qualified native65 whole-cell exchange to authoritative
existing owner storage across EQU2,TEQ26,WPN1,TWP25,gem8 and MED. Final marker1
is not quantity: the service records the actual complete source count. Native
48 replies preserve complete20; scalar and all typed overlays/provenance move
atomically with full-owner CAS, late world/trade/battle/lease checks and durable
receipts. Existing63/64 writers and the disabled-flag old route stay preserved.

The bounded original-machine oracle passed2232 cases; CTest passed26/26. Actual
original TW/CN hidden-desktop run06 passed144/144 native UI mutations, including
96vault exchanges and48deposits/withdrawals, then two truly fresh client logins
verified full50 bags/full300 vaults. All six fixture-owned PIDs closed, and
the user desktop, original client, frozen chat and formal data stayed intact.
Root qualify/stage/apply ended0 and formal schema46 candidate925f is installed
with no old saved-row change, grant or capacity addition. Full receipts and
remaining original-rule limits are in
[the CUSTOM0070 report](native-owned-mixed-bank-20261003.md).

The next targeted gap is native27 typed whole-instance discard:419 original
machine cases now qualify request/UI/41-clear behavior, but the formal route
still admits only the accepted scalar CUSTOM0061 policy. See
[the bounded integration plan](native-owned-instance-discard-plan-20261003.md).
Neither a wire census nor these case counts establish a whole-game percentage.

## 2026-10-03: native27 complete typed-instance discard activated

The preceding native27 gap is now connected to the formal server through
CUSTOM0071 custody, preserving the original27 request and41 clear layouts.
Existing scalar0061 behavior is preserved. Only already-owned complete20
EQU2/TEQ26/WPN1/TWP25/gem8 instances, ordinary sources0..29 and quantity1,
qualified current-world ownership/projection and no active trade/battle may
commit. Exact overlay/scalar CAS and immutable typed receipts preserve other
players, economic state and existing bank/trade history.

Original-machine checks passed419 cases and CTest passed32/32. Actual TW/CN
hidden-desktop run01 passed48 typed commits,24 confirmation cancellations,
4 old scalar MED mutations,2 equipped and2 trade local suppressions, then true
close/relaunch of both clients with full50/full20 verification. Local suppression
is not server-negative acceptance. All six owned PIDs closed and frozen source,
desktop, original client and chat remained intact. Independent release gates
verified the lossless event/receipt chain and actual48 Application commit logs.

Root qualify/stage/apply each ended0; formal candidate f918809a/schema47 is
installed and restarted, with zero changed old saved rows, grants or added
capacity. See [the CUSTOM0071 report](native-owned-instance-discard-20261003.md)
and its postinstall proof. The bounded route is complete; original bind/drop
policy and delayed same-key refill ambiguity remain open. No whole-game packet
percentage is inferred from these scenario counts.

## 2026-10-03: native59 party position query connected

CUSTOM0072 connects actual native roster-row double-click59 to requester-only
native56 with fresh authoritative same-party/same-area/scene positions. Native
name16 remains opaque advisory data. Exact leases, readiness and membership
are rechecked; no party or persisted state is changed. Original cross-map
authorization/failure policy remains OPEN because56 carries no map identity.

Original-machine checks passed26 cases and final CTest passed43/43. The actual
TW/CN hidden-desktop run passed eight UI queries across both sender/leader
directions, cooldown/timeout reset, four chats in both visible/archive rings,
and prior decline/leave/kick/rejoin/disconnect behavior. All four owned test
PIDs closed; protected desktop/processes/client/locale and all SQL rows stayed
unchanged. No rendered-pixel claim is made.

Executable-only qualify/stage/apply and independent postinstall check each
exited0. Formal candidated9be18c9/schema47 is installed and restarted with both
loopback listeners active and no saved-row change. See
[the CUSTOM0072 report](native-party-position-query-20261003.md). Bounded
same-party/same-map query acceptance is100%; whole-game denominator remains
unqualified.

## 2026-10-03: native2F/5C party channel connected

CUSTOM0073 adds the original selector1 party-chat route independently of the
frozen common chat path. It retains all four advisory request header bytes,
uses actual authenticated consenting party ownership and current source/target
leases, converts text for each recipient locale and prefixes the owned sender
name. It prepares/rechecks the audience before publication. Chat itself does
not mutate membership or saved rows; authorized coalesced movement retains
the existing writer and immediate native56 party observer.

Original/current machine checks passed44 cases. The candidate passed46 CTest
cases and two extra actual TCP movement/chat checks. Actual hidden TW/CN run06
passed four prefix and four selected-channel broadcasts, one filter broadcast
(18 recipient deliveries), both native channel1 rings/colorFF00/name prefixes,
unchanged native bubble fields, filter hide/archive/replay, eight59 query
regressions, four common chats and both leadership lifecycle directions.
Native common10/party20 settings were enabled and restored through normal UI.
Failed attempts01..05 are preserved: default filters, incorrect modifier and
hidden-menu input residue were diagnosed and the new harness corrected. No
client byte or frozen common-chat change was made. No pixel claim is made.

Executable-only qualify/stage/apply and independent postinstall check exited0.
Formal candidatea161414a/schema47 is installed with both loopback listeners;
all formal saved rows, config, client and frozen chat remain unchanged. Exact
evidence is in `artifacts/research/native-party-chat-0073/release-gate.json`
and `artifacts/releases/native-party-chat-20261003/deployment/postinstall-root-proof.json`.
The bounded same-map world-party route is100% accepted. Original server
audience/denial policy, cross-map/battle live acceptance, persisted options1D,
private/guild channels and the whole-game denominator remain open.

## 2026-10-03: native2F/5C private and automatic reply connected

CUSTOM0074 adds separate selector2/9 request types before every unrelated
mutation and the frozen common/party dispatch. Recipient authority is the
exact Unicode owned online name in native `$recipient message`; the opaque
caller WORD grants no access. Only sender and target receive mode2/9. Both
owned names remain exact and representable; the native-supported
`Sender: [Recipient] message` summary also supports native dedicated self
filtering. Source/target audience, exact-name lookup and batching are CUSTOM
server policies, not recovered original server rules. Chat writes no SQL.

Original/current machine checks passed152 cases, including native private
producer, consumer, dedicated summary, speaker extraction and Away mode9
nonrecursive behavior. Final unchanged564-source closure passed49 CTest and
two additional accepted party movement/chat checks. Seven actual Application
TCP cases used three independent accounts to check third-party isolation,
bilingual modes2/9, exact/ambiguous names, stale ownership/location, atomic
batch denial, offline/relogin and existing common/party/movement behavior.

Strict hidden TW/CN client run02 passed eight user private sends, one native
Away reply (18 recipient deliveries), prefix/selected producers, both channel2
rings/colorFFFF/no bubble, filter hide/archive/replay, offline and both-direction
relogin, two common and two party regressions. Every Away ring contained
exactly one new correct template row. All five owned test PIDs closed; source,
client, locale, saves and desktop stayed unchanged. Failed run01 is retained:
its final guard observed another naturally ending isolated TCP server; the
strict rerun ran after TCP completion and tightened Away row measurement.
No rendered-pixel acceptance is claimed.

Executable-only qualify/stage/apply and independent postinstall check exited0.
Formal candidate4d2a9ac2/schema47 is installed and restarted with both loopback
listeners. All formal rows/config/client/frozen chat stayed unchanged. Evidence:
`artifacts/research/native-private-chat-0074/implementation-report.json`,
`artifacts/research/native-private-chat-0074/release-gate.json` and
`artifacts/releases/native-private-chat-20261003/deployment/postinstall-root-proof.json`.
Bounded same-map world-private acceptance is100%. Original server policies,
folded/translated name aliases, offline mail, cross-map/battle live acceptance,
live dedicated-view activation, guild channels and the whole-game denominator
remain OPEN. These limits do not count as native restoration or full-game completion.


## CUSTOM-0075 native guild chat (2026-10-03)

Connected typed C2S2F mode3 to a fresh owned persistent guild audience and native
S2C5C mode3 display. Native2D fixed17 projects the owned guild name, including
clearing on maintenance removal. Names/member ids come from new independent
schema48 storage, never from the native caller WORD or client-side string.
Administrator-configured membership policy is CUSTOM; no original guild cost,
NPC/context, rank, building or management rule has been silently invented.

Acceptance:252 original/current chat machine cases;84 additional guild-operation
probes (research only);53 CTest cases and2 additional accepted party TCP cases;
6 actual TCP guild cases;8 hidden original TW/CN UI sends/16 owned deliveries,
selected/prefix input,visible/archive/filter replay,no bubble,remove/restore and
relogin;common2/party2/private2 live regressions. Source/client/save guards pass.
Formal server installed schema48 with both new tables empty and all existing
typed save rows unchanged. Report:artifacts/research/native-guild-chat-0075/
implementation-report.json. Current client pixel rendering is not claimed.

Open: native8D/6F create/join NPC/context authority,29 guild pagination,
8E/91/92 header/roster/building logic,71/72/73/75 management, original economics,
cross-map live UI. Those packets are not counted as completed by84 probes.
The global gameplay denominator remains unknown; this round completes the
administrator-configured guild-chat acceptance scope only.


## CUSTOM-0076 guild roster reader and native lifecycle (2026-10-03)

New complete read-only SQLite guild roster snapshot includes offline members,
account ownership, exact name encoding/profile and optional saved role state.
It detects rename, role and deletion changes without assuming guild revision
was advanced.4 CTest cases pass, including72 new storage assertions; no schema
or formal database mutation and no new Application route yet.

Correction to the0075 research lead: negative-WORD C2S29 is an already-open
guild tower interaction, not roster pagination. Native roster controls use
local twenty-row pages. Native91 logical22 upserts21-byte records with capacity
50; at full capacity even an existing-slot update is ignored. Native92 logical2
removes a slot; removing self takes a reset/close path.26 original/current
machine lifecycle cases passed. Earlier hardcoded count metadata was replaced
by counted108 native upsert entries in lifecycle-v02; no server rule is inferred.

OPEN: trace initial NPC/knowledge37->8E producer/context, full8E header authority,
owned rank fields, recipient name collisions and full-capacity refresh protocol;
then integrate native91/92 runtime and original TW/CN UI acceptance. Existing
formal CUSTOM0075 remains installed. Live roster acceptance0%; global gameplay
denominator remains unmeasured. Report:artifacts/research/native-guild-roster-0076/
implementation-report.json.


## CUSTOM-0076 runtime cache integration (2026-10-03)

Supersedes the earlier reader-only activation, preserving its immutable report.
Formal schema48 remains unchanged. NativeS2C91/92 andC2SB800 now connect to
Application and complete owned snapshots.9 CTests,40 service checks,72 reader
checks,24 actual C++-output/native-consumer cases and3 actualTCP cases pass.
The latter preserve B8 coalesced common/party/private/guild routes and verify
level updates, removal/restore and malformed-batch source disconnect.

OriginalTW/CN hidden-desktop clients accepted5/5 cache observations:50 members
(including48 offlinefixtures),remove0,restore50,relogin50. Every row's exact name,
saved level,class/sex index and selfslot0 was checked. Existing common2/party2/
private2/guild8 sends with16 guild deliveries pass. No screenshots, foreground
use, packet injection, client change or formal fixture grants; all5 test PIDs
closed, all SQL rows preserved. Cache-scope100%; rendered panel acceptance0%.

Correction: native551DE0 is ASCII bytewise case-insensitive in qualified default
CRT state, not exact-case strcmp. Projection now rejects those collisions while
leaving stored/auth names unchanged.50-member refresh removes others before
upserts;92 remains slot removal, never page termination.

Initial8E producer/NPC binding and original rank/economics remain OPEN. All-zero
8E would invent visible numerical metadata, so it is not sent. Missing saved
role/unrepresentable/colliding name or over50 count withholds the entire new
projection and logs unavailable; a prior cache can remain. Same-process role
return/switch requires further native reset qualification. Wholegame percentage
remains unmeasured. See native-guild-roster-0076/implementation-runtime-report.json.
