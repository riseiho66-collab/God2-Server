# TW native timer lifecycle, root binding and actual input owner

Round306, baseline `3a0dd9294c4d4b02291f935c4defb281e3654919`.
Previous305 is progress: concrete owner initialization/queued89 evidence and
the actual C2S36 input gap changed the next trace; the corrected instruction
boundaries and historical candidates remain immutable. This round continues
TW first without reducing the complete TW/CN/web objective. No compiler/build/
tests/runtime/native/VM/emulator/codec/gameDBSQL/migration/activation/deployment.

## Actual background producer and independent timer channels

4119B0 receives the network owner and binds it to worker+0x14, then uses actual
thread entry4117E0.4115D0 initializes timing/control fields;411780(1) immediately
invokes4117B0 and updates the last36 time before enabling subsequent36 sends.
411780(0) clears that channel flag, not the whole thread or the separate30 path.
Selected thread loop waits once with1000 and then with10; an active worker flag
is required for timed processing. The separate30 channel uses5000, while the
enabled36 path requires elapsed time at least10000 and updates its own last
send time through411690. These are local native lifecycle conditions, not a
recovered server turn/grant clock, terminal ACK or mandatory server response.

4119B0 returns1 without qualifying successful thread creation. Its thread
wrapper and actual callback are linked, but that return is not a live-thread
receipt. The selected stop path waits/deletes locks without a qualified join
in that cut; other lifetime/OS children remain outside the bounded evidence.

Native memory offsets here are hexadecimal. The actual36 sender copies8 bytes
from worker+0x84/+0x88 and uses the existing send/flush path.4115D0 does not
initialize those two payload fields. They cannot be assumed zero. The separate
last-send time is worker+0x28; a time field elsewhere does not make the payload
itself a timestamp.

Actual outer465672 stores the raw context from its scratch+0x28 into worker+0x84.
That scratch field originates from82 logical byte1 DWORD.465678/46567C reads
another raw DWORD at outerESP+0x18 and stores it at worker+0x88 before enabling
the timer at465694. The actual82 second context is at scratch+0x2C, i.e. outer
ESP+0x264 for this supplied scratch atESP+0x238. It is a different byte range
fromESP+0x18. The second36 DWORD remains opaque; it is not qualified as context_b,
room ID, observer flag, timestamp or callback result. Both MOVs retain32 bits;
the raw copying does not establish signed interpretation.

## Root allocation, writer and exact instance lineage

Actual thunk531C50 supplies root5E00F8 to40D7F0; initializer bridge531D10 supplies
the same root to40DA10. Constructor40D836 initializes root+0x438 to0. Actual
40DD43 allocates0x4204,40DD65 invokes412D10, and40DD87 writes the resulting owner
to that root member before412E70. The destructor selects release through
40D985/40D996 and clears root+0x438 at40D9A4. These are qualified actual callers
and this/argument dataflow, not displacement/rel32 candidate lists.

412E70's actual third-argument branch obtains owner+0x40D4 and calls4119B0 with
the owner and supplied argument. This connects the root member and the timer
worker without assuming two same-offset pointers share identity. The actual
world initializer callers40E0D5 and40EF64 pass their retained root to464910;
the latter selected path replaces root+0x440 world storage rather than writing
root+0x438. Global-root initialization and the successful world caller branch
are qualified within the captured selected cuts.

5112C0 reads root+0x438 into phase+0x10 before any call in its selected prefix.
The first qualified reached child4181B0 clears8 bytes on the separately supplied
phase+8 child;51D350 operates the phase queue object, with an assertion child
still opaque. These bounded direct readsets do not establish equality across
every subsequent phase child, root lifetime, replacement or concurrent worker.
The complete pending-record custody and original current81-byte6F issuer,
opaque logical DWORD9/17 and resources remain open.

## Actual server frame-to-input boundary

Session.cpp1758..2003 parses/stages complete native frames, invokes the exact
installed world_records callback on the game executor, validates acceptance/
response, then sends/resumes on the strand. Timer36 receives no implicit
transport acceptance at that cut. Without the callback only movement/Tick are
allowed; other typed records fail. Pending battle/PK/terminal ownership gates
can reject a batch before the game callback. A Timer interrupting a continued
skill sequence also fails; a TCP read is not an arbitrary gameplay transaction.

Application6443..6464 installs guild_ordered_world_records, while the actual
private PK backend/source assembly remains unhosted. The exact limited
dispatch_native_basic search found private definitions/forwarders, not an
Application call; this is not a whole-repository absence proof. The default-off
single-record diagnostic Timer handler can bootstrap fixture resources and
does not establish a formal timer purpose or original server control response.

The currently private CUSTOM-0111 initial82 source uses a checked future Session
battle generation for context_a and explicit0x00001400 policy for context_b;
its protocol encoder stores them at logical bytes1 and5. The new native copy
lineage links first36 raw DWORD to the supplied first82 field. That does not
turn the CUSTOM generation policy into an original timestamp/nonce or qualify
the opaque second36 DWORD. No generic ignored/noop acceptance is added to make
the unsupported private input look complete.

## Scope and remaining work

