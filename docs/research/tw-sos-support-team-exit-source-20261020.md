# Current TW SOS, team and party exit source separation

2026-10-20, PHASE1 source/static only. No build, tests, client/native/VM,
codec execution, game database SQL, schema install, migration or deployment.

## Qualified native wire

Current disk SHA256 is
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`.
REA Ghidra used separate nonexecuted analyst seed PEs; all13 original PE
sections were byte-identical to that target. Synthetic seed calls are not
original callers. Initial unseeded failures remain in evidence.

`41A860` registers26 cursor entries from585A48. Current PE pointer/string
reads independently verify mode5 `team.ani`, mode6 `support.ani` and mode10
`watch.ani`. These are three different original inputs:

| Native input | Qualified chain | C2S logical contract |
| --- | --- | --- |
| Team cursor5 |4835A0→selection4→481F70 action-10→465FA0:4660DC→497170|57, whole target DWORD;5 bytes; formal self argument ignored|
| Support cursor6 |4835A0→selection5→481F70 action-11→465FA0:466057→497140|6A, self DWORD, target DWORD;9 bytes|
| Watch cursor10 |4835A0→selection10→481F70 action-17→465FA0:466274→497D40|6E spectator mode1; not support admission|
| SOS battle action8 |512790→5156E0→518E50|35, actor,8,side,opaque4,self-target masks,context DWORD,requested DWORD;17 bytes|

For action8,518E50 clears the14-byte target scratch, obtains the same
controlled actor again and forces one target. Its final DWORD is the
boolean `(B+488==0)`, also stored at B+48C. Actor and side select the current
primary/secondary producer path; they do not grant the submitted actor.
The17-byte codec preserves context and opaque4 and limits the actual native
producer subset, including actor0..14, side0/1, self mask and requested0/1.
The native actor14 producer bound is not proof that such a slot is present.

S2C83/action8 is a separate15-byte result:516AE0 updates B+488 only for
acting side0, using logical WORD9 zero/nonzero. It is not C35's final DWORD
and cannot be substituted for HP or late admission permission.52C520 forwards
the action to the actor presentation path. Original server admission rules,
turn ordering, expiry and causal C35→83 success semantics remain unknown.

S2C6A is another direction and only5 logical bytes. Current table46B77C
selects46AC6C; length4014CC points to4012AC(return5). Two WORDs bothFFFF call
47C900, which changes guarded UI state, calls47DAF0/507B20/498A60. Other
values pass471310 and choose text from the second WORD before type0
484710 dialog. This branch neither installs battle participants nor proves
request acceptance. It must not be invented as a success ACK.

## Self leave and selected member removal share C5A

4971B0 takes no target argument. It copies own PlayerData WORD and name+B7
to C5A/body18. The separate original selected-member path is complete:
4EA530 selects a bounded native party row, copies its WORD to UI+AFEEC and
name to AFEEE, then calls4EF560(name).4EF560 opens dialog type0x11;
483C80 case0x11 calls4EA510.4EA510 queues C5A/body18 directly from AFEEC.
Thus C5A has target WORD/name16 and can name self or a selected member.
Post-NUL name residue remains raw display context, never an identity grant.

The raw483910 seed began before a proven procedure boundary and produced
an implausible prefix write; no complete original toolbar handler claim is
based on that candidate.4971B0,4EA530,4EF560,483C80 and4EA510 provide the
qualified argument/data/queue chain independently.

## Source correction and actual integration boundary

Previously `RecoveredParty` decoded C6A as Join, C57 as Kick and every C5A
as self Leave. Native cursor/source evidence contradicts those unconditional
wire labels. Dedicated `RecoveredSosSupportRequest`,
`RecoveredTeamRequest57`, `RecoveredPartyExitRequest5A` and
`RecoveredSosBattleCommand` now retain the separate full raw contracts.
All four alternatives append to WorldRecords; existing alternative indices
remain unchanged. World batch structural validation still precedes dispatch.

`RecoveredParty` retains C58 answer wire only. Its Join/Kick/Leave values
remain trusted INTERNAL CUSTOM-0062 operations used by the existing party
directory/model; their old misleading native encoders now throw. NativeParty
membership, leader-only removal, leave/disconnect behavior and policy do not
change here. Application owns the actual routing separately:

- C57: authenticated actual sender identity plus whole target DWORD enters
  the existing explicitly CUSTOM consenting Join policy, not a native kick.
- C5A: target equal to actual sender selects internal Leave; nonself target
  selects internal Kick only through actual current group/leader checks.
- C6A and C35/action8 require the actual shared SOS room owner. Passing them
  back to party Join, spectator6E or returning empty success is not admission.

These source corrections and the corresponding visitor/test updates do not
implement a shared multiplayer encounter, late joins, pets or settlement.
Application routing is integrated separately by the root. The author also
owns the bounded party publication fix described below; final integration
still requires the root's independent review.

## Actual PvE owner audit and next implementation units

Application's actual `diagnostic_combat->bind` is in the guarded diagnostic
bootstrap; it is not a general multiplayer PvE entry owner.
RecoveredBattleService::Bound owns one Battle, one Session policy and one
checkpoint callback per Session. Creating another independent binding copies
combat state rather than joining the first battle. The saved diagnostic
checkpoint source additionally requires exactly one controlled actor and
CUSTOM-0012 reservation ownership. The existing PK repository/entry/return
sources intentionally require two viewers and private paired capabilities.
None of these can safely be relabelled as multi-owner SOS.

The implementation split remains concrete but NOT yet implemented:

1. `OwnedSosRoomState`: one canonical checkpoint/RNG/revision, exact live
   member incarnations, player/pet slot ownership, grant epochs and support
   state. Late admission stages from the current checkpoint, retaining dead
   enemies and all prior HP/MP/status. It cannot replay the initial snapshot.
2. `SqliteOwnedSosRoomRepository`: independent typed room/member/slot/outbox
   source, same-connection transaction CAS over room/checkpoint and every
   participating character/pet/resource revision. It must not reuse the
   two-member PK schema or single-character diagnostic reservation.
3. `OwnedSosBattleAdmission`/publication: actual Session private entry/current/
   Written capabilities for each joining member; build-qualified player and
   pet material, current dead/alive roster,82/1C/appearance/vitals and separate
   primary/secondary86/5 grants. Only current living owned actors may command.
4. `OwnedSosReturn`: per-member accepted terminal context, durable full-room
   final resource save and genuine current world return. Initiator departure
   cannot delete everyone else's room. Recovery/timeout/failed fanout must
   retain durable claims; a committed save cannot be called rolled back.

Native517590 independently handles flag bit0/low nibble primary and bit1/high
nibble secondary. Existing `RecoveredBattlePlayerGrant` is explicitly the
two-player owner-slot0 subset, not a complete pet grant source. The original
server rules for admitting helpers, rewards, costs, timeout or initiator death
cannot be recovered merely from these client stores. New policy, if adopted,
must be separately labelled CUSTOM and attached to the actual room owner.

Existing two-member terminal saving was checked: RoomState owns written bytes,
Operation defers callback-time erase, the repository updates both exact
resource rows and the terminal ledger in one transaction, and disconnect
retains recovery custody. No new proven leader-departure/multiplayer-save
defect was fabricated in a system that has no such owner yet. A separate
legacy party callback cut issue was reported to root: fresh Session IDs are
read between multiple SQL queries and stale staged membership can overwrite
callback-time retirement without a final model/owner fence.

## Party observation and publication correction

The proven source defect above is corrected in Application's actual party
observer, projection, membership request, movement refresh and disconnect
entries. `party_source` owns a strong Session, fixed account/character,
phase, battle generation, readiness, language, pending transfer flags,
registry incarnation, pure GAME movement pose and any actual normal-entry
initialization. Every saved position/profile/role/resources query uses the
captured IDs and is followed by the same pure source check. The position
query reads an owned saved value directly and compares the pure movement
snapshot, preserving an unsaved initial spawn's revision-zero semantics.
It does not borrow a movement map iterator across SQL callbacks.

`OwnedPartyPublicationGuard` retains every earlier peer witness until the
final source cut. Each actual native party model writer uses its Scope;
nested entry poisons its parent and every model publication advances a
monotonic epoch even when the values are equal. Registry rebind/erase and
host stop invalidate older candidates. The C91 directory/party two-model
publication uses the existing callback-free directory memory CAS inside
the same final cut. This does not add a new party rule or change the
existing CUSTOM-0062 consent, group limit or leader departure policy.
A separate source-incarnation epoch advances on ready/registry retirement,
not on an ordinary model publication. Scope-free observers can reject an
identical-value rebind without invalidating their own successful delivery.

Disconnect first commits exact-incarnation transient retirement, then
projects the departure. Projection/delivery failure cannot restore the
retired model. Stop invalidates sources while still permitting subsequent
disconnect cleanup. Delivery rechecks the retained witnesses before each
recipient, so a callback-time replacement cannot receive an older roster.
These are source corrections, not proof of native transport acceptance.
The related C59 readonly query, both party-chat prepare paths and directory
watcher readsets also retain the complete Scope through the last observer
and final publication/send. Mixed party chat plus movement discards the
earlier readset before movement and obtains a fresh readset afterward.
Directory observation retains full common IDs and exact pure pose witnesses;
it does not impose the membership actor-handle subset on discovery.

The SOS actor bound is separately grounded in the complete current target
`518E50`: its initial predicate returns before queuing if `param_2 > 0x0e`
or `param_3 > 0x0e`. Action8 subsequently forces one mask element from the
same `5156E0` selected actor. Although `5156E0` can expose a larger raw
primary/secondary byte, that does not bypass this producer's first bound.
The self mask therefore preserves actors0..14 (actor14 is high WORD bit0);
it is not borrowed from the old BasicAttack grammar. Build pin and evidence
`sos-producers-v1.json` / `sos-external-support-producer-v3.json` remain
required qualifications; actor ownership and current native grants are
still separate actual-room obligations, not granted by this codec.

## Evidence and review

External evidence root:
`C:/Users/risei/.codex/artifact-archives/god2-server/20261020/discord-bank-sos-formation-pass3/sos/`.
Key retained files: `sos-support-world-menu-v2.json`,
`sos-external-support-producer-v3.json`, `sos-result-response-grant-v6.json`,
`sos-s2c6a-success-and-dialog-v7.json`,
`sos-team-leave-actual-producers-v10.json`,
`sos-team-kick-confirmation-v12.json`,
`sos-team-kick-wire-assembly-v12.json`,
`sos-current-cursor-team-support-watch-v13.json`, and all seed provenance /
session close receipts. No earlier failed query is overwritten.

Regression SOURCE is added to existing `tests/test_native_party.cpp`: exact
full widths/raw tails, separated variants, malformed whole-batch suffix,
support+tick ordering, SOS self masks/primary-secondary bytes and requested
flag. Existing `test_recovered_world_records.cpp::reconstruct` receives four
matching encode visitor branches. No compiler or test was run; these are not
native acceptance or a claim that every pre-existing stale test is fixed.
