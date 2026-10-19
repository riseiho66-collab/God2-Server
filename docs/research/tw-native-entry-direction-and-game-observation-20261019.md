# Taiwan entry direction and actual game observation, round485

The real first-entry direction source is now connected to the existing HMD
movement supplier. It reads this Session's actual qualified Written2A and
original common lease/saved pose, instead of requiring a fabricated direction
callback. Both HostPlan source families can explicitly select it. The generic
genuine dynamic PoseSource path remains available; default Main is not enabled.
This implements the original-entry branch, not the whole pose lifecycle.

## Native direction chain

REA/Ghidra statically decompiled nine procedures in four successful batches.
An initial interior-address lookup465194 failed and is retained; seeding the
known actual function entry464910 resolved it. This is not native code absence.
All five targets closed. Analysis-only seed callers are not original callers.
All13 original PE sections and their headers/mappings match the current EXE:
aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48.
Full raw results, assembly, failures and close receipts: C:/Users/risei/.codex/artifact-archives/god2-server/20261019/entry-direction-round485.

464910's normal successful branch calls468160 at465194. Afterward46536A writes
world+2C=0, but that is not the final direction. At465435 the same world calls
500180 with R=world+1539683C. In500180,50021B loads DWORD[R+24] and50021E
writes it to world+2C. The earlier46874F..4687A8 switch mapped full2A bodyB4
low3 bits to R+24 as0->7,1->0,...7->6. Thus the entry projection is
((B4 & 7) + 7) & 7.502700's previously proved stationary-step path reads
world+2C and its actual step writes computed0..7 there;502210 uses that field
with the action/frame field. R+FC and movement cursor+236 are not substituted
for direction. The recovered client projection does not choose the server's
original B4 value or prove the remote client actually ran this branch.

The readonly entry view exposes only this projection. The server first-entry
pose supplier requires the exact real INIT, full account/character/Session/Lease,
original geometry, current original physical-entry battle phase and real saved
prefix. NormalWorldInitialization::original_entry_battle_phase compares the
actual effective battle epoch with its physical Entry epoch, without inventing
a numerical first-battle value. A post-battle reused entry is not first entry.
A real later physical entry can qualify independently.

New supply refuses after any saved-position revision/geometry advancement or
post-battle initialization reuse. Its held Current is an immutable retained
entry witness, not a live saved-position reader: a retained old witness alone
does not attest that durable pose stayed unchanged. The supplier and actual
ResourceOwner still perform their existing canonical saved-pose checks. After
installation, actual movement owns direction updates; provider Current does not
freeze ordinary walking to the initial direction. Dynamic resupply after walking,
resource replacement, battle return and transfer still needs its real owner.

## Actual source integration corrections

The old normal_world_initialization getter requires world-records callback TLS.
Using it from the movement factory could throw; the earlier direct regression
source also used that invalid context. The new readonly on_game getter loads
the real private immutable receipt and invokes existing current_on_game, whose
physical Entry game-thread check precedes mutable Session fields. HMD reads use
it. It sets no TLS and grants no response/input/output callback custody. The
original TLS getter and all existing write/callback guards are unchanged.

HMD provider Current previously called ready_lease, which reaches ready/current
and the repository. This corrects earlier overly broad no-SQL claims: provider
Current now checks retained_ready_current only. Actual supply retains full root/
saved observations. No configuration SQL is added per input. Existing real
ResourceOwner/authority/CAS guards remain; a retained asset witness is not a
standalone durable-root permission.

## Actual HMD selection

500180 takes entry kind into world+22C. Kind2 selects46C5A0 ->448300 ->437900
HMD; the other branch uses46C520 ->444B80. The HMD supplier now requires actual
entry kind2 rather than pretending another native loader is the same resource.
46C620 ->444F70 publishes CAN. The retained CAN consists of an8-byte CAN v1.0
header,4-byte file count,64-byte records,4-byte scene count and2-byte indices.
The native loader also has a same-filename cached-success branch; server whole
publication remains explicit and digest-validated. Native assertion/error paths
and raw field sizes are not general gameplay caps or full-load health proofs.

The actual kind2 caller uses the selected CAN row reference at+1; this bounded
path does not use byte0 as the HMD discriminator. The optional configured tag
is now an additional operator assertion, not a compulsory invented tag rule.
Full row bytes remain retained. Other CAN consumers/tag meanings remain open.
55AAAA copies the CString data pointer and increments its reference count when
shareable, or calls the existing string assignment path for negative counts;
this also closes the prior selected-manager getter copy helper. No string or
resource function was executed. Root/manager lifetime and alternate paths remain
separate from the server's explicit CUSTOM-0158 root and cache policy.

## Verification and remaining work

Regression SOURCE covers all8 direction selectors, actual Session -> original
pose supplier -> HMD bundle -> real Host installation for0->7 and1->0, six
entry kind/actor/geometry disagreements, optional tag absence, saved-prefix
advancement, battle refusal, preserved old TLS restriction, wrong-thread readonly
refusal and SQLite trace assertions around held Current with a positive control.
These tests were not run. The existing suite remains registered. Genuine
post-battle INIT success and MovementOnly runtime acceptance are not claimed.

Main still needs complete full2A/Entered/initial population sources. Outdoor MDL,
complete dynamic pose/transfer integration, other gameplay/formulas and current
original-client own-server acceptance remain open. No build, test, native/game/
Lua/codec execution, game SQL, migration, import/export execution, activation or
deployment occurred. The one formal packet report is static; complete gameplay
route credit remains0 and the whole-game denominator/percentage remain unknown.

## Owner three-channel addition during this round

The owner now requires exactly three selectable native channels after server
selection, with switching. AGENTS and GOAL_ACCEPTANCE retain that requirement.
CUSTOM-0159 adds the full three-endpoint04/05/06 producer and registered source
regressions using physical native table replay, not three labels over one world.
Existing one-channel bytes stay exact. Current Application still hosts one G
listener and one world: this source component is not completed channel gameplay.
See THREE_CHANNEL_PLAN_20261019.md for the actual owner/isolation/handoff work.
The process-global connection allocator already prevents per-listener ID
collisions; per-world presence alone does not exclude cross-channel duplicate
characters. All G listeners must share the real L-issued handoff lineage.

REA continued on the current original EXE for the actual login/UI/selection
roots; see tw-native-three-channel-selection-20261019.md and its retained raw
evidence. No native function, resource codec or client was executed.
