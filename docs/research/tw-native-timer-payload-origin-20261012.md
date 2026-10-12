# TW native Timer36 local provenance and context consumers — round307

The preceding round recovered the real owner/thread/send chain. This round
continues the unresolved second payload DWORD rather than assigning it a guessed
room ID, time, generation, acknowledgement or opponent property. Current server
baseline is `3abfdbddc58a0a677053861878fab8bd49faafb2`.

External bounded evidence:
`C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-timer-payload-origin-307`.
The original306 packages remain immutable. New source accounting is distinct
from native evidence, deployment and client acceptance.

## Stack-relative addresses are different storage

At the actual `4655E0` entry, the fixed outer stack base U is entry ESP minus
`A24`: `SUB ESP,A14` followed by four saved registers. The Timer36 writer reads
U+18, which is a callee-local address at entry ESP minus A0C. It is not a caller
argument. Earlier textual `[ESP+18]` at4655F7 has only two saved registers on the
stack and therefore refers to U+20, the scratch pointer; `[ESP+14]` at46560B is
U+1C, the root slot. Neither is a producer for U+18.

The selector3 path reaches465644 and passes output U+238 to467860. Receiver
stack allocation and output rebasing must be considered before comparing an
offset spelled `18`: output+18 is U+250, not U+18. The incoming82 fields are
output+28/+2C, hence U+260/+264. Timer36 takes its first raw DWORD from U+260,
but its second from the separate U+18 storage. The next phase call's pointer
escape occurs later than the first Timer36 send; that later escape cannot by
itself explain the first read.

This closes a concrete address-identity error, not the complete writer set.
Selected direct instructions do not establish that all opaque callees,
callbacks, indirect aliases or later iterations leave U+18 untouched. The
second DWORD stays opaque; no native garbage/uninitialised-value claim is made.

## Native82 consumers and server policy have separate provenance

The original82 logical DWORDs at byte1/byte5 are copied into scratch+28/+2C.
The actual outer initializer writes the scratch pointer into U+20 and later
passes struct base U+1C, so input+4 names that pointer slot. With that pointer
still current across intervening opaque children, the phase initializer consumes
these scratch slots as phase+3C/+40 and copies the current block into phase+48.
Complete pointer/owner lifetime across those children remains open.
These are raw field copies, not proof
of the original server's issuer, global uniqueness or timebase.

The current private `OwnedTaiwanPkInitialContextSource` is explicitly
CUSTOM-0111: its first82 field is a checked next Session battle generation,
and its second is `00001400`. `SqliteOwnedPkRoomRepository` checks the exact
owned source and generation bound. Those checks implement private source
authority; they do not establish the original meaning of either82 DWORD or
the independent Timer36 second DWORD. No source policy is relabelled native.

An additional actual path is515770→515AD8→518E50. The sender initially copies
phase+3C into its35 body+8 storage (logical DWORD9). This caller uses action0B,
phase+51 actor slot, phase+45C target count and phase+44C target array. The
callee slot/count<=14 guards do not prove that every target byte is below28:
the quotient14 mask loop can alias the low WORD of that context storage for
targets>=28. The finding is a qualified initial value and conditional overwrite,
not an unconditional82-to35 byte-for-byte echo or an original authority token.

Native context_b byte0==FF selects a phase marker and skips the selected
180000ms timeout branch. Its byte1 is zero-extended into initial countdown
storage; the selected phase-update path513C14..513C3F subtracts elapsed/1000 before passing a value
to decimal-digit display. These field uses do not prescribe an original server
default20, every spectator behavior or the authoritative battle deadline.

The selected resource-choice path also passes ctx_a to4F76D0. Its complete
helper calls547D7F, adds the supplied raw DWORD and masks the result with3.
The complete547D7F helper advances an LCG state with343FD/269EC3 and returns
the shifted15-bit result. This establishes a conditional local selector use,
not a recovered combat random seed or an original server context issuer.

## Actual server Timer36 custody

`RecoveredWorldRecords`547..558 admits30 only with a zero payload byte, and
copies36's eight payload bytes into `TimerNotification` while consuming nine
logical bytes. It does not interpret the payload as generation or clock.

Bounded Application views2718..2740,3017..3083,3161..3179 and3500..3517, plus
the complete `OwnedGuildAnnouncementBatch` and `GuildAdmission53Application`,
show Timer36 in notification/modal batch predicates. This avoids treating it
as an unrelated gameplay mutation in those predicates. It does not grant
write authority, room ownership or an original timer response. Recursive
prefix dispatch and actual runtime owners remain independent.

The complete188-line `RecoveredWorldService::handle` rejects Timer36 in its
operation loop before invoking a battle callback. Its inventory and companion
batches permit their qualified Tick controls, not Timer36. Consequently the
later empty-movement success cannot justify accepting a Timer record: the
record would already have taken the non-Tick rejection. This is a claim about
the captured function, not a repository-wide absence claim.

Application5759..5778 contains the existing standalone36 diagnostic transition
and vitals bootstrap. It requires diagnostic state and is not original
gameplay authority. Application6437..6464 binds `world_records` to
`guild_ordered_world_records`; seeing this assignment does not qualify every
hosting precondition or handler. The complete `RecoveredWorldReady` has its
existing one30/00-before-tail grammar and no36 branch.

The complete `RecoveredBattleCommand` parser already reads35 logical DWORD9
as `context_storage` and warns about the target alias. Bounded private
`OwnedPkOutboxPublication`168..225 rejects Timer36 before durable mutation;
terminal `ContextNotification` is the distinct1C record. The private basic
policy uses entry command_contexts, and `OwnedPkRoomState`110..132 checks that
policy against the exact owned entry/revision/grant/profile before persisting
an intent. This is existing private authority, still unhosted in Application;
native field-copy evidence does not automatically promote or replace it.

