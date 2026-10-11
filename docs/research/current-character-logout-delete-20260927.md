# Current character logout and deletion

## Evidence and identity

Current client SHA256 `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
Mapped image SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`,
base `400000`, RVA equals the mapped-image file offset. The owned hidden-desktop
harness checks current process code against this image using VM_READ. The lab
client is the already-qualified port-only copy; live client binaries and original
accounts remain untouched.

## Qualified character pose, explicitly not logout

The original ToolMenu HUD control8 opens the menu; category control24 selects
category2 (UI+A3CF4=24). Control28 executes `4A6BA2`, which posts the original
window message402/1. `40E86F ->465EF0 ->503820` maps this to pose1. `503820`
calls `497E00`, which queues C2S66 with three payload bytes:

* payload0: zero for this producer;
* payload1: `(pose_mode << 3) | local_direction`, direction occupies the low3 bits;
* payload2: opaque producer stack tail, never an authorization field.

Modes1/2/3 select native animation16/17/18. They do not cause logout.
Native `497E00` and `497E70` both call `4132E0`
with payload length3. General pose propagation remains OPEN.

The receive reply is **S2C77**, logical length7, wire length10:
`77 id_lo id_hi effect packed_pose flags tail`. The actual dispatcher at
`468B61` uses table `46B5D4`; entry77 points to `469BBA`, and ordinary flags
bit3 clear plus matching local ID calls `501610`. The length table at `401324`
entry77 points to `4012CA`, which returns7.

The earlier tentative S2C67 interpretation was disproved: that dispatcher entry
goes to the default `46B517`. It must not be sent as a logout acknowledgment.

`50169C` sets World+30 to16/17/18 then updates direction. UI06 proves native
local ID4, World+30 0->16 and pose4->12 after66 `00 0C 00` and77 reply.
The previous inference that these states were logout was disproved: `502210`
uses them for character animation. Outer world loop4655E0 exits after GUI
requests. Earlier runs02..06 do not qualify functional logout.

`current_character_pose_20260927.py` runs the unchanged `501610` body for all
24 mode/direction pairs. Its explicit boundary adapter records/returns the
`503860` direction/renderer call. Artifact
`artifacts/research/native-character-pose-20260927.json` proves the state writes;
it is labeled native consumer arithmetic only, not live gameplay acceptance.

## Native logout chain

Actual logout is HUD control9 (`4B1987 ->4F5E50`), which opens settings
UI+232DC2. Control3 (`4F622D`) selects character logout and sets UI+86870=0;
`4F6080` opens confirmation UI+232E58. Its control2 (`4F619B`) returns2,
`482972` returns GUI request -9 and `466BEF` returns inner result1. World-loop
table `465A14[1] ->4659A0` returns2 to the outer application; `40E17C` sets
login mode1 then `415730` sends **C2S02/01**. Settings control2 instead sets
UI+86870=1, confirmation returns1, and the outer application ultimately ends.
It must not be used to qualify character logout. Other native outer paths at
`40E18D`/`40E249` emit02/02 and02/00; reason alone does not prove destination.
`415180` waits for S2C03 under `415BD0(30000)`. Session queues logical03/00/00
and drains it before closing. Normal disconnect cleanup releases the world lease.

## Native deletion chain

Selection control9 enters the native deletion panel. Its controls1/2/3 hold the
typed character-name confirmation/account/password. Native deletion action4
is reached by widget5 input-button7 (bounds432,358..511,395), not its decorative
graphic node4's extended bounds. Native
`409185` compares typed confirmation with the selected name locally.
`40C210 ->4152E0` queues C2S19, payload53/logical54/wire57:

* payload0..15: account string;
* payload16..31: password string;
* payload32: native owned slot token;
* payload33: language marker4;
* payload34..36: unwritten padding;
* payload37..52: selected character name.

