# Three-channel common-world custody, round486

Previous goal turn was progress: commit62834fa added the native three-channel
advertisement and current-EXE UI evidence. This round implements the shared
character occupation owner and three independent common-world containers.
This is concrete source progress, not three-channel playable acceptance.

## World ownership source integration

CUSTOM-0159 SharedTaiwanChannelWorlds creates exactly three SharedWorldHost
instances on one game thread and one RecoveredCharacterRepository. Each owns
a separate presence, actor visibility and native transport registry. Actor
handles may repeat between channels. No account-wide exclusion is imposed:
different owned characters and the actual L/G authentication flow remain valid.
The three hosts share one SharedChannelCharacterOwnership instance, which
excludes full64-bit character IDs and physical connection IDs across them.

SharedWorldPresence acquires a private world/Session/account/character/epoch
claim before virtual root or saved-position qualification. Rejection, exception
or caught nested preparation releases only that exact pending claim. Successful
entry retains it through active presence until the actual Presence release.
InitialPopulation retirement alone still does not release occupation. Existing
world lifecycle cleanup order is unchanged: scene cancellation, transport and
visibility retirement precede Presence release. No repository query is needed
to release a character whose stored root has already been removed.

The shared registry stages immutable map structures before publication and
rechecks the exact prior registry/world after allocation. Retirement only marks
private flags without allocation, callbacks or SQL; later candidates prune old
entries. Old population copies do not keep retired claims current or evict a
replacement registry at the same channel ordinal. The local Presence stages a
detached std::map node and transfers it only after final pure qualification;
there is no allocation between that final cut and publication.

Local population snapshots retain their own epochs and complete claim set.
Unrelated-channel activity does not invalidate a local population solely by
changing a global serial. Plain activation now refinds its exact entry after
virtual repository reads. Current, ready and saved-position reads recheck
retained custody afterward. Movement commit owns copies of both input values
and refences the exact ready claim before invoking the existing position CAS.
The actual SQLite CAS remains synchronous; an arbitrary repository override
that mutates inside commit_position is not made transactional by this registry.

The private scalar registry is not Session-pointer authentication, native wire
authority, a save receipt or a switch permission. Actual Session pointer and
full tuple qualification remain in the existing SharedTaiwanWorldLifecycle.
Process-wide connection IDs already never wrap or reuse. Default standalone
SharedWorldHost/Presence construction keeps a private world0 owner; unrelated
defaults do not silently join this collection. Application must explicitly
select the one collection and isolate every per-channel gameplay controller.

## Current original-client logout and reselection

REA/Ghidra current God2.exe SHA256:
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`.
All addresses here are VAs. Four opened targets closed; the negative containing
queries are retained. All13 original PE sections remain byte-identical in the
analysis-only seed images. Synthetic seed callers are not original call sites.

HUD4B1900 WORD control9 calls4F5E50. Settings4F6200 BYTE event mask01,
WORD control3 writes DWORD UI+86870=0; control2 writes1. Confirmation4F6140
control2 returns AL=2-(UI+86870!=0). Role logout returns2, application exit1.
The actual GUI function4820A0 maps AL2 to result-9.466B00 maps-9 through
cleanup to result1;467860 calls it at467A63. The original465A14[1] branch
targets4659A0 and returns world result2.40DE80 then sets login mode1 at
40E17C and calls415730(2,1,1).

415730 sends C2S02 plus one BYTE reason1, flushes and waits through415180.
The latter has a30000ms timeout, consumes S2C03, clears G+2CB8 and sets
G+2CB9. It does not inspect03 body. Prior round485 current-client evidence
then proves mode1 reauthentication and native group/subgroup UI reselection,
preserving WORD Main+8F4/B40 as initial selections. This is a recovered
logout/reselection route, not an invented direct channel-switch packet.

Native evidence IDs and raw outputs are retained under
C:/Users/risei/.codex/artifact-archives/god2-server/20261019/three-channel-ownership-round486/native-switch.
The exact summary is native-switch-findings-v2.json, SHA256
`f68d86475ed712dba7665e6a34d4a7c26c3f70c443e44a9b4c1b474a59429aba`.
4655E0 pseudocode stopped at an indirect table; it is not complete world-loop
decompilation. True containing functions4820A0/466B00 were resolved only after
following467860. UI+232DE4 ->483B00 -> GUI-26 remains the next native trace;
its semantics are not relabelled as channel switching.

Existing Session G02/reason0..2 queues03/0000 then closes. This matches the
bounded ACK format but does not prove durable save, game cleanup or character
custody release. Complete source retirement, save and target admission must be
joined before treating reselection as a successful cross-channel handoff.

## Source regressions and remaining work

The registered C++ source fixture uses actual three-world containers and an
in-memory repository with full64-bit IDs. It covers pending/active exclusion,
all six directed collision pairs, same-account distinct characters, repeated
local handles, isolated populations/transports, exact stale cleanup, observer
failure/reentry, rollback, invalid constructors/thread access, private default
hosts and retired-world population tokens. A late position observer can replace
the source in another channel; obsolete movement refuses before calling CAS.
No allocator failure injection, positive durable CAS, native Session login or
playable switching is claimed by that fixture. It has not been executed.

Application still hosts one G listener and one selected common world. Three
real listeners, client configuration slots, channel-specific gameplay owners,
shared issued-list lineage and durable logout/handoff integration remain open.
Builds, tests, product/native/VM/Lua/codec execution, game SQL, schema/migration,
import/export execution, activation and deployment remain unperformed in PHASE1.
The formal report is static; no full gameplay route credit is added and the
whole-game denominator/percentage remain unknown. The goal stays active.
