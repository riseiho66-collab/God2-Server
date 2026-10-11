# TW259: client options notification and full-WORD feedback

Phase1 source connection only. No compiler, build, tests, gameplay/native/VM or
codec execution, game database/SQL execution, migration, activation or deployment.
Prior TW258 and stopped TW259 preliminary evidence remain immutable.

## Native scope

The current Taiwan image is pinned to
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
At 4F4F5B the client toggles bit0200 in PlayerData+449C, a WORD. The set branch
passes BYTE7 and the clear branch BYTE8 through 4D6BA0 to C2S B1. Other B1
values are separate, unqualified variants. C2S B1 logical2 is not a target ID.

C2S1D is a separate notification from 497D80 with the full two bytes supplied
by the caller. 4F4CFB toggles bit1 before passing the actual449C address. Keep
all sixteen bits and direction separate from the unrelated S2C1D record.

S2C1B has an independent length leaf at4012DC returning logical3. World
dispatch46AE4D skips the opcode and calls4F5030; 4F5041 reads the payload WORD
and4F5046 writes it to the same449C. The consumer also reads an existing
adjacent449E BYTE during refresh; it is not another byte in this packet.
The refresh implementation remains opaque. S2C2C RoleAuxiliary logical61 and
role/vitals snapshots do not establish a449C supplier.

## Source policy and unresolved scope

CUSTOM-0100 explicitly qualifies server retention and S1B feedback from an
actual authenticated, current client C1D notification. This native wire evidence
does not prove the original server paired C1D or B1 with S1B. No initial0,
saved options, reconnect persistence, or original server permission is inferred.
Only an already supplied full WORD can support B1 bit0200 changes; the other
bits must be retained exactly. Options are display preferences, not authority
to alter permissions, game rules, chat/filter/IME/fonts or text conversion.

Eight C++ files supply the actual opt-in: six existing Application, Config,
Session and parser files plus TaiwanNativeClientOptions and OwnedClientOptions.
`world.owned_client_options.enabled` defaults off; configuration requires actual
dual-connection authentication and world entry, excluding mock login. Disabled
mode preserves the existing standalone C1D transport-only source. Enabled mode
adds only B1 selectors7/8 to the parser; other B1 values remain unsupported.

The transient copy-on-write map retains a full WORD and checked uint64 preference
revision, exact weak Session, full Session/account/character IDs and actual
private initialization. The final TW wrapper strongly holds the real Session
and checks its private written/current entry on the recorded game owner before
reading game-owned fields. Pure owner/phase/battle/closing/ready fences and the
expected map snapshot must still match after reply framing and allocation.
This revision belongs to preferences; it does not assert a role/database revision.

Ready only marks existing same-owner state for replay: the actual ready callback
runs before normal-entry publication. A later successful original handler run,
including Tick, obtains the genuine current written entry and can return S1B.
C1D can instead supply a fresh full WORD; no replay or B1 may create an unknown
baseline. Disconnect retires only the exact incarnation. No options table,
database write or cross-session persistence was introduced.

The final wrapper preserves each contiguous unrelated original run and its
already framed reply order. S1B framing/allocation occurs before preference
publication, but eventual ordinary IO submission is neither Written nor ACK.
A mutation earlier in a mixed batch is not rolled back if a later original run
fails; output already submitted elsewhere cannot be treated as untouched.
Copy-on-write retirement can fail allocation and leave an exact stale entry
occupying bounded capacity. Wrong-owner/old-incarnation entries fail closed and
are not rebound; capacity can prevent a new seed. Post-battle private entry
renewal remains an unavailable variant. These limits are not full lifecycle
completion, delivery atomicity or proof of official settings behavior.

Static evidence contains24 bounded spans,705 summed bytes/679 union bytes and
204 instruction sites; overlapping sums are not new global native coverage.
Source accounting keeps the three settings request variants and one deferred
restoration branch separate from gameplay C2S counts. Whole TW directional/
state/variant denominator and completion percentage remain unknown.

The owner requested goal-mode continuation on2026-10-11. The goal API was still
paused when this round started; the available interface cannot resume it.
Work in this user-authorized turn proceeds, without inventing an active API
receipt or silently replacing the existing full TW/CN/web objective.

Evidence directory:
`C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-world-option-controls-source-259`.
