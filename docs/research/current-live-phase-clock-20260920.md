# Live Native Phase Scanner And OS Clock

## Scope

An opt-in `--probe-native-phase` mode extends the existing guarded offline
constructor experiment. It requires `--probe-native-monster` and local entry;
normal constructor mode is unchanged. After original text binding and the
side1 diagnostic identity constructor return, an RX lab thunk calls original
12AC20 on the actual world-owned manager with explicit phase0. It does not
create substitute actor objects, supply numerical stats or receive a packet.

Transport stop-before-call guards, working-copy firewall and bounded process
lifetime remain in the existing runner. There is no listener, official server
connection, desktop input, account data or production activation.

## Observed Runs

- `artifacts/runs/offline-phase-live-20260920-01`: PID10856, returned normally;
  observed before/after the timer bridge, but not the OS export entry.
- `artifacts/runs/offline-phase-live-20260920-02`: PID14852, TID13208, observed
  12AC20 ->12AE2F ->winmm!timeGetTime ->12AE35 ->RX thunk return.

Run02's IAT target00E30000 is the existing verified timer compatibility tail
bridge, not the OS export itself. Its captured8 bytes are validated as
`sub esp,0; jmp rel32`; the resolved destination74917860 is separately hit and
identified by CDB as winmm!timeGetTime, forwarding to KERNEL32!timeGetTime.
The OS entry preserves native return address0052AE35. No timestamp or return
value is written by the observer. Returned EAX3995103 matches the DWORD stored
at manager+A7FBCC0. The count at+A7FBC64 is0 and original function returns0,
consistent with its signed count>0 predicate; this is not a failed invocation.
RET4 restores entry ESP exactly. Before/after112-byte snapshots have recorded
SHA256 values and are verified by the regression test.

Both runs restored the alternate-entry instruction and timer IAT, reported
unchanged executable disk bytes, and ended their owned processes. Process
queries confirmed neither PID remained. Run02 reports no error or transport
boundary event. Nine `test_current_offline_monster_live` tests pass, including
stage order, PCs/thread, bridge destination, stack, timestamp, snapshot hashes
and restoration evidence for this new run.

## Reproduce

Use a fresh evidence directory name:

```powershell
python -B -m tools.strike_lab.current_offline_client_run --run-id offline-phase-NEW --timeout 90 --enter-local-world --probe-native-monster 1 --probe-native-phase
python -m unittest tests.research.test_current_offline_monster_live -v
```

This closes the native scanner/clock/return boundary under actual post-constructor
objects. It does NOT close a received88's full dispatcher path, active battle
animation, normal battle initialization, server turn policy, original formulas
or playable own-server E2E. The explicit diagnostic invocation must not be
presented as an organically triggered packet consumer. The next integration
must validate receiver prerequisites on these real objects before invoking it.
