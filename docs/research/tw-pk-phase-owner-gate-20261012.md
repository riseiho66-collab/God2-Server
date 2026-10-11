# TW phase owner, queued89 gate and actual control obligation

Round305, baseline `b189bf1979b362288d6bc0693083b738ce9c1c0f`.
Previous304 is progress: actual receiver/state/dataflow evidence changed the next
trace, even though completed gameplay counts stayed0. This round is bounded
static native/source recovery. C++ changes0, new source branches0, opcodes0,
fullroutes0; no build/compiler/tests/runtime/native/VM/emulator/codec/DBSQL/
migration/activation/deployment. TW first, full TW/CN/web scope remains active.

## Initialization alias is concrete, later equality remains conditional

World initializer464910 saves its first argument in world+0xA7E05C4 and copies
that root+0x438 into world+0xA7E05E0. Outer4655E0 reads the saved root and places
it in the actual final stack+0x1C struct.5112C0 reads struct[0], then copies
root+0x438 into phase+0x10. These are linked callers and stack/dataflow, not a
rel32 target list. They establish shared initialization provenance.

The WORLD owner is an earlier copied pointer; the phase owner is a later fresh
read. Root/owner replacement and opaque intervening effects still need current
qualification. The initialization alias alone does not prove that pending
records transfer unchanged. Old live addresses are not current identity.

## Actual queued89 producer, gate and conditional exit

5112C0 writes phase+0xA9DF6BC=0 at5117F8. Actual secondary519370 selects opcode89
through compact index24/5195CC. It obtains native length, then51D4E0 copies the
record into phase+0xA9EA4B0 queue with capacity/wrap checks. The caller ignores
append failure, sets its local stop flag, and consumes/polls. Thus queue custody
is conditional on successful append. The3046F route consumes without this copy.

The actual phase loop calls5140C0 at515A4C. That consumer requires the active
phase+0xA9EA4C4 gate, a nonempty peek and phase+0xA9DF6C4==0 before its selected
dispatch.51D3D0 copies the queued head without consumption. Opcode89 selects
index8/514582; the second output pointee must be0 or it disables the active
gate and skips the handler. On that allowed branch518BF0 processes the copied
record. Its DWORD at record+0x31 selects0..3, while larger unsigned values join
direct cleanup; the common tail writes receive gate1. Parent consumes through
51D3D0(flag1) and repeats gate1. Copy/consume failure returns are ignored too;
this is not a lossless queue or complete error recovery proof.

Gate nonzero skips519370 and the subsequent automatic-processing cut. Gate1
does not directly set result1 or immediately exit. Separate helper conditions
52AED0()==1 and485260()!=0 lead to mode+0x44=5; a later mode5 loop with
52AED0()!=0 reaches the exit.5140C0's second output is a distinct local pointee,
cleared by its tail, not the phase result. Helper gameplay meanings remain
open.82 forward entry/staging, existing89/88 terminal semantics and eventual
return completion retain their separate evidence; no new native ACK is claimed.

## Worker send storage is distinct from parsed pending input

Actual4116F0 returns worker+0x14 send owner.411690 locks worker+0x6C, writes
time at+0x28 and increments counter+0x38.411970/411990 check worker+0x8 before
locking/unlocking+0x3C. Earlier291 already qualified4132E0/413370/4124D0; these
are historical overlap. Send staging uses owner+0x36C8/count+0x36C4, then the
embedded object at owner+0x758. New selected410A90/410960 writes framed output
at that object's+0x10. Referenced303 receive storage is object+0xC10 with its
own read cursors; parsed pending input is owner+0x2CC4. Sharing the object does
not make these byte ranges equal.

The pinned4108F0 returns constant0, excluding that selected compression branch.
The optional transform operates the supplied output bytes in place, using the
selected object seed/key fields. The socket thunk resolves originalPE ws2_32
ordinal19 (`send`); mapped IAT words differ from originalPE import words and are
separately pinned. No socket/codec execution occurred. This bounded send cut
has no direct parsed-pending consume/refill, but other children, concurrent
worker activity and owner replacement are not globally excluded. The early
same-object lead and import assumptions remain preserved as corrected history.

## Resource subobject cannot supply the adjacent opaque DWORD