Authentication is revalidated against the session's bound account, with account
registration disabled. Owned slot/name are checked and active world characters
cannot be deleted. The repository rechecks owner/name in BEGIN IMMEDIATE.
It walks the recovered-character foreign-key graph, removes character-owned
descendants (including composite inventory/deity and runtime quest tables), and
removes battle descendants before reservations. Deferred foreign-key validation
and transaction rollback prevent partial deletion. Accounts, siblings, foreign
owners, and unrelated legacy character tables remain outside the operation.

Native `415475` consumes S2C02/result WORD zero (logical23/wire26).
`40C251` shifts the local selection array and decrements count only after that
success. `405A67` then sends C2S02/04 and waits for03 before reconnect/list
refresh. CharacterReady now handles that exact terminal request too.

## Server integration and qualification

Protocol and runtime paths: `RecoveredCharacterDelete.h`,
`RecoveredCharacterPose.h`, `RecoveredWorldRecords.h`, `Session.cpp`,
`RecoveredWorldService.cpp`, the Application owned-deletion callback, and
`SqliteRecoveredCharacterRepository::erase_owned`.

Tests cover malformed66 frames, opaque-tail preservation, exact77 pose replies,
owned identity bounds, battle/selection rejection, wrong deletion owner/name,
deferred commit failure rollback, descendants, siblings, accounts, and slot reuse.
The deletion rollback test compares against the settled resource revision: battle
settlement itself legitimately advances it before the deletion attempt.

Server integration and current-client functional acceptance passed UI13.
Earlier runs02..06 are failed logout tests with normal cleanup/source preservation;
UI06 qualifies pose synchronization only. Neither66 admission nor77 pose qualifies logout.

Run04 exposed the existing native session convention: the exact world-ready
tail marks `recovered_world_ready()` while state remains `CharacterSelected`.
The pose reply now accepts this established lease as well as `InWorld`, within
the existing authenticated standalone gate. Battle and unready selection still
reject. Its regression acquires the lease through a real socket handshake.
Run04 terminated normally and preserved all source hashes/nonfixture rows;
it is a failed live test, not functional acceptance.

## Current-client acceptance, UI13

Receipt: `artifacts/playtests/private-logout-delete-20260927-13/run-result.json`.
Candidate before/after SHA256:
`4d9ac6a4830e3f31f8637c89ae07359e51b31cf7fa6a6a45a1153164c07b9aaf`.
Runner exit0; accepted=true;14 current-process code ranges match the mapped image.

The native role-logout confirmation sent02/01 and received03 without the30s
timeout. Its fresh login/server menu returned in1.922s. The native server
confirmation then fetched an account-owned role list in2.828s total, including
the additional server-choice clicks. Automatic direct return to the same
server's role list is not claimed. Static follow-up below explains its preserved
server selection and confirmation step.

Deletion committed only fixture character4 in the isolated cloned database.
The native client reauthenticated/reconnected, fetched a fresh empty07 list,
and reached state21/count0 in1.203s. Native `4056B9..4056CC` opens creation21
when no role remains; an empty list does not remain in selection19.
SQLite fixture character4 count is0 and foreign_key_check is empty.
Every nonfixture table row hash, source DB and original/lab client hashes stayed
unchanged. The owned client, runner and candidate server closed, and the visible
desktop stayed unchanged. No production process or account was changed.

Regression results supplied by the integrating lane: world service, repository,
movement/active lease, door/config all pass; updated session_state passes97.73s,
including native02 reasons0/1/2 ACK/close through a real world-ready session.

## Last-server behavior after role logout

Outer `40E17C` chooses login mode1. Native `404DA0` mode1 branch
`404E37..404EC4` waits03, closes the prior login connection, sleeps1000ms,
copies saved credentials and calls `40BA60` to authenticate again. Its normal
login continuation `4053F3 ->407A10` builds the menu and assigns state17.
`407A10` passes saved server fields8F4/B40 to `407440` to select the prior entry.
It does not submit that choice. `407A70` moves to state18 after confirmation;
the client then sends post-server-select and receives a fresh account role list.
UI13 observes this exact sequence. The preserved selection requires its native
confirmation; there is no evidence here of a missing server-reply field causing
the former30s delay, and no forced state change or guessed auto-route was added.
