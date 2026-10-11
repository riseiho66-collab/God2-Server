# Current C2S30 and black-box regression

## Authority

Current mapped image:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Image base is 0x400000; addresses below are RVAs/file offsets.

Both retained corpora were searched first. Classic
`OfficialLiveMovementWorldBatchWire.cs` recognizes C2S30 as a five-byte
parser-only sideband, without qualified gameplay mutations or an S2C reply.
XJZ did not provide a concrete equivalent in the scoped heartbeat search.
Old fixture opcodes 1005/2005 are not used for the recovered connection.

Current native evidence:

- 115D0 initializes the timer period to 5000 ms.
- 11837..11852 uses unsigned `(now - anchor) / period > sent_count` to select
  the periodic-send branch. The native test covers threshold and DWORD wrap.
- 11750 obtains the network pointer through 116F0 (timer+14), queues exactly
  opcode 30 and a zero body byte using 132E0, then flushes via 13370.
- The null network branch returns without queueing.
- The existing movement builder 15790 queues into that same buffer. Original
  execution proves a pending movement record can precede 30 00 in one frame.
- Original zero-seed encoder output for an otherwise empty queue is
  `05 00 2D 2D 22`. Logical payload is `30 00`; checksum is 25 hex.

`test_current_periodic_tick.py` executes these original instructions with
pinned image identity. The send run stops before the socket call at 12501;
the timer slice stops at the branch decision. This is not an OS timer run,
live capture, rendered-world acceptance, or proof of a server response.

## Fix

The previous executable rejected the native mixed movement/tick queue and
closed the connection before ACK. Reproducer:

```
python -B -m unittest test_recovered_periodic_tick_server.RecoveredPeriodicTickServerTests.test_original_mixed_queue_and_coalesced_frames -v
```

Run from `tests/research`. Before rebuild it failed with unexpected EOF.

`RecoveredMovement::parse_world_batch` now validates the whole declared frame,
bounded length, checksum, every record opcode, record bounds and the exact
tick body constant. It extracts movements and counts ticks. The original
`parse_batch` API remains movement-only and rejects mixed or tick-only input.

The opt-in world stream accepts complete ticks after world-ready, including
fragmented TCP delivery, mixed logical batches and coalesced wire frames.
A tick produces no fabricated reply, no position write and no movement-ring
advance. Existing idle timer behavior remains. Malformed/unknown frames
close the connection without committing any movement from that decoded batch.
The login state still rejects ticks. A later private-desktop original-client
playtest proved that the independent character connection can send the same
tick while waiting at character selection. That authenticated preselection
state now accepts the exact decoded `30 00` frame without a reply; see
`docs/research/private-desktop-playtest-20260923.md`.

## Parallel Black-Box Work

- Login/reconnect: seven new cases, including concurrent first registration,
  replay, malformed credentials, wrong state, account isolation, invalid stored
  hashes and recovery after a transaction failure. No production bug reproduced.
- Position: seven new cases with failure matrices, including reservation
  cleanup, stale snapshots, ownership change, reconnect/ring reset and atomic
  rollback of batch and trigger side effects. No production bug reproduced.
- Content CLIs: malformed companion section counts now reject; quest structural
  validation must pass before publishing; invalid skill-book lookup is checked
  before publishing. Nine subprocess tests cover bounded failures and preservation
  of pre-existing output on those rejected inputs. Missing gameplay semantics
  remain unknown rather than being filled with synthetic values.
- NPC: two retained S2C72 logical records have bounded current-native catalog
  and scalar checks. See `current-npc-spawn-20260919.md`; no runtime spawn enabled.

The four agents are closed after handoff. No Lua gameplay rule, formula,
coordinate placement, database schema or default production mode was changed
by this verification round.

## Verification Result

- `cmake --build build --config Release --parallel 2`: PASS. The first build
  caught a shadowed local fixture name under /WX; renamed and rebuilt cleanly.
  Existing Session getenv deprecation warnings remain unchanged.
- Core CTest: 26/26 PASS, including new `recovered_npc_spawn`. The five unrelated
  research suites `artifact_vault`, `runtime_evidence`, `gate_review`,
  `counter_resolution`, `runtime_environment` were excluded, not claimed tested.
- Rebuilt executable and native-code selection: 65/65 PASS in 163.428 seconds;
  additional native timer threshold and world-tail/tick coalescence: 2/2 PASS.
- All six content suites plus subprocess CLI black-box suite: 53/53 PASS in
  19.150 seconds. Real client source bytes and retained artifacts still agree.
- The old-binary EOF reproducer now passes with the identical native-generated
  input. Tick-only frames do not generate ACKs or position revisions, and valid
  movement remains usable afterward.

Total selected checks: 26 CTest cases and 120 Python tests passed. This is not
the entire repository test inventory. No original client world was rendered in
this round; full playable-world acceptance remains outstanding.
