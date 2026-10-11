# Current Client Live Movement ACK

Scope: owned loopback server, original Taiwan client, isolated diagnostic DB.
This is native-function-driven movement, not mouse-input or visual acceptance.

## Evidence

Run `artifacts/runs/native-movement-ack-20260920-02` completed with
`NATIVE_MOVEMENT_ACK_APPLIED`. The existing login/create/select/world prefix
and three frame iterations preceded the probe in the same process.

- Actual coordinates before probe: (17,13); ring count/read/write: 1/0/1.
- Private immutable RX thunk called native RVA 0x102700 with adjacent target
  (18,12), slot 1, and the existing live world object. No coordinate, queue or
  success-result field was overwritten.
- Native call returned 1; ring became 2/0/2.
- Original receive consumer at RVA 0x692FA received logical `5d01`.
- Continued original consumer through RVA 0x6B517; ACK token became 1 and ring
  became 1/1/2. Checks read actual memory rather than forcing expected values.
- Read-only SQLite inspection found recovered_positions row
  (character_id=1, area=2, scene=15, x=18, y=12, revision=1).

Regression: `LiveLoginEntryTests.test_native_movement_ack_applies_and_position_is_committed`.
It checks saved live artifacts, thunk identity, same-thread event order,
consumer completion and persisted coordinates; it does not rerun the client.

## Failed Attempt Preserved

Run `native-movement-ack-20260920-01` stopped because the diagnostic command
`bp 427 ...` was parsed as an address instead of a numbered breakpoint.
The corrected `bp427 ...` was tested in a fresh isolated run. This was a probe
error, not evidence of a game crash. Earlier `native-movement-step-20260920-01`
stopped before the ACK consumer and is not ACK-application evidence.

## Remaining Acceptance

Actual pointer-input path planning, rendered movement, multi-step traversal,
fresh reconnect restoration and full playable world acceptance remain open.
No custom combat or balance rules are promoted by this movement result.

## Three-Step Native Path Continuation

`native-movement-chain-20260920-03` used the higher-level native RVA 0x1024C0
path entry rather than calling only the low-level step sender. Three alternating
adjacent requests completed with logical ACKs 5D01, 5D02, 5D03 and queue states
1/1/2, 1/2/3, 1/3/4. Actual coordinates before each request were respectively
(17,13), (18,12), (17,13). SQLite persisted (18,12), revision 3.

The earlier chain attempts 01 and 02 are retained as diagnostic failures:
direct RVA 0x102700 could send/ack one step but did not initialize path fields
used by the original RVA 0x102570 completion logic. Waiting 100 frames did not
resolve that missing path context. RVA 0x1024C0 builds that context through
0x102B90, then calls 0x102700. No path fields or coordinates were patched.
The successful run required 11 readiness samples over three steps.

This proves consecutive native path requests with two intervening native
coordinate transitions, three accepted ACKs and three persisted revisions.
It does not prove final-step animation completion, visible pixels, physical
pointer input, arbitrary-map traversal, or reconnect restoration.

## Fresh Process Persistence Acceptance

Run `native-movement-restore-20260920-01` completed with
`NATIVE_SAVED_POSITION_RESTORED`. The harness read-only SQLite backup copied
the three-step diagnostic DB to a new isolated run; the source remained
unchanged. A new server and original client authenticated the existing lab
account, consumed a populated character list, selected character 1 and
completed native world initialization plus three frame iterations.

Actual world coordinates read from the new process were (18,12), not the
default (17,13). There was no new character submission or movement probe;
both source and destination DB rows remain (1,2,15,18,12,3). This verifies
fresh-process saved-position restoration, not automatic dropped-connection
recovery or visible scene rendering. The preceding open reconnect item is
closed only to this explicit fresh-login scope.

The restore option accepts only isolated artifact-run databases with the exact
verified three-step position row. It does not open the production database for
writing. Saved-data provenance and normal client protocol validation remain
unchanged; no custom gameplay promotion is involved.

## Final Step Completion

`native-movement-complete-20260920-01` continues after the third ACK until a
subsequent original frame returns with coordinates (18,12), movement state
at world+0x30 equal to zero, and queue count/read/write 1/3/4. It completes as
`NATIVE_MOVEMENT_PATH_COMPLETED`; DB revision remains 3. No fourth request is
generated. This closes the final-step internal coordinate/idle-state gap, not
the separate visual or physical-input acceptance gap.

Current next gameplay integration gap: RecoveredBattleService requires an
authoritative InBattle binding and encoder, while Application currently wires
RecoveredWorldService only to movement. The native logical 82 transition is
known, but its opaque context and explicit bootstrap participants still need
an isolated socket-fed live transition test before any balanced custom combat
can be promoted. Existing offline battle initializer evidence must not be
represented as this missing socket-to-battle transition.