Native memory offsets in this section are hexadecimal. Actual4FCDB0 passes
actor+0x224 to4FF510 and4FFA60. Insertion4FC29D supplies pool+4 to constructor
4FF3C0, which writes subobject+0x28, i.e.actor+0x24C. That Action-interface owner
is distinct from opaque actor+0x220. The constructor, init, slot, activate,
reset and cleanup bodies operate four stride6 slots and that supplied owner.
ROM WORDs are+4/+A/+10/+16, handles+6/+C/+12/+18 and per-slot BYTEs+8/+E/+14/+1A;
Action records derive from owner+0x10+handle*0x290. The signed16 table57131C is
0,-1,-2,-1. Diagnostic names/table values do not establish skill IDs or rules.

The qualified methods do not load this-4, derive the whole actor, or copy its
previous DWORD. Unexpanded Action-interface bodies/global aliases remain open;
this is a bounded readset result, not global absence. Historical302 reset and
cleanup,298/301/304 caller/insertion sites remain overlap. Original full6F
DWORDs at logical byte offsets9 and17 retain their unknown authority, including
the latter copied to actor+0x220; mandatory complete81-byte input stays intact.

## Concrete C2S36 server obligation

`RecoveredWorldRecords.h`552 retains all8 opaque payload bytes as a9-byte C2S36
TimerNotification. The actual private path is RoomBackend→BasicDriver→
LuaBasicOwner→OwnedPkOutboxPublication. Its first overload normally reads an
active owned profile before classifying; the second skips Tick and accepts
control/basic attack/context, but rejects TimerNotification. Driver failure
retires and closes both actual bound Sessions while retaining durable state.

Application5768's accepted timer path is the default-off diagnostic transition,
requiring its own one-shot diagnostic state and a solitary record. It can emit
fixture bootstrap/vitals; it is not a formal PK control implementation. Config
also disallows combining that diagnostic with owned PK invitations. Guild and
modal safe-batch classifications do not install a PK timer source. Historical
20260920 timing experiments do not prove official readiness/meaning for its
two DWORDs or early-coalesced packets. No generic no-op or guessed-success
branch is added to bypass this gap. It remains a concrete control/lifecycle
source obligation, not another completed gameplay opcode.

## Scope, accounting and next action

External archive:
`C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-pk-phase-owner-gate-305`.
Worker complete closures, qualified metadata and bounded manual scopes are
independent; entire captured files/images are not wholly manually reviewed.
Failed root guessed paths/literal wildcards were corrected with rg inventory;
combined/truncated output is not full-file review or global absence.

All990 tracked source files unchanged. Mixed segments282, CUSTOM135,
reviewed groups26/pending10. TW C2S candidate union156; world parser74=
limited50/control11/unconnected13. S2C supported252=fixed230/variable22,
nondefault206/default46, reply48/push11/gated4/unclassified117. Battle indexed
110/specialized9;86 selectors7/cases6;83 actions23/projections2/outside21.
TW unhosted chains3/bindings38/unique34; CN chains35/bindings93/unique71.
CN historical C2S156/S2C phase-opcode280/length253 have distinct scopes; CN
increment0. Whole-game packet count/completed routes/denominator, TW/game
percentages remain null. Static native instructions are not playable routes.

Next: qualify actual root+0x438 binding/replacement and reached post-reset/
pre-receive children; continue actual queued-record capacity/phase lifecycle
and original C2S36 control purpose/timing before the private PK input owner.
Continue full immutable current6F issuer/opaque DWORD9/17/packed marker/resources,
then actual Application/backend, canonical paired recipient order/ReturnHolds,
exact fullwrite failure/recovery, normal/model publication, marker retirement,
input resume and durable Finished recovery. Preserve shared64, skill/reward/
companion work, native fonts, saved accounts and existing CN/web support.

## Qualified evidence capsule

Independent static review rejected two original owner slices starting midinstruction (511797 and515858). Original seal/candidate1 retained immutable; corrected successor requalifies boundaries and replaces effective owner metrics, without new source/opcode/fullroute credit.

