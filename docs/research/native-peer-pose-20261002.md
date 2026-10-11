# Native character pose peer route — 2026-10-02

## Delivered scope

C2S66 already had a local S2C77 response. The candidate now sends the same
qualified ordinary-player pose to other admitted players in the same area and
scene. Sender identity comes from the bound presence, not the request bytes.
Modes 1/2/3 and all eight directions are qualified; other modes keep the prior
opaque/no-response behavior. Existing battle/readiness gates remain in force.

Native6F initializes remote pose state to zero. The server retains persistent
modes1/2 and replays77 after6F for a late observer, appearance replacement or battle
world refresh. Mode3 is a one-shot: native502570 and4FB290 reset animation18
at ACT track completion. It is broadcast immediately but never cached/replayed
because77 has no animation time offset and would restart an old action. It also
clears a previous persistent pose. A persistent pose before first tick is retained for the
later presence admission. Actual movement (including an out-and-back batch),
battle title change, transfer and disconnect invalidate the stationary cache.
No account, character or gameplay save schema is changed.

## Native evidence

- Captured image SHA256:
  `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
- C2S producer503820 →497E00: `66 00 packedPose opaqueTail`.
- S2C77 size7; dispatch469BBA. Ordinary matching self →501610;
  ordinary non-self →4FB980, identity lookup4FC960.
- Remote actor: mode at+79, direction WORD at+3A, animation WORD at+38.
  Non-transformed modes1/2/3 select animation16/17/18.
- Native4FC1C0 used by6F initializes actor+79 to zero.
- Local502570 ->504080 and remote4FB290 ->4FD140 use4FFCB0 ->41AF90
  to detect ACT track completion. Only animation18 resets here;16/17 persist.
- Native497E00 silently drops UI pose requests within500ms. Actual-client
  tests respect this producer throttle; server authorization was not relaxed.
- Emitted record: `77 idLo idHi 00 packedPose 00 00`.
- `tools/strike_lab/current_peer_pose_20261002.py` executes the actual native
  lookup and consumer for48 cases: first/last remote pool slots ×3 modes ×8
  directions. Renderer callback4FD160 is recorded, not rendered.

Wire/layout is native evidence; membership, caching and replay policy remains
the existing CUSTOM-0027 server design. No original server implementation or
unqualified animation/effect semantics are asserted.

## Checks

- 48/48 native consumer cases, artifact:
  `artifacts/research/native-peer-pose-20261002.json`.
- 6/6 native502570 lifecycle cases (three modes × completed/not completed).
  ACT completion/renderer callbacks are isolated; native reset branch executes.
- 2 new isolated TCP tests in `tests/research/test_native_peer_pose_server.py`:
  two-way48 exchanges, pre-first-tick pose, late join, unknown payload,
  out-and-back movement, reconnect and battle-return replay.
  Includes suppression of expired one-shot replay and retained mode2 replay.
- 3 existing TCP regressions: bilingual chat/movement, join/batched movement/
  reconnect, battle title lifecycle, in `test_player_visibility_server.py`.
- 3 C++ targets pass: recovered_visibility, recovered_world_service,
  peer_role_text. Includes wrong owner/scene, unknown modes, cross-map
  isolation, movement without observers, transfer, disconnect and battle cache.
- Frozen chat verifier passes; baseline was not changed.

Initial TCP setup failed because the synthetic fixture used the wrong database
filename for the existing isolated visibility guard. The fixture was corrected
to `player-visibility-diagnostic.db`; no runtime guard was relaxed.

## Deployment and completion

Candidate: `build-town-visibility/Release/god2-server-native-results.exe`.
Real-client run `artifacts/playtests/private-peer-pose-20261002-05` passed.
Current production client SHA256 is
`c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575`.
Eleven code regions are checked against captured native bytes in both clients.
Eight UI-originating pose events cover both senders/all modes, followed by
one-shot local/remote idle completion, late idle admission without replay,
persistent mode2 late replay, original movement/save and another mode1.
The real clients execute producer, network consumer and renderer; read-only
observations verify their actual component ACT group/track bindings. This is
native functional acceptance, **not screenshot/pixel visual acceptance**.
Temporary TW/CN images differ only at the isolated server port; current client,
IME/launcher/locale config and source fixture remain hash-identical. All owned
clients, runner and isolated server exited; input desktop never changed.

Runs01/02 exposed the native producer throttle. Runs03/04 exposed stale mode3
replay and were rejected, not counted as success. The lifecycle correction is
covered by unit, TCP and real-client run05. No live saves were used for testing.

Executable-only deployment is gated by the native receipt, candidate-specific
TCP/C++ tests, frozen-chat baseline, no connected players and exact staged/live
save snapshots. Its definitive outcome is `deployment/release.json`.

Installed2026-10-02: managed server PID26352 listens on127.0.0.1:2592;
executable SHA256
`1146517e842de4b34e7228a3cf1affae3dd6e4f1db9158fdd4288d58ba221cdc`.
No migration, saved-row, configuration or production-client changes. All20
test-owned EXE/profile files were removed after process and hash checks;
receipts and rollback executable remain. The first staging attempt used an
incorrect diagnostic DB filename and was rejected before live mutation;
`deployment-stage-failed-01` preserves that evidence. Retried staging passed.

This round's automated gate:8/8 test cases/targets =100%, plus48/48 consumer
and6/6 lifecycle cases. Real-client run05 passed its bounded acceptance scope.
Whole-game packet completion remains unknown:27 parsed world C2S opcodes and
252 S2C length contracts are inventories, not a gameplay-completion denominator.
Fresh inventory: `artifacts/research/packet-gap-ledger-20261002.json`.
Before-edit snapshots and machine-readable results are in
`artifacts/releases/native-peer-pose-20261002/`.