External archive:
`C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-timer-lifecycle-306`.
Complete byte captures, actual function-entry boundary maps, selected source
views and full manual review are different scopes. Explicit historical overlap
and exploratory candidates remain excluded from local novelty. Source-routing
scope successor corrects a clerical line annotation and approximate narrow
claim ranges; the original sealed package remains preserved.

Failed guessed source paths/literal wildcard lookups were corrected using rg
inventory; combined truncated output is not full-file review or global absence.
990src unchanged. No new C++ branch, native opcode or full bidirectional route
is claimed. TW world parser74 remains limited50/control11/unconnected13; C2S
candidate union156; S2C252=fixed230/variable22. Mixed282/CUSTOM135/groups26/
pending10 unchanged. CN/web/shared64/frozen fonts/accounts/saves preserved.
Whole-game packet count/fullroutes/denominator/TW and game percentages stay null.

Next: trace the actual outerESP+0x18 writer and reached36 enable/disable callers,
then establish original server control purpose and exact allowed phase/current
owner before a genuine private input consumer. Continue post-binding opaque
children/custody and immutable current6F source, then actual Application backend,
paired recipient order/ReturnHolds/fullwrites/failure/normal publication/marker
retirement/inputresume/durable Finished recovery. Lifecycle recovery is not
formal hosting, gameplay acceptance or deployment.

## Qualified evidence capsule

Local byte/site selections are not whole-game packet coverage. Root/Timer
overlap remains separate; no global novelty sum. All seals below use producer
whole-minus-canonical sorted compact JSON without newline; key names differ.
Corrected scope/report successors reference complete immutable originals.

```json
{
  "native-timer": {
    "qualified_spans": 23,
    "bytes": 1117,
    "sites": 394,
    "new_selected_spans_vs_reference": 18,
    "new_bytes": 938,
    "new_sites": 336,
    "explicit_overlap_bytes": 179,
    "overlap_sites": 58,
    "data_slices": 5,
    "data_bytes": 119,
    "global_new_coverage_claim": false,
    "raw_seal_sha256": "feb14f1b5481aa07eee710a14b1684d32b6470f947d4c3fc16a3a38c3f3f1503",
    "canonical_closure_sha256": "9f56c731f0ab97d8ac4f6f55f7bc1c443a8d2fd229fd0e8f1af8f4c2b28c7607",
    "closure_members": 157,
    "closure_bytes": 6879234,
    "canonical_format": "Whole seal excluding own canonical field; defaultASCII compact sorted JSON no newline"
  },
  "native-binding": {
    "qualified_code_intervals": 19,
    "qualified_code_bytes": 4048,
    "qualified_instruction_sites": 1109,
    "new_local_intervals_vs_captured305_bounds": 15,
    "new_local_bytes_vs_captured305_bounds": 3707,
    "explicit_overlap_bytes": 341,
    "boundary_proof_extra_bytes_not_new_credit": 603,
    "global_historical_novelty_claim": false,
    "timer_agent_4119b0_lifecycle_not_counted": true,
    "new_source_branches": 0,
    "new_opcode_values": 0,
    "new_full_routes": 0,
    "completion_credit": 0,
    "raw_seal_sha256": "0e95c09697f805f6701125e54460a633919f481c71c35e804742e8f186bb6ad7",
    "canonical_closure_sha256": "8ec8f55050fd9ca9695aaa9ce60d80ad578bcdadb6878d6aa7debb1786a892d0",
    "closure_members": 174,
    "closure_bytes": 7076289,
    "canonical_format": "Whole seal excluding own canonical field; defaultASCII compact sorted JSON no newline",
    "report_argument_list_corrected_by": "native-binding-scope-corrected",
    "qualified_metrics_unchanged": true
  },
  "source-routing": {
    "raw_seal_sha256": "9a45c62c97ec7b943eedad2cd662ed925a97037007133ff1718fb1d268162c9e",
    "canonical_closure_sha256": "6e52994dbd53b0448ea77824948805df43865cbcc0a7700f99d621dc89ceee87",
    "closure_members": 14,
    "closure_bytes": 1048398,
    "canonical_format": "Whole seal excluding own canonical field; defaultASCII compact sorted JSON no newline",
    "scope_superseded_by": "source-routing-corrected",
    "qualified_gameplay_credit": 0,
    "complete_inputs": 10,
    "input_bytes": 1041999
  },
  "source-routing-corrected": {
    "raw_seal_sha256": "1876d0da0ef6d3ed89e93557b549f6c05b066d0589139cef7306fb8f5f4a522f",
    "canonical_closure_sha256": "9c93f0b4c8fa9d43f4a500570967e7a77e8d809f15c437e74e18d0719414a72c",
    "closure_members": 6,
    "closure_bytes": 10724,
    "canonical_format": "Whole seal excluding own canonical field; defaultASCII compact sorted JSON no newline"
  },
  "native-binding-scope-corrected": {
    "raw_seal_sha256": "0a178f603408c6f3d8f8957415c8cd307432f99e99c86e0f2bccd939734672af",
    "canonical_closure_sha256": "445b55f59b0c3e52e7a71814e24444998e411af0a72536b3ba69f0c4d5142bdb",
    "closure_members": 9,
    "closure_bytes": 115699,
    "canonical_format": "Whole seal excluding own canonical field; defaultASCII compact sorted JSON no newline"
  }
}
```