Original owner capsule is retained as superseded history, not qualified credit.
Corrected successor is the effective owner readset. Other bounded packages
retain explicit overlap. Original/mapped IAT words differ; each capture is12B.
Canonical formats: owner and successor whole seal excluding canonical field;
custody member-list; resource/source-obligation entire seal; sorted compact
JSON without newline. No global new coverage or gameplay completion credit.

```json
{
  "native-owner": {
    "qualified_spans": 19,
    "bytes": 2282,
    "sites": 694,
    "new_selected_spans_vs_qualified304": 15,
    "new_bytes": 2062,
    "new_sites": 629,
    "explicit_overlap_bytes": 220,
    "overlap_sites": 65,
    "data_slices": 5,
    "data_bytes": 26,
    "closure_members": 135,
    "closure_bytes": 6931644,
    "raw_seal_sha256": "c7cdf508ce49e39609c749b7eab7f8c576529f270bd652538976382f7389882b",
    "canonical_closure_sha256": "b7403607780babc306538cda530a52f81f50994caa553dacea352bf7e19a01f9",
    "global_new_coverage_claim": false,
    "qualification_superseded_by": "native-owner-corrected",
    "rejected_extents": [
      "phase_gate_zero_producer starts511797 midinstruction",
      "phase_gate_receive_overlap starts515858 midinstruction"
    ],
    "qualification_credit": false
  },
  "native-custody": {
    "qualified_spans": 16,
    "bytes": 730,
    "sites": 274,
    "new_selected_child_spans": 13,
    "new_bytes": 421,
    "new_sites": 172,
    "explicit_historical_overlap_spans": 3,
    "overlap_bytes": 309,
    "overlap_sites": 102,
    "iat_bytes_each_original_and_mapped": 12,
    "original_PE_import_metadata_bytes": 50,
    "closure_members": 159,
    "closure_bytes": 6920595,
    "raw_seal_sha256": "0a68483432eaa070c05b525aa726433d9d53e81b4b3c05508858a5b18cb8d53e",
    "canonical_closure_sha256": "7bf59128df81f730ba3f212e031b557fe4621ab123c75ca284463110e2134bd2",
    "global_new_coverage_claim": false
  },
  "native-resource": {
    "qualified_spans": 9,
    "bytes": 1477,
    "sites": 507,
    "new_selected_children": 4,
    "new_bytes": 726,
    "new_sites": 260,
    "explicit_historical_overlap_spans": 5,
    "overlap_bytes": 751,
    "overlap_sites": 247,
    "data_spans": 6,
    "data_bytes": 256,
    "complete_inputs": 18,
    "input_bytes": 6456328,
    "closure_members": 85,
    "closure_bytes": 6714116,
    "raw_seal_sha256": "d2a715670f65d45a13fe1e1083a4596ddb615bb104dbf38f024ed656688d7d98",
    "canonical_closure_sha256": "aef627f5d02305e8c4749182d9aa1f81c4fb52805e711e57f78c21edeebd5dbe",
    "global_new_coverage_claim": false
  },
  "source-obligation": {
    "complete_inputs": 16,
    "input_bytes": 979768,
    "closure_members": 22,
    "closure_bytes": 1006804,
    "raw_seal_sha256": "5d6eac1766dd53f90859a93d2c9f4804eef5314774aa547e2263c447f1d0f73e",
    "canonical_closure_sha256": "ccd97dee226278a5325802d0b7220265436e7d712777882b67c57a7a6a7d81f1",
    "global_new_coverage_claim": false
  },
  "native-owner-corrected": {
    "qualified_spans": 19,
    "bytes": 2284,
    "sites": 692,
    "new_selected_spans_vs_qualified304": 15,
    "new_bytes": 2063,
    "new_sites": 627,
    "explicit_overlap_bytes": 221,
    "overlap_sites": 65,
    "data_slices": 5,
    "data_bytes": 26,
    "global_new_coverage_claim": false,
    "raw_seal_sha256": "72ca8138af90af6a551f74a2238fd753f343331b63bea96a56228ce289cb3437",
    "canonical_closure_sha256": "0e5f43aa9ae76d4d2da40369b542b4710ec7806a52ea00a4224be960c2a4d53a",
    "closure_members": 92,
    "closure_bytes": 619272
  }
}
```