## Scope, progress and remaining work

990 tracked source files are captured unchanged. Full byte captures are not
complete manual source review. Root manually read the named bounded Application
windows, complete WorldService/Ready/initial-context/guild predicate files,
and repository455..490. An initial combined Application output was truncated;
retained claim windows were reread in bounded visible output. Failed literal
PowerShell glob and guessed Application path were corrected with `rg` inventory;
neither is absence evidence. The parser and private command windows named above
were also read; a further literal handler glob was corrected with `rg -g`.
Native workers and review retain their own exact
selection and manual scopes.

C++ modifications/additions0; source branches0; newly known opcodes0; complete
bidirectional gameplay routes0. Mixed source segments282, CUSTOM135, source
groups26/pending10 remain unchanged. TW C2S candidate union156; world parser74
is limited50/control11/unconnected13. TW S2C252 is fixed230/variable22;
nondefault206/default46, reply48/push11/gated4/unclassified117. Battle indexed110,
specialized9;86 selectors7/cases6;83 actions23/projections2/outside21.
TW unhosted chains3/bindings38(unique34); CN chains35/bindings93(unique71).
CN historical C2S156/S2C phaseopcode280/length253 remain distinct scopes, with
no CN increment. Full-game packet count, completed-route inventory, denominator
and TW/whole-game percentages remain unknown/null.

Original U+18 producer and authoritative Timer36 purpose/phase/response remain
open. Current immutable81-byte6F issuer, logical DWORD9/17, packed state,
resources and directed scene ownership remain open. Actual Application PK
hosting, paired ReturnHold/full writes/normal publication/marker retirement,
input resume and durable Finished recovery still require complete sources.
Original TW/CN/web/shared64/full-game scope is preserved.

No build/compiler/tests/runtime/native/VM/emulator/codec/game DB SQL,
migration/activation/deployment was performed. Frozen accounts/saves, native
fonts, text conversion, chat/IME/authentication/portraits/client remain intact.

## Qualified evidence capsule

Native selections and limited-reference new bytes/sites are not gameplay coverage.
Overlap is retained separately; no global novelty sum. Worker closures use
whole-minus-canonical defaultASCII compact sorted JSON without newline.

```json
{
  "native-payload": {
    "qualified_spans": 15,
    "bytes": 953,
    "sites": 245,
    "new_selected_spans_vs_reference": 1,
    "new_bytes": 47,
    "new_sites": 17,
    "explicit_overlap_bytes": 906,
    "overlap_sites": 228,
    "data_slices": 2,
    "data_bytes": 36,
    "global_new_coverage_claim": false,
    "raw_seal_sha256": "9772464cc8f33d02c6eab77d8679a2c6802794ba524f8fe5e81b3c21df68dd0d",
    "canonical_closure_sha256": "d6af4525e9e4a499956c208bdb9e4a8240814b3eebb5aa7b6d283e575d5a148c",
    "closure_members": 94,
    "closure_bytes": 6818696,
    "canonical_format": "Whole seal excluding own canonical_closure_sha256; defaultASCII compact sorted JSON no newline"
  },
  "native-context": {
    "qualified_code_intervals": 18,
    "qualified_code_bytes": 3895,
    "qualified_instruction_sites": 1060,
    "new_local_intervals_with_bytes_vs_captured303_304_305_306_qualified_bounds": 14,
    "new_local_bytes_vs_captured303_304_305_306_qualified_bounds": 3578,
    "explicit_reference_overlap_bytes": 317,
    "qualified_data_slices": 3,
    "qualified_data_bytes": 44,
    "boundary_map_extra_bytes_not_new_credit": 3031,
    "global_historical_novelty_claim": false,
    "new_source_branches": 0,
    "new_opcode_values": 0,
    "new_full_routes": 0,
    "completion_credit": 0,
    "completion_percentage": null,
    "raw_seal_sha256": "29045b8fb4bbb876e98bab57a585c31b55902be6ef54c4151ab152c75e7f9575",
    "canonical_closure_sha256": "bcd1dc316ce98f6829c7ddd8180aecc22eed2e48280991985765296383cb1c2e",
    "closure_members": 206,
    "closure_bytes": 8086569,
    "canonical_format": "Whole seal excluding own canonical_closure_sha256; defaultASCII compact sorted JSON no newline"
  },
  "source-routing": {
    "complete_inputs": 9,
    "input_bytes": 838744,
    "raw_seal_sha256": "97a8c1ef5e659025ba06b255ef82a45f2ba7c4feae7fda499fe611c69f17c2c5",
    "canonical_closure_sha256": "f3b0f4c473bace2f8fa3361b9f17c777bc75b7da457084e34288cc64e173ef09",
    "closure_members": 13,
    "closure_bytes": 847190,
    "canonical_format": "Whole seal excluding own canonical_closure_sha256; defaultASCII compact sorted JSON no newline"
  },
  "source-command": {
    "complete_inputs": 3,
    "input_bytes": 73352,
    "raw_seal_sha256": "50cefe9baa6f0bf17d1837bd7930cfde9e8f57990090b5eb6c313306e63db53f",
    "canonical_closure_sha256": "1d375417620ff4c11735c024e82e015b642738b5d66861eca11d8d9d15409cb7",
    "closure_members": 7,
    "closure_bytes": 77042,
    "canonical_format": "Whole seal excluding own canonical_closure_sha256; defaultASCII compact sorted JSON no newline"
  }
}
```
